"""Commander-bound cargo projection; carrier stock deliberately remains unknown.

See docs/mining-inventory.md for the source audit and conservative boundaries.
Journal files are the durable event source. Only verified Cargo.json snapshots
need an additional QSettings checkpoint because Elite overwrites that sidecar.
"""
from copy import deepcopy
from dataclasses import dataclass, field
import hashlib
import json
import logging
from pathlib import Path
from typing import NamedTuple

from .cargo import cargo_snapshot, read_cargo_snapshot
from .journal_files import journal_sort_key
from .material_inventory import frontier_name, quantity
from .mining_carrier import journal_successor
from .ship_identity import is_definite_non_ship

logger = logging.getLogger(__name__)
SRV_TYPES = ("mev_rhino", "testbuggy", "combat_multicrew_srv_01", "lander01")

EVENTS = {"LoadGame", "ClearSavedGame", "Died", "Loadout", "LaunchSRV", "DockSRV",
          "SRVDestroyed", "Cargo", "MiningRefined", "CollectCargo", "EjectCargo", "MarketBuy",
          "MarketSell", "CargoTransfer", "BuyDrones", "SellDrones", "CargoDepot", "MissionCompleted",
          "EngineerContribution", "SearchAndRescue", "CarrierDepositFuel", "EjectTacticalCore",
          "PowerplayCollect", "PowerplayDeliver", "PowerplayFastTrack", "ShipyardSwap", "ShipyardBuy",
          "Resurrect", "_InvalidCargo"}


def total_stock(*amounts):
    return sum(amounts) if all(amount is not None for amount in amounts) else None


class MiningStock(NamedTuple):
    srv_amount: int | None
    ship_amount: int | None
    carrier_amount: int | None
    total_amount: int | None


@dataclass
class MiningInventory:
    commander_id: int
    fid: str
    vessel: str = "Ship"
    srv: dict | None = None
    ship: dict | None = None
    carrier: dict | None = None
    checkpoints: dict = field(default_factory=dict)
    snapshot_verified: bool = False  # Read diagnostics only; never affects cargo reconstruction.
    cargo_pending: bool = False
    carrier_id: int | None = None
    carrier_feed: dict | None = field(default=None, repr=False)
    carrier_records: dict = field(default_factory=dict)
    vehicle_records: dict = field(default_factory=dict)
    carrier_ledger: dict | None = field(default=None, repr=False)
    carrier_ledger_before: dict | None = field(default=None, repr=False)

    @property
    def vehicle(self):
        """Active vessel for refresh validation; never a combined balance."""
        return self.srv if self.vessel == "SRV" else self.ship

    def stock(self, symbol):
        srv_amount = self.srv.get(symbol, 0) if self.srv is not None else None
        ship_amount = self.ship.get(symbol, 0) if self.ship is not None else None
        carrier_amount = self.carrier.get(symbol, 0) if self.carrier is not None else None
        return MiningStock(srv_amount, ship_amount, carrier_amount,
                           total_stock(srv_amount, ship_amount, carrier_amount))


def validated_cargo(event, fid):
    """Reuse cargo validation, with strict quantities and canonical journal names."""
    payload = deepcopy(event)
    items = payload.get("Inventory")
    if not isinstance(items, list):
        if payload.get("Count") == 0 and type(payload.get("Count")) is int:
            items = payload["Inventory"] = []
        else:
            return None
    try:
        for item in items:
            item["Name"] = frontier_name(item.get("Name"))
            quantity(item.get("Count"))
        if "Count" not in payload:
            payload["Count"] = sum(item["Count"] for item in items)
        quantity(payload["Count"])
        return cargo_snapshot(payload, fid=fid)
    except (ValueError, TypeError, AttributeError):
        return None


