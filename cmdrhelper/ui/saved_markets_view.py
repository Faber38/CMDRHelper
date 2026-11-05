"""Location-independent, read-only browser of complete saved commodity markets."""
from cmdrhelper.exit_tasks import submit
from datetime import timedelta
from threading import Event
import logging

from PySide6.QtCore import (QAbstractTableModel, QModelIndex, QObject, QLocale, QRunnable,
                           QSortFilterProxyModel, QThreadPool, Qt, Signal, Slot)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QButtonGroup, QRadioButton, QComboBox,
    QDoubleSpinBox, QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QPushButton, QScrollArea, QSizePolicy, QSplitter, QTableView, QVBoxLayout, QWidget)

from cmdrhelper.commodity_localization import commodity_name
from cmdrhelper.commodity_master import lookup_by_id, lookup_by_symbol
from cmdrhelper.i18n import get_language, tr
from cmdrhelper.mining_catalog import MINING_COMMODITIES
from cmdrhelper.ship_cargo import current_ship_inventory
from cmdrhelper.observed_market_cache import timestamp, utcnow
from cmdrhelper.saved_markets import (ReadCancelled, read_market, read_markets,
                                     read_reference, source_from_state)
from .market_age import HOURS
from .mission_cargo import (MISSION_CARGO_ROLE, MissionCargoDelegate,
                            current_mission_cargo, mission_cargo_tooltip,
                            POSSIBLE_MISSION_CARGO_ROLE,
                            current_possible_mission_cargo, possible_mission_cargo_tooltip,
                            CargoMissionLegend)

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
        if role == MISSION_CARGO_ROLE and col == 0:
            return row.get('mission_cargo')
        if role == POSSIBLE_MISSION_CARGO_ROLE and col == 0:
            return row.get('possible_mission_cargo')
        if role == Qt.ToolTipRole:
            parts = [row.get('tooltip', row['display'][col])]
            if col == 0:
                if row.get('mission_cargo'):
                    parts.append(mission_cargo_tooltip(row['mission_cargo'], own_cargo=True))
                if row.get('possible_mission_cargo'):
                    parts.append(possible_mission_cargo_tooltip(row['possible_mission_cargo']))
            return '\n'.join(parts)
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
        self.cargo_ids = None  # None: inactive/paused; empty set: confirmed empty.
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
            return ((not self.mining or item['mining'])
                    and (self.cargo_ids is None or item.get('commodity_id') in self.cargo_ids))
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
        self._reference_key = None
        self._goods_filter_key = None
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
        self.goods_mode = QButtonGroup(self)
        self.all_goods = QRadioButton(tr('browse.all_goods'))
        self.mining_only = QRadioButton(tr('browse.mining'))
        self.cargo_only = QRadioButton(tr('browse.cargo_only'))
        # A short vertical group also fits long translations in the split view.
        goods_filters = QVBoxLayout()
        goods_filters.setSpacing(2)
        for mode, button in enumerate((self.all_goods, self.mining_only, self.cargo_only)):
            self.goods_mode.addButton(button, mode)
            goods_filters.addWidget(button)
        self.all_goods.setChecked(True)
        right_layout.addLayout(goods_filters)
        self.cargo_notice = QLabel()
        self.cargo_notice.setTextFormat(Qt.PlainText)
        self.cargo_notice.setWordWrap(True)
        self.cargo_notice.hide()
        right_layout.addWidget(self.cargo_notice)
        self.cargo_mission_legend = CargoMissionLegend()
        right_layout.addWidget(self.cargo_mission_legend)
        self.goods_model = BrowseModel(('browse.commodity', 'browse.buy', 'browse.sell',
                                       'browse.supply', 'browse.demand'), self)
        self.goods_proxy = BrowseProxy(parent=self)
        self.goods_table = self._table(self.goods_model, self.goods_proxy)
        self.goods_table.setItemDelegateForColumn(0, MissionCargoDelegate(self.goods_table))
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
        self.goods_mode.idToggled.connect(self._goods_mode_changed)
        for name in ('cargoSnapshotChanged', 'changed', 'commanderIdentityChanged',
                     'viewedCommanderChanged', 'shipLoadoutChanged'):
            signal = getattr(state, name, None)
            if signal is not None:
                signal.connect(self._cargo_changed)
        self.apply_reference.clicked.connect(self.change_reference)
        self.reference.returnPressed.connect(self.change_reference)
        self.refresh_button.clicked.connect(self.reload)
        signal = getattr(state, 'observedMarketsChanged', None)
        if signal is not None:
            signal.connect(self.mark_dirty)
        signal = getattr(state, 'databaseImportFinished', None)
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
        self.filter_goods()
        if not self._manual_reference:
            name = str(getattr(self.state, 'system', '') or '').strip('– ')
            self._reference_name = name
            self.reference.setText(name)
        source = source_from_state(self.state)
        if self._dirty or not self._loaded or source != self.source:
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
        submit(self.pool, job)

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
        self._start_reference(force=True)

    def _start_reference(self, *, force=False):
        key = (self.source.database_path, self._reference_name.casefold())
        if key == self._reference_key and not force:
            return
        if key != self._reference_key:
            # Never apply the previous system's distances to a new reference.
            self._reference_coordinates = None
        self._reference_key = key
        self._start('reference', read_reference, self.source, self._reference_name)
        self._render_markets()

    @Slot()
    def change_reference(self):
        self._manual_reference = True
        self._reference_name = self.reference.text().strip()
        if source_from_state(self.state) != self.source:
            self.reload()
        else:
            self._start_reference(force=self._reference_coordinates is None)

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
        bars = (self.markets_table.horizontalScrollBar(), self.markets_table.verticalScrollBar())
        positions = [bar.value() for bar in bars]
        selection = self.markets_table.selectionModel()
        blocked = selection.blockSignals(True)
        model = self.markets_model
        if ([row['header'].market_id for row in records]
                != [row['header'].market_id for row in model.rows]):
            model.replace(records)
        else:
            # Age, distance and metadata updates do not change row identity.
            previous, model.rows = model.rows, records
            for index, (old, new) in enumerate(zip(previous, records)):
                if old != new:
                    model.dataChanged.emit(model.index(index, 0),
                                           model.index(index, model.columnCount() - 1))
        self.filter_markets()
        self._restore_selection(selected)
        selection.blockSignals(blocked)
        for bar, position in zip(bars, positions):
            bar.setValue(position)
        pending = ('reference', self._generations['reference']) in self._jobs
        self.reference_status.setText(
            tr('browse.reference_loading') if pending and self._reference_coordinates is None else
            tr('browse.reference_unknown') if self._reference_coordinates is None else
            tr('browse.reference') + ': ' + self._reference_name)
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
        selected = QModelIndex()
        for index, row in enumerate(self.markets_model.rows):
            if row['header'].market_id == self._selected_id:
                selected = proxy.mapFromSource(self.markets_model.index(index, 0))
                break
        if selected != self.markets_table.currentIndex():
            self.markets_table.setCurrentIndex(selected)
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
                commodity_id=master.frontier_id if master else item.get('commodity_id'),
                search=f'{name} {symbol}'.casefold(), mining=symbol.casefold() in MINING))
        self.goods_model.replace(rows)
        self._refresh_mission_cargo()
        self.filter_goods()

    def _cargo_changed(self, *_):
        self._refresh_mission_cargo()
        if self.cargo_only.isChecked():
            self.filter_goods()

    def _refresh_mission_cargo(self):
        missions = current_mission_cargo(self.state)
        possible = current_possible_mission_cargo(self.state)
        self.cargo_mission_legend.refresh()
        for number, row in enumerate(self.goods_model.rows):
            details = missions.get(row.get('commodity_id'))
            candidate = possible.get(row.get('commodity_id'))
            if details != row.get('mission_cargo') or candidate != row.get('possible_mission_cargo'):
                row['mission_cargo'] = details
                row['possible_mission_cargo'] = candidate
                index = self.goods_model.index(number, 0)
                self.goods_model.dataChanged.emit(index, index,
                    [MISSION_CARGO_ROLE, POSSIBLE_MISSION_CARGO_ROLE, Qt.ToolTipRole])

    @Slot(int, bool)
    def _goods_mode_changed(self, mode, checked):
        if checked:
            self.filter_goods()

    def _cargo_filter(self):
        if not self.cargo_only.isChecked():
            return None, ''
        state = self.state
        viewed = getattr(state, 'viewed_commander_id', None)
        if ((viewed is not None and viewed != getattr(state, 'commander_id', None))
                or (getattr(state, 'sources', None) is not None
                    and not getattr(state, '_source_live_context', False))):
            return None, tr('browse.cargo_unavailable')
        # Revalidate in memory, not the signal payload (which may be SRV cargo)
        # or a cached ship_inventory still awaiting the end of a state refresh.
        snapshot = current_ship_inventory(state)
        if snapshot is None:
            return None, tr('browse.cargo_unavailable')
        ids = set()
        for row in snapshot['inventory']:
            if row['count'] <= 0:
                continue
            master = lookup_by_symbol(row['frontier_name'])
            if master is None:
                # Never guess from translated names or silently drop an unknown
                # positive stock. Retain the user's choice, visibly paused.
                return None, tr('browse.cargo_identity_unknown')
            ids.add(master.frontier_id)
        return ids, tr('browse.cargo_empty') if not ids else ''

    @Slot()
    def filter_goods(self):
        # Validate provenance on every relevant signal BEFORE comparing the
        # effective filter. Quantities alone do not change membership.
        ids, notice = self._cargo_filter()
        search = self.goods_search.text().strip().casefold()
        key = (search, self.goods_mode.checkedId(),
               None if ids is None else frozenset(ids), notice)
        if key != self._goods_filter_key:
            self._goods_filter_key = key
            self.goods_proxy.search = search
            self.goods_proxy.mining = self.mining_only.isChecked()
            self.goods_proxy.cargo_ids = ids
            self.cargo_notice.setText(notice)
            self.cargo_notice.setVisible(bool(notice))
            self.goods_proxy.invalidateFilter()
        # A market-detail replacement resets the source model independently of
        # the filter key; its new row count must still reach the status label.
        self.goods_status.setText(tr('browse.goods', shown=self.goods_proxy.rowCount(), total=len(self.goods_model.rows)))
