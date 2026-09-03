from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import QSize
    from PySide6.QtWidgets import QApplication, QWidget
    from cmdrhelper.app import (
        INITIAL_WINDOW_MARGIN,
        _resize_initial_window,
    )
except ImportError:
    QApplication = None


class _Geometry:
    def __init__(self, width, height):
        self._width = width
        self._height = height

    def width(self):
        return self._width

    def height(self):
        return self._height


class _Screen:
    def __init__(self, width, height):
        self._geometry = _Geometry(width, height)

    def availableGeometry(self):
        return self._geometry


@unittest.skipIf(QApplication is None, "PySide6 ist nicht installiert")
class InitialWindowSizeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def window(self, minimum_width=0, minimum_height=0):
        window = QWidget()
        window.setMinimumSize(minimum_width, minimum_height)
        return window

    def test_leaves_margin_on_smaller_screen(self):
        window = self.window(900, 600)

        _resize_initial_window(window, _Screen(1366, 768))

        self.assertEqual(
            window.size(),
            QSize(1366 - INITIAL_WINDOW_MARGIN, 768 - INITIAL_WINDOW_MARGIN),
        )

    def test_keeps_preferred_size_on_larger_screen(self):
        window = self.window(900, 600)

        _resize_initial_window(window, _Screen(1920, 1080))

        self.assertEqual(window.size(), QSize(1500, 900))

    def test_never_undercuts_layout_minimum(self):
        window = self.window(1320, 740)

        _resize_initial_window(window, _Screen(1280, 720))

        self.assertEqual(window.size(), QSize(1320, 740))


if __name__ == "__main__":
    unittest.main()
