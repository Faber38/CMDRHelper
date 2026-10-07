"""Rare purchase selection and unchanged offer eligibility; no external IO."""
from dataclasses import replace
from unittest.mock import Mock
import unittest

from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QImage, QPainter, QPalette
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QStyleOptionViewItem
from cmdrhelper.commodity_master import all_commodities, lookup_by_symbol
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language
from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus, PadSize, TradeSide
from cmdrhelper.trade_search import search_trade
from cmdrhelper.ui.commodity_picker import CommodityPicker, COMMODITY_ID_ROLE, RARE_ROLE, commodity_name, text_layout
from cmdrhelper.ui.trade_view import TradeView
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from test_trade_view import State
from test_trade_recommendations import market, item, NOW


class RarePickerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        previous = get_language()
        self.addCleanup(set_language, previous)
        set_language('de')
        self.picker = CommodityPicker(rare_filter=True)
        self.addCleanup(self.picker.close)

    def ids(self):
        return {self.picker.model.index(i).data(COMMODITY_ID_ROLE)
                for i in range(self.picker.model.rowCount())}

    def test_normal_rare_and_back_with_expected_goods(self):
        self.assertEqual(self.picker.goods_filter.checkedButton().text(), 'Waren')
        self.assertEqual(self.ids(), {c.frontier_id for c in all_commodities() if not c.rare})
        self.picker.goods_filter.button(1).click()
        self.assertEqual(self.ids(), {c.frontier_id for c in all_commodities() if c.rare})
        self.assertEqual(len(self.ids()), 142)
        for symbol in ('LavianBrandy', 'SoontillRelics', 'JaquesQuinentianStill'):
            self.assertIn(lookup_by_symbol(symbol).frontier_id, self.ids())
        self.assertNotIn(lookup_by_symbol('Gold').frontier_id, self.ids())
        self.picker.goods_filter.button(0).click()
        self.assertEqual(len(self.ids()), 270)

    def test_search_combines_with_filter_and_selection_retains_id(self):
        self.picker.goods_filter.button(1).click()
        self.picker.search.setText('LavianBrandy')
        index = self.picker.model.index(0)
        self.assertEqual(self.picker.model.rowCount(), 1)
        self.assertNotIn('Selten', index.data(Qt.DisplayRole))
        self.picker._choose(index)
        self.assertEqual(self.picker.commodity_id, lookup_by_symbol('LavianBrandy').frontier_id)
        self.picker.search.setText('Gold')
        self.assertNotIn(lookup_by_symbol('Gold').frontier_id, self.ids())

    def test_exclusive_compact_buttons_keyboard_and_search_in_both_themes(self):
        previous = self.app.styleSheet()
        self.addCleanup(self.app.setStyleSheet, previous)
        for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.app.setStyleSheet(theme)
            self.picker.show()
            self.app.processEvents()
            normal = self.picker.goods_filter.button(0)
            rare = self.picker.goods_filter.button(1)
            normal.click()
            normal.click()  # Clicking the active option cannot deselect both.
            self.assertEqual(self.picker.goods_filter.checkedId(), 0)
            self.assertEqual(sum(b.isChecked() for b in (normal, rare)), 1)
            self.assertLess(normal.width() + rare.width(), self.picker.width() * .8)
            rare.setFocus()
            QTest.keyClick(rare, Qt.Key_Space)
            self.assertEqual(self.picker.goods_filter.checkedId(), 1)
            self.assertEqual(sum(b.isChecked() for b in (normal, rare)), 1)
            self.picker.search.setText('LavianBrandy')
            self.assertEqual(self.picker.model.rowCount(), 1)
            normal.setFocus()
            QTest.keyClick(normal, Qt.Key_Space)
            self.assertEqual(self.picker.model.rowCount(), 0)
            self.picker.search.setText('Gold')
            self.assertIn(lookup_by_symbol('Gold').frontier_id, self.ids())
            rare.click()
            self.assertNotIn(lookup_by_symbol('Gold').frontier_id, self.ids())
            rare.setFocus()
            QTest.keyClick(rare, Qt.Key_Tab)
            self.assertTrue(self.picker.search.hasFocus())
            self.picker.search.clear()

    def test_galactic_travel_guide_keeps_catalogue_classification(self):
        # Real Market.json reports Rare:false for this ID. Phase 1 deliberately
        # uses the catalogue and does not merge/persist the Elite Rare flag.
        self.picker.goods_filter.button(1).click()
        guide = lookup_by_symbol('GalacticTravelGuide')
        self.assertTrue(guide.rare)
        self.assertIn(guide.frontier_id, self.ids())

    def test_rare_border_in_both_filters_and_themes_without_text_suffix(self):
        rare = lookup_by_symbol('LavianBrandy')
        normal = lookup_by_symbol('Gold')
        delegate = self.picker.grid.itemDelegate()
        for light in (False, True):
            for rare_only in (False, True):
                self.picker.goods_filter.button(int(rare_only)).click()
                for item in (rare,) if rare_only else (normal,):
                    with self.subTest(light=light, rare_only=rare_only, symbol=item.symbol):
                        index = self.picker.model.index_for_id(item.frontier_id)
                        self.assertEqual(index.data(RARE_ROLE), item.rare)
                        self.assertEqual(index.data(), commodity_name(item))
                        image = QImage(240, 100, QImage.Format_ARGB32)
                        image.fill(Qt.transparent)
                        option = QStyleOptionViewItem()
                        option.rect = QRect(0, 0, 240, 100)
                        option.palette.setColor(QPalette.Window, QColor('white' if light else 'black'))
                        painter = QPainter(image)
                        delegate.paint(painter, option, index)
                        painter.end()
                        # Top straight edge is painted by the real delegate.
                        actual = image.pixelColor(120, delegate.MARGIN - 1)
                        expected = QColor(delegate.BORDER_COLORS[light][int(item.rare)])
                        for a, b in zip(actual.getRgb()[:3], expected.getRgb()[:3]):
                            self.assertLessEqual(abs(a-b), 2)

    def test_long_rare_names_use_only_name_for_text_layout(self):
        self.picker.goods_filter.button(1).click()
        rare = lookup_by_symbol('ClassifiedExperimentalEquipment')
        index = self.picker.model.index_for_id(rare.frontier_id)
        name = commodity_name(rare)
        self.assertEqual(index.data(), name)
        font = self.picker.grid.font()
        self.assertLessEqual(text_layout(index.data(), font, 120)[1],
                             text_layout(name + ' · Selten', font, 120)[1])

    def test_filter_only_enabled_on_buy_tab(self):
        view = TradeView(State(), provider=Mock(), pool=Mock())
        self.addCleanup(view.close)
        self.assertFalse(view.commodity.rare_filter)
        view.tabs.setCurrentIndex(1)
        view.commodity.open_picker()
        self.assertIsNotNone(view.commodity._picker.goods_filter)
        view.commodity._picker.reject()
        view.tabs.setCurrentIndex(0)
        view.commodity.open_picker()
        self.assertIsNone(view.commodity._picker.goods_filter)
        self.assertFalse(view.commodity._picker.model.mark_rare)
        view.commodity._picker.reject()

    def test_all_twelve_languages_have_explicit_translations(self):
        self.assertEqual(len(_TRANSLATIONS), 12)
        for language, texts in _TRANSLATIONS.items():
            for key in ('odyssey.items', 'trade.goods_rare'):
                with self.subTest(language=language, key=key):
                    self.assertTrue(texts.get(key))


