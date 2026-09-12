"""Event-driven background cargo reconstruction using the existing journal index."""
from copy import deepcopy
import logging
from pathlib import Path
import sqlite3

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal

from .mining_inventory import MiningInventory, MiningInventoryReader
from .mining_carrier import CarrierLedger, read_carrier_feed, stable_id

logger = logging.getLogger(__name__)


class _Result(QObject):
    ready = Signal(int, object)


class _Read(QRunnable):
    def __init__(self, reader, path, cid, generation, checkpoints, live_path, signals):
        super().__init__()
        self.reader, self.path, self.cid = reader, path, cid
        self.generation, self.checkpoints, self.live_path = generation, checkpoints, live_path
        self.signals = signals

    def run(self):
        inventory = MiningInventory(self.cid, "")
        try:
            with sqlite3.connect(Path(self.path).resolve().as_uri() + "?mode=ro", uri=True) as con:
                con.row_factory = sqlite3.Row
                commander = con.execute("SELECT fid FROM commanders WHERE id=?", (self.cid,)).fetchone()
                sessions = [dict(row) for row in con.execute(
                    "SELECT * FROM journal_sessions WHERE commander_id=?", (self.cid,))]
                carrier = None
                if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='commander_carriers'").fetchone():
                    carrier = con.execute("SELECT carrier_id FROM commander_carriers WHERE commander_id=?", (self.cid,)).fetchone()
            if commander and commander["fid"]:
                inventory = self.reader.reconstruct(self.cid, commander["fid"], sessions,
                    checkpoints=self.checkpoints, live_path=self.live_path)
                inventory.carrier_id = stable_id(carrier["carrier_id"]) if carrier else None
                live_rows = [s for s in sessions if self.live_path and Path(s["journal_file"]).resolve() == Path(self.live_path).resolve()]
                if live_rows and all(s["fid_seen"] == commander["fid"] and s["attribution_status"] == "identified" for s in live_rows):
                    inventory.carrier_feed = read_carrier_feed(self.live_path, commander["fid"])
        except Exception:
            logger.exception("Mining inventory reconstruction failed")
        self.signals.ready.emit(self.generation, inventory)


