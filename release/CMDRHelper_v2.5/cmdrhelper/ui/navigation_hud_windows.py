"""Win32 HUD backend: automated tests only; real Elite validation is pending.

DLLs are loaded only when Win32Api is constructed on Windows. Importing this
module on Linux is safe, and tests inject an API instead of calling Windows.
Qt owns the translucent backing store; this module never changes its alpha API.
"""
from contextlib import contextmanager
import ctypes
from dataclasses import dataclass
import math
import ntpath
import sys

from PySide6.QtCore import QRect
from PySide6.QtGui import QGuiApplication

from cmdrhelper.ui.navigation_hud import TargetWindow


WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
WS_EX_LAYERED = 0x00080000
WS_EX_NOACTIVATE = 0x08000000
WS_CHILD = 0x40000000
OVERLAY_STYLES = WS_EX_TRANSPARENT | WS_EX_LAYERED | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
SWP_NOOWNERZORDER = 0x0200
HWND_TOPMOST = -1

# Explicit Win32 widths also make the structures testable on a 64-bit Linux host.
BOOL = ctypes.c_int32
DWORD = ctypes.c_uint32
HWND = ctypes.c_void_p
LONG_PTR = ctypes.c_ssize_t


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int32), ("y", ctypes.c_int32)]


class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_int32), ("top", ctypes.c_int32),
                ("right", ctypes.c_int32), ("bottom", ctypes.c_int32)]


class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [("cbSize", DWORD), ("rcMonitor", RECT), ("rcWork", RECT),
                ("dwFlags", DWORD), ("szDevice", ctypes.c_wchar * 32)]


@dataclass(frozen=True)
class MonitorInfo:
    device: str
    geometry: QRect


def native_to_logical(rect, native_monitor, logical_monitor, ratio):
    """Convert relative to the monitor origins, never scale desktop origins.

    Windows/Qt mixed-DPI desktops keep screen origins but scale screen sizes.
    The final Win32 placement below retains exact physical client pixels even
    when integer Qt coordinates have to round a fractional logical pixel.
    """
    if not math.isfinite(ratio) or ratio <= 0:
        raise ValueError("Invalid HUD device pixel ratio")
    return QRect(
        logical_monitor.x() + round((rect.x() - native_monitor.x()) / ratio),
        logical_monitor.y() + round((rect.y() - native_monitor.y()) / ratio),
        max(1, round(rect.width() / ratio)), max(1, round(rect.height() / ratio)),
    )


