"""Manually anchored carrier ledger with verified, indexed journal continuation."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import logging
from itertools import chain
from pathlib import Path

from .material_inventory import frontier_name, quantity
from .mining_catalog import MINING_COMMODITIES
from .journal_files import journal_sort_key
from .mining_persistence import save_values

logger = logging.getLogger(__name__)


def journal_successor(previous, current):
    """Known filenames must form consecutive parts or a new session's first part."""
    before, after = journal_sort_key(previous), journal_sort_key(current)
    return (before[0] == after[0] == 1 and
            ((before[1] == after[1] and after[2] == before[2] + 1)
             or (after[1] > before[1] and after[2] == 1)))


def read_carrier_feed(path, fid):
    if not path:
        return None
    try:
        path = Path(path).resolve()
        before = path.stat()
        raw = path.read_bytes()
        complete = raw.endswith(b"\n")
        after = path.stat()
        if (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            return None
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
        return dict(path=str(path), raw=raw, events=events, complete=complete)
    except (OSError, ValueError, TypeError):
        return None


def _read_safe_preamble(path, rows):
    """Verify an indexed, closed intermediate file; unknown events fail closed."""
    if any(row.get("attribution_status") != "unknown"
           or row.get("commander_id") is not None or row.get("fid_seen")
           or row.get("commander_name_seen") for row in rows):
        return None
    try:
        path = Path(path)
        before = path.stat()
        # Require unchanged index evidence as well as stability during reading.
        if any(row.get("file_size") != before.st_size
               or row.get("modified_ns") != before.st_mtime_ns for row in rows):
            return None
        raw = path.read_bytes()
        events, offset = [], 0
        if not raw.endswith(b"\n") or len(raw) != before.st_size:
            return None
        for line in raw.splitlines(keepends=True):
            event = json.loads(line)
            if not isinstance(event, dict) or event.get("event") not in ("Fileheader", "Friends"):
                return None
            events.append((offset, event))
            offset += len(line)
        if not events or events[0][1]["event"] != "Fileheader":
            return None
        after = path.stat()
        signature = lambda stat: (stat.st_dev, stat.st_ino, stat.st_size,
                                  stat.st_mtime_ns, stat.st_ctime_ns)
        if signature(before) != signature(after):
            return None
        return dict(path=str(path), raw=raw, events=events, complete=True)
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
        return self.normalize(fid, carrier_id, saved)

    @staticmethod
    def normalize(fid, carrier_id, saved):
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
            last = record.get("last_confirmed", count)
            if (record.get("status") not in ("manual", "tracked", "inconsistent")
                    or not isinstance(record.get("confirmed_at"), str)
                    or (count is not None and (type(count) is not int or not 0 <= count <= 2_147_483_647))):
                record = dict(count=None, status="inconsistent", confirmed_at="")
            records[symbol] = record
            record["last_confirmed"] = (last if type(last) is int and 0 <= last <= 2_147_483_647 else None)
            resume = record.get("resume_count")
            if (record.get("status") != "inconsistent" or count is not None
                    or type(resume) is not int or not 0 <= resume <= 2_147_483_647):
                record.pop("resume_count", None)
            if record.get("status") == "inconsistent":
                record["count"] = None
        saved["records"] = records
        return saved

    def _save(self, ledger):
        key = self.key(ledger["fid"], ledger["carrier_id"])
        save_values(self.settings, {key: ledger})

    @staticmethod
    def _anchor(feed):
        return dict(path=feed["path"], offset=len(feed["raw"]),
                    digest=hashlib.sha256(feed["raw"]).hexdigest())

    @staticmethod
    def _invalidate(ledger, symbol=None, *, continuity=False):
        for name, record in ledger["records"].items():
            if symbol is None or name == symbol:
                if continuity and record.get("count") is not None:
                    record["resume_count"] = record["count"]
                elif not continuity:
                    record.pop("resume_count", None)
                record.update(count=None, status="inconsistent")

    def update(self, fid, carrier_id, feed, *, sessions=None):
        ledger = self._load(fid, carrier_id)
        ledger = self.advance(ledger, feed, sessions=sessions)
        self._save(ledger)
        return ledger

    def advance(self, ledger, feed, *, sessions=None):
        """Pure ledger calculation; indexed catch-up is called in the reader worker.

        On an unavailable chain retain both the old cursor and its resumable
        balance. Never use the manual confirmation alone to fill a journal gap.
        """
        ledger = deepcopy(ledger)
        anchor = ledger.get("anchor")
        if not isinstance(anchor, dict) and ledger["records"]:
            self._invalidate(ledger)
        elif isinstance(anchor, dict):
            offset = anchor.get("offset")
            remaining = iter(self._chain(ledger, feed, sessions) or [])
            first = next(remaining, None)
            continuous = (first and type(offset) is int and 0 <= offset <= len(first["raw"])
                          and (offset == 0 or first["raw"][offset - 1:offset] == b"\n")
                          and hashlib.sha256(first["raw"][:offset]).hexdigest() == anchor.get("digest"))
            if not continuous:
                self._invalidate(ledger, continuity=True)
                logger.info("Carrier continuity unclear; last confirmation retained, stock remains unknown")
                return ledger
            else:
                baseline = deepcopy(ledger)
                for record in ledger["records"].values():
                    if "resume_count" in record:
                        record.update(count=record.pop("resume_count"), status="tracked")
                context = ledger.get("context")
                if not (isinstance(context, (tuple, list)) and len(context) == 2
                        and (context[0] is None or stable_id(context[0]) is not None)
                        and type(context[1]) is bool):
                    context = None
                for index, part in enumerate(chain((first,), remaining)):
                    if part is None or (part["path"] != feed["path"] and not part.get("complete")):
                        # Discard all tentative deltas if a later file is bad.
                        self._invalidate(baseline, continuity=True)
                        logger.info("Carrier continuity unclear; last confirmation retained, stock remains unknown")
                        return baseline
                    context = self._consume(ledger, part, offset if index == 0 else 0, context)
                ledger["context"] = list(context)
                if index > 0:
                    logger.info("Carrier anchor continued; continuity across sessions verified")
        if feed is not None:
            ledger["anchor"] = self._anchor(feed)
        return ledger

    @staticmethod
    def _chain(ledger, feed, sessions):
        if feed is None:
            return None
        anchor_path = ledger["anchor"].get("path")
        if anchor_path == feed["path"]:
            return [feed]
        rows = {}
        for row in sessions or []:
            path = str(Path(row["journal_file"]).resolve())
            rows.setdefault(path, []).append(row)
        ordered = sorted(rows, key=journal_sort_key)
        if anchor_path not in rows or feed["path"] not in rows:
            return None
        start, end = ordered.index(anchor_path), ordered.index(feed["path"])
        if start >= end:
            return None
        paths = ordered[start:end + 1]
        if any(not journal_successor(a, b) for a, b in zip(paths, paths[1:])):
            return None
        preambles = set()
        for path in paths:
            if any(row.get("fid_seen") != ledger["fid"] or row.get("attribution_status") != "identified"
                   for row in rows[path]):
                # Never exempt the anchor or live feed. Only strictly intermediate,
                # genuinely unattributed files may pass the narrow content check.
                if path in (anchor_path, feed["path"]):
                    return None
                preambles.add(path)
        # Validate preambles lazily with the other chain parts. Any failed read
        # rolls back tentative deltas through advance's existing baseline path.
        return (feed if path == feed["path"] else
                _read_safe_preamble(path, rows[path]) if path in preambles else
                read_carrier_feed(path, ledger["fid"]) for path in paths)

    def confirm(self, fid, carrier_id, symbol, count, feed):
        if not fid or stable_id(carrier_id) is None or feed is None:
            raise ValueError("carrier identity or live journal unavailable")
        if symbol not in {c.symbol for c in MINING_COMMODITIES}:
            raise ValueError("unknown commodity")
        if count is not None and (type(count) is not int or count < 0 or count > 2_147_483_647):
            raise ValueError("invalid stock")
        ledger = self.update(fid, carrier_id, feed)
        new_anchor = self._anchor(feed)
        if ledger.get("anchor") != new_anchor:
            # A new manual baseline cannot repair the missing history of other
            # commodities. Their saved retry counts belong to the OLD cursor.
            self._invalidate(ledger)
            ledger.pop("context", None)
        if count is None:
            ledger["records"].pop(symbol, None)
        else:
            ledger["records"][symbol] = dict(count=count, last_confirmed=count, status="manual",
                confirmed_at=datetime.now(timezone.utc).isoformat())
        ledger["anchor"] = new_anchor
        if "context" not in ledger:
            ledger["context"] = list(self._consume(ledger, feed, len(feed["raw"])))
        self._save(ledger)
        return ledger

    def _consume(self, ledger, feed, start, context=None):
        dock, srv = context if context is not None else (None, False)
        for offset, event in feed["events"]:
            if context is not None and offset < start:
                continue
            et = event.get("event")
            if et in ("Undocked", "FSDJump", "SupercruiseEntry", "Died"):
                dock = None
            if et in ("Commander", "LoadGame") and event.get("FID") != ledger["fid"]:
                dock = None
            if et == "LoadGame":
                srv = str(event.get("Ship", "")).casefold() in ("mev_rhino", "testbuggy", "combat_multicrew_srv_01")
            elif et in ("LaunchSRV", "DockSRV") and event.get("PlayerControlled", True):
                srv = et == "LaunchSRV"
            elif et == "Cargo" and event.get("Vessel") in ("Ship", "SRV"):
                srv = event["Vessel"] == "SRV"
            if et in ("Docked", "Location", "CarrierJump"):
                market = stable_id(event.get("MarketID"))
                station = event.get("StationType")
                if market is not None:
                    if station == "FleetCarrier" and (et == "Docked" or event.get("Docked") is True):
                        dock = market
                    elif market != dock or (station and station != "FleetCarrier") or event.get("Docked") is False:
                        dock = None
                elif (event.get("Docked") is False
                      or (isinstance(station, str) and station and station != "FleetCarrier")):
                    dock = None
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
                        logger.debug("Carrier transfer applied after confirmed journal cursor")
                except (ValueError, TypeError, AttributeError):
                    self._invalidate(ledger)
        return dock, srv

    def attach(self, inventory, ledger):
        inventory.carrier = {c.symbol: ledger["records"].get(c.symbol, {}).get("count")
                             for c in MINING_COMMODITIES}
        inventory.carrier_records = deepcopy(ledger["records"])
