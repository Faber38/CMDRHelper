"""Paint-only accents for ordinary checkbox/radio indicators.

Install before the application stylesheet. Only the two verified Qt common
styles are wrapped; unknown/native styles retain their original rendering.
"""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QProxyStyle,
                              QRadioButton, QStyle, QStyleFactory)


class SelectionIndicatorStyle(QProxyStyle):
    def __init__(self, base_style):
        super().__init__(base_style)
        self.set_theme("dark")

    def set_theme(self, theme):
        # A primitive's palette can differ from the application's theme palette.
        self._accent = QColor("#1565C0" if theme == "light" else "#FFCC33")

    @staticmethod
    def _eligible(widget):
        if (not isinstance(widget, (QCheckBox, QRadioButton))
                or widget.property("preserveSelectionIndicator") or widget.styleSheet()):
            return False
        parent = widget.parentWidget()
        while parent is not None:
            if isinstance(parent, QAbstractItemView):
                return False
            parent = parent.parentWidget()
        return True

    def polish(self, target):
        if isinstance(target, (QCheckBox, QRadioButton)):
            # Also covers dialogs and commander fields created after startup.
            target.setProperty("accentIndicator", self._eligible(target))
        return super().polish(target)

    def drawPrimitive(self, element, option, painter, widget=None):
        super().drawPrimitive(element, option, painter, widget)
        if element not in (QStyle.PE_IndicatorCheckBox, QStyle.PE_IndicatorRadioButton):
            return
        if (not self._eligible(widget) or not widget.property("accentIndicator")
                or widget.property("carrierConfirmPulse")):
            return
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(self._accent, 1))
        painter.setBrush(Qt.NoBrush)
        rect = QRectF(option.rect).adjusted(.5, .5, -.5, -.5)
        if element == QStyle.PE_IndicatorRadioButton:
            painter.drawEllipse(rect)
        else:
            painter.drawRoundedRect(rect, 2, 2)
        painter.restore()


def install_selection_indicators(app):
    """Preserve unsupported platform styles, rather than replace their glyphs."""
    if getattr(app, "_selection_indicator_style", None) is not None:
        return
    current = app.style()
    supported = {"QFusionStyle": "fusion", "QWindowsStyle": "windows"}
    name = supported.get(current.metaObject().className())
    if name is None:
        return
    # Give the proxy its own base; never transfer the application's shared style.
    base = QStyleFactory.create(name)
    if base is None:
        return
    style = SelectionIndicatorStyle(base)
    app.setStyle(style)
    app._selection_indicator_style = style


def set_selection_indicator_theme(app, theme):
    """Called alongside the existing application stylesheet replacement."""
    style = getattr(app, "_selection_indicator_style", None)
    if style is not None:
        style.set_theme(theme)
