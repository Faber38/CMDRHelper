"""Mission status accents, confined to the status column including selection."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStyledItemDelegate

from cmdrhelper.models import (
    STATUS_ACCEPTED, STATUS_REDIRECTED, STATUS_COMPLETED,
    STATUS_DATA_RECEIVED, STATUS_AT_DESTINATION,
)
from .mission_arrival import draw_arrival_cell


MISSION_STATUS_ROLE = Qt.UserRole + 21
GREEN_STATUSES = frozenset((
    STATUS_REDIRECTED, STATUS_COMPLETED, STATUS_DATA_RECEIVED, STATUS_AT_DESTINATION,
))


class MissionStatusDelegate(QStyledItemDelegate):
    def __init__(self, table, *, light=False):
        super().__init__(table)
        self._light = light

    def set_light_mode(self, light):
        self._light = light
        self.parent().viewport().update()

    def paint(self, painter, option, index):
        status = index.data(MISSION_STATUS_ROLE)
        if status in GREEN_STATUSES:
            color = "#226626" if self._light else "#65d067"
        elif status == STATUS_ACCEPTED:
            color = "#765400" if self._light else "#ffb000"
        else:
            color = None
        if not draw_arrival_cell(painter, option, index, self, color):
            super().paint(painter, option, index)
