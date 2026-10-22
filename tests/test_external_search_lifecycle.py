"""Real Qt threadpool ownership regressions; all search responses are synthetic."""
import gc
import os
import sys
import threading
import time
import unittest
import weakref
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QCoreApplication, QEvent, QThreadPool, QTimer
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication, QWidget
from shiboken6 import isValid

from cmdrhelper.external_system import search_system
from cmdrhelper.route_planner.system_resolution import SpanshError
from cmdrhelper.ui.external_system_search import ExternalSystemSearch, SearchWorker
from tests.test_external_system import tai, request


class SearchLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.owner = QWidget()
        self.owner.ui_theme = 'dark'
        self.owner.commander_id = 1
        self.owner.system_address = 1
        self.pool = QThreadPool()
        self.pool.setMaxThreadCount(1)
        with patch('cmdrhelper.external_system.edsm_snapshot', return_value=None):
            self.model = search_system('Tai Qing', request=request, fetch=lambda _: tai())
        self.provider = Mock(return_value=self.model)
        self.search = ExternalSystemSearch(self.owner, None, provider=self.provider, pool=self.pool)
        self.gates = []

    def events(self):
        self.app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.processEvents()

    def wait_until(self, predicate):
        deadline = time.monotonic() + 3
        while not predicate() and time.monotonic() < deadline:
            QTest.qWait(1)
        self.assertTrue(predicate())

    def drain(self):
        # Blocking is restricted to this test harness, never the product GUI.
        self.assertTrue(self.pool.waitForDone(3000))
        self.events()
        gc.collect()

    def tearDown(self):
        for gate in self.gates:
            gate.set()
        self.drain()
        if isValid(self.owner):
            self.owner.close()
            self.owner.deleteLater()
        self.events()

    def start(self, name='Tai Qing'):
        self.search.edit.setText(name)
        self.search.start_search()
        return self.search.workers[self.search.request_state['token']]

    def gate(self):
        gate = threading.Event()
        self.gates.append(gate)
        return gate

    def test_30_and_100_completed_searches_release_workers_and_signals(self):
        workers, signals = [], []
        for number in range(1, 101):
            worker = self.start()
            workers.append(weakref.ref(worker))
            signals.append(weakref.ref(worker.signals))
            del worker
            self.drain()
            self.assertEqual(len(self.search.windows), 1)
            self.search.windows[0].close()
            self.events()
            if number in (30, 100):
                gc.collect()
                self.assertEqual(self.pool.activeThreadCount(), 0)
                self.assertFalse(self.search.workers)
                self.assertFalse(self.search.windows)
                self.assertEqual(sum(ref() is not None for ref in workers), 0)
                self.assertEqual(sum(ref() is not None for ref in signals), 0)
                self.assertFalse(any(ref() is not None and isValid(ref()) for ref in workers + signals))

    def test_queued_result_survives_pool_deleting_runnable_before_gui_delivery(self):
        worker = self.start()
        signals = worker.signals
        spy = QSignalSpy(signals.finished)
        self.assertTrue(self.pool.waitForDone(3000))
        self.assertFalse(isValid(worker))
        self.assertFalse(self.search.windows)  # GUI has not consumed the result.
        self.events()
        self.assertEqual(spy.count(), 1)
        self.assertEqual(len(self.search.windows), 1)
        self.assertFalse(isValid(signals))
        self.assertFalse(self.search.workers)

    def test_result_before_run_return_does_not_delete_running_runnable(self):
        release, emitted = self.gate(), threading.Event()

        class HeldReturnWorker(SearchWorker):
            def run(self):
                super().run()
                emitted.set()
                release.wait(3)

        with patch('cmdrhelper.ui.external_system_search.SearchWorker', HeldReturnWorker):
            worker = self.start()
        self.wait_until(lambda: emitted.is_set() and len(self.search.windows) == 1)
        self.events()
        self.assertFalse(self.search.workers)
        self.assertTrue(isValid(worker))
        self.assertEqual(self.pool.activeThreadCount(), 1)
        ticks = []
        QTimer.singleShot(0, lambda: ticks.append(True))
        self.events()
        self.assertTrue(ticks)  # No GUI wait for run() to return.
        release.set()
        self.drain()
        self.assertFalse(isValid(worker))

    def test_errors_unknown_ambiguous_and_timeout_release_once(self):
        for error in (SpanshError('system_unknown'), SpanshError('ambiguous'),
                      TimeoutError('synthetic timeout'), ValueError('bad response')):
            with self.subTest(error=repr(error)):
                self.search.provider = Mock(side_effect=error)
                worker = self.start()
                signals = worker.signals
                spy = QSignalSpy(signals.finished)
                self.drain()
                self.assertEqual(spy.count(), 1)
                self.assertFalse(isValid(worker))
                self.assertFalse(isValid(signals))
                self.assertFalse(self.search.workers)
                self.assertFalse(self.search.windows)
                self.assertTrue(self.search.status.text())
                self.search.provider.assert_called_once()

    def test_fast_superseding_requests_skip_queued_stale_job_and_coalesce_identical(self):
        release, started = self.gate(), threading.Event()

        def provider(name, path):
            if name == 'First':
                started.set()
                release.wait(3)
            return self.model

        self.search.provider = Mock(side_effect=provider)
        first = self.start('First')
        self.wait_until(started.is_set)
        second = self.start('Second')
        third = self.start()
        self.assertIs(self.start(), third)
        workers = [first, second, third]
        spies = [QSignalSpy(worker.signals.finished) for worker in workers]
        release.set()
        self.drain()
        self.assertEqual(self.search.provider.call_count, 2)
        self.assertEqual([spy.count() for spy in spies], [1, 1, 1])
        self.assertTrue(all(not isValid(worker) for worker in workers))
        self.assertFalse(self.search.workers)
        self.assertEqual(len(self.search.windows), 1)

    def test_system_and_commander_switch_preserve_result_and_release_worker(self):
        release, started = self.gate(), threading.Event()

        def provider(*_):
            started.set()
            release.wait(3)
            return self.model

        self.search.provider = provider
        worker = self.start()
        self.wait_until(started.is_set)
        self.owner.commander_id = 2
        self.owner.system_address = 999
        self.search.hide()  # Changing the page must not cancel the search.
        release.set()
        self.drain()
        self.assertFalse(isValid(worker))
        self.assertEqual(len(self.search.windows), 1)
        self.assertEqual(self.search.windows[0].system_address, self.model['system_address'])
        self.search.windows[0].close()
        self.events()
        self.assertFalse(self.search.windows)

    def test_owner_close_or_destruction_during_work_discards_late_result(self):
        for destroy in (False, True):
            with self.subTest(destroy=destroy):
                owner = QWidget()
                release, started = self.gate(), threading.Event()

                def provider(*_):
                    started.set()
                    release.wait(3)
                    return self.model

                search = ExternalSystemSearch(owner, None, provider=provider, pool=self.pool)
                search.edit.setText('Tai Qing')
                search.start_search()
                worker = next(iter(search.workers.values()))
                signals = worker.signals
                spy = QSignalSpy(signals.finished)
                self.wait_until(started.is_set)
                if destroy:
                    owner.deleteLater()
                else:
                    owner.show()
                    owner.close()
                self.events()
                self.assertNotEqual(search.request_state['token'], worker.token)
                self.assertFalse(search.workers)
                self.assertTrue(isValid(worker))
                release.set()
                with patch('cmdrhelper.ui.external_system_search.ExternalSystemWindow') as window:
                    self.drain()
                    window.assert_not_called()
                self.assertEqual(spy.count(), 1)
                self.assertFalse(isValid(worker))
                self.assertFalse(isValid(signals))
                if isValid(owner):
                    owner.deleteLater()
                    self.events()

    def test_close_and_reopen_does_not_reuse_running_request_token(self):
        release, started = self.gate(), threading.Event()

        def provider(name, path):
            if name == 'First':
                started.set()
                release.wait(3)
            return self.model

        self.search.provider = Mock(side_effect=provider)
        first = self.start('First')
        self.wait_until(started.is_set)
        self.owner.show()
        self.owner.close()
        self.owner.show()
        second = self.start()
        self.assertGreater(second.token, first.token)
        release.set()
        self.drain()
        self.assertEqual(self.search.provider.call_count, 2)
        self.assertFalse(isValid(first))
        self.assertFalse(isValid(second))
        self.assertFalse(self.search.workers)
        self.assertEqual(len(self.search.windows), 1)

    def test_gui_callback_error_does_not_prevent_cleanup(self):
        errors = []
        with patch('cmdrhelper.ui.external_system_search.ExternalSystemWindow',
                   side_effect=RuntimeError('synthetic callback failure')), \
                patch.object(sys, 'excepthook', side_effect=lambda *args: errors.append(args)):
            worker = self.start()
            signals = worker.signals
            spy = QSignalSpy(signals.finished)
            self.drain()
        self.assertEqual(len(errors), 1)
        self.assertEqual(str(errors[0][1]), 'synthetic callback failure')
        self.assertEqual(spy.count(), 1)
        self.assertFalse(isValid(worker))
        self.assertFalse(isValid(signals))
        self.assertFalse(self.search.workers)
        self.assertFalse(self.search.windows)
