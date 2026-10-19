"""Highlight only the first displayed line, retaining Qt's native item drawing."""
import math

from PySide6.QtCore import QEvent, QPersistentModelIndex, QRect, Qt, QTimer
from PySide6.QtGui import QColor, QTextLayout, QTextOption
from PySide6.QtWidgets import QApplication, QListWidget, QStyledItemDelegate, QStyle, QStyleOptionViewItem, QToolTip

from cmdrhelper.i18n import tr


SYSTEM_NAME_ROLE = Qt.UserRole + 1
COPY_CONFIRMED_ROLE = Qt.UserRole + 2


def copy_rect(rect):
    return QRect(rect.right() - 27, rect.center().y() - 12, 24, 24)


class FavoritesListWidget(QListWidget):
    """Handle the copy area before Qt changes the current/selected item."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._copy_timers = {}
        self.model().modelReset.connect(self._clear_copy_confirmations)

    def _clear_copy_confirmations(self):
        for timer in self._copy_timers.values():
            timer.stop()
            timer.deleteLater()
        self._copy_timers.clear()

    def _confirm_copy(self, index):
        key = QPersistentModelIndex(index)
        timer = self._copy_timers.get(key)
        if timer is None:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.setTimerType(Qt.PreciseTimer)
            def reset():
                self._copy_timers.pop(key, None)
                if key.isValid():
                    self.model().setData(key, False, COPY_CONFIRMED_ROLE)
                timer.deleteLater()
            timer.timeout.connect(reset)
            self._copy_timers[key] = timer
        self.model().setData(index, True, COPY_CONFIRMED_ROLE)
        timer.start(2000)

    def _copy_index(self, position):
        index = self.indexAt(position)
        return index if index.isValid() and copy_rect(self.visualRect(index)).contains(position) else None

    def mousePressEvent(self, event):
        index = self._copy_index(event.position().toPoint())
        self._copy_pressed = None
        if event.button() == Qt.LeftButton and index is not None:
            self._copy_pressed = QPersistentModelIndex(index)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        pressed = getattr(self, '_copy_pressed', None)
        self._copy_pressed = None
        index = self._copy_index(event.position().toPoint())
        if event.button() == Qt.LeftButton and (pressed is not None or index is not None):
            if pressed is not None and pressed.isValid() and index == pressed:
                name = index.data(SYSTEM_NAME_ROLE)
                if isinstance(name, str) and name.strip():
                    QApplication.clipboard().setText(name)
                    self._confirm_copy(index)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and self._copy_index(event.position().toPoint()) is not None:
            self.mousePressEvent(event)
            return
        super().mouseDoubleClickEvent(event)

    def viewportEvent(self, event):
        if event.type() == QEvent.ToolTip and self._copy_index(event.pos()) is not None:
            QToolTip.showText(event.globalPos(), tr('favorites.copy_system'), self)
            return True
        return super().viewportEvent(event)


class FavoriteTitleDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        background = QStyleOptionViewItem(opt)
        background.text = ''
        painter.save()
        painter.setClipRect(QRect(opt.rect.right() - 29, opt.rect.top(), 30, opt.rect.height()), Qt.IntersectClip)
        opt.widget.style().drawControl(QStyle.CE_ItemViewItem, background, painter, opt.widget)
        painter.restore()
        button = copy_rect(opt.rect)
        painter.save()
        role = (opt.palette.ColorRole.HighlightedText if opt.state & QStyle.State_Selected
                else opt.palette.ColorRole.Text)
        painter.setPen(opt.palette.color(role) if index.data(SYSTEM_NAME_ROLE)
                       else opt.palette.color(opt.palette.ColorGroup.Disabled, opt.palette.ColorRole.Text))
        if index.data(COPY_CONFIRMED_ROLE):
            painter.setPen(QColor('#28a745'))
            painter.drawText(button, Qt.AlignCenter, '✓')
        else:
            painter.drawRoundedRect(button.adjusted(5, 4, -7, -8), 1, 1)
            painter.drawRoundedRect(button.adjusted(9, 8, -3, -4), 1, 1)
        painter.restore()
        style = opt.widget.style()
        text_rect = style.subElementRect(QStyle.SE_ItemViewItemText, opt, opt.widget)
        text_rect.adjust(0, 0, -30, 0)
        # Qt lays out explicit newlines as line separators in item text.
        layout = QTextLayout(opt.text.replace('\n', '\u2028'), opt.font)
        text_option = QTextOption()
        text_option.setWrapMode(QTextOption.NoWrap)
        layout.setTextOption(text_option)
        layout.beginLayout()
        height = 0
        first_height = 0
        while True:
            line = layout.createLine()
            if not line.isValid():
                break
            line.setLineWidth(max(1, text_rect.width()))
            line_height = math.ceil(line.height())
            first_height = first_height or line_height
            height += line_height
        layout.endLayout()
        top = text_rect.top()
        if opt.displayAlignment & Qt.AlignVCenter:
            top += (text_rect.height() - height) // 2
        elif opt.displayAlignment & Qt.AlignBottom:
            top += text_rect.height() - height
        title_rect = QRect(text_rect.left(), top, text_rect.width(), first_height)
        title, separator, remaining = opt.text.partition('\u2028')
        # A zero-width character retains the first line's height. Let the style
        # paint everything else, including the original selected text colors.
        opt.text = '\u200b' + separator + remaining
        painter.save()
        painter.setClipRect(opt.rect.adjusted(0, 0, -30, 0), Qt.IntersectClip)
        style.drawControl(QStyle.CE_ItemViewItem, opt, painter, opt.widget)
        painter.setClipRect(title_rect, Qt.IntersectClip)
        margin = style.pixelMetric(QStyle.PM_FocusFrameHMargin, opt, opt.widget) + 1
        title_rect.adjust(margin, 0, -margin, 0)
        painter.setFont(opt.font)
        painter.setPen(QColor('#FFCC33'))
        painter.drawText(title_rect, Qt.AlignLeft | Qt.AlignVCenter,
                         opt.fontMetrics.elidedText(title, opt.textElideMode,
                                                   max(0, title_rect.width())))
        painter.restore()
