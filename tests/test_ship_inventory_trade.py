"""Inventory sales use the existing search, with manual empty/unknown modes."""
import unittest
from unittest.mock import Mock
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QColor, QImage, QPainter, QPalette
from PySide6.QtWidgets import QApplication, QStyleOptionViewItem
from PySide6.QtTest import QTest
from cmdrhelper.commodity_master import lookup_by_symbol
from cmdrhelper.i18n import _TRANSLATIONS, set_language, get_language, tr
from cmdrhelper.market_data import MarketSearchResult, MarketStatus, PadSize
from cmdrhelper.ui.trade_view import TradeView
from cmdrhelper.ui.commodity_picker import RARE_ROLE, CommodityTileDelegate
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests.test_trade_view import State, offer


def inventory(**quantities):
    return dict(count=sum(quantities.values()), ship_id=20,
                inventory=[dict(frontier_name=name, display_name=name, count=count)
                           for name, count in quantities.items()])


class CargoState(State):
    cargoSnapshotChanged = Signal(object)
    ship_inventory = None
    ship_cargo_total = None


class InventoryTradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        old = get_language()
        self.addCleanup(set_language, old)
        set_language('de')
        self.state = CargoState()
        self.pool = Mock()
        self.provider = Mock()
        self.provider.search_sell.side_effect = lambda q, **kw: MarketSearchResult(
            MarketStatus.OK, (offer(commodity_id=q.commodity, commodity_symbol=next(
                m.symbol for m in (lookup_by_symbol('gold'), lookup_by_symbol('tritium'),
                                   lookup_by_symbol('jaquesquinentianstill')) if m.frontier_id == q.commodity)),), q)
        self.view = TradeView(self.state, provider=self.provider, pool=self.pool)
        self.view.show()
        self.addCleanup(self.cleanup)

    def cleanup(self):
        if self.view.worker:
            self.view.cancel_search()
            self.view.worker.run()
        self.view.close()
        self.view.deleteLater()
        self.app.processEvents()

    def set_cargo(self, snapshot, count=None):
        self.state.ship_inventory = snapshot
        self.state.ship_cargo_total = {'count': count} if count is not None else None
        self.state.cargoSnapshotChanged.emit(snapshot)

    def test_known_loaded_uses_cargo_and_actual_eight_tonnes(self):
        self.set_cargo(inventory(gold=8), 8)
        v = self.view
        self.assertTrue(v.cargo_panel.isVisible())
        self.assertTrue(v.cargo_list.isVisible())
        self.assertFalse(v.commodity.isVisible())
        self.assertFalse(v.quantity.isVisible())
        self.assertEqual(v.cargo_list.count(), 1)
        self.assertIn('8 t', v.cargo_list.item(0).text())
        self.assertFalse(v.search_button.isEnabled())
        v.cargo_list.item(0).setCheckState(Qt.Checked)
        v.start_search()
        self.assertEqual(v.worker.queries[0].minimum_quantity, 8)
        self.assertEqual(v.worker.queries[0].commodity, lookup_by_symbol('gold').frontier_id)

    def test_rare_only_visible_but_no_search_and_inventory_unchanged(self):
        snapshot = inventory(jaquesquinentianstill=8)
        self.set_cargo(snapshot, 8)
        item = self.view.cargo_list.item(0)
        self.assertIn('8 t', item.text())
        self.assertTrue(item.data(RARE_ROLE))
        self.assertFalse(item.flags() & Qt.ItemIsUserCheckable)
        self.assertFalse(item.flags() & Qt.ItemIsSelectable)
        self.assertTrue(self.view.cargo_rare_notice.isVisible())
        self.view.cargo_select_all.click()
        self.assertEqual(self.view._selected_cargo(), [])
        self.assertFalse(self.view.search_button.isEnabled())
        self.view.start_search()
        self.pool.start.assert_not_called()
        self.assertEqual(snapshot, inventory(jaquesquinentianstill=8))
        self.assertIs(self.state.ship_inventory, snapshot)

    def test_cargo_rare_border_reuses_picker_colors_in_both_themes(self):
        self.set_cargo(inventory(jaquesquinentianstill=8), 8)
        for light in (False, True):
            image = QImage(240, 40, QImage.Format_ARGB32)
            image.fill(Qt.transparent)
            option = QStyleOptionViewItem()
            option.rect = QRect(0, 0, 240, 40)
            option.palette.setColor(QPalette.Window, QColor('white' if light else 'black'))
            painter = QPainter(image)
            self.view.cargo_list.itemDelegate().paint(
                painter, option, self.view.cargo_list.model().index(0, 0))
            painter.end()
            self.assertEqual(image.pixelColor(120, 1),
                             QColor(CommodityTileDelegate.BORDER_COLORS[light][1]))

    def test_mixed_cargo_select_all_only_gold(self):
        self.set_cargo(inventory(jaquesquinentianstill=8, gold=10), 18)
        self.assertEqual(self.view.cargo_list.count(), 2)
        self.view.cargo_select_all.click()
        self.assertEqual(self.view._selected_cargo(), [(lookup_by_symbol('gold').frontier_id, 10)])
        self.view.start_search()
        self.assertEqual(len(self.view.worker.queries), 1)
        self.assertEqual(self.view.worker.queries[0].minimum_quantity, 10)

    def test_manual_picker_excludes_rare_and_buy_selection_cannot_leak(self):
        self.set_cargo(None, 0)
        field = self.view.commodity
        rare_id = lookup_by_symbol('jaquesquinentianstill').frontier_id
        self.assertFalse(field.set_commodity(rare_id))
        field.open_picker()
        picker = field._picker
        self.assertFalse(picker.model.index_for_id(rare_id).isValid())
        picker.search.setText('jaques')
        self.assertEqual(picker.model.rowCount(), 0)
        picker.reject()
        self.view.tabs.setCurrentIndex(1)
        self.assertTrue(field.set_commodity(rare_id))
        self.view.tabs.setCurrentIndex(0)
        self.assertIsNone(field.currentData())
        # Also guard a stale/injected field value at the search boundary.
        field._commodity_id = rare_id
        self.view.start_search()
        self.pool.start.assert_not_called()

    def test_empty_is_normal_manual_mode_not_warning(self):
        for snapshot in (inventory(), None):
            with self.subTest(snapshot=snapshot):
                self.set_cargo(snapshot, 0)
                self.assertFalse(self.view.cargo_panel.isVisible())
                self.assertTrue(self.view.commodity.isVisible())
                self.assertTrue(self.view.quantity.isVisible())
                self.assertEqual(self.view.search_button.text(), tr('trade.search'))
                self.assertTrue(self.view.search_button.isEnabled())

    def test_occupied_unknown_has_warning_and_manual_search(self):
        self.set_cargo(None, 8)
        self.assertTrue(self.view.cargo_panel.isVisible())
        self.assertEqual(self.view.cargo_heading.text(), 'Aktueller Warenbestand nicht sicher bekannt.')
        self.assertFalse(self.view.cargo_list.isVisible())
        self.assertTrue(self.view.commodity.isVisible())
        self.view.commodity.set_commodity(lookup_by_symbol('gold').frontier_id)
        self.view.quantity.setValue(5)
        self.view.start_search()
        self.assertEqual(self.view.worker.query.minimum_quantity, 5)
        self.assertFalse(hasattr(self.view.worker, 'queries'))

    def test_multiple_selection_searches_each_quantity_and_preserves_filters(self):
        self.set_cargo(inventory(jaquesquinentianstill=8, lavianbrandy=2, gold=12, tritium=4), 26)
        v = self.view
        v.radius.setCurrentIndex(1)
        v.pad.setCurrentIndex(v.pad.findData(PadSize.LARGE.value))
        v.arrival.setText('900')
        v.carriers.setChecked(False)
        v.cargo_select_all.click()
        self.assertEqual(len(v._selected_cargo()), 2)
        v.start_search()
        queries = v.worker.queries
        self.assertEqual([q.minimum_quantity for q in queries], [12, 4])
        for q in queries:
            self.assertEqual(q.radius_ly, v.radius.currentData())
            self.assertEqual(q.required_pad, PadSize.LARGE)
            self.assertEqual(q.max_distance_to_arrival_ls, 900)
            self.assertFalse(q.include_fleet_carriers)
            self.assertEqual(q.max_age, v.max_age.max_age())
        v.worker.run()
        self.assertEqual(self.provider.search_sell.call_count, 2)
        self.assertEqual(v.cargo_results.count(), 2)
        self.assertTrue(v.cargo_results.isVisible())
        v.cargo_results.setCurrentIndex(0)
        self.assertIn('12 t', v.cargo_results.currentText())
        self.assertEqual(v.table.rowCount(), 1)
        self.assertEqual(v.offers[0].commodity_symbol, lookup_by_symbol('gold').symbol)
        self.assertEqual(v.table.item(0, 5).value, 12 * v.offers[0].commander_sell_price)
        v.radius.setCurrentIndex(0)
        self.assertFalse(v.cargo_results.isVisible())

    def test_local_only_never_calls_provider(self):
        self.set_cargo(inventory(jaquesquinentianstill=8, gold=12), 20)
        self.view.cargo_select_all.click()
        self.view.local_only.setChecked(True)
        self.view.start_search()
        self.view.worker.run()
        self.provider.search_sell.assert_not_called()

    def test_live_changes_cancel_and_transition_between_all_three_modes(self):
        self.set_cargo(inventory(gold=8), 8)
        self.view.cargo_select_all.click()
        self.view.start_search()
        worker = self.view.worker
        self.set_cargo(None, 8)
        self.assertTrue(worker.cancel.is_set())
        worker.run()
        self.assertTrue(self.view.commodity.isVisible())
        self.assertTrue(self.view.cargo_panel.isVisible())
        self.set_cargo(inventory(gold=2), 2)
        self.assertIn('2 t', self.view.cargo_list.item(0).text())
        self.assertFalse(self.view.commodity.isVisible())
        self.set_cargo(inventory(), 0)
        self.assertTrue(self.view.commodity.isVisible())
        self.assertFalse(self.view.cargo_panel.isVisible())

    def test_keyboard_selection(self):
        self.set_cargo(inventory(gold=2, jaquesquinentianstill=8), 10)
        self.view.cargo_list.setCurrentRow(0)
        self.view.cargo_list.setFocus()
        QTest.keyClick(self.view.cargo_list, Qt.Key_Space)
        self.assertEqual(len(self.view._selected_cargo()), 1)
        self.assertTrue(self.view.search_button.isEnabled())

    def test_deselecting_all_and_buy_direction(self):
        self.set_cargo(inventory(gold=2, jaquesquinentianstill=8), 10)
        self.view.cargo_select_all.click()
        for i in range(2):
            self.view.cargo_list.item(i).setCheckState(Qt.Unchecked)
        self.assertFalse(self.view.search_button.isEnabled())
        self.view.start_search()
        self.pool.start.assert_not_called()
        self.view.tabs.setCurrentIndex(1)
        self.assertTrue(self.view.commodity.isVisible())
        self.assertTrue(self.view.quantity.isVisible())
        self.assertFalse(self.view.cargo_panel.isVisible())

    def test_i18n_and_both_themes(self):
        keys = ['ship_inventory','cargo_select_all','cargo_results','cargo_unknown',
                'cargo_item','cargo_search','cargo_choose','rare_sell_excluded']
        self.assertEqual(len(_TRANSLATIONS), 12)
        for language, strings in _TRANSLATIONS.items():
            for key in keys:
                self.assertIn('trade.'+key, strings, language)
        self.set_cargo(inventory(jaquesquinentianstill=8), 8)
        for sheet in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.view.setStyleSheet(sheet)
            self.assertTrue(self.view.cargo_list.isVisible())
            self.assertNotEqual(self.view.cargo_list.focusPolicy(), Qt.NoFocus)
