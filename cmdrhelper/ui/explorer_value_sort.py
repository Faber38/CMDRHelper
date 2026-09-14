"""Sorting confined to the Explorer tables; display values stay untouched."""
import math
import re

from PySide6.QtCore import QCollator, QLocale, Qt
from PySide6.QtWidgets import QTableWidgetItem

from cmdrhelper.i18n import get_language


class ValueItem(QTableWidgetItem):
    def __init__(self, text, key):
        super().__init__(str(text))
        self.sort_key = key

    def __lt__(self, other):
        return self.sort_key < other.sort_key


def natural_key(name):
    return tuple((0, int(part)) if part.isdigit() else (1, part.casefold())
                 for part in re.split(r"(\d+)", str(name)))


def text_key(text):
    collator = QCollator(QLocale(get_language()))
    collator.setCaseSensitivity(Qt.CaseInsensitive)
    return collator.sortKey(str(text))


def distance_key(body):
    try:
        distance = float(body.get("distance_ls"))
        if not math.isfinite(distance):
            distance = float("-inf")
    except (TypeError, ValueError):
        distance = float("-inf")
    return distance


def sort_keys(body, values, visited, self_mapped, was_mapped, possible_value):
    # Ascending: unknown, first mapping possible, already mapped, self mapped.
    mapping = 3 if self_mapped else 2 if was_mapped is True else 1 if was_mapped is False else 0
    return [natural_key(values[0]), text_key(values[1]), distance_key(body),
            int(body.get("scan_value") or 0), int(body.get("current_value") or 0),
            possible_value, mapping, (bool(visited), mapping)]


def bio_sort_keys(body, values, bio_names, known_value, visited, found, completed, analysed):
    signals, geo, mining = (max(0, int(body.get(key) or 0)) for key in
                            ("biological_signals", "geological_signals", "planetary_mining_signals"))
    # Same states as the displayed cells: open, signals known, visited, analysed.
    status = (3 if analysed else 2 if visited else 1) if signals else 0
    progress = completed if analysed else found if visited else signals
    return [natural_key(values[0]), text_key(values[1]), signals, geo, mining,
            text_key(", ".join(name for name, _ in bio_names) if signals else ""),
            known_value if signals else 0, distance_key(body), bool(visited),
            (status, progress if signals else 0), status]


def apply_sort(table):
    selection = getattr(table, "_value_sort", None)
    if selection is not None:
        table.sortItems(*selection)


def setup_sort(table, settings, prefix="explorer/value"):
    header = table.horizontalHeader()
    table._value_sort = None
    header.setSectionsClickable(True)
    header.setSortIndicatorShown(False)
    try:
        column = int(settings.value(f"{prefix}_sort_column"))
        order = int(settings.value(f"{prefix}_sort_order"))
        if 0 <= column < table.columnCount() and order in (0, 1):
            table._value_sort = (column, Qt.SortOrder(order))
    except (TypeError, ValueError):
        pass
    if table._value_sort is not None:
        header.setSortIndicator(*table._value_sort)
        header.setSortIndicatorShown(True)
        apply_sort(table)

    def clicked(column):
        previous = table._value_sort
        order = Qt.AscendingOrder
        if previous == (column, Qt.AscendingOrder):
            order = Qt.DescendingOrder
        table._value_sort = (column, order)
        apply_sort(table)
        header.setSortIndicator(column, order)
        header.setSortIndicatorShown(True)
        settings.setValue(f"{prefix}_sort_column", column)
        settings.setValue(f"{prefix}_sort_order", order.value)
        settings.sync()

    header.sectionClicked.connect(clicked)
