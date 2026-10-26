"""Location-independent, read-only browser of complete saved commodity markets."""
from datetime import timedelta
from threading import Event
import logging

from PySide6.QtCore import (QAbstractTableModel, QModelIndex, QObject, QLocale, QRunnable,
                           QSortFilterProxyModel, QThreadPool, Qt, Signal, Slot)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QDoubleSpinBox, QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSizePolicy, QSplitter, QTableView, QVBoxLayout, QWidget)

from cmdrhelper.commodity_localization import commodity_name
from cmdrhelper.commodity_master import lookup_by_id, lookup_by_symbol
from cmdrhelper.i18n import get_language, tr
from cmdrhelper.mining_catalog import MINING_COMMODITIES
from cmdrhelper.observed_market_cache import timestamp, utcnow
from cmdrhelper.saved_markets import (ReadCancelled, read_market, read_markets,
                                     read_reference, source_from_state)
from .market_age import HOURS

logger = logging.getLogger(__name__)
MINING = frozenset(c.symbol.casefold() for c in MINING_COMMODITIES)


def quantity_text(value, locale):
    if value is None:
        return '—'
    if value <= 2**63 - 1:
        return locale.toString(value)
    # SQLite supports uint64 values; Qt's Python signed integer overload does
    # not. Keep every digit instead of converting large amounts to float.
    return format(value, ',').replace(',', locale.groupSeparator())


class BrowseModel(QAbstractTableModel):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        self.columns, self.rows = columns, []

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.columns)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return tr(self.columns[section])
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row, col = self.rows[index.row()], index.column()
        if role == Qt.DisplayRole:
            return row['display'][col]
        if role == Qt.UserRole:
            return row['values'][col]
        if role == Qt.ToolTipRole:
            return row.get('tooltip', row['display'][col])
        if role == Qt.TextAlignmentRole and isinstance(row['values'][col], (int, float)):
            return Qt.AlignRight | Qt.AlignVCenter
        return None

    def replace(self, rows):
        self.beginResetModel()
        self.rows = rows
        self.endResetModel()


class BrowseProxy(QSortFilterProxyModel):
    def __init__(self, market=False, parent=None):
        super().__init__(parent)
        self.market = market
        self.search, self.radius, self.pad, self.age, self.mining = '', 0, '', None, False
        self.now = utcnow()
        self.setDynamicSortFilter(True)

    def lessThan(self, left, right):
        rows = self.sourceModel().rows
        a, b = rows[left.row()]['values'][left.column()], rows[right.row()]['values'][right.column()]
        if a is None or b is None:
            return a is not None and b is None
        if isinstance(a, str):
            return a.casefold() < b.casefold()
        return a < b

    def filterAcceptsRow(self, row, parent):
        item = self.sourceModel().rows[row]
        if self.search and self.search not in item['search']:
            return False
        if not self.market:
            return not self.mining or item['mining']
        if self.radius and (item['distance'] is None or item['distance'] > self.radius):
            return False
        if self.pad and item['pad'] != self.pad:
            return False
        return self.age is None or (self.now - item['header'].observed_at).total_seconds() <= self.age


class _Signals(QObject):
    finished = Signal(object)


class _Read(QRunnable):
    def __init__(self, kind, generation, fn, args):
        super().__init__()
        self.kind, self.generation, self.fn, self.args = kind, generation, fn, args
        self.cancel = Event()
        self.signals = _Signals()

    def run(self):
        try:
            result = self.fn(*self.args, cancel=self.cancel)
            error = None
        except ReadCancelled:
            result, error = None, 'cancelled'
        except Exception:
            logger.exception('Saved market read failed (%s)', self.kind)
            result, error = None, 'error'
        self.signals.finished.emit((self.kind, self.generation, result, error))


