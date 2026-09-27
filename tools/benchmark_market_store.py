"""Offline reproducible prototype benchmark; databases exist only in TemporaryDirectory.

Run from the repository root:
    PYTHONDONTWRITEBYTECODE=1 venv/bin/python tools/benchmark_market_store.py > /tmp/market-store-results.json
Each size runs in a fresh subprocess. No application settings or productive paths.
"""
import argparse
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import platform
import resource
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from cmdrhelper.commodity_master import all_commodities
from cmdrhelper.market_data import TradeSide
from cmdrhelper.market_store import CommodityRef, MarketStore

NOW = datetime(2026, 9, 26, 12, tzinfo=timezone.utc)
FID = 'F_SYNTHETIC_BENCHMARK'
MASTERS = all_commodities()[:350]
REF = CommodityRef(MASTERS[170].frontier_id, MASTERS[170].symbol)


def observation(mid, stamp, variant=0):
    return dict(fid=FID, source='local_elite', market_id=mid,
                station_name=f'Synthetic Port {mid}', system_name=f'Synthetic System {mid // 5}',
                system_address=2**63 + mid // 5, station_type='Coriolis',
                observed_at=stamp.isoformat(),
                commodities=[dict(commodity_id=c.frontier_id, symbol=c.symbol,
                    commander_buy_price=(100 + i*79 + mid % 100) if i % 3 != 0 else 0,
                    commander_sell_price=(120 + i*81 + mid % 100 + variant) if i % 4 != 0 else 0,
                    supply=(500 + mid % 300 + variant) if i % 3 != 0 else 0,
                    demand=(700 + mid % 200 + variant) if i % 4 != 0 else 0,
                    category=c.category) for i, c in enumerate(MASTERS)])


def measure(operation, repeats=7):
    durations = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        operation()
        durations.append((time.perf_counter_ns() - start) / 1_000_000)
    return dict(median_ms=statistics.median(durations), max_ms=max(durations), repetitions=repeats)


def rss_mib():
    # Linux current RSS; ru_maxrss below includes interpreter/SQLite/native memory.
    status = Path('/proc/self/status')
    if not status.exists():
        return None
    for line in status.read_text().splitlines():
        if line.startswith('VmRSS:'):
            return int(line.split()[1]) / 1024
    return None


