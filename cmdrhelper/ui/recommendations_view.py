"""Manual recommendations page; immutable inputs cross the worker boundary."""
from copy import deepcopy
import logging
from html import escape
from datetime import timedelta

from PySide6.QtCore import QObject, QRunnable, QLocale, Qt, Signal, Slot, QTimer, QSignalBlocker
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QSpinBox, QComboBox, QCheckBox, QLineEdit, QPushButton, QScrollArea, QTableWidget,
    QHeaderView, QApplication, QProgressBar, QStyle, QSizePolicy)

from cmdrhelper.trade_station_body import known_station_body
from cmdrhelper.cargo import free_cargo_space
from cmdrhelper.commodity_master import lookup_by_id, lookup_by_symbol
from cmdrhelper.commodity_localization import commodity_name
from cmdrhelper.i18n import tr, get_language
from cmdrhelper.market_data import MarketSearch, MarketTarget, PadSize
from cmdrhelper.observed_market_cache import timestamp
from .market_read_status import MarketReadStatus
from .recent_system_copy import RecentSystemCopyDelegate
from .remembered_targets import RememberedTargets, RememberedTargetDelegate as RememberedRecommendationDelegate
from .system_clipboard import copy_system_name
from cmdrhelper.trade_recommendations import search_recommendations, search_supply_recommendations, RecommendationResult
from cmdrhelper.trade_market_source import prepare_trade_source
from cmdrhelper.recommendation_market_source import RecommendationStoreSession
from cmdrhelper.recommendation_diagnostic_text import format_recommendation_diagnostic
from cmdrhelper.recommendation_diagnostics import (
    RecommendationDiagnostics, RecommendationCancellation, PartialReason)

from .market_age import MarketAgeCombo
from .observed_market_status import observed_market_text


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


def current_market(state, max_age=timedelta(hours=24)):
    context = current_market_context(state)
    if context is None:
        return None
    fid = getattr(state, 'commander_fid', '')
    row = state.observed_markets.cache.get_header(context['MarketID'], max_age=max_age)
    if (row is None or row['source'] != 'local_elite'
            or row['station_name'] != context['StationName'] or row['system_name'] != context['StarSystem']):
        return None
    return row


def ship_space(state):
    """Validated ship total; inventory and SRV quantities stay separate."""
    from cmdrhelper.ship_cargo import current_ship_cargo
    loadout = getattr(state, 'ship_loadout', None)
    name = (getattr(loadout, 'ship_name', '') or getattr(state, 'ship', '')
            or getattr(loadout, 'ship_type', '') or '–')
    total = current_ship_cargo(state)
    return name, (free_cargo_space(total['count'], loadout.cargo_capacity)
                  if total is not None else None)


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
    def __init__(self, origin, local, distances, free, margin, query, provider, clock, *, local_only=False, market_source=None, supply=False, quantity=None):
        super().__init__()
        self.args = (origin, local, distances, free, margin, query, provider)
        self.clock = clock
        self.local_only = local_only
        self.supply, self.quantity = supply, quantity
        self.market_source = market_source
        self.cancel = RecommendationCancellation()
        self.diagnostics = RecommendationDiagnostics(local_only=local_only)
        self.signals = RecommendationSignals()

    def _validate_sources(self, result):
        if self.local_only and any(row.remote.provider != 'local_elite' for row in result.rows):
            raise ValueError('Non-local destination in local-only recommendations')

    def _publish_progress(self, result):
        self._validate_sources(result)
        self.signals.progress.emit(result)

    @Slot()
    def run(self):
        search = search_supply_recommendations if self.supply else search_recommendations
        options = dict(quantity=self.quantity) if self.supply else {}
        try:
            fallback = (self.market_source.fallback_cache(self.cancel)
                        if self.market_source is not None else None)
            if self.market_source is None or fallback is not None:
                args = self.args
                if fallback is not None:
                    rows, distances = self.market_source.legacy_rows(fallback, self.args[5].max_age)
                    origin = next((row for row in rows if row['market_id'] == self.args[0]['market_id']), None)
                    if self.supply and (origin is None or any(origin.get(k) != self.args[0].get(k)
                            for k in ('fid', 'market_id', 'station_name', 'system_name', 'observed_at'))):
                        origin = None
                    args = (origin, rows, distances, *self.args[3:])
                result = search(*args, **options, cancel=self.cancel, clock=self.clock,
                    progress=self._publish_progress, diagnostics=self.diagnostics,
                    diagnostic_progress=self.signals.diagnostic.emit, local_only=self.local_only)
            else:
                with RecommendationStoreSession(self.market_source, self.args[0], self.args[5],
                                                clock=self.clock, cancel=self.cancel, supply=self.supply) as session:
                    if session.origin is None:
                        result = RecommendationResult(partial=True, diagnostics=self.diagnostics.finish(
                            partial=True, reason=PartialReason.CONTEXT_CHANGED))
                    else:
                        args = (session.origin, (), {}, *self.args[3:])
                        result = search(*args, **options, cancel=self.cancel, clock=self.clock,
                            progress=self._publish_progress, diagnostics=self.diagnostics,
                            diagnostic_progress=self.signals.diagnostic.emit, local_only=self.local_only,
                            local_evaluator=session, progress_interval=.1)
            self._validate_sources(result)
        except Exception:
            logging.getLogger(__name__).exception('Local recommendation read failed')
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


