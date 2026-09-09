"""On-demand trader UI; background I/O, no inventory or navigation logic."""
from datetime import datetime, timezone
import logging
from pathlib import Path
import sqlite3
import time

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QLocale, Qt, Signal, Slot, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton

from cmdrhelper.i18n import tr, get_language
from cmdrhelper.material_traders import (
    Coordinates, MaterialTraderSearchService, SearchStatus, TraderSearchResult, TraderType,
)

logger = logging.getLogger(__name__)


class _Signals(QObject):
    finished = Signal(object, str, object)


class _Search(QRunnable):
    def __init__(self, service, reference, kind, database_path):
        super().__init__()
        self.reference, self.kind = reference, kind
        self.service, self.database_path = service, database_path
        self.signals = _Signals()

    def run(self):
        _, name, address, coordinates = self.reference
        try:
            # AppState retains the system identity; known coordinates are stored
            # in systems. Reading them belongs in this worker, never the UI thread.
            if coordinates is None and address is not None and self.database_path:
                try:
                    with sqlite3.connect(Path(self.database_path).resolve().as_uri() + '?mode=ro', uri=True) as con:
                        row = con.execute('SELECT name,x,y,z FROM systems WHERE system_address=?', (address,)).fetchone()
                    if row and (not name or row[0].casefold() == name.casefold()):
                        name = name or row[0]
                        coordinates = Coordinates(*row[1:])
                except (sqlite3.Error, ValueError, TypeError, OSError):
                    logger.debug('No usable stored trader reference coordinates')
            result = self.service.find_nearest(self.kind, system_name=name, coordinates=coordinates)
        except Exception:
            logger.exception('Material trader background search failed')
            result = TraderSearchResult(SearchStatus.SCHEMA_ERROR)
        self.signals.finished.emit(self.reference, self.kind, result)