def run(size):
    baseline = rss_mib()
    with tempfile.TemporaryDirectory(prefix='cmdrhelper-market-bench-') as directory:
        path = Path(directory) / 'markets.db'
        store = MarketStore(path, clock=lambda: NOW)
        started = time.perf_counter()
        for mid in range(1, size+1):
            if mid % 10 == 0:
                for days, variant in ((21, 3), (14, 2), (7, 1), (6, 1)):
                    store.record_observation(observation(mid, NOW-timedelta(days=days), variant))
            store.record_observation(observation(mid, NOW-timedelta(hours=1 if mid % 2 else 48)))
        setup_seconds = time.perf_counter() - started
        initial = asdict(store.get_stats())
        setup_rss = rss_mib()
        store.close()
        checkpoint_bytes = path.stat().st_size

        def reopen():
            with MarketStore(path, clock=lambda: NOW, read_only=True):
                pass
        timings = {'open': measure(reopen)}
        store = MarketStore(path, clock=lambda: NOW)
        plans = {}

        def explain(name, operation):
            statements = []
            store._con.set_trace_callback(statements.append)
            try:
                operation()
            finally:
                store._con.set_trace_callback(None)
            selects = list(dict.fromkeys(s for s in statements if s.lstrip().upper().startswith('SELECT')))
            plans[name] = [
                dict(sql=sql, plan=[r['detail'] for r in store._con.execute('EXPLAIN QUERY PLAN '+sql)])
                for sql in selects]

        def pages(**kwargs):
            cursor, revision, count = None, None, 0
            while True:
                page = store.query_current_candidates(limit=500, cursor=cursor,
                    expected_revision=revision, **kwargs)
                revision = page.revision
                count += len(page.items)
                cursor = page.next_cursor
                if cursor is None:
                    return count

        operations = dict(
            station_read=lambda: store.get_current(1, None),
            age_filter_all_pages=lambda: pages(max_age=timedelta(days=1)),
            commodity_all_pages=lambda: pages(commodity=REF, max_age=None),
            buy_all_pages=lambda: pages(commodity=REF, side=TradeSide.BUY, max_age=None),
            sell_all_pages=lambda: pages(commodity=REF, side=TradeSide.SELL, max_age=None),
            best_current=lambda: store.best_sell_prices([REF], max_age=timedelta(days=1)),
            best_history=lambda: store.best_sell_prices([REF], scope='history', max_age=None),
        )
        for name, operation in operations.items():
            operation()  # Explicit warmup: these are warm-cache timings.
            timings[name] = measure(operation)
        assert pages(max_age=timedelta(days=1)) == size // 2
        assert pages(commodity=REF, side=TradeSide.BUY, max_age=None) == size
        assert pages(commodity=REF, side=TradeSide.SELL, max_age=None) == size
        explain('station_read', operations['station_read'])
        explain('age_filter_page', lambda: store.query_current_candidates(max_age=timedelta(days=1), limit=500))
        explain('commodity_page', lambda: store.query_current_candidates(REF, max_age=None, limit=500))
        explain('buy_page', lambda: store.query_current_candidates(REF, side=TradeSide.BUY, max_age=None, limit=500))
        explain('sell_page', lambda: store.query_current_candidates(REF, side=TradeSide.SELL, max_age=None, limit=500))
        explain('best_current', operations['best_current'])
        explain('best_history', operations['best_history'])
        explain('history_page', lambda: store.get_history(FID, 10))
        explain('system_page', lambda: store.query_current_candidates(system_address=2**63, max_age=None))

        # Prepare one fixture at a time outside measurement; no huge Python dataset.
        # Each measured write is durable and includes validation, hashing and FULL commit.
        for kind in ('new_station', 'changed_snapshot', 'unchanged_snapshot'):
            durations = []
            for repeat in range(7):
                if kind == 'new_station':
                    value = observation(size+repeat+1, NOW)
                elif kind == 'changed_snapshot':
                    value = observation(1, NOW-timedelta(seconds=20-repeat), repeat+1)
                else:
                    value = observation(1, NOW-timedelta(seconds=10-repeat), 7)
                start = time.perf_counter_ns()
                result = store.record_observation(value)
                durations.append((time.perf_counter_ns()-start)/1_000_000)
                assert result.snapshot_reused == (kind == 'unchanged_snapshot')
            timings[kind] = dict(median_ms=statistics.median(durations), max_ms=max(durations), repetitions=7)

        timings['stats'] = measure(store.get_stats)
        timings['cleanup_no_expired'] = measure(store.cleanup, repeats=3)
        final = asdict(store.get_stats())
        final_rss = rss_mib()
        peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        store.close()
        return dict(stations=size, current_commodity_rows=size*350,
                    setup_seconds=setup_seconds, baseline_rss_mib=baseline,
                    setup_rss_mib=setup_rss, final_rss_mib=final_rss, peak_rss_mib=peak_rss,
                    initial_stats=initial, initial_checkpoint_bytes=checkpoint_bytes,
                    final_stats=final, final_checkpoint_bytes=path.stat().st_size,
                    timings=timings, plans=plans)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--size', type=int, choices=(100, 500, 1000, 5000))
    args = parser.parse_args()
    if args.size:
        print(json.dumps(run(args.size)))
    else:
        results = []
        for size in (100, 500, 1000, 5000):
            print(f'Benchmark: {size} stations', file=sys.stderr, flush=True)
            result = subprocess.run([sys.executable, __file__, '--size', str(size)],
                                    check=True, capture_output=True, text=True)
            results.append(json.loads(result.stdout))
        print(json.dumps(dict(python=sys.version, sqlite=sqlite3.sqlite_version,
                              platform=platform.platform(), results=results), indent=2))
