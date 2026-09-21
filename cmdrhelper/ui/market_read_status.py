"""Compact painted market acknowledgement; presentation only, no cache access."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QPainterPath, QPen, QColor
from PySide6.QtWidgets import QLabel

from cmdrhelper.i18n import tr


class MarketReadStatus(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('observedMarketStatus')
        self.setTextFormat(Qt.TextFormat.PlainText)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.status = 'open'

    def set_status(self, status):
        self.status = status
        self.setProperty('observed', status == 'read')
        self.setText(tr('recommend.market_' + status))
        self.setToolTip(tr('recommend.market_' + status + '_tooltip'))
        self.setAccessibleName(self.text())
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        color = self.palette().color(self.foregroundRole())
        top = max(2.0, (self.fontMetrics().height() - 12) / 2)
        painter.setPen(QPen(color, 1.3))
        painter.setBrush(color if self.status == 'read' else Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(2, top, 12, 12))
        if self.status == 'read':
            painter.setPen(QPen(QColor('white'), 1.6, Qt.PenStyle.SolidLine,
                                Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            tick = QPainterPath()
            tick.moveTo(5, top + 6)
            tick.lineTo(7, top + 8)
            tick.lineTo(11, top + 4)
            painter.drawPath(tick)
