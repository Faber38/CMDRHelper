"""Paint the existing carrier pencil independently of stock/text colours."""
from PySide6.QtCore import QEvent, QRect, QSize, Qt
from PySide6.QtGui import QColor, QPalette, QPainter, QPainterPath
from PySide6.QtWidgets import QHeaderView, QStyle, QStyleOptionHeader, QToolTip

from cmdrhelper.i18n import tr


def marker_color(light, hovered=False):
    return QColor(("#B07D00" if hovered else "#8A6100") if light
                  else ("#FFECB3" if hovered else "#FFD54F"))


def marker_layout(text, metrics, rect, alignment, direction=Qt.LeftToRight):
    value = text.replace("✎", "").rstrip()
    width, gap = max(14, metrics.horizontalAdvance("✎")), metrics.horizontalAdvance(" ")
    value = metrics.elidedText(value, Qt.ElideRight, max(0, rect.width() - width - gap))
    value_width = metrics.horizontalAdvance(value)
    combined = QStyle.alignedRect(direction, alignment,
                                  QSize(value_width + gap + width, metrics.height()), rect)
    value_rect = QRect(combined.left(), combined.top(), value_width, combined.height())
    pen_rect = QRect(combined.left() + value_width + gap, combined.top(), width, combined.height())
    return value, value_rect, pen_rect


def paint_marker_text(painter, layout, text_color, pencil_color):
    value, value_rect, pen_rect = layout
    painter.setPen(text_color)
    painter.drawText(value_rect, Qt.AlignVCenter | Qt.AlignLeft, value)
    # A font may substitute a multicolour emoji for U+270E and ignore setPen.
    # Draw the same pencil affordance as a small scalable monochrome shape.
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)
    size = min(pen_rect.width() - 2, pen_rect.height() - 2)
    painter.translate(pen_rect.center().x() - size / 2, pen_rect.center().y() - size / 2)
    painter.scale(size / 12, size / 12)
    path = QPainterPath()
    for points in (((2, 8), (8, 2), (10, 4), (4, 10)),
                   ((1, 11), (2, 8), (4, 10)),
                   ((8.6, 1.4), (9.6, .4), (11.6, 2.4), (10.6, 3.4))):
        path.moveTo(*points[0])
        for point in points[1:]:
            path.lineTo(*point)
        path.closeSubpath()
    painter.setPen(Qt.NoPen)
    painter.setBrush(pencil_color)
    painter.drawPath(path)
    painter.restore()


class CarrierHeader(QHeaderView):
    """Keep native section sorting/resizing; only paint the pencil separately."""
    def __init__(self, parent):
        super().__init__(Qt.Horizontal, parent)
        self.light = False
        self.hover_position = None
        self.viewport().setMouseTracking(True)

    def _option(self, section):
        option = QStyleOptionHeader()
        self.initStyleOption(option)
        self.initStyleOptionForIndex(option, section)
        option.rect = QRect(self.sectionViewportPosition(section), 0, self.sectionSize(section), self.height())
        return option

    def marker_rect(self):
        if self.count() <= 3 or self.isSectionHidden(3):
            return QRect()
        option = self._option(3)
        rect = self.style().subElementRect(QStyle.SE_HeaderLabel, option, self)
        return marker_layout(option.text, option.fontMetrics, rect, option.textAlignment, self.layoutDirection())[2]

    def paintSection(self, painter, rect, logical_index):
        if logical_index != 3:
            return super().paintSection(painter, rect, logical_index)
        option = self._option(logical_index)
        option.rect = rect
        label_rect = self.style().subElementRect(QStyle.SE_HeaderLabel, option, self)
        layout = marker_layout(option.text, option.fontMetrics, label_rect, option.textAlignment, self.layoutDirection())
        option.text = ""
        painter.save()
        painter.setClipRect(rect)
        self.style().drawControl(QStyle.CE_Header, option, painter, self)
        hovered = self.hover_position is not None and layout[2].contains(self.hover_position)
        group = QPalette.Active if self.isEnabled() else QPalette.Disabled
        color = marker_color(self.light, hovered) if self.isEnabled() else option.palette.color(group, QPalette.ButtonText)
        paint_marker_text(painter, layout, option.palette.color(group, QPalette.ButtonText), color)
        painter.restore()

    def viewportEvent(self, event):
        kind = event.type()
        if kind == QEvent.MouseMove:
            self.hover_position = event.position().toPoint()
            self.viewport().update()
        elif kind in (QEvent.Leave, QEvent.Hide):
            self.hover_position = None
            self.viewport().update()
        elif kind == QEvent.ToolTip and self.isEnabled() and self.marker_rect().contains(event.pos()):
            QToolTip.showText(event.globalPos(), tr("mining.carrier_edit"), self.viewport(), self.marker_rect())
            return True
        return super().viewportEvent(event)
