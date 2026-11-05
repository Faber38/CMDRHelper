"""Presentation of mission quantities from verified personal ship cargo only."""
from functools import lru_cache
from dataclasses import dataclass

from PySide6.QtCore import QEvent, QLocale, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QGridLayout, QLabel, QStyledItemDelegate, QWidget

from cmdrhelper.commodity_master import lookup_by_symbol
from cmdrhelper.i18n import get_language, tr
from cmdrhelper.ship_cargo import current_ship_inventory


MISSION_CARGO_ROLE = Qt.UserRole + 74


def current_mission_cargo(state):
    """Map commodity IDs to (mission tonnes, total tonnes, mission count).

    Revalidate instead of trusting a cached ship_inventory or a signal payload:
    those may still describe the previous commander, vessel or generation.
    """
    viewed = getattr(state, 'viewed_commander_id', None)
    if ((viewed is not None and viewed != getattr(state, 'commander_id', None))
            or (getattr(state, 'sources', None) is not None
                and not getattr(state, '_source_live_context', False))):
        return {}
    snapshot = current_ship_inventory(state)
    result = {}
    for row in (snapshot or {}).get('inventory', []):
        missions = row.get('mission_counts') or {}
        if not isinstance(missions, dict) or not missions:
            continue
        if any(type(mid) is not int or mid <= 0 or type(count) is not int or count <= 0
               for mid, count in missions.items()):
            continue
        amount = sum(missions.values())
        master = lookup_by_symbol(row['frontier_name'])
        if master and 0 < amount <= row['count']:
            result[master.frontier_id] = (amount, row['count'], len(missions))
    return result


POSSIBLE_MISSION_CARGO_ROLE = Qt.UserRole + 75
CARGO_BASE_TOOLTIP_ROLE = Qt.UserRole + 76
CARGO_COMMODITY_ROLE = Qt.UserRole + 77


@dataclass(frozen=True)
class PossibleMissionCargo:
    total: int
    available: int
    remaining: int
    coverable: int
    known_missions: int
    unknown_required: int
    unknown_missions: int


def current_possible_mission_cargo(state):
    """Shared stock, not an allocation or a claim that Elite accepts the goods.

    state.missions contains the active commander's open missions plus offers.
    Unknown delivery counters remain unknown, including for newly accepted jobs.
    """
    from cmdrhelper.mission_manager import is_goods_mission
    viewed = getattr(state, 'viewed_commander_id', None)
    if ((viewed is not None and viewed != getattr(state, 'commander_id', None))
            or (getattr(state, 'sources', None) is not None
                and not getattr(state, '_source_live_context', False))):
        return {}
    # Cheap mission-only gate: no extra cargo validation without an eligible
    # confirmed open goods mission. Blue MissionID handling is independent.
    by_commodity, seen = {}, set()
    for mission in getattr(state, 'missions', ()):
        mid = mission.mission_id
        if (type(mid) is not int or mid <= 0 or mid in seen
                or mission.extra.get('pending_offer') or not is_goods_mission(mission)):
            continue
        seen.add(mid)
        master = lookup_by_symbol(mission.commodity_symbol)
        total, delivered = mission.required_count, mission.delivered_count
        if (master is None or type(total) is not int or total <= 0
                or (delivered is not None and
                    (type(delivered) is not int or not 0 <= delivered <= total))):
            continue
        if delivered == total:
            continue
        by_commodity.setdefault(master.frontier_id, []).append(mission)
    if not by_commodity:
        return {}
    snapshot = current_ship_inventory(state)
    if snapshot is None:
        return {}
    result = {}
    for row in snapshot['inventory']:
        master = lookup_by_symbol(row['frontier_name'])
        bound = row.get('mission_counts') or {}
        if (master is None or not isinstance(bound, dict)
                or any(type(mid) is not int or mid <= 0 or type(n) is not int or n <= 0
                       for mid, n in bound.items())):
            continue
        available = row['count'] - sum(bound.values())
        if available <= 0:
            continue
        remaining = uncovered = known = unknown_total = unknown = 0
        for mission in by_commodity.get(master.frontier_id, ()):
            if mission.delivered_count is None:
                unknown_total += mission.required_count
                unknown += 1
            else:
                rest = mission.required_count - mission.delivered_count
                need = max(0, rest - bound.get(mission.mission_id, 0))
                remaining += rest
                uncovered += need
                known += 1
        if uncovered or unknown:
            result[master.frontier_id] = PossibleMissionCargo(
                row['count'], available, remaining, min(available, uncovered),
                known, unknown_total, unknown)
    return result