class Win32Api:
    """Small checked ctypes boundary. No keyboard, activation or focus APIs."""
    def __init__(self, *, user32=None, kernel32=None, error_state=None):
        injected = user32 is not None and kernel32 is not None
        if not injected and sys.platform != "win32":
            raise RuntimeError("Win32 HUD requires Windows")
        try:
            self.user32 = user32 if injected else ctypes.WinDLL("user32", use_last_error=True)
            self.kernel32 = kernel32 if injected else ctypes.WinDLL("kernel32", use_last_error=True)
            self.errors = error_state if error_state is not None else ctypes
            callback = ctypes.CFUNCTYPE if injected else ctypes.WINFUNCTYPE
            self.enum_callback = callback(BOOL, HWND, LONG_PTR)
            self._bind()
        except (AttributeError, OSError) as exc:
            raise RuntimeError(f"Win32 HUD API initialization failed: {exc}") from exc

    @staticmethod
    def _signature(function, args, result):
        function.argtypes, function.restype = args, result
        return function

    def _bind(self):
        u, k, bind = self.user32, self.kernel32, self._signature
        bind(u.EnumWindows, [self.enum_callback, LONG_PTR], BOOL)
        bind(u.GetForegroundWindow, [], HWND)
        bind(u.IsWindow, [HWND], BOOL)
        bind(u.IsWindowVisible, [HWND], BOOL)
        bind(u.IsIconic, [HWND], BOOL)
        bind(u.GetWindow, [HWND, DWORD], HWND)
        bind(u.GetWindowThreadProcessId, [HWND, ctypes.POINTER(DWORD)], DWORD)
        bind(u.GetClientRect, [HWND, ctypes.POINTER(RECT)], BOOL)
        bind(u.ClientToScreen, [HWND, ctypes.POINTER(POINT)], BOOL)
        bind(u.MonitorFromWindow, [HWND, DWORD], HWND)
        bind(u.GetMonitorInfoW, [HWND, ctypes.POINTER(MONITORINFOEXW)], BOOL)
        bind(u.SetThreadDpiAwarenessContext, [HWND], HWND)
        bind(u.GetWindowDpiAwarenessContext, [HWND], HWND)
        bind(u.GetAwarenessFromDpiAwarenessContext, [HWND], ctypes.c_int32)
        getter = getattr(u, "GetWindowLongPtrW", None) or u.GetWindowLongW
        setter = getattr(u, "SetWindowLongPtrW", None) or u.SetWindowLongW
        self._get_long = bind(getter, [HWND, ctypes.c_int32], LONG_PTR)
        self._set_long = bind(setter, [HWND, ctypes.c_int32, LONG_PTR], LONG_PTR)
        bind(u.SetWindowPos, [HWND, HWND, ctypes.c_int32, ctypes.c_int32,
                             ctypes.c_int32, ctypes.c_int32, DWORD], BOOL)
        bind(k.OpenProcess, [DWORD, BOOL, DWORD], HWND)
        bind(k.QueryFullProcessImageNameW, [HWND, DWORD, ctypes.c_wchar_p, ctypes.POINTER(DWORD)], BOOL)
        bind(k.CloseHandle, [HWND], BOOL)

    def _check(self, result, operation):
        if not result:
            raise OSError(self.errors.get_last_error(), f"{operation} failed")
        return result

    @contextmanager
    def physical_coordinates(self):
        # Only this thread, only while reading/placing native geometry. Never
        # change the application's global DPI policy or another window's policy.
        previous = self._check(self.user32.SetThreadDpiAwarenessContext(-4),
                               "SetThreadDpiAwarenessContext(PER_MONITOR_AWARE_V2)")
        try:
            yield
        finally:
            self._check(self.user32.SetThreadDpiAwarenessContext(previous),
                        "Restore thread DPI awareness")

    def enum_windows(self):
        windows = []

        @self.enum_callback
        def collect(hwnd, _param):
            windows.append(int(hwnd))
            return 1

        self._check(self.user32.EnumWindows(collect, 0), "EnumWindows")
        return windows

    def foreground_window(self):
        return int(self.user32.GetForegroundWindow() or 0)

    def is_window(self, hwnd):
        return bool(self.user32.IsWindow(hwnd))

    def is_visible(self, hwnd):
        return bool(self.user32.IsWindowVisible(hwnd))

    def is_minimized(self, hwnd):
        return bool(self.user32.IsIconic(hwnd))

    def owner(self, hwnd):
        return int(self.user32.GetWindow(hwnd, 4) or 0)  # GW_OWNER

    def process_id(self, hwnd):
        pid = DWORD()
        self._check(self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid)),
                    "GetWindowThreadProcessId")
        return pid.value

    def process_path(self, pid):
        handle = self._check(self.kernel32.OpenProcess(0x1000, False, pid), "OpenProcess")
        try:
            size = DWORD(32768)
            name = ctypes.create_unicode_buffer(size.value)
            self._check(self.kernel32.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(size)),
                        "QueryFullProcessImageNameW")
            return name.value
        finally:
            self._check(self.kernel32.CloseHandle(handle), "CloseHandle")

    def get_style(self, hwnd, index=-20):  # GWL_EXSTYLE / GWL_STYLE=-16
        self.errors.set_last_error(0)
        value = self._get_long(hwnd, index)
        if value == 0 and self.errors.get_last_error():
            self._check(0, "GetWindowLongPtrW")
        return int(value) & 0xFFFFFFFF

    def set_overlay_styles(self, hwnd):
        context = self._check(self.user32.GetWindowDpiAwarenessContext(hwnd),
                              "GetWindowDpiAwarenessContext")
        if self.user32.GetAwarenessFromDpiAwarenessContext(context) != 2:
            raise RuntimeError("HUD window must be per-monitor DPI aware (Qt 6 default)")
        wanted = (self.get_style(hwnd) | OVERLAY_STYLES) & ~WS_EX_APPWINDOW
        self.errors.set_last_error(0)
        previous = self._set_long(hwnd, -20, wanted)
        if previous == 0 and self.errors.get_last_error():
            self._check(0, "SetWindowLongPtrW")
        self._check(self.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_NOOWNERZORDER | SWP_FRAMECHANGED),
                    "Apply overlay styles")

    def client_geometry(self, hwnd):
        with self.physical_coordinates():
            rect = RECT()
            self._check(self.user32.GetClientRect(hwnd, ctypes.byref(rect)), "GetClientRect")
            first, last = POINT(rect.left, rect.top), POINT(rect.right, rect.bottom)
            self._check(self.user32.ClientToScreen(hwnd, ctypes.byref(first)), "ClientToScreen")
            self._check(self.user32.ClientToScreen(hwnd, ctypes.byref(last)), "ClientToScreen")
            return QRect(first.x, first.y, last.x - first.x, last.y - first.y)

    def monitor_info(self, hwnd):
        with self.physical_coordinates():
            monitor = self._check(self.user32.MonitorFromWindow(hwnd, 2), "MonitorFromWindow")
            info = MONITORINFOEXW()
            info.cbSize = ctypes.sizeof(info)
            self._check(self.user32.GetMonitorInfoW(monitor, ctypes.byref(info)), "GetMonitorInfoW")
            r = info.rcMonitor
            return MonitorInfo(info.szDevice, QRect(r.left, r.top, r.right-r.left, r.bottom-r.top))

    def position_overlay(self, hwnd, rect):
        with self.physical_coordinates():
            self._check(self.user32.SetWindowPos(hwnd, None, *rect.getRect(),
                        SWP_NOZORDER | SWP_NOACTIVATE | SWP_NOOWNERZORDER), "Position overlay")


