"""Optional, event-driven width distribution for the eight-column value list."""
from PySide6.QtCore import QObject, QEvent, QSignalBlocker, QTimer


SETTING_KEY = "explorer/value_fit_width"


class ValueListWidthFit(QObject):
    # Character-based floors scale with the user's font; text columns get more room.
    MIN_CHARACTERS = (9, 14, 10, 11, 13, 17, 15, 19)
    WEIGHTS = (1, 2, 1, 1, 1.4, 2.3, 2, 2.3)

    def __init__(self, table, checkbox, settings):
        super().__init__(table)
        self.table, self.checkbox, self.settings = table, checkbox, settings
        self.pending = False
        self.applying = False
        saved = settings.value(SETTING_KEY, True)
        enabled = saved.strip().lower() not in ("false", "0", "no", "off") if isinstance(saved, str) else bool(saved)
        checkbox.setChecked(enabled)
        checkbox.toggled.connect(self.toggled)
        table.installEventFilter(self)
        table.viewport().installEventFilter(self)

    def toggled(self, enabled):
        self.settings.setValue(SETTING_KEY, enabled)
        self.settings.sync()
        if enabled:
            self.apply()

    def eventFilter(self, watched, event):
        kind = event.type()
        if (kind in (QEvent.Show, QEvent.FontChange, QEvent.StyleChange)
                or (kind == QEvent.Resize and watched is self.table.viewport()
                    and event.size().width() != event.oldSize().width())):
            self.request()
        return super().eventFilter(watched, event)

    def request(self):
        if self.checkbox.isChecked() and not self.pending:
            self.pending = True
            # Coalesce Qt layout events; no polling or recurring timer.
            QTimer.singleShot(0, self.flush)

    def flush(self):
        self.pending = False
        self.apply()

    def minimum_widths(self):
        unit = self.table.fontMetrics().horizontalAdvance("0")
        return [max(60, unit * count + 16) for count in self.MIN_CHARACTERS]

    def apply(self):
        if self.applying or not self.checkbox.isChecked() or not self.table.isVisible():
            return
        self.applying = True
        try:
            header = self.table.horizontalHeader()
            columns = [i for i in range(self.table.columnCount()) if not self.table.isColumnHidden(i)]
            minima = self.minimum_widths()
            extra = max(0, self.table.viewport().width() - sum(minima[i] for i in columns))
            weight = sum(self.WEIGHTS[i] for i in columns)
            used = 0
            # Automated widths are not saved as manual column-width preferences.
            with QSignalBlocker(header):
                header.setStretchLastSection(False)
                for position, column in enumerate(columns):
                    share = extra - used if position == len(columns) - 1 else int(extra * self.WEIGHTS[column] / weight)
                    used += share
                    header.resizeSection(column, minima[column] + share)
            self.table.updateGeometries()
            self.table.resizeRowsToContents()
            self.table.viewport().update()
        finally:
            self.applying = False
