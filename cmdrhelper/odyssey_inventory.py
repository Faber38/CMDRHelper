"""Commander-local Odyssey inventory, reconstructed without Qt or database writes.

Journal snapshots are authoritative. Sidecars are deliberately not read: their
unscoped, overwritten contents cannot establish a historical commander identity.
Actions which also emit BackpackChange are observations, not a second delta.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

CATEGORIES = ("Items", "Components", "Data", "Consumables")
CONTAINERS = ("ShipLocker", "Backpack")
EVENTS = set(CONTAINERS) | {
    "BackpackChange", "CollectItems", "UseConsumable", "DropItems",
    "BuyMicroResources", "SellMicroResources", "TradeMicroResources",
    "UpgradeSuit", "UpgradeWeapon", "MissionAccepted", "MissionCompleted",
    "MissionRedirected", "MissionFailed", "MissionAbandoned", "Embark", "Disembark",
    "TransferMicroResources", "Died", "Resurrect",
}


def canonical_name(value):
    if not isinstance(value, str):
        raise ValueError("missing Frontier name")
    value = value.strip().casefold()
    if value.startswith("$") and value.endswith("_name;"):
        value = value[1:-6]
    if not re.fullmatch(r"[a-z0-9_]+", value):
        raise ValueError("invalid Frontier name")
    return value


def category(value):
    value = str(value or "").casefold()
    prefix = "$microresource_category_"
    if value.startswith(prefix) and value.endswith(";"):
        value = value[len(prefix):-1]
    return {"item": "Items", "items": "Items", "component": "Components",
            "components": "Components", "data": "Data", "consumable": "Consumables",
            "consumables": "Consumables"}.get(value)


def _quantity(value):
    if type(value) is not int or value < 0:
        raise ValueError("invalid quantity")
    return value


def _time(value):
    result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timestamp requires timezone")
    return result


@dataclass(frozen=True)
class StackKey:
    category: str
    name: str
    mission_id: int | None = None
    owner_id: int | None = None
    stolen: bool | None = None


@dataclass(frozen=True)
class Stack:
    key: StackKey
    count: int
    display_name: str = ""


@dataclass
class Container:
    snapshot_timestamp: str | None = None
    updated_at: str | None = None
    valid: bool = False
    stacks: dict[StackKey, Stack] = field(default_factory=dict)
    pending: list[tuple] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)

    @property
    def known(self):
        return self.valid and not self.pending

    def count(self, name, selected_category=None):
        if not self.known:
            return None
        name = canonical_name(name)
        return sum(s.count for s in self.stacks.values()
                   if s.key.name == name and
                   (selected_category is None or s.key.category == selected_category))


@dataclass(frozen=True)
class InventoryRow:
    key: StackKey
    display_name: str
    locker: int | None
    backpack: int | None
    total: int | None
    known: bool
    mission_status: str


@dataclass
class OdysseyInventory:
    commander_id: int
    fid: str
    reconstructed_at: str | None = None
    containers: dict[str, Container] = field(default_factory=lambda: {
        name: Container() for name in CONTAINERS})
    missions: dict[int, str] = field(default_factory=dict)
    coherent: bool = False
    issues: list[str] = field(default_factory=list)
    last_change: dict | None = None

    @property
    def known(self):
        return (self.coherent and not self.issues
                and all(c.known for c in self.containers.values()))

    @property
    def total_count(self):
        if not self.known:
            return None
        return sum(s.count for c in self.containers.values() for s in c.stacks.values())

    @property
    def rows(self):
        locker, backpack = (self.containers[c] for c in CONTAINERS)
        result = []
        for key in sorted(locker.stacks.keys() | backpack.stacks.keys(), key=repr):
            left, right = locker.stacks.get(key), backpack.stacks.get(key)
            a = (left.count if left else 0) if locker.known and not self.issues else None
            b = (right.count if right else 0) if backpack.known and not self.issues else None
            result.append(InventoryRow(
                key, (left.display_name if left else "") or
                (right.display_name if right else ""), a, b,
                a + b if self.known else None, self.known,
                self.missions.get(key.mission_id, "unknown")))
        return tuple(result)

    def count(self, name, container=None, selected_category=None):
        if self.issues:
            return None
        if container is not None:
            return self.containers[container].count(name, selected_category)
        if not self.known:
            return None
        return sum(c.count(name, selected_category) for c in self.containers.values())


class OdysseyReducer:
    """Fresh per reconstruction. Source identity is (resolved journal, byte offset)."""

    def __init__(self, commander_id, fid):
        self.result = OdysseyInventory(commander_id, fid)
        self.seen = set()
        self.embarked = False
        self.observed_changes = []

    def _key(self, item, selected=None):
        cat = selected or category(item.get("Type", item.get("Category")))
        if cat not in CATEGORIES:
            raise ValueError("unresolved Odyssey category")
        mission = item.get("MissionID")
        if mission in (None, 0, 18446744073709551615):
            mission = None
        elif type(mission) is not int or mission < 0:
            raise ValueError("invalid MissionID")
        owner = item.get("OwnerID")
        if owner is not None:
            _quantity(owner)
        stolen = item.get("Stolen")
        if stolen is not None and type(stolen) is not bool:
            raise ValueError("invalid Stolen flag")
        return StackKey(cat, canonical_name(item.get("Name")), mission, owner, stolen)

    def _invalidate(self, name, reason):
        c = self.result.containers[name]
        c.valid = False
        c.issues.append(reason)
        self.result.coherent = False

    def _snapshot(self, event):
        name = event["event"]
        c = self.result.containers[name]
        if not any(cat in event for cat in CATEGORIES):
            # Notification cannot supply a replacement, nor certify old counts.
            self._invalidate(name, "snapshot notification awaits full journal contents")
            return
        fresh = {}
        for cat in CATEGORIES:
            if not isinstance(event.get(cat), list):
                raise ValueError("incomplete snapshot")
            for item in event[cat]:
                key = self._key(item, cat)
                count = _quantity(item.get("Count"))
                if key in fresh:
                    raise ValueError("duplicate snapshot stack")
                fresh[key] = Stack(key, count, str(item.get("Name_Localised") or ""))
        c.stacks = fresh
        c.snapshot_timestamp = c.updated_at = event["timestamp"]
        c.valid = True
        c.pending.clear()
        c.issues.clear()
        if name == "Backpack":
            self.observed_changes.clear()
        other = self.result.containers["Backpack" if name == "ShipLocker" else "ShipLocker"]
        self.result.coherent = bool(other.known and (
            other.snapshot_timestamp == c.snapshot_timestamp or
            (name == "ShipLocker" and self.embarked and not any(
                s.count for s in other.stacks.values()))))

    def _delta(self, container, changes, event, source):
        c = self.result.containers[container]
        if not c.valid:
            return
        fresh = dict(c.stacks)
        applied = []
        for item, sign in changes:
            name = canonical_name(item.get("Name"))
            cat = category(item.get("Type", item.get("Category")))
            candidates = [key for key in fresh if key.name == name and
                          (cat is None or key.category == cat) and
                          key.mission_id == (None if item.get("MissionID") in
                              (None, 0, 18446744073709551615) else item["MissionID"]) and
                          all(field not in item or getattr(key, attr) == item[field]
                              for field, attr in (("OwnerID", "owner_id"), ("Stolen", "stolen")))]
            # Missing ownership/mission details cannot select between stacks.
            if len(candidates) > 1:
                raise ValueError(f"ambiguous stack delta: {name}")
            key = candidates[0] if candidates else self._key(item, cat)
            old = fresh.get(key)
            amount = _quantity(item.get("Count")) * sign
            count = (old.count if old else 0) + amount
            if count < 0:
                raise ValueError(f"inventory underflow: {name}")
            fresh[key] = Stack(key, count, str(item.get("Name_Localised") or
                                              (old.display_name if old else "")))
            applied.append({"container": container, "key": key, "delta": amount})
        c.stacks = fresh
        c.updated_at = event["timestamp"]
        if applied:
            self.result.last_change = {"event": event["event"], "timestamp": event["timestamp"],
                                       "source": source, "changes": applied}

    @staticmethod
    def _observation(item, sign, timestamp):
        return (timestamp, canonical_name(item.get("Name")),
                category(item.get("Type", item.get("Category"))),
                _quantity(item.get("Count", 1)), sign, item.get("OwnerID"),
                item.get("MissionID"), item.get("Stolen"))

    @staticmethod
    def _match(observation, candidates):
        return next((candidate for candidate in candidates
                     if candidate[:5] == observation[:5] and
                     all(a is None or b is None or a == b
                         for a, b in zip(candidate[5:], observation[5:]))), None)

    def apply(self, event, source):
        if source in self.seen:
            return
        self.seen.add(source)
        r = self.result
        et, ts = event.get("event"), event.get("timestamp")
        r.reconstructed_at = ts
        affected = "Backpack" if et in ("Backpack", "BackpackChange", "CollectItems",
                                        "UseConsumable", "DropItems") else "ShipLocker"
        try:
            if et in CONTAINERS:
                self._snapshot(event)
            elif et == "Embark":
                # Do not invent a successful locker transfer (capacity/loss may
                # intervene). The following full locker snapshot establishes it.
                self.embarked = True
                self.observed_changes.clear()
                r.containers["Backpack"] = Container(updated_at=ts, valid=True)
                self._invalidate("ShipLocker", "Embark awaits locker snapshot")
            elif et == "Disembark":
                self.embarked = False
                self.observed_changes.clear()
                self._invalidate("Backpack", "Disembark awaits backpack snapshot")
                self._invalidate("ShipLocker", "Disembark may transfer inventory")
            elif et in ("Died", "Resurrect", "TransferMicroResources"):
                # No speculative transfer/death rules; authoritative snapshots
                # must settle both containers, including possible losses.
                for name in CONTAINERS:
                    self._invalidate(name, f"{et} awaits inventory snapshot")
            elif et in ("CollectItems", "UseConsumable", "DropItems"):
                observation = self._observation(event, 1 if et == "CollectItems" else -1, ts)
                match = self._match(observation, self.observed_changes)
                if match is not None:
                    self.observed_changes.remove(match)
                else:
                    r.containers["Backpack"].pending.append(observation)
            elif et == "BackpackChange":
                changes = [(item, sign) for field, sign in (("Added", 1), ("Removed", -1))
                           for item in event.get(field, [])]
                self._delta("Backpack", changes, event, source)
                for item, sign in changes:
                    observation = self._observation(item, sign, ts)
                    pending = r.containers["Backpack"].pending
                    match = self._match(observation, pending)
                    if match is not None:
                        pending.remove(match)
                    else:
                        self.observed_changes.append(observation)
            elif et in ("BuyMicroResources", "SellMicroResources"):
                items = event.get("MicroResources", [event])
                self._delta("ShipLocker", [(item, 1 if et == "BuyMicroResources" else -1)
                                           for item in items], event, source)
            elif et == "TradeMicroResources":
                changes = [(item, -1) for item in event["Offered"]]
                changes.append(({"Name": event["Received"], "Count": event["Count"],
                                 "Category": event["Category"],
                                 "Name_Localised": event.get("Received_Localised", "")}, 1))
                self._delta("ShipLocker", changes, event, source)
            elif et in ("UpgradeSuit", "UpgradeWeapon"):
                self._delta("ShipLocker", [(item, -1) for item in event["Resources"]], event, source)
            elif et.startswith("Mission"):
                states = {"MissionAccepted": "active", "MissionCompleted": "completed",
                          "MissionFailed": "failed", "MissionAbandoned": "abandoned"}
                if et in states and type(event.get("MissionID")) is int:
                    r.missions[event["MissionID"]] = states[et]
                if et == "MissionCompleted":
                    changes = []
                    for item in event.get("MaterialsReward", []):
                        token = str(item.get("Category", "")).casefold()
                        # Bare Data is shared with Horizons; without a catalog
                        # only the explicit Odyssey token proves its identity.
                        cat = category(token)
                        if cat and (cat != "Data" or token == "$microresource_category_data;"):
                            changes.append((item, 1))
                    self._delta("ShipLocker", changes, event, source)
        except (KeyError, ValueError, TypeError, AttributeError) as exc:
            self._invalidate(affected, f"{source}: {et}: {exc}")


class OdysseyInventoryReader:
    """Read only identified journal_sessions; cache immutable parsed file facts.

    Calling again replays a fresh reducer, never shared commander state. Complete
    duplicate journal files are deduplicated by digest, physical events by offset.
    Partial file copies are not guessed to be identical events.
    """

    def __init__(self):
        self._cache = {}
        self._results = {}

    @staticmethod
    def _signature(path):
        s = path.stat()
        return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns

    def _read(self, path):
        signature = self._signature(path)
        if path in self._cache and self._cache[path][0] == signature:
            return self._cache[path][1]
        events, identities, errors = [], set(), []
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            while True:
                offset = stream.tell()
                line = stream.readline()
                if not line or not line.endswith(b"\n"):
                    break
                digest.update(line)
                try:
                    event = json.loads(line)
                    if event.get("event") in ("Commander", "LoadGame") and event.get("FID"):
                        identities.add(event["FID"])
                    if event.get("event") in EVENTS:
                        events.append((_time(event.get("timestamp")), offset, event))
                except (ValueError, AttributeError, TypeError) as exc:
                    errors.append(f"{path}:{offset}: {exc}")
        if self._signature(path) != signature:
            raise OSError(f"journal changed during read: {path}; retry")
        facts = events, identities, errors, digest.hexdigest()
        self._cache[path] = signature, facts
        return facts

    def reconstruct(self, commander_id, fid, sessions, *, until=None):
        if type(commander_id) is not int or commander_id <= 0 or not isinstance(fid, str) or not fid.strip():
            raise ValueError("explicit commander ID and FID required")
        fid = fid.strip()
        limit = _time(until) if until else None
        grouped = {}
        for raw in sessions:
            row = dict(raw)
            grouped.setdefault(Path(row["journal_file"]).resolve(), []).append(row)
        events, errors, digests = [], [], set()
        eligible = []
        for path, rows in sorted(grouped.items()):
            if any(row.get("commander_id") != commander_id or row.get("fid_seen") != fid
                   or row.get("attribution_status") != "identified" for row in rows):
                continue
            try:
                eligible.append((path, self._signature(path)))
            except OSError as exc:
                errors.append(str(exc))
        cache_key = commander_id, fid, limit, tuple(eligible)
        if not errors and cache_key in self._results:
            # Callers may annotate/mutate a returned result; never share it with
            # the cached result or a different commander request.
            return deepcopy(self._results[cache_key])
        for path, _ in eligible:
            try:
                facts, identities, problems, digest = self._read(path)
                if identities != {fid}:
                    errors.append(f"{path}: journal identity disagrees with index")
                    continue
                errors.extend(problems)
                if digest not in digests:
                    events.extend((ts, str(path), offset, e) for ts, offset, e in facts
                                  if limit is None or ts <= limit)
                    digests.add(digest)
            except OSError as exc:
                errors.append(str(exc))
        reducer = OdysseyReducer(commander_id, fid)
        for _, path, offset, event in sorted(events, key=lambda row: row[:3]):
            reducer.apply(event, (path, offset))
        reducer.result.issues.extend(errors)
        if errors:
            for name in CONTAINERS:
                reducer._invalidate(name, "incomplete or untrusted journal history")
        if not errors:
            if len(self._results) >= 8:
                self._results.pop(next(iter(self._results)))
            self._results[cache_key] = deepcopy(reducer.result)
        return reducer.result
