"""Last reported mode, reconstructed without persisting a second journal index."""
from datetime import datetime
from functools import lru_cache
from pathlib import Path
import json


def _timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return stamp if stamp.tzinfo is not None else None
    except ValueError:
        return None


@lru_cache(maxsize=4096)
def _file_mode(path, size, modified_ns):
    """Cache only a compact summary; revalidate identity across the whole file."""
    identities = set()
    latest = None
    with Path(path).open("rb") as handle:
        for line in handle:
            # Incomplete live writes must wait for the terminating newline.
            if not line.endswith(b"\n"):
                continue
            if b'LoadGame' not in line and b'Commander' not in line:
                continue
            try:
                event = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                continue
            if not isinstance(event, dict):
                continue
            if event.get("event") not in ("Commander", "LoadGame"):
                continue
            fid = str(event.get("FID") or "").strip()
            if fid:
                identities.add(fid)
            if event.get("event") != "LoadGame" or not fid:
                continue
            mode = event.get("GameMode")
            stamp = _timestamp(event.get("timestamp"))
            if mode not in ("Open", "Solo", "Group") or stamp is None:
                continue
            group = event.get("Group", "") if mode == "Group" else ""
            if not isinstance(group, str):
                continue
            if latest is None or stamp >= latest[0]:
                latest = (stamp, fid, mode, group, event["timestamp"])
    if latest is not None and identities == {latest[1]}:
        return latest
    return None


def reconstruct_game_mode(sessions, fid):
    """Use the newest valid LoadGame of this FID, including repeated logins."""
    result = {"game_mode": "", "group_name": "", "game_mode_timestamp": ""}
    if not fid:
        return result
    latest = None
    for session in sessions:
        if (session.get("attribution_status") != "identified"
                or session.get("fid_seen") != fid):
            continue
        path = Path(session["journal_file"])
        try:
            stat = path.stat()
            candidate = _file_mode(str(path), stat.st_size, stat.st_mtime_ns)
        except OSError:
            # An unavailable historical journal cannot establish a mode.
            continue
        if candidate is not None and candidate[1] == fid:
            if latest is None or candidate[0] >= latest[0]:
                latest = candidate
    if latest is not None:
        result.update(game_mode=latest[2], group_name=latest[3],
                      game_mode_timestamp=latest[4])
    return result
