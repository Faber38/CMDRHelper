"""Opt-in live visits only. No journal/archive enumeration or startup fetch."""
from collections import OrderedDict
import logging
from datetime import timedelta
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from cmdrhelper.spansh_cache import SystemCache, timestamp, utcnow, valid_id

SETTING = 'spansh_stations/enabled'


def enabled(settings):
    value = settings.value(SETTING, False)
    return value.strip().lower() not in ('0','false','no','off','') if isinstance(value,str) else bool(value)


class LiveEntryGate:
    """Baseline on every refresh; only new, committed watcher jumps qualify."""
    def __init__(self, now=utcnow):
        self.now = now
        self.started_at = now()
        self.commander, self.address = '', None

    def observe(self, events, commander, address, *, live=False):
        previous = (self.commander, self.address)
        self.commander, self.address = commander, address
        if (not live or not commander or not valid_id(address)
                or previous[0] != commander or previous[1] == address):
            return None
        for event in reversed(events or []):
            when = timestamp(event.get('timestamp'))
            if (event.get('event') in ('FSDJump','CarrierJump','Location')
                    and type(event.get('SystemAddress')) is int and event['SystemAddress'] == address
                    and when and self.started_at <= when <= self.now() + timedelta(minutes=5)):
                return address
        return None


class WorkerSignals(QObject):
    finished = Signal(int, object, object)


class CacheWorker(QRunnable):
    def __init__(self, generation, address, cache, current, manual=False):
        super().__init__()
        self.setAutoDelete(False)
        self.manual, self.success = manual, None
        self.signals = WorkerSignals()
        self.generation, self.address, self.cache, self.current = generation, address, cache, current

    @Slot()
    def run(self):
        data = None
        try:
            if self.current():
                data, self.success = self.cache.request(self.address, manual=self.manual, automatic=not self.manual)
        except Exception:
            logging.getLogger(__name__).exception('Spansh cache worker failed')
        finally:
            self.signals.finished.emit(self.generation, self.address, data)


class SpanshStations(QObject):
    updated = Signal(object)
    activityChanged = Signal()
    completed = Signal(object, bool)
    alreadyUpdated = Signal(object)

    def __init__(self, settings, parent=None, *, cache=None, pool=None, now=utcnow):
        super().__init__(parent)
        self.settings = settings
        self.cache = cache if cache is not None else SystemCache()
        self.pool = pool if pool is not None else QThreadPool(self)
        if pool is None: self.pool.setMaxThreadCount(1)
        self.gate = LiveEntryGate(now)
        self.active = enabled(settings)
        self.generation = 0
        self.workers = {}
        self.documents = OrderedDict()

    def set_enabled(self, value):
        self.active = bool(value)
        self.settings.setValue(SETTING, self.active)
        self.settings.sync()
        self.generation += 1
        # Toggling changes only the displayed local cache, never starts a fetch.
        self.updated.emit(self.gate.address)
        self.activityChanged.emit()

    def cached(self, address):
        if not self.active or not valid_id(address): return None
        if address not in self.documents: self.documents[address] = self.cache.read(address)
        self.documents.move_to_end(address)
        while len(self.documents) > 8: self.documents.popitem(last=False)
        return self.documents[address]

    def observe(self, events, commander, address, *, live=False):
        if commander != self.gate.commander: self.generation += 1
        entered = self.gate.observe(events, commander, address, live=live)
        if entered is None or not self.active: return
        cached = self.cached(entered)
        if cached and self.cache.fresh(cached): return
        self._start(entered, manual=False)

    def busy(self, address):
        return any(key[1] == address for key in self.workers)

    def refresh_system(self, address):
        """Bypass TTL/automatic attempts, but not a successful fetch today."""
        return self._start(address, manual=True)

    def _start(self, address, *, manual):
        if not self.active or not valid_id(address) or self.busy(address): return False
        if manual and self.cache.fetched_today(self.cache.read(address)):
            self.alreadyUpdated.emit(address)
            return False
        generation = self.generation
        worker = CacheWorker(generation, address, self.cache,
            lambda: self.active and self.generation == generation
                    and (manual or self.gate.address == address), manual=manual)
        worker.signals.finished.connect(self._finished)
        self.workers[(generation, address)] = worker
        self.activityChanged.emit()
        self.pool.start(worker)
        return True

    @Slot(int, object, object)
    def _finished(self, generation, address, data):
        worker = self.workers.pop((generation,address), None)
        # A cache may have been updated while this worker was queued.
        if worker and worker.manual and worker.success is None and data is not None:
            if self.active and generation == self.generation:
                self.alreadyUpdated.emit(address)
            self.activityChanged.emit()
            return
        if data is not None:
            self.documents[address] = data
            self.documents.move_to_end(address)
            while len(self.documents) > 8: self.documents.popitem(last=False)
        if self.active and generation == self.generation:
            if address == self.gate.address or (worker and worker.manual):
                self.updated.emit(address)
            if worker and worker.manual:
                self.completed.emit(address, worker.success is True)
        self.activityChanged.emit()
