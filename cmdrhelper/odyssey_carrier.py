"""Private Odyssey stock persistence, separate from the bartender market."""
from copy import deepcopy
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from urllib.parse import quote

from .odyssey_inventory import canonical_name

CARRIER_CATEGORIES = ("Items", "Components", "Data")
PRIVATE_CARRIER_CAPACITY = 1000


@dataclass(frozen=True)
class CarrierCapacity:
    known_amount: int
    unknown_positions: int
    limit: int = PRIVATE_CARRIER_CAPACITY

    @property
    def complete(self):
        return self.unknown_positions == 0

    @property
    def inconsistent(self):
        return self.known_amount > self.limit


def carrier_capacity(records, extra_positions=()):
    """Shared limit for all three categories; never modifies confirmations.

    Missing catalog positions are unknown, including explicit zero candidates.
    Previously recorded and newly observed symbols extend the completeness set.
    Inputs are validated current records, independent of UI and journal tracking.
    """
    from .odyssey_catalog import all_materials
    positions = {(m.category, m.symbol) for m in all_materials() if m.category in CARRIER_CATEGORIES}
    positions.update((cat, name) for cat, name in extra_positions if cat in CARRIER_CATEGORIES)
    for token in records:
        if isinstance(token, str) and "/" in token:
            cat, name = token.split("/", 1)
            if cat in CARRIER_CATEGORIES:
                positions.add((cat, name))
    total = unknown = 0
    for cat, name in positions:
        record = records.get(f"{cat}/{name}", {})
        amount = record.get("current_amount") if isinstance(record, dict) else None
        if valid_amount(amount):
            total += amount
        else:
            unknown += 1
    return CarrierCapacity(total, unknown)


def inventory_carrier_capacity(inventory):
    records = inventory.carrier_records if inventory.carrier_id is not None else {}
    positions = {(k.category, k.name) for container in inventory.containers.values() for k in container.stacks}
    return carrier_capacity(records, positions)


def valid_amount(value):
    return type(value) is int and 0 <= value <= 2_147_483_647


def owned_carrier(database_path, commander_id, fid):
    """Resolve ownership, not current presence on that carrier, without writes."""
    if type(commander_id) is not int or commander_id <= 0 or not fid:
        return None
    try:
        with closing(sqlite3.connect(Path(database_path).resolve().as_uri() + "?mode=ro", uri=True)) as con:
            row = con.execute(
                "SELECT f.carrier_id FROM commanders c JOIN commander_carriers f "
                "ON f.commander_id=c.id WHERE c.id=? AND c.fid=?", (commander_id, fid)).fetchone()
        return row[0] if row and type(row[0]) is int and row[0] > 0 else None
    except (OSError, sqlite3.Error, TypeError):
        return None


