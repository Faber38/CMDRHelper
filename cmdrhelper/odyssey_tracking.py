"""Incremental own-carrier projection from the existing sidecar capture.

This is the user's location-based accounting rule, not proof of a live carrier
inventory. All mutation runs on the State/GUI thread, independently of views.
Sessions and process restarts deliberately establish a new personal baseline.
"""
from copy import deepcopy
from collections import deque
from itertools import islice
import logging
from pathlib import Path

from .odyssey_carrier import OdysseyCarrierStore, owned_carrier, carrier_capacity
from .odyssey_inventory import OdysseyReducer, category, canonical_name, validate_snapshot

logger = logging.getLogger(__name__)


def snapshot_amounts(event):
    validate_snapshot(event, "ShipLocker")
    amounts = {}
    for cat in ("Items", "Components", "Data"):
        for item in event[cat]:
            token = f"{cat}/{canonical_name(item['Name'])}"
            amounts[token] = amounts.get(token, 0) + item["Count"]
    return amounts


def personal_delta(event):
    """Reuse explicit reducer arithmetic without touching personal inventory."""
    kind = event.get("event", "")
    if kind not in {"BuyMicroResources", "SellMicroResources", "TradeMicroResources",
                    "UpgradeSuit", "UpgradeWeapon", "MissionCompleted"}:
        return {}
    changes = []
    if kind in ("BuyMicroResources", "SellMicroResources"):
        changes = [(item, 1 if kind == "BuyMicroResources" else -1)
                   for item in event.get("MicroResources", [event])]
    elif kind == "TradeMicroResources":
        changes = [(item, -1) for item in event["Offered"]]
        changes.append((dict(Name=event["Received"], Count=event["Count"],
                             Category=event["Category"]), 1))
    elif kind in ("UpgradeSuit", "UpgradeWeapon"):
        changes = [(item, -1) for item in event["Resources"]]
    else:
        for item in event.get("MaterialsReward", []):
            token = str(item.get("Category", "")).casefold()
            cat = category(token)
            if cat and (cat != "Data" or token == "$microresource_category_data;"):
                changes.append((item, 1))
    result = {}
    validator = OdysseyReducer(0, "")
    for item, sign in changes:
        key = validator._key(item)
        count = item["Count"]
        if type(count) is not int or count < 0:
            raise ValueError("invalid explicit personal quantity")
        token = f"{key.category}/{key.name}"
        result[token] = result.get(token, 0) + sign * count
    return result


class CarrierProjection:
    """Small in-memory interval. Never resume a persisted locker delta at login."""
    def __init__(self, carrier_id):
        self.carrier_id = carrier_id
        self.location_state = "UNKNOWN"
        self.location_market_id = None
        self.anchor = None
        self.known = {}
        self.blocked = False

    @property
    def present(self):
        return self.location_state == "OWN_CARRIER"

    def _set_location(self, state, market=None):
        if (state, market) != (self.location_state, self.location_market_id):
            self.anchor = None
            self.known = {}
            self.blocked = False
        self.location_state, self.location_market_id = state, market

    def location(self, event):
        kind = event.get("event", "")
        if kind in {"Undocked", "FSDJump", "StartJump", "SupercruiseEntry"}:
            self._set_location("OTHER_LOCATION")
        elif (kind in {"BuyMicroResources", "SellMicroResources"}
              and type(event.get("MarketID")) is int and event["MarketID"] > 0
              and event["MarketID"] != self.carrier_id):
            self._set_location("UNKNOWN", event["MarketID"])
        elif kind in {"Died", "Resurrect", "Shutdown", "JoinACrew", "QuitACrew", "LoadGame", "Commander"}:
            # Session/container continuity is separate from evidence of a place.
            self.anchor = None
            self.known = {}
            self.blocked = False
        elif kind in {"Docked", "Location", "Embark", "Disembark"}:
            market = event.get("MarketID")
            station = event.get("StationType")
            if type(market) is int and market > 0:
                if station == "FleetCarrier":
                    self._set_location("OWN_CARRIER" if market == self.carrier_id else "OTHER_CARRIER", market)
                elif isinstance(station, str) and station:
                    self._set_location("STATION", market)
                elif market != self.location_market_id:
                    # A different numeric place is evidence of a change, but
                    # does not identify its type or establish carrier presence.
                    self._set_location("UNKNOWN", market)
            elif isinstance(station, str) and station and station != "FleetCarrier":
                self._set_location("STATION")
            elif (kind == "Location" and event.get("Docked") is False
                  and event.get("BodyType") in {"Planet", "Star"}
                  and not station and "MarketID" not in event):
                self._set_location("OTHER_LOCATION")
            # Missing fields and Embark/Disembark's OnStation/OnPlanet, Taxi
            # or SRV flags alone do not establish a new geographical position.
            if kind in {"Embark", "Disembark"} and (market is not None or station):
                # Keep the existing protection against container redistribution.
                self.anchor = None
                self.known = {}
                self.blocked = False

    def event(self, event):
        self.location(event)
        if not self.present or self.anchor is None:
            return
        kind = event.get("event", "")
        try:
            for token, amount in personal_delta(event).items():
                self.known[token] = self.known.get(token, 0) + amount
        except (KeyError, ValueError, TypeError, AttributeError):
            self.blocked = True
        if kind == "TransferMicroResources" or (
                "MicroResource" in kind and kind not in
                {"BuyMicroResources", "SellMicroResources", "TradeMicroResources"}):
            self.blocked = True

    def snapshot(self, proof, ledger):
        amounts = snapshot_amounts(proof["snapshot"])
        anchor = dict(offset=proof["offset"], prefix=proof["prefix"],
                      journal_file=proof["journal_file"], amounts=amounts,
                      timestamp=proof["snapshot"]["timestamp"])
        previous = self.anchor
        self.anchor = anchor if self.present else None
        reason = None
        if self.present and previous is not None:
            tokens = set(previous["amounts"]) | set(amounts) | set(self.known)
            deltas = {token: amounts.get(token, 0) - previous["amounts"].get(token, 0)
                      - self.known.get(token, 0) for token in tokens}
            affected = {token for token, delta in deltas.items() if delta
                        and ledger["records"].get(token, {}).get("status") in ("manual", "tracked")}
            candidate = deepcopy(ledger["records"])
            if self.blocked:
                reason = "unclassified"
            for token in affected:
                amount = candidate[token]["current_amount"] - deltas[token]
                if amount < 0:
                    reason = "negative"
                candidate[token].update(current_amount=amount, status="tracked")
            if carrier_capacity(candidate).inconsistent:
                reason = "capacity"
            if reason:
                # All changed materials in the interval fail together.
                for token in affected:
                    ledger["records"][token].update(current_amount=None, status="inconsistent",
                                                    uncertainty_reason=reason)
            else:
                ledger["records"] = candidate
        self.known = {}
        self.blocked = False
        ledger["tracking"] = dict(rule_version=1, anchor=self.anchor,
                                  present=self.present, location_state=self.location_state,
                                  location_market_id=self.location_market_id,
                                  cursor=proof["offset"], prefix=proof["prefix"])


