"""Opt-in, startup-only parent repair. Journals are always opened read-only."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone

from cmdrhelper.body_parents import parent_metadata
from cmdrhelper.journal_files import journal_files

MIGRATION_KEY = 'parent_hierarchy_migration'
COMPLETE = '3.4.1-complete'
BACKUP_KEY = 'parent_hierarchy_backup.3.4.1'


class MigrationError(RuntimeError):
    def __init__(self, key, *, restored=False, detail=''):
        super().__init__(detail or key)
        self.key, self.restored, self.detail = key, restored, detail


def readonly(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)


def migration_required(path):
    if not Path(path).exists():
        return False
    with readonly(path) as con:
        if not con.execute("SELECT 1 FROM sqlite_master WHERE name='bodies'").fetchone():
            return False
        if not con.execute("SELECT 1 FROM bodies LIMIT 1").fetchone():
            return False
        try:
            row = con.execute('SELECT value FROM app_meta WHERE key=?', (MIGRATION_KEY,)).fetchone()
        except sqlite3.OperationalError:
            return True
        return not row or row[0] != COMPLETE


def elite_running():
    """Check the game executable, including Wine/Proton, without optional packages."""
    if os.name == 'nt':
        result = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True,
                                text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        return any('elitedangerous' in line.lower() and '.exe' in line.lower()
                   for line in result.stdout.splitlines())
    for entry in Path('/proc').iterdir():
        if not entry.name.isdecimal():
            continue
        try:
            args = (entry / 'cmdline').read_bytes().split(b'\0')
        except FileNotFoundError:
            continue
        except PermissionError:
            # Process names remain available on normal Linux /proc mounts.
            args = [(entry / 'comm').read_bytes().strip()]
        if any(Path(arg.decode(errors='replace').replace('\\', '/')).name.lower()
               in ('elitedangerous64.exe', 'elitedangerous.exe', 'elitedangerous64', 'elitedangerous')
               for arg in args):
            return True
    return False


def inventory(folder):
    files = journal_files(Path(folder)) if folder else []
    return {str(p.resolve()): (p.stat().st_size, p.stat().st_mtime_ns, p.stat().st_ctime_ns)
            for p in files}


def collect_candidates(paths, *, strict=False):
    candidates, used, scans = {}, set(), 0
    for path in paths:
        try:
            with Path(path).open(encoding='utf-8-sig') as stream:
                for line in stream:
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    if not isinstance(event, dict) or event.get('event') != 'Scan':
                        continue
                    address, body = event.get('SystemAddress'), event.get('BodyID')
                    if type(address) is not int or type(body) is not int or address < 0 or body < 0:
                        continue
                    metadata = parent_metadata(event.get('Parents'), 'Journal')
                    if metadata:
                        candidates.setdefault((address, body), {})[json.dumps(metadata, sort_keys=True)] = metadata
                        scans += 1
                        used.add(str(path))
        except (OSError, UnicodeError):
            if strict:
                raise
    return candidates, used, scans


def apply_candidates(con, candidates):
    """Same verified, conflict-skipping repair as the targeted manual repair."""
    result = dict(checked_systems=0, systems=0, bodies=0, parent_id=0,
                  parent_star_id=0, fields=0, metadata=0)
    checked, changed = set(), set()
    for (address, body), alternatives in sorted(candidates.items()):
        if len(alternatives) != 1:
            continue
        old = con.execute('SELECT parent_id,parent_star_id FROM bodies WHERE system_address=? AND body_id=?',
                          (address, body)).fetchone()
        if old is None:
            continue
        checked.add(address)
        encoded, metadata = next(iter(alternatives.items()))
        values = (metadata['parent_id'], metadata['parent_star_id'])
        if tuple(old) != values:
            con.execute('UPDATE bodies SET parent_id=?,parent_star_id=? WHERE system_address=? AND body_id=?',
                        (*values, address, body))
            changed.add(address)
            result['bodies'] += 1
            for i, key in enumerate(('parent_id', 'parent_star_id')):
                result[key] += old[i] != values[i]
        key = f'body_parents.v1:{address}:{body}'
        previous = con.execute('SELECT value FROM app_meta WHERE key=?', (key,)).fetchone()
        if not previous or previous[0] != encoded:
            con.execute('INSERT OR REPLACE INTO app_meta(key,value) VALUES(?,?)', (key, encoded))
            result['metadata'] += 1
    result.update(checked_systems=len(checked), systems=len(changed),
                  fields=result['parent_id'] + result['parent_star_id'])
    return result


def digest(path):
    sha = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            sha.update(chunk)
    return sha.hexdigest()


def verify_backup(source, backup):
    size = Path(source).stat().st_size
    sha = digest(source)
    if not size or Path(backup).stat().st_size != size or digest(backup) != sha:
        raise MigrationError('backup_error')
    with Path(source).open('rb') as a, Path(backup).open('rb') as b:
        while True:
            chunk = a.read(1024 * 1024)
            if chunk != b.read(1024 * 1024):
                raise MigrationError('backup_error')
            if not chunk:
                break
    return dict(size=size, sha256=sha, byte_equal=True)


def check_integrity(con):
    if con.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
        raise MigrationError('integrity_error')
    if con.execute('PRAGMA foreign_key_check').fetchall():
        raise MigrationError('integrity_error')


def fingerprint(con, *, protected=False):
    """Compare every table, excluding only explicitly permitted repair values."""
    result = {}
    for (table,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
        quote = '"' + table.replace('"', '""') + '"'
        columns = [row[1] for row in con.execute(f'PRAGMA table_info({quote})')]
        if protected and table == 'bodies':
            columns = [c for c in columns if c not in ('parent_id', 'parent_star_id')]
        selection = ','.join('"' + c.replace('"', '""') + '"' for c in columns)
        rows = con.execute(f'SELECT {selection} FROM {quote}').fetchall()
        if protected and table == 'app_meta':
            key_index = columns.index('key')
            rows = [r for r in rows if not (str(r[key_index]).startswith('body_parents.v1:')
                    or r[key_index] in (MIGRATION_KEY, BACKUP_KEY))]
        result[table] = hashlib.sha256(repr(sorted(rows, key=repr)).encode()).hexdigest()
    return result


def migrate(path, folder, *, progress=lambda step: None, process_check=elite_running,
            expected_inventory=None, repair=apply_candidates, integrity=check_integrity):
    path = Path(path)
    progress(0)
    con = None
    backup = None
    baseline = None
    try:
        if process_check():
            raise MigrationError('active')
        before = inventory(folder)
        if expected_inventory is not None and before != expected_inventory:
            raise MigrationError('active')
        if not before:
            raise MigrationError('missing')
        candidates, used, scans = collect_candidates(before, strict=True)
        if inventory(folder) != before or process_check():
            raise MigrationError('active')
        if not candidates:
            raise MigrationError('missing')
        hashes = {p: digest(p) for p in before}
        if inventory(folder) != before:
            raise MigrationError('active')
        progress(1)
        con = sqlite3.connect(path, timeout=0)
        con.execute('PRAGMA foreign_keys=ON')
        # Incorporate committed WAL pages before the required byte-identical copy.
        checkpoint = con.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()
        if checkpoint[0]:
            raise MigrationError('backup_error')
        con.execute('BEGIN IMMEDIATE')
        wal = Path(str(path) + '-wal')
        if wal.exists() and wal.stat().st_size:
            raise MigrationError('backup_error')
        baseline = fingerprint(con)
        protected = fingerprint(con, protected=True)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        backup = path.with_name(f'cmdrhelper_pre_parent_repair_3.4.1_{stamp}.db')
        try:
            with path.open('rb') as source, backup.open('xb') as target:
                shutil.copyfileobj(source, target)
                target.flush()
                os.fsync(target.fileno())
            metadata = verify_backup(path, backup)
            metadata.update(path=str(backup.resolve()), release='3.4.1', created_utc=stamp,
                            purpose='pre-parent-hierarchy-migration', retain=True)
            # Sidecar survives a failed/rolled-back DB transaction.
            with backup.with_suffix('.db.json').open('x', encoding='utf-8') as stream:
                json.dump(metadata, stream, indent=2)
                stream.flush()
                os.fsync(stream.fileno())
        except Exception as exc:
            raise MigrationError('backup_error', detail=str(exc)) from exc
        progress(2)
        check_integrity(con)
        progress(3)
        result = repair(con, candidates)
        if not result['checked_systems']:
            raise MigrationError('missing')
        progress(4)
        integrity(con)
        if fingerprint(con, protected=True) != protected:
            raise MigrationError('consistency_error')
        second = apply_candidates(con, candidates)
        if second['fields'] or second['metadata']:
            raise MigrationError('consistency_error')
        if inventory(folder) != before or process_check() or any(digest(p) != sha for p, sha in hashes.items()):
            raise MigrationError('active')
        con.execute('INSERT OR REPLACE INTO app_meta(key,value) VALUES(?,?)',
                    (BACKUP_KEY, json.dumps(metadata, sort_keys=True)))
        con.execute('INSERT OR REPLACE INTO app_meta(key,value) VALUES(?,?)', (MIGRATION_KEY, COMPLETE))
        integrity(con)
        con.commit()
        result.update(journals=len(used), scans=scans, backup=str(backup), remaining=second['fields'])
        progress(5)
        return result
    except Exception as exc:
        restored = False
        if con is not None:
            try:
                con.rollback()
                check_integrity(con)
                restored = baseline is not None and fingerprint(con) == baseline
            except Exception:
                pass
            if baseline is not None and not restored and backup and backup.exists():
                try:
                    with readonly(backup) as source:
                        check_integrity(source)
                        if fingerprint(source) != baseline:
                            raise RuntimeError('Backup differs from original state')
                        source.backup(con)
                    check_integrity(con)
                    restored = fingerprint(con) == baseline
                except Exception:
                    pass
        key = exc.key if isinstance(exc, MigrationError) else 'failed'
        raise MigrationError(key, restored=restored, detail=str(exc)) from exc
    finally:
        if con is not None:
            con.close()
