"""Shared vector footprints in logical pixels, independent of emoji fonts."""
from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget


def footfall_color(light=False):
    return QColor("#28752c" if light else "#65d067")


def paint_footprints(painter, rect, light=False):
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)
    painter.translate(rect.x(), rect.y())
    painter.scale(rect.width() / 20, rect.height() / 20)
    painter.setPen(Qt.NoPen)
    painter.setBrush(footfall_color(light))
    for x, y, angle in ((5, 12, -18), (14, 8, 18)):
        painter.save()
        painter.translate(x, y)
        painter.rotate(angle)
        painter.drawEllipse(QRectF(-2.2, -2.5, 4.4, 7))
        painter.drawEllipse(QRectF(-2.5, -7, 5, 3.5))
        painter.restore()
    painter.restore()


class FootfallIcon(QWidget):
    def __init__(self, light=False, parent=None):
        super().__init__(parent)
        self.light = light
        self.setFixedSize(22, 22)

    def sizeHint(self):
        return QSize(22, 22)

    def set_light_mode(self, light):
        self.light = light
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        paint_footprints(painter, QRectF(1, 1, 20, 20), self.light)
