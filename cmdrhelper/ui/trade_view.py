"""Manual, transient trade UI. Identity and network semantics belong to providers."""
from datetime import datetime, timezone
from threading import Event

from PySide6.QtCore import QObject, QLocale, QRunnable, QThreadPool, Qt, Signal, Slot, QSignalBlocker
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QPushButton, QScrollArea, QSpinBox, QTableWidget,
    QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from cmdrhelper.commodity_master import lookup_by_id
from cmdrhelper.i18n import get_language, tr
from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus, PadSize, TradeSide
from cmdrhelper.observed_market_cache import timestamp
from cmdrhelper.spansh_market import SpanshMarketProvider
from cmdrhelper.trade_search import search_trade
from cmdrhelper.trade_result_text import community_failure_text, market_notice_text
from cmdrhelper.ui.commodity_picker import CommodityField
from cmdrhelper.ui.recent_system_copy import RecentSystemCopyDelegate
from cmdrhelper.ui.remembered_targets import RememberedTargets, RememberedTargetDelegate
from cmdrhelper.ui.system_clipboard import copy_system_name

from .market_age import MarketAgeCombo


def format_age(stamp, now=None):
    seconds = max(0, int(((now or datetime.now(timezone.utc)) - stamp).total_seconds()))
    if seconds < 3600:
        return tr('trade.age_minutes', count=seconds // 60)
    if seconds < 86400:
        return tr('trade.age_hours', count=seconds // 3600)
    return tr('trade.age_days', count=seconds // 86400)


class MarketSignals(QObject):
    finished = Signal(object)


class MarketWorker(QRunnable):
    def __init__(self, provider, query, side=TradeSide.SELL, generation=0, *, local_markets=(),
                 distances=None, fid='', clock=None):
        super().__init__()
        self.provider, self.query = provider, query
        self.side, self.generation = side, generation
        self.local_markets, self.distances, self.fid = local_markets, distances, fid
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.cancel = Event()
        self.signals = MarketSignals()

    @Slot()
    def run(self):
        try:
            result = search_trade(self.provider, self.query, self.side, self.local_markets,
                                  self.distances, self.fid, cancel=self.cancel, clock=self.clock)
        except Exception:
            # No raw exception or HTTP response is exposed to the user.
            result = MarketSearchResult(MarketStatus.INVALID_RESPONSE, query=self.query)
        if self.cancel.is_set():
            result = MarketSearchResult(MarketStatus.CANCELLED, query=self.query)
        self.signals.finished.emit(result)


class NumericItem(QTableWidgetItem):
    def __init__(self, text, value):
        super().__init__(text)
        self.value = value
        self.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def __lt__(self, other):
        if isinstance(other, NumericItem):
            return (self.value is not None, self.value or 0) < (other.value is not None, other.value or 0)
        return super().__lt__(other)


class TextItem(QTableWidgetItem):
    def __lt__(self, other):
        # Equal casefolded names retain their row order in Qt's stable sort.
        return self.text().casefold() < other.text().casefold()


class PadItem(QTableWidgetItem):
    def __init__(self, text, pad):
        super().__init__(text)
        self.rank = {PadSize.SMALL: 1, PadSize.MEDIUM: 2, PadSize.LARGE: 3}.get(pad)

    def __lt__(self, other):
        if not isinstance(other, PadItem):
            return super().__lt__(other)
        if self.rank is None or other.rank is None:
            if self.rank is other.rank:
                return False
            # Qt reverses the comparison for descending order. Keep unknown
            # pads at the end in either direction, independently of UI language.
            table = self.tableWidget()
            descending = (table is not None and table.horizontalHeader().sortIndicatorOrder()
                          == Qt.SortOrder.DescendingOrder)
            return (self.rank is None) if descending else (self.rank is not None)
        return self.rank < other.rank


_STATUS_KEYS = {
    MarketStatus.OK: 'trade.sell_success', MarketStatus.NO_RESULTS: 'trade.sell_no_results',
    MarketStatus.UNKNOWN_COMMODITY: 'trade.unknown_commodity',
    MarketStatus.UNKNOWN_SYSTEM: 'trade.unknown_system',
    MarketStatus.INVALID_QUERY: 'trade.invalid_query',
    MarketStatus.NETWORK_ERROR: 'trade.network_error',
    MarketStatus.TIMEOUT: 'trade.timeout', MarketStatus.HTTP_ERROR: 'trade.network_error',
    MarketStatus.RATE_LIMIT: 'trade.rate_limit', MarketStatus.INVALID_JSON: 'trade.invalid_response',
    MarketStatus.INVALID_RESPONSE: 'trade.invalid_response', MarketStatus.CANCELLED: 'trade.cancelled',
}


class TradeView(QWidget):
    """Two trade directions share one transient form, table, provider and worker."""

    def __init__(self, state, parent=None, *, provider=None, pool=None):
        super().__init__(parent)
        self.state = state
        self.provider = provider if provider is not None else SpanshMarketProvider()
        self.pool = pool if pool is not None else QThreadPool.globalInstance()
        self.worker = None
        self._query = None
        self.offers = ()
        self._reference = None
        self.side = TradeSide.SELL
        self._generation = 0
        self._fid = getattr(state, 'commander_fid', '')
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(tr('nav.trade'), objectName='sectionTitle'))
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll.setWidget(content)
        self._scroll = scroll
        for key in ('trade.sell', 'trade.buy'):
            page = QWidget()
            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(0, 0, 0, 0)
            self.tabs.addTab(page, tr(key))
        self.tabs.widget(0).layout().addWidget(scroll)
        body = QVBoxLayout(content)
        self.reference = QLabel()
        self.reference.setTextFormat(Qt.TextFormat.PlainText)
        self.reference.setWordWrap(True)
        body.addWidget(self.reference)
        self.observed_status = QLabel(objectName='muted')
        self.observed_status.setTextFormat(Qt.TextFormat.PlainText)
        self.observed_status.setWordWrap(True)
        self._refreshing_observed = False
        body.addWidget(self.observed_status)
        self.filters = QWidget()
        form = QFormLayout(self.filters)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.commodity = CommodityField()
        form.addRow(tr('trade.commodity'), self.commodity)
        self.quantity = QSpinBox()
        self.quantity.setRange(1, 2147483647)
        self.quantity.setValue(1)
        form.addRow(tr('trade.quantity'), self.quantity)
        self.radius = QComboBox()
        for value in (25, 50, 100, 250, 500):
            self.radius.addItem(str(value), value)
        self.radius.setCurrentIndex(2)
        form.addRow(tr('trade.radius'), self.radius)
        self.max_age = MarketAgeCombo(state)
        form.addRow(tr('trade.max_age'), self.max_age)
        self.pad = QComboBox()
        for pad in PadSize:
            self.pad.addItem(tr('trade.pad_' + pad.value), pad)
        form.addRow(tr('trade.pad'), self.pad)
        self.carriers = QCheckBox(tr('trade.carriers'))
        form.addRow(self.carriers)
        self.arrival = QLineEdit()
        self.arrival.setPlaceholderText(tr('trade.unlimited'))
        form.addRow(tr('trade.arrival'), self.arrival)
        body.addWidget(self.filters)
        buttons = QHBoxLayout()
        self.search_button = QPushButton(tr('trade.search'))
        self.search_button.setToolTip(tr('trade.help'))
        self.cancel_button = QPushButton(tr('trade.cancel'))
        self.cancel_button.setEnabled(False)
        self.cancel_button.hide()
        buttons.addWidget(self.search_button)
        buttons.addWidget(self.cancel_button)
        buttons.addStretch()
        body.addLayout(buttons)
        self.status = QLabel(tr('trade.ready'))
        self.status.setWordWrap(True)
        body.addWidget(self.status)
        self.market_notice = QLabel(tr('trade.market_notice'), objectName='marketDataNotice')
        self.market_notice.setTextFormat(Qt.TextFormat.PlainText)
        self.market_notice.setWordWrap(True)
        self.market_notice.setMargin(8)
        self.market_notice.setStyleSheet('QLabel#marketDataNotice { border-left: 2px solid #ad7927; }')
        body.addWidget(self.market_notice)
        self.remembered_lists = {side: RememberedTargets(state=state) for side in TradeSide}
        for panel in self.remembered_lists.values():
            body.addWidget(panel)
        self.table = QTableWidget(0, 11)
        for side, panel in self.remembered_lists.items():
            panel.bind_table(self.table, 10, lambda side=side: self.side == side)
        self.table.setHorizontalHeaderLabels([tr('trade.' + key) for key in (
            'system', 'station', 'distance', 'price', 'demand', 'revenue', 'arrival_column', 'pad', 'age', 'type')] + [''])
        for column in range(self.table.columnCount()):
            self.table.horizontalHeaderItem(column).setData(
                Qt.ItemDataRole.InitialSortOrderRole,
                Qt.SortOrder.DescendingOrder if column == 3 else Qt.SortOrder.AscendingOrder)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().moveSection(10, 0)
        self.table.horizontalHeaderItem(10).setToolTip(tr('trade.remembered_targets'))
        self.table.setItemDelegate(RememberedTargetDelegate(self.table, column=10))
        self.table.itemChanged.connect(self.remember_changed)
        self.system_copy_delegate = RecentSystemCopyDelegate(
            self.table, column=0, name_role=Qt.DisplayRole, style_delegate=self.table.itemDelegate())
        self.table.setItemDelegateForColumn(0, self.system_copy_delegate)
        self.system_copy_delegate.copyRequested.connect(
            lambda row, _column: copy_system_name(
                self.table.item(row, 0).data(Qt.UserRole).system_name))
        self.table.setMinimumHeight(240)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()
        body.addWidget(self.table, 1)
        self.commodity.commodityChanged.connect(self._invalidate_results)
        for field in (self.radius, self.max_age, self.pad):
            field.currentIndexChanged.connect(self._invalidate_results)
        self.max_age.currentIndexChanged.connect(self.refresh_observed_markets)
        self.quantity.valueChanged.connect(self._invalidate_results)
        self.carriers.toggled.connect(self._invalidate_results)
        self.arrival.textChanged.connect(self._invalidate_results)
        self.search_button.clicked.connect(self.start_search)
        self.cancel_button.clicked.connect(self.cancel_search)
        changed = getattr(state, 'changed', None)
        if changed is not None:
            changed.connect(self.refresh_reference)
        for name in ('observedMarketsChanged', 'commanderIdentityChanged'):
            signal = getattr(state, name, None)
            if signal is not None:
                signal.connect(self.refresh_observed_markets)
        QApplication.instance().aboutToQuit.connect(self.cancel_search)
        # A removed page must also stop background work without waiting on the GUI thread.
        self._cancel_event = None
        self.refresh_reference()
        from .recommendations_view import RecommendationsView
        self.recommendations = RecommendationsView(state, self.provider, self.pool)
        self.tabs.addTab(self.recommendations, tr('recommend.title'))
        self.max_age.currentIndexChanged.connect(self.recommendations.max_age.setCurrentIndex)
        self.recommendations.max_age.currentIndexChanged.connect(self.max_age.setCurrentIndex)
        self.tabs.currentChanged.connect(self._change_side)

    @Slot(int)
    def _change_side(self, index):
        self._generation += 1
        self.cancel_search()
        self.recommendations.cancel_for_context()
        if index == 2:
            self.recommendations.refresh()
            return
        self.side = TradeSide.BUY if index == 1 else TradeSide.SELL
        self.update_remembered()
        # Move the same form instead of copying filter state or widget trees.
        self.tabs.widget(index).layout().addWidget(self._scroll)
        self._scroll.show()
        self.offers = ()
        self.table.setRowCount(0)
        self.search_button.setText(tr('trade.buy_search' if self.side == TradeSide.BUY else 'trade.search'))
        self.search_button.setToolTip(tr('trade.buy_help' if self.side == TradeSide.BUY else 'trade.help'))
        for column, key in ((4, 'trade.buy_supply' if self.side == TradeSide.BUY else 'trade.demand'),
                            (5, 'trade.buy_cost' if self.side == TradeSide.BUY else 'trade.revenue')):
            self.table.horizontalHeaderItem(column).setText(tr(key))
        self.table.horizontalHeaderItem(3).setData(Qt.ItemDataRole.InitialSortOrderRole, self._price_order())
        self.table.sortItems(3, self._price_order())
        self.table.resizeColumnsToContents()
        self.status.setText(tr('trade.cancelling') if self.worker is not None else
                            tr('trade.ready') if self._reference else tr('trade.no_system'))

    def _price_order(self):
        return Qt.SortOrder.AscendingOrder if self.side == TradeSide.BUY else Qt.SortOrder.DescendingOrder

    @Slot()
    def _invalidate_results(self):
        if self.worker is None:
            self.offers = ()
            self.table.setRowCount(0)
            self.status.setText(tr('trade.ready') if self._reference else tr('trade.no_system'))

    @Slot()
    def refresh_reference(self):
        reference = str(getattr(self.state, 'system', '') or '').strip()
        if reference in ('–', '-'):
            reference = ''
        if reference != self._reference:
            self._reference = reference
            self.cancel_search()
            self.table.setRowCount(0)
            self.offers = ()
            if self.worker is None:
                self.status.setText(tr('trade.ready') if reference else tr('trade.no_system'))
        self.reference.setText(tr('trade.reference', system=reference or '–'))
        self.refresh_observed_markets()

    @Slot()
    def refresh_observed_markets(self):
        fid = getattr(self.state, 'commander_fid', '')
        if fid != self._fid:
            for panel in self.remembered_lists.values():
                panel.clear()
            self._fid = fid
            self._generation += 1
            self.cancel_search()
            self.offers = ()
            self.table.setRowCount(0)
            self._invalidate_results()
        # Only count currently fresh observations; keep older snapshots on disk.
        if self._refreshing_observed:
            return
        self._refreshing_observed = True
        try:
            observer = getattr(self.state, 'observed_markets', None)
            fid = getattr(self.state, 'commander_fid', '')
            markets = observer.cache.all(fid, max_age=self.max_age.max_age()) if observer is not None and fid else []
            markets = {row['market_id']: row for row in markets
                       if row['fid'] == fid and row['source'] == 'local_elite'}
            count = len(markets)
            text = tr('trade.observed_one' if count == 1 else 'trade.observed_many', count=count)
            if markets:
                latest = max(timestamp(row['observed_at']) for row in markets.values())
                now = observer.cache.clock()
                text += ' · ' + (tr('trade.observed_now') if (now - latest).total_seconds() < 60
                                else tr('trade.observed_last', age=format_age(latest, now)))
            self.observed_status.setText(text)
            self.observed_status.setToolTip(tr('trade.observed_tooltip'))
        finally:
            self._refreshing_observed = False

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_observed_markets()

    @Slot()
    def start_search(self):
        if self.worker is not None:
            return
        self.refresh_reference()
        commodity = self.commodity.currentData()
        if commodity is None:
            self.status.setText(tr('trade.choose_commodity'))
            return
        if lookup_by_id(commodity) is None:
            self.status.setText(tr('trade.unknown_commodity'))
            return
        if not self._reference:
            self.status.setText(tr('trade.no_system'))
            return
        arrival = self.arrival.text().strip()
        distance = None
        if arrival:
            # Whole positive light seconds, with an explicit upper bound.
            if not arrival.isascii() or not arrival.isdecimal() or len(arrival) > 10:
                self.status.setText(tr('trade.invalid_arrival'))
                return
            distance = int(arrival)
            if not 1 <= distance <= 2147483647:
                self.status.setText(tr('trade.invalid_arrival'))
                return
        self.quantity.interpretText()
        self._query = MarketSearch(
            commodity, self._reference, radius_ly=self.radius.currentData(),
            minimum_quantity=self.quantity.value(), max_age=self.max_age.max_age(),
            required_pad=PadSize(self.pad.currentData()), include_fleet_carriers=self.carriers.isChecked(),
            max_distance_to_arrival_ls=distance, limit=100,
        )
        self.table.setRowCount(0)
        self.offers = ()
        self.status.setText(tr('trade.buy_searching' if self.side == TradeSide.BUY else 'trade.sell_searching'))
        self.filters.setEnabled(False)
        self.search_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.cancel_button.show()
        from .recommendations_view import local_distances
        observer = getattr(self.state, 'observed_markets', None)
        cache = observer.cache if observer is not None else None
        local = cache.all(self._fid, max_age=None) if cache is not None and self._fid else []
        origin = dict(system_name=self._reference,
                      system_address=getattr(self.state, 'system_address', None))
        distances = local_distances(self.state, origin, local) if local else {}
        self.worker = MarketWorker(self.provider, self._query, self.side, self._generation,
                                   local_markets=local, distances=distances, fid=self._fid,
                                   clock=cache.clock if cache is not None else None)
        self._cancel_event = self.worker.cancel
        self.destroyed.connect(self._cancel_event.set)
        self.worker.signals.finished.connect(self._finished)
        self.pool.start(self.worker)

    @Slot()
    def cancel_search(self):
        if self.worker is not None:
            self.worker.cancel.set()
            self.cancel_button.setEnabled(False)
            self.cancel_button.hide()
            self.status.setText(tr('trade.cancelling'))

    def closeEvent(self, event):
        self.cancel_search()
        self.recommendations.cancel_search()
        super().closeEvent(event)

    @Slot(object)
    def _finished(self, result):
        stale_direction = self.worker is not None and self.worker.generation != self._generation
        cancelled = self.worker is not None and self.worker.cancel.is_set()
        self.destroyed.disconnect(self._cancel_event.set)
        self.worker = None
        self._cancel_event = None
        self.filters.setEnabled(True)
        self.search_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.cancel_button.hide()
        if stale_direction:
            self._invalidate_results()
            return
        if cancelled or self._query.reference_system != self._reference:
            result = MarketSearchResult(MarketStatus.CANCELLED, query=self._query)
        self.show_result(result, self._query)

    def show_result(self, result, query):
        """Retain offers by row identity for future actions; no route action yet."""
        blocker = QSignalBlocker(self.table)
        now = datetime.now(timezone.utc)
        locale = QLocale(get_language())
        self.offers = result.offers[:100] if result.status == MarketStatus.OK else ()
        if self.side == TradeSide.BUY:
            self.offers = tuple(o for o in self.offers if o.commander_buy_price is not None
                                and o.commander_buy_price > 0 and o.supply is not None
                                and o.supply >= (query.minimum_quantity or 1))
        self.market_notice.setText(market_notice_text(get_language())
                                   if any(o.provider == 'local_elite' for o in self.offers)
                                   else tr('trade.market_notice'))
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.offers))
        for row, offer in enumerate(self.offers):
            price = offer.commander_buy_price if self.side == TradeSide.BUY else offer.commander_sell_price
            amount = offer.supply if self.side == TradeSide.BUY else offer.demand
            revenue = (price * query.minimum_quantity if price is not None and amount is not None
                       and amount >= query.minimum_quantity else None)
            age = max(0, (now - offer.market_updated_at).total_seconds())
            items = [
                TextItem(offer.system_name), TextItem(offer.station_name),
                NumericItem(locale.toString(float(offer.distance_ly), 'f', 1) + ' ly', offer.distance_ly),
                NumericItem('–' if price is None else locale.toString(price) + ' Cr', price),
                NumericItem('–' if amount is None else locale.toString(amount), amount),
                NumericItem('–' if revenue is None else locale.toString(revenue) + ' Cr', revenue),
                NumericItem('–' if offer.distance_to_arrival_ls is None else locale.toString(float(offer.distance_to_arrival_ls), 'f', 0), offer.distance_to_arrival_ls),
                PadItem(tr('trade.pad_' + offer.largest_pad.value) if offer.largest_pad else '–', offer.largest_pad),
                NumericItem(format_age(offer.market_updated_at, now), age),
                QTableWidgetItem(tr('trade.fleet_carrier') if offer.is_fleet_carrier else tr('trade.station')),
                self.remembered_lists[self.side].mark(offer),
            ]
            items[0].setData(Qt.ItemDataRole.UserRole, offer)
            items[8].setToolTip(offer.market_updated_at.astimezone(timezone.utc).isoformat())
            for column, item in enumerate(items):
                self.table.setItem(row, column, item)
        self.table.setSortingEnabled(True)
        self.table.sortItems(3, self._price_order())
        self.table.resizeColumnsToContents()
        # Keep long system/station names usable via tooltips and horizontal scrolling.
        self.table.resizeRowsToContents()
        for row in range(self.table.rowCount()):
            for column in (0, 1):
                item = self.table.item(row, column)
                source = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole).provider
                label = tr('recommend.local') if source == 'local_elite' else 'Spansh'
                item.setToolTip(item.text() + '\n' + tr('recommend.source') + ': ' + label)
        for column in (0, 1):
            self.table.setColumnWidth(column, min(300, self.table.columnWidth(column)))
        self.update_remembered()
        status_key = _STATUS_KEYS.get(result.status, 'trade.invalid_response')
        prefix = 'trade.buy_' if self.side == TradeSide.BUY else 'trade.sell_'
        if result.status in (MarketStatus.OK, MarketStatus.NO_RESULTS):
            status_key = prefix + ('success_one' if len(self.offers) == 1 else
                                   'success' if self.offers else 'no_results')
        message = tr(status_key, count=len(self.offers))
        if result.community_failure is not None:
            message += '\n' + community_failure_text(get_language())
        if result.truncated:
            message += '\n' + tr('trade.truncated')
        if result.from_cache:
            message += '\n' + ('Spansh: ' if any(o.provider == 'local_elite' for o in self.offers) else '') + tr('trade.cached')
        self.status.setText(message)

    def remember_changed(self, item):
        if item.column() != 10:
            return
        self.remembered_lists[self.side].changed(item, item.data(Qt.UserRole))
        self.update_remembered()

    def update_remembered(self):
        for side, panel in self.remembered_lists.items():
            panel.setVisible(side == self.side and bool(panel.targets))
        blocker = QSignalBlocker(self.table)
        for row in range(self.table.rowCount()):
            marked = self.table.item(row, 10).checkState() == Qt.Checked
            for column in range(self.table.columnCount()):
                self.table.item(row, column).setData(Qt.UserRole + 1, marked)
