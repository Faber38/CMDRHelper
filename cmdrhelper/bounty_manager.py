"""Live bounty snapshots with bounded current-journal resume; no archive/DB access."""
from copy import deepcopy
from datetime import datetime, timezone
import json
import hashlib
import logging
import os
from pathlib import Path
import re
import shutil
import tempfile
import uuid

from PySide6.QtCore import QObject, QStandardPaths, Signal
from cmdrhelper.journal_files import journal_files, journal_sort_key

logger = logging.getLogger(__name__)
UNKNOWN_FACTION = ""  # Translate only for display; never persist translated keys.


def _amount(value):
    return type(value) is int and value >= 0


class BountyManager(QObject):
    changed = Signal()

    def __init__(self, root=None, parent=None):
        super().__init__(parent)
        self._root = Path(root) if root is not None else None
        self.fid = ""
        self.states = {}
        self.damaged = set()
        self.known_snapshots = set()
        self.storage_errors = set()
        self.cursors = {}
        self.boundary = None
        self.initial_path = None
        self.armed = False

    @property
    def storage_error(self):
        return self.fid in self.storage_errors

    @property
    def root(self):
        if self._root is None:
            location = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            if not location:
                raise OSError("AppDataLocation is unavailable")
            return Path(location) / "bounties"
        return self._root

    @staticmethod
    def _valid_fid(fid):
        return isinstance(fid, str) and re.fullmatch(r"[A-Za-z0-9_-]+", fid) is not None

    @staticmethod
    def _empty(fid, name="", uncertain=False):
        return dict(schema=1, fid=fid, commander_name=name, updated_at="",
                    total=0, factions={}, uncertain=uncertain, from_now=True,
                    last_reset="", last_event=None)

    def _load(self, fid, name):
        empty = self._empty(fid, name)
        try:
            data = json.loads((self.root / f"{fid}.json").read_text(encoding="utf-8"))
            if (not isinstance(data, dict) or type(data.get("schema")) is not int
                    or data["schema"] != 1 or data.get("fid") != fid
                    or not isinstance(data.get("commander_name"), str)
                    or not isinstance(data.get("updated_at"), str)
                    or not _amount(data.get("total"))
                    or not isinstance(data.get("factions"), dict)
                    or any(not isinstance(k, str) or not _amount(v)
                           for k, v in data["factions"].items())
                    or sum(data["factions"].values()) != data["total"]
                    or type(data.get("uncertain", False)) is not bool
                    or type(data.get("from_now", False)) is not bool
                    or data.get("last_reset", "") not in ("", "manual", "died", "redeemed")):
                raise ValueError("Invalid bounty snapshot")
            last = data.get("last_event")
            empty.update({key: data[key] for key in empty if key in data})
            if last is not None and not self._valid_anchor(last):
                logger.warning("Invalid bounty journal anchor for FID %s; keeping balance", fid)
                empty.update(last_event=None, uncertain=True, from_now=False)
            self.known_snapshots.add(fid)
            return empty
        except FileNotFoundError:
            return empty
        except (OSError, ValueError, TypeError):
            logger.exception("Cannot load bounty snapshot for FID %s", fid)
            self.damaged.add(fid)
            empty["uncertain"] = True
            empty["from_now"] = False
            return empty

    @staticmethod
    def _valid_anchor(anchor):
        return (isinstance(anchor, dict) and isinstance(anchor.get("file"), str)
                and _amount(anchor.get("offset"))
                and isinstance(anchor.get("prefix_sha256"), str)
                and re.fullmatch(r"[a-f0-9]{64}", anchor["prefix_sha256"]) is not None)

    def identify(self, fid, name="", path=None):
        """Use the existing FID index and resume only its current journal."""
        if not self._valid_fid(fid):
            return
        name = name if isinstance(name, str) else ""
        if fid not in self.states:
            self.states[fid] = self._load(fid, name)
        changed = self.fid != fid
        self.fid = fid
        self.states[fid]["commander_name"] = name or self.states[fid]["commander_name"]
        # Only the startup tail may obtain its identity from the existing index.
        # New files establish their own identity through Commander/LoadGame.
        key = str(Path(path)) if path else None
        if key == self.initial_path and key in self.cursors:
            cursor = self.cursors[key]
            if not cursor["fid"]:
                cursor["fid"], cursor["name"] = fid, name
            if not cursor["ready"] and self._initialize_current(Path(key), cursor):
                self.consume([Path(key)])
        if changed:
            self.changed.emit()

    def snapshot(self):
        return deepcopy(self.states.get(self.fid, self._empty("")))

    def _save(self, data):
        directory = self.root
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f'{data["fid"]}.json'
        if data["fid"] in self.damaged and target.exists():
            # Preserve the original bytes before replacing a damaged snapshot.
            backup = target.with_name(target.name + f".corrupt-{uuid.uuid4().hex}")
            with target.open("rb") as source, backup.open("xb") as dest:
                shutil.copyfileobj(source, dest)
                dest.flush()
                os.fsync(dest.fileno())
            self.damaged.discard(data["fid"])
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory,
                                             prefix=".bounty-", suffix=".tmp", delete=False) as stream:
                temporary = stream.name
                json.dump(data, stream, ensure_ascii=False, allow_nan=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)

    @staticmethod
    def _is_reset(event):
        return event.get("event") == "Died" or (event.get("event") == "RedeemVoucher"
                and str(event.get("Type", "")).casefold() == "bounty")

    def apply(self, fid, name, event, source, offset, prefix_sha256):
        """Commit one event and its identity together; failure leaves it retryable."""
        kind = event.get("event")
        reset = self._is_reset(event)
        if kind != "Bounty" and not reset:
            return True
        if not self._valid_fid(fid):
            logger.warning("Ignoring live bounty event without an identified FID")
            return True
        self.identify(fid, name)
        previous = self.states[fid]
        last = previous["last_event"]
        if (last and last["file"] == source and offset <= last["offset"]
                and (offset < last["offset"]
                     or last.get("prefix_sha256") == prefix_sha256)):
            return True
        data = deepcopy(previous)
        if reset:
            data.update(total=0, factions={}, uncertain=False, from_now=False,
                        last_reset="died" if kind == "Died" else "redeemed")
        else:
            rewards = event.get("Rewards")
            if (not isinstance(rewards, list) or not rewards
                    or any(not isinstance(r, dict) or not _amount(r.get("Reward")) for r in rewards)
                    or not _amount(event.get("TotalReward"))
                    or sum(r["Reward"] for r in rewards) != event["TotalReward"]):
                logger.error("Invalid live Bounty rewards at %s:%s", source, offset)
                data["uncertain"] = True
            else:
                for reward in rewards:
                    faction = reward.get("Faction")
                    faction = faction.strip() if isinstance(faction, str) else UNKNOWN_FACTION
                    if reward["Reward"]:
                        data["factions"][faction] = data["factions"].get(faction, 0) + reward["Reward"]
                data["total"] = sum(data["factions"].values())
        data["last_event"] = dict(file=source, offset=offset, prefix_sha256=prefix_sha256)
        return self._commit(fid, data)

    def _commit(self, fid, data):
        previous = self.states[fid]
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.states[fid] = data
        try:
            self._save(data)
        except OSError:
            self.states[fid] = previous
            self.storage_errors.add(fid)
            logger.exception("Cannot persist live bounty event; cursor not acknowledged")
            self.changed.emit()
            return False
        self.storage_errors.discard(fid)
        self.known_snapshots.add(fid)
        self.changed.emit()
        return True

    def _initialize_current(self, path, cursor):
        """One startup read of CURRENT journal only. Hash old bytes, replay only
        a verified suffix; otherwise look for its last explicit reset for FID.
        Never open the file named by an old snapshot's anchor.
        """
        fid = cursor["fid"]
        if not fid:
            return False
        try:
            before = path.stat()
            raw = path.read_bytes()
            after = path.stat()
            if ((before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)
                    or after.st_size < len(raw)):
                raise OSError("Current journal changed during resume")
            complete = raw.rfind(b"\n") + 1
            state = self.states[fid]
            anchor = state["last_event"]
            valid = (self._valid_anchor(anchor) and anchor["file"] == str(path)
                     and anchor["offset"] <= complete
                     and (anchor["offset"] == 0 or raw[anchor["offset"]-1:anchor["offset"]] == b"\n")
                     and hashlib.sha256(raw[:anchor["offset"]]).hexdigest() == anchor["prefix_sha256"])
            start = anchor["offset"] if valid else None
            if not valid:
                # The index supplied this file's FID. Explicit identity records
                # still prevent another Commander's reset from becoming ours.
                identity = fid
                position = 0
                # A manual reset has no journal event. An invalid anchor in
                # that same file must not resurrect kills before that reset.
                manual_boundary = (state["last_reset"] == "manual"
                                   and (anchor is None or anchor.get("file") == str(path)))
                for line in raw[:complete].splitlines(keepends=True):
                    try:
                        event = json.loads(line)
                        if not isinstance(event, dict):
                            raise ValueError("Expected journal object")
                        if event.get("event") in ("Commander", "LoadGame"):
                            identity = event.get("FID", "")
                        if identity == fid and self._is_reset(event) and not manual_boundary:
                            start = position
                    except (ValueError, UnicodeError):
                        pass
                    position += len(line)
                if start is None:
                    # No safe null point: keep the old balance, acknowledge EOF
                    # and explicitly record a gap (or first capture from now).
                    start = complete
                    data = deepcopy(state)
                    existing = fid in self.known_snapshots or fid in self.damaged
                    data.update(uncertain=existing, from_now=not existing,
                                last_event=dict(file=str(path), offset=start,
                                                prefix_sha256=hashlib.sha256(raw[:start]).hexdigest()))
                    if not self._commit(fid, data):
                        return False
                else:
                    # Discard only the unusable dedup anchor in memory. The
                    # actual reset + its new anchor are committed together.
                    self.states[fid] = deepcopy(state)
                    self.states[fid]["last_event"] = None
            cursor.update(offset=start, digest=hashlib.sha256(raw[:start]),
                          identity=(after.st_dev, after.st_ino), ready=True, checkpoint=True)
            return True
        except OSError:
            logger.exception("Cannot resume current bounty journal %s", path)
            return False

    def manual_reset(self, expected_fid):
        """Reset only after UI confirmation, anchored to this current file's EOF.

        Read-only journal access also includes complete events not delivered by
        the watcher yet. A changed Commander or unverified file fails closed.
        """
        if not expected_fid or self.fid != expected_fid or not self.cursors:
            return False
        key = max(self.cursors, key=lambda item: journal_sort_key(Path(item)))
        cursor = self.cursors[key]
        if cursor["fid"] != expected_fid or not cursor["ready"] or cursor["blocked"]:
            return False
        try:
            path = Path(key)
            stat = path.stat()
            raw = path.read_bytes()
            after = path.stat()
            if ((stat.st_dev, stat.st_ino) != cursor["identity"]
                    or (after.st_dev, after.st_ino) != cursor["identity"]
                    or len(raw) < cursor["offset"] or after.st_size < len(raw)
                    or hashlib.sha256(raw[:cursor["offset"]]).hexdigest() != cursor["digest"].hexdigest()):
                raise ValueError("Cannot verify current journal for manual reset")
            complete = raw.rfind(b"\n") + 1
            for line in raw[cursor["offset"]:complete].splitlines():
                event = json.loads(line)
                if (not isinstance(event, dict) or (event.get("event") in ("Commander", "LoadGame")
                        and event.get("FID") != expected_fid)):
                    raise ValueError("Current journal identity changed during reset")
            digest = hashlib.sha256(raw[:complete])
            data = deepcopy(self.states[expected_fid])
            data.update(total=0, factions={}, uncertain=False, from_now=False, last_reset="manual",
                        last_event=dict(file=key, offset=complete, prefix_sha256=digest.hexdigest()))
            if not self._commit(expected_fid, data):
                return False
            cursor.update(offset=complete, digest=digest, checkpoint=False)
            return True
        except (OSError, ValueError, UnicodeError):
            logger.exception("Cannot safely reset bounty snapshot for FID %s", expected_fid)
            return False

    def set_folder(self, folder):
        """Set an EOF boundary using names/stat only; never open old journals."""
        self.cursors.clear()
        self.boundary = self.initial_path = None
        self.armed = False
        self.fid = ""
        self.changed.emit()
        if not folder:
            return
        try:
            paths = journal_files(Path(folder))
            if paths:
                current = paths[-1]
                self.boundary = journal_sort_key(current)
                self.initial_path = str(current)
                self.cursors[str(current)] = self._cursor(current, current.stat().st_size, ready=False)
            self.armed = True
        except OSError:
            logger.exception("Cannot establish live bounty EOF boundary; tracking disabled")

    @staticmethod
    def _cursor(path, offset=0, ready=True):
        stat = path.stat()
        return dict(offset=offset, identity=(stat.st_dev, stat.st_ino),
                    fid="", name="", blocked=False, ready=ready,
                    digest=hashlib.sha256(), checkpoint=False)

    def consume(self, paths):
        """Called only on an existing watcher's change notification, never a timer.

        Byte offsets and complete-line boundaries mirror read_journal_delta.
        Unlike the archive reader, truncation must NEVER rewind to byte zero.
        """
        if not self.armed:
            return True
        candidates = {str(Path(p)): Path(p) for p in paths
                      if self.boundary is None or journal_sort_key(Path(p)) > self.boundary
                      or str(Path(p)) in self.cursors}
        # Drain the preceding live file once more on rotation (late tail).
        candidates.update({key: Path(key) for key in self.cursors})
        previous = None
        for key, path in sorted(candidates.items(), key=lambda item: journal_sort_key(item[1])):
            try:
                if key not in self.cursors:
                    self.cursors[key] = self._cursor(path)
                    self.cursors[key]["checkpoint"] = True
                    # Numbered parts belong to the same Elite session only.
                    if previous and path.name.rsplit(".", 2)[0] == previous[0].name.rsplit(".", 2)[0]:
                        self.cursors[key].update(fid=previous[1]["fid"], name=previous[1]["name"])
                cursor = self.cursors[key]
                previous = path, cursor
                if not cursor["ready"]:
                    if not cursor["fid"]:
                        continue  # Wait for the existing index's identity.
                    if not self._initialize_current(path, cursor):
                        return False
                stat = path.stat()
                if cursor["blocked"]:
                    continue
                if (stat.st_dev, stat.st_ino) != cursor["identity"] or stat.st_size < cursor["offset"]:
                    logger.error("Live bounty journal replaced/truncated; not replaying %s", path)
                    cursor["blocked"] = True
                    if cursor["fid"] in self.states:
                        self.states[cursor["fid"]]["uncertain"] = True
                        self.changed.emit()
                    continue
                with path.open("rb") as stream:
                    stream.seek(cursor["offset"])
                    while True:
                        line = stream.readline()
                        if not line.endswith(b"\n"):
                            break
                        end = stream.tell()
                        digest = cursor["digest"].copy()
                        digest.update(line)
                        try:
                            event = json.loads(line)
                            if not isinstance(event, dict):
                                raise ValueError("Expected journal object")
                        except (ValueError, UnicodeError):
                            logger.error("Invalid new live journal line at %s:%s", key, end)
                            if cursor["fid"] in self.states:
                                data = deepcopy(self.states[cursor["fid"]])
                                data.update(uncertain=True, last_event=dict(
                                    file=key, offset=end, prefix_sha256=digest.hexdigest()))
                                if not self._commit(cursor["fid"], data):
                                    return False
                            cursor["offset"] = end
                            cursor["digest"] = digest
                            continue
                        if event.get("event") in ("Commander", "LoadGame"):
                            fid = event.get("FID", "")
                            cursor["fid"] = fid if self._valid_fid(fid) else ""
                            cursor["name"] = event.get("Name") or event.get("Commander") or ""
                            self.identify(cursor["fid"], cursor["name"])
                        if not self.apply(cursor["fid"], cursor["name"], event, key, end, digest.hexdigest()):
                            return False
                        cursor["offset"] = end
                        cursor["digest"] = digest
                if cursor["checkpoint"] and cursor["fid"] in self.states:
                    data = deepcopy(self.states[cursor["fid"]])
                    anchor = dict(file=key, offset=cursor["offset"],
                                  prefix_sha256=cursor["digest"].hexdigest())
                    if data["last_event"] != anchor:
                        data["last_event"] = anchor
                        if not self._commit(cursor["fid"], data):
                            return False
                    cursor["checkpoint"] = False
            except OSError:
                logger.exception("Cannot consume live bounty journal %s", path)
                return False
        # Retain just the current and preceding file, not a growing archive index.
        keys = sorted(self.cursors, key=lambda key: journal_sort_key(Path(key)))
        for key in keys[:-2]:
            del self.cursors[key]
        if keys:
            self.boundary = journal_sort_key(Path(keys[-1]))
        return True
