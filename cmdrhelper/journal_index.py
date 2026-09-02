from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path

from cmdrhelper.journal_files import journal_sort_key
from cmdrhelper.journal_reader import classify_journal_file


def should_show_index_progress(total: int, work: int) -> bool:
    """Sichtbar nur für einen Erstaufbau oder mindestens 25 Prüfungen."""
    total, work = max(0, int(total)), max(0, int(work))
    return work >= 25 or (work > 0 and work == total)


def journal_index_plan(database, folder: Path) -> tuple[int, int]:
    """Metadaten-Preflight ohne Dateiinhalt zu öffnen oder zu hashen."""
    folder = Path(folder)
    database.ensure_schema_v10()
    with database._connect() as con:
        rows = con.execute(
            """SELECT journal_file, file_size, modified_ns, sha256,
                      fully_imported FROM journal_sessions"""
        ).fetchall()
    cached = {str(row[0]): row for row in rows}
    total = changed = 0
    with os.scandir(folder) as iterator:
        for entry in iterator:
            if not (entry.is_file(follow_symlinks=False)
                    and entry.name.startswith("Journal.")
                    and entry.name.endswith(".log")):
                continue
            total += 1
            stat = entry.stat(follow_symlinks=False)
            old = cached.get(str(Path(entry.path)))
            if (old is None or not old[3] or not bool(old[4])
                    or int(old[1] or 0) != int(stat.st_size)
                    or int(old[2] or 0) != int(stat.st_mtime_ns)):
                changed += 1
    return total, changed


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _complete_line_offset(path: Path, start: int = 0) -> int:
    """Liefert das Ende der letzten newline-terminierten Bytezeile."""
    complete = max(0, int(start))
    with path.open("rb") as handle:
        handle.seek(complete)
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            newline = block.rfind(b"\n")
            if newline >= 0:
                complete = handle.tell() - len(block) + newline + 1
    return complete


def scan_journal_folder(database, folder: Path, progress_callback=None):
    """Ein scandir-Pass; unveränderte Dateien werden weder geöffnet noch gehasht."""
    folder = Path(folder)
    database.ensure_schema_v10()
    with database._connect() as con:
        rows = con.execute(
            """SELECT journal_file, file_size, modified_ns, sha256,
                      commander_id, fid_seen, commander_name_seen,
                      first_event_at, last_event_at, attribution_status,
                      last_read_offset, last_complete_line_offset, fully_imported
                 FROM journal_sessions"""
        ).fetchall()
    cached = {str(row[0]): row for row in rows}

    entries = []
    with os.scandir(folder) as iterator:
        for entry in iterator:
            if entry.is_file(follow_symlinks=False) and (
                entry.name.startswith("Journal.") and entry.name.endswith(".log")
            ):
                stat = entry.stat(follow_symlinks=False)
                entries.append((Path(entry.path), int(stat.st_size), int(stat.st_mtime_ns)))
    entries.sort(key=lambda item: journal_sort_key(item[0]))

    result = []
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    total = len(entries)
    for number, (path, size, modified_ns) in enumerate(entries, 1):
        old = cached.get(str(path))
        if (old is not None and old[3]
                and int(old[1] or 0) == size
                and int(old[2] or 0) == modified_ns):
            session = {
                "journal_file": str(path), "file_size": size,
                "modified_ns": modified_ns, "sha256": old[3],
                "commander_id": old[4], "fid_seen": old[5],
                "commander_name_seen": old[6], "first_event_at": old[7],
                "last_event_at": old[8], "attribution_status": old[9],
                "last_read_offset": int(old[10] or 0),
                "last_complete_line_offset": int(old[11] or 0),
                "fully_imported": bool(old[12]), "unchanged": True,
            }
        else:
            digest = _sha256(path)
            # Gleicher Inhalt mit lediglich abweichender mtime: Metadaten
            # aktualisieren, ohne erneut zu klassifizieren.
            if old is not None and old[3] and old[3] == digest:
                session = {
                    "journal_file": str(path), "file_size": size,
                    "modified_ns": modified_ns, "sha256": digest,
                    "commander_id": old[4], "fid_seen": old[5],
                    "commander_name_seen": old[6], "first_event_at": old[7],
                    "last_event_at": old[8], "attribution_status": old[9],
                    "last_read_offset": int(old[10] or 0),
                    "last_complete_line_offset": int(old[11] or 0),
                    "fully_imported": bool(old[12]), "unchanged": True,
                }
            else:
                session = classify_journal_file(path)
                complete = _complete_line_offset(path)
                processed = 0
                if old is not None and size >= int(old[1] or 0):
                    processed = min(int(old[10] or 0), complete)
                session.update({
                    "sha256": digest,
                    "last_read_offset": processed,
                    "last_complete_line_offset": complete,
                    "fully_imported": False,
                    "unchanged": False,
                })
            session["last_indexed_at"] = now
            database.store_journal_session(session)
            session["commander_id"] = database.resolve_session_commander(session)
        result.append(session)
        if progress_callback:
            progress_callback(number, total, path.name)
    return result