class SavedMarketsView(QWidget):
    def __init__(self, state, parent=None, *, pool=None, clock=utcnow):
        super().__init__(parent)
        self.state, self.clock = state, clock
        self.pool = pool or QThreadPool.globalInstance()
        self.source = source_from_state(state)
        self._jobs, self._generations = {}, dict(headers=0, detail=0, reference=0)
        self._cancel_events = set()
        events = self._cancel_events
        self.destroyed.connect(lambda *_: [e.set() for e in tuple(events)])
        QApplication.instance().aboutToQuit.connect(self.cancel_reads)
        self._dirty, self._loaded = True, False
        self._header_error = False
        self._headers, self._reference_coordinates = [], None
        self._selected_id, self._snapshot = None, None
        self._reference_name = str(getattr(state, 'system', '') or '').strip('– ')
        self._manual_reference = False
        layout = QVBoxLayout(self)
        self.notice = QLabel(tr('browse.notice'))
        self.notice.setWordWrap(True)
        layout.addWidget(self.notice)
        self.splitter = QSplitter(Qt.Horizontal)
        self._splitter_initialized = False
        self.splitter.setChildrenCollapsible(False)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.splitter)
        layout.addWidget(self.scroll, 1)
        left, right = QWidget(), QWidget()
        self.splitter.addWidget(left)
        self.splitter.addWidget(right)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        left_layout, right_layout = QVBoxLayout(left), QVBoxLayout(right)
        left_layout.setContentsMargins(0, 0, 4, 0)
        right_layout.setContentsMargins(4, 0, 0, 0)
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr('browse.search'))
        self.search.setAccessibleName(tr('browse.search'))
        left_layout.addWidget(self.search)
        form = QFormLayout()
        form.setRowWrapPolicy(QFormLayout.WrapLongRows)
        self.reference = QLineEdit(self._reference_name)
        self.reference.setAccessibleName(tr('browse.reference'))
        self.apply_reference = QPushButton(tr('browse.apply'))
        reference_row = QWidget()
        reference_layout = QHBoxLayout(reference_row)
        reference_layout.setContentsMargins(0, 0, 0, 0)
        reference_layout.addWidget(self.reference, 1)
        reference_layout.addWidget(self.apply_reference)
        form.addRow(tr('browse.reference'), reference_row)
        self.radius = QDoubleSpinBox()
        self.radius.setRange(0, 1000000)
        self.radius.setDecimals(1)
        self.radius.setSpecialValueText(tr('trade.age_option_0'))
        self.radius.setSuffix(' ' + tr('browse.ly'))
        form.addRow(tr('browse.radius'), self.radius)
        self.pad = QComboBox()
        for label, value in ((tr('trade.pad_any'), ''), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('—', '?')):
            self.pad.addItem(label, value)
        self.pad.setToolTip(tr('browse.pad_help'))
        form.addRow(tr('trade.pad'), self.pad)
        self.age = QComboBox()
        for hours in (0, *(h for h in HOURS if h)):
            self.age.addItem(tr('trade.age_option_' + str(hours)), hours)
        form.addRow(tr('browse.max_age'), self.age)
        left_layout.addLayout(form)
        self.reference_status = QLabel()
        self.reference_status.setWordWrap(True)
        left_layout.addWidget(self.reference_status)
        refresh_row = QHBoxLayout()
        self.status = QLabel(tr('browse.loading'))
        self.status.setWordWrap(True)
        self.refresh_button = QPushButton(tr('browse.refresh'))
        refresh_row.addWidget(self.status, 1)
        refresh_row.addWidget(self.refresh_button)
        left_layout.addLayout(refresh_row)
        self.markets_model = BrowseModel(('trade.system', 'trade.station', 'browse.market_id',
            'browse.distance', 'trade.pad', 'trade.age', 'facilities.type'), self)
        self.markets_proxy = BrowseProxy(True, self)
        self.markets_table = self._table(self.markets_model, self.markets_proxy)
        for column, width in enumerate((170, 180, 120, 120, 90, 170, 120)):
            self.markets_table.setColumnWidth(column, width)
        left_layout.addWidget(self.markets_table, 1)
        self.detail_header = QLabel(tr('browse.select'))
        self.detail_header.setTextFormat(Qt.PlainText)
        self.detail_header.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.detail_header.setWordWrap(True)
        right_layout.addWidget(self.detail_header)
        self.goods_search = QLineEdit()
        self.goods_search.setPlaceholderText(tr('browse.goods_search'))
        self.goods_search.setAccessibleName(tr('browse.goods_search'))
        right_layout.addWidget(self.goods_search)
        self.mining_only = QCheckBox(tr('browse.mining'))
        right_layout.addWidget(self.mining_only)
        self.goods_model = BrowseModel(('browse.commodity', 'browse.buy', 'browse.sell',
                                       'browse.supply', 'browse.demand'), self)
        self.goods_proxy = BrowseProxy(parent=self)
        self.goods_table = self._table(self.goods_model, self.goods_proxy)
        self.goods_table.setColumnWidth(0, 180)
        for column in range(1, 5):
            self.goods_table.setColumnWidth(column, 130)
        right_layout.addWidget(self.goods_table, 1)
        self.goods_status = QLabel()
        self.goods_status.setWordWrap(True)
        right_layout.addWidget(self.goods_status)
        self.markets_table.selectionModel().currentRowChanged.connect(self._selection_changed)
        self.search.textChanged.connect(self.filter_markets)
        self.radius.valueChanged.connect(self.filter_markets)
        self.pad.currentIndexChanged.connect(self.filter_markets)
        self.age.currentIndexChanged.connect(self.filter_markets)
        self.goods_search.textChanged.connect(self.filter_goods)
        self.mining_only.toggled.connect(self.filter_goods)
        self.apply_reference.clicked.connect(self.change_reference)
        self.reference.returnPressed.connect(self.change_reference)
        self.refresh_button.clicked.connect(self.reload)
        signal = getattr(state, 'observedMarketsChanged', None)
        if signal is not None:
            signal.connect(self.mark_dirty)
        # Commander movement never changes a manual reference or selected market.
        self.markets_table.sortByColumn(0, Qt.AscendingOrder)
        self.goods_table.sortByColumn(0, Qt.AscendingOrder)

    def _table(self, model, proxy):
        proxy.setSourceModel(model)
        table = QTableView()
        table.setObjectName('savedMarketTable')
        table.setModel(proxy)
        table.setSortingEnabled(True)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.verticalHeader().hide()
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.horizontalHeader().setStretchLastSection(True)
        table.setMinimumSize(180, 130)
        table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        return table

    def resizeEvent(self, event):
        super().resizeEvent(event)
        orientation = Qt.Horizontal if self.width() >= 1050 else Qt.Vertical
        if not self._splitter_initialized or self.splitter.orientation() != orientation:
            self._splitter_initialized = True
            self.splitter.setOrientation(orientation)
            self.splitter.setSizes([self.width() // 2, self.width() // 2])

    def showEvent(self, event):
        super().showEvent(event)
        if not self._manual_reference:
            name = str(getattr(self.state, 'system', '') or '').strip('– ')
            self._reference_name = name
            self.reference.setText(name)
        if self._dirty or not self._loaded:
            self.reload()
        else:
            self._start_reference()
            self._render_markets()  # Update displayed age without a timer/DB read.

    @Slot()
    def cancel_reads(self):
        for event in tuple(self._cancel_events):
            event.set()

    def _start(self, kind, fn, *args):
        for (old_kind, _), job in tuple(self._jobs.items()):
            if old_kind == kind:
                job.cancel.set()
        self._generations[kind] += 1
        generation = self._generations[kind]
        job = _Read(kind, generation, fn, args)
        self._jobs[kind, generation] = job
        self._cancel_events.add(job.cancel)
        job.signals.finished.connect(self._finished)
        self.pool.start(job)

    @Slot()
    def mark_dirty(self):
        self._dirty = True
        if self.isVisible() and not any(k[0] == 'headers' for k in self._jobs):
            self.reload()

    @Slot()
    def reload(self):
        self._dirty = False
        self.source = source_from_state(self.state)
        self.status.setText(tr('browse.loading'))
        self.refresh_button.setEnabled(False)
        self._start('headers', lambda source, cancel: read_markets(source, cancel, clock=self.clock), self.source)
        self._start_reference()

    def _start_reference(self):
        self._reference_coordinates = None
        self._render_markets()
        self._start('reference', read_reference, self.source, self._reference_name)

    @Slot()
    def change_reference(self):
        self._manual_reference = True
        self._reference_name = self.reference.text().strip()
        self._start_reference()

    @Slot(object)
    def _finished(self, message):
        kind, generation, result, error = message
        job = self._jobs.pop((kind, generation), None)
        if job:
            self._cancel_events.discard(job.cancel)
        if generation != self._generations[kind]:
            return
        if error == 'cancelled':
            return
        if kind == 'reference':
            self._reference_coordinates = result if error is None else None
            self._render_markets()
        elif kind == 'headers':
            self.refresh_button.setEnabled(True)
            self._loaded = True
            self._header_error = bool(error)
            self._headers = result[0] if error is None else []
            self._metadata_incomplete = result[1] if error is None else False
            self._render_markets()
            if error:
                self.status.setText(tr('browse.error'))
            elif self._selected_id is not None:
                self._load_detail(self._selected_id)
            if self._dirty and self.isVisible():
                self.reload()
        elif kind == 'detail':
            self._snapshot = result if error is None else None
            self._render_goods()
            self._render_detail()
            if error:
                self.detail_header.setText(tr('browse.error'))

    def _distance(self, item):
        target = item['coordinates']
        return self._reference_coordinates.distance_to(target) if self._reference_coordinates and target else None

    def _render_markets(self):
        from .trade_view import format_age
        locale, now = QLocale(get_language()), self.clock()
        records = []
        for item in self._headers:
            h = item['header']
            distance = self._distance(item)
            pad = item['pad'].value[0].upper() if item['pad'] else '?'
            age = (now - h.observed_at).total_seconds()
            old = age >= 86400
            age_text = format_age(h.observed_at, now)
            if old:
                age_text += ' · ' + tr('browse.old')
            values = (h.system_name, h.station_name, h.market_id, distance,
                      {'S': 0, 'M': 1, 'L': 2}.get(pad), age, h.station_type)
            records.append(dict(header=h, distance=distance, pad=pad, age=age,
                values=values, display=(h.system_name, h.station_name, str(h.market_id),
                    locale.toString(distance, 'f', 1) if distance is not None else '—',
                    pad if pad != '?' else '—', age_text, h.station_type or '—'),
                search=f'{h.system_name} {h.station_name} {h.market_id}'.casefold(),
                tooltip=f'{h.system_name} · {h.station_name}\nMarketID: {h.market_id}\n{self._date(h.observed_at)}'))
        selected = self._selected_id
        self.markets_table.selectionModel().blockSignals(True)
        self.markets_model.replace(records)
        self.filter_markets()
        self.markets_table.selectionModel().blockSignals(False)
        self._restore_selection(selected)
        self.reference_status.setText(tr('browse.reference_unknown') if self._reference_coordinates is None
                                      else tr('browse.reference') + ': ' + self._reference_name)
        self._render_detail()

    def _restore_selection(self, market_id):
        if market_id is None:
            return
        for index, row in enumerate(self.markets_model.rows):
            if row['header'].market_id == market_id:
                proxy = self.markets_proxy.mapFromSource(self.markets_model.index(index, 0))
                if proxy.isValid():
                    self.markets_table.setCurrentIndex(proxy)
                return
        self._clear_detail()

    @Slot()
    def filter_markets(self):
        proxy = self.markets_proxy
        proxy.search = self.search.text().strip().casefold()
        proxy.radius, proxy.pad = self.radius.value(), self.pad.currentData()
        hours = self.age.currentData()
        proxy.age = hours * 3600 if hours else None
        proxy.now = self.clock()
        # Proxy filtering can move currentRow; do not let it open another market.
        selection = self.markets_table.selectionModel()
        was_blocked = selection.blockSignals(True)
        proxy.invalidateFilter()
        self.markets_table.setCurrentIndex(QModelIndex())
        for index, row in enumerate(self.markets_model.rows):
            if row['header'].market_id == self._selected_id:
                selected = proxy.mapFromSource(self.markets_model.index(index, 0))
                if selected.isValid():
                    self.markets_table.setCurrentIndex(selected)
                break
        selection.blockSignals(was_blocked)
        self.status.setText(tr('browse.markets', shown=proxy.rowCount(), total=len(self._headers)))
        if not self._headers and self._loaded:
            self.status.setText(tr('browse.empty'))
        if self._header_error:
            self.status.setText(tr('browse.error'))
        if getattr(self, '_metadata_incomplete', False):
            self.status.setText(self.status.text() + '\n' + tr('browse.metadata_missing'))

    def _selection_changed(self, current, previous):
        if not current.isValid():
            return
        row = self.markets_model.rows[self.markets_proxy.mapToSource(current).row()]
        mid = row['header'].market_id
        if mid != self._selected_id:
            self._load_detail(mid)

    def _load_detail(self, market_id):
        self._selected_id, self._snapshot = market_id, None
        self.goods_model.replace([])
        self.goods_status.setText('')
        self.detail_header.setText(tr('browse.loading'))
        self._start('detail', lambda source, mid, cancel: read_market(source, mid, cancel, clock=self.clock),
                    self.source, market_id)

    def _clear_detail(self):
        self._generations['detail'] += 1
        for (kind, _), job in self._jobs.items():
            if kind == 'detail':
                job.cancel.set()
        self._selected_id, self._snapshot = None, None
        self.goods_model.replace([])
        self.goods_status.setText('')
        self.detail_header.setText(tr('browse.select'))

    @staticmethod
    def _date(value):
        return value.astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')

    def _render_detail(self):
        if self._selected_id is None:
            return
        if self._snapshot is None:
            loading = any(k[0] == 'detail' and k[1] == self._generations['detail'] for k in self._jobs)
            self.detail_header.setText(tr('browse.loading' if loading else 'browse.missing'))
            return
        row = self._snapshot
        item = next((i for i in self._headers if i['header'].market_id == self._selected_id), None)
        if item and any(getattr(item['header'], key) != row.get(key)
                        for key in ('station_name', 'system_name', 'system_address')):
            item = None  # A carrier may have moved between list and detail reads.
        distance = self._distance(item) if item else None
        pad = item['pad'].value[0].upper() if item and item['pad'] else '—'
        distance_text = QLocale(get_language()).toString(distance, 'f', 1) if distance is not None else '—'
        stamp = timestamp(row['observed_at'])
        updated = self._date(stamp)
        if self.clock() - stamp >= timedelta(days=1):
            updated += ' · ' + tr('browse.old')
        self.detail_header.setText(
            f"{row['system_name']} · {row['station_name']}\n"
            f"MarketID: {row['market_id']} · {tr('facilities.type')}: {row.get('station_type') or '—'}\n"
            f"{tr('trade.pad')}: {pad} · {tr('browse.distance')}: {distance_text}\n"
            f"{tr('browse.updated')}: {updated}\n"
            f"{tr('browse.source')}: {tr('browse.local')} ({row['source']})")

    def _render_goods(self):
        locale, rows = QLocale(get_language()), []
        for item in (self._snapshot or {}).get('commodities', []):
            master = lookup_by_id(item.get('commodity_id')) or lookup_by_symbol(item['symbol'])
            name = commodity_name(master) if master else item.get('localized_name') or item['symbol']
            values = (name, *(item.get(k) for k in
                ('commander_buy_price', 'commander_sell_price', 'supply', 'demand')))
            # Keep integers as sort keys; formatting never determines order.
            display = (name, *(quantity_text(v, locale) for v in values[1:]))
            symbol = master.symbol if master else item['symbol']
            rows.append(dict(values=values, display=display,
                search=f'{name} {symbol}'.casefold(), mining=symbol.casefold() in MINING))
        self.goods_model.replace(rows)
        self.filter_goods()

    @Slot()
    def filter_goods(self):
        self.goods_proxy.search = self.goods_search.text().strip().casefold()
        self.goods_proxy.mining = self.mining_only.isChecked()
        self.goods_proxy.invalidateFilter()
        self.goods_status.setText(tr('browse.goods', shown=self.goods_proxy.rowCount(), total=len(self.goods_model.rows)))
