from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QCheckBox, QHBoxLayout, QLabel, QWidget

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.ui.chronicle_view import ChronicleMapWidget, commander_color
from cmdrhelper.ui.main_window import MainWindow


def snapshot(address, name, x):
    return {
        "system_address": address,
        "system": name,
        "last_timestamp": f"2026-01-{address:02d}T00:00:00Z",
        "star_pos": [x, 0.0, float(address)],
        "system_body_count": 0,
        "system_bodies": [],
    }


class MultiCommanderChronicleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.database = CMDRDatabase(Path(self.tmp.name) / "test.db")
        self.a = self.database.upsert_commander("FID-A", "Alpha")
        self.b = self.database.upsert_commander("FID-B", "Bravo")
        for address, name, x in (
            (1, "A Start", 1.0), (2, "Shared", 2.0),
            (3, "A End", 3.0), (4, "B Start", 4.0), (5, "B End", 5.0),
        ):
            self.database.store_snapshot(snapshot(address, name, x))
        for address, timestamp in ((1, "T01"), (2, "T02"), (3, "T03")):
            self.database.store_visit(address, timestamp=timestamp, commander_id=self.a)
        for address, timestamp in ((4, "T01"), (2, "T02"), (5, "T03")):
            self.database.store_visit(address, timestamp=timestamp, commander_id=self.b)

    def tearDown(self):
        self.tmp.cleanup()

    def test_personal_visits_and_shared_system_are_aggregated_correctly(self):
        data = self.database.multi_commander_chronicle([self.a, self.b])
        systems = {item["system_address"]: item for item in data["systems"]}
        self.assertEqual(set(systems), {1, 2, 3, 4, 5})
        self.assertEqual(
            {item["commander_id"] for item in systems[2]["commanders"]},
            {self.a, self.b},
        )
        self.assertEqual(
            ChronicleMapWidget.marker_commander_ids(systems[2]),
            [self.a, self.b],
        )

    def test_routes_never_connect_different_commanders(self):
        data = self.database.multi_commander_chronicle([self.a, self.b])
        widget = ChronicleMapWidget()
        widget.set_systems(data["systems"], data["routes"])
        segments = [
            (commander_id, first["system_address"], second["system_address"])
            for commander_id, first, second in widget.route_segments()
        ]
        self.assertEqual(segments, [
            (self.a, 1, 2), (self.a, 2, 3),
            (self.b, 4, 2), (self.b, 2, 5),
        ])
        self.assertNotIn((self.a, 3, 4), segments)

    def test_database_filter_and_single_commander_remain_isolated(self):
        only_a = self.database.multi_commander_chronicle([self.a])
        only_b = self.database.multi_commander_chronicle([self.b])
        self.assertEqual(
            {item["system_address"] for item in only_a["systems"]}, {1, 2, 3}
        )
        self.assertEqual(
            {item["system_address"] for item in only_b["systems"]}, {2, 4, 5}
        )
        self.assertEqual([route["commander_id"] for route in only_a["routes"]], [self.a])
        self.assertEqual([route["commander_id"] for route in only_b["routes"]], [self.b])

    def test_filter_controls_support_each_none_and_all(self):
        host = QWidget()
        window = MainWindow.__new__(MainWindow)
        window.ui_theme = "dark"
        window.chronicle_filter_layout = QHBoxLayout(host)
        window.chronicle_filter_layout.addWidget(QLabel("filter"))
        window.chronicle_all_commanders = QCheckBox()
        window.chronicle_filter_layout.addWidget(window.chronicle_all_commanders)
        window.chronicle_filter_layout.addStretch()
        window.chronicle_commander_checks = {}
        window._chronicle_filter_ids = ()
        window._refresh_chronicle = lambda: None
        commanders = self.database.list_commanders()
        MainWindow._sync_chronicle_filters(window, commanders)

        window.chronicle_commander_checks[self.a].setChecked(False)
        self.assertEqual(MainWindow._selected_chronicle_commander_ids(window), [self.b])
        window.chronicle_commander_checks[self.a].setChecked(True)
        window.chronicle_commander_checks[self.b].setChecked(False)
        self.assertEqual(MainWindow._selected_chronicle_commander_ids(window), [self.a])
        MainWindow._toggle_all_chronicle_commanders(window, False)
        self.assertEqual(MainWindow._selected_chronicle_commander_ids(window), [])
        MainWindow._toggle_all_chronicle_commanders(window, True)
        self.assertEqual(
            MainWindow._selected_chronicle_commander_ids(window), [self.a, self.b]
        )

    def test_color_is_deterministic_and_orientation_is_unchanged(self):
        self.assertEqual(commander_color(self.a).rgba(), commander_color(self.a).rgba())
        self.assertNotEqual(commander_color(self.a).rgba(), commander_color(self.b).rgba())
        widget = ChronicleMapWidget()
        self.assertEqual(widget._display_pitch_offset, 3.141592653589793)
        self.assertAlmostEqual(widget.yaw, -0.4886921905584123)
        self.assertAlmostEqual(widget.pitch, 0.4188790204786391)


if __name__ == "__main__":
    unittest.main()
