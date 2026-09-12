"""Commander-bound cargo projection; carrier stock deliberately remains unknown.

See docs/mining-inventory.md for the source audit and conservative boundaries.
Journal files are the durable event source. Only verified Cargo.json snapshots
need an additional QSettings checkpoint because Elite overwrites that sidecar.
"""
from copy import deepcopy
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path

from .cargo import cargo_snapshot, read_cargo_snapshot
from .journal_files import journal_sort_key
from .material_inventory import frontier_name, quantity

EVENTS = {"LoadGame", "ClearSavedGame", "Died", "Loadout", "LaunchSRV", "DockSRV",
          "SRVDestroyed", "Cargo", "MiningRefined", "CollectCargo", "EjectCargo", "MarketBuy",
          "MarketSell", "CargoTransfer", "BuyDrones", "SellDrones", "CargoDepot", "MissionCompleted",
          "EngineerContribution", "SearchAndRescue", "CarrierDepositFuel", "EjectTacticalCore",
          "PowerplayCollect", "PowerplayDeliver", "PowerplayFastTrack", "ShipyardSwap", "ShipyardBuy",
          "Resurrect", "_InvalidCargo"}


def total_stock(vehicle, carrier):
    return vehicle + carrier if vehicle is not None and carrier is not None else None


@dataclass
class MiningInventory:
    commander_id: int
    fid: str
    vessel: str = "Ship"
    vehicle: dict | None = None
    carrier: dict | None = None
    checkpoints: dict = field(default_factory=dict)
    snapshot_verified: bool = False  # Read diagnostics only; never affects cargo reconstruction.
    carrier_id: int | None = None
    carrier_feed: dict | None = field(default=None, repr=False)
    carrier_records: dict = field(default_factory=dict)

    def stock(self, symbol):
        vehicle = self.vehicle.get(symbol, 0) if self.vehicle is not None else None
        carrier = self.carrier.get(symbol, 0) if self.carrier is not None else None
        return vehicle, carrier, total_stock(vehicle, carrier)


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
            if et in ("LoadGame", "ClearSavedGame", "Died", "_InvalidCargo"):
                self.stocks = {"Ship": None, "SRV": None}
                self.result.vessel = ("SRV" if str(event.get("Ship", "")).casefold()
                                      in ("mev_rhino", "testbuggy", "combat_multicrew_srv_01") else "Ship")
                self.ship_id = event.get("ShipID")
            elif et == "Loadout":
                if event.get("ShipID") is not None and str(event.get("Ship", "")).casefold() not in (
                        "mev_rhino", "testbuggy", "combat_multicrew_srv_01"):
                    if self.ship_id is not None and event["ShipID"] != self.ship_id:
                        self.stocks = {"Ship": None, "SRV": None}
                    self.ship_id = event["ShipID"]
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
        self.result.vehicle = deepcopy(self.stocks[self.result.vessel])


class MiningInventoryReader:
    def __init__(self):
        self._cache = {}

    def _read(self, path):
        stat = path.stat()
        signature = (stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
        old = self._cache.get(path)
        if old and old[0] == signature:
            return old[1]
        events, identities = [], set()
        with path.open("rb") as stream:
            while True:
                offset = stream.tell()
                line = stream.readline()
                if not line or not line.endswith(b"\n"):
                    break
                try:
                    event = json.loads(line)
                    if not isinstance(event, dict):
                        raise ValueError("invalid event")
                    if event.get("event") in ("Commander", "LoadGame") and event.get("FID"):
                        identities.add(event["FID"])
                except (ValueError, TypeError):
                    event = {"event": "_InvalidCargo"}
                if event.get("event") in EVENTS:
                    events.append((offset, event))
        after = path.stat()
        if signature != (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise OSError("journal changed during cargo reconstruction")
        self._cache[path] = (signature, (identities, events))
        return identities, events

    def reconstruct(self, commander_id, fid, sessions, *, checkpoints=None, live_path=None):
        reducer = MiningReducer(commander_id, fid)
        saved = deepcopy(checkpoints) if isinstance(checkpoints, dict) else {}
        events = []
        paths = {}
        for raw in sessions:
            row = dict(raw)
            path = Path(row["journal_file"]).resolve()
            paths.setdefault(path, []).append(row)
        for path in sorted(paths, key=journal_sort_key):
            rows = paths[path]
            if any(row.get("commander_id") != commander_id or row.get("fid_seen") != fid
                   or row.get("attribution_status") != "identified" for row in rows):
                continue
            try:
                identities, facts = self._read(path)
                if identities != {fid}:
                    events.append((path, -1, {"event": "_InvalidCargo"}))
                    continue
                events.extend((path, offset, event) for offset, event in facts)
            except OSError:
                events.append((path, -1, {"event": "_InvalidCargo"}))
        latest = next(((path, offset) for path, offset, e in reversed(events) if e.get("event") == "Cargo"), None)
        for path, offset, original in events:
            event = original
            is_live_snapshot = bool(live_path and path == Path(live_path).resolve()
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
                if live_path and path == Path(live_path).resolve() and (path, offset) == latest:
                    snapshot = read_cargo_snapshot(path.parent / "Cargo.json", original,
                                                   fid=fid, attempts=2, retry_delay=0.04)
                    if snapshot is not None:
                        reducer.result.snapshot_verified = True
                        event = {**original, "Inventory": [
                            {"Name": item["frontier_name"], "Count": item["count"]}
                            for item in snapshot["inventory"]]}
                        saved[vessel] = dict(fid=fid, source=[str(path), offset], trigger=fingerprint, payload=event)
            reducer.apply(event, (str(path), offset))
        reducer.result.checkpoints = saved
        return reducer.result
