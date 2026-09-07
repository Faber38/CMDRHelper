"""Opt-in native X11 cargo overlay probe above an inert test window.

Only discovery is substituted. Geometry, compositor, native input shape and
mapping use the production X11 backend. No focus requests or input injection.
Run: QT_QPA_PLATFORM=xcb venv/bin/python tools/test_cargo_hud_x11.py
"""
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QObject, QRect, Qt, Signal
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget
from cmdrhelper.i18n import set_language
from cmdrhelper.ui.cargo_hud import CargoHudData
from cmdrhelper.ui.navigation_hud import NavigationHud, TargetWindow, X11WindowTracker


def main():
    app = QApplication([])
    set_language("de")
    active = lambda: subprocess.check_output(['xprop', '-root', '_NET_ACTIVE_WINDOW'])
    foreground = active()
    target = QWidget(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus
                     | Qt.WindowTransparentForInput | Qt.X11BypassWindowManagerHint)
    target.setAttribute(Qt.WA_ShowWithoutActivating)
    target.setFocusPolicy(Qt.NoFocus)
    target.setGeometry(60, 80, 1000, 550)
    target.setStyleSheet('background: #183040')
    target.show()
    app.processEvents()

    class Tracker(X11WindowTracker):
        def current(self):
            if not target.isVisible():
                self.reason = "hidden"
                return None
            ratio = target.devicePixelRatioF()
            return TargetWindow(int(target.winId()), QRect(*(
                round(v*ratio) for v in target.geometry().getRect())))

    class Controller(QObject):
        changed = Signal(object)

    controller = Controller()
    controller.state = SimpleNamespace(snapshot=None, solution=None)
    tracker = Tracker()
    hud = NavigationHud(controller, tracker)
    data = CargoHudData("Rhino", 67, 72)
    hud.cargo_provider = lambda: data
    try:
        assert tracker.compositor_available(), 'X11 compositor required'
        hud.set_cargo_enabled(True)
        QTest.qWait(250)
        assert hud.isVisible() and not hud.enabled
        assert tracker.input_is_empty(int(hud.winId()))
        assert tracker.window_is_viewable(int(hud.winId()))
        assert hud.paint_count > 0 and active() == foreground
        hud.grab().save('/tmp/cargo-hud-x11-layer.png')
        controller.state = SimpleNamespace(snapshot=object(), solution=SimpleNamespace(
            relative=2, bearing=17, distance_m=145600, undefined_reason=""))
        hud.set_enabled(True)
        hud.show_message(('★ Favorit gespeichert', 'Sol 1'), 500)
        QTest.qWait(200)
        hud.grab().save('/tmp/cargo-hud-x11-combined.png')
        QTest.qWait(400)
        assert not hud.message_lines and hud.isVisible() and hud.cargo_enabled
        hud.set_enabled(False)
        target.hide()
        QTest.qWait(250)
        assert not hud.isVisible()
        target.setGeometry(100, 100, 850, 500)
        target.show()
        data = CargoHudData("ERFT-BÜFFEL", 128, 256)
        QTest.qWait(250)
        assert hud.isVisible() and hud.geometry() == target.geometry()
        assert hud.cargo_data == data and active() == foreground
        print(json.dumps(dict(result="PASS", native_input_empty=True,
                              foreground_unchanged=True, cargo_without_navigation=True,
                              concurrent_message_expiry=True, hide_restore=True,
                              geometry=hud.geometry().getRect(),
                              captures=['/tmp/cargo-hud-x11-layer.png',
                                        '/tmp/cargo-hud-x11-combined.png'])))
    finally:
        hud.close()
        target.close()


if __name__ == '__main__':
    main()
