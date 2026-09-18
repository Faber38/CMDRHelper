"""Local Explorer projection of the existing merged station display model."""
from copy import deepcopy

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox,
    QScrollArea, QLabel, QSizePolicy,
)

from cmdrhelper.i18n import tr, get_language
from cmdrhelper.ui.ship_widgets import ShipImage, FleetHeader, ElidedShipLabel
from cmdrhelper.ui.station_assets import station_preview
from cmdrhelper.ui.station_details import StationDetailsWidget
from cmdrhelper.ui.station_items import type_key
from cmdrhelper.ui.system_theme import THEMES


def parent_label(station, system_name):
    if station.get('parent_body_id') is None:
        return tr('common.unknown')
    name = station.get('body_name') or str(station['parent_body_id'])
    prefix = system_name + ' '
    return name[len(prefix):] if name.startswith(prefix) else name


def distance(station):
    value = (station.get('spansh') or {}).get('distance_ls')
    return value if isinstance(value, (int, float)) else None


def station_key(station):
    return station.get('identity') or station.get('market_id')


class StationCard(QFrame):
    def __init__(self, station, system_name, *, light=False, expanded=False):
        super().__init__(objectName='stationCard')
        self.station, self.system_name, self.light = station, system_name, light
        self.details = None
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(8, 4, 8, 4)
        self.header = FleetHeader()
        self.header.setMinimumHeight(96)
        row = QHBoxLayout(self.header)
        row.setContentsMargins(4, 4, 28, 4)
        self.image = ShipImage(112, 76, preview_resolver=station_preview)
        name = station.get('station_name') or tr('common.unknown')
        self.image.set_ship(station, ship_name=name)
        row.addWidget(self.image)
        text = QVBoxLayout()
        text.setSpacing(2)
        row.addLayout(text, 1)
        self.title = ElidedShipLabel(name)
        font = self.title.font(); font.setBold(True); self.title.setFont(font)
        text.addWidget(self.title)
        text.addWidget(ElidedShipLabel(
            tr('facilities.' + type_key(station)) + ' · ' + parent_label(station, system_name)))
        external = station.get('spansh') or {}
        summary = []
        if distance(station) is not None:
            summary.append(f'{distance(station):,.1f} ls')
        summary.extend(str(external[k]) for k in ('primary_economy', 'controlling_faction') if external.get(k))
        if summary:
            text.addWidget(ElidedShipLabel(' · '.join(summary)))
        services = external.get('services') or []
        if services:
            priority = ('market', 'repair', 'refuel')
            ordered = [key for key in priority if key in services]
            ordered.extend(key for key in services if key not in priority)
            short = [tr('spansh.service.' + key) for key in ordered[:3]]
            if len(services) > 3:
                short.append(f'+{len(services) - 3}')
            text.addWidget(ElidedShipLabel(' · '.join(short)))
        for child in self.header.findChildren(QWidget):
            child.setAttribute(Qt.WA_TransparentForMouseEvents, not isinstance(child, ShipImage))
        self.header.setAccessibleName(name)
        self.card_layout.addWidget(self.header)
        self.header.toggled.connect(self._toggle)
        self.header.setChecked(expanded)

    def _toggle(self, expanded):
        if expanded and self.details is None:
            self.details = StationDetailsWidget(self.station, self.system_name, light=self.light)
            self.card_layout.addWidget(self.details)
        if self.details is not None:
            self.details.setVisible(expanded)
        self.header.setArrowType(Qt.DownArrow if expanded else Qt.RightArrow)

    def set_light_mode(self, light):
        self.light = light
        if self.details is not None:
            self.details.set_light_mode(light)


