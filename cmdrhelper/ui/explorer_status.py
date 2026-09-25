"""Explorer presentation of existing exploration and EDSM observations."""
from html import escape

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle

from cmdrhelper.i18n import tr
from cmdrhelper.edsm_system_status import STATUS_KEYS


# Shared Explorer accents, including readable light-theme variants.
STATUS_COLORS_DARK = ("#68c7ff", "#65d067", "#ffb000", "#9ba9b7")
STATUS_COLORS_LIGHT = ("#17679b", "#28752c", "#856000", "#536574")

FOOTFALL_COLOR_ROLE = Qt.UserRole + 20


class FootfallStatusDelegate(QStyledItemDelegate):
    """Two compact lines retain each status accent and the full accessible text."""

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        if index.data(FOOTFALL_COLOR_ROLE):
            opt = QStyleOptionViewItem(option)
            self.initStyleOption(opt, index)
            size.setHeight(max(size.height(), opt.fontMetrics.lineSpacing() * 2 + 8))
        return size

    def paint(self, painter, option, index):
        color = index.data(FOOTFALL_COLOR_ROLE)
        if not color:
            return super().paint(painter, option, index)
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        lines = index.data(Qt.DisplayRole).split("\n", 1)
        opt.text = ""
        style = opt.widget.style()
        style.drawControl(QStyle.CE_ItemViewItem, opt, painter, opt.widget)
        rect = style.subElementRect(QStyle.SE_ItemViewItemText, opt, opt.widget).adjusted(4, 0, -4, 0)
        height = opt.fontMetrics.lineSpacing()
        rect.setTop(rect.top() + max(0, (rect.height() - 2 * height) // 2))
        rect.setHeight(height)
        painter.save()
        painter.setClipRect(option.rect)
        painter.setFont(opt.font)
        for text, foreground in zip(lines, (QColor(color), index.data(Qt.ForegroundRole))):
            painter.setPen(foreground.color() if hasattr(foreground, "color") else foreground)
            painter.drawText(rect, Qt.AlignLeft | Qt.AlignVCenter,
                             opt.fontMetrics.elidedText(text, Qt.ElideRight, max(0, rect.width())))
            rect.translate(0, height)
        painter.restore()


def edsm_status_html(status, *, light=False):
    colors = STATUS_COLORS_LIGHT if light else STATUS_COLORS_DARK
    color = colors[0 if status == "known" else 2 if status == "unknown" else 3]
    # No completed request (disabled, pending or a new system) is not a failure.
    text = tr(STATUS_KEYS[status]) if status in STATUS_KEYS else "EDSM: —"
    return f'<span style="color: {color}">{escape(text)}</span>'



def mapping_status_presentation(status, *, light=False):
    """Return text, tooltip, foreground and ascending rank; retain unknowns."""
    own, previous = status["self_mapped"], status["was_mapped_at_scan"]
    if own is True:
        kind, rank = "self", 0
    elif previous is True:
        kind, rank = "already", 1
    elif own is False and previous is False:
        kind, rank = "not", 2
    else:
        kind, rank = "unknown", 3
    # Dark palette follows existing body/status accents; darker light variants
    # keep the same meaning with readable contrast on light table backgrounds.
    colors = STATUS_COLORS_LIGHT if light else STATUS_COLORS_DARK
    prefix = "explorer.mapping_status_"
    return ("?" if kind == "unknown" else tr(prefix + kind),
            tr(prefix + kind + "_tip"), colors[rank], rank)
