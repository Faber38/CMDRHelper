"""Local pad evidence and independent, atomic per-journal checkpoints.

No commander state, market data, network access or implicit schema migration.
Unchanged files are stat-only; append checks read at most two 4 KiB ranges.
"""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
from threading import Lock
from time import perf_counter

from .observed_market_cache import timestamp

PARSER_VERSION = 1
_locks = {}
_registry_lock = Lock()

_SCHEMA = """
CREATE TABLE station_pad_journals (
    id INTEGER PRIMARY KEY,
    journal_path TEXT NOT NULL UNIQUE,
    folder TEXT NOT NULL,
    signature TEXT NOT NULL,
    processed_offset INTEGER NOT NULL CHECK(processed_offset >= 0),
    parser_version INTEGER NOT NULL,
    context_json TEXT NOT NULL,
    prefix_hash BLOB NOT NULL,
    boundary_hash BLOB NOT NULL
);
CREATE INDEX station_pad_folder ON station_pad_journals(folder);
CREATE TABLE station_pad_evidence (
    journal_id INTEGER NOT NULL REFERENCES station_pad_journals(id) ON DELETE CASCADE,
    market_id BLOB NOT NULL CHECK(typeof(market_id)='blob' AND length(market_id)=8 AND market_id>X'0000000000000000'),
    system_address BLOB CHECK(system_address IS NULL OR (typeof(system_address)='blob' AND length(system_address)=8)),
    system_name TEXT NOT NULL,
    station_name TEXT NOT NULL,
    station_type TEXT,
    small_pads INTEGER NOT NULL CHECK(typeof(small_pads)='integer' AND small_pads>=0),
    medium_pads INTEGER NOT NULL CHECK(typeof(medium_pads)='integer' AND medium_pads>=0),
    large_pads INTEGER NOT NULL CHECK(typeof(large_pads)='integer' AND large_pads>=0),
    source TEXT NOT NULL CHECK(source='local_elite'),
    event_type TEXT NOT NULL CHECK(event_type IN ('Docked','DockingRequested')),
    observed_at TEXT NOT NULL,
    event_offset INTEGER NOT NULL CHECK(event_offset>=0),
    PRIMARY KEY(journal_id,market_id)
);
CREATE INDEX station_pad_market ON station_pad_evidence(market_id,observed_at);
"""


def create_schema(con):
    """Called only by the owning database's schema-22 transaction."""
    for statement in _SCHEMA.split(';'):
        if statement.strip():
            con.execute(statement)


def check_cancel(cancel):
    if cancel is not None and cancel.is_set():
        from .trade_market_source import TradeReadCancelled
        raise TradeReadCancelled()


def signature(st):
    return [st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns]


def _u64(value):
    if type(value) is not int or not 0 < value < 2**64:
        raise ValueError('Invalid station identifier')
    return value.to_bytes(8, 'big')


def evidence(event, offset):
    """None means no complete concrete pad evidence, never an inferred pad."""
    try:
        if event.get('event') not in ('Docked', 'DockingRequested'):
            return None
        mid = _u64(event.get('MarketID'))
        address = event.get('SystemAddress')
        address = _u64(address) if address is not None else None
        for key in ('StarSystem', 'StationName'):
            if not isinstance(event.get(key), str) or not event[key].strip():
                return None
        kind = event.get('StationType')
        if kind is not None and (not isinstance(kind, str) or not kind.strip()):
            return None
        raw = event.get('LandingPads')
        if not isinstance(raw, dict):
            return None
        pads = {k.lower(): v for k, v in raw.items()}
        values = [pads.get(k) for k in ('small', 'medium', 'large')]
        if any(type(v) is not int or not 0 <= v < 2**63 for v in values):
            return None
        stamp = timestamp(event.get('timestamp')).isoformat(timespec='microseconds')
        return (mid, address, event['StarSystem'], event['StationName'], kind,
                *values, 'local_elite', event['event'], stamp, offset)
    except (ValueError, TypeError, AttributeError, OverflowError):
        return None


def _fingerprints(stream, offset, stats):
    values = []
    for start in (0, max(0, offset - 4096)):
        stream.seek(start)
        raw = stream.read(min(4096, offset - start))
        stats['journal_bytes'] += len(raw)
        values.append(hashlib.sha256(raw).digest())
    return values


