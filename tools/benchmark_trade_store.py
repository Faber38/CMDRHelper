"""Offline A/B handoff benchmark; temporary DBs, real Qt workers, mocked Spansh.

QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 venv/bin/python tools/benchmark_trade_store.py > /tmp/trade-store.json
"""
import argparse
import gc
import json
import os
from pathlib import Path
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.benchmark_market_store import NOW, FID, REF, observation, rss_mib
from cmdrhelper.market_store import MarketStore
from cmdrhelper.observed_market_cache import ObservedMarketCache
from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus, TradeSide


def fixture(root, size):
    coords = root/'coordinates.db'
    with sqlite3.connect(coords) as con:
        con.execute('CREATE TABLE systems(system_address INTEGER PRIMARY KEY,name TEXT,x REAL,y REAL,z REAL)')
        con.executemany('INSERT INTO systems VALUES(?,?,?,?,?)',
            [(100+i, f'Synthetic System {i}', i % 80, 0, 0) for i in range(size//5+1)])
    with MarketStore(root/'markets.db', clock=lambda: NOW) as store:
        for mid in range(1, size+1):
            row = observation(mid, NOW)
            row['system_address'] = 100+mid//5
            store.record_observation(row)


def measure(root, mode):
    from PySide6.QtCore import QEventLoop, QThreadPool, QTimer
    from PySide6.QtWidgets import QApplication
    from cmdrhelper.ui.trade_view import MarketWorker
    from cmdrhelper.ui.recommendations_view import local_distances
    from cmdrhelper.trade_market_source import prepare_trade_source
    app = QApplication.instance() or QApplication([])
    pool = QThreadPool()
    cache = ObservedMarketCache(root/'absent.json', clock=lambda: NOW)
    if mode == 'legacy':
        # Model the existing transitional cache projection. Above the original
        # JSON limits this is an algorithmic comparison, not a supported JSON load.
        with MarketStore(root/'markets.db', read_only=True, clock=lambda: NOW) as store:
            for r in store._con.execute('SELECT observation_id,fid FROM current_markets'):
                value = store.get_observation(r['fid'], r['observation_id'])
                cache._markets[(value['fid'], value['market_id'])] = value
    else:
        def forbidden(*args, **kwargs):
            raise AssertionError('New trade path must not load complete market payloads')
        cache.all = forbidden
        MarketStore._payload = forbidden
    class CoordinatesDB:
        path = root/'coordinates.db'
        def _connect(self):
            return sqlite3.connect(self.path)
    state = SimpleNamespace(database=CoordinatesDB())
    observer = SimpleNamespace(cache=cache)
    origin = dict(system_name='Synthetic System 0', system_address=100)
    class Provider:
        def search_buy(self, query, *, cancel):
            return MarketSearchResult(MarketStatus.NO_RESULTS, query=query)
        search_sell = search_buy
    class TimedWorker(MarketWorker):
        def run(self):
            begin = time.perf_counter()
            super().run()
            self.elapsed = (time.perf_counter()-begin)*1000
    output = {}
    baseline = rss_mib()
    for side in TradeSide:
        durations, digests = [], []
        for repeat in range(5):
            gc.collect()
            loop = QEventLoop()
            query = MarketSearch(REF.commodity_id, origin['system_name'], limit=100)
            values = {}
            ticks = []
            pulse = QTimer()
            pulse.setInterval(10)
            previous = [time.perf_counter()]
            def tick():
                now = time.perf_counter()
                ticks.append((now-previous[0])*1000)
                previous[0] = now
            pulse.timeout.connect(tick)
            pulse.start()
            worker = [None]
            def start():
                begin = time.perf_counter()
                if mode == 'legacy':
                    local = cache.all(FID, None)
                    distances = local_distances(state, origin, local)
                    kwargs = dict(local_markets=local, distances=distances)
                else:
                    kwargs = dict(local_source=prepare_trade_source(
                        observer, FID, origin['system_name'], origin['system_address'], state.database))
                values['gui_ms'] = (time.perf_counter()-begin)*1000
                worker[0] = TimedWorker(Provider(), query, side, fid=FID, clock=lambda: NOW, **kwargs)
                def done(result):
                    values['total_ms'] = (time.perf_counter()-begin)*1000
                    assert result.status == MarketStatus.OK and len(result.offers) == 100
                    digests.append([(o.market_id, o.commander_buy_price, o.commander_sell_price,
                                     o.supply, o.demand, o.distance_ly, o.provider) for o in result.offers])
                    loop.quit()
                worker[0].signals.finished.connect(done)
                pool.start(worker[0])
            QTimer.singleShot(0, start)
            loop.exec()
            pulse.stop()
            pool.waitForDone()
            values['worker_ms'] = worker[0].elapsed
            values['heartbeat_max_ms'] = max(ticks, default=0)
            values['rss_mib'] = rss_mib()
            durations.append(values)
            worker[0] = None
        assert all(v == digests[0] for v in digests)
        output[side.value] = dict(
            measurements={key: dict(median=statistics.median(v[key] for v in durations),
                                    maximum=max(v[key] for v in durations)) for key in durations[0]},
            offers=digests[0])
    output['baseline_rss_mib'] = baseline
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root')
    parser.add_argument('--mode', choices=('legacy', 'store'))
    args = parser.parse_args()
    if args.root:
        print(json.dumps(measure(Path(args.root), args.mode)))
    else:
        results = []
        for size in (100, 500, 1000, 5000):
            print(f'Fixture {size}', file=sys.stderr, flush=True)
            with tempfile.TemporaryDirectory(prefix='cm-trade-ab-') as directory:
                root = Path(directory)
                fixture(root, size)
                row = dict(stations=size, commodity_rows=size*350)
                for mode in ('legacy', 'store'):
                    print(f'{size}: {mode}', file=sys.stderr, flush=True)
                    result = subprocess.run([sys.executable, __file__, '--root', str(root), '--mode', mode],
                        env={**os.environ, 'QT_QPA_PLATFORM':'offscreen', 'PYTHONDONTWRITEBYTECODE':'1'},
                        capture_output=True, text=True, check=True)
                    row[mode] = json.loads(result.stdout)
                for side in ('buy', 'sell'):
                    assert row['legacy'][side]['offers'] == row['store'][side]['offers']
                results.append(row)
        print(json.dumps(results, indent=2))
