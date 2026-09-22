"""Manual recommendations page; immutable inputs cross the worker boundary."""
from copy import deepcopy
from dataclasses import dataclass
from datetime import timedelta

from PySide6.QtCore import QObject, QRunnable, QLocale, Qt, Signal, Slot, QTimer, QSignalBlocker, QRectF
from PySide6.QtGui import QBrush, QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QSpinBox, QComboBox, QCheckBox, QLineEdit, QPushButton, QScrollArea, QTableWidget,
    QHeaderView, QApplication, QProgressBar, QFrame, QTableWidgetItem, QStyledItemDelegate, QStyle,
    QStyleOptionViewItem)

from cmdrhelper.cargo import free_cargo_space
from cmdrhelper.ship_identity import is_definite_non_ship
from cmdrhelper.commodity_master import lookup_by_id, lookup_by_symbol
from cmdrhelper.commodity_localization import commodity_name
from cmdrhelper.i18n import tr, get_language
from cmdrhelper.market_data import MarketSearch, PadSize
from cmdrhelper.observed_market_cache import timestamp
from .market_read_status import MarketReadStatus
from cmdrhelper.trade_recommendations import search_recommendations, RecommendationResult
from cmdrhelper.recommendation_diagnostic_text import format_recommendation_diagnostic
from cmdrhelper.recommendation_diagnostics import (
    RecommendationDiagnostics, RecommendationCancellation, PartialReason)


def diagnostic_reason_text(reason):
    category = {
        PartialReason.PROVIDER_NETWORK: 'network', PartialReason.PROVIDER_TIMEOUT: 'timeout',
        PartialReason.PROVIDER_HTTP: 'http', PartialReason.PROVIDER_RATE_LIMIT: 'rate_limit',
        PartialReason.PROVIDER_INVALID_RESPONSE: 'invalid_response',
        PartialReason.PROVIDER_UNKNOWN_SYSTEM: 'unknown_system',
        PartialReason.PROVIDER_TRUNCATED: 'limit', PartialReason.PROVIDER_PAGE_LIMIT: 'limit',
        PartialReason.PROVIDER_RESULT_LIMIT: 'limit', PartialReason.COMMODITY_ERROR: 'commodity',
        PartialReason.CANCELLED: 'cancelled', PartialReason.CONTEXT_CHANGED: 'context',
    }.get(reason, 'other')
    return tr('recommend.reason_' + category)



def current_market_context(state):
    """Require current dock context AND matching live state, not the last cache row."""
    observer = getattr(state, 'observed_markets', None)
    fid = getattr(state, 'commander_fid', '')
    context = getattr(observer, 'context', {})
    if (not fid or context.get('FID') != fid or not context.get('MarketID')
            or not context.get('StationName') or not context.get('StarSystem')
            or context['StationName'] != getattr(state, 'station', '')
            or context['StarSystem'] != getattr(state, 'system', '')):
        return None
    return context


def current_market(state):
    context = current_market_context(state)
    if context is None:
        return None
    fid = getattr(state, 'commander_fid', '')
    row = state.observed_markets.cache.get(fid, context['MarketID'])
    if (row is None or row['source'] != 'local_elite' or row['fid'] != fid
            or row['station_name'] != context['StationName'] or row['system_name'] != context['StarSystem']):
        return None
    return row


def ship_space(state):
    """Confirmed Ship Cargo includes all inventory, missions/stolen cargo and limpets.

    Status HUD fallback is display-only and deliberately not used for trading.
    """
    loadout = getattr(state, 'ship_loadout', None)
    name = (getattr(loadout, 'ship_name', '') or getattr(state, 'ship', '')
            or getattr(loadout, 'ship_type', '') or '–')
    snapshot = getattr(state, 'cargo_snapshot', None)
    fid = getattr(state, 'commander_fid', '')
    if (not fid or not isinstance(snapshot, dict) or snapshot.get('fid') != fid
            or snapshot.get('vessel') != 'Ship' or loadout is None
            or loadout.ship_id is None or snapshot.get('ship_id') != loadout.ship_id
            or is_definite_non_ship(loadout.ship_type)
            or not loadout.loadout_complete or loadout.loadout_stale):
        return name, None
    return name, free_cargo_space(snapshot.get('count'), loadout.cargo_capacity)


