"""Small painter-based facilities shared by both system maps."""
from html import escape

from PySide6.QtCore import Qt, QRectF, Signal
from PySide6.QtGui import QColor, QPen, QFontMetricsF
from PySide6.QtWidgets import QGraphicsObject

from cmdrhelper.i18n import tr
from cmdrhelper.ui.system_theme import THEMES
from cmdrhelper.stations import ORBITAL_TYPES, SURFACE_TYPES

DIRECT_LIMIT = 3
CARD_WIDTH = 252
CARD_HEIGHT = 64
ROW_HEIGHT = 76
PARENT_GAP = 16


def type_key(station):
    kind = station.get('station_type')
    if kind == 'FleetCarrier':
        return 'carrier'
    if kind == 'OnFootSettlement':
        return 'settlement'
    if kind in SURFACE_TYPES or station.get('is_planetary'):
        return 'surface'
    if kind in ORBITAL_TYPES:
        return 'orbital'
    return {'Outpost': 'outpost', 'MegaShip': 'megaship'}.get(kind, 'station')


def label(stations):
    if len(stations) > 1:
        return tr('facilities.group', count=len(stations))
    return stations[0].get('station_name') or tr('common.unknown')


def tooltip(stations):
    # Large groups stay cheap; the complete list is available on click.
    return '<br>'.join(escape(s.get('station_name') or tr('common.unknown')) for s in stations[:DIRECT_LIMIT]) + (
        '<br>' + escape(tr('facilities.group', count=len(stations))) if len(stations) > DIRECT_LIMIT else '')


def facility_groups(stations, bodies):
    ids = {b.get('body_id') for b in bodies}
    groups = {}
    for station in stations or []:
        parent = station.get('parent_body_id')
        groups.setdefault(parent if parent in ids else None, []).append(station)
    return groups


def rows(stations):
    return [stations] if len(stations) > DIRECT_LIMIT else [[s] for s in stations]


def extra_height(stations):
    return len(rows(stations)) * ROW_HEIGHT + (PARENT_GAP if stations else 0)


def blocks(nodes, groups, width):
    result = []
    for node in nodes.values():
        if node.body is None or node.belt_members:
            continue
        stations = groups.get(node.body.get('body_id'), [])
        y = node.y + node.layout_height - extra_height(stations) + PARENT_GAP
        for group in rows(stations):
            result.append((QRectF(node.x, y, CARD_WIDTH, CARD_HEIGHT), group))
            y += ROW_HEIGHT
    unknown = groups.get(None, [])
    footer = None
    if unknown:
        y = max((n.y + n.layout_height for n in nodes.values()), default=0) + 32
        footer = QRectF(26, y, CARD_WIDTH, 0 if len(unknown) > DIRECT_LIMIT else 32)
        y += footer.height()
        for group in rows(unknown):
            result.append((QRectF(26, y, CARD_WIDTH, CARD_HEIGHT), group))
            y += ROW_HEIGHT
    return result, footer


def card_title(stations):
    if len(stations) > 1 and all(s.get('parent_body_id') is None for s in stations):
        return tr('facilities.other')
    return label(stations)


def paint_facility(painter, rect, stations, light, hovered=False):
    painter.save()
    theme = THEMES[bool(light)]
    painter.setBrush(QColor(theme['background']))
    painter.setPen(QPen(QColor(theme['selected']), 2 if hovered else 1.3))
    painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 6, 6)
    font = painter.font()
    font.setPointSizeF(18)
    painter.setFont(font)
    glyph = {'orbital': '◇', 'surface': '⌂', 'outpost': '□', 'settlement': '▱',
             'carrier': '⬡', 'megaship': '▭'}.get(type_key(stations[0]), '◇')
    painter.drawText(QRectF(rect.x() + 8, rect.y() + 9, 30, 38), Qt.AlignCenter,
                     glyph if len(stations) == 1 else '◇')
    font.setPointSizeF(10)
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(QColor(theme['text']))
    text_rect = QRectF(rect.x() + 44, rect.y() + 9, rect.width() - 54, 23)
    painter.drawText(text_rect, Qt.AlignVCenter,
                     QFontMetricsF(font).elidedText(card_title(stations), Qt.ElideRight, text_rect.width()))
    font.setPointSizeF(9)
    font.setBold(False)
    painter.setFont(font)
    painter.setPen(QColor(theme['muted']))
    subtitle = (tr('facilities.group', count=len(stations)) if len(stations) > 1
                else tr('facilities.' + type_key(stations[0])))
    painter.drawText(text_rect.translated(0, 23), Qt.AlignVCenter,
                     QFontMetricsF(font).elidedText(subtitle, Qt.ElideRight, text_rect.width()))
    painter.restore()


def parent_links(nodes, groups):
    """Only through the vertical space reserved below the body's labels."""
    links = []
    for node in nodes.values():
        if node.body is None or node.belt_members:
            continue
        stations = groups.get(node.body.get('body_id'), [])
        if not stations:
            continue
        y = node.y + node.layout_height - extra_height(stations)
        x = node.x + node.layout_width / 2
        links.append((x, y, x, y + PARENT_GAP))
    return links


def show_details(parent, stations, system_name, *, light=False):
    from cmdrhelper.ui.station_details import StationDetailDialog, StationSelectionDialog
    dialog = (StationDetailDialog(stations[0], system_name, parent, light=light) if len(stations) == 1
              else StationSelectionDialog(stations, system_name, parent, light=light))
    dialog.show()
    return dialog


class FacilityItem(QGraphicsObject):
    clicked = Signal(object)

    def __init__(self, rect, stations, light=False):
        super().__init__()
        self.rect = QRectF(0, 0, rect.width(), rect.height())
        self.stations, self.light = stations, light
        self.hovered = False
        self.setAcceptHoverEvents(True)
        self.setPos(rect.topLeft())
        self.setToolTip(tooltip(stations))
        self.setCursor(Qt.PointingHandCursor)

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget=None):
        paint_facility(painter, self.rect, self.stations, self.light, self.hovered)

    def hoverEnterEvent(self, event):
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        self.hovered = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.stations)
            event.accept()
        else:
            super().mousePressEvent(event)
