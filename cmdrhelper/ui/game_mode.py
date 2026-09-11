"""Compact overview row; only the mode value receives a status color."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel

from cmdrhelper.i18n import tr


class GameModeRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.caption = QLabel(tr("overview.game_mode") + ":")
        self.value = QLabel()
        self.value.setTextFormat(Qt.PlainText)
        self.value.setWordWrap(True)
        layout.addWidget(self.caption, 0, Qt.AlignTop)
        layout.addWidget(self.value, 1)
        self.set_mode("", "")

    def set_mode(self, mode, group_name=""):
        key = {"Open": "open", "Solo": "solo", "Group": "group"}.get(mode)
        text = tr("game_mode." + key) if key else "–"
        if mode == "Group" and group_name:
            text += " · " + group_name
        self.value.setText(text)
        self.value.setProperty("gameMode", mode if key else "")
        self.value.style().unpolish(self.value)
        self.value.style().polish(self.value)
        self.value.update()
