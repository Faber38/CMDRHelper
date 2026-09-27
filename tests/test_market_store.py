"""Isolated synthetic SQLite stores; no app paths, journals, settings or network."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import tempfile
import unittest
from threading import Event
from types import SimpleNamespace
from unittest.mock import patch

from cmdrhelper.commodity_master import lookup_by_symbol
from cmdrhelper.market_data import TradeSide
from cmdrhelper.market_store import (
    APPLICATION_ID, SCHEMA_VERSION, CleanupCancelled, CommodityRef, MarketStore,
    ObservationConflict, StaleReadError, StoreFormatError, encode_u64, decode_u64,
)

NOW = datetime(2026, 9, 26, 12, tzinfo=timezone.utc)
FID = 'F_SYNTHETIC_STORE'
BEER = lookup_by_symbol('Beer')
GOLD = lookup_by_symbol('Gold')
REF = CommodityRef(BEER.frontier_id, BEER.symbol)


def commodity(master=BEER, *, buy=100, sell=130, supply=500, demand=400):
    return dict(commodity_id=master.frontier_id, symbol=master.symbol,
                commander_buy_price=buy, commander_sell_price=sell, supply=supply, demand=demand)


def observation(mid=1, *, fid=FID, stamp=NOW, rows=None, **kwargs):
    value = dict(fid=fid, source='local_elite', market_id=mid, station_name='Synthetic Port',
                 system_name='Synthetic System', system_address=42, station_type='Coriolis',
                 observed_at=stamp.isoformat(), commodities=[commodity()] if rows is None else rows)
    value.update(kwargs)
    return value


class MarketStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'markets.db'
        self.now = NOW
        self.store = MarketStore(self.path, clock=lambda: self.now)
        self.addCleanup(self.store.close)

    def counts(self):
        s = self.store.get_stats()
        return s.stations, s.current_markets, s.observations, s.snapshots, s.commodity_rows, s.revision

    def test_schema_pragmas_and_empty_stats(self):
        self.assertEqual(self.counts(), (0, 0, 0, 0, 0, 0))
        for name, expected in (('foreign_keys', 1), ('journal_mode', 'wal'), ('synchronous', 2),
                               ('user_version', SCHEMA_VERSION), ('application_id', APPLICATION_ID)):
            self.assertEqual(self.store._con.execute('PRAGMA '+name).fetchone()[0], expected)
        tables = {r[0] for r in self.store._con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertEqual(tables, {'stations', 'commodity_keys', 'market_snapshots', 'commodity_observations',
                                  'market_observations', 'current_markets', 'store_meta'})
        stats = self.store.get_stats()
        self.assertGreater(stats.total_bytes, 0)
        self.assertEqual(stats.main_bytes, self.path.stat().st_size)
        self.assertFalse(hasattr(self.store, 'all'))

    def test_first_write_persisted_and_reads_are_owned(self):
        value = observation()
        result = self.store.record_observation(value)
        self.assertTrue(result.inserted)
        self.assertTrue(result.current_changed)
        self.assertFalse(result.snapshot_reused)
        self.assertEqual(self.store.get_current(1), value)
        read = self.store.get_current(1)
        read['commodities'].clear()
        value['commodities'][0]['demand'] = 99
        self.assertEqual(self.store.get_current(1), observation())
        self.assertFalse(self.store._con.in_transaction)

    def test_restart_read_only_persistence(self):
        self.store.record_observation(observation())
        self.store.close()
        with MarketStore(self.path, read_only=True, clock=lambda: NOW) as reopened:
            self.assertEqual(reopened.get_current(1), observation())
            self.assertEqual(reopened.get_stats().observations, 1)
            self.assertEqual(reopened._con.execute('PRAGMA foreign_keys').fetchone()[0], 1)
            with self.assertRaises(sqlite3.OperationalError):
                reopened.record_observation(observation(mid=2))

    def test_shared_markets_preserve_observer_and_distinct_market_ids(self):
        self.store.record_observation(observation(stamp=NOW-timedelta(minutes=1)))
        other = self.store.record_observation(observation(fid='OTHER', rows=[commodity(sell=999)]))
        self.store.record_observation(observation(mid=2))
        self.assertEqual(self.counts()[:2], (2, 2))
        self.assertEqual(self.store.get_current(1)['commodities'][0]['commander_sell_price'], 999)
        self.assertEqual(self.store.get_current(1)['fid'], 'OTHER')
        self.assertEqual(len(self.store.query_current_candidates(REF).items), 2)
        self.assertEqual(len(self.store.get_current_headers([1, 2], None)), 2)
        self.assertIsNone(self.store.get_observation(FID, other.observation_id))
        self.assertEqual(self.store.best_sell_prices([REF])[0].commodity.commander_sell_price, 999)

    def test_reobserve_identical_content_and_new_timestamp(self):
        old = self.store.record_observation(observation(stamp=NOW-timedelta(hours=2)))
        new = self.store.record_observation(observation())
        self.assertEqual(old.snapshot_id, new.snapshot_id)
        self.assertNotEqual(old.observation_id, new.observation_id)
        self.assertTrue(new.snapshot_reused)
        self.assertEqual(self.counts(), (1, 1, 2, 1, 1, 2))
        self.assertEqual(self.store.get_current(1)['observed_at'], NOW.isoformat())

    def test_changed_content_and_a_b_a(self):
        a = self.store.record_observation(observation(stamp=NOW-timedelta(hours=2)))
        b = self.store.record_observation(observation(stamp=NOW-timedelta(hours=1), rows=[commodity(demand=3)]))
        last = self.store.record_observation(observation())
        self.assertNotEqual(a.snapshot_id, b.snapshot_id)
        self.assertEqual(a.snapshot_id, last.snapshot_id)
        self.assertEqual(self.counts(), (1, 1, 3, 2, 2, 3))
        self.assertEqual(self.store.get_observation(FID, b.observation_id)['commodities'][0]['demand'], 3)
        self.assertEqual(self.store.get_current(1), observation())

    def test_old_observation_records_history_without_rewinding_current(self):
        new = self.store.record_observation(observation())
        old = self.store.record_observation(observation(stamp=NOW-timedelta(days=300), rows=[commodity(sell=999)]))
        self.assertFalse(old.current_changed)
        self.assertEqual(self.store.get_current_headers([1])[0].observation_id, new.observation_id)
        self.assertEqual(self.store.best_sell_prices([REF])[0].commodity.commander_sell_price, 130)
        history = self.store.best_sell_prices([REF], scope='history', max_age=None)[0]
        self.assertEqual(history.commodity.commander_sell_price, 130)
        self.assertEqual(history.scope, 'history')

    def test_same_time_same_content_is_idempotent(self):
        first = self.store.record_observation(observation())
        again = self.store.record_observation(observation())
        self.assertFalse(again.inserted)
        self.assertFalse(again.current_changed)
        self.assertEqual(first.observation_id, again.observation_id)
        self.assertEqual(first.revision, again.revision)
        self.assertEqual(self.counts(), (1, 1, 1, 1, 1, 1))

    def test_same_time_conflicts_do_not_change_anything(self):
        self.store.record_observation(observation())
        before = self.counts()
        for row in (observation(rows=[commodity(sell=999)]), observation(system_address=77),
                    observation(station_name='Another Port'), observation(station_type='FleetCarrier')):
            with self.subTest(row=row), self.assertRaises(ObservationConflict):
                self.store.record_observation(row)
            self.assertEqual(self.counts(), before)
            self.assertEqual(self.store.get_current(1), observation())

    def test_full_empty_snapshot_and_missing_commodity_never_revive(self):
        self.store.record_observation(observation(stamp=NOW-timedelta(hours=2), rows=[commodity(sell=999), commodity(GOLD)]))
        self.store.record_observation(observation(stamp=NOW-timedelta(hours=1), rows=[commodity(GOLD)]))
        candidate = self.store.query_current_candidates(REF).items[0]
        self.assertIsNone(candidate.commodity)
        self.assertEqual(candidate.header.commodity_count, 1)
        self.assertEqual(self.store.query_current_candidates(REF, side=TradeSide.SELL).items, ())
        self.assertEqual(self.store.best_sell_prices([REF]), ())
        self.assertEqual(len(self.store.best_sell_prices([REF], scope='history')), 1)
        self.store.record_observation(observation(rows=[]))
        self.assertEqual(self.store.get_current(1)['commodities'], [])
        self.assertEqual(self.store.query_current_candidates().items[0].header.commodity_count, 0)

    def test_zero_prices_supply_demand_and_direction(self):
        cases = ((0, 0, 0, 0), (100, 130, 0, 400), (100, 130, 500, 0), (100, 0, 500, 400))
        for mid, (buy, sell, supply, demand) in enumerate(cases, 1):
            self.store.record_observation(observation(mid=mid, rows=[commodity(buy=buy, sell=sell, supply=supply, demand=demand)]))
        raw = self.store.query_current_candidates(REF).items
        self.assertEqual((raw[0].commodity.commander_buy_price, raw[0].commodity.demand), (0, 0))
        buys = self.store.query_current_candidates(REF, side=TradeSide.BUY, min_quantity=500).items
        sells = self.store.query_current_candidates(REF, side=TradeSide.SELL, min_quantity=400).items
        self.assertEqual([c.header.market_id for c in buys], [3, 4])
        self.assertEqual([c.header.market_id for c in sells], [2])
        self.assertEqual(self.store.query_current_candidates(REF, side=TradeSide.BUY, min_quantity=501).items, ())

    def test_unsigned_extremes_and_exact_ordering(self):
        values = (0, 1, 2**53+1, 2**63-1, 2**63, 2**64-1)
        for value in values:
            self.assertEqual(decode_u64(encode_u64(value)), value)
        self.assertEqual(sorted(map(encode_u64, values)), list(map(encode_u64, values)))
        for mid, price in ((2**63, 2**63), (2**64-1, 2**64-1)):
            row = dict(commodity(), commodity_id=2**64-1, symbol='FutureUint64',
                       commander_buy_price=price, commander_sell_price=price, supply=2**64-1, demand=2**64-1)
            self.store.record_observation(observation(mid=mid, rows=[row], system_address=2**64-1))
            self.assertEqual(self.store.get_current(mid), observation(mid=mid, rows=[row], system_address=2**64-1))
        ref = CommodityRef(2**64-1, 'FutureUint64')
        best = self.store.best_sell_prices([ref], min_demand=2**64-1)[0]
        self.assertEqual(best.header.market_id, 2**64-1)
        self.assertEqual(best.commodity.commander_sell_price, 2**64-1)
        self.assertEqual(len(self.store.query_current_candidates(ref, side=TradeSide.BUY, min_quantity=2**64-1).items), 2)

    def test_unknown_commodities_with_and_without_ids_preserve_fields(self):
        rows = [dict(commodity(), commodity_id=None, symbol='$FutureOne_name;', localized_name='Zukunft', category='Future'),
                dict(commodity(), commodity_id=199999991, symbol='FutureTwo')]
        self.store.record_observation(observation(rows=rows))
        self.assertEqual(self.store.get_current(1)['commodities'], rows)
        self.assertEqual(self.store.query_current_candidates(CommodityRef(None, '$futureone_name;')).items[0].commodity.localized_name, 'Zukunft')
        self.assertEqual(self.store.query_current_candidates(CommodityRef(199999991, 'futuretwo')).items[0].commodity.symbol, 'FutureTwo')
        absent = self.store.query_current_candidates(CommodityRef(None, 'Unobserved')).items
        self.assertIsNone(absent[0].commodity)

    def test_order_independent_hash_and_optional_fields(self):
        rows = [commodity(), commodity(GOLD)]
        first = self.store.record_observation(observation(stamp=NOW-timedelta(hours=1), rows=rows))
        second = self.store.record_observation(observation(rows=list(reversed(rows))))
        self.assertEqual(first.snapshot_id, second.snapshot_id)
        value = observation(mid=2)
        del value['system_address'], value['station_type']
        self.store.record_observation(value)
        self.assertEqual(self.store.get_current(2), value)

    def test_age_boundaries_unlimited_and_clock_rollback(self):
        for mid, age in enumerate((timedelta(hours=24)-timedelta(microseconds=1), timedelta(hours=24),
                                    timedelta(hours=24)+timedelta(microseconds=1), timedelta(days=300)), 1):
            self.store.record_observation(observation(mid=mid, stamp=NOW-age))
        self.assertEqual([c.header.market_id for c in self.store.query_current_candidates().items], [1, 2])
        self.assertEqual(len(self.store.query_current_candidates(max_age=None).items), 4)
        self.assertEqual(self.counts()[0], 4)
        self.now = NOW-timedelta(days=400)
        self.assertEqual(self.store.query_current_candidates(max_age=None).items, ())
        self.assertEqual(self.store.get_history(FID, 1).items, ())
        self.assertEqual(self.store.best_sell_prices([REF], max_age=None), ())

    def test_timezone_microseconds_are_exact(self):
        stamp = NOW.astimezone(timezone(timedelta(hours=5, minutes=30)))-timedelta(microseconds=1)
        self.store.record_observation(observation(stamp=stamp))
        self.assertEqual(self.store.get_current_headers([1])[0].observed_at, NOW-timedelta(microseconds=1))

    def test_station_context_history_and_latest_system_filter(self):
        self.store.record_observation(observation(stamp=NOW-timedelta(hours=1), station_type='FleetCarrier'))
        self.store.record_observation(observation(system_name='Moved System', system_address=99, station_type='FleetCarrier'))
        self.assertEqual(len(self.store.query_current_candidates(system_address=42).items), 0)
        self.assertEqual(len(self.store.query_current_candidates(system_name='mOvEd SyStEm').items), 1)
        history = self.store.get_history(FID, 1).items
        self.assertEqual([h.system_address for h in history], [99, 42])
        self.assertEqual(history[0].snapshot_id, history[1].snapshot_id)

    def test_current_pagination_and_revision_guard(self):
        for mid in (5, 1, 3, 2, 4):
            self.store.record_observation(observation(mid=mid))
        first = self.store.query_current_candidates(REF, limit=2)
        second = self.store.query_current_candidates(REF, limit=2, cursor=first.next_cursor, expected_revision=first.revision)
        third = self.store.query_current_candidates(REF, limit=2, cursor=second.next_cursor)
        self.assertEqual([c.header.market_id for p in (first, second, third) for c in p.items], [1, 2, 3, 4, 5])
        self.assertIsNone(third.next_cursor)
        self.store.record_observation(observation(mid=6))
        with self.assertRaises(StaleReadError):
            self.store.query_current_candidates(cursor=first.next_cursor, expected_revision=first.revision)

    def test_history_pagination_since_and_read_one(self):
        for hours in range(5):
            self.store.record_observation(observation(stamp=NOW-timedelta(hours=hours)))
        first = self.store.get_history(FID, 1, limit=2)
        second = self.store.get_history(FID, 1, cursor=first.next_cursor, limit=2)
        third = self.store.get_history(FID, 1, cursor=second.next_cursor, limit=2)
        self.assertEqual([h.observed_at for p in (first, second, third) for h in p.items], [NOW-timedelta(hours=i) for i in range(5)])
        self.assertIsNone(third.next_cursor)
        self.assertEqual(len(self.store.get_history(FID, 1, since=NOW-timedelta(hours=2)).items), 3)
        self.assertIsNone(self.store.get_observation(FID, 99999))
        self.store.record_observation(observation(mid=2))
        with self.assertRaises(StaleReadError):
            self.store.get_history(FID, 1, expected_revision=first.revision)

    def test_best_prices_scope_since_quantity_and_latest_confirming_visit(self):
        self.store.record_observation(observation(stamp=NOW-timedelta(days=10), rows=[commodity(sell=999)]))
        self.store.record_observation(observation(stamp=NOW-timedelta(days=2), rows=[commodity(sell=999)]))
        self.store.record_observation(observation(rows=[commodity(sell=100)]))
        self.store.record_observation(observation(mid=2, rows=[commodity(sell=200, demand=1)]))
        self.assertEqual(self.store.best_sell_prices([REF])[0].header.market_id, 2)
        self.assertEqual(self.store.best_sell_prices([REF], min_demand=2)[0].commodity.commander_sell_price, 100)
        best = self.store.best_sell_prices([REF], scope='history', max_age=None, since=NOW-timedelta(days=3))[0]
        self.assertEqual(best.commodity.commander_sell_price, 999)
        self.assertEqual(best.header.observed_at, NOW-timedelta(days=2))
        self.assertEqual(self.store.best_sell_prices([CommodityRef(GOLD.frontier_id, GOLD.symbol)]), ())

    def test_invalid_input_is_rejected_without_writes(self):
        bad = [observation(fid='../bad'), observation(source='spansh'), observation(mid=0),
               observation(stamp=NOW+timedelta(microseconds=1)), observation(rows=[commodity(), commodity()]),
               observation(rows=[dict(commodity(), supply=True)]), observation(rows=[dict(commodity(), demand=2**64)])]
        for value in bad:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.store.record_observation(value)
        for value in (True, -1, 1.5, 2**64):
            with self.assertRaises(ValueError):
                encode_u64(value)
        self.assertEqual(self.counts(), (0, 0, 0, 0, 0, 0))

    def test_invalid_queries_and_empty_headers(self):
        self.assertEqual(self.store.get_current_headers([]), ())
        for kwargs in ({'limit': 0}, {'limit': 501}, {'cursor': True}, {'max_age': timedelta(seconds=-1)},
                       {'side': 'buy'}, {'side': TradeSide.BUY}, {'min_quantity': 0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                self.store.query_current_candidates(**kwargs)
        with self.assertRaises(ValueError):
            self.store.get_current_headers(range(1, 502))
        with self.assertRaises(ValueError):
            self.store.best_sell_prices([], scope='invalid')
        with self.assertRaises(ValueError):
            self.store.get_history(FID, 1, since=NOW.replace(tzinfo=None))
        self.assertFalse(self.store._con.in_transaction)

    def test_failure_mid_write_rolls_back_every_table(self):
        self.store.record_observation(observation())
        before = self.counts()
        self.store._con.execute('''CREATE TEMP TRIGGER fail_current BEFORE INSERT ON current_markets
            BEGIN SELECT RAISE(ABORT, 'synthetic write failure'); END''')
        unknown = dict(commodity(), commodity_id=None, symbol='NotCommitted')
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.record_observation(observation(mid=2, rows=[unknown]))
        self.assertEqual(self.counts(), before)
        self.assertEqual(self.store._con.execute("SELECT COUNT(*) FROM commodity_keys WHERE symbol_key='notcommitted'").fetchone()[0], 0)
        self.assertIsNone(self.store.get_current(2))
        self.store._con.execute('DROP TRIGGER fail_current')
        self.assertTrue(self.store.record_observation(observation(mid=2)).inserted)

    def test_deferred_commit_failure_rolls_back(self):
        # A deferred FK fails specifically at COMMIT, after all record writes.
        self.store._con.executescript('''CREATE TEMP TABLE parent(id INTEGER PRIMARY KEY);
            CREATE TEMP TABLE deferred_child(id INTEGER REFERENCES parent(id) DEFERRABLE INITIALLY DEFERRED);
            CREATE TEMP TRIGGER fail_commit AFTER INSERT ON main.market_observations
            BEGIN INSERT INTO deferred_child VALUES(123); END;''')
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.record_observation(observation())
        self.assertEqual(self.counts(), (0, 0, 0, 0, 0, 0))
        self.assertFalse(self.store._con.in_transaction)

    def test_foreign_keys_reject_wrong_fid_and_missing_commodity_parent(self):
        result = self.store.record_observation(observation())
        with self.assertRaises(sqlite3.IntegrityError):
            self.store._con.execute("UPDATE current_markets SET fid='OTHER'")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store._con.execute('UPDATE commodity_observations SET commodity_key=99999')
        with self.assertRaises(sqlite3.IntegrityError):
            self.store._con.execute('DELETE FROM market_snapshots WHERE snapshot_id=?', (result.snapshot_id,))
        self.assertEqual(self.store._con.execute('PRAGMA foreign_key_check').fetchall(), [])
        self.assertEqual(self.store._con.execute('PRAGMA integrity_check').fetchone()[0], 'ok')

    def test_thread_affinity_and_independent_worker_connection(self):
        self.store.record_observation(observation())
        def read_in_worker():
            with MarketStore(self.path, read_only=True, clock=lambda: NOW) as reader:
                return reader.get_current(1)
        with ThreadPoolExecutor(max_workers=1) as pool:
            with self.assertRaises(sqlite3.ProgrammingError):
                pool.submit(self.store.get_stats).result()
            self.assertEqual(pool.submit(read_in_worker).result(), observation())

    def test_wal_reader_does_not_see_uncommitted_write_and_busy_writer_fails(self):
        self.store.record_observation(observation())
        with MarketStore(self.path, clock=lambda: NOW, busy_timeout_ms=1) as second:
            with self.store._transaction(write=True):
                self.store._con.execute("UPDATE store_meta SET value='99' WHERE key='revision'")
                self.assertEqual(second.get_stats().revision, 1)
                with self.assertRaises(sqlite3.OperationalError):
                    second.record_observation(observation(mid=2))
            self.assertEqual(second.get_stats().revision, 99)
            self.assertTrue(second.record_observation(observation(mid=2)).inserted)

    def test_missing_read_only_corrupt_and_foreign_databases_are_not_replaced(self):
        missing = self.path.parent/'missing.db'
        with self.assertRaises(sqlite3.OperationalError):
            MarketStore(missing, read_only=True)
        self.assertFalse(missing.exists())
        foreign = self.path.parent/'foreign.db'
        with sqlite3.connect(foreign) as con:
            con.execute('CREATE TABLE sentinel(value TEXT)')
            con.execute('PRAGMA user_version=20')
        before = foreign.read_bytes()
        with self.assertRaises(StoreFormatError):
            MarketStore(foreign)
        self.assertEqual(foreign.read_bytes(), before)
        corrupt = self.path.parent/'corrupt.db'
        corrupt.write_bytes(b'not a database')
        with self.assertRaises(sqlite3.DatabaseError):
            MarketStore(corrupt)
        self.assertEqual(corrupt.read_bytes(), b'not a database')

    def test_sqlite_full_rolls_back_without_partial_market(self):
        pages = self.store._con.execute('PRAGMA page_count').fetchone()[0]
        self.store._con.execute(f'PRAGMA max_page_count={pages}')
        rows = [dict(commodity(), commodity_id=None, symbol=f'Future{i}',
                     localized_name='L'*512, category='C'*512) for i in range(350)]
        with self.assertRaises(sqlite3.OperationalError):
            self.store.record_observation(observation(rows=rows))
        self.assertEqual(self.counts(), (0, 0, 0, 0, 0, 0))
        self.assertEqual(self.store._con.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_get_current_uses_one_read_transaction_and_no_write(self):
        self.store.record_observation(observation())
        statements = []
        self.store._con.set_trace_callback(statements.append)
        try:
            self.store.get_current(1)
        finally:
            self.store._con.set_trace_callback(None)
        self.assertEqual(sum(s == 'BEGIN' for s in statements), 1)
        self.assertEqual(sum(s == 'COMMIT' for s in statements), 1)
        self.assertFalse(any(s.startswith(('UPDATE', 'INSERT', 'DELETE')) for s in statements))

    def cleanup_worker(self, configure=None, cancel=None):
        def work():
            with MarketStore(self.path, clock=lambda: self.now) as worker:
                if configure:
                    configure(worker)
                return worker.cleanup(cancel=cancel)
        with ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(work).result()

    def test_cleanup_keeps_two_year_old_shared_last_stand(self):
        for fid in (FID, 'OTHER'):
            self.store.record_observation(observation(fid=fid, stamp=NOW-timedelta(days=731)))
            self.store.record_observation(observation(fid=fid, stamp=NOW-timedelta(days=730),
                                                      rows=[commodity(sell=800)]))
        result = self.cleanup_worker()
        self.assertEqual((result.observations_removed, result.snapshots_removed), (3, 3))
        for fid in (FID, 'OTHER'):
            self.assertEqual(self.store.get_current(1, None)['commodities'][0]['commander_sell_price'], 800)
            self.assertIsNone(self.store.get_current(1, timedelta(days=7)))
            self.assertEqual(self.store.get_history(fid, 1).items, ())
            self.assertEqual(self.store.best_sell_prices([REF], scope='history', max_age=None), ())
            quote = self.store.best_sell_prices([REF], scope='last_known')[0]
            self.assertEqual(quote.scope, 'last_known')
            self.assertEqual(quote.commodity.commander_sell_price, 800)

    def test_cleanup_single_visit_two_years_ago_and_noop_revision(self):
        self.store.record_observation(observation(stamp=NOW-timedelta(days=730)))
        before = self.counts()
        self.assertEqual(self.cleanup_worker().observations_removed, 0)
        self.assertEqual(self.counts(), before)
        self.assertIsNotNone(self.store.get_current(1, None))

    def test_cleanup_boundary_recent_history_and_orphan_commodity_keys(self):
        old = self.store.record_observation(observation(stamp=NOW-timedelta(days=30, microseconds=1),
                                                        rows=[commodity(GOLD)]))
        for age in (30, 20, 1):
            self.store.record_observation(observation(stamp=NOW-timedelta(days=age),
                                                      rows=[commodity(sell=age)]))
        before = self.counts()
        # Reads/search age changes never delete data.
        self.store.get_history(FID, 1)
        self.store.query_current_candidates(max_age=timedelta(days=7))
        self.store.query_current_candidates(max_age=None)
        self.assertEqual(self.counts(), before)
        result = self.cleanup_worker()
        self.assertEqual((result.observations_removed, result.snapshots_removed,
                          result.commodity_rows_removed, result.commodity_keys_removed), (1, 1, 1, 1))
        self.assertIsNone(self.store.get_observation(FID, old.observation_id))
        self.assertEqual(len(self.store.get_history(FID, 1).items), 3)
        self.assertEqual(self.store._con.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_cleanup_a_b_a_preserves_shared_referenced_snapshot(self):
        a = self.store.record_observation(observation(stamp=NOW-timedelta(days=40)))
        b = self.store.record_observation(observation(stamp=NOW-timedelta(days=20), rows=[commodity(sell=999)]))
        last = self.store.record_observation(observation(stamp=NOW-timedelta(days=5)))
        self.assertEqual(a.snapshot_id, last.snapshot_id)
        result = self.cleanup_worker()
        self.assertEqual((result.observations_removed, result.snapshots_removed), (1, 0))
        self.assertEqual(self.store.get_current_headers([1], None)[0].snapshot_id, a.snapshot_id)
        self.assertIsNotNone(self.store.get_observation(FID, b.observation_id))
        self.now += timedelta(days=40)
        result = self.cleanup_worker()
        self.assertEqual((result.observations_removed, result.snapshots_removed), (1, 1))
        self.assertEqual(self.store.get_current(1, None)['commodities'], [commodity()])

    def seed_cleanup(self):
        self.store.record_observation(observation(stamp=NOW-timedelta(days=40), rows=[commodity(GOLD)]))
        self.store.record_observation(observation())
        return self.counts()

    def test_cleanup_failure_rolls_back_observations_and_snapshots(self):
        before = self.seed_cleanup()
        def configure(worker):
            worker._con.execute("""CREATE TEMP TRIGGER fail_cleanup BEFORE DELETE ON market_snapshots
                BEGIN SELECT RAISE(ABORT, 'synthetic failure'); END""")
        with self.assertRaises(sqlite3.IntegrityError):
            self.cleanup_worker(configure)
        self.assertEqual(self.counts(), before)
        self.assertEqual(self.store._con.execute('PRAGMA foreign_key_check').fetchall(), [])
        self.assertEqual(self.store.get_current(1), observation())

    def test_cleanup_cancellation_before_and_during_transaction_rolls_back(self):
        before = self.seed_cleanup()
        cancel = Event()
        cancel.set()
        with self.assertRaises(CleanupCancelled):
            self.cleanup_worker(cancel=cancel)
        cancel.clear()
        def configure(worker):
            worker._con.create_function('cancel_cleanup', 0, lambda: cancel.set())
            worker._con.execute("""CREATE TEMP TRIGGER cancel_cleanup AFTER DELETE ON market_observations
                BEGIN SELECT cancel_cleanup(); END""")
        with self.assertRaises(CleanupCancelled):
            self.cleanup_worker(configure, cancel)
        self.assertEqual(self.counts(), before)
        self.assertEqual(self.store._con.execute('PRAGMA integrity_check').fetchone()[0], 'ok')

    def test_cleanup_rejects_gui_thread_before_transaction(self):
        app = SimpleNamespace(thread=lambda: 'GUI')
        qt = SimpleNamespace(QCoreApplication=SimpleNamespace(instance=lambda: app),
                             QThread=SimpleNamespace(currentThread=lambda: 'GUI'))
        with patch.dict('sys.modules', {'PySide6.QtCore': qt}):
            with self.assertRaisesRegex(RuntimeError, 'GUI'):
                self.store.cleanup()
        self.assertFalse(self.store._con.in_transaction)

    def test_cleanup_invalidates_page_revision(self):
        self.seed_cleanup()
        page = self.store.query_current_candidates()
        self.cleanup_worker()
        with self.assertRaises(StaleReadError):
            self.store.query_current_candidates(expected_revision=page.revision)


if __name__ == '__main__':
    unittest.main()
