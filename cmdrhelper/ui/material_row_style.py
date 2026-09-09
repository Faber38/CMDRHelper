"""Material-row backgrounds: selection > collection > hover > five-row rhythm."""
from PySide6.QtCore import QEvent, QPersistentModelIndex, Qt
from PySide6.QtGui import QBrush, QColor, QPalette, QCursor
from PySide6.QtWidgets import QStyle, QStyledItemDelegate

STRIPE_ROLE = Qt.ItemDataRole.UserRole + 1
COLLECTED_ROLE = Qt.ItemDataRole.UserRole + 2
THEMES = {
    False: dict(rows=("#101a23", "#17212b", "#1e242c", "#17262a", "#242830"),
                hover="#2e3c49", live="#294a36", selected="#765324",
                text="#d8dde3", selected_text="#fff4de"),
    True: dict(rows=("#f1f4f7", "#e7edf2", "#eef0ec", "#e3e8ee", "#eceaf0"),
               hover="#d4dee7", live="#cfe3d1", selected="#e9c68d",
               text="#20262c", selected_text="#252018"),
}


class MaterialRowDelegate(QStyledItemDelegate):
    def __init__(self, tree, light=False):
        super().__init__(tree)
        self.light = light
        self.hovered = QPersistentModelIndex()
        self._inside = False
        tree.setMouseTracking(True)
        tree.viewport().installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Enter, QEvent.Type.MouseMove, QEvent.Type.Leave):
            tree = self.parent()
            self._inside = event.type() != QEvent.Type.Leave
            index = tree.indexAt(event.position().toPoint()) if self._inside else None
            hovered = (QPersistentModelIndex(index.siblingAtColumn(0))
                       if index is not None and index.isValid() else QPersistentModelIndex())
            if hovered != self.hovered:
                self.hovered = hovered
                tree.viewport().update()
        return super().eventFilter(watched, event)

    def refresh_hover(self):
        # Item indexes are replaced on render. Keep hover under a stationary
        # pointer, including when a collection marker expires.
        tree = self.parent()
        point = tree.viewport().mapFromGlobal(QCursor.pos())
        index = tree.indexAt(point) if self._inside and tree.viewport().rect().contains(point) else None
        self.hovered = (QPersistentModelIndex(index.siblingAtColumn(0))
                        if index is not None and index.isValid() else QPersistentModelIndex())
        tree.viewport().update()

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        first = index.siblingAtColumn(0)
        stripe = first.data(STRIPE_ROLE)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        # Suppress native hover/selection painting so it cannot override the
        # explicit priority (in particular, hover must never obscure collection).
        option.state &= ~(QStyle.StateFlag.State_MouseOver | QStyle.StateFlag.State_Selected
                          | QStyle.StateFlag.State_HasFocus)
        if stripe is None:  # Grade headers do not participate in the rhythm.
            return
        theme = THEMES[self.light]
        color = (theme['selected'] if selected else theme['live'] if first.data(COLLECTED_ROLE)
                 else theme['hover'] if first == self.hovered else theme['rows'][stripe])
        option.backgroundBrush = QBrush(QColor(color))
        option.palette.setColor(QPalette.ColorRole.Text,
                                QColor(theme['selected_text'] if selected else theme['text']))
