"""Compact Engineering inventory page; all counts come from Phases 1 and 2."""
from PySide6.QtCore import QCollator, QLocale, QTimer, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTabBar, QTreeWidget, QTreeWidgetItem, QProgressBar,
)

from cmdrhelper.i18n import tr, get_language
from cmdrhelper.material_catalog import merge_inventory, localized_name
from cmdrhelper.material_controller import MaterialController
from cmdrhelper.material_inventory import MaterialInventory
from cmdrhelper.ui.table_widths import persist_header_layout
from cmdrhelper.ui.material_row_style import MaterialRowDelegate, STRIPE_ROLE, COLLECTED_ROLE


class _MaterialItem(QTreeWidgetItem):
    sort_key = 0

    def __lt__(self, other):
        return self.sort_key < other.sort_key


class MaterialCategoryTabs(QTabBar):
    """Paint an inset active border without changing native tab metrics or input."""
    def __init__(self, light=False):
        super().__init__()
        self.light = light

    @property
    def active_border_color(self):
        return QColor("#9a620e" if self.light else "#c57a00")

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.currentIndex() < 0:
            return
        painter = QPainter(self)
        painter.setPen(QPen(self.active_border_color, 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self.tabRect(self.currentIndex()).adjusted(1, 1, -2, -2), 2, 2)
        painter.end()


class MaterialView(QWidget):
    routeRequested = Signal(str)
    CATEGORIES = ("Raw", "Manufactured", "Encoded", "Odyssey", "Mining")
    FILTERS = ("all", "empty", "low", "near_full", "full")

    def __init__(self, state, parent=None, *, controller=None, odyssey_controller=None, trader_service=None):
        super().__init__(parent)
        self.state = state
        self.odyssey = None
        self.mining = None
        self._odyssey_controller = odyssey_controller
        self.inventory = MaterialInventory(0, "")
        self.rows = ()
        self.items = {}
        self._row_items = {}
        self._groups = {}
        self._bars = {}
        self._row_signatures = {}
        self._render_signature = None
        self.highlight = {}
        self._baseline = False
        self._last_source = None
        self._last_time = ""
        self._light = str(state.settings.value("ui_theme", "dark")) == "light"
        self.highlight_timer = QTimer(self)
        self.highlight_timer.setSingleShot(True)
        self.highlight_timer.setInterval(4000)
        self.highlight_timer.timeout.connect(self.clear_highlight)
        layout = QVBoxLayout(self)
        self._page_layout = layout
        title = QHBoxLayout()
        title.addWidget(QLabel(tr("materials.title"), objectName="commanderTitle"))
        title.addStretch()
        from cmdrhelper.ui.material_trader_panel import MaterialTraderPanel
        self.trader_panel = MaterialTraderPanel(state, self, service=trader_service)
        self.trader_panel.routeRequested.connect(self.routeRequested)
        title.addWidget(self.trader_panel.search_button)
        self.commander_label = QLabel(objectName="muted")
        title.addWidget(self.commander_label)
        layout.addLayout(title)
        self.tabs = MaterialCategoryTabs(self._light)
        self.tabs.setExpanding(True)
        self.tabs.setUsesScrollButtons(True)
        for key in ("raw", "manufactured", "encoded"):
            self.tabs.addTab(tr("materials." + key))
        self.tabs.addTab(tr("odyssey.title"))
        self.tabs.addTab(tr("mining.title"))
        saved_tab = str(state.settings.value("materials/category", "Raw"))
        self.tabs.setCurrentIndex(self.CATEGORIES.index(saved_tab) if saved_tab in self.CATEGORIES else 0)
        layout.addWidget(self.tabs)
        controls = QHBoxLayout()
        self._controls = controls
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("materials.search"))
        self.search.setAccessibleName(tr("materials.search"))
        self.search.setClearButtonEnabled(True)
        controls.addWidget(self.search, 1)
        self.filter = QComboBox()
        self.filter.setAccessibleName(tr("materials.filter"))
        for key in self.FILTERS:
            self.filter.addItem(tr("materials." + key), key)
        saved_filter = str(state.settings.value("materials/filter", "all"))
        self.filter.setCurrentIndex(self.FILTERS.index(saved_filter) if saved_filter in self.FILTERS else 0)
        controls.addWidget(self.filter)
        layout.addLayout(controls)
        self.status = QLabel(tr("materials.loading"), objectName="muted")
        self.status.setWordWrap(True)
        layout.addWidget(self.trader_panel)
        layout.addWidget(self.status)
        self.tree = QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels([tr("materials.name"), tr("materials.grade"),
                                   tr("materials.stock"), tr("materials.fill")])
        self.tree.setRootIsDecorated(False)
        self.tree.setIndentation(0)
        self.tree.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        self.tree.setSelectionBehavior(QTreeWidget.SelectionBehavior.SelectRows)
        self.row_delegate = MaterialRowDelegate(self.tree, self._light)
        self.tree.setItemDelegate(self.row_delegate)
        self.tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        persist_header_layout(
            self.tree.header(), state.settings, "materials/columns",
            columns=("name", "grade", "stock", "fill"),
            default_widths=(320, 80, 160, 160),
        )
        layout.addWidget(self.tree, 1)
        self.tabs.currentChanged.connect(self._selection_changed)
        self.filter.currentIndexChanged.connect(self._selection_changed)
        self.search.textChanged.connect(self.render)
        from .loading_state import LoadingState
        self.loading_state = LoadingState(self.tree)
        self.controller = controller if controller is not None else MaterialController(state, self)
        self.controller.loading.connect(self.begin_loading)
        self.controller.ready.connect(self.set_inventory)
        self.begin_loading()

    def _selection_changed(self, *_):
        self.state.settings.setValue("materials/category", self.CATEGORIES[self.tabs.currentIndex()])
        self.state.settings.setValue("materials/filter", self.filter.currentData())
        self.state.settings.sync()
        self.render()

    def begin_loading(self):
        self.loading_state.begin()
        self.inventory = MaterialInventory(0, "")
        self.rows = merge_inventory(self.inventory)
        self._baseline = False
        self._last_source = None
        self._last_time = ""
        self.highlight_timer.stop()
        self.highlight = {}
        self.commander_label.clear()
        self.status.setText(tr("materials.loading"))
        self.status.show()
        self.render()

    def set_inventory(self, inventory, name=""):
        if not inventory.known or (inventory.commander_id, inventory.fid) != (self.inventory.commander_id, self.inventory.fid):
            self._baseline = False
            self._last_source, self._last_time = None, ""
            self.highlight_timer.stop()
            self.highlight = {}
        change = inventory.last_change
        source = change.get("source") if change else None
        timestamp = change.get("timestamp", "") if change else (inventory.snapshot_timestamp or "")
        if self._baseline and source != self._last_source:
            self.highlight = {}
            self.highlight_timer.stop()
            if (inventory.known and change and change.get("event") == "MaterialCollected"
                    and timestamp >= self._last_time):
                self.highlight = {c["name"]: c["delta"] for c in change.get("changes", []) if c["delta"] > 0}
                if self.highlight:
                    self.highlight_timer.start()
        self._baseline = inventory.known
        self._last_source, self._last_time = source, max(timestamp, self._last_time)
        self.inventory = inventory
        self.rows = merge_inventory(inventory)
        self.commander_label.setText(name or inventory.fid)
        self.commander_label.setToolTip(inventory.fid)
        self.status.setText("" if inventory.known else tr("materials.unknown_stock"))
        self.status.setVisible(not inventory.known)
        self.render()
        self.loading_state.finish(inventory.issues[0] if inventory.issues and inventory.snapshot_timestamp is None else "")

    def clear_highlight(self):
        self.highlight = {}
        self.render()

    def set_light_mode(self, light):
        self._light = bool(light)
        self.tabs.light = self._light
        self.tabs.update()
        self.row_delegate.light = self._light
        if self.odyssey is not None:
            self.odyssey.set_light_mode(self._light)
        if self.mining is not None:
            self.mining.set_light_mode(self._light)
        self.render()

    def render(self, *_):
        self.trader_panel.set_category(self.CATEGORIES[self.tabs.currentIndex()])
        is_odyssey = self.CATEGORIES[self.tabs.currentIndex()] == "Odyssey"
        if is_odyssey and self.odyssey is None:
            from cmdrhelper.ui.odyssey_view import OdysseyView
            self.odyssey = OdysseyView(self.state, self.search, self,
                                       controller=self._odyssey_controller)
            self.odyssey.set_light_mode(self._light)
            self._controls.addWidget(self.odyssey.filter)
            self._page_layout.addWidget(self.odyssey, 1)
        is_mining = self.CATEGORIES[self.tabs.currentIndex()] == "Mining"
        if is_mining and self.mining is None:
            from cmdrhelper.ui.mining_view import MiningView
            self.mining = MiningView(self.state.settings, self, state=self.state)
            self.mining.set_light_mode(self._light)
            self._page_layout.addWidget(self.mining, 1)
        if self.mining is not None:
            self.mining.setVisible(is_mining)
        self.search.setVisible(not is_mining)
        self.tree.setVisible(not is_odyssey and not is_mining)
        self.commander_label.setVisible(not is_odyssey and not is_mining)
        self.filter.setVisible(not is_odyssey and not is_mining)
        self.status.setVisible(not is_odyssey and not is_mining and bool(self.status.text()))
        if self.odyssey is not None:
            self.odyssey.setVisible(is_odyssey)
            self.odyssey.filter.setVisible(is_odyssey)
        if is_odyssey:
            self.odyssey.render()
            return
        if is_mining:
            return
        scroll = self.tree.verticalScrollBar().value()
        selected_items = self.tree.selectedItems()
        selected_symbol = selected_items[0].data(0, Qt.ItemDataRole.UserRole) if selected_items else None
        signature = (self.CATEGORIES[self.tabs.currentIndex()], self.search.text(),
                     self.filter.currentData(), get_language(), self._light, self.font().toString(),
                     tuple(repr(row) for row in self.rows), tuple(sorted(self.highlight.items())))
        if signature == self._render_signature:
            return
        self._render_signature = signature
        self.tree.setUpdatesEnabled(False)
        for item in self._row_items.values():
            item.setHidden(True)
        for group in self._groups.values():
            group.setHidden(True)
        self.items = {}
        category = self.CATEGORIES[self.tabs.currentIndex()]
        query = self.search.text().strip().casefold()
        selected = self.filter.currentData()
        collator = QCollator(QLocale(get_language()))
        named = []
        for row in self.rows:
            m = row.material
            name = localized_name(m.symbol)
            if m.category != category or (selected != "all" and row.fill_state != selected):
                continue
            if query and query not in name.casefold() and query not in m.english_name.casefold():
                continue
            named.append((row, name))
        named.sort(key=lambda pair: (pair[0].material.grade or 6, collator.sortKey(pair[1])))
        groups = {}
        stripes = {}
        colors = ({"empty": "#d89991", "low": "#e3b963", "near_full": "#a1cca9", "full": "#82bd94"}
                  if self._light else {"empty": "#934e47", "low": "#936516", "near_full": "#326845", "full": "#28643e"})
        for row, name in named:
            m = row.material
            grade = tr("materials.grade_number", grade=m.grade) if m.grade else tr("materials.unknown_grade")
            if m.grade not in groups:
                group_key = (category, m.grade)
                group = self._groups.get(group_key)
                if group is None:
                    group = _MaterialItem(self.tree, [grade])
                    group.sort_key = m.grade or 6
                    self._groups[group_key] = group
                group.setText(0, grade)
                group.setHidden(False)
                group.setFlags(group.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                group.setFirstColumnSpanned(True)
                group.setExpanded(True)
                font = group.font(0)
                font.setBold(True)
                group.setFont(0, font)
                groups[m.grade] = group
            delta = self.highlight.get(m.symbol)
            label = f"{name} +{delta}" if delta else name
            count = str(row.count) if row.known else "?"
            maximum = str(m.maximum) if m.maximum is not None else "?"
            stripe = stripes.get(m.grade, 0)
            stripes[m.grade] = stripe + 1
            item = self._row_items.get(m.symbol)
            texts = [label, str(m.grade) if m.grade else "?", f"{count} / {maximum}", ""]
            row_signature = (repr(row), label, stripe, self._light, get_language(), self.font().toString())
            if item is None:
                item = _MaterialItem(groups[m.grade], texts)
                self._row_items[m.symbol] = item
            item.sort_key = collator.sortKey(name)
            item.setHidden(False)
            self.items[m.symbol] = item
            if self._row_signatures.get(m.symbol) == row_signature:
                continue
            self._row_signatures[m.symbol] = row_signature
            for column, text in enumerate(texts):
                if item.text(column) != text:
                    item.setText(column, text)
            item.setSizeHint(0, QSize(0, max(26, self.fontMetrics().height() + 10)))
            item.setData(0, Qt.ItemDataRole.UserRole, m.symbol)
            # Start at A in each visible grade block; headings consume no color.
            item.setData(0, STRIPE_ROLE, stripe % 5)
            item.setData(0, COLLECTED_ROLE, bool(delta))
            item.setToolTip(0, name)
            item.setToolTip(2, "")
            item.setTextAlignment(2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.items[m.symbol] = item
            if m.symbol == selected_symbol:
                item.setSelected(True)
            if row.percent is not None:
                bar = self._bars.get(m.symbol)
                if bar is None:
                    bar = QProgressBar()
                    self._bars[m.symbol] = bar
                    self.tree.setItemWidget(item, 3, bar)
                bar.show()
                bar.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                bar.setRange(0, 1000)
                bar.setValue(min(1000, round(row.percent * 10)))
                percent = QLocale(get_language()).toString(row.percent, 'f', 1) + " %"
                bar.setFormat(percent)
                bar.setAccessibleName(f"{name}: {count} / {maximum}, {percent}")
                bar.setFixedHeight(max(20, bar.fontMetrics().height() + 4))
                color = colors.get(row.fill_state, "#d7b783" if self._light else "#765829")
                background = "#edf0f2" if self._light else "#19232c"
                foreground = "#17212a" if self._light else "#f2f4f5"
                bar.setStyleSheet(f"QProgressBar {{background:{background}; color:{foreground}; border:1px solid {color}; border-radius:3px; text-align:center;}} QProgressBar::chunk {{background:{color};}}")
            else:
                if m.symbol in self._bars:
                    self.tree.removeItemWidget(item, 3)
                    self._bars.pop(m.symbol)
                item.setToolTip(2, tr("materials.unknown_stock") if not row.known else tr("materials.unknown_maximum"))
        self.tree.sortItems(0, Qt.AscendingOrder)
        self.tree.setUpdatesEnabled(True)
        self.tree.doItemsLayout()
        self.tree.verticalScrollBar().setValue(scroll)
        self.row_delegate.refresh_hover()
