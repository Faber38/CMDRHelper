"""Read-only, full-resolution image viewing for favorite details."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QImageReader, QPainter, QPalette, QPixmap
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QWidget


class FavoriteImageCanvas(QWidget):
    MAX_ZOOM = 32.0  # Relative to the fitted overview.

    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.pixmap = pixmap
        self.zoom = 1.0
        self.offset = QPointF()
        self._drag = None
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QPalette.Base)

    def image_rect(self):
        scale = min(self.width() / self.pixmap.width(),
                    self.height() / self.pixmap.height()) * self.zoom
        size = self.pixmap.size().toSizeF() * scale
        return QRectF(QPointF((self.width() - size.width()) / 2,
                             (self.height() - size.height()) / 2) + self.offset, size)

    def reset_view(self):
        self.zoom = 1.0
        self.offset = QPointF()
        self._drag = None
        self.unsetCursor()
        self.update()

    def _constrain(self):
        rect = self.image_rect()
        x = max(0, (rect.width() - self.width()) / 2)
        y = max(0, (rect.height() - self.height()) / 2)
        self.offset = QPointF(max(-x, min(x, self.offset.x())),
                              max(-y, min(y, self.offset.y())))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.drawPixmap(self.image_rect(), self.pixmap, QRectF(self.pixmap.rect()))

    def wheelEvent(self, event):
        delta = event.angleDelta().y() or event.pixelDelta().y()
        if not delta:
            event.ignore()
            return
        old_zoom = self.zoom
        self.zoom = max(1.0, min(self.MAX_ZOOM,
                                self.zoom * 2 ** (max(-1200, min(1200, delta)) / 600)))
        center = QPointF(self.width() / 2, self.height() / 2)
        anchor = event.position() - center
        self.offset = anchor - (anchor - self.offset) * (self.zoom / old_zoom)
        self._constrain()
        self.setCursor(Qt.OpenHandCursor if self.zoom > 1 else Qt.ArrowCursor)
        self.update()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.zoom > 1:
            self._drag = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag is not None:
            self.offset += event.position() - self._drag
            self._drag = event.position()
            self._constrain()
            self.update()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._drag is not None:
            self._drag = None
            self.setCursor(Qt.OpenHandCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.reset_view()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def resizeEvent(self, event):
        self._constrain()
        super().resizeEvent(event)


class FavoriteImageDialog(QDialog):
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setWindowTitle(parent.window().windowTitle() if parent else '')
        layout = QVBoxLayout(self)
        self.canvas = FavoriteImageCanvas(pixmap, self)
        layout.addWidget(self.canvas)
        available = self.screen().availableGeometry()
        self.resize(int(available.width() * 0.9), int(available.height() * 0.9))


class FavoriteImageLabel(QLabel):
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path
        self.setAlignment(Qt.AlignCenter)

    def setPixmap(self, pixmap):
        super().setPixmap(pixmap)
        self.setProperty("cursorClickable", bool(self.path and not pixmap.isNull()))
        self.setCursor(Qt.PointingHandCursor if self.path and not pixmap.isNull() else Qt.ArrowCursor)

    def clear(self):
        super().clear()
        self.setProperty("cursorClickable", False)
        self.setCursor(Qt.ArrowCursor)

    def mouseDoubleClickEvent(self, event):
        if event.button() != Qt.LeftButton or not self.path or self.pixmap().isNull():
            super().mouseDoubleClickEvent(event)
            return
        reader = QImageReader(str(self.path))
        reader.setAutoTransform(True)
        pixmap = QPixmap.fromImage(reader.read())
        if not pixmap.isNull():
            dialog = FavoriteImageDialog(pixmap, self)
            try:
                dialog.exec()
            finally:
                dialog.deleteLater()
        event.accept()