class MiningInventoryController(QObject):
    loading = Signal()
    ready = Signal(object)
    refreshFinished = Signal(str)

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self.reader = MiningInventoryReader()
        self.carrier_ledger = CarrierLedger(state.settings)
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.results = _Result(self)
        self.results.ready.connect(self._finished)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(150)
        self.timer.timeout.connect(self._start)
        self._identity, self._generation = None, 0
        self._running, self._dirty = False, False
        self._manual_pending = False
        self._active_manual = False
        self._last_inventory = None
        self._manual_before = None
        self.ready.connect(self._remember_inventory)
        for name in ("changed", "cargoSnapshotChanged", "viewedCommanderChanged",
                     "commanderIdentityChanged", "journalIndexReady", "databaseImportFinished"):
            signal = getattr(state, name, None)
            if signal is not None:
                signal.connect(self.request)
        QTimer.singleShot(0, self.request)

    def request(self, *_):
        cid = getattr(self.state, "viewed_commander_id", None) or getattr(self.state, "commander_id", None)
        sessions = getattr(self.state, "_journal_index_sessions", None) or []
        live = sessions[-1] if sessions else {}
        live_identity = tuple(live.get(key) for key in ("journal_file", "commander_id", "fid_seen", "attribution_status"))
        identity = (cid, getattr(self.state, "commander_fid", ""),
                    str(getattr(getattr(self.state, "database", None), "path", "")), live_identity)
        if identity != self._identity:
            self._identity = identity
            self._generation += 1
            self.loading.emit()
        self._dirty = True
        if not self.timer.isActive():
            self.timer.start()

    def refresh_now(self):
        """Manually reread verified snapshots without the event debounce delay."""
        self.request()  # Recheck commander and journal identity, just like live updates.
        self._manual_before = self._inventory_signature(self._last_inventory)
        self.timer.stop()
        self._manual_pending = True
        self._start()

    def _start(self):
        if self._running or not self._dirty:
            return
        self._active_manual = self._manual_pending
        self._manual_pending = False
        self._dirty = False
        cid, fid, path, _ = self._identity
        if not cid or not path:
            self.ready.emit(MiningInventory(cid or 0, ""))
            self._report_manual(None)
            return
        checkpoints = deepcopy(self.state.settings.value(f"materials/mining/cargo_checkpoints/{cid}", {}))
        sessions = getattr(self.state, "_journal_index_sessions", None) or []
        live = sessions[-1] if sessions else {}
        live_path = (live.get("journal_file") if live.get("commander_id") == cid
                     and live.get("fid_seen") == fid and live.get("attribution_status") == "identified" else None)
        if sessions and cid == getattr(self.state, "commander_id", None) and not live_path:
            self.ready.emit(MiningInventory(cid, fid))
            self._report_manual(None)
            return
        self._running = True
        self.pool.start(_Read(self.reader, path, cid, self._generation, checkpoints, live_path, self.results))

    def _finished(self, generation, inventory):
        self._running = False
        if generation == self._generation:
            if inventory.carrier_id is not None and inventory.carrier_feed is not None:
                ledger = self.carrier_ledger.update(inventory.fid, inventory.carrier_id, inventory.carrier_feed)
                self.carrier_ledger.attach(inventory, ledger)
            key = f"materials/mining/cargo_checkpoints/{inventory.commander_id}"
            if inventory.checkpoints and self.state.settings.value(key) != inventory.checkpoints:
                self.state.settings.setValue(key, inventory.checkpoints)
                self.state.settings.sync()
            self.ready.emit(inventory)
        self._report_manual(inventory if generation == self._generation else None)
        if self._dirty:
            if self._manual_pending:
                self.timer.stop()
                self._start()
            else:
                self.timer.start()

    @staticmethod
    def _inventory_signature(inventory):
        if inventory is None:
            return None
        def stock_signature(stock):
            return None if stock is None else tuple(sorted((name, count) for name, count in stock.items() if count))
        return (inventory.commander_id, inventory.fid, inventory.vessel,
                stock_signature(inventory.vehicle), stock_signature(inventory.carrier))

    def _remember_inventory(self, inventory):
        self._last_inventory = inventory

    def _report_manual(self, inventory):
        if not self._active_manual:
            return
        self._active_manual = False
        if inventory is None or not inventory.snapshot_verified or inventory.vehicle is None:
            self.refreshFinished.emit("error")
        else:
            self.refreshFinished.emit("unchanged" if self._inventory_signature(inventory)
                                      == self._manual_before else "updated")

    def confirm_carrier(self, symbol, count, identity):
        """Confirm against the exact displayed identity; never attach to a new commander."""
        inventory = self._last_inventory
        current = (inventory.commander_id, inventory.fid, inventory.carrier_id) if inventory else None
        cid = getattr(self.state, "viewed_commander_id", None) or getattr(self.state, "commander_id", None)
        sessions = getattr(self.state, "_journal_index_sessions", None) or []
        live = sessions[-1] if sessions else {}
        if (self._running or current != identity or inventory is None or cid != inventory.commander_id
                or cid != getattr(self.state, "commander_id", None)
                or inventory.fid != getattr(self.state, "commander_fid", "")
                or inventory.carrier_id is None or inventory.carrier_feed is None
                or live.get("commander_id") != cid or live.get("fid_seen") != inventory.fid
                or live.get("attribution_status") != "identified"
                or str(Path(live.get("journal_file", "")).resolve()) != inventory.carrier_feed["path"]):
            raise ValueError("carrier identity not verified")
        try:
            with sqlite3.connect(Path(self.state.database.path).resolve().as_uri() + "?mode=ro", uri=True) as con:
                owner = con.execute("SELECT c.fid, f.carrier_id FROM commanders c JOIN commander_carriers f "
                                    "ON f.commander_id=c.id WHERE c.id=?", (cid,)).fetchone()
            if owner != (inventory.fid, inventory.carrier_id):
                raise ValueError("carrier owner changed")
        except sqlite3.Error as exc:
            raise ValueError("carrier identity unavailable") from exc
        # Read a fresh anchor at confirmation time; transfers during the dialog are
        # before the user's new baseline, while other commodities keep their deltas.
        feed = read_carrier_feed(live["journal_file"], inventory.fid)
        ledger = self.carrier_ledger.confirm(inventory.fid, inventory.carrier_id, symbol, count, feed)
        inventory.carrier_feed = feed
        self.carrier_ledger.attach(inventory, ledger)
        self.ready.emit(inventory)
