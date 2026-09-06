"""Bounded, focus-neutral X11 HUD visibility probe.

--window opens the real navigation window for testing its HUD switch.
--capture records the first visible HUD layer and desktop under /tmp.
Only --verify-switch deliberately prepares/restores foreground for the test.
No synthetic game input, movement or resize is performed.
"""
import argparse
import faulthandler
import json
from pathlib import Path
import sys
import subprocess
import time
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from cmdrhelper.planet_navigation import PlanetNavigationController
from cmdrhelper.ui.navigation_hud import NavigationHud
from cmdrhelper.ui.planet_navigation_window import PlanetNavigationWindow


class ProbeSettings:
    def value(self, key, default=None):
        return default

    def setValue(self, *args):
        pass

    def sync(self):
        pass


def main():
    faulthandler.enable()
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=180)
    parser.add_argument("--window", action="store_true")
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--journal-folder", type=Path)
    parser.add_argument("--live-target", nargs=2, type=float, metavar=("LAT", "LON"))
    parser.add_argument("--verify-switch", action="store_true",
                        help="Controlled native test: prepare Elite foreground, toggle the overlay, restore focus")
    args = parser.parse_args()
    app = QApplication([sys.argv[0]])
    app.setQuitOnLastWindowClosed(False)
    from cmdrhelper.ui.styles import DARK_STYLESHEET
    app.setStyleSheet(DARK_STYLESHEET)
    controller = PlanetNavigationController(SimpleNamespace(journal_folder=args.journal_folder))
    if args.live_target:
        if args.journal_folder is None:
            parser.error("--live-target requires --journal-folder")
        controller.start()
        controller.set_target(*args.live_target)
    window = PlanetNavigationWindow(controller, ProbeSettings()) if args.window or args.verify_switch else None
    standalone = NavigationHud(controller)
    start = time.monotonic()
    previous = None
    captured = False
    inspected = set()
    restore_id = None
    timer = QTimer()

    def hud():
        return standalone

    def report():
        nonlocal previous, captured
        overlay = hud()
        observation = {}
        if controller.state.solution is not None:
            solution = controller.state.solution
            observation.update(course=solution.bearing, heading=controller.state.snapshot.heading,
                               relative=solution.relative)
        if overlay is not None:
            tracker = overlay.tracker
            from cmdrhelper.ui.navigation_hud import hud_lines
            observation['text'] = hud_lines(controller.state)
            observation.update(overlay.diagnostics())
            observation.update(enabled=overlay.enabled,
                active=tracker._read('xprop', '-root', '_NET_ACTIVE_WINDOW').strip(),
                input_empty=tracker.input_is_empty(int(overlay.winId())))
            wid = hex(int(overlay.winId()))
            if overlay.isVisible() and wid not in inspected:
                inspected.add(wid)
                observation['native'] = tracker._read('xprop', '-id', wid,
                    '_NET_WM_WINDOW_TYPE', '_NET_WM_STATE', '_NET_WM_WINDOW_OPACITY', 'WM_HINTS')
                observation['native_geometry'] = tracker._read('xwininfo', '-id', wid)
                observation['stacking'] = tracker._read('xprop', '-root', '_NET_CLIENT_LIST_STACKING')
            if args.capture and overlay.isVisible() and overlay.paint_count and not captured:
                app.primaryScreen().grabWindow(0).save('/tmp/hud-feedback-desktop.png')
                overlay.grab().save('/tmp/hud-feedback-layer.png')
                if window:
                    window.grab().save('/tmp/hud-feedback-window.png')
                captured = True
                observation['capture'] = '/tmp/hud-feedback-desktop.png'
        if observation != previous:
            print(json.dumps(dict(seconds=round(time.monotonic()-start, 1), **observation)), flush=True)
            previous = observation

    def finish():
        timer.stop()
        if window:
            window.close()
        standalone.close()
        if restore_id:
            subprocess.run(["wmctrl", "-ia", restore_id], check=False)
        app.quit()

    def prepare_verification():
        nonlocal restore_id
        import re
        active = subprocess.check_output(["xprop", "-root", "_NET_ACTIVE_WINDOW"], text=True)
        restore_id = re.search(r"0x[0-9a-fA-F]+", active)[0]
        rows = subprocess.check_output(["wmctrl", "-lx"], text=True).splitlines()
        elite = next(row.split()[0] for row in rows
                     if 'steam_app_359320' in row.lower() and 'Elite - Dangerous' in row)
        # Test preparation only. Production HUD never requests foreground/focus.
        subprocess.run(["wmctrl", "-ia", elite], check=True)
        print(json.dumps(dict(test_preparation="Elite foreground requested", elite_id=elite)), flush=True)
        QTimer.singleShot(1000, lambda: standalone.set_enabled(False))
        QTimer.singleShot(5000, lambda: standalone.set_enabled(True))
        QTimer.singleShot(6000, report)

    try:
        if window:
            window.setWindowTitle('Planeten-Navigation – HUD-Sichttest')
            window.show()
        standalone.set_enabled(True)
        report()
        if args.verify_switch:
            QTimer.singleShot(500, prepare_verification)
        timer.timeout.connect(report)
        timer.start(500)
        QTimer.singleShot(args.seconds * 1000, finish)
        app.exec()
    finally:
        timer.stop()
        if window:
            window.close()
        standalone.close()


if __name__ == '__main__':
    main()
