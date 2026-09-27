"""Offline synthetic transition benchmark, including isolated AppState construction.

Run: QT_QPA_PLATFORM=offscreen venv/bin/python tools/benchmark_market_transition.py
No settings, journals, database or network outside TemporaryDirectory are used.
"""
import gc
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import tracemalloc
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmark_market_store import NOW, observation, measure, rss_mib
from cmdrhelper.market_store import MarketStore
from cmdrhelper.market_migration import migrate_market_cache
from cmdrhelper.observed_market_observer import ObservedMarketObserver
from cmdrhelper.ui.observed_market_status import observed_market_text


def deep_size(value, seen=None):
    seen = set() if seen is None else seen
    if id(value) in seen:
        return 0
    seen.add(id(value))
    size = sys.getsizeof(value)
    if isinstance(value, dict):
        size += sum(deep_size(k, seen)+deep_size(v, seen) for k,v in value.items())
    elif isinstance(value, (tuple, list)):
        size += sum(deep_size(v, seen) for v in value)
    return size


def run(count):
    with tempfile.TemporaryDirectory(prefix='cmdrhelper-transition-') as directory:
        root = Path(directory)
        os.environ['XDG_CONFIG_HOME'] = str(root/'config')
        os.environ['XDG_DATA_HOME'] = str(root/'data')
        source, path = root/'observed_markets.json', root/'markets.db'
        migrate_market_cache(source, path, clock=lambda: NOW)
        with MarketStore(path, clock=lambda: NOW) as store:
            for mid in range(1, count+1):
                store.record_observation(observation(mid, NOW))
            aggregate = measure(store.storage_stats, 100)
        def open_store():
            with MarketStore(path, read_only=True):
                pass
        opening = measure(open_store, 30)
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QSettings
        from cmdrhelper.database import CMDRDatabase
        from cmdrhelper.state import AppState
        app = QApplication.instance() or QApplication([])
        database = CMDRDatabase(root/'cmdrhelper.db')
        settings = QSettings(str(root/'settings.ini'), QSettings.IniFormat)
        with patch('cmdrhelper.state.QSettings', return_value=settings), \
                patch('cmdrhelper.state.CMDRDatabase', return_value=database), \
                patch('cmdrhelper.state.default_journal_paths', return_value=[]), \
                patch('cmdrhelper.state.QTimer.singleShot'), \
                patch('PySide6.QtCore.QStandardPaths.writableLocation', return_value=str(root/'appdata')):
            start = time.perf_counter()
            state = AppState()
            app_ms = (time.perf_counter()-start)*1000
        observer = state.observed_markets
        # Isolated actual startup path, including asynchronous writer and cleanup.
        gc.collect()
        rss_before = rss_mib()
        tracemalloc.start()
        with patch('cmdrhelper.observed_market_observer.cache_path', return_value=source), \
                patch.object(MarketStore, '_payload', side_effect=AssertionError('No full DB load')):
            start = time.perf_counter()
            observer.cache
            dispatch_ms = (time.perf_counter()-start)*1000
            observer.writer.ready.result(60)
            ready_ms = (time.perf_counter()-start)*1000
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        headers_bytes = deep_size(observer.cache._markets)
        rss_after = rss_mib()
        # Historical full-payload baseline from GENERATED data, never loading DB.
        sample = {( 'F_SYNTHETIC_BENCHMARK', mid): observation(mid, NOW) for mid in range(1, 101)}
        full_estimate = deep_size(sample)*count/100
        del sample
        with patch.object(MarketStore, '__init__', side_effect=AssertionError('No GUI SQL')):
            status = measure(lambda: observed_market_text(state), 1000)
        result = dict(stations=count, commodities_per_station=350, status=status,
            worker_status_aggregate=aggregate, store_open=opening, app_state_ms=app_ms,
            observer_dispatch_ms=dispatch_ms, observer_ready_ms=ready_ms,
            retained_python_mib=current/1024**2, peak_python_mib=peak/1024**2,
            headers_mib=headers_bytes/1024**2, estimated_old_projection_mib=full_estimate/1024**2,
            rss_before_mib=rss_before, rss_after_mib=rss_after,
            storage_bytes=observer.cache.storage_stats()[1])
        observer.close()
        return result


if __name__ == '__main__':
    # Fail closed if a future AppState constructor tries to contact a service.
    with patch.object(socket.socket, 'connect', side_effect=AssertionError('No network')):
        if len(sys.argv) > 1:
            print(json.dumps(run(int(sys.argv[1]))))
        else:
            results = [json.loads(subprocess.check_output([sys.executable, __file__, str(n)], text=True))
                       for n in (100, 1000, 5000)]
            print(json.dumps(results, indent=2))
