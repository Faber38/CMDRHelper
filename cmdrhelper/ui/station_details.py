"""Non-modal facility details using the existing CMDRHelper image viewer."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QFrame, QLabel, QListWidget, QScrollArea, QWidget, QGridLayout
from cmdrhelper.i18n import tr
from cmdrhelper.ui.ship_widgets import ShipImage
from cmdrhelper.ui.station_assets import station_preview
from cmdrhelper.ui.system_theme import THEMES


def apply_theme(dialog, light):
    theme = THEMES[bool(light)]
    dialog.setStyleSheet(f"""
        QDialog, QListWidget {{ background: {theme['background']}; color: {theme['text']}; }}
        QFrame#facilityPanel {{ background: {theme['background']}; border: 1px solid {theme['selected']}; border-radius: 8px; }}
        QLabel {{ color: {theme['text']}; background: transparent; border: none; }}
        QListWidget {{ border: 1px solid {theme['selected']}; padding: 8px; }}
        QLabel#serviceChip {{ border: 1px solid {theme["line"]}; border-radius: 5px; padding: 5px; }}
        QScrollArea {{ border: none; background: {theme["background"]}; }}
        QListWidget::item {{ padding: 10px; }}
        QListWidget::item:selected {{ background: {theme['selected']}; color: {theme['background']}; }}
    """)


class StationDetailDialog(QDialog):
    def __init__(self, station, system_name, parent=None, *, light=False):
        super().__init__(parent)
        from cmdrhelper.ui.station_items import type_key
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle(station.get('station_name') or tr('facilities.station'))
        self.resize(720, 630)
        apply_theme(self, light)
        root = QVBoxLayout(self)
        panel = QFrame(objectName='facilityPanel')
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(panel)
        root.addWidget(scroll)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        self.image = ShipImage(640, 300, preview_resolver=station_preview)
        self.image.set_ship(station, ship_name=self.windowTitle())
        layout.addWidget(self.image, alignment=Qt.AlignCenter)
        self.details = StationDetailsWidget(station, system_name, light=light)
        layout.addWidget(self.details)
        # Preserve the existing dialog API used by callers and UI checks.
        for name in ('name_label', 'info', 'external_info', 'service_labels', 'external_dates'):
            setattr(self, name, getattr(self.details, name))


class StationDetailsWidget(QWidget):
    """Shared station fields for the map dialog and expandable Explorer cards."""
    def __init__(self, station, system_name, parent=None, *, light=False):
        super().__init__(parent)
        from cmdrhelper.ui.station_items import type_key
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.name_label = QLabel(station.get('station_name') or tr('facilities.station'))
        self.name_label.setTextFormat(Qt.PlainText)
        self.name_label.setWordWrap(True)
        font = self.name_label.font(); font.setPointSize(18); font.setBold(True)
        self.name_label.setFont(font)
        layout.addWidget(self.name_label)
        fields = []
        if station.get('station_type') or station.get('is_planetary'):
            kind = tr('facilities.' + type_key(station))
            if station.get('station_type'):
                kind += ' (' + station['station_type'] + ')'
            fields.append((tr('facilities.type'), kind))
        fields += [(tr('facilities.system'), system_name),
                   (tr('facilities.parent'), station.get('body_name') if station.get('parent_body_id') is not None else None),
                   ('MarketID', station.get('market_id')),
                   (tr('facilities.updated'), station.get('last_seen')),
                   (tr('facilities.source'), station.get('source'))]
        self.info = QLabel('\n'.join(f'{key}: {value}' for key, value in fields if value is not None and value != ''))
        self.info.setTextFormat(Qt.PlainText)
        self.info.setWordWrap(True)
        self.info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        font = self.info.font(); font.setPointSize(11); self.info.setFont(font)
        layout.addWidget(self.info)
        external = station.get('spansh') or {}
        extra_fields = []
        for key in ('distance_ls', 'allegiance', 'government', 'controlling_faction',
                    'primary_economy', 'secondary_economy'):
            value = external.get(key)
            if value is not None:
                shown = f"{value:,.1f} ls" if key == 'distance_ls' else str(value)
                extra_fields.append(f"{tr('spansh.' + key)}: {shown}")
        economies = external.get('economies') or {}
        if economies:
            # Spansh values can exceed 100; do not mislabel them as percentages.
            extra_fields.append(tr('spansh.economies') + ': ' + ', '.join(
                f'{name}: {amount:g}' for name, amount in economies.items()))
        pads = external.get('landing_pads') or {}
        if pads:
            extra_fields.append(tr('spansh.pads') + ': ' + '   '.join(
                f'{short}: {pads[key]}' for key,short in [('large','L'),('medium','M'),('small','S')] if key in pads))
        self.external_info = QLabel('\n'.join(extra_fields))
        self.external_info.setTextFormat(Qt.PlainText)
        self.external_info.setWordWrap(True)
        self.external_info.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.external_info)
        self.service_labels = []
        if external.get('services'):
            layout.addWidget(QLabel(tr('spansh.services')))
            chips = QWidget()
            grid = QGridLayout(chips)
            grid.setContentsMargins(0, 0, 0, 0)
            for index, service in enumerate(external['services']):
                chip = QLabel(tr('spansh.service.' + service), objectName='serviceChip')
                chip.setTextFormat(Qt.PlainText)
                chip.setWordWrap(True)
                grid.addWidget(chip, index // 3, index % 3)
                self.service_labels.append(chip)
            layout.addWidget(chips)
        dates = []
        for key in ('station_updated_at','source_updated_at','fetched_at'):
            if external.get(key): dates.append(tr('spansh.' + key) + ': ' + external[key])
        self.external_dates = QLabel('\n'.join(dates))
        self.external_dates.setTextFormat(Qt.PlainText)
        self.external_dates.setWordWrap(True)
        self.external_dates.setStyleSheet(f"color: {THEMES[bool(light)]['muted']};")
        layout.addWidget(self.external_dates)


    def set_light_mode(self, light):
        self.external_dates.setStyleSheet(f"color: {THEMES[bool(light)]['muted']};")


class StationSelectionDialog(QDialog):
    def __init__(self, stations, system_name, parent=None, *, light=False):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowTitle(tr('facilities.group', count=len(stations)))
        self.resize(560, 420)
        apply_theme(self, light)
        layout = QVBoxLayout(self)
        self.listing = QListWidget()
        self.listing.addItems([s.get('station_name') or tr('common.unknown') for s in stations])
        layout.addWidget(self.listing)
        self._details = None

        def open_station(item):
            if self._details is not None:
                self._details.close()
            detail = StationDetailDialog(stations[self.listing.row(item)], system_name, self, light=light)
            self._details = detail
            detail.destroyed.connect(lambda: setattr(self, '_details', None)
                                     if self._details is detail else None)
            detail.show()
        self.listing.itemClicked.connect(open_station)
        self.listing.itemActivated.connect(open_station)
