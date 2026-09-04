import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from cmdrhelper.cargo import cargo_snapshot, normalize_inventory, read_cargo_snapshot
from cmdrhelper.i18n import set_language
from cmdrhelper.journal_reader import read_latest_state
from cmdrhelper.route_planner.models import ShipLoadoutData
from cmdrhelper.state import AppState
from cmdrhelper.ui.main_window import CargoLiveWindow


class _Signal:
    def __init__(self):
        self.values = []

    def emit(self, value):
        self.values.append(value)


class _Settings:
    def __init__(self):
        self.values = {}

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value

    def sync(self):
        pass


def _cargo(vessel="Ship", count=0, inventory=None, timestamp="2026-09-04T16:31:29Z"):
    event = {"timestamp": timestamp, "event": "Cargo", "Vessel": vessel,
             "Count": count}
    if inventory is not None:
        event["Inventory"] = inventory
    return event


class CargoSnapshotTests(unittest.TestCase):
    def test_reader_exposes_latest_cargo_event_and_active_rhino(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "Journal.2026-09-04T160000.01.log"
            events = [
                {"timestamp": "2026-09-04T16:00:00Z", "event": "Fileheader"},
                {"timestamp": "2026-09-04T16:00:01Z", "event": "Commander",
                 "FID": "F-A", "Name": "Alpha"},
                {"timestamp": "2026-09-04T16:00:02Z", "event": "LoadGame",
                 "FID": "F-A", "Commander": "Alpha", "Ship": "CobraMkIII",
                 "ShipID": 51},
                {"timestamp": "2026-09-04T16:00:03Z", "event": "Loadout",
                 "Ship": "CobraMkIII", "ShipID": 51, "CargoCapacity": 256,
                 "Modules": []},
                {"timestamp": "2026-09-04T16:00:04Z", "event": "LaunchSRV",
                 "SRVType": "mev_rhino", "SRVType_Localised": "SRV Rhino",
                 "PlayerControlled": True},
                _cargo("SRV", 11, timestamp="2026-09-04T16:00:05Z"),
            ]
            path.write_text("".join(json.dumps(event) + "\n" for event in events),
                            encoding="utf-8")
            state = read_latest_state(Path(folder))
        self.assertEqual(state["commander_fid"], "F-A")
        self.assertEqual(state["active_srv_type"], "SRV Rhino")
        self.assertEqual(state["last_cargo_event"]["Vessel"], "SRV")
        self.assertEqual(state["ship_loadout"].cargo_capacity, 256)

    def test_full_ship_snapshot_has_capacity_free_space_and_multiple_commodities(self):
        snapshot = cargo_snapshot(_cargo(count=199, inventory=[
            {"Name": "palladium", "Name_Localised": "Palladium", "Count": 126, "Stolen": 0},
            {"Name": "osmium", "Name_Localised": "Osmium", "Count": 28, "Stolen": 0},
            {"Name": "silver", "Name_Localised": "Silber", "Count": 45, "Stolen": 0},
        ]), fid="F-A", ship_id=51, cargo_capacity=256)
        self.assertEqual(snapshot["count"], 199)
        self.assertEqual(snapshot["capacity"], 256)
        self.assertEqual(snapshot["ship_id"], 51)
        self.assertEqual([item["display_name"] for item in snapshot["inventory"]],
                         ["Palladium", "Osmium", "Silber"])

    def test_drones_are_case_insensitively_combined_and_still_count_as_cargo(self):
        items = normalize_inventory([
            {"Name": "drones", "Name_Localised": "Drohne", "Count": 3, "Stolen": 0},
            {"Name": "Drones", "Name_Localised": "Drohne", "Count": 95, "Stolen": 2},
        ])
        self.assertEqual(len(items), 1)
        self.assertEqual((items[0]["count"], items[0]["stolen"]), (98, 2))
        self.assertTrue(items[0]["is_drones"])

    def test_count_only_event_uses_matching_cargo_json(self):
        with TemporaryDirectory() as folder:
            trigger = _cargo(count=56)
            path = Path(folder) / "Cargo.json"
            path.write_text(json.dumps({**trigger, "Inventory": [
                {"Name": "copper", "Name_Localised": "Kupfer", "Count": 56,
                 "Stolen": 0},
            ]}), encoding="utf-8")
            snapshot = read_cargo_snapshot(
                path, trigger, fid="F-A", ship_id=51, cargo_capacity=256
            )
        self.assertEqual(snapshot["inventory"][0]["display_name"], "Kupfer")

    def test_mismatching_or_half_written_cargo_json_is_not_accepted(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "Cargo.json"
            path.write_text('{"event":"Cargo",', encoding="utf-8")
            snapshot = read_cargo_snapshot(
                path, _cargo(count=1), fid="F-A", attempts=2, retry_delay=0,
            )
            self.assertIsNone(snapshot)
            path.write_text(json.dumps({**_cargo(vessel="SRV", count=1),
                                        "Inventory": [{"Name": "gold", "Count": 1,
                                                       "Stolen": 0}]}), encoding="utf-8")
            snapshot = read_cargo_snapshot(path, _cargo(count=1), fid="F-A")
            self.assertIsNone(snapshot)

    def test_short_json_failure_is_retried_before_accepting_stable_snapshot(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "Cargo.json"
            path.write_text("{", encoding="utf-8")
            payload = {**_cargo(count=1), "Inventory": [
                {"Name": "gold", "Name_Localised": "Gold", "Count": 1, "Stolen": 0}
            ]}
            calls = []

            def repair(_delay):
                calls.append(True)
                path.write_text(json.dumps(payload), encoding="utf-8")

            snapshot = read_cargo_snapshot(
                path, _cargo(count=1), fid="F-A", attempts=2, sleeper=repair
            )
        self.assertEqual(len(calls), 1)
        self.assertEqual(snapshot["count"], 1)

    def test_srv_snapshot_has_no_ship_capacity_or_ship_id(self):
        snapshot = cargo_snapshot(_cargo("SRV", 11, [
            {"Name": "gold", "Name_Localised": "Gold", "Count": 11, "Stolen": 0}
        ]), fid="F-A", ship_id=51, cargo_capacity=256, srv_type="SRV Rhino")
        self.assertEqual(snapshot["vessel"], "SRV")
        self.assertIsNone(snapshot["capacity"])
        self.assertIsNone(snapshot["ship_id"])
        self.assertEqual(snapshot["vehicle_name"], "SRV Rhino")

    def test_active_fid_reset_discards_old_snapshot(self):
        state = SimpleNamespace(cargo_snapshot={"fid": "F-A"},
                                cargoSnapshotChanged=_Signal())
        AppState.reset_commander_runtime_state(state)
        self.assertIsNone(state.cargo_snapshot)
        self.assertEqual(state.cargoSnapshotChanged.values, [None])

    def test_rhino_dock_waits_for_authoritative_ship_cargo(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "Cargo.json"
            srv_event = _cargo("SRV", 11)
            path.write_text(json.dumps({**srv_event, "Inventory": [
                {"Name": "gold", "Name_Localised": "Gold", "Count": 11,
                 "Stolen": 0}
            ]}), encoding="utf-8")
            state = SimpleNamespace(
                cargo_snapshot=None, cargoSnapshotChanged=_Signal(),
                commander_fid="F-A", journal_folder=Path(folder),
                ship_loadout=ShipLoadoutData(ship_id=51, cargo_capacity=256),
                viewed_commander_id=999,
            )
            session = {"attribution_status": "identified", "commander_id": 1,
                       "fid_seen": "F-A"}
            AppState._apply_live_cargo_snapshot(
                state, {"last_cargo_event": srv_event,
                        "active_srv_type": "SRV Rhino"}, session
            )
            self.assertEqual(state.cargo_snapshot["vessel"], "SRV")

            # DockSRV alone leaves the last authoritative SRV snapshot intact.
            state.viewed_commander_id = 2
            AppState._apply_live_cargo_snapshot(
                state, {"last_cargo_event": srv_event, "active_srv_type": ""}, session
            )
            self.assertEqual(state.cargo_snapshot["vessel"], "SRV")

            ship_event = _cargo("Ship", 11, timestamp="2026-09-04T16:33:00Z")
            path.write_text(json.dumps({**ship_event, "Inventory": [
                {"Name": "gold", "Name_Localised": "Gold", "Count": 11,
                 "Stolen": 0}
            ]}), encoding="utf-8")
            AppState._apply_live_cargo_snapshot(
                state, {"last_cargo_event": ship_event, "active_srv_type": ""}, session
            )
            self.assertEqual(state.cargo_snapshot["vessel"], "Ship")
            self.assertEqual(state.cargo_snapshot["capacity"], 256)
            self.assertEqual(state.viewed_commander_id, 2)

    def test_unidentified_fid_or_ship_change_never_reuses_old_ship_cargo(self):
        state = SimpleNamespace(
            cargo_snapshot={"fid": "F-A", "vessel": "Ship", "ship_id": 51},
            cargoSnapshotChanged=_Signal(), commander_fid="F-A",
            journal_folder=Path("."),
            ship_loadout=ShipLoadoutData(ship_id=51, cargo_capacity=256),
        )
        AppState._apply_live_cargo_snapshot(
            state, {}, {"attribution_status": "ambiguous", "commander_id": None}
        )
        self.assertIsNone(state.cargo_snapshot)

        state.cargo_snapshot = {"fid": "F-A", "vessel": "Ship", "ship_id": 51}
        state.ship_loadout = ShipLoadoutData(ship_id=52, cargo_capacity=64)
        AppState._apply_live_cargo_snapshot(
            state, {}, {"attribution_status": "identified", "commander_id": 1,
                        "fid_seen": "F-A"}
        )
        self.assertIsNone(state.cargo_snapshot)


class CargoLiveWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        set_language("de")
        self.window = CargoLiveWindow(_Settings())
        self.addCleanup(self.window.close)

    def test_ship_capacity_empty_unknown_and_stolen_display(self):
        self.window.set_snapshot({
            "vessel": "Ship", "count": 56, "capacity": 256,
            "inventory": [{"frontier_name": "copper", "display_name": "Kupfer",
                           "count": 56, "stolen": 3, "is_drones": False}],
        })
        self.assertEqual(self.window.title_label.text(), "FRACHTRAUM — SCHIFF")
        self.assertEqual(self.window.summary_label.text(), "56 / 256 t · 200 t frei")
        self.assertEqual(self.window.table.horizontalHeaderItem(0).text(), "Name")
        self.assertEqual(self.window.table.horizontalHeaderItem(1).text(), "Anzahl")
        self.assertEqual(
            self.window.table.item(0, 0).text(),
            "Kupfer · davon 3 t gestohlen",
        )
        self.assertEqual(self.window.table.item(0, 1).text(), "56 t")
        self.assertEqual(
            self.window.table.item(0, 1).textAlignment(),
            int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter),
        )

        self.window.set_snapshot({"vessel": "Ship", "count": 0,
                                  "capacity": None, "inventory": []})
        self.assertEqual(self.window.summary_label.text(),
                         "0 t geladen · Kapazität unbekannt")
        self.assertEqual(self.window.table.item(0, 0).text(), "Frachtraum leer")
        self.assertEqual(self.window.table.columnSpan(0, 0), 2)

    def test_rhino_and_drones_are_visibly_separate(self):
        self.window.set_snapshot({
            "vessel": "SRV", "vehicle_name": "SRV Rhino", "count": 12,
            "capacity": None, "inventory": [
                {"frontier_name": "gold", "display_name": "Gold", "count": 11,
                 "stolen": 0, "is_drones": False},
                {"frontier_name": "drones", "display_name": "Drohne", "count": 1,
                 "stolen": 0, "is_drones": True},
            ],
        })
        self.assertEqual(self.window.title_label.text(), "FRACHTRAUM — RHINO")
        self.assertEqual(self.window.summary_label.text(), "12 t")
        self.assertEqual(self.window.table.item(0, 0).text(), "Gold")
        self.assertEqual(self.window.table.item(0, 1).text(), "11 t")
        self.assertEqual(self.window.table.item(1, 0).text(), "Drohnen")
        self.assertEqual(self.window.table.item(1, 1).text(), "1")
        self.assertTrue(self.window.table.item(1, 0).font().bold())


if __name__ == "__main__":
    unittest.main()
