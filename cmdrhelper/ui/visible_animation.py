"""Visibility lifecycle for decorative timers only; no data acquisition."""
from PySide6.QtCore import QEvent, QTimer


class VisibleAnimationTimer(QTimer):
    def __init__(self, widget):
        super().__init__(widget)
        self._widget = widget
        self._window = None
        self._enabled = False
        widget.installEventFilter(self)
        self._watch_window()

    def _watch_window(self):
        window = self._widget.window()
        if window is self._window:
            return
        if self._window is not None and self._window is not self._widget:
            self._window.removeEventFilter(self)
        self._window = window
        if window is not self._widget:
            window.installEventFilter(self)

    def start(self, interval=None):
        if interval is not None:
            self.setInterval(interval)
        self._enabled = True
        self._sync()

    def stop(self):
        self._enabled = False
        super().stop()

    def _sync(self):
        self._watch_window()
        visible = self._widget.isVisible() and not self._window.isMinimized()
        if self._enabled and visible:
            if not self.isActive():
                super().start()
        else:
            super().stop()

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Show, QEvent.Hide, QEvent.WindowStateChange,
                            QEvent.ParentChange):
            self._sync()
        return False
