"""Asynchronous adapter between journal refresh signals and Odyssey inventory."""
from pathlib import Path
import sqlite3
import logging

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal, Slot

from .odyssey_inventory import OdysseyInventory, OdysseyInventoryReader
from .odyssey_carrier import OdysseyCarrierStore, owned_carrier

logger = logging.getLogger(__name__)


class _Result(QObject):
    ready = Signal(int, object, str)


class _Read(QRunnable):
    def __init__(self, reader, database_path, commander_id, generation, signals, sidecars=None, sidecar_only=False):
        super().__init__()
        self.reader, self.path, self.commander_id = reader, database_path, commander_id
        self.generation, self.signals = generation, signals
        self.sidecars, self.sidecar_only = sidecars, sidecar_only

    def run(self):
        inventory = OdysseyInventory(self.commander_id, "")
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
                options = dict(sidecars=self.sidecars, sidecar_only=self.sidecar_only) if self.sidecars else {}
                inventory = self.reader.reconstruct(self.commander_id, inventory.fid, sessions, **options)
                inventory.carrier_id = owned_carrier(self.path, self.commander_id, inventory.fid)
        except Exception as exc:
            logger.exception("Odyssey inventory background read failed")
            inventory.issues.append(str(exc))
        self.signals.ready.emit(self.generation, inventory, name)


class OdysseyController(QObject):
    """One reader, at most one job, coalesced refreshes; no cross-commander cache.

    Results of an obsolete identity generation never reach the view. Inventory
    reconstruction runs in the pool. Manual stock publication additionally checks
    the current owned-carrier identity; all state and widgets stay on the GUI thread.
    """
    loading = Signal()
    ready = Signal(object, str)

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self.reader = OdysseyInventoryReader()
        self.carrier_store = OdysseyCarrierStore(state.settings)
        self._last_inventory = None
        self._last_name = ""
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
        self._sidecar_only = False
        signal = getattr(state, "odysseySidecarsChanged", None)
        if signal is not None:
            signal.connect(lambda: self.request(force=True, sidecar_only=True))
        for signal_name in ("inventoryChanged" if hasattr(state, "inventoryChanged") else "changed", "viewedCommanderChanged", "commanderIdentityChanged",
                            "journalIndexReady", "databaseImportFinished"):
            signal = getattr(state, signal_name, None)
            if signal is not None:
                if signal_name in ("journalIndexReady", "databaseImportFinished"):
                    signal.connect(lambda *args: self.request(force=True))
                else:
                    signal.connect(self.request)
        QTimer.singleShot(0, self.request)

    @Slot()
    def request(self, *args, force=False, sidecar_only=False):
        cid = getattr(self.state, "viewed_commander_id", None) or getattr(self.state, "commander_id", None)
        if sidecar_only and cid != getattr(self.state, "commander_id", None):
            return
        fid = getattr(self.state, "commander_fid", "") if cid == getattr(self.state, "commander_id", None) else ""
        identity = (cid, fid)
        revisions = getattr(self.state, "_inventory_revisions", None)
        if revisions is not None:
            signature = (identity, revisions.get("odyssey", 0))
            if not force and signature == getattr(self, "_request_signature", None):
                return
            self._request_signature = signature
        if identity != self._identity:
            self._identity = identity
            self._generation += 1
            self._last_inventory = None
            self.loading.emit()
        self._sidecar_only = sidecar_only and (not self._dirty or self._sidecar_only)
        self._dirty = True
        if not self.timer.isActive():
            self.timer.start()

    def refresh_now(self):
        self.request(force=True)
        self.timer.stop()
        self._start()

    def _start(self):
        if self._running or not self._dirty:
            return
        self._dirty = False
        cid = self._identity[0]
        if not cid:
            self.ready.emit(OdysseyInventory(0, ""), "")
            return
        self._running = True
        capture = getattr(getattr(self.state, "watcher", None), "odyssey_sidecars", None)
        self.pool.start(_Read(self.reader, self.state.database.path, cid, self._generation, self.results,
                             capture.export() if capture else None, self._sidecar_only))

    @Slot(int, object, str)
    def _finished(self, generation, inventory, name):
        self._running = False
        if generation == self._generation and not self._dirty:
            self._attach_carrier(inventory)
            self._last_inventory, self._last_name = inventory, name
            self.ready.emit(inventory, name)
        if self._dirty:
            self.timer.start()

    def _active(self, inventory):
        return (inventory.commander_id == getattr(self.state, "commander_id", None)
                and inventory.commander_id == (getattr(self.state, "viewed_commander_id", None)
                                                or getattr(self.state, "commander_id", None))
                and inventory.fid == getattr(self.state, "commander_fid", None))

    def _attach_carrier(self, inventory):
        inventory.carrier_records = {}
        if (not self._active(inventory) or inventory.carrier_id is not None
                and owned_carrier(self.state.database.path, inventory.commander_id, inventory.fid)
                    != inventory.carrier_id):
            inventory.carrier_id = None
        if inventory.carrier_id is not None:
            inventory.carrier_records = self.carrier_store.load(inventory.fid, inventory.carrier_id)["records"]

    def confirm_carrier(self, category, name, amount, identity):
        inventory = self._last_inventory
        if (inventory is None or not self._active(inventory)
                or identity != (inventory.commander_id, inventory.fid, inventory.carrier_id)
                or inventory.carrier_id is None
                or owned_carrier(self.state.database.path, inventory.commander_id, inventory.fid)
                   != inventory.carrier_id):
            raise ValueError("carrier identity changed or unavailable")
        self.carrier_store.confirm(inventory.fid, inventory.carrier_id, category, name, amount)
        tracker = getattr(self.state, "odyssey_carrier_tracking", None)
        if tracker is not None:
            tracker.reanchor()
        self._attach_carrier(inventory)
        self.ready.emit(inventory, self._last_name)
