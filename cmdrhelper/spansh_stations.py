"""Opt-in live visits and one current-system check after startup; no archives."""
from cmdrhelper import performance_profile as profile
from cmdrhelper.exit_tasks import submit
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
        current_time = self.now()
        earliest = max(self.started_at, current_time - timedelta(minutes=5))
        for event in reversed(events or []):
            when = timestamp(event.get('timestamp'))
            if (event.get('event') in ('FSDJump','CarrierJump','Location')
                    and type(event.get('SystemAddress')) is int and event['SystemAddress'] == address
                    and when and earliest <= when <= current_time + timedelta(minutes=5)):
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
    @profile.measure('spansh.worker')
    def run(self):
        data = None
        try:
            if self.current():
                data, self.success = self.cache.request(self.address, manual=self.manual, automatic=not self.manual)
        except Exception:
            logging.getLogger(__name__).exception('Spansh cache worker failed')
        finally:
            if profile.ENABLED:
                profile.mark(('spansh', id(self)))
            self.signals.finished.emit(self.generation, self.address, data)


class SpanshStations(QObject):
    updated = Signal(object)
    activityChanged = Signal()
    completed = Signal(object, bool)

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
        from .spansh_origins import OriginLookup
        self.origins = OriginLookup(self.cache, self)
        self.origins.updated.connect(self._origin_updated)

    @Slot(object)
    def _origin_updated(self, address):
        self.documents.pop(address, None)
        self.updated.emit(address)

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
        self.ensure_current(entered)

    def ensure_current(self, address):
        """Share automatic cache/worker rules with the startup handoff."""
        if not self.active or not valid_id(address) or address != self.gate.address:
            return
        cached = self.cached(address)
        if cached and self.cache.fresh(cached):
            if profile.ENABLED:
                profile.event('spansh.decision', trigger='automatic', outcome='cache_hit',
                    cache_age_seconds=max(0, (self.cache.now()-timestamp(cached['fetched_at'])).total_seconds()))
            return
        self._start(address, manual=False)

    def status(self, address):
        """One status projection shared by both existing station controls."""
        if not self.active:
            return 'spansh.refresh_disabled', ''
        if not valid_id(address):
            return 'spansh.status_missing', ''
        if self.busy(address):
            return 'spansh.refresh_busy', ''
        wait = self.cache.server_wait(address)
        if wait:
            until = timestamp(wait['retry_not_before']).astimezone().isoformat(timespec='seconds')
            return 'spansh.status_server_wait', until
        attempt = self.cache.attempt(address)
        if attempt.get('kind') == 'server' and not attempt.get('retry_not_before'):
            return 'spansh.status_server_unknown', ''
        if attempt:
            return 'spansh.refresh_failed', ''
        data = self.cached(address)
        if data:
            return ('spansh.status_current' if self.cache.fresh(data) else 'spansh.status_old'), ''
        return 'spansh.status_missing', ''

    def busy(self, address):
        return any(key[1] == address for key in self.workers)

    def refresh_system(self, address):
        """Bypass age and local error pauses, never an explicit server wait."""
        return self._start(address, manual=True)

    def _start(self, address, *, manual):
        if not self.active or not valid_id(address) or self.busy(address):
            if profile.ENABLED:
                profile.event('spansh.decision', trigger='manual' if manual else 'automatic',
                              outcome='busy' if self.active and valid_id(address) else 'inactive')
            return False
        server_wait = self.cache.server_wait(address)
        if server_wait or (not manual and not self.cache.automatic_allowed(address)):
            if profile.ENABLED:
                profile.event('spansh.decision', trigger='manual' if manual else 'automatic',
                              outcome='server_wait' if server_wait else 'error_pause')
            self.activityChanged.emit()
            return False
        if profile.ENABLED:
            profile.event('spansh.decision', trigger='manual' if manual else 'automatic', outcome='started')
        generation = self.generation
        worker = CacheWorker(generation, address, self.cache,
            lambda: self.active and self.generation == generation
                    and (manual or self.gate.address == address), manual=manual)
        worker.signals.finished.connect(self._finished)
        self.workers[(generation, address)] = worker
        self.activityChanged.emit()
        try:
            submit(self.pool, worker)
        except Exception:
            self.workers.pop((generation, address), None)
            self.activityChanged.emit()
            raise
        return True

    @Slot(int, object, object)
    @profile.measure('spansh.publish')
    def _finished(self, generation, address, data):
        worker = self.workers.pop((generation,address), None)
        if profile.ENABLED and worker:
            profile.receive(('spansh', id(worker)), 'spansh.handoff')
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
