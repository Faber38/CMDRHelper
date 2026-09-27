"""Transition regression tests: synthetic temp files, providers never use network."""
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from cmdrhelper.market_migration import MigrationError, migrate_market_cache
from cmdrhelper.market_store import MarketStore, market_storage_bytes
from cmdrhelper.market_writer import MarketWriteWorker
from cmdrhelper.observed_market_cache import ObservedMarketCache
from cmdrhelper.observed_market_observer import ObservedMarketObserver
from cmdrhelper.trade_market_source import prepare_trade_source
from cmdrhelper.trade_search import search_trade
from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus, TradeSide
from cmdrhelper.ui.observed_market_status import observed_market_text
from cmdrhelper.ui.recommendations_view import RecommendationWorker
from test_trade_recommendations import market, item, NOW, FID, BEER


class TransitionTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.path = self.root/'markets.db'
        self.cache = ObservedMarketCache(self.root/'observed_markets.json', clock=lambda: NOW)
        self.cache.put(market())
        self.cache.put(market(mid=2, rows=[item(sell=12000)]))
        self.before = self.cache.path.read_bytes()
        self.observer = ObservedMarketObserver(self.cache, clock=lambda: NOW, use_market_store=True)
        self.addCleanup(self.observer.close)
        self.provider = Mock()
        self.provider.search_buy.return_value = self.provider.search_sell.return_value = MarketSearchResult(MarketStatus.NO_RESULTS)
        self.query = MarketSearch(BEER.frontier_id, 'Fixture System', limit=100)

    def source(self):
        return prepare_trade_source(self.observer, FID, 'Fixture System', 100)

    def activate(self):
        self.observer.cache
        self.observer.writer.ready.result(5)

    def search(self, side=TradeSide.SELL, source=None):
        return search_trade(self.provider, self.query, side, fid=FID, clock=lambda: NOW,
                            local_source=source or self.source())

    def recommendations(self):
        worker = RecommendationWorker(self.cache.get_header(1), (), {}, 10, 0,
            self.query, self.provider, lambda: NOW, local_only=True, market_source=self.source())
        results = []
        worker.signals.finished.connect(results.append)
        worker.run()
        return results[-1]

    def test_pre_migration_fallback_all_trade_readers_then_retry(self):
        with patch('cmdrhelper.market_writer.migrate_market_cache', side_effect=MigrationError('synthetic disk full')):
            self.observer.cache
            with self.assertRaises(MigrationError):
                self.observer.writer.ready.result(5)
            for side in TradeSide:
                self.assertEqual(self.search(side).status, MarketStatus.OK)
            self.assertTrue(self.recommendations().rows)
            self.assertEqual(self.cache.storage_stats(), (2, len(self.before)))
        old_source = self.source()  # Failed ready future must not poison recovery.
        self.observer.writer.retry_initialization().result(5)
        self.assertEqual(self.search(source=old_source).status, MarketStatus.OK)
        self.assertIsNone(old_source.fallback_cache())
        self.assertEqual(self.cache.path.read_bytes(), self.before)

    def test_status_global_unique_ids_wal_cleanup_and_no_gui_sql(self):
        self.activate()
        writer = self.observer.writer
        writer.record(market(fid='OTHER', mid=1)).result(5)
        writer.record(market(fid='OTHER', mid=3, stamp=NOW-timedelta(days=700))).result(5)
        with MarketStore(self.path, read_only=True) as store:
            count, size = store.storage_stats()
            self.assertEqual(count, 3)
            self.assertGreater(Path(str(self.path)+'-wal').stat().st_size, 0)
            expected = sum(Path(str(self.path)+s).stat().st_size for s in ('', '-wal', '-shm'))
            self.assertEqual(size, expected)
        state = SimpleNamespace(observed_markets=self.observer)
        with patch.object(MarketStore, '__init__', side_effect=AssertionError('No GUI DB')):
            self.assertEqual(self.cache.storage_stats()[0], 3)
            self.assertIn('3', observed_market_text(state))
        writer.cleanup().result(5)
        self.assertEqual(self.cache.storage_stats()[0], 3)
        self.assertEqual(self.cache.storage_stats()[1], market_storage_bytes(self.path))
        writer.close()
        self.assertEqual(market_storage_bytes(self.path), self.path.stat().st_size)
        self.assertEqual(self.cache.path.read_bytes(), self.before)

    def test_active_readers_ignore_stale_json_and_projection_has_no_prices(self):
        self.activate()
        before = [self.search(side) for side in TradeSide]
        recommendations = self.recommendations()
        self.cache.path.write_text('deliberately invalid stale backup')
        with patch.object(self.cache, 'all', side_effect=AssertionError('No JSON fallback')):
            self.assertEqual([self.search(side) for side in TradeSide], before)
            self.assertEqual(self.recommendations().rows, recommendations.rows)
        self.assertTrue(all('commodities' not in row for row in self.cache._markets.values()))
        self.assertFalse(hasattr(self.cache, 'install_projection'))
        self.assertEqual(self.cache.path.read_text(), 'deliberately invalid stale backup')

    def test_read_error_after_activation_does_not_fallback(self):
        self.activate()
        with patch.object(MarketStore, '__init__', side_effect=OSError('synthetic database error')), \
                patch.object(self.cache, 'all', side_effect=AssertionError('No JSON fallback')):
            for side in TradeSide:
                with self.assertRaisesRegex(OSError, 'synthetic database error'):
                    self.search(side)
            with self.assertLogs('cmdrhelper.ui.recommendations_view', level='ERROR'):
                self.assertTrue(self.recommendations().partial)

    def test_restart_does_not_load_json_or_complete_database(self):
        self.activate()
        self.observer.close()
        observer = ObservedMarketObserver(clock=lambda: NOW, use_market_store=True)
        self.addCleanup(observer.close)
        with patch('cmdrhelper.observed_market_observer.cache_path', return_value=self.cache.path), \
                patch.object(ObservedMarketCache, '_load', side_effect=AssertionError('No JSON load')), \
                patch.object(MarketStore, '_payload', side_effect=AssertionError('No full DB load')):
            observer.cache
            observer.writer.ready.result(5)
        self.assertEqual(observer.cache.storage_stats()[0], 2)
        self.assertNotIn('commodities', observer.cache.get_header(1))

    def test_missing_or_corrupt_activated_database_on_restart_is_visible(self):
        self.activate()
        self.observer.close()
        for corrupt in (False, True):
            with self.subTest(corrupt=corrupt):
                if corrupt:
                    self.path.write_bytes(b'not a database')
                else:
                    self.path.unlink()
                observer = ObservedMarketObserver(clock=lambda: NOW, use_market_store=True)
                try:
                    with patch('cmdrhelper.observed_market_observer.cache_path', return_value=self.cache.path), \
                            patch.object(ObservedMarketCache, '_load', side_effect=AssertionError('No JSON load')):
                        observer.cache
                        with self.assertRaises(MigrationError):
                            observer.writer.ready.result(5)
                    source = prepare_trade_source(observer, FID, 'Fixture System', 100)
                    with self.assertRaises(MigrationError):
                        self.search(source=source)
                    text = observed_market_text(SimpleNamespace(observed_markets=observer))
                    self.assertTrue(text.startswith('markets.db: '), text)
                    self.assertEqual(self.cache.path.read_bytes(), self.before)
                finally:
                    observer.close()

    def test_activation_reads_only_bounded_migration_metadata(self):
        self.activate()
        self.observer.close()
        statements = []
        original = MarketStore.__init__
        def opened(store, *args, **kwargs):
            original(store, *args, **kwargs)
            store._con.set_trace_callback(statements.append)
        with patch.object(MarketStore, '__init__', opened):
            migrate_market_cache(self.cache.path, self.path, clock=lambda: NOW)
        metadata = [sql for sql in statements if 'SELECT key,value FROM store_meta' in sql]
        self.assertEqual(len(metadata), 1)
        self.assertIn('WHERE key IN', metadata[0])
        self.assertNotIn('current_order:', metadata[0])

    def test_cleanup_status_and_commit_notifications_follow_commits(self):
        notifications = []
        self.observer.on_changed = lambda: notifications.append(True)
        self.activate()
        count = len(notifications)
        self.observer.writer.record(market(mid=9)).result(5)
        self.assertGreater(len(notifications), count)
        self.assertEqual(self.cache.storage_stats()[0], 3)
        self.assertIsNotNone(self.cache.get_header(9))
        self.assertEqual(self.cache.path.read_bytes(), self.before)
