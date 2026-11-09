"""Demand-driven process evidence. All policy/state belongs to the GUI thread."""
from dataclasses import dataclass
from threading import Event, Thread, get_ident
from time import monotonic

from PySide6.QtCore import QObject, Signal, Slot, Qt

from .game_instances import ProcessObservation, ProcessSnapshot
from . import performance_profile as profile


@dataclass(frozen=True)
class ScanResult:
    generation: int
    started: float
    finished: float
    available: bool
    instances: tuple


class _Results(QObject):
    ready = Signal(object)


@profile.measure('process.scan_worker')
def _scan(inspector, generation, clock, cancelled, signals):
    # No manager, settings, widgets or source runtimes cross into this thread.
    started = clock()
    try:
        snapshot = inspector() if not cancelled.is_set() else ProcessSnapshot(False)
        available, instances = snapshot.available, tuple(snapshot.instances)
        # Production Linux identities must never fall back to a wall-clock time.
        if any(type(p.start_ticks) is not int for p in instances):
            available, instances = False, ()
    except Exception:
        available, instances = False, ()
        if profile.ENABLED:
            profile.event('process.scan_failure', outcome='error')
    result = ScanResult(generation, started, clock(), available, instances)
    if not cancelled.is_set():
        try:
            signals.ready.emit(result)
        except RuntimeError:
            if profile.ENABLED:
                profile.event('process.scan_discard', outcome='skipped', scan_discarded=1)
    elif profile.ENABLED:
        profile.event('process.scan_discard', outcome='skipped', scan_discarded=1)


class ProcessScan(QObject):
    ready = Signal()
    MAX_AGE = ProcessObservation.MAX_AGE

    def __init__(self, inspector, context, parent=None, *, clock=monotonic, allowed=lambda: True):
        super().__init__(parent)
        self._inspector, self._context, self._clock = inspector, context, clock
        self._allowed = allowed
        self._owner = get_ident()
        self._signals = _Results()
        self._signals.ready.connect(self._receive, Qt.QueuedConnection)
        self._cancelled = Event()
        self._generation = 0
        self._running = None
        self._result = None
        self._result_context = None
        self._pending = False
        self._requests = 0
        self._requested_at = 0
        self._delivering = False

    @property
    def pending(self):
        return self._running is not None and not self._cancelled.is_set()

    def invalidate(self):
        self._generation += 1
        self._result = None

    def valid(self, result=None):
        result = result or self._result
        return bool(not self._cancelled.is_set() and result is not None
                    and self._allowed()
                    and result.generation == self._generation
                    and self._result_context == self._context()
                    and 0 <= self._clock()-result.started < self.MAX_AGE)

    def read(self):
        # A background caller must neither access GUI state nor start a scan.
        if get_ident() != self._owner or self._cancelled.is_set() or not self._allowed():
            return ProcessSnapshot(False)
        if self.valid():
            return ProcessSnapshot(self._result.available, list(self._result.instances), self._result)
        self._result = None
        if not self._delivering:
            self.request()
        return ProcessSnapshot(False)

    def current(self, snapshot):
        return snapshot._scan_token is self._result and self.valid()

    def request(self):
        if (get_ident() != self._owner or self._cancelled.is_set()
                or self._delivering or not self._allowed()):
            return
        context = self._context()
        if self._running is not None:
            self._requests += 1
            # Only a demand for a new context requires a replacement scan.
            if (self._running[0], self._running[1]) != (self._generation, context):
                self._pending = True
            return
        self._result = None
        self._requests = 1
        self._requested_at = self._clock()
        self._running = (self._generation, context)
        thread = Thread(target=_scan, args=(self._inspector, self._generation,
                        self._clock, self._cancelled, self._signals),
                        name='CMDRHelper-ProcessScan', daemon=True)
        try:
            thread.start()
        except Exception:
            self._running = None
            if profile.ENABLED:
                profile.event('process.scan_failure', outcome='error')

    @Slot(object)
    @profile.measure('process.scan_apply')
    def _receive(self, result):
        if self._cancelled.is_set():
            return
        self._result_context = self._running[1]
        self._running = None
        pending, self._pending = self._pending, False
        if profile.ENABLED:
            profile.event('process.scan_wait', duration_ms=(self._clock()-self._requested_at)*1000,
                          scan_requests=self._requests, scan_coalesced=max(0, self._requests-1))
        self._result = result if self.valid(result) else None
        if self._result is None and profile.ENABLED:
            profile.event('process.scan_discard', outcome='skipped', scan_discarded=1)
        # Expiry during callbacks must not create a self-sustaining scan loop.
        self._delivering = True
        try:
            self.ready.emit()
        finally:
            self._delivering = False
        if pending:
            self.request()  # One already requested replacement, no periodic retry.

    def stop(self):
        self._cancelled.set()
        self.invalidate()
        self._pending = False
        # Read-only daemon work may finish, but shutdown never joins the thread.
