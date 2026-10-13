"""Read-only presentation of confirmed cargo for the current Status vehicle."""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import time
from PySide6.QtCore import QObject, Qt, QTimer, Signal

from cmdrhelper.i18n import tr
from cmdrhelper.status_reader import read_status_data, utc_timestamp


class CargoVisibility(QObject):
    """Shared inactivity policy; polling/duplicate snapshots are not activity."""
    expired = Signal()

    def __init__(self, parent, expired):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(15000)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self._expire)
        self.expired.connect(expired)
        self.key = None
        self.active = False
        self.manual = False

    def observe(self, key, *, manual=False):
        changed = key != self.key
        self.key = key
        if manual:
            self.manual = self.active = True
            self.timer.stop()
        elif changed:
            self.active = True
            if not self.manual:
                self.timer.start()

    def close(self):
        self.timer.stop()
        self.manual = self.active = False

    def reset(self):
        self.close()
        self.key = None

    def _expire(self):
        if not self.manual:
            self.timer.stop()
            self.active = False
            self.expired.emit()


def _session_key(context):
    return tuple((context or {}).get(key) for key in
                 ("fid", "journal", "session_start", "session_generation", "vessel"))


def cargo_activity_key(snapshot):
    """Inventory identity/quantities, excluding timestamps and translated labels."""
    if not isinstance(snapshot, dict):
        return None
    return (_session_key(snapshot.get("context")),
            snapshot.get("fid"), snapshot.get("vessel"), snapshot.get("ship_id"),
            snapshot.get("vehicle_name"), snapshot.get("count"),
            tuple(sorted((str(item.get("frontier_name") or "").casefold(),
                          int(item.get("count") or 0), int(item.get("stolen") or 0))
                         for item in snapshot.get("inventory") or [])))


def same_cargo_context(state, snapshot):
    """A missing sidecar may retain presentation, never inventory for computation.

    Generation changes on every cargo mutation; session/vehicle identity must
    nevertheless remain exact. Unknown/reset contexts cannot retain anything.
    """
    if not isinstance(snapshot, dict):
        return False
    origin = snapshot.get("context") or {}
    current = getattr(state, "ship_cargo_context", None) or {}
    pending = getattr(state, "_cargo_refresh_data", None)
    session = pending[1] if pending else None
    if not isinstance(session, dict) or not current.get("active"):
        return False
    identity = ("fid", "journal", "session_start", "session_generation", "vessel")
    if (any(origin.get(k) is None or origin[k] != current.get(k) for k in identity)
            or snapshot.get("fid") != origin.get("fid")
            or origin.get("fid") != getattr(state, "commander_fid", None)
            or session.get("attribution_status") != "identified"
            or session.get("commander_id") is None
            or session.get("fid_seen") != origin.get("fid")
            or session.get("journal_file") != origin.get("journal")):
        return False
    if snapshot.get("vessel") == "Ship":
        ship_id = getattr(getattr(state, "ship_loadout", None), "ship_id", None)
        return ship_id is not None and snapshot.get("ship_id") == current.get("ship_id") == ship_id
    return (snapshot.get("vessel") == "SRV" and snapshot.get("vehicle_name")
            == getattr(state, "active_srv_type", None))


def cargo_item_name(item):
    """Keep journal localization; resolve raw identifiers via the offline catalog."""
    from cmdrhelper.commodities import commodity_key, commodity_name
    from cmdrhelper.commodity_master import lookup_by_symbol
    from cmdrhelper.commodity_localization import commodity_name as catalog_name
    if item.get("is_drones"):
        return tr("cargo.live.drones")
    raw = str(item.get("frontier_name") or "")
    label = str(item.get("display_name") or "")
    if label and commodity_key(label) != commodity_key(raw):
        return label
    definition = lookup_by_symbol(raw)
    return catalog_name(definition) if definition else commodity_name(raw, label) or "–"


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


class CargoHudPresentation:
    """Briefly retain a verified value during Status lag, never across contexts."""

    def __init__(self, state):
        self.state = state
        self.data = None
        self.context = None
        self.status_time = None
        self.verified_at = 0.0
        self.snapshot = None

    def __call__(self):
        data = cargo_hud_data(self.state, _presentation=self)
        if data is None:
            self.data = None
        return data

    def remember(self, data, context, timestamp):
        self.data, self.context, self.status_time = data, context, timestamp
        self.verified_at = time.monotonic()
        self.snapshot = getattr(self.state, "cargo_snapshot", None)
        return data

    def pending(self):
        return (self.data is not None and time.monotonic() - self.verified_at <= 15
                and self.context[1] == str(getattr(self.state, "journal_folder", None))
                and same_cargo_context(self.state, self.snapshot))

    def activity_key(self):
        snapshot = getattr(self.state, "cargo_snapshot", None)
        if snapshot is None and self.pending():
            snapshot = self.snapshot
        return cargo_activity_key(snapshot)


def cargo_hud_data(state, *, _presentation=None):
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
        if _presentation is not None and _presentation.pending():
            return _presentation.data
        return None
    # On foot, taxi, multicrew and fighters have no own cargo context here.
    if flags2 & 0b111 or flags & (1 << 25):
        return None
    in_ship, in_srv = bool(flags & (1 << 24)), bool(flags & (1 << 26))
    if in_ship == in_srv:
        return None
    vessel = "Ship" if in_ship else "SRV"
    loadout = getattr(state, "ship_loadout", None)
    context = (fid, str(folder), vessel, getattr(loadout, "ship_id", None),
               getattr(state, "active_srv_type", ""),
               _session_key(snapshot.get("context") if isinstance(snapshot, dict)
                            else getattr(state, "ship_cargo_context", None)))
    if (snapshot is None and _presentation is not None and _presentation.pending()
            and _presentation.context == context and _presentation.status_time is not None
            and timestamp >= _presentation.status_time):
        return _presentation.data
    # Keep only an already verified presentation during a monotonic Status lag.
    # Never accept the new amount with old Status or carry it across vehicles.
    if isinstance(snapshot, dict) and snapshot.get("fid") == fid:
        try:
            if timestamp < utc_timestamp(snapshot.get("timestamp")):
                if (_presentation is not None and _presentation.data is not None
                        and _presentation.context == context
                        and time.monotonic() - _presentation.verified_at <= 15
                        and _presentation.status_time is not None
                        and timestamp >= _presentation.status_time
                        and _confirmed_cargo(state, snapshot, fid, status,
                            utc_timestamp(snapshot.get("timestamp")), vessel) is not None):
                    return _presentation.data
                return None
        except (ValueError, TypeError, OverflowError):
            pass  # An unusable snapshot may still allow independently verified Status.
    confirmed = _confirmed_cargo(state, snapshot, fid, status, timestamp, vessel)
    if confirmed is None and in_ship:
        confirmed = _status_ship_cargo(state, status, timestamp, fid)
    if confirmed is not None and _presentation is not None:
        return _presentation.remember(confirmed, context, timestamp)
    return confirmed


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
    """Share the validated total fallback with trading, never its inventory."""
    from cmdrhelper.ship_cargo import status_ship_count
    used = status_ship_count(state, status)
    if used is None:
        return None
    loadout = state.ship_loadout
    name = str(loadout.ship_name or state.ship or loadout.ship_type).strip()
    return CargoHudData(name, used, loadout.cargo_capacity)
