"""Recover only missing DSS metadata for one explicitly identified journal event.

Run with python -m cmdrhelper.mapping_metadata_backfill. Default is a preview;
--apply creates a SQLite backup before changing any of the three columns.
"""
import argparse
import json
from pathlib import Path
import sqlite3

from cmdrhelper.mapping_metadata import mapping_metadata, apply_mapping_metadata
from cmdrhelper.backfill_support import committed_journals, create_repair_backup


FIELDS = ("mapped_at", "probes_used", "efficiency_target")


def apply_mapping_plan(con, updates):
    before = con.total_changes
    for commander_id, address, body_id, values in updates:
        con.execute("""UPDATE commander_bodies SET
            mapped_at=COALESCE(NULLIF(mapped_at,''),?,mapped_at),
            probes_used=COALESCE(probes_used,?),
            efficiency_target=COALESCE(efficiency_target,?)
            WHERE commander_id=? AND system_address=? AND body_id=?""",
            (values.get("mapped_at"), values.get("probes_used"), values.get("efficiency_target"),
             commander_id, address, body_id))
    return con.total_changes - before


def plan_mapping_backfill(con, commander_id):
    rows = con.execute("""SELECT cb.system_address,cb.body_id,b.name,
        cb.mapped_at,cb.probes_used,cb.efficiency_target FROM commander_bodies cb
        JOIN bodies b USING(system_address,body_id) WHERE cb.commander_id=?
        AND cb.self_mapped=1 AND (cb.mapped_at IS NULL OR cb.mapped_at=''
            OR cb.probes_used IS NULL OR cb.efficiency_target IS NULL)""", (commander_id,)).fetchall()
    targets = {(r[0], r[1]): r for r in rows}
    observed, checked = {}, []
    for filename, events in committed_journals(con, commander_id):
        checked.append(filename)
        for event in events:
            if event.get('event') != 'SAAScanComplete':
                continue
            address, body_id = event.get('SystemAddress'), event.get('BodyID')
            if type(address) is not int or type(body_id) is not int:
                continue
            key = (address, body_id)
            if key not in targets:
                continue
            if event.get('BodyName') != targets[key][2]:
                raise ValueError(f'Mapping body identity mismatch: {filename}: {key}')
            apply_mapping_metadata(observed.setdefault(key, {}), event)
    updates, unresolved = [], []
    for key, row in targets.items():
        missing = {field for field, value in zip(FIELDS, row[3:])
                   if value is None or (field == 'mapped_at' and value == '')}
        values = {field: value for field, value in observed.get(key, {}).items() if field in missing}
        if values:
            updates.append((commander_id, *key, values))
        if missing - values.keys():
            unresolved.append((row[2], sorted(missing - values.keys())))
    return {'journals': checked, 'updates': updates, 'unresolved': unresolved}


def journal_metadata(journal, commander_fid, system_address, body_id, body_name, timestamp):
    fid = None
    matches = []
    with Path(journal).open(encoding="utf-8") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue  # An actively appended final line may still be incomplete.
            if event.get("event") in ("Commander", "LoadGame"):
                fid = event.get("FID")
            if (event.get("event") != "SAAScanComplete"
                    or event.get("timestamp") != timestamp
                    or event.get("SystemAddress") != system_address
                    or event.get("BodyID") != body_id
                    or event.get("BodyName") != body_name):
                continue
            if fid != commander_fid:
                raise ValueError("DSS event is not attributed to the requested commander")
            matches.append(mapping_metadata(event))
    if not matches or any(value != matches[0] for value in matches):
        raise ValueError("Missing or conflicting matching DSS event")
    if set(matches[0]) != set(FIELDS):
        raise ValueError("The selected DSS event does not supply all three metadata fields")
    return matches[0]


def backfill_mapping_metadata(database, journal, commander_fid, system_address,
                              body_id, body_name, timestamp, apply=False, backup_path=None):
    metadata = journal_metadata(journal, commander_fid, system_address,
                                body_id, body_name, timestamp)
    database = Path(database).resolve()
    with sqlite3.connect(database.as_uri() + ("?mode=rw" if apply else "?mode=ro"),
                         uri=True, timeout=30) as con:
        con.row_factory = sqlite3.Row
        if apply:
            con.execute("BEGIN IMMEDIATE")  # Freeze writers until backup and repair complete.
        rows = con.execute("""
            SELECT cb.* FROM commander_bodies cb
            JOIN commanders c ON c.id=cb.commander_id
            JOIN bodies b USING(system_address,body_id)
            WHERE c.fid=? AND cb.system_address=? AND cb.body_id=? AND b.name=?
        """, (commander_fid, system_address, body_id, body_name)).fetchall()
        if len(rows) != 1 or rows[0]["self_mapped"] != 1:
            raise ValueError("Expected exactly one matching, already self-mapped commander body")
        before = dict(rows[0])
        changes = {field: value for field, value in metadata.items()
                   if before[field] is None or (field == "mapped_at" and before[field] == "")}
        backup = None
        if apply and changes:
            backup = create_repair_backup(database, 'mapping-metadata', backup_path)
            apply_mapping_plan(con, [(before['commander_id'], system_address, body_id, changes)])
        after = dict(con.execute("""SELECT * FROM commander_bodies
            WHERE commander_id=? AND system_address=? AND body_id=?""",
            (before["commander_id"], system_address, body_id)).fetchone())
        expected = {**before, **changes} if apply else before
        if after != expected:
            raise RuntimeError("Unexpected changes outside the missing mapping metadata")
        return {"applied": apply, "changed_rows": int(bool(changes) and apply),
                "missing_fields": changes, "backup": str(backup) if backup else None,
                "before": before, "after": after}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("database", "journal", "commander-fid", "body-name", "timestamp"):
        parser.add_argument("--" + name, required=True)
    for name in ("system-address", "body-id"):
        parser.add_argument("--" + name, type=int, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup-path")
    print(json.dumps(backfill_mapping_metadata(**vars(parser.parse_args())), indent=2))


if __name__ == "__main__":
    main()
