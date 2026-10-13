from __future__ import annotations

import csv
import re
from pathlib import Path

from PySide6.QtCore import QSignalBlocker, QThreadPool, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QDialog,
    QFileDialog,
    QApplication,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

from cmdrhelper.i18n import tr
from .ctsvision_csv import export_ctsvision_csv
from .fsd_specs import derive_ship_route_technical_data
from .models import ShipRouteRequest
from .carrier_input_widget import CarrierInputWidget
from .manual_ship_data import ManualShipData, LIVE, identity, configuration, live_binding
from .ship_route_controller import ShipRouteController
from .spansh_galaxy_client import ALGORITHMS
from .workers import CarrierRouteWorker, ShipRouteWorker


class RoutePlannerView(QWidget):
    """Grundgerüst der eigenständigen Routenplaner-Ansicht."""

    def __init__(self, state=None, parent=None):
        super().__init__(parent)
        self.state = state
        self._manual_ship_data = getattr(state, '_ship_route_manual_data', None)
        if not isinstance(self._manual_ship_data, ManualShipData):
            self._manual_ship_data = ManualShipData(getattr(state, 'settings', None))
            if state is not None:
                state._ship_route_manual_data = self._manual_ship_data
        self._manual_ship_identity = None
        self._manual_live_binding = None
        self._manual_live_active = False
        self._thread_pool = QThreadPool.globalInstance()
        self._carrier_worker = None
        self._carrier_route = None
        self._ship_generation = 0
        self._ship_workers = {}
        self._destination_identity = None
        self._ship_controller = ShipRouteController(
            copy_callback=self._copy_ship_target,
            changed_callback=self._refresh_ship_route_status,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        layout.addWidget(QLabel(tr("nav.route_planner"), objectName="sectionTitle"))

        tabs = QTabWidget()
        self.route_tabs = tabs
        tabs.addTab(self._build_ship_tab(), tr("route_planner.ship_route"))
        tabs.addTab(self._build_carrier_tab(), tr("route_planner.carrier_route"))
        layout.addWidget(tabs, 1)

        self._manual_starts = set()
        for field in (self.ship_start_system, self.carrier_start_system):
            field.textEdited.connect(
                lambda text, field=field: self._start_system_edited(field, text)
            )
        if self.state is not None and hasattr(self.state, "changed"):
            self.state.changed.connect(self._sync_current_system)
            self.state.changed.connect(self._sync_carrier_identity)
        self._carrier_identity = self._current_carrier_identity()
        self._sync_current_system()
        if self.state is not None and hasattr(self.state, "positionChanged"):
            self.state.positionChanged.connect(self._ship_position_changed)
        if self.state is not None and hasattr(self.state, "shipLoadoutChanged"):
            self.state.shipLoadoutChanged.connect(self._ship_loadout_changed)
        if self.state is not None and hasattr(self.state, "shipRouteInputsChanged"):
            self.state.shipRouteInputsChanged.connect(self._ship_route_inputs_changed)
        self._apply_ship_loadout_inputs()
        self._manual_input_timer = QTimer(self)
        self._manual_input_timer.setInterval(1000)
        self._manual_input_timer.timeout.connect(self._refresh_manual_live_inputs)
        self._manual_input_timer.start()
        self._ship_controller.handle_position(
            getattr(self.state, "system", "") if self.state else "",
            getattr(self.state, "system_address", None) if self.state else None,
            "Location",
        )

    def set_destination_system(self, system_name, system_id64=None):
        """Prepare the existing ship planner without calculating or starting a route."""
        self._sync_current_system()
        self.ship_destination_system.setText(str(system_name).strip())
        self._destination_identity = (str(system_name).strip().casefold(), system_id64)
        self.route_tabs.setCurrentIndex(0)

    def _start_system_edited(self, field, text):
        if text.strip():
            self._manual_starts.add(field)
        else:
            self._manual_starts.discard(field)

    def _sync_current_system(self):
        """Refresh planning defaults from AppState, without advancing any route."""
        current = str(getattr(self.state, "system", "") or "").strip()
        self.ship_current_system.setText(current or "–")
        for field in (self.ship_start_system, self.carrier_start_system):
            if field not in self._manual_starts or not field.text().strip():
                self._manual_starts.discard(field)
                field.setText(current)

    def _current_carrier_identity(self):
        fid, session, _, snapshot = self.carrier_inputs.context()
        return (fid, session, snapshot.carrier_id if snapshot else None,
                snapshot.callsign if snapshot else "")

    def _sync_carrier_identity(self):
        identity = self._current_carrier_identity()
        if identity != self._carrier_identity:
            self._carrier_identity = identity
            self._reset_carrier_results()
            self.carrier_status.setText("")

    def showEvent(self, event):
        self._sync_current_system()
        super().showEvent(event)

    def closeEvent(self, event):
        self.carrier_inputs.stop_animations()
        super().closeEvent(event)

    def _build_ship_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        progress_card = QFrame(objectName="card")
        card_layout = QFormLayout(progress_card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        self.ship_current_system = QLabel("–")
        self.ship_next_system = QLabel("–")
        self.ship_route_status = QLabel(tr("route_planner.ship_status_no_route"))
        card_layout.addRow(
            tr("route_planner.ship_current_system"), self.ship_current_system
        )
        card_layout.addRow(
            tr("route_planner.ship_next_system"), self.ship_next_system
        )
        card_layout.addRow(
            tr("route_planner.ship_route_status"), self.ship_route_status
        )
        layout.addWidget(progress_card)

        actions = QHBoxLayout()
        self.ship_copy_button = QPushButton(tr("route_planner.copy_next_system"))
        self.ship_copy_button.setEnabled(False)
        self.ship_copy_button.clicked.connect(self._copy_next_ship_system)
        actions.addWidget(self.ship_copy_button)

        actions.addStretch()
        layout.addLayout(actions)

        self.ship_clipboard_status = QLabel("", objectName="muted")
        layout.addWidget(self.ship_clipboard_status)

        input_card = QFrame(objectName="card")
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(10, 8, 10, 8)
        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)

        self.ship_start_system = QLineEdit()
        self.ship_start_system.setMinimumWidth(320)
        self.ship_start_system.setMaximumWidth(420)
        self.ship_start_system.setText(str(getattr(self.state, "system", "") or ""))
        form.addRow(tr("route_planner.start_system"), self.ship_start_system)
        self.ship_destination_system = QLineEdit()
        self.ship_destination_system.setMinimumWidth(320)
        self.ship_destination_system.setMaximumWidth(420)
        form.addRow(tr("route_planner.destination_system"), self.ship_destination_system)

        self.ship_tank_size = self._ship_number_input(0, 100000, " t")
        self.ship_cargo = self._ship_number_input(0, 100000, " t")
        self.ship_base_mass = self._ship_number_input(0, 100000, " t")
        self.ship_internal_tank = self._ship_number_input(0, 10000, " t")
        self.ship_reserve_size = self._ship_number_input(0, 10000, " t")
        self.ship_optimal_mass = self._ship_number_input(0, 100000, " t")
        self.ship_max_fuel = self._ship_number_input(0, 10000, " t")
        self.ship_fuel_power = self._ship_number_input(0, 100, "")
        self.ship_fuel_multiplier = self._ship_number_input(0, 100, "")
        self.ship_range_boost = self._ship_number_input(0, 10000, " ly")
        self._ship_auto_fields = {
            "tank_size": self.ship_tank_size,
            "cargo": self.ship_cargo,
            "base_mass": self.ship_base_mass,
            "internal_tank_size": self.ship_internal_tank,
            "reserve_size": self.ship_reserve_size,
            "optimal_mass": self.ship_optimal_mass,
            "max_fuel_per_jump": self.ship_max_fuel,
            "fuel_power": self.ship_fuel_power,
            "fuel_multiplier": self.ship_fuel_multiplier,
            "range_boost": self.ship_range_boost,
        }
        self._ship_field_translation_keys = {
            "tank_size": "route_planner.ship_tank_size",
            "cargo": "route_planner.ship_cargo",
            "base_mass": "route_planner.ship_base_mass",
            "internal_tank_size": "route_planner.ship_internal_tank",
            "reserve_size": "route_planner.ship_reserve_size",
            "optimal_mass": "route_planner.ship_optimal_mass",
            "max_fuel_per_jump": "route_planner.ship_max_fuel",
            "fuel_power": "route_planner.ship_fuel_power",
            "fuel_multiplier": "route_planner.ship_fuel_multiplier",
            "range_boost": "route_planner.ship_range_boost",
        }
        self._ship_manual_overrides = set()
        self._ship_auto_values = {}
        self._ship_field_has_value = {
            name: False for name in self._ship_auto_fields
        }
        for name, field in self._ship_auto_fields.items():
            field.valueChanged.connect(
                lambda _value, field_name=name: self._ship_field_edited(field_name)
            )

        technical_layout = QGridLayout()
        technical_layout.setHorizontalSpacing(16)
        technical_layout.setVerticalSpacing(4)
        technical_fields = tuple(self._ship_auto_fields.items())
        for index, (name, widget) in enumerate(technical_fields):
            row = index % 5
            column = 0 if index < 5 else 2
            technical_layout.addWidget(
                QLabel(tr(self._ship_field_translation_keys[name])), row, column
            )
            technical_layout.addWidget(widget, row, column + 1)
        technical_layout.setColumnStretch(1, 1)
        technical_layout.setColumnStretch(3, 1)

        self.ship_algorithm = QComboBox()
        for algorithm in ALGORITHMS:
            self.ship_algorithm.addItem(algorithm, algorithm)
        algorithm_form = QFormLayout()
        algorithm_form.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        algorithm_form.addRow(
            tr("route_planner.ship_algorithm"), self.ship_algorithm
        )

        self.ship_use_supercharge = QCheckBox(tr("route_planner.ship_use_supercharge"))
        self.ship_is_supercharged = QCheckBox(tr("route_planner.ship_is_supercharged"))
        self.ship_use_injections = QCheckBox(tr("route_planner.ship_use_injections"))
        self.ship_exclude_secondary = QCheckBox(tr("route_planner.ship_exclude_secondary"))
        self.ship_refuel_scoopable = QCheckBox(tr("route_planner.ship_refuel_scoopable"))
        option_layout = QGridLayout()
        for index, checkbox in enumerate((
            self.ship_use_supercharge,
            self.ship_is_supercharged,
            self.ship_use_injections,
            self.ship_exclude_secondary,
            self.ship_refuel_scoopable,
        )):
            option_layout.addWidget(checkbox, index // 3, index % 3)
        for column in range(3):
            option_layout.setColumnStretch(column, 1)
        input_layout.addLayout(form)
        input_layout.addLayout(technical_layout)
        input_layout.addLayout(algorithm_form)
        input_layout.addLayout(option_layout)

        loadout_row = QHBoxLayout()
        self.ship_apply_loadout_button = QPushButton(
            tr("route_planner.ship_loadout_apply")
        )
        self.ship_apply_loadout_button.clicked.connect(
            self._reset_ship_input_overrides
        )
        self.ship_loadout_status = QLabel("", objectName="muted")
        loadout_row.addWidget(self.ship_apply_loadout_button)
        self.ship_complete_data_button = QPushButton(tr('route_planner.assistant_open'))
        self.ship_complete_data_button.clicked.connect(self._complete_ship_data)
        loadout_row.addWidget(self.ship_complete_data_button)
        loadout_row.addWidget(self.ship_loadout_status)
        loadout_row.addStretch()
        input_layout.addLayout(loadout_row)

        calculate_row = QHBoxLayout()
        self.ship_calculate_button = QPushButton(
            tr("route_planner.ship_calculate_spansh"), objectName="primary"
        )
        self.ship_calculate_button.clicked.connect(self._calculate_ship_route)
        self.ship_calculation_status = QLabel("", objectName="muted")
        self.ship_calculation_status.setWordWrap(True)
        calculate_row.addWidget(self.ship_calculate_button)
        calculate_row.addWidget(self.ship_calculation_status, 1)
        input_layout.addLayout(calculate_row)
        layout.addWidget(input_card)

        self.ship_results = QTableWidget(0, 8)
        self.ship_results.setHorizontalHeaderLabels([
            tr("route_planner.col_number"),
            tr("route_planner.col_system"),
            tr("route_planner.col_jump_distance"),
            tr("route_planner.col_remaining_distance"),
            tr("route_planner.ship_col_fuel_used"),
            tr("route_planner.ship_col_fuel_tank"),
            tr("route_planner.ship_col_neutron"),
            tr("route_planner.ship_col_refuel"),
        ])
        header = self.ship_results.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        for column in range(2, 8):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
        layout.addWidget(self.ship_results, 1)

        summary = QHBoxLayout()
        self.ship_total_distance = QLabel(tr("route_planner.total_distance", value="–"))
        self.ship_jump_count = QLabel(tr("route_planner.jump_count", value="–"))
        self.ship_total_fuel = QLabel(tr("route_planner.ship_total_fuel", value="–"))
        summary.addWidget(self.ship_total_distance)
        summary.addSpacing(16)
        summary.addWidget(self.ship_jump_count)
        summary.addSpacing(16)
        summary.addWidget(self.ship_total_fuel)
        summary.addStretch()
        layout.addLayout(summary)
        return tab

    @staticmethod
    def _ship_number_input(minimum, maximum, suffix):
        field = QDoubleSpinBox()
        field.setRange(minimum - 1, maximum)
        field.setDecimals(4)
        field.setSingleStep(0.1)
        field.setSuffix(suffix)
        field.setSpecialValueText("–")
        field.setValue(minimum - 1)
        return field

    def _ship_field_edited(self, field_name):
        field = self._ship_auto_fields[field_name]
        field.setToolTip(tr('route_planner.assistant_form'))
        self._ship_manual_overrides.add(field_name)
        self._ship_field_has_value[field_name] = field.value() != field.minimum()

    def _ship_loadout_changed(self, _loadout=None):
        self._apply_ship_loadout_inputs()

    def _ship_route_inputs_changed(self, _loadout=None):
        self._apply_ship_loadout_inputs({"cargo", "reserve_size"})

    def _reset_ship_input_overrides(self):
        self._ship_manual_overrides.clear()
        self._apply_ship_loadout_inputs()

    def _complete_ship_data(self):
        if getattr(self.state, 'ship_loadout', None) is None:
            return
        from .ship_data_dialog import ShipDataDialog
        dialog = ShipDataDialog(self.state, self._manual_ship_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._reset_ship_input_overrides()

    def _refresh_manual_live_inputs(self):
        if self._manual_ship_data.live or self._manual_live_active:
            self._apply_ship_loadout_inputs(LIVE)

    def _apply_ship_loadout_inputs(self, field_names=None):
        loadout = getattr(self.state, "ship_loadout", None) if self.state else None
        if loadout is None or not hasattr(self, "_ship_auto_fields"):
            return

        technical = derive_ship_route_technical_data(loadout)
        current_identity = (identity(self.state), configuration(self.state))
        binding = live_binding(self.state)
        if current_identity != self._manual_ship_identity:
            self._ship_manual_overrides.clear()
            self._manual_ship_identity = current_identity
            field_names = None
        elif binding != self._manual_live_binding:
            self._ship_manual_overrides.difference_update(LIVE)
        self._manual_live_binding = binding
        values, sources, records = self._manual_ship_data.resolve(self.state)
        self._manual_live_active = any(sources[name] == 'manual' for name in LIVE)
        selected = set(field_names or self._ship_auto_fields)
        for name, field in self._ship_auto_fields.items():
            if name not in selected or name in self._ship_manual_overrides:
                continue
            value = values[name]
            tooltip = tr('route_planner.assistant_' + sources[name])
            if name in records:
                tooltip += '\n' + tr('route_planner.assistant_stored', value=records[name]['value'])
            field.setToolTip(tooltip)
            self._ship_auto_values[name] = value
            with QSignalBlocker(field):
                field.setValue(field.minimum() if value is None else value)
            self._ship_field_has_value[name] = value is not None
        self._update_ship_loadout_status(technical)
        if any(source == 'manual' for source in sources.values()):
            key = 'ready' if all(value is not None for value in values.values()) else 'incomplete'
            self.ship_loadout_status.setText(tr('route_planner.assistant_' + key))

    def _update_ship_loadout_status(self, technical):
        item = getattr(getattr(self.state, 'ship_loadout', None), 'fsd_item', None)
        self.ship_loadout_status.setToolTip(item or '')
        self.ship_loadout_status.setWordWrap(True)
        if technical.stale:
            key = "route_planner.ship_loadout_stale"
        elif technical.unknown_fsd:
            key = ("route_planner.ship_loadout_missing_fsd_specs" if item
                   else "route_planner.ship_loadout_unknown_fsd")
        elif technical.complete:
            key = "route_planner.ship_loadout_complete"
        elif technical.missing_fields and set(technical.missing_fields) <= {"cargo", "reserve_size"}:
            key = "route_planner.ship_loadout_missing_live_data"
        else:
            key = "route_planner.ship_loadout_incomplete"
        self.ship_loadout_status.setText(tr(key))

    def _ship_input_value(self, name):
        # Keep full Journal precision for automatic values; the spinbox only
        # displays four decimals. Explicit manual values come from the widget.
        if name in self._ship_manual_overrides:
            return self._ship_auto_fields[name].value()
        return self._ship_auto_values.get(name)

    def _missing_ship_input_fields(self):
        return [
            name for name in self._ship_auto_fields
            if not self._ship_field_has_value[name]
        ]

    def _calculate_ship_route(self):
        self._refresh_manual_live_inputs()
        source = self.ship_start_system.text().strip()
        destination = self.ship_destination_system.text().strip()
        if not source:
            self.ship_calculation_status.setText(tr("route_planner.error_start_required"))
            return
        if not destination:
            self.ship_calculation_status.setText(tr("route_planner.error_destination_required"))
            return
        missing = self._missing_ship_input_fields()
        if missing:
            labels = ", ".join(
                tr(self._ship_field_translation_keys[name]) for name in missing
            )
            self.ship_calculation_status.setText(
                tr("route_planner.ship_error_missing_fields", fields=labels)
            )
            return
        required = (
            self.ship_tank_size,
            self.ship_base_mass,
            self.ship_optimal_mass,
            self.ship_max_fuel,
            self.ship_fuel_power,
            self.ship_fuel_multiplier,
        )
        if any(field.value() <= 0 for field in required):
            self.ship_calculation_status.setText(tr("route_planner.ship_error_positive_values"))
            return
        if self.ship_reserve_size.value() > self.ship_internal_tank.value():
            self.ship_calculation_status.setText(tr("route_planner.ship_error_reserve"))
            return

        request = ShipRouteRequest(
            source=source,
            destination=destination,
            source_id64=(getattr(self.state, 'system_address', None)
                         if source.casefold() == str(getattr(self.state, 'system', '') or '').strip().casefold()
                         else None),
            destination_id64=(self._destination_identity[1]
                              if self._destination_identity and self._destination_identity[0] == destination.casefold()
                              else None),
            is_supercharged=self.ship_is_supercharged.isChecked(),
            use_supercharge=self.ship_use_supercharge.isChecked(),
            use_injections=self.ship_use_injections.isChecked(),
            exclude_secondary=self.ship_exclude_secondary.isChecked(),
            refuel_every_scoopable=self.ship_refuel_scoopable.isChecked(),
            algorithm=self.ship_algorithm.currentData(),
            **{name: self._ship_input_value(name) for name in self._ship_auto_fields},
        )
        self._ship_generation += 1
        generation = self._ship_generation
        self._reset_ship_results()
        self.ship_calculation_status.setText(tr("route_planner.ship_calculating"))
        worker = ShipRouteWorker(request, generation,
                                 database_path=getattr(getattr(self.state, 'database', None), 'path', None))
        worker.signals.finished.connect(self._ship_route_finished)
        worker.signals.failed.connect(self._ship_route_failed)
        self._ship_workers[generation] = worker
        self._thread_pool.start(worker)

    def _ship_route_finished(self, generation, route):
        self._ship_workers.pop(generation, None)
        if generation != self._ship_generation:
            return
        self.ship_results.setRowCount(len(route.jumps))
        distances = []
        fuel_values = []
        for row, jump in enumerate(route.jumps):
            distances.append(jump.distance)
            fuel_values.append(jump.fuel_used)
            values = (
                str(row), jump.system, self._format_ly(jump.distance),
                self._format_ly(jump.distance_remaining),
                self._format_tonnes(jump.fuel_used), self._format_tonnes(jump.fuel_in_tank),
                self._format_bool(jump.has_neutron), self._format_bool(jump.must_refuel),
            )
            for column, value in enumerate(values):
                self.ship_results.setItem(row, column, QTableWidgetItem(value))
        total_distance = None if any(value is None for value in distances) else sum(distances)
        total_fuel = None if any(value is None for value in fuel_values) else sum(fuel_values)
        self.ship_total_distance.setText(tr("route_planner.total_distance", value=self._format_ly(total_distance)))
        self.ship_jump_count.setText(tr("route_planner.jump_count", value=max(len(route.jumps) - 1, 0)))
        self.ship_total_fuel.setText(tr("route_planner.ship_total_fuel", value=self._format_tonnes(total_fuel)))
        current = getattr(self.state, "system", "") if self.state else ""
        address = getattr(self.state, "system_address", None) if self.state else None
        self._ship_controller.set_route(route, current, address)
        self.ship_calculation_status.setText(tr("route_planner.route_ready"))

    def _ship_route_failed(self, generation, code, detail):
        self._ship_workers.pop(generation, None)
        if generation != self._ship_generation:
            return
        messages = {
            "no_route": tr("route_planner.ship_error_no_route"),
            "source_unknown": tr("route_planner.system_source_unresolved"),
            "destination_unknown": tr("route_planner.system_destination_unresolved"),
            "unreachable": tr("route_planner.error_unreachable"),
            "timeout": tr("route_planner.error_timeout"),
            "invalid_response": tr("route_planner.error_invalid_response"),
            "server_error": tr("route_planner.error_server"),
            "spansh_error": tr("route_planner.error_spansh"),
            "unexpected": tr("route_planner.error_unexpected"),
        }
        message = messages.get(code, tr("route_planner.error_unexpected"))
        if code == "no_route":
            message += "\n" + tr("route_planner.ship_no_route_help")
            message += "\n" + tr(
                "route_planner.ship_no_route_tip",
                apply=tr("route_planner.ship_loadout_apply"),
                supercharge=tr("route_planner.ship_use_supercharge"),
            )
        self.ship_calculation_status.setText(message)

    def _reset_ship_results(self):
        self._ship_controller.clear_route()
        self.ship_results.setRowCount(0)
        self.ship_total_distance.setText(tr("route_planner.total_distance", value="–"))
        self.ship_jump_count.setText(tr("route_planner.jump_count", value="–"))
        self.ship_total_fuel.setText(tr("route_planner.ship_total_fuel", value="–"))
        self.ship_clipboard_status.setText("")

    def _ship_position_changed(self, system, system_address, event_type):
        self._sync_current_system()
        self._ship_controller.handle_position(system, system_address, event_type)

    def _copy_next_ship_system(self):
        if not self._ship_controller.copy_next():
            self.ship_clipboard_status.setText(
                tr("route_planner.ship_no_next_system")
            )

    def _copy_ship_target(self, system):
        QApplication.clipboard().setText(str(system))
        self.ship_clipboard_status.setText(
            tr("route_planner.ship_copied", system=system)
        )

    def _refresh_ship_route_status(self):
        if not hasattr(self, "ship_current_system"):
            return
        controller = self._ship_controller
        self.ship_current_system.setText(str(getattr(self.state, "system", "") or "–"))
        next_jump = controller.next_jump
        self.ship_next_system.setText(next_jump.system if next_jump else "–")
        self.ship_copy_button.setEnabled(next_jump is not None)

        if controller.route is None:
            status = tr("route_planner.ship_status_no_route")
        elif controller.route.status == ShipRouteController.COMPLETE:
            status = tr("route_planner.ship_status_complete")
        elif controller.route.status == ShipRouteController.OFF_ROUTE:
            status = tr("route_planner.ship_status_off_route")
        else:
            status = tr("route_planner.ship_status_active")
        self.ship_route_status.setText(status)

    def _build_carrier_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        input_card = QFrame(objectName="card")
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(10, 8, 10, 8)

        form = QFormLayout()
        form.setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)

        self.carrier_start_system = QLineEdit()
        self.carrier_start_system.setMinimumWidth(320)
        self.carrier_start_system.setMaximumWidth(420)
        current_system = getattr(self.state, "system", "") if self.state else ""
        self.carrier_start_system.setText(str(current_system or ""))
        form.addRow(tr("route_planner.start_system"), self.carrier_start_system)

        self.carrier_destination_system = QLineEdit()
        self.carrier_destination_system.setMinimumWidth(320)
        self.carrier_destination_system.setMaximumWidth(420)
        for field in (self.carrier_start_system, self.carrier_destination_system):
            field.textChanged.connect(
                lambda _, field=field: CarrierInputWidget._mark(field, "carrierInputInvalid", False)
            )
        form.addRow(
            tr("route_planner.destination_system"),
            self.carrier_destination_system,
        )

        self.carrier_inputs = CarrierInputWidget(self.state)
        self.carrier_tritium_tank = self.carrier_inputs.tank
        self.carrier_tritium_storage = self.carrier_inputs.storage
        form.addRow(self.carrier_inputs)

        self.carrier_jump_range = QSpinBox()
        self.carrier_jump_range.setRange(1, 500)
        self.carrier_jump_range.setValue(500)
        self.carrier_jump_range.setSuffix(" ly")
        form.addRow(tr("route_planner.max_jump_range"), self.carrier_jump_range)
        input_layout.addLayout(form)

        action_row = QHBoxLayout()
        self.carrier_calculate_button = QPushButton(
            tr("route_planner.calculate_spansh"), objectName="primary"
        )
        self.carrier_calculate_button.clicked.connect(self._calculate_carrier_route)
        action_row.addWidget(self.carrier_calculate_button)
        self.carrier_status = QLabel("", objectName="muted")
        action_row.addWidget(self.carrier_status)
        action_row.addStretch()
        input_layout.addLayout(action_row)
        layout.addWidget(input_card)

        self.carrier_results = QTableWidget(0, 5)
        self.carrier_results.setHorizontalHeaderLabels(
            [
                tr("route_planner.col_number"),
                tr("route_planner.col_system"),
                tr("route_planner.col_jump_distance"),
                tr("route_planner.col_remaining_distance"),
                tr("route_planner.col_tritium"),
            ]
        )
        header = self.carrier_results.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        for column in range(2, 5):
            header.setSectionResizeMode(column, QHeaderView.ResizeToContents)
        layout.addWidget(self.carrier_results, 1)

        summary = QHBoxLayout()
        self.carrier_total_distance = QLabel(
            tr("route_planner.total_distance", value="–")
        )
        self.carrier_jump_count = QLabel(tr("route_planner.jump_count", value="–"))
        self.carrier_estimated_tritium = QLabel(
            tr("route_planner.estimated_tritium", value="–")
        )
        summary.addWidget(self.carrier_total_distance)
        summary.addSpacing(16)
        summary.addWidget(self.carrier_jump_count)
        summary.addSpacing(16)
        summary.addWidget(self.carrier_estimated_tritium)
        summary.addStretch()

        self.carrier_export_button = QPushButton(tr("route_planner.export_ctsvision"))
        self.carrier_export_button.setEnabled(False)
        self.carrier_export_button.clicked.connect(self._export_carrier_route)
        summary.addWidget(self.carrier_export_button)
        layout.addLayout(summary)
        return tab

    @staticmethod
    def _tonnage_input(minimum, maximum):
        field = QSpinBox()
        field.setRange(minimum, maximum)
        field.setSuffix(" t")
        return field

    def _calculate_carrier_route(self):
        if self._carrier_worker is not None:
            return

        self.carrier_inputs.refresh()
        self.carrier_inputs.blink_snapshot_hint()

        source = self.carrier_start_system.text().strip()
        destination = self.carrier_destination_system.text().strip()
        if not source:
            self.carrier_status.setText(tr("route_planner.error_start_required"))
            self.carrier_inputs._mark(self.carrier_start_system, "carrierInputInvalid", True)
            self.carrier_inputs._reveal(self.carrier_start_system)
            return
        if not destination:
            self.carrier_status.setText(tr("route_planner.error_destination_required"))
            self.carrier_inputs._mark(self.carrier_destination_system, "carrierInputInvalid", True)
            self.carrier_inputs._reveal(self.carrier_destination_system)
            return

        request = self.carrier_inputs.request(
            source, destination, self.carrier_jump_range.value(),
            source_id64=(getattr(self.state, 'system_address', None)
                         if source.casefold() == str(getattr(self.state, 'system', '') or '').strip().casefold()
                         else None),
        )
        if request.validation_error():
            self.carrier_status.setText("")
            self.carrier_inputs.show_validation_feedback(request)
            return
        self.carrier_inputs.clear_feedback()
        self._carrier_request_context = self.carrier_inputs.context()
        self._reset_carrier_results()
        self.carrier_calculate_button.setEnabled(False)
        self.carrier_inputs.setEnabled(False)
        self.carrier_status.setText(tr("route_planner.calculating"))

        worker = CarrierRouteWorker(request,
                                    database_path=getattr(getattr(self.state, 'database', None), 'path', None))
        worker.signals.finished.connect(self._carrier_route_finished)
        worker.signals.failed.connect(self._carrier_route_failed)
        self._carrier_worker = worker
        self._thread_pool.start(worker)

    def _carrier_route_finished(self, route):
        self._carrier_worker = None
        self.carrier_inputs.setEnabled(True)
        if getattr(self, "_carrier_request_context", None) != self.carrier_inputs.context():
            self.carrier_calculate_button.setEnabled(True)
            self.carrier_status.setText(tr("route_planner.carrier_input_error"))
            return
        self._carrier_route = route
        self.carrier_calculate_button.setEnabled(True)
        self.carrier_export_button.setEnabled(True)
        self.carrier_results.setRowCount(len(route.jumps))
        for row, jump in enumerate(route.jumps):
            values = (
                str(row),
                jump.system,
                self._format_ly(jump.distance),
                self._format_ly(jump.distance_remaining),
                "–" if jump.tritium_used is None else f"{jump.tritium_used} t",
            )
            for column, value in enumerate(values):
                self.carrier_results.setItem(row, column, QTableWidgetItem(value))

        self.carrier_total_distance.setText(
            tr("route_planner.total_distance", value=self._format_ly(route.total_distance))
        )
        self.carrier_jump_count.setText(
            tr("route_planner.jump_count", value=route.jump_count)
        )
        self.carrier_estimated_tritium.setText(
            tr("route_planner.estimated_tritium", value=f"{route.estimated_tritium} t")
        )
        self.carrier_status.setText(tr("route_planner.route_ready"))

    def _carrier_route_failed(self, code, detail):
        self._carrier_worker = None
        self.carrier_inputs.setEnabled(True)
        self._carrier_route = None
        self.carrier_calculate_button.setEnabled(True)
        self.carrier_export_button.setEnabled(False)
        messages = {
            "carrier_inputs": tr("route_planner.carrier_input_error"),
            "source_unknown": tr("route_planner.system_source_unresolved"),
            "destination_unknown": tr("route_planner.system_destination_unresolved"),
            "no_route": tr("route_planner.error_no_route"),
            "unreachable": tr("route_planner.error_unreachable"),
            "timeout": tr("route_planner.error_timeout"),
            "invalid_response": tr("route_planner.error_invalid_response"),
            "server_error": tr("route_planner.error_server"),
            "spansh_error": tr("route_planner.error_spansh"),
            "unexpected": tr("route_planner.error_unexpected"),
        }
        self.carrier_status.setText(
            messages.get(code, tr("route_planner.error_unexpected"))
        )

    def _reset_carrier_results(self):
        self._carrier_route = None
        self.carrier_export_button.setEnabled(False)
        self.carrier_results.setRowCount(0)
        self.carrier_total_distance.setText(
            tr("route_planner.total_distance", value="–")
        )
        self.carrier_jump_count.setText(tr("route_planner.jump_count", value="–"))
        self.carrier_estimated_tritium.setText(
            tr("route_planner.estimated_tritium", value="–")
        )

    @staticmethod
    def _format_ly(value):
        return "–" if value is None else f"{value:.2f} ly"

    @staticmethod
    def _format_tonnes(value):
        return "–" if value is None else f"{value:.4f}".rstrip("0").rstrip(".") + " t"

    @staticmethod
    def _format_bool(value):
        if value is None:
            return "–"
        return tr("common.yes") if value else tr("common.no")

    def _export_carrier_route(self):
        if self._carrier_route is None:
            self.carrier_export_button.setEnabled(False)
            return

        source = self.carrier_start_system.text().strip()
        destination = self.carrier_destination_system.text().strip()
        suggested = self._safe_export_filename(
            f"fleet-carrier-{source}-{destination}.csv"
        )
        selected, _ = QFileDialog.getSaveFileName(
            self,
            tr("route_planner.export_dialog_title"),
            suggested,
            "CSV (*.csv)",
        )
        if not selected:
            return

        target = Path(selected)
        if target.suffix.lower() != ".csv":
            target = target.with_suffix(".csv")
        if target.exists():
            self.carrier_status.setText(tr("route_planner.export_exists"))
            return

        try:
            export_ctsvision_csv(self._carrier_route, target)
        except (OSError, csv.Error) as exc:
            self.carrier_status.setText(
                tr("route_planner.export_failed", error=str(exc))
            )
            return
        self.carrier_status.setText(
            tr("route_planner.export_success", path=str(target))
        )

    @staticmethod
    def _safe_export_filename(value):
        return re.sub(r'[<>:"/\\|?*]+', "_", value).strip() or "fleet-carrier.csv"
