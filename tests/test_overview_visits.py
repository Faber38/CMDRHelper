"""The existing overview renders persisted stays, including true returns."""
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication, QSpinBox, QTableWidget

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.ui.main_window import MainWindow


class OverviewVisitsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_overview_shows_returns_in_time_order_with_existing_limit(self):
        with tempfile.TemporaryDirectory() as folder:
            db = CMDRDatabase(Path(folder) / "test.db")
            commander = db.upsert_commander("FID-A", "Alpha")
            db.active_commander_id = commander
            for minute, address in enumerate([1, 1, 2, 1]):
                db.apply_commander_journal_delta(commander, "journal", [{
                    "event": "Location", "SystemAddress": address,
                    "StarSystem": f"System {address}",
                    "timestamp": f"2026-09-07T12:{minute:02d}:00Z",
                }], minute + 1)
            table = QTableWidget(0, 2)
            spin = QSpinBox()
            spin.setValue(10)
            view = SimpleNamespace(state=SimpleNamespace(database=db),
                                   recent_systems_table=table,
                                   recent_systems_count_spin=spin,
                                   _format_timestamp=lambda value: value)
            MainWindow._refresh_recent_systems(view)
            self.assertEqual(table.rowCount(), 3)
            self.assertEqual([table.item(i, 1).text() for i in range(3)],
                             ["System 1", "System 2", "System 1"])
            self.assertEqual([table.item(i, 0).text() for i in range(3)],
                             [f"2026-09-07T12:{minute:02d}:00Z" for minute in [3, 2, 0]])
            spin.setValue(2)
            MainWindow._refresh_recent_systems(view)
            self.assertEqual(table.rowCount(), 2)