def historical_location(state, fid, carrier, current_path):
    """Seed only location from indexed predecessors, never personal quantities.

    Run once on capture/session initialization. Walk backwards only as far as a
    definite position, then apply the collected location events chronologically.
    The existing index and delta reader are the sole journal discovery/read path.
    """
    from .journal_files import journal_sort_key
    from .journal_reader import read_journal_delta
    from .odyssey_sidecars import signature

    current = Path(current_path).resolve()
    sessions = sorted(getattr(state, "_journal_index_sessions", None) or [],
                      key=lambda row: journal_sort_key(Path(row["journal_file"])))
    collected = []
    for row in reversed(sessions):
        path = Path(row["journal_file"]).resolve()
        if path.parent != current.parent or journal_sort_key(path) >= journal_sort_key(current):
            continue
        if row.get("attribution_status") != "identified" or row.get("fid_seen") != fid:
            break
        try:
            before = signature(path)
            if (before[2], before[3]) != (row.get("file_size"), row.get("modified_ns")):
                return CarrierProjection(carrier)
            events, end = read_journal_delta(path, 0)
            if signature(path) != before or end != before[2]:
                return CarrierProjection(carrier)
            identities = {e["FID"] for e in events
                          if e.get("event") in {"Commander", "LoadGame"} and e.get("FID")}
            if identities != {fid}:
                return CarrierProjection(carrier)
        except (OSError, ValueError, TypeError):
            return CarrierProjection(carrier)
        location_events = [e for e in events if e.get("event") in {
            "Docked", "Location", "Undocked", "FSDJump", "StartJump", "SupercruiseEntry",
            "Embark", "Disembark", "BuyMicroResources", "SellMicroResources"}]
        collected.append(location_events)
        probe = CarrierProjection(carrier)
        for event in location_events:
            probe.location(event)
        if probe.location_state != "UNKNOWN":
            break
    result = CarrierProjection(carrier)
    for events in reversed(collected):
        for event in events:
            result.location(event)
    return result


