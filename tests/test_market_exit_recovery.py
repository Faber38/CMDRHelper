"""Noncritical market exit policy; important writes retain their existing guard."""
import json
import os
from pathlib import Path
import threading
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from PySide6.QtTest import QTest
from cmdrhelper import diagnostics
from cmdrhelper.market_writer import MarketWriteWorker
from cmdrhelper.market_store import MarketStore, ObservationConflict
from cmdrhelper.observed_market_observer import ObservedMarketObserver
import test_safe_exit as safe
import test_observed_market_cache as captures
from test_market_store import observation, commodity, NOW


class MarketExitRecoveryTests(unittest.TestCase):
    setUpClass = classmethod(safe.SafeExitTests.setUpClass.__func__)
    setUp = safe.SafeExitTests.setUp
    wait = safe.SafeExitTests.wait
    work = safe.SafeExitTests.work

    def cleanup(self):
        QTest.qWait(20)
        safe.SafeExitTests.cleanup(self)

    def writer(self):
        writer = MarketWriteWorker(self.root/'legacy.json', self.root/'markets.db', clock=lambda:NOW)
        self.addCleanup(writer.close)
        observer = ObservedMarketObserver()
        observer.writer = writer
        self.w.state.observed_markets = observer
        return writer, observer

    def finish(self):
        self.w.close()
        self.wait(lambda:not self.w.isVisible())
        self.assertEqual(self.w._exit_controller.phase, 'finished')
        self.assertIsNone(self.w._exit_controller.dialog)

    def export(self, name):
        target = self.root/(name+'.zip')
        diagnostics.create_package(target, state=self.w.state, exit_controller=self.w._exit_controller, folder=self.root)
        with ZipFile(target) as archive:
            self.assertIsNone(archive.testzip())
            data = json.loads(archive.read('exit_diagnostics.json'))
            contents = '\n'.join(archive.read(n).decode() for n in archive.namelist())
            for private in (str(self.root),'F_SYNTHETIC_STORE','Conflicting observation at the same timestamp'):
                self.assertNotIn(private, contents)
        out = os.environ.get('EXIT_RECOVERY_EVIDENCE')
        if out:
            Path(out, target.name).write_bytes(target.read_bytes())
        return data

    def test_initialization_failure_exits_without_retry_or_question(self):
        source = self.root/'legacy.json'; source.write_text('{')
        before = source.read_bytes()
        writer, observer = self.writer()
        with self.assertRaises(Exception): writer.ready.result(3)
        with patch.object(writer, 'retry_initialization', side_effect=AssertionError('No exit retry')):
            self.finish()
        self.assertEqual(source.read_bytes(), before)
        self.assertTrue(writer.is_stopped())
        self.assertIsNotNone(writer.last_error)
        data = self.export('policy-A-initialization-failed-exited')
        self.assertEqual(data['pending_count'], 0)
        self.assertIn('market_initialization_failed', data['reasons'])
        self.assertIn('market_errors_discarded', data['reasons'])
        self.assertEqual(data['writer_states'], {'closed':1})

    def test_conflicting_record_is_discarded_without_retry_or_confirmation(self):
        writer, observer = self.writer(); writer.ready.result(3)
        writer.record(observation()).result(3)
        bad = observation(rows=[commodity(buy=999)])
        future = writer.record(bad)
        with self.assertRaises(ObservationConflict): future.result(3)
        observer._writes = [(bad, future)]
        with patch.object(writer, 'record', side_effect=AssertionError('No exit retry')):
            self.finish()
        self.assertEqual(observer._writes, [])
        self.assertEqual(observer.exit_discarded_writes, 1)
        self.assertIsNotNone(writer.last_error)
        with MarketStore(writer.destination, read_only=True) as store:
            self.assertEqual(store.get_stats().observations, 1)
            self.assertEqual(store.get_current(1,None)['commodities'][0]['commander_buy_price'],100)
        data = self.export('policy-B-conflict-discarded-exited')
        self.assertEqual(data['phase'], 'finished')
        self.assertEqual(data['market']['result_pending'], 0)
        self.assertIn('market_observation_conflict', data['reasons'])
        self.assertIn('market_write_discarded', data['reasons'])

    def test_running_and_queued_writes_finish_then_failure_is_discarded(self):
        writer, observer = self.writer(); writer.ready.result(3)
        writer.record(observation()).result(3)
        entered, release = threading.Event(), threading.Event()
        original = MarketStore.record_observation
        calls=[]
        good, bad = observation(mid=2), observation(rows=[commodity(buy=999)])
        def record(store, value):
            calls.append(value['market_id'])
            if value['market_id']==2:
                entered.set()
                if not release.wait(4): raise AssertionError('Synthetic release timeout')
            return original(store,value)
        try:
            with patch.object(MarketStore,'record_observation',record):
                first=writer.record(good); self.assertTrue(entered.wait(2))
                second=writer.record(bad); observer._writes=[(good,first),(bad,second)]
                self.w.close(); c=self.w._exit_controller; c.started-=30
                QTest.qWait(50)
                self.assertTrue(self.w.isVisible()); self.assertFalse(c.approved)
                self.assertFalse(first.done()); self.assertFalse(second.done())
                self.assertFalse(writer.is_stopped()); self.assertEqual(writer.pending_count(),2)
                data=self.export('policy-running-writes-not-aborted')
                self.assertEqual(data['market']['running'],1)
                self.assertEqual(data['market']['queued'],1)
                release.set(); self.wait(lambda:not self.w.isVisible())
                self.assertTrue(first.result(3).inserted)
                with self.assertRaises(ObservationConflict): second.result(3)
                self.assertEqual(calls,[2,1])
        finally: release.set()
        with MarketStore(writer.destination,read_only=True) as store:
            self.assertEqual(store.get_stats().observations,2)
        self.assertEqual(observer.exit_discarded_writes,1)
        self.export('policy-queue-drained-failure-discarded')

    def test_market_failure_cannot_bypass_important_worker(self):
        (self.root/'legacy.json').write_text('{')
        writer, observer=self.writer()
        with self.assertRaises(Exception): writer.ready.result(3)
        job,release=self.work()
        self.w.close(); QTest.qWait(60)
        self.assertTrue(self.w.isVisible()); self.assertFalse(self.w._exit_controller.approved)
        self.assertTrue(writer.exit_errors_discarded)
        release.set(); self.wait(lambda:not self.w.isVisible())

    def test_cancel_running_market_write_then_close_again(self):
        writer,observer=self.writer(); writer.ready.result(3)
        entered,release=threading.Event(),threading.Event()
        original=MarketStore.record_observation
        def record(store,value):
            entered.set()
            if not release.wait(4): raise AssertionError('Synthetic release timeout')
            return original(store,value)
        try:
            with patch.object(MarketStore,'record_observation',record):
                value=observation(); future=writer.record(value);observer._writes=[(value,future)]
                self.assertTrue(entered.wait(2));self.w.close();QTest.qWait(30)
                self.w._exit_controller.cancel()
                self.assertFalse(observer.exit_draining)
                self.assertTrue(self.w.isVisible());self.assertFalse(future.done())
                release.set();self.assertTrue(future.result(3).inserted)
            observer._poll_writes();self.finish()
        finally:release.set()
        with MarketStore(writer.destination,read_only=True) as store:
            self.assertEqual(store.get_stats().observations,1)
        self.assertEqual(observer.exit_discarded_writes,0)

    def test_queued_consume_and_repeated_close_cannot_retry_failed_record(self):
        writer,observer=self.writer();writer.ready.result(3)
        writer.record(observation()).result(3)
        bad=observation(rows=[commodity(buy=999)]);future=writer.record(bad)
        with self.assertRaises(ObservationConflict):future.result(3)
        observer._writes=[(bad,future)]
        job,release=self.work()
        self.w.shortcut_manager.set_binding('quit','Ctrl+Q')
        with patch.object(writer,'record',side_effect=AssertionError('No retry during exit')):
            self.button.click();QTest.qWait(20)
            for _ in range(5):
                observer.consume([])
                self.w._exit_controller.dialog.repeat()
                self.w.close()
            self.assertEqual(observer.exit_discarded_writes,1)
            self.assertEqual(observer._writes,[])
            self.assertTrue(self.w.isVisible())
            self.w._exit_controller.cancel();self.assertFalse(observer.exit_draining)
            release.set();self.wait(lambda:not self.gate.pending())
            self.finish()
        self.assertEqual(observer.exit_discarded_writes,1)

    def capture(self, *, expired=False, sqlite=True):
        case=captures.ObserverTests();case.setUp();self.addCleanup(case.doCleanups)
        case.observer.use_market_store=sqlite
        case.append(captures.event())
        case.write_sidecar(dict(captures.sidecar(),MarketID=999))
        self.assertFalse(case.consume())
        if expired:case.tick+=16
        self.w.state.observed_markets=case.observer
        return case

    def test_expired_capture_is_discarded_even_if_sidecar_arrives_later(self):
        case=self.capture(expired=True);case.write_sidecar()
        before=case.path.read_bytes(),(case.root/'Market.json').read_bytes()
        with patch('cmdrhelper.observed_market_observer.read_market',side_effect=AssertionError('No expired capture retry')):
            self.finish()
        self.assertIsNone(case.observer.pending)
        self.assertEqual(case.observer.exit_expired_captures,1)
        self.assertEqual(before,(case.path.read_bytes(),(case.root/'Market.json').read_bytes()))
        data=self.export('policy-C-expired-capture-exited')
        self.assertEqual(data['pending_count'],0)
        self.assertEqual(data['market']['captures_open'],0)
        self.assertEqual(data['market']['expired_captures_discarded'],1)
        self.assertIn('market_capture_expired',data['reasons'])

    def test_unavailable_nonexpired_capture_does_not_wait_for_fifteen_seconds(self):
        case=self.capture()
        deadline=case.observer.pending[2]
        self.finish()  # Qt fixture timeout is 4 s; synthetic clock never advances.
        self.assertLess(case.tick,deadline)
        self.assertIsNone(case.observer.pending)
        self.assertEqual(case.observer.exit_discarded_captures,1)
        self.assertEqual(case.observer.exit_expired_captures,0)
        self.export('policy-capture-unavailable-no-delay')

    def test_nonexpired_valid_capture_commits_once(self):
        case=self.capture();case.write_sidecar()
        self.finish()
        writer=case.observer.writer
        with MarketStore(writer.destination,read_only=True) as store:
            self.assertEqual(store.get_stats().observations,1)
            self.assertEqual(store.get_current(123,None)['commodities'],captures.snapshot()['commodities'])
        self.assertEqual(case.observer.exit_discarded_captures,0)
        self.assertEqual(case.observer.exit_discarded_writes,0)
        self.export('policy-valid-capture-saved')

    def test_failed_legacy_cache_write_is_not_retried_on_exit(self):
        case=self.capture(sqlite=False);case.write_sidecar()
        with patch.object(case.cache,'put',return_value=False) as write:
            self.finish()
            write.assert_called_once()
        self.assertEqual(case.observer.exit_discarded_writes,1)
        self.assertEqual(case.observer.exit_discarded_captures,1)
        self.assertIsNone(case.cache.get(captures.FID,123))
        self.assertIn('market_write_discarded',self.export('policy-cache-failure-discarded')['reasons'])

    def test_market_discard_does_not_override_checkpoint_error(self):
        from types import SimpleNamespace
        from PySide6.QtCore import QTimer
        observer=ObservedMarketObserver(monotonic=lambda:20)
        observer.pending=({'event':'Market'},{},15)
        self.w.state.observed_markets=observer
        checkpoint=SimpleNamespace(_running=False,_dirty=False,_exit_write_error=True,
            timer=QTimer(),cargo_retry=QTimer(),retry_pending_save=lambda:None)
        self.w.state.mining_inventory_controller=checkpoint
        self.w.close();QTest.qWait(60)
        self.assertTrue(self.w.isVisible());self.assertFalse(self.w._exit_controller.approved)
        self.assertTrue(checkpoint._exit_write_error)
        self.assertIn('mining_checkpoint_failed',self.export('policy-checkpoint-still-protected')['reasons'])
        self.w._exit_controller.cancel()
        del self.w.state.mining_inventory_controller
        self.finish()
