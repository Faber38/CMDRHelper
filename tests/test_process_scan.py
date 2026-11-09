"""Synthetic process evidence and real Qt event delivery; never scan live /proc."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from cmdrhelper.game_instances import GameInstance, ProcessSnapshot
from cmdrhelper.process_scan import ProcessScan


class ProcessScanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.context = ('source-A',)
        self.now = [10.]
        self.owner = threading.get_ident()

    def scanner(self, inspector, real_clock=False):
        def context():
            self.assertEqual(threading.get_ident(), self.owner)
            return self.context
        scanner = ProcessScan(inspector, context,
                              clock=time.monotonic if real_clock else lambda: self.now[0])
        self.addCleanup(scanner.stop)
        return scanner

    def wait(self, predicate, timeout=3):
        deadline = time.monotonic()+timeout
        while time.monotonic() < deadline:
            self.app.processEvents()
            if predicate():
                return
            time.sleep(.001)
        self.fail('queued result not delivered')

    @staticmethod
    def snapshot(ticks=100):
        return ProcessSnapshot(True, [GameInstance(12, 0, start_ticks=ticks)])

    def test_slow_scan_does_not_block_gui_and_requests_coalesce(self):
        entered, release = threading.Event(), threading.Event()
        calls, ticks, results = [], [], []
        def inspect():
            calls.append(threading.get_ident())
            entered.set()
            release.wait(4)
            return self.snapshot()
        scanner = self.scanner(inspect, real_clock=True)
        self.addCleanup(release.set)
        scanner.ready.connect(lambda: results.append(scanner.read()))
        timer = QTimer(); timer.setInterval(5); timer.timeout.connect(lambda: ticks.append(1))
        timer.start(); self.addCleanup(timer.stop)
        start = time.monotonic()
        scanner.request()
        self.wait(entered.is_set)
        for _ in range(100):
            self.assertFalse(scanner.read().available)
        QTimer.singleShot(2200, release.set)
        self.wait(lambda: bool(results))
        self.assertGreaterEqual(len(ticks), 10)
        self.assertEqual(calls, [calls[0]])
        self.assertNotEqual(calls[0], self.owner)
        self.assertFalse(results[0].available)  # Scan exceeded freshness bound.
        self.assertGreater(time.monotonic()-start, 2.)
        self.assertFalse(scanner.pending)
        self.app.processEvents()
        self.assertEqual(len(calls), 1)  # No automatic retry loop.

    def test_source_change_rejects_old_result_and_runs_one_requested_replacement(self):
        release, entered = threading.Event(), threading.Event()
        calls, results = [], []
        def inspect():
            calls.append(1)
            if len(calls) == 1:
                entered.set(); release.wait(2)
            return self.snapshot(100*len(calls))
        scanner = self.scanner(inspect); self.addCleanup(release.set)
        scanner.ready.connect(lambda: results.append(scanner.read()))
        scanner.request(); self.wait(entered.is_set)
        self.context = ('source-B',)
        for _ in range(20): scanner.request()
        self.assertEqual(len(calls), 1)
        release.set(); self.wait(lambda: len(results) == 2)
        self.assertFalse(results[0].available)
        self.assertEqual(results[1].instances[0].identity, (12, 200))
        self.assertEqual(len(calls), 2)

    def test_generation_change_and_delayed_delivery_are_rejected(self):
        scanner = self.scanner(self.snapshot)
        results = []; scanner.ready.connect(lambda: results.append(scanner.read()))
        scanner.request(); scanner.invalidate()
        self.wait(lambda: len(results) == 1)
        self.assertFalse(results[-1].available)
        scanner.request(); self.wait(lambda: len(results) == 2)
        self.assertTrue(results[-1].available)
        self.now[0] += .101
        self.assertFalse(scanner.current(results[-1]))
        # Hold the GUI queue until the completed result is already stale.
        finished = threading.Event()
        def inspect():
            finished.set()
            return self.snapshot()
        scanner._inspector = inspect
        scanner.request()
        self.assertTrue(finished.wait(1))
        self.now[0] += .101
        self.wait(lambda: len(results) == 3)
        self.assertFalse(results[-1].available)

    def test_game_start_exit_restart_and_missing_stable_identity(self):
        inspector = Mock()
        scanner = self.scanner(inspector)
        results = []; scanner.ready.connect(lambda: results.append(scanner.read()))
        for index, snapshot in enumerate([ProcessSnapshot(True), self.snapshot(100),
                                         ProcessSnapshot(True), self.snapshot(200),
                                         ProcessSnapshot(True, [GameInstance(12, 0)])], 1):
            inspector.return_value = snapshot
            scanner.request(); self.wait(lambda: len(results) == index)
        self.assertEqual(results[0].instances, [])
        self.assertEqual(results[1].instances[0].identity, (12, 100))
        self.assertEqual(results[2].instances, [])
        self.assertEqual(results[3].instances[0].identity, (12, 200))
        self.assertFalse(results[4].available)

    def test_real_proc_identity_recheck_is_preserved_in_worker(self):
        from test_process_selection_regression import StableProcessTests
        from cmdrhelper.game_instances import inspect_instances
        f = StableProcessTests(); f.setUp(); self.addCleanup(f.doCleanups)
        original = Path.read_text
        reads = []
        def changed(path, *args, **kwargs):
            if path == f.entry/'stat':
                reads.append(threading.get_ident())
                if len(reads) == 2:
                    f.start(200)
            return original(path, *args, **kwargs)
        scanner = self.scanner(lambda: inspect_instances(f.proc))
        results = []; scanner.ready.connect(lambda: results.append(scanner.read()))
        with patch.object(Path, 'read_text', changed):
            scanner.request(); self.wait(lambda: bool(results))
        self.assertFalse(results[0].available)
        self.assertEqual(results[0].instances, [])
        self.assertEqual(len(reads), 2)
        self.assertTrue(all(thread != self.owner for thread in reads))

    def test_exception_and_shutdown_do_not_apply_or_restart(self):
        inspector = Mock(side_effect=OSError('PRIVATE'))
        scanner = self.scanner(inspector)
        results = []; scanner.ready.connect(lambda: results.append(scanner.read()))
        scanner.request(); self.wait(lambda: len(results) == 1)
        self.assertFalse(results[-1].available)
        release, entered = threading.Event(), threading.Event()
        def inspect():
            entered.set(); release.wait(2)
            return self.snapshot()
        scanner._inspector = inspect; self.addCleanup(release.set)
        scanner.request(); self.wait(entered.is_set)
        start = time.monotonic(); scanner.stop()
        self.assertLess(time.monotonic()-start, .05)
        scanner.request(); self.assertFalse(scanner.read().available)
        release.set()
        self.wait(lambda: not any(t.name == 'CMDRHelper-ProcessScan' for t in threading.enumerate()))
        self.assertEqual(len(results), 1)

    def test_arrival_requires_current_confirmed_process_evidence(self):
        from test_mission_arrival import ArrivalSourceTests
        f = ArrivalSourceTests(); f.setUp(); self.addCleanup(f.doCleanups)
        snapshot = ProcessSnapshot(True, [GameInstance(12, 0, journals=(str(f.path),), start_ticks=100)])
        scanner = self.scanner(lambda: snapshot)
        f.state.sources._process_scanner = scanner
        f.state.sources._current_processes = scanner.read
        self.assertIsNone(f.source.snapshot(f.state))
        self.wait(lambda: not scanner.pending)
        self.assertIsNotNone(f.source.snapshot(f.state))
        scanner.invalidate()
        self.assertIsNone(f.source.snapshot(f.state))
        self.wait(lambda: not scanner.pending)
        # Expiry during journal/projection work must also revoke authorization.
        with patch('cmdrhelper.mission_arrival.presentation_is_current', return_value=False):
            self.assertIsNone(f.source.snapshot(f.state))
        self.assertIsNone(f.source.confirmed)
        f.mock_process.assert_not_called()

    def test_exit_pause_prevents_a_queued_replacement_scan(self):
        release, entered = threading.Event(), threading.Event()
        calls = []
        def inspect():
            calls.append(1); entered.set(); release.wait(2)
            return self.snapshot()
        scanner = self.scanner(inspect); self.addCleanup(release.set)
        scanner.request(); self.wait(entered.is_set)
        scanner.invalidate(); scanner.request()
        scanner._allowed = lambda: False
        release.set(); self.wait(lambda: not scanner.pending)
        self.assertFalse(scanner.read().available)
        self.assertEqual(len(calls), 1)

    def test_result_only_refreshes_a_changed_selection(self):
        from types import SimpleNamespace
        from PySide6.QtCore import QObject
        from cmdrhelper.source_manager import SourceManager
        manager = SourceManager.__new__(SourceManager); QObject.__init__(manager)
        manager.state = SimpleNamespace(_startup_cancel=threading.Event(), viewed_commander_id=1)
        manager.preferred_source = 'a'
        manager._current_processes = lambda: ProcessSnapshot(False)
        manager.choose = Mock()
        manager.refresh_selected = Mock()
        manager._process_ready()
        manager.refresh_selected.assert_not_called()
        manager.choose.side_effect = lambda: setattr(manager, 'preferred_source', 'b')
        manager._process_ready()
        manager.refresh_selected.assert_called_once_with()

    def test_profile_on_off_and_private_values(self):
        code = r'''
import json, tempfile, threading, time, os
from pathlib import Path
from PySide6.QtWidgets import QApplication
from cmdrhelper import performance_profile as p
from cmdrhelper.game_instances import ProcessSnapshot
from cmdrhelper.process_scan import ProcessScan
app=QApplication([])
with tempfile.TemporaryDirectory() as root:
    if p.ENABLED: p._recorder=p.Recorder(root)
    recorder=p._recorder
    release=threading.Event()
    def inspect():
        with p.section('process.inspect_instances'):
            release.wait(1)
            return ProcessSnapshot(False)
    s=ProcessScan(inspect,lambda:('PRIVATE_PATH','PRIVATE_FID'))
    s.request()
    for _ in range(10): s.request()
    s.invalidate();release.set()
    deadline=time.monotonic()+2
    while s.pending and time.monotonic()<deadline:
        app.processEvents();time.sleep(.001)
    assert not s.pending
    s.stop()
    if recorder:
        recorder.queue.join();p.shutdown()
        data=json.loads(Path(str(recorder.path)+'.summary.json').read_text())
        groups=data['aggregates']
        assert any(a['point']=='process.scan_worker.end' and a['thread']=='worker' for a in groups)
        assert any(a['point']=='process.inspect_instances.end' and a['thread']=='worker' for a in groups)
        assert any(a['point']=='process.scan_apply.end' and a['thread']=='main' for a in groups)
        wait=next(a for a in groups if a['point']=='process.scan_wait')
        assert wait['metrics']['scan_requests']['sum']==11
        assert wait['metrics']['scan_coalesced']['sum']==10
        discarded=next(a for a in groups if a['point']=='process.scan_discard')
        assert discarded['metrics']['scan_discarded']['sum']==1
        assert 'PRIVATE' not in recorder.path.read_text()
    else:
        assert not list(Path(root).iterdir())
'''
        for enabled in ['0', '1']:
            result = subprocess.run([sys.executable, '-B', '-c', code], capture_output=True,
                                    text=True, timeout=10, env=dict(os.environ,
                                    CMDRHELPER_PROFILE=enabled, QT_QPA_PLATFORM='offscreen'))
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_screenshot_wait_preserves_pending_file_and_retries_on_result(self):
        from test_screenshot_sources import SourcesTests
        from dataclasses import replace
        f = SourcesTests(); f.setUp(); self.addCleanup(f.doCleanups)
        scanner = self.scanner(lambda: ProcessSnapshot(True,
            [replace(p, start_ticks=100) for p in f.snapshot().instances]))
        f.manager._process_scanner = scanner
        f.manager._current_processes = scanner.read
        scanner.ready.connect(f.view._process_ready)
        source = f.bmp()
        f.view._scan()
        self.assertIsNone(f.view._context)
        self.assertEqual(f.workers, [])
        self.wait(lambda: not scanner.pending)
        self.assertEqual(f.view._pending[str(source.resolve())][1], 1)
        scanner.invalidate()
        f.view._scan()  # Do not erase the first stable-file observation.
        self.wait(lambda: not scanner.pending)
        self.assertEqual([w.source for w in f.workers], [source])
        self.assertEqual(f.workers[0].target.parent.name, 'TEST_ALPHA_FA')

    def test_manual_screenshot_request_waits_for_fresh_identity(self):
        from test_screenshot_sources import SourcesTests
        from dataclasses import replace
        f = SourcesTests(); f.setUp(); self.addCleanup(f.doCleanups)
        scanner = self.scanner(lambda: ProcessSnapshot(True,
            [replace(p, start_ticks=100) for p in f.snapshot().instances]))
        f.manager._process_scanner = scanner
        f.manager._current_processes = scanner.read
        scanner.ready.connect(f.view._process_ready)
        f.view.auto_check.setChecked(False)
        source = f.bmp()
        f.view._convert_existing()
        self.assertEqual(f.workers, [])
        self.wait(lambda: not scanner.pending)
        self.assertEqual([w.source for w in f.workers], [source])

    def test_expired_evidence_cannot_commit_commander_selection(self):
        from test_source_manager import ManagerTests
        ManagerTests.setUpClass()
        f = ManagerTests(); self.addCleanup(f.doCleanups); f.setUp()
        manager = f.state.sources
        runtime = list(manager.runtimes.values())[-1]
        journal = runtime.processor.sessions[-1]['journal_file']
        snapshot = ProcessSnapshot(True, [GameInstance(12, 0, journals=(journal,), start_ticks=100)])
        f.state.set_follow_live_commander(False)
        f.observe_processes(snapshot)
        scanner = manager._process_scanner
        now = [100.]; scanner._clock = lambda: now[0]
        before = f.state.viewed_commander_id
        original = f.state.database.list_commanders
        def slow_commanders():
            now[0] += .2
            return original()
        with patch.object(f.state.database, 'list_commanders', side_effect=slow_commanders):
            manager._select(runtime.processor.sessions[-1]['commander_id'],
                            processes=scanner.read(), source=runtime.source.id)
        self.assertEqual(f.state.viewed_commander_id, before)
