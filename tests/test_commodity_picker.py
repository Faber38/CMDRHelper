"""Offline selection, rendering, keyboard and performance checks for all 412 goods."""
import time
import unittest
from unittest.mock import patch

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QFont
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QPushButton, QWidget

from cmdrhelper.commodity_master import all_commodities, lookup_by_id, lookup_by_symbol
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.ui.commodity_picker import (
    CHOSEN_ROLE, COMMODITY_ID_ROLE, CommodityField, CommodityPicker,
    CommodityTileDelegate, commodity_name, text_layout,
)
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class CommodityPickerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.language = get_language()
        self.style = self.app.styleSheet()
        self.font = self.app.font()
        set_language('de')
        self.app.setStyleSheet(DARK_STYLESHEET)
        self.field = CommodityField()
        self.field.resize(400, 45)
        self.field.show()
        self.addCleanup(self.cleanup)
        self.platinum = lookup_by_symbol('platinum')

    def cleanup(self):
        if self.field._picker:
            self.field._picker.reject()
        self.field.close()
        self.field.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.setStyleSheet(self.style)
        self.app.setFont(self.font)
        set_language(self.language)

    def open(self):
        self.field.click()
        self.app.processEvents()
        return self.field._picker

    def test_single_field_opens_search_focused_dialog_with_all_master_ids(self):
        with patch('cmdrhelper.spansh_market.SpanshMarketProvider.search_sell', side_effect=AssertionError('network')):
            picker = self.open()
        self.assertTrue(picker.isVisible())
        self.assertTrue(picker.search.hasFocus())
        self.assertEqual(picker.model.rowCount(), 412)
        self.assertEqual({picker.model.index(i).data(COMMODITY_ID_ROLE) for i in range(412)},
                         {c.frontier_id for c in all_commodities()})
        self.assertLess(len(picker.findChildren(QPushButton)), 5)
        self.assertLess(len(picker.findChildren(QWidget)), 30)

    def test_desktop_grid_is_multicolumn_and_small_window_reduces_columns(self):
        picker = self.open()
        picker.resize(1100, 700)
        self.app.processEvents()
        self.assertIn(picker.grid.columns, (4, 5, 6))
        first = picker.grid.visualRect(picker.model.index(0))
        second = picker.grid.visualRect(picker.model.index(1))
        self.assertEqual(first.top(), second.top())
        self.assertGreater(second.left(), first.left())
        self.assertTrue(picker.grid.verticalScrollBar().maximum() > 0)
        self.assertEqual(picker.grid.horizontalScrollBar().maximum(), 0)
        before = picker.grid.columns
        picker.resize(360, 450)
        self.app.processEvents()
        self.assertLess(picker.grid.columns, before)
        self.assertEqual(picker.grid.horizontalScrollBar().maximum(), 0)

    def test_initial_window_fits_available_screen(self):
        picker = self.open()
        available = picker.screen().availableGeometry()
        self.assertTrue(available.contains(picker.frameGeometry()))
        self.assertGreaterEqual(picker.width(), min(700, available.width()-32))

    def test_search_visible_name_english_symbol_trim_and_casefold(self):
        picker = self.open()
        crystal = lookup_by_symbol('methanolmonohydratecrystals')
        for item, text in ((self.platinum, '  pLaTiN  '), (self.platinum, 'PLATINUM'),
                           (crystal, commodity_name(crystal)), (crystal, crystal.english_name),
                           (crystal, crystal.symbol.upper())):
            picker.search.setText(text)
            self.assertTrue(picker.model.index_for_id(item.frontier_id).isValid(), text)
        picker.search.clear()
        self.assertEqual(picker.model.rowCount(), 412)

    def test_no_aggressive_normalization_and_clear_no_matches_message(self):
        picker = self.open()
        for query in ('nonexistent commodity', '$platinum_name;'):
            picker.search.setText(query)
            self.assertEqual(picker.model.rowCount(), 0)
            self.assertTrue(picker.empty.isVisible())
            self.assertEqual(picker.empty.text(), 'Keine passende Ware gefunden.')
        picker.search.clear()
        self.assertFalse(picker.empty.isVisible())
        self.assertTrue(picker.grid.isVisible())
        self.assertEqual(picker.model.rowCount(), 412)

    def test_german_english_and_symbol_search_resolve_same_identity(self):
        picker = self.open()
        for symbol, queries in (('Beer', ('Bier', 'Beer', '  BEER  ')),
                                ('Platinum', ('Platin', 'Platinum')),
                                ('Praseodymium', ('Praseodym', 'Praseodymium')),
                                ('PericlaseDunite', ('Periklas-Dunit', 'Periclase Dunite', 'PericlaseDunite'))):
            item = lookup_by_symbol(symbol)
            for query in queries:
                picker.search.setText(query)
                index = picker.model.index_for_id(item.frontier_id)
                self.assertTrue(index.isValid(), query)
                self.assertEqual(index.data(COMMODITY_ID_ROLE), item.frontier_id)

    def test_click_commits_exact_id_and_closes_dialog(self):
        picker = self.open()
        picker.search.setText('platinum')
        self.app.processEvents()
        index = picker.model.index_for_id(self.platinum.frontier_id)
        QTest.mouseClick(picker.grid.viewport(), Qt.MouseButton.LeftButton,
                         pos=picker.grid.visualRect(index).center())
        self.assertIsNone(self.field._picker)
        self.assertEqual(self.field.currentData(), self.platinum.frontier_id)
        self.assertIn('Platin', self.field.text())
        self.assertEqual(lookup_by_id(self.field.currentData()).symbol, self.platinum.symbol)

    def test_escape_preserves_no_selection(self):
        picker = self.open()
        picker.search.setText('platinum')
        QTest.keyClick(picker.search, Qt.Key.Key_Escape)
        self.assertIsNone(self.field.currentData())
        self.assertIsNone(self.field._picker)

    def test_cancel_button_preserves_previous_selection_after_navigation(self):
        self.field.set_commodity(self.platinum.frontier_id)
        picker = self.open()
        self.assertTrue(picker.model.index_for_id(self.platinum.frontier_id).data(CHOSEN_ROLE))
        picker.search.setText('gold')
        picker.grid.setFocus()
        picker.grid.setCurrentIndex(picker.model.index(0))
        picker.buttons.buttons()[0].click()
        self.assertEqual(self.field.currentData(), self.platinum.frontier_id)
        self.assertIsNone(self.field._picker)

    def test_escape_from_grid_preserves_previous_selection(self):
        self.field.set_commodity(self.platinum.frontier_id)
        picker = self.open()
        picker.search.setText('gold')
        picker.grid.setFocus()
        QTest.keyClick(picker.grid, Qt.Key.Key_Escape)
        self.assertEqual(self.field.currentData(), self.platinum.frontier_id)
        self.assertIsNone(self.field._picker)

    def test_tab_arrow_enter_choose_focused_tile(self):
        picker = self.open()
        QTest.keyClick(picker.search, Qt.Key.Key_Tab)
        self.assertTrue(picker.grid.hasFocus())
        before = picker.grid.currentIndex()
        QTest.keyClick(picker.grid, Qt.Key.Key_Right)
        after = picker.grid.currentIndex()
        self.assertNotEqual(before.row(), after.row())
        expected = after.data(COMMODITY_ID_ROLE)
        QTest.keyClick(picker.grid, Qt.Key.Key_Return)
        self.assertEqual(self.field.currentData(), expected)
        self.assertIsNone(self.field._picker)

    def test_tab_reaches_cancel_and_shift_tab_returns_to_search(self):
        picker = self.open()
        QTest.keyClick(picker.search, Qt.Key.Key_Tab)
        QTest.keyClick(picker.grid, Qt.Key.Key_Tab)
        cancel = picker.buttons.buttons()[0]
        self.assertTrue(cancel.hasFocus())
        QTest.keyClick(cancel, Qt.Key.Key_Backtab)
        self.assertTrue(picker.grid.hasFocus())
        QTest.keyClick(picker.grid, Qt.Key.Key_Backtab)
        self.assertTrue(picker.search.hasFocus())

    def test_opening_twice_reuses_dialog_and_reopening_resets_filter(self):
        picker = self.open()
        self.field.open_picker()
        self.assertIs(self.field._picker, picker)
        picker.search.setText('gold')
        picker.reject()
        picker = self.open()
        self.assertEqual(picker.search.text(), '')
        self.assertEqual(picker.model.rowCount(), 412)

    def test_unknown_id_cannot_replace_existing_identity(self):
        self.field.set_commodity(self.platinum.frontier_id)
        self.assertFalse(self.field.set_commodity(999999999))
        self.assertEqual(self.field.currentData(), self.platinum.frontier_id)

    def test_performance_open_and_filter_all_412_without_tile_widgets(self):
        started = time.perf_counter()
        picker = self.open()
        opening = time.perf_counter()-started
        timings = []
        for query in ('plat', 'PLATINUM', 'gold', '', 'methanol', 'unobtainium', ''):
            started = time.perf_counter()
            picker.search.setText(query)
            self.app.processEvents()
            timings.append(time.perf_counter()-started)
        # Generous CI limits detect accidental widget-per-commodity or blocking IO.
        self.assertLess(opening, 1.0)
        self.assertLess(max(timings), .5)
        self.assertLess(len(picker.findChildren(QWidget)), 30)
        print(f'PICKER PERFORMANCE: open={opening*1000:.1f} ms; worst filter={max(timings)*1000:.1f} ms')

    def test_twelve_languages_both_themes_large_fonts_and_unclipped_names(self):
        for language in _TRANSLATIONS:
            set_language(language)
            self.assertIn('trade.no_commodity_matches', _TRANSLATIONS[language])
            for stylesheet in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                for size in (10, 18):
                    with self.subTest(language=language, light=stylesheet==LIGHT_STYLESHEET, size=size):
                        self.app.setFont(QFont(self.font.family(), size))
                        self.app.setStyleSheet(stylesheet + f'\nQWidget {{font-size: {size}pt;}}')
                        picker = CommodityPicker(self.platinum.frontier_id, self.field)
                        picker.resize(1000, 700)
                        picker.show()
                        self.app.processEvents()
                        grid = picker.grid
                        first_top = grid.visualRect(picker.model.index(0)).top()
                        first_row_count = sum(grid.visualRect(picker.model.index(i)).top() == first_top
                                              for i in range(6))
                        self.assertEqual(first_row_count, grid.columns)
                        inset = 2 * (CommodityTileDelegate.MARGIN + CommodityTileDelegate.PADDING)
                        for row in range(412):
                            index = picker.model.index(row)
                            _text, height = text_layout(index.data(), grid.font(), grid.gridSize().width()-inset)
                            self.assertLessEqual(height, grid.gridSize().height()-inset)
                            rect = grid.visualRect(index)
                            self.assertGreaterEqual(rect.left(), 0)
                            self.assertLessEqual(rect.right(), grid.viewport().width())
                        self.assertEqual(grid.horizontalScrollBar().maximum(), 0)
                        chosen = picker.model.index_for_id(self.platinum.frontier_id)
                        self.assertTrue(chosen.data(CHOSEN_ROLE))
                        self.assertFalse(picker.grab().isNull())
                        picker.reject()
                        picker.deleteLater()
                        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)


if __name__ == '__main__':
    unittest.main()
