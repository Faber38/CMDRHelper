"""Read complete Status.json snapshots without inheriting any prior fields."""
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path

from cmdrhelper.planet_geometry import heading360


class StatusError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def utc_timestamp(value):
    if not isinstance(value, str):
        raise ValueError("Missing timestamp")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("Timestamp without timezone")
    return result.astimezone(timezone.utc)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


@dataclass(frozen=True)
class StatusSnapshot:
    timestamp: datetime
    mtime_ns: int
    latitude: float
    longitude: float
    heading: float
    radius_m: float
    body_name: str
    flags: int
    flags2: int


def parse_status(data, mtime_ns=0, now=None):
    """Validate planetary telemetry independently of flight phase or vehicle.

    Supercruise (Flags bit 4) deliberately does not block coordinates: Frontier
    supplies planetary positions already during the approach, before glide.
    """
    if not isinstance(data, dict) or data.get("event") != "Status":
        raise StatusError("invalid_status")
    flags, flags2 = data.get("Flags"), data.get("Flags2", 0)
    if any(type(v) is not int or v < 0 for v in (flags, flags2)):
        raise StatusError("invalid_status")
    if flags & (1 << 30):
        raise StatusError("hyperspace")
    if not flags & (1 << 21):
        raise StatusError("no_coordinates")
    try:
        timestamp = utc_timestamp(data.get("timestamp"))
        values = [data.get(k) for k in ("Latitude", "Longitude", "Heading", "PlanetRadius")]
        if not all(type(v) in (int, float) and math.isfinite(v) for v in values):
            raise ValueError("Missing or invalid number")
        latitude, longitude, heading, radius = values
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180 and radius > 0):
            raise ValueError("Out of range")
        name = data.get("BodyName")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Missing body")
        if (timestamp - (now or datetime.now(timezone.utc))).total_seconds() > 5:
            raise ValueError("Future timestamp")
    except (ValueError, TypeError, OverflowError) as exc:
        raise StatusError("invalid_status") from exc
    return StatusSnapshot(timestamp, mtime_ns, latitude, longitude,
                          heading360(heading), radius, name, flags, flags2)


def read_status_data(path: Path):
    """Shared complete-file read; consumers validate only their own telemetry."""
    try:
        before = path.stat()
        with path.open("rb") as handle:
            raw = handle.read(65537)
        after = path.stat()
        signature = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)
        if (len(raw) > 65536 or len(raw) != after.st_size
                or signature(before) != signature(after)):
            raise ValueError("Concurrent status write")
        data = json.loads(raw, object_pairs_hook=unique_object)
    except (OSError, ValueError) as exc:
        raise StatusError("invalid_status") from exc
    return data, after.st_mtime_ns


def read_status(path: Path):
    data, mtime_ns = read_status_data(path)
    return parse_status(data, mtime_ns)
