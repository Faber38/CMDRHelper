"""Modal migration gate, before AppState or any database writers exist."""
from __future__ import annotations

import logging
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QScrollArea, QWidget

from cmdrhelper.i18n import tr
from cmdrhelper.parent_migration import inventory, migrate, MigrationError
from cmdrhelper.ui.startup_progress import ShipLane

logger = logging.getLogger(__name__)


class MigrationWorker(QThread):
    phase = Signal(int)
    completed = Signal(object)

    def __init__(self, path, folder, snapshot, parent=None):
        super().__init__(parent)
        self.path, self.folder, self.snapshot = path, folder, snapshot

    def run(self):
        try:
            result = migrate(self.path, self.folder, progress=self.phase.emit,
                             expected_inventory=self.snapshot)
        except Exception as exc:
            logger.exception('Parent hierarchy migration failed')
            result = exc
        self.completed.emit(result)


class ParentMigrationDialog(QDialog):
    def __init__(self, path, folder, light=False, parent=None):
        super().__init__(parent)
        self.path, self.folder = path, folder
        self.worker = None
        self.succeeded = False
        self.setModal(True)
        self.setWindowTitle(tr('migration.title'))
        self.resize(720, 760)
        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        panel = QWidget()
        content = QVBoxLayout(panel)
        scroll.setWidget(panel)
        layout.addWidget(scroll)

        def label(text):
            item = QLabel(text)
            item.setTextFormat(Qt.PlainText)
            item.setWordWrap(True)
            item.setTextInteractionFlags(Qt.TextSelectableByMouse)
            content.addWidget(item)
            return item

        label(tr('migration.intro'))
        assurance = label(tr('migration.readonly'))
        font = assurance.font()
        font.setBold(True)
        assurance.setFont(font)
        label(tr('migration.explanation'))
        label(tr('migration.prerequisites'))
        label(tr('migration.history'))
        try:
            self.snapshot = inventory(folder)
            names = list(self.snapshot)
            label(tr('migration.inventory', path=str(folder or '—'), count=len(names),
                     oldest=names[0].rsplit('/', 1)[-1] if names else '—',
                     newest=names[-1].rsplit('/', 1)[-1] if names else '—'))
        except OSError:
            self.snapshot = None
            label(tr('migration.failed'))
        label(tr('migration.safety'))
        self.instructions = [content.itemAt(i).widget() for i in range(5)]
        self.ships = ShipLane(light=light)
        content.addWidget(self.ships)
        self.steps = label('')
        self.outcome = label('')
        content.addStretch()
        persistent_note = QLabel(tr('migration.readonly'))
        persistent_note.setWordWrap(True)
        layout.addWidget(persistent_note)
        row = QHBoxLayout()
        self.start_button = QPushButton(tr('migration.start'))
        self.cancel_button = QPushButton(tr('migration.cancel'))
        row.addWidget(self.start_button)
        row.addWidget(self.cancel_button)
        layout.addLayout(row)
        self.start_button.clicked.connect(self.start)
        self.cancel_button.clicked.connect(self.reject)

    def start(self):
        if self.succeeded:
            self.accept()
            return
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        for item in self.instructions:
            item.hide()
        self.ships.start()
        self.outcome.clear()
        self.worker = MigrationWorker(self.path, self.folder, self.snapshot, self)
        self.worker.phase.connect(self.set_phase)
        self.worker.completed.connect(self.finished_migration)
        self.worker.start()

    def set_phase(self, phase):
        self.steps.setText('\n'.join(('✓ ' if i < phase else '… ' if i == phase else '') +
                                    tr(f'migration.step{i}') for i in range(5)))

    def finished_migration(self, result):
        self.worker.wait()
        self.ships.stop()
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        if isinstance(result, Exception):
            key = result.key if isinstance(result, MigrationError) else 'failed'
            if key not in ('active', 'missing', 'backup_error'):
                key = 'failed'
            message = tr('migration.failed')
            if key != 'failed':
                message += '\n' + tr('migration.' + key)
            if getattr(result, 'restored', False):
                message += '\n' + tr('migration.restored')
            self.outcome.setStyleSheet('color: #d64b4b;')
            self.outcome.setText(message)
            # Reopen the dialog for a fresh inventory and another explicit start.
            self.start_button.setEnabled(False)
            return
        self.succeeded = True
        self.outcome.setStyleSheet('color: #369b54;')
        self.outcome.setText(tr('migration.success') + '\n' + tr('migration.result', **result) +
                             '\n' + tr('migration.retained') + '\n' + result['backup'])
        self.start_button.setText(tr('migration.launch'))
        self.cancel_button.hide()

    def reject(self):
        if self.worker is not None and self.worker.isRunning():
            return
        super().reject()

    def closeEvent(self, event):
        if self.worker is not None and self.worker.isRunning():
            event.ignore()
        else:
            super().closeEvent(event)
