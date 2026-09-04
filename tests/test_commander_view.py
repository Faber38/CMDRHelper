from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.state import AppState
from cmdrhelper.ui.commander_view import CommanderView
from cmdrhelper.ui.main_window import MainWindow


class MemorySettings:
    def __init__(self):
        self.values = {}

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value


def make_state(database):
    state = AppState.__new__(AppState)
    QObject.__init__(state)
    state.database = database
    state.settings = MemorySettings()
    state.commander_id = None
    state.commander_fid = ""
    state.commander = ""
    state.viewed_commander_id = None
    state._viewed_commander_user_selected = False
    return state


class CommanderReadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.database = CMDRDatabase(Path(self.tmp.name) / "test.db")
        self.a = self.database.upsert_commander("FID-A", "Same", "2026-01-01T00:00:00Z")
        self.b = self.database.upsert_commander("FID-B", "Same", "2026-02-01T00:00:00Z")

        self.database.store_visit(1, "Alpha", "2026-03-01T00:00:00Z", commander_id=self.a)
        self.database.store_biology(1, 1, species="A Bio", commander_id=self.a)
        self.database.store_geology(1, 1, name="A Geo", commander_id=self.a)
        self.database.store_codex_entry(1, name="A Codex", commander_id=self.a)
        with self.database._connect() as con:
            con.execute(
                "INSERT INTO cartography_sales(commander_id,journal_file,event_timestamp,event_type) "
                "VALUES(?,?,?,?)",
                (self.a, "a.log", "T", "SellExplorationData"),
            )

        self.database.store_visit(2, "Bravo", "2026-04-01T00:00:00Z", commander_id=self.b)
        self.database.store_visit(3, "Bravo Two", "2026-05-01T00:00:00Z", commander_id=self.b)
        self.database.store_biology(2, 1, species="B Bio", commander_id=self.b)

    def tearDown(self):
        self.tmp.cleanup()

    def test_list_commanders_keeps_same_names_distinguishable(self):
        commanders = self.database.list_commanders()
        self.assertEqual([item["id"] for item in commanders], [self.a, self.b])
        self.assertEqual({item["fid"] for item in commanders}, {"FID-A", "FID-B"})
        self.assertEqual(
            {item["display_name"] for item in commanders},
            {"Same (FID-A)", "Same (FID-B)"},
        )

    def test_summaries_are_strictly_commander_scoped(self):
        summary_a = self.database.commander_summary(self.a)
        summary_b = self.database.commander_summary(self.b)
        self.assertEqual(summary_a["visited_systems"], 1)
        self.assertEqual(summary_a["biology_findings"], 1)
        self.assertEqual(summary_a["geology_findings"], 1)
        self.assertEqual(summary_a["codex_entries"], 1)
        self.assertEqual(summary_a["cartography_sales"], 1)
        self.assertEqual(summary_a["last_location"]["system_name"], "Alpha")
        self.assertEqual(summary_b["visited_systems"], 2)
        self.assertEqual(summary_b["biology_findings"], 1)
        self.assertEqual(summary_b["geology_findings"], 0)
        self.assertEqual(summary_b["codex_entries"], 0)
        self.assertEqual(summary_b["cartography_sales"], 0)
        self.assertEqual(summary_b["last_location"]["system_name"], "Bravo Two")

    def test_missing_summary_and_location_do_not_fall_back(self):
        empty = self.database.upsert_commander("FID-EMPTY", "Empty")
        self.assertIsNone(self.database.commander_summary(999999))
        summary = self.database.commander_summary(empty)
        self.assertIsNone(summary["last_location"])
        self.assertEqual(summary["visited_systems"], 0)


class CommanderSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.database = CMDRDatabase(Path(self.tmp.name) / "test.db")
        self.a = self.database.upsert_commander("FID-A", "Alpha")
        self.b = self.database.upsert_commander("FID-B", "Bravo")
        self.state = make_state(self.database)

    def tearDown(self):
        self.tmp.cleanup()

    def test_live_is_default_and_status_is_live(self):
        self.state.commander_id = self.a
        view = CommanderView(self.state)
        self.assertEqual(self.state.viewed_commander_id, self.a)
        self.assertEqual(view.commander_combo.currentData(), self.a)
        self.assertEqual(view.status_label.objectName(), "statusOk")
        self.assertEqual(view.tabs.count(), 5)

    def test_manual_view_does_not_change_live_or_follow_live_switch(self):
        self.state.commander_id = self.a
        view = CommanderView(self.state)
        self.state.select_viewed_commander(self.b)
        self.assertEqual(self.state.commander_id, self.a)
        self.assertEqual(self.state.viewed_commander_id, self.b)
        self.assertEqual(view.status_label.objectName(), "muted")

        self.state.commander_id = self.b
        self.state.commander_fid = "FID-B"
        self.state._apply_commander_identity({
            "commander_fid": "FID-A", "commander_identity_name": "Alpha"
        })
        self.assertEqual(self.state.commander_id, self.a)
        self.assertEqual(self.state.viewed_commander_id, self.b)
        self.assertEqual(view.status_label.objectName(), "muted")

    def test_unselected_view_follows_live_switch(self):
        self.state.commander_id = self.a
        view = CommanderView(self.state)
        self.state.commander_fid = "FID-A"
        self.state._apply_commander_identity({
            "commander_fid": "FID-B", "commander_identity_name": "Bravo"
        })
        self.assertEqual(self.state.commander_id, self.b)
        self.assertEqual(self.state.viewed_commander_id, self.b)
        self.assertEqual(view.status_label.objectName(), "statusOk")

    def test_missing_location_is_rendered_unknown(self):
        self.state.commander_id = self.a
        view = CommanderView(self.state)
        self.assertEqual(view.values["last_location"].text(), "–")

    def test_mercenary_credits_are_scoped_and_show_frontier_tooltip(self):
        self.database.store_commander_mercenary_credits(self.a, {
            "current": 1275, "total_earned": 25, "total_spent": 220,
            "spent_on_gear": 0, "spent_on_engineering": 220,
            "event_timestamp": "2026-09-04T11:25:39Z",
        })
        self.database.store_commander_mercenary_credits(self.b, {
            "current": 9, "event_timestamp": "2026-09-04T11:25:40Z",
        })
        self.state.commander_id = self.a
        view = CommanderView(self.state)
        self.assertEqual(view.mercenary_values["current"].text(), "1.275")
        self.assertEqual(view.mercenary_values["spent_on_gear"].text(), "0")
        self.assertTrue(view.mercenary_values["total_earned"].toolTip())
        self.state.select_viewed_commander(self.b)
        self.assertEqual(view.mercenary_values["current"].text(), "9")
        self.assertEqual(view.mercenary_values["total_spent"].text(), "–")

    def test_navigation_keeps_existing_pages_and_appends_commander_view(self):
        self.assertEqual(
            (
                MainWindow.PAGE_OVERVIEW, MainWindow.PAGE_MISSIONS,
                MainWindow.PAGE_EXPLORER, MainWindow.PAGE_CHRONICLE,
                MainWindow.PAGE_JUMP_TIP, MainWindow.PAGE_ROUTE_PLANNER,
                MainWindow.PAGE_IMAGES, MainWindow.PAGE_COMMANDER_VIEW,
                MainWindow.PAGE_SETTINGS,
            ),
            tuple(range(9)),
        )


if __name__ == "__main__":
    unittest.main()
