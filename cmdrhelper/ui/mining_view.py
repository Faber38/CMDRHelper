"""One offline mining table, with independent, identity-based settings."""
from PySide6.QtCore import QCollator, QLocale, QSize, Qt, QTimer, QVariantAnimation, QDateTime, QEvent, QPersistentModelIndex
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTreeWidget, QTreeWidgetItem, QPushButton, QCheckBox, QDialog, QMessageBox, QStyledItemDelegate, QStyle,
)

from cmdrhelper.i18n import get_language, tr, tr_for_language
from cmdrhelper.mining_catalog import MINING_COMMODITIES, value_class
from cmdrhelper.ui.table_widths import persist_header_layout, _validated_widths
from cmdrhelper.mining_inventory import MiningInventory
from cmdrhelper.ui.material_row_style import THEMES


def _migrate_columns(settings, columns):
    """Retain all Phase 1 widths/order by identity when inserting stock columns."""
    key = "materials/mining/columns"
    saved = settings.value(key)
    old = ["name", "average_price", "value_class"]
    if (not isinstance(saved, dict) or type(saved.get("version")) is not int
            or saved["version"] != 1 or saved.get("columns") != old):
        return
    widths = _validated_widths(saved.get("widths"), 3)
    order = saved.get("order")
    if (widths is None or not isinstance(order, list) or len(order) != 3
            or any(type(i) is not int for i in order) or sorted(order) != [0, 1, 2]):
        return
    migrated_order = []
    for logical in order:
        migrated_order.append(columns.index(old[logical]))
        if logical == 0:
            migrated_order.extend([1, 2, 3])
    settings.setValue(key, dict(version=1, columns=list(columns),
        widths=[widths[0], 95, 95, 95, widths[1], widths[2]], order=migrated_order))
    settings.sync()


class _MiningItem(QTreeWidgetItem):
    def __lt__(self, other):
        column = self.treeWidget().sortColumn()
        if column == 0:
            return self.treeWidget().collator.compare(self.text(0), other.text(0)) < 0
        left = self.data(column, Qt.ItemDataRole.UserRole)
        right = other.data(column, Qt.ItemDataRole.UserRole)
        if (left is None) != (right is None):
            descending = self.treeWidget().header().sortIndicatorOrder() == Qt.SortOrder.DescendingOrder
            return (left is None) == descending  # Unknown is last in either direction.
        if left != right:
            return left < right
        return self.treeWidget().collator.compare(self.text(0), other.text(0)) < 0


class _CarrierDelegate(QStyledItemDelegate):
    """Material-table row tones, preserving semantic text and carrier hover."""
    def __init__(self, tree):
        super().__init__(tree)
        self.tree = tree
        self.hover_position = None
        self.hovered = QPersistentModelIndex()
        self.light = False
        self.color = QColor("#79d45a")
        tree.setMouseTracking(True)
        tree.viewport().installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.MouseMove:
            self.hover_position = event.position().toPoint()
            self.hovered = QPersistentModelIndex(self.tree.indexAt(self.hover_position))
            watched.update()
        elif event.type() in (QEvent.Type.Leave, QEvent.Type.Hide):
            self.hover_position = None
            self.hovered = QPersistentModelIndex()
            watched.update()
        return super().eventFilter(watched, event)

    @staticmethod
    def _blend(base, accent, amount):
        return QColor.fromRgbF(*(a * (1 - amount) + b * amount for a, b in
                                zip(base.getRgbF()[:3], accent.getRgbF()[:3])))

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        # Count visible rows in their current sorted order, without modifying
        # item data, filters or persisted settings.
        row = sum(not self.tree.topLevelItem(i).isHidden() for i in range(index.row()))
        theme = THEMES[self.light]
        background = QColor(theme["rows"][row % 5])
        hovered = self.hovered
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        if selected:
            background = self._blend(background, QColor(theme["selected"]), 0.35)
        elif hovered.isValid() and hovered.row() == index.row():
            background = self._blend(background, QColor(theme["hover"]), 0.25)
        if index.column() == 2 and hovered == index:
            background = self._blend(background, self.color, 0.11)
        # Native selection would replace both background and semantic text
        # colors. Keep the item's foreground and paint only our subtle tones.
        option.state &= ~(QStyle.StateFlag.State_Selected | QStyle.StateFlag.State_MouseOver
                          | QStyle.StateFlag.State_HasFocus)
        option.backgroundBrush = QBrush(background)


