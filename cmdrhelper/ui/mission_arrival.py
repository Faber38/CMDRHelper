"""Short-lived arrival animation; no journal/database mutations or polling timer."""
from PySide6.QtCore import QObject, QEvent, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QStyle, QStyledItemDelegate, QStyleOptionViewItem

from cmdrhelper.mission_arrival import ArrivalSource


def draw_arrival_cell(painter, option, index, delegate, color=None):
    table = delegate.parent()
    controller = getattr(table, 'mission_arrival', None)
    marked = controller is not None and controller.marked(index)
    if not marked and color is None:
        return False
    opt = QStyleOptionViewItem(option)
    delegate.initStyleOption(opt, index)
    text, opt.text = opt.text, ''
    style = table.style()
    style.drawControl(QStyle.CE_ItemViewItem, opt, painter, table)
    rect = style.subElementRect(QStyle.SE_ItemViewItemText, opt, table)
    painter.save()
    painter.setClipRect(option.rect)
    if marked:
        selected = bool(opt.state & QStyle.State_Selected)
        light = controller.light
        background = ('#eadca5' if selected else '#fff4cf') if light else (
            '#514222' if selected else '#302918')
        painter.fillRect(option.rect, QColor(background))
        if selected:
            painter.setPen(QColor('#92721f' if light else '#c49a3c'))
            painter.drawLine(option.rect.topLeft(), option.rect.topRight())
            painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
        if color is None:
            color = '#20262c' if light else '#d8dde3'
    painter.setFont(opt.font)
    painter.setPen(QColor(color))
    painter.drawText(rect, opt.displayAlignment,
                     opt.fontMetrics.elidedText(text, opt.textElideMode, max(0, rect.width())))
    painter.restore()
    return True


class MissionRowDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if not draw_arrival_cell(painter, option, index, self):
            super().paint(painter, option, index)


class MissionArrivalController(QObject):
    def __init__(self, state, table, *, light=False):
        super().__init__(table)
        self.state, self.table, self.light = state, table, light
        self.source = ArrivalSource()
        self.identity = None
        self.evidence = ()
        self.hits = set()
        self.blink = {}  # mission ID -> remaining phases (six toggles = three pulses)
        self.timer = QTimer(self)
        self.timer.setInterval(180)
        self.timer.timeout.connect(self.advance)
        table.mission_arrival = self
        table.installEventFilter(self)
        if hasattr(state, 'changed'):
            state.changed.connect(self.update)
        manager = getattr(state, 'sources', None)
        if manager is not None:
            manager.changed.connect(self.update)
            # Reuse the existing process/source check, including process loss
            # without a new journal event. Never introduce another poller.
            manager.timer.timeout.connect(self.update)

    def set_light_mode(self, light):
        self.light = light
        self.table.viewport().update()

    def update(self):
        snapshot = self.source.snapshot(self.state)
        if snapshot is None:
            identity, evidence, hits = None, (), set()
        else:
            identity, position, closed = snapshot
            evidence = position.evidence
            hits = {m.mission_id for m in self.state.missions
                    if m.mission_id not in closed and position.matches(m)}
        same = identity is not None and identity == self.identity
        new = hits - self.hits
        if same and evidence and self.evidence and evidence != self.evidence:
            # A departure and new landing may arrive in a single journal batch.
            # Repeated confirmations at the same place retain their evidence ID.
            new |= hits
        if not same:
            self.blink.clear()
        else:
            self.blink = {mid: phase for mid, phase in self.blink.items() if mid in hits}
            if new and evidence != self.evidence and self.table.isVisible():
                self.blink.update({mid: 6 for mid in new})
        self.identity, self.evidence, self.hits = identity, evidence, hits
        if self.blink and not self.timer.isActive():
            self.timer.start()
        elif not self.blink:
            self.timer.stop()
        self.table.viewport().update()

    def advance(self):
        self.blink = {mid: phase - 1 for mid, phase in self.blink.items() if phase > 1}
        if not self.blink:
            self.timer.stop()
        self.table.viewport().update()

    def marked(self, index):
        item = self.table.item(index.row(), index.column())
        mission = getattr(item, 'mission', None)
        return bool(self.identity and mission and mission.mission_id in self.hits
                    and getattr(self.table, 'arrival_commander', None) == self.identity[2]
                    and self.blink.get(mission.mission_id, 0) % 2 == 0)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Hide:
            self.blink.clear()
            self.timer.stop()
        return super().eventFilter(watched, event)
