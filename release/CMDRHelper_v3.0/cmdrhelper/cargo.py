from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import time


def _timestamp(value):
    try:
        return datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
    except ValueError:
        return None


def normalize_inventory(items) -> list[dict]:
    """Combine Frontier commodity names case-insensitively."""
    merged = {}
    order = []
    for raw in items or []:
        if not isinstance(raw, dict):
            continue
        frontier_name = str(raw.get("Name") or "").strip()
        key = frontier_name.casefold()
        if not key:
            continue
        try:
            count = max(0, int(raw.get("Count") or 0))
            stolen = max(0, int(raw.get("Stolen") or 0))
        except (TypeError, ValueError):
            continue
        display_name = str(raw.get("Name_Localised") or "").strip()
        if key not in merged:
            order.append(key)
            merged[key] = {
                "frontier_name": frontier_name,
                "display_name": display_name or frontier_name,
                "count": 0,
                "stolen": 0,
                "is_drones": key == "drones",
            }
        item = merged[key]
        item["count"] += count
        item["stolen"] += min(stolen, count)
        if display_name:
            item["display_name"] = display_name
    return [merged[key] for key in order if merged[key]["count"] > 0]


def cargo_snapshot(payload, *, fid, ship_id=None, cargo_capacity=None,
                   srv_type="") -> dict | None:
    if not isinstance(payload, dict) or payload.get("event") != "Cargo":
        return None
    vessel = str(payload.get("Vessel") or "").strip().casefold()
    if vessel not in ("ship", "srv") or not str(fid or "").strip():
        return None
    inventory = payload.get("Inventory")
    if not isinstance(inventory, list):
        return None
    normalized = normalize_inventory(inventory)
    try:
        count = max(0, int(payload.get("Count") or 0))
    except (TypeError, ValueError):
        return None
    if sum(item["count"] for item in normalized) != count:
        return None
    capacity = None
    if vessel == "ship":
        try:
            capacity = max(0, int(cargo_capacity))
        except (TypeError, ValueError):
            capacity = None
    return {
        "fid": str(fid).strip(),
        "vessel": "Ship" if vessel == "ship" else "SRV",
        "vehicle_name": str(srv_type or "").strip(),
        "ship_id": int(ship_id) if vessel == "ship" and ship_id is not None else None,
        "timestamp": str(payload.get("timestamp") or ""),
        "count": count,
        "capacity": capacity,
        "inventory": normalized,
    }


def _matches_trigger(payload, trigger, tolerance_seconds):
    if not isinstance(payload, dict) or not isinstance(trigger, dict):
        return False
    if payload.get("event") != "Cargo" or trigger.get("event") != "Cargo":
        return False
    if str(payload.get("Vessel") or "").casefold() != str(
        trigger.get("Vessel") or ""
    ).casefold():
        return False
    try:
        if int(payload.get("Count")) != int(trigger.get("Count")):
            return False
    except (TypeError, ValueError):
        return False
    payload_time = _timestamp(payload.get("timestamp"))
    trigger_time = _timestamp(trigger.get("timestamp"))
    if payload_time is None or trigger_time is None:
        return False
    return abs((payload_time - trigger_time).total_seconds()) <= tolerance_seconds


def read_cargo_snapshot(path, trigger, *, fid, ship_id=None,
                        cargo_capacity=None, srv_type="", attempts=3,
                        retry_delay=0.03, tolerance_seconds=5.0,
                        sleeper=time.sleep) -> dict | None:
    """Read the stable Cargo.json matching one authoritative Cargo event."""
    if isinstance(trigger, dict) and isinstance(trigger.get("Inventory"), list):
        return cargo_snapshot(
            trigger, fid=fid, ship_id=ship_id,
            cargo_capacity=cargo_capacity, srv_type=srv_type,
        )

    path = Path(path)
    for attempt in range(max(1, int(attempts))):
        try:
            before = path.stat()
            raw = path.read_bytes()
            after = path.stat()
            if (before.st_size, before.st_mtime_ns) != (
                after.st_size, after.st_mtime_ns
            ):
                raise OSError("Cargo.json changed while being read")
            payload = json.loads(raw.decode("utf-8-sig"))
            if not _matches_trigger(payload, trigger, tolerance_seconds):
                raise ValueError("Cargo.json does not match the Cargo event")
            snapshot = cargo_snapshot(
                payload, fid=fid, ship_id=ship_id,
                cargo_capacity=cargo_capacity, srv_type=srv_type,
            )
            if snapshot is not None:
                return snapshot
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
            pass
        if attempt + 1 < max(1, int(attempts)):
            sleeper(max(0.0, float(retry_delay)))
    return None
