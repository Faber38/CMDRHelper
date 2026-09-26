"""Inline copy controls without changing the table's normal row actions."""
from PySide6.QtCore import QEvent, QPersistentModelIndex, QRect, Qt, Signal
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QStyle, QStyledItemDelegate, QStyleOptionToolButton, QStyleOptionViewItem,
    QToolButton, QToolTip,
)

from cmdrhelper.i18n import tr


class RecentSystemCopyDelegate(QStyledItemDelegate):
    copyRequested = Signal(int, int)

    def __init__(self, table, *, column=1, name_role=Qt.UserRole, style_delegate=None):
        super().__init__(table)
        self._column = column
        self._name_role = name_role
        self._style_delegate = style_delegate
        # Use the same native tool-button appearance as the chronicle heading.
        self._button = QToolButton(table)
        self._button.setText("⧉")
        self._button.setAutoRaise(True)
        self._button.hide()
        self._pressed = QPersistentModelIndex()
        table.setMouseTracking(True)
        table.viewport().installEventFilter(self)

    def initStyleOption(self, option, index):
        if self._style_delegate is not None:
            self._style_delegate.initStyleOption(option, index)
        else:
            super().initStyleOption(option, index)

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        self._button.setFont(option.font)
        size.setHeight(max(size.height(), self._button.sizeHint().height()))
        name = index.data(self._name_role)
        if isinstance(name, str) and name.strip() and name.strip() != "–":
            size.setWidth(size.width() + self._button.sizeHint().width() + 4)
        return size

    def copy_rect(self, option, index):
        name = index.data(self._name_role)
        if not isinstance(name, str) or not name.strip() or name.strip() == "–":
            return QRect(), ""
        self._button.setFont(option.font)
        size = self._button.sizeHint()
        area = option.rect.adjusted(3, 0, -3, 0)
        width = min(size.width(), max(0, area.width()))
        text = option.fontMetrics.elidedText(
            index.data() or "", Qt.ElideRight, max(0, area.width() - width - 4)
        )
        x = area.left() + option.fontMetrics.horizontalAdvance(text) + (4 if text else 0)
        height = min(size.height(), area.height())
        return QRect(x, area.top() + (area.height() - height) // 2, width, height), text

    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        rect, text = self.copy_rect(opt, index)
        if rect.isEmpty():
            super().paint(painter, option, index)
            return
        style = self.parent().style()
        opt.text = ""
        style.drawControl(QStyle.CE_ItemViewItem, opt, painter, self.parent())
        painter.save()
        painter.setClipRect(option.rect)
        painter.setFont(opt.font)
        role = QPalette.HighlightedText if opt.state & QStyle.State_Selected else QPalette.Text
        text_rect = option.rect.adjusted(3, 0, 0, 0)
        text_rect.setRight(rect.left() - 5)
        style.drawItemText(painter, text_rect, Qt.AlignLeft | Qt.AlignVCenter,
                           opt.palette, True, text, role)
        button_opt = QStyleOptionToolButton()
        self._button.initStyleOption(button_opt)
        button_opt.rect = rect
        button_opt.palette = option.palette
        if option.state & QStyle.State_Selected:
            button_opt.palette.setColor(QPalette.ButtonText,
                                        option.palette.color(QPalette.HighlightedText))
        style.drawComplexControl(QStyle.CC_ToolButton, button_opt, painter, self._button)
        painter.restore()

    def _hit(self, point):
        table = self.parent()
        index = table.indexAt(point)
        if not index.isValid() or index.column() != self._column:
            return index, False
        option = QStyleOptionViewItem()
        option.initFrom(table)
        option.font = table.font()
        self.initStyleOption(option, index)
        option.rect = table.visualRect(index)
        rect, _ = self.copy_rect(option, index)
        return index, rect.contains(point)

    def eventFilter(self, watched, event):
        kind = event.type()
        if kind == QEvent.Leave:
            watched.unsetCursor()
        elif kind == QEvent.ToolTip:
            _, hit = self._hit(event.pos())
            if hit:
                QToolTip.showText(event.globalPos(), tr("recommend.copy_system"), watched)
                return True
        elif kind in (QEvent.MouseMove, QEvent.MouseButtonPress,
                      QEvent.MouseButtonRelease, QEvent.MouseButtonDblClick):
            index, hit = self._hit(event.position().toPoint())
            if kind == QEvent.MouseMove:
                if hit:
                    watched.setCursor(Qt.PointingHandCursor)
                else:
                    watched.unsetCursor()
            elif event.button() == Qt.LeftButton:
                if kind in (QEvent.MouseButtonPress, QEvent.MouseButtonDblClick):
                    self._pressed = QPersistentModelIndex(index) if hit else QPersistentModelIndex()
                    if hit:
                        return True
                elif self._pressed.isValid():
                    pressed = self._pressed
                    self._pressed = QPersistentModelIndex()
                    if hit and index == pressed:
                        self.copyRequested.emit(index.row(), index.column())
                    return True
                elif hit:
                    return True
        return super().eventFilter(watched, event)
