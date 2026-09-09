"""Asynchronous adapter between journal refresh signals and Engineering inventory."""
from pathlib import Path
import sqlite3
import logging

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal, Slot

from .material_inventory import MaterialInventory, MaterialInventoryReader

logger = logging.getLogger(__name__)


class _Result(QObject):
    ready = Signal(int, object, str)


class _Read(QRunnable):
    def __init__(self, reader, database_path, commander_id, generation, signals):
        super().__init__()
        self.reader, self.path, self.commander_id = reader, database_path, commander_id
        self.generation, self.signals = generation, signals

    def run(self):
        inventory = MaterialInventory(self.commander_id, "")
        name = ""
        try:
            with sqlite3.connect(Path(self.path).resolve().as_uri() + "?mode=ro", uri=True) as con:
                con.row_factory = sqlite3.Row
                commander = con.execute("SELECT fid,current_name FROM commanders WHERE id=?", (self.commander_id,)).fetchone()
                if commander and commander["fid"]:
                    name = commander["current_name"] or commander["fid"]
                    inventory.fid = commander["fid"]
                    sessions = [dict(row) for row in con.execute(
                        "SELECT * FROM journal_sessions WHERE commander_id=?", (self.commander_id,))]
                else:
                    sessions = []
            if inventory.fid:
                inventory = self.reader.reconstruct(self.commander_id, inventory.fid, sessions)
        except Exception as exc:
            logger.exception("Material inventory background read failed")
            inventory.issues.append(str(exc))
        self.signals.ready.emit(self.generation, inventory, name)


class MaterialController(QObject):
    """One reader, at most one job, coalesced refreshes; no cross-commander cache.

    Results of an obsolete identity generation never reach the view. File/SQL I/O
    is exclusively performed in the pool; all state and widgets stay on the GUI thread.
    """
    loading = Signal()
    ready = Signal(object, str)

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self.reader = MaterialInventoryReader()
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.results = _Result(self)
        self.results.ready.connect(self._finished)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(150)
        self.timer.timeout.connect(self._start)
        self._identity = None
        self._generation = 0
        self._running = False
        self._dirty = False
        for signal_name in ("changed", "viewedCommanderChanged", "commanderIdentityChanged",
                            "journalIndexReady", "databaseImportFinished"):
            signal = getattr(state, signal_name, None)
            if signal is not None:
                signal.connect(self.request)
        QTimer.singleShot(0, self.request)

    @Slot()
    def request(self, *args):
        cid = getattr(self.state, "viewed_commander_id", None) or getattr(self.state, "commander_id", None)
        fid = getattr(self.state, "commander_fid", "") if cid == getattr(self.state, "commander_id", None) else ""
        identity = (cid, fid)
        if identity != self._identity:
            self._identity = identity
            self._generation += 1
            self.loading.emit()
        self._dirty = True
        if not self.timer.isActive():
            self.timer.start()

    def _start(self):
        if self._running or not self._dirty:
            return
        self._dirty = False
        cid = self._identity[0]
        if not cid:
            self.ready.emit(MaterialInventory(0, ""), "")
            return
        self._running = True
        self.pool.start(_Read(self.reader, self.state.database.path, cid, self._generation, self.results))

    @Slot(int, object, str)
    def _finished(self, generation, inventory, name):
        self._running = False
        if generation == self._generation:
            self.ready.emit(inventory, name)
        if self._dirty:
            self.timer.start()
