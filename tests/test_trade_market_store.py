"""A/B trade semantics: temporary identical cache and SQLite data, mocked provider."""
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus, PadSize, TradeSide
from cmdrhelper.market_store import MarketStore, StaleReadError
from cmdrhelper.observed_market_cache import ObservedMarketCache
from cmdrhelper.trade_market_source import TradeMarketSource, prepare_trade_source
from cmdrhelper.trade_search import search_trade
from test_trade_recommendations import market, item, offer, NOW, FID, BEER


class TradeStoreTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.path = self.root/'markets.db'
        self.cache = ObservedMarketCache(self.root/'observed.json', clock=lambda: NOW)
        self.store = MarketStore(self.path, clock=lambda: NOW)
        self.addCleanup(self.store.close)
        self.source = TradeMarketSource(self.path, FID, 'Fixture System', 100)
        self.query = MarketSearch(BEER.frontier_id, 'Fixture System', limit=100)
        self.provider = Mock()
        self.set_provider()

    def set_provider(self, quotes=(), status=MarketStatus.OK):
        self.provider.search_buy.return_value = self.provider.search_sell.return_value = MarketSearchResult(status, tuple(quotes))

    def put(self, value):
        self.assertTrue(self.cache.put(value))
        self.store.record_observation(value)

    def compare(self, query=None, fid=FID, source=None, distances=None):
        query = query or self.query
        source = source or replace(self.source, fid=fid)
        local = self.cache.shared(None)
        if distances is None:
            distances = {s['market_id']: 0.0 for s in local}
        for side in TradeSide:
            with self.subTest(side=side, query=query):
                old = search_trade(self.provider, query, side, local, distances, fid, clock=lambda: NOW)
                new = search_trade(self.provider, query, side, fid=fid, clock=lambda: NOW, local_source=source)
                self.assertEqual(new, old)  # All offers/fields/order/source/status.
        return new

    def test_fid_prices_quantities_nulls_and_missing_newest_snapshot(self):
        self.put(market(stamp=NOW-timedelta(hours=2)))
        self.put(market(rows=[]))
        self.put(market(mid=2, rows=[item(buy=0, supply=0, sell=0, demand=0)]))
        self.put(market(mid=3, rows=[item(buy=42, supply=7, sell=55, demand=9)]))
        self.put(market(fid='OTHER', rows=[item(buy=1, sell=999999)]))
        self.set_provider([offer(mid=1, stamp=NOW-timedelta(hours=1)),
                           offer(mid=2, stamp=NOW-timedelta(hours=1))])
        for minimum in (1, 7, 8, 9, 10):
            self.compare(replace(self.query, minimum_quantity=minimum))
        self.compare(fid='OTHER')
        self.compare(fid='EMPTY')

    def test_newest_source_tie_and_age_boundaries(self):
        for mid, seconds in enumerate((-1, 0, 1), 1):
            self.put(market(mid=mid, stamp=NOW-timedelta(hours=24, seconds=seconds)))
        self.put(market(mid=4, stamp=NOW-timedelta(days=700)))
        for maximum in (timedelta(hours=24), timedelta(days=7), None):
            for delta in (-1, 0, 1):
                self.set_provider([offer(mid=mid, stamp=NOW-timedelta(hours=24, seconds=delta))
                                   for mid in range(1, 5)])
                self.compare(replace(self.query, max_age=maximum))

    def test_location_planetary_carrier_pad_arrival_and_radius(self):
        coords = self.root/'coordinates.db'
        with sqlite3.connect(coords) as con:
            con.execute('CREATE TABLE systems(system_address INTEGER PRIMARY KEY,name TEXT,x REAL,y REAL,z REAL)')
            con.executemany('INSERT INTO systems VALUES(?,?,?,?,?)', [
                (100,'Fixture System',0,0,0), (101,'Nearby',3,4,0), (102,'Far',101,0,0)])
        for mid, kind, address in ((1,'CraterPort',100),(2,'FleetCarrier',101),(3,'Outpost',102),(4,'',999)):
            row = market(mid=mid, station_type=kind, system_address=address)
            if not kind:
                row.pop('station_type')
            self.put(row)
        self.set_provider([offer(mid=5, station_type='CraterPort', largest_pad=PadSize.LARGE),
                           offer(mid=1, stamp=NOW-timedelta(seconds=1), largest_pad=PadSize.LARGE)])
        source = replace(self.source, coordinates_path=coords)
        for pad in PadSize:
            for carriers in (False, True):
                for arrival in (None, 500):
                    self.compare(replace(self.query, required_pad=pad, include_fleet_carriers=carriers,
                                         max_distance_to_arrival_ls=arrival), source=source,
                                 distances={1:0, 2:5, 3:101, 4:None})

    def test_pagination_ranking_limit_and_provider_errors(self):
        # Populate through Store and a synthetic legacy projection (no JSON I/O).
        for mid in range(1, 507):
            row = market(mid=mid, rows=[item(buy=1000-mid, sell=1000+mid)])
            self.cache._markets[(FID, mid)] = row
            self.store.record_observation(row)
        for status in (MarketStatus.OK, MarketStatus.NO_RESULTS, MarketStatus.TIMEOUT, MarketStatus.INVALID_QUERY):
            self.set_provider(status=status)
            for limit in (1, 20, 100):
                self.compare(replace(self.query, limit=limit))
        with patch.object(self.cache, 'all', side_effect=AssertionError('No cache copying')),              patch.object(MarketStore, '_payload', side_effect=AssertionError('No complete snapshots')):
            result = search_trade(self.provider, self.query, TradeSide.BUY, fid=FID,
                                  clock=lambda: NOW, local_source=self.source)
            self.assertEqual(result.status, MarketStatus.INVALID_QUERY)

    def test_no_full_payload_no_cache_copy_and_fixed_clock(self):
        self.put(market())
        with patch.object(self.cache, 'all', side_effect=AssertionError('No cache copy')),              patch.object(MarketStore, '_payload', side_effect=AssertionError('No full snapshot')):
            self.assertEqual(search_trade(self.provider, self.query, TradeSide.BUY, fid=FID,
                clock=lambda: NOW, local_source=self.source).offers[0].market_id, 1)
        observer = SimpleNamespace(cache=self.cache)
        with patch.object(sqlite3, 'connect', side_effect=AssertionError('No GUI database work')):
            self.assertEqual(prepare_trade_source(observer, FID, 'Fixture System', 100).path, self.path)

    def test_cancellation_before_provider_and_during_pages(self):
        cancel = Event()
        cancel.set()
        result = search_trade(self.provider, self.query, TradeSide.BUY, cancel=cancel, local_source=self.source)
        self.assertEqual(result.status, MarketStatus.CANCELLED)
        self.provider.search_buy.assert_not_called()
        cancel.clear()
        self.put(market())
        original = MarketStore.query_current_candidates
        def cancelling(store, *args, **kwargs):
            page = original(store, *args, **kwargs)
            cancel.set()
            return page
        with patch.object(MarketStore, 'query_current_candidates', cancelling):
            result = search_trade(self.provider, self.query, TradeSide.BUY, cancel=cancel,
                                  clock=lambda: NOW, local_source=self.source)
        self.assertEqual(result.status, MarketStatus.CANCELLED)

    def test_pending_migration_wait_is_cancellable_without_gui_wait(self):
        cancel, entered = Event(), Event()
        ready = Future()
        original = ready.result
        def waiting(*args, **kwargs):
            entered.set()
            return original(*args, **kwargs)
        ready.result = waiting
        source = replace(self.source, ready=ready)
        with ThreadPoolExecutor(max_workers=1) as pool:
            task = pool.submit(search_trade, self.provider, self.query, TradeSide.BUY,
                               cancel=cancel, clock=lambda: NOW, local_source=source)
            self.assertTrue(entered.wait(2))
            cancel.set()
            self.assertEqual(task.result(timeout=2).status, MarketStatus.CANCELLED)

    def test_failed_activation_cannot_expose_existing_unmarked_store(self):
        from cmdrhelper.market_migration import MigrationError
        ready = Future()
        ready.set_exception(MigrationError('Store was never activated'))
        writer = SimpleNamespace(destination=self.path, ready=ready, activated=False)
        observer = SimpleNamespace(cache=self.cache, writer=writer)
        source = prepare_trade_source(observer, FID, 'Fixture System', 100)
        with self.assertRaises(MigrationError):
            search_trade(self.provider, self.query, TradeSide.BUY,
                         clock=lambda: NOW, local_source=source)
        # A later successful initialization permits a fresh search even though
        # the original startup future still records the previous failure.
        writer.activated = True
        self.assertIsNone(prepare_trade_source(observer, FID, 'Fixture System', 100).ready)

    def test_revision_change_rejects_mixed_pages(self):
        for mid in range(1, 502):
            self.store.record_observation(market(mid=mid))
        original = MarketStore.query_current_candidates
        def changing(store, *args, **kwargs):
            page = original(store, *args, **kwargs)
            if kwargs.get('cursor') is None:
                self.store.record_observation(market(mid=999))
            return page
        with patch.object(MarketStore, 'query_current_candidates', changing):
            with self.assertRaises(StaleReadError):
                search_trade(self.provider, self.query, TradeSide.BUY,
                             clock=lambda: NOW, local_source=self.source)


if __name__ == '__main__':
    unittest.main()