class OdysseyCarrierTracking:
    def __init__(self, state):
        self.state = state
        self.store = OdysseyCarrierStore(state.settings)
        self.identity = None
        self.engine = None
        self.serial = None
        self.queue = []
        self.processed = None

    def reanchor(self):
        """A manual confirmation wins; no worker ever writes this ledger."""
        capture = self.state.watcher.odyssey_sidecars
        if capture.path is not None:
            capture.poll(capture.path)
        self.processed = None
        self.poll(rebase=True)
        if self.engine:
            # A missing sidecar can hold later location events in the queue.
            # Discard amounts at manual confirmation, never an observed exit.
            for entry in self.queue:
                self.engine.location(entry["event"])
        safe_anchor = (self.engine.anchor if self.engine is not None and not self.queue
                       and not self.engine.known and not self.engine.blocked else None)
        self.queue = []
        if self.engine:
            self.engine.anchor = None
            self.engine.known = {}
            self.engine.blocked = False
        exported = capture.export()
        batch = capture.tracking_batch
        if self.engine is None or not exported or not batch or self.identity is None:
            return
        self.serial = batch["serial"]
        fid, carrier = self.identity[1:3]
        ledger = self.store.load(fid, carrier)
        for proof in exported["snapshots"]:
            if (proof["snapshot"]["event"] == "ShipLocker"
                    and proof["journal_file"] == exported["journal_file"]
                    and capture._latest.get("ShipLocker", (None,))[0] == proof["offset"]
                    and safe_anchor is not None and safe_anchor["prefix"] == proof["prefix"]):
                self.engine.snapshot(proof, ledger)
                self.store.save(fid, carrier, ledger)
        self.processed = None

    def poll(self, rebase=False):
        capture = self.state.watcher.odyssey_sidecars
        exported = capture.export()
        batch = capture.tracking_batch
        fid = getattr(self.state, "commander_fid", None)
        cid = getattr(self.state, "commander_id", None)
        if not exported or not batch or not fid or exported["fid"] != fid:
            self.identity = None
            self.engine = None
            return
        signature = (id(capture), cid, fid, exported["journal_signature"],
                     tuple((p["offset"], p["prefix"], p["signature"])
                           for p in exported["snapshots"]))
        if signature == self.processed and not rebase:
            return
        carrier = owned_carrier(self.state.database.path, cid, fid)
        if carrier is None:
            self.identity = None
            self.engine = None
            return
        identity = (id(capture), fid, carrier, exported["journal_file"])
        reset = identity != self.identity or batch["reset"] and batch["serial"] != self.serial
        engine = CarrierProjection(carrier) if reset else deepcopy(self.engine)
        if reset:
            # A definite position in the active file supersedes every older one.
            # Otherwise seed from indexed predecessors before replaying its tail.
            probe = CarrierProjection(carrier)
            for entry in batch["events"]:
                probe.location(entry["event"])
            if probe.location_state == "UNKNOWN":
                engine = historical_location(self.state, fid, carrier, exported["journal_file"])
        queue = deque() if reset else deque(deepcopy(self.queue))
        if reset or batch["serial"] != self.serial:
            queue.extend(batch["events"])
        ledger = self.store.load(fid, carrier)
        original = deepcopy(ledger)
        location_before = (engine.location_state, engine.location_market_id)
        proofs = {p["offset"]: p for p in exported["snapshots"]
                  if p["snapshot"]["event"] == "ShipLocker"
                  and p["journal_file"] == exported["journal_file"]}
        changed = False
        last_entry = None
        while queue:
            entry = queue[0]
            event = entry["event"]
            if event.get("event") == "ShipLocker":
                proof = proofs.get(entry["offset"])
                if proof is None:
                    try:
                        snapshot = validate_snapshot(event, "ShipLocker")
                        proof = dict(snapshot=snapshot, offset=entry["offset"], prefix=entry["prefix"],
                                     journal_file=exported["journal_file"])
                    except (ValueError, TypeError, KeyError):
                        pass
                if proof is None:
                    if not any(e["event"].get("event") == "ShipLocker" for e in islice(queue, 1, None)):
                        break
                    # An overwritten intermediate snapshot is not invented.
                    # Keep the witnessed start and account for the entire journal
                    # interval up to the next witnessed end (including exits).
                elif proof["prefix"] == entry["prefix"]:
                    if reset or rebase:
                        engine.anchor = None
                    engine.snapshot(proof, ledger)
                    changed = True
            else:
                engine.event(event)
            last_entry = entry
            queue.popleft()
        if len(queue) > 2048:
            # Do not retain an unbounded pending interval. Replay only the current
            # batch to establish context and a fresh baseline on the next poll.
            self.identity = None
            return
        if last_entry is not None and location_before != (engine.location_state, engine.location_market_id):
            # Persist a witnessed move even if no new locker snapshot arrives.
            ledger["tracking"] = dict(rule_version=1, anchor=engine.anchor, present=engine.present,
                location_state=engine.location_state, location_market_id=engine.location_market_id,
                journal_file=exported["journal_file"], cursor=last_entry["offset"], prefix=last_entry["prefix"])
            changed = True
        try:
            if changed:
                self.store.save(fid, carrier, ledger)
        except (OSError, ValueError):
            logger.exception("Odyssey carrier projection could not be persisted")
            return
        self.engine, self.queue, self.identity = engine, queue, identity
        self.serial, self.processed = batch["serial"], signature
        if ledger["records"] != original["records"]:
            self.state.odysseySidecarsChanged.emit()
