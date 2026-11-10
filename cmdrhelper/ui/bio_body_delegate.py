"""First-footfall decoration for the BIO/GEO/mining body-name column."""
from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionViewItem, QToolTip

from cmdrhelper.i18n import tr
from cmdrhelper.ui.footfall_icon import paint_footprints


class BioBodyDelegate(QStyledItemDelegate):
    def __init__(self, parent, is_light):
        super().__init__(parent)
        self._is_light = is_light
        self._icons = {}

    @staticmethod
    def _has_footfall(index):
        body = index.data(Qt.UserRole)
        return isinstance(body, dict) and body.get("first_footfall") is True

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        if not self._has_footfall(index):
            return
        light = self._is_light()
        ratio = option.widget.devicePixelRatioF() if option.widget else 1.0
        key = (light, ratio)
        if key not in self._icons:
            pixmap = QPixmap(round(20 * ratio), round(20 * ratio))
            pixmap.setDevicePixelRatio(ratio)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            paint_footprints(painter, QRectF(0, 0, 20, 20), light)
            painter.end()
            self._icons[key] = QIcon(pixmap)
        option.icon = self._icons[key]
        option.decorationSize = QSize(20, 20)
        option.decorationPosition = QStyleOptionViewItem.Left
        option.features |= QStyleOptionViewItem.HasDecoration
        option.features &= ~QStyleOptionViewItem.WrapText
        option.textElideMode = Qt.ElideRight

    def helpEvent(self, event, view, option, index):
        if event.type() == event.Type.ToolTip and self._has_footfall(index):
            styled = QStyleOptionViewItem(option)
            self.initStyleOption(styled, index)
            icon_rect = view.style().subElementRect(
                QStyle.SE_ItemViewItemDecoration, styled, view)
            text = tr("footfall.label") if icon_rect.contains(event.pos()) else str(index.data(Qt.ToolTipRole) or index.data() or "")
            QToolTip.showText(event.globalPos(), text, view)
            return True
        return super().helpEvent(event, view, option, index)
