"""Engineering inventory reconstructed from identified journal files, without UI/DB writes.

Source identity is the resolved journal path plus physical byte offset, never an
importer's batch key. Recreate the reducer on each read; cached immutable file
facts make repeated queries cheap and prevent state leaking between commanders.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
from pathlib import Path
import re

from .material_catalog import get_material

logger = logging.getLogger(__name__)
CATEGORIES = ("Raw", "Manufactured", "Encoded")
EVENTS = {"Materials", "MaterialCollected", "MaterialDiscarded", "MaterialTrade",
          "EngineerCraft", "Synthesis", "MissionCompleted", "EngineerContribution"}


def frontier_name(value):
    """Only Frontier identifiers, never display-name inference."""
    if not isinstance(value, str):
        raise ValueError("missing Frontier name")
    name = value.strip().casefold()
    if name.startswith("$") and name.endswith("_name;"):
        name = name[1:-6]
    if not re.fullmatch(r"[a-z0-9_]+", name):
        raise ValueError("invalid Frontier name")
    return name


def category(value):
    token = str(value or "").strip().casefold()
    prefix = "$microresource_category_"
    if token.startswith(prefix) and token.endswith(";"):
        token = token[len(prefix):-1]
    return {"raw": "Raw", "elements": "Raw", "manufactured": "Manufactured",
            "encoded": "Encoded"}.get(token)


def quantity(value):
    if type(value) is not int or value < 0:
        raise ValueError("invalid material quantity")
    return value


def event_time(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("journal timestamp lacks timezone")
    return parsed


@dataclass(frozen=True)
class MaterialStock:
    category: str | None
    name: str
    count: int | None
    known: bool
    display_name: str = ""


@dataclass
class MaterialInventory:
    commander_id: int
    fid: str
    snapshot_timestamp: str | None = None
    _stocks: dict[str, MaterialStock] = field(default_factory=dict, repr=False)
    issues: list[str] = field(default_factory=list)
    last_change: dict | None = None

    @property
    def known(self):
        return self.snapshot_timestamp is not None and not self.issues

    @property
    def stocks(self):
        """Public counts are unknown while any unresolved inconsistency exists."""
        return {name: self.material(name) for name in self._stocks}

    def material(self, name):
        name = frontier_name(name)
        stock = self._stocks.get(name)
        if stock is None:
            return MaterialStock(None, name, None, False)
        if not self.known:
            return MaterialStock(stock.category, name, None, False, stock.display_name)
        return stock

    def by_category(self, selected):
        return {name: self.material(name) for name, stock in self._stocks.items()
                if stock.category == selected}


class _Reducer:
    def __init__(self, commander_id, fid):
        self.result = MaterialInventory(commander_id, fid)
        self.seen = set()

    def apply(self, event, source):
        if source in self.seen:
            return
        self.seen.add(source)
        result = self.result
        et = event.get("event")
        try:
            if et == "Materials":
                # Validate the whole replacement before touching inventory.
                fresh = {}
                for cat in CATEGORIES:
                    if not isinstance(event.get(cat), list):
                        raise ValueError("incomplete Materials snapshot")
                    for item in event[cat]:
                        name = frontier_name(item.get("Name"))
                        if name in fresh:
                            raise ValueError("duplicate snapshot material")
                        fresh[name] = MaterialStock(cat, name, quantity(item.get("Count")),
                                                   True, str(item.get("Name_Localised") or ""))
                for name, old in result._stocks.items():
                    if name in fresh and fresh[name].category != old.category:
                        raise ValueError("material category conflict")
                    if name not in fresh:
                        fresh[name] = MaterialStock(old.category, name, 0, True, old.display_name)
                result._stocks = fresh
                result.snapshot_timestamp = event["timestamp"]
                result.issues.clear()
                result.last_change = None
                return

            changes = []
            if et in ("MaterialCollected", "MaterialDiscarded"):
                changes = [(event, "Name", "Count", 1 if et == "MaterialCollected" else -1)]
            elif et == "MaterialTrade":
                changes = [(event["Paid"], "Material", "Quantity", -1),
                           (event["Received"], "Material", "Quantity", 1)]
            elif et in ("EngineerCraft", "Synthesis"):
                field_name = "Ingredients" if et == "EngineerCraft" else "Materials"
                items = event[field_name]
                if not isinstance(items, list):
                    raise ValueError("invalid ingredients")
                changes = [(item, "Name", "Count", -1) for item in items]
            elif et == "EngineerContribution" and event.get("Type") == "Materials":
                changes = [(event, "Material", "Quantity", -1)]
            elif et == "MissionCompleted":
                for item in event.get("MaterialsReward", []):
                    cat = category(item.get("Category"))
                    # Data is ambiguous with Odyssey. An Encoded catalog identity
                    # also admits materials this commander has never owned.
                    token = str(item.get("Category") or "").casefold()
                    if cat is None and token in ("data", "$microresource_category_data;"):
                        name = frontier_name(item.get("Name"))
                        old = result._stocks.get(name)
                        definition = get_material(name)
                        if ((definition and definition.category == "Encoded")
                                or (definition is None and old and old.category == "Encoded")):
                            cat = "Encoded"
                    if cat:
                        changes.append(({**item, "Category": cat}, "Name", "Count", 1))

            updated = dict(result._stocks)
            applied = []
            for item, name_key, count_key, sign in changes:
                name = frontier_name(item.get(name_key))
                amount = quantity(item.get(count_key))
                old = updated.get(name)
                cat = category(item.get("Category"))
                if cat is None and old:
                    cat = old.category
                if cat is None:
                    raise ValueError(f"unresolved material category: {name}")
                if old and old.category != cat:
                    raise ValueError(f"material category conflict: {name}")
                display = str(item.get(name_key + "_Localised") or (old.display_name if old else ""))
                if result.snapshot_timestamp is None:
                    updated[name] = MaterialStock(cat, name, None, False, display)
                    continue
                previous = old.count if old and old.count is not None else 0
                count = previous + sign * amount
                if count < 0:
                    raise ValueError(f"material underflow: {name} ({previous} {sign * amount:+})")
                updated[name] = MaterialStock(cat, name, count, True, display)
                if amount:
                    applied.append({"name": name, "category": cat, "delta": sign * amount})
            result._stocks = updated
            if applied:
                result.last_change = {"timestamp": event["timestamp"], "event": et,
                                      "source": source, "changes": applied}
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            message = f"{source}: {et}: {exc}"
            result.issues.append(message)
            logger.warning("Material inventory inconsistency: %s", message)


class MaterialInventoryReader:
    """Reusable reader for journal_sessions rows (dicts or sqlite3.Row).

    No general journal offsets are advanced or trusted as material-processing
    checkpoints. Complete physical lines are read, including unprocessed live
    tails; a fresh stat invalidates cached files after append/replacement.
    Call reconstruct again on journal changes. No AppState mutation is needed.
    """
    def __init__(self):
        self._cache = {}

    @staticmethod
    def _signature(stat):
        # Reading can change atime; it is not evidence of content mutation.
        return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)

    def _read(self, path):
        signature = self._signature(path.stat())
        cached = self._cache.get(path)
        if cached and cached[0] == signature:
            return cached[1]
        events, identities, errors = [], set(), []
        with path.open("rb") as handle:
            while True:
                offset = handle.tell()
                line = handle.readline()
                if not line or not line.endswith(b"\n"):
                    break
                try:
                    event = json.loads(line)
                    if not isinstance(event, dict):
                        raise ValueError("event is not an object")
                    et = event.get("event")
                    if et in ("Commander", "LoadGame") and event.get("FID"):
                        identities.add(str(event["FID"]).strip())
                    if et in EVENTS:
                        events.append((event_time(event.get("timestamp")), offset, event))
                except (ValueError, TypeError) as exc:
                    errors.append(f"{path}:{offset}: unreadable journal event ({exc})")
        if self._signature(path.stat()) != signature:
            raise OSError(f"journal changed during read: {path}; retry reconstruction")
        facts = (events, identities, errors)
        self._cache[path] = (signature, facts)
        return facts

    def reconstruct(self, commander_id, fid, sessions):
        if type(commander_id) is not int or commander_id <= 0 or not isinstance(fid, str) or not fid.strip():
            raise ValueError("explicit commander ID and FID required")
        fid = str(fid).strip()
        reducer = _Reducer(commander_id, fid)
        errors, events = [], []
        # Conflicting duplicate index rows are never silently merged.
        grouped = {}
        for raw in sessions:
            session = dict(raw)
            path = Path(session["journal_file"]).resolve()
            grouped.setdefault(path, []).append(session)
        for path, rows in grouped.items():
            if not any(row.get("commander_id") == commander_id for row in rows):
                continue
            if any(row.get("attribution_status") != "identified"
                   or row.get("commander_id") != commander_id
                   or row.get("fid_seen") != fid for row in rows):
                continue
            try:
                facts, identities, file_errors = self._read(path)
                if identities != {fid}:
                    errors.append(f"{path}: journal identity disagrees with index")
                    continue
                errors.extend(file_errors)
                events.extend((ts, str(path), offset, event) for ts, offset, event in facts)
            except OSError as exc:
                errors.append(str(exc))
        for _, path, offset, event in sorted(events, key=lambda row: row[:3]):
            reducer.apply(event, (path, offset))
        reducer.result.issues.extend(errors)
        return reducer.result
