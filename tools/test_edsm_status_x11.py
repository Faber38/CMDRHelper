#!/usr/bin/env python3
"""Opt-in native X11 EDSM notice test over a focus-neutral test window.

No Elite interaction, hotkey registration, keyboard or mouse injection, or HTTP.
Run: QT_QPA_PLATFORM=xcb venv/bin/python tools/test_edsm_status_x11.py
"""
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QObject, QRect, Qt, Signal
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtTest import QTest
from cmdrhelper.ui.navigation_hud import NavigationHud, X11WindowTracker, TargetWindow
from cmdrhelper.ui.cargo_hud import CargoHudData


def main():
    app = QApplication([])
    foreground = lambda: subprocess.check_output(['xprop', '-root', '_NET_ACTIVE_WINDOW'])
    before = foreground()
    target = QWidget(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus
                     | Qt.WindowTransparentForInput | Qt.X11BypassWindowManagerHint)
    target.setAttribute(Qt.WA_ShowWithoutActivating)
    target.setFocusPolicy(Qt.NoFocus)
    target.setGeometry(60, 80, 900, 420)
    target.setStyleSheet('background: #183040')
    target.show()
    app.processEvents()

    class Tracker(X11WindowTracker):
        def current(self):
            ratio = target.devicePixelRatioF()
            return TargetWindow(int(target.winId()), QRect(*(round(v*ratio) for v in target.geometry().getRect())))

    class Controller(QObject):
        changed = Signal(object)
    controller = Controller()
    controller.state = SimpleNamespace(snapshot=None, solution=None)
    tracker = Tracker()
    hud = NavigationHud(controller, tracker)
    results = []
    try:
        assert tracker.compositor_available(), 'A real compositor is required'
        for text in ('EDSM: BEKANNT', 'EDSM: NICHT BEKANNT', 'EDSM: KEINE ANTWORT'):
            hud.show_message((text,), 2500, channel='edsm')
            QTest.qWait(150)
            assert hud.isVisible() and not hud.enabled and not hud.cargo_enabled
            assert tracker.input_is_empty(int(hud.winId()))
            assert tracker.window_is_viewable(int(hud.winId())) and hud.paint_count > 0
            assert foreground() == before
            QTest.qWait(2500)
            assert not hud.isVisible() and not hud.edsm_message_lines
            results.append(text)
        hud.cargo_provider = lambda: CargoHudData('Rhino', 67, 72)
        hud.set_cargo_enabled(True)
        hud.show_message(('Schnellfavorit: Testmeldung',), 4000)
        hud.show_message(('EDSM: BEKANNT',), 2500, channel='edsm')
        QTest.qWait(150)
        assert hud.cargo_data and hud.message_lines and hud.edsm_message_lines
        QTest.qWait(2500)
        assert hud.isVisible() and hud.cargo_data and hud.message_lines
        assert not hud.edsm_message_lines
        assert tracker.input_is_empty(int(hud.winId()))
        assert foreground() == before
        print(json.dumps(dict(platform='real Linux/X11', statuses=results, input_region='empty',
                              focus='unchanged', timeout_ms=2500, cargo='preserved',
                              quick_favorite='independent', diagnostics=hud.diagnostics()), indent=2))
    finally:
        hud.close()
        target.close()


if __name__ == '__main__':
    main()
