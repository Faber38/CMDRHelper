import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import csv
import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtWidgets import QApplication
from cmdrhelper.route_planner.carrier_inputs import CarrierInputTracker, parse_snapshot
from cmdrhelper.route_planner.carrier_input_widget import CarrierInputWidget
from cmdrhelper.route_planner.models import CarrierRouteRequest
from cmdrhelper.route_planner.spansh_client import SpanshFleetCarrierClient, SpanshError, ROUTE_URL
from cmdrhelper.route_planner.workers import CarrierRouteWorker
from cmdrhelper.route_planner.ctsvision_csv import HEADER, export_ctsvision_csv
from cmdrhelper.journal_reader import read_latest_state, classify_journal_file


def now():
    return datetime.now(timezone.utc).isoformat()


def stats(**changes):
    event = dict(event="CarrierStats", timestamp=now(), CarrierID=42,
                 Callsign="ABC-123", CarrierType="FleetCarrier", FuelLevel=1000,
                 Crew=[{"CrewRole": "Repair"}],
                 SpaceUsage=dict(TotalCapacity=25000, FreeSpace=19666, Cargo=4404,
                                 Crew=930, CargoSpaceReserved=0, ShipPacks=0, ModulePacks=0))
    event.update(changes)
    return event


def request(**changes):
    return replace(CarrierRouteRequest("Pueloi VY-S d3-94", "Greae Phoea CG-S c6-82",
        1000, 4400, 500, capacity_used=5334, commander_fid="F-A",
        carrier_callsign="ABC-123", carrier_id=42, confirmed_at=now()), **changes)


