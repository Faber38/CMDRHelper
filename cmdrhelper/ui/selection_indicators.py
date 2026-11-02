"""Paint-only accents for ordinary checkbox/radio indicators.

Install before the application stylesheet. Wrap Qt common and Windows styles;
unknown styles retain their original rendering.
"""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPalette, QPen
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QProxyStyle,
                              QRadioButton, QStyle, QStyleFactory, QStyleOptionButton)


class SelectionIndicatorStyle(QProxyStyle):
    def __init__(self, base_style):
        windows11 = base_style.metaObject().className() == "QWindows11Style"
        super().__init__(base_style)
        self._windows11 = windows11
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
        accented = (element in (QStyle.PE_IndicatorCheckBox, QStyle.PE_IndicatorRadioButton)
                    and self._eligible(widget) and widget.property("accentIndicator")
                    and not widget.property("carrierConfirmPulse"))
        if (accented and self._windows11 and element == QStyle.PE_IndicatorRadioButton
                and option.state & QStyle.State_On):
            # Windows11 paints the native inner dot with Window, which can be
            # identical to the QSS Button/background. Change only this primitive's
            # palette: retain native radii, animation, hover and disabled colors.
            native_option = QStyleOptionButton(option)
            for group in (QPalette.Active, QPalette.Inactive, QPalette.Disabled):
                native_option.palette.setBrush(
                    group, QPalette.Window, option.palette.brush(group, QPalette.WindowText))
            super().drawPrimitive(element, native_option, painter, widget)
        else:
            super().drawPrimitive(element, option, painter, widget)
        if not accented:
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
    """Keep an owned instance of the active Qt style, including native Windows."""
    if getattr(app, "_selection_indicator_style", None) is not None:
        return
    current = app.style()
    supported = {"QFusionStyle": "fusion", "QWindowsStyle": "windows",
                 "QWindowsVistaStyle": "windowsvista", "QWindows11Style": "windows11"}
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
