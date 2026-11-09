"""One offline mining table, with independent, identity-based settings."""
from cmdrhelper import performance_profile as profile
from contextlib import contextmanager

from PySide6.QtCore import QCollator, QLocale, Qt, QTimer, QVariantAnimation, QDateTime, QEvent, QPersistentModelIndex
from PySide6.QtGui import QBrush, QColor, QPalette
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTreeWidget, QTreeWidgetItem, QPushButton, QCheckBox, QDialog, QMessageBox, QStyledItemDelegate, QStyle, QHeaderView,
    QStyleOptionViewItem, QToolTip, QSizePolicy,
)

from cmdrhelper.commodity_master import lookup_by_symbol
from cmdrhelper.ui.mission_cargo import (CargoMissionLegend, MissionCargoDelegate, POSSIBLE_MISSION_CARGO_ROLE,
    current_possible_mission_cargo, possible_mission_cargo_tooltip)
from cmdrhelper.i18n import get_language, tr, tr_for_language
from cmdrhelper.mining_catalog import MINING_COMMODITIES, value_class
from cmdrhelper.ui.table_widths import persist_header_layout, _validated_widths
from cmdrhelper.ui.preferences import set_preference
from cmdrhelper.mining_inventory import MiningInventory
from cmdrhelper.ui.material_row_style import THEMES
from cmdrhelper.ui.carrier_edit_marker import CarrierHeader, marker_color, marker_layout, paint_marker_text


def _migrate_columns(settings, columns):
    """Migrate only mining layouts, keeping existing identities and widths."""
    key = "materials/mining/columns"
    saved = settings.value(key)
    legacy = ["name", "average_price", "value_class"]
    previous = ["name", "srv", "ship", "carrier", "total", "average_price", "value_class"]
    combined = ["name", "vehicle", "carrier", "total", "average_price", "value_class"]
    if (not isinstance(saved, dict) or type(saved.get("version")) is not int
            or saved["version"] != 1 or saved.get("columns") not in (legacy, combined, previous)):
        return
    old = saved["columns"]
    widths = _validated_widths(saved.get("widths"), len(old))
    order = saved.get("order")
    if (widths is None or not isinstance(order, list) or len(order) != len(old)
            or any(type(i) is not int for i in order) or sorted(order) != list(range(len(old)))):
        return
    migrated_order = []
    sizes = dict(zip(old, widths))
    for logical in order:
        name = old[logical]
        if name == "vehicle":
            migrated_order.extend([columns.index("srv"), columns.index("ship")])
        else:
            migrated_order.append(columns.index(name))
            if name == "name" and old == legacy:
                migrated_order.extend([1, 2, 3, 4])
    if old != previous:
        sizes["srv"] = sizes["ship"] = sizes.get("vehicle", 95)
    migrated_order.extend(i for i in range(len(columns)) if i not in migrated_order)
    settings.setValue(key, dict(version=1, columns=list(columns),
        widths=[sizes.get(name, 95) for name in columns], order=migrated_order))
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


