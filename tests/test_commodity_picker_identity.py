"""Real viewport events: mouse focus must never move a tile before hit testing."""
import unittest

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QFont
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from cmdrhelper.commodity_master import all_commodities, lookup_by_id, lookup_by_symbol
from cmdrhelper.i18n import get_language, set_language
from cmdrhelper.ui.commodity_picker import COMMODITY_ID_ROLE, commodity_name
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.ui.trade_view import TradeView
from test_trade_view import State, Provider


class PickerIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.language, self.style, self.font = get_language(), self.app.styleSheet(), self.app.font()
        set_language('de')
        self.app.setStyleSheet(DARK_STYLESHEET)
        self.state, self.provider = State(), Provider()
        self.view = TradeView(self.state, provider=self.provider)
        self.view.resize(1000, 850)
        self.view.show()
        self.addCleanup(self.cleanup)

    def cleanup(self):
        if self.view.commodity._picker:
            self.view.commodity._picker.reject()
        self.view.close()
        self.view.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.setStyleSheet(self.style)
        self.app.setFont(self.font)
        set_language(self.language)

    def open(self):
        self.view.commodity.click()
        self.app.processEvents()
        picker = self.view.commodity._picker
        self.assertTrue(picker.search.hasFocus())
        return picker

    def choose(self, picker, item, method='mouse'):
        grid = picker.grid
        index = picker.model.index_for_id(item.frontier_id)
        self.assertTrue(index.isValid())
        self.assertEqual(index.data(), commodity_name(item))
        self.assertEqual(index.data(COMMODITY_ID_ROLE), item.frontier_id)
        grid.scrollTo(index)
        self.app.processEvents()
        pos = grid.visualRect(index).center()
        self.assertEqual(grid.indexAt(pos).data(COMMODITY_ID_ROLE), item.frontier_id)
        if method == 'enter':
            QTest.keyClick(picker.search, Qt.Key.Key_Tab)
            grid.setCurrentIndex(index)
            QTest.keyClick(grid, Qt.Key.Key_Return)
        else:
            # The search retains focus, as in the real bug. Do not pre-focus the
            # grid: that would conceal the scroll occurring during mouse press.
            self.assertTrue(picker.search.hasFocus())
            scroll = grid.verticalScrollBar().value()
            if method == 'double':
                QTest.mouseDClick(grid.viewport(), Qt.MouseButton.LeftButton, pos=pos)
            else:
                QTest.mousePress(grid.viewport(), Qt.MouseButton.LeftButton, pos=pos)
            self.assertEqual(grid.verticalScrollBar().value(), scroll)
            self.assertEqual(grid.indexAt(pos).data(COMMODITY_ID_ROLE), item.frontier_id)
            QTest.mouseRelease(grid.viewport(), Qt.MouseButton.LeftButton, pos=pos)
        self.assertIsNone(self.view.commodity._picker)
        self.assertEqual(self.view.commodity.currentData(), item.frontier_id)
        self.assertEqual(lookup_by_id(self.view.commodity.currentData()).symbol, item.symbol)
        self.assertEqual(self.view.commodity.currentText(), commodity_name(item))
        self.assertFalse(self.provider.queries)

    def test_grandidierite_repeated_mouse_selection_from_scrolled_unfiltered_grid(self):
        item = lookup_by_symbol('Grandidierite')
        self.assertEqual(item.frontier_id, 128924330)
        self.assertEqual(commodity_name(item), 'Grandidierit')
        for attempt in range(8):
            with self.subTest(attempt=attempt):
                # Mix no prior selection and remote prior selections to ensure
                # the result cannot be made correct by the previous choice.
                previous = (None, lookup_by_symbol('Beer').frontier_id,
                            lookup_by_symbol('Platinum').frontier_id, item.frontier_id)[attempt % 4]
                self.view.commodity.set_commodity(previous)
                self.choose(self.open(), item)

    def test_additional_named_goods_reach_trade_view_by_id(self):
        for symbol, name in [('Platinum', 'Platin'), ('Gold', 'Gold'), ('Beer', 'Bier'),
                             ('Alexandrite', 'Alexandrit'), ('Praseodymium', 'Praseodym'),
                             ('PericlaseDunite', 'Periklas-Dunit')]:
            with self.subTest(symbol=symbol):
                item = lookup_by_symbol(symbol)
                self.assertEqual(commodity_name(item), name)
                self.choose(self.open(), item)

    def test_filter_display_partial_english_symbol_and_clear(self):
        item = lookup_by_symbol('Grandidierite')
        for text in ('Grandidierit', 'Grandi', item.english_name, item.symbol.upper(), ''):
            with self.subTest(text=text):
                picker = self.open()
                picker.search.setText('Grandi')
                picker.search.setText(text)
                self.app.processEvents()
                self.assertEqual(picker.model.rowCount(), 1 if text else 412)
                self.choose(picker, item)

    def test_immediate_click_on_initial_visible_tile(self):
        picker = self.open()
        index = picker.grid.indexAt(picker.grid.visualRect(picker.model.index(0)).center())
        self.choose(picker, lookup_by_id(index.data(COMMODITY_ID_ROLE)))

    def test_scrolling_resize_columns_themes_and_large_font(self):
        item = lookup_by_symbol('Grandidierite')
        for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            for size in (10, 18):
                with self.subTest(light=style == LIGHT_STYLESHEET, font=size):
                    self.app.setFont(QFont(self.font.family(), size))
                    self.app.setStyleSheet(style + f'\nQWidget {{font-size: {size}pt;}}')
                    self.view.commodity.set_commodity(lookup_by_symbol('Beer').frontier_id)
                    picker = self.open()
                    picker.resize(1100, 700)
                    self.app.processEvents()
                    wide = picker.grid.columns
                    picker.grid.scrollToBottom()
                    self.app.processEvents()
                    picker.grid.scrollToTop()
                    picker.resize(400, 650)
                    self.app.processEvents()
                    self.assertLess(picker.grid.columns, wide)
                    self.choose(picker, item)

    def test_double_click_and_keyboard_enter_use_same_role(self):
        item = lookup_by_symbol('Grandidierite')
        for method in ('double', 'enter'):
            self.view.commodity.set_commodity(lookup_by_symbol('Gold').frontier_id)
            self.choose(self.open(), item, method)

    def test_all_412_display_roles_and_hit_targets_match_master_after_filtering(self):
        picker = self.open()
        for text in ('', 'a', 'Grandi', ''):
            picker.search.setText(text)
            self.app.processEvents()
            seen = set()
            for row in range(picker.model.rowCount()):
                index = picker.model.index(row)
                identifier = index.data(COMMODITY_ID_ROLE)
                item = lookup_by_id(identifier)
                self.assertIsNotNone(item)
                self.assertNotIn(identifier, seen)
                seen.add(identifier)
                self.assertEqual(index.data(), commodity_name(item))
                self.assertIs(lookup_by_symbol(item.symbol), item)
                picker.grid.scrollTo(index)
                hit = picker.grid.indexAt(picker.grid.visualRect(index).center())
                self.assertEqual(hit.data(COMMODITY_ID_ROLE), identifier)
            if not text:
                self.assertEqual(seen, {c.frontier_id for c in all_commodities()})
