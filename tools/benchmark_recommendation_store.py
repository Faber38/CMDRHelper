"""Synthetic recommendation A/B, real Qt callbacks; never productive data/network."""
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
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tests'))
from tools.benchmark_market_store import NOW, FID, observation, rss_mib
from cmdrhelper.market_store import MarketStore
from cmdrhelper.observed_market_cache import ObservedMarketCache
from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus
from cmdrhelper.trade_recommendations import search_recommendations


def fixture(root, size):
    with MarketStore(root/'markets.db', clock=lambda:NOW) as store:
        for mid in range(1,size+1):
            row=observation(mid,NOW)
            row.update(system_name='Synthetic System',system_address=100)
            for i, c in enumerate(row['commodities']):
                c.update(commander_buy_price=(1000+i if i<35 else 0),supply=(500 if i<35 else 0),
                         commander_sell_price=1600+i+mid%100,demand=300)
            store.record_observation(row)


def digest(rows):
    return [(r.destination.market_id,r.destination.commodity_id,r.quantity,r.buy_price,
             r.destination.commander_sell_price,r.total_profit,r.destination.provider) for r in rows]


class Provider:
    def search_sell(self,q,*,cancel):
        return MarketSearchResult(MarketStatus.NO_RESULTS,query=q)


def run(root,size,mode):
    from PySide6.QtCore import QEventLoop,QThreadPool,QTimer,QObject,Signal
    from PySide6.QtWidgets import QApplication
    app=QApplication.instance() or QApplication([])
    cache=ObservedMarketCache(root/'absent.json',clock=lambda:NOW)
    with MarketStore(root/'markets.db',read_only=True,clock=lambda:NOW) as store:
        origin=store.get_current(1,None)
        if mode=='legacy':
            for r in store._con.execute('SELECT fid,observation_id FROM current_markets'):
                value=store.get_observation(r['fid'],r['observation_id'])
                # Match original input order, retained in current Store metadata.
                cache._markets[(value['fid'],value['market_id'])]=store.get_current(value['market_id'],None)
        else:
            cache.install_headers({1:{k:v for k,v in origin.items() if k!='commodities'}})
    header={k:v for k,v in origin.items() if k!='commodities'}
    metrics=[]
    outputs=[]
    baseline=rss_mib()
    if mode=='legacy':
        # GUI preparation and actual old callback cost are measured at every size.
        # Full old O(items² * markets * rows) run is bounded to <=100 stations.
        for repeat in range(3):
            gc.collect()
            start=time.perf_counter()
            old_origin=cache.get(FID,1,None)
            local=cache.all(FID,None)
            distances={r['market_id']:0.0 for r in local}
            prep=(time.perf_counter()-start)*1000
            calls=[]
            def callback(_=None):
                stamp=time.perf_counter()
                cache.get(FID,1,None)
                cache.get(FID,1,None)
                calls.append((time.perf_counter()-stamp)*1000)
            callback()
            entry=dict(gui_ms=prep,callback_ms=max(calls),rss_mib=rss_mib())
            if size<=100:
                start=time.perf_counter()
                result=search_recommendations(old_origin,local,distances,280,10,
                    MarketSearch('',header['system_name'],limit=100),Provider(),clock=lambda:NOW,progress=callback)
                entry.update(full_ms=prep+(time.perf_counter()-start)*1000,callbacks=len(calls)-1)
                outputs.append(digest(result.rows))
            metrics.append(entry)
    else:
        from test_recommendations_view import State
        from cmdrhelper.route_planner.models import ShipLoadoutData
        from cmdrhelper.ui.recommendations_view import RecommendationsView,RecommendationWorker
        from cmdrhelper.trade_market_source import prepare_trade_source
        from cmdrhelper.recommendation_market_source import RecommendationStoreSession
        # Oracle: same legacy engine over identity-only rows containing the 35
        # relevant origin commodities, retaining identical prices/metadata.
        with MarketStore(root/'markets.db',read_only=True,clock=lambda:NOW) as store:
            oracle=[]
            for mid in range(1,size+1):
                row=store.get_current(mid,None)
                row['commodities']=[r for r in row['commodities'] if r['commander_buy_price']>0]
                oracle.append(row)
        oracle_result=search_recommendations(origin,oracle,{r['market_id']:0. for r in oracle},280,10,
            MarketSearch('',header['system_name'],limit=100),Provider(),clock=lambda:NOW)
        expected=digest(oracle_result.rows)
        del oracle
        gc.collect()
        # No legacy cache or complete target payload can be used by measured runs.
        cache.all=lambda *a,**k: (_ for _ in ()).throw(AssertionError('No all'))
        cache.get=lambda *a,**k: (_ for _ in ()).throw(AssertionError('No get'))
        pool=QThreadPool()
        state=State()
        state.commander_fid=FID;state.system=header['system_name'];state.station=header['station_name']
        state.ship='Synthetic'
        state.ship_loadout=ShipLoadoutData(ship_id=7,ship_name='Synthetic',ship_type='anaconda',
            cargo_capacity=300,loadout_complete=True,loadout_stale=False)
        state.cargo_snapshot=dict(fid=FID,vessel='Ship',ship_id=7,count=20,capacity=300,inventory=[])
        state.observed_markets=SimpleNamespace(cache=cache,context=dict(FID=FID,MarketID=1,
            StationName=header['station_name'],StarSystem=header['system_name']))
        view=RecommendationsView(state,Provider(),pool)
        view.local_only.setChecked(mode=='store-local')
        view.resize(1100,900);view.show();app.processEvents()
        baseline=rss_mib()
        original_get=MarketStore.get_current
        original_query=MarketStore.query_current_candidates
        original_init=MarketStore.__init__
        original_run=RecommendationWorker.run
        for repeat in range(3):
            gc.collect()
            data=dict(origin_ms=0.,candidate_ms=0.,db_selects=0,origin_reads=0,candidate_pages=0)
            callbacks=[]
            loop=QEventLoop()
            def trace(sql):
                if sql.lstrip().upper().startswith('SELECT'):data['db_selects']+=1
            def opened(store,*a,**k):
                original_init(store,*a,**k);store._con.set_trace_callback(trace)
            def get(store,*a,**k):
                start=time.perf_counter();result=original_get(store,*a,**k)
                data['origin_ms']+=(time.perf_counter()-start)*1000;data['origin_reads']+=1
                return result
            def candidates(store,*a,**k):
                start=time.perf_counter();result=original_query(store,*a,**k)
                data['candidate_ms']+=(time.perf_counter()-start)*1000;data['candidate_pages']+=1
                return result
            def worker_run(worker):
                start=time.perf_counter();original_run(worker)
                data['worker_ms']=(time.perf_counter()-start)*1000
            original_progress=view.progress;original_diagnostic=view.diagnostic_progress;original_finished=view.finished
            def timed_progress(result):
                start=time.perf_counter();original_progress(result)
                callbacks.append((time.perf_counter()-start)*1000)
            def timed_diagnostic(result):
                start=time.perf_counter();original_diagnostic(result)
                callbacks.append((time.perf_counter()-start)*1000)
            def finished(result):
                data['handoff_ms']=(time.perf_counter()-began[0])*1000
                start=time.perf_counter();original_finished(result)
                data['finish_callback_ms']=(time.perf_counter()-start)*1000
                outputs.append(digest(result.rows));assert outputs[-1]==expected
                QTimer.singleShot(20,loop.quit)  # Include final rendering/paint in heartbeat.
            view.progress=timed_progress;view.diagnostic_progress=timed_diagnostic;view.finished=finished
            MarketStore.__init__=opened;MarketStore.get_current=get
            MarketStore.query_current_candidates=candidates;RecommendationWorker.run=worker_run
            pulses=[];last=[time.perf_counter()];timer=QTimer();timer.setInterval(10)
            def tick():
                now=time.perf_counter();pulses.append((now-last[0])*1000);last[0]=now
            timer.timeout.connect(tick);timer.start();began=[0.]
            def start():
                began[0]=time.perf_counter();view.start_search()
                data['gui_ms']=(time.perf_counter()-began[0])*1000
            QTimer.singleShot(0,start);loop.exec();timer.stop();pool.waitForDone()
            data.update(callbacks=len(callbacks),callback_ms=max(callbacks,default=0),
                heartbeat_ms=max(pulses,default=0),rss_mib=rss_mib())
            assert data['origin_reads']==1
            metrics.append(data)
            view.progress=original_progress;view.diagnostic_progress=original_diagnostic;view.finished=original_finished
            MarketStore.__init__=original_init;MarketStore.get_current=original_get
            MarketStore.query_current_candidates=original_query;RecommendationWorker.run=original_run
        view.close()
    return dict(baseline_rss_mib=baseline,measurements=metrics,offers=outputs[-1] if outputs else None)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root');parser.add_argument('--size',type=int);parser.add_argument('--mode')
    args=parser.parse_args()
    if args.root:
        print(json.dumps(run(Path(args.root),args.size,args.mode)))
    else:
        results=[]
        for size in (10,100,500,1000,5000):
            print(f'Fixture {size}',file=sys.stderr,flush=True)
            with tempfile.TemporaryDirectory(prefix='cm-recommend-ab-') as directory:
                root=Path(directory);fixture(root,size);row=dict(stations=size)
                for mode in ('legacy','store','store-local'):
                    print(f'{size}: {mode}',file=sys.stderr,flush=True)
                    child=subprocess.run([sys.executable,__file__,'--root',str(root),'--size',str(size),'--mode',mode],
                        capture_output=True,text=True,env={**os.environ,'QT_QPA_PLATFORM':'offscreen','PYTHONDONTWRITEBYTECODE':'1'})
                    if child.returncode:
                        raise RuntimeError(child.stderr[-5000:])
                    row[mode]=json.loads(child.stdout)
                if row['legacy']['offers'] is not None:assert row['legacy']['offers']==row['store']['offers']
                results.append(row)
                print(json.dumps(row),file=sys.stderr,flush=True)
        print(json.dumps(results,indent=2))
