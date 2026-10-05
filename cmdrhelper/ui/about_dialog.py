"""Application information, opened from the existing sidebar version label."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QScrollArea, QVBoxLayout, QWidget

from cmdrhelper.i18n import tr
from cmdrhelper import version


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('CMDRHelper')
        self.setModal(True)
        layout = QVBoxLayout(self)
        heading = QLabel('CMDRHelper')
        font = heading.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 2)
        heading.setFont(font)
        layout.addWidget(heading)
        self.version_label = QLabel(tr('about.version', version=version.__version__))
        layout.addWidget(self.version_label)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 8, 0, 0)
        self.description = QLabel('\n\n'.join(tr('about.' + key) for key in (
            'intro', 'purpose', 'origin', 'development', 'support', 'independent', 'trademark')))
        self.description.setTextFormat(Qt.PlainText)
        self.description.setWordWrap(True)
        self.description.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.description.setAlignment(Qt.AlignTop)
        content_layout.addWidget(self.description)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Close)
        self.buttons.button(QDialogButtonBox.Close).setText(tr('common.close'))
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        screen = self.screen().availableGeometry()
        self.resize(min(490, screen.width() - 40), min(530, screen.height() - 40))

    def showEvent(self, event):
        super().showEvent(event)
        parent = self.parentWidget()
        bounds = self.screen().availableGeometry()
        center = parent.frameGeometry().center() if parent else bounds.center()
        frame = self.frameGeometry()
        frame.moveCenter(center)
        self.move(max(bounds.left(), min(frame.left(), bounds.right() - frame.width() + 1)),
                  max(bounds.top(), min(frame.top(), bounds.bottom() - frame.height() + 1)))


class VersionLabel(QLabel):
    """Keep the existing muted label style, with mouse and keyboard activation."""
    def __init__(self, parent=None):
        super().__init__(f'CMDRHelper {version.__version__}', parent, objectName='appSubTitle')
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)

    def open_info(self):
        dialog = AboutDialog(self.window())
        try:
            dialog.exec()
        finally:
            dialog.deleteLater()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            self.open_info()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.open_info()
            event.accept()
        else:
            super().keyPressEvent(event)
