import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtCore import QSettings, Qt, QPoint, QByteArray
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMainWindow, QHeaderView, QTableWidget
from cmdrhelper.ui.main_window import MainWindow


KEY = 'overview/recent_systems_column_widths'


class OverviewWindow(MainWindow):
    def __init__(self, settings):
        QMainWindow.__init__(self)
        self.state = SimpleNamespace(settings=settings, database=SimpleNamespace(
            recent_system_visits=lambda limit: [dict(visited_at='2026-09-08T10:00:00Z', system_name='Sol')]))
        self.setCentralWidget(self._overview())


class OverviewColumnWidthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / 'ui.ini')
        self.settings = QSettings(self.path, QSettings.Format.IniFormat)
        self.window = self.make_window(self.settings)

    def make_window(self, settings):
        window = OverviewWindow(settings)
        window.resize(900, 800)
        window.show()
        self.app.processEvents()
        self.addCleanup(window.close)
        return window

    def widths(self, window=None):
        table = (window or self.window).recent_systems_table
        return [table.columnWidth(i) for i in range(2)]

    def drag(self, column=0, amount=70):
        header = self.window.recent_systems_table.horizontalHeader()
        point = QPoint(header.sectionViewportPosition(column) + header.sectionSize(column) - 1, header.height() // 2)
        QTest.mousePress(header.viewport(), Qt.MouseButton.LeftButton, pos=point)
        QTest.mouseMove(header.viewport(), point + QPoint(amount, 0), 30)
        QTest.mouseRelease(header.viewport(), Qt.MouseButton.LeftButton, pos=point + QPoint(amount, 0))
        self.app.processEvents()

    def test_existing_defaults_until_user_resize(self):
        table = self.window.recent_systems_table
        self.assertEqual(len(self.window.centralWidget().findChildren(QTableWidget)), 1)
        self.assertEqual(self.widths()[0], 150)
        self.assertTrue(table.horizontalHeader().stretchLastSection())
        for width in (700, 1100):
            self.window.resize(width, 800)
            self.window._refresh_recent_systems()
            self.app.processEvents()
            self.assertEqual(self.widths()[0], 150)
            self.assertGreater(self.widths()[1], 40)
            self.assertIsNone(self.settings.value(KEY))

    def test_mouse_resize_is_saved_and_freezes_stretch(self):
        self.drag()
        self.assertGreater(self.widths()[0], 150)
        self.assertEqual(self.settings.value(KEY), self.widths())
        header = self.window.recent_systems_table.horizontalHeader()
        self.assertFalse(header.stretchLastSection())
        self.assertFalse(header.sectionsMovable())
        self.assertTrue(all(header.sectionResizeMode(i) == QHeaderView.ResizeMode.Interactive for i in range(2)))

    def test_first_drag_can_shrink_the_previously_stretched_system_column(self):
        before = self.widths()[1]
        self.drag(column=1, amount=-80)
        self.assertLess(self.widths()[1], before)
        self.assertEqual(self.settings.value(KEY), self.widths())
        self.assertFalse(self.window.recent_systems_table.horizontalHeader().stretchLastSection())

    def test_click_without_resize_preserves_unsaved_defaults(self):
        self.drag(amount=0)
        self.assertIsNone(self.settings.value(KEY))
        self.assertTrue(self.window.recent_systems_table.horizontalHeader().stretchLastSection())

    def test_reopening_and_restart_restore_both_widths(self):
        self.drag()
        self.window.recent_systems_table.setColumnWidth(1, 385)
        expected = self.widths()
        self.window.hide()
        self.window.show()
        self.assertEqual(self.widths(), expected)
        reopened = self.make_window(self.settings)
        restarted = self.make_window(QSettings(self.path, QSettings.Format.IniFormat))
        self.assertEqual(self.widths(reopened), expected)
        self.assertEqual(self.widths(restarted), expected)
        self.assertFalse(restarted.recent_systems_table.horizontalHeader().stretchLastSection())

    def test_refresh_and_window_resize_do_not_replace_user_widths_or_data(self):
        self.drag()
        expected = self.widths()
        for width in (600, 1200):
            self.window.resize(width, 800)
            self.window._refresh_recent_systems()
            self.app.processEvents()
            self.assertEqual(self.widths(), expected)
            self.assertEqual(self.settings.value(KEY), expected)
            self.assertEqual(self.window.recent_systems_table.item(0, 1).text(), 'Sol')

    def test_invalid_or_obsolete_values_use_visible_defaults(self):
        for saved in ([0, 200], [-1, 200], [10000, 200], [True, 200], [150.5, 200],
                      [150], [150, 200, 300], ['bad', 200], 'broken', QByteArray(b'broken')):
            with self.subTest(saved=saved):
                self.settings.setValue(KEY, saved)
                self.settings.sync()
                window = self.make_window(QSettings(self.path, QSettings.Format.IniFormat))
                self.assertEqual(self.widths(window)[0], 150)
                self.assertTrue(window.recent_systems_table.horizontalHeader().stretchLastSection())
                self.assertTrue(all(w >= 40 for w in self.widths(window)))
                self.assertTrue(all(not window.recent_systems_table.isColumnHidden(i) for i in range(2)))
                window.close()

    def test_overview_has_its_own_settings_key(self):
        self.settings.setValue('materials/columns', dict(widths=[320, 80, 160, 160]))
        self.settings.setValue('explorer/bio_geo_mining_column_widths', [100] * 11)
        self.drag()
        self.assertEqual(self.settings.value('materials/columns'), dict(widths=[320, 80, 160, 160]))
        self.assertEqual(self.settings.value('explorer/bio_geo_mining_column_widths'), [100] * 11)
