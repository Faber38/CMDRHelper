"""Focus-neutral, one-target navigation. Input is an explicit user action."""
from datetime import datetime, timezone
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QEvent, Signal
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                              QLabel, QPushButton, QDoubleSpinBox, QDialogButtonBox,
                              QMessageBox, QComboBox, QLineEdit)

from cmdrhelper.i18n import tr, get_language
from cmdrhelper.ui.help_dialog import HelpDialog
from cmdrhelper.ui.planet_3d_widget import Planet3DWidget
from cmdrhelper.ui.system_view import SystemMapWidget


def angle_text(value):
    return "–" if value is None else f"{round(value) % 360:03d}°"


def coordinates(latitude, longitude):
    return f"{latitude:.6f}° / {longitude:.6f}°"


def direction_text(solution):
    if solution.undefined_reason:
        return tr("planet_nav." + solution.undefined_reason)
    value = round(solution.relative)
    if abs(value) == 180:
        return tr("planet_nav.behind")
    if value == 0:
        return tr("planet_nav.ahead")
    return tr("planet_nav.right" if value > 0 else "planet_nav.left", degrees=abs(value))


class PlanetNavigationWindow(QDialog):
    HELP_CONTEXT = "planet_navigation"
    save_location_requested = Signal()

    def __init__(self, controller, settings, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.settings = settings
        self.geometry_key = "planet_navigation/geometry"
        self.setWindowTitle(tr("planet_nav.title"))
        self.setWindowFlags(self.windowFlags() | Qt.Window)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.resize(450, 620)
        self.setMinimumWidth(360)
        root = QVBoxLayout(self)
        self.body_label = QLabel()
        self.body_label.setTextFormat(Qt.PlainText)
        self.body_label.setWordWrap(True)
        root.addWidget(self.body_label)
        self.target_name_label = QLabel(objectName="navigationTargetName")
        self.target_name_label.setTextFormat(Qt.PlainText)
        self.target_name_label.setWordWrap(True)
        root.addWidget(self.target_name_label)
        buttons = QHBoxLayout()
        self.input_button = QPushButton(tr("planet_nav.enter_target"))
        self.input_button.clicked.connect(self._enter_target)
        self.stop_button = QPushButton(tr("planet_nav.stop"))
        self.stop_button.clicked.connect(controller.stop_target)
        buttons.addWidget(self.input_button)
        buttons.addWidget(self.stop_button)
        self.help_button = QPushButton("? " + tr("nav.help"))
        self.help_button.clicked.connect(self._open_help)
        buttons.addWidget(self.help_button)
        self._help_dialog = None
        root.addLayout(buttons)
        self.save_location_button = QPushButton(tr("favorites.save_surface"))
        self.save_location_button.clicked.connect(lambda: self.save_location_requested.emit())
        root.addWidget(self.save_location_button)
        self.pause_label = QLabel()
        self.pause_label.setWordWrap(True)
        self.pause_label.setStyleSheet("font-weight: bold; color: #e6a94b;")
        root.addWidget(self.pause_label)
        self.globe = Planet3DWidget(None, self, diameter=260, navigation=True)
        root.addWidget(self.globe, stretch=1)
        schematic = QLabel(tr("planet_nav.schematic"))
        schematic.setWordWrap(True)
        root.addWidget(schematic)
        legend = QLabel(tr("planet_nav.legend"))
        legend.setTextFormat(Qt.RichText)
        legend.setWordWrap(True)
        root.addWidget(legend)
        self.target_distance_label = QLabel()
        self.target_distance_label.setTextFormat(Qt.PlainText)
        self.target_distance_label.setStyleSheet("font-size: 21px; font-weight: bold;")
        root.addWidget(self.target_distance_label)
        self.values = {}
        form = QFormLayout()
        for key in ("target_coords", "current_coords", "distance", "bearing", "heading", "relative"):
            label = QLabel("–")
            label.setTextFormat(Qt.PlainText)
            if key == "relative":
                label.setStyleSheet("font-size: 21px; font-weight: bold;")
            self.values[key] = label
            form.addRow(tr("planet_nav." + key), label)
        self.target_course_label = QLabel()
        self.target_course_label.setTextFormat(Qt.PlainText)
        self.target_course_label.setStyleSheet("font-size: 21px; font-weight: bold;")
        form.addRow("", self.target_course_label)
        root.addLayout(form)
        self.age_label = QLabel()
        root.addWidget(self.age_label)
        geometry = self.settings.value(self.geometry_key)
        if geometry is not None:
            try:
                self.restoreGeometry(geometry)
            except (TypeError, ValueError):
                pass
        controller.changed.connect(self.refresh_navigation)
        self._age_timer = QTimer(self)
        self._age_timer.setInterval(1000)
        self._age_timer.timeout.connect(self._refresh_age)
        self._age_timer.start()
        self.refresh_navigation(controller.state)

    def _open_help(self):
        if self._help_dialog is not None:
            self._help_dialog.close()
        self._help_dialog = HelpDialog(self.HELP_CONTEXT, self, language=get_language())
        self._help_dialog.show()

    def _save_geometry(self):
        self.settings.setValue(self.geometry_key, self.saveGeometry())
        self.settings.sync()

    def moveEvent(self, event):
        super().moveEvent(event)
        self._save_geometry()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_minimum_height()
        self._save_geometry()

    def event(self, event):
        result = super().event(event)
        if event.type() == QEvent.LayoutRequest:
            self._update_minimum_height()
        return result

    def _update_minimum_height(self):
        layout = self.layout()
        if layout is None:
            return
        margins = layout.contentsMargins()
        width = max(1, self.width() - margins.left() - margins.right())
        minimum = layout.minimumSize().height()
        # Qt's layout minimum omits the extra height of wrapped explanations.
        # Reserve that height before allowing the graphic to shrink to its minimum.
        for index in range(layout.count()):
            label = layout.itemAt(index).widget()
            if isinstance(label, QLabel) and label.wordWrap():
                minimum += max(0, label.heightForWidth(width) - label.minimumSizeHint().height())
        self.setMinimumHeight(minimum)

    def closeEvent(self, event):
        self._save_geometry()
        self.controller.timer.stop()
        super().closeEvent(event)

    def _refresh_age(self):
        timestamp = self.controller.state.last_confirmed_at
        age = max(0, int((datetime.now(timezone.utc)-timestamp).total_seconds())) if timestamp else None
        self.age_label.setText(tr("planet_nav.age", seconds=age) if age is not None else tr("planet_nav.no_status"))

    def refresh_navigation(self, state):
        self.save_location_button.setEnabled(
            state.snapshot is not None
            and bool(getattr(self.controller.app_state, "commander_id", None)))
        binding = self.controller.current_body
        target_body = state.target.binding.body_name if state.target else ""
        body = binding.body_name if binding else "–"
        self.body_label.setText(tr("planet_nav.body", body=body)
                                + ("\n" + tr("planet_nav.target_body", body=target_body) if target_body else ""))
        target_name = state.target.name if state.target else ""
        self.target_name_label.setText(target_name)
        self.target_name_label.setVisible(bool(target_name))
        self.input_button.setEnabled(True)
        self.stop_button.setEnabled(state.target is not None)
        self.pause_label.setText(tr("planet_nav." + state.reason) if state.reason else tr("planet_nav.active"))
        self.values["target_coords"].setText(
            coordinates(state.target.latitude, state.target.longitude) if state.target else "–")
        for key in ("current_coords", "distance", "bearing", "heading", "relative"):
            self.values[key].setText("–")
        self.target_distance_label.setText(tr("planet_nav.target_distance", value="–"))
        self.target_course_label.setText(tr("planet_nav.target_course", value="–"))
        if state.snapshot is not None:
            s = state.snapshot
            self.values["current_coords"].setText(coordinates(s.latitude, s.longitude))
            self.values["heading"].setText(angle_text(s.heading))
        if state.solution is not None:
            solution = state.solution
            distance = (f"{solution.distance_m / 1000:.2f} km" if solution.distance_m >= 1000
                        else f"{solution.distance_m:.1f} m")
            primary_distance = (f"{solution.distance_m / 1000:.1f} km" if solution.distance_m >= 1000
                                else f"{solution.distance_m:.1f} m")
            if get_language() == "de":
                distance = distance.replace(".", ",")
                primary_distance = primary_distance.replace(".", ",")
            self.target_distance_label.setText(tr("planet_nav.target_distance", value=primary_distance))
            self.values["distance"].setText(distance)
            self.values["bearing"].setText(angle_text(solution.bearing))
            self.values["relative"].setText(direction_text(solution))
            self.target_course_label.setText(tr("planet_nav.target_course", value=angle_text(solution.bearing)))
        # Only use body artwork belonging to the current live system and body ID.
        texture = None
        app = self.controller.app_state
        if binding and getattr(app, "system_address", None) == binding.system_address:
            for candidate in getattr(app, "system_bodies", ()):
                if candidate.get("body_id") == binding.body_id and candidate.get("name") == binding.body_name:
                    name = SystemMapWidget._body_image_name(candidate)
                    if name:
                        path = Path(__file__).resolve().parent.parent / "assets" / "bodies" / (Path(name).stem + "_texture.png")
                        if path.is_file():
                            texture = path
                    break
        self.globe.set_navigation_texture(texture)
        self.globe.set_navigation_solution(state.solution)
        self._refresh_age()

    def _enter_target(self):
        self.controller.poll()
        target = self.controller.target
        snapshot = self.controller.state.snapshot
        binding = self.controller.current_body
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("planet_nav.enter_target"))
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        selector = QComboBox()
        selector.setEditable(True)
        selector.addItems(self.controller.body_names())
        selector.setCurrentText(binding.body_name if binding else target.binding.body_name if target else "")
        form.addRow(tr("planet_nav.body_name"), selector)
        name_field = QLineEdit(target.name if target else "")
        form.addRow(tr("planet_nav.target_name"), name_field)
        latitude, longitude = QDoubleSpinBox(), QDoubleSpinBox()
        for spin, limit, value in (
            (latitude, 90, target.latitude if target else snapshot.latitude if snapshot else 0),
            (longitude, 180, target.longitude if target else snapshot.longitude if snapshot else 0),
        ):
            spin.setRange(-limit, limit)
            spin.setDecimals(6)
            spin.setSingleStep(0.001)
            spin.setValue(value)
            spin.setKeyboardTracking(False)
        form.addRow(tr("planet_nav.latitude"), latitude)
        form.addRow(tr("planet_nav.longitude"), longitude)

        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText(tr("planet_nav.set_target"))
        buttons.button(QDialogButtonBox.Cancel).setText(tr("planet_nav.cancel"))

        def accept_target():
            try:
                self.controller.set_target(latitude.value(), longitude.value(),
                                           selector.currentText(), name_field.text())
            except ValueError:
                QMessageBox.information(dialog, tr("planet_nav.title"), tr("planet_nav.invalid_target"))
                return
            dialog.accept()
        buttons.accepted.connect(accept_target)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        dialog.exec()
