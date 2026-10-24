"""Synthetic 57-commodity / 100, 1000, 5000-journal benchmark; no network or user files.
Run: QT_QPA_PLATFORM=offscreen venv/bin/python tools/benchmark_mining_market.py
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import gc
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import tracemalloc
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cmdrhelper.mining_catalog import MINING_COMMODITIES
from cmdrhelper.mining_market import read_mining_prices
from benchmark_market_store import measure, rss_mib
NOW=datetime(2026,9,27,12,tzinfo=timezone.utc)


def run(count):
    with tempfile.TemporaryDirectory(prefix='cmdrhelper-mining-bench-') as directory:
        root=Path(directory);path=root/'sales.db'
        os.environ['XDG_CONFIG_HOME']=str(root/'config');os.environ['XDG_DATA_HOME']=str(root/'data')
        with sqlite3.connect(path) as con:
            con.executescript('CREATE TABLE commanders(id INTEGER, fid TEXT); '
                'INSERT INTO commanders VALUES(1,"F1"); '
                'CREATE TABLE journal_sessions(journal_file TEXT, commander_id INTEGER, fid_seen TEXT, attribution_status TEXT);')
            for index in range(count):
                journal=root/f'Journal.{index:08d}.log'
                events=[dict(event='Commander',FID='F1'),
                        dict(event='Docked',StationName='Synthetic Port',StarSystem='Synthetic System')]
                events.extend(dict(event='MarketSell',timestamp=(NOW+timedelta(seconds=index)).isoformat(),
                                   Type=c.symbol,SellPrice=10000+index,Count=1) for c in MINING_COMMODITIES)
                journal.write_text(''.join(json.dumps(e)+'\n' for e in events))
                con.execute('INSERT INTO journal_sessions VALUES(?,1,"F1","identified")',(str(journal),))
        gc.collect()
        from PySide6.QtCore import QObject, Signal, QSettings, QTimer, QEventLoop
        from PySide6.QtWidgets import QApplication
        from cmdrhelper.ui.mining_view import MiningView
        app=QApplication.instance() or QApplication([])
        class Inventory(QObject):
            loading=Signal();ready=Signal(object);refreshFinished=Signal(str)
            def refresh_now(self):pass
        class State(QObject):
            observedMarketsChanged=Signal();viewedCommanderChanged=Signal(object)
        state=State();state.settings=QSettings(str(root/'ui.ini'),QSettings.IniFormat)
        state.database=SimpleNamespace(path=path)
        state.commander_id=state.viewed_commander_id=1
        view=MiningView(state.settings,state=state,controller=Inventory())
        view.resize(1250,750)
        cache={}
        def read():return read_mining_prices(path,1,cache=cache)
        with ThreadPoolExecutor(1) as pool:
            timing=measure(lambda:pool.submit(read).result(),7)
            tracemalloc.start();baseline=rss_mib()
            result=pool.submit(read).result()
            retained,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        assert len(result.quotes)==57 and all(q.price==10000+count-1 for q in result.quotes)
        with patch.object(sqlite3,'connect',side_effect=AssertionError('No GUI DB')):
            rendering=measure(lambda:view.set_market_prices(result),30)
        loop=QEventLoop();pulses=[];last=[time.perf_counter()];done=[]
        timer=QTimer();timer.setInterval(5)
        def tick():
            now=time.perf_counter();pulses.append((now-last[0])*1000);last[0]=now
        timer.timeout.connect(tick);timer.start()
        start=time.perf_counter()
        def finished(value):
            if value.status=='ok':
                done.append((time.perf_counter()-start)*1000);QTimer.singleShot(20,loop.quit)
        # Unchanged prices intentionally emit no UI update; measure worker completion.
        view.market_controller.signals.finished.connect(lambda generation, value: finished(value))
        view.show();QTimer.singleShot(30000,loop.quit);loop.exec();timer.stop()
        assert done
        first_show_ms=done[0]
        first_paint_heartbeat=max(pulses,default=0)
        # Measure refresh separately from initial font/layout/first paint work.
        pulses.clear();done.clear();last[0]=time.perf_counter();start=last[0]
        timer.start();view.market_controller.request();loop.exec();timer.stop()
        assert done
        view.close();view.market_controller.pool.waitForDone()
        return dict(journals=count,commodities=57,commanders=1,read_batch=timing,gui_render=rendering,
            gui_heartbeat_max_ms=max(pulses,default=0),refresh_to_result_ms=done[0],show_to_result_ms=first_show_ms,
            initial_paint_heartbeat_max_ms=first_paint_heartbeat,
            returned_quotes=len(result.quotes),
            python_retained_kib=retained/1024,python_peak_kib=peak/1024,rss_mib=baseline,
            schema_changes=False)


if __name__=='__main__':
    with patch.object(socket.socket,'connect',side_effect=AssertionError('No network')):
        if len(sys.argv)>1:print(json.dumps(run(int(sys.argv[1]))))
        else:
            results=[]
            for n in (100,1000,5000):
                results.append(json.loads(subprocess.check_output([sys.executable,__file__,str(n)],text=True)))
            print(json.dumps(results,indent=2))
