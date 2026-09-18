"""Offline system overview with shared orbital layout and CMDRHelper assets."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from cmdrhelper.ui.system_layout import LayoutNode, build_positions, connector_points

from PySide6.QtCore import QPointF, QRectF, Qt, Signal, QTimer
from PySide6.QtGui import QBitmap, QColor, QFont, QPainter, QPainterPath, QPen, QRegion
from PySide6.QtWidgets import (
    QDialog, QGraphicsObject, QGraphicsScene, QGraphicsView, QHBoxLayout,
    QLabel, QPushButton, QVBoxLayout,
)

from cmdrhelper.i18n import tr
from cmdrhelper.ui import station_items
from cmdrhelper.ui.system_view import SystemMapWidget


from cmdrhelper.ui.system_theme import THEMES


CELL_WIDTH = 176.0
GAP = 26.0


def _is_star(body):
    return bool(body.get('star_type') or body.get('body_type') == 'Star')


def body_diameter(body):
    if SystemMapWidget._is_belt_cluster(body):
        return 50.0
    size = SystemMapWidget._visual_body_size(body)
    if _is_star(body):
        return min(148.0, max(124.0, size * 1.6))
    if 'giant' in str(body.get('planet_class', '')).lower():
        return min(100.0, max(78.0, size * 1.6))
    return min(70.0, max(30.0, size * 1.15))


@dataclass
class OverviewNode(LayoutNode):
    x: float = 0
    y: float = 0

    @property
    def diameter(self):
        return body_diameter(self.body) if self.body is not None else 0.0

    @property
    def height(self):
        return 82 + self.diameter / 2 + 66 if self.body is not None else 110.0

    @property
    def center(self):
        if self.body is None:
            return QPointF(self.x, self.y)
        return QPointF(self.x + CELL_WIDTH / 2, self.y + 82)

    @property
    def rect(self):
        if self.body is None:
            return QRectF(self.x, self.y, 0, 0)
        return QRectF(self.x, self.y, CELL_WIDTH, self.height)


def build_layout(bodies, groups=None):
    groups = groups or {}
    return build_positions(bodies, OverviewNode, width=CELL_WIDTH,
                           height=lambda node: node.height, gap=GAP,
                           reserved_width=lambda n: station_items.CARD_WIDTH if groups.get(n.body.get("body_id")) else 0,
                           extra_height=lambda n: station_items.extra_height(groups.get(n.body.get("body_id"), [])) if not n.belt_members else 0,
                           image_center=82, image_radius=lambda node: node.diameter / 2)


class BodyItem(QGraphicsObject):
    clicked = Signal(object)

    def __init__(self, node, resolver, system_name, light=False):
        super().__init__()
        self.node, self.resolver = node, resolver
        self.light = light
        body = node.body
        self.name = str(body.get('short_name') or body.get('name') or body.get('body_id', '–'))
        if self.name.startswith(system_name + ' '):
            self.name = self.name[len(system_name) + 1:]
        if self.name == system_name:
            self.name = str(body.get('body_id', '–'))
        self.type_text = SystemMapWidget._type_text(body)
        if node.belt_members:
            self.type_text = ''
        self.pixmap = resolver._body_pixmap(body)
        self.image_source = QRectF()
        if self.pixmap is not None:
            # Assets have different transparent margins. Fit the visible artwork,
            # retaining its aspect ratio and the shared resolver's original PNG.
            mask = self.pixmap.toImage().createAlphaMask(Qt.ImageConversionFlag.ThresholdDither)
            visible = QRegion(QBitmap.fromImage(mask)).boundingRect()
            if visible.isEmpty():
                visible = self.pixmap.rect()
            self.image_source = QRectF(visible.adjusted(-2, -2, 2, 2).intersected(self.pixmap.rect()))
        self.setToolTip(f"{body.get('name') or self.name}\n{self.type_text}")
        if node.belt_members:
            self.setToolTip(f"{body['name']}\n{len(node.belt_members)} × "
                            + tr('system_view.type.asteroid_cluster'))
        self.setPos(node.x, node.y)
        if node.belt_members:
            self.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
        else:
            self.setFlag(QGraphicsObject.GraphicsItemFlag.ItemIsSelectable)
            self.setAcceptHoverEvents(True)
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hovered = False

    def boundingRect(self):
        return QRectF(0, 0, CELL_WIDTH, self.node.height)

    def paint(self, painter, option, widget=None):
        theme = THEMES[self.light]
        diameter = self.node.diameter
        image_rect = QRectF((CELL_WIDTH - diameter) / 2, 82 - diameter / 2, diameter, diameter)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.hovered or self.isSelected():
            painter.setPen(QPen(QColor(theme['selected'] if self.isSelected() else theme['hover']), 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(self.boundingRect().adjusted(3, 3, -3, -3), 9, 9)
        if self.pixmap is not None:
            scale = diameter / max(self.image_source.width(), self.image_source.height())
            target = QRectF(0, 0, self.image_source.width() * scale, self.image_source.height() * scale)
            target.moveCenter(image_rect.center())
            painter.drawPixmap(target, self.pixmap, self.image_source)
        else:
            painter.setPen(QPen(QColor(theme['muted']), 1))
            painter.setBrush(SystemMapWidget._body_color(self.node.body))
            if SystemMapWidget._is_belt_cluster(self.node.body):
                for dx, dy, size in ((-18, 2, 13), (0, -8, 18), (19, 7, 10)):
                    painter.drawEllipse(QRectF(CELL_WIDTH / 2 + dx - size / 2, 82 + dy - size / 2, size, size))
            else:
                painter.drawEllipse(image_rect)
        font = QFont(painter.font())
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(theme['text']))
        label_y = image_rect.bottom() + 7
        painter.fillRect(QRectF(10, label_y, CELL_WIDTH - 20, 53), QColor(theme['background']))
        painter.drawText(QRectF(10, label_y, CELL_WIDTH - 20, 21), Qt.AlignmentFlag.AlignCenter,
                         painter.fontMetrics().elidedText(self.name, Qt.TextElideMode.ElideRight, int(CELL_WIDTH - 24)))
        font.setPointSize(9)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor(theme['muted']))
        painter.drawText(QRectF(10, label_y + 22, CELL_WIDTH - 20, 31),
                         Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                         self.type_text)

    def hoverEnterEvent(self, event):
        self.hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.hovered = False
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if not self.node.belt_members and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.node.body)


class SystemOverviewView(QGraphicsView):
    bodyClicked = Signal(object)

    def __init__(self, system_name, bodies, *, stations=None, light=False, parent=None):
        super().__init__(parent)
        self.system_name = system_name
        self.bodies = deepcopy(list(bodies or []))
        self.resolver = SystemMapWidget(self)
        self.resolver.hide()
        self.setScene(QGraphicsScene(self))
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._populate_scene(stations, light)
        self._first_show = True
        self._initial_scroll_timer = QTimer(self)
        self._initial_scroll_timer.setSingleShot(True)
        self._initial_scroll_timer.timeout.connect(self._scroll_to_start)

    def _populate_scene(self, stations, light):
        self.scene().clear()
        groups = station_items.facility_groups(stations, self.bodies)
        self.nodes = build_layout(self.bodies, groups)
        self.items_by_key = {}
        self.connections = []
        self.empty_label = None
        for node in self.nodes.values():
            if node.parent in self.nodes:
                parent_node = self.nodes[node.parent]
                points = connector_points(parent_node, node, GAP)
                path = QPainterPath(QPointF(*points[0]))
                for point in points[1:]:
                    path.lineTo(QPointF(*point))
                line = self.scene().addPath(path)
                line.setZValue(-1)
                self.connections.append(line)
            if node.body is None:
                marker = self.scene().addEllipse(node.x - 3, node.y - 3, 6, 6)
                marker.setAcceptedMouseButtons(Qt.MouseButton.NoButton)
                self.connections.append(marker)
            if node.body is not None:
                item = BodyItem(node, self.resolver, self.system_name, light)
                item.clicked.connect(self.bodyClicked)
                self.scene().addItem(item)
                self.items_by_key[node.key] = item
        for x1, y1, x2, y2 in station_items.parent_links(self.nodes, groups):
            line = self.scene().addLine(x1, y1, x2, y2)
            line.setZValue(-1)
            self.connections.append(line)
        self.facility_items = []
        facility_blocks, footer = station_items.blocks(self.nodes, groups, CELL_WIDTH)
        self.facility_footer = self.scene().addText(tr('facilities.other')) if footer is not None and footer.height() else None
        if self.facility_footer is not None:
            self.facility_footer.setPos(footer.topLeft())
        for rect, group in facility_blocks:
            item = station_items.FacilityItem(rect, group, light)
            item.clicked.connect(lambda stations: station_items.show_details(self, stations, self.system_name, light=self.light))
            self.scene().addItem(item)
            self.facility_items.append(item)
        if not self.items_by_key and not self.facility_items:
            self.empty_label = self.scene().addText(tr('explorer.no_system_data_available'))
        self.setSceneRect(self.scene().itemsBoundingRect().adjusted(-28, -28, 28, 28))
        self.set_light_mode(light)

    def set_stations(self, stations):
        center = self.mapToScene(self.viewport().rect().center())
        self._populate_scene(stations, self.light)
        self.centerOn(center)

    def showEvent(self, event):
        super().showEvent(event)
        if self._first_show:
            self._first_show = False
            self._initial_scroll_timer.start(0)

    def _scroll_to_start(self):
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().minimum())
        self.verticalScrollBar().setValue(self.verticalScrollBar().minimum())

    def set_light_mode(self, light):
        self.light = bool(light)
        theme = THEMES[self.light]
        self.setBackgroundBrush(QColor(theme['background']))
        if self.empty_label is not None:
            self.empty_label.setDefaultTextColor(QColor(theme['muted']))
        if self.facility_footer is not None:
            self.facility_footer.setDefaultTextColor(QColor(theme['muted']))
        for item in self.facility_items:
            item.light = self.light
            item.update()
        for line in self.connections:
            line.setPen(QPen(QColor(theme['line']), 1.2))
        for item in self.items_by_key.values():
            item.light = self.light
            item.update()
        self.viewport().update()

    def reset_zoom(self):
        self.resetTransform()
        self._scroll_to_start()

    def fit_system(self):
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        if self.transform().m11() > 1.0:
            self.reset_zoom()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            target = max(0.6, min(1.8, self.transform().m11() * (1.15 if event.angleDelta().y() > 0 else 1 / 1.15)))
            self.scale(target / self.transform().m11(), target / self.transform().m11())
            event.accept()
        else:
            super().wheelEvent(event)


class SystemOverviewDialog(QDialog):
    def __init__(self, system_name, bodies, on_body_clicked=None, parent=None, *,
                 light=False, settings=None, system_address=None, commander_id=None, stations=None, spansh=None):
        super().__init__(parent)
        self.system_name = system_name or ''
        self.system_address, self.commander_id = system_address, commander_id
        self.settings = settings
        self.setWindowTitle(tr('explorer.show_all_title', system=self.system_name))
        self.resize(1050, 720)
        if settings is not None:
            geometry = settings.value('system_overview/geometry')
            if geometry is not None:
                self.restoreGeometry(geometry)
        root = QVBoxLayout(self)
        root.addWidget(QLabel(self.system_name, objectName='sectionTitle'))
        hint = QLabel(tr('explorer.overview_hint'), objectName='muted')
        hint.setWordWrap(True)
        root.addWidget(hint)
        self.preview = SystemOverviewView(self.system_name, bodies, stations=stations, light=light, parent=self)
        if callable(on_body_clicked):
            self.preview.bodyClicked.connect(on_body_clicked)
        root.addWidget(self.preview, 1)
        buttons = QHBoxLayout()
        self.reset_button = QPushButton('100 %')
        self.reset_button.setCursor(Qt.PointingHandCursor)
        self.reset_button.clicked.connect(self.preview.reset_zoom)
        buttons.addWidget(self.reset_button)
        self.fit_button = QPushButton(tr('explorer.overview_fit'))
        self.fit_button.setCursor(Qt.PointingHandCursor)
        self.fit_button.clicked.connect(self.preview.fit_system)
        buttons.addWidget(self.fit_button)
        self.spansh = spansh
        self.spansh_button = QPushButton(tr('spansh.refresh'))
        self.spansh_button.setCursor(Qt.PointingHandCursor)
        self.spansh_button.setStyleSheet(
            'QPushButton:disabled { color: #888888; background-color: rgba(128, 128, 128, 35); border-color: #888888; }')
        self.spansh_status = QLabel('', objectName='muted')
        self.spansh_status.setWordWrap(True)
        root.addWidget(self.spansh_status)
        buttons.addWidget(self.spansh_button)
        self.spansh_button.clicked.connect(self._refresh_spansh)
        if spansh is not None:
            spansh.activityChanged.connect(self._spansh_activity)
            spansh.completed.connect(self._spansh_completed)
            spansh.alreadyUpdated.connect(self._spansh_already_updated)
        self._spansh_activity()
        buttons.addStretch()
        close = QPushButton(tr('common.close'))
        close.setCursor(Qt.PointingHandCursor)
        close.clicked.connect(self.close)
        buttons.addWidget(close)
        root.addLayout(buttons)

    def _spansh_activity(self):
        from cmdrhelper.spansh_cache import valid_id
        active = bool(self.spansh and self.spansh.active)
        busy = bool(self.spansh and self.spansh.busy(self.system_address))
        self.spansh_button.setEnabled(active and valid_id(self.system_address) and not busy)
        disabled_hint = tr('spansh.refresh_disabled')
        busy_hint = tr('spansh.refresh_busy')
        hint = disabled_hint if not active else busy_hint if busy else ''
        self.spansh_button.setToolTip(hint)
        # Disabled widgets do not reliably receive tooltip events on every platform.
        # Keep the reason readable in the existing status line as well.
        if hint or self.spansh_status.text() in (disabled_hint, busy_hint):
            self.spansh_status.setText(hint)

    def _refresh_spansh(self):
        self._spansh_activity()
        if self.spansh_button.isEnabled():
            self.spansh.refresh_system(self.system_address)

    def _spansh_completed(self, address, success):
        if address == self.system_address:
            self.spansh_status.setText(tr('spansh.refresh_success' if success else 'spansh.refresh_failed'))

    def _spansh_already_updated(self, address):
        if address == self.system_address:
            self.spansh_status.setText(tr('spansh.refresh_already_today'))

    def set_light_mode(self, light):
        self.preview.set_light_mode(light)

    def closeEvent(self, event):
        if self.settings is not None:
            self.settings.setValue('system_overview/geometry', self.saveGeometry())
        super().closeEvent(event)
