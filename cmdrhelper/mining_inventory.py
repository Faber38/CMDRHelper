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
          "Resurrect", "Embark", "Disembark", "ShipyardNew", "_InvalidCargo"}


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
    ship_id: int | None = None
    ship_type: str | None = None
    source_folder: str = ""
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

    def displayed_stock(self, vessel, symbol):
        """Historical ship values are presentation only, never stock()/totals."""
        stock = self.ship if vessel == "Ship" else self.srv
        record = self.vehicle_records.get(vessel, {})
        if stock is not None:
            return stock.get(symbol, 0), record.get("quality", "confirmed")
        if (vessel == "Ship" and type(self.ship_id) is int
                and record.get("ship_id") == self.ship_id
                and (not record.get("ship_type") or record["ship_type"] == self.ship_type)
                and record.get("source_folder") == self.source_folder
                and isinstance(record.get("last_confirmed"), dict)):
            return record["last_confirmed"].get(symbol, 0), "stale"
        return None, "unknown"


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
        self.srv_id = None
        self.srv_type = None
        self.pending_count = None
        self.docking_stock = None
        self.corroborated_count = False
        self._journal = None
        self._folder = ""

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
        self.corroborated_count = False
        before = deepcopy(self.stocks)
        previous_count, self.pending_count = self.pending_count, None
        if source[0] != self._journal:
            self._journal = source[0]
            self._folder = str(Path(source[0]).resolve().parent)
        folder = self._folder
        if self.result.source_folder and folder != self.result.source_folder:
            self.stocks = {"Ship": None, "SRV": None}
            self.result.vehicle_records.clear()
            self.ship_id = self.ship_type = self.srv_id = None
            self.srv_type = None
            self.docking_stock = None
        self.result.source_folder = folder
        if et not in ("DockSRV", "Loadout", "Cargo", "Embark", "Disembark"):
            self.docking_stock = None
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
                same_srv = (event.get("FID") == self.result.fid and ship_type in SRV_TYPES
                            and self.result.vessel == "SRV" and type(ship_id) is int
                            and ship_id == self.srv_id and ship_type == self.srv_type
                            and type(self.ship_id) is int)
                if same_ship or same_srv:
                    logger.debug("Vehicle continuity across sessions verified")
                else:
                    # An SRV login does not identify its mothership. Missing or
                    # conflicting identity cannot revive either previous base.
                    self.stocks["Ship"] = None
                    self.stocks["SRV"] = None
                    logger.debug("Vehicle continuity unclear; stock remains unknown")
                self.result.vessel = "SRV" if ship_type in SRV_TYPES else "Ship"
                if not is_definite_non_ship(ship_type):
                    self.ship_id, self.ship_type = ship_id, ship_type
                self.srv_id = ship_id if ship_type in SRV_TYPES else self.srv_id
                if ship_type in SRV_TYPES:
                    self.srv_type = ship_type
            elif et in ("ClearSavedGame", "Died", "_InvalidCargo"):
                self.stocks = {"Ship": None, "SRV": None}
                self.result.vessel = ("SRV" if str(event.get("Ship", "")).casefold()
                                      in SRV_TYPES else "Ship")
                self.ship_id = event.get("ShipID")
                self.ship_type = None
                self.srv_id = None
                self.srv_type = None
                if et == "ClearSavedGame":
                    self.result.vehicle_records.clear()
            elif et == "Loadout":
                if type(event.get("ShipID")) is int and event["ShipID"] >= 0 and not is_definite_non_ship(event.get("Ship")):
                    ship_type = str(event.get("Ship", "")).casefold() or None
                    if ((event["ShipID"] != self.ship_id)
                            or (self.ship_type and ship_type and self.ship_type != ship_type)):
                        self.stocks = {"Ship": None, "SRV": None}
                        self.docking_stock = None
                    self.ship_id = event["ShipID"]
                    self.ship_type = ship_type
            elif et == "LaunchSRV" and event.get("PlayerControlled", True):
                self.result.vessel = "SRV"
                self.stocks["SRV"] = None
                self.srv_id = event.get("ID")
                self.srv_type = str(event.get("SRVType", "")).casefold() or None
            elif et == "DockSRV" and event.get("PlayerControlled", True):
                self.result.vessel = "Ship"
                # Empty SRV cannot change ship cargo. Otherwise require a fresh
                # Ship count to corroborate automatic unloading before publishing.
                ship, srv = self.stocks["Ship"], self.stocks["SRV"]
                if event.get("ID") is not None and event["ID"] != self.srv_id:
                    srv = None
                if ship is not None and srv is not None and type(self.ship_id) is int:
                    self.docking_stock = deepcopy(ship)
                    for name, count in srv.items():
                        self.docking_stock[name] = self.docking_stock.get(name, 0) + count
                if srv is None or sum(srv.values()):
                    self.stocks["Ship"] = None
                self.stocks["SRV"] = None
            elif et in ("Embark", "Disembark"):
                if not event.get("Taxi") and not event.get("Multicrew"):
                    self.result.vessel = "SRV" if event.get("SRV") else "Ship"
                    vehicle_id = event.get("ID")
                    if type(vehicle_id) is int and vehicle_id >= 0:
                        if event.get("SRV") and self.srv_id != vehicle_id:
                            self.stocks["SRV"] = None
                            self.srv_id, self.srv_type = vehicle_id, None
                        elif not event.get("SRV") and self.ship_id != vehicle_id:
                            self.stocks = {"Ship": None, "SRV": None}
                            self.ship_id, self.ship_type = vehicle_id, None
                            self.srv_id = self.srv_type = None
                            self.docking_stock = None
            elif et == "SRVDestroyed":
                self.stocks["SRV"] = None
            elif et == "Cargo":
                vessel = {"ship": "Ship", "srv": "SRV"}.get(str(event.get("Vessel", "")).casefold())
                if vessel is None:
                    raise ValueError("unknown cargo vessel")
                self.result.vessel = vessel
                previous = deepcopy(self.stocks[vessel])
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
                    if (vessel == "Ship" and self.docking_stock is not None
                            and sum(self.docking_stock.values()) == count):
                        self.stocks[vessel] = self.docking_stock
                        self.corroborated_count = True
                self.docking_stock = None
                if (event.get("timestamp") and type(event.get("Count")) is int
                        and (snapshot is not None or "Inventory" not in event)
                        and (previous is None or sum(previous.values()) != event["Count"])):
                    self.pending_count = dict(stock=previous, snapshot=deepcopy(self.stocks[vessel]),
                        vessel=vessel, count=event["Count"], timestamp=event["timestamp"], journal=source[0])
            elif et in ("MiningRefined", "CollectCargo", "EjectCargo", "MarketBuy", "MarketSell"):
                name = frontier_name(event.get("Type"))
                amount = 1 if et in ("MiningRefined", "CollectCargo") else quantity(event.get("Count"))
                sign = -1 if et in ("EjectCargo", "MarketSell") else 1
                vessel = "Ship" if et in ("MarketBuy", "MarketSell") else self.result.vessel
                leading_count = (previous_count and et in ("MiningRefined", "CollectCargo")
                    and previous_count["vessel"] == vessel
                    and previous_count["journal"] == source[0]
                    and previous_count["timestamp"] == event.get("timestamp"))
                if leading_count:
                    base = previous_count["stock"]
                    if base is not None:
                        base[name] = base.get(name, 0) + 1
                    snapshot = previous_count["snapshot"]
                    # Reconcile only the exact one-tonne, same-second sequence.
                    # A full snapshot must also agree on commodity composition.
                    if (base is not None and sum(base.values()) == previous_count["count"]
                            and (snapshot is None or {k:v for k,v in snapshot.items() if v}
                                 == {k:v for k,v in base.items() if v})):
                        self.stocks[vessel] = base
                    else:
                        self.stocks[vessel] = None
                else:
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
            elif et in ("ShipyardSwap", "ShipyardBuy", "ShipyardNew"):
                self.stocks = {"Ship": None, "SRV": None}
                self.ship_id = event.get("NewShipID") if et == "ShipyardNew" else event.get("ShipID")
                self.ship_type = None
                self.srv_id = None
            elif et in ("CargoDepot", "SearchAndRescue",
                        "CarrierDepositFuel", "EjectTacticalCore", "PowerplayCollect", "PowerplayDeliver",
                        "PowerplayFastTrack", "Resurrect"):
                # These can change cargo through additional rules. Wait for Cargo
                # rather than displaying an incomplete arithmetic reconstruction.
                self.stocks[self.result.vessel] = None
        except (ValueError, TypeError, AttributeError):
            self.stocks = {"Ship": None, "SRV": None}
        self.result.srv = deepcopy(self.stocks["SRV"])
        self.result.ship = deepcopy(self.stocks["Ship"])
        self.result.ship_id = self.ship_id
        self.result.ship_type = self.ship_type
        for vessel, stock in self.stocks.items():
            record = self.result.vehicle_records.setdefault(vessel, {})
            record["status"] = "known" if stock is not None else "unknown"
            if stock is None:
                record["quality"] = "stale" if "last_confirmed" in record else "unknown"
            elif stock != before[vessel] or (et == "Cargo" and event.get("Vessel", "").casefold() == vessel.casefold()):
                full = et == "Cargo" and validated_cargo(event, self.result.fid) is not None
                record["quality"] = "confirmed" if full else "tracked"
                record.update(last_confirmed=deepcopy(stock), source=list(source),
                              confirmed_at=event.get("timestamp", ""), ship_id=self.ship_id,
                              ship_type=self.ship_type, source_folder=folder)


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
        sessions = [dict(row) for row in sessions]
        folders = {str(Path(row["journal_file"]).resolve().parent) for row in sessions
                   if row.get("commander_id") == commander_id and row.get("fid_seen") == fid}
        folder = str(live_path.parent) if live_path else next(iter(folders)) if len(folders) == 1 else None
        if folder is None:
            return reducer.result  # No selected source and multiple candidate instances.
        sessions = [row for row in sessions if str(Path(row["journal_file"]).resolve().parent) == folder]
        reducer.result.source_folder = folder
        histories = saved.get("histories", {})
        if not isinstance(histories, dict):
            histories = {}
        history = saved.get("continuity", {})
        if folder in histories:
            history = histories[folder]
        if not isinstance(history, dict) or history.get("fid") != fid or history.get("version") != 1:
            history = {}
        old_records = history.get("vehicles", {})
        if not isinstance(old_records, dict):
            old_records = {}
        old_records = {v: r for v, r in old_records.items() if isinstance(r, dict)
                       and isinstance(r.get("source"), list) and len(r["source"]) == 2
                       and isinstance(r["source"][0], str)
                       and str(Path(r["source"][0]).resolve().parent) == folder}
        archive = saved.get("snapshots", {})
        if not isinstance(archive, dict):
            archive = {}
        # Bound both versions and retained contexts; old contexts are evicted as
        # a unit, never combined with another ship/source to create a baseline.
        archive = {k: [entry for entry in v if isinstance(entry, dict)][-10:]
                   for k, v in list(archive.items())[-32:] if isinstance(v, list)}
        saved["snapshots"] = archive
        candidates = [entry for entries in archive.values() for entry in entries]
        candidates += [saved.get("Ship"), saved.get("SRV")]  # Legacy migration.
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
                checkpoint = next((c for c in candidates if isinstance(c, dict)
                    and c.get("fid") == fid and c.get("source") == [str(path), offset]
                    and c.get("trigger") == fingerprint
                    and ("context" not in c or c["context"] == [folder, fid, reducer.ship_id,
                         vessel, reducer.srv_id if vessel == "SRV" else None])), None)
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
            if event.get("event") == "Cargo" and validated_cargo(event, fid) is not None:
                vessel = event.get("Vessel")
                context = [folder, fid, reducer.ship_id, vessel, reducer.srv_id if vessel == "SRV" else None]
                # Unknown vehicle identity is still replayable at its exact
                # trigger, but kept in its own non-transferable context.
                key = json.dumps(context, separators=(",", ":"))
                entry = dict(fid=fid, source=[str(path), offset],
                    trigger=hashlib.sha256(json.dumps(original, sort_keys=True).encode()).hexdigest(),
                    payload=deepcopy(event), context=context, timestamp=event.get("timestamp", ""))
                if isinstance(saved.get(vessel), dict) and saved[vessel].get("source") == entry["source"]:
                    saved[vessel] = deepcopy(entry)
                versions = archive.pop(key, [])
                versions = [c for c in versions if isinstance(c, dict) and c.get("source") != entry["source"]]
                archive[key] = (versions + [entry])[-10:]
                while len(archive) > 32:
                    archive.pop(next(iter(archive)))
            if pending_vessel in ("Ship", "SRV"):
                # Retain last_confirmed diagnostics, never label an older
                # same-total composition as the new authoritative snapshot.
                if reducer.corroborated_count:
                    reducer.result.cargo_pending = False
                else:
                    reducer.stocks[pending_vessel] = None
                    setattr(reducer.result, pending_vessel.lower(), None)
                    reducer.result.vehicle_records[pending_vessel]["status"] = "pending"
                    reducer.result.vehicle_records[pending_vessel]["quality"] = "stale"
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
                                   ("last_confirmed", "source", "confirmed_at", "ship_id", "ship_type", "source_folder") if k in old})
        saved["continuity"] = dict(version=1, fid=fid, vehicles=deepcopy(reducer.result.vehicle_records))
        histories.pop(folder, None)
        histories[folder] = deepcopy(saved["continuity"])
        saved["histories"] = dict(list(histories.items())[-32:])
        # Legacy aliases may reference retained versions, never become an
        # eleventh copy or keep an evicted context alive outside the limit.
        retained = [entry for entries in archive.values() for entry in entries]
        for vessel in ("Ship", "SRV"):
            alias = saved.get(vessel)
            if isinstance(alias, dict) and "context" in alias:
                if not any(entry.get("source") == alias.get("source")
                           and entry.get("trigger") == alias.get("trigger") for entry in retained):
                    saved.pop(vessel, None)
        reducer.result.checkpoints = saved
        return reducer.result
