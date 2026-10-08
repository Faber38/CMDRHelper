"""Targeted catalogue-radius, existing bookmarks and demand-only cache contracts."""
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
import sqlite3
import unittest

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from cmdrhelper.commodity_master import all_commodities, lookup_by_symbol
from cmdrhelper.commodity_origin import OriginResolver
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.market_data import MarketSearch, MarketStatus, PadSize, TradeSide
from cmdrhelper.rare_search import search_rare_origins
from cmdrhelper.spansh_cache import SystemCache
from cmdrhelper.spansh_origins import OriginLookup, lookup_documents
from cmdrhelper.spansh_market import SpanshMarketProvider
from cmdrhelper.trade_market_source import TradeMarketSource
from cmdrhelper.market_store import MarketStore
from cmdrhelper.ui.trade_view import TradeView
from cmdrhelper.ui.commodity_picker import CommodityPicker
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from test_spansh_origins import row, response, EXAMPLES, NOW
from test_trade_view import State, offer
from test_trade_recommendations import market, item


class RareRadiusFixture(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.db = self.root/'coordinates.db'
        with sqlite3.connect(self.db) as con:
            con.executescript('''CREATE TABLE systems(system_address INTEGER,name TEXT,x REAL,y REAL,z REAL);
                INSERT INTO systems VALUES(1,'Reference',0,0,0);''')
        self.cache = SystemCache(root=self.root/'spansh', now=lambda: NOW)
        self.resolver = OriginResolver(self.db, spansh_folder=self.cache.root)
        self.query = MarketSearch('', 'Reference', radius_ly=100)
        self.blue = lookup_by_symbol('BlueMilk')
        self.add_station(EXAMPLES[0], 100)

    def add_station(self, example, distance, *, pads=True, arrival=200):
        value = row(example)
        value.update(system_x=distance, system_y=0, system_z=0)
        if distance is None:
            for key in ('system_x', 'system_y', 'system_z'):
                value.pop(key)
        if not pads:
            for size in ('small', 'medium', 'large'):
                value.pop(size+'_pads')
        if arrival is not None:
            value['distance_to_arrival'] = arrival
        for data in lookup_documents(response([value]), {value['market_id']}, NOW):
            self.cache.merge_lookup(data)

    def search(self, query=None, **kwargs):
        return search_rare_origins(self.resolver, query or self.query, 1, now=NOW, **kwargs)


class RareRadiusTests(RareRadiusFixture):
    def test_100ly_inclusive_outside_shared_origin_sorted_and_no_market_claim(self):
        self.add_station(EXAMPLES[1], 101)
        self.add_station(EXAMPLES[2], 50)
        with patch('cmdrhelper.spansh_market.SpanshMarketProvider._request', side_effect=AssertionError('network')):
            result = self.search()
        self.assertEqual([r.distance_ly for r in result.rows], [50, 100, 100])
        shared = [r for r in result.rows if r.market_id == self.blue.origin_market_id]
        self.assertEqual({r.commodity_symbol for r in shared}, {'BlueMilk', 'LeestianEvilJuice'})
        self.assertTrue(all(r.confirmed is None for r in result.rows))
        self.assertEqual(shared[0].coordinates, (100, 0, 0))
        self.assertEqual(shared[0].distance_to_arrival_ls, 200)

    def test_unknown_coordinates_excluded_and_requested_once(self):
        self.cache = SystemCache(root=self.root/'unknown', now=lambda: NOW)
        self.resolver = OriginResolver(self.db, spansh_folder=self.cache.root)
        self.add_station(EXAMPLES[0], None)
        result = self.search()
        self.assertFalse(result.rows)
        self.assertIn(self.blue.origin_market_id, result.unresolved)
        self.assertIn(self.blue.origin_market_id, result.lookup_ids)

    def test_pad_arrival_filters_and_missing_metadata(self):
        self.assertEqual(len(self.search(replace(self.query, required_pad=PadSize.LARGE)).rows), 2)
        self.assertFalse(self.search(replace(self.query, max_distance_to_arrival_ls=199)).rows)
        self.assertEqual(len(self.search(replace(self.query, max_distance_to_arrival_ls=200)).rows), 2)
        # Separate cache: merge_lookup intentionally retains known static metadata.
        self.cache = SystemCache(root=self.root/'missing', now=lambda: NOW)
        self.resolver = OriginResolver(self.db, spansh_folder=self.cache.root)
        self.add_station(EXAMPLES[0], 10, pads=False, arrival=None)
        for query in (replace(self.query, required_pad=PadSize.SMALL),
                      replace(self.query, max_distance_to_arrival_ls=500)):
            result = self.search(query)
            self.assertFalse(result.rows)
            self.assertIn(self.blue.origin_market_id, result.lookup_ids)
        self.assertEqual(len(self.search().rows), 2)

    def quote(self, **kwargs):
        return offer(commodity_id=self.blue.frontier_id, commodity_symbol=self.blue.symbol,
            system_name='Leesti', station_name='George Lucas', system_id64=EXAMPLES[0][4],
            market_id=self.blue.origin_market_id, market_updated_at=NOW-timedelta(hours=1),
            supply=20, commander_buy_price=4200, **kwargs)

    def test_confirmed_community_own_only_and_age_leave_origins(self):
        quote = self.quote()
        result = self.search(community=(quote,))
        self.assertEqual(sum(r.confirmed is not None for r in result.rows), 1)
        for options in ({'community': (quote,), 'local_only': True},
                        {'community': (replace(quote, market_updated_at=NOW-timedelta(days=2)),)},
                        {'community': (replace(quote, supply=0),)},
                        {'community': (replace(quote, commander_buy_price=0),)}):
            result = self.search(**options)
            self.assertEqual(len(result.rows), 2)
            self.assertTrue(all(r.confirmed is None for r in result.rows))

    def test_local_snapshot_once_per_station_and_new_empty_suppresses_quote(self):
        path = self.root/'markets.db'
        snapshot = market(rows=[item(self.blue, buy=4000, supply=23)])
        snapshot.update(market_id=self.blue.origin_market_id, system_name='Leesti',
                        station_name='George Lucas', system_address=EXAMPLES[0][4], observed_at=NOW.isoformat())
        with MarketStore(path, clock=lambda: NOW) as store:
            store.record_observation(snapshot)
        source = TradeMarketSource(path, '', 'Reference', 1, self.db,
                                   station_cache_folder=self.cache.root)
        calls = []
        original = MarketStore.get_current
        def read(store, mid, **kwargs):
            calls.append(mid)
            return original(store, mid, **kwargs)
        with patch.object(MarketStore, 'get_current', read):
            result = self.search(source=source, local_only=True)
        self.assertEqual(calls, [self.blue.origin_market_id])
        self.assertEqual(next(r.confirmed for r in result.rows if r.confirmed).supply, 23)
        # A newer empty snapshot invalidates an older positive community quote.
        empty = dict(snapshot, commodities=[], observed_at=(NOW+timedelta(minutes=1)).isoformat())
        with MarketStore(path, clock=lambda: NOW+timedelta(minutes=1)) as store:
            store.record_observation(empty)
        result = search_rare_origins(self.resolver, self.query, 1, source=source,
            community=(self.quote(),), now=NOW+timedelta(minutes=1))
        self.assertTrue(all(r.confirmed is None for r in result.rows))

    def test_bulk_one_location_pass_and_warm_cache_no_lookup(self):
        with patch.object(self.resolver, 'locations', wraps=self.resolver.locations) as locations:
            result = self.search()
        locations.assert_called_once()
        self.assertNotIn(self.blue.origin_market_id, result.lookup_ids)
        provider = SpanshMarketProvider(opener=Mock(side_effect=AssertionError('network')))
        self.assertEqual(provider.cached_offers(), ())

    def test_absent_market_database_keeps_static_origins(self):
        source = TradeMarketSource(self.root/'absent.db', '', 'Reference', 1, self.db,
                                   station_cache_folder=self.cache.root)
        result = self.search(source=source)
        self.assertEqual(len(result.rows), 2)
        self.assertTrue(all(r.confirmed is None for r in result.rows))
        self.assertFalse(source.path.exists())

    def test_carrier_filter_applies_to_quote_without_removing_static_origin(self):
        quote = self.quote(is_fleet_carrier=True)
        self.assertTrue(all(r.confirmed is None for r in self.search(community=(quote,)).rows))
        result = self.search(replace(self.query, include_fleet_carriers=True), community=(quote,))
        self.assertEqual(sum(r.confirmed is not None for r in result.rows), 1)

    def test_missing_reference_does_not_refetch_known_target_coordinates(self):
        result = search_rare_origins(self.resolver, replace(self.query, reference_system='Missing'), 999, now=NOW)
        self.assertFalse(result.rows)
        self.assertNotIn(self.blue.origin_market_id, result.lookup_ids)

    def test_catalogue_lookup_batches_and_negative_results_are_session_cached(self):
        app = QApplication.instance() or QApplication([])
        provider = Mock()
        provider._request.return_value = response([])
        service = OriginLookup(self.cache, provider=provider, pool=Mock())
        self.addCleanup(lambda: service.timer.stop())
        ids = {c.origin_market_id for c in all_commodities() if c.rare}
        for _ in range(2):
            for mid in ids:
                service.request(mid)
        while service.pending:
            service.timer.stop()
            service.flush()
            service.worker.run()
        self.assertEqual(provider._request.call_count, (len(ids)+4)//5)
        sent = [mid for call in provider._request.call_args_list
                for mid in call.args[1]['filters']['market_id']['value']]
        self.assertEqual(len(sent), len(ids))
        for mid in ids:
            service.request(mid)
        self.assertFalse(service.pending)
        self.assertFalse(service.timer.isActive())


class RareRadiusUiTests(RareRadiusFixture):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_all_languages_themes_remember_dedup_and_single_search(self):
        previous_language, previous_style = get_language(), self.app.styleSheet()
        self.addCleanup(set_language, previous_language)
        self.addCleanup(self.app.setStyleSheet, previous_style)
        result = self.search()
        for language, translations in _TRANSLATIONS.items():
            set_language(language)
            for key in ('rare_search_all', 'rare_unconfirmed', 'rare_results', 'rare_origin_notice'):
                self.assertIn('trade.'+key, translations)
            for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                self.app.setStyleSheet(theme)
                view = TradeView(State(), provider=Mock(), pool=Mock())
                view.tabs.setCurrentIndex(1)
                view.show_rare_result(result)
                self.assertEqual(view.table.rowCount(), 2)
                self.assertEqual(view.offers, ())
                self.assertIn(tr('trade.rare_unconfirmed'), view.table.item(0, 3).text())
                for i in (0, 1, 0):
                    view.table.item(i, 10).setCheckState(Qt.Checked)
                panel = view.remembered_lists[TradeSide.BUY]
                self.assertEqual(len(panel.targets), 1)
                saved = next(iter(panel.targets.values()))
                self.assertEqual(saved.market_id, self.blue.origin_market_id)
                self.assertEqual(saved.coordinates, (100, 0, 0))
                self.assertTrue(saved.commodity_id)
                self.assertEqual(len(saved.remembered_commodities), 2)
                panel.remove(next(iter(panel.targets)))
                self.assertTrue(all(view.table.item(i, 10).checkState() == Qt.Unchecked for i in range(2)))
                view.close()
                view.deleteLater()

    def test_picker_action_without_selected_commodity_uses_existing_worker_flow(self):
        view = TradeView(State(), provider=Mock(), pool=Mock())
        self.addCleanup(view.close)
        self.assertTrue(view.rare_search_button.isHidden())
        view.tabs.setCurrentIndex(1)
        view.commodity.open_picker()
        picker = view.commodity._picker
        self.assertTrue(picker.rare_search_button.isHidden())
        picker.goods_filter.button(1).click()
        self.assertFalse(picker.rare_search_button.isHidden())
        picker.rare_search_button.click()
        self.assertEqual(type(view.worker).__name__, 'RareMarketWorker')
        view.worker.resolver = self.resolver
        view.worker.reference_address = 1
        view.worker.provider = SpanshMarketProvider()
        view._query = replace(view._query, reference_system='Reference')
        view._reference = 'Reference'
        view.worker.query = view._query
        view.worker.run()
        self.assertEqual(view.table.rowCount(), 2)
        self.assertIsNone(view.worker)
        self.assertTrue(view.search_button.isEnabled())

    def test_resolution_finishing_during_local_worker_refreshes_once(self):
        state = State()
        state.system = 'Reference'
        state.system_address = 1
        view = TradeView(state, provider=SpanshMarketProvider(), pool=Mock())
        self.addCleanup(view.close)
        view.tabs.setCurrentIndex(1)
        view._rare_resolver = self.resolver
        view.start_search(all_rare=True)
        first = view.worker
        view._rare_origins_ready()
        self.assertTrue(view._rare_refresh_pending)
        first.run()
        self.assertIsNotNone(view.worker)
        self.assertIsNot(view.worker, first)
        self.assertFalse(view._rare_refresh_pending)
        view.worker.run()
        self.assertIsNone(view.worker)
        self.assertEqual(view.table.rowCount(), 2)

    def test_single_result_layout_restored_after_catalogue_results(self):
        from cmdrhelper.market_data import MarketSearchResult
        view = TradeView(State(), provider=Mock(), pool=Mock())
        self.addCleanup(view.close)
        view.tabs.setCurrentIndex(1)
        view.show_rare_result(self.search())
        quote = offer(supply=10)
        query = MarketSearch(quote.commodity_id, 'Reference', minimum_quantity=1)
        view.show_result(MarketSearchResult(MarketStatus.OK, offers=(quote,)), query)
        self.assertEqual(view.offers, (quote,))
        self.assertEqual(view.table.columnCount(), 11)
        self.assertTrue(all(not view.table.isColumnHidden(c) for c in (5, 8, 9)))
