"""Persist only table widths, without restoring hidden columns or sort state."""
from PySide6.QtCore import QByteArray
from PySide6.QtWidgets import QHeaderView, QTableWidget


def persist_column_widths(table, settings, key, *, legacy_key=None):
    header = table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.Interactive)
    header.setStretchLastSection(False)
    header.setMinimumSectionSize(40)
    count = table.columnCount()
    defaults = [table.columnWidth(i) for i in range(count)]

    def validated(values):
        if not isinstance(values, (list, tuple)) or len(values) != count:
            return None
        result = []
        for value in values:
            if isinstance(value, bool) or not isinstance(value, (int, str)):
                return None
            try:
                width = int(value)
            except (ValueError, TypeError):
                return None
            if not 40 <= width <= 2000:
                return None
            result.append(width)
        return result

    saved = settings.value(key)
    widths = validated(saved)
    if saved is None and legacy_key:
        legacy = settings.value(legacy_key)
        if isinstance(legacy, QByteArray):
            # Inspect old Qt state away from the real table: restoreState also
            # restores hidden/moved sections and resize modes, which we don't want.
            probe = QTableWidget(0, count)
            probe_header = probe.horizontalHeader()
            if probe_header.restoreState(legacy) and probe_header.count() == count:
                widths = validated([probe.columnWidth(i) for i in range(count)])
            probe.deleteLater()
    for i, width in enumerate(widths or defaults):
        table.setColumnWidth(i, width)

    def save(*_args):
        values = validated([table.columnWidth(i) for i in range(count)])
        if values is not None:
            settings.setValue(key, values)
            settings.sync()

    header.sectionResized.connect(save)
