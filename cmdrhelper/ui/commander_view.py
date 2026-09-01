from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QVBoxLayout,
    QWidget,
)

from cmdrhelper.i18n import tr
from cmdrhelper.mission_manager import translate_mission_text


class CommanderView(QWidget):
    """Rein lesende Offline-/Live-Übersicht bekannter Commanderprofile."""

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
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
        layout = QVBoxLayout(tab)
        layout.addWidget(QLabel(tr("commander_view.ship.title"), objectName="sectionTitle"))
        ship_card = QFrame(objectName="card")
        ship_form = QFormLayout(ship_card)
        self.ship_values = {}
        ship_fields = (
            ("ship_id", tr("commander_view.ship.ship_id")),
            ("ship_type", tr("commander_view.ship.ship_type")),
            ("ship_name", tr("commander_view.ship.ship_name")),
            ("ship_ident", tr("commander_view.ship.ship_ident")),
            ("loadout_timestamp", tr("commander_view.ship.loadout_timestamp")),
            ("max_jump_range", tr("commander_view.ship.max_jump_range")),
            ("unladen_mass", tr("commander_view.ship.unladen_mass")),
            ("cargo_capacity", tr("commander_view.ship.cargo_capacity")),
            ("main_tank_capacity", tr("commander_view.ship.main_tank_capacity")),
            ("reserve_tank_capacity", tr("commander_view.ship.reserve_tank_capacity")),
            ("fsd_item", tr("commander_view.ship.fsd_item")),
            ("guardian_booster", tr("commander_view.ship.guardian_booster")),
            ("loadout_status", tr("commander_view.ship.loadout_status")),
        )
        for field, label in ship_fields:
            value = QLabel("–")
            value.setWordWrap(True)
            self.ship_values[field] = value
            ship_form.addRow(label, value)
        layout.addWidget(ship_card)

        layout.addWidget(QLabel(tr("commander_view.carrier.title"), objectName="sectionTitle"))
        carrier_card = QFrame(objectName="card")
        carrier_form = QFormLayout(carrier_card)
        self.carrier_values = {}
        for field, label in (
            ("name", tr("commander_view.carrier.name")),
            ("callsign", tr("commander_view.carrier.callsign")),
            ("carrier_id", tr("commander_view.carrier.carrier_id")),
            ("location", tr("commander_view.carrier.location")),
            ("last_updated", tr("commander_view.carrier.last_updated")),
        ):
            value = QLabel("–")
            self.carrier_values[field] = value
            carrier_form.addRow(label, value)
        layout.addWidget(carrier_card)
        layout.addStretch()
        return tab

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

    def refresh(self, *args):
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

        summary = self.state.database.commander_summary(viewed_id)
        if summary is None:
            self.identity_label.setText("–")
            self.status_label.setText("–")
            self.status_label.setObjectName("muted")
            for value in self.values.values():
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
        ship = summary.get("ship") if summary else None
        for field, label in self.ship_values.items():
            value = ship.get(field) if ship else None
            if field == "guardian_booster":
                value = ", ".join(
                    item.get("item") or ""
                    for item in (ship.get("guardian_fsd_boosters") if ship else [])
                    if item.get("item")
                )
            elif field == "loadout_status":
                value = (
                    tr("commander_view.ship.status.stale") if ship and ship["loadout_stale"]
                    else tr("commander_view.ship.status.complete") if ship and ship["loadout_complete"]
                    else tr("commander_view.ship.status.incomplete") if ship else "–"
                )
            label.setText(str(value) if value not in (None, "") else "–")

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
