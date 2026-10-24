"""Debounced commander sale reads using the existing journal index."""
import logging
from threading import Event

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal, Slot

from .mining_catalog import MINING_COMMODITIES
from .mining_market import MiningPrices, read_mining_prices

logger = logging.getLogger(__name__)


class _Signals(QObject):
    finished = Signal(int, object)


class _Read(QRunnable):
    def __init__(self, generation, args, commodities, cache, cancel, signals):
        super().__init__()
        self.generation, self.args = generation, args
        self.commodities, self.cache = commodities, cache
        self.cancel, self.signals = cancel, signals

    def run(self):
        try:
            result = read_mining_prices(*self.args, commodities=self.commodities,
                                       cache=self.cache, cancel=self.cancel)
        except Exception:
            if not self.cancel.is_set():
                logger.exception('Mining own-sale read failed')
            result = MiningPrices(status='error')
        try:
            self.signals.finished.emit(self.generation, result)
        except RuntimeError:
            pass  # View destroyed while the cancellable read was finishing.


class MiningMarketController(QObject):
    ready = Signal(object)

    def __init__(self, state, parent=None, *, commodities=MINING_COMMODITIES,
                 pool=None):
        super().__init__(parent)
        self.state, self.commodities = state, tuple(commodities)
        self._cache = {}
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
        self._result = MiningPrices()
        self._args = None
        self._identity = self._current_identity()
        self._dirty = True  # Initial read, also when the tab is first opened later.
        for name, slot in (('miningSalesChanged', self.request),
                           ('journalIndexReady', self.request),
                           ('journalCatchupReady', self.request),
                           ('viewedCommanderChanged', self._identity_changed),
                           ('commanderIdentityChanged', self._identity_changed),
                           ('databaseImportFinished', self._import_finished)):
            signal = getattr(state, name, None)
            if signal is not None:
                signal.connect(slot)

    def _current_identity(self):
        return (getattr(self.state, 'viewed_commander_id', None)
                or getattr(self.state, 'commander_id', None),
                str(getattr(getattr(self.state, 'database', None), 'path', '')))

    def _identity_changed(self, *_):
        identity = self._current_identity()
        if identity != self._identity:
            self._identity = identity
            self._result = MiningPrices()
            self.ready.emit(self._result)  # Never show another commander's prices.
            self.request()

    def _import_finished(self, stats=None, error=''):
        # Archive imports explicitly report zero processed files. Other import
        # paths only provide DB totals: their sale relevance is unknown.
        if not error and isinstance(stats, dict) and stats.get('imported_journals') == 0:
            return
        self.request()

    def set_active(self, active):
        if active == self._active:
            return
        self._active = active
        if active:
            self._identity_changed()
            if self._dirty:
                self.timer.start()
        else:
            self._generation += 1
            self._cancel.set()
            self._dirty = self._dirty or self._running
            self.timer.stop()

    def request(self, *_):
        self._generation += 1
        self._cancel.set()
        # Keep accepted prices until a replacement is ready. Identity changes
        # clear separately, including while the view is hidden.
        self._dirty = True
        if self._active:
            self.timer.start()

    def _start(self):
        if self._running or not self._dirty or not self._active:
            return
        self._dirty, self._running = False, True
        self._cancel.clear()
        cancel = self._cancel
        cid = getattr(self.state, 'viewed_commander_id', None) or getattr(self.state, 'commander_id', None)
        self._args = (getattr(getattr(self.state, 'database', None), 'path', None), cid)
        self.pool.start(_Read(self._generation, self._args, self.commodities, self._cache,
                              cancel, self.signals))

    @Slot(int, object)
    def _finished(self, generation, result):
        self._running = False
        if generation == self._generation and self._active:
            if result.status != 'ok':
                result = MiningPrices(self._result.quotes, result.status)
            if result != self._result:
                self._result = result
                self.ready.emit(result)
        if self._dirty and self._active:
            self.timer.start()
