"""Win32 contracts exercised offscreen on Linux; no real Windows/game claim."""
import ctypes
import os
import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QObject, QRect, Qt, Signal
from PySide6.QtWidgets import QApplication
from cmdrhelper.ui import navigation_hud as hud_module
from cmdrhelper.ui import navigation_hud_windows as win
from cmdrhelper.ui.navigation_hud import TargetWindow
from cmdrhelper.ui.navigation_hud_windows import (
    MonitorInfo, OVERLAY_STYLES, WindowsWindowTracker, screen_for_monitor,
)


class Controller(QObject):
    changed = Signal(object)


class FakeApi:
    def __init__(self):
        self.windows = {42: dict(path=r'C:\Elite\EliteDangerous64.exe', rect=QRect(30, 40, 700, 500),
                                visible=True, minimized=False, owner=0, style=0, exstyle=0)}
        self.foreground = 42
        self.styles = {}
        self.positions = {}
        self.prepared = []
        self.moves = []

    def enum_windows(self): return list(self.windows)
    def foreground_window(self): return self.foreground
    def is_window(self, hwnd): return hwnd in self.windows or hwnd in self.styles
    def is_visible(self, hwnd): return self.windows.get(hwnd, {}).get('visible', True)
    def is_minimized(self, hwnd): return self.windows.get(hwnd, {}).get('minimized', False)
    def owner(self, hwnd): return self.windows[hwnd]['owner']
    def process_id(self, hwnd): return hwnd
    def process_path(self, pid): return self.windows[pid]['path']
    def get_style(self, hwnd, index=-20):
        if hwnd in self.windows:
            return self.windows[hwnd]['style' if index == -16 else 'exstyle']
        return self.styles.get(hwnd, 0)
    def set_overlay_styles(self, hwnd):
        self.prepared.append(hwnd)
        self.styles[hwnd] = win.OVERLAY_STYLES
    def client_geometry(self, hwnd):
        return self.windows[hwnd]['rect'] if hwnd in self.windows else self.positions.get(hwnd, QRect())
    def monitor_info(self, hwnd):
        screen = QApplication.primaryScreen()
        return win.MonitorInfo(screen.name(), screen.geometry())
    def position_overlay(self, hwnd, rect):
        self.moves.append(QRect(rect))
        self.positions[hwnd] = QRect(rect)


class WindowsHudTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.api = FakeApi()
        self.tracker = win.WindowsWindowTracker(self.api)
        self.controller = Controller()
        self.controller.state = SimpleNamespace(snapshot=object(), solution=SimpleNamespace(
            relative=51, bearing=43, distance_m=78300, undefined_reason=''))
        self.hud = hud_module.NavigationHud(self.controller, self.tracker)
        self.addCleanup(self.hud.deleteLater)
        self.addCleanup(self.hud.close)

    def test_move_resize_minimize_restore_close_and_focus(self):
        with patch.object(self.hud, 'activateWindow', side_effect=AssertionError), \
             patch.object(self.hud, 'setFocus', side_effect=AssertionError), \
             patch.object(self.hud, 'raise_', side_effect=AssertionError):
            self.hud.set_enabled(True)
            self.assertTrue(self.hud.isVisible())
            self.assertEqual(self.api.moves[-1], QRect(30, 40, 700, 500))
            self.api.windows[42]['rect'] = QRect(80, 90, 600, 400)
            self.hud.follow_target()
            self.assertEqual(self.api.moves[-1], QRect(80, 90, 600, 400))
            self.assertEqual(self.hud.geometry(), QRect(80, 90, 600, 400))
            moves = len(self.api.moves)
            self.hud.follow_target()
            self.assertEqual(len(self.api.moves), moves)
            self.assertEqual(len(self.api.prepared), 1)
            self.api.windows[42]['minimized'] = True
            self.hud.follow_target()
            self.assertFalse(self.hud.isVisible())
            self.api.windows[42]['minimized'] = False
            self.hud.follow_target()
            self.assertTrue(self.hud.isVisible())
            self.api.windows.clear()
            self.hud.follow_target()
            self.assertFalse(self.hud.isVisible())

    def test_invalid_navigation_toggle_and_background(self):
        self.hud.set_enabled(True)
        valid = self.controller.state
        self.controller.state = SimpleNamespace(solution=None)
        self.controller.changed.emit(self.controller.state)
        self.assertFalse(self.hud.isVisible())
        self.controller.state = valid
        self.controller.changed.emit(valid)
        self.assertTrue(self.hud.isVisible())
        self.api.foreground = 100
        self.hud.follow_target()
        self.assertFalse(self.hud.isVisible())
        self.api.foreground = 42
        self.hud.follow_target()
        self.assertTrue(self.hud.isVisible())
        self.hud.set_enabled(False)
        self.controller.changed.emit(valid)
        self.assertFalse(self.hud.isVisible())

    def test_qt_and_native_input_contract(self):
        self.hud.set_enabled(True)
        for attr in (Qt.WA_TranslucentBackground, Qt.WA_ShowWithoutActivating, Qt.WA_TransparentForMouseEvents):
            self.assertTrue(self.hud.testAttribute(attr))
        self.assertFalse(self.hud.testAttribute(Qt.WA_X11DoNotAcceptFocus))
        for flag in (Qt.Tool, Qt.FramelessWindowHint, Qt.WindowDoesNotAcceptFocus, Qt.WindowTransparentForInput):
            self.assertTrue(self.hud.windowFlags() & flag)
        self.assertEqual(self.api.styles[int(self.hud.winId())], win.OVERLAY_STYLES)

    def test_native_errors_hide_stop_and_do_not_retry_on_navigation_updates(self):
        for method in ('enum_windows', 'client_geometry', 'set_overlay_styles', 'monitor_info', 'position_overlay'):
            with self.subTest(method=method):
                self.tracker.close()
                with patch.object(self.api, method, side_effect=OSError('native failure')) as failed:
                    with self.assertLogs('cmdrhelper.ui.navigation_hud', level='WARNING'):
                        self.hud.set_enabled(True)
                    self.assertFalse(self.hud.isVisible())
                    self.assertFalse(self.hud.timer.isActive())
                    self.assertEqual(self.hud.status, 'error')
                    count = failed.call_count
                    self.controller.changed.emit(self.controller.state)
                    self.hud.follow_target()
                    self.assertEqual(failed.call_count, count)
                    self.assertIsNotNone(self.controller.state.solution)
                self.hud.set_enabled(True)
                self.assertTrue(self.hud.isVisible())
                self.hud.set_enabled(False)

    def test_missing_styles_and_wrong_geometry_fail_closed(self):
        for method in ('get_style', 'position_overlay'):
            self.tracker.close()
            self.api.positions.clear()
            with patch.object(self.api, method, return_value=0):
                with self.assertLogs('cmdrhelper.ui.navigation_hud', level='WARNING'):
                    self.hud.set_enabled(True)
                self.assertFalse(self.hud.isVisible())
                self.assertEqual(self.hud.status, 'error')

    def test_game_closing_during_geometry_query_recovers_after_restart(self):
        game = dict(self.api.windows[42])
        def close_game(hwnd):
            self.api.windows.pop(42, None)
            raise OSError('window destroyed')
        with patch.object(self.api, 'client_geometry', side_effect=close_game):
            self.hud.set_enabled(True)
        self.assertFalse(self.hud.isVisible())
        self.assertTrue(self.hud.timer.isActive())
        self.api.windows[42] = game
        self.hud.follow_target()
        self.assertTrue(self.hud.isVisible())

    def test_game_minimizing_during_overlay_placement_recovers(self):
        def minimize_game(hwnd):
            self.api.windows[42]['minimized'] = True
            raise OSError('monitor changed')
        with patch.object(self.api, 'monitor_info', side_effect=minimize_game):
            self.hud.set_enabled(True)
        self.assertFalse(self.hud.isVisible())
        self.assertTrue(self.hud.timer.isActive())
        self.api.windows[42]['minimized'] = False
        self.hud.follow_target()
        self.assertTrue(self.hud.isVisible())

    def test_process_selection_ignores_launcher_titles_owned_tool_child_and_zero_area(self):
        original = dict(self.api.windows[42])
        self.api.windows[1] = dict(original, path=r'C:\Elite\EDLaunch.exe')
        self.api.windows[2] = dict(original, path=r'C:\other\EliteDangerous64.exe.bak')
        self.api.windows[3] = dict(original, owner=42)
        self.api.windows[4] = dict(original, exstyle=win.WS_EX_TOOLWINDOW)
        self.api.windows[5] = dict(original, style=win.WS_CHILD)
        self.api.windows[6] = dict(original, rect=QRect())
        self.api.windows[7] = dict(original, rect=QRect(0, 0, 3000, 2000))
        self.api.windows[42]['path'] = r'D:\Spiele\ELITEDANGEROUS64.EXE'
        self.assertEqual(self.tracker.current().window_id, 42)
        self.api.foreground = 1
        self.assertIsNone(self.tracker.current())
        self.assertEqual(self.tracker.last_target.window_id, 7)
        self.api.foreground = 42
        with patch.object(self.api, 'process_path', side_effect=OSError('access denied')):
            self.assertIsNone(self.tracker.current())

    def test_platform_factory_isolation(self):
        with patch.object(hud_module.sys, 'platform', 'win32'), \
             patch.object(hud_module.QGuiApplication, 'platformName', return_value='windows'), \
             patch.object(win, 'WindowsWindowTracker', return_value=self.tracker) as windows, \
             patch.object(hud_module, 'X11WindowTracker', side_effect=AssertionError):
            self.assertIs(hud_module.create_window_tracker(), self.tracker)
            windows.assert_called_once_with()
        with patch.object(hud_module.sys, 'platform', 'linux'), \
             patch.object(win, 'WindowsWindowTracker', side_effect=AssertionError), \
             patch.object(hud_module, 'X11WindowTracker', return_value='x11'):
            self.assertEqual(hud_module.create_window_tracker(), 'x11')


