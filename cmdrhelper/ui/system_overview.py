"""Offline system overview; independent layout, shared CMDRHelper body assets."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from cmdrhelper.belt_projection import BodyNode, build_body_nodes, node_sort_key

from PySide6.QtCore import QPointF, QRectF, Qt, Signal, QTimer
from PySide6.QtGui import QBitmap, QColor, QFont, QPainter, QPainterPath, QPen, QRegion
from PySide6.QtWidgets import (
    QDialog, QGraphicsObject, QGraphicsScene, QGraphicsView, QHBoxLayout,
    QLabel, QPushButton, QVBoxLayout,
)

from cmdrhelper.i18n import tr
from cmdrhelper.ui.system_view import SystemMapWidget


THEMES = {
    False: dict(background='#080d12', line='#465361', text='#d8dde3',
                muted='#9ba9b7', hover='#c4a264', selected='#ffb34f'),
    True: dict(background='#f1f4f7', line='#9caab7', text='#20262c',
               muted='#536574', hover='#927035', selected='#965900'),
}
CELL_WIDTH = 176.0
GAP = 26.0
MOONS_PER_COLUMN = 4


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
class OverviewNode(BodyNode):
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
        return QPointF(self.x + CELL_WIDTH / 2, self.y + 82)

    @property
    def rect(self):
        return QRectF(self.x, self.y, CELL_WIDTH, self.height)


def build_layout(bodies):
    """Make a deterministic forest. Names label bodies, never determine parents.

    Stars/barycentres have horizontal planet axes and separate companion lanes.
    Planet satellites occupy vertical branches, split after four direct children.
    Subtree rectangles reserve space before adjacent branches are placed.
    """
    nodes = build_body_nodes(bodies, OverviewNode)
    roots = sorted((n for n in nodes.values() if n.parent is None),
                   key=lambda n: (not (n.body is None or _is_star(n.body)), node_sort_key(n)))

    def translate(group, dx, dy):
        for node in group:
            node.x += dx
            node.y += dy

    def place(node):
        group = [node]
        width, height = CELL_WIDTH, node.height
        if node.body is None or _is_star(node.body):
            planets = [n for n in node.children if n.body is not None and not _is_star(n.body)]
            companions = [n for n in node.children if n not in planets]
            index = 0
            while index < len(planets):
                column = [planets[index]]
                index += 1
                if not column[0].belt_members and SystemMapWidget._is_belt_cluster(column[0].body):
                    while (index < len(planets) and len(column) < MOONS_PER_COLUMN
                           and not planets[index].belt_members
                           and SystemMapWidget._is_belt_cluster(planets[index].body)):
                        column.append(planets[index])
                        index += 1
                column_y, column_width = 0, 0
                for child in column:
                    members, w, h = place(child)
                    translate(members, width + GAP, column_y)
                    group.extend(members)
                    column_width = max(column_width, w)
                    column_y += h + GAP
                width += GAP + column_width
                height = max(height, column_y - GAP)
            for child in companions:
                members, w, h = place(child)
                translate(members, 48, height + 48)
                group.extend(members)
                width = max(width, 48 + w)
                height += 48 + h
        else:
            column_x = 40.0
            for start in range(0, len(node.children), MOONS_PER_COLUMN):
                column_y = node.height + GAP
                column_width = 0
                for child in node.children[start:start + MOONS_PER_COLUMN]:
                    members, w, h = place(child)
                    translate(members, column_x, column_y)
                    group.extend(members)
                    column_width = max(column_width, w)
                    column_y += h + GAP
                width = max(width, column_x + column_width)
                height = max(height, column_y - GAP)
                column_x += column_width + GAP
        return group, width, height

    bottom = 0
    for root in roots:
        group, width, height = place(root)
        translate(group, 0, bottom)
        bottom += height + 64
    return nodes


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

    def __init__(self, system_name, bodies, *, light=False, parent=None):
        super().__init__(parent)
        self.system_name = system_name
        self.bodies = deepcopy(list(bodies or []))
        self.nodes = build_layout(self.bodies)
        self.resolver = SystemMapWidget(self)
        self.resolver.hide()
        self.setScene(QGraphicsScene(self))
        self.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.items_by_key = {}
        self.connections = []
        self.empty_label = None
        for node in self.nodes.values():
            if node.parent in self.nodes:
                parent_node = self.nodes[node.parent]
                path = QPainterPath(parent_node.center)
                if node.center.y() != parent_node.center.y():
                    trunk = parent_node.x + 8
                    if (parent_node.body is None or _is_star(parent_node.body)) and node.body is not None and not _is_star(node.body):
                        trunk = node.x - 18
                    path.lineTo(trunk, parent_node.center.y())
                    if parent_node.body is not None and not _is_star(parent_node.body):
                        branch_y = parent_node.y + parent_node.height + GAP / 2
                        path.lineTo(trunk, branch_y)
                        trunk = node.x - 18
                        path.lineTo(trunk, branch_y)
                    path.lineTo(trunk, node.center.y())
                path.lineTo(node.center)
                line = self.scene().addPath(path)
                line.setZValue(-1)
                self.connections.append(line)
            if node.body is not None:
                item = BodyItem(node, self.resolver, system_name, light)
                item.clicked.connect(self.bodyClicked)
                self.scene().addItem(item)
                self.items_by_key[node.key] = item
        if not self.items_by_key:
            self.empty_label = self.scene().addText(tr('explorer.no_system_data_available'))
        self.setSceneRect(self.scene().itemsBoundingRect().adjusted(-28, -28, 28, 28))
        self.set_light_mode(light)
        self._first_show = True
        self._initial_scroll_timer = QTimer(self)
        self._initial_scroll_timer.setSingleShot(True)
        self._initial_scroll_timer.timeout.connect(self._scroll_to_start)

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
                 light=False, settings=None, system_address=None, commander_id=None):
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
        self.preview = SystemOverviewView(self.system_name, bodies, light=light, parent=self)
        if callable(on_body_clicked):
            self.preview.bodyClicked.connect(on_body_clicked)
        root.addWidget(self.preview, 1)
        buttons = QHBoxLayout()
        self.reset_button = QPushButton('100 %')
        self.reset_button.clicked.connect(self.preview.reset_zoom)
        buttons.addWidget(self.reset_button)
        self.fit_button = QPushButton(tr('explorer.overview_fit'))
        self.fit_button.clicked.connect(self.preview.fit_system)
        buttons.addWidget(self.fit_button)
        buttons.addStretch()
        close = QPushButton(tr('common.close'))
        close.clicked.connect(self.close)
        buttons.addWidget(close)
        root.addLayout(buttons)

    def set_light_mode(self, light):
        self.preview.set_light_mode(light)

    def closeEvent(self, event):
        if self.settings is not None:
            self.settings.setValue('system_overview/geometry', self.saveGeometry())
        super().closeEvent(event)
