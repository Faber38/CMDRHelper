"""Shared journal validation and SQLite backups for historical repairs."""
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from cmdrhelper.journal_files import journal_sort_key


class IncompleteRepair(ValueError):
    """Historical input is absent; retry when it becomes available."""


def create_repair_backup(database, label='startup-repairs', backup_path=None):
    database = Path(database).resolve()
    backup = Path(backup_path) if backup_path else database.with_name(
        database.name + '.pre-' + label + '-'
        + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.bak')
    with backup.open('xb'):
        pass
    with closing(sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)) as source:
        with closing(sqlite3.connect(backup)) as destination:
            source.backup(destination)
            if destination.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
                raise RuntimeError('Repair backup integrity check failed')
    return backup


def committed_journals(con, commander_id, journals=None, relevant_events=None):
    """Read only previously consumed prefixes, including pre-offset import records.

    Retained DB sessions/import records, not just files found in today's folder,
    define coverage. Missing old files must not silently disappear from a repair.
    """
    commander = con.execute('SELECT fid FROM commanders WHERE id=?', (commander_id,)).fetchone()
    if not commander:
        raise ValueError('Commander does not exist')
    imports = dict(con.execute('SELECT journal_file,file_size FROM journal_imports WHERE commander_id=?',
                               (commander_id,)).fetchall())
    columns = {row[1] for row in con.execute('PRAGMA table_info(journal_sessions)')}
    protected = 'repair_read_offset' in columns
    floor = 'repair_read_offset' if protected else '0'
    owner = '(commander_id=? OR repair_commander_id=?)' if protected else 'commander_id=?'
    sessions = con.execute(f"""SELECT journal_file,last_read_offset,last_complete_line_offset,
        fully_imported,attribution_status,{floor} FROM journal_sessions WHERE {owner}
        ORDER BY first_event_at,journal_file""",
        (commander_id, commander_id) if protected else (commander_id,)).fetchall()
    records = {row[0]: row for row in sessions}
    # Legacy imports can predate the identity index. Validate their journal
    # contents directly, never infer identity from the old import assignment.
    for filename in imports:
        records.setdefault(filename, (filename, 0, 0, False, 'unknown', 0))
    for filename, read_offset, complete_offset, imported, identity, saved_floor in sorted(
            records.values(), key=lambda row: journal_sort_key(Path(row[0]))):
        if journals is not None and str(Path(filename).resolve()) not in journals:
            continue
        limit = max(int(saved_floor or 0), int(read_offset or 0), int(complete_offset or 0) if imported else 0,
                    int(imports.get(filename) or 0))
        if limit <= 0:
            continue  # Unread input remains the regular importer's responsibility.
        try:
            with Path(filename).open('rb') as handle:
                raw = handle.read(limit)
        except FileNotFoundError as exc:
            raise IncompleteRepair(f'Missing historical journal: {filename}') from exc
        if len(raw) != limit or not raw.endswith(b'\n'):
            raise ValueError(f'Journal prefix is incomplete: {filename}')
        events = [json.loads(line) for line in raw.splitlines() if line.strip()]
        if any(not isinstance(event, dict) for event in events):
            raise ValueError(f'Invalid journal event: {filename}')
        relevant = relevant_events if relevant_events is not None else {
            'ScanOrganic', 'SAAScanComplete', 'Location', 'FSDJump', 'CarrierJump'}
        if not any(e.get('event') in relevant for e in events):
            # Menu-only/empty legacy journals have no facts for any of these
            # repairs. Certifying absence does not attribute data to a commander.
            yield filename, []
            continue
        identities = {str(e['FID']) for e in events
                      if e.get('event') in ('Commander', 'LoadGame') and e.get('FID')}
        if identities != {str(commander[0])}:
            raise ValueError(f'Journal identity does not match commander: {filename}')
        yield filename, events
