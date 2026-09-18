from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QMessageBox,
    QPushButton,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QGridLayout,
    QSizePolicy,
    QLabel,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QToolButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from cmdrhelper.i18n import tr
from cmdrhelper.mission_manager import translate_mission_text
from cmdrhelper.ship_equipment import analyze_ship_modules
from cmdrhelper.ui.ship_assets import ship_display_name, carrier_preview
from cmdrhelper.ui.personal_ship_images import (
    IMAGE_NAME_PATTERNS, personal_ship_image, import_ship_image, remove_ship_image,
    personal_carrier_image, import_carrier_image, remove_carrier_image,
)
from cmdrhelper.ui.fleet_actions import FleetReadTask, reversible_image_removal
from cmdrhelper.journal_files import journal_files
from cmdrhelper.ui.ship_widgets import ElidedShipLabel, ShipImage, FleetHeader


class CommanderView(QWidget):
    """Rein lesende Offline-/Live-Übersicht bekannter Commanderprofile."""

    FLEET_SORT_SETTINGS_KEY = "commander_view/fleet_sort_key"
    FLEET_SORT_DIRECTION_SETTINGS_KEY = "commander_view/fleet_sort_direction"
    FLEET_SORT_DEFAULT_DIRECTIONS = {
        "recent": "descending",
        "name": "ascending",
        "type": "ascending",
        "jump_range": "descending",
        "cargo": "descending",
        "mass": "descending",
        "location": "ascending",
        "last_seen": "descending",
    }

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self._fleet_rebuild_id = None
        self._protected_ship_id = None
        self._ship_image_fid = ""
        self._fleet_commander_id = None
        self._expanded_ship_ids = set()
        self._build_ui()
        self.state.commanderIdentityChanged.connect(self.refresh)
        self.state.viewedCommanderChanged.connect(self.refresh)
        self.state.changed.connect(self.refresh)
        self.refresh()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 6, 10, 6)
        root.setSpacing(8)
        root.addWidget(QLabel(tr("commander_view.title"), objectName="sectionTitle"))

        selector = QFrame(objectName="card")
        selector_layout = QHBoxLayout(selector)
        selector_layout.addWidget(QLabel(tr("commander_view.commander")))
        self.commander_combo = QComboBox()
        self.commander_combo.setMinimumWidth(260)
        self.commander_combo.currentIndexChanged.connect(self._selection_changed)
        selector_layout.addWidget(self.commander_combo)
        self.identity_label = QLabel("–", objectName="muted")
        selector_layout.addWidget(self.identity_label)
        self.status_label = QLabel("–", objectName="muted")
        selector_layout.addWidget(self.status_label)
        selector_layout.addStretch()
        root.addWidget(selector)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._overview_tab(), tr("commander_view.tab.overview"))
        self.tabs.addTab(self._missions_tab(), tr("commander_view.tab.missions"))
        self.tabs.addTab(self._exploration_tab(), tr("commander_view.tab.exploration"))
        self.tabs.addTab(self._placeholder(), tr("commander_view.tab.chronicle"))
        self.tabs.addTab(self._ships_tab(), tr("commander_view.tab.ships"))
        root.addWidget(self.tabs, 1)

    def _overview_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        card = QFrame(objectName="card")
        form = QFormLayout(card)
        self.values = {}
        fields = (
            ("name", tr("commander_view.field.name")),
            ("fid", tr("commander_view.field.fid")),
            ("status", tr("commander_view.field.status")),
            ("first_seen", tr("commander_view.field.first_seen")),
            ("last_seen", tr("commander_view.field.last_seen")),
            ("visited_systems", tr("commander_view.field.visited_systems")),
            ("biology_findings", tr("commander_view.field.biology_findings")),
            ("geology_findings", tr("commander_view.field.geology_findings")),
            ("codex_entries", tr("commander_view.field.codex_entries")),
            ("cartography_sales", tr("commander_view.field.cartography_sales")),
            ("last_location", tr("commander_view.field.last_location")),
            ("open_missions", tr("commander_view.field.open_missions")),
            ("last_ship", tr("commander_view.field.last_ship")),
            ("fleet_carrier", tr("commander_view.field.fleet_carrier")),
            ("carrier_location", tr("commander_view.field.carrier_location")),
            ("wealth", tr("commander_view.field.wealth")),
            ("unsold_biology", tr("commander_view.field.unsold_biology")),
            ("unsold_cartography", tr("commander_view.field.unsold_cartography")),
        )
        for field, label in fields:
            value = QLabel("–")
            value.setWordWrap(True)
            self.values[field] = value
            form.addRow(label, value)
        layout.addWidget(card)
        mercenary_card = QFrame(objectName="card")
        mercenary_form = QFormLayout(mercenary_card)
        mercenary_form.addRow(
            QLabel(tr("commander_view.mercenary.title"), objectName="sectionTitle")
        )
        self.mercenary_values = {}
        for field, label in (
            ("current", tr("commander_view.mercenary.current")),
            ("total_spent", tr("commander_view.mercenary.total_spent")),
            ("spent_on_engineering", tr("commander_view.mercenary.engineering")),
            ("spent_on_gear", tr("commander_view.mercenary.gear")),
            ("total_earned", tr("commander_view.mercenary.total_earned")),
        ):
            value = QLabel("–")
            if field == "total_earned":
                value.setToolTip(tr("commander_view.mercenary.total_earned_tooltip"))
            self.mercenary_values[field] = value
            mercenary_form.addRow(label, value)
        layout.addWidget(mercenary_card)
        layout.addStretch()
        return tab

    def _exploration_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        card = QFrame(objectName="card")
        form = QFormLayout(card)
        self.exploration_values = {}
        for field, label in (
            ("unsold_biology", tr("commander_view.field.unsold_biology")),
            ("unsold_cartography", tr("commander_view.field.unsold_cartography")),
            ("biology_findings", tr("commander_view.field.biology_findings")),
            ("first_footfalls", tr("commander_view.exploration.first_footfalls")),
            ("self_mapped_bodies", tr("commander_view.exploration.self_mapped")),
            ("efficiently_mapped_bodies", tr("commander_view.exploration.efficient_mapped")),
            ("visited_systems", tr("commander_view.field.visited_systems")),
        ):
            value = QLabel("–")
            self.exploration_values[field] = value
            form.addRow(label, value)
        layout.addWidget(card)
        layout.addStretch()
        return tab

    def _missions_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        self.missions_table = QTableWidget(0, 5)
        self.missions_table.setHorizontalHeaderLabels([
            tr("commander_view.missions.status"),
            tr("commander_view.missions.mission"),
            tr("commander_view.missions.destination"),
            tr("commander_view.missions.expiry"),
            tr("commander_view.missions.reward"),
        ])
        self.missions_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.missions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.missions_table.verticalHeader().setVisible(False)
        self.missions_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents
        )
        self.missions_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.missions_table)
        return tab

    def _ships_tab(self):
        tab = QWidget()
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        self.fleet_scroll = QScrollArea()
        self.fleet_scroll.setWidgetResizable(True)
        self.fleet_scroll.setFrameShape(QFrame.NoFrame)
        self.fleet_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.fleet_scroll.setObjectName("commanderFleetScroll")
        content = QWidget()
        self.fleet_scroll.setWidget(content)
        layout = QVBoxLayout(content)
        tab_layout.addWidget(self.fleet_scroll)
        layout.addWidget(QLabel(tr("commander_view.fleet.current"), objectName="sectionTitle"))
        self.current_ship_card = QFrame(objectName="card")
        current_layout = QHBoxLayout(self.current_ship_card)
        self.current_ship_image = ShipImage(144, 100)
        current_layout.addWidget(self.current_ship_image, 0, Qt.AlignTop)
        current_info = QVBoxLayout()
        current_layout.addLayout(current_info, 1)
        name = ElidedShipLabel()
        font = name.font()
        font.setPointSizeF(font.pointSizeF() + 2)
        font.setBold(True)
        name.setFont(font)
        current_info.addWidget(name)
        current_form = QFormLayout()
        current_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        current_info.addLayout(current_form)
        self.current_ship_values = {"name": name}
        for field, label in (
            ("type", tr("commander_view.ship.ship_type")),
            ("location", tr("commander_view.ship.location")),
            ("ship_id", tr("commander_view.ship.ship_id")),
        ):
            value = ElidedShipLabel()
            self.current_ship_values[field] = value
            current_form.addRow(label, value)
        self.current_ship_status = ElidedShipLabel()
        current_form.addRow(tr("commander_view.field.status"), self.current_ship_status)
        self.ship_values = self.current_ship_values
        layout.addWidget(self.current_ship_card)

        self.fleet_title = QLabel(objectName="sectionTitle")
        sort_bar = QFrame(objectName="card")
        sort_layout = QGridLayout(sort_bar)
        sort_layout.setContentsMargins(8, 4, 8, 4)
        sort_layout.addWidget(QLabel(tr("commander_view.fleet.sort_by")), 0, 0)
        self.fleet_sort_combo = QComboBox()
        for key in self.FLEET_SORT_DEFAULT_DIRECTIONS:
            self.fleet_sort_combo.addItem(
                tr(f"commander_view.fleet.sort.{key}"), key
            )
        sort_layout.addWidget(self.fleet_sort_combo, 0, 1)
        self.fleet_sort_direction_combo = QComboBox()
        self.fleet_sort_direction_combo.addItem(
            tr("commander_view.fleet.sort.ascending"), "ascending"
        )
        self.fleet_sort_direction_combo.addItem(
            tr("commander_view.fleet.sort.descending"), "descending"
        )
        sort_layout.addWidget(self.fleet_sort_direction_combo, 0, 2)
        sort_layout.addWidget(QLabel(tr("commander_view.fleet.filter_by")), 1, 0)
        self.fleet_filter_combo = QComboBox()
        for key in ("all", "vehicle_hangar", "fighter_hangar"):
            self.fleet_filter_combo.addItem(
                tr(f"commander_view.fleet.filter.{key}"), key
            )
        sort_layout.addWidget(self.fleet_filter_combo, 1, 1, 1, 2)
        self._restore_fleet_sort_settings()
        self.fleet_sort_combo.currentIndexChanged.connect(
            self._fleet_sort_criterion_changed
        )
        self.fleet_sort_direction_combo.currentIndexChanged.connect(
            self._fleet_sort_direction_changed
        )
        self.fleet_filter_combo.currentIndexChanged.connect(
            self._fleet_filter_changed
        )
        self.fleet_rebuild_button = QPushButton(tr("commander_view.fleet.rebuild.button"))
        self.fleet_rebuild_button.clicked.connect(self._request_fleet_rebuild)
        sort_layout.addWidget(self.fleet_rebuild_button, 2, 0, 1, 3)
        self.fleet_action_status = QLabel()
        self.fleet_action_status.setWordWrap(True)
        sort_layout.addWidget(self.fleet_action_status, 3, 0, 1, 3)
        layout.addWidget(sort_bar)
        layout.addWidget(self.fleet_title)
        self.fleet_container = QWidget()
        self.fleet_layout = QVBoxLayout(self.fleet_container)
        self.fleet_layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.fleet_container)

        layout.addWidget(QLabel(tr("commander_view.carrier.title"), objectName="sectionTitle"))
        carrier_card = QFrame(objectName="card")
        carrier_layout = QVBoxLayout(carrier_card)
        carrier_row = QHBoxLayout()
        self.carrier_image = ShipImage(144, 100, preview_resolver=carrier_preview)
        carrier_row.addWidget(self.carrier_image, 0, Qt.AlignTop)
        carrier_details = QVBoxLayout()
        carrier_name = ElidedShipLabel()
        font = carrier_name.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 2)
        carrier_name.setFont(font)
        carrier_details.addWidget(carrier_name)
        carrier_form = QFormLayout()
        carrier_form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        carrier_details.addLayout(carrier_form)
        carrier_row.addLayout(carrier_details, 1)
        carrier_layout.addLayout(carrier_row)
        self.carrier_values = {"name": carrier_name}
        for field, label in (
            ("callsign", tr("commander_view.carrier.callsign")),
            ("carrier_id", tr("commander_view.carrier.carrier_id")),
            ("location", tr("commander_view.carrier.location")),
            ("last_updated", tr("commander_view.carrier.last_updated")),
        ):
            value = ElidedShipLabel()
            self.carrier_values[field] = value
            carrier_form.addRow(label, value)
        carrier_actions = QHBoxLayout()
        self.carrier_select_image = QPushButton(tr("commander_view.carrier.image.select"))
        self.carrier_remove_image = QPushButton(tr("commander_view.ship.image.remove"))
        self.carrier_select_image.clicked.connect(self._select_carrier_image)
        self.carrier_remove_image.clicked.connect(self._remove_carrier_image)
        carrier_actions.addWidget(self.carrier_select_image)
        carrier_actions.addWidget(self.carrier_remove_image)
        carrier_actions.addStretch()
        carrier_layout.addLayout(carrier_actions)
        self._carrier_image_identity = None
        layout.addWidget(carrier_card)
        layout.addStretch()
        self.fleet_layout.addStretch()
        return tab

    def _restore_fleet_sort_settings(self):
        sort_key = str(self.state.settings.value(
            self.FLEET_SORT_SETTINGS_KEY, "recent"
        ) or "recent")
        if sort_key not in self.FLEET_SORT_DEFAULT_DIRECTIONS:
            sort_key = "recent"
        direction = str(self.state.settings.value(
            self.FLEET_SORT_DIRECTION_SETTINGS_KEY,
            self.FLEET_SORT_DEFAULT_DIRECTIONS[sort_key],
        ) or "")
        if direction not in ("ascending", "descending"):
            direction = self.FLEET_SORT_DEFAULT_DIRECTIONS[sort_key]
        self.fleet_sort_combo.setCurrentIndex(self.fleet_sort_combo.findData(sort_key))
        self.fleet_sort_direction_combo.setCurrentIndex(
            self.fleet_sort_direction_combo.findData(direction)
        )

    def _fleet_sort_criterion_changed(self, _index):
        sort_key = self.fleet_sort_combo.currentData()
        direction = self.FLEET_SORT_DEFAULT_DIRECTIONS[sort_key]
        self.fleet_sort_direction_combo.blockSignals(True)
        self.fleet_sort_direction_combo.setCurrentIndex(
            self.fleet_sort_direction_combo.findData(direction)
        )
        self.fleet_sort_direction_combo.blockSignals(False)
        self.state.settings.setValue(self.FLEET_SORT_SETTINGS_KEY, sort_key)
        self.state.settings.setValue(
            self.FLEET_SORT_DIRECTION_SETTINGS_KEY, direction
        )
        self._refresh_ship_for_current_commander()

    def _fleet_sort_direction_changed(self, _index):
        self.state.settings.setValue(
            self.FLEET_SORT_DIRECTION_SETTINGS_KEY,
            self.fleet_sort_direction_combo.currentData(),
        )
        self._refresh_ship_for_current_commander()

    def _fleet_filter_changed(self, _index):
        self._refresh_ship_for_current_commander()

    def _refresh_ship_for_current_commander(self):
        if not hasattr(self, "fleet_layout"):
            return
        viewed_id = self.state.resolve_viewed_commander(
            self.state.database.list_commanders()
        )
        self._refresh_ship(self.state.database.commander_summary(viewed_id))

    @staticmethod
    def _placeholder():
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel(tr("commander_view.placeholder"), objectName="muted"))
        layout.addStretch()
        return tab

    def _selection_changed(self, index):
        if index < 0:
            return
        commander_id = self.commander_combo.itemData(index)
        if commander_id is not None:
            self.state.select_viewed_commander(commander_id)

    def _set_status(self, is_live):
        text = (
            tr("commander_view.status.live")
            if is_live else tr("commander_view.status.view_only")
        )
        self.status_label.setText(text)
        self.status_label.setObjectName("statusOk" if is_live else "muted")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)
        self.values["status"].setText(text)

    def showEvent(self, event):
        super().showEvent(event)
        if getattr(self, "_refresh_dirty", True):
            self.refresh()

    def refresh(self, *args):
        if not self.isVisible():
            self._refresh_dirty = True
            return
        if getattr(self, "_refresh_running", False):
            return  # resolve_viewed_commander may synchronously emit its identity.
        self._refresh_running = True
        try:
            self._refresh_visible()
            self._refresh_dirty = False
        finally:
            self._refresh_running = False

    def _refresh_visible(self):
        commanders = self.state.database.list_commanders()
        viewed_id = self.state.resolve_viewed_commander(commanders)

        self.commander_combo.blockSignals(True)
        self.commander_combo.clear()
        selected_index = -1
        for index, commander in enumerate(commanders):
            self.commander_combo.addItem(commander["display_name"], commander["id"])
            if commander["id"] == viewed_id:
                selected_index = index
        self.commander_combo.setCurrentIndex(selected_index)
        self.commander_combo.blockSignals(False)

        shared = getattr(self.state, "_refresh_summary", None)
        summary = (shared[1] if shared and shared[0] == viewed_id
                   else self.state.database.commander_summary(viewed_id))
        if not summary:
            self.identity_label.setText("–")
            self.status_label.setText("–")
            self.status_label.setObjectName("muted")
            for value in self.values.values():
                value.setText("–")
            for value in self.mercenary_values.values():
                value.setText("–")
            self._refresh_missions(None)
            self._refresh_ship(None)
            for value in self.exploration_values.values():
                value.setText("–")
            return

        is_live = int(summary["id"]) == self.state.commander_id
        name = summary["current_name"] or "–"
        self.identity_label.setText(tr("commander_view.identity", name=name))
        self._set_status(is_live)
        self.values["name"].setText(name)
        self.values["fid"].setText(summary["fid"] or "–")
        self.values["first_seen"].setText(summary["first_seen"] or "–")
        self.values["last_seen"].setText(summary["last_seen"] or "–")
        for field in (
            "visited_systems", "biology_findings", "geology_findings",
            "codex_entries", "cartography_sales",
        ):
            self.values[field].setText(str(summary[field]))
        location = summary.get("latest_location") or summary["last_location"]
        self.values["last_location"].setText(
            self._location_text(location)
        )
        self.values["open_missions"].setText(str(summary["open_missions"]))
        ship = summary.get("ship")
        self.values["last_ship"].setText(
            ((ship.get("ship_name") or ship.get("ship_type") or "–") if ship else "–")
        )
        carrier = summary.get("carrier")
        self.values["fleet_carrier"].setText(
            ((carrier.get("carrier_name") or carrier.get("callsign") or "–")
             if carrier else "–")
        )
        self.values["carrier_location"].setText(self._location_text(carrier))
        wealth = summary.get("wealth")
        self.values["wealth"].setText(
            self._credits(wealth.get("credits")) if wealth else "–"
        )
        mercenary = summary.get("mercenary_credits") or {}
        for field, value in self.mercenary_values.items():
            amount = mercenary.get(field)
            value.setText(self._number(amount) if amount is not None else "–")
        bio_text = self._unsold_bio_text(summary["unsold_biology"])
        cartography_text = self._unsold_cartography_text(summary["unsold_cartography"])
        self.values["unsold_biology"].setText(bio_text)
        self.values["unsold_cartography"].setText(cartography_text)
        exploration = summary["exploration"]
        exploration_values = {
            "unsold_biology": bio_text,
            "unsold_cartography": cartography_text,
            "biology_findings": str(summary["biology_findings"]),
            "first_footfalls": str(exploration["first_footfalls"]),
            "self_mapped_bodies": str(exploration["self_mapped_bodies"]),
            "efficiently_mapped_bodies": str(exploration["efficiently_mapped_bodies"]),
            "visited_systems": str(summary["visited_systems"]),
        }
        for field, value in exploration_values.items():
            self.exploration_values[field].setText(value)
        self._refresh_missions(viewed_id)
        self._refresh_ship(summary)

    @staticmethod
    def _credits(value):
        return f"{int(value):,} Cr".replace(",", ".")

    @staticmethod
    def _number(value):
        return f"{int(value):,}".replace(",", ".")

    def _unsold_bio_text(self, data):
        count = int(data.get("findings") or 0)
        if not count:
            return tr("commander_view.unsold.bio", count=0, value="–")
        value = self._credits(data["estimated_value"]) if data.get("estimated_value") else "–"
        return tr("commander_view.unsold.bio", count=count, value=value)

    def _unsold_cartography_text(self, data):
        value = self._credits(data["estimated_value"]) if data.get("estimated_value") else "–"
        return tr("commander_view.unsold.cartography", systems=int(data.get("systems") or 0),
                  bodies=int(data.get("bodies") or 0), value=value)

    @staticmethod
    def _location_text(location):
        if not location:
            return "–"
        parts = [
            location.get("system_name") or "",
            location.get("station_name") or "",
            location.get("body_name") or "",
        ]
        text = " / ".join(part for part in parts if part)
        if not text and location.get("system_address") is not None:
            text = str(location["system_address"])
        return text or "–"

    def _refresh_missions(self, commander_id):
        missions = (
            self.state.database.commander_missions(commander_id)
            if commander_id is not None else []
        )
        self.missions_table.setRowCount(len(missions))
        for row, mission in enumerate(missions):
            destination = " / ".join(
                value for value in (
                    mission.get("destination_system") or "",
                    mission.get("destination_station") or "",
                    mission.get("destination_body") or "",
                ) if value
            ) or "–"
            values = (
                translate_mission_text(mission.get("status") or ""),
                mission.get("name") or mission.get("internal_name") or "–",
                destination,
                mission.get("expiry") or "–",
                (
                    f"{int(mission.get('reward') or 0):,}"
                    if int(mission.get("reward") or 0) > 0 else "–"
                ),
            )
            for column, value in enumerate(values):
                self.missions_table.setItem(row, column, QTableWidgetItem(str(value)))

    def _refresh_ship(self, summary):
        commander_id = summary.get("id") if summary else None
        ships = self.state.database.commander_ships(commander_id)
        current = next((ship for ship in ships if ship["is_current"]), ships[0] if ships else None)
        self._protected_ship_id = current.get("ship_id") if current else None
        self.fleet_rebuild_button.setEnabled(bool(summary) and self._fleet_rebuild_id is None)
        current_data = {
            "name": self._ship_display_title(current),
            "type": ship_display_name(current.get("ship_type")) if current else None,
            "location": self._ship_location(current),
            "ship_id": current.get("ship_id") if current else None,
        }
        for field, label in self.current_ship_values.items():
            value = current_data[field]
            label.setText(str(value) if value not in (None, "") else "–")

        self._ship_image_fid = summary.get("fid", "") if summary else ""
        self.current_ship_image.set_ship(
            current.get("ship_type") if current else None,
            self._personal_ship_image(current.get("ship_id")) if current else None,
            self._ship_display_title(current),
        )
        self.current_ship_status.setText(tr("commander_view.fleet.current_marker") if current else "–")

        if commander_id == self._fleet_commander_id:
            self._remember_visible_expanded_ship_ids()
        else:
            self._expanded_ship_ids.clear()
            self._fleet_commander_id = commander_id
        while self.fleet_layout.count():
            item = self.fleet_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        viewed_is_live = bool(
            summary and int(summary["id"]) == self.state.commander_id
        )
        current_is_live = bool(viewed_is_live and current and current["is_current"])
        current_color = self._fleet_color(current, is_live=current_is_live)
        self.current_ship_card.setProperty("liveShip", current_is_live)
        self.current_ship_card.setStyleSheet(
            f"QFrame#card {{ border-left: 5px solid {current_color.name()}; }}"
            if current_color is not None else ""
        )
        visible_ships = self._filtered_fleet_ships(ships)
        if self.fleet_filter_combo.currentData() == "all":
            title = tr("commander_view.fleet.title", count=len(ships))
        else:
            title = tr(
                "commander_view.fleet.title_filtered",
                visible=len(visible_ships),
                total=len(ships),
            )
        self.fleet_title.setText(title)
        for ship in self._sorted_fleet_ships(visible_ships):
            self.fleet_layout.addWidget(self._fleet_ship_widget(
                ship,
                is_live=bool(viewed_is_live and ship["is_current"]),
                expanded=ship.get("ship_id") in self._expanded_ship_ids,
            ))
        self.fleet_layout.addStretch()

        carrier = summary.get("carrier") if summary else None
        carrier_data = {
            "name": carrier.get("carrier_name") if carrier else None,
            "callsign": carrier.get("callsign") if carrier else None,
            "carrier_id": carrier.get("carrier_id") if carrier else None,
            "location": self._location_text(carrier),
            "last_updated": carrier.get("last_updated") if carrier else None,
        }
        for field, label in self.carrier_values.items():
            value = carrier_data[field]
            label.setText(str(value) if value not in (None, "") else "–")
        try:
            carrier_id = int(carrier_data["carrier_id"])
            self._carrier_image_identity = (self._ship_image_fid, carrier_id) if self._ship_image_fid else None
        except (ValueError, TypeError):
            self._carrier_image_identity = None
        personal = (personal_carrier_image(self.state.settings, *self._carrier_image_identity)
                    if self._carrier_image_identity else None)
        self.carrier_image.set_ship(None, personal, carrier_data["name"] or "–")
        self.carrier_select_image.setEnabled(self._carrier_image_identity is not None)
        self.carrier_remove_image.setEnabled(personal is not None)

    @staticmethod
    def _ship_display_title(ship):
        if not ship:
            return "–"
        return ship.get("ship_name") or ship_display_name(ship.get("ship_type"))

    @staticmethod
    def _ship_name(ship):
        if not ship:
            return "–"
        return ship.get("ship_name") or ship.get("ship_type") or "–"

    @staticmethod
    def _ship_location(ship):
        if not ship:
            return "–"
        parts = [ship.get("system_name") or "", ship.get("station_name") or ""]
        text = " / ".join(part for part in parts if part)
        return text or (str(ship["system_address"]) if ship.get("system_address") is not None else "–")

    @staticmethod
    def _ship_location_key(ship):
        if not ship:
            return ""
        system = str(ship.get("system_name") or "").strip().casefold()
        station = str(ship.get("station_name") or "").strip().casefold()
        address = ship.get("system_address")
        if not system and address is None:
            return ""
        return f"{system or address}|{station}"

    @staticmethod
    def _fleet_ship_id_key(ship):
        ship_id = ship.get("ship_id")
        try:
            return 0, int(ship_id)
        except (TypeError, ValueError):
            return 1, str(ship_id or "").casefold()

    def _fleet_tie_breaker(self, ship):
        return self._ship_name(ship).casefold(), self._fleet_ship_id_key(ship)

    def _sorted_fleet_ships(self, ships):
        sort_key = self.fleet_sort_combo.currentData() or "recent"
        direction = self.fleet_sort_direction_combo.currentData() or "descending"
        descending = direction == "descending"
        ordered = sorted(ships, key=self._fleet_tie_breaker)

        if sort_key == "recent":
            current = [ship for ship in ordered if ship.get("is_current")]
            remaining = [ship for ship in ordered if not ship.get("is_current")]
            known = [ship for ship in remaining if ship.get("last_seen")]
            missing = [ship for ship in remaining if not ship.get("last_seen")]
            known.sort(key=lambda ship: ship["last_seen"], reverse=descending)
            return current + known + missing

        field_names = {
            "name": None,
            "type": "ship_type",
            "jump_range": "max_jump_range",
            "cargo": "cargo_capacity",
            "mass": "unladen_mass",
            "location": None,
            "last_seen": "last_seen",
        }
        field = field_names.get(sort_key)

        def value(ship):
            if sort_key == "name":
                return self._ship_name(ship).casefold()
            if sort_key == "location":
                location = self._ship_location_key(ship)
                return location if location else None
            raw_value = ship.get(field) if field else None
            if raw_value in (None, ""):
                return None
            if sort_key in ("type", "last_seen"):
                return str(raw_value).casefold()
            return raw_value

        known = [ship for ship in ordered if value(ship) is not None]
        missing = [ship for ship in ordered if value(ship) is None]
        known.sort(key=value, reverse=descending)
        return known + missing

    @staticmethod
    def _ship_equipment(ship):
        return analyze_ship_modules(ship.get("modules") or [])

    def _filtered_fleet_ships(self, ships):
        filter_key = self.fleet_filter_combo.currentData() or "all"
        if filter_key == "all":
            return list(ships)

        def matches(ship):
            equipment = self._ship_equipment(ship)
            if filter_key == "vehicle_hangar":
                return equipment["vehicle_hangar"]
            if filter_key == "fighter_hangar":
                return equipment["fighter_hangar"]
            return True

        return [ship for ship in ships if matches(ship)]

    def _remember_visible_expanded_ship_ids(self):
        for index in range(self.fleet_layout.count()):
            card = self.fleet_layout.itemAt(index).widget()
            if card is None or card.property("shipId") is None:
                continue
            header = card.findChild(QToolButton)
            if header is not None and header.isChecked():
                self._expanded_ship_ids.add(card.property("shipId"))
            else:
                self._expanded_ship_ids.discard(card.property("shipId"))

    def _fleet_color(self, ship, is_live=False):
        dark_theme = self.palette().color(QPalette.Window).lightness() < 128
        if is_live:
            return QColor.fromHsv(125, 185 if dark_theme else 210, 205 if dark_theme else 145)
        key = self._ship_location_key(ship)
        if not key:
            return None
        digest = hashlib.sha256(key.encode("utf-8")).digest()
        # Grünbereich bleibt vollständig dem Live-Schiff vorbehalten.
        hue = int.from_bytes(digest[:2], "big") % 300
        if hue >= 85:
            hue += 60
        saturation = 145 + digest[2] % 55
        value = 225 if dark_theme else 155
        return QColor.fromHsv(hue, saturation, value)

    def _fleet_ship_widget(self, ship, is_live=False, expanded=False):
        card = QFrame(objectName="card")
        color = self._fleet_color(ship, is_live=is_live)
        card.setProperty("fleetColor", color.name() if color else "")
        card.setProperty("liveShip", bool(is_live))
        card.setProperty("locationKey", self._ship_location_key(ship))
        card.setProperty("shipId", ship.get("ship_id"))
        if color is not None:
            card.setStyleSheet(
                f"QFrame#card {{ border-left: 5px solid {color.name()}; }} "
                f"QFrame#card > QToolButton {{ color: {color.name()}; font-weight: 600; }}"
            )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        card.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        header = FleetHeader()
        row = QHBoxLayout(header)
        row.setContentsMargins(4, 4, 28, 4)
        picture = ShipImage(72, 52)
        picture.set_ship(ship.get("ship_type"), self._personal_ship_image(ship.get("ship_id")),
                         self._ship_display_title(ship))
        row.addWidget(picture)
        text = QVBoxLayout()
        text.setSpacing(2)
        row.addLayout(text, 1)
        title = ElidedShipLabel(self._ship_display_title(ship))
        font = title.font()
        font.setBold(True)
        title.setFont(font)
        text.addWidget(title)
        marker = f" · {tr('commander_view.fleet.current_marker')}" if ship["is_current"] else ""
        text.addWidget(ElidedShipLabel(ship_display_name(ship.get("ship_type")) + marker))
        location = self._ship_location(ship)
        text.addWidget(ElidedShipLabel(f"{tr('commander_view.ship.location')}: {location}"))
        header.setAccessibleName(f"{title.text()} · {ship_display_name(ship.get('ship_type'))} · {location}{marker}")
        header.setToolTip(header.accessibleName())
        for child in header.findChildren(QWidget):
            child.setAttribute(Qt.WA_TransparentForMouseEvents, not isinstance(child, ShipImage))
        layout.addWidget(header)
        details = QWidget()
        form = QFormLayout(details)
        form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        actions = QWidget()
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        select_image = QPushButton(tr("commander_view.ship.image.select"))
        remove_image = QPushButton(tr("commander_view.ship.image.remove"))
        fid, ship_id = self._ship_image_fid, ship.get("ship_id")
        select_image.setEnabled(bool(fid) and ship_id is not None)
        remove_image.setEnabled(self._personal_ship_image(ship_id) is not None)
        select_image.clicked.connect(lambda _checked=False: self._select_ship_image(fid, ship_id))
        remove_image.clicked.connect(lambda _checked=False: self._remove_ship_image(fid, ship_id))
        actions_layout.addWidget(select_image)
        actions_layout.addWidget(remove_image)
        delete_ship = QPushButton(tr("commander_view.ship.delete.button"))
        delete_ship.setObjectName("deleteFleetShip")
        delete_ship.setStyleSheet("QPushButton:enabled { color: #e87979; }")
        protected = ship_id == self._protected_ship_id or self._is_live_ship(self._fleet_commander_id, ship_id)
        delete_ship.setEnabled(not protected and self._fleet_rebuild_id is None)
        if protected:
            delete_ship.setToolTip(tr("commander_view.ship.delete.active"))
        commander_id = self._fleet_commander_id
        delete_ship.clicked.connect(lambda _checked=False: self._delete_ship(commander_id, fid, ship))
        actions_layout.addWidget(delete_ship)
        actions_layout.addStretch()
        form.addRow(actions)
        boosters = ", ".join(
            item.get("item") or "" for item in ship.get("guardian_fsd_boosters", [])
            if item.get("item")
        ) or "–"
        status = (
            tr("commander_view.ship.status.stale") if ship["loadout_stale"]
            else tr("commander_view.ship.status.complete") if ship["loadout_complete"]
            else tr("commander_view.ship.status.incomplete")
        )
        equipment = self._ship_equipment(ship)
        has_module_data = bool(ship.get("modules"))
        vehicles = equipment["vehicle_hangar_item"] or (
            tr("commander_view.ship.hangar_present")
            if has_module_data and equipment["vehicle_hangar"] else "–"
        )
        fighters = equipment["fighter_hangar_item"] or (
            tr("commander_view.ship.hangar_present")
            if has_module_data and equipment["fighter_hangar"] else "–"
        )
        shield_parts = [equipment["shield_generator"]]
        shield_engineering = equipment["shield_engineering"]
        if shield_engineering:
            blueprint = str(shield_engineering.get("BlueprintName") or "").strip()
            level = shield_engineering.get("Level")
            if blueprint:
                shield_parts.append(blueprint)
            if level not in (None, ""):
                shield_parts.append(f"L{level}")
        shield_generator = " · ".join(part for part in shield_parts if part)
        fields = (
            (tr("commander_view.ship.ship_ident"), ship.get("ship_ident")),
            (tr("commander_view.ship.ship_id"), ship.get("ship_id")),
            (tr("commander_view.ship.location"), self._ship_location(ship)),
            (tr("commander_view.ship.last_seen"), ship.get("last_seen")),
            (tr("commander_view.ship.max_jump_range"), ship.get("max_jump_range")),
            (tr("commander_view.ship.fsd_item"), ship.get("fsd_item")),
            (tr("commander_view.ship.guardian_booster"), boosters),
            (tr("commander_view.ship.unladen_mass"), ship.get("unladen_mass")),
            (tr("commander_view.ship.cargo_capacity"), ship.get("cargo_capacity")),
            (tr("commander_view.ship.main_tank_capacity"), ship.get("main_tank_capacity")),
            (tr("commander_view.ship.reserve_tank_capacity"), ship.get("reserve_tank_capacity")),
            (tr("commander_view.ship.loadout_timestamp"), ship.get("loadout_timestamp")),
            (tr("commander_view.ship.loadout_status"), status),
            (tr("commander_view.ship.vehicles"), vehicles),
            (tr("commander_view.ship.fighter_hangar"), fighters),
            (tr("commander_view.ship.shield_generator"),
             shield_generator if has_module_data else None),
            (tr("commander_view.ship.shield_boosters"),
             equipment["shield_boosters"] if has_module_data else None),
            (tr("commander_view.ship.guardian_shield_reinforcements"),
             equipment["guardian_shield_reinforcements"] if has_module_data else None),
            (tr("commander_view.ship.weapons"),
             equipment["weapons"] if has_module_data else None),
            (tr("commander_view.ship.hull_reinforcements"),
             equipment["hull_reinforcements"] if has_module_data else None),
            (tr("commander_view.ship.module_reinforcements"),
             equipment["module_reinforcements"] if has_module_data else None),
            (tr("commander_view.ship.passenger_cabins"),
             equipment["passenger_cabins"] if has_module_data else None),
        )
        for title, value in fields:
            form.addRow(title, ElidedShipLabel(str(value) if value not in (None, "") else "–"))
        details.setVisible(False)
        header.toggled.connect(details.setVisible)
        header.toggled.connect(lambda checked, button=header: button.setArrowType(
            Qt.DownArrow if checked else Qt.RightArrow
        ))
        layout.addWidget(details)
        header.setChecked(expanded)
        return card

    def _personal_ship_image(self, ship_id):
        return personal_ship_image(self.state.settings, self._ship_image_fid, ship_id)

    def _select_carrier_image(self):
        identity = self._carrier_image_identity
        if identity is None:
            return
        filename, _filter = QFileDialog.getOpenFileName(
            self, tr("commander_view.carrier.image.select"), "",
            f"{tr('commander_view.ship.image.filter')} ({IMAGE_NAME_PATTERNS})",
        )
        if not filename:
            return
        try:
            import_carrier_image(self.state.settings, *identity, filename)
        except (OSError, ValueError):
            QMessageBox.warning(self, tr("commander_view.carrier.image.select"),
                                tr("commander_view.carrier.image.error"))
            return
        self._refresh_ship_for_current_commander()

    def _remove_carrier_image(self):
        if self._carrier_image_identity is None:
            return
        try:
            remove_carrier_image(self.state.settings, *self._carrier_image_identity)
        except (OSError, ValueError):
            QMessageBox.warning(self, tr("commander_view.ship.image.remove"),
                                tr("commander_view.carrier.image.error"))
            return
        self._refresh_ship_for_current_commander()

    def _select_ship_image(self, fid, ship_id):
        filename, _filter = QFileDialog.getOpenFileName(
            self, tr("commander_view.ship.image.select"), "",
            f"{tr('commander_view.ship.image.filter')} ({IMAGE_NAME_PATTERNS})",
        )
        if not filename:
            return
        try:
            import_ship_image(self.state.settings, fid, ship_id, filename)
        except (OSError, ValueError):
            QMessageBox.warning(self, tr("commander_view.ship.image.select"),
                                tr("commander_view.ship.image.error"))
            return
        self._refresh_ship_for_current_commander()

    def _remove_ship_image(self, fid, ship_id):
        try:
            remove_ship_image(self.state.settings, fid, ship_id)
        except (OSError, ValueError):
            QMessageBox.warning(self, tr("commander_view.ship.image.remove"),
                                tr("commander_view.ship.image.error"))
            return
        self._refresh_ship_for_current_commander()

    def _is_live_ship(self, commander_id, ship_id):
        return (commander_id == self.state.commander_id
                and getattr(getattr(self.state, "ship_loadout", None), "ship_id", None) == ship_id)

    def _confirm_fleet_action(self, title, body, action, destructive=False):
        dialog = QMessageBox(QMessageBox.Warning, title, body, parent=self)
        dialog.setTextFormat(Qt.PlainText)
        cancel = dialog.addButton(tr("migration.cancel"), QMessageBox.RejectRole)
        confirm = dialog.addButton(action, QMessageBox.DestructiveRole if destructive else QMessageBox.AcceptRole)
        if destructive:
            confirm.setStyleSheet("color: #e87979;")
        dialog.setDefaultButton(cancel)
        dialog.setEscapeButton(cancel)
        dialog.exec()
        return dialog.clickedButton() is confirm

    def _delete_ship(self, commander_id, fid, ship):
        ship_id = ship["ship_id"]
        if self._fleet_rebuild_id is not None:
            return
        if ship.get("is_current") or self._is_live_ship(commander_id, ship_id):
            QMessageBox.warning(self, tr("commander_view.ship.delete.title"), tr("commander_view.ship.delete.active"))
            return
        if not self._confirm_fleet_action(
            tr("commander_view.ship.delete.title"),
            tr("commander_view.ship.delete.body", name=self._ship_display_title(ship),
               ship_type=ship_display_name(ship.get("ship_type")), ship_id=ship_id),
            tr("commander_view.ship.delete.confirm"), destructive=True,
        ):
            return
        try:
            with reversible_image_removal(self.state.settings, fid, ship_id) as cleanup:
                self.state.database.delete_commander_ship(
                    commander_id, ship_id, before_commit=cleanup,
                    live_ship_id=(getattr(getattr(self.state, "ship_loadout", None), "ship_id", None)
                                  if commander_id == self.state.commander_id else None),
                )
        except (sqlite3.Error, OSError, ValueError, RuntimeError) as exc:
            key = "active" if str(exc) == "active_ship" else "error"
            QMessageBox.warning(self, tr("commander_view.ship.delete.title"), tr("commander_view.ship.delete." + key))
            return
        self._expanded_ship_ids.discard(ship_id)
        self._refresh_ship_for_current_commander()

    def _request_fleet_rebuild(self):
        if self._fleet_rebuild_id is not None:
            return
        commander_id = self._fleet_commander_id
        if commander_id is None or not self._confirm_fleet_action(
            tr("commander_view.fleet.rebuild.title"), tr("commander_view.fleet.rebuild.body"),
            tr("commander_view.fleet.rebuild.confirm"),
        ):
            return
        try:
            with self.state.database._connect() as con:
                paths = {Path(row[0]) for row in con.execute(
                    "SELECT journal_file FROM journal_sessions WHERE commander_id=?", (commander_id,)
                ) if Path(row[0]).is_file()}
            folder = getattr(self.state, "journal_folder", None)
            if folder:
                paths.update(journal_files(Path(folder)))
            if not paths:
                raise ValueError("No journals available")
            task = FleetReadTask(paths, self._ship_image_fid)
        except (OSError, ValueError, sqlite3.Error):
            self.fleet_action_status.setText(tr("commander_view.fleet.rebuild.error"))
            return
        self._fleet_rebuild_id = commander_id
        self._fleet_read_task = task
        task.signals.done.connect(self._fleet_rebuild_finished, Qt.QueuedConnection)
        self.fleet_action_status.setText(tr("commander_view.fleet.rebuild.running"))
        self._refresh_ship_for_current_commander()
        QThreadPool.globalInstance().start(task)

    def _fleet_rebuild_finished(self, fleet, error):
        commander_id = self._fleet_rebuild_id
        try:
            if error or commander_id is None:
                raise ValueError(error)
            self.state.database.rebuild_commander_fleet(
                commander_id, fleet,
                live_ship_id=(getattr(getattr(self.state, "ship_loadout", None), "ship_id", None)
                              if commander_id == self.state.commander_id else None),
            )
        except (OSError, ValueError, sqlite3.Error):
            self.fleet_action_status.setText(tr("commander_view.fleet.rebuild.error"))
        else:
            self.fleet_action_status.setText(tr("commander_view.fleet.rebuild.done"))
        finally:
            self._fleet_rebuild_id = None
            self._fleet_read_task = None
            self._refresh_ship_for_current_commander()