class _CarrierDelegate(MissionCargoDelegate):
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
        self._visible_rows = None
        tree.model().layoutChanged.connect(self.invalidate_rows)
        tree.model().modelReset.connect(self.invalidate_rows)
        tree.model().rowsInserted.connect(self.invalidate_rows)
        tree.model().rowsRemoved.connect(self.invalidate_rows)

    def invalidate_rows(self, *_):
        self._visible_rows = None

    def visible_row(self, row):
        if self._visible_rows is None:
            self._visible_rows = {}
            visible = 0
            for i in range(self.tree.topLevelItemCount()):
                self._visible_rows[i] = visible
                visible += not self.tree.topLevelItem(i).isHidden()
        return self._visible_rows.get(row, 0)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.MouseMove:
            self.hover_position = event.position().toPoint()
            self.hovered = QPersistentModelIndex(self.tree.indexAt(self.hover_position))
            watched.update()
        elif event.type() in (QEvent.Type.Leave, QEvent.Type.Hide):
            self.hover_position = None
            self.hovered = QPersistentModelIndex()
            watched.update()
        elif event.type() == QEvent.Type.ToolTip and self.tree.isEnabled():
            index = self.tree.indexAt(event.pos())
            if (index.isValid() and index.flags() & Qt.ItemIsEnabled
                    and index.column() == 3 and self.marker_rect(index).contains(event.pos())):
                QToolTip.showText(event.globalPos(), tr("mining.carrier_edit"), watched, self.marker_rect(index))
                return True
        return super().eventFilter(watched, event)

    def marker_rect(self, index):
        option = QStyleOptionViewItem()
        option.initFrom(self.tree)
        self.initStyleOption(option, index)
        option.rect = self.tree.visualRect(index)
        rect = self.tree.style().subElementRect(QStyle.SE_ItemViewItemText, option, self.tree)
        return marker_layout(option.text, option.fontMetrics, rect, option.displayAlignment,
                             self.tree.layoutDirection())[2]

    def paint(self, painter, option, index):
        if index.column() != 3:
            return super().paint(painter, option, index)
        option = QStyleOptionViewItem(option)
        self.initStyleOption(option, index)
        rect = self.tree.style().subElementRect(QStyle.SE_ItemViewItemText, option, self.tree)
        layout = marker_layout(option.text, option.fontMetrics, rect, option.displayAlignment,
                               self.tree.layoutDirection())
        option.text = ""
        painter.save()
        painter.setClipRect(option.rect)
        self.tree.style().drawControl(QStyle.CE_ItemViewItem, option, painter, self.tree)
        painter.setFont(option.font)
        enabled = bool(option.state & QStyle.State_Enabled) and bool(index.flags() & Qt.ItemIsEnabled)
        hovered = self.hover_position is not None and layout[2].contains(self.hover_position)
        group = QPalette.Active if enabled else QPalette.Disabled
        color = marker_color(self.light, hovered) if enabled else option.palette.color(group, QPalette.Text)
        paint_marker_text(painter, layout, option.palette.color(group, QPalette.Text), color)
        painter.restore()

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setHeight(max(30, size.height(), option.fontMetrics.height() + 12))
        return size

    @staticmethod
    def _blend(base, accent, amount):
        return QColor.fromRgbF(*(a * (1 - amount) + b * amount for a, b in
                                zip(base.getRgbF()[:3], accent.getRgbF()[:3])))

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        # Count visible rows in their current sorted order, without modifying
        # item data, filters or persisted settings.
        row = self.visible_row(index.row())
        theme = THEMES[self.light]
        background = QColor(theme["rows"][row % 5])
        hovered = self.hovered
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        if selected:
            background = self._blend(background, QColor(theme["selected"]), 0.35)
        elif hovered.isValid() and hovered.row() == index.row():
            background = self._blend(background, QColor(theme["hover"]), 0.25)
        if index.column() == 3 and hovered == index:
            background = self._blend(background, self.color, 0.11)
        # Native selection would replace both background and semantic text
        # colors. Keep the item's foreground and paint only our subtle tones.
        option.state &= ~(QStyle.StateFlag.State_Selected | QStyle.StateFlag.State_MouseOver
                          | QStyle.StateFlag.State_HasFocus)
        option.backgroundBrush = QBrush(background)


