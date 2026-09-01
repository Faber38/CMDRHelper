from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from cmdrhelper.i18n import tr


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
        for title in (
            tr("commander_view.tab.missions"),
            tr("commander_view.tab.exploration"),
            tr("commander_view.tab.chronicle"),
            tr("commander_view.tab.ships"),
        ):
            self.tabs.addTab(self._placeholder(), title)
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
        )
        for field, label in fields:
            value = QLabel("–")
            value.setWordWrap(True)
            self.values[field] = value
            form.addRow(label, value)
        layout.addWidget(card)
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
        location = summary["last_location"]
        self.values["last_location"].setText(
            (location.get("system_name") or "–") if location else "–"
        )
