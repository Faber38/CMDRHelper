"""Highlight only the first displayed line, retaining Qt's native item drawing."""
import math

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QTextLayout, QTextOption
from PySide6.QtWidgets import QStyledItemDelegate, QStyle, QStyleOptionViewItem


class FavoriteTitleDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        style = opt.widget.style()
        text_rect = style.subElementRect(QStyle.SE_ItemViewItemText, opt, opt.widget)
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
        painter.setClipRect(opt.rect, Qt.IntersectClip)
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
