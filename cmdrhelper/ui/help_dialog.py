from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from cmdrhelper.help_content import help_topic


class HelpDialog(QDialog):
    """Gemeinsames, kontextbezogenes Hilfefenster."""

    def __init__(self, context: str, parent=None, language: str = "de"):
        super().__init__(parent)
        topic = help_topic(context, language)
        self.context = context
        self.setWindowTitle(topic.dialog_title)
        self.setMinimumSize(480, 320)
        self.setMaximumSize(900, 700)
        self.resize(640, 480)

        layout = QVBoxLayout(self)
        self.scroll_area = QScrollArea(objectName="helpScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        content = QWidget()
        content_layout = QVBoxLayout(content)
        self.help_text = QLabel(topic.text, objectName="helpText")
        self.help_text.setTextFormat(Qt.TextFormat.RichText)
        self.help_text.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.help_text.setWordWrap(True)
        self.help_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_layout.addWidget(self.help_text)
        content_layout.addStretch()
        self.scroll_area.setWidget(content)
        layout.addWidget(self.scroll_area)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.buttons.button(QDialogButtonBox.StandardButton.Close).setText(
            topic.close_label
        )
        self.buttons.rejected.connect(self.close)
        layout.addWidget(self.buttons)
