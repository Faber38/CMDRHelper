"""Delayed, view-local loading feedback; never starts work or changes navigation."""
import time

from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

from cmdrhelper.i18n import tr
from .loading_scanner import LoadingScanner


class LoadingState(QWidget):
    def __init__(self, target, delay_ms=150):
        super().__init__(target)
        self.target = target
        self.delay_ms = delay_ms
        self.pending = False
        self.started = 0.0
        self.error = ""
        # Do not repaint the covered item view for every scanner frame.
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        layout = QVBoxLayout(self)
        self.scanner = LoadingScanner(self)
        self.message = QLabel(self)
        self.message.setWordWrap(True)
        self.message.setTextFormat(Qt.PlainText)
        self.message.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.scanner)
        layout.addWidget(self.message)
        self.delay = QTimer(self)
        self.delay.setSingleShot(True)
        self.delay.timeout.connect(self._sync)
        target.installEventFilter(self)
        self.hide()

    def begin(self):
        if not self.pending:
            self.started = time.monotonic()
        self.pending = True
        self.error = ""
        self._sync()

    def finish(self, error=""):
        self.pending = False
        self.error = str(error or "")
        self.delay.stop()
        self._sync()

    def _sync(self):
        self.delay.stop()
        if not self.target.isVisible() or not (self.pending or self.error):
            self.hide()
            return
        remaining = self.delay_ms - (time.monotonic() - self.started) * 1000
        if self.pending and remaining > 0:
            self.hide()
            self.delay.start(max(1, int(remaining + 1)))
            return
        self.setGeometry(self.target.rect())
        self.scanner.setVisible(self.pending)
        self.message.setVisible(bool(self.error))
        self.message.setText(tr('loading.error', error=self.error) if self.error else "")
        self.show()
        self.raise_()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().window())
        painter.end()

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Show, QEvent.Resize):
            self._sync()
        elif event.type() in (QEvent.Hide, QEvent.Close):
            self.delay.stop()
            self.hide()
        return False
