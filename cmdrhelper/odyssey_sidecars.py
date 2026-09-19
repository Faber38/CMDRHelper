"""Small live personal snapshots, captured independently of the lazy UI.

Only the active journal is read (once initially, then appended complete lines).
An exact, unique trigger and its prefix digest bind each otherwise unscoped file.
No carrier inventory or market data is read or changed here.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from .odyssey_inventory import CONTAINERS, _time, validate_snapshot
from .live_journal import open_journal


def signature(path):
    stat = path.stat()
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def read_snapshot(path, expected):
    before = signature(path)
    raw = path.read_bytes()
    if signature(path) != before or len(raw) != before[2]:
        raise OSError("personal snapshot changed during read")
    def invalid_constant(value):
        raise ValueError("non-JSON numeric constant")
    event = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=invalid_constant)
    return validate_snapshot(event, expected), before


class OdysseySidecars:
    def __init__(self):
        self.path = None
        self._sig = None
        self._offset = 0
        self._digest = hashlib.sha256()
        self._identities = set()
        self._identity_time = None
        self._trusted = True
        self._latest = {}
        self._timestamps = {}
        self._attempts = {}
        self._snapshots = {}
        self.tracking_batch = None
        self._tracking_serial = 0

    @property
    def fid(self):
        return next(iter(self._identities)) if self._trusted and len(self._identities) == 1 else None

    def export(self):
        if self.path is None or self._sig is None:
            return None
        return dict(fid=self.fid, journal_file=str(self.path), journal_signature=self._sig,
                    snapshots=deepcopy(list(self._snapshots.values())) if self.fid else [])

    def _journal(self, path):
        before = signature(path)
        reset = (path != self.path or self._sig is None or before[:2] != self._sig[:2]
                 or before[2] < self._sig[2] or before != self._sig and before[2] == self._sig[2])
        if not reset and before == self._sig:
            return
        offset = 0 if reset else self._offset
        digest = hashlib.sha256() if reset else self._digest.copy()
        identities = set() if reset else set(self._identities)
        identity_time = None if reset else self._identity_time
        latest = {} if reset else dict(self._latest)
        timestamps = {} if reset else dict(self._timestamps)
        trusted = True if reset else self._trusted
        events = []
        with open_journal(path) as stream:
            stream.seek(offset)
            while True:
                start = stream.tell()
                line = stream.readline()
                if not line or not line.endswith(b"\n"):
                    break
                offset = stream.tell()
                digest.update(line)
                try:
                    event = json.loads(line)
                    kind = event.get("event")
                    events.append(dict(offset=start, end=offset, prefix=digest.hexdigest(), event=event))
                    if kind in ("Commander", "LoadGame") and event.get("FID"):
                        identities.add(event["FID"])
                        identity_time = _time(event.get("timestamp"))
                    if kind in CONTAINERS:
                        stamp = _time(event.get("timestamp"))
                        timestamps[(kind, stamp)] = timestamps.get((kind, stamp), 0) + 1
                        latest[kind] = (start, stamp, digest.hexdigest())
                except (ValueError, TypeError, AttributeError):
                    trusted = False
        if signature(path) != before:
            raise OSError("active journal changed during capture")
        if reset:
            self._attempts.clear()
            # A rotation can retain already witnessed snapshots of the same FID.
            # Rewriting the same path cannot reuse any old witness.
            if path == self.path:
                self._snapshots.clear()
        self.path, self._sig, self._offset, self._digest = path, before, offset, digest
        self._identities, self._identity_time, self._trusted = identities, identity_time, trusted
        self._latest, self._timestamps = latest, timestamps
        self._tracking_serial += 1
        self.tracking_batch = dict(serial=self._tracking_serial, reset=reset, events=events)
        if self.fid:
            self._snapshots = {name: proof for name, proof in self._snapshots.items()
                               if proof["fid"] == self.fid}

    def poll(self, journal):
        previous = (self.fid, self.path, deepcopy(self._snapshots))
        try:
            self._journal(Path(journal).resolve())
            if self.fid:
                for name, (offset, stamp, prefix) in self._latest.items():
                    if (self._identity_time is None or stamp < self._identity_time
                            or self._timestamps[(name, stamp)] != 1):
                        continue
                    path = self.path.parent / (name + ".json")
                    try:
                        sig = signature(path)
                    except OSError:
                        sig = None
                    attempt = (offset, prefix, sig)
                    if self._attempts.get(name) == attempt:
                        continue
                    self._attempts[name] = attempt
                    try:
                        event, stable_sig = read_snapshot(path, name)
                        if (_time(event["timestamp"]) != stamp or
                                event.get("FID", self.fid) != self.fid):
                            continue
                        if signature(self.path) != self._sig:
                            # Retry after consuming the new journal tail.
                            self._attempts.pop(name, None)
                            continue
                        self._snapshots[name] = dict(fid=self.fid, journal_file=str(self.path),
                            offset=offset, prefix=prefix, snapshot=event, signature=stable_sig)
                    except (OSError, ValueError, TypeError):
                        # Stable malformed files need another attempt only after
                        # their signature or the trigger changes.
                        continue
        except OSError:
            return False
        return previous != (self.fid, self.path, self._snapshots)
