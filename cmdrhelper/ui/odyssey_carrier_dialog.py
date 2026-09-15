"""Manual confirmation and explanations of private carrier projections."""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton

from cmdrhelper.i18n import tr
from cmdrhelper.odyssey_carrier import valid_amount


def carrier_tooltip(record):
    record = record or {}
    current, last = record.get("current_amount"), record.get("last_confirmed_amount")
    key = "odyssey.carrier_tracked" if record.get("status") == "tracked" else "odyssey.carrier_manual"
    text = (tr(key, amount=current, time=record.get("confirmed_at", ""))
            if current is not None else tr("odyssey.carrier_unknown"))
    if current is None and last is not None:
        text += "\n" + tr("odyssey.carrier_last", amount=last, time=record.get("confirmed_at", ""))
    reason = record.get("uncertainty_reason")
    if reason in ("negative", "capacity", "unclassified"):
        text += "\n" + tr("odyssey.carrier_reason_" + reason)
    return text + "\n" + tr("odyssey.carrier_hint")


class OdysseyCarrierDialog(QDialog):
    def __init__(self, name, record, editable, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("odyssey.carrier_edit"))
        self.amount = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(name))
        self.status = QLabel(carrier_tooltip(record))
        self.status.setWordWrap(True)
        self.status.setMaximumWidth(440)
        layout.addWidget(self.status)
        layout.addWidget(QLabel(tr("odyssey.carrier_amount")))
        current = (record or {}).get("current_amount")
        self.input = QLineEdit("" if current is None else str(current))
        self.input.setAccessibleName(tr("odyssey.carrier_amount"))
        self.input.setPlaceholderText("—")
        self.input.setEnabled(editable)
        layout.addWidget(self.input)
        self.error = QLabel("" if editable else tr("odyssey.carrier_unavailable"))
        self.error.setWordWrap(True)
        layout.addWidget(self.error)
        buttons = QHBoxLayout()
        self.reset_button = QPushButton(tr("odyssey.carrier_reset"))
        self.reset_button.setEnabled(editable)
        self.reset_button.clicked.connect(self._reset)
        buttons.addWidget(self.reset_button)
        cancel = QPushButton(tr("planet_nav.cancel"))
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        self.apply_button = QPushButton(tr("mining.carrier_apply"))
        self.apply_button.setEnabled(editable)
        self.apply_button.setDefault(True)
        self.apply_button.clicked.connect(self._apply)
        buttons.addWidget(self.apply_button)
        layout.addLayout(buttons)

    def _apply(self):
        value = self.input.text().strip()
        if not value.isascii() or not value.isdigit() or len(value) > 10 or not valid_amount(int(value)):
            self.error.setText(tr("odyssey.carrier_invalid"))
            return
        self.amount = int(value)
        self.accept()

    def _reset(self):
        self.amount = None
        self.accept()