def possible_mission_cargo_tooltip(details):
    number = QLocale(get_language()).toString
    parts = [tr('trade.possible_cargo_stock', count=number(details.available))]
    if details.known_missions:
        parts.append(tr('trade.possible_cargo_need', missions=number(details.known_missions),
                        count=number(details.remaining)))
        parts.append(tr('trade.possible_cargo_cover', count=number(details.coverable)))
    if details.unknown_missions:
        parts.append(tr('trade.possible_cargo_unknown', missions=number(details.unknown_missions),
                        count=number(details.unknown_required)))
    parts.append(tr('trade.possible_cargo_warning'))
    return '\n'.join(parts)


def mission_cargo_tooltip(details, *, own_cargo=False):
    amount, total, missions = details
    locale = QLocale(get_language())
    text = tr('trade.mission_cargo' if amount == total else 'trade.mission_cargo_mixed',
              count=locale.toString(amount), total=locale.toString(total))
    if missions > 1:
        text += '\n' + tr('trade.mission_cargo_missions', count=locale.toString(missions))
    if own_cargo:
        text = tr('trade.mission_cargo_own') + '\n' + text
    return text


@lru_cache(maxsize=2)
def mission_cargo_icon(light):
    # Draw at 2x resolution for sharp high-DPI rendering. Palette selection in
    # initStyleOption also follows theme changes without rebuilding the model.
    pixmap = QPixmap(28, 28)
    pixmap.setDevicePixelRatio(2)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    # Blue globe, matching the supplied reference's ring and latitude/longitude
    # grid. Transparent interior keeps it legible on selection and both themes.
    ring = QRectF(1.5, 1.5, 11, 11)
    clip = QPainterPath()
    clip.addEllipse(ring)
    painter.save()
    painter.setClipPath(clip)
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(QColor('#397ca6' if light else '#18638a'), .8))
    painter.drawEllipse(QRectF(4, 1.5, 6, 11))
    painter.drawLine(7, 1, 7, 13)
    for y in (4, 7, 10):
        painter.drawLine(1, y, 13, y)
    painter.restore()
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(QColor('#0074b8' if light else '#16b5f5'), 1.4))
    painter.drawEllipse(ring)
    painter.end()
    return QIcon(pixmap)


@lru_cache(maxsize=2)
def possible_mission_cargo_icon(light):
    pixmap = QPixmap(32, 28)
    pixmap.setDevicePixelRatio(2)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor('#a32269' if light else '#ff83c4'), 1.3))
    painter.setBrush(Qt.NoBrush)
    painter.drawEllipse(QRectF(1.5, 1.5, 10, 11))
    painter.drawEllipse(QRectF(4, 1.5, 5, 11))
    painter.drawLine(2, 7, 11, 7)
    # Draw the exclamation as geometry, legible independently of font fallback.
    painter.setPen(QPen(QColor('#a32269' if light else '#ff83c4'), 1.8))
    painter.drawLine(14, 3, 14, 8)
    painter.drawPoint(14, 11)
    painter.end()
    return QIcon(pixmap)


@lru_cache(maxsize=2)
def mixed_mission_cargo_icon(light):
    pixmap = QPixmap(64, 28)
    pixmap.setDevicePixelRatio(2)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    mission_cargo_icon(light).paint(painter, 0, 0, 14, 14)
    possible_mission_cargo_icon(light).paint(painter, 16, 0, 16, 14)
    painter.end()
    return QIcon(pixmap)


class MissionCargoDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        blue = bool(index.data(MISSION_CARGO_ROLE))
        pink = bool(index.data(POSSIBLE_MISSION_CARGO_ROLE))
        if blue or pink:
            light = option.palette.window().color().lightness() > 128
            icon = mixed_mission_cargo_icon if blue and pink else (
                possible_mission_cargo_icon if pink else mission_cargo_icon)
            option.icon = icon(light)
            option.decorationSize = QSize(32 if blue and pink else 16 if pink else 14, 14)
            option.features |= option.ViewItemFeature.HasDecoration


class CargoMissionLegend(QWidget):
    """Two compact wrapping explanations using the actual themed symbols."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setVerticalSpacing(2)
        self.entries = []
        for row, (key, icon) in enumerate((
                ('trade.cargo_legend_blue', mission_cargo_icon),
                ('trade.cargo_legend_pink', possible_mission_cargo_icon))):
            symbol, label = QLabel(), QLabel()
            label.setTextFormat(Qt.PlainText)
            label.setWordWrap(True)
            layout.addWidget(symbol, row, 0, Qt.AlignTop)
            layout.addWidget(label, row, 1)
            self.entries.append((key, icon, symbol, label))
        layout.setColumnStretch(1, 1)
        self.refresh()

    def refresh(self):
        light = self.palette().window().color().lightness() > 128
        for key, icon, symbol, label in self.entries:
            symbol.setPixmap(icon(light).pixmap(QSize(16, 14)))
            label.setText(tr(key))
        self.setAccessibleName(' · '.join(tr(key) for key, *_ in self.entries))

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in (QEvent.PaletteChange, QEvent.LanguageChange) and hasattr(self, 'entries'):
            self.refresh()
