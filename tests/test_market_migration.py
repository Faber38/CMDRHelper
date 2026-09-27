"""Only temporary synthetic JSON/SQLite files; no app state or network."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
from pathlib import Path
import sqlite3
import tempfile
from threading import Event, get_ident
import unittest
from unittest.mock import patch

from cmdrhelper.market_migration import migrate_market_cache, MigrationError, MigrationCancelled
from cmdrhelper.market_store import MarketStore
from cmdrhelper.market_writer import MarketWriteWorker
from cmdrhelper.observed_market_cache import ObservedMarketCache
from test_market_store import NOW, FID, commodity, observation


class TemporaryMarketFixture(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source, self.destination = self.root/'observed_markets.json', self.root/'markets.db'

    def write(self, rows):
        self.source.write_text(json.dumps(dict(version=1, markets=rows)), encoding='utf-8')
        return self.source.read_bytes()

    def migrate(self, **kwargs):
        return migrate_market_cache(self.source, self.destination, clock=lambda: NOW, **kwargs)


class MigrationTests(TemporaryMarketFixture):
    def test_missing_and_empty_market_list(self):
        result = self.migrate()
        self.assertEqual(result.markets, 0)
        self.assertFalse(self.source.exists())
        with tempfile.TemporaryDirectory() as directory:
            source, dest = Path(directory)/'source.json', Path(directory)/'markets.db'
            source.write_bytes(b'{"version":1,"markets":[]}')
            self.assertEqual(migrate_market_cache(source, dest).markets, 0)
            self.assertEqual(source.read_bytes(), b'{"version":1,"markets":[]}')

    def test_all_fids_old_stands_u64_and_exact_legacy_semantics(self):
        rows = [observation(stamp=NOW-timedelta(days=730)),
                observation(fid='OTHER', mid=1, rows=[]),
                observation(mid=2**64-1, system_address=2**64-1,
                            rows=[commodity(buy=0, sell=2**64-1, supply=0, demand=2**64-1)]),
                observation(mid=3, stamp=NOW+timedelta(days=1))]
        before = self.write(rows)
        legacy = ObservedMarketCache(self.source, clock=lambda: NOW)
        result = self.migrate()
        self.assertEqual(result.markets, 4)
        with MarketStore(self.destination, read_only=True, clock=lambda: NOW) as store:
            for row in rows:
                oid = store._con.execute('SELECT observation_id FROM market_observations WHERE fid=? AND market_id=?',
                    (row['fid'], row['market_id'].to_bytes(8, 'big'))).fetchone()[0]
                self.assertEqual(store.get_observation(row['fid'], oid), row)
            self.assertEqual(store.get_current(1, None)['fid'], 'OTHER')
            self.assertEqual(store.get_stats().current_markets, 2)
            self.assertEqual(store.get_stats().observations, 4)
            self.assertEqual(store._con.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            self.assertEqual(store._con.execute("SELECT value FROM store_meta WHERE key='migration_complete'").fetchone()[0], '1')
            self.assertTrue(store._con.execute("SELECT 1 FROM sqlite_master WHERE name='sqlite_stat1'").fetchone())
        self.assertEqual(self.source.read_bytes(), before)

    def test_invalid_source_rejected_completely(self):
        invalid = (b'', b'{', b'{"version":1,"version":1,"markets":[]}',
                   b'{"version":true,"markets":[]}', b'{"version":1,"markets":[NaN]}',
                   json.dumps(dict(version=1, markets=[observation(), observation()])).encode(),
                   json.dumps(dict(version=1, markets=[observation(), {}])).encode())
        for raw in invalid:
            with self.subTest(raw=raw):
                self.source.write_bytes(raw)
                with self.assertRaises(MigrationError):
                    self.migrate()
                self.assertFalse(self.destination.exists())
                self.assertEqual(self.source.read_bytes(), raw)
                self.assertEqual(list(self.root.glob('.market-migration-*')), [])

    def test_restart_is_idempotent_and_does_not_reimport_backup(self):
        before = self.write([observation()])
        self.assertTrue(self.migrate().imported)
        with MarketStore(self.destination, clock=lambda: NOW) as store:
            store.record_observation(observation(mid=2))
        with patch('cmdrhelper.market_migration._source', side_effect=AssertionError('No JSON reread')):
            self.assertFalse(self.migrate().imported)
        with MarketStore(self.destination, clock=lambda: NOW) as store:
            self.assertEqual(store.get_stats().observations, 2)
        self.assertEqual(self.source.read_bytes(), before)

    def test_cancel_during_import_never_activates_and_restart_succeeds(self):
        before = self.write([observation(mid=1), observation(mid=2)])
        cancel = Event()
        original = MarketStore.record_observation
        def record(store, value, **kwargs):
            result = original(store, value, **kwargs)
            cancel.set()
            return result
        with patch.object(MarketStore, 'record_observation', record):
            with self.assertRaises(MigrationCancelled):
                self.migrate(cancel=cancel)
        self.assertFalse(self.destination.exists())
        self.assertEqual(self.source.read_bytes(), before)
        self.assertTrue(self.migrate().imported)

    def test_write_and_publish_failures_preserve_source_and_retry(self):
        before = self.write([observation()])
        for target in ('cmdrhelper.market_migration.MarketStore.record_observation',
                       'cmdrhelper.market_migration.os.link'):
            with patch(target, side_effect=OSError('synthetic disk failure')):
                with self.assertRaises(MigrationError):
                    self.migrate()
            self.assertFalse(self.destination.exists())
            self.assertEqual(self.source.read_bytes(), before)
        self.assertTrue(self.migrate().imported)

    def test_existing_unmarked_or_foreign_database_not_overwritten(self):
        self.write([observation()])
        with MarketStore(self.destination):
            pass
        before = self.destination.read_bytes()
        with self.assertRaisesRegex(MigrationError, 'completed migration'):
            self.migrate()
        self.assertEqual(self.destination.read_bytes(), before)

    def test_verification_detects_source_change_and_semantic_mismatch(self):
        self.write([observation()])
        original = MarketStore.record_observation
        def changed(store, row, **kw):
            result = original(store, row, **kw)
            self.write([observation(mid=2)])
            return result
        with patch.object(MarketStore, 'record_observation', changed):
            with self.assertRaisesRegex(MigrationError, 'changed during'):
                self.migrate()
        self.assertFalse(self.destination.exists())
        with patch.object(MarketStore, 'get_observation', return_value=observation(mid=999)):
            with self.assertRaisesRegex(MigrationError, 'content differs'):
                self.migrate()
        self.assertFalse(self.destination.exists())

    def test_two_migrators_never_overwrite_destination(self):
        self.write([observation()])
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [f.result() for f in (pool.submit(self.migrate), pool.submit(self.migrate))]
        self.assertEqual(sum(r.imported for r in results), 1)


class WriterTests(TemporaryMarketFixture):
    def worker(self, **kwargs):
        worker = MarketWriteWorker(self.source, self.destination, clock=lambda: NOW, **kwargs)
        self.addCleanup(worker.close)
        return worker

    def test_observation_during_migration_order_commit_and_read_projection(self):
        before = self.write([observation(stamp=NOW-timedelta(days=2))])
        cache = ObservedMarketCache(self.source, clock=lambda: NOW)
        entered, release = Event(), Event()
        from cmdrhelper.market_writer import migrate_market_cache as original
        def blocked(*args, **kwargs):
            entered.set()
            if not release.wait(5):
                raise RuntimeError('test release timeout')
            return original(*args, **kwargs)
        calls = []
        def committed(value):
            with MarketStore(self.destination, read_only=True, clock=lambda: NOW) as reader:
                self.assertIsNotNone(reader.get_current(value['market_id'], None))
            calls.append((value['observed_at'], get_ident()))
            cache.apply_committed_header(value)
        try:
            with patch('cmdrhelper.market_writer.migrate_market_cache', blocked):
                worker = self.worker(on_loaded=cache.install_headers, on_committed=committed)
                self.assertTrue(entered.wait(5))
                values = [observation(stamp=NOW-timedelta(seconds=10-i), rows=[commodity(sell=i)]) for i in range(10)]
                futures = [worker.record(value) for value in values]
                self.assertFalse(any(f.done() for f in futures))
                self.assertEqual(cache.get(FID, 1, None)['commodities'][0]['commander_sell_price'], 130)
                release.set()
                for f in futures:
                    self.assertTrue(f.result(timeout=10).inserted)
        finally:
            release.set()
        self.assertEqual([c[0] for c in calls], [v['observed_at'] for v in values])
        self.assertTrue(all(c[1] != get_ident() for c in calls))
        self.assertEqual(cache.get_header(1), {k:v for k,v in values[-1].items() if k != 'commodities'})
        with MarketStore(self.destination, read_only=True, clock=lambda: NOW) as reader:
            self.assertEqual(reader.get_current(1), values[-1])
        self.assertEqual(self.source.read_bytes(), before)
        self.assertFalse(worker.record(values[-1]).result(timeout=5).inserted)
        worker.close()
        second = self.worker(on_loaded=cache.install_headers)
        second.ready.result(timeout=5)
        self.assertEqual(cache.get_header(1), {k:v for k,v in values[-1].items() if k != 'commodities'})
        with MarketStore(self.destination, read_only=True, clock=lambda: NOW) as reader:
            self.assertEqual(reader.get_current(1), values[-1])

    def test_shutdown_drains_pending_write_and_rejects_new_admission(self):
        worker = self.worker()
        worker.ready.result(timeout=5)
        entered, release = Event(), Event()
        original = MarketStore.record_observation
        def blocked(store, value, **kwargs):
            entered.set()
            if not release.wait(5):
                raise RuntimeError('test release timeout')
            return original(store, value, **kwargs)
        try:
            with patch.object(MarketStore, 'record_observation', blocked):
                first = worker.record(observation())
                self.assertTrue(entered.wait(5))
                second = worker.record(observation(mid=2))
                with ThreadPoolExecutor(max_workers=1) as pool:
                    closed = pool.submit(worker.close)
                    self.assertFalse(first.done())
                    self.assertFalse(second.done())
                    release.set()
                    self.assertTrue(closed.result(timeout=10))
        finally:
            release.set()
        self.assertTrue(first.result().inserted)
        self.assertTrue(second.result().inserted)
        with self.assertRaises(RuntimeError):
            worker.record(observation(mid=3))
        with MarketStore(self.destination, read_only=True) as store:
            self.assertEqual(store.get_stats().current_markets, 2)

    def test_failed_migration_keeps_legacy_projection_and_retry_recovers(self):
        before = self.write([observation()])
        cache = ObservedMarketCache(self.source, clock=lambda: NOW)
        with patch('cmdrhelper.market_writer.migrate_market_cache', side_effect=MigrationError('disk full')):
            worker = self.worker(on_loaded=cache.install_headers, on_committed=cache.apply_committed_header)
            with self.assertRaises(MigrationError):
                worker.ready.result(timeout=5)
            with self.assertRaises(MigrationError):
                worker.record(observation(mid=2)).result(timeout=5)
            self.assertEqual(worker.status, 'migration_error')
            self.assertEqual(cache.get_header(1), {k:v for k,v in observation().items() if k != 'commodities'})
        worker.retry_initialization().result(timeout=5)
        worker.record(observation(mid=2)).result(timeout=5)
        self.assertIsNotNone(cache.get_header(2))
        self.assertEqual(self.source.read_bytes(), before)

    def test_commit_failure_never_updates_projection_or_confirms_success(self):
        cache = ObservedMarketCache(self.source, clock=lambda: NOW)
        worker = self.worker(on_loaded=cache.install_headers, on_committed=cache.apply_committed_header)
        worker.ready.result(timeout=5)
        # Independent connection installs a persistent trigger in the temp DB.
        with sqlite3.connect(self.destination) as con:
            con.execute("""CREATE TRIGGER fail_write BEFORE INSERT ON market_observations
                           BEGIN SELECT RAISE(ABORT, 'synthetic disk error'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            worker.record(observation()).result(timeout=5)
        self.assertIsNone(cache.get_header(1))
        with sqlite3.connect(self.destination) as con:
            con.execute('DROP TRIGGER fail_write')
        worker.record(observation()).result(timeout=5)
        self.assertEqual(cache.get_header(1), {k:v for k,v in observation().items() if k != 'commodities'})

    def test_explicit_worker_cleanup_protects_all_current_stands(self):
        worker = self.worker()
        worker.ready.result(timeout=5)
        for fid in (FID, 'OTHER'):
            for days in (731, 730):
                worker.record(observation(fid=fid, stamp=NOW-timedelta(days=days),
                                          rows=[commodity(sell=days)])).result(timeout=5)
        result = worker.cleanup().result(timeout=5)
        self.assertEqual(result.observations_removed, 3)
        with MarketStore(self.destination, read_only=True, clock=lambda: NOW) as store:
            self.assertEqual(store.get_stats().current_markets, 1)
            for fid in (FID, 'OTHER'):
                self.assertEqual(store.get_current(1, None)['commodities'][0]['commander_sell_price'], 730)
        self.assertFalse(self.source.exists())

    def test_failure_is_not_hidden_by_later_success_at_shutdown(self):
        worker = self.worker()
        worker.ready.result(timeout=5)
        with patch.object(MarketStore, 'record_observation', side_effect=sqlite3.OperationalError('disk error')):
            failed = worker.record(observation())
            with self.assertRaises(sqlite3.OperationalError):
                failed.result(timeout=5)
        worker.record(observation(mid=2)).result(timeout=5)
        self.assertFalse(worker.close())
        self.assertIn('disk error', worker.last_error)

    def test_commit_constraint_failure_does_not_emit_confirmation(self):
        published = []
        worker = self.worker(on_committed=published.append)
        worker.ready.result(timeout=5)
        with sqlite3.connect(self.destination) as con:
            con.execute('PRAGMA foreign_keys=ON')
            con.execute('CREATE TABLE test_parent(id INTEGER PRIMARY KEY)')
            con.execute("""CREATE TABLE test_child(id INTEGER REFERENCES test_parent(id)
                           DEFERRABLE INITIALLY DEFERRED)""")
            con.execute("""CREATE TRIGGER deferred_failure AFTER INSERT ON market_observations
                           BEGIN INSERT INTO test_child VALUES(99); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            worker.record(observation()).result(timeout=5)
        self.assertEqual(published, [])
        with MarketStore(self.destination, read_only=True) as store:
            self.assertEqual(store.get_stats().observations, 0)
            self.assertEqual(store._con.execute('PRAGMA foreign_key_check').fetchall(), [])


class ObserverWriterTests(unittest.TestCase):
    def setUp(self):
        import os
        from cmdrhelper.observed_market_observer import ObservedMarketObserver
        from test_observed_market_cache import NOW as JOURNAL_NOW, FID as JOURNAL_FID
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.now, self.fid = JOURNAL_NOW, JOURNAL_FID
        self.journal = self.root/'Journal.2026-01-02T110000.01.log'
        self.journal.write_text(json.dumps(dict(event='LoadGame', FID=self.fid))+'\n')
        self.cache = ObservedMarketCache(self.root/'cache'/'observed_markets.json', clock=lambda: self.now)
        self.cache.path.parent.mkdir()
        self.cache.path.write_bytes(b'{"version":1,"markets":[]}')
        self.before = self.cache.path.read_bytes()
        self.observer = ObservedMarketObserver(self.cache, clock=lambda: self.now, use_market_store=True)
        self.addCleanup(self.observer.close)
        self.observer.set_folder(self.root)
        self.observer.writer.ready.result(timeout=5)

    def capture(self):
        import os
        from test_observed_market_cache import event, sidecar
        with self.journal.open('a') as stream:
            stream.write(json.dumps(event(self.now))+'\n')
        market = self.root/'Market.json'
        market.write_text(json.dumps(sidecar(self.now)))
        os.utime(market, (self.now.timestamp(), self.now.timestamp()))
        return self.observer.consume([self.journal])

    def test_observer_queue_is_not_success_and_readers_see_only_commit(self):
        entered, release = Event(), Event()
        original = MarketStore.record_observation
        def blocked(store, value, **kw):
            entered.set()
            if not release.wait(5):
                raise RuntimeError('test release timeout')
            return original(store, value, **kw)
        try:
            with patch.object(MarketStore, 'record_observation', blocked):
                self.assertFalse(self.capture())
                self.assertTrue(entered.wait(5))
                self.assertIsNone(self.cache.get_header(123))
                release.set()
                self.observer._writes[0][1].result(timeout=5)
        finally:
            release.set()
        self.assertTrue(self.observer.consume([self.journal]))
        self.assertIsNotNone(self.cache.get_header(123))
        self.assertNotIn('commodities',self.cache.get_header(123))
        self.assertEqual(self.cache.path.read_bytes(), self.before)
        # The existing trade search still consumes the old cache API.
        from unittest.mock import Mock
        from cmdrhelper.commodity_master import lookup_by_symbol
        from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus, TradeSide
        from cmdrhelper.trade_search import search_trade
        provider = Mock()
        provider.search_buy.return_value = MarketSearchResult(MarketStatus.OK, ())
        query = MarketSearch(lookup_by_symbol('Beer').frontier_id, 'Fixture System')
        from cmdrhelper.trade_market_source import prepare_trade_source
        result = search_trade(provider, query, TradeSide.BUY, fid=self.fid, clock=lambda:self.now,
            local_source=prepare_trade_source(self.observer,self.fid,'Fixture System',None))
        self.assertEqual(result.status, MarketStatus.NO_RESULTS)
        self.assertFalse(self.cache.put(observation()))

    def test_observer_failed_write_retries_same_captured_observation(self):
        with patch.object(MarketStore, 'record_observation', side_effect=sqlite3.OperationalError('locked')):
            self.assertFalse(self.capture())
            with self.assertRaises(sqlite3.OperationalError):
                self.observer._writes[0][1].result(timeout=5)
        self.assertFalse(self.observer.consume([self.journal]))
        self.observer._writes[0][1].result(timeout=5)
        self.assertTrue(self.observer.consume([self.journal]))
        self.assertIsNotNone(self.cache.get_header(123))
        self.assertEqual(self.cache.path.read_bytes(), self.before)

    def test_observer_fast_captures_keep_futures_after_pending_changes(self):
        entered, release = Event(), Event()
        original = MarketStore.record_observation
        def blocked(store, value, **kw):
            entered.set()
            if not release.wait(5):
                raise RuntimeError('test release timeout')
            return original(store, value, **kw)
        try:
            with patch.object(MarketStore, 'record_observation', blocked):
                self.assertFalse(self.capture())
                self.assertTrue(entered.wait(5))
                self.now += timedelta(seconds=1)
                self.assertFalse(self.capture())
                self.assertEqual(len(self.observer._writes), 2)
                futures = [f for _, f in self.observer._writes]
                release.set()
                for future in futures:
                    future.result(timeout=5)
        finally:
            release.set()
        self.assertTrue(self.observer.consume([self.journal]))
        self.assertEqual(self.cache.get_header(123)['observed_at'], self.now.isoformat())
        with MarketStore(self.root/'cache'/'markets.db', read_only=True, clock=lambda: self.now) as store:
            self.assertEqual(store.get_stats().observations, 2)


if __name__ == '__main__':
    unittest.main()
