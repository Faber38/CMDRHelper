"""Regression for closed cyclic widgets surviving into stylesheet changes."""
import os
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QWidget
from shiboken6 import isValid
from qt_widget_cleanup import destroy_widget


class WidgetCleanupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_closed_cycle_and_timer_are_destroyed_before_theme_change(self):
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        for color in ('#FFCC33', '#1565C0'):
            widget = QWidget()
            widget.cycle = widget
            timer = QTimer(widget)
            timer.start(10000)
            widget.show()
            self.app.processEvents()
            widget.close()
            self.assertTrue(isValid(widget))
            destroy_widget(widget)
            self.assertFalse(isValid(widget))
            self.assertFalse(isValid(timer))
            self.assertNotIn(widget, self.app.allWidgets())
            self.app.setStyleSheet('QWidget { color: ' + color + '; }')
            destroy_widget(widget)  # Cleanup registrations may run after explicit cleanup.

    def test_partial_window_cleanup_does_not_restart_close_protocol(self):
        class PartialWindow(QWidget):
            def closeEvent(self, event):
                raise AssertionError('partial fixture must not initiate shutdown')
        widget = PartialWindow()
        destroy_widget(widget, close=False)
        self.assertFalse(isValid(widget))
