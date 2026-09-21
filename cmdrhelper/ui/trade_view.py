"""Manual, transient trade UI. Identity and network semantics belong to providers."""
from datetime import datetime, timedelta, timezone
from threading import Event

from PySide6.QtCore import QObject, QLocale, QRunnable, QThreadPool, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QPushButton, QScrollArea, QSpinBox, QTableWidget,
    QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

from cmdrhelper.commodity_master import lookup_by_id
from cmdrhelper.i18n import get_language, tr
from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus, PadSize
from cmdrhelper.spansh_market import SpanshMarketProvider
from cmdrhelper.ui.commodity_picker import CommodityField


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
    def __init__(self, provider, query):
        super().__init__()
        self.provider, self.query = provider, query
        self.cancel = Event()
        self.signals = MarketSignals()

    @Slot()
    def run(self):
        try:
            result = self.provider.search_sell(self.query, cancel=self.cancel)
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
    """Sell is an independent tab; later trade workflows can add their own tabs."""

    def __init__(self, state, parent=None, *, provider=None, pool=None):
        super().__init__(parent)
        self.state = state
        self.provider = provider if provider is not None else SpanshMarketProvider()
        self.pool = pool if pool is not None else QThreadPool.globalInstance()
        self.worker = None
        self._query = None
        self.offers = ()
        self._reference = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(tr('nav.trade'), objectName='sectionTitle'))
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll.setWidget(content)
        self.tabs.addTab(scroll, tr('trade.sell'))
        body = QVBoxLayout(content)
        self.reference = QLabel()
        self.reference.setTextFormat(Qt.TextFormat.PlainText)
        self.reference.setWordWrap(True)
        body.addWidget(self.reference)
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
        self.max_age = QComboBox()
        for hours in (1, 6, 12, 24, 72, 168):
            self.max_age.addItem(tr('trade.age_option_' + str(hours)), hours)
        self.max_age.setCurrentIndex(3)
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
        self.table = QTableWidget(0, 10)
        self.table.setHorizontalHeaderLabels([tr('trade.' + key) for key in (
            'system', 'station', 'distance', 'price', 'demand', 'revenue', 'arrival_column', 'pad', 'age', 'type')])
        for column in range(self.table.columnCount()):
            self.table.horizontalHeaderItem(column).setData(
                Qt.ItemDataRole.InitialSortOrderRole,
                Qt.SortOrder.DescendingOrder if column == 3 else Qt.SortOrder.AscendingOrder)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setMinimumHeight(240)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()
        body.addWidget(self.table, 1)
        self.commodity.commodityChanged.connect(self._invalidate_results)
        for field in (self.radius, self.max_age, self.pad):
            field.currentIndexChanged.connect(self._invalidate_results)
        self.quantity.valueChanged.connect(self._invalidate_results)
        self.carriers.toggled.connect(self._invalidate_results)
        self.arrival.textChanged.connect(self._invalidate_results)
        self.search_button.clicked.connect(self.start_search)
        self.cancel_button.clicked.connect(self.cancel_search)
        changed = getattr(state, 'changed', None)
        if changed is not None:
            changed.connect(self.refresh_reference)
        QApplication.instance().aboutToQuit.connect(self.cancel_search)
        # A removed page must also stop background work without waiting on the GUI thread.
        self._cancel_event = None
        self.refresh_reference()

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
            minimum_quantity=self.quantity.value(), max_age=timedelta(hours=self.max_age.currentData()),
            required_pad=PadSize(self.pad.currentData()), include_fleet_carriers=self.carriers.isChecked(),
            max_distance_to_arrival_ls=distance, limit=100,
        )
        self.table.setRowCount(0)
        self.offers = ()
        self.status.setText(tr('trade.sell_searching'))
        self.filters.setEnabled(False)
        self.search_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.cancel_button.show()
        self.worker = MarketWorker(self.provider, self._query)
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
        super().closeEvent(event)

    @Slot(object)
    def _finished(self, result):
        cancelled = self.worker is not None and self.worker.cancel.is_set()
        self.destroyed.disconnect(self._cancel_event.set)
        self.worker = None
        self._cancel_event = None
        self.filters.setEnabled(True)
        self.search_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.cancel_button.hide()
        if cancelled or self._query.reference_system != self._reference:
            result = MarketSearchResult(MarketStatus.CANCELLED, query=self._query)
        self.show_result(result, self._query)

    def show_result(self, result, query):
        """Retain offers by row identity for future actions; no route action yet."""
        now = datetime.now(timezone.utc)
        locale = QLocale(get_language())
        self.offers = result.offers[:100] if result.status == MarketStatus.OK else ()
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(self.offers))
        for row, offer in enumerate(self.offers):
            price = offer.commander_sell_price
            revenue = (price * query.minimum_quantity if price is not None and offer.demand is not None
                       and offer.demand >= query.minimum_quantity else None)
            age = max(0, (now - offer.market_updated_at).total_seconds())
            items = [
                TextItem(offer.system_name), TextItem(offer.station_name),
                NumericItem(locale.toString(float(offer.distance_ly), 'f', 1) + ' ly', offer.distance_ly),
                NumericItem('–' if price is None else locale.toString(price) + ' Cr', price),
                NumericItem('–' if offer.demand is None else locale.toString(offer.demand), offer.demand),
                NumericItem('–' if revenue is None else locale.toString(revenue) + ' Cr', revenue),
                NumericItem('–' if offer.distance_to_arrival_ls is None else locale.toString(float(offer.distance_to_arrival_ls), 'f', 0), offer.distance_to_arrival_ls),
                PadItem(tr('trade.pad_' + offer.largest_pad.value) if offer.largest_pad else '–', offer.largest_pad),
                NumericItem(format_age(offer.market_updated_at, now), age),
                QTableWidgetItem(tr('trade.fleet_carrier') if offer.is_fleet_carrier else tr('trade.station')),
            ]
            items[0].setData(Qt.ItemDataRole.UserRole, offer)
            items[8].setToolTip(offer.market_updated_at.astimezone(timezone.utc).isoformat())
            for column, item in enumerate(items):
                self.table.setItem(row, column, item)
        self.table.setSortingEnabled(True)
        self.table.sortItems(3, Qt.SortOrder.DescendingOrder)
        self.table.resizeColumnsToContents()
        # Keep long system/station names usable via tooltips and horizontal scrolling.
        for row in range(self.table.rowCount()):
            for column in (0, 1):
                item = self.table.item(row, column)
                item.setToolTip(item.text())
        for column in (0, 1):
            self.table.setColumnWidth(column, min(300, self.table.columnWidth(column)))
        status_key = _STATUS_KEYS.get(result.status, 'trade.invalid_response')
        if result.status == MarketStatus.OK and len(self.offers) == 1:
            status_key = 'trade.sell_success_one'
        message = tr(status_key, count=len(self.offers))
        if result.truncated:
            message += '\n' + tr('trade.truncated')
        if result.from_cache:
            message += '\n' + tr('trade.cached')
        self.status.setText(message)
