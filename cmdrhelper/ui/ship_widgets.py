"""Compact, theme-aware presentation widgets for the commander fleet."""
from PySide6.QtCore import Qt, QSize, QRect
from PySide6.QtGui import QPainter, QPalette, QImageReader, QColor
from PySide6.QtWidgets import QLabel, QSizePolicy, QToolButton, QStyle, QStyleOptionToolButton, QDialog, QWidget, QVBoxLayout

from cmdrhelper.ui.ship_assets import ship_preview


class ElidedShipLabel(QLabel):
    def __init__(self, text="–", parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        self.setText(text)

    def setText(self, text):
        super().setText(text)
        self.setToolTip(text)

    def minimumSizeHint(self):
        return QSize(0, super().minimumSizeHint().height())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(self.palette().color(QPalette.WindowText))
        painter.drawText(self.contentsRect(), Qt.AlignVCenter | Qt.AlignLeft,
                         self.fontMetrics().elidedText(self.text(), Qt.ElideRight,
                                                       self.contentsRect().width()))


class ShipImage(QLabel):
    def __init__(self, width, height, preview_resolver=ship_preview):
        super().__init__()
        self._preview_resolver = preview_resolver
        self.setFixedSize(width, height)
        self.setAlignment(Qt.AlignCenter)
        self.set_ship(None)

    def set_ship(self, ship_type, personal_path=None, ship_name=""):
        self.clear()
        self._ship_name = ship_name
        pixmap, self._source_path = self._preview_resolver(
            ship_type, self.width(), self.height(), self.devicePixelRatioF(), personal_path,
        )
        self.setProperty("hasShipImage", pixmap is not None)
        if pixmap is not None:
            self.setPixmap(pixmap)
        self.update()

    def mousePressEvent(self, event):
        # Do not propagate image clicks to the expandable fleet header.
        if event.button() == Qt.LeftButton:
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() != Qt.LeftButton:
            super().mouseDoubleClickEvent(event)
            return
        event.accept()
        if self._source_path is None:
            return
        reader = QImageReader(str(self._source_path))
        reader.setAutoTransform(True)
        image = reader.read()  # Full source resolution, never the thumbnail.
        if image.isNull():
            return
        viewer = ShipImageViewer(image, self._ship_name, self.window())
        viewer.show()

    def paintEvent(self, event):
        if self.property("hasShipImage"):
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        color = self.palette().color(QPalette.WindowText)
        color.setAlpha(12)
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)
        color.setAlpha(65)
        painter.setPen(color)
        painter.drawText(self.rect(), Qt.AlignCenter, "◇")


class ShipImageCanvas(QWidget):
    def __init__(self, image, parent=None):
        super().__init__(parent)
        self.image = image
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

    def image_rect(self):
        size = self.image.size().scaled(self.size(), Qt.KeepAspectRatio)
        return QRect((self.width() - size.width()) // 2,
                     (self.height() - size.height()) // 2, size.width(), size.height())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#0b1016"))
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.drawImage(self.image_rect(), self.image)


class ShipImageViewer(QDialog):
    """Non-modal native window; QDialog provides Escape-to-close on both OSes."""
    def __init__(self, image, ship_name, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowFlag(Qt.Window, True)
        self.setWindowFlag(Qt.WindowMinMaxButtonsHint, True)
        self.setWindowTitle(ship_name)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = ShipImageCanvas(image, self)
        layout.addWidget(self.canvas)
        screen = parent.screen()
        available = screen.availableGeometry()
        self.setGeometry(self.initial_geometry(image.size(), available))

    @staticmethod
    def initial_geometry(image_size, available):
        # Leave space for native window decorations and desktop panels.
        limit = QSize(max(1, int(available.width() * .85)),
                      max(1, int(available.height() * .85)))
        size = image_size.expandedTo(QSize(320, 240)).boundedTo(limit)
        return QRect(available.x() + (available.width() - size.width()) // 2,
                     available.y() + (available.height() - size.height()) // 2,
                     size.width(), size.height())


class FleetHeader(QToolButton):
    """One accessible clickable row, with its arrow at the right edge."""
    def __init__(self):
        super().__init__()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumWidth(0)
        self.setCheckable(True)
        self.setArrowType(Qt.RightArrow)

    def sizeHint(self):
        return QSize(240, self.layout().sizeHint().height())

    def minimumSizeHint(self):
        return QSize(0, self.sizeHint().height())

    def paintEvent(self, event):
        option = QStyleOptionToolButton()
        self.initStyleOption(option)
        option.text = ""
        option.arrowType = Qt.NoArrow
        option.features = QStyleOptionToolButton.None_
        painter = QPainter(self)
        self.style().drawComplexControl(QStyle.CC_ToolButton, option, painter, self)
        option.rect = self.rect().adjusted(self.width() - 22, 0, -6, 0)
        self.style().drawPrimitive(QStyle.PE_IndicatorArrowDown if self.isChecked()
                                  else QStyle.PE_IndicatorArrowRight, option, painter, self)
