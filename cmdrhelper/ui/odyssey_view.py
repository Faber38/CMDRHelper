"""Odyssey stacks with a separate, manually confirmed private carrier inventory."""
from PySide6.QtCore import QCollator, QLocale, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTreeWidget, QTreeWidgetItem, QStyle, QDialog, QMessageBox, QToolButton

from cmdrhelper.i18n import tr, get_language
from cmdrhelper.odyssey_inventory import CATEGORIES, OdysseyInventory
from cmdrhelper.odyssey_catalog import FILTERS, capacity, merge_inventory
from cmdrhelper.odyssey_controller import OdysseyController
from cmdrhelper.odyssey_carrier import CARRIER_CATEGORIES, material_amounts, inventory_carrier_capacity
from cmdrhelper.odyssey_market_capacity import read_reservation, usable_with_inventory
from cmdrhelper.ui.odyssey_carrier_dialog import OdysseyCarrierDialog, carrier_tooltip
from cmdrhelper.ui.material_view import MaterialCategoryTabs
from cmdrhelper.ui.material_row_style import MaterialRowDelegate, STRIPE_ROLE, COLLECTED_ROLE
from cmdrhelper.ui.table_widths import persist_header_layout


POSITIVE_STOCK_ROLE = Qt.ItemDataRole.UserRole + 3
STOCK_TEXT_COLORS = {False: "#c2a45e", True: "#806015"}
CARRIER_KEY_ROLE = Qt.ItemDataRole.UserRole + 4
COLUMNS = ("name", "locker", "backpack", "carrier", "total", "usage")


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
    settings.setValue(key, dict(version=1, columns=list(COLUMNS),
        widths=[sizes[c] for c in COLUMNS], order=[COLUMNS.index(c) for c in names]))


class OdysseyRowDelegate(MaterialRowDelegate):
    def initStyleOption(self, option, index):
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        super().initStyleOption(option, index)
        # Preserve the existing selection contrast and all row backgrounds.
        if not selected and index.data(POSITIVE_STOCK_ROLE):
            option.palette.setColor(QPalette.ColorRole.Text, QColor(STOCK_TEXT_COLORS[self.light]))


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
        self.tree = QTreeWidget()
        self.tree.setColumnCount(6)
        self.tree.setHeaderLabels([tr("odyssey." + key) + (" ✎" if key == "carrier" else "") for key in COLUMNS])
        for column in range(6):
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
        persist_header_layout(self.tree.header(), state.settings, "materials/odyssey/columns",
                              columns=COLUMNS, default_widths=(340, 105, 105, 110, 95, 220))
        layout.addWidget(self.tree, 1)
        self.highlight_timer = QTimer(self)
        self.highlight_timer.setSingleShot(True)
        self.highlight_timer.setInterval(4000)
        self.highlight_timer.timeout.connect(self.clear_highlight)
        self.tabs.currentChanged.connect(self._selection_changed)
        self.filter.currentIndexChanged.connect(self._selection_changed)
        self.search.textChanged.connect(self.render)
        self.controller = controller if controller is not None else OdysseyController(state, self)
        self.controller.loading.connect(self.begin_loading)
        self.controller.ready.connect(self.set_inventory)
        self.begin_loading()

    def _selection_changed(self, *_):
        self.state.settings.setValue("materials/odyssey/category", CATEGORIES[self.tabs.currentIndex()])
        self.state.settings.setValue("materials/odyssey/filter", self.filter.currentData())
        self.state.settings.sync()
        self.render()

    def begin_loading(self):
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
        self.rows = merge_inventory(inventory)
        self._loading = False
        self.commander_label.setText(name or inventory.fid)
        self.commander_label.setToolTip(inventory.fid)
        self.render()

    def clear_highlight(self):
        self.highlight = {}
        self.render()

    def set_light_mode(self, light):
        self.tabs.light = bool(light)
        self.tabs.update()
        self._style_carrier_help(light)
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
        visible.sort(key=lambda r: (collator.sortKey(r.name), repr(r.key)))
        scroll = self.tree.verticalScrollBar().value()
        selected = next((k for k, item in self.items.items() if item.isSelected()), None)
        self.tree.clear()
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
                    summary = QTreeWidgetItem(self.tree, [tr("odyssey.carrier_summary", name=row.name),
                        *["—" if v is None else str(v) for v in amounts], ""])
                    self._stock_cells(summary, amounts, identity)
                    summary.setData(0, STRIPE_ROLE, index % 5)
                    summary.setExpanded(True)
                    self.summaries[identity] = summary
                parent = self.summaries[identity]
            values = (stock.locker, stock.backpack, None, None) if multiple else amounts
            numbers = ["—" if value is None else str(value) for value in values]
            item = QTreeWidgetItem(parent, [name, *numbers, " · ".join(tags)])
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