class MaterialTraderPanel(QFrame):
    routeRequested = Signal(str)

    def __init__(self, state, parent=None, *, service=None, pool=None):
        super().__init__(parent)
        self.state = state
        self.service = service or MaterialTraderSearchService()
        self.pool = pool or QThreadPool.globalInstance()
        self.kind = 'Raw'
        self._reference = None
        self._results = {}
        self._running = False
        self._worker = None
        self.setObjectName('card')
        self.search_button = QPushButton(tr('trader.search'), parent)
        self.search_button.clicked.connect(self.search)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        content = QVBoxLayout()
        content.setSpacing(3)
        self.heading = QLabel(objectName='sectionTitle')
        self.description = QLabel()
        self.metadata = QLabel(objectName='muted')
        for label in (self.heading, self.description, self.metadata):
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setWordWrap(True)
            label.setStyleSheet("background: transparent;")
            content.addWidget(label)
        layout.addLayout(content, 1)
        self.route_button = QPushButton(tr('trader.route'))
        self.route_button.clicked.connect(self.open_route)
        layout.addWidget(self.route_button)
        self.setToolTip(tr('trader.access_unknown'))
        for signal_name in ('changed', 'positionChanged', 'commanderIdentityChanged', 'viewedCommanderChanged'):
            signal = getattr(state, signal_name, None)
            if signal is not None:
                signal.connect(self.refresh_reference)
        self.expiry = QTimer(self)
        self.expiry.setInterval(1000)
        self.expiry.timeout.connect(self.render)
        self.expiry.start()
        self.refresh_reference()

    def reference(self):
        name = getattr(self.state, 'system', '') or ''
        name = name.strip() if isinstance(name, str) else ''
        address = getattr(self.state, 'system_address', None)
        if type(address) is not int:
            address = None
        coordinates = getattr(self.state, 'star_pos', None)
        try:
            if not isinstance(coordinates, Coordinates):
                coordinates = Coordinates(*coordinates) if coordinates is not None else None
        except (ValueError, TypeError):
            coordinates = None
        return (getattr(self.state, 'commander_id', None), name, address, coordinates)

    def refresh_reference(self, *_):
        reference = self.reference()
        if reference != self._reference:
            self._reference = reference
            self._results.clear()
        self.render()

    def set_category(self, kind):
        self.kind = kind
        self.refresh_reference()

    @Slot()
    def search(self):
        self.refresh_reference()
        if self._running or self.kind not in {t.value for t in TraderType}:
            return
        _, name, address, coordinates = self._reference
        if not name and coordinates is None and address is None:
            self._results[self.kind] = (time.monotonic(), TraderSearchResult(SearchStatus.INVALID_INPUT))
            self.render()
            return
        self._running = True
        self._results.pop(self.kind, None)
        path = getattr(getattr(self.state, 'database', None), 'path', None)
        worker = _Search(self.service, self._reference, self.kind, path)
        self._worker = worker
        worker.signals.finished.connect(self._finished)
        self.render()
        self.pool.start(worker)

    @Slot(object, str, object)
    def _finished(self, reference, kind, result):
        self._running = False
        self._worker = None
        self.refresh_reference()
        if reference == self._reference:
            self._results[kind] = (time.monotonic(), result)
            if result.status != SearchStatus.FOUND:
                logger.info('Material trader search: %s (HTTP %s)', result.status.value, result.http_status)
        self.render()

    def current_result(self):
        saved = self._results.get(self.kind)
        if not saved:
            return None
        received, result = saved
        age = time.monotonic() - received
        if result.station and result.station.retrieved_at:
            age = max(age, (datetime.now(timezone.utc) - result.station.retrieved_at).total_seconds())
        if age >= MaterialTraderSearchService.CACHE_TTL_SECONDS:
            self._results.pop(self.kind, None)
            return None
        return result

    def render(self):
        classic = self.kind in {t.value for t in TraderType}
        self.search_button.setVisible(classic)
        self.search_button.setEnabled(not self._running)
        self.search_button.setText(tr('trader.searching' if self._running else 'trader.search'))
        result = self.current_result()
        self.setVisible(classic and result is not None)
        self.route_button.hide()
        if not result:
            return
        if result.status == SearchStatus.FOUND and result.station:
            station = result.station
            # Only accept the service's validated type-specific result. Carrier
            # recognition remains solely in the service, not duplicated here.
            if station.trader_type.value != self.kind:
                self.hide()
                return
            self.heading.setText(tr('trader.nearest', kind=tr('trader.' + self.kind.lower())))
            distance = QLocale(get_language()).toString(station.distance_ly, 'f', 1)
            self.description.setText(f'{station.station_name}\n{station.system_name} · {distance} ly')
            details = [self.kind, tr('trader.access_unknown')]
            if station.source_updated_at:
                try:
                    date = datetime.fromisoformat(station.source_updated_at.replace('Z', '+00:00'))
                    locale = QLocale(get_language())
                    date_format = locale.dateFormat(QLocale.FormatType.ShortFormat)
                    if 'yyyy' not in date_format:
                        date_format = date_format.replace('yy', 'yyyy')
                    details.insert(1, tr('trader.updated', date=locale.toString(date.date(), date_format)))
                except ValueError:
                    pass
            self.metadata.setText(' · '.join(details))
            self.metadata.show()
            self.route_button.show()
        else:
            self.heading.setText(tr('trader.search'))
            if result.status in (SearchStatus.INVALID_INPUT, SearchStatus.REFERENCE_UNKNOWN):
                key = 'unknown_system'
            elif result.status == SearchStatus.NOT_FOUND:
                key = 'not_found'
            elif result.status in (SearchStatus.NETWORK_ERROR, SearchStatus.TIMEOUT):
                key = 'unreachable'
            else:
                key = 'unavailable'
            self.description.setText(tr('trader.' + key))
            self.metadata.hide()

    def open_route(self):
        self.refresh_reference()
        result = self.current_result()
        if result and result.status == SearchStatus.FOUND and result.station.trader_type.value == self.kind:
            self.routeRequested.emit(result.station.system_name)
