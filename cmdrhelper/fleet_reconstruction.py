"""Read-only fleet reconstruction; deliberately no cross-domain import calls."""
import copy
import json
from pathlib import Path

from cmdrhelper.journal_files import journal_sort_key
from cmdrhelper.journal_reader import _loadout_from_event, _optional_int
from cmdrhelper.route_planner.models import ShipLoadoutData
from cmdrhelper.ship_identity import is_definite_non_ship
from cmdrhelper.ship_ownership import journal_time, ship_sale, stored_ship_observations

FLEET_EVENTS = {
    "LoadGame", "Loadout", "ShipyardSwap", "ShipyardBuy", "ShipyardNew", "SetUserShipName",
    "ShipyardSell", "SellShipOnRebuy", "StoredShips",
    "Location", "FSDJump", "CarrierJump", "Docked", "Undocked",
    "ModuleBuy", "ModuleSell", "ModuleSwap", "ModuleStore", "ModuleRetrieve",
    "MassModuleStore", "MassModuleRetrieve", "EngineerCraft",
}


class FleetReconstruction(list):
    def __init__(self, ships, sales):
        super().__init__(ships)
        self.sales = sales


def reconstruct_fleet(paths, fid):
    all_events = []
    for path in sorted({Path(p) for p in paths}, key=journal_sort_key):
        events, identities = [], set()
        before = path.stat()
        with path.open("rb") as handle:
            for line in handle:
                if not line.endswith(b"\n"):
                    break  # An incomplete live tail is not an event.
                event = json.loads(line)
                if event.get("event") in ("Commander", "LoadGame") and event.get("FID"):
                    identities.add(str(event["FID"]))
                if event.get("event") in FLEET_EVENTS:
                    events.append(event)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise OSError("Journal changed while reading; retry required")
        if identities != {fid}:
            continue
        all_events.extend(events)
    # Timestamp order also covers rotated/copied journals whose names differ
    # from their event chronology; the stable sort preserves equal-time order.
    all_events.sort(key=lambda event: journal_time(event.get("timestamp")) or "")
    return _reconstruct_events(all_events)


def _reconstruct_events(events):
    fleet, sales = {}, {}
    loadout = ShipLoadoutData()
    location = {}
    away = False
    for event in events:
        kind = event["event"]
        timestamp = str(event.get("timestamp") or "")
        sale = ship_sale(event)
        if sale is not None:
            sid = sale["ship_id"]
            if sid not in sales or sale["sold_at"] > sales[sid]["sold_at"]:
                sales[sid] = sale
            if (journal_time(fleet.get(sid, {}).get("last_seen")) or "") <= sales[sid]["sold_at"]:
                fleet.pop(sid, None)
                if loadout.ship_id == sid:
                    loadout = ShipLoadoutData()
        if kind in ("ShipyardSell", "SellShipOnRebuy"):
            continue
        if kind == "StoredShips":
            for stored, stored_location in stored_ship_observations(event):
                sid = stored.ship_id
                if sid in sales and (journal_time(timestamp) or "") <= sales[sid]["sold_at"]:
                    continue
                previous = fleet.get(sid, {})
                known = copy.deepcopy(previous.get("loadout") or stored)
                known.ship_type = stored.ship_type or known.ship_type
                known.ship_name = stored.ship_name or known.ship_name
                fleet[sid] = {"loadout": known, "location": stored_location or previous.get("location"),
                    "first_seen": previous.get("first_seen") or timestamp, "last_seen": timestamp,
                    "is_current": previous.get("is_current", False)}
            continue
        if kind in ("Location", "FSDJump", "CarrierJump", "Docked"):
            location = {
                "system_name": event.get("StarSystem") or location.get("system_name", ""),
                "system_address": event.get("SystemAddress", location.get("system_address")),
                "station_name": event.get("StationName", ""),
            }
        elif kind == "Undocked":
            location["station_name"] = ""
            continue
        elif kind in ("LoadGame", "ShipyardSwap", "ShipyardBuy", "ShipyardNew"):
            ship_type = event.get("Ship") or event.get("ShipType")
            if is_definite_non_ship(ship_type, event.get("Ship_Localised")):
                away = True
                continue
            sid = _optional_int(event.get("NewShipID") if kind == "ShipyardNew" else event.get("ShipID"))
            if sid is None:
                continue
            if sid != loadout.ship_id:
                loadout = copy.deepcopy(fleet[sid]["loadout"]) if sid in fleet else ShipLoadoutData(ship_id=sid)
            loadout.ship_type = ship_type or loadout.ship_type
            loadout.ship_name = event.get("ShipName") or loadout.ship_name
            loadout.ship_ident = event.get("ShipIdent") or loadout.ship_ident
            away = False
        elif kind == "Loadout":
            if is_definite_non_ship(event.get("Ship")):
                continue
            loadout = _loadout_from_event(event, loadout)
            away = False
        elif kind == "SetUserShipName":
            if event.get("ShipID") != loadout.ship_id:
                continue
            loadout.ship_name = event.get("UserShipName") or loadout.ship_name
            loadout.ship_ident = event.get("UserShipId") or loadout.ship_ident
        else:
            if event.get("ShipID") not in (None, loadout.ship_id):
                continue
            loadout.loadout_stale = True
        if away or loadout.ship_id is None:
            continue
        if loadout.ship_id in sales and (journal_time(timestamp) or "") <= sales[loadout.ship_id]["sold_at"]:
            continue
        previous = fleet.get(loadout.ship_id, {})
        fleet[loadout.ship_id] = {
            "loadout": copy.deepcopy(loadout), "location": dict(location),
            "first_seen": previous.get("first_seen") or timestamp,
            "last_seen": timestamp, "is_current": True,
        }
        for sid, item in fleet.items():
            item["is_current"] = sid == loadout.ship_id
    return FleetReconstruction(fleet.values(), sales)
