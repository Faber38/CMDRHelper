"""Observed carrier planning inputs, never a fuel simulator or inventory ledger."""
from dataclasses import dataclass, replace
from datetime import datetime, timezone

# Personal carrier profile, not values inferred from LoadGame's ship tanks.
# Sources and freshness policy: docs/carrier-route-inputs.md.
BASE_MASS = 25000
PERSONAL_CAPACITY = 25000
TANK_CAPACITY = 1000
MAX_AGE_SECONDS = 15 * 60
SPACE_FIELDS = ("Cargo", "Crew", "CargoSpaceReserved", "ShipPacks", "ModulePacks")


def quantity(value):
    return value if type(value) is int and value >= 0 else None


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo is not None else None
    except (ValueError, TypeError, AttributeError):
        return None


@dataclass(frozen=True)
class CarrierSnapshot:
    fid: str
    session: str
    carrier_id: int | None
    callsign: str
    carrier_type: str
    observed_at: str
    fuel: int | None
    capacity: int | None
    used: int | None
    cargo: int | None
    space: tuple[tuple[str, int | None], ...]
    invalidated: bool = False

    def usable(self, fid, session, now=None):
        observed = timestamp(self.observed_at)
        now = now or datetime.now(timezone.utc)
        return bool(not self.invalidated and self.fid and self.fid == fid
                    and self.session == session and self.carrier_id is not None
                    and self.callsign and self.carrier_type == "FleetCarrier"
                    and observed and 0 <= (now - observed).total_seconds() <= MAX_AGE_SECONDS)


def parse_snapshot(event, fid, session):
    space = event.get("SpaceUsage")
    space = space if isinstance(space, dict) else {}
    capacity, free = quantity(space.get("TotalCapacity")), quantity(space.get("FreeSpace"))
    parts = tuple((key, quantity(space.get(key))) for key in SPACE_FIELDS)
    used = capacity - free if capacity is not None and free is not None and free <= capacity else None
    # A partial breakdown cannot prove a sum, but even its known parts cannot
    # exceed the total. Never silently replace a contradictory snapshot.
    if used is not None and (any(key in space and value is None for key, value in parts)
            or sum(v for _, v in parts if v is not None) > used
            or all(v is not None for _, v in parts) and sum(v for _, v in parts) != used):
        used = None
    fuel = quantity(event.get("FuelLevel"))
    kind = str(event.get("CarrierType") or "")
    if kind == "FleetCarrier" and fuel is not None and fuel > TANK_CAPACITY:
        fuel = None
    carrier_id = quantity(event.get("CarrierID"))
    return CarrierSnapshot(fid, session, carrier_id if carrier_id else None,
                           str(event.get("Callsign") or ""), kind,
                           str(event.get("timestamp") or ""), fuel, capacity, used,
                           quantity(space.get("Cargo")), parts)


class CarrierInputTracker:
    """Feed through the existing attributed journal pass; no new journal reads."""
    def __init__(self):
        self.snapshot = None
        self.session = ""
        self.file = ""
        self.fid = ""
        self.revision = ""
        self._sequence = 0

    def apply(self, event, fid, journal):
        file = str(journal)
        kind = event.get("event")
        stamp = str(event.get("timestamp") or "")
        if (file, fid) != (self.file, self.fid):
            self.file, self.fid = file, fid
            self.session = file
            self.snapshot = None
            self.revision = file
            self._sequence = 0
        self._sequence += 1
        revision = f"{kind}:{stamp}:{self._sequence}"
        if kind in {"LoadGame", "Shutdown", "CarrierBuy", "CarrierDecommission"}:
            self.session = file + ":" + stamp
            self.snapshot = None
            self.revision = revision
        elif kind == "CarrierStats":
            candidate = parse_snapshot(event, fid, self.session)
            if (self.snapshot is not None and timestamp(candidate.observed_at)
                    and timestamp(self.snapshot.observed_at)
                    and timestamp(candidate.observed_at) < timestamp(self.snapshot.observed_at)):
                self.snapshot = replace(self.snapshot, invalidated=True)
            else:
                self.snapshot = candidate
            self.revision = revision
        elif kind in {"CarrierJump", "CarrierJumpRequest", "CarrierDepositFuel", "CargoTransfer",
                      "CarrierTradeOrder", "CarrierCrewServices", "CarrierShipPack", "CarrierModulePack",
                      "MarketBuy", "MarketSell", "CarrierNameChange", "CarrierNameChanged"}:
            # Invalidate rather than guessing stock deltas (donated fuel may
            # come from another player's ship). Conservative for trades/transfers.
            if self.snapshot is not None:
                self.snapshot = replace(self.snapshot, invalidated=True)
            self.revision = revision
