"""Optional arrival notices. Requests are isolated by commander and stay generation."""
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from cmdrhelper.online_services import fetch_edsm_system_status
from cmdrhelper.i18n import tr

SETTING = "edsm_system_status/enabled"


def enabled(settings):
    value = settings.value(SETTING, False)
    return value.strip().lower() not in ("0", "false", "no", "off", "") if isinstance(value, str) else bool(value)


class StatusSignals(QObject):
    finished = Signal(int, str)


class StatusWorker(QRunnable):
    def __init__(self, generation, name, address, current, fetch):
        super().__init__()
        self.setAutoDelete(False)
        self.signals = StatusSignals()
        self.generation, self.name, self.address = generation, name, address
        self.current, self.fetch = current, fetch

    @Slot()
    def run(self):
        result = "no_response"
        if self.current():
            try:
                result = self.fetch(self.name, self.address)
            except Exception:
                pass
        self.signals.finished.emit(self.generation, result)


class EdsmSystemStatus(QObject):
    notice = Signal(object)
    cleared = Signal()

    def __init__(self, settings, parent=None, *, fetch=fetch_edsm_system_status, pool=None):
        super().__init__(parent)
        self.settings, self.fetch = settings, fetch
        self.pool = pool or QThreadPool(self)
        if pool is None:
            self.pool.setMaxThreadCount(2)
        self.generation = 0
        self.commander = ""
        self.name, self.address = "", None
        self.workers = {}
        self.active = enabled(settings)

    def set_enabled(self, value):
        self.active = bool(value)
        self.settings.setValue(SETTING, self.active)
        self.settings.sync()
        self._invalidate()

    def _invalidate(self):
        self.generation += 1
        self.cleared.emit()

    @Slot(object, str)
    def observe(self, events, commander):
        if commander != self.commander:
            self._invalidate()
            self.commander = commander
            self.name, self.address = "", None
        if not commander:
            return
        for event in events:
            if event.get("event") not in ("Location", "FSDJump", "CarrierJump"):
                continue
            name = str(event.get("StarSystem") or "").strip()
            address = event.get("SystemAddress")
            if not name:
                continue
            same = (address == self.address if isinstance(address, int) and isinstance(self.address, int)
                    else name.casefold() == self.name.casefold())
            self.name, self.address = name, address
            if same:
                continue
            self._invalidate()
            if not self.active:
                continue
            generation = self.generation
            worker = StatusWorker(generation, name, address,
                lambda g=generation: self.active and g == self.generation, self.fetch)
            worker.signals.finished.connect(self._finished)
            self.workers[generation] = worker
            self.pool.start(worker)

    @Slot(int, str)
    def _finished(self, generation, status):
        self.workers.pop(generation, None)
        if generation != self.generation or not self.active:
            return
        if status not in ("known", "unknown", "no_response"):
            status = "no_response"
        keys = {"known": "edsm_status.known", "unknown": "edsm_status.unknown",
                "no_response": "edsm_status.no_response"}
        self.notice.emit((tr(keys[status]),))
