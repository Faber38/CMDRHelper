"""Optional, output-only navigation HUD. Platform tracking is replaceable."""
import ctypes
from ctypes.util import find_library
from dataclasses import dataclass, replace
import os
import logging
import re
import subprocess
import sys

from PySide6.QtCore import QPointF, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFontMetricsF, QGuiApplication, QPainter, QPen, QPainterPath
from PySide6.QtWidgets import QWidget

from cmdrhelper.i18n import tr, get_language
from cmdrhelper.ui.planet_navigation_window import angle_text, direction_text


def hud_lines(state):
    """Only confirmed compass values; no HUD navigation or cached telemetry."""
    solution = getattr(state, "solution", None)
    if (getattr(state, "snapshot", None) is None or solution is None
            or solution.bearing is None or solution.relative is None):
        return ()
    distance = f"{solution.distance_m / 1000:.1f} km"
    if get_language() == "de":
        distance = distance.replace(".", ",")
    return (direction_text(solution).upper(),
            tr("planet_nav.target_course", value=angle_text(solution.bearing)).upper(),
            tr("navigation_hud.distance", value=distance))


@dataclass(frozen=True)
class TargetWindow:
    window_id: int
    geometry: QRect  # Native pixels, client area, desktop coordinates.


class X11WindowTracker:
    """Read-only foreground/client geometry tracking. Never activates a window."""
    def __init__(self):
        if QGuiApplication.platformName() != "xcb":
            raise RuntimeError("HUD prototype requires Linux/X11 (Qt xcb).")
        libraries = [find_library(name) for name in ("X11", "Xext")]
        if not all(libraries):
            raise RuntimeError("HUD prototype requires libX11 and libXext.")
        self.x11, self.shape = (ctypes.CDLL(name) for name in libraries)
        self.x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.x11.XOpenDisplay.restype = ctypes.c_void_p
        self.display = self.x11.XOpenDisplay(None)
        if not self.display:
            raise RuntimeError("Cannot open X11 display.")
        self.x11.XDefaultScreen.argtypes = [ctypes.c_void_p]
        self.x11.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        self.x11.XInternAtom.restype = ctypes.c_ulong
        self.x11.XGetSelectionOwner.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        self.x11.XGetSelectionOwner.restype = ctypes.c_ulong
        self.x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
        self.x11.XFree.argtypes = [ctypes.c_void_p]
        self.shape.XShapeQueryExtension.argtypes = [ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
        event_base, error_base = ctypes.c_int(), ctypes.c_int()
        if not self.shape.XShapeQueryExtension(self.display, ctypes.byref(event_base), ctypes.byref(error_base)):
            self.close()
            raise RuntimeError("HUD prototype requires X11 SHAPE input regions.")
        self.shape.XShapeGetRectangles.argtypes = [ctypes.c_void_p, ctypes.c_ulong,
            ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)]
        self.shape.XShapeGetRectangles.restype = ctypes.c_void_p

    def close(self):
        if self.display:
            self.x11.XCloseDisplay(self.display)
            self.display = None

    @staticmethod
    def _read(*args):
        return subprocess.run(args, capture_output=True, text=True, check=True,
                              timeout=.3, env=dict(os.environ, LC_ALL="C")).stdout

    def compositor_available(self):
        if not self.display:
            return False
        screen = self.x11.XDefaultScreen(self.display)
        atom = self.x11.XInternAtom(self.display, f"_NET_WM_CM_S{screen}".encode(), 0)
        return bool(self.x11.XGetSelectionOwner(self.display, atom))

    def input_is_empty(self, window_id):
        if not self.display:
            return False
        # ShapeInput=2. Check the native input region, not just a Qt attribute.
        count, ordering = ctypes.c_int(-1), ctypes.c_int()
        rectangles = self.shape.XShapeGetRectangles(self.display, window_id, 2,
                                                    ctypes.byref(count), ctypes.byref(ordering))
        if rectangles:
            self.x11.XFree(rectangles)
        return count.value == 0

    def window_is_viewable(self, window_id):
        try:
            return "Map State: IsViewable" in self._read("xwininfo", "-id", hex(window_id))
        except (OSError, subprocess.SubprocessError):
            return False

    def current(self):
        self.reason, self.error, self.last_target = "not_found", "", None
        try:
            if not self.compositor_available():
                self.reason = "no_compositor"
                return None
            active = self._read("xprop", "-root", "_NET_ACTIVE_WINDOW")
            match = re.search(r"0x[0-9a-fA-F]+", active)
            active_id = int(match[0], 16) if match else 0
            # Discover Elite even while the user is clicking the Helper's switch.
            rows = self._read("wmctrl", "-lx").splitlines()
            matches = [row for row in rows if 'steam_app_359320' in row.lower()
                       and re.search(r'Elite\s*-\s*Dangerous', row, re.I)]
            if not matches:
                return None
            wid = matches[0].split()[0]
            props = self._read("xprop", "-id", wid, "_NET_WM_STATE")
            info = self._read("xwininfo", "-id", wid)
            values = [int(re.search(pattern + r"\s*(-?\d+)", info)[1]) for pattern in
                      ("Absolute upper-left X:", "Absolute upper-left Y:", "Width:", "Height:")]
            if values[2] <= 0 or values[3] <= 0:
                raise ValueError("Invalid Elite window dimensions")
            self.last_target = TargetWindow(int(wid, 16), QRect(*values))
            if '_NET_WM_STATE_HIDDEN' in props or "Map State: IsViewable" not in info:
                self.reason = "hidden"
                return None
            if int(wid, 16) != active_id:
                self.reason = "foreground"
                return None
            self.reason = "active"
            return self.last_target
        except (OSError, subprocess.SubprocessError, TypeError, ValueError) as exc:
            self.reason, self.error = "error", str(exc)
            return None