class MiningView(QWidget):
    COLUMNS = ("name", "srv", "ship", "carrier", "total", "average_price", "value_class", "own_sell_price")
    SORT_KEY = "materials/mining/sort"
    STOCK_FILTER_KEY = "materials/mining/only_stock"
    ORIGIN_FILTER_KEY = "materials/mining/origin_filter"
    CLASS_FILTER_KEY = "materials/mining/value_class_filter"

    def __init__(self, settings, parent=None, *, commodities=MINING_COMMODITIES, state=None, controller=None):
        super().__init__(parent)
        self.settings = settings
        self.state = state
        commodities = tuple(commodities)
        self._search_text = {}
        self.items = {}
        self._origins = {c.symbol: c.origin for c in commodities}
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.content = QWidget()
        self.content.setMaximumWidth(1215)
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
        self.stock_legend = QWidget()
        self.stock_legend.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        legend_layout = QHBoxLayout(self.stock_legend)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(14)
        self.stock_legend_dots, self.stock_legend_labels = [], []
        for name, tooltip in (
                ("confirmed", tr("mining.stock_confirmed")),
                ("last_known", tr("mining.stock_tracked") + "\n" + tr("mining.stock_stale")),
                ("unknown", tr("mining.stock_unknown")),
                ("inconsistent", tr("mining.carrier_inconsistent"))):
            group = QHBoxLayout()
            group.setSpacing(4)
            dot = QLabel("●")
            label = QLabel(tr("mining.legend_" + name))
            label.setToolTip(tooltip)
            dot.setToolTip(tooltip)
            group.addWidget(dot)
            group.addWidget(label)
            legend_layout.addLayout(group)
            self.stock_legend_dots.append(dot)
            self.stock_legend_labels.append(label)
        legend_layout.addStretch(1)
        layout.addWidget(self.stock_legend)
        self.cargo_mission_legend = CargoMissionLegend()
        layout.addWidget(self.cargo_mission_legend)
        self.tree = QTreeWidget()
        self.tree.setHeader(CarrierHeader(self.tree))
        self.tree.collator = QCollator(QLocale(get_language()))
        self.tree.setColumnCount(len(self.COLUMNS))
        # Populate the initial projection before enabling content measurement.
        self.tree.header().setSectionResizeMode(QHeaderView.Fixed)
        self._table_update_depth = 0
        self.tree.setHeaderLabels([tr("mining.name"), tr("mining.srv"), tr("mining.ship"), tr("mining.carrier_marked", value=tr("mining.carrier")),
                                   tr("mining.total"), tr("mining.average_price"),
                                   tr("mining.value_class"), tr("mining.own_sell_price")])
        self.tree.headerItem().setTextAlignment(0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.tree.headerItem().setToolTip(3, tr("mining.carrier_header_help"))
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
            item = _MiningItem(self.tree, [tr(commodity.name_key), "—", "—", "—", "—",
                locale.toString(price) if price is not None else "—",
                "● " + tr("mining." + category) if category else "—", "—"])
            if price is None:
                item.setToolTip(5, tr("mining.reference_unknown"))
                item.setToolTip(6, tr("mining.reference_unknown"))
            self.items[commodity.symbol] = item
            self._search_text[commodity.symbol] = "\n".join((
                tr(commodity.name_key), tr_for_language("en", commodity.name_key),
                commodity.symbol,
            )).casefold()
            item.setData(0, Qt.ItemDataRole.UserRole, commodity.symbol)
            item.setData(5, Qt.ItemDataRole.UserRole, price)
            item.setData(6, Qt.ItemDataRole.UserRole,
                         {"low": 0, "medium": 1, "high": 2}.get(category))
            item.setTextAlignment(0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            for column in range(1, len(self.COLUMNS)):
                item.setTextAlignment(column, Qt.AlignmentFlag.AlignCenter)
            price_font = item.font(5)
            price_font.setBold(True)
            item.setFont(5, price_font)
            item.setToolTip(0, tr(commodity.name_key))
        _migrate_columns(settings, self.COLUMNS)
        saved = settings.value(self.SORT_KEY)
        if isinstance(saved, dict) and saved.get("column") == "vehicle":
            saved = {**saved, "column": "ship"}
            settings.setValue(self.SORT_KEY, saved)
            settings.sync()
        column, order = 5, Qt.SortOrder.DescendingOrder
        if (isinstance(saved, dict) and saved.get("column") in self.COLUMNS
                and saved.get("direction") in ("ascending", "descending")):
            column = self.COLUMNS.index(saved["column"])
            order = (Qt.SortOrder.AscendingOrder if saved["direction"] == "ascending"
                     else Qt.SortOrder.DescendingOrder)
        self.tree.sortItems(column, order)
        self.tree.header().sortIndicatorChanged.connect(self._save_sort)
        self.search.textChanged.connect(self._apply_filters)
        self.class_filter.currentIndexChanged.connect(self._class_filter_changed)
        self.origin_filter.currentIndexChanged.connect(self._origin_filter_changed)
        self.only_stock.toggled.connect(self._stock_filter_changed)
        self.set_light_mode(str(settings.value("ui_theme", "dark")) == "light")
        from .loading_state import LoadingState
        self.loading_state = LoadingState(self.tree)
        self.controller = controller
        if self.controller is None and state is not None:
            self.controller = getattr(state, "mining_inventory_controller", None)
            if self.controller is None:
                from cmdrhelper.mining_controller import MiningInventoryController
                self.controller = MiningInventoryController(state, self)
        if self.controller is not None:
            self.controller.loading.connect(self._begin_inventory_loading)
            self.controller.ready.connect(self.set_inventory)
            self.refresh_button.clicked.connect(self._begin_refresh)
            self.controller.refreshFinished.connect(self._refresh_finished)
        self.refresh_button.setEnabled(self.controller is not None)
        if self.controller is not None:
            existing = getattr(self.controller, "_last_inventory", None)
            if existing is not None:
                self.set_inventory(existing)
            else:
                self._begin_inventory_loading()
        else:
            self.set_inventory(MiningInventory(0, ""))

        self.market_controller = None
        self.own_market_prices = {}
        self._market_status = 'ok'
        if state is not None and hasattr(state, 'database'):
            from cmdrhelper.mining_market_controller import MiningMarketController
            self.market_controller = MiningMarketController(state, self, commodities=commodities)
            self.market_controller.ready.connect(self.set_market_prices)
            self.refresh_button.clicked.connect(self.market_controller.request)
        self._render_market_prices()
        self.tree.setSortingEnabled(True)
        persist_header_layout(self.tree.header(), settings, "materials/mining/columns",
                              columns=self.COLUMNS, auto_widths=True)
        for name in ('cargoSnapshotChanged', 'changed', 'commanderIdentityChanged',
                     'viewedCommanderChanged', 'shipLoadoutChanged'):
            signal = getattr(state, name, None)
            if signal is not None:
                signal.connect(self._refresh_mission_cargo)
        for name in ('ready', 'loading', 'publicationChanged'):
            signal = getattr(self.controller, name, None)
            if signal is not None:
                signal.connect(self._refresh_mission_cargo)
        self._refresh_mission_cargo()

    @profile.measure('slot.mining.refresh_mission_cargo')
    def _refresh_mission_cargo(self, *_):
        possible = current_possible_mission_cargo(self.state)
        for symbol, item in self.items.items():
            master = lookup_by_symbol(symbol)
            details = possible.get(master.frontier_id) if master else None
            if item.data(0, POSSIBLE_MISSION_CARGO_ROLE) != details:
                item.setData(0, POSSIBLE_MISSION_CARGO_ROLE, details)
            tooltip = item.text(0)
            if details:
                tooltip += '\n' + possible_mission_cargo_tooltip(details)
            if item.toolTip(0) != tooltip:
                item.setToolTip(0, tooltip)

    @contextmanager
    def _table_update(self):
        if self._table_update_depth:
            self._table_update_depth += 1
            try:
                yield
            finally:
                self._table_update_depth -= 1
            return
        header = self.tree.header()
        modes = [header.sectionResizeMode(i) for i in range(header.count())]
        updates = self.tree.updatesEnabled()
        sorting = self.tree.isSortingEnabled()
        self._table_update_depth = 1
        self.tree.setUpdatesEnabled(False)
        header.setSectionResizeMode(QHeaderView.Fixed)
        self.tree.setSortingEnabled(False)
        try:
            yield
        finally:
            self.tree.setSortingEnabled(sorting)
            self.carrier_delegate.invalidate_rows()
            for i, mode in enumerate(modes):
                header.setSectionResizeMode(i, mode)
            self._table_update_depth = 0
            if QHeaderView.ResizeToContents in modes:
                header.resizeSections()
            self.tree.setUpdatesEnabled(updates)

    def set_market_prices(self, result):
        self.own_market_prices = {q.symbol.casefold(): q for q in result.quotes}
        self._market_status = result.status
        self._render_market_prices()

    def _render_market_prices(self):
        help_text = tr('mining.own_price_help')
        if self.tree.headerItem().toolTip(7) != help_text:
            self.tree.headerItem().setToolTip(7, help_text)
        notice = tr('mining.reference_short') + (
            ' · ' + tr('mining.own_price_error') if self._market_status == 'error' else '')
        if self.notice.text() != notice:
            self.notice.setText(notice)
        locale = QLocale(get_language())
        changes = []
        for symbol, item in self.items.items():
            quote = self.own_market_prices.get(symbol)
            price = quote.price if quote is not None else None
            text = locale.toString(price) if price is not None else '—'
            if quote is None:
                key = 'mining.own_price_error' if self._market_status == 'error' else 'mining.own_price_none'
                tooltip = tr(key) + '\n' + help_text
            else:
                stamp = QDateTime.fromString(quote.timestamp.isoformat(), Qt.DateFormat.ISODate)
                observed = locale.toString(stamp.toLocalTime(), QLocale.FormatType.ShortFormat)
                tooltip = '\n'.join((help_text, observed,
                    tr('trade.station') + ': ' + (quote.station or '—'),
                    tr('trade.system') + ': ' + (quote.system or '—'),
                    tr('trade.quantity') + ': ' + locale.toString(quote.count),
                    tr('trade.price') + ': ' + locale.toString(quote.price) + ' Cr/t'))
            if (item.data(7, Qt.ItemDataRole.UserRole), item.text(7), item.toolTip(7)) != (price, text, tooltip):
                changes.append((item, price, text, tooltip))
        if not changes:
            return
        with self._table_update():
            for item, price, text, tooltip in changes:
                if item.data(7, Qt.ItemDataRole.UserRole) != price:
                    item.setData(7, Qt.ItemDataRole.UserRole, price)
                if item.text(7) != text:
                    item.setText(7, text)
                if item.toolTip(7) != tooltip:
                    item.setToolTip(7, tooltip)

    def showEvent(self, event):
        super().showEvent(event)
        if self.market_controller is not None:
            self.market_controller.set_active(True)
        self._render_market_prices()


    def _begin_inventory_loading(self):
        self.set_inventory(MiningInventory(0, ""))
        self.loading_state.begin()

    def set_inventory(self, inventory):
        # Always adopt the current identity/feed, even when its visible values
        # match. Only the presentation is compared; no inventory is cached here.
        self._inventory = inventory
        locale = QLocale(get_language())
        changes = []
        for symbol, item in self.items.items():
            cells = []
            for column, count in enumerate(inventory.stock(symbol), 1):
                text = locale.toString(count) if count is not None else "—"
                quality = "confirmed" if count is not None else "unknown"
                display = count
                tooltip = tr("mining.stock_" + quality)
                if column in (1, 2):
                    vessel = "SRV" if column == 1 else "Ship"
                    display, quality = inventory.displayed_stock(vessel, symbol)
                    text = locale.toString(display) if display is not None else "—"
                    if quality == "stale":
                        text = tr("mining.stock_stale_value", value=text)
                    tooltip = tr("mining.stock_" + quality)
                    record = inventory.vehicle_records.get(vessel, {})
                    if record.get("confirmed_at"):
                        tooltip += "\n" + record["confirmed_at"]
                    if quality == "stale":
                        tooltip += "\nShipID: " + str(record.get("ship_id", "—"))
                cells.append([count, quality, display,
                    tr("mining.carrier_marked", value=text) if column == 3 else text, tooltip])
            record = inventory.carrier_records.get(symbol)
            tooltip = tr("mining.stock_" + cells[2][1])
            if record:
                cells[2][1] = record.get("status", cells[2][1])
                stamp = QDateTime.fromString(record.get("confirmed_at", ""), Qt.DateFormat.ISODateWithMs)
                time_text = locale.toString(stamp.toLocalTime(), QLocale.FormatType.ShortFormat) if stamp.isValid() else record.get("confirmed_at", "")
                tooltip = tr("mining.carrier_confirmed", time=time_text)
                if record.get("status") == "tracked":
                    tooltip += "\n" + tr("mining.carrier_tracked")
                elif record.get("status") == "inconsistent":
                    tooltip += "\n" + tr("mining.carrier_inconsistent")
            elif inventory.carrier is None or inventory.carrier.get(symbol) is None:
                tooltip = tr("mining.carrier_unknown_help")
            cells[2][4] = tr("mining.carrier_edit_hint") + ("\n" + tooltip if tooltip else "")
            if cells[3][0] is not None:
                quality = "tracked" if any(cell[1] == "tracked" for cell in cells[:3]) else "confirmed"
                cells[3][1] = quality
                cells[3][4] = tr("mining.stock_" + quality)
            if any([item.data(column, Qt.ItemDataRole.UserRole),
                    item.data(column, Qt.ItemDataRole.UserRole + 1),
                    item.data(column, Qt.ItemDataRole.UserRole + 2),
                    item.text(column), item.toolTip(column)] != cell
                   for column, cell in enumerate(cells, 1)):
                changes.append((item, cells))
        if changes:
            with self._table_update():
                for item, cells in changes:
                    for column, (count, quality, display, text, tooltip) in enumerate(cells, 1):
                        for role, value in ((Qt.ItemDataRole.UserRole, count),
                                            (Qt.ItemDataRole.UserRole + 1, quality),
                                            (Qt.ItemDataRole.UserRole + 2, display)):
                            if item.data(column, role) != value:
                                item.setData(column, role, value)
                        if item.text(column) != text:
                            item.setText(column, text)
                        if item.toolTip(column) != tooltip:
                            item.setToolTip(column, tooltip)
                    self._style_stock(item)
                self._apply_filters()
        if hasattr(self, "loading_state"):
            self.loading_state.finish()

    def _edit_carrier(self, item, column):
        if column != 3:
            return
        from .mining_carrier_dialog import CarrierStockDialog
        inventory = self._inventory
        identity = (inventory.commander_id, inventory.fid, inventory.carrier_id)
        symbol = item.data(0, Qt.ItemDataRole.UserRole)
        editable = (self.controller is not None and inventory.carrier_id is not None
                    and inventory.carrier_feed is not None)
        dialog = CarrierStockDialog(item.text(0), inventory.stock(symbol).carrier_amount, editable, self)
        try:
            if dialog.exec() == QDialog.DialogCode.Accepted and editable:
                try:
                    self.controller.confirm_carrier(symbol, dialog.count, identity)
                except (ValueError, OSError):
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
        if self.market_controller is not None:
            self.market_controller.set_active(False)
        self.refresh_animation.stop()
        self.refresh_status_timer.stop()
        if self._refresh_state == "busy" and self._refresh_result is not None:
            self._finish_refresh_feedback()
        if self._refresh_state != "error":
            self.refresh_status.hide()
        super().hideEvent(event)

    def _stock_filter_changed(self, checked):
        set_preference(self.settings, self.STOCK_FILTER_KEY, checked)
        self._apply_filters()

    def _style_stock(self, item):
        for column in (1, 2, 3, 4):
            count = item.data(column, Qt.ItemDataRole.UserRole)
            positive = count is not None and count > 0
            quality = item.data(column, Qt.ItemDataRole.UserRole + 1)
            stale = quality == "stale"
            color = (3 if quality == "inconsistent" else
                     2 if quality in ("stale", "tracked") else
                     1 if count is not None and quality in ("confirmed", "manual") else 0)
            item.setForeground(column, QColor(self._stock_colors[color]))
            font = item.font(column)
            font.setBold(positive)
            font.setItalic(stale)
            item.setFont(column, font)

    def _apply_filters(self, *_):
        query = self.search.text().strip().casefold()
        rank = self.class_filter.currentData()
        origin = self.origin_filter.currentData()
        visible = 0
        # Preserve items and sorting; measure only the remaining visible rows.
        for row in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(row)
            matches = (query in self._search_text[item.data(0, Qt.ItemDataRole.UserRole)]
                       and (origin == "all" or self._origins[item.data(0, Qt.ItemDataRole.UserRole)] in (origin, "both"))
                       and (rank is None or rank == item.data(6, Qt.ItemDataRole.UserRole))
                       and (not self.only_stock.isChecked() or any(
                           item.data(column, Qt.ItemDataRole.UserRole + 2) is not None
                           and item.data(column, Qt.ItemDataRole.UserRole + 2) > 0
                           for column in (1, 2, 3))))
            item.setHidden(not matches)
            visible += matches
        self.carrier_delegate.invalidate_rows()
        self.empty_label.setVisible(visible == 0)
        if not self._table_update_depth:
            self.tree.header().resizeSections(QHeaderView.ResizeMode.ResizeToContents)

    def set_origin_filter(self, origin):
        index = self.origin_filter.findData(origin)
        self.origin_filter.setCurrentIndex(max(0, index))

    def _origin_filter_changed(self, *_):
        set_preference(self.settings, self.ORIGIN_FILTER_KEY, self.origin_filter.currentData())
        self._apply_filters()

    def _class_filter_changed(self, *_):
        rank = self.class_filter.currentData()
        set_preference(self.settings, self.CLASS_FILTER_KEY, "all" if rank is None else str(rank))
        self._apply_filters()

    def set_light_mode(self, light):
        self._light_mode = light
        self._paint_refresh(self.refresh_animation.currentValue() or 0.0)
        self.carrier_delegate.light = light
        self.tree.header().light = light
        self.tree.header().viewport().update()
        # Reuse styles.py's statusOk, statusWarn and muted foregrounds.
        colors = (("#65717c", "#b36a00", "#37852d") if light
                  else ("#8e969e", "#f0ad4e", "#79d45a"))
        self._stock_colors = (colors[0], colors[2], colors[1], "#b83232" if light else "#ff6b6b")
        for dot, color_index in zip(self.stock_legend_dots, (1, 2, 0, 3)):
            dot.setStyleSheet(f"color: {self._stock_colors[color_index]};")
        self.carrier_delegate.color = QColor(colors[2])
        self.tree.viewport().update()
        for row in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(row)
            rank = item.data(6, Qt.ItemDataRole.UserRole)
            item.setForeground(6, QColor(colors[rank if rank is not None else 0]))
            self._style_stock(item)

    def _save_sort(self, column, order):
        if 0 <= column < len(self.COLUMNS):
            set_preference(self.settings, self.SORT_KEY, {
                "column": self.COLUMNS[column],
                "direction": "ascending" if order == Qt.SortOrder.AscendingOrder else "descending",
            })
