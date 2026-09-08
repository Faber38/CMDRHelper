"""Shared persistence of chronological, commander-specific system stays."""


def visit_row(commander_id, address, name, timestamp, star_pos=None):
    if not isinstance(address, int) or not timestamp:
        return None
    pos = list(star_pos or [])[:3]
    pos += [None] * (3 - len(pos))
    return (int(commander_id), address, str(name or ""), str(timestamp), *pos)


def plan_visits(con, rows):
    """Merge complete input batches before collapsing consecutive equal addresses.

    Sorting the combined timeline also handles archive/backfill rows older than
    existing visits. Equal timestamps retain existing/source order. System names
    are display data; identity and stay boundaries use SystemAddress.
    """
    grouped = {}
    for row in rows:
        if row is not None:
            grouped.setdefault(row[0], []).append(tuple(row))
    inserted, removed = [], []
    for commander_id, incoming in grouped.items():
        existing = con.execute("""SELECT id,commander_id,system_address,
            system_name,visited_at,x,y,z FROM system_visits
            WHERE commander_id=? ORDER BY visited_at,id""", (commander_id,)).fetchall()
        timeline = {(row[2], row[4]): (row[0], tuple(row[1:])) for row in existing}
        for row in incoming:
            timeline.setdefault((row[1], row[3]), (None, row))
        previous = None
        for row_id, row in sorted(timeline.values(), key=lambda item: item[1][3]):
            if row[1] == previous:
                if row_id is not None:
                    removed.append(row_id)
                continue
            previous = row[1]
            if row_id is None:
                inserted.append(row)
    return {"missing": inserted, "redundant_ids": removed}


def apply_visit_plan(con, plan):
    con.executemany("DELETE FROM system_visits WHERE id=?",
                    [(row_id,) for row_id in plan["redundant_ids"]])
    con.executemany("""INSERT INTO system_visits
        (commander_id,system_address,system_name,visited_at,x,y,z)
        VALUES(?,?,?,?,?,?,?)""", plan["missing"])


def store_visit_rows(con, rows):
    plan = plan_visits(con, rows)
    apply_visit_plan(con, plan)
    return plan
