"""Odyssey stacks with a separate, manually confirmed private carrier inventory."""
from PySide6.QtCore import QCollator, QLocale, QSize, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QPalette
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTreeWidget, QTreeWidgetItem, QStyle, QDialog, QMessageBox, QToolButton, QPushButton

from cmdrhelper.i18n import tr, get_language
from cmdrhelper.odyssey_inventory import CATEGORIES, OdysseyInventory
from cmdrhelper.odyssey_catalog import FILTERS, capacity, merge_inventory
from cmdrhelper.odyssey_ranks import rating, sort_priority
from cmdrhelper.odyssey_controller import OdysseyController
from cmdrhelper.odyssey_carrier import CARRIER_CATEGORIES, material_amounts, inventory_carrier_capacity
from cmdrhelper.odyssey_market_capacity import read_reservation, usable_with_inventory
from cmdrhelper.ui.odyssey_carrier_dialog import OdysseyCarrierDialog, carrier_tooltip
from cmdrhelper.ui.material_view import MaterialCategoryTabs
from cmdrhelper.ui.material_row_style import MaterialRowDelegate, STRIPE_ROLE, COLLECTED_ROLE
from cmdrhelper.ui.table_widths import persist_header_layout
from cmdrhelper.ui import odyssey_cleanup


POSITIVE_STOCK_ROLE = Qt.ItemDataRole.UserRole + 3
STOCK_TEXT_COLORS = {False: "#c2a45e", True: "#806015"}
CARRIER_KEY_ROLE = Qt.ItemDataRole.UserRole + 4
CLEANUP_ROLE = Qt.ItemDataRole.UserRole + 5
CLEANUP_COLORS = {False: ("#482027", "#ffffff"), True: ("#f4d9dd", "#482027")}
# Keep stock column identities stable; rank is visually placed before name.
COLUMNS = ("name", "locker", "backpack", "carrier", "total", "usage", "rank")
RANK_COLUMN = COLUMNS.index("rank")
SORT_MODES = ("cleanup", "alphabetical", "rank_asc", "rank_desc")
RANK_COLORS = {
    False: dict(A="#77e39b", B="#76d9ee", C="#ffd078", D="#ff929c", **{"?": "#c0c7cf"}),
    True: dict(A="#12652f", B="#075b79", C="#805000", D="#a0192b", **{"?": "#505761"}),
}


def migrate_carrier_columns(settings):
    key = "materials/odyssey/columns"
    old = ("name", "locker", "backpack", "total", "usage")
    saved = settings.value(key)
    if not isinstance(saved, dict) or saved.get("version") != 1 or saved.get("columns") != list(old):
        return
    widths, order = saved.get("widths"), saved.get("order")
    if (not isinstance(widths, list) or len(widths) != 5
            or any(type(w) is not int or not 40 <= w <= 2000 for w in widths)
            or not isinstance(order, list) or len(order) != 5
            or any(type(i) is not int for i in order) or sorted(order) != list(range(5))):
        return
    names = [old[i] for i in order]
    names.insert(names.index("backpack") + 1, "carrier")
    sizes = dict(zip(old, widths), carrier=110)
    columns = COLUMNS[:-1]
    settings.setValue(key, dict(version=1, columns=list(columns),
        widths=[sizes[c] for c in columns], order=[columns.index(c) for c in names]))


def migrate_rank_column(settings):
    key = "materials/odyssey/columns"
    saved = settings.value(key)
    old = COLUMNS[:-1]
    if not isinstance(saved, dict) or saved.get("version") != 1 or saved.get("columns") != list(old):
        return
    widths, order = saved.get("widths"), saved.get("order")
    if (not isinstance(widths, list) or len(widths) != len(old)
            or any(type(w) is not int or not 40 <= w <= 2000 for w in widths)
            or not isinstance(order, list) or len(order) != len(old)
            or any(type(i) is not int for i in order) or sorted(order) != list(range(len(old)))):
        return
    order = list(order)
    order.insert(order.index(0), RANK_COLUMN)
    settings.setValue(key, dict(version=1, columns=list(COLUMNS), widths=[*widths, 65], order=order))


