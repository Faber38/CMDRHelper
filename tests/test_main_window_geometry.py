"""Main-window persistence without AppState, journals or production settings."""
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QByteArray, QRect, QSettings, Qt
from PySide6.QtWidgets import QApplication, QMainWindow

from cmdrhelper.app import _resize_initial_window
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class MainWindowGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = str(Path(directory.name) / "settings.ini")
        self.windows = []
        self.addCleanup(self.cleanup_windows)

    def cleanup_windows(self):
        for window in self.windows:
            window.close()
            window.deleteLater()
        self.app.processEvents()

    def window(self):
        window = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(window)
        window.state = SimpleNamespace(
            settings=QSettings(self.path, QSettings.IniFormat))
        self.windows.append(window)
        return window

    def test_first_start_keeps_existing_default_size_policy(self):
        window = self.window()
        self.assertFalse(window.restore_main_geometry())
        _resize_initial_window(window, self.app.primaryScreen())
        available = self.app.primaryScreen().availableGeometry()
        self.assertEqual(window.width(), min(1500, available.width() - 80))
        self.assertEqual(window.height(), min(900, available.height() - 80))
        self.assertFalse(window.isMaximized())

    def test_close_and_reopen_size_position_in_both_themes(self):
        for stylesheet in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            with self.subTest(theme=stylesheet[:30]):
                window = self.window()
                window.setStyleSheet(stylesheet)
                window.resize(500, 360)
                window.move(100, 80)
                window.show()
                self.app.processEvents()
                expected = window.geometry()
                window.close()
                restored = self.window()
                restored.setStyleSheet(stylesheet)
                self.assertTrue(restored.restore_main_geometry())
                restored.show()
                self.app.processEvents()
                self.assertEqual(restored.geometry(), expected)
                self.assertFalse(restored.isMaximized())
                restored.close()

    def test_maximized_restart_preserves_normal_geometry(self):
        window = self.window()
        window.resize(500, 360)
        window.move(100, 80)
        window.show()
        self.app.processEvents()
        normal = window.geometry()
        window.showMaximized()
        self.app.processEvents()
        window.close()
        restored = self.window()
        self.assertTrue(restored.restore_main_geometry())
        restored.show()
        self.app.processEvents()
        self.assertTrue(restored.isMaximized())
        self.assertEqual(restored.normalGeometry(), normal)
        restored.showNormal()
        self.app.processEvents()
        self.assertEqual(restored.geometry(), normal)

    def test_invalid_settings_use_fallback(self):
        for value in ("invalid", 123, QByteArray(), QByteArray(b"broken geometry")):
            with self.subTest(value=value):
                window = self.window()
                window.state.settings.setValue("main_window/geometry", value)
                self.assertFalse(window.restore_main_geometry())
                _resize_initial_window(window, self.app.primaryScreen())
                self.assertGreater(window.width(), 0)
                self.assertGreaterEqual(window.y(), 0)

    def test_maximized_normal_size_is_repaired_for_smaller_screen(self):
        window = self.window()
        window.setGeometry(100, 80, 600, 500)
        window.show()
        window.showMaximized()
        self.app.processEvents()
        window.close()
        restored = self.window()
        fit = MainWindow._visible_main_geometry
        smaller = QRect(0, 0, 480, 400)
        with patch.object(MainWindow, "_visible_main_geometry",
                          side_effect=lambda rect, screens: fit(rect, [smaller])):
            self.assertTrue(restored.restore_main_geometry())
        restored.show()
        self.app.processEvents()
        self.assertTrue(restored.isMaximized())
        restored.showNormal()
        self.app.processEvents()
        self.assertTrue(smaller.contains(restored.geometry()))

    def test_valid_second_monitor_position_is_preserved(self):
        screens = [QRect(0, 0, 1920, 1080), QRect(1920, 0, 2560, 1440)]
        rect = QRect(2050, 100, 1400, 900)
        self.assertEqual(MainWindow._visible_main_geometry(rect, screens), rect)

    def test_removed_monitor_returns_to_visible_primary(self):
        rect = MainWindow._visible_main_geometry(
            QRect(2050, 100, 1400, 900), [QRect(0, 0, 1920, 1080)])
        self.assertTrue(QRect(0, 0, 1920, 1080).contains(rect))
        self.assertEqual((rect.width(), rect.height()), (1400, 900))

    def test_smaller_resolution_limits_size(self):
        screen = QRect(0, 0, 1280, 720)
        rect = MainWindow._visible_main_geometry(QRect(100, 80, 1400, 900), [screen])
        self.assertTrue(screen.contains(rect))
        self.assertGreaterEqual(rect.top(), 30)
        self.assertLess(rect.width(), 1280)
        self.assertLess(rect.height(), 720)

    def test_rearranged_monitors_and_negative_position(self):
        screens = [QRect(0, 0, 1920, 1080), QRect(-2560, 0, 2560, 1440)]
        rect = MainWindow._visible_main_geometry(QRect(-2300, -100, 1400, 900), screens)
        self.assertTrue(screens[0].contains(rect))
        self.assertGreaterEqual(rect.x(), 0)
        self.assertGreaterEqual(rect.y(), 0)

    def test_partial_visibility_moves_whole_window_onto_screen(self):
        screen = QRect(0, 0, 1920, 1080)
        rect = MainWindow._visible_main_geometry(QRect(1850, 1000, 800, 600), [screen])
        self.assertTrue(screen.contains(rect))


if __name__ == "__main__":
    unittest.main()