class MiningView(QWidget):
    COLUMNS = ("name", "vehicle", "carrier", "total", "average_price", "value_class")
    SORT_KEY = "materials/mining/sort"
    STOCK_FILTER_KEY = "materials/mining/only_stock"
    ORIGIN_FILTER_KEY = "materials/mining/origin_filter"
    CLASS_FILTER_KEY = "materials/mining/value_class_filter"

    def __init__(self, settings, parent=None, *, commodities=MINING_COMMODITIES, state=None, controller=None):
        super().__init__(parent)
        self.settings = settings
        commodities = tuple(commodities)
        self._search_text = {}
        self.items = {}
        self._origins = {c.symbol: c.origin for c in commodities}
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.content = QWidget()
        self.content.setMaximumWidth(1120)
        outer.addWidget(self.content, 5)
        outer.addStretch(1)  # Reserved space; no future controls or stock logic yet.
        layout = QVBoxLayout(self.content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.heading = QLabel(tr("mining.heading"), objectName="sectionTitle")
        self.heading.setWordWrap(True)
        heading_row = QHBoxLayout()
        heading_row.addWidget(self.heading, 1)
        self.refresh_button = QPushButton(tr("mining.refresh"))
        self.refresh_button.setToolTip(tr("mining.refresh_tooltip"))
        self._refresh_state = "ready"
        self._refresh_result = None
        self.refresh_animation = QVariantAnimation(self)
        self.refresh_animation.setDuration(1500)
        self.refresh_animation.setStartValue(0.0)
        self.refresh_animation.setEndValue(1.0)
        self.refresh_animation.valueChanged.connect(self._paint_refresh)
        self.refresh_animation.finished.connect(self._finish_refresh_feedback)
        self.refresh_status_timer = QTimer(self)
        self.refresh_status_timer.setSingleShot(True)
        self.refresh_status_timer.setInterval(2500)
        heading_row.addWidget(self.refresh_button)
        layout.addLayout(heading_row)
        self.refresh_status = QLabel(objectName="muted")
        self.refresh_status.setWordWrap(True)
        self.refresh_status.hide()
        self.refresh_status_timer.timeout.connect(self.refresh_status.hide)
        layout.addWidget(self.refresh_status)
        self.summary = QLabel(tr("mining.count_summary", count=len(commodities)), objectName="muted")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        self.notice = QLabel(tr("mining.reference_short"), objectName="muted")
        self.notice.setWordWrap(True)
        self.notice.setToolTip(tr("mining.reference_notice"))
        layout.addWidget(self.notice)
        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("mining.search"))
        self.search.setAccessibleName(tr("mining.search"))
        self.search.setClearButtonEnabled(True)
        filters.addWidget(self.search, 3)
        self.class_filter = QComboBox()
        self.class_filter.setAccessibleName(tr("mining.value_class"))
        self.class_filter.addItem(tr("materials.all"), None)
        for category, rank in (("high", 2), ("medium", 1), ("low", 0)):
            self.class_filter.addItem(tr("mining." + category), rank)
        saved_class = str(settings.value(self.CLASS_FILTER_KEY, "all"))
        self.class_filter.setCurrentIndex(self.class_filter.findData(int(saved_class))
                                         if saved_class in ("0", "1", "2") else 0)
        filters.addWidget(self.class_filter, 1)
        self.origin_filter = QComboBox()
        self.origin_filter.setAccessibleName(tr("mining.origin"))
        self.origin_filter.addItem(tr("materials.all"), "all")
        self.origin_filter.addItem(tr("mining.origin_surface"), "surface")
        self.origin_filter.addItem(tr("mining.origin_asteroid"), "asteroid")
        self.set_origin_filter(settings.value(self.ORIGIN_FILTER_KEY, "all"))
        filters.addWidget(self.origin_filter, 1)
        self.only_stock = QCheckBox(tr("mining.only_stock"))
        self.only_stock.setToolTip(tr("mining.only_stock_tooltip"))
        self.only_stock.setChecked(settings.value(self.STOCK_FILTER_KEY, False, type=bool))
        filters.addWidget(self.only_stock)
        layout.addLayout(filters)
        self.empty_label = QLabel(tr("mining.no_matches"), objectName="muted")
        self.empty_label.setWordWrap(True)
        self.empty_label.hide()
        layout.addWidget(self.empty_label)
        self.tree = QTreeWidget()
        self.tree.collator = QCollator(QLocale(get_language()))
        self.tree.setColumnCount(len(self.COLUMNS))
        self.tree.setHeaderLabels([tr("mining.name"), tr("mining.vehicle"), tr("mining.carrier_marked", value=tr("mining.carrier")),
                                   tr("mining.total"), tr("mining.average_price"),
                                   tr("mining.value_class")])
        self.tree.headerItem().setTextAlignment(0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.tree.headerItem().setToolTip(2, tr("mining.carrier_header_help"))
        for column in range(1, len(self.COLUMNS)):
            self.tree.headerItem().setTextAlignment(column, Qt.AlignmentFlag.AlignCenter)
        self.carrier_delegate = _CarrierDelegate(self.tree)
        self.tree.setItemDelegate(self.carrier_delegate)
        self.tree.setRootIsDecorated(False)
        self.tree.setIndentation(0)
        self.tree.setAlternatingRowColors(False)
        self.tree.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
        self.tree.setEditTriggers(QTreeWidget.EditTrigger.NoEditTriggers)
        self.tree.itemDoubleClicked.connect(self._edit_carrier)
        layout.addWidget(self.tree, 1)
        locale = QLocale(get_language())
        for commodity in commodities:
            price = commodity.average_price
            category = value_class(price)
            item = _MiningItem(self.tree, [tr(commodity.name_key), "—", "—", "—",
                locale.toString(price) if price is not None else "—",
                "● " + tr("mining." + category) if category else "—"])
            if price is None:
                item.setToolTip(4, tr("mining.reference_unknown"))
                item.setToolTip(5, tr("mining.reference_unknown"))
            self.items[commodity.symbol] = item
            self._search_text[commodity.symbol] = "\n".join((
                tr(commodity.name_key), tr_for_language("en", commodity.name_key),
                commodity.symbol,
            )).casefold()
            item.setData(0, Qt.ItemDataRole.UserRole, commodity.symbol)
            item.setData(4, Qt.ItemDataRole.UserRole, price)
            item.setData(5, Qt.ItemDataRole.UserRole,
                         {"low": 0, "medium": 1, "high": 2}.get(category))
            item.setTextAlignment(0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            for column in range(1, len(self.COLUMNS)):
                item.setTextAlignment(column, Qt.AlignmentFlag.AlignCenter)
            item.setSizeHint(0, QSize(0, max(30, self.fontMetrics().height() + 12)))
            price_font = item.font(4)
            price_font.setBold(True)
            item.setFont(4, price_font)
            item.setToolTip(0, tr(commodity.name_key))
        _migrate_columns(settings, self.COLUMNS)
        persist_header_layout(self.tree.header(), settings, "materials/mining/columns",
                              columns=self.COLUMNS, default_widths=(320, 95, 95, 95, 180, 160))
        saved = settings.value(self.SORT_KEY)
        column, order = 4, Qt.SortOrder.DescendingOrder
        if (isinstance(saved, dict) and saved.get("column") in self.COLUMNS
                and saved.get("direction") in ("ascending", "descending")):
            column = self.COLUMNS.index(saved["column"])
            order = (Qt.SortOrder.AscendingOrder if saved["direction"] == "ascending"
                     else Qt.SortOrder.DescendingOrder)
        self.tree.sortItems(column, order)
        self.tree.setSortingEnabled(True)
        self.tree.header().sortIndicatorChanged.connect(self._save_sort)
        self.search.textChanged.connect(self._apply_filters)
        self.class_filter.currentIndexChanged.connect(self._class_filter_changed)
        self.origin_filter.currentIndexChanged.connect(self._origin_filter_changed)
        self.only_stock.toggled.connect(self._stock_filter_changed)
        self.set_light_mode(str(settings.value("ui_theme", "dark")) == "light")
        self._apply_filters()
        self.set_inventory(MiningInventory(0, ""))
        self.controller = controller
        if self.controller is None and state is not None:
            from cmdrhelper.mining_controller import MiningInventoryController
            self.controller = MiningInventoryController(state, self)
        if self.controller is not None:
            self.controller.loading.connect(lambda: self.set_inventory(MiningInventory(0, "")))
            self.controller.ready.connect(self.set_inventory)
            self.refresh_button.clicked.connect(self._begin_refresh)
            self.controller.refreshFinished.connect(self._refresh_finished)
        self.refresh_button.setEnabled(self.controller is not None)

    def set_inventory(self, inventory):
        self._inventory = inventory
        self.tree.setSortingEnabled(False)
        locale = QLocale(get_language())
        for symbol, item in self.items.items():
            for column, count in enumerate(inventory.stock(symbol), 1):
                item.setData(column, Qt.ItemDataRole.UserRole, count)
                text = locale.toString(count) if count is not None else "—"
                item.setText(column, tr("mining.carrier_marked", value=text) if column == 2 else text)
                item.setToolTip(column, tr("mining.stock_unknown") if count is None else "")
            record = inventory.carrier_records.get(symbol)
            tooltip = ""
            if record:
                stamp = QDateTime.fromString(record.get("confirmed_at", ""), Qt.DateFormat.ISODateWithMs)
                time_text = locale.toString(stamp.toLocalTime(), QLocale.FormatType.ShortFormat) if stamp.isValid() else record.get("confirmed_at", "")
                tooltip = tr("mining.carrier_confirmed", time=time_text)
                if record.get("status") == "tracked":
                    tooltip += "\n" + tr("mining.carrier_tracked")
                elif record.get("status") == "inconsistent":
                    tooltip += "\n" + tr("mining.carrier_inconsistent")
            elif inventory.carrier is None or inventory.carrier.get(symbol) is None:
                tooltip = tr("mining.carrier_unknown_help")
            item.setToolTip(2, tr("mining.carrier_edit_hint") + ("\n" + tooltip if tooltip else ""))
            self._style_stock(item)
        self.tree.setSortingEnabled(True)
        self._apply_filters()

    def _edit_carrier(self, item, column):
        if column != 2:
            return
        from .mining_carrier_dialog import CarrierStockDialog
        inventory = self._inventory
        identity = (inventory.commander_id, inventory.fid, inventory.carrier_id)
        symbol = item.data(0, Qt.ItemDataRole.UserRole)
        editable = (self.controller is not None and inventory.carrier_id is not None
                    and inventory.carrier_feed is not None)
        dialog = CarrierStockDialog(item.text(0), inventory.stock(symbol)[1], editable, self)
        try:
            if dialog.exec() == QDialog.DialogCode.Accepted and editable:
                try:
                    self.controller.confirm_carrier(symbol, dialog.count, identity)
                except ValueError:
                    QMessageBox.warning(self, tr("mining.carrier_edit"), tr("mining.carrier_unavailable"))
        finally:
            dialog.deleteLater()

    def _begin_refresh(self):
        if self._refresh_state == "busy":
            return
        self.refresh_animation.stop()
        self.refresh_status_timer.stop()
        self.refresh_status.hide()
        self._refresh_state, self._refresh_result = "busy", None
        self.refresh_button.setEnabled(False)
        self.refresh_animation.start()
        self.controller.refresh_now()

    def _refresh_finished(self, result):
        if self._refresh_state != "busy":
            return
        self._refresh_result = result
        if result == "error" or not self.isVisible():
            self.refresh_animation.stop()
        if self.refresh_animation.state() != QVariantAnimation.State.Running:
            self._finish_refresh_feedback()

    def _finish_refresh_feedback(self):
        if self._refresh_result is None:
            return  # Visual duration elapsed; the real read is still running.
        self._refresh_state = "error" if self._refresh_result == "error" else "ready"
        self.refresh_button.setEnabled(self.controller is not None)
        self.refresh_status.setText(tr("mining.refresh_" + self._refresh_result))
        self.refresh_status.show()
        self._paint_refresh()
        if self._refresh_state != "error" and self.isVisible():
            self.refresh_status_timer.start()
        elif self._refresh_state != "error":
            self.refresh_status.hide()

    def _paint_refresh(self, progress=0.0):
        green = QColor("#37852d" if self._light_mode else "#79d45a")
        red = QColor("#b83232" if self._light_mode else "#ff6b6b")
        accent = red if self._refresh_state == "error" else green
        if self._refresh_state == "busy":
            accent = QColor.fromHsvF((0.33 + float(progress)) % 1.0, 0.45, 0.75)
        base = QColor("#ffffff" if self._light_mode else "#111820")
        background = QColor(*[round(base.getRgb()[i] * 0.88 + accent.getRgb()[i] * 0.12)
                              for i in range(3)])
        foreground = ("#252b31" if self._light_mode else "#d7dce1") if self._refresh_state == "busy" else accent.name()
        self.refresh_button.setStyleSheet(
            f"QPushButton {{ background: {background.name()}; color: {foreground}; border: 1px solid {accent.name()}; }}")
        self.refresh_status.setStyleSheet(f"color: {red.name() if self._refresh_state == 'error' else green.name()};")

    def hideEvent(self, event):
        self.refresh_animation.stop()
        self.refresh_status_timer.stop()
        if self._refresh_state == "busy" and self._refresh_result is not None:
            self._finish_refresh_feedback()
        if self._refresh_state != "error":
            self.refresh_status.hide()
        super().hideEvent(event)

    def _stock_filter_changed(self, checked):
        self.settings.setValue(self.STOCK_FILTER_KEY, checked)
        self.settings.sync()
        self._apply_filters()

    def _style_stock(self, item):
        for column in (1, 2, 3):
            count = item.data(column, Qt.ItemDataRole.UserRole)
            positive = count is not None and count > 0
            item.setForeground(column, QColor(self._stock_colors[1 if positive else 0]))
            font = item.font(column)
            font.setBold(positive)
            item.setFont(column, font)

    def _apply_filters(self, *_):
        query = self.search.text().strip().casefold()
        rank = self.class_filter.currentData()
        origin = self.origin_filter.currentData()
        visible = 0
        # Preserve the items and header: filtering never rebuilds or resizes columns.
        for row in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(row)
            matches = (query in self._search_text[item.data(0, Qt.ItemDataRole.UserRole)]
                       and (origin == "all" or self._origins[item.data(0, Qt.ItemDataRole.UserRole)] in (origin, "both"))
                       and (rank is None or rank == item.data(5, Qt.ItemDataRole.UserRole))
                       and (not self.only_stock.isChecked() or any(
                           item.data(column, Qt.ItemDataRole.UserRole) is not None
                           and item.data(column, Qt.ItemDataRole.UserRole) > 0
                           for column in (1, 2, 3))))
            item.setHidden(not matches)
            visible += matches
        self.empty_label.setVisible(visible == 0)

    def set_origin_filter(self, origin):
        index = self.origin_filter.findData(origin)
        self.origin_filter.setCurrentIndex(max(0, index))

    def _origin_filter_changed(self, *_):
        self.settings.setValue(self.ORIGIN_FILTER_KEY, self.origin_filter.currentData())
        self.settings.sync()
        self._apply_filters()

    def _class_filter_changed(self, *_):
        rank = self.class_filter.currentData()
        self.settings.setValue(self.CLASS_FILTER_KEY, "all" if rank is None else str(rank))
        self.settings.sync()
        self._apply_filters()

    def set_light_mode(self, light):
        self._light_mode = light
        self._paint_refresh(self.refresh_animation.currentValue() or 0.0)
        self.carrier_delegate.light = light
        # Reuse styles.py's statusOk, statusWarn and muted foregrounds.
        colors = (("#65717c", "#b36a00", "#37852d") if light
                  else ("#8e969e", "#f0ad4e", "#79d45a"))
        self._stock_colors = (colors[0], colors[2])
        self.carrier_delegate.color = QColor(colors[2])
        self.tree.viewport().update()
        for row in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(row)
            rank = item.data(5, Qt.ItemDataRole.UserRole)
            item.setForeground(5, QColor(colors[rank if rank is not None else 0]))
            self._style_stock(item)

    def _save_sort(self, column, order):
        if 0 <= column < len(self.COLUMNS):
            self.settings.setValue(self.SORT_KEY, {
                "column": self.COLUMNS[column],
                "direction": "ascending" if order == Qt.SortOrder.AscendingOrder else "descending",
            })
            self.settings.sync()
