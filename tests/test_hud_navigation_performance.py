"""Deterministic 5-Hz tracking replay and isolated navigation lifecycle checks.

No desktop manipulation, user settings, user DB or network access.
"""
import ctypes
import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QRect
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from cmdrhelper.planet_navigation import PlanetNavigationController
from cmdrhelper.ui.navigation_hud import NavigationHud, X11WindowTracker
from cmdrhelper.ui.planet_navigation_window import PlanetNavigationWindow


class SimulatedX11(X11WindowTracker):
    def __init__(self):
        self._reset_cache()
        self.present = True
        self.foreground = 42
        self.hidden = False
        self.viewable = True
        self.rect = QRect(0, 0, 800, 600)
        self.compositor_available = Mock(return_value=True)
        self._active_window = Mock(side_effect=lambda: self.foreground)
        self._read = Mock(side_effect=self.read)

    def read(self, *args):
        if args[0] == "wmctrl":
            return '0x2a 0 steam_app_359320 host Elite - Dangerous' if self.present else ''
        if not self.present:
            raise OSError("window gone")
        if args[0] == "xprop":
            return '_NET_WM_STATE_HIDDEN' if self.hidden else ''
        x, y, w, h = self.rect.getRect()
        return (f'Absolute upper-left X: {x}\nAbsolute upper-left Y: {y}\n'
                f'Width: {w}\nHeight: {h}\nMap State: '
                + ('IsViewable' if self.viewable else 'IsUnMapped'))


class TrackingPerformanceTests(unittest.TestCase):
    def test_invalid_overlay_map_state_fails_closed_with_backoff(self):
        tracker = SimulatedX11()
        tracker._read.return_value = ''
        tracker._read.side_effect = None
        with patch('cmdrhelper.ui.navigation_hud.time.monotonic', return_value=5):
            self.assertFalse(tracker.window_is_viewable(99))
            self.assertTrue(tracker.viewability_failed)
            self.assertEqual(tracker._retry_after, 6)

    def test_process_budget_at_5hz_for_twenty_seconds(self):
        # Baseline, same 100 ticks: foreground=500, background=400, absent=200.
        for mode, maximum in (("foreground", 320), ("background", 20), ("absent", 20)):
            with self.subTest(mode=mode):
                tracker = SimulatedX11()
                tracker.foreground = 42 if mode == "foreground" else 7
                tracker.present = mode != "absent"
                for i in range(100):
                    with patch('cmdrhelper.ui.navigation_hud.time.monotonic', return_value=i / 5):
                        target = tracker.current()
                        if target:
                            tracker.window_is_viewable(99)
                self.assertLessEqual(tracker._read.call_count, maximum)
                self.assertFalse(any(c.args[:2] == ('xprop', '-root')
                                     for c in tracker._read.call_args_list))

    def test_focus_is_never_cached_and_rechecked_after_slow_commands(self):
        tracker = SimulatedX11()
        self.assertIsNotNone(tracker.current())
        tracker.foreground = 7
        self.assertIsNone(tracker.current())
        self.assertEqual(tracker.reason, 'foreground')
        tracker._active_window.side_effect = [42, 7]
        self.assertIsNone(tracker.current())
        self.assertEqual(tracker.reason, 'foreground')

    def test_minimize_close_reopen_and_negative_monitor_geometry(self):
        tracker = SimulatedX11()
        with patch('cmdrhelper.ui.navigation_hud.time.monotonic', return_value=0):
            self.assertIsNotNone(tracker.current())
            tracker.hidden = True
            self.assertIsNone(tracker.current())
            tracker.hidden = False
            tracker.viewable = False
            self.assertIsNone(tracker.current())
            tracker.viewable = True
            # No geometry TTL: moves/resizes/monitor changes apply on the next tick.
            for rect in (QRect(10, 20, 900, 700), QRect(-1920, -50, 1920, 1080)):
                tracker.rect = rect
                self.assertEqual(tracker.current().geometry, rect)
            tracker.present = False
            self.assertIsNone(tracker.current())
            self.assertEqual(tracker.reason, 'error')
        tracker.present = True
        with patch('cmdrhelper.ui.navigation_hud.time.monotonic', return_value=1.01):
            self.assertIsNotNone(tracker.current())

    def test_absent_identity_expires_and_failure_has_backoff(self):
        tracker = SimulatedX11()
        tracker.present = False
        with patch('cmdrhelper.ui.navigation_hud.time.monotonic', return_value=0):
            self.assertIsNone(tracker.current())
        tracker.present = True
        with patch('cmdrhelper.ui.navigation_hud.time.monotonic', return_value=.99):
            self.assertIsNone(tracker.current())
        with patch('cmdrhelper.ui.navigation_hud.time.monotonic', return_value=1):
            self.assertIsNotNone(tracker.current())
        tracker._read.side_effect = subprocess.TimeoutExpired('xprop', .3)
        with patch('cmdrhelper.ui.navigation_hud.time.monotonic', return_value=1.1):
            self.assertIsNone(tracker.current())
        count = tracker._read.call_count
        with patch('cmdrhelper.ui.navigation_hud.time.monotonic', return_value=1.9):
            self.assertIsNone(tracker.current())
        self.assertEqual(tracker._read.call_count, count)
        tracker._read.side_effect = tracker.read
        with patch('cmdrhelper.ui.navigation_hud.time.monotonic', return_value=2.1):
            self.assertIsNotNone(tracker.current())

    def test_native_root_property_validation_and_free(self):
        tracker = X11WindowTracker.__new__(X11WindowTracker)
        tracker.display = 1
        tracker.x11 = Mock()
        value = ctypes.c_ulong(42)
        def get_property(*args):
            for arg, ctype, number in ((args[7], ctypes.c_ulong, 33),
                                       (args[8], ctypes.c_int, 32),
                                       (args[9], ctypes.c_ulong, 1)):
                ctypes.cast(arg, ctypes.POINTER(ctype))[0] = number
            ctypes.cast(args[11], ctypes.POINTER(ctypes.c_void_p))[0] = ctypes.addressof(value)
            return 0
        tracker.x11.XGetWindowProperty.side_effect = get_property
        self.assertEqual(tracker._active_window(), 42)
        tracker.x11.XFree.assert_called_once()
        tracker.x11.XGetWindowProperty.side_effect = None
        tracker.x11.XGetWindowProperty.return_value = 1
        with self.assertRaises(RuntimeError):
            tracker._active_window()


class NavigationLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.controller = PlanetNavigationController(SimpleNamespace(journal_folder=self.folder))
        self.addCleanup(self.controller.deleteLater)
        self.addCleanup(self.controller.timer.stop)

    def test_leases_are_idempotent_last_release_stops_and_restart_polls(self):
        c = self.controller
        with patch.object(c, '_poll') as poll:
            self.assertFalse(c.timer.isActive())
            c.consumer_acquire('navigation_hud')
            timer_id = c.timer.timerId()
            c.consumer_acquire('navigation_hud')
            c.consumer_acquire('navigation_window')
            self.assertEqual(c.timer.timerId(), timer_id)
            self.assertEqual(poll.call_count, 1)
            c.consumer_release('navigation_hud')
            self.assertTrue(c.timer.isActive())
            c.consumer_release('navigation_window')
            c.consumer_release('navigation_window')
            self.assertFalse(c.timer.isActive())
            c.consumer_acquire('favorites')
            self.assertEqual(poll.call_count, 2)
            self.assertEqual(c.timer.interval(), 250)

    def test_no_consumers_means_no_status_reads_or_journal_searches(self):
        c = self.controller
        with patch('cmdrhelper.planet_navigation.journal_files', return_value=[]) as files, \
                patch('cmdrhelper.planet_navigation.read_status', side_effect=ValueError) as status:
            # Replace only the status error with its normal domain exception.
            from cmdrhelper.status_reader import StatusError
            status.side_effect = StatusError('invalid_status')
            c.consumer_acquire('navigation_hud')
            files.reset_mock(); status.reset_mock()
            QTest.qWait(1100)
            self.assertIn(status.call_count, (4, 5))
            self.assertEqual(files.call_count, status.call_count)
            c.consumer_release('navigation_hud')
            files.reset_mock(); status.reset_mock()
            QTest.qWait(600)
            files.assert_not_called(); status.assert_not_called()

    def test_hud_switch_and_window_visibility_own_independent_leases(self):
        tracker = Mock()
        tracker.input_is_empty.return_value = True
        tracker.current.return_value = None
        hud = NavigationHud(self.controller, tracker)
        self.addCleanup(hud.deleteLater)
        self.addCleanup(hud.close)
        settings = SimpleNamespace(value=lambda *a: None, setValue=lambda *a: None, sync=lambda: None)
        window = PlanetNavigationWindow(self.controller, settings)
        self.addCleanup(window.deleteLater)
        self.addCleanup(window.close)
        self.assertFalse(window._age_timer.isActive())
        hud.set_enabled(True)
        self.assertTrue(self.controller.timer.isActive())
        window.show()
        self.assertTrue(window._age_timer.isActive())
        hud.set_enabled(False)
        self.assertTrue(self.controller.timer.isActive())
        window.close()
        self.assertFalse(window._age_timer.isActive())
        self.assertFalse(self.controller.timer.isActive())
        window.show()
        self.assertTrue(self.controller.timer.isActive())
        window.hide()
        self.assertFalse(self.controller.timer.isActive())
        hud.set_enabled(True)
        hud.set_enabled(False)
        self.assertFalse(self.controller.timer.isActive())

    def test_active_navigation_detects_new_status_and_journal(self):
        c = self.controller
        journal = self.folder / 'Journal.20260916000000.01.log'
        journal.write_text(json.dumps(dict(event='Location', StarSystem='Test')) + '\n')
        status = dict(event='Status', timestamp='2026-09-16T00:00:00Z', Flags=1 << 21,
                      Latitude=1, Longitude=2, Heading=3, PlanetRadius=1000000, BodyName='Test 1')
        (self.folder / 'Status.json').write_text(json.dumps(status))
        c.consumer_acquire('navigation_window')
        self.assertEqual(c.state.snapshot.latitude, 1)
        status['Latitude'] = 4
        (self.folder / 'Status.json').write_text(json.dumps(status))
        with journal.open('a') as handle:
            handle.write(json.dumps(dict(event='FSDJump', StarSystem='New', SystemAddress=10)) + '\n')
        QTest.qWait(350)
        self.assertEqual(c.state.snapshot.latitude, 4)
        self.assertEqual(c.tail.context.system_name, 'New')
