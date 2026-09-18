"""Read-only presentation of confirmed cargo for the current Status vehicle."""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import math

from cmdrhelper.i18n import tr
from cmdrhelper.ship_identity import is_definite_non_ship
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
    """Prefer confirmed vehicle cargo; Status may supply only a ship HUD total."""
    snapshot = getattr(state, "cargo_snapshot", None)
    fid = str(getattr(state, "commander_fid", "") or "").strip()
    folder = getattr(state, "journal_folder", None)
    if not fid or not folder:
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
    except (OSError, ValueError, TypeError, OverflowError):
        return None
    # On foot, taxi, multicrew and fighters have no own cargo context here.
    if flags2 & 0b111 or flags & (1 << 25):
        return None
    in_ship, in_srv = bool(flags & (1 << 24)), bool(flags & (1 << 26))
    if in_ship == in_srv:
        return None
    # A newer confirmed snapshot proves that Status is still behind. Do not
    # bypass this existing safety boundary via the display-only fallback.
    if isinstance(snapshot, dict) and snapshot.get("fid") == fid:
        try:
            if timestamp < utc_timestamp(snapshot.get("timestamp")):
                return None
        except (ValueError, TypeError, OverflowError):
            pass  # An unusable snapshot may still allow independently verified Status.
    vessel = "Ship" if in_ship else "SRV"
    confirmed = _confirmed_cargo(state, snapshot, fid, status, timestamp, vessel)
    if confirmed is not None:
        return confirmed
    if in_ship:
        return _status_ship_cargo(state, status, timestamp, fid)
    return None


def _confirmed_cargo(state, snapshot, fid, status, timestamp, vessel):
    if not isinstance(snapshot, dict) or snapshot.get("fid") != fid:
        return None
    used = snapshot.get("count")
    if type(used) is not int or used < 0 or snapshot.get("vessel") != vessel:
        return None
    try:
        if timestamp < utc_timestamp(snapshot.get("timestamp")):
            return None
    except (ValueError, TypeError, OverflowError):
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
    name = str(name or "").strip() or tr("cargo.hud.ship" if vessel == "Ship" else "cargo.hud.srv")
    return CargoHudData(name, used, capacity)


def _status_ship_cargo(state, status, timestamp, fid):
    """Display-only total: no inventory, writes, or additional journal/DB reads.

    Status carries no FID or ShipID. Require the current identified journal
    session and a complete, non-stale Loadout from that session. Status must
    postdate that Loadout. Foreground/running-game gating remains in the HUD.
    """
    sessions = getattr(state, "_journal_index_sessions", None) or []
    session = sessions[-1] if sessions else None
    commander_id = getattr(state, "commander_id", None)
    loadout = getattr(state, "ship_loadout", None)
    if (not isinstance(session, dict) or commander_id is None
            or session.get("attribution_status") != "identified"
            or session.get("commander_id") != commander_id
            or session.get("fid_seen") != fid
            or loadout is None or type(loadout.ship_id) is not int or loadout.ship_id < 0
            or not loadout.loadout_complete or loadout.loadout_stale
            or not loadout.ship_type or is_definite_non_ship(loadout.ship_type)
            or not getattr(state, "ship", "") or getattr(state, "active_srv_type", "")):
        return None
    try:
        session_start = utc_timestamp(session.get("first_event_at"))
        loadout_time = utc_timestamp(loadout.loadout_timestamp)
        # LoadGame can start a new game within the same journal file.
        game_start = getattr(state, "game_mode_timestamp", "")
        if game_start:
            session_start = max(session_start, utc_timestamp(game_start))
        if not session_start <= loadout_time <= timestamp:
            return None
    except (ValueError, TypeError, OverflowError):
        return None
    capacity = loadout.cargo_capacity
    used = status.get("Cargo")
    if (type(capacity) is not int or capacity < 0
            or type(used) not in (int, float)
            or (type(used) is float and (not math.isfinite(used) or not used.is_integer()))
            or not 0 <= used <= capacity):
        return None
    name = str(loadout.ship_name or state.ship or loadout.ship_type).strip()
    return CargoHudData(name, int(used), capacity)