class CarrierInputTests(unittest.TestCase):
    def test_nyenyon_snapshot(self):
        snapshot = parse_snapshot(stats(), "F-A", "session")
        self.assertEqual((snapshot.capacity, snapshot.used, snapshot.cargo, snapshot.fuel),
                         (25000, 5334, 4404, 1000))
        self.assertEqual(dict(snapshot.space)["Crew"], 930)
        self.assertTrue(snapshot.usable("F-A", "session"))

    def test_all_capacity_components(self):
        space = dict(TotalCapacity=25000, FreeSpace=19000, Cargo=4404, Crew=930,
                     CargoSpaceReserved=66, ShipPacks=200, ModulePacks=400)
        self.assertEqual(parse_snapshot(stats(SpaceUsage=space), "F-A", "s").used, 6000)

    def test_partial_breakdown_does_not_replace_total(self):
        for space in ({"TotalCapacity": 25000, "FreeSpace": 19000},
                      {"TotalCapacity": 25000, "FreeSpace": 19000, "Cargo": 4404, "Crew": 930}):
            self.assertEqual(parse_snapshot(stats(SpaceUsage=space), "F-A", "s").used, 6000)

    def test_missing_and_contradictory_capacity_unknown(self):
        for space in ({}, {"Cargo": 4404, "Crew": 930},
                      {"TotalCapacity": 25000, "FreeSpace": 25001},
                      {"TotalCapacity": 25000, "FreeSpace": 24000, "Cargo": 4404},
                      {"TotalCapacity": 25000, "FreeSpace": 19000, "Cargo": -1},
                      dict(stats()["SpaceUsage"], FreeSpace=19000)):
            with self.subTest(space=space):
                self.assertIsNone(parse_snapshot(stats(SpaceUsage=space), "F-A", "s").used)

    def test_missing_fuel_not_zero(self):
        for fuel in (None, -1, 1001, True, "1000"):
            self.assertIsNone(parse_snapshot(stats(FuelLevel=fuel), "F-A", "s").fuel)

    def test_empty_and_full_journal_capacity(self):
        for free, expected in ((25000, 0), (0, 25000)):
            snapshot = parse_snapshot(stats(SpaceUsage={"TotalCapacity": 25000, "FreeSpace": free}), "F-A", "s")
            self.assertEqual(snapshot.used, expected)

    def test_snapshot_identity_and_time(self):
        observed = parse_snapshot(stats(), "F-A", "session")
        for changes in (dict(fid="F-B"), dict(session="other"), dict(carrier_id=None),
                        dict(callsign=""), dict(carrier_type="SquadronCarrier"),
                        dict(carrier_type=""), dict(invalidated=True),
                        dict(observed_at=(datetime.now(timezone.utc)-timedelta(minutes=16)).isoformat()),
                        dict(observed_at=(datetime.now(timezone.utc)+timedelta(minutes=1)).isoformat()),
                        dict(observed_at="invalid")):
            self.assertFalse(replace(observed, **changes).usable("F-A", "session"))

    def test_valid_empty_full_separate_tank(self):
        for used, stored, tank in ((0, 0, 0), (0, 0, 1000), (25000, 25000, 1000),
                                  (25000, 0, 0), (5334, 4400, 1000)):
            self.assertIsNone(request(capacity_used=used, tritium_in_storage=stored,
                                      tritium_in_tank=tank).validation_error())

    def test_invalid_requests(self):
        for changes in (dict(capacity_used=None), dict(capacity_used=-1), dict(capacity_used=25001),
                        dict(capacity_used=4399), dict(tritium_in_storage=-1),
                        dict(tritium_in_tank=-1), dict(tritium_in_tank=1001), dict(capacity=60000),
                        dict(capacity_used=True), dict(confirmed_at=""), dict(carrier_callsign=""),
                        dict(commander_fid=""), dict(input_source="unknown")):
            with self.subTest(changes=changes):
                self.assertEqual(request(**changes).validation_error(), "carrier_inputs")

    def test_confirmation_expires(self):
        old = (datetime.now(timezone.utc)-timedelta(minutes=16)).isoformat()
        self.assertEqual(request(confirmed_at=old).validation_error(), "carrier_inputs")

    def test_auto_request_bound_to_observation(self):
        observed = parse_snapshot(stats(), "F-A", "session")
        auto = request(input_source="journal", snapshot=observed, session="session")
        self.assertIsNone(auto.validation_error())
        for changes in (dict(carrier_id=43), dict(carrier_callsign="OTHER"),
                        dict(session="old"), dict(capacity_used=5400), dict(tritium_in_tank=900),
                        dict(tritium_in_storage=4500), dict(snapshot=None)):
            self.assertIsNotNone(replace(auto, **changes).validation_error())

    def test_mutations_invalidate_without_simulating(self):
        for kind in ("CarrierDepositFuel", "CargoTransfer", "CarrierJump", "CarrierJumpRequest",
                     "CarrierTradeOrder", "CarrierCrewServices", "CarrierShipPack", "CarrierModulePack",
                     "MarketBuy", "MarketSell"):
            tracker = CarrierInputTracker()
            tracker.apply(stats(), "F-A", "journal")
            tracker.apply(dict(event=kind, timestamp=now(), Amount=100, Total=1000), "F-A", "journal")
            self.assertTrue(tracker.snapshot.invalidated)
            self.assertEqual((tracker.snapshot.used, tracker.snapshot.fuel), (5334, 1000))

    def test_session_and_commander_reset(self):
        for fid, file, event in (("F-B", "a", {"event": "Location"}),
                                 ("F-A", "b", {"event": "Location"}),
                                 ("F-A", "a", {"event": "LoadGame"}),
                                 ("F-A", "a", {"event": "Shutdown"})):
            tracker = CarrierInputTracker()
            tracker.apply(stats(), "F-A", "a")
            tracker.apply(event, fid, file)
            self.assertIsNone(tracker.snapshot)

    def test_repeated_same_second_transfer_has_distinct_revision(self):
        tracker = CarrierInputTracker()
        event = dict(event="CargoTransfer", timestamp=now())
        tracker.apply(event, "F-A", "a")
        first = tracker.revision
        tracker.apply(event, "F-A", "a")
        self.assertNotEqual(tracker.revision, first)

    def test_carrier_switch_replaces_snapshot(self):
        tracker = CarrierInputTracker()
        tracker.apply(stats(), "F-A", "a")
        tracker.apply(stats(CarrierID=43, Callsign="DEF-456", FuelLevel=100), "F-A", "a")
        self.assertEqual((tracker.snapshot.carrier_id, tracker.snapshot.callsign, tracker.snapshot.fuel),
                         (43, "DEF-456", 100))

    def test_out_of_order_stats_invalidated(self):
        tracker = CarrierInputTracker()
        tracker.apply(stats(), "F-A", "a")
        tracker.apply(stats(timestamp="2020-01-01T00:00:00Z"), "F-A", "a")
        self.assertTrue(tracker.snapshot.invalidated)

    def test_journal_data_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            events = [dict(event="Commander", FID="F-A", Name="Alpha", timestamp=now()),
                      dict(event="LoadGame", FID="F-A", Commander="Alpha", timestamp=now()), stats()]
            path = folder / "Journal.2026-10-13T120000.01.log"
            path.write_text("\n".join(json.dumps(e) for e in events)+"\n")
            data = read_latest_state(folder, powerplay_history=False)
            self.assertEqual(data["carrier_snapshot"].used, 5334)
            self.assertTrue(data["carrier_snapshot"].usable("F-A", data["carrier_input_session"]))
            second = folder / "Journal.2026-10-13T130000.01.log"
            second.write_text(json.dumps(dict(event="Commander", FID="F-B", Name="Beta", timestamp=now()))+"\n")
            data = read_latest_state(folder, powerplay_history=False)
            self.assertIsNone(data["carrier_snapshot"])

    def test_unknown_latest_journal_does_not_reuse_older_stats(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            events = [dict(event="Commander", FID="F-A", Name="Alpha", timestamp=now()), stats()]
            (folder/"Journal.2026-10-13T120000.01.log").write_text(
                "\n".join(json.dumps(e) for e in events)+"\n")
            (folder/"Journal.2026-10-13T130000.01.log").write_text(
                json.dumps(dict(event="Location", StarSystem="Sol", timestamp=now()))+"\n")
            self.assertIsNone(read_latest_state(folder, powerplay_history=False)["carrier_snapshot"])

    def test_indexed_journal_refresh_invalidates_after_transfer(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            path = folder/"Journal.2026-10-13T120000.01.log"
            events = [dict(event="Commander", FID="F-A", Name="Alpha", timestamp=now()), stats()]
            path.write_text("\n".join(json.dumps(e) for e in events)+"\n")
            sessions = [classify_journal_file(path)]
            data = read_latest_state(folder, indexed_sessions=sessions, powerplay_history=False)
            self.assertEqual(data["carrier_snapshot"].used, 5334)
            with path.open("a") as stream:
                stream.write(json.dumps(dict(event="CarrierDepositFuel", timestamp=now(),
                                             CarrierID=42, Amount=100, Total=1000))+"\n")
            data = read_latest_state(folder, indexed_sessions=sessions, powerplay_history=False)
            self.assertTrue(data["carrier_snapshot"].invalidated)

    def test_invalid_client_request_never_uses_network(self):
        client = SpanshFleetCarrierClient()
        with patch.object(client, "_request_json") as network:
            with self.assertRaises(SpanshError):
                client.calculate(request(capacity_used=None))
            network.assert_not_called()

    def test_invalid_worker_never_resolves_or_calls_client(self):
        client = Mock()
        worker = CarrierRouteWorker(request(capacity_used=None), client)
        with patch("cmdrhelper.route_planner.workers.with_known_system_ids") as resolve:
            worker.run()
            resolve.assert_not_called()
            client.calculate.assert_not_called()

    def test_nyenyon_payload_multiple_jumps_and_csv(self):
        client = SpanshFleetCarrierClient()
        response = {"result": {"jumps": [
            dict(name="Pueloi VY-S d3-94", distance=0, fuel_used=0, fuel_in_tank=1000, tritium_in_market=4400),
            dict(name="Middle", distance=480, fuel_used=81, fuel_in_tank=919, tritium_in_market=4400),
            dict(name="Greae Phoea CG-S c6-82", distance=490, fuel_used=82, fuel_in_tank=918,
                 tritium_in_market=4319, must_restock=True)]}}
        with patch("cmdrhelper.route_planner.spansh_client.resolve_system", side_effect=[11, 22]), \
                patch.object(client, "_request_json", return_value=response) as network:
            route = client.calculate(request())
        network.assert_called_once_with(ROUTE_URL, data=dict(source=11, destinations=22,
            mass=25000, capacity=25000, capacity_used=5334, fuel_loaded=1000,
            tritium_stored=4400, calculate_starting_fuel=0))
        self.assertEqual(route.estimated_tritium, 163)
        self.assertEqual([(j.fuel_in_tank, j.tritium_in_market) for j in route.jumps],
                         [(1000, 4400), (919, 4400), (918, 4319)])
        self.assertTrue(route.jumps[-1].must_restock)
        with tempfile.TemporaryDirectory() as tmp:
            path = export_ctsvision_csv(route, Path(tmp)/"route.csv")
            with path.open(newline="") as stream:
                rows = list(csv.reader(stream))
            self.assertEqual(rows[0], list(HEADER))
            self.assertEqual(rows[-1][3:6], ["918", "4319", "82"])


class CarrierWidgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.state = SimpleNamespace(commander_fid="F-A", carrier_input_session="s",
            carrier_input_revision="stats", carrier_snapshot=parse_snapshot(stats(), "F-A", "s"))
        self.widget = CarrierInputWidget(self.state)
        self.addCleanup(self.widget.close)

    def confirm(self):
        self.widget.storage.setValue(4400)
        self.widget.confirm.setChecked(True)
        return self.widget.request("Sol", "Alpha", 500)

    def test_auto_values_storage_unknown(self):
        self.assertEqual((self.widget.used.value(), self.widget.tank.value(), self.widget.storage.value()),
                         (5334, 1000, -1))
        self.assertEqual(self.widget.free.text(), "19666 t")
        self.assertFalse(self.widget.used.isEnabled())
        self.assertIsNone(self.confirm().validation_error())

    def test_manual_inputs_require_confirmation(self):
        self.widget.manual.setChecked(True)
        self.widget.used.setValue(5334)
        self.widget.tank.setValue(1000)
        self.widget.storage.setValue(4400)
        self.assertIsNotNone(self.widget.request("S", "D", 500).validation_error())
        self.widget.confirm.setChecked(True)
        self.assertIsNone(self.widget.request("S", "D", 500).validation_error())
        self.widget.used.setValue(5400)
        self.assertFalse(self.widget.confirm.isChecked())

    def test_manual_without_snapshot(self):
        self.state.carrier_snapshot = None
        self.widget.refresh()
        self.widget.manual.setChecked(True)
        self.widget.callsign.setText("DEF-456")
        self.widget.used.setValue(0)
        self.widget.tank.setValue(1000)
        self.widget.storage.setValue(0)
        self.widget.confirm.setChecked(True)
        self.assertIsNone(self.widget.request("S", "D", 500).validation_error())

    def test_context_changes_clear_inputs_and_confirmation(self):
        for field, value in (("commander_fid", "F-B"), ("carrier_input_session", "other"),
                             ("carrier_input_revision", "transfer")):
            self.confirm()
            setattr(self.state, field, value)
            self.widget.refresh()
            self.assertFalse(self.widget.confirm.isChecked())
            self.assertEqual(self.widget.storage.value(), -1)

    def test_transfer_requires_fresh_values_no_inference(self):
        self.widget.manual.setChecked(True)
        self.widget.used.setValue(5334)
        self.widget.tank.setValue(900)
        self.confirm()
        self.state.carrier_input_revision = "transfer"
        self.widget.refresh()
        self.assertEqual((self.widget.used.value(), self.widget.tank.value()), (-1, -1))
        self.widget.used.setValue(5234)
        self.widget.tank.setValue(1000)
        self.widget.storage.setValue(4300)
        self.widget.confirm.setChecked(True)
        self.assertIsNone(self.widget.request("S", "D", 500).validation_error())

    def test_stale_snapshot_becomes_unknown(self):
        self.confirm()
        self.state.carrier_snapshot = replace(self.state.carrier_snapshot,
            observed_at=(datetime.now(timezone.utc)-timedelta(minutes=16)).isoformat())
        self.widget.refresh()
        self.assertEqual((self.widget.used.value(), self.widget.tank.value()), (-1, -1))
        self.assertFalse(self.widget.confirm.isChecked())

    def test_carrier_change_in_view_rejects_pending_result(self):
        from cmdrhelper.route_planner.route_planner_view import RoutePlannerView
        view = RoutePlannerView(self.state)
        self.addCleanup(view.close)
        view.carrier_start_system.setText("Sol")
        view.carrier_destination_system.setText("Alpha")
        view.carrier_inputs.storage.setValue(4400)
        view.carrier_inputs.confirm.setChecked(True)
        with patch("cmdrhelper.route_planner.route_planner_view.CarrierRouteWorker") as worker, \
                patch.object(view._thread_pool, "start"):
            view._calculate_carrier_route()
            self.assertEqual(worker.call_args.args[0].capacity_used, 5334)
        self.state.carrier_snapshot = parse_snapshot(stats(CarrierID=43, Callsign="DEF-456"), "F-A", "s")
        view.carrier_inputs.refresh()
        view._sync_carrier_identity()
        view._carrier_route_finished(Mock())
        self.assertIsNone(view._carrier_route)
        self.assertFalse(view.carrier_export_button.isEnabled())
        self.assertTrue(view.carrier_calculate_button.isEnabled())
        self.assertFalse(view.carrier_inputs.confirm.isChecked())

    def test_themes_and_all_languages(self):
        from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language
        from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
        keys = ("carrier_manual", "carrier_callsign", "carrier_base", "carrier_capacity", "carrier_used",
                "carrier_free", "carrier_observed", "carrier_unavailable", "carrier_confirm", "carrier_input_error")
        self.assertEqual(len(_TRANSLATIONS), 12)
        self.addCleanup(set_language, get_language())
        for lang, translations in _TRANSLATIONS.items():
            for key in keys:
                self.assertTrue(translations["route_planner."+key], (lang, key))
            set_language(lang)
            widget = CarrierInputWidget(self.state)
            self.addCleanup(widget.close)
            self.assertEqual(widget.manual.text(), translations["route_planner.carrier_manual"])
            for stylesheet in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                widget.setStyleSheet(stylesheet)
                widget.show()
                self.app.processEvents()
                self.assertFalse(widget.grab().isNull())
                self.assertEqual(widget.used.value(), 5334)
