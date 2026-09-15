"""Event-driven background cargo reconstruction using the existing journal index."""
from copy import deepcopy
import logging
from pathlib import Path
import sqlite3

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal

from .mining_inventory import MiningInventory, MiningInventoryReader
from .mining_carrier import CarrierLedger, read_carrier_feed, stable_id
from .mining_persistence import save_values

logger = logging.getLogger(__name__)


class _Result(QObject):
    ready = Signal(int, object)


class _Read(QRunnable):
    def __init__(self, reader, path, cid, generation, checkpoints, live_path, signals, carrier_saved=None):
        super().__init__()
        self.reader, self.path, self.cid = reader, path, cid
        self.generation, self.checkpoints, self.live_path = generation, checkpoints, live_path
        self.signals = signals
        self.carrier_saved = carrier_saved or {}

    def run(self):
        inventory = MiningInventory(self.cid, "")
        try:
            with sqlite3.connect(Path(self.path).resolve().as_uri() + "?mode=ro", uri=True) as con:
                con.row_factory = sqlite3.Row
                commander = con.execute("SELECT fid FROM commanders WHERE id=?", (self.cid,)).fetchone()
                sessions = [dict(row) for row in con.execute(
                    "SELECT * FROM journal_sessions WHERE commander_id=? OR commander_id IS NULL "
                    "OR attribution_status<>'identified'", (self.cid,))]
                carrier = None
                if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='commander_carriers'").fetchone():
                    carrier = con.execute("SELECT carrier_id FROM commander_carriers WHERE commander_id=?", (self.cid,)).fetchone()
            if commander and commander["fid"]:
                inventory = self.reader.reconstruct(self.cid, commander["fid"], sessions,
                    checkpoints=self.checkpoints, live_path=self.live_path, include_carrier_feed=True)
                inventory.carrier_id = stable_id(carrier["carrier_id"]) if carrier else None
                if inventory.carrier_id is not None:
                    key = CarrierLedger.key(inventory.fid, inventory.carrier_id)
                    inventory.carrier_ledger_before = self.carrier_saved.get(key)
                    ledger = CarrierLedger.normalize(inventory.fid, inventory.carrier_id,
                                                     inventory.carrier_ledger_before)
                    # File verification, catch-up and hashing stay in this worker.
                    inventory.carrier_ledger = CarrierLedger(None).advance(
                        ledger, inventory.carrier_feed, sessions=sessions)
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
        self._cargo_retries = 0
        self.cargo_retry = QTimer(self)
        self.cargo_retry.setSingleShot(True)
        self.cargo_retry.setInterval(500)
        self.cargo_retry.timeout.connect(lambda: self.request(force=True, cargo_retry=True))
        self.ready.connect(self._remember_inventory)
        for name in ("inventoryChanged" if hasattr(state, "inventoryChanged") else "changed", "cargoSnapshotChanged", "viewedCommanderChanged",
                     "commanderIdentityChanged", "journalIndexReady", "databaseImportFinished"):
            signal = getattr(state, name, None)
            if signal is not None:
                if name in ("journalIndexReady", "databaseImportFinished"):
                    signal.connect(lambda *args: self.request(force=True))
                else:
                    signal.connect(self.request)
        QTimer.singleShot(0, self.request)

    def request(self, *_, force=False, cargo_retry=False):
        if not cargo_retry:
            self._cargo_retries = 0
            self.cargo_retry.stop()
        cid = getattr(self.state, "viewed_commander_id", None) or getattr(self.state, "commander_id", None)
        sessions = getattr(self.state, "_journal_index_sessions", None) or []
        live = sessions[-1] if sessions else {}
        live_identity = tuple(live.get(key) for key in ("journal_file", "commander_id", "fid_seen", "attribution_status"))
        identity = (cid, getattr(self.state, "commander_fid", ""),
                    str(getattr(getattr(self.state, "database", None), "path", "")), live_identity)
        revisions = getattr(self.state, "_inventory_revisions", None)
        if revisions is not None:
            snapshot = getattr(self.state, "cargo_snapshot", None) or {}
            signature = (identity, revisions.get("mining", 0), deepcopy(snapshot))
            if not force and signature == getattr(self, "_request_signature", None):
                return
            self._request_signature = signature
        if identity != self._identity:
            self._identity = identity
            self._generation += 1
            self.loading.emit()
        self._dirty = True
        if not self.timer.isActive():
            self.timer.start()

    def refresh_now(self):
        """Manually reread verified snapshots without the event debounce delay."""
        logger.info("Manual mining/cargo refresh started")
        self.request(force=True)  # Recheck commander and journal identity, just like live updates.
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
        self.state.settings.beginGroup("materials/mining/carrier")
        try:
            carrier_saved = {f"materials/mining/carrier/{key}": deepcopy(self.state.settings.value(key))
                             for key in self.state.settings.allKeys()}
        finally:
            self.state.settings.endGroup()
        self.pool.start(_Read(self.reader, path, cid, self._generation, checkpoints, live_path,
                             self.results, carrier_saved))

    def _finished(self, generation, inventory):
        self._running = False
        if generation == self._generation:
            ledger = inventory.carrier_ledger
            writes = {}
            if ledger is not None:
                key = self.carrier_ledger.key(inventory.fid, inventory.carrier_id)
                if self.state.settings.value(key) != inventory.carrier_ledger_before:
                    # Another accepted confirmation/update supersedes the worker's
                    # starting cursor. Recalculate, never overwrite newer balances.
                    self._dirty = True
                    self.timer.start()
                    if self._active_manual:
                        self._manual_pending = True
                        self._active_manual = False
                    return
                writes[key] = ledger
            key = f"materials/mining/cargo_checkpoints/{inventory.commander_id}"
            if inventory.checkpoints:
                writes[key] = inventory.checkpoints
            try:
                save_values(self.state.settings, writes)
            except OSError:
                logger.exception("Mining result not published: settings write failed")
                self.ready.emit(MiningInventory(inventory.commander_id, inventory.fid))
                self._report_manual(None)
                if self._dirty:
                    self.timer.start()
                return
            if ledger is not None:
                self.carrier_ledger.attach(inventory, ledger)
            self.ready.emit(inventory)
            if inventory.cargo_pending and self._cargo_retries < 3:
                self._cargo_retries += 1
                self.cargo_retry.start()
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
                stock_signature(inventory.srv), stock_signature(inventory.ship),
                stock_signature(inventory.carrier))

    def _remember_inventory(self, inventory):
        self._last_inventory = inventory

    def _report_manual(self, inventory):
        if not self._active_manual:
            return
        self._active_manual = False
        logger.info("Manual mining/cargo refresh finished")
        # A verified replay/checkpoint is also a valid refresh result when the
        # new session has not written another Cargo notification yet.
        if inventory is None or inventory.vehicle is None:
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
