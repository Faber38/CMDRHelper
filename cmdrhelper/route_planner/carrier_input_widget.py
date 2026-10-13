"""Carrier planning inputs with explicit provenance and confirmation."""
from datetime import datetime, timezone
from dataclasses import replace

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget, QFormLayout, QLabel, QSpinBox, QCheckBox, QLineEdit, QScrollArea

from cmdrhelper.i18n import tr
from .carrier_inputs import BASE_MASS, PERSONAL_CAPACITY, TANK_CAPACITY
from .models import CarrierRouteRequest


class CarrierInputWidget(QWidget):
    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self._token = None
        self.confirmed_at = ""
        form = QFormLayout(self)
        form.setContentsMargins(0, 0, 0, 0)
        self.manual = QCheckBox(tr("route_planner.carrier_manual"))
        form.addRow(self.manual)
        self.callsign = QLineEdit()
        form.addRow(tr("route_planner.carrier_callsign"), self.callsign)
        form.addRow(tr("route_planner.carrier_base"), QLabel(f"{BASE_MASS} t"))
        self.capacity = QLabel(f"{PERSONAL_CAPACITY} t")
        form.addRow(tr("route_planner.carrier_capacity"), self.capacity)
        self.used = self._quantity(PERSONAL_CAPACITY)
        self.tank = self._quantity(TANK_CAPACITY)
        self.storage = self._quantity(PERSONAL_CAPACITY)
        form.addRow(tr("route_planner.carrier_used"), self.used)
        self.free = QLabel("—")
        form.addRow(tr("route_planner.carrier_free"), self.free)
        form.addRow(tr("route_planner.tritium_in_tank"), self.tank)
        form.addRow(tr("route_planner.tritium_in_storage"), self.storage)
        self.source = QLabel()
        self.source.setWordWrap(True)
        form.addRow(self.source)
        self.snapshot_hint = QLabel(tr("route_planner.carrier_snapshot_help"))
        self.snapshot_hint.setObjectName("carrierSnapshotHint")
        self.snapshot_hint.setWordWrap(True)
        form.addRow(self.snapshot_hint)
        self.snapshot_blink_timer = QTimer(self)
        self.snapshot_blink_timer.setInterval(250)
        self.snapshot_blink_timer.timeout.connect(self._advance_snapshot_blink)
        self._snapshot_blink_phase = 0
        self._snapshot_missing = False
        self._snapshot_pulse_pending = False
        self.confirm = QCheckBox(tr("route_planner.carrier_confirm"))
        form.addRow(self.confirm)
        self.input_hint = QLabel()
        self.input_hint.setWordWrap(True)
        self.input_hint.setProperty("carrierInputInvalid", True)
        self.input_hint.hide()
        form.addRow(self.input_hint)
        self.blink_timer = QTimer(self)
        self.blink_timer.setInterval(180)
        self.blink_timer.timeout.connect(self._advance_blink)
        self._blink_phase = 0
        self.confirmation_time = QLabel("—", objectName="muted")
        form.addRow(self.confirmation_time)
        for field in (self.used, self.tank, self.storage):
            field.valueChanged.connect(self._edited)
        self.callsign.textChanged.connect(self._edited)
        self.confirm.toggled.connect(self._confirmed)
        self.manual.toggled.connect(self._mode_changed)
        if state is not None and hasattr(state, "changed"):
            state.changed.connect(self.refresh)
        self.timer = QTimer(self)
        self.timer.setInterval(15000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    @staticmethod
    def _quantity(maximum):
        field = QSpinBox()
        field.setRange(-1, maximum)
        field.setSpecialValueText("—")
        field.setSuffix(" t")
        field.setValue(-1)
        return field

    def context(self):
        return (getattr(self.state, "commander_fid", ""),
                getattr(self.state, "carrier_input_session", ""),
                getattr(self.state, "carrier_input_revision", ""),
                getattr(self.state, "carrier_snapshot", None))

    def _mode_changed(self):
        self._token = None
        self.refresh()

    def _edited(self, *args):
        self.clear_feedback()
        self.confirm.setChecked(False)
        self.free.setText(f"{self._capacity - self.used.value()} t"
                          if self._capacity is not None and 0 <= self.used.value() <= self._capacity else "—")

    def _confirmed(self, checked):
        self.confirmed_at = datetime.now(timezone.utc).isoformat() if checked else ""
        self.confirmation_time.setText(self.confirmed_at or "—")
        if checked:
            self.clear_feedback()

    @staticmethod
    def _mark(widget, name, value):
        widget.setProperty(name, value)
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def _stop_blink(self):
        self.blink_timer.stop()
        self._mark(self.confirm, "carrierConfirmPulse", False)

    def _advance_blink(self):
        self._blink_phase += 1
        self._mark(self.confirm, "carrierConfirmPulse", bool(self._blink_phase % 2))
        if self._blink_phase >= 6:
            self._stop_blink()

    def clear_feedback(self):
        self._stop_blink()
        self.input_hint.hide()
        for field in (self.callsign, self.used, self.tank, self.storage, self.capacity):
            self._mark(field, "carrierInputInvalid", False)

    @staticmethod
    def _reveal(field):
        ancestor = field.parentWidget()
        while ancestor is not None:
            if isinstance(ancestor, QScrollArea):
                ancestor.ensureWidgetVisible(field, 20, 60)
            ancestor = ancestor.parentWidget()
        if field.isEnabled():
            field.setFocus()

    def show_validation_feedback(self, request):
        # Probe the existing validator without changing the actual request.
        # Only confirmation may be missing before we draw attention to it.
        technical = replace(request, confirmed_at=datetime.now(timezone.utc).isoformat())
        if technical.validation_error() is None:
            self.input_hint.setText(tr("route_planner.carrier_confirmation_required"))
            self.input_hint.show()
            if not self.blink_timer.isActive():
                self._blink_phase = 0
                self.blink_timer.start()
                self._advance_blink()
            self._reveal(self.confirm)
            return

        self.clear_feedback()
        fields = []
        if not request.carrier_callsign.strip():
            fields.append((self.callsign, "carrier_callsign"))
        if request.capacity != PERSONAL_CAPACITY:
            fields.append((self.capacity, "carrier_capacity"))
        if request.capacity_used is None or not 0 <= request.capacity_used <= (request.capacity or 0):
            fields.append((self.used, "carrier_used"))
        if not 0 <= request.tritium_in_tank <= TANK_CAPACITY:
            fields.append((self.tank, "tritium_in_tank"))
        if (not 0 <= request.tritium_in_storage <= max(request.capacity_used or 0, 0)
                or request.input_source == "journal" and request.snapshot
                and request.snapshot.cargo is not None and request.tritium_in_storage > request.snapshot.cargo):
            fields.append((self.storage, "tritium_in_storage"))
        for field, _ in fields:
            self._mark(field, "carrierInputInvalid", True)
        message = (tr("route_planner.carrier_check_fields",
                      fields=", ".join(tr("route_planner." + key) for _, key in fields))
                   if fields else tr("route_planner.carrier_input_error"))
        self.input_hint.setText(message)
        self.input_hint.show()
        if fields:
            self._reveal(fields[0][0])

    def hideEvent(self, event):
        self.stop_animations()
        super().hideEvent(event)

    def closeEvent(self, event):
        self.stop_animations()
        super().closeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()
        if self._snapshot_pulse_pending:
            self.blink_snapshot_hint()

    def stop_animations(self):
        self._stop_blink()
        self._stop_snapshot_blink()

    def _stop_snapshot_blink(self):
        self.snapshot_blink_timer.stop()
        self._mark(self.snapshot_hint, "carrierSnapshotDim", False)

    def _advance_snapshot_blink(self):
        self._snapshot_blink_phase += 1
        self._mark(self.snapshot_hint, "carrierSnapshotDim", bool(self._snapshot_blink_phase % 2))
        if self._snapshot_blink_phase >= 6:
            self._stop_snapshot_blink()

    def blink_snapshot_hint(self):
        if not self._snapshot_missing or not self.isVisible():
            return
        self._snapshot_pulse_pending = False
        if not self.snapshot_blink_timer.isActive():
            self._snapshot_blink_phase = 0
            self.snapshot_blink_timer.start()
            self._advance_snapshot_blink()

    def refresh(self):
        fid, session, revision, snapshot = self.context()
        usable = bool(snapshot and snapshot.usable(fid, session))
        complete = bool(usable and snapshot.capacity == PERSONAL_CAPACITY
                        and snapshot.used is not None and snapshot.fuel is not None)
        if complete:
            self._snapshot_pulse_pending = False
            self._stop_snapshot_blink()
        elif not self._snapshot_missing:
            self._snapshot_pulse_pending = True
        self._snapshot_missing = not complete
        self.snapshot_hint.setVisible(not complete)
        if self._snapshot_pulse_pending:
            self.blink_snapshot_hint()
        token = (fid, session, revision, snapshot, usable, self.manual.isChecked())
        if token == self._token:
            if self.confirmed_at and self.request("", "", 500).validation_error():
                self.confirm.setChecked(False)
            return
        self._token = token
        manual = self.manual.isChecked()
        self._capacity = PERSONAL_CAPACITY if manual else (snapshot.capacity if usable else None)
        self.capacity.setText(f"{self._capacity} t" if self._capacity is not None else "—")
        self.callsign.setReadOnly(not manual)
        self.used.setEnabled(manual)
        self.tank.setEnabled(manual)
        self.callsign.setText(snapshot.callsign if usable else "")
        self.used.setValue(snapshot.used if not manual and usable and snapshot.used is not None else -1)
        self.tank.setValue(snapshot.fuel if not manual and usable and snapshot.fuel is not None else -1)
        self.storage.setValue(-1)  # CarrierStats has no commodity inventory.
        self._edited()
        key = "carrier_manual" if manual else "carrier_observed" if usable else "carrier_unavailable"
        text = tr("route_planner." + key)
        text += f" · {fid}" if fid else ""
        if snapshot and not manual:
            text += f" · {snapshot.callsign} · {snapshot.carrier_type} · {snapshot.observed_at}"
        self.source.setText(text)

    def request(self, source, destination, jump_range, source_id64=None):
        fid, session, _, snapshot = self.context()
        return CarrierRouteRequest(
            source, destination, self.tank.value(), self.storage.value(), jump_range,
            source_id64=source_id64, capacity_used=self.used.value(), capacity=self._capacity,
            commander_fid=fid, carrier_callsign=self.callsign.text().strip(),
            carrier_id=(snapshot.carrier_id if snapshot and snapshot.fid == fid
                        and snapshot.callsign == self.callsign.text().strip() else None), session=session,
            input_source="manual" if self.manual.isChecked() else "journal",
            confirmed_at=self.confirmed_at, snapshot=snapshot if not self.manual.isChecked() else None,
        )
