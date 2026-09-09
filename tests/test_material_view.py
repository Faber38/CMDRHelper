import json
import sqlite3
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PySide6.QtCore import QObject, QSettings, Signal, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from cmdrhelper.i18n import set_language, get_language, _TRANSLATIONS
from cmdrhelper.material_catalog import get_material, localized_name
from cmdrhelper.material_controller import MaterialController
from cmdrhelper.material_inventory import MaterialInventory, MaterialInventoryReader, _Reducer
from cmdrhelper.ui.material_view import MaterialView
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


def event(kind, second=0, **fields):
    return dict(event=kind, timestamp=f"2026-09-08T10:00:{second:02d}Z", **fields)


def snapshot(raw=None):
    return event("Materials", Raw=raw or [], Manufactured=[], Encoded=[])


class StubController(QObject):
    loading = Signal()
    ready = Signal(object, str)


class State(QObject):
    changed = Signal()
    viewedCommanderChanged = Signal(object)
    commanderIdentityChanged = Signal(object, str, str)
    journalIndexReady = Signal(object)
    databaseImportFinished = Signal(object, str)


class MaterialViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        previous = get_language()
        self.addCleanup(set_language, previous)
        set_language("de")
        self.state = SimpleNamespace(settings=QSettings(str(Path(self.tmp.name) / "settings.ini"), QSettings.Format.IniFormat))
        self.controller = StubController()
        self.view = MaterialView(self.state, controller=self.controller)
        self.view.resize(850, 720)
        self.view.show()
        self.addCleanup(self.view.close)
        self.reducer = _Reducer(1, "F1")
        self.reducer.apply(snapshot(), ("file", 0))
        self.view.set_inventory(self.reducer.result, "Commander A")

    def fixture(self):
        self.reducer = _Reducer(1, "FTEST0001")
        events = json.loads((Path(__file__).parent / "fixtures/materials_faber38.json").read_text())
        for i, e in enumerate(events):
            self.reducer.apply(e, ("faber", i))
        self.view.set_inventory(self.reducer.result, "FABER38")

    def test_three_categories_all_special_groups_visible(self):
        self.assertEqual(self.view.tabs.count(), 4)
        groups = set()
        total = 0
        for index, count in enumerate((28, 71, 47)):
            self.view.tabs.setCurrentIndex(index)
            self.assertEqual(len(self.view.items), count)
            total += len(self.view.items)
            groups.update(get_material(s).group for s in self.view.items)
        self.assertEqual(total, 146)
        self.assertEqual(groups, {"standard", "guardian", "thargoid"})

    def test_search_localized_and_english_and_combined_filter(self):
        self.fixture()
        self.view.search.setText("Schwefel")
        self.assertEqual(set(self.view.items), {"sulphur"})
        self.view.search.setText("sulphur")
        self.assertEqual(set(self.view.items), {"sulphur"})
        self.view.filter.setCurrentIndex(4)
        self.assertEqual(set(self.view.items), {"sulphur"})
        self.view.filter.setCurrentIndex(1)
        self.assertFalse(self.view.items)
        self.view.search.setText("does not exist")
        self.assertFalse(self.view.items)

    def test_all_five_filters(self):
        raw = [dict(Name=n, Count=c) for n, c in dict(sulphur=0, carbon=60, iron=61, nickel=240, phosphorus=300).items()]
        self.reducer.apply(snapshot(raw), ("file", 1))
        self.view.set_inventory(self.reducer.result)
        expected = {"all": {"carbon", "iron", "nickel", "phosphorus", "sulphur"},
                    "empty": {"sulphur"}, "low": {"carbon"}, "near_full": {"nickel"}, "full": {"phosphorus"}}
        sample = expected["all"]
        for i, key in enumerate(self.view.FILTERS):
            self.view.filter.setCurrentIndex(i)
            self.assertEqual(set(self.view.items) & sample, expected[key])

    def test_grade_groups_and_alphabetical_names(self):
        set_language("en")
        self.view.render()
        tree = self.view.tree
        self.assertEqual([tree.topLevelItem(i).text(0) for i in range(tree.topLevelItemCount())],
                         ["Grade 1", "Grade 2", "Grade 3", "Grade 4"])
        for i in range(tree.topLevelItemCount()):
            group = tree.topLevelItem(i)
            names = [group.child(j).text(0) for j in range(group.childCount())]
            self.assertEqual(names, sorted(names, key=str.casefold))
        self.view.tabs.setCurrentIndex(2)
        last = tree.topLevelItem(tree.topLevelItemCount() - 1)
        self.assertEqual(last.text(0), "Unknown grade")
        self.assertEqual(last.child(0), self.view.items["tg_shipsystemsdata"])

    def test_zero_stock_has_empty_bar(self):
        item = self.view.items["vanadium"]
        self.assertEqual(item.text(2), "0 / 250")
        self.assertEqual(self.view.tree.itemWidget(item, 3).value(), 0)

    def test_unknown_stock_has_no_bar_or_specific_filter(self):
        self.controller.loading.emit()
        self.assertIn("geladen", self.view.status.text())
        self.assertEqual(self.view.items["vanadium"].text(2), "? / 250")
        self.assertIsNone(self.view.tree.itemWidget(self.view.items["vanadium"], 3))
        self.view.set_inventory(MaterialInventory(2, "F2"), "B")
        self.assertEqual(self.view.status.text(), "Bestand unbekannt")
        for index in range(1, 5):
            self.view.filter.setCurrentIndex(index)
            self.assertFalse(self.view.items)

    def test_unknown_maximum_has_no_bar_or_specific_filter(self):
        self.reducer.apply(event("MaterialCollected", 1, Name="tg_shipsystemsdata", Category="Encoded", Count=12), ("file", 1))
        self.view.set_inventory(self.reducer.result)
        self.view.tabs.setCurrentIndex(2)
        item = self.view.items["tg_shipsystemsdata"]
        self.assertEqual(item.text(2), "12 / ?")
        self.assertEqual(item.text(1), "?")
        self.assertIsNone(self.view.tree.itemWidget(item, 3))
        for index in range(1, 5):
            self.view.filter.setCurrentIndex(index)
            self.assertNotIn("tg_shipsystemsdata", self.view.items)

    def test_faber38_values_and_percent(self):
        self.fixture()
        for symbol, count in dict(sulphur=300, vanadium=244, tin=53, molybdenum=63, niobium=53, yttrium=35).items():
            self.assertTrue(self.view.items[symbol].text(2).startswith(f"{count} / "))
        self.assertEqual(self.view.items["vanadium"].text(2), "244 / 250")
        self.assertEqual(self.view.tree.itemWidget(self.view.items["vanadium"], 3).format(), "97,6 %")
        self.view.tabs.setCurrentIndex(2)
        self.assertEqual(self.view.items["dataminedwake"].text(2), "0 / 100")
        self.assertFalse(self.view.highlight)  # Initial reconstruction is not a fresh collection.

    def test_real_faber38_journals_render_correctly(self):
        database = Path(__file__).resolve().parents[1] / "data/cmdrhelper.db"
        if not database.exists():
            self.skipTest("local FABER38 database unavailable")
        with sqlite3.connect(database.as_uri() + "?mode=ro&immutable=1", uri=True) as con:
            con.row_factory = sqlite3.Row
            commander = con.execute("SELECT id,current_name,fid FROM commanders WHERE current_name='FABER38' COLLATE NOCASE").fetchone()
            if commander is None:
                self.skipTest("local FABER38 commander unavailable")
            sessions = [dict(row) for row in con.execute("SELECT * FROM journal_sessions WHERE commander_id=?", (commander["id"],))
                        if Path(row["journal_file"]).name <= "Journal.2026-09-08T123632.01.log"]
        if not sessions or not all(Path(s["journal_file"]).exists() for s in sessions):
            self.skipTest("original FABER38 journals unavailable")
        inventory = MaterialInventoryReader().reconstruct(commander["id"], commander["fid"], sessions)
        self.assertTrue(inventory.known, inventory.issues)
        self.view.set_inventory(inventory, commander["current_name"])
        for symbol, count in dict(sulphur=300, vanadium=244, tin=53, molybdenum=63, niobium=53, yttrium=35).items():
            self.assertTrue(self.view.items[symbol].text(2).startswith(f"{count} / "))
        self.assertEqual(self.view.tree.itemWidget(self.view.items["vanadium"], 3).format(), "97,6 %")
        for tab, count in enumerate((28, 71, 47)):
            self.view.tabs.setCurrentIndex(tab)
            self.assertEqual(len(self.view.items), count)
        self.assertEqual(self.view.items["dataminedwake"].text(2), "0 / 100")

    def test_english_name_fallback(self):
        set_language("fi")
        self.view.tabs.setCurrentIndex(2)
        self.assertEqual(self.view.items["consumerfirmware"].text(0), "Modified Consumer Firmware")
        self.assertNotEqual(self.view.items["consumerfirmware"].text(0), "consumerfirmware")
        self.assertEqual(localized_name("sulphur"), _TRANSLATIONS["fi"]["body_detail.material.sulphur"])

    def test_collection_highlight_expires_and_is_not_replayed(self):
        self.view.highlight_timer.setInterval(35)
        self.reducer.apply(event("MaterialCollected", 1, Name="vanadium", Category="Raw", Count=1), ("file", 1))
        self.view.set_inventory(self.reducer.result)
        self.assertEqual(self.view.items["vanadium"].text(0), "Vanadium +1")
        self.assertNotIn("+", self.view.items["tin"].text(0))
        QTest.qWait(65)
        self.assertEqual(self.view.items["vanadium"].text(0), "Vanadium")
        self.view.set_inventory(self.reducer.result)
        self.assertFalse(self.view.highlight)

    def test_recovery_from_unknown_does_not_replay_historical_collection(self):
        self.view.set_inventory(MaterialInventory(1, "F1"))
        self.reducer.apply(event("MaterialCollected", 1, Name="vanadium", Category="Raw", Count=3), ("file", 1))
        self.view.set_inventory(self.reducer.result)
        self.assertFalse(self.view.highlight)
        self.assertEqual(self.view.items["vanadium"].text(2), "3 / 250")

    def test_consumption_clears_collection_highlight(self):
        self.reducer.apply(event("MaterialCollected", 1, Name="vanadium", Category="Raw", Count=3), ("file", 1))
        self.view.set_inventory(self.reducer.result)
        self.reducer.apply(event("Synthesis", 2, Materials=[dict(Name="vanadium", Count=1)]), ("file", 2))
        self.view.set_inventory(self.reducer.result)
        self.assertFalse(self.view.highlight)
        self.assertEqual(self.view.items["vanadium"].text(2), "2 / 250")

    def test_commander_change_clears_values_and_keeps_search_filter(self):
        self.fixture()
        self.view.search.setText("Vanadium")
        self.view.filter.setCurrentIndex(3)
        self.controller.loading.emit()
        self.assertFalse(self.view.items)
        self.assertEqual(self.view.search.text(), "Vanadium")
        self.assertEqual(self.view.filter.currentData(), "near_full")
        other = _Reducer(2, "F2")
        other.apply(snapshot([dict(Name="vanadium", Count=200)]), ("other", 0))
        self.controller.ready.emit(other.result, "Commander B")
        self.assertEqual(self.view.items["vanadium"].text(2), "200 / 250")
        self.assertEqual(self.view.commander_label.text(), "Commander B")
        self.assertFalse(self.view.highlight)

    def test_tab_and_filter_persist_but_not_inventory(self):
        self.view.tabs.setCurrentIndex(2)
        self.view.filter.setCurrentIndex(4)
        restarted = MaterialView(self.state, controller=StubController())
        self.addCleanup(restarted.close)
        self.assertEqual(restarted.tabs.currentIndex(), 2)
        self.assertEqual(restarted.filter.currentData(), "full")
        self.assertFalse(restarted.inventory.known)
        self.assertEqual(set(self.state.settings.allKeys()), {"materials/category", "materials/filter"})

    def test_dark_light_and_resizing(self):
        previous = self.app.styleSheet()
        self.addCleanup(self.app.setStyleSheet, previous)
        self.fixture()
        for light, stylesheet in ((False, DARK_STYLESHEET), (True, LIGHT_STYLESHEET)):
            self.app.setStyleSheet(stylesheet)
            self.view.set_light_mode(light)
            for width in (600, 1100):
                self.view.resize(width, 600)
                self.app.processEvents()
                item = self.view.items["vanadium"]
                self.assertEqual(item.text(2), "244 / 250")
                self.assertGreaterEqual(self.view.tree.columnWidth(2), self.view.fontMetrics().horizontalAdvance(item.text(2)))
                bar = self.view.tree.itemWidget(item, 3)
                self.assertIn("#17212a" if light else "#f2f4f5", bar.styleSheet())

    def test_all_new_ui_keys_in_all_twelve_languages(self):
        keys = {k for k in _TRANSLATIONS["en"] if k.startswith("materials.")}
        self.assertEqual(len(keys), 20)
        for code, table in _TRANSLATIONS.items():
            self.assertTrue(all(table.get(k) for k in keys), code)


class MaterialControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.db = self.path / "test.db"
        with sqlite3.connect(self.db) as con:
            con.execute("CREATE TABLE commanders(id INTEGER, fid TEXT, current_name TEXT)")
            con.execute("CREATE TABLE journal_sessions(commander_id INTEGER, fid_seen TEXT, journal_file TEXT, attribution_status TEXT)")
            for cid, amount in ((1, 40), (2, 200)):
                fid = f"F{cid}"
                file = self.path / f"{cid}.log"
                records = [event("Commander", FID=fid), snapshot([dict(Name="vanadium", Count=amount)])]
                file.write_text(''.join(json.dumps(e)+'\n' for e in records))
                con.execute("INSERT INTO commanders VALUES(?,?,?)", (cid, fid, f"Commander {cid}"))
                con.execute("INSERT INTO journal_sessions VALUES(?,?,?,?)", (cid, fid, str(file), "identified"))
        self.state = State()
        self.state.commander_id = self.state.viewed_commander_id = 1
        self.state.commander_fid = "F1"
        self.state.database = SimpleNamespace(path=self.db)
        self.state.settings = QSettings(str(self.path / "settings.ini"), QSettings.Format.IniFormat)
        self.controller = MaterialController(self.state)
        self.view = MaterialView(self.state, controller=self.controller)
        self.addCleanup(self.cleanup_worker)

    def cleanup_worker(self):
        self.controller.timer.stop()
        self.controller.pool.waitForDone(10000)
        self.app.processEvents()
        self.controller.timer.stop()
        self.view.close()
        self.controller.deleteLater()
        self.app.processEvents()

    def wait_until(self, predicate):
        deadline = time.monotonic() + 8
        while not predicate() and time.monotonic() < deadline:
            QTest.qWait(15)
        self.assertTrue(predicate())

    def append(self, e):
        with (self.path / "1.log").open('a') as f:
            f.write(json.dumps(e)+'\n')
        self.state.changed.emit()

    def test_two_commanders_live_refresh_and_reader_reuse(self):
        self.wait_until(lambda: self.view.inventory.known)
        reader = self.controller.reader
        self.assertEqual(self.view.items["vanadium"].text(2), "40 / 250")
        self.append(event("MaterialCollected", 1, Name="vanadium", Category="Raw", Count=1))
        self.wait_until(lambda: self.view.inventory.material("vanadium").count == 41)
        self.assertEqual(self.view.items["vanadium"].text(0), "Vanadium +1")
        self.state.viewed_commander_id = 2
        self.state.viewedCommanderChanged.emit(2)
        self.assertFalse(self.view.inventory.known)
        self.wait_until(lambda: self.view.inventory.known and self.view.inventory.commander_id == 2)
        self.assertEqual(self.view.items["vanadium"].text(2), "200 / 250")
        self.assertFalse(self.view.highlight)
        self.append(event("MaterialCollected", 2, Name="vanadium", Category="Raw", Count=2))
        self.state.viewed_commander_id = 1
        self.state.viewedCommanderChanged.emit(1)
        self.wait_until(lambda: self.view.inventory.known and self.view.inventory.commander_id == 1)
        self.assertEqual(self.view.items["vanadium"].text(2), "43 / 250")
        self.assertIs(self.controller.reader, reader)
        self.assertFalse(self.view.highlight)

    def test_late_old_commander_result_is_discarded_and_gui_responsive(self):
        entered, release = threading.Event(), threading.Event()
        original = self.controller.reader.reconstruct
        def slow(*args):
            entered.set()
            release.wait(4)
            return original(*args)
        with patch.object(self.controller.reader, 'reconstruct', side_effect=slow):
            self.wait_until(entered.is_set)
            self.state.viewed_commander_id = 2
            self.state.viewedCommanderChanged.emit(2)
            seen = []
            self.controller.ready.connect(lambda inventory, _: seen.append(inventory.commander_id))
            tick = []
            QTimer.singleShot(10, lambda: tick.append(True))
            self.wait_until(lambda: bool(tick))
            self.assertFalse(self.view.inventory.known)
            release.set()
            self.wait_until(lambda: self.view.inventory.known)
            self.assertEqual(seen, [2])
            self.assertEqual(self.view.inventory.commander_id, 2)

    def test_all_supported_changes_refresh_automatically(self):
        self.wait_until(lambda: self.view.inventory.known)
        changes = [
            event("MaterialTrade", 1, Paid=dict(Material="vanadium", Category="Raw", Quantity=2), Received=dict(Material="tin", Category="Raw", Quantity=3)),
            event("EngineerCraft", 2, Ingredients=[dict(Name="vanadium", Count=1)]),
            event("Synthesis", 3, Materials=[dict(Name="vanadium", Count=1)]),
            event("MissionCompleted", 4, MaterialsReward=[dict(Name="dataminedwake", Category="Data", Count=3)]),
            event("EngineerContribution", 5, Type="Materials", Material="vanadium", Quantity=1),
            event("MaterialDiscarded", 6, Name="vanadium", Category="Raw", Count=1),
        ]
        for e in changes:
            self.append(e)
        self.wait_until(lambda: self.view.inventory.material("vanadium").count == 34)
        self.assertEqual(self.view.inventory.material("tin").count, 3)
        self.view.tabs.setCurrentIndex(2)
        self.assertEqual(self.view.items["dataminedwake"].text(2), "3 / 100")
        self.assertFalse(self.view.highlight)

    def test_database_error_publishes_unknown_without_previous_values(self):
        self.wait_until(lambda: self.view.inventory.known)
        self.state.database.path = self.path / "missing.db"
        with self.assertLogs('cmdrhelper.material_controller', level='ERROR'):
            self.state.changed.emit()
            self.wait_until(lambda: bool(self.view.inventory.issues))
        self.assertEqual(self.view.items["vanadium"].text(2), "? / 250")
