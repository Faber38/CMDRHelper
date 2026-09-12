"""Manually anchored carrier ledger; only forward changes in the live journal.

No archive replay and no market-stock inference. A durable byte cursor and prefix
hash bind every balance to the exact journal content already consumed.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from .material_inventory import frontier_name, quantity
from .mining_catalog import MINING_COMMODITIES


def read_carrier_feed(path, fid):
    if not path:
        return None
    try:
        path = Path(path).resolve()
        raw = path.read_bytes()
        raw = raw[:raw.rfind(b"\n") + 1]  # Never consume an incomplete event.
        events, identities, offset = [], set(), 0
        for line in raw.splitlines(keepends=True):
            event = json.loads(line)
            if not isinstance(event, dict):
                return None
            if event.get("event") in ("Commander", "LoadGame") and event.get("FID"):
                identities.add(event["FID"])
            events.append((offset, event))
            offset += len(line)
        if identities != {fid}:
            return None
        return dict(path=str(path), raw=raw, events=events)
    except (OSError, ValueError, TypeError):
        return None


def stable_id(value):
    return value if type(value) is int and value > 0 else None


class CarrierLedger:
    def __init__(self, settings):
        self.settings = settings

    @staticmethod
    def key(fid, carrier_id):
        # Escape FID rather than allowing it to create QSettings path components.
        from urllib.parse import quote
        return f"materials/mining/carrier/{quote(fid, safe='')}/{carrier_id}"

    def _load(self, fid, carrier_id):
        saved = self.settings.value(self.key(fid, carrier_id), {})
        if (not isinstance(saved, dict) or saved.get("fid") != fid
                or saved.get("carrier_id") != carrier_id or saved.get("version") != 1):
            return dict(version=1, fid=fid, carrier_id=carrier_id, records={})
        saved = deepcopy(saved)
        if not isinstance(saved.get("records"), dict):
            saved["records"] = {}
        records = {}
        for symbol, record in saved["records"].items():
            if symbol not in {c.symbol for c in MINING_COMMODITIES} or not isinstance(record, dict):
                continue
            count = record.get("count")
            if (record.get("status") not in ("manual", "tracked", "inconsistent")
                    or not isinstance(record.get("confirmed_at"), str)
                    or (count is not None and (type(count) is not int or not 0 <= count <= 2_147_483_647))):
                record = dict(count=None, status="inconsistent", confirmed_at="")
            records[symbol] = record
            if record.get("status") == "inconsistent":
                record["count"] = None
        saved["records"] = records
        return saved

    def _save(self, ledger):
        key = self.key(ledger["fid"], ledger["carrier_id"])
        if self.settings.value(key) != ledger:
            self.settings.setValue(key, ledger)
            self.settings.sync()  # Balance and consumed cursor are one value.

    @staticmethod
    def _anchor(feed):
        return dict(path=feed["path"], offset=len(feed["raw"]),
                    digest=hashlib.sha256(feed["raw"]).hexdigest())

    @staticmethod
    def _invalidate(ledger, symbol=None):
        for name, record in ledger["records"].items():
            if symbol is None or name == symbol:
                record.update(count=None, status="inconsistent")

    def update(self, fid, carrier_id, feed):
        ledger = self._load(fid, carrier_id)
        anchor = ledger.get("anchor")
        if not isinstance(anchor, dict) and ledger["records"]:
            self._invalidate(ledger)
        elif isinstance(anchor, dict):
            offset = anchor.get("offset")
            continuous = (feed is not None and anchor.get("path") == feed["path"]
                          and type(offset) is int and 0 <= offset <= len(feed["raw"])
                          and hashlib.sha256(feed["raw"][:offset]).hexdigest() == anchor.get("digest"))
            if not continuous:
                self._invalidate(ledger)
            else:
                self._consume(ledger, feed, offset)
        if feed is not None:
            ledger["anchor"] = self._anchor(feed)
        self._save(ledger)
        return ledger

    def confirm(self, fid, carrier_id, symbol, count, feed):
        if not fid or stable_id(carrier_id) is None or feed is None:
            raise ValueError("carrier identity or live journal unavailable")
        if symbol not in {c.symbol for c in MINING_COMMODITIES}:
            raise ValueError("unknown commodity")
        if count is not None and (type(count) is not int or count < 0 or count > 2_147_483_647):
            raise ValueError("invalid stock")
        ledger = self.update(fid, carrier_id, feed)
        if count is None:
            ledger["records"].pop(symbol, None)
        else:
            ledger["records"][symbol] = dict(count=count, status="manual",
                confirmed_at=datetime.now(timezone.utc).isoformat())
        ledger["anchor"] = self._anchor(feed)
        self._save(ledger)
        return ledger

    def _consume(self, ledger, feed, start):
        dock, srv = None, False
        for offset, event in feed["events"]:
            et = event.get("event")
            if et in ("LoadGame", "Commander", "Undocked", "FSDJump", "SupercruiseEntry", "Died"):
                dock = None
            if et == "LoadGame":
                srv = str(event.get("Ship", "")).casefold() in ("mev_rhino", "testbuggy", "combat_multicrew_srv_01")
            elif et in ("LaunchSRV", "DockSRV") and event.get("PlayerControlled", True):
                srv = et == "LaunchSRV"
            elif et == "Cargo" and event.get("Vessel") in ("Ship", "SRV"):
                srv = event["Vessel"] == "SRV"
            if et in ("Docked", "Location", "CarrierJump"):
                dock = (stable_id(event.get("MarketID")) if event.get("StationType") == "FleetCarrier"
                        and (et == "Docked" or event.get("Docked") is True) else None)
            if offset < start or et != "CargoTransfer":
                continue
            ids = [stable_id(event[k]) for k in ("CarrierID", "MarketID") if k in event]
            target = ids[0] if ids and None not in ids and len(set(ids)) == 1 else dock if not ids else None
            if target is not None and target != ledger["carrier_id"]:
                continue
            if ids and dock is not None and target != dock:
                target = None  # Conflicting stable IDs cannot establish a safe transfer.
            transfers = event.get("Transfers")
            if not isinstance(transfers, list):
                self._invalidate(ledger)
                continue
            for transfer in transfers:
                try:
                    direction = transfer.get("Direction")
                    if direction == "tosrv" or (direction == "toship" and srv):
                        continue
                    symbol = frontier_name(transfer.get("Type"))
                    amount = quantity(transfer.get("Count"))
                    record = ledger["records"].get(symbol)
                    if record is None or record.get("count") is None:
                        continue
                    if target != ledger["carrier_id"] or direction not in ("toship", "tocarrier") or srv:
                        self._invalidate(ledger, symbol)
                        continue
                    value = record["count"] + (amount if direction == "tocarrier" else -amount)
                    if not 0 <= value <= 2_147_483_647:
                        self._invalidate(ledger, symbol)
                    else:
                        record.update(count=value, status="tracked")
                except (ValueError, TypeError, AttributeError):
                    self._invalidate(ledger)

    def attach(self, inventory, ledger):
        inventory.carrier = {c.symbol: ledger["records"].get(c.symbol, {}).get("count")
                             for c in MINING_COMMODITIES}
        inventory.carrier_records = deepcopy(ledger["records"])