class WindowsWindowTracker:
    """Output-only window tracking. Windows game testing is still pending."""
    native_platform = "windows"

    def __init__(self, api=None):
        self.api = api if api is not None else Win32Api()
        self.reason, self.error, self.last_target = "not_found", "", None
        self._prepared_hwnd = None

    def close(self):
        self._prepared_hwnd = None  # Process handles are closed within each query.

    def input_is_empty(self, hwnd):
        if self._prepared_hwnd != hwnd:
            self.api.set_overlay_styles(hwnd)
            self._prepared_hwnd = hwnd
        styles = self.api.get_style(hwnd)
        return styles & OVERLAY_STYLES == OVERLAY_STYLES and not styles & WS_EX_APPWINDOW

    def window_is_viewable(self, hwnd):
        return self.api.is_window(hwnd) and self.api.is_visible(hwnd) and not self.api.is_minimized(hwnd)

    def current(self):
        self.reason, self.error, self.last_target = "not_found", "", None
        foreground = self.api.foreground_window()
        candidates, processes = [], {}
        for hwnd in self.api.enum_windows():
            if not self.api.is_window(hwnd) or self.api.owner(hwnd):
                continue
            try:
                if self.api.get_style(hwnd, -16) & WS_CHILD or self.api.get_style(hwnd) & WS_EX_TOOLWINDOW:
                    continue
            except OSError:
                if not self.api.is_window(hwnd):
                    continue  # Window closed between enumeration and inspection.
                raise
            # Protected/unrelated processes and windows disappearing during
            # enumeration are normal. Do not require elevated privileges.
            try:
                pid = self.api.process_id(hwnd)
                if pid not in processes:
                    processes[pid] = self.api.process_path(pid)
            except OSError:
                continue
            if ntpath.basename(processes[pid]).casefold() != "elitedangerous64.exe":
                continue
            if not self.window_is_viewable(hwnd):
                self.reason = "hidden"
                continue
            try:
                rect = self.api.client_geometry(hwnd)
            except OSError:
                if not self.window_is_viewable(hwnd):
                    self.reason = "hidden"
                    continue
                raise
            if rect.width() > 0 and rect.height() > 0:
                candidates.append(TargetWindow(hwnd, rect))
        if not candidates:
            return None
        # Foreground game first; otherwise the largest ownerless game window.
        target = max(candidates, key=lambda item: (item.window_id == foreground,
                     item.geometry.width() * item.geometry.height(), -item.window_id))
        self.last_target = target
        if target.window_id != foreground:
            self.reason = "foreground"
            return None
        self.reason = "active"
        return target

    def place_overlay(self, hud, target):
        monitor = self.api.monitor_info(target.window_id)
        screen = next((s for s in QGuiApplication.screens()
                       if s.name().casefold() == monitor.device.casefold()), None)
        if screen is None:
            raise RuntimeError(f"Cannot match Elite monitor to Qt screen: {monitor.device}")
        logical = native_to_logical(target.geometry, monitor.geometry,
                                    screen.geometry(), screen.devicePixelRatio())
        if hud.windowHandle().screen() != screen:
            hud.windowHandle().setScreen(screen)
        hwnd = int(hud.winId())
        if not self.input_is_empty(hwnd):
            raise RuntimeError("Windows HUD click-through/no-activate styles are missing")
        if hud.geometry() != logical:
            hud.setGeometry(logical)
        was_hidden = not hud.isVisible()
        if was_hidden:
            hud.show()  # Qt WA_ShowWithoutActivating + matching Win32 styles.
        hwnd = int(hud.winId())  # Qt may recreate a handle during a screen change.
        if not self.input_is_empty(hwnd):
            raise RuntimeError("Qt changed Windows HUD input styles while showing")
        if was_hidden or self.api.client_geometry(hwnd) != target.geometry:
            self.api.position_overlay(hwnd, target.geometry)
        if self.api.client_geometry(hwnd) != target.geometry:
            raise RuntimeError("Windows HUD client geometry does not match Elite")
        if not self.window_is_viewable(hwnd):
            raise RuntimeError("Windows HUD remained natively hidden")
        return logical
