"""The existing Yes/No update message box, with optional release highlights."""
from html import escape

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialogButtonBox, QMessageBox, QTextBrowser

from cmdrhelper.i18n import tr
from cmdrhelper.release_summaries import release_summary


class UpdateConfirmationBox(QMessageBox):
    def __init__(self, parent, title, text, version, release_notes=""):
        super().__init__(
            QMessageBox.Question, title, text,
            QMessageBox.Yes | QMessageBox.No, parent,
        )
        self.setTextFormat(Qt.PlainText)
        self.setDefaultButton(QMessageBox.Yes)
        self.setEscapeButton(QMessageBox.No)
        highlights = release_summary(version, release_notes)
        if not highlights:
            return

        self.changes = QTextBrowser(self)
        self.changes.setObjectName("updateChanges")
        self.changes.setAccessibleName(tr("settings.update_changes"))
        self.changes.setOpenLinks(False)
        self.changes.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        screen = self.screen().availableGeometry()
        self.changes.setMinimumWidth(min(460, max(240, screen.width() - 120)))
        self.changes.setFixedHeight(min(200, max(100, screen.height() // 3)))
        heading = tr("settings.update_new_in_version", version=version)
        self.changes.setHtml(
            f"<b>{escape(heading)}</b><ul>"
            + "".join(f"<li>{escape(item)}</li>" for item in highlights)
            + "</ul>"
        )
        # Preserve QMessageBox's native icon, text, buttons and return values.
        # Only insert the bounded notes area immediately before its button row.
        layout = self.layout()
        buttons = self.findChild(QDialogButtonBox)
        row, column, row_span, column_span = layout.getItemPosition(layout.indexOf(buttons))
        layout.removeWidget(buttons)
        layout.addWidget(self.changes, row, 0, 1, layout.columnCount())
        layout.addWidget(buttons, row + 1, column, row_span, column_span)
