from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QDialog, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget,
)

from cmdrhelper.i18n import tr


class ShipLane(QWidget):
    """Leichte, rein mit Qt gezeichnete Zwei-Schiff-Animation."""

    def __init__(self, light=False, parent=None):
        super().__init__(parent)
        self.light = bool(light)
        self.position = 0.0
        self.animation_ticks = 0
        self.setFixedHeight(54)
        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self._advance)

    @property
    def running(self):
        return self.timer.isActive()

    def start(self):
        self.timer.start()

    def stop(self):
        self.timer.stop()

    def _advance(self):
        self.position = (self.position + 0.006) % 1.0
        self.animation_ticks += 1
        self.update()

    @staticmethod
    def _ship_path(x, y, direction):
        sign = 1 if direction > 0 else -1
        path = QPainterPath()
        path.moveTo(x + sign * 15, y)
        path.lineTo(x - sign * 9, y - 7)
        path.lineTo(x - sign * 4, y - 2)
        path.lineTo(x - sign * 15, y)
        path.lineTo(x - sign * 4, y + 2)
        path.lineTo(x - sign * 9, y + 7)
        path.closeSubpath()
        return path

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        muted = QColor("#89939c" if not self.light else "#65717c")
        orange = QColor("#ff9d00" if not self.light else "#c56f00")
        painter.setPen(QPen(muted, 1, Qt.DotLine))
        painter.drawLine(22, 16, max(22, self.width() - 22), 16)
        painter.drawLine(22, 38, max(22, self.width() - 22), 38)
        span = max(1, self.width() - 54)
        x_top = 27 + span * self.position
        x_bottom = 27 + span * (1.0 - self.position)
        painter.setPen(QPen(orange, 1.2))
        painter.setBrush(orange)
        painter.drawPath(self._ship_path(x_top, 16, 1))
        painter.drawPath(self._ship_path(x_bottom, 38, -1))


class StartupProgressDialog(QDialog):
    def __init__(self, light=False, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("startup.title"))
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        self.setModal(False)
        self.setMinimumWidth(470)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(8)
        self.ships = ShipLane(light=light)
        layout.addWidget(self.ships)
        self.title_label = QLabel(tr("startup.title"), objectName="appTitle")
        layout.addWidget(self.title_label)
        self.phase_label = QLabel(tr("startup.phase.preparing"), objectName="sectionTitle")
        layout.addWidget(self.phase_label)
        self.count_label = QLabel(tr("startup.busy"), objectName="cardValue")
        layout.addWidget(self.count_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(True)
        layout.addWidget(self.progress)
        self.file_label = QLabel("", objectName="muted")
        self.file_label.setWordWrap(True)
        layout.addWidget(self.file_label)
        self.close_button = QPushButton(tr("common.close"))
        self.close_button.clicked.connect(self.reject)
        self.close_button.setVisible(False)
        layout.addWidget(self.close_button)

    def begin(self, total=0):
        if total > 0:
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
            self.progress.setFormat("0 %")
            self.count_label.setText(tr("startup.count", current=0, total=total))
        else:
            self.progress.setRange(0, 0)
            self.count_label.setText(tr("startup.busy"))
        self.ships.start()
        self.show()
        self.raise_()

    def set_progress(self, current, total, phase_key, filename=""):
        current, total = int(current), int(total)
        self.phase_label.setText(tr(phase_key))
        self.file_label.setText(str(filename or ""))
        if total > 0:
            percent = max(0, min(100, int(round(current * 100 / total))))
            self.progress.setRange(0, 100)
            self.progress.setValue(percent)
            self.progress.setFormat(f"{percent} %")
            self.count_label.setText(
                tr("startup.count", current=current, total=total)
            )
        else:
            self.progress.setRange(0, 0)
            self.count_label.setText(tr("startup.busy"))

    def finish(self, error=""):
        self.ships.stop()
        if error:
            self.phase_label.setText(tr("startup.error"))
            self.count_label.setText(tr("startup.error_detail", error=error))
            self.progress.setRange(0, 100)
            self.progress.setValue(0)
            self.progress.setFormat(tr("startup.failed"))
            self.close_button.setVisible(True)
            return
        self.phase_label.setText(tr("startup.ready"))
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.progress.setFormat("100 %")
        QTimer.singleShot(120, self.accept)