def recommendation_identity(row):
    target = row.destination
    return (target.commodity_id, target.commodity_symbol, target.market_id,
            target.system_name, target.station_name)


class RecommendationsView(QWidget):
    supply = False

    def text(self, key, **kwargs):
        # Only direction-dependent labels differ; all filters/status machinery is shared.
        overrides = {'question', 'origin', 'search', 'help', 'notice', 'buy_here',
                     'sell_there', 'target_age', 'ready', 'results'}
        if self.supply and key.startswith('recommend.') and key.split('.', 1)[1] in overrides:
            key = key.replace('recommend.', 'supply.', 1)
        return tr(key, **kwargs)

    def cargo_context(self, free):
        # Outward recommendations intentionally survive partial purchases.
        return free if self.supply else (None if free is None else free > 0)

    def __init__(self, state, provider, pool, parent=None, *, market_read_status=None):
        super().__init__(parent)
        self.state, self.provider, self.pool = state, provider, pool
        self.worker = None
        self.fixed_target_offer = None
        self.fixed_target_key = None
        self.fixed_target_fid = None
        self._pending_fixed_search = False
        self.current_run = None
        self.last_run = None
        self.rows = ()
        self._remembered_fid = None
        self.origin = None
        self._expired_market_key = None
        self.free = None
        self._context = None
        self._refreshing = False
        self._invalidated = False
        self._pending_rows = None
        self._progress_render_timer = QTimer(self)
        self._progress_render_timer.setSingleShot(True)
        self._progress_render_timer.setInterval(100)
        self._progress_render_timer.timeout.connect(self._render_progress)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll)
        content = QWidget()
        scroll.setWidget(content)
        body = QVBoxLayout(content)
        self.fixed_target_box = QWidget()
        target_layout = QVBoxLayout(self.fixed_target_box)
        target_layout.setContentsMargins(0, 0, 0, 0)
        self.fixed_target_label = QLabel()
        self.fixed_target_label.setTextFormat(Qt.PlainText)
        self.fixed_target_label.setWordWrap(True)
        self.fixed_target_enabled = QCheckBox(tr('outbound.only_target'))
        self.fixed_target_enabled.toggled.connect(self.fixed_target_toggled)
        self.fixed_target_hint = QLabel(tr('outbound.filters'))
        self.fixed_target_hint.setWordWrap(True)
        for widget in (self.fixed_target_label, self.fixed_target_enabled, self.fixed_target_hint):
            target_layout.addWidget(widget)
        body.addWidget(self.fixed_target_box)
        self.fixed_target_box.hide()
        self.explanation = QLabel()
        self.origin_label = QLabel()
        self.ship_label = QLabel()
        self.observed_status = QLabel(objectName='muted')
        for label in (self.explanation, self.origin_label, self.ship_label, self.observed_status):
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setWordWrap(True)
        body.addWidget(self.explanation)
        market_line = QHBoxLayout()
        market_line.addWidget(self.origin_label, 3)
        self._shared_market_status = market_read_status is not None
        self.market_read_status = market_read_status if self._shared_market_status else MarketReadStatus()
        if not self._shared_market_status:
            market_line.addWidget(self.market_read_status, 1, Qt.AlignmentFlag.AlignTop)
        body.addLayout(market_line)
        body.addWidget(self.ship_label)
        body.addWidget(self.observed_status)
        self.remember_tip = QLabel('<small>' + escape(self.text('recommend.remember_tip')) + '</small>',
                                  objectName='supplyRememberTip' if self.supply else 'recommendationRememberTip')
        self.remember_tip.setTextFormat(Qt.TextFormat.RichText)
        self.remember_tip.setWordWrap(True)
        self.remember_tip.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.remember_tip.setAccessibleName(self.text('recommend.remember_tip'))
        body.addWidget(self.remember_tip)
        self.filters = QWidget()
        form = QFormLayout(self.filters)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        if self.supply:
            self._quantity_automatic = True
            self.quantity = QSpinBox()
            self.quantity.setRange(1, 2147483647)
            self.quantity.setValue(max(1, ship_space(state)[1] or 1))
            self.quantity.setToolTip(tr('supply.quantity_help'))
            form.addRow(tr('trade.quantity'), self.quantity)
            self.quantity.valueChanged.connect(self.quantity_changed)
        self.margin = QSpinBox()
        self.margin.setRange(0, 1000)
        self.margin.setValue(10)
        self.margin.setSuffix(' %')
        form.addRow(self.text('recommend.margin'), self.margin)
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
        self.local_only = QCheckBox(self.text('recommend.local_only'))
        self.local_only.setToolTip(self.text('recommend.local_only_tooltip'))
        form.addRow(self.local_only)
        self.carriers = QCheckBox(tr('trade.carriers'))
        form.addRow(self.carriers)
        self.arrival = QLineEdit()
        self.arrival.setPlaceholderText(tr('trade.unlimited'))
        form.addRow(tr('trade.arrival'), self.arrival)
        body.addWidget(self.filters)
        buttons = QHBoxLayout()
        self.search_button = QPushButton(self.text('recommend.search'), objectName='recommendationSearch')
        self.search_button.setToolTip(self.text('recommend.help'))
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
        self.copy_diagnostic_button = QPushButton(self.text('recommend.copy_diagnostic'))
        self.copy_diagnostic_button.setEnabled(False)
        self.copy_diagnostic_button.clicked.connect(self.copy_diagnostic)
        diagnostic_actions.addWidget(self.copy_diagnostic_button)
        body.addLayout(diagnostic_actions)
        self.copy_notice_timer = QTimer(self)
        self.copy_notice_timer.setSingleShot(True)
        self.copy_notice_timer.setInterval(3000)
        self.copy_notice_timer.timeout.connect(self.copy_notice.clear)
        self.notice = QLabel(self.text('recommend.notice'), objectName='marketDataNotice')
        self.notice.setWordWrap(True)
        self.notice.setMargin(8)
        self.notice.setStyleSheet('QLabel#marketDataNotice { border-left: 2px solid #ad7927; }')
        body.addWidget(self.notice)
        self.remembered_panel = RememberedTargets(state=state, route_bookmarks=self.supply)
        self.remembered_flights = self.remembered_panel.targets
        body.addWidget(self.remembered_panel)
        self.table = QTableWidget(0, 18 if self.supply else 15)
        self.remembered_panel.bind_table(self.table, 0)
        self.table.setHorizontalHeaderLabels([''] + [self.text(k) for k in (
            'trade.commodity', 'recommend.total_profit', 'recommend.profit_percent',
            'trade.quantity', 'recommend.buy_here', 'recommend.sell_there', 'recommend.profit_ton',
            'trade.station', 'trade.system', 'trade.distance', 'trade.arrival_column',
            'trade.pad', 'recommend.source', 'recommend.target_age')] +
            ([tr('supply.supply'), tr('supply.demand'), tr('explorer.col_body')] if self.supply else []))
        if self.supply:
            self.table.horizontalHeaderItem(8).setText(tr('supply.station'))
            self.table.horizontalHeaderItem(9).setText(tr('supply.system'))
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setItemDelegate(RememberedRecommendationDelegate(self.table))
        self.system_copy_delegate = RecentSystemCopyDelegate(
            self.table, column=9, name_role=Qt.DisplayRole,
            style_delegate=self.table.itemDelegate())
        self.table.setItemDelegateForColumn(9, self.system_copy_delegate)
        self.system_copy_delegate.copyRequested.connect(
            lambda row, _column: copy_system_name(
                self.table.item(row, 0).data(Qt.UserRole).remote.system_name))
        self.table.horizontalHeaderItem(0).setToolTip(tr('trade.remembered_targets'))
        self.table.itemChanged.connect(self.remember_changed)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setMinimumSectionSize(30)
        # Move only visual sections: sorting, row data and delegates keep their
        # logical columns. Location is followed directly by the three prices.
        header = self.table.horizontalHeader()
        for visual, logical in enumerate((0, 1, 2, 3, 4, 9, 8, 12, 5, 6, 7, 10, 11, 13, 14)):
            header.moveSection(header.visualIndex(logical), visual)
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

    def active_target(self):
        offer = self.fixed_target_offer
        return (MarketTarget(offer.market_id, offer.system_id64)
                if offer is not None and self.fixed_target_enabled.isChecked() else None)

    def set_fixed_target(self, row, key, body):
        if self.supply:
            return
        offer = row.source
        MarketTarget(offer.market_id, offer.system_id64)  # Validate before accepting the action.
        self.invalidate()
        self.fixed_target_offer, self.fixed_target_key = offer, key
        self.fixed_target_fid = getattr(self.state, 'commander_fid', '')
        parts = [tr('outbound.target', station=offer.station_name, system=offer.system_name)]
        if body:
            parts.append(tr('explorer.col_body') + ': ' + body)
        if offer.largest_pad in (PadSize.SMALL, PadSize.MEDIUM, PadSize.LARGE):
            parts.append(tr('trade.pad') + ': ' + tr('trade.pad_' + offer.largest_pad.value))
        master = lookup_by_id(offer.commodity_id) or lookup_by_symbol(offer.commodity_symbol)
        name = commodity_name(master) if master else offer.commodity_name
        parts.append(tr('outbound.return_route', commodity=name,
                        station=row.target.station_name, system=row.target.system_name))
        self.fixed_target_label.setText('\n'.join(parts))
        with QSignalBlocker(self.fixed_target_enabled):
            self.fixed_target_enabled.setChecked(True)
        self.fixed_target_box.show()
        self.refresh()
        self._pending_fixed_search = True
        self._start_fixed_search()

    def _start_fixed_search(self):
        if self._pending_fixed_search and self.worker is None:
            self._pending_fixed_search = False
            if self.active_target() is not None:
                self.start_search()

    def clear_fixed_target(self):
        self._pending_fixed_search = False
        self.fixed_target_offer = self.fixed_target_key = self.fixed_target_fid = None
        with QSignalBlocker(self.fixed_target_enabled):
            self.fixed_target_enabled.setChecked(False)
        self.fixed_target_box.hide()
        self.invalidate()
        self.refresh()

    def fixed_target_toggled(self):
        self._pending_fixed_search = False
        self.filters_changed()

    @Slot()
    def quantity_changed(self):
        self._quantity_automatic = False
        self.filters_changed()

    @Slot()
    def filters_changed(self):
        self.invalidate()
        self.refresh()

    @Slot()
    def markets_changed(self):
        self.invalidate()
        self.refresh()

    def invalidate(self, reason=PartialReason.CONTEXT_CHANGED):
        self._pending_fixed_search = False
        self._invalidated = True
        self._progress_render_timer.stop()
        self._pending_rows = None
        self.progress_bar.hide()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        if self.worker is not None:
            self.worker.cancel.request(reason)
        self.rows = ()
        self.render(())
        self.status.setText(self.text('recommend.ready'))

    @Slot()
    def refresh(self):
        if self._refreshing:
            return
        self._refreshing = True
        try:
            self.observed_status.setText(observed_market_text(self.state))
            self.observed_status.setToolTip(tr('trade.observed_tooltip'))
            fid = getattr(self.state, 'commander_fid', '')
            if self.fixed_target_offer is not None and fid and fid != self.fixed_target_fid:
                self.clear_fixed_target()
            if self.remembered_flights and fid and fid != self._remembered_fid:
                self.clear_remembered()
                self.render(self.rows)
            previous_origin = self.origin
            self.origin = current_market(self.state, self.max_age.max_age())
            context = current_market_context(self.state)
            key = tuple(context.get(k) for k in ('FID', 'MarketID', 'StationName', 'StarSystem')) if context else None
            previous_key = (getattr(self.state, 'commander_fid', ''), previous_origin['market_id'],
                            previous_origin['station_name'], previous_origin['system_name']) if previous_origin else None
            if self.origin is not None or key != self._expired_market_key:
                self._expired_market_key = None
            if self.origin is None and context is not None and previous_key == key:
                cache = self.state.observed_markets.cache
                if not cache.is_valid(previous_origin, cache.clock(), self.max_age.max_age()):
                    self._expired_market_key = key
            self.market_read_status.setVisible(self._shared_market_status or context is not None)
            status = 'read' if self.origin is not None else (
                'expired' if context is not None and key == self._expired_market_key else 'open')
            self.market_read_status.set_status(status, station=(
                context['StationName'] if context else '') if self._shared_market_status else None)
            self.notice.setText(self.text('recommend.local_notice' if self.local_only.isChecked() else 'recommend.notice'))
            previous_free = self.free
            name, self.free = ship_space(self.state)
            if self.supply and self._quantity_automatic:
                with QSignalBlocker(self.quantity):
                    self.quantity.setValue(max(1, self.free or 1))
            # Partial purchases do not change the recommendation context while
            # confirmed cargo space remains. Full/unknown cargo still invalidates.
            cargo_available = self.cargo_context(self.free)
            signature = (getattr(self.state, 'commander_fid', ''), getattr(self.state, 'system', ''),
                         getattr(self.state, 'station', ''), self.origin, name, cargo_available,
                         getattr(getattr(self.state, 'ship_loadout', None), 'ship_id', None), self.active_target())
            if signature != self._context:
                self.invalidate()
                self._context = deepcopy(signature)
            if self.remembered_flights and self.free != previous_free:
                self.update_remembered()
            self.explanation.setText(self.text('recommend.question', margin=self.margin.value()))
            if self.origin:
                from .trade_view import format_age
                age = format_age(timestamp(self.origin['observed_at']), self.state.observed_markets.cache.clock())
                self.origin_label.setText(self.text('recommend.origin', station=self.origin['station_name'],
                    system=self.origin['system_name'], age=age, source=self.text('recommend.local')))
            else:
                text = self.text('recommend.no_market')
                if context is not None:
                    text = self.text('recommend.current_market', station=context['StationName']) + '\n' + text
                self.origin_label.setText(text)
            cargo = self.text('recommend.cargo_unknown') if self.free is None else (
                self.text('recommend.cargo_full') if self.free == 0 else self.text('recommend.cargo', count=self.free))
            self.ship_label.setText(self.text('recommend.ship', name=name) + '\n' + cargo)
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
        query = MarketSearch('', self.origin['system_name'], radius_ly=self.radius.currentData(),
            max_age=self.max_age.max_age(), required_pad=PadSize(self.pad.currentData()),
            include_fleet_carriers=self.carriers.isChecked(),
            max_distance_to_arrival_ls=int(arrival) if arrival else None, limit=100,
            target=self.active_target())
        source = prepare_trade_source(self.state.observed_markets, self.origin['fid'],
            self.origin['system_name'], self.origin.get('system_address'), getattr(self.state, 'database', None))
        self.invalidate()
        self._invalidated = False
        self.worker = RecommendationWorker(dict(self.origin), (), {}, self.free,
            self.margin.value(), query, self.provider, cache.clock, local_only=local_only, market_source=source,
            supply=self.supply, quantity=self.quantity.value() if self.supply else None)
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
        self.status.setText(self.text('recommend.progress', checked=self.current_run.checked_commodities, total='…'))
        self.progress_bar.setAccessibleName(self.status.text())
        self.pool.start(self.worker)

    @Slot()
    def cancel_search(self):
        self._cancel_search(PartialReason.CANCELLED)

    def cancel_for_context(self):
        self._cancel_search(PartialReason.CONTEXT_CHANGED)

    def _cancel_search(self, reason):
        self._pending_fixed_search = False
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
        text = self.text('recommend.progress', checked=checked, total=planned)
        self.progress_bar.setAccessibleName(text)
        self.status.setText(text)

    @Slot(object)
    def diagnostic_progress(self, diagnostic):
        if not self.current_worker_signal():
            return
        if not self._progress_context_valid():
            return
        if self._invalidated or self.worker.cancel.is_set():
            return
        self.current_run = diagnostic
        self.update_diagnostic_tooltip(diagnostic)
        self.update_progress_bar(diagnostic)

    def update_diagnostic_tooltip(self, diagnostic):
        if diagnostic is not None:
            self.status.setToolTip(self.text('recommend.diagnostic_details',
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

        if self.worker is None or self._invalidated or self.worker.cancel.is_set():
            return
        self._pending_rows = result.rows
        if not self._progress_render_timer.isActive():
            self._progress_render_timer.start()

    def _progress_context_valid(self):
        if self.worker is None or self._invalidated:
            return False
        header = current_market(self.state, self.max_age.max_age())
        name, free = ship_space(self.state)
        signature = (getattr(self.state, 'commander_fid', ''), getattr(self.state, 'system', ''),
                     getattr(self.state, 'station', ''), header, name,
                     self.cargo_context(free),
                     getattr(getattr(self.state, 'ship_loadout', None), 'ship_id', None), self.active_target())
        if signature != self._context or free is None or free <= 0:
            self.invalidate()
            return False
        return True

    def _render_progress(self):
        rows, self._pending_rows = self._pending_rows, None
        if rows is not None and self._progress_context_valid() and rows != self.rows:
            self.render(rows)

    @Slot(object)
    def finished(self, result):
        if not self.current_worker_signal():
            return
        self._progress_render_timer.stop()
        self._pending_rows = None
        self._progress_context_valid()
        accepted = self.worker is not None and not self._invalidated and not self.worker.cancel.is_set()
        local_only = self.worker.local_only
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
            if result.rows != self.rows:
                self.render(result.rows)
            message = self.text('recommend.results', count=len(result.rows))
            if result.partial:
                reason = self.last_run.partial_reason if self.last_run else PartialReason.OTHER
                message += '\n' + self.text('recommend.partial_counts', checked=result.checked, total=result.total,
                                     reason=diagnostic_reason_text(reason))
            else:
                if not result.rows:
                    message = self.text('recommend.no_results_local' if local_only
                                 else 'recommend.no_results')
                message += '\n' + self.text('recommend.complete', checked=result.checked, total=result.total)
            self.status.setText(message)
        else:
            self.status.setText(self.text('recommend.ready'))

        if self._pending_fixed_search:
            QTimer.singleShot(0, self._start_fixed_search)

    @Slot()
    def copy_diagnostic(self):
        if self.last_run is None or self.last_run.finished_at is None:
            return
        QApplication.clipboard().setText(format_recommendation_diagnostic(self.last_run))
        self.copy_notice.setText(self.text('recommend.diagnostic_copied'))
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
            o = row.remote
            master = lookup_by_id(o.commodity_id) or lookup_by_symbol(o.commodity_symbol)
            name = commodity_name(master) if master else o.commodity_name
            def number(value, unit=''):
                return NumericItem('–' if value is None else locale.toString(value) + unit, value)
            profit = number(row.total_profit, ' Cr')
            font = profit.font()
            font.setBold(True)
            profit.setFont(font)
            mark = self.remembered_panel.mark(o, row)
            cells = [mark, TextItem(name), profit,
                NumericItem(locale.toString(float(row.profit_percent), 'f', 2) + ' %', row.profit_percent),
                number(row.quantity, ' t'), number(row.buy_price, ' Cr'),
                number(row.sell_price, ' Cr'), number(row.profit_per_ton, ' Cr'),
                TextItem(o.station_name), TextItem(o.system_name),
                number(o.distance_ly, ' ly'), number(o.distance_to_arrival_ls),
                PadItem(tr('trade.pad_' + o.largest_pad.value) if o.largest_pad else '–', o.largest_pad),
                TextItem(self.text('recommend.local') if o.provider == 'local_elite' else 'Spansh'),
                NumericItem(format_age(o.market_updated_at, now), (now-o.market_updated_at).total_seconds())]
            if self.supply:
                cells.extend((number(row.source.supply, ' t'), number(row.target.demand, ' t'),
                              TextItem(known_station_body(self.state, o) or '–')))
            cells[1].setData(Qt.ItemDataRole.UserRole, row)
            cells[14].setToolTip(o.market_updated_at.isoformat())
            for column, cell in enumerate(cells):
                self.table.setItem(index, column, cell)
        self.table.setSortingEnabled(True)
        self.table.sortItems(2, Qt.SortOrder.DescendingOrder)
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
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
        self.remembered_panel.changed(item, item.data(Qt.UserRole).remote)
        self._remembered_fid = getattr(self.state, 'commander_fid', '')
        self.update_remembered()

    def clear_remembered(self):
        self.remembered_panel.clear()
        self._remembered_fid = None

    def update_remembered(self):
        blocker = QSignalBlocker(self.table)
        for index in range(self.table.rowCount()):
            remembered = self.table.item(index, 0).checkState() == Qt.Checked
            for column in range(self.table.columnCount()):
                self.table.item(index, column).setData(Qt.UserRole + 1, remembered)
        self.remembered_panel.refresh()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()

    def closeEvent(self, event):
        self.cancel_search()
        super().closeEvent(event)


class SupplyRecommendationsView(RecommendationsView):
    """Fixed current selling target, with the shared recommendation lifecycle."""
    supply = True