class OdysseyRowDelegate(MaterialRowDelegate):
    def initStyleOption(self, option, index):
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        super().initStyleOption(option, index)
        if not selected and index.siblingAtColumn(0).data(CLEANUP_ROLE):
            background, foreground = CLEANUP_COLORS[self.light]
            option.backgroundBrush = QBrush(QColor(background))
            option.palette.setColor(QPalette.ColorRole.Text, QColor(foreground))
        # Preserve the existing selection contrast and all row backgrounds.
        elif not selected and index.data(POSITIVE_STOCK_ROLE):
            option.palette.setColor(QPalette.ColorRole.Text, QColor(STOCK_TEXT_COLORS[self.light]))
        if not selected and index.column() == RANK_COLUMN:
            option.palette.setColor(QPalette.ColorRole.Text,
                                    QColor(RANK_COLORS[self.light].get(index.data(), RANK_COLORS[self.light]["?"])))
            option.font.setBold(True)


class OdysseyView(QWidget):
    def __init__(self, state, search, parent=None, *, controller=None):
        super().__init__(parent)
        self.state, self.search = state, search
        self.inventory = OdysseyInventory(0, "")
        self.rows, self.items, self.highlight = (), {}, {}
        self._baseline = False
        self._last_source = None
        self._last_time = ""
        self._loading = True
        self._cleanup_dialog = None
        self._cleanup_key = None
        self._cleanup_symbols = frozenset()
        light = str(state.settings.value("ui_theme", "dark")) == "light"
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.tabs = MaterialCategoryTabs(light)
        self.tabs.setExpanding(True)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.setElideMode(Qt.ElideNone)
        for category in CATEGORIES:
            self.tabs.addTab(tr("odyssey." + category.lower()))
        saved = str(state.settings.value("materials/odyssey/category", "Items"))
        self.tabs.setCurrentIndex(CATEGORIES.index(saved) if saved in CATEGORIES else 0)
        layout.addWidget(self.tabs)
        self.filter = QComboBox(self)
        self.filter.setAccessibleName(tr("materials.filter"))
        for key in FILTERS:
            self.filter.addItem(tr("materials.all" if key == "all" else "odyssey." + key), key)
        saved = str(state.settings.value("materials/odyssey/filter", "all"))
        self.filter.setCurrentIndex(FILTERS.index(saved) if saved in FILTERS else 0)
        summary = QHBoxLayout()
        self.status = QLabel(objectName="muted")
        self.status.setWordWrap(True)
        summary.addWidget(self.status, 1)
        self.commander_label = QLabel(objectName="muted")
        summary.addWidget(self.commander_label)
        self.cleanup_button = QPushButton(tr("odyssey.cleanup.manage"))
        self.cleanup_button.setEnabled(False)
        self.cleanup_button.clicked.connect(self.manage_cleanup)
        summary.addWidget(self.cleanup_button)
        layout.addLayout(summary)
        self.carrier_status = QLabel()
        self.carrier_status.setWordWrap(True)
        carrier_summary = QHBoxLayout()
        self.carrier_help = QToolButton()
        self.carrier_help.setText("!")
        self.carrier_help.setCursor(Qt.PointingHandCursor)
        self.carrier_help.setAccessibleName(tr("odyssey.carrier_setup_title"))
        help_font = self.carrier_help.font()
        help_font.setBold(True)
        self.carrier_help.setFont(help_font)
        self._style_carrier_help(light)
        self.carrier_help.clicked.connect(self.show_carrier_setup)
        carrier_summary.addWidget(self.carrier_help, 0, Qt.AlignTop)
        carrier_summary.addWidget(self.carrier_status, 1)
        layout.addLayout(carrier_summary)
        legend = QHBoxLayout()
        self.cleanup_swatch = QLabel()
        self.cleanup_swatch.setFixedSize(16, 12)
        self.cleanup_legend = QLabel()
        legend.addWidget(self.cleanup_swatch)
        legend.addWidget(self.cleanup_legend)
        self.sort_order = QComboBox()
        for mode in SORT_MODES:
            self.sort_order.addItem(tr("odyssey.sort." + mode), mode)
        saved_sort = str(state.settings.value("materials/odyssey/sort", "alphabetical"))
        self.sort_order.setCurrentIndex(SORT_MODES.index(saved_sort) if saved_sort in SORT_MODES else 1)
        legend.addWidget(self.sort_order)
        legend.addStretch()
        layout.addLayout(legend)
        self._style_cleanup_legend(light)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(len(COLUMNS))
        self.tree.setHeaderLabels([tr("odyssey." + key) + (" ✎" if key == "carrier" else "") for key in COLUMNS])
        for column in range(len(COLUMNS)):
            self.tree.headerItem().setTextAlignment(column, Qt.AlignmentFlag.AlignVCenter |
                (Qt.AlignmentFlag.AlignLeft if column in (0, 5) else Qt.AlignmentFlag.AlignHCenter))
        self.tree.headerItem().setToolTip(3, tr("odyssey.carrier_hint"))
        self.tree.headerItem().setToolTip(4, tr("odyssey.carrier_total"))
        self.tree.setRootIsDecorated(False)
        self.tree.setExpandsOnDoubleClick(False)
        self.tree.setIndentation(16)
        self.tree.setEditTriggers(QTreeWidget.EditTrigger.NoEditTriggers)
        self.tree.itemDoubleClicked.connect(self._edit_carrier)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.tree.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.row_delegate = OdysseyRowDelegate(self.tree, light)
        self.tree.setItemDelegate(self.row_delegate)
        migrate_carrier_columns(state.settings)
        migrate_rank_column(state.settings)
        persist_header_layout(self.tree.header(), state.settings, "materials/odyssey/columns",
                              columns=COLUMNS, default_widths=(340, 105, 105, 110, 95, 220, 65))
        header = self.tree.header()
        # Rank belongs directly before the name, including restored layouts.
        order = [header.logicalIndex(i) for i in range(len(COLUMNS)) if header.logicalIndex(i) != RANK_COLUMN]
        order.insert(order.index(0), RANK_COLUMN)
        for visual, logical in enumerate(order):
            header.moveSection(header.visualIndex(logical), visual)
        layout.addWidget(self.tree, 1)
        self.highlight_timer = QTimer(self)
        self.highlight_timer.setSingleShot(True)
        self.highlight_timer.setInterval(4000)
        self.highlight_timer.timeout.connect(self.clear_highlight)
        self.tabs.currentChanged.connect(self._selection_changed)
        self.filter.currentIndexChanged.connect(self._selection_changed)
        self.sort_order.currentIndexChanged.connect(self._sort_changed)
        self.search.textChanged.connect(self.render)
        from .loading_state import LoadingState
        self.loading_state = LoadingState(self.tree)
        self.controller = controller if controller is not None else OdysseyController(state, self)
        self.controller.loading.connect(self.begin_loading)
        self.controller.ready.connect(self.set_inventory)
        from .odyssey_diagnostics import OdysseyDisplayDiagnostics
        self.display_diagnostics = OdysseyDisplayDiagnostics(self)
        self.begin_loading()

    def _selection_changed(self, *_):
        self.state.settings.setValue("materials/odyssey/category", CATEGORIES[self.tabs.currentIndex()])
        self.state.settings.setValue("materials/odyssey/filter", self.filter.currentData())
        self.state.settings.sync()
        self.render()

    def _sort_changed(self, *_):
        self.state.settings.setValue("materials/odyssey/sort", self.sort_order.currentData())
        self.state.settings.sync()
        self.render()

    def begin_loading(self):
        self.display_diagnostics.invalidate()
        if self._cleanup_dialog is not None:
            self._cleanup_dialog.reject()
        self._cleanup_key = None
        self._cleanup_symbols = frozenset()
        self.cleanup_button.setEnabled(False)
        self.loading_state.begin()
        self.inventory = OdysseyInventory(0, "")
        self.rows = merge_inventory(self.inventory)
        self._baseline, self._last_source, self._last_time = False, None, ""
        self._loading = True
        self.highlight_timer.stop()
        self.highlight = {}
        self.commander_label.clear()
        self.render()

    def set_inventory(self, inventory, name=""):
        identity = (inventory.commander_id, inventory.fid)
        if identity != (self.inventory.commander_id, self.inventory.fid):
            self.begin_loading()
        change = inventory.last_change or {}
        source, timestamp = change.get("source"), change.get("timestamp", "")
        if source != self._last_source or not inventory.known:
            self.highlight_timer.stop()
            self.highlight = {}
            # BackpackChange is O1's authoritative pickup delta. Observational
            # CollectItems/UseConsumable and container transfers cannot flash twice.
            changes = change.get("changes", [])
            if (self._baseline and inventory.known and timestamp >= self._last_time
                    and source != self._last_source and change.get("event") == "BackpackChange"
                    and changes and all(c["delta"] > 0 for c in changes)):
                for c in changes:
                    self.highlight[c["key"]] = self.highlight.get(c["key"], 0) + c["delta"]
                self.highlight_timer.start()
        self._baseline = inventory.known
        self._last_source = source
        self._last_time = max(self._last_time, inventory.reconstructed_at or "", timestamp)
        self.inventory = inventory
        self._cleanup_key = odyssey_cleanup.selection_key(inventory.commander_id, inventory.fid)
        self._cleanup_symbols = odyssey_cleanup.load_selection(self.state.settings, self._cleanup_key)
        self.cleanup_button.setEnabled(self._cleanup_key is not None)
        self.rows = merge_inventory(inventory)
        self._loading = False
        self.commander_label.setText(name or inventory.fid)
        self.commander_label.setToolTip(inventory.fid)
        self.render()
        self.loading_state.finish(inventory.issues[0] if inventory.issues and inventory.reconstructed_at is None else "")

    def clear_highlight(self):
        self.highlight = {}
        self.render()

    def manage_cleanup(self):
        if self._cleanup_key is None:
            return
        if self._cleanup_dialog is not None:
            self._cleanup_dialog.raise_()
            self._cleanup_dialog.activateWindow()
            return
        key = self._cleanup_key
        dialog = odyssey_cleanup.OdysseyCleanupDialog(self._cleanup_symbols, self)
        self._cleanup_dialog = dialog
        try:
            if dialog.exec() != QDialog.DialogCode.Accepted or key != self._cleanup_key:
                return
            selected = dialog.selected_symbols()
            try:
                odyssey_cleanup.save_selection(self.state.settings, key, selected)
            except OSError:
                QMessageBox.warning(self, tr("odyssey.cleanup.manage"), tr("odyssey.cleanup.save_error"))
                return
            self._cleanup_symbols = selected
            self.render()
        finally:
            self._cleanup_dialog = None
            dialog.deleteLater()

    def _mark_cleanup(self, item, row):
        definition = row.definition
        marked = self._is_cleanup(row)
        item.setData(0, CLEANUP_ROLE, marked)
        if marked:
            default = definition.symbol in odyssey_cleanup.DEFAULT_SYMBOLS
            tip = tr("odyssey.cleanup.no_use" if default else "odyssey.cleanup.personal")
            for column in range(self.tree.columnCount()):
                existing = item.toolTip(column)
                item.setToolTip(column, existing + "\n" + tip if existing else tip)

    def _is_cleanup(self, row):
        return (row.definition is not None and row.definition.category == row.key.category
                and row.definition.symbol in self._cleanup_symbols)

    def _style_cleanup_legend(self, light):
        self.cleanup_swatch.setStyleSheet("background-color: " + CLEANUP_COLORS[bool(light)][0] + ";")

    def set_light_mode(self, light):
        self.tabs.light = bool(light)
        self.tabs.update()
        self._style_carrier_help(light)
        self._style_cleanup_legend(light)
        self.row_delegate.light = bool(light)
        self.tree.viewport().update()

    def _style_carrier_help(self, light):
        accent = "#9a620e" if light else "#c57a00"
        hover = "#b87813" if light else "#e0a32e"
        self.carrier_help.setStyleSheet(
            "QToolButton {"
            f"color: {accent}; border: 1px solid {accent};"
            "font-weight: bold; border-radius: 3px; padding: 2px 7px;"
            "background-color: transparent; }"
            "QToolButton:hover {"
            f"border-color: {hover};"
            "background-color: rgba(197, 122, 0, 28); }"
        )

    def show_carrier_setup(self):
        dialog = QMessageBox(self)
        dialog.setWindowTitle(tr("odyssey.carrier_setup_title"))
        dialog.setIcon(QMessageBox.Information)
        dialog.setTextFormat(Qt.PlainText)
        dialog.setText(tr("odyssey.carrier_setup_text"))
        dialog.addButton(tr("common.close"), QMessageBox.AcceptRole)
        dialog.exec()

    def render(self, *_):
        self.cleanup_button.setText(tr("odyssey.cleanup.manage"))
        self.cleanup_legend.setText(tr("odyssey.cleanup.legend"))
        for widget in (self.cleanup_swatch, self.cleanup_legend):
            widget.setToolTip(tr("odyssey.cleanup.legend_tip"))
        self.sort_order.setAccessibleName(tr("odyssey.sort.label"))
        for index, mode in enumerate(SORT_MODES):
            self.sort_order.setItemText(index, tr("odyssey.sort." + mode))
        self.tree.headerItem().setText(RANK_COLUMN, tr("odyssey.rank"))
        self.tree.headerItem().setToolTip(RANK_COLUMN, tr("odyssey.rank.own"))
        self.rows = merge_inventory(self.inventory)
        locker = self.inventory.containers["ShipLocker"]
        for index, tab_category in enumerate(CATEGORIES):
            label = tr("odyssey." + tab_category.lower())
            maximum = capacity("ShipLocker", tab_category)
            if maximum is not None:
                count = (sum(s.count for k, s in locker.stacks.items()
                             if k.category == tab_category)
                         if locker.known and not self.inventory.issues else None)
                label += f" {'—' if count is None else count} / {maximum}"
            self.tabs.setTabText(index, label)
        self._capacity = inventory_carrier_capacity(self.inventory)
        locale = QLocale(get_language())
        amount = locale.toString(self._capacity.known_amount)
        capacity_key = ("unknown" if self.inventory.carrier_id is None else
                        "inconsistent" if self._capacity.inconsistent else
                        "exact" if self._capacity.complete else "partial")
        if capacity_key == "inconsistent" and not self._capacity.complete:
            amount = "≥ " + amount
        self._capacity_text = tr("odyssey.carrier_capacity_" + capacity_key,
                                amount=amount, capacity=locale.toString(self._capacity.limit),
                                unknown=locale.toString(self._capacity.unknown_positions))
        reservation = None
        if self.inventory.fid == getattr(self.state, "commander_fid", None):
            reservation = read_reservation(getattr(self.state, "journal_folder", None), self.inventory.carrier_id)
        usable = usable_with_inventory(reservation, self.inventory)
        stock = "—" if self.inventory.carrier_id is None else amount
        if not self._capacity.complete and not stock.startswith("≥") and stock != "—":
            stock = "≥ " + stock
        occupancy = (locale.toString(reservation.occupancy(self._capacity.known_amount))
                     if usable and self._capacity.complete else "—")
        display = tr("odyssey.market_capacity", amount=stock, occupancy=occupancy,
                     capacity=locale.toString(self._capacity.limit))
        if self._capacity.inconsistent:
            display += " · " + self._capacity_text
        tip = self._capacity_text + "\n" + tr("odyssey.market_capacity_hint")
        if reservation is not None:
            observed = reservation.observed_at.astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
            dated = tr("odyssey.market_reservation", amount=locale.toString(reservation.reserved), time=observed)
            tip += "\n" + dated
            if usable and self._capacity.complete:
                display += " · " + tr("odyssey.market_snapshot", time=observed)
        self.carrier_status.setText(display)
        self.carrier_status.setToolTip(tip + "\n" + tr("odyssey.carrier_hint"))
        font = self.carrier_status.font()
        font.setBold(self._capacity.inconsistent)
        self.carrier_status.setFont(font)
        category = CATEGORIES[self.tabs.currentIndex()]
        query = self.search.text().strip().casefold()
        collator = QCollator(QLocale(get_language()))
        visible = [r for r in self.rows if r.key.category == category
                   and (material_amounts(self.inventory, r.key.category, r.key.name, capacity_state=self._capacity)[3] == 0
                        if self.filter.currentData() == "empty" else r.matches_filter(self.filter.currentData()))
                   and (not query or query in r.name.casefold()
                        or r.definition is not None and query in r.definition.name_en.casefold())]
        cleanup_first = self.sort_order.currentData() == "cleanup"
        rank_sort = self.sort_order.currentData() in ("rank_asc", "rank_desc")
        visible.sort(key=lambda r: (sort_priority(rating(r.key.name, r.key.category).rank,
                                                self.sort_order.currentData() == "rank_desc") if rank_sort
                                    else not self._is_cleanup(r) if cleanup_first else False,
                                    collator.sortKey(r.name), r.key.name, repr(r.key)))
        scroll = self.tree.verticalScrollBar().value()
        selected = next((k for k, item in self.items.items() if item.isSelected()), None)
        old_items, old_summaries = self.items, getattr(self, "summaries", {})
        expanded = {key: item.isExpanded() for key, item in old_summaries.items()}
        # Detach without deleting: both stock stacks and aggregate rows retain
        # their identity across reordering and ordinary inventory updates.
        for summary in old_summaries.values():
            summary.takeChildren()
        while self.tree.topLevelItemCount():
            self.tree.takeTopLevelItem(0)
        self.items = {}
        self.summaries = {}
        groups = {}
        for row in self.rows:
            groups.setdefault((row.key.category, row.key.name), []).append(row)
        for index, row in enumerate(visible):
            stock, definition = row.stock, row.definition
            tags, tips = [], []
            if row.key.mission_id is not None:
                tags.append(tr("odyssey.mission"))
                tips.append(f'{tr("odyssey.mission")} {row.key.mission_id}: '
                            + tr("odyssey.status." + stock.mission_status))
            if row.engineering_relevant:
                tags.append(tr("odyssey.engineering"))
                tips.extend(tr("odyssey.use." + flag) for flag in sorted(definition.engineering_flags))
            if definition is not None and definition.special_group != "standard":
                tags.append(tr("odyssey.group." + definition.special_group))
                if definition.availability_status == "context_dependent":
                    tips.append(tr("odyssey.availability_unknown"))
            if row.key.owner_id is not None:
                tips.append(f'{tr("odyssey.owner")}: {row.key.owner_id}')
            if row.key.stolen:
                tags.append(tr("odyssey.stolen"))
            delta = self.highlight.get(row.key)
            name = f"{row.name} +{delta}" if delta else row.name
            identity = (row.key.category, row.key.name)
            amounts = material_amounts(self.inventory, *identity, capacity_state=self._capacity)
            parent = self.tree
            multiple = len(groups[identity]) > 1
            if multiple:
                if identity not in self.summaries:
                    summary = old_summaries.get(identity)
                    if summary is None:
                        summary = QTreeWidgetItem()
                    self.tree.addTopLevelItem(summary)
                    for column, value in enumerate([tr("odyssey.carrier_summary", name=row.name),
                            *["—" if v is None else str(v) for v in amounts], ""]):
                        summary.setText(column, value)
                        summary.setToolTip(column, "")
                    self._stock_cells(summary, amounts, identity)
                    summary.setData(0, STRIPE_ROLE, index % 5)
                    summary.setExpanded(expanded.get(identity, True))
                    self._mark_cleanup(summary, row)
                    self._rank_cell(summary, row)
                    self.summaries[identity] = summary
                parent = self.summaries[identity]
            values = (stock.locker, stock.backpack, None, None) if multiple else amounts
            numbers = ["—" if value is None else str(value) for value in values]
            item = old_items.get(row.key)
            if item is None:
                item = QTreeWidgetItem()
            if parent is self.tree:
                self.tree.addTopLevelItem(item)
            else:
                parent.addChild(item)
            for column, value in enumerate([name, *numbers, " · ".join(tags)]):
                item.setText(column, value)
                item.setToolTip(column, "")
            item.setTextAlignment(5, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            item.setData(0, STRIPE_ROLE, index % 5)
            item.setData(0, COLLECTED_ROLE, bool(delta))
            item.setSizeHint(0, QSize(0, max(26, self.fontMetrics().height() + 10)))
            self._stock_cells(item, values, identity)
            if multiple:
                item.setToolTip(3, tr("odyssey.carrier_detail"))
                item.setToolTip(4, tr("odyssey.carrier_detail"))
            item.setToolTip(0, "\n".join([row.name, *tips]))
            item.setToolTip(5, "\n".join(tips))
            self._mark_cleanup(item, row)
            self._rank_cell(item, row)
            self.items[row.key] = item
            if row.key == selected:
                item.setSelected(True)
        if self._loading:
            text = tr("odyssey.loading")
        else:
            locker = self.inventory.containers["ShipLocker"]
            count = (sum(s.count for k, s in locker.stacks.items() if k.category == category)
                     if locker.known and not self.inventory.issues else None)
            maximum = capacity("ShipLocker", category)
            text = f'{tr("odyssey.locker")} – {tr("odyssey." + category.lower())}: '
            text += "—" if count is None else str(count)
            if maximum is not None:
                text += f" / {maximum}"
            if not self.inventory.known:
                text += " · " + tr("materials.unknown_stock")
        self.status.setText(text)
        self.status.setToolTip(self.inventory.reconstructed_at or "")
        self.tree.doItemsLayout()
        self.tree.verticalScrollBar().setValue(scroll)
        self.row_delegate.refresh_hover()

    def _rank_cell(self, item, row):
        assessment = rating(row.key.name, row.key.category)
        item.setText(RANK_COLUMN, assessment.rank)
        item.setTextAlignment(RANK_COLUMN, Qt.AlignmentFlag.AlignCenter)
        tips = [tr("odyssey.rank." + assessment.rank), tr("odyssey.rank.own")]
        if assessment.rank != "?":
            tips.append(tr("odyssey.rank.keep" if assessment.rank in "AB" else
                           "odyssey.rank.reduce" if assessment.rank == "C" else "odyssey.rank.sell"))
        # Counts describe source recipe references, not a fabricated scarcity score.
        for flag in sorted({flag for flag, _ in assessment.recipes}):
            tips.append(tr("odyssey.use." + flag) + ": " + str(sum(f == flag for f, _ in assessment.recipes)))
        item.setToolTip(RANK_COLUMN, "\n".join(tips))

    def _stock_cells(self, item, values, identity):
        for column in (0, 5):
            item.setTextAlignment(column, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        for col, value in enumerate(values, 1):
            item.setData(col, POSITIVE_STOCK_ROLE, value is not None and value > 0)
            item.setTextAlignment(col, Qt.AlignmentFlag.AlignCenter)
            if value is None:
                item.setToolTip(col, tr("materials.unknown_stock"))
        category, name = identity
        item.setData(3, CARRIER_KEY_ROLE, identity)
        record = self.inventory.carrier_records.get(f"{category}/{name}")
        item.setToolTip(3, carrier_tooltip(record) if category in CARRIER_CATEGORIES
                        else tr("odyssey.carrier_not_applicable"))
        if category in CARRIER_CATEGORIES and values[3] is not None:
            item.setToolTip(4, tr("odyssey.carrier_total") + "\n" + carrier_tooltip(record))
        if category in CARRIER_CATEGORIES and self._capacity.inconsistent:
            for column in (3, 4):
                item.setToolTip(column, item.toolTip(column) + "\n" + self._capacity_text)

    def _edit_carrier(self, item, column):
        if column != 3:
            return
        key = item.data(3, CARRIER_KEY_ROLE)
        if not key or key[0] not in CARRIER_CATEGORIES:
            return
        category, name = key
        inventory = self.inventory
        identity = (inventory.commander_id, inventory.fid, inventory.carrier_id)
        record = inventory.carrier_records.get(f"{category}/{name}")
        display = next((r.name for r in self.rows if r.key.category == category and r.key.name == name), name)
        editable = inventory.carrier_id is not None and hasattr(self.controller, "confirm_carrier")
        dialog = OdysseyCarrierDialog(display, record, editable, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                self.controller.confirm_carrier(category, name, dialog.amount, identity)
            except (ValueError, OSError):
                QMessageBox.warning(self, tr("odyssey.carrier_edit"), tr("odyssey.carrier_unavailable"))
