from __future__ import annotations

import csv
import re
from pathlib import Path

from PySide6.QtCore import QSignalBlocker, QThreadPool
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QApplication,
    QFormLayout,
    QFrame,
    QHBoxLayout,
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
from .models import CarrierRouteRequest, ShipRouteRequest
from .ship_route_controller import ShipRouteController
from .spansh_galaxy_client import ALGORITHMS
from .workers import CarrierRouteWorker, ShipRouteWorker


class RoutePlannerView(QWidget):
    """Grundgerüst der eigenständigen Routenplaner-Ansicht."""

    def __init__(self, state=None, parent=None):
        super().__init__(parent)
        self.state = state
        self._thread_pool = QThreadPool.globalInstance()
        self._carrier_worker = None
        self._carrier_route = None
        self._ship_generation = 0
        self._ship_workers = {}
        self._ship_controller = ShipRouteController(
            copy_callback=self._copy_ship_target,
            changed_callback=self._refresh_ship_route_status,
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)
        layout.addWidget(QLabel(tr("nav.route_planner"), objectName="sectionTitle"))

        tabs = QTabWidget()
        tabs.addTab(self._build_ship_tab(), tr("route_planner.ship_route"))
        tabs.addTab(self._build_carrier_tab(), tr("route_planner.carrier_route"))
        layout.addWidget(tabs, 1)

        if self.state is not None and hasattr(self.state, "positionChanged"):
            self.state.positionChanged.connect(self._ship_position_changed)
        if self.state is not None and hasattr(self.state, "shipLoadoutChanged"):
            self.state.shipLoadoutChanged.connect(self._ship_loadout_changed)
        if self.state is not None and hasattr(self.state, "shipRouteInputsChanged"):
            self.state.shipRouteInputsChanged.connect(self._ship_route_inputs_changed)
        self._apply_ship_loadout_inputs()
        self._ship_controller.handle_position(
            getattr(self.state, "system", "") if self.state else "",
            getattr(self.state, "system_address", None) if self.state else None,
            "Location",
        )

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
        self._ship_field_has_value = {
            name: False for name in self._ship_auto_fields
        }
        for name, field in self._ship_auto_fields.items():
            field.valueChanged.connect(
                lambda _value, field_name=name: self._ship_field_edited(field_name)
            )

        fields = (
            (self._ship_field_translation_keys[name], widget)
            for name, widget in self._ship_auto_fields.items()
        )
        for label_key, widget in fields:
            form.addRow(tr(label_key), widget)

        self.ship_algorithm = QComboBox()
        for algorithm in ALGORITHMS:
            self.ship_algorithm.addItem(algorithm, algorithm)
        form.addRow(tr("route_planner.ship_algorithm"), self.ship_algorithm)

        self.ship_use_supercharge = QCheckBox(tr("route_planner.ship_use_supercharge"))
        self.ship_is_supercharged = QCheckBox(tr("route_planner.ship_is_supercharged"))
        self.ship_use_injections = QCheckBox(tr("route_planner.ship_use_injections"))
        self.ship_exclude_secondary = QCheckBox(tr("route_planner.ship_exclude_secondary"))
        self.ship_refuel_scoopable = QCheckBox(tr("route_planner.ship_refuel_scoopable"))
        option_row = QHBoxLayout()
        for checkbox in (
            self.ship_use_supercharge,
            self.ship_is_supercharged,
            self.ship_use_injections,
            self.ship_exclude_secondary,
            self.ship_refuel_scoopable,
        ):
            option_row.addWidget(checkbox)
        option_row.addStretch()
        input_layout.addLayout(form)
        input_layout.addLayout(option_row)

        loadout_row = QHBoxLayout()
        self.ship_apply_loadout_button = QPushButton(
            tr("route_planner.ship_loadout_apply")
        )
        self.ship_apply_loadout_button.clicked.connect(
            self._reset_ship_input_overrides
        )
        self.ship_loadout_status = QLabel("", objectName="muted")
        loadout_row.addWidget(self.ship_apply_loadout_button)
        loadout_row.addWidget(self.ship_loadout_status)
        loadout_row.addStretch()
        input_layout.addLayout(loadout_row)

        calculate_row = QHBoxLayout()
        self.ship_calculate_button = QPushButton(
            tr("route_planner.ship_calculate_spansh"), objectName="primary"
        )
        self.ship_calculate_button.clicked.connect(self._calculate_ship_route)
        self.ship_calculation_status = QLabel("", objectName="muted")
        calculate_row.addWidget(self.ship_calculate_button)
        calculate_row.addWidget(self.ship_calculation_status)
        calculate_row.addStretch()
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
        self._ship_manual_overrides.add(field_name)
        self._ship_field_has_value[field_name] = field.value() != field.minimum()

    def _ship_loadout_changed(self, _loadout=None):
        self._apply_ship_loadout_inputs()

    def _ship_route_inputs_changed(self, _loadout=None):
        self._apply_ship_loadout_inputs({"cargo", "reserve_size"})

    def _reset_ship_input_overrides(self):
        self._ship_manual_overrides.clear()
        self._apply_ship_loadout_inputs()

    def _apply_ship_loadout_inputs(self, field_names=None):
        loadout = getattr(self.state, "ship_loadout", None) if self.state else None
        if loadout is None or not hasattr(self, "_ship_auto_fields"):
            return

        technical = derive_ship_route_technical_data(loadout)
        selected = set(field_names or self._ship_auto_fields)
        for name, field in self._ship_auto_fields.items():
            if name not in selected or name in self._ship_manual_overrides:
                continue
            value = getattr(technical, name)
            with QSignalBlocker(field):
                field.setValue(field.minimum() if value is None else value)
            self._ship_field_has_value[name] = value is not None
        self._update_ship_loadout_status(technical)

    def _update_ship_loadout_status(self, technical):
        if technical.stale:
            key = "route_planner.ship_loadout_stale"
        elif technical.unknown_fsd:
            key = "route_planner.ship_loadout_unknown_fsd"
        elif technical.complete:
            key = "route_planner.ship_loadout_complete"
        else:
            key = "route_planner.ship_loadout_incomplete"
        self.ship_loadout_status.setText(tr(key))

    def _missing_ship_input_fields(self):
        return [
            name for name in self._ship_auto_fields
            if not self._ship_field_has_value[name]
        ]

    def _calculate_ship_route(self):
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
            is_supercharged=self.ship_is_supercharged.isChecked(),
            use_supercharge=self.ship_use_supercharge.isChecked(),
            use_injections=self.ship_use_injections.isChecked(),
            exclude_secondary=self.ship_exclude_secondary.isChecked(),
            refuel_every_scoopable=self.ship_refuel_scoopable.isChecked(),
            algorithm=self.ship_algorithm.currentData(),
            tank_size=self.ship_tank_size.value(),
            cargo=self.ship_cargo.value(),
            optimal_mass=self.ship_optimal_mass.value(),
            base_mass=self.ship_base_mass.value(),
            internal_tank_size=self.ship_internal_tank.value(),
            max_fuel_per_jump=self.ship_max_fuel.value(),
            range_boost=self.ship_range_boost.value(),
            fuel_power=self.ship_fuel_power.value(),
            fuel_multiplier=self.ship_fuel_multiplier.value(),
            reserve_size=self.ship_reserve_size.value(),
        )
        self._ship_generation += 1
        generation = self._ship_generation
        self._reset_ship_results()
        self.ship_calculation_status.setText(tr("route_planner.ship_calculating"))
        worker = ShipRouteWorker(request, generation)
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
            "no_route": tr("route_planner.error_no_route"),
            "source_unknown": tr("route_planner.error_source_unknown"),
            "destination_unknown": tr("route_planner.error_destination_unknown"),
            "unreachable": tr("route_planner.error_unreachable"),
            "timeout": tr("route_planner.error_timeout"),
            "invalid_response": tr("route_planner.error_invalid_response"),
            "server_error": tr("route_planner.error_server"),
            "spansh_error": tr("route_planner.error_spansh"),
            "unexpected": tr("route_planner.error_unexpected"),
        }
        self.ship_calculation_status.setText(messages.get(code, tr("route_planner.error_unexpected")))

    def _reset_ship_results(self):
        self._ship_controller.clear_route()
        self.ship_results.setRowCount(0)
        self.ship_total_distance.setText(tr("route_planner.total_distance", value="–"))
        self.ship_jump_count.setText(tr("route_planner.jump_count", value="–"))
        self.ship_total_fuel.setText(tr("route_planner.ship_total_fuel", value="–"))
        self.ship_clipboard_status.setText("")

    def _ship_position_changed(self, system, system_address, event_type):
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
        self.ship_current_system.setText(controller.current_system or "–")
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
        form.addRow(
            tr("route_planner.destination_system"),
            self.carrier_destination_system,
        )

        self.carrier_tritium_tank = self._tonnage_input(0, 1000)
        self.carrier_tritium_tank.valueChanged.connect(
            self._update_calculated_carrier_mass
        )
        form.addRow(
            tr("route_planner.tritium_in_tank"), self.carrier_tritium_tank
        )

        self.carrier_tritium_storage = self._tonnage_input(0, 25000)
        self.carrier_tritium_storage.valueChanged.connect(
            self._update_calculated_carrier_mass
        )
        form.addRow(
            tr("route_planner.tritium_in_storage"), self.carrier_tritium_storage
        )

        self.carrier_calculated_mass = QLabel()
        form.addRow(
            tr("route_planner.calculated_carrier_mass"),
            self.carrier_calculated_mass,
        )
        self._update_calculated_carrier_mass()

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

        source = self.carrier_start_system.text().strip()
        destination = self.carrier_destination_system.text().strip()
        if not source:
            self.carrier_status.setText(tr("route_planner.error_start_required"))
            return
        if not destination:
            self.carrier_status.setText(tr("route_planner.error_destination_required"))
            return

        tritium_in_tank = self.carrier_tritium_tank.value()
        tritium_in_storage = self.carrier_tritium_storage.value()
        if tritium_in_tank + tritium_in_storage > 25000:
            self.carrier_status.setText(tr("route_planner.error_tritium_capacity"))
            return

        request = CarrierRouteRequest(
            source=source,
            destination=destination,
            tritium_in_tank=tritium_in_tank,
            tritium_in_storage=tritium_in_storage,
            max_jump_range=self.carrier_jump_range.value(),
        )
        self._reset_carrier_results()
        self.carrier_calculate_button.setEnabled(False)
        self.carrier_status.setText(tr("route_planner.calculating"))

        worker = CarrierRouteWorker(request)
        worker.signals.finished.connect(self._carrier_route_finished)
        worker.signals.failed.connect(self._carrier_route_failed)
        self._carrier_worker = worker
        self._thread_pool.start(worker)

    def _carrier_route_finished(self, route):
        self._carrier_worker = None
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
        self._carrier_route = None
        self.carrier_calculate_button.setEnabled(True)
        self.carrier_export_button.setEnabled(False)
        messages = {
            "source_unknown": tr("route_planner.error_source_unknown"),
            "destination_unknown": tr("route_planner.error_destination_unknown"),
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

    def _update_calculated_carrier_mass(self, *args):
        total = (
            25000
            + self.carrier_tritium_tank.value()
            + self.carrier_tritium_storage.value()
        )
        self.carrier_calculated_mass.setText(f"{total} t")

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
