"""Debounced mining price reads, independent of inventory and active game FID."""
import logging
import math
from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal, Slot

from .market_store import market_store_path
from .mining_catalog import MINING_COMMODITIES
from .mining_market import MiningPrices, read_mining_prices
from .observed_market_cache import utcnow
from .ui.market_age import age_events, saved_max_age

logger = logging.getLogger(__name__)


class _Signals(QObject):
    finished = Signal(int, object)


class _Read(QRunnable):
    def __init__(self, generation, args, commodities, clock, cancel, signals):
        super().__init__()
        self.generation, self.args = generation, args
        self.commodities, self.clock = commodities, clock
        self.cancel, self.signals = cancel, signals

    def run(self):
        try:
            result = read_mining_prices(*self.args, commodities=self.commodities,
                                       clock=self.clock, cancel=self.cancel)
        except Exception:
            if not self.cancel.is_set():
                logger.exception('Mining own-market price read failed')
            result = MiningPrices(status='error')
        try:
            self.signals.finished.emit(self.generation, result)
        except RuntimeError:
            pass  # View destroyed while the cancellable read was finishing.


class MiningMarketController(QObject):
    ready = Signal(object)

    def __init__(self, state, parent=None, *, commodities=MINING_COMMODITIES,
                 clock=utcnow, pool=None):
        super().__init__(parent)
        self.state, self.commodities, self.clock = state, tuple(commodities), clock
        self.pool = pool or QThreadPool.globalInstance()
        self.signals = _Signals(self)
        self.signals.finished.connect(self._finished)
        self._generation, self._running, self._dirty, self._active = 0, False, False, False
        self._cancel = Event()
        self.destroyed.connect(self._cancel.set)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self._start)
        self.expiry = QTimer(self)
        self.expiry.setSingleShot(True)
        self.expiry.timeout.connect(self.request)
        self._result = MiningPrices()
        self._args = None
        age_events.changed.connect(self.request)
        for name in ('observedMarketsChanged', 'viewedCommanderChanged',
                     'commanderIdentityChanged', 'databaseImportFinished'):
            signal = getattr(state, name, None)
            if signal is not None:
                signal.connect(self.request)

    def set_active(self, active):
        self._active = active
        if active:
            self.request()
        else:
            self._generation += 1
            self._cancel.set()
            self._dirty = False
            self.timer.stop()
            self.expiry.stop()

    def request(self, *_):
        self._generation += 1
        self._cancel.set()
        self.expiry.stop()
        self._result = MiningPrices(status='loading')
        self.ready.emit(self._result)  # Clear old commander/age/commit results immediately.
        self._dirty = True
        if self._active:
            self.timer.start()

    def _start(self):
        if self._running or not self._dirty or not self._active:
            return
        self._dirty, self._running = False, True
        self._cancel.clear()
        cancel = self._cancel
        observer = getattr(self.state, 'observed_markets', None)
        writer = getattr(observer, 'writer', None)
        cache = getattr(observer, '_cache', None)
        path = (writer.destination if writer is not None else cache.path.parent/'markets.db'
                if cache is not None else market_store_path())
        self._args = (Path(path), saved_max_age(getattr(self.state, 'settings', None)))
        self.pool.start(_Read(self._generation, self._args, self.commodities, self.clock,
                              cancel, self.signals))

    @Slot(int, object)
    def _finished(self, generation, result):
        self._running = False
        if generation == self._generation and self._active:
            self._result = result
            self.ready.emit(result)
            max_age = self._args[1]
            if max_age is not None and result.quotes:
                deadline = min(q.header.observed_at+max_age for q in result.quotes)
                delay = max(1, math.ceil((deadline-self.clock()).total_seconds()*1000)+1)
                self.expiry.start(min(delay, 2_147_483_647))
        if self._dirty and self._active:
            self.timer.start()