class RareOfferTests(unittest.TestCase):
    def setUp(self):
        self.rare = lookup_by_symbol('LavianBrandy')
        self.provider = Mock()
        self.provider.search_buy.return_value = MarketSearchResult(MarketStatus.NO_RESULTS)
        self.query = MarketSearch(self.rare.frontier_id, 'Fixture', minimum_quantity=10)

    def search(self, *, supply=24, price=3500, distance=5, query=None, carrier=False, local_only=False):
        row = market(rows=[item(self.rare, buy=price, supply=supply)],
                     station_type='FleetCarrier' if carrier else 'Coriolis')
        return search_trade(self.provider, query or self.query, TradeSide.BUY,
                            [row], {1: distance}, clock=lambda: NOW, local_only=local_only)

    def test_rare_purchase_uses_real_price_and_supply(self):
        result = self.search()
        self.assertEqual(len(result.offers), 1)
        self.assertEqual(result.offers[0].commander_buy_price, 3500)
        self.assertEqual(result.offers[0].supply, 24)
        self.provider.search_buy.assert_called_once()
        self.provider.search_sell.assert_not_called()

    def test_no_stock_or_insufficient_stock_or_zero_price_is_not_buyable(self):
        for args in ({'supply': 0}, {'supply': 9}, {'price': 0}):
            with self.subTest(args=args):
                self.assertFalse(self.search(**args).offers)

    def test_local_only_never_calls_provider(self):
        self.assertEqual(len(self.search(local_only=True).offers), 1)
        self.provider.search_buy.assert_not_called()
        self.provider.search_sell.assert_not_called()

    def test_radius_and_pad_filters_still_apply(self):
        self.assertFalse(self.search(distance=101).offers)
        self.assertFalse(self.search(query=replace(self.query, required_pad=PadSize.LARGE)).offers)

    def test_carrier_rare_offer_requires_existing_carrier_filter_and_stock(self):
        self.assertFalse(self.search(carrier=True).offers)
        query = replace(self.query, include_fleet_carriers=True)
        self.assertEqual(len(self.search(carrier=True, query=query).offers), 1)
        self.assertFalse(self.search(carrier=True, query=query, supply=0).offers)
