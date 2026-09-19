"""Compact live snapshot card, using the application's theme and Cr formatter."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                               QTableWidget, QTableWidgetItem, QHeaderView,
                               QPushButton, QMessageBox, QSizePolicy)
from cmdrhelper.i18n import tr


class CombatBondView(QFrame):
    def __init__(self, manager, format_reward, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.manager = manager
        self.format_reward = format_reward
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        header = QHBoxLayout()
        self.title = QLabel(objectName="sectionTitle")
        self.total = QLabel(objectName="cardValue")
        header.addWidget(self.title)
        header.addStretch()
        header.addWidget(self.total)
        self.reset_button = QPushButton()
        self.reset_button.clicked.connect(self.confirm_reset)
        header.addWidget(self.reset_button)
        layout.addLayout(header)
        self.empty = QLabel(objectName="muted")
        layout.addWidget(self.empty)
        self.table = QTableWidget(0, 2)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().hide()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.horizontalHeader().geometriesChanged.connect(self._resize_table)
        self.table.verticalHeader().sectionResized.connect(self._resize_table)
        layout.addWidget(self.table)
        self.notice = QLabel(objectName="muted")
        self.notice.setWordWrap(True)
        layout.addWidget(self.notice)
        manager.changed.connect(self.refresh)
        self.refresh()

    def _resize_table(self, *_):
        height = (self.table.horizontalHeader().sizeHint().height()
                  + sum(self.table.rowHeight(row) for row in range(min(self.table.rowCount(), 5)))
                  + 2 * self.table.frameWidth())
        if self.table.height() != height:
            self.table.setFixedHeight(height)

    def reset_dialog(self):
        dialog = QMessageBox(QMessageBox.Question, tr("combat_bonds.reset_title"),
                             tr("combat_bonds.reset_text"), parent=self)
        cancel = dialog.addButton(tr("planet_nav.cancel"), QMessageBox.RejectRole)
        confirm = dialog.addButton(tr("chronicle.reset"), QMessageBox.DestructiveRole)
        dialog.setDefaultButton(cancel)
        dialog.setEscapeButton(cancel)
        return dialog, confirm

    def confirm_reset(self):
        fid = self.manager.fid
        dialog, confirm = self.reset_dialog()
        dialog.exec()
        if dialog.clickedButton() is confirm:
            if not self.manager.manual_reset(fid):
                QMessageBox.warning(self, tr("combat_bonds.reset_title"), tr("combat_bonds.reset_failed"))
        dialog.deleteLater()

    def refresh(self):
        data = self.manager.snapshot()
        self.title.setText(tr("combat_bonds.title"))
        self.reset_button.setText(tr("chronicle.reset") + "…")
        self.reset_button.setEnabled(bool(self.manager.fid))
        label = tr("combat_bonds.observed") if data["uncertain"] else tr("mining.total")
        self.total.setText(f'{label}: {self.format_reward(data["total"])}')
        self.setToolTip(tr("combat_bonds.hint"))
        self.empty.setText(tr("combat_bonds.empty"))
        self.table.setHorizontalHeaderLabels([tr("bounties.faction"), tr("bounties.amount")])
        rows = sorted(data["factions"].items(), key=lambda item: (-item[1], item[0].casefold()))
        self.table.setRowCount(len(rows))
        for row, (faction, amount) in enumerate(rows):
            self.table.setItem(row, 0, QTableWidgetItem(faction or tr("bounties.unknown")))
            item = QTableWidgetItem(self.format_reward(amount))
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 1, item)
        self.table.setVisible(bool(rows))
        self._resize_table()
        self.empty.setVisible(not rows and not data["uncertain"] and not self.manager.storage_error and not data["from_now"])
        notice = tr("combat_bonds.hint")
        if data["from_now"]:
            notice += "\n" + tr("bounties.from_now")
        if data["uncertain"]:
            notice += "\n" + tr("combat_bonds.uncertain")
        if data["redemption_pending"]:
            notice += "\n" + tr("combat_bonds.redemption_pending")
        if self.manager.storage_error:
            notice += "\n" + tr("combat_bonds.storage_error")
        self.notice.setText(notice)
        self.setToolTip(notice)