def local_distances(state, origin, markets):
    # Reuse the same stored-coordinate resolver and Coordinates.distance_to as
    # Favorites. No online lookup, DB schema change or guessed location.
    from cmdrhelper.ui.favorites_view import stored_coordinates
    result = {}
    database = getattr(state, 'database', None)
    if database is not None:
        with database._connect() as con:
            reference = stored_coordinates(con, origin.get('system_address'), origin['system_name'])
            for row in markets:
                target = stored_coordinates(con, row.get('system_address'), row['system_name'])
                result[row['market_id']] = reference.distance_to(target) if reference and target else None
    for row in markets:
        # Exact system identity is sufficient to know the distance is zero.
        if origin.get('system_address') is not None and row.get('system_address') == origin['system_address']:
            result[row['market_id']] = 0.0
    return result


class RecommendationSignals(QObject):
    progress = Signal(object)
    finished = Signal(object)
    diagnostic = Signal(object)


class RecommendationWorker(QRunnable):
    def __init__(self, origin, local, distances, free, margin, query, provider, clock, *, local_only=False):
        super().__init__()
        self.args = (origin, local, distances, free, margin, query, provider)
        self.clock = clock
        self.local_only = local_only
        self.cancel = RecommendationCancellation()
        self.diagnostics = RecommendationDiagnostics(local_only=local_only)
        self.signals = RecommendationSignals()

    def _validate_sources(self, result):
        if self.local_only and any(row.destination.provider != 'local_elite' for row in result.rows):
            raise ValueError('Non-local destination in local-only recommendations')

    def _publish_progress(self, result):
        self._validate_sources(result)
        self.signals.progress.emit(result)

    @Slot()
    def run(self):
        try:
            result = search_recommendations(*self.args, cancel=self.cancel, clock=self.clock,
                                            progress=self._publish_progress, diagnostics=self.diagnostics,
                                            diagnostic_progress=self.signals.diagnostic.emit, local_only=self.local_only)
            self._validate_sources(result)
        except Exception:
            cancelled = self.cancel.is_set()
            reason = self.cancel.reason if cancelled else PartialReason.OTHER
            self.diagnostics.reason(reason)
            if not cancelled:
                step = next((s for s in self.diagnostics.steps
                             if s.search_started and not s.local_completed), None)
                if step is None:
                    step = next((s for s in self.diagnostics.steps
                                 if s.commodity == self.diagnostics.current_commodity), None)
                if step is not None:
                    self.diagnostics.current_commodity = step.commodity
                    step.failed = True
                    self.diagnostics.reason(reason, step)
            result = RecommendationResult(partial=True, cancelled=cancelled,
                diagnostics=self.diagnostics.finish(partial=True, cancelled=cancelled, reason=reason))
        self.signals.finished.emit(result)


@dataclass(frozen=True)
class RememberedFlight:
    commodity_id: int | None
    commodity_symbol: str
    commodity_name: str
    market_id: int | None
    system_name: str
    station_name: str
    total_profit: int


def recommendation_identity(row):
    target = row.destination
    return (target.commodity_id, target.commodity_symbol, target.market_id,
            target.system_name, target.station_name)


