"""Committed-byte proof in existing app_meta; no schema or cursor migration."""
import hashlib
import json
from pathlib import Path


def key(path):
    return 'journal_prefix/v1/' + hashlib.sha256(str(path).encode()).hexdigest()


def store(con, path, fid, offset, digest):
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
        raise ValueError('journal_prefix_unverified')
    con.execute('INSERT INTO app_meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',
                (key(path), json.dumps(dict(fid=fid, offset=offset, sha256=digest))))


def verify_previous(database, folder):
    """Before indexing, bind persisted cursors to their original byte prefix."""
    from .journal_catchup import load_sessions, JournalConflict, _prefix_digest
    from .startup_runtime import JournalPending
    for row in load_sessions(database):
        path = Path(row['journal_file'])
        if path.parent != Path(folder) or not row.get('last_read_offset'):
            continue
        stat = path.stat()
        offset = row['last_read_offset']
        with database._connect() as con:
            saved = con.execute('SELECT value FROM app_meta WHERE key=?', (key(path),)).fetchone()
        if saved:
            proof = json.loads(saved[0])
            if (proof['offset'] != offset or proof['fid'] != row.get('fid_seen')
                    or stat.st_size < offset or _prefix_digest(path, offset) != proof['sha256']):
                raise JournalConflict('journal_committed_prefix_changed')
        elif row.get('sha256'):
            if stat.st_size < row['file_size'] or _prefix_digest(path, row['file_size']) != row['sha256']:
                raise JournalConflict('journal_committed_prefix_changed')
        elif stat.st_size != row['file_size'] or stat.st_mtime_ns != row['modified_ns']:
            # A legacy live cursor without a digest cannot prove a changed
            # prefix. Preserve it; never guess/reset/replay non-idempotent data.
            raise JournalPending('journal_legacy_prefix_unverified')
