"""Offline GUI/worker regressions for the fixed current selling destination."""
from dataclasses import replace
from datetime import timedelta
from threading import get_ident
import unittest
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from cmdrhelper.i18n import tr, set_language, _TRANSLATIONS
from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus, PadSize
from cmdrhelper.recommendation_diagnostics import PartialReason
from cmdrhelper.trade_recommendations import RecommendationResult, SupplyRecommendation
from cmdrhelper.market_candidates import local_offer
from cmdrhelper.ui.recommendations_view import RecommendationWorker, SupplyRecommendationsView, diagnostic_reason_text
from cmdrhelper.ui.commodity_picker import CommodityField
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
import test_recommendations_view as fixtures
from test_trade_recommendations import market, item, BEER, GOLD, NOW
from test_supply_recommendations import source


class SupplyViewTests(unittest.TestCase):
    setUpClass = fixtures.RecommendationViewTests.__dict__['setUpClass']
    tearDown = fixtures.RecommendationViewTests.tearDown
    wait = fixtures.RecommendationViewTests.wait
    search = fixtures.RecommendationViewTests.search

    def setUp(self):
        fixtures.RecommendationViewTests.setUp(self)
        self.view = self.trade.supply_recommendations
        self.trade.tabs.setCurrentIndex(3)
        def buy(q, *, cancel):
            self.provider.calls.append(q)
            self.provider.threads.append(get_ident())
            while not self.provider.gate.wait(.005):
                if cancel.is_set():
                    return MarketSearchResult(MarketStatus.CANCELLED)
            return MarketSearchResult(MarketStatus.OK, (source(
                master=BEER if q.commodity==BEER.frontier_id else GOLD),))
        self.provider.search_buy = buy
        self.app.processEvents()

    def test_new_tab_fixed_target_no_picker_no_automatic_search(self):
        self.assertEqual(self.trade.tabs.tabText(3), 'Hier verkaufen')
        self.assertEqual(self.trade.tabs.tabText(2), 'Empfehlungen')
        self.assertEqual(self.view.search_button.text(), 'Bezugsquellen suchen')
        self.assertIn('Festes Verkaufsziel: Fixture Port', self.view.origin_label.text())
        self.assertIn('Alternative', self.view.explanation.text())
        self.assertEqual(self.view.quantity.value(), 280)
        self.assertFalse(self.view.findChildren(CommodityField))
        self.assertFalse(self.provider.calls)
        self.assertEqual(self.view.table.columnCount(), 18)
        self.assertFalse(self.view.table.isColumnHidden(0))

    def test_async_query_filters_quantity_table_and_source_copy(self):
        self.view.quantity.setValue(20)
        self.view.pad.setCurrentIndex(self.view.pad.findData(PadSize.LARGE))
        self.view.carriers.setChecked(True)
        self.view.radius.setCurrentIndex(3)
        self.view.arrival.setText('300')
        self.search()
        q = self.provider.calls[0]
        self.assertEqual((q.required_pad, q.radius_ly, q.max_distance_to_arrival_ls,
                          q.include_fleet_carriers), (PadSize.LARGE,250,300,True))
        self.assertTrue(all(t != get_ident() for t in self.provider.threads))
        row = self.view.rows[0]
        self.assertEqual((row.quantity, row.total_profit), (20,30000))
        self.assertEqual(row.target.market_id, 1)
        self.assertEqual(row.source.market_id, 2)
        table = self.view.table
        self.assertEqual(table.item(0, 9).text(), row.source.system_name)
        self.assertEqual(table.item(0, 15).text(), '200 t')
        self.assertEqual(table.item(0, 16).text(), '190 t')
        for column in range(18):
            self.assertIsNotNone(table.item(0, column))
        with patch('cmdrhelper.ui.recommendations_view.copy_system_name') as copy:
            self.view.system_copy_delegate.copyRequested.emit(0, 9)
            copy.assert_called_once_with(row.source.system_name)
        self.assertFalse(self.view.progress_bar.isVisible())
        self.assertEqual(self.view.progress_bar.value(), 1)

    def test_local_only_matches_existing_checkbox_worker_and_persists_tabs(self):
        self.assertEqual(self.view.local_only.text(), self.trade.recommendations.local_only.text())
        self.assertEqual(self.view.local_only.toolTip(), self.trade.recommendations.local_only.toolTip())
        self.assertFalse(self.view.local_only.isChecked())
        self.cache.put(market(mid=3, fid='F_OTHER'))
        self.view.local_only.setChecked(True)
        self.search()
        self.assertEqual(self.view.rows[0].source.provider, 'local_elite')
        self.assertFalse(self.provider.calls)
        self.assertTrue(self.view.last_run.local_only)
        self.assertEqual((self.view.last_run.http_requests, self.view.last_run.cache_hits), (0,0))
        self.assertFalse(self.view.last_run.partial)
        self.assertEqual(self.view.notice.text(), tr('recommend.local_notice'))
        self.trade.tabs.setCurrentIndex(0)
        self.trade.tabs.setCurrentIndex(3)
        self.assertTrue(self.view.local_only.isChecked())
        self.assertFalse(self.trade.recommendations.local_only.isChecked())

    def test_toggle_to_mixed_uses_freshness_and_clears_previous_rows(self):
        self.cache.put(market(mid=2, stamp=NOW-timedelta(minutes=1)))
        self.view.local_only.setChecked(True)
        self.search()
        self.assertEqual(self.view.rows[0].source.provider, 'local_elite')
        self.view.local_only.setChecked(False)
        self.assertFalse(self.view.rows)
        self.search()
        self.assertTrue(self.provider.calls)
        self.assertEqual(self.view.rows[0].source.provider, 'spansh')
        self.assertFalse(self.view.last_run.local_only)
        self.assertEqual(self.view.notice.text(), tr('supply.notice'))

    def test_newer_local_empty_suppresses_community_in_gui(self):
        self.cache.put(market(mid=2, rows=[]))
        self.search()
        self.assertFalse(self.view.rows)
        self.assertTrue(self.provider.calls)
        self.assertFalse(self.view.last_run.partial)

    def test_local_only_empty_no_provider_and_filters_still_apply(self):
        self.view.local_only.setChecked(True)
        self.search()
        self.assertFalse(self.view.rows)
        self.assertFalse(self.view.last_run.partial)
        self.cache.put(market(mid=3))
        self.view.arrival.setText('100')
        self.search()
        self.assertFalse(self.view.rows)  # no invented local arrival
        self.assertFalse(self.provider.calls)
        self.assertIn(tr('recommend.no_results_local'), self.view.status.text())

    def test_toggle_during_run_rejects_old_mixed_results(self):
        self.provider.gate.clear()
        self.view.start_search()
        old = self.view.worker
        self.assertFalse(self.view.filters.isEnabled())
        self.view.local_only.setChecked(True)
        self.assertTrue(old.cancel.is_set())
        self.provider.gate.set()
        self.wait()
        self.assertFalse(self.view.rows)
        calls = len(self.provider.calls)
        self.cache.put(market(mid=3))
        self.search()
        self.assertEqual(len(self.provider.calls), calls)
        self.assertEqual(self.view.rows[0].source.provider, 'local_elite')

    def test_quantity_and_exact_free_cargo_changes_invalidate(self):
        self.search()
        self.view.quantity.setValue(7)
        self.assertFalse(self.view.rows)
        self.search()
        self.assertEqual(self.view.rows[0].quantity, 7)
        self.provider.gate.clear()
        self.view.start_search()
        old = self.view.worker
        self.state.cargo_snapshot['count'] = 25
        self.state.cargoSnapshotChanged.emit(self.state.cargo_snapshot)
        self.assertTrue(old.cancel.is_set())
        self.provider.gate.set()
        self.wait()
        self.assertFalse(self.view.rows)
        self.assertEqual(self.view.free, 275)

    def test_station_market_commander_and_ship_context_changes_cancel(self):
        for change, restore in (
            (lambda: setattr(self.state, 'station', 'Elsewhere'), lambda: setattr(self.state, 'station', 'Fixture Port')),
            (lambda: setattr(self.state, 'system', 'Elsewhere'), lambda: setattr(self.state, 'system', 'Fixture System')),
            (lambda: setattr(self.state, 'commander_fid', 'Other'), lambda: setattr(self.state, 'commander_fid', market()['fid'])),
            (lambda: setattr(self.state.ship_loadout, 'ship_id', 99), lambda: setattr(self.state.ship_loadout, 'ship_id', 7)),
        ):
            self.provider.gate.clear()
            self.view.start_search()
            old = self.view.worker
            self.assertIsNotNone(old)
            change()
            self.state.changed.emit()
            self.assertTrue(old.cancel.is_set())
            self.provider.gate.set()
            self.wait()
            self.assertFalse(self.view.rows)
            restore()
            self.state.changed.emit()
        self.provider.gate.clear()
        self.view.start_search()
        old = self.view.worker
        self.now = NOW+timedelta(seconds=1)
        self.cache.put(market(stamp=self.now))
        self.assertTrue(old.cancel.is_set())
        self.provider.gate.set()
        self.wait()
        self.assertFalse(self.view.rows)

    def test_tab_switch_cancel_and_late_signals(self):
        self.provider.gate.clear()
        self.view.start_search()
        old = self.view.worker
        self.trade.tabs.setCurrentIndex(2)
        self.trade.tabs.setCurrentIndex(3)
        self.assertTrue(old.cancel.is_set())
        self.provider.gate.set()
        self.wait()
        self.assertFalse(self.view.rows)
        self.search()
        expected = self.view.rows
        old.signals.finished.emit(RecommendationResult())
        self.app.processEvents()
        self.assertEqual(self.view.rows, expected)

    def test_missing_expired_full_or_unknown_cargo_blocks_search(self):
        self.now = NOW+timedelta(days=2)
        self.view.refresh()
        self.assertFalse(self.view.search_button.isEnabled())
        self.assertIsNone(self.view.origin)
        self.view.start_search()
        self.assertFalse(self.provider.calls)
        self.now = NOW
        for count in (300, None):
            self.state.cargo_snapshot['count'] = count
            self.view.refresh()
            self.assertFalse(self.view.search_button.isEnabled())
        self.state.cargo_snapshot['count'] = 20
        self.state.observed_markets.context['MarketID'] = 999
        self.view.refresh()
        self.assertFalse(self.view.search_button.isEnabled())

    def test_worker_validates_local_only_sources(self):
        target = local_offer(market(), item(), 0, NOW)
        foreign = SupplyRecommendation(source(), target, 10)
        worker = RecommendationWorker(market(), (), {}, 100, 10, MarketSearch('', 'Fixture System'),
            self.provider, lambda:NOW, supply=True, local_only=True)
        with self.assertRaises(ValueError):
            worker._validate_sources(RecommendationResult(rows=(foreign,)))

    def test_all_languages_placeholders_and_theme_render(self):
        keys = {key for key in _TRANSLATIONS['en'] if key.startswith('supply.')}
        for language, table in _TRANSLATIONS.items():
            self.assertTrue(keys.issubset(table), language)
            set_language(language)
            for key in keys:
                text = tr(key, margin=10, station='Port', system='System', source='Local', age='1 h', count=2)
                self.assertNotIn('{', text)
                self.assertNotEqual(text, key)
            for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                view = SupplyRecommendationsView(self.state, self.provider, self.pool)
                view.setStyleSheet(style)
                font = view.font(); font.setPointSize(18); view.setFont(font)
                view.resize(640, 700); view.show()
                self.app.processEvents()
                self.assertEqual(view.search_button.text(), tr('supply.search'))
                self.assertTrue(view.local_only.isVisible())
                view.close(); view.deleteLater()
        self.assertFalse(self.provider.calls)

    def test_default_quantity_tracks_confirmed_space_until_manually_chosen(self):
        self.state.cargo_snapshot['count'] = 50
        self.state.changed.emit()
        self.assertEqual(self.view.quantity.value(), 250)
        self.view.quantity.setValue(25)
        self.state.cargo_snapshot['count'] = 100
        self.state.changed.emit()
        self.assertEqual(self.view.quantity.value(), 25)
        self.search()
        self.assertEqual(self.view.rows[0].quantity, 25)

    def test_partial_error_and_limits_are_visible_with_local_results(self):
        self.cache.put(market(mid=3))
        for response in (MarketSearchResult(MarketStatus.TIMEOUT),
                         MarketSearchResult(MarketStatus.OK, (source(),), truncated=True)):
            self.provider.search_buy = lambda q, cancel: response
            self.search()
            self.assertTrue(self.view.rows)
            self.assertTrue(self.view.last_run.partial)
            self.assertIn(tr('recommend.partial_counts', checked=1, total=1,
                reason=diagnostic_reason_text(self.view.last_run.partial_reason)),
                self.view.status.text())