class RememberedRecommendationDelegate(QStyledItemDelegate):
    """Remembered rows remain visible independently of selection and focus."""
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        if index.data(Qt.ItemDataRole.UserRole + 1):
            base = option.palette.base().color()
            accent = option.palette.highlight().color()
            option.backgroundBrush = QBrush(QColor(
                *[round(base.getRgb()[i] * .8 + accent.getRgb()[i] * .2) for i in range(3)]))
            option.state &= ~QStyle.StateFlag.State_Selected

    def paint(self, painter, option, index):
        if index.column() != 0:
            return super().paint(painter, option, index)
        option = QStyleOptionViewItem(option)
        self.initStyleOption(option, index)
        if not option.features & QStyleOptionViewItem.ViewItemFeature.HasCheckIndicator:
            return super().paint(painter, option, index)
        style = option.widget.style() if option.widget else QApplication.style()
        indicator = style.subElementRect(QStyle.SubElement.SE_ItemViewItemCheckIndicator,
                                        option, option.widget)
        # Keep the native indicator geometry, hit target and row sizing. Only
        # replace its paint; selection/focus and the remembered row stay native.
        option.features &= ~QStyleOptionViewItem.ViewItemFeature.HasCheckIndicator
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter, option.widget)
        light = option.palette.base().color().lightness() > 128
        enabled = bool(option.state & QStyle.StateFlag.State_Enabled)
        emphasized = enabled and bool(option.state & (
            QStyle.StateFlag.State_MouseOver | QStyle.StateFlag.State_HasFocus))
        checked = option.checkState == Qt.CheckState.Checked
        accent = QColor('#b47613' if light else '#ffb000')
        border = QColor('#995600' if light else '#ffc65c') if emphasized else accent
        fill = QColor('#c57a00' if light else '#ffb000')
        tick = QColor('#080d12')
        if not enabled:
            border = fill = QColor('#a0a8af' if light else '#58636d')
            tick = QColor('#edf1f5' if light else '#b8c0c8')
        painter.save()
        painter.setClipRect(option.rect)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        box = QRectF(indicator).adjusted(.5, .5, -.5, -.5)
        painter.setPen(QPen(border, 1.6 if emphasized else 1.0))
        painter.setBrush(QBrush(fill) if checked else Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(box, 1.5, 1.5)
        if checked:
            path = QPainterPath()
            path.moveTo(box.left() + box.width() * .22, box.top() + box.height() * .50)
            path.lineTo(box.left() + box.width() * .43, box.top() + box.height() * .72)
            path.lineTo(box.left() + box.width() * .80, box.top() + box.height() * .27)
            painter.setPen(QPen(tick, 1.8, Qt.PenStyle.SolidLine,
                                Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.drawPath(path)
        painter.restore()


class RecommendationsView(QWidget):
    def __init__(self, state, provider, pool, parent=None):
        super().__init__(parent)
        self.state, self.provider, self.pool = state, provider, pool
        self.worker = None
        self.current_run = None
        self.last_run = None
        self.rows = ()
        self.remembered_identity = None
        self.remembered_flight = None
        self._remembered_fid = None
        self.origin = None
        self._expired_market_key = None
        self.free = None
        self._context = None
        self._refreshing = False
        self._invalidated = False
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)
        content = QWidget()
        scroll.setWidget(content)
        body = QVBoxLayout(content)
        self.explanation = QLabel()
        self.origin_label = QLabel()
        self.ship_label = QLabel()
        for label in (self.explanation, self.origin_label, self.ship_label):
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setWordWrap(True)
        body.addWidget(self.explanation)
        market_line = QHBoxLayout()
        market_line.addWidget(self.origin_label, 3)
        self.market_read_status = MarketReadStatus()
        market_line.addWidget(self.market_read_status, 1, Qt.AlignmentFlag.AlignTop)
        body.addLayout(market_line)
        body.addWidget(self.ship_label)
        self.filters = QWidget()
        form = QFormLayout(self.filters)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.margin = QSpinBox()
        self.margin.setRange(0, 1000)
        self.margin.setValue(10)
        self.margin.setSuffix(' %')
        form.addRow(tr('recommend.margin'), self.margin)
        self.radius = QComboBox()
        for value in (25, 50, 100, 250, 500):
            self.radius.addItem(str(value), value)
        self.radius.setCurrentIndex(2)
        form.addRow(tr('trade.radius'), self.radius)
        self.max_age = QComboBox()
        for hours in (1, 6, 12, 24, 72, 168):
            self.max_age.addItem(tr('trade.age_option_' + str(hours)), hours)
        self.max_age.setCurrentIndex(3)
        form.addRow(tr('recommend.target_age'), self.max_age)
        self.pad = QComboBox()
        for pad in PadSize:
            self.pad.addItem(tr('trade.pad_' + pad.value), pad)
        form.addRow(tr('trade.pad'), self.pad)
        self.local_only = QCheckBox(tr('recommend.local_only'))
        self.local_only.setToolTip(tr('recommend.local_only_tooltip'))
        form.addRow(self.local_only)
        self.carriers = QCheckBox(tr('trade.carriers'))
        form.addRow(self.carriers)
        self.arrival = QLineEdit()
        self.arrival.setPlaceholderText(tr('trade.unlimited'))
        form.addRow(tr('trade.arrival'), self.arrival)
        body.addWidget(self.filters)
        buttons = QHBoxLayout()
        self.search_button = QPushButton(tr('recommend.search'), objectName='recommendationSearch')
        self.search_button.setToolTip(tr('recommend.help'))
        self.cancel_button = QPushButton(tr('trade.cancel'))
        self.cancel_button.hide()
        buttons.addWidget(self.search_button)
        buttons.addWidget(self.cancel_button)
        buttons.addStretch()
        body.addLayout(buttons)
        self.progress_bar = QProgressBar(objectName='recommendationProgress')
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        body.addWidget(self.progress_bar)
        self.status = QLabel()
        self.status.setWordWrap(True)
        body.addWidget(self.status)
        diagnostic_actions = QHBoxLayout()
        self.copy_notice = QLabel()
        self.copy_notice.setWordWrap(True)
        diagnostic_actions.addWidget(self.copy_notice, 1)
        self.copy_system_button = QPushButton(tr('recommend.copy_system'))
        self.copy_system_button.setEnabled(False)
        self.copy_system_button.clicked.connect(self.copy_system)
        self.copy_diagnostic_button = QPushButton(tr('recommend.copy_diagnostic'))
        self.copy_diagnostic_button.setEnabled(False)
        self.copy_diagnostic_button.clicked.connect(self.copy_diagnostic)
        diagnostic_actions.addWidget(self.copy_diagnostic_button)
        body.addLayout(diagnostic_actions)
        self.copy_notice_timer = QTimer(self)
        self.copy_notice_timer.setSingleShot(True)
        self.copy_notice_timer.setInterval(3000)
        self.copy_notice_timer.timeout.connect(self.copy_notice.clear)
        self.notice = QLabel(tr('recommend.notice'), objectName='marketDataNotice')
        self.notice.setWordWrap(True)
        self.notice.setMargin(8)
        self.notice.setStyleSheet('QLabel#marketDataNotice { border-left: 2px solid #ad7927; }')
        body.addWidget(self.notice)
        self.remembered_panel = QFrame(objectName='rememberedFlight')
        self.remembered_panel.setStyleSheet(
            'QFrame#rememberedFlight { border: 1px solid palette(mid); border-radius: 4px; }')
        self.remembered_panel.setToolTip(tr('recommend.remembered_snapshot'))
        remembered_layout = QHBoxLayout(self.remembered_panel)
        remembered_layout.setContentsMargins(8, 6, 8, 6)
        remembered_text = QVBoxLayout()
        remembered_text.setSpacing(2)
        self.remembered_label = QLabel(tr('recommend.remembered_flight'))
        font = self.remembered_label.font()
        font.setBold(True)
        self.remembered_label.setFont(font)
        self.remembered_details = QLabel()
        self.remembered_profit = QLabel()
        for label in (self.remembered_label, self.remembered_details, self.remembered_profit):
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setWordWrap(True)
            remembered_text.addWidget(label)
        remembered_layout.addLayout(remembered_text, 1)
        remembered_actions = QVBoxLayout()
        remembered_actions.addWidget(self.copy_system_button)
        self.remove_remembered_button = QPushButton(tr('recommend.remove_remembered'))
        self.remove_remembered_button.clicked.connect(self.remove_remembered)
        remembered_actions.addWidget(self.remove_remembered_button)
        remembered_actions.addStretch()
        remembered_layout.addLayout(remembered_actions)
        self.remembered_panel.hide()
        body.addWidget(self.remembered_panel)
        self.table = QTableWidget(0, 15)
        self.table.setHorizontalHeaderLabels([''] + [tr(k) for k in (
            'trade.commodity', 'recommend.total_profit', 'recommend.profit_percent',
            'trade.quantity', 'recommend.buy_here', 'recommend.sell_there', 'recommend.profit_ton',
            'trade.station', 'trade.system', 'trade.distance', 'trade.arrival_column',
            'trade.pad', 'recommend.source', 'recommend.target_age')])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setItemDelegate(RememberedRecommendationDelegate(self.table))
        self.table.horizontalHeaderItem(0).setToolTip(tr('recommend.remember'))
        self.table.itemChanged.connect(self.remember_changed)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setMinimumSectionSize(30)
        self.table.setMinimumHeight(240)
        self.table.setSortingEnabled(True)
        body.addWidget(self.table, 1)
        self.margin.valueChanged.connect(self.filters_changed)
        for field in (self.radius, self.max_age, self.pad):
            field.currentIndexChanged.connect(self.filters_changed)
        self.local_only.toggled.connect(self.filters_changed)
        self.carriers.toggled.connect(self.filters_changed)
        self.arrival.textChanged.connect(self.filters_changed)
        self.search_button.clicked.connect(self.start_search)
        self.cancel_button.clicked.connect(self.cancel_search)
        for name in ('changed', 'commanderIdentityChanged', 'cargoSnapshotChanged', 'shipLoadoutChanged'):
            signal = getattr(state, name, None)
            if signal is not None:
                signal.connect(self.refresh)
        signal = getattr(state, 'observedMarketsChanged', None)
        if signal is not None:
            signal.connect(self.markets_changed)
        QApplication.instance().aboutToQuit.connect(self.cancel_search)
        self.refresh()

    @Slot()
    def filters_changed(self):
        self.invalidate()
        self.refresh()

    @Slot()
    def markets_changed(self):
        self.invalidate()
        self.refresh()

    def invalidate(self, reason=PartialReason.CONTEXT_CHANGED):
        self._invalidated = True
        self.progress_bar.hide()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        if self.worker is not None:
            self.worker.cancel.request(reason)
        self.rows = ()
        self.render(())
        self.status.setText(tr('recommend.ready'))

    @Slot()
    def refresh(self):
        if self._refreshing:
            return
        self._refreshing = True
        try:
            fid = getattr(self.state, 'commander_fid', '')
            if self.remembered_flight is not None and fid and fid != self._remembered_fid:
                self.clear_remembered()
                self.render(self.rows)
            previous_origin = self.origin
            self.origin = current_market(self.state)
            context = current_market_context(self.state)
            key = tuple(context.get(k) for k in ('FID', 'MarketID', 'StationName', 'StarSystem')) if context else None
            previous_key = (previous_origin['fid'], previous_origin['market_id'],
                            previous_origin['station_name'], previous_origin['system_name']) if previous_origin else None
            if self.origin is not None or key != self._expired_market_key:
                self._expired_market_key = None
            if self.origin is None and context is not None and previous_key == key:
                cache = self.state.observed_markets.cache
                if not cache.is_valid(previous_origin, cache.clock()):
                    self._expired_market_key = key
            self.market_read_status.setVisible(context is not None)
            if context is not None:
                status = 'read' if self.origin is not None else (
                    'expired' if key == self._expired_market_key else 'open')
                self.market_read_status.set_status(status)
            self.notice.setText(tr('recommend.local_notice' if self.local_only.isChecked() else 'recommend.notice'))
            name, self.free = ship_space(self.state)
            signature = (getattr(self.state, 'commander_fid', ''), getattr(self.state, 'system', ''),
                         getattr(self.state, 'station', ''), self.origin, name, self.free,
                         getattr(getattr(self.state, 'ship_loadout', None), 'ship_id', None))
            if signature != self._context:
                self.invalidate()
                self._context = deepcopy(signature)
            self.explanation.setText(tr('recommend.question', margin=self.margin.value()))
            if self.origin:
                from .trade_view import format_age
                age = format_age(timestamp(self.origin['observed_at']), self.state.observed_markets.cache.clock())
                self.origin_label.setText(tr('recommend.origin', station=self.origin['station_name'],
                    system=self.origin['system_name'], age=age, source=tr('recommend.local')))
            else:
                text = tr('recommend.no_market')
                if context is not None:
                    text = tr('recommend.current_market', station=context['StationName']) + '\n' + text
                self.origin_label.setText(text)
            cargo = tr('recommend.cargo_unknown') if self.free is None else (
                tr('recommend.cargo_full') if self.free == 0 else tr('recommend.cargo', count=self.free))
            self.ship_label.setText(tr('recommend.ship', name=name) + '\n' + cargo)
            self.search_button.setEnabled(self.worker is None and self.origin is not None
                                          and self.free is not None and self.free > 0)
        finally:
            self._refreshing = False

    @Slot()
    def start_search(self):
        if self.worker is not None:
            return
        self.refresh()
        if self.origin is None or self.free is None or self.free <= 0:
            return
        arrival = self.arrival.text().strip()
        if arrival and (not arrival.isascii() or not arrival.isdecimal() or len(arrival) > 10
                        or not 1 <= int(arrival) <= 2147483647):
            self.status.setText(tr('trade.invalid_arrival'))
            return
        local_only = self.local_only.isChecked()
        cache = self.state.observed_markets.cache
        local = cache.all(self.origin['fid'])
        query = MarketSearch('', self.origin['system_name'], radius_ly=self.radius.currentData(),
            max_age=timedelta(hours=self.max_age.currentData()), required_pad=PadSize(self.pad.currentData()),
            include_fleet_carriers=self.carriers.isChecked(),
            max_distance_to_arrival_ls=int(arrival) if arrival else None, limit=100)
        distances = local_distances(self.state, self.origin, local)
        self.clear_remembered()
        self.invalidate()
        self._invalidated = False
        self.worker = RecommendationWorker(deepcopy(self.origin), local, distances, self.free,
            self.margin.value(), query, self.provider, cache.clock, local_only=local_only)
        self.current_run = self.worker.diagnostics.snapshot()
        self.worker.signals.diagnostic.connect(self.diagnostic_progress)
        self.worker.signals.progress.connect(self.progress)
        self.worker.signals.finished.connect(self.finished)
        self._cancel_event = self.worker.cancel
        self.destroyed.connect(self._cancel_event.set)
        self.filters.setEnabled(False)
        self.search_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.cancel_button.show()
        self.progress_bar.setRange(0, 0)  # The worker has not published its plan yet.
        self.progress_bar.show()
        self.status.setText(tr('recommend.progress', checked=self.current_run.checked_commodities, total='…'))
        self.progress_bar.setAccessibleName(self.status.text())
        self.pool.start(self.worker)

    @Slot()
    def cancel_search(self):
        self._cancel_search(PartialReason.CANCELLED)

    def cancel_for_context(self):
        self._cancel_search(PartialReason.CONTEXT_CHANGED)

    def _cancel_search(self, reason):
        self.invalidate(reason)
        if self.worker is not None:
            self.cancel_button.setEnabled(False)
            self.status.setText(tr('trade.cancelling'))

    def current_worker_signal(self):
        sender = self.sender()
        return self.worker is not None and (sender is None or sender is self.worker.signals)

    def update_progress_bar(self, diagnostic):
        if diagnostic is None:
            return
        checked, planned = diagnostic.checked_commodities, diagnostic.planned_commodities
        # Qt treats 0..0 as busy; an empty known plan must not keep animating.
        self.progress_bar.setRange(0, max(1, planned))
        self.progress_bar.setValue(checked)
        text = tr('recommend.progress', checked=checked, total=planned)
        self.progress_bar.setAccessibleName(text)
        self.status.setText(text)

    @Slot(object)
    def diagnostic_progress(self, diagnostic):
        if not self.current_worker_signal():
            return
        self.refresh()
        if self._invalidated or self.worker.cancel.is_set():
            return
        self.current_run = diagnostic
        self.update_diagnostic_tooltip(diagnostic)
        self.update_progress_bar(diagnostic)

    def update_diagnostic_tooltip(self, diagnostic):
        if diagnostic is not None:
            self.status.setToolTip(tr('recommend.diagnostic_details',
                local=diagnostic.local_commodities_completed,
                total=diagnostic.planned_commodities,
                started=diagnostic.spansh_commodities_started,
                completed=diagnostic.spansh_commodities_completed,
                requests=diagnostic.http_requests, hits=diagnostic.cache_hits,
                commodity=(diagnostic.first_failed_commodity.symbol
                           if diagnostic.first_failed_commodity is not None else '–')))

    @Slot(object)
    def progress(self, result):
        if not self.current_worker_signal():
            return
        self.diagnostic_progress(result.diagnostics)
        self.refresh()  # Recheck TTL and current identity before accepting queued output.
        if self.worker is None or self._invalidated or self.worker.cancel.is_set():
            return
        self.render(result.rows)

    @Slot(object)
    def finished(self, result):
        if not self.current_worker_signal():
            return
        self.refresh()
        accepted = self.worker is not None and not self._invalidated and not self.worker.cancel.is_set()
        if accepted and not result.cancelled:
            self.update_progress_bar(result.diagnostics)
        elif result.cancelled:
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(0)
        self.progress_bar.hide()
        self.last_run = result.diagnostics
        if self.last_run is not None and self.worker is not None and self.worker.cancel.is_set():
            self.last_run.cancelled = True
            self.last_run.reason(self.worker.cancel.reason)
        self.current_run = None
        self.copy_diagnostic_button.setEnabled(self.last_run is not None
                                              and self.last_run.finished_at is not None)
        self.update_diagnostic_tooltip(self.last_run)
        if self.worker is not None:
            self.destroyed.disconnect(self._cancel_event.set)
        self.worker = None
        self.filters.setEnabled(True)
        self.cancel_button.hide()
        self.refresh()
        if accepted and not result.cancelled:
            self.render(result.rows)
            message = tr('recommend.results', count=len(result.rows))
            if result.partial:
                reason = self.last_run.partial_reason if self.last_run else PartialReason.OTHER
                message += '\n' + tr('recommend.partial_counts', checked=result.checked, total=result.total,
                                     reason=diagnostic_reason_text(reason))
            else:
                message += '\n' + tr('recommend.complete', checked=result.checked, total=result.total)
            self.status.setText(message)
        else:
            self.status.setText(tr('recommend.ready'))

    @Slot()
    def copy_diagnostic(self):
        if self.last_run is None or self.last_run.finished_at is None:
            return
        QApplication.clipboard().setText(format_recommendation_diagnostic(self.last_run))
        self.copy_notice.setText(tr('recommend.diagnostic_copied'))
        self.copy_notice_timer.start()

    def render(self, rows):
        from .trade_view import NumericItem, TextItem, PadItem, format_age
        self.rows = rows
        blocker = QSignalBlocker(self.table)
        locale = QLocale(get_language())
        now = self.state.observed_markets.cache.clock() if rows else None
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for index, row in enumerate(rows):
            o = row.destination
            master = lookup_by_id(o.commodity_id) or lookup_by_symbol(o.commodity_symbol)
            name = commodity_name(master) if master else o.commodity_name
            def number(value, unit=''):
                return NumericItem('–' if value is None else locale.toString(value) + unit, value)
            profit = number(row.total_profit, ' Cr')
            font = profit.font()
            font.setBold(True)
            profit.setFont(font)
            mark = QTableWidgetItem()
            mark.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsUserCheckable)
            mark.setData(Qt.ItemDataRole.UserRole, row)
            mark.setToolTip(tr('recommend.remember'))
            mark.setCheckState(Qt.CheckState.Unchecked)
            cells = [mark, TextItem(name), profit,
                NumericItem(locale.toString(float(row.profit_percent), 'f', 2) + ' %', row.profit_percent),
                number(row.quantity, ' t'), number(row.buy_price, ' Cr'),
                number(o.commander_sell_price, ' Cr'), number(row.profit_per_ton, ' Cr'),
                TextItem(o.station_name), TextItem(o.system_name),
                number(o.distance_ly, ' ly'), number(o.distance_to_arrival_ls),
                PadItem(tr('trade.pad_' + o.largest_pad.value) if o.largest_pad else '–', o.largest_pad),
                TextItem(tr('recommend.local') if o.provider == 'local_elite' else 'Spansh'),
                NumericItem(format_age(o.market_updated_at, now), (now-o.market_updated_at).total_seconds())]
            cells[1].setData(Qt.ItemDataRole.UserRole, row)
            cells[14].setToolTip(o.market_updated_at.isoformat())
            for column, cell in enumerate(cells):
                self.table.setItem(index, column, cell)
        self.table.setSortingEnabled(True)
        self.table.sortItems(2, Qt.SortOrder.DescendingOrder)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, max(30, self.table.style().pixelMetric(QStyle.PixelMetric.PM_IndicatorWidth) + 16))
        for column in (1, 8, 9):
            self.table.setColumnWidth(column, min(240 if column == 1 else 300,
                                                 self.table.columnWidth(column)))
            for index in range(self.table.rowCount()):
                self.table.item(index, column).setToolTip(self.table.item(index, column).text())
        self.update_remembered()

    def remember_changed(self, item):
        if item.column() != 0:
            return
        row = item.data(Qt.ItemDataRole.UserRole)
        if item.checkState() == Qt.CheckState.Checked:
            target = row.destination
            master = lookup_by_id(target.commodity_id) or lookup_by_symbol(target.commodity_symbol)
            self.remembered_flight = RememberedFlight(
                target.commodity_id, target.commodity_symbol,
                commodity_name(master) if master else target.commodity_name,
                target.market_id, target.system_name, target.station_name, row.total_profit)
            self._remembered_fid = getattr(self.state, 'commander_fid', '')
            self.remembered_identity = recommendation_identity(row)
        else:
            self.clear_remembered()
        self.update_remembered()

    @Slot()
    def remove_remembered(self):
        self.clear_remembered()
        self.update_remembered()

    def clear_remembered(self):
        self.remembered_flight = None
        self.remembered_identity = None
        self._remembered_fid = None

    def update_remembered(self):
        blocker = QSignalBlocker(self.table)
        for index in range(self.table.rowCount()):
            item = self.table.item(index, 0)
            remembered = recommendation_identity(item.data(Qt.ItemDataRole.UserRole)) == self.remembered_identity
            item.setCheckState(Qt.CheckState.Checked if remembered else Qt.CheckState.Unchecked)
            for column in range(self.table.columnCount()):
                self.table.item(index, column).setData(Qt.ItemDataRole.UserRole + 1, remembered)
        flight = self.remembered_flight
        self.remembered_details.setText(
            ' · '.join((flight.commodity_name, flight.station_name, flight.system_name)) if flight else '')
        self.remembered_profit.setText(
            tr('recommend.total_profit') + ': ' + QLocale(get_language()).toString(flight.total_profit) + ' Cr'
            if flight else '')
        self.copy_system_button.setEnabled(self.remembered_flight is not None
                                          and bool(self.remembered_flight.system_name))
        self.remembered_panel.setVisible(flight is not None)

    @Slot()
    def copy_system(self):
        row = self.remembered_flight
        if row is None or not row.system_name:
            return
        QApplication.clipboard().setText(row.system_name)
        self.copy_notice.setText(tr('recommend.system_copied'))
        self.copy_notice_timer.start()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()

    def closeEvent(self, event):
        self.cancel_search()
        super().closeEvent(event)
