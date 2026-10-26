"""Observed Stronghold event order, synthetic identities/prices and temp files only.

The production failure was a pre-start Market event, not a failed SQLite COMMIT.
Exercise JournalWatcher -> observer -> writer -> SQLite -> saved-market UI.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import time
import unittest
from unittest.mock import patch

from PySide6.QtCore import QEvent, QThreadPool
from PySide6.QtWidgets import QApplication
from cmdrhelper.journal_watcher import JournalWatcher
from cmdrhelper.market_store import MarketStore
from cmdrhelper.observed_market_cache import ObservedMarketCache
from cmdrhelper.observed_market_observer import ObservedMarketObserver
from cmdrhelper.ui.saved_markets_view import SavedMarketsView

FID = 'F_SYNTHETIC_STEAM'
MID = 3930539521
START = datetime(2026, 1, 2, 9, 0, 47, tzinfo=timezone.utc)
STATION = dict(StationName='Stronghold Carrier', StarSystem='HIP 60989',
               MarketID=MID, SystemAddress=22798140612, StationType='SurfaceStation')


def event(kind, stamp, **values):
    return dict(timestamp=stamp.isoformat(), event=kind, **values)


def market(stamp, **values):
    row = event('Market', stamp, MarketID=MID, StationName=STATION['StationName'],
                StarSystem=STATION['StarSystem'], StationType='')
    row.update(values)
    return row


def sidecar(trigger):
    return dict(trigger, Items=[dict(id=900000000+i, Name=f'fixture_commodity_{i}',
        BuyPrice=100+i, SellPrice=90+i, Stock=1000+i, Demand=i) for i in range(364)])


class LivePipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.folder = self.root/'steam';self.folder.mkdir()
        self.path = self.folder/'Journal.2026-01-02T075229.01.log'
        self.db = self.root/'cache'/'markets.db'
        self.now, self.tick = START, 100
        self.path.write_text('')
        self.append(event('Fileheader', START-timedelta(hours=2)))
        self.append(event('Commander',START-timedelta(hours=2),FID=FID,Name='Synthetic'))
        self.append(event('LoadGame',START-timedelta(hours=2),FID=FID,Commander='Synthetic'))
        self.observers, self.watchers = [], []
        self.addCleanup(self.close)

    def close(self):
        for watcher in self.watchers: watcher.stop()
        for observer in self.observers: observer.close()

    def append(self, row):
        with self.path.open('a') as stream: stream.write(json.dumps(row)+'\n')

    def write_sidecar(self, trigger):
        path=self.folder/'Market.json'
        path.write_text(json.dumps(sidecar(trigger)))
        stamp=datetime.fromisoformat(trigger['timestamp']).timestamp()
        os.utime(path,(stamp,stamp))

    def start(self):
        cache=ObservedMarketCache(self.db.parent/'observed_markets.json',clock=lambda:self.now)
        observer=ObservedMarketObserver(cache,clock=lambda:self.now,monotonic=lambda:self.tick,
                                        use_market_store=True)
        watcher=JournalWatcher()
        watcher.live_observers=[observer]
        watcher.journalChanged.connect(lambda:watcher.refresh_finished(True))
        watcher.set_folder(self.folder)
        observer.writer.ready.result(timeout=5)
        self.observers.append(observer);self.watchers.append(watcher)
        self.observer,self.watcher=observer,watcher
        return observer,watcher

    def dock(self, **values):
        station=dict(STATION);station.update(values)
        self.append(event('Docked',self.now,Taxi=False,Multicrew=False,**station))

    def poll(self):
        self.watcher.check_now()
        for _,future in tuple(self.observer._writes): future.result(timeout=5)
        self.watcher.check_now()  # Existing _live_pending path acknowledges COMMIT.

    def current(self, mid=MID):
        with MarketStore(self.db,read_only=True,clock=lambda:self.now) as store:
            return store.get_current(mid,max_age=None)

    def historical_sequence(self):
        # Relative times and event ordering of journal lines 641–661.
        self.append(event('Docked',START.replace(hour=8,minute=17,second=50),**STATION))
        entries=[(17,50,'Music'),(17,54,'RefuelAll'),(18,6,'Market'),
                 (18,22,'ShipTargeted'),(18,35,'MarketSell'),(18,36,'PowerplayMerits'),
                 (18,38,'Cargo'),(18,50,'MarketSell'),(18,51,'PowerplayMerits'),
                 (18,51,'PowerplayRank'),(18,52,'Cargo'),(19,20,'Market'),
                 (55,59,'ShipLocker'),(56,32,'PowerplayMerits'),(56,32,'PowerplayMerits'),
                 (56,32,'MultiSellExplorationData'),(56,43,'Repair'),(56,43,'Repair'),
                 (57,37,'Market'),(57,48,'Friends')]
        for minute,second,kind in entries:
            stamp=START.replace(hour=8,minute=minute,second=second)
            row=market(stamp) if kind=='Market' else event(kind,stamp)
            self.append(row)
            if kind=='Market': self.write_sidecar(row)

    def test_production_order_before_start_never_reaches_validation_or_writer(self):
        self.historical_sequence()
        boundary=self.path.stat().st_size
        self.start()
        with patch('cmdrhelper.observed_market_observer.normalize_observation',
                   side_effect=AssertionError('Pre-start Market must not be normalized')), \
             patch.object(self.observer.writer,'record',side_effect=AssertionError('No stale write')):
            self.poll()
        self.assertEqual(self.observer._baseline,boundary)
        self.assertEqual(self.observer._offset,boundary)
        self.assertEqual(self.observer.context,dict(FID=FID,**STATION))
        self.assertIsNone(self.observer.pending)
        self.assertIsNone(self.current())
        self.assertIsNone(self.observer.last_error)

    def test_new_market_after_start_commits_364_without_new_dock_or_embark(self):
        self.historical_sequence();self.start();self.poll()
        self.now+=timedelta(seconds=1)
        trigger=market(self.now);self.append(trigger);self.write_sidecar(trigger)
        self.poll()
        row=self.current()
        self.assertEqual(len(row['commodities']),364)
        self.assertEqual(row['station_type'],'SurfaceStation')
        self.assertEqual(row['system_address'],STATION['SystemAddress'])
        self.assertEqual(row['fid'],FID)
        self.assertFalse(self.watcher._live_pending)
        self.assertEqual(self.observer._offset,self.path.stat().st_size)

    def test_live_docked_then_market_before_first_poll_needs_no_ui_context(self):
        self.start()  # AppState / its asynchronous journal projection is absent.
        self.dock()
        self.append(event('Music',self.now));self.append(event('RefuelAll',self.now))
        trigger=market(self.now);self.append(trigger);self.write_sidecar(trigger)
        self.poll()
        self.assertEqual(len(self.current()['commodities']),364)
        self.assertEqual(self.observer.context,dict(FID=FID,**STATION))

    def test_mismatched_id_type_and_stale_file_remain_rejected(self):
        self.start();self.dock()
        for change in ({'MarketID':999},{'StationType':'FleetCarrier'},
                       {'timestamp':(START-timedelta(seconds=10)).isoformat()}):
            with self.subTest(change=change):
                self.now+=timedelta(seconds=1)
                trigger=market(self.now);self.append(trigger)
                bad=dict(trigger,**change);self.write_sidecar(bad)
                self.poll()
                self.assertIsNone(self.current())
                self.assertIsNotNone(self.observer.pending)
        # A new valid Market replaces the rejected pending request.
        self.now+=timedelta(seconds=1)
        trigger=market(self.now);self.append(trigger);self.write_sidecar(trigger);self.poll()
        self.assertEqual(len(self.current()['commodities']),364)

    def test_repeated_market_updates_one_current_snapshot(self):
        self.start();self.dock()
        for i in range(2):
            self.now+=timedelta(seconds=1)
            trigger=market(self.now);self.append(trigger);self.write_sidecar(trigger);self.poll()
            self.assertEqual(self.current()['observed_at'],self.now.isoformat())
        with MarketStore(self.db,read_only=True,clock=lambda:self.now) as store:
            self.assertEqual(len(store.query_current_candidates(max_age=None).items),1)
            self.assertEqual(len(store.get_history(FID,MID).items),2)

    def test_restart_keeps_commit_without_replaying_checkpoint(self):
        self.start();self.dock()
        trigger=market(self.now);self.append(trigger);self.write_sidecar(trigger);self.poll()
        saved=self.current()
        self.watcher.stop();self.observer.close()
        self.now+=timedelta(minutes=3);self.start()
        with patch.object(self.observer.writer,'record',side_effect=AssertionError('No replay')):
            self.poll()
        self.assertEqual(self.current(),saved)
        self.now+=timedelta(seconds=1)
        trigger=market(self.now);self.append(trigger);self.write_sidecar(trigger);self.poll()
        self.assertEqual(self.current()['observed_at'],self.now.isoformat())

    def test_missing_sidecar_retries_without_new_event_or_context(self):
        self.start();self.dock();trigger=market(self.now);self.append(trigger)
        self.poll();self.assertIsNone(self.current())
        self.assertTrue(self.watcher._live_pending)
        self.write_sidecar(trigger);self.poll()
        self.assertEqual(len(self.current()['commodities']),364)

    def test_disembark_noop_and_embark_cannot_replay_old_market(self):
        self.historical_sequence();self.start();self.poll()
        context=deepcopy(self.observer.context)
        self.append(event('Disembark',self.now,OnStation=True,**STATION));self.poll()
        self.assertEqual(self.observer.context,context)
        self.append(event('Embark',self.now,OnStation=True,SRV=False,Taxi=False,Multicrew=False,ID=1,**STATION))
        self.poll()
        self.assertIsNone(self.current())
        self.now+=timedelta(seconds=1)
        trigger=market(self.now);self.append(trigger);self.write_sidecar(trigger);self.poll()
        self.assertEqual(len(self.current()['commodities']),364)

    def test_later_context_change_cancels_rejected_market_until_fresh_event(self):
        self.start();self.dock(StationType='FleetCarrier')
        trigger=market(self.now,StationType='SurfaceStation');self.append(trigger);self.write_sidecar(trigger)
        self.poll();self.assertIsNone(self.current());self.assertIsNotNone(self.observer.pending)
        self.dock();self.poll()
        self.assertIsNone(self.observer.pending)
        self.assertIsNone(self.current())
        self.now+=timedelta(seconds=1)
        trigger=market(self.now);self.append(trigger);self.write_sidecar(trigger);self.poll()
        self.assertEqual(len(self.current()['commodities']),364)

    def test_embark_updates_context_but_does_not_replay_pending_market(self):
        self.start()
        trigger=market(self.now);self.append(trigger)
        self.poll();self.assertIsNotNone(self.observer.pending)
        self.assertEqual(self.observer.context,{'FID':FID})
        self.append(event('Embark',self.now,OnStation=True,SRV=False,Taxi=False,
                          Multicrew=False,ID=1,**STATION))
        self.write_sidecar(trigger);self.poll()
        self.assertEqual(self.observer.context,dict(FID=FID,**STATION))
        self.assertIsNone(self.observer.pending);self.assertIsNone(self.current())
        self.now+=timedelta(seconds=1)
        trigger=market(self.now);self.append(trigger);self.write_sidecar(trigger);self.poll()
        self.assertEqual(len(self.current()['commodities']),364)

    def test_commander_change_cancels_pending_without_using_other_sidecar(self):
        self.start();self.dock();trigger=market(self.now);self.append(trigger)
        self.poll();self.assertIsNotNone(self.observer.pending)
        self.append(event('LoadGame',self.now,FID='F_SYNTHETIC_OTHER'))
        self.write_sidecar(trigger);self.poll()
        self.assertIsNone(self.current());self.assertIsNone(self.observer.pending)
        self.assertEqual(self.observer.context,{'FID':'F_SYNTHETIC_OTHER'})

    def test_normal_station_and_fleet_carrier_same_pipeline(self):
        self.start()
        for mid,kind in ((100,'Coriolis'),(200,'FleetCarrier')):
            self.now+=timedelta(seconds=1)
            self.dock(MarketID=mid,StationType=kind)
            trigger=market(self.now,MarketID=mid,StationType=kind)
            self.append(trigger);self.write_sidecar(trigger);self.poll()
            self.assertEqual(self.current(mid)['station_type'],kind)
            self.assertEqual(len(self.current(mid)['commodities']),364)

    def test_committed_market_selectable_in_saved_view_while_undocked(self):
        self.start();self.dock()
        trigger=market(self.now);self.append(trigger);self.write_sidecar(trigger);self.poll()
        self.append(event('Undocked',self.now));self.poll()
        state=SimpleNamespace(observed_markets=self.observer,commander_fid='F_OTHER_VIEW',
                              system='Other system',station='')
        pool=QThreadPool()
        view=SavedMarketsView(state,pool=pool,clock=lambda:self.now)
        try:
            view.show()
            def wait():
                until=time.monotonic()+5
                while view._jobs and time.monotonic()<until:
                    self.app.processEvents();time.sleep(.002)
                self.assertFalse(view._jobs)
            wait()
            self.assertEqual(view.markets_model.rowCount(),1)
            self.assertEqual(view.markets_model.rows[0]['header'].market_id,MID)
            view.markets_table.setCurrentIndex(view.markets_proxy.index(0,0));wait()
            self.assertEqual(view.goods_model.rowCount(),364)
            self.assertEqual(view._snapshot,self.current())
            self.assertEqual(self.observer.context,{'FID':FID})
        finally:
            view.cancel_reads();pool.waitForDone(5000)
            view.close();view.deleteLater();self.app.sendPostedEvents(None,QEvent.DeferredDelete)
