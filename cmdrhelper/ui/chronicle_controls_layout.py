"""Width-aware layouts for the existing Chronicle controls; no data handling."""
from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtWidgets import QLayout, QSizePolicy, QSpacerItem, QWidgetItem


class ChronicleControlsLayout(QLayout):
    """Wrap controls at their natural widths, or expand the two filter panels."""

    def __init__(self, parent=None, *, panels=False):
        super().__init__(parent)
        self._items = []
        self._panels = panels
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(6)

    def addItem(self, item):
        self._items.append(item)
        self.invalidate()

    def insertWidget(self, index, widget):
        self.addChildWidget(widget)
        self._items.insert(index, QWidgetItem(widget))
        self.invalidate()

    def addStretch(self):
        # Preserve the insertion point used by the existing commander builder.
        self.addItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum))

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        return self._items[index] if 0 <= index < self.count() else None

    def takeAt(self, index):
        if 0 <= index < self.count():
            item = self._items.pop(index)
            self.invalidate()
            return item
        return None

    def expandingDirections(self):
        return Qt.Horizontal

    def hasHeightForWidth(self):
        return True

    def _size(self, item):
        return item.minimumSize() if self._panels else item.sizeHint().expandedTo(item.minimumSize())

    def minimumSize(self):
        size = QSize(0, 0)
        for item in self._items:
            if not item.isEmpty():
                size = size.expandedTo(self._size(item))
        margins = self.contentsMargins()
        return size + QSize(margins.left() + margins.right(), margins.top() + margins.bottom())

    def sizeHint(self):
        return self.minimumSize()

    def heightForWidth(self, width):
        return self._arrange(QRect(0, 0, width, 0))

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._arrange(rect, apply=True)

    def _arrange(self, rect, apply=False):
        margins = self.contentsMargins()
        inner = rect.adjusted(margins.left(), margins.top(), -margins.right(), -margins.bottom())
        rows, row, used = [], [], 0
        for item in self._items:
            if item.isEmpty():
                continue
            size = self._size(item)
            if row and used + self.spacing() + size.width() > inner.width():
                rows.append(row)
                row, used = [], 0
            used += (self.spacing() if row else 0) + size.width()
            row.append((item, size))
        if row:
            rows.append(row)
        y = inner.y()
        for row in rows:
            extra = max(0, inner.width() - sum(size.width() for _, size in row)
                        - self.spacing() * (len(row) - 1)) if self._panels else 0
            cells = []
            for column, (item, size) in enumerate(row):
                width = size.width() + extra // len(row) + (column < extra % len(row))
                height = max(size.height(), item.heightForWidth(width) if item.hasHeightForWidth() else 0)
                cells.append((item, width, height))
            height = max(h for _, _, h in cells)
            x = inner.x()
            for item, width, cell_height in cells:
                if apply:
                    item.setGeometry(QRect(x, y, width, cell_height))
                x += width + self.spacing()
            y += height + self.spacing()
        return y - inner.y() - (self.spacing() if rows else 0) + margins.top() + margins.bottom()
