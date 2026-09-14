"""Small settings panel using the desktop's native file/URL integration."""
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox

from cmdrhelper.i18n import tr
from cmdrhelper.logging_config import log_folder
from cmdrhelper.diagnostics import create_package, suggested_name


class DiagnosticsPanel(QWidget):
    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        layout = QVBoxLayout(self)
        title = QLabel(tr('diagnostics.title'))
        title.setObjectName('sectionTitle')
        layout.addWidget(title)
        label = QLabel(tr('diagnostics.info'))
        label.setWordWrap(True)
        layout.addWidget(label)
        row = QHBoxLayout()
        self.open_button = QPushButton(tr('diagnostics.open'))
        self.create_button = QPushButton(tr('diagnostics.create'))
        self.open_button.clicked.connect(self.open_log)
        self.create_button.clicked.connect(self.create)
        row.addWidget(self.open_button)
        row.addWidget(self.create_button)
        row.addStretch()
        layout.addLayout(row)

    def open_log(self):
        try:
            path = log_folder() / 'cmdrhelper.log'
            if not path.is_file() or not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve()))):
                QMessageBox.information(self, tr('diagnostics.title'), tr('diagnostics.unavailable'))
        except OSError:
            QMessageBox.information(self, tr('diagnostics.title'), tr('diagnostics.unavailable'))

    def create(self):
        target, _ = QFileDialog.getSaveFileName(self, tr('diagnostics.create'), suggested_name(), 'ZIP (*.zip)')
        if not target:
            return
        # Do not append a suffix after the dialog's overwrite check.
        if Path(target).suffix.lower() != '.zip':
            QMessageBox.warning(self, tr('diagnostics.title'), tr('diagnostics.failed'))
            return
        self.create_button.setEnabled(False)
        try:
            create_package(target, database=self.state.database.path,
                           journals=self.state.journal_folder, overwrite=True)
        except Exception:
            QMessageBox.warning(self, tr('diagnostics.title'), tr('diagnostics.failed'))
        else:
            QMessageBox.information(self, tr('diagnostics.title'), tr('diagnostics.saved', path=target))
        finally:
            self.create_button.setEnabled(True)
