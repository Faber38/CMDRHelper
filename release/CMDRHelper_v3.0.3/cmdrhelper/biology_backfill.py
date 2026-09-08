"""Explicit, insert-only recovery of durable BIO findings from read journals.

Uses plain SQLite connections: preview and application never initialize or
migrate the user's database. No journal offsets or sale inventories are changed.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from cmdrhelper.database import _biology_from_event, _store_biology_rows


def plan_biology_backfill(con, commander_id, *, journals=None,
                         system_address=None, body_id=None):
    """Read a bounded, identity-checked journal prefix and return missing rows."""
    commander_id = int(commander_id)
    commander = con.execute("SELECT fid FROM commanders WHERE id=?", (commander_id,)).fetchone()
    if commander is None:
        raise ValueError("Commander does not exist")
    allowed = None if journals is None else {str(Path(p).resolve()) for p in journals}
    sessions = con.execute("""SELECT journal_file,last_read_offset,
        last_complete_line_offset,fully_imported FROM journal_sessions
        WHERE commander_id=? AND attribution_status='identified'
        ORDER BY journal_file""", (commander_id,)).fetchall()
    findings = {}
    checked = []
    ranks = {"log": 1, "sample": 2, "analyse": 3, "analyze": 3}
    for filename, read_offset, complete_offset, fully_imported in sessions:
        if allowed is not None and str(Path(filename).resolve()) not in allowed:
            continue
        limit = int(complete_offset if fully_imported else read_offset or 0)
        if limit <= 0:
            continue
        # A missing, shortened or corrupt selected journal aborts the plan.
        with Path(filename).open("rb") as handle:
            raw = handle.read(limit)
        if len(raw) != limit or not raw.endswith(b"\n"):
            raise ValueError(f"Journal prefix is incomplete: {filename}")
        events = [json.loads(line) for line in raw.splitlines() if line.strip()]
        identities = {str(e["FID"]) for e in events
                      if e.get("event") in ("Commander", "LoadGame") and e.get("FID")}
        if identities != {str(commander[0])}:
            raise ValueError(f"Journal identity does not match commander: {filename}")
        checked.append(filename)
        for event in events:
            # Do not infer body/system from flight context during a repair.
            entry = _biology_from_event(event)
            if entry is None or not entry["timestamp"]:
                continue
            if system_address is not None and entry["system_address"] != system_address:
                continue
            if body_id is not None and entry["body_id"] != body_id:
                continue
            key = (commander_id, entry["system_address"], entry["body_id"],
                   entry["genus"], entry["species"], entry["variant"])
            ts = entry["timestamp"]
            previous = findings.get(key)
            if previous is None:
                findings[key] = [entry["scan_type"], ts, ts]
            else:
                if ranks[entry["scan_type"].casefold()] > ranks[previous[0].casefold()]:
                    previous[0] = entry["scan_type"]
                previous[1] = min(previous[1], ts)
                previous[2] = max(previous[2], ts)
    if allowed is not None and allowed != {str(Path(p).resolve()) for p in checked}:
        raise ValueError("Not all requested journals have an identified, already read prefix")
    missing = []
    for key, progress in sorted(findings.items()):
        exists = con.execute("""SELECT 1 FROM biology WHERE commander_id=?
            AND system_address=? AND body_id=? AND genus=? AND species=? AND variant=?""",
            key).fetchone()
        if exists is None:
            missing.append((*key, *progress))
    return {"journals": checked, "identified_findings": len(findings), "missing": missing}


def backfill_biology(database, commander_id, *, apply=False, backup_path=None, **scope):
    """Preview by default; apply under a write lock after a consistent backup."""
    path = Path(database).resolve()
    uri = path.as_uri() + ("?mode=rw" if apply else "?mode=ro")
    with closing(sqlite3.connect(uri, uri=True)) as con:
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("BEGIN IMMEDIATE" if apply else "BEGIN")
        try:
            plan = plan_biology_backfill(con, commander_id, **scope)
            result = {**plan, "inserted": 0, "backup": None}
            if apply and plan["missing"]:
                backup = Path(backup_path) if backup_path else path.with_name(
                    path.name + ".pre-biology-" + datetime.now(timezone.utc).strftime(
                        "%Y%m%dT%H%M%S%fZ") + ".bak")
                # Refuse to overwrite any backup. A second read connection can
                # back up the pre-write state while BEGIN IMMEDIATE excludes writers.
                with backup.open("xb"):
                    pass
                with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as source:
                    with closing(sqlite3.connect(backup)) as dest:
                        source.backup(dest)
                        if dest.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                            raise ValueError("Backup integrity check failed")
                result["backup"] = str(backup)
                result["inserted"] = _store_biology_rows(con, plan["missing"], missing_only=True)
            con.commit()
            return result
        except Exception:
            con.rollback()
            raise
