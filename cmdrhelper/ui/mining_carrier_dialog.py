"""Explicit manual confirmation, correction and reset of one carrier commodity."""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from cmdrhelper.i18n import tr


class CarrierStockDialog(QDialog):
    def __init__(self, name, count, editable, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("mining.carrier_edit"))
        self.count = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(name))
        self.help_text = QLabel(tr("mining.carrier_dialog_help"), objectName="muted")
        self.unknown_note = QLabel(tr("mining.carrier_baseline_unknown"), objectName="muted")
        for label in (self.help_text, self.unknown_note):
            label.setWordWrap(True)
            label.setMaximumWidth(420)
            layout.addWidget(label)
        layout.addWidget(QLabel(tr("mining.carrier_amount")))
        self.input = QLineEdit("" if count is None else str(count))
        self.input.setAccessibleName(tr("mining.carrier_amount"))
        self.input.setPlaceholderText(tr("mining.stock_unknown"))
        self.input.setEnabled(editable)
        layout.addWidget(self.input)
        self.error = QLabel("" if editable else tr("mining.carrier_unavailable"))
        self.error.setWordWrap(True)
        layout.addWidget(self.error)
        buttons = QHBoxLayout()
        self.reset_button = QPushButton(tr("mining.carrier_reset"))
        self.reset_button.setToolTip(tr("mining.stock_unknown"))
        self.reset_button.setEnabled(editable)
        self.reset_button.clicked.connect(self._reset)
        buttons.addWidget(self.reset_button)
        cancel = QPushButton(tr("planet_nav.cancel"))
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        self.apply_button = QPushButton(tr("mining.carrier_apply"))
        self.apply_button.setEnabled(editable)
        self.apply_button.clicked.connect(self._apply)
        self.apply_button.setDefault(True)
        buttons.addWidget(self.apply_button)
        layout.addLayout(buttons)

    def _apply(self):
        text = self.input.text().strip()
        if not text.isascii() or not text.isdigit() or len(text) > 10 or int(text) > 2_147_483_647:
            self.error.setText(tr("mining.carrier_invalid"))
            return
        self.count = int(text)
        self.accept()

    def _reset(self):
        self.count = None
        self.accept()
