"""Explicit recovery of system stays from identity-checked, committed journals.

Uses plain SQLite without schema initialization; only system_visits is changed.
"""
import sqlite3
from contextlib import closing
from pathlib import Path

from cmdrhelper.backfill_support import committed_journals, create_repair_backup
from cmdrhelper.system_visits import apply_visit_plan, plan_visits, visit_row


def plan_visits_backfill(con, commander_id):
    commander_id = int(commander_id)
    commander = con.execute("SELECT fid FROM commanders WHERE id=?", (commander_id,)).fetchone()
    if commander is None:
        raise ValueError("Commander does not exist")
    rows, checked = [], []
    for filename, events in committed_journals(con, commander_id):
        checked.append(filename)
        for event in events:
            if event.get("event") in ("Location", "FSDJump", "CarrierJump"):
                row = visit_row(commander_id, event.get("SystemAddress"),
                                event.get("StarSystem"), event.get("timestamp"),
                                event.get("StarPos"))
                if row is not None:
                    rows.append(row)
    return {"journals": checked, "position_events": len(rows), **plan_visits(con, rows)}


def backfill_visits(database, commander_id, *, apply=False, backup_path=None):
    """Preview by default. Application locks writers and first backs up SQLite."""
    path = Path(database).resolve()
    uri = path.as_uri() + ("?mode=rw" if apply else "?mode=ro")
    with closing(sqlite3.connect(uri, uri=True)) as con:
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("BEGIN IMMEDIATE" if apply else "BEGIN")
        try:
            plan = plan_visits_backfill(con, commander_id)
            result = {**plan, "inserted": 0, "removed": 0, "backup": None}
            if apply and (plan["missing"] or plan["redundant_ids"]):
                backup = create_repair_backup(path, 'visits', backup_path)
                result["backup"] = str(backup)
                apply_visit_plan(con, plan)
                result.update(inserted=len(plan["missing"]), removed=len(plan["redundant_ids"]))
            con.commit()
            return result
        except Exception:
            con.rollback()
            raise
