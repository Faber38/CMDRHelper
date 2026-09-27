"""Synthetic 57-commodity / 100, 1000, 5000-station benchmark; no network or user files.
Run: QT_QPA_PLATFORM=offscreen venv/bin/python tools/benchmark_mining_market.py
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
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

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from cmdrhelper.market_store import MarketStore
from cmdrhelper.mining_catalog import MINING_COMMODITIES
from cmdrhelper.mining_market import read_mining_prices
from benchmark_market_store import measure, rss_mib
NOW=datetime(2026,9,27,12,tzinfo=timezone.utc)


def run(count):
    with tempfile.TemporaryDirectory(prefix='cmdrhelper-mining-bench-') as directory:
        root=Path(directory);path=root/'markets.db'
        os.environ['XDG_CONFIG_HOME']=str(root/'config');os.environ['XDG_DATA_HOME']=str(root/'data')
        with MarketStore(path,clock=lambda:NOW) as store:
            for mid in range(1,count+1):
                value=dict(fid='CMDR'+str(mid%3),source='local_elite',market_id=mid,
                    station_name='Synthetic Port '+str(mid),system_name='Synthetic System '+str(mid//5),
                    system_address=100+mid//5,station_type='Coriolis',observed_at=NOW.isoformat(),
                    commodities=[dict(commodity_id=None,symbol=c.symbol,commander_buy_price=999999,
                        commander_sell_price=10000+mid+i,supply=1000,demand=10) for i,c in enumerate(MINING_COMMODITIES)])
                store.record_observation(value)
                if mid%10==0:
                    value=dict(value,fid='OTHER',observed_at=(NOW-timedelta(hours=2)).isoformat())
                    store.record_observation(value)  # Late older observation must never take over.
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
        state.observed_markets=SimpleNamespace(writer=SimpleNamespace(destination=path))
        view=MiningView(state.settings,state=state,controller=Inventory())
        view.market_controller.clock=lambda:NOW;view._market_clock=lambda:NOW
        view.resize(1250,750)
        def read():return read_mining_prices(path,timedelta(days=1),clock=lambda:NOW)
        with ThreadPoolExecutor(1) as pool:
            timing=measure(lambda:pool.submit(read).result(),7)
            tracemalloc.start();baseline=rss_mib()
            result=pool.submit(read).result()
            retained,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        assert len(result.quotes)==57 and all(q.header.market_id==count for q in result.quotes)
        statements=[];original=MarketStore.__init__
        def opened(store,*args,**kwargs):
            original(store,*args,**kwargs);store._con.set_trace_callback(statements.append)
        with patch.object(MarketStore,'__init__',opened),patch.object(MarketStore,'_payload',side_effect=AssertionError('No full DB load')):
            with ThreadPoolExecutor(1) as pool:pool.submit(read).result()
        with patch.object(MarketStore,'__init__',side_effect=AssertionError('No GUI DB')):
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
        view.market_controller.ready.connect(finished)
        view.show();QTimer.singleShot(30000,loop.quit);loop.exec();timer.stop()
        assert done
        first_show_ms=done[0]
        first_paint_heartbeat=max(pulses,default=0)
        # Measure refresh separately from initial font/layout/first paint work.
        pulses.clear();done.clear();last[0]=time.perf_counter();start=last[0]
        timer.start();view.market_controller.request();loop.exec();timer.stop()
        assert done
        view.close();view.market_controller.pool.waitForDone()
        selects=[sql for sql in statements if sql.lstrip().upper().startswith('SELECT')]
        return dict(stations=count,commodities=57,observers=4,read_batch=timing,gui_render=rendering,
            gui_heartbeat_max_ms=max(pulses,default=0),refresh_to_result_ms=done[0],show_to_result_ms=first_show_ms,
            initial_paint_heartbeat_max_ms=first_paint_heartbeat,
            batch_selects=len(selects),returned_quotes=len(result.quotes),
            python_retained_kib=retained/1024,python_peak_kib=peak/1024,rss_mib=baseline,
            schema=2)


if __name__=='__main__':
    with patch.object(socket.socket,'connect',side_effect=AssertionError('No network')):
        if len(sys.argv)>1:print(json.dumps(run(int(sys.argv[1]))))
        else:
            results=[]
            for n in (100,1000,5000):
                results.append(json.loads(subprocess.check_output([sys.executable,__file__,str(n)],text=True)))
            print(json.dumps(results,indent=2))
