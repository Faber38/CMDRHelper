#!/usr/bin/env python3
"""Opt-in real X11 smoke test. Never sends keys to the desktop/Elite.

Parent display: passive registration/conflict/cleanup + no-activate transparent
message above a test rectangle. Key injection runs ONLY in a private Xephyr.
Run from the repository: QT_QPA_PLATFORM=xcb venv/bin/python tools/test_quick_favorite_x11.py
"""
import ctypes as C
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QObject, Signal, Qt, QRect, QTimer
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtTest import QTest
from cmdrhelper.global_hotkey_x11 import X11Hotkey
from cmdrhelper.ui.navigation_hud import NavigationHud, X11WindowTracker, TargetWindow
from types import SimpleNamespace


def nested():
    app = QApplication([])
    process = subprocess.Popen([sys.executable, __file__, '--target'], stdout=subprocess.PIPE,
                               text=True, env=os.environ)
    target_id = int(process.stdout.readline().strip())
    backend = X11Hotkey(lambda: received.append(True))
    received = []
    try:
        token = backend.register('Ctrl+Alt+Shift+F11')
        # Explicitly focus ONLY a window on the isolated nested X server.
        backend.x.XSetInputFocus.argtypes = [C.c_void_p, C.c_ulong, C.c_int, C.c_ulong]
        backend.x.XSetInputFocus(backend.display, target_id, 1, 0)
        backend.x.XSync(backend.display, 0)
        subprocess.run(['xdotool', 'key', 'ctrl+alt+shift+F11'], check=True)
        QTest.qWait(100)
        assert len(received) == 1, received
        backend.unregister(token)
        subprocess.run(['xdotool', 'key', 'ctrl+alt+shift+F11'], check=True)
        QTest.qWait(100)
        assert len(received) == 1
        print('PASS isolated X11: foreign focus, native event, exactly once, removal', flush=True)
    finally:
        backend.close()
        process.terminate()
        process.wait(timeout=5)


def desktop():
    app = QApplication([])
    a, b = X11Hotkey(lambda: None), X11Hotkey(lambda: None)
    try:
        token = a.register('Ctrl+Alt+Shift+F11')
        try:
            b.register('Ctrl+Alt+Shift+F11')
        except RuntimeError:
            pass
        else:
            raise AssertionError('Conflict was not detected')
        replacement = a.register('Ctrl+Alt+Shift+F10')
        a.unregister(token)
        b.register('Ctrl+Alt+Shift+F11')
        a.close()
        b.register('Ctrl+Alt+Shift+F10')
        print('PASS desktop X11: registration, conflict, replacement, cleanup', flush=True)
    finally:
        a.close()
        b.close()

    active = lambda: subprocess.check_output(['xprop', '-root', '_NET_ACTIVE_WINDOW'])
    before = active()
    target = QWidget(None, Qt.Tool | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus
                      | Qt.WindowTransparentForInput | Qt.X11BypassWindowManagerHint)
    target.setAttribute(Qt.WA_ShowWithoutActivating)
    target.setFocusPolicy(Qt.NoFocus)
    target.setGeometry(60, 80, 800, 450)
    target.setStyleSheet('background: #183040')
    target.show()
    app.processEvents()

    class Tracker(X11WindowTracker):
        def current(self):
            # Deliberately substitute only target discovery, never pretend this
            # test rectangle is an actual foreground Elite process.
            rect = target.geometry()
            ratio = target.devicePixelRatioF()
            return TargetWindow(int(target.winId()), QRect(*(round(v*ratio) for v in rect.getRect())))

    class Controller(QObject):
        changed = Signal(object)
    controller = Controller()
    controller.state = SimpleNamespace(snapshot=None, solution=None)
    tracker = Tracker()
    assert tracker.compositor_available(), 'Real transparency requires a compositor'
    hud = NavigationHud(controller, tracker)
    try:
        hud.show_message(('★ FAVORIT GESPEICHERT', 'X11 test window', '0.000000° / 0.000000°'))
        QTest.qWait(200)
        assert hud.isVisible() and not hud.enabled
        assert tracker.input_is_empty(int(hud.winId()))
        assert tracker.window_is_viewable(int(hud.winId()))
        assert hud.paint_count > 0
        assert active() == before, 'Focus changed'
        QTest.qWait(2100)
        assert not hud.isVisible() and not hud.enabled and not hud.timer.isActive()
        assert active() == before
        print('PASS desktop X11: native map/paint, empty input region, unchanged foreground, two-second expiry, HUD off', flush=True)
    finally:
        hud.close()
        target.close()

    # Nested server prevents any generated key from reaching desktop applications.
    display_number = next(n for n in range(90, 110) if not Path(f'/tmp/.X11-unix/X{n}').exists())
    display = f':{display_number}'
    with tempfile.TemporaryDirectory(prefix='cmdrh-x11-') as folder:
        with open(Path(folder) / 'xephyr.log', 'w') as log:
            server = subprocess.Popen(['Xephyr', display, '-screen', '640x480', '-ac', '-no-host-grab'],
                                      stdout=log, stderr=log)
            try:
                for _ in range(50):
                    if Path(f'/tmp/.X11-unix/X{display_number}').exists():
                        break
                    if server.poll() is not None:
                        raise RuntimeError('Xephyr failed')
                    time.sleep(.1)
                env = dict(os.environ, DISPLAY=display, QT_QPA_PLATFORM='xcb', CMDRH_PRIVATE_X11_TEST='1')
                subprocess.run([sys.executable, __file__, '--nested'], env=env, check=True, timeout=15)
            finally:
                server.terminate()
                server.wait(timeout=5)


if __name__ == '__main__':
    if '--target' in sys.argv:
        if os.environ.get('CMDRH_PRIVATE_X11_TEST') != '1':
            raise SystemExit('Target mode requires the isolated test server')
        app = QApplication([])
        target = QWidget()
        target.setWindowTitle('CMDRHelper isolated foreign process')
        target.resize(500, 300)
        target.show()
        app.processEvents()
        print(int(target.winId()), flush=True)
        QTimer.singleShot(10000, app.quit)
        app.exec()
    elif '--nested' in sys.argv:
        if os.environ.get('CMDRH_PRIVATE_X11_TEST') != '1':
            raise SystemExit('Nested mode must be launched by the test harness')
        nested()
    else:
        desktop()