def _process(con, path, folder, cancel, stats):
    before = signature(path.stat())
    old = con.execute('SELECT * FROM station_pad_journals WHERE journal_path=?', (str(path),)).fetchone()
    if old and json.loads(old['signature']) == before and old['parser_version'] == PARSER_VERSION:
        return
    check_cancel(cancel)
    offset, context, rows = 0, {}, {}
    append = bool(old and old['parser_version'] == PARSER_VERSION
                  and json.loads(old['signature'])[:2] == before[:2]
                  and json.loads(old['signature'])[2] < before[2])
    with path.open('rb') as stream:
        if signature(os.fstat(stream.fileno())) != before:
            raise OSError('Pad journal changed before reading')
        if append:
            hashes = _fingerprints(stream, old['processed_offset'], stats)
            append = hashes == [old['prefix_hash'], old['boundary_hash']]
        if append:
            offset = old['processed_offset']
            context = json.loads(old['context_json'])
        stream.seek(offset)
        while offset < before[2]:
            check_cancel(cancel)
            start = offset
            raw = stream.readline(before[2] - start)
            stats['journal_bytes'] += len(raw)
            if not raw or not raw.endswith(b'\n'):
                break
            offset = stream.tell()
            try:
                event = json.loads(raw)
                if not isinstance(event, dict):
                    raise ValueError('Event is not an object')
            except (ValueError, UnicodeError):
                context = {}
                stats['invalid_lines'] += 1
                continue
            kind = event.get('event')
            if kind in ('Fileheader', 'LoadGame', 'Shutdown'):
                context = {}
            if kind in ('Location', 'FSDJump', 'CarrierJump', 'Docked'):
                context = {k: event[k] for k in ('StarSystem', 'SystemAddress') if k in event}
            if kind in ('Docked', 'DockingRequested'):
                row = evidence(dict(context, **event), start)
                if row is not None:
                    previous = rows.get(row[0])
                    if previous is None or row[-2:] >= previous[-2:]:
                        rows[row[0]] = row
        hashes = _fingerprints(stream, offset, stats)
        if signature(os.fstat(stream.fileno())) != before or signature(path.stat()) != before:
            raise OSError('Pad journal changed during reading')
    check_cancel(cancel)
    # Parsing never holds a write lock. Recheck the checkpoint after acquiring it.
    with con:
        con.execute('BEGIN IMMEDIATE')
        current = con.execute('SELECT * FROM station_pad_journals WHERE journal_path=?', (str(path),)).fetchone()
        if (dict(current) if current else None) != (dict(old) if old else None):
            raise OSError('Concurrent pad import changed checkpoint; retry')
        if signature(path.stat()) != before:
            raise OSError('Pad journal changed before commit')
        con.execute('''INSERT INTO station_pad_journals
            (journal_path,folder,signature,processed_offset,parser_version,context_json,prefix_hash,boundary_hash)
            VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(journal_path) DO UPDATE SET
            folder=excluded.folder,signature=excluded.signature,processed_offset=excluded.processed_offset,
            parser_version=excluded.parser_version,context_json=excluded.context_json,
            prefix_hash=excluded.prefix_hash,boundary_hash=excluded.boundary_hash''',
            (str(path), folder, json.dumps(before), offset, PARSER_VERSION, json.dumps(context), *hashes))
        jid = con.execute('SELECT id FROM station_pad_journals WHERE journal_path=?', (str(path),)).fetchone()[0]
        if not append:
            con.execute('DELETE FROM station_pad_evidence WHERE journal_id=?', (jid,))
        con.executemany('''INSERT INTO station_pad_evidence VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(journal_id,market_id) DO UPDATE SET
            system_address=excluded.system_address,system_name=excluded.system_name,
            station_name=excluded.station_name,station_type=excluded.station_type,
            small_pads=excluded.small_pads,medium_pads=excluded.medium_pads,large_pads=excluded.large_pads,
            source=excluded.source,event_type=excluded.event_type,observed_at=excluded.observed_at,
            event_offset=excluded.event_offset
            WHERE excluded.observed_at>station_pad_evidence.observed_at OR
            (excluded.observed_at=station_pad_evidence.observed_at AND excluded.event_offset>=station_pad_evidence.event_offset)''',
            ((jid, *row) for row in rows.values()))
        check_cancel(cancel)
    stats['processed_files'] += 1


def read_local(database_path, journal_folder, cancel=None, stats=None):
    """Synchronize independent pad checkpoints, then return a consistent projection.

    Fail closed: any file/DB/import error propagates to the existing search error
    path. No stale partial projection and no fallback to a memory-only full scan.
    """
    stats = stats if stats is not None else {}
    stats.update(journal_bytes=0, processed_files=0, invalid_lines=0)
    db = Path(database_path).resolve()
    folder = Path(journal_folder).resolve()
    with _registry_lock:
        lock = _locks.setdefault(str(db), Lock())
    while not lock.acquire(timeout=.05):
        check_cancel(cancel)
    try:
        check_cancel(cancel)
        # scandir must succeed before missing files can be retired.
        with os.scandir(folder) as entries:
            paths = sorted(folder / e.name for e in entries
                           if e.name.startswith('Journal.') and e.name.endswith('.log') and e.is_file())
        with closing(sqlite3.connect(db.as_uri() + '?mode=rw', uri=True, timeout=.25)) as con:
            con.row_factory = sqlite3.Row
            con.execute('PRAGMA foreign_keys=ON')
            if con.execute('PRAGMA user_version').fetchone()[0] != 22:
                raise RuntimeError('Persistent pad metadata requires database schema 22')
            for path in paths:
                _process(con, path, str(folder), cancel, stats)
            check_cancel(cancel)
            active = {str(p) for p in paths}
            retired = [r[0] for r in con.execute('SELECT journal_path FROM station_pad_journals WHERE folder=?', (str(folder),)) if r[0] not in active]
            if retired:
                with con:
                    con.executemany('DELETE FROM station_pad_journals WHERE journal_path=?', ((p,) for p in retired))
            start = perf_counter()
            rows = con.execute('''SELECT e.*,j.journal_path FROM station_pad_evidence e
                JOIN station_pad_journals j ON j.id=e.journal_id WHERE j.folder=?
                ORDER BY j.journal_path''', (str(folder),)).fetchall()
            from .pad_metadata import largest_pad
            result = {}
            for row in rows:
                mid = int.from_bytes(row['market_id'], 'big')
                stamp = timestamp(row['observed_at'])
                if mid not in result or stamp > result[mid]['timestamp']:
                    address = row['system_address']
                    result[mid] = dict(market_id=mid, station_name=row['station_name'],
                        system_name=row['system_name'], system_address=int.from_bytes(address, 'big') if address else None,
                        pad=largest_pad(dict(small=row['small_pads'], medium=row['medium_pads'], large=row['large_pads'])),
                        source='journal', timestamp=stamp)
            stats['query_seconds'] = perf_counter() - start
            return result
    finally:
        lock.release()
