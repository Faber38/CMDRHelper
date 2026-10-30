"""Real two-slot status pool: obsolete queued work and late network responses."""
import tempfile
import threading
import time
import unittest
from pathlib import Path
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from cmdrhelper.edsm_system_status import EdsmSystemStatus


class StatusQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.settings = QSettings(str(Path(tmp.name) / 'test.ini'), QSettings.IniFormat)

    def wait(self, condition):
        end = time.monotonic() + 4
        while time.monotonic() < end:
            self.app.processEvents()
            if condition():
                return
            time.sleep(.005)
        self.fail('status condition timed out')

    def arrive(self, status, name, fid='F1'):
        status.observe([dict(event='FSDJump', StarSystem=name)], fid)

    def test_two_running_slots_finish_but_obsolete_queued_jobs_are_removed(self):
        entered_a, entered_b, release_a, release_b = [threading.Event() for _ in range(4)]
        calls, notices = [], []
        def fetch(name, address):
            calls.append(name)
            if name == 'A':
                entered_a.set(); release_a.wait(4)
            if name == 'B':
                entered_b.set(); release_b.wait(4)
            return 'known' if name == 'E' else 'unknown'
        status = EdsmSystemStatus(self.settings, fetch=fetch)
        status.set_enabled(True)
        status.notice.connect(notices.append)
        try:
            self.arrive(status, 'A')
            self.wait(entered_a.is_set)
            self.arrive(status, 'B')
            self.wait(entered_b.is_set)
            for name in ('C', 'D', 'E'):
                self.arrive(status, name)
            self.assertEqual(calls, ['A', 'B'])
            self.assertEqual(len(status.workers), 3)  # Two running, only newest queued.
            self.assertEqual(status.pool.maxThreadCount(), 2)
            release_a.set()
            self.wait(lambda: status.status == 'known')
            self.assertEqual(calls, ['A', 'B', 'E'])
            release_b.set()
            status.pool.waitForDone(3000)
            self.app.processEvents()
            self.assertEqual(len(notices), 1)
            self.assertEqual(status.status, 'known')
            self.assertEqual(status.workers, {})
        finally:
            release_a.set(); release_b.set()
            status.pool.waitForDone(3000)
            self.app.processEvents()

    def test_a_b_a_late_first_a_does_not_replace_new_a(self):
        started, release = threading.Event(), threading.Event()
        first = [True]
        def fetch(name, address):
            if first[0]:
                first[0] = False
                started.set(); release.wait(4)
                return 'unknown'
            return 'known'
        status = EdsmSystemStatus(self.settings, fetch=fetch)
        status.set_enabled(True)
        try:
            self.arrive(status, 'A')
            self.wait(started.is_set)
            self.arrive(status, 'B')
            self.arrive(status, 'A')
            self.wait(lambda: status.status == 'known')
            release.set()
            status.pool.waitForDone(3000)
            self.app.processEvents()
            self.assertEqual((status.name, status.status), ('A', 'known'))
        finally:
            release.set()
            status.pool.waitForDone(3000)
            self.app.processEvents()

    def test_commander_change_and_disable_drop_waiting_and_running_results(self):
        started, release = threading.Event(), threading.Event()
        def fetch(*args):
            started.set(); release.wait(4)
            return 'known'
        status = EdsmSystemStatus(self.settings, fetch=fetch)
        status.pool.setMaxThreadCount(1)
        status.set_enabled(True)
        notices = []
        status.notice.connect(notices.append)
        try:
            self.arrive(status, 'A')
            self.wait(started.is_set)
            self.arrive(status, 'B', fid='F2')
            self.assertEqual(len(status.workers), 2)
            status.set_enabled(False)
            self.assertEqual(len(status.workers), 1)
            release.set()
            status.pool.waitForDone(3000)
            self.app.processEvents()
            self.assertEqual(notices, [])
            self.assertIsNone(status.status)
            self.assertEqual(status.workers, {})
        finally:
            release.set()
            status.pool.waitForDone(3000)
