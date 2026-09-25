"""Isolated value-list layout regressions; no database, journals or network."""
import cProfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication, QHeaderView
from cmdrhelper.i18n import get_language, set_language, tr
from cmdrhelper.ui.explorer_status import FOOTFALL_COLOR_ROLE
from cmdrhelper.ui.explorer_value_sort import apply_sort
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from test_explorer_table_ux import ExplorerWindow


class ExplorerValueLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(set_language, get_language())
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        set_language('de')
        self.window = ExplorerWindow(QSettings(str(Path(self.tmp.name) / 'ui.ini'), QSettings.IniFormat))
        self.addCleanup(self.window.deleteLater)
        self.addCleanup(self.window.close)
        self.window.resize(1100, 850)
        self.window.show()
        self.window.explorer_tabs.setCurrentIndex(1)
        self.table = self.window.explorer_value_table
        self.settle()

    def settle(self):
        for _ in range(5):
            self.app.processEvents()

    @staticmethod
    def bodies(count):
        return [dict(body_id=i, name=f'Example {i}', short_name=str(i), body_type='Planet',
                     planet_class='Rocky body', journal_scanned=True, source='Journal',
                     first_footfall=i % 2 == 0, self_mapped=i % 2 == 0, was_mapped=False,
                     possible_value=1000, scan_value=1000, current_value=1000,
                     biology=[], biological_signals=1, geological_signals=2,
                     planetary_mining_signals=3) for i in range(1, count + 1)]

    def refresh(self, bodies):
        self.window.state.system_bodies = bodies
        self.window._refresh_explorer_tables(tab=1)
        self.settle()

    def test_empty_single_and_large_tables_have_bounded_size_hint_work(self):
        for fit in (False, True):
            self.window.explorer_value_fit_check.setChecked(fit)
            for count in (0, 1, 10, 50, 100, 200):
                with self.subTest(fit=fit, count=count):
                    bodies = self.bodies(count)
                    self.refresh(bodies)
                    profile = cProfile.Profile()
                    profile.enable()
                    self.refresh(bodies)
                    profile.disable()
                    hints = sum(entry.callcount for entry in profile.getstats()
                                if getattr(entry.code, 'co_name', '') == 'sizeHint'
                                and entry.code.co_filename.endswith('/ui/explorer_status.py'))
                    self.assertEqual(self.table.rowCount(), count)
                    # A few final/viewport layout passes are fine; per-cell full
                    # table measurement (roughly 8*N*N) must not return.
                    self.assertLessEqual(hints, 12 * count + 12)
                    if count:
                        self.assertEqual(self.table.verticalHeader().sectionResizeMode(0),
                                         QHeaderView.ResizeToContents)

    def test_multiline_long_text_theme_font_and_width_fit_matrix(self):
        bodies = self.bodies(3)
        bodies[1]['name'] = 'A very long synthetic system and planet name ' * 3
        bodies[1]['short_name'] = bodies[1]['name']
        for light, theme in ((False, DARK_STYLESHEET), (True, LIGHT_STYLESHEET)):
            self.window.ui_theme = 'light' if light else 'dark'
            for points in (10, 18, 24):
                self.app.setStyleSheet(theme + '\nQWidget { font-size: ' + str(points) + 'pt; }')
                for fit in (False, True):
                    self.window.explorer_value_fit_check.setChecked(fit)
                    for width in (500, 1600):
                        with self.subTest(light=light, points=points, fit=fit, width=width):
                            self.window.resize(width, 850)
                            if not fit:
                                self.table.setColumnWidth(0, 140)
                                self.table.setColumnWidth(6, 120)
                                self.table.setColumnWidth(7, 210)
                            self.refresh(bodies)
                            self.assertEqual(self.table.font().pointSize(), points)
                            row = next(r for r in range(3) if self.table.item(r, 0).data(Qt.UserRole)['body_id'] == 2)
                            status = self.table.item(row, 7)
                            self.assertEqual(status.text(), tr('explorer.first_footfall') + '\n' +
                                             tr('explorer.mapping_status_self'))
                            self.assertTrue(status.data(FOOTFALL_COLOR_ROLE))
                            self.assertIn(tr('explorer.first_footfall_tip'), status.toolTip())
                            self.assertGreaterEqual(self.table.rowHeight(row),
                                                    self.table.fontMetrics().lineSpacing() * 2 + 8)
                            for r in range(3):
                                self.assertGreaterEqual(self.table.rowHeight(r), self.table.sizeHintForRow(r))
                            self.assertTrue(self.table.item(row, 6).toolTip())
                            self.assertTrue(self.table.wordWrap())

    def test_one_sort_after_population_and_preserved_roles(self):
        self.table._value_sort = (0, Qt.AscendingOrder)
        calls = []
        def sort(table):
            calls.append(table.rowCount())
            self.assertEqual(table.verticalHeader().sectionResizeMode(0), QHeaderView.Fixed)
            apply_sort(table)
        with patch('cmdrhelper.ui.main_window.apply_sort', side_effect=sort):
            self.refresh(list(reversed(self.bodies(12))))
        self.assertEqual(calls, [12])
        self.assertEqual([self.table.item(r, 0).data(Qt.UserRole)['body_id'] for r in range(12)],
                         list(range(1, 13)))
        before = [[(self.table.item(r, c).text(), self.table.item(r, c).toolTip(),
                    self.table.item(r, c).foreground().color().name())
                   for c in range(8)] for r in range(12)]
        self.window.resize(1500, 850)
        self.settle()
        after = [[(self.table.item(r, c).text(), self.table.item(r, c).toolTip(),
                   self.table.item(r, c).foreground().color().name())
                  for c in range(8)] for r in range(12)]
        self.assertEqual(before, after)

    def test_resize_burst_remains_coalesced(self):
        self.refresh(self.bodies(100))
        fit = self.window._explorer_value_width_fit
        with patch.object(fit, 'apply', wraps=fit.apply) as apply:
            for i in range(100):
                self.window.resize(1100 + i % 2 * 20, 850)
            self.settle()
            self.assertEqual(apply.call_count, 1)
            self.assertFalse(fit.pending)

    def test_resize_mode_restored_after_population_error(self):
        self.refresh(self.bodies(1))
        with patch('cmdrhelper.ui.main_window.ValueItem', side_effect=RuntimeError('synthetic')):
            with self.assertRaises(RuntimeError):
                self.window._refresh_explorer_tables(tab=1)
        self.assertEqual(self.table.verticalHeader().sectionResizeMode(0), QHeaderView.ResizeToContents)
        self.refresh(self.bodies(2))
        self.assertEqual(self.table.rowCount(), 2)
