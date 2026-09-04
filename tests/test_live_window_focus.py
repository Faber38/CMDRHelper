import os
import unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow

from cmdrhelper.ui.main_window import MainWindow


class _Settings:
    def __init__(self):
        self.values = {"cargo_live/enabled": True}

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value

    def sync(self):
        pass


class LiveWindowFocusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        # Use the production constructors and refresh paths without starting
        # journal watchers, network services, or the full main-window UI.
        self.main = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(self.main)
        self.main.state = SimpleNamespace(
            settings=_Settings(), system="Test System", system_address=42,
            system_bodies=[{
                "body_id": 2, "name": "Test System 2", "body_type": "Planet",
                "planet_class": "High metal content body",
                "possible_value": 300_000, "biological_signals": 3,
                "biology": [],
            }],
        )
        self.main._cargo_live_window = None
        self.main._explorer_value_live_window = None
        self.main._explorer_bio_live_window = None
        self.main._explorer_live_system = "Test System"
        self.main._explorer_value_yellow_threshold = lambda: 200_000
        self.main._explorer_live_window_enabled = lambda kind: True
        self.main._format_reward = lambda value: f"{int(value)} Cr"
        self.snapshot = {"vessel": "Ship", "count": 0, "inventory": []}
        self.addCleanup(self.cleanup_windows)

    def cleanup_windows(self):
        for window in self.windows():
            if window is not None:
                window.close()
        self.main.deleteLater()
        self.app.processEvents()

    def windows(self):
        return (
            self.main._cargo_live_window,
            self.main._explorer_value_live_window,
            self.main._explorer_bio_live_window,
        )

    def refresh(self):
        self.main._refresh_cargo_live_window(self.snapshot)
        self.main._refresh_explorer_live_windows()

    def test_automatic_show_updates_and_reopening(self):
        from cmdrhelper.ui.main_window import CargoLiveWindow, ExplorerLiveListWindow

        shown = []

        def checked_show(window):
            self.assertTrue(window.testAttribute(Qt.WA_ShowWithoutActivating))
            self.assertFalse(window.windowFlags() & Qt.WindowDoesNotAcceptFocus)
            self.assertFalse(window.windowFlags() & Qt.WindowTransparentForInput)
            self.assertTrue(window.isEnabled())
            shown.append(window)
            QMainWindow.show(window)

        with ExitStack() as stack:
            for cls in (CargoLiveWindow, ExplorerLiveListWindow):
                stack.enter_context(patch.object(cls, "show", checked_show))
                for method in ("raise_", "activateWindow", "setFocus",
                               "showNormal", "setWindowState"):
                    stack.enter_context(patch.object(
                        cls, method, side_effect=AssertionError(
                            f"Automatic refresh must not call {method}"
                        ),
                    ))
            self.refresh()
            self.assertEqual(shown, list(self.windows()))
            self.assertTrue(all(window.isVisible() for window in self.windows()))

            self.snapshot["count"] = 1
            self.main.state.system_bodies[0]["possible_value"] = 400_000
            self.main.state.system_bodies[0]["biological_signals"] = 4
            self.refresh()
            self.assertEqual(len(shown), 3)

            for window in self.windows():
                window.close()
            self.refresh()
            self.assertEqual(shown[3:], list(self.windows()))

            self.main._refresh_cargo_live_window(None)
            self.main.state.system = "Next System"
            self.main._refresh_explorer_live_windows()
            self.assertTrue(all(not window.isVisible() for window in self.windows()))
            self.refresh()
            self.assertEqual(shown[6:], list(self.windows()))


if __name__ == "__main__":
    unittest.main()
