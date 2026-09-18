"""Confirmed ownership facts from Frontier Journal Manual v37, §§8.44/47–53."""
from datetime import datetime, timezone

from cmdrhelper.route_planner.models import ShipLoadoutData
from cmdrhelper.ship_identity import is_definite_non_ship

SALE_ID_FIELDS = {
    "ShipyardSell": "SellShipID",
    "SellShipOnRebuy": "SellShipId",
    "ShipyardBuy": "SellShipID",
    "ShipyardSwap": "SellShipID",
}


def journal_time(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    except (ValueError, TypeError, OverflowError):
        return None


def ship_sale(event):
    field = SALE_ID_FIELDS.get(event.get("event"))
    sid = event.get(field) if field else None
    if type(sid) is not int or sid < 0:
        return None
    timestamp = journal_time(event.get("timestamp"))
    if timestamp is None:
        return None
    return {"ship_id": sid, "sold_at": timestamp, "event_type": event["event"]}


def stored_ship_observations(event):
    """Presence is evidence; absence from these lists is never a sale."""
    for field in ("ShipsHere", "ShipsRemote"):
        for item in event.get(field) or []:
            sid = item.get("ShipID")
            if type(sid) is not int or sid < 0 or is_definite_non_ship(item.get("ShipType")):
                continue
            location = {}
            if field == "ShipsHere":
                location = {"system_name": event.get("StarSystem", ""),
                            "station_name": event.get("StationName", "")}
            elif not item.get("InTransit"):
                location = {"system_name": item.get("StarSystem", "")}
            yield ShipLoadoutData(ship_id=sid, ship_type=item.get("ShipType"),
                                  ship_name=item.get("Name")), location
