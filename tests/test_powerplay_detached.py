"""Reparent the real PP2 chronicle, using synthetic state and temporary settings."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from datetime import date, datetime, timedelta
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QSettings, Qt, QTime
from PySide6.QtWidgets import QApplication, QMainWindow
from cmdrhelper.powerplay import PowerplayState
from cmdrhelper.powerplay_chronicle import ChronicleGroup
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.powerplay_view import ChronicleTable, PowerplayView
from tests.test_powerplay import ViewState


DAY = date(2026, 10, 6)


class DetachedChronicleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.settings_path = str(Path(tmp.name) / 'ui.ini')
        self.state = ViewState()
        self.state.settings = QSettings(self.settings_path, QSettings.IniFormat)
        clock = patch('cmdrhelper.ui.powerplay_view.local_today', return_value=DAY)
        clock.start()
        self.addCleanup(clock.stop)
        self.main = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(self.main)
        self.view = PowerplayView(self.state, self.main)
        self.main.setCentralWidget(self.view)
        self.main.resize(1200, 900)
        self.main.show()
        self.app.processEvents()
        self.addCleanup(self.main.deleteLater)
        self.addCleanup(self.main.close)

    @staticmethod
    def group(hour, merit, name='Synthetic', day=DAY):
        stamp = datetime(day.year, day.month, day.day, hour, 0).astimezone().isoformat()
        return ChronicleGroup(dict(timestamp=stamp, event='PowerplayDeliver',
            Type_Localised=name, Count=merit), 'explicit', system='Synthetic',
            credits=[dict(timestamp=stamp, MeritsGained=merit, TotalMerits=1000)])

    def rows(self):
        return [tuple(self.view.recent.item(r, c).text() for c in range(5))
                for r in range(self.view.recent.rowCount())]

    def test_same_table_filters_order_and_data_survive_docking_and_close(self):
        self.state.powerplay.chronicle.groups = [self.group(10, 1), self.group(12, 2),
                                                self.group(13, 3)]
        self.view.from_time.setTime(QTime(12, 0))
        self.view.time_filter_enabled.setChecked(True)
        table, model = self.view.recent, self.view.recent.model()
        summary = self.view.filtered_merits
        summary_text = summary.text()
        self.assertTrue(summary_text.endswith('+5'))
        rows = self.rows()
        self.assertEqual([row[3] for row in rows], ['+3', '+2'])
        self.view.detach_chronicle_button.click()
        window = self.view.chronicle_window
        self.assertTrue(window.isVisible())
        self.assertTrue(window.isAncestorOf(summary))
        self.assertEqual(summary.text(), summary_text)
        self.assertIs(self.view.recent_section.parentWidget(), window)
        self.assertEqual(self.main.findChildren(ChronicleTable), [table])
        self.assertEqual(self.rows(), rows)
        self.assertFalse(table.wordWrap())
        self.assertEqual(table.textElideMode(), Qt.ElideRight)
        self.view.detach_chronicle_button.click()
        self.assertFalse(window.isVisible())
        self.assertIs(self.view.filtered_merits, summary)
        self.assertEqual(summary.text(), summary_text)
        self.assertIs(self.view.recent_section.parentWidget(), self.view.widget())
        self.assertIs(self.view.recent.model(), model)
        self.assertEqual(self.rows(), rows)
        self.view.detach_chronicle_button.click()
        window.close()
        self.assertFalse(self.view.chronicle_detached)
        self.assertTrue(self.view.recent.isVisible())
        self.assertTrue(self.view.time_filter_enabled.isChecked())
        self.assertEqual(self.view.from_time.time(), QTime(12, 0))
        self.view.detach_chronicle_button.click()
        self.assertIs(self.view.chronicle_window, window)
        self.assertEqual(self.rows(), rows)

    def test_selected_commander_updates_while_main_page_hidden(self):
        a, b = PowerplayState(), PowerplayState()
        previous = DAY - timedelta(days=1)
        a.chronicle.groups = [self.group(13, 11, 'Commander A', previous)]
        b.chronicle.groups = [self.group(10, 99, 'Too early', previous),
                              self.group(13, 22, 'Commander B', previous)]
        query = Mock(side_effect=lambda cid, day: {1: a, 2: b}[cid].chronicle)
        self.state.database = SimpleNamespace(powerplay_day=query)
        self.state.commander_id = 1
        self.view.selected_day = previous
        self.view.from_time.setTime(QTime(12, 0))
        self.view.time_filter_enabled.setChecked(True)
        self.view.detach_chronicle()
        self.assertTrue(self.view.filtered_merits.text().endswith('+11'))
        self.view.hide()
        self.assertTrue(self.view.timer.isActive())
        query.reset_mock()
        self.state.commander_id = 2
        self.state.powerplay = b
        with patch.object(self.view, 'render', wraps=self.view.render) as render:
            self.state.changed.emit()
            render.assert_called_once_with()
        query.assert_called_once_with(2, previous)
        self.assertEqual(len(self.rows()), 1)
        self.assertIn('Commander B', self.rows()[0][2])
        self.assertEqual(self.rows()[0][3:], ('+22', '✓'))
        self.assertTrue(self.view.filtered_merits.text().endswith('+22'))
        self.view.attach_chronicle()
        self.assertEqual(self.view.selected_day, previous)
        self.assertFalse(self.view.timer.isActive())

    def test_resizing_scrolling_and_geometry_across_new_settings_instance(self):
        self.state.powerplay.chronicle.groups = [self.group(12, n) for n in range(100)]
        self.view.detach_chronicle()
        window = self.view.chronicle_window
        window.resize(600, 450)
        window.move(40, 50)
        self.app.processEvents()
        small = self.view.recent.size()
        self.assertTrue(self.view.recent.verticalScrollBar().isVisible())
        window.resize(750, 650)
        self.app.processEvents()
        self.assertGreater(self.view.recent.width(), small.width())
        self.assertGreater(self.view.recent.height(), small.height())
        expected_size, expected_pos = window.size(), window.pos()
        self.view.attach_chronicle()
        self.state.settings = QSettings(self.settings_path, QSettings.IniFormat)
        self.assertIsNotNone(self.state.settings.value(self.view.chronicle_geometry_key))
        window.resize(800, 600)
        window.move(10, 10)
        self.view.detach_chronicle()
        self.app.processEvents()
        self.assertEqual(window.size(), expected_size)
        self.assertEqual(window.pos(), expected_pos)
        # Minimum usable column widths overflow a narrow viewport and scroll.
        self.view.recent.column_widths.minimums = [300] * 5
        self.view.recent.fit_columns()
        self.app.processEvents()
        self.assertGreater(self.view.recent.horizontalScrollBar().maximum(), 0)

    def test_auxiliary_flags_minimize_and_main_close(self):
        self.view.detach_chronicle()
        window = self.view.chronicle_window
        self.assertIs(window.parentWidget(), self.main)
        self.assertEqual(window.windowType(), Qt.Window)
        self.assertTrue(window.windowFlags() & Qt.WindowStaysOnTopHint)
        self.assertIsNone(window.windowHandle().transientParent())
        self.main.showMinimized()
        self.app.processEvents()
        self.assertTrue(window.isVisible())
        self.assertFalse(window.isMinimized())
        self.main.showNormal()
        window.showMinimized()
        self.app.processEvents()
        self.assertTrue(window.isMinimized())
        self.assertFalse(self.main.isMinimized())
        self.view.open_chronicle_button.click()
        self.assertFalse(window.isMinimized())
        self.main.close()
        self.assertFalse(window.isVisible())
        self.assertFalse(self.view.chronicle_detached)

    def test_main_close_exits_event_loop_with_detached_chronicle(self):
        code = '''
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QTimer
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.powerplay_view import PowerplayView
from tests.test_powerplay import ViewState
app = QApplication([])
main = MainWindow.__new__(MainWindow)
QMainWindow.__init__(main)
view = PowerplayView(ViewState(), main)
main.setCentralWidget(view)
main.show()
view.detach_chronicle()
QTimer.singleShot(50, main.close)
QTimer.singleShot(3000, lambda: app.exit(99))
result = app.exec()
assert not view.chronicle_window.isVisible()
assert not view.chronicle_detached
raise SystemExit(result)
'''
        result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
