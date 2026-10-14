"""Independent checkbox selection for the existing favorites package export."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QRadioButton, QVBoxLayout, QWidget,
)

from cmdrhelper.i18n import tr


class FavoritesExportDialog(QDialog):
    def __init__(self, records, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('favorites.transfer.export'))
        self.resize(640, 480)
        layout = QVBoxLayout(self)
        self.all_favorites = QRadioButton(tr('favorites.export_selection.all'))
        self.selected_favorites = QRadioButton(tr('favorites.export_selection.selected'))
        layout.addWidget(self.all_favorites)
        layout.addWidget(self.selected_favorites)
        self.selection = QWidget()
        selection_layout = QVBoxLayout(self.selection)
        selection_layout.setContentsMargins(0, 0, 0, 0)
        self.list = QListWidget()
        self.list.setSelectionMode(QListWidget.NoSelection)
        for record in records:
            location = record['system_name']
            if record['body_name']:
                location += ' / ' + record['body_name']
            item = QListWidgetItem(record['name'] + '\n' + location, self.list)
            item.setData(Qt.UserRole, record['id'])
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setToolTip(item.text())
        selection_layout.addWidget(self.list)
        actions = QHBoxLayout()
        self.select_all = QPushButton(tr('favorites.export_selection.select_all'))
        self.select_none = QPushButton(tr('favorites.export_selection.select_none'))
        self.select_all.clicked.connect(lambda: self._check_all(Qt.Checked))
        self.select_none.clicked.connect(lambda: self._check_all(Qt.Unchecked))
        actions.addWidget(self.select_all)
        actions.addWidget(self.select_none)
        selection_layout.addLayout(actions)
        layout.addWidget(self.selection)
        self.count = QLabel()
        layout.addWidget(self.count)
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.button(QDialogButtonBox.Ok).setText(tr('favorites.transfer.export'))
        self.buttons.button(QDialogButtonBox.Cancel).setText(tr('planet_nav.cancel'))
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.list.itemChanged.connect(self._update_selection)
        self.all_favorites.toggled.connect(self._update_selection)
        self.all_favorites.setChecked(True)

    def selected_ids(self):
        if self.all_favorites.isChecked():
            return None
        return {self.list.item(i).data(Qt.UserRole) for i in range(self.list.count())
                if self.list.item(i).checkState() == Qt.Checked}

    def _check_all(self, state):
        self.list.blockSignals(True)
        for i in range(self.list.count()):
            self.list.item(i).setCheckState(state)
        self.list.blockSignals(False)
        self._update_selection()

    def _update_selection(self):
        selected = self.selected_ids()
        self.selection.setVisible(selected is not None)
        count = self.list.count() if selected is None else len(selected)
        self.count.setText(tr('favorites.export_selection.count', count=count))
        self.buttons.button(QDialogButtonBox.Ok).setEnabled(selected is None or bool(selected))

    def accept(self):
        if self.selected_ids() != set():
            super().accept()
