"""Explicit, single-combination global shortcut configuration."""
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QDialog, QKeySequenceEdit, QDialogButtonBox, QLineEdit)
from PySide6.QtCore import Qt
from cmdrhelper.i18n import tr


class QuickFavoriteSettings(QWidget):
    def __init__(self, hotkey, parent=None):
        super().__init__(parent)
        self.hotkey = hotkey
        root = QVBoxLayout(self)
        root.addWidget(QLabel(tr('quick_favorite.title'), objectName='sectionTitle'))
        self.label = QLabel()
        root.addWidget(self.label)
        row = QHBoxLayout()
        self.edit = QPushButton()
        self.remove = QPushButton(tr('quick_favorite.remove'))
        self.edit.clicked.connect(self.choose)
        self.remove.clicked.connect(self.clear)
        row.addWidget(self.edit)
        row.addWidget(self.remove)
        row.addStretch()
        root.addLayout(row)
        self.error = QLabel()
        self.error.setWordWrap(True)
        self.error.setTextFormat(Qt.PlainText)
        root.addWidget(self.error)
        hotkey.failed.connect(self.failed)
        hotkey.changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        active = self.hotkey.active
        display = QKeySequence(active).toString(QKeySequence.NativeText) if active else tr('quick_favorite.unassigned')
        self.label.setText(tr('quick_favorite.hotkey') + ': ' + display)
        self.edit.setText(tr('quick_favorite.change') if active else tr('quick_favorite.set'))
        self.remove.setEnabled(bool(active or self.hotkey.settings.value('quick_favorite/hotkey', '')))
        self.error.setText(tr('quick_favorite.registration_failed') if self.hotkey.error else '')

    def failed(self, _error):
        self.refresh()

    def clear(self):
        self.hotkey.set_hotkey('')
        self.refresh()

    def choose(self):
        dialog = QDialog(self)
        dialog.setWindowTitle(tr('quick_favorite.title'))
        root = QVBoxLayout(dialog)
        edit = QKeySequenceEdit(QKeySequence(self.hotkey.active))
        edit.setMaximumSequenceLength(1)
        edit.findChild(QLineEdit).setPlaceholderText(tr('quick_favorite.set'))
        edit.setFinishingKeyCombinations([])  # Tab/Backtab are assignable too.
        root.addWidget(edit)
        error = QLabel()
        error.setWordWrap(True)
        root.addWidget(error)
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Save).setText(tr('favorites.save'))
        buttons.button(QDialogButtonBox.Cancel).setText(tr('planet_nav.cancel'))
        root.addWidget(buttons)
        buttons.rejected.connect(dialog.reject)

        def accept():
            sequence = edit.keySequence().toString(QKeySequence.PortableText)
            if not sequence or not self.hotkey.set_hotkey(sequence):
                error.setText(tr('quick_favorite.registration_failed'))
                return
            self.refresh()
            dialog.accept()

        buttons.accepted.connect(accept)
        dialog.exec()
