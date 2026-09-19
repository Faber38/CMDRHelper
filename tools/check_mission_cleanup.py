#!/usr/bin/env python3
"""Copy a database, then optionally clean definite terminal missions on the copy.

Usage: python -m tools.check_mission_cleanup SOURCE NEW_COPY [--clean]
The source is opened read-only. An existing destination is always refused.
No CMDRDatabase initialization, schema migration, journal import or VACUUM.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3

from cmdrhelper.mission_persistence import cleanup_terminal_missions


def fingerprint(con, table):
    quoted = '"' + table.replace('"', '""') + '"'
    rows = sorted(repr(row) for row in con.execute('SELECT * FROM ' + quoted))
    return hashlib.sha256('\n'.join(rows).encode()).hexdigest()


def counts(con):
    return [dict(zip(('commander_id', 'fid', 'is_open', 'terminal_state', 'count'), row))
            for row in con.execute('SELECT m.commander_id,c.fid,m.is_open,m.terminal_state,count(*) '
                                   'FROM commander_missions m JOIN commanders c ON c.id=m.commander_id '
                                   'GROUP BY m.commander_id,m.is_open,m.terminal_state')]


def check_copy(source, destination, *, clean=False):
    source, destination = Path(source).resolve(strict=True), Path(destination).resolve()
    # Exclusive creation also prevents following an existing symlink to production.
    with destination.open('xb'):
        pass
    with sqlite3.connect(source.as_uri() + '?mode=ro', uri=True) as original:
        with sqlite3.connect(destination) as con:
            original.backup(con)
            con.execute('PRAGMA foreign_keys=ON')
            schema = con.execute('SELECT name,sql FROM sqlite_master ORDER BY name').fetchall()
            version = con.execute('PRAGMA user_version').fetchone()[0]
            tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")
                      if r[0] not in ('commander_missions', 'app_meta')]
            before_tables = {t: fingerprint(con, t) for t in tables}
            before_open = con.execute('SELECT * FROM commander_missions WHERE is_open=1 '
                                      'ORDER BY commander_id,mission_id').fetchall()
            before_inactive = con.execute("SELECT * FROM commander_missions WHERE terminal_state='inactive' "
                                          'ORDER BY commander_id,mission_id').fetchall()
            before_meta = con.execute("SELECT * FROM app_meta WHERE key NOT LIKE 'mission_state_anchor/%' ORDER BY key").fetchall()
            report = dict(source=str(source), copy=str(destination), schema_version=version,
                          before=counts(con), removed={})
            with con:
                if clean:
                    for cid, in con.execute('SELECT id FROM commanders').fetchall():
                        report['removed'][cid] = cleanup_terminal_missions(con, cid)
            report.update(after=counts(con), integrity=con.execute('PRAGMA integrity_check').fetchall(),
                          foreign_keys=con.execute('PRAGMA foreign_key_check').fetchall(),
                          other_tables_unchanged=before_tables == {t:fingerprint(con,t) for t in tables},
                          open_rows_identical=before_open == con.execute('SELECT * FROM commander_missions WHERE is_open=1 ORDER BY commander_id,mission_id').fetchall(),
                          inactive_rows_identical=before_inactive == con.execute("SELECT * FROM commander_missions WHERE terminal_state='inactive' ORDER BY commander_id,mission_id").fetchall(),
                          other_meta_including_pending_unchanged=before_meta == con.execute("SELECT * FROM app_meta WHERE key NOT LIKE 'mission_state_anchor/%' ORDER BY key").fetchall(),
                          schema_unchanged=schema == con.execute('SELECT name,sql FROM sqlite_master ORDER BY name').fetchall()
                          and version == con.execute('PRAGMA user_version').fetchone()[0])
            if not (report['integrity'] == [('ok',)] and report['foreign_keys'] == []
                    and all(report[key] for key in ('other_tables_unchanged', 'open_rows_identical',
                                                   'inactive_rows_identical', 'other_meta_including_pending_unchanged', 'schema_unchanged'))):
                raise RuntimeError('Copy verification failed: ' + json.dumps(report))
            return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('new_copy', type=Path)
    parser.add_argument('--clean', action='store_true', help='Clean only the newly created copy')
    args = parser.parse_args()
    print(json.dumps(check_copy(args.source, args.new_copy, clean=args.clean), indent=2))
