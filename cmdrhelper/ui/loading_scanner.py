"""Reusable, visibility-bound holographic loading indicator."""
import math
import time

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget

from cmdrhelper.i18n import tr
from cmdrhelper.ui.visible_animation import VisibleAnimationTimer


class LoadingScanner(QWidget):
    def __init__(self, parent=None, *, text=None):
        super().__init__(parent)
        self._text = text
        self.setMinimumSize(220, 220)
        self.timer = VisibleAnimationTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.update)
        self.timer.start()

    def setText(self, text=None):
        """Accept an already translated status, or None for the default."""
        self._text = text
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        light = self.palette().window().color().lightness() > 128
        orange = QColor('#c56f00' if light else '#ff9d00')
        cx, cy = self.width() / 2, self.height() / 2 - 20
        p.translate(cx, cy)
        faint = QColor(orange)
        faint.setAlpha(85)
        p.setPen(QPen(faint, 1))
        p.drawEllipse(QRectF(-62, -62, 124, 124))
        for step in range(24):
            a = math.radians(step * 15)
            p.drawLine(QPointF(67 * math.cos(a), 67 * math.sin(a)),
                       QPointF(72 * math.cos(a), 72 * math.sin(a)))
        p.setPen(QPen(orange, 2.5, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(QRectF(-56, -56, 112, 112), int(-(time.monotonic() * 75 % 360) * 16), 75 * 16)
        p.setPen(QPen(orange, 1.5))
        p.drawPolygon(QPolygonF([QPointF(0, -14), QPointF(11, 10),
                                QPointF(0, 5), QPointF(-11, 10)]))
        p.resetTransform()
        p.setPen(self.palette().windowText().color())
        p.drawText(QRectF(0, cy + 90, self.width(), 40), Qt.AlignCenter,
                   self._text if self._text is not None else tr('loading.data'))