def create_window_tracker():
    if sys.platform == "win32":
        if QGuiApplication.platformName() != "windows":
            raise RuntimeError("Windows HUD requires Qt's Windows platform")
        from cmdrhelper.ui.navigation_hud_windows import WindowsWindowTracker
        return WindowsWindowTracker()
    return X11WindowTracker()


class NavigationHud(QWidget):
    """Text display, no controls/input; independent of navigation."""
    status_changed = Signal(str, str)
    def __init__(self, controller, tracker=None):
        super().__init__(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
                         | Qt.WindowDoesNotAcceptFocus | Qt.WindowTransparentForInput)
        # A managed utility follows the Helper's desktop and KWin can keep it
        # unmapped beneath fullscreen Elite even while QWidget.isVisible is true.
        # X11 override-redirect maps this output-only window independently. Input
        # and foreground checks remain mandatory; no per-update stacking requests.
        if QGuiApplication.platformName() == "xcb":
            self.setWindowFlag(Qt.X11BypassWindowManagerHint, True)
        self.setWindowTitle("CMDRHelper Navigation HUD")
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.tracker = tracker if tracker is not None else create_window_tracker()
        self._native_windows = getattr(self.tracker, "native_platform", None) == "windows"
        self._windows_failed = False
        if not self._native_windows:
            self.setAttribute(Qt.WA_X11DoNotAcceptFocus)
        self.setFocusPolicy(Qt.NoFocus)
        self.controller = controller
        self.enabled = False
        self.cargo_enabled = False
        self.cargo_provider = None
        self.cargo_data = None
        self.cargo_geometry = QRectF()
        self.message_lines = ()
        self.message_timer = QTimer(self)
        self.message_timer.setSingleShot(True)
        self.message_timer.timeout.connect(self.clear_message)
        self.safe_input = False
        self.status = "off"
        self.status_detail = ""
        self.paint_count = 0
        self.target_geometry = None
        self.setWindowOpacity(1.0)
        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self.follow_target)
        controller.changed.connect(self.refresh_navigation)

    def _status(self, status, detail=""):
        if (status, detail) != (self.status, self.status_detail):
            self.status, self.status_detail = status, detail
            self.status_changed.emit(status, detail)

    def diagnostics(self):
        return dict(created=self.testAttribute(Qt.WA_WState_Created), visible=self.isVisible(),
                    geometry=self.geometry().getRect(),
                    global_origin=(self.mapToGlobal(self.rect().topLeft()).x(),
                                   self.mapToGlobal(self.rect().topLeft()).y()),
                    target_geometry=self.target_geometry.getRect() if self.target_geometry else None,
                    opacity=self.windowOpacity(), mask_empty=self.mask().isEmpty(),
                    paint_count=self.paint_count, status=self.status)

    def _prepare_input(self):
        self._windows_failed = False
        wid = int(self.winId())
        QGuiApplication.sync()
        try:
            self.safe_input = self.tracker.input_is_empty(wid)
            if not self.safe_input:
                raise RuntimeError("HUD input region is not empty; overlay remains hidden.")
        except (OSError, RuntimeError, ValueError) as exc:
            self.safe_input = False
            self.timer.stop()
            self.hide()
            self._status("error", str(exc))
            if self._native_windows:
                self._windows_failure(exc)
                return False
            self.enabled = False
            raise
        return True

    def set_enabled(self, enabled):
        if enabled and not self._prepare_input():
            return
        self.enabled = bool(enabled)
        self._sync_visibility()

    def show_message(self, lines, duration_ms=2000):
        """Temporary output shares native placement; never changes the HUD switch."""
        if not self._prepare_input():
            return
        self.message_lines = tuple(str(line) for line in lines)
        self.message_timer.start(duration_ms)
        self._sync_visibility()

    def set_cargo_enabled(self, enabled):
        """A second persistent group, independent of navigation and messages."""
        if enabled and not self._prepare_input():
            return
        self.cargo_enabled = bool(enabled)
        if not enabled:
            self.cargo_data = None
        self._sync_visibility()

    def clear_message(self):
        self.message_timer.stop()
        self.message_lines = ()
        self._sync_visibility()

    def _sync_visibility(self):
        if self.enabled or self.cargo_enabled or self.message_lines:
            self.timer.start()
            self.follow_target()
        else:
            self.timer.stop()
            self.hide()
            self._status("off")

    def _windows_failure(self, exc):
        self._windows_failed = True
        self.enabled = self.safe_input = False
        self.cargo_enabled = False
        self.timer.stop()
        self.hide()
        self._status("error", str(exc))
        logging.getLogger(__name__).warning("Windows navigation HUD disabled: %s", exc)

    def follow_target(self):
        if self._windows_failed:
            return  # Retry only after explicitly switching the HUD on again.
        self.cargo_data = self.cargo_provider() if self.cargo_enabled and self.cargo_provider else None
        if (not self.cargo_data and not self.message_lines
                and (not self.enabled or not hud_lines(self.controller.state))):
            self.hide()
            self._status("waiting_navigation" if self.enabled else
                         "waiting_cargo" if self.cargo_enabled else "off")
            return
        try:
            target = self.tracker.current() if self.safe_input else None
        except (OSError, RuntimeError, ValueError) as exc:
            if not self._native_windows:
                raise
            self._windows_failure(exc)
            return
        if target is None:
            self.hide()
            candidate = getattr(self.tracker, "last_target", None)
            self.target_geometry = candidate.geometry if isinstance(candidate, TargetWindow) else None
            reason = getattr(self.tracker, "reason", "not_found")
            self._status(reason, getattr(self.tracker, "error", ""))
            return
        self.target_geometry = QRect(target.geometry)
        if self._native_windows:
            try:
                logical = self.tracker.place_overlay(self, target)
            except (OSError, RuntimeError, ValueError) as exc:
                if not self.tracker.window_is_viewable(target.window_id):
                    self.hide()
                    self._status("hidden")
                    return  # Elite closed/minimized mid-update; keep polling.
                self._windows_failure(exc)
                return
            self._status("active", f"{logical.width()} × {logical.height()} @ {logical.x()}, {logical.y()}")
            self.update()
            return
        ratio = self.devicePixelRatioF()
        rect = target.geometry
        logical = QRect(*(round(v / ratio) for v in (rect.x(), rect.y(), rect.width(), rect.height())))
        if not any(screen.geometry().intersects(logical) for screen in QGuiApplication.screens()):
            self.hide()
            self._status("outside")
            return
        if self.geometry() != logical:
            self.setGeometry(logical)
        if not self.isVisible():
            self.show()
        if not self.tracker.window_is_viewable(int(self.winId())):
            self._status("native_hidden")
            return
        self._status("active", f"{logical.width()} × {logical.height()} @ {logical.x()}, {logical.y()}")
        self.update()

    def refresh_navigation(self, _state):
        self.follow_target()

    def closeEvent(self, event):
        self.message_timer.stop()
        self.message_lines = ()
        self.cargo_enabled = False
        self.cargo_data = None
        self.set_enabled(False)
        self.tracker.close()
        super().closeEvent(event)

    def paintEvent(self, event):
        self.paint_count += 1
        self.cargo_geometry = QRectF()
        if not self.enabled and not self.message_lines and not self.cargo_data:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        top = 14.
        navigation = hud_lines(self.controller.state) if self.enabled else ()
        rows = list(zip(navigation, (38, 26, 18), (10, 8, 8)))
        rows += [(text, 30 if index == 0 else 20, 10)
                 for index, text in enumerate(self.message_lines)]
        leftmost = float("inf")
        for text, pixel_size, gap in rows:
            font = painter.font()
            font.setBold(False)
            font.setPixelSize(pixel_size)
            path = QPainterPath()
            path.addText(QPointF(0, 0), font, text)
            bounds = path.boundingRect()
            scale = min(1., max(1., self.width()-24)/max(1., bounds.width()))
            leftmost = min(leftmost, (self.width()-bounds.width()*scale)/2)
            painter.save()
            painter.translate((self.width()-bounds.width()*scale)/2-bounds.left()*scale,
                              top-bounds.top()*scale)
            painter.scale(scale, scale)
            # Dark outlines preserve readability over both bright and dark scenery.
            painter.strokePath(path, QPen(QColor(0, 0, 0, 235), 5,
                                         Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.fillPath(path, QColor("#ff9100"))
            painter.restore()
            top += bounds.height()*scale + gap
        if self.cargo_data:
            self._paint_cargo(painter, leftmost, top)

    def _paint_cargo(self, painter, other_left, other_bottom):
        width = min(420., max(1., self.width() - 32.))
        left = 16.
        room = other_left - left - 12
        if room >= 240:
            width = min(width, room)
        # Keep the tested centered navigation/message layout unchanged. On
        # narrow clients place cargo just below those rows to avoid overlap.
        top = 16. if left + width + 12 <= other_left else other_bottom + 12
        font = painter.font()
        font.setPixelSize(16)
        font.setBold(False)
        metrics = QFontMetricsF(font)
        data = self.cargo_data
        fixed_width = metrics.horizontalAdvance(replace(data, vehicle_name="").text)
        name = metrics.elidedText(data.vehicle_name, Qt.ElideRight, max(0., width - fixed_width))
        path = QPainterPath()
        path.addText(QPointF(0, 0), font, replace(data, vehicle_name=name).text)
        bounds = path.boundingRect()
        scale = min(1., width / max(1., bounds.width()))
        painter.save()
        painter.translate(left - bounds.left()*scale, top - bounds.top()*scale)
        painter.scale(scale, scale)
        painter.strokePath(path, QPen(QColor(0, 0, 0, 235), 3,
                                     Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.fillPath(path, QColor("#ff9100"))
        painter.restore()
        bottom = top + bounds.height()*scale
        if data.fraction is not None:
            bar = QRectF(left, bottom + 6, width, 5)
            painter.setPen(QPen(QColor(0, 0, 0, 235), 1))
            painter.setBrush(QColor(40, 30, 18, 180))
            painter.drawRoundedRect(bar, 2, 2)
            fill = bar.adjusted(1, 1, -1, -1)
            fill.setWidth(fill.width() * data.fraction)
            if fill.width() > 0:
                painter.fillRect(fill, QColor("#c57a00"))
            bottom = bar.bottom()
        self.cargo_geometry = QRectF(left, top, width, bottom-top)
