"""Validated width/layout persistence without restoring hidden columns or sorting."""
from PySide6.QtCore import QByteArray, QSignalBlocker, QObject, QEvent, Qt
from PySide6.QtWidgets import QHeaderView, QTableWidget


def _validated_widths(values, count):
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


class _HeaderGesture(QObject):
    """Recognize header resizing initiated by mouse, not by layout/stretch."""
    def __init__(self, header, begin, end):
        super().__init__(header)
        self.begin, self.end = begin, end
        self.pressed = False
        header.viewport().installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonDblClick):
            self.pressed = event.button() == Qt.MouseButton.LeftButton
            if self.pressed:
                self.begin(event.position().toPoint().x())
        elif event.type() == QEvent.Type.MouseButtonRelease:
            self.pressed = False
            self.end()
        return super().eventFilter(watched, event)


def persist_column_widths(table, settings, key, *, legacy_key=None, preserve_default_stretch=False):
    """Optionally retain an existing default stretch until the first user resize."""
    header = table.horizontalHeader()
    original_stretch = header.stretchLastSection()
    header.setSectionResizeMode(QHeaderView.Interactive)
    header.setStretchLastSection(False)
    header.setMinimumSectionSize(40)
    count = table.columnCount()
    defaults = [table.columnWidth(i) for i in range(count)]

    def validated(values):
        return _validated_widths(values, count)

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

    default_stretch = bool(preserve_default_stretch and original_stretch and widths is None)
    suspended = False

    def begin_drag(x):
        nonlocal suspended
        if not default_stretch or suspended:
            return
        if not any(abs(x - (header.sectionViewportPosition(i) + header.sectionSize(i))) <= 4
                   for i in range(count)):
            return
        # Freeze before Qt handles the drag, so even the stretched last column
        # can be made narrower. Merely clicking a handle is not a saved change.
        visible = [table.columnWidth(i) for i in range(count)]
        with QSignalBlocker(header):
            header.setStretchLastSection(False)
            for i, width in enumerate(visible):
                table.setColumnWidth(i, width)
        suspended = True

    def end_drag():
        nonlocal suspended
        if default_stretch and suspended:
            header.setStretchLastSection(True)
        suspended = False

    gesture = _HeaderGesture(header, begin_drag, end_drag) if default_stretch else None
    if default_stretch:
        header.setStretchLastSection(True)

    def save(*_args):
        nonlocal default_stretch
        if default_stretch and not gesture.pressed:
            return  # Window/layout changes are not user preferences.
        values = validated([table.columnWidth(i) for i in range(count)])
        if values is not None:
            if default_stretch:
                default_stretch = False
                # Disabling stretch can revert the last section to its old base
                # width. Preserve the visible widths of the user's first drag.
                with QSignalBlocker(header):
                    header.setStretchLastSection(False)
                    for i, width in enumerate(values):
                        table.setColumnWidth(i, width)
            settings.setValue(key, values)
            settings.sync()

    header.sectionResized.connect(save)


def persist_header_layout(header, settings, key, *, columns, default_widths):
    """Opt-in shared layout for a header, excluding hidden/sort/Qt resize state.

    Column identities and version make schema changes invalidate the entire layout.
    Existing width-only consumers retain their behavior. Widths are logical-indexed;
    order lists logical indexes in visual order. Never auto-stretch user widths.
    """
    count = header.count()
    defaults = _validated_widths(default_widths, count)
    if defaults is None or len(columns) != count or len(set(columns)) != count:
        raise ValueError("Invalid default table layout")
    widths, order = defaults, list(range(count))
    saved = settings.value(key)
    if (isinstance(saved, dict) and type(saved.get("version")) is int
            and saved["version"] == 1 and saved.get("columns") == list(columns)):
        saved_widths = _validated_widths(saved.get("widths"), count)
        saved_order = saved.get("order")
        if (saved_widths is not None and isinstance(saved_order, list)
                and len(saved_order) == count and all(type(i) is int for i in saved_order)
                and sorted(saved_order) == list(range(count))):
            widths, order = saved_widths, saved_order

    header.setStretchLastSection(False)
    header.setSectionResizeMode(QHeaderView.Interactive)
    header.setMinimumSectionSize(40)
    header.setMaximumSectionSize(2000)
    header.setSectionsMovable(True)
    header.setFirstSectionMovable(True)  # QTreeWidget otherwise pins logical column 0.
    for visual, logical in enumerate(order):
        header.moveSection(header.visualIndex(logical), visual)
    for logical, width in enumerate(widths):
        header.showSection(logical)
        header.resizeSection(logical, width)

    def save(*_args):
        if header.count() != count:
            return
        # Qt permits resizeSection(i, 0) despite minimumSectionSize. Never retain
        # a collapsed/hidden section, even after a programmatic header change.
        with QSignalBlocker(header):
            for i in range(count):
                width = min(2000, max(40, header.sectionSize(i)))
                if header.isSectionHidden(i):
                    header.showSection(i)
                if header.sectionSize(i) != width:
                    header.resizeSection(i, width)
        current = _validated_widths([header.sectionSize(i) for i in range(count)], count)
        if current is None:
            return
        settings.setValue(key, dict(version=1, columns=list(columns), widths=current,
                                   order=[header.logicalIndex(i) for i in range(count)]))
        settings.sync()

    header.sectionResized.connect(save)
    header.sectionMoved.connect(save)