class StationsView(QWidget):
    def __init__(self, parent=None, *, light=False, spansh=None):
        super().__init__(parent)
        self.setObjectName('stationsView')
        self.stations, self.cards = [], []
        self.system_address, self.system_name = None, ''
        self.language = get_language()
        self._model_key = None
        self._spansh = spansh
        self._spansh_active = bool(spansh and spansh.active)
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        self.local_notice = QLabel(objectName='stationLocalNotice')
        self.local_notice.setWordWrap(True)
        self.local_notice.setTextFormat(Qt.PlainText)
        root.addWidget(self.local_notice)
        filters = QHBoxLayout()
        self.search = QLineEdit()
        filters.addWidget(self.search, 2)
        self.type_filter, self.body_filter, self.sort_order = QComboBox(), QComboBox(), QComboBox()
        for control in (self.type_filter, self.body_filter, self.sort_order):
            control.setMinimumContentsLength(10)
            control.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
            filters.addWidget(control, 1)
        root.addLayout(filters)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.content = QWidget(objectName='stationList')
        self.list_layout = QVBoxLayout(self.content)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.empty = QLabel()
        self.empty.setWordWrap(True)
        self.list_layout.addWidget(self.empty)
        self.list_layout.addStretch()
        self.scroll.setWidget(self.content)
        root.addWidget(self.scroll)
        self._translate_controls()
        self.search.textChanged.connect(self._filter)
        self.type_filter.currentIndexChanged.connect(self._filter)
        self.body_filter.currentIndexChanged.connect(self._filter)
        self.sort_order.currentIndexChanged.connect(self._filter)
        self.set_light_mode(light)
        self._filter()
        self.local_notice.setVisible(not self._spansh_active)
        if spansh is not None:
            spansh.activityChanged.connect(self._sync_spansh_notice)

    def _sync_spansh_notice(self):
        active = bool(self._spansh and self._spansh.active)
        if active == self._spansh_active:
            return
        self._spansh_active = active
        self.local_notice.setVisible(not active)
        self._update_empty_text()

    @property
    def tab_title(self):
        return tr('stations.tab', count=len(self.stations))

    def _translate_controls(self):
        self.local_notice.setText(tr('stations.local_notice') + '\n' + tr('stations.local_notice_settings'))
        self.search.setPlaceholderText(tr('stations.search'))
        self.search.setAccessibleName(tr('stations.search'))
        for control, label in ((self.type_filter, tr('facilities.type')),
                               (self.body_filter, tr('facilities.parent')),
                               (self.sort_order, tr('commander_view.fleet.sort_by'))):
            control.setAccessibleName(label)
            control.setToolTip(label)
        for control in (self.type_filter, self.sort_order):
            control.blockSignals(True)
        old_type, old_sort = self.type_filter.currentData(), self.sort_order.currentData()
        self.type_filter.clear()
        self.type_filter.addItem(tr('favorites.all_types'), 'all')
        for key in ('orbital', 'outpost', 'surface', 'settlement', 'megaship', 'carrier', 'station'):
            self.type_filter.addItem(tr('facilities.other' if key == 'station' else 'facilities.' + key), key)
        self.sort_order.clear()
        for key, label in [('name', 'favorites.name'), ('type', 'facilities.type'),
                           ('body', 'facilities.parent'), ('distance', 'spansh.distance_ls')]:
            self.sort_order.addItem(tr(label), key)
        for control, value in ((self.type_filter, old_type), (self.sort_order, old_sort)):
            control.setCurrentIndex(max(0, control.findData(value)))
            control.blockSignals(False)

    def set_system(self, system_address, system_name, stations):
        # No DB access, cache reads, or network calls: consume the supplied model only.
        key = (system_address, system_name, stations, get_language())
        if key == self._model_key:
            return
        changed_system = (system_address, system_name) != (self.system_address, self.system_name)
        self._model_key = deepcopy(key)
        expanded = {station_key(c.station) for c in self.cards if c.header.isChecked()} if not changed_system else set()
        old_body = self.body_filter.currentData()
        for control in (self.search, self.type_filter, self.body_filter, self.sort_order):
            control.blockSignals(True)
        if changed_system:
            self.search.clear()
            self.type_filter.setCurrentIndex(0)
            old_body = 'all'
        self.system_address, self.system_name = system_address, system_name or ''
        self.stations = deepcopy(list(stations or []))
        if self.language != get_language():
            self.language = get_language()
            self._translate_controls()
        self.body_filter.clear()
        self.body_filter.addItem(tr('stations.all_bodies'), 'all')
        parents = {s['parent_body_id']: parent_label(s, self.system_name)
                   for s in self.stations if s.get('parent_body_id') is not None}
        for body_id, label in sorted(parents.items(), key=lambda item: item[1].casefold()):
            self.body_filter.addItem(label, body_id)
        if any(s.get('parent_body_id') is None for s in self.stations):
            self.body_filter.addItem(tr('common.unknown'), 'unknown')
        self.body_filter.setCurrentIndex(max(0, self.body_filter.findData(old_body)))
        for card in self.cards:
            self.list_layout.removeWidget(card)
            card.hide()
            card.deleteLater()
        self.cards = [StationCard(s, self.system_name, light=self.light, expanded=station_key(s) in expanded)
                      for s in self.stations]
        for card in self.cards:
            self.list_layout.insertWidget(self.list_layout.count() - 1, card)
        for control in (self.search, self.type_filter, self.body_filter, self.sort_order):
            control.blockSignals(False)
        self._filter()
        if changed_system:
            self.scroll.verticalScrollBar().setValue(0)

    def _filter(self, *_):
        query = self.search.text().strip().casefold()
        kind, body, order = self.type_filter.currentData(), self.body_filter.currentData(), self.sort_order.currentData()
        def sort_key(card):
            station = card.station
            name = str(station.get('station_name') or '').casefold()
            if order == 'distance':
                value = distance(station)
                return (value is None, value if value is not None else 0, name)
            if order == 'body':
                return (station.get('parent_body_id') is None, parent_label(station, self.system_name).casefold(), name)
            if order == 'type':
                return (tr('facilities.' + type_key(station)).casefold(), name)
            return (name,)
        self.cards.sort(key=sort_key)
        visible = 0
        self.content.setUpdatesEnabled(False)
        for card in self.cards:
            station = card.station
            parent = station.get('parent_body_id')
            match = (query in str(station.get('station_name') or '').casefold()
                     and (kind == 'all' or kind == type_key(station))
                     and (body in (None, 'all') or (body == 'unknown' and parent is None) or body == parent))
            self.list_layout.removeWidget(card)
            self.list_layout.insertWidget(self.list_layout.count() - 1, card)
            card.setVisible(match)
            visible += bool(match)
        self._update_empty_text()
        self.empty.setVisible(not visible)
        self.content.setUpdatesEnabled(True)

    def _update_empty_text(self):
        key = 'stations.no_matches' if self.stations else (
            'stations.empty' if self._spansh_active else 'stations.empty_local')
        self.empty.setText(tr(key))

    def set_light_mode(self, light):
        self.light = bool(light)
        theme = THEMES[self.light]
        self.setStyleSheet(f"""
            QWidget#stationsView, QWidget#stationList {{ background: {theme['background']}; }}
            QLabel#stationLocalNotice {{ background: #080d12; color: #d8dde3; border: 1px solid #ffb34f; border-radius: 5px; padding: 7px 9px; }}
            QFrame#stationCard {{ background: {theme['background']}; border: 1px solid {theme['selected']}; border-radius: 6px; }}
            QFrame#stationCard QLabel {{ color: {theme['text']}; border: none; background: transparent; }}
            QFrame#stationCard QToolButton {{ color: {theme['text']}; border: none; background: transparent; }}
            QFrame#stationCard QToolButton:hover {{ background: {theme['line']}; }}
            QFrame#stationCard QLabel#serviceChip {{ border: 1px solid {theme['line']}; border-radius: 5px; padding: 4px; }}
        """)
        for card in self.cards:
            card.set_light_mode(self.light)