class MiningReducer:
    def __init__(self, commander_id, fid):
        self.result = MiningInventory(commander_id, fid)
        self.stocks = {"Ship": None, "SRV": None}
        self.ship_id = None
        self.ship_type = None
        self.seen = set()

    def _delta(self, vessel, name, amount):
        stock = self.stocks[vessel]
        if stock is None:
            return
        updated = stock.get(name, 0) + amount
        if updated < 0:
            raise ValueError("negative cargo")
        stock[name] = updated

    def apply(self, event, source):
        if source in self.seen:
            return
        self.seen.add(source)
        et = event.get("event")
        try:
            if et == "LoadGame":
                ship_type = str(event.get("Ship", "")).casefold()
                ship_id = event.get("ShipID")
                if type(ship_id) is not int or ship_id < 0:
                    ship_id = None
                same_ship = (event.get("FID") == self.result.fid
                             and ship_type and not is_definite_non_ship(ship_type)
                             and type(ship_id) is int and ship_id == self.ship_id
                             and ship_type == self.ship_type)
                if same_ship:
                    logger.debug("Vehicle continuity across sessions verified")
                else:
                    # An SRV login does not identify its mothership. Missing or
                    # conflicting identity cannot revive either previous base.
                    self.stocks["Ship"] = None
                    self.stocks["SRV"] = None
                    logger.debug("Vehicle continuity unclear; stock remains unknown")
                self.result.vessel = "SRV" if ship_type in SRV_TYPES else "Ship"
                self.ship_id = ship_id if not is_definite_non_ship(ship_type) else None
                self.ship_type = ship_type if not is_definite_non_ship(ship_type) else None
            elif et in ("ClearSavedGame", "Died", "_InvalidCargo"):
                self.stocks = {"Ship": None, "SRV": None}
                self.result.vessel = ("SRV" if str(event.get("Ship", "")).casefold()
                                      in SRV_TYPES else "Ship")
                self.ship_id = event.get("ShipID")
                self.ship_type = None
            elif et == "Loadout":
                if type(event.get("ShipID")) is int and event["ShipID"] >= 0 and not is_definite_non_ship(event.get("Ship")):
                    ship_type = str(event.get("Ship", "")).casefold() or None
                    if ((self.ship_id is not None and event["ShipID"] != self.ship_id)
                            or (self.ship_type and ship_type and self.ship_type != ship_type)):
                        self.stocks = {"Ship": None, "SRV": None}
                    self.ship_id = event["ShipID"]
                    self.ship_type = ship_type
            elif et == "LaunchSRV" and event.get("PlayerControlled", True):
                self.result.vessel = "SRV"
                self.stocks["SRV"] = None
            elif et == "DockSRV" and event.get("PlayerControlled", True):
                self.result.vessel = "Ship"
                # Automatic unloading needs a new authoritative ship snapshot.
                self.stocks = {"Ship": None, "SRV": None}
            elif et == "SRVDestroyed":
                self.stocks["SRV"] = None
            elif et == "Cargo":
                vessel = {"ship": "Ship", "srv": "SRV"}.get(str(event.get("Vessel", "")).casefold())
                if vessel is None:
                    raise ValueError("unknown cargo vessel")
                self.result.vessel = vessel
                snapshot = validated_cargo(event, self.result.fid)
                if snapshot is not None:
                    self.stocks[vessel] = {item["frontier_name"]: item["count"]
                                           for item in snapshot["inventory"]}
                elif "Inventory" in event:
                    self.stocks[vessel] = None
                else:
                    # A count-only notification is not another delta. Retain a
                    # fully reconstructed inventory only if its total agrees.
                    count = quantity(event.get("Count"))
                    stock = self.stocks[vessel]
                    if stock is not None and sum(stock.values()) != count:
                        self.stocks[vessel] = None
            elif et in ("MiningRefined", "CollectCargo", "EjectCargo", "MarketBuy", "MarketSell"):
                name = frontier_name(event.get("Type"))
                amount = 1 if et in ("MiningRefined", "CollectCargo") else quantity(event.get("Count"))
                sign = -1 if et in ("EjectCargo", "MarketSell") else 1
                vessel = "Ship" if et in ("MarketBuy", "MarketSell") else self.result.vessel
                self._delta(vessel, name, sign * amount)
            elif et == "CargoTransfer":
                transfers = event.get("Transfers")
                if not isinstance(transfers, list):
                    raise ValueError("missing transfers")
                for transfer in transfers:
                    name, amount = frontier_name(transfer.get("Type")), quantity(transfer.get("Count"))
                    direction = transfer.get("Direction")
                    if direction == "tosrv":
                        self._delta("Ship", name, -amount)
                        self._delta("SRV", name, amount)
                    elif direction == "tocarrier":
                        self._delta("Ship", name, -amount)
                    elif direction == "toship":
                        self._delta("Ship", name, amount)
                        if self.result.vessel == "SRV":
                            self._delta("SRV", name, -amount)
                    else:
                        raise ValueError("unknown transfer direction")
                # No transfer is ever used to infer personal carrier stock.
            elif et in ("BuyDrones", "SellDrones"):
                self._delta("Ship", "drones", quantity(event.get("Count")) * (1 if et == "BuyDrones" else -1))
            elif et == "MissionCompleted":
                if event.get("CommodityReward") or event.get("Commodity"):
                    self.stocks["Ship"] = None
            elif et == "EngineerContribution":
                if event.get("Type") == "Commodity":
                    self.stocks["Ship"] = None
            elif et in ("CargoDepot", "SearchAndRescue",
                        "CarrierDepositFuel", "EjectTacticalCore", "PowerplayCollect", "PowerplayDeliver",
                        "PowerplayFastTrack", "ShipyardSwap", "ShipyardBuy", "Resurrect"):
                # These can change cargo through additional rules. Wait for Cargo
                # rather than displaying an incomplete arithmetic reconstruction.
                self.stocks[self.result.vessel] = None
        except (ValueError, TypeError, AttributeError):
            self.stocks = {"Ship": None, "SRV": None}
        self.result.srv = deepcopy(self.stocks["SRV"])
        self.result.ship = deepcopy(self.stocks["Ship"])
        for vessel, stock in self.stocks.items():
            record = self.result.vehicle_records.setdefault(vessel, {})
            record["status"] = "known" if stock is not None else "unknown"
            if stock is not None:
                record.update(last_confirmed=deepcopy(stock), source=list(source),
                              confirmed_at=event.get("timestamp", ""), ship_id=self.ship_id)


