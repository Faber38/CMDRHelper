"""Flat Odyssey inventory presentation. Identity and all quantities belong to O1/O2."""
from PySide6.QtCore import QCollator, QLocale, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTreeWidget, QTreeWidgetItem, QStyle

from cmdrhelper.i18n import tr, get_language
from cmdrhelper.odyssey_inventory import CATEGORIES, OdysseyInventory
from cmdrhelper.odyssey_catalog import FILTERS, capacity, merge_inventory
from cmdrhelper.odyssey_controller import OdysseyController
from cmdrhelper.ui.material_view import MaterialCategoryTabs
from cmdrhelper.ui.material_row_style import MaterialRowDelegate, STRIPE_ROLE, COLLECTED_ROLE
from cmdrhelper.ui.table_widths import persist_header_layout


POSITIVE_STOCK_ROLE = Qt.ItemDataRole.UserRole + 3
STOCK_TEXT_COLORS = {False: "#c2a45e", True: "#806015"}


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
        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels([tr("odyssey." + key) for key in ("name", "locker", "backpack", "total", "usage")])
        self.tree.headerItem().setTextAlignment(4, Qt.AlignmentFlag.AlignCenter)
        self.tree.setRootIsDecorated(False)
        self.tree.setIndentation(0)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.tree.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.row_delegate = OdysseyRowDelegate(self.tree, light)
        self.tree.setItemDelegate(self.row_delegate)
        persist_header_layout(self.tree.header(), state.settings, "materials/odyssey/columns",
                              columns=("name", "locker", "backpack", "total", "usage"),
                              default_widths=(340, 105, 105, 95, 220))
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
        self.row_delegate.light = bool(light)
        self.tree.viewport().update()

    def render(self, *_):
        self.rows = merge_inventory(self.inventory)
        category = CATEGORIES[self.tabs.currentIndex()]
        query = self.search.text().strip().casefold()
        collator = QCollator(QLocale(get_language()))
        visible = [r for r in self.rows if r.key.category == category
                   and r.matches_filter(self.filter.currentData())
                   and (not query or query in r.name.casefold()
                        or r.definition is not None and query in r.definition.name_en.casefold())]
        visible.sort(key=lambda r: (collator.sortKey(r.name), repr(r.key)))
        scroll = self.tree.verticalScrollBar().value()
        selected = next((k for k, item in self.items.items() if item.isSelected()), None)
        self.tree.clear()
        self.items = {}
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
            numbers = ["?" if value is None else str(value) for value in (stock.locker, stock.backpack, stock.total)]
            item = QTreeWidgetItem(self.tree, [name, *numbers, " · ".join(tags)])
            item.setTextAlignment(4, Qt.AlignmentFlag.AlignCenter)
            item.setData(0, STRIPE_ROLE, index % 5)
            item.setData(0, COLLECTED_ROLE, bool(delta))
            item.setSizeHint(0, QSize(0, max(26, self.fontMetrics().height() + 10)))
            for col, value in enumerate((stock.locker, stock.backpack, stock.total), start=1):
                item.setData(col, POSITIVE_STOCK_ROLE, value is not None and value > 0)
                item.setTextAlignment(col, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                if item.text(col) == "?":
                    item.setToolTip(col, tr("materials.unknown_stock"))
            item.setToolTip(0, "\n".join([row.name, *tips]))
            item.setToolTip(4, "\n".join(tips))
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
            text += "?" if count is None else str(count)
            if maximum is not None:
                text += f" / {maximum}"
            if not self.inventory.known:
                text += " · " + tr("materials.unknown_stock")
        self.status.setText(text)
        self.status.setToolTip(self.inventory.reconstructed_at or "")
        self.tree.doItemsLayout()
        self.tree.verticalScrollBar().setValue(scroll)
        self.row_delegate.refresh_hover()
