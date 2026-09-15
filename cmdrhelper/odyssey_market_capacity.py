"""Read-only bartender reservation information; never changes private stock."""
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path


def timestamp(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timezone required")
    return result


@dataclass(frozen=True)
class MarketReservation:
    reserved: int
    observed_at: datetime

    def occupancy(self, stock):
        return stock + self.reserved


def read_reservation(folder, carrier_id):
    """MarketID is numeric; CarrierID in FCMaterials is only a callsign.

    Demand is outstanding buying quantity. Stock is offered existing stock,
    never additional occupancy. CarrierTradeOrder fields are not snapshots.
    A returned value describes the dated file, not guaranteed live market data.
    """
    if not folder or type(carrier_id) is not int or carrier_id <= 0:
        return None
    try:
        path = Path(folder) / "FCMaterials.json"
        before = path.stat()
        raw = path.read_bytes()
        after = path.stat()
        signature = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        if signature(before) != signature(after):
            return None
        data = json.loads(raw)
        if (data.get("event") != "FCMaterials" or type(data.get("MarketID")) is not int
                or data["MarketID"] != carrier_id or not isinstance(data.get("Items"), list)):
            return None
        observed = timestamp(data["timestamp"])
        if observed > datetime.now(timezone.utc):
            return None
        seen, reserved = set(), 0
        for row in data["Items"]:
            name = row["Name"]
            if not isinstance(name, str) or not name.strip() or name in seen:
                return None
            seen.add(name)
            for field in ("Demand", "Stock"):
                if type(row.get(field)) is not int or row[field] < 0:
                    return None
            reserved += row["Demand"]
        return MarketReservation(reserved, observed)
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return None


def usable_with_inventory(reservation, inventory):
    """Do not combine older market information with a newer stock anchor."""
    if reservation is None:
        return False
    anchors = [inventory.reconstructed_at]
    anchors.extend(r.get("confirmed_at") for r in inventory.carrier_records.values())
    try:
        times = [timestamp(t) for t in anchors if t]
        return bool(times) and reservation.observed_at >= max(times)
    except (ValueError, TypeError, AttributeError):
        return False
