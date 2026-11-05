"""Compact, wrapping legend for mission semantics, never selection/hover colors."""
from html import escape
from math import ceil

from PySide6.QtCore import QEvent, QSize, QUrl
from PySide6.QtGui import QColor, QPainter, QPixmap, QTextDocument
from PySide6.QtWidgets import QSizePolicy, QWidget

from cmdrhelper.i18n import tr
from .mission_arrival import team_icon


class MissionLegend(QWidget):
    def __init__(self, parent=None, *, light=False):
        super().__init__(parent)
        self.light = light
        self.document = QTextDocument(self)
        self.document.setDocumentMargin(0)
        policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)
        self.refresh()

    def set_light_mode(self, light):
        self.light = light
        self.refresh()

    def refresh(self):
        self.document.setDefaultFont(self.font())
        gold = '#765400' if self.light else '#ffb000'
        green = '#226626' if self.light else '#65d067'
        swatch = QPixmap(12, 12)
        swatch.fill(QColor('#fff4cf' if self.light else '#302918'))
        painter = QPainter(swatch)
        painter.setPen(QColor('#92721f' if self.light else '#c49a3c'))
        painter.drawRect(0, 0, 11, 11)
        painter.end()
        for name, image in (
            ('arrival', swatch.toImage()),
            ('team', team_icon(self.light).pixmap(QSize(16, 16)).toImage()),
        ):
            self.document.addResource(QTextDocument.ImageResource, QUrl('mission:' + name), image)
        labels = [tr('missions.legend_arrival'), tr('missions.legend_accepted'),
                  tr('missions.legend_progress'), tr('missions.team_capable')]
        parts = [f'<img src="mission:arrival" width="12" height="12"> {escape(labels[0])}',
                 f'<span style="color:{gold}">●</span> {escape(labels[1])}',
                 f'<span style="color:{green}">●</span> {escape(labels[2])}',
                 f'<img src="mission:team" width="16" height="16"> {escape(labels[3])}']
        color = self.palette().windowText().color().name()
        self.document.setHtml(f'<span style="color:{color}">' + ' &nbsp; · &nbsp; '.join(parts) + '</span>')
        self.document.setTextWidth(max(1, self.width()))
        self.setAccessibleName(' · '.join(labels))
        self.setToolTip(tr('missions.team_capable_tooltip'))
        self.setFixedHeight(self.heightForWidth(self.width()))
        self.updateGeometry()
        self.update()

    def heightForWidth(self, width):
        self.document.setTextWidth(max(1, width))
        return ceil(self.document.size().height())

    def sizeHint(self):
        return QSize(800, self.heightForWidth(max(1, self.width())))

    def minimumSizeHint(self):
        return QSize(0, self.fontMetrics().height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.setFixedHeight(self.heightForWidth(event.size().width()))

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QEvent.FontChange, QEvent.PaletteChange) and hasattr(self, 'document'):
            self.refresh()

    def paintEvent(self, event):
        self.document.setTextWidth(max(1, self.width()))
        painter = QPainter(self)
        self.document.drawContents(painter)
        painter.end()
