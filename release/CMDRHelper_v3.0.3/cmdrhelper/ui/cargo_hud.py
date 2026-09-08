"""Read-only presentation of confirmed cargo for the current Status vehicle."""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from cmdrhelper.i18n import tr
from cmdrhelper.status_reader import read_status_data, utc_timestamp


def cargo_hud_enabled(settings):
    value = settings.value("cargo_hud/enabled", False)
    return value.strip().lower() in ("1", "true", "yes", "on") if isinstance(value, str) else bool(value)


def cargo_fill_fraction(used, capacity):
    if type(used) is not int or type(capacity) is not int or capacity <= 0:
        return None
    return max(0, min(used, capacity)) / capacity


@dataclass(frozen=True)
class CargoHudData:
    vehicle_name: str
    used: int
    capacity: int | None

    @property
    def fraction(self):
        return cargo_fill_fraction(self.used, self.capacity)

    @property
    def text(self):
        amount = (f"{self.used} / {self.capacity} t" if self.capacity is not None
                  else tr("cargo.live.loaded", count=self.used))
        return tr("cargo.hud.summary", vehicle=self.vehicle_name,
                  cargo=tr("cargo.hud.label").upper(), amount=amount)


def cargo_hud_data(state):
    """Never cache inventory or infer transfers from material/journal events.

    Status flags gate the confirmed snapshot during vehicle transitions. Ship
    loadout capacity/name are used only after matching the snapshot's ship ID.
    Flag definitions: EDCD/EDMarketConnector edmc_data.py (Dashboard constants).
    """
    snapshot = getattr(state, "cargo_snapshot", None)
    fid = str(getattr(state, "commander_fid", "") or "").strip()
    folder = getattr(state, "journal_folder", None)
    if not isinstance(snapshot, dict) or not fid or snapshot.get("fid") != fid or not folder:
        return None
    used = snapshot.get("count")
    if type(used) is not int or used < 0:
        return None
    try:
        status, _ = read_status_data(Path(folder) / "Status.json")
        if not isinstance(status, dict) or status.get("event") != "Status":
            return None
        flags, flags2 = status.get("Flags"), status.get("Flags2", 0)
        if any(type(v) is not int or v < 0 for v in (flags, flags2)):
            return None
        timestamp = utc_timestamp(status.get("timestamp"))
        if (timestamp - datetime.now(timezone.utc)).total_seconds() > 5:
            return None
        # Never combine an old session's status with newer confirmed cargo.
        if timestamp < utc_timestamp(snapshot.get("timestamp")):
            return None
    except (OSError, ValueError, TypeError, OverflowError):
        return None
    # On foot, taxi, multicrew and fighters have no own cargo context here.
    if flags2 & 0b111 or flags & (1 << 25):
        return None
    in_ship, in_srv = bool(flags & (1 << 24)), bool(flags & (1 << 26))
    if in_ship == in_srv:
        return None
    vessel = "Ship" if in_ship else "SRV"
    if snapshot.get("vessel") != vessel:
        return None
    capacity = snapshot.get("capacity")
    if vessel == "Ship":
        loadout = getattr(state, "ship_loadout", None)
        if (snapshot.get("ship_id") is None or loadout is None
                or snapshot["ship_id"] != loadout.ship_id):
            return None
        if loadout.cargo_capacity is not None:
            capacity = loadout.cargo_capacity
        name = loadout.ship_name or getattr(state, "ship", "") or loadout.ship_type
    else:
        name = snapshot.get("vehicle_name")
        active_name = getattr(state, "active_srv_type", name)
        if str(active_name or "").strip().casefold() != str(name or "").strip().casefold():
            return None
    # An explicitly reported capacity for the verified active vehicle wins.
    reported_capacity = status.get("CargoCapacity")
    if type(reported_capacity) is int and reported_capacity >= 0:
        capacity = reported_capacity
    if type(capacity) is not int or capacity < 0:
        capacity = None
    name = str(name or "").strip() or tr("cargo.hud.ship" if in_ship else "cargo.hud.srv")
    return CargoHudData(name, used, capacity)