class MiningInventoryReader:
    def __init__(self):
        self._cache = {}

    def _read(self, path, *, carrier_feed=None):
        stat = path.stat()
        signature = (stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
        old = self._cache.get(path)
        if carrier_feed is None and old and old[0] == signature:
            return old[1]
        events, identities = [], set()
        raw_lines, all_events, valid, complete = [], [], True, True
        with path.open("rb") as stream:
            while True:
                offset = stream.tell()
                line = stream.readline()
                if not line or not line.endswith(b"\n"):
                    complete = not line
                    break
                try:
                    event = json.loads(line)
                    if not isinstance(event, dict):
                        raise ValueError("invalid event")
                    if event.get("event") in ("Commander", "LoadGame") and event.get("FID"):
                        identities.add(event["FID"])
                except (ValueError, TypeError):
                    valid = False
                    event = {"event": "_InvalidCargo"}
                if carrier_feed is not None:
                    raw_lines.append(line)
                    all_events.append((offset, event))
                if event.get("event") in EVENTS:
                    events.append((offset, event))
        after = path.stat()
        if signature != (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise OSError("journal changed during cargo reconstruction")
        if carrier_feed is not None and valid:
            carrier_feed.update(path=str(path), raw=b"".join(raw_lines), events=all_events,
                                complete=complete)
        self._cache[path] = (signature, (identities, events), complete)
        return identities, events

    def reconstruct(self, commander_id, fid, sessions, *, checkpoints=None, live_path=None,
                    include_carrier_feed=False):
        reducer = MiningReducer(commander_id, fid)
        live_path = Path(live_path).resolve() if live_path else None
        saved = deepcopy(checkpoints) if isinstance(checkpoints, dict) else {}
        history = saved.get("continuity", {})
        if not isinstance(history, dict) or history.get("fid") != fid or history.get("version") != 1:
            history = {}
        old_records = history.get("vehicles", {})
        if not isinstance(old_records, dict):
            old_records = {}
        events = []
        paths = {}
        for raw in sessions:
            row = dict(raw)
            path = Path(row["journal_file"]).resolve()
            paths.setdefault(path, []).append(row)
        # If a previously verified source has disappeared from the index, place
        # an explicit gap at its chronological position instead of bridging it.
        for record in old_records.values():
            source = record.get("source") if isinstance(record, dict) else None
            if isinstance(source, list) and len(source) == 2 and isinstance(source[0], str):
                paths.setdefault(Path(source[0]).resolve(), [{}])
        previous = None
        for path in sorted(paths, key=journal_sort_key):
            if previous is not None and not journal_successor(previous, path):
                events.append((path, -2, {"event": "_InvalidCargo"}))
            previous = path
            rows = paths[path]
            if any(row.get("commander_id") != commander_id or row.get("fid_seen") != fid
                   or row.get("attribution_status") != "identified" for row in rows):
                events.append((path, -1, {"event": "_InvalidCargo"}))
                continue
            try:
                feed = {} if include_carrier_feed and path == live_path else None
                identities, facts = self._read(path, carrier_feed=feed)
                if identities != {fid}:
                    events.append((path, -1, {"event": "_InvalidCargo"}))
                    continue
                if feed:
                    reducer.result.carrier_feed = feed
                events.extend((path, offset, event) for offset, event in facts)
                offsets = None
                missing_source = False
                for record in old_records.values():
                    source = record.get("source") if isinstance(record, dict) else None
                    if isinstance(source, list) and len(source) == 2 and source[0] == str(path):
                        if offsets is None:
                            offsets = {offset for offset, _ in facts}
                        if type(source[1]) is not int or source[1] not in offsets:
                            missing_source = True
                if missing_source or (path != live_path and not self._cache[path][2]):
                    events.append((path, -3, {"event": "_InvalidCargo"}))
            except OSError:
                events.append((path, -1, {"event": "_InvalidCargo"}))
        latest = next(((path, offset) for path, offset, e in reversed(events) if e.get("event") == "Cargo"), None)
        for path, offset, original in events:
            event = original
            pending_vessel = None
            is_live_snapshot = bool(live_path and path == live_path
                                    and (path, offset) == latest)
            if is_live_snapshot:
                reducer.result.snapshot_verified = validated_cargo(original, fid) is not None
            if event.get("event") == "Cargo" and "Inventory" not in event:
                vessel = event.get("Vessel")
                fingerprint = hashlib.sha256(json.dumps(event, sort_keys=True).encode()).hexdigest()
                checkpoint = saved.get(vessel)
                if (isinstance(checkpoint, dict) and checkpoint.get("fid") == fid
                        and checkpoint.get("source") == [str(path), offset]
                        and checkpoint.get("trigger") == fingerprint):
                    candidate = checkpoint.get("payload")
                    if (isinstance(candidate, dict) and validated_cargo(candidate, fid) is not None
                            and all(candidate.get(k) == original.get(k) for k in ("Vessel", "timestamp", "Count"))):
                        event = candidate
                        if is_live_snapshot:
                            reducer.result.snapshot_verified = True
                        logger.debug("Vehicle inventory restored from verified checkpoint")
                if is_live_snapshot:
                    # The sidecar has no FID or byte offset: the identified live
                    # journal supplies those. Reject ambiguous same-second
                    # triggers and a journal changing around the sidecar read.
                    matches = sum(1 for p, _, e in events if p == path and e.get("event") == "Cargo"
                                  and all(e.get(k) == original.get(k) for k in ("timestamp", "Vessel", "Count")))
                    signature = lambda s: (s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
                    snapshot = None
                    try:
                        if matches == 1 and signature(path.stat()) == self._cache[path][0]:
                            snapshot = read_cargo_snapshot(path.parent / "Cargo.json", original,
                                                           fid=fid, attempts=2, retry_delay=0.04)
                            if signature(path.stat()) != self._cache[path][0]:
                                snapshot = None
                    except OSError:
                        pass
                    if snapshot is not None:
                        reducer.result.snapshot_verified = True
                        event = {**original, "Inventory": [
                            {"Name": item["frontier_name"], "Count": item["count"]}
                            for item in snapshot["inventory"]]}
                        saved[vessel] = dict(fid=fid, source=[str(path), offset], trigger=fingerprint, payload=event)
                    elif event is original and validated_cargo(original, fid) is None:
                        reducer.result.cargo_pending = True
                        pending_vessel = vessel
            reducer.apply(event, (str(path), offset))
            if pending_vessel in ("Ship", "SRV"):
                # Retain last_confirmed diagnostics, never label an older
                # same-total composition as the new authoritative snapshot.
                reducer.stocks[pending_vessel] = None
                setattr(reducer.result, pending_vessel.lower(), None)
                reducer.result.vehicle_records[pending_vessel]["status"] = "pending"
        # Historical values are diagnostic anchors, never a fallback current
        # inventory. Keep a newer stored confirmation if its journal is missing.
        for vessel in ("Ship", "SRV"):
            record = reducer.result.vehicle_records.setdefault(vessel, {"status": "unknown"})
            old = old_records.get(vessel, {})
            if isinstance(old, dict) and isinstance(old.get("last_confirmed"), dict):
                old_source, source = old.get("source"), record.get("source")
                if (isinstance(old_source, list) and len(old_source) == 2
                        and isinstance(old_source[0], str) and type(old_source[1]) is int
                        and (not source or (journal_sort_key(old_source[0]), old_source[1]) >
                             (journal_sort_key(source[0]), source[1]))):
                    record.update({k: deepcopy(old[k]) for k in
                                   ("last_confirmed", "source", "confirmed_at", "ship_id") if k in old})
        saved["continuity"] = dict(version=1, fid=fid, vehicles=deepcopy(reducer.result.vehicle_records))
        reducer.result.checkpoints = saved
        return reducer.result
