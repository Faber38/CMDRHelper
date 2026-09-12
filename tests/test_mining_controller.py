import json
import os
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QObject, Signal, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from cmdrhelper.mining_controller import MiningInventoryController
from cmdrhelper.mining_inventory import MiningInventory
from cmdrhelper.ui.mining_view import MiningView


class State(QObject):
    changed = Signal()
    viewedCommanderChanged = Signal(object)
    cargoSnapshotChanged = Signal(object)


class MiningControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.journal = self.folder / "Journal.2026-09-12T120000.01.log"
        self.database = self.folder / "inventory.db"
        self.settings_path = str(self.folder / "settings.ini")
        self.events = [dict(event="Commander", FID="F1"), dict(event="LoadGame", FID="F1", Ship="CobraMkIII"),
                       dict(event="Cargo", Vessel="Ship", Count=12)]
        self.write()
        (self.folder / "Cargo.json").write_text(json.dumps({**self.events[-1], "Inventory": [dict(Name="gold", Count=12)]}))
        with sqlite3.connect(self.database) as con:
            con.executescript("CREATE TABLE commanders(id INTEGER,fid TEXT); INSERT INTO commanders VALUES(1,'F1'),(2,'F2');"
                "CREATE TABLE journal_sessions(journal_file TEXT,commander_id INTEGER,fid_seen TEXT,attribution_status TEXT);")
            con.execute("INSERT INTO journal_sessions VALUES(?,?,?,?)", (str(self.journal), 1, "F1", "identified"))
        self.state = State()
        self.state.database = SimpleNamespace(path=self.database)
        self.state.settings = QSettings(self.settings_path, QSettings.Format.IniFormat)
        self.state.commander_id = self.state.viewed_commander_id = 1
        self.state.commander_fid = "F1"
        self.state._journal_index_sessions = [dict(journal_file=str(self.journal), commander_id=1,
                                                  fid_seen="F1", attribution_status="identified")]

    def write(self):
        for i, event in enumerate(self.events):
            event["timestamp"] = f"2026-09-12T12:00:{i:02}Z"
        self.journal.write_text("".join(json.dumps(e) + "\n" for e in self.events))

    def make_controller(self):
        controller = MiningInventoryController(self.state)
        self.addCleanup(controller.deleteLater)
        self.addCleanup(controller.pool.waitForDone)
        self.addCleanup(controller.timer.stop)
        results = []
        controller.ready.connect(results.append)
        return controller, results

    def wait_for(self, results, count):
        for _ in range(400):
            self.app.processEvents()
            if len(results) >= count:
                return
            QTest.qWait(10)
        self.fail("No background mining inventory result")

    def test_start_live_refinement_and_restart_with_persisted_sidecar(self):
        controller, results = self.make_controller()
        self.wait_for(results, 1)
        self.assertEqual(results[-1].stock("gold")[0], 12)
        self.assertTrue(self.state.settings.value("materials/mining/cargo_checkpoints/1"))
        self.events.append(dict(event="MiningRefined", Type="gold"))
        self.write()
        self.state.changed.emit()
        self.wait_for(results, 2)
        self.assertEqual(results[-1].stock("gold")[0], 13)
        (self.folder / "Cargo.json").write_text("{}")
        self.state.settings = QSettings(self.settings_path, QSettings.Format.IniFormat)
        restarted, restored = self.make_controller()
        self.wait_for(restored, 1)
        self.assertEqual(restored[-1].stock("gold")[0], 13)
        self.assertFalse(restarted.timer.isActive())  # No polling loop.

    def test_commander_switch_clears_immediately_and_rejects_old_results(self):
        controller, results = self.make_controller()
        loading = []
        controller.loading.connect(lambda: loading.append(True))
        self.wait_for(results, 1)
        old_generation = controller._generation
        self.state.viewed_commander_id = 2
        self.state.viewedCommanderChanged.emit(2)
        self.assertEqual(len(loading), 2)
        controller._finished(old_generation, MiningInventory(1, "F1", vehicle={"gold": 1000}))
        self.assertEqual(len(results), 1)
        self.wait_for(results, 2)
        self.assertEqual(results[-1].fid, "F2")
        self.assertIsNone(results[-1].stock("gold")[0])

    def test_ambiguous_current_session_does_not_display_previous_live_stock(self):
        controller, results = self.make_controller()
        self.wait_for(results, 1)
        self.assertEqual(results[-1].stock("gold")[0], 12)
        self.state._journal_index_sessions[-1]["attribution_status"] = "ambiguous"
        self.state.changed.emit()
        self.wait_for(results, 2)
        self.assertIsNone(results[-1].vehicle)

    def make_view(self, controller):
        view = MiningView(self.state.settings, controller=controller)
        self.addCleanup(view.deleteLater)
        return view

    def test_manual_refresh_rereads_sidecar_and_updates_table_then_live_events(self):
        snapshot = (self.folder / "Cargo.json").read_text()
        (self.folder / "Cargo.json").write_text("{")
        controller, results = self.make_controller()
        outcomes = []
        controller.refreshFinished.connect(outcomes.append)
        view = self.make_view(controller)
        self.wait_for(results, 1)
        self.assertEqual(view.items["gold"].text(1), "—")
        # Only the sidecar changes; no journal event or state signal is emitted.
        (self.folder / "Cargo.json").write_text(snapshot)
        QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
        self.assertTrue(controller._running)
        self.assertFalse(controller.timer.isActive())
        self.wait_for(results, 2)
        self.assertEqual(results[-1].vessel, "Ship")
        self.assertEqual(view.items["gold"].text(1), "12")
        self.assertEqual(outcomes, ["updated"])
        self.assertEqual(view.items["gold"].text(2), "— ✎")
        self.events.append(dict(event="MiningRefined", Type="gold"))
        self.write()
        self.state.changed.emit()
        self.wait_for(results, 3)
        self.assertEqual(view.items["gold"].text(1), "13")
        self.assertFalse(controller.timer.isActive())

    def test_manual_status_distinguishes_unchanged_and_invalid_sidecar_with_checkpoint(self):
        controller, results = self.make_controller()
        outcomes = []
        controller.refreshFinished.connect(outcomes.append)
        self.wait_for(results, 1)
        self.assertEqual(outcomes, [])
        controller.refresh_now()
        self.wait_for(results, 2)
        self.assertEqual(outcomes, ["unchanged"])
        (self.folder / "Cargo.json").write_text("{}")
        controller.refresh_now()
        self.wait_for(results, 3)
        self.assertEqual(results[-1].stock("gold")[0], 12)  # Keep valid persisted cargo.
        self.assertEqual(outcomes, ["unchanged", "error"])

    def test_manual_refresh_switches_to_verified_srv_snapshot(self):
        controller, results = self.make_controller()
        view = self.make_view(controller)
        self.wait_for(results, 1)
        self.events.extend([dict(event="LaunchSRV"), dict(event="Cargo", Vessel="SRV", Count=3)])
        self.write()
        (self.folder / "Cargo.json").write_text(json.dumps({**self.events[-1],
            "Inventory": [dict(Name="gold", Count=3)]}))
        QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
        self.wait_for(results, 2)
        self.assertEqual(results[-1].vessel, "SRV")
        self.assertEqual(view.items["gold"].text(1), "3")  # Not Ship + SRV.

    def test_manual_refresh_missing_snapshot_stays_unknown(self):
        (self.folder / "Cargo.json").unlink()
        controller, results = self.make_controller()
        view = self.make_view(controller)
        self.wait_for(results, 1)
        QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
        self.wait_for(results, 2)
        self.assertIsNone(results[-1].vehicle)
        self.assertEqual(view.items["gold"].text(1), "—")

    def test_manual_refresh_rejects_wrong_fid_and_vessel(self):
        (self.folder / "Cargo.json").unlink()
        controller, results = self.make_controller()
        outcomes = []
        controller.refreshFinished.connect(outcomes.append)
        self.wait_for(results, 1)
        (self.folder / "Cargo.json").write_text(json.dumps({**self.events[-1], "Vessel": "SRV",
            "Inventory": [dict(Name="gold", Count=12)]}))
        controller.refresh_now()
        self.wait_for(results, 2)
        self.assertIsNone(results[-1].vehicle)
        # Sidecar identity is established by the journal, not an invented Cargo.json FID.
        self.events[0]["FID"] = self.events[1]["FID"] = "F2"
        self.write()
        (self.folder / "Cargo.json").write_text(json.dumps({**self.events[-1],
            "Inventory": [dict(Name="gold", Count=12)]}))
        controller.refresh_now()
        self.wait_for(results, 3)
        self.assertIsNone(results[-1].vehicle)
        self.assertEqual(outcomes, ["error", "error"])

    def test_manual_status_accepts_verified_full_journal_snapshot(self):
        self.events[-1]["Inventory"] = [dict(Name="gold", Count=12)]
        self.write()
        (self.folder / "Cargo.json").unlink()
        controller, results = self.make_controller()
        outcomes = []
        controller.refreshFinished.connect(outcomes.append)
        self.wait_for(results, 1)
        controller.refresh_now()
        self.wait_for(results, 2)
        self.assertEqual(outcomes, ["unchanged"])

    def test_status_comparison_ignores_explicit_zero_entries(self):
        self.assertEqual(MiningInventoryController._inventory_signature(MiningInventory(1, "F1", vehicle={})),
                         MiningInventoryController._inventory_signature(MiningInventory(1, "F1", vehicle={"gold": 0})))

    def test_manual_status_accepts_verified_empty_journal_cargo(self):
        self.events[-1]["Count"] = 0
        self.write()
        (self.folder / "Cargo.json").unlink()
        controller, results = self.make_controller()
        outcomes = []
        controller.refreshFinished.connect(outcomes.append)
        self.wait_for(results, 1)
        controller.refresh_now()
        self.wait_for(results, 2)
        self.assertEqual(results[-1].vehicle, {})
        self.assertEqual(outcomes, ["unchanged"])

    def test_manual_refresh_while_running_is_followed_up_without_debounce(self):
        controller, results = self.make_controller()
        self.wait_for(results, 1)
        controller._running = True
        controller.refresh_now()
        self.assertTrue(controller._manual_pending)
        self.assertFalse(controller.timer.isActive())
        controller._finished(controller._generation, results[-1])
        self.assertTrue(controller._running)
        self.assertFalse(controller._manual_pending)
        self.assertFalse(controller.timer.isActive())
        self.wait_for(results, 3)

    def add_owned_carrier(self):
        with sqlite3.connect(self.database) as con:
            con.execute("CREATE TABLE commander_carriers(commander_id INTEGER, carrier_id INTEGER)")
            con.execute("INSERT INTO commander_carriers VALUES(1,123)")

    def test_confirm_carrier_refresh_restart_and_live_transfer(self):
        self.add_owned_carrier()
        controller, results = self.make_controller()
        view = self.make_view(controller)
        self.wait_for(results, 1)
        self.assertEqual(view.items["gold"].text(2), "— ✎")
        identity = (1, "F1", 123)
        controller.confirm_carrier("gold", 504, identity)
        self.assertEqual(view.items["gold"].text(2), "504 ✎")
        self.assertEqual(view.items["gold"].text(3), "516")
        before = len(results)
        controller.refresh_now()
        self.wait_for(results, before + 1)
        self.assertEqual(view.items["gold"].text(2), "504 ✎")
        self.assertEqual(results[-1].carrier_records["gold"]["status"], "manual")
        self.assertIn("504", view.items["gold"].text(2))
        restarted, restored = self.make_controller()
        self.wait_for(restored, 1)
        self.assertEqual(restored[-1].stock("gold")[1], 504)
        (self.folder / "Cargo.json").write_text("{}")
        before = len(results)
        controller.refresh_now()
        self.wait_for(results, before + 1)
        self.assertEqual(results[-1].stock("gold")[1], 504)
        self.events.extend([dict(event="Docked", MarketID=123, StationType="FleetCarrier"),
            dict(event="CargoTransfer", Transfers=[dict(Type="gold", Count=50, Direction="toship")])])
        self.write()
        before = len(results)
        self.state.changed.emit()
        self.wait_for(results, before + 1)
        self.assertEqual(results[-1].stock("gold"), (62, 454, 516))
        self.assertEqual(results[-1].carrier_records["gold"]["status"], "tracked")
        controller.confirm_carrier("gold", None, identity)
        self.assertEqual(view.items["gold"].text(2), "— ✎")
        self.assertEqual(view.items["gold"].text(3), "—")

    def test_carrier_confirmation_rejects_changed_identity_and_missing_owner(self):
        self.add_owned_carrier()
        controller, results = self.make_controller()
        self.wait_for(results, 1)
        for identity in ((1, "F2", 123), (1, "F1", 999), (2, "F1", 123)):
            with self.assertRaises(ValueError):
                controller.confirm_carrier("gold", 504, identity)
        with sqlite3.connect(self.database) as con:
            con.execute("UPDATE commander_carriers SET carrier_id=999")
        with self.assertRaises(ValueError):
            controller.confirm_carrier("gold", 504, (1, "F1", 123))

    def test_confirmation_anchors_at_dialog_accept_not_older_background_result(self):
        self.add_owned_carrier()
        controller, results = self.make_controller()
        self.wait_for(results, 1)
        self.events.append(dict(event="CargoTransfer", CarrierID=123,
                                Transfers=[dict(Type="gold", Count=50, Direction="toship")]))
        self.write()
        controller.confirm_carrier("gold", 504, (1, "F1", 123))
        before = len(results)
        controller.refresh_now()
        self.wait_for(results, before + 1)
        self.assertEqual(results[-1].stock("gold")[1], 504)

    def test_jadeite_cargo_snapshot_and_live_refinement_are_visible_with_filters(self):
        self.events[-1]["Count"] = 22
        self.write()
        (self.folder / "Cargo.json").write_text(json.dumps({**self.events[-1],
            "Inventory": [dict(Name="jadeite", Name_Localised="Jadeit", Count=22)]}))
        controller, results = self.make_controller()
        view = self.make_view(controller)
        view.set_origin_filter("surface")
        view.only_stock.setChecked(True)
        self.wait_for(results, 1)
        jadeite = view.items["jadeite"]
        self.assertEqual(jadeite.text(1), "22")
        self.assertEqual(jadeite.data(4, Qt.ItemDataRole.UserRole), 41895)
        self.assertFalse(jadeite.isHidden())
        self.assertEqual({symbol for symbol, item in view.items.items() if not item.isHidden()}, {"jadeite"})
        self.events.append(dict(event="MiningRefined", Type="jadeite"))
        self.write()
        self.state.changed.emit()
        self.wait_for(results, 2)
        self.assertEqual(jadeite.text(1), "23")
        self.assertFalse(jadeite.isHidden())