class OdysseyCarrierStore:
    VERSION = 2

    def __init__(self, settings):
        self.settings = settings

    @staticmethod
    def key(fid, carrier_id):
        if not isinstance(fid, str) or not fid.strip() or type(carrier_id) is not int or carrier_id <= 0:
            raise ValueError("unverified carrier identity")
        return f"materials/odyssey/carrier/{quote(fid, safe='')}/{carrier_id}"

    def load(self, fid, carrier_id):
        key = self.key(fid, carrier_id)
        saved = self.settings.value(key)
        result = dict(version=self.VERSION, fid=fid, carrier_id=carrier_id, records={},
                      tracking_policy=dict(mode="own_carrier_locker_projection",
                          requires_verified_own_carrier_stay=True,
                          standalone_shiplocker_delta_is_transfer_evidence=False,
                          standalone_backpack_change_is_transfer_evidence=False))
        if (not isinstance(saved, dict) or saved.get("version") not in (1, self.VERSION)
                or any(saved.get(k) != result[k] for k in ("fid", "carrier_id"))):
            return result
        result["revision"] = saved.get("revision", 0)
        result["tracking"] = deepcopy(saved.get("tracking"))
        records = saved.get("records")
        if not isinstance(records, dict):
            return result
        for token, raw in records.items():
            if not isinstance(raw, dict):
                continue
            cat, name = raw.get("category"), raw.get("name")
            try:
                if cat not in CARRIER_CATEGORIES or canonical_name(name) != name or token != f"{cat}/{name}":
                    continue
            except ValueError:
                continue
            record = deepcopy(raw)
            last = record.get("last_confirmed_amount")
            record["last_confirmed_amount"] = last if valid_amount(last) else None
            timestamp = record.get("confirmed_at")
            try:
                valid_time = isinstance(timestamp, str) and datetime.fromisoformat(timestamp).tzinfo is not None
            except ValueError:
                valid_time = False
            if not valid_time:
                record["confirmed_at"] = ""
            status = record.get("status")
            if not (status in ("manual", "tracked") and valid_time and valid_amount(last)
                    and valid_amount(record.get("current_amount"))
                    and (status != "manual" or record.get("current_amount") == last)
                    and (status != "tracked" or saved.get("version") == self.VERSION)):
                record.update(current_amount=None, status=status if status in
                              ("unknown", "inconsistent", "pending") else "unknown")
            result["records"][token] = record
        return result

    def confirm(self, fid, carrier_id, category, name, amount):
        if category not in CARRIER_CATEGORIES or (amount is not None and not valid_amount(amount)):
            raise ValueError("invalid manual stock")
        name = canonical_name(name)
        key = self.key(fid, carrier_id)
        saved = self.settings.value(key)
        if isinstance(saved, dict) and saved.get("version") not in (1, self.VERSION):
            raise ValueError("unsupported stock version")
        ledger = self.load(fid, carrier_id)
        token = f"{category}/{name}"
        record = ledger["records"].get(token, dict(category=category, name=name,
            last_confirmed_amount=None, confirmed_at=""))
        if amount is None:
            record.update(current_amount=None, status="unknown")
        else:
            record.update(current_amount=amount, last_confirmed_amount=amount, status="manual",
                          confirmed_at=datetime.now(timezone.utc).isoformat())
        ledger["records"][token] = record
        record.pop("uncertainty_reason", None)
        ledger["revision"] = int(ledger.get("revision", 0)) + 1
        tracking = ledger.get("tracking")
        # Confirming a quantity resets its accounting anchor, not the witnessed
        # geographical position. Only journal location evidence changes that.
        ledger["tracking"] = (dict(tracking, anchor=None, cursor=None, prefix=None)
                              if isinstance(tracking, dict) and "location_state" in tracking else None)
        return self.save(fid, carrier_id, ledger)

    def save(self, fid, carrier_id, ledger):
        """Publish quantities and their cursor together, only after sync succeeds."""
        key = self.key(fid, carrier_id)
        saved = self.settings.value(key)
        if isinstance(saved, dict) and saved.get("version") not in (1, self.VERSION):
            raise ValueError("unsupported stock version")
        self.settings.setValue(key, ledger)
        self.settings.sync()
        if self.settings.status() != self.settings.Status.NoError:
            # Do not publish an unpersisted confirmation as successful.
            if saved is None:
                self.settings.remove(key)
            else:
                self.settings.setValue(key, saved)
            raise OSError("manual stock could not be saved")
        return ledger


def material_amounts(inventory, category, name, *, capacity_state=None):
    """One aggregate per material, independent of ownership/mission stack count."""
    locker = inventory.count(name, "ShipLocker", category)
    backpack = inventory.count(name, "Backpack", category)
    personal = inventory.count(name, selected_category=category)
    record = inventory.carrier_records.get(f"{category}/{name}", {})
    carrier = record.get("current_amount") if record.get("status") in ("manual", "tracked") else None
    if inventory.carrier_id is None:
        carrier = None
    if category not in CARRIER_CATEGORIES:
        return locker, backpack, None, personal
    total = personal + carrier if personal is not None and carrier is not None else None
    capacity_state = capacity_state or inventory_carrier_capacity(inventory)
    if capacity_state.inconsistent:
        total = None
    return locker, backpack, carrier, total
