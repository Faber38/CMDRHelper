"""Window-width fitting uses temporary settings and synthetic Explorer bodies."""
import os
import tempfile
import unittest
from importlib import import_module
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.ui.explorer_width_fit import SETTING_KEY
from cmdrhelper.ui.explorer_status import FOOTFALL_COLOR_ROLE
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests.test_explorer_table_ux import ExplorerWindow


class ExplorerWidthFitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / 'preferences.ini')
        self.addCleanup(set_language, get_language())
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        set_language('de')

    def settle(self):
        for _ in range(5):
            self.app.processEvents()

    def window(self, width=1600, theme='dark'):
        w = ExplorerWindow(QSettings(self.path, QSettings.IniFormat), theme)
        self.addCleanup(w.deleteLater)
        self.addCleanup(w.close)
        w.resize(width, 700)
        w.show()
        w.explorer_tabs.setCurrentIndex(1)
        w.state.system_bodies = [dict(body_id=i, name=f'Example {i}', body_type='Planet',
            planet_class='Rocky body', journal_scanned=True, first_footfall=True,
            was_mapped=False, self_mapped=i == 1) for i in (2, 1)]
        w._refresh_explorer_tables(tab=1)
        self.settle()
        return w

    @staticmethod
    def widths(w):
        return [w.explorer_value_table.columnWidth(i) for i in range(8)]

    def assert_fit(self, w):
        table = w.explorer_value_table
        widths = self.widths(w)
        minima = w._explorer_value_width_fit.minimum_widths()
        self.assertTrue(all(width >= minimum for width, minimum in zip(widths, minima)))
        self.assertEqual(sum(widths), max(table.viewport().width(), sum(minima)))
        self.assertGreater(widths[7], widths[0])
        self.assertGreater(widths[5], widths[3])
        self.assertEqual(table.horizontalScrollBar().maximum() > 0, sum(minima) > table.viewport().width())

    def test_default_and_persistence_both_directions(self):
        w = self.window()
        self.assertTrue(w.explorer_value_fit_check.isChecked())
        self.assertEqual(w.explorer_value_fit_check.text(), 'An Fensterbreite anpassen')
        w.explorer_value_fit_check.setChecked(False)
        second = self.window()
        self.assertFalse(second.explorer_value_fit_check.isChecked())
        second.explorer_value_fit_check.setChecked(True)
        third = self.window()
        self.assertTrue(third.explorer_value_fit_check.isChecked())
        self.assertEqual(QSettings(self.path, QSettings.IniFormat).value(SETTING_KEY, type=bool), True)

    def test_resize_widths_and_minima(self):
        w = self.window()
        before = self.widths(w)
        self.assert_fit(w)
        for width in (2100, 1200, 600, 1800):
            w.resize(width, 700)
            self.settle()
            self.assert_fit(w)
        self.assertNotEqual(before, self.widths(w))

    def test_toggle_off_freezes_and_manual_resize_survives(self):
        w = self.window()
        before = self.widths(w)
        w.explorer_value_fit_check.setChecked(False)
        self.settle()
        self.assertEqual(before, self.widths(w))
        w.resize(2100, 700)
        self.settle()
        self.assertEqual(before, self.widths(w))
        w.explorer_value_table.setColumnWidth(2, 220)
        manual = self.widths(w)
        w.resize(1500, 700)
        self.settle()
        self.assertEqual(manual, self.widths(w))
        w.explorer_value_fit_check.setChecked(True)
        # Apply synchronously when enabled, before processing deferred events.
        self.assertNotEqual(manual, self.widths(w))
        self.settle()
        self.assert_fit(w)

    def test_tab_change_data_refresh_and_sort_unchanged(self):
        w = self.window()
        t = w.explorer_value_table
        t.horizontalHeader().sectionClicked.emit(0)
        t.horizontalHeader().sectionClicked.emit(0)
        original_order = [t.item(r, 0).text() for r in range(t.rowCount())]
        original_sort = t._value_sort
        w.explorer_tabs.setCurrentIndex(2)
        w.resize(2100, 700)
        self.settle()
        w.explorer_tabs.setCurrentIndex(1)
        self.settle()
        self.assert_fit(w)
        widths = self.widths(w)
        w._refresh_explorer_tables(tab=1)
        self.settle()
        self.assertEqual(widths, self.widths(w))
        self.assertEqual(t._value_sort, original_sort)
        self.assertEqual([t.item(r, 0).text() for r in range(t.rowCount())], original_order)
        self.assertEqual(t.horizontalHeader().sortIndicatorOrder(), Qt.DescendingOrder)
        self.assertEqual(t.horizontalHeader().sortIndicatorSection(), 0)

    def test_dark_light_fonts_and_full_status_tooltips(self):
        for theme, style in [('dark', DARK_STYLESHEET), ('light', LIGHT_STYLESHEET)]:
            self.app.setStyleSheet(style)
            w = self.window(theme=theme)
            for pt in (10, 18, 24):
                with self.subTest(theme=theme, pt=pt):
                    font = QFont(w.explorer_value_table.font())
                    font.setPointSize(pt)
                    w.explorer_value_table.setFont(font)
                    w.resize(900 if pt == 24 else 1700, 700)
                    self.settle()
                    self.assert_fit(w)
                    self.assertEqual(w.explorer_value_table.font().pointSize(), pt)
                    if pt == 24:
                        self.assertGreater(w.explorer_value_table.horizontalScrollBar().maximum(), 0)
                    items = [w.explorer_value_table.item(r, 7) for r in range(2)]
                    item = next(i for i in items if i.data(Qt.UserRole)['self_mapped'])
                    self.assertEqual(item.text(), 'ERSTBETRETUNG\nSELBST KARTIERT')
                    self.assertEqual(item.data(FOOTFALL_COLOR_ROLE), '#856000' if theme == 'light' else '#ffb000')
                    self.assertEqual(item.foreground().color().name(), '#17679b' if theme == 'light' else '#68c7ff')
                    self.assertIn(tr('explorer.first_footfall_tip'), item.toolTip())
                    self.assertIn(tr('explorer.mapping_status_self_tip'), item.toolTip())
                    self.assertIn(tr('exploration.historical_notice'), w.explorer_value_table.item(0, 6).toolTip())

    def test_all_languages_checkbox_tooltip_and_help(self):
        for lang in 'de en el es fi fr it nl no pl sv tr'.split():
            with self.subTest(lang=lang):
                set_language(lang)
                w = self.window()
                self.assertEqual(w.explorer_value_fit_check.text(), _TRANSLATIONS[lang]['explorer.value_fit_width'])
                self.assertEqual(w.explorer_value_fit_check.toolTip(), _TRANSLATIONS[lang]['explorer.value_fit_width_tip'])
                if lang != 'en':
                    self.assertNotEqual(w.explorer_value_fit_check.text(), 'Fit to window width')
                help_text = import_module('cmdrhelper.help_content.' + lang).HELP_TOPICS['explorer'][1]
                self.assertIn(w.explorer_value_fit_check.text(), help_text)
                self.assert_fit(w)

    def test_automatic_changes_do_not_overwrite_manual_widths_or_overview_setting(self):
        settings = QSettings(self.path, QSettings.IniFormat)
        manual = [130, 220, 120, 130, 160, 230, 170, 200]
        settings.setValue('explorer/value_column_widths', manual)
        settings.setValue('system_overview/auto_fit', False)
        settings.sync()
        w = self.window()
        w.resize(2000, 700)
        self.settle()
        self.assertEqual(w.state.settings.value('explorer/value_column_widths'), manual)
        self.assertFalse(w.state.settings.value('system_overview/auto_fit', type=bool))
        self.assertEqual(set(w.state.settings.allKeys()), {'explorer/value_column_widths', 'system_overview/auto_fit'})

    def test_no_per_cell_adjustments_or_recurring_resize_loop(self):
        w = self.window()
        controller = w._explorer_value_width_fit
        with patch.object(controller, 'apply', wraps=controller.apply) as apply:
            w.resize(1850, 700)
            self.settle()
            self.assertGreater(apply.call_count, 0)
            self.assertLess(apply.call_count, 5)
            calls = apply.call_count
            self.settle()
            self.assertEqual(apply.call_count, calls)
            w._refresh_explorer_tables(tab=1)
            self.settle()
            self.assertEqual(apply.call_count, calls)
