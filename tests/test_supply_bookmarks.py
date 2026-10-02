"""Shared bookmark and station-body integration for fixed selling targets."""
from dataclasses import replace
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import Qt
from cmdrhelper.market_candidates import local_offer
from cmdrhelper.trade_recommendations import SupplyRecommendation
from test_trade_recommendations import market, item, NOW, GOLD
from test_supply_recommendations import source
from test_trade_station_body import cache_document
import test_supply_view as fixtures


class SupplyBookmarkTests(unittest.TestCase):
    setUpClass = fixtures.SupplyViewTests.__dict__['setUpClass']
    setUp = fixtures.SupplyViewTests.setUp
    tearDown = fixtures.SupplyViewTests.tearDown
    wait = fixtures.SupplyViewTests.wait
    search = fixtures.SupplyViewTests.search

    def row(self, **changes):
        return SupplyRecommendation(source(**changes), local_offer(market(), item(), 0, NOW), 20)

    def mark(self, index=0):
        mark = self.view.table.item(index, 0)
        mark.setCheckState(Qt.Checked)
        return mark.data(Qt.UserRole + 2)

    def test_mark_snapshot_direction_highlight_and_source_copy(self):
        row = self.row()
        self.view.render((row,))
        key = self.mark()
        panel = self.view.remembered_panel
        self.assertEqual(panel.targets[key], row)
        saved = panel.targets[key]
        self.assertEqual((saved.buy_price, saved.sell_price, saved.quantity), (10000, 11500, 20))
        self.assertEqual((saved.source.supply, saved.target.demand), (200, 190))
        self.assertIn('Synthetic Target · Synthetic Port', panel.text())
        self.assertIn('→ Fixture System · Fixture Port', panel.text())
        for col in range(self.view.table.columnCount()):
            self.assertTrue(self.view.table.item(0, col).data(Qt.UserRole + 1))
        with patch('cmdrhelper.ui.remembered_targets.copy_system_name') as copy:
            panel.entries[key][3].click()
            copy.assert_called_once_with(row.source.system_name)
        with patch('cmdrhelper.ui.recommendations_view.copy_system_name') as copy:
            self.view.system_copy_delegate.copyRequested.emit(0, 9)
            copy.assert_called_once_with(row.source.system_name)

    def test_uncheck_and_remove_button_use_shared_lifecycle(self):
        row = self.row()
        self.view.render((row,))
        self.mark()
        self.view.table.item(0, 0).setCheckState(Qt.Unchecked)
        self.assertFalse(self.view.remembered_flights)
        key = self.mark()
        self.view.remembered_panel.entries[key][2].click()
        self.assertFalse(self.view.remembered_flights)
        self.assertEqual(self.view.table.item(0, 0).checkState(), Qt.Unchecked)
        self.assertFalse(self.view.table.item(0, 1).data(Qt.UserRole + 1))

    def test_refresh_search_and_changed_prices_keep_original_route_snapshot(self):
        self.search()
        row = self.view.rows[0]
        key = self.mark()
        self.view.refresh()
        self.search()
        self.assertEqual(self.view.table.item(0, 0).checkState(), Qt.Checked)
        self.view.render((replace(row, quantity=3, source=replace(row.source, commander_buy_price=9000)),))
        self.assertEqual(self.view.table.item(0, 0).checkState(), Qt.Checked)
        self.assertEqual(self.view.remembered_flights[key], row)
        self.view.render(())
        self.assertEqual(self.view.remembered_flights[key], row)
        self.view.remembered_panel.entries[key][2].click()
        self.view.render((row,))
        self.assertEqual(self.view.table.item(0, 0).checkState(), Qt.Unchecked)

    def test_commodity_and_target_are_part_of_route_identity(self):
        row = self.row()
        others = (replace(row, source=source(master=GOLD),
                          target=replace(row.target, commodity_id=GOLD.frontier_id, commodity_symbol=GOLD.symbol)),
                  replace(row, target=replace(row.target, station_name='Other target', market_id=44)),
                  replace(row, target=replace(row.target, system_name='Other system')))
        self.view.render((row,))
        self.mark()
        for other in others:
            self.view.render((other,))
            self.assertEqual(self.view.table.item(0, 0).checkState(), Qt.Unchecked)
            self.mark()
        self.assertEqual(len(self.view.remembered_flights), 4)
        self.view.render((row,))
        self.assertEqual(self.view.table.item(0, 0).checkState(), Qt.Checked)

    def test_body_uses_existing_cached_metadata_and_bookmark_snapshot(self):
        service = Mock(spec=['cached', 'refresh_system'])
        service.cached.return_value = cache_document()
        self.state.spansh_stations = service
        surface = self.row(station_type='CraterPort')
        orbital = replace(surface, source=replace(surface.source, station_type='Coriolis'))
        unknown = replace(surface, source=replace(surface.source, station_name='Unknown', market_id=77))
        for row, expected in ((orbital, '–'), (unknown, '–'), (surface, '4 a')):
            self.view.render((row,))
            self.assertEqual(self.view.table.item(0, 17).text(), expected)
        key = self.mark()
        self.assertIn(' · 4 a · ', self.view.remembered_panel.text())
        self.view.render(())
        service.cached.return_value = None
        self.view.render((surface,))
        self.assertEqual(self.view.table.item(0, 17).text(), '–')
        self.assertEqual(self.view.table.item(0, 0).checkState(), Qt.Checked)
        self.assertEqual(self.view.remembered_panel.body_labels[key], '4 a')
        service.cached.return_value = cache_document(name='Synthetic Target 5 b', parent=8)
        self.view.render((surface,))
        self.assertEqual(self.view.table.item(0, 17).text(), '5 b')
        self.assertEqual(self.view.remembered_panel.body_labels[key], '4 a')
        service.refresh_system.assert_not_called()

    def test_commander_change_clears_routes_but_travel_keeps_direction(self):
        row = self.row()
        self.view.render((row,))
        key = self.mark()
        self.state.station = 'Other station'
        self.state.changed.emit()
        self.assertEqual(self.view.remembered_flights[key], row)
        self.assertIn('→ Fixture System · Fixture Port', self.view.remembered_panel.text())
        self.state.commander_fid = 'Other'
        self.state.changed.emit()
        self.assertFalse(self.view.remembered_flights)