class CoordinateTests(unittest.TestCase):
    def test_mixed_dpi_monitor_origins_and_rounding(self):
        for origin in (-2560, 1920):
            for ratio in (1., 1.25, 1.5, 2.):
                with self.subTest(origin=origin, ratio=ratio):
                    result = win.native_to_logical(QRect(origin+150, 300, 1500, 900),
                        QRect(origin, 0, 2560, 1440), QRect(origin, 0, 1707, 960), ratio)
                    self.assertEqual(result, QRect(origin+round(150/ratio), round(300/ratio),
                                                   round(1500/ratio), round(900/ratio)))
        for ratio in (0, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                win.native_to_logical(QRect(), QRect(), QRect(), ratio)

    @unittest.skipUnless(sys.platform == 'linux', 'Linux import isolation')
    def test_linux_imports_never_load_windows_dlls(self):
        code = '''import ctypes, sys
ctypes.WinDLL = lambda *a, **k: (_ for _ in ()).throw(AssertionError("Windows DLL on Linux"))
import cmdrhelper.ui.navigation_hud
assert "cmdrhelper.ui.navigation_hud_windows" not in sys.modules
from cmdrhelper.ui.navigation_hud_windows import Win32Api
try:
    Win32Api()
except RuntimeError:
    pass
else:
    raise AssertionError("Expected platform guard")
'''
        subprocess.run([sys.executable, '-c', code], check=True, capture_output=True)


class NativeApiTests(unittest.TestCase):
    def setUp(self):
        self.u, self.k = Mock(), Mock()
        self.error = 0
        def set_error(value): self.error = value
        errors = SimpleNamespace(set_last_error=set_error, get_last_error=lambda: self.error)
        self.api = win.Win32Api(user32=self.u, kernel32=self.k, error_state=errors)
        self.u.SetThreadDpiAwarenessContext.return_value = 99
        self.u.GetWindowDpiAwarenessContext.return_value = 10
        self.u.GetAwarenessFromDpiAwarenessContext.return_value = 2
        self.u.GetWindowLongPtrW.return_value = 0
        self.u.SetWindowLongPtrW.return_value = 0
        self.u.SetWindowPos.return_value = 1

    def test_client_coordinates_exclude_frame_and_restore_dpi_context(self):
        def get_rect(hwnd, ptr):
            r = ptr._obj
            r.left, r.top, r.right, r.bottom = 0, 0, 1500, 900
            return 1
        def to_screen(hwnd, ptr):
            ptr._obj.x += -2452
            ptr._obj.y += 131
            return 1
        self.u.GetClientRect.side_effect = get_rect
        self.u.ClientToScreen.side_effect = to_screen
        self.assertEqual(self.api.client_geometry(42), QRect(-2452, 131, 1500, 900))
        self.assertEqual(self.u.ClientToScreen.call_count, 2)
        self.assertEqual([c.args for c in self.u.SetThreadDpiAwarenessContext.call_args_list], [(-4,), (99,)])
        self.u.GetClientRect.side_effect = None
        self.u.GetClientRect.return_value = 0
        with self.assertRaises(OSError): self.api.client_geometry(42)
        self.assertEqual(self.u.SetThreadDpiAwarenessContext.call_args.args, (99,))

    def test_styles_preserve_bits_remove_appwindow_and_never_activate(self):
        self.u.GetWindowLongPtrW.return_value = win.WS_EX_APPWINDOW | 0x100
        self.api.set_overlay_styles(88)
        self.u.SetWindowLongPtrW.assert_called_once_with(88, -20, win.OVERLAY_STYLES | 0x100)
        args = self.u.SetWindowPos.call_args.args
        self.assertEqual(args[1], win.HWND_TOPMOST)
        self.assertTrue(args[-1] & win.SWP_NOACTIVATE)
        self.assertTrue(args[-1] & win.SWP_FRAMECHANGED)
        self.api.position_overlay(88, QRect(-900, 200, 600, 400))
        args = self.u.SetWindowPos.call_args.args
        self.assertEqual(args[:6], (88, None, -900, 200, 600, 400))
        self.assertTrue(args[-1] & win.SWP_NOACTIVATE)
        self.assertTrue(args[-1] & win.SWP_NOZORDER)
        self.u.GetAwarenessFromDpiAwarenessContext.return_value = 1
        with self.assertRaises(RuntimeError): self.api.set_overlay_styles(88)

    def test_checked_native_failures_and_zero_style_success(self):
        self.assertEqual(self.api.get_style(88), 0)
        def fail(*args):
            self.error = 5
            return 0
        self.u.GetWindowLongPtrW.side_effect = fail
        with self.assertRaises(OSError): self.api.get_style(88)
        self.u.GetWindowLongPtrW.side_effect = None
        self.u.SetWindowLongPtrW.side_effect = fail
        with self.assertRaises(OSError): self.api.set_overlay_styles(88)
        self.u.SetWindowPos.return_value = 0
        with self.assertRaises(OSError): self.api.position_overlay(88, QRect(0, 0, 100, 100))
        self.u.EnumWindows.return_value = 0
        with self.assertRaises(OSError): self.api.enum_windows()

    def test_process_identity_and_handle_cleanup(self):
        self.k.OpenProcess.return_value = 123
        self.k.CloseHandle.return_value = 1
        def query(handle, flags, name, size):
            name.value = r'C:\Elite\EliteDangerous64.exe'
            return 1
        self.k.QueryFullProcessImageNameW.side_effect = query
        self.assertEqual(self.api.process_path(77), r'C:\Elite\EliteDangerous64.exe')
        self.k.OpenProcess.assert_called_with(0x1000, False, 77)
        self.k.CloseHandle.assert_called_with(123)
        self.k.QueryFullProcessImageNameW.side_effect = None
        self.k.QueryFullProcessImageNameW.return_value = 0
        with self.assertRaises(OSError): self.api.process_path(77)
        self.assertEqual(self.k.CloseHandle.call_count, 2)

    def test_enum_preserves_pointer_width_and_initialization_failure(self):
        def enumerate_windows(callback, param):
            callback(2**40, param)
            return 1
        self.u.EnumWindows.side_effect = enumerate_windows
        self.assertEqual(self.api.enum_windows(), [2**40])
        self.assertIs(self.u.GetForegroundWindow.restype, ctypes.c_void_p)
        with self.assertRaises(RuntimeError):
            win.Win32Api(user32=object(), kernel32=object())

    def test_monitor_identity_geometry_and_process_id(self):
        self.u.MonitorFromWindow.return_value = 55
        def monitor_info(handle, ptr):
            self.assertEqual(handle, 55)
            self.assertEqual(ptr._obj.cbSize, ctypes.sizeof(win.MONITORINFOEXW))
            ptr._obj.rcMonitor = win.RECT(-2560, -100, 0, 1340)
            ptr._obj.szDevice = r'\\.\DISPLAY2'
            return 1
        self.u.GetMonitorInfoW.side_effect = monitor_info
        result = self.api.monitor_info(42)
        self.assertEqual(result, win.MonitorInfo(r'\\.\DISPLAY2', QRect(-2560, -100, 2560, 1440)))
        def process_id(hwnd, ptr):
            ptr._obj.value = 7788
            return 99
        self.u.GetWindowThreadProcessId.side_effect = process_id
        self.assertEqual(self.api.process_id(42), 7788)
        self.u.GetMonitorInfoW.side_effect = None
        self.u.GetMonitorInfoW.return_value = 0
        with self.assertRaises(OSError): self.api.monitor_info(42)
        self.assertEqual(self.u.SetThreadDpiAwarenessContext.call_args.args, (99,))


def screen(name, geometry, ratio=1.0):
    result = Mock()
    result.name.return_value = name
    result.geometry.return_value = QRect(*geometry)
    result.devicePixelRatio.return_value = ratio
    return result


class MonitorMappingTests(unittest.TestCase):
    def setUp(self):
        self.first = screen("25G3ZM", (0, 0, 1920, 1080))
        self.second = screen("LF24T35", (1920, 0, 1920, 1080))

    def test_display1_friendly_name_matches_by_geometry(self):
        monitor = MonitorInfo(r"\\.\DISPLAY1", QRect(0, 0, 1920, 1080))
        self.assertIs(screen_for_monitor(monitor, [self.second, self.first]), self.first)

    def test_display2_friendly_name_matches_by_geometry(self):
        monitor = MonitorInfo(r"\\.\DISPLAY2", QRect(1920, 0, 1920, 1080))
        self.assertIs(screen_for_monitor(monitor, [self.first, self.second]), self.second)

    def test_coincidentally_equal_names_also_work(self):
        self.first.name.return_value = r"\\.\DISPLAY1"
        self.assertIs(screen_for_monitor(
            MonitorInfo(r"\\.\DISPLAY1", QRect(0, 0, 1920, 1080)), [self.first]), self.first)

    def test_names_are_never_read_even_if_wrong_screen_has_matching_name(self):
        self.second.name.return_value = r"\\.\DISPLAY1"
        self.first.name.side_effect = AssertionError("Screen names are not identifiers")
        self.assertIs(screen_for_monitor(
            MonitorInfo(r"\\.\DISPLAY1", QRect(0, 0, 1920, 1080)),
            [self.second, self.first]), self.first)
        self.second.name.assert_not_called()

    def test_exact_match_precedes_larger_overlapping_screen(self):
        larger = screen("larger", (-100, -100, 3000, 2000))
        self.assertIs(screen_for_monitor(
            MonitorInfo("native", QRect(0, 0, 1920, 1080)),
            [larger, self.first]), self.first)

    def test_unique_largest_overlap(self):
        monitor = MonitorInfo("native", QRect(1800, 0, 2040, 1080))
        self.assertIs(screen_for_monitor(monitor, [self.first, self.second]), self.second)

    def test_scaled_qt_rectangle_can_match_by_overlap(self):
        scaled = screen("scaled", (1920, 0, 1280, 720), 1.5)
        monitor = MonitorInfo("native", QRect(1920, 0, 1920, 1080))
        self.assertIs(screen_for_monitor(monitor, [self.first, scaled]), scaled)

    def test_negative_desktop_coordinates(self):
        left = screen("left", (-1920, -200, 1920, 1080))
        self.assertIs(screen_for_monitor(
            MonitorInfo("native", QRect(-1920, -200, 1920, 1080)),
            [self.first, left]), left)

    def test_missing_or_nonoverlapping_screens_fail(self):
        monitor = MonitorInfo("native", QRect(0, 0, 1920, 1080))
        for screens in ([], [self.second]):
            with self.subTest(screens=screens):
                with self.assertRaisesRegex(RuntimeError, "no overlapping Qt screen"):
                    screen_for_monitor(monitor, screens)

    def test_duplicate_exact_geometries_fail(self):
        duplicate = screen("different name", (0, 0, 1920, 1080))
        with self.assertRaisesRegex(RuntimeError, "multiple equally matching"):
            screen_for_monitor(MonitorInfo("native", QRect(0, 0, 1920, 1080)),
                               [self.first, duplicate])

    def test_equal_positive_overlap_fails(self):
        with self.assertRaisesRegex(RuntimeError, "multiple equally matching"):
            screen_for_monitor(MonitorInfo("native", QRect(960, 0, 1920, 1080)),
                               [self.first, self.second])

    def test_invalid_monitor_geometry_fails(self):
        with self.assertRaisesRegex(RuntimeError, "no overlapping Qt screen"):
            screen_for_monitor(MonitorInfo("native", QRect()), [self.first])


class OverlayPlacementTests(unittest.TestCase):
    def place(self, client, monitor_rect, qt_rect, ratio=1.0):
        chosen = screen("25G3ZM", qt_rect, ratio)
        api = Mock()
        api.monitor_info.return_value = MonitorInfo(r"\\.\DISPLAY1", QRect(*monitor_rect))
        api.get_style.return_value = OVERLAY_STYLES
        api.client_geometry.return_value = QRect(*client)
        api.is_window.return_value = True
        api.is_visible.return_value = True
        api.is_minimized.return_value = False
        hud = Mock()
        hud.winId.return_value = 22
        hud.geometry.return_value = QRect(2560, 276, 640, 480)
        hud.isVisible.return_value = False
        tracker = WindowsWindowTracker(api)
        target = TargetWindow(11, QRect(*client))
        with patch("cmdrhelper.ui.navigation_hud_windows.QGuiApplication") as application:
            application.screens.return_value = [chosen]
            logical = tracker.place_overlay(hud, target)
        api.monitor_info.assert_called_once_with(11)
        hud.windowHandle().setScreen.assert_called_once_with(chosen)
        hud.setGeometry.assert_called_once_with(logical)
        hud.show.assert_called_once_with()
        api.position_overlay.assert_called_once_with(22, QRect(*client))
        api.set_overlay_styles.assert_called_once_with(22)
        return logical

    def test_real_elite_client_uses_full_1920_by_1080(self):
        rect = (0, 0, 1920, 1080)
        self.assertEqual(self.place(rect, rect, rect), QRect(*rect))

    def test_windowed_client_remains_distinct_from_monitor(self):
        client = (200, 150, 1280, 720)
        self.assertEqual(self.place(client, (0, 0, 1920, 1080),
                                    (0, 0, 1920, 1080)), QRect(*client))

    def test_dpi_conversion_keeps_exact_native_client_placement(self):
        self.assertEqual(self.place((1920, 0, 1920, 1080), (1920, 0, 1920, 1080),
                                    (1920, 0, 1280, 720), 1.5),
                         QRect(1920, 0, 1280, 720))

    def test_ambiguous_mapping_fails_before_touching_overlay(self):
        api, hud = Mock(), Mock()
        api.monitor_info.return_value = MonitorInfo("native", QRect(0, 0, 1920, 1080))
        screens = [screen("a", (0, 0, 1920, 1080)), screen("b", (0, 0, 1920, 1080))]
        with patch("cmdrhelper.ui.navigation_hud_windows.QGuiApplication") as application:
            application.screens.return_value = screens
            with self.assertRaisesRegex(RuntimeError, "multiple equally matching"):
                WindowsWindowTracker(api).place_overlay(hud, TargetWindow(11, QRect()))
        self.assertEqual(hud.mock_calls, [])
        api.set_overlay_styles.assert_not_called()
        api.position_overlay.assert_not_called()



if __name__ == '__main__':
    unittest.main()
