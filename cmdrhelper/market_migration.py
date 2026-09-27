"""Strict, offline JSON migration. Publish only a verified, closed SQLite file."""
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import tempfile

from .market_store import MarketStore
from .observed_market_cache import (
    MAX_FILE_BYTES, MAX_MARKETS, SCHEMA_VERSION, _json,
    utcnow, validate_snapshot, timestamp,
)


class MigrationError(RuntimeError):
    pass


class MigrationCancelled(MigrationError):
    pass


@dataclass(frozen=True)
class MigrationResult:
    path: Path
    imported: bool
    markets: int
    source_hash: str


def _cancelled(cancel):
    if cancel is not None and cancel.is_set():
        raise MigrationCancelled('Market migration cancelled; JSON remains authoritative')


def _source(path):
    try:
        with path.open('rb') as stream:
            raw = stream.read(MAX_FILE_BYTES + 1)
    except FileNotFoundError:
        return 'missing', []
    if len(raw) > MAX_FILE_BYTES:
        raise MigrationError('Market JSON exceeds the supported size limit')
    data = _json(raw)
    if (not isinstance(data, dict) or type(data.get('version')) is not int
            or data['version'] != SCHEMA_VERSION):
        raise MigrationError('Invalid market JSON version')
    rows = data.get('markets')
    if not isinstance(rows, list) or len(rows) > MAX_MARKETS:
        raise MigrationError('Invalid market JSON list/limit')
    result, seen = [], set()
    for row in rows:
        value = validate_snapshot(row)
        key = value['fid'], value['market_id']
        if key in seen:
            raise MigrationError('Duplicate FID/MarketID in market JSON')
        seen.add(key)
        result.append(value)
    return hashlib.sha256(raw).hexdigest(), result


def _canonical(value):
    value = dict(value)
    value['commodities'] = sorted(value['commodities'], key=lambda r: r['symbol'].casefold())
    return value


def activation_marker(path):
    return Path(str(path) + '.activated')


def database_authoritative(path):
    # An existing but unreadable database must be diagnosed, never replaced.
    return Path(path).exists() or activation_marker(path).exists()


def _mark_active(path):
    with activation_marker(path).open('ab') as stream:
        stream.flush()
        os.fsync(stream.fileno())
    if os.name == 'posix':
        fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)


def _completed(path, clock):
    with MarketStore(path, clock=clock) as store:
        meta = dict(store._con.execute('''SELECT key,value FROM store_meta
            WHERE key IN ('migration_complete', 'migration_markets', 'migration_source_sha256')'''))
        if meta.get('migration_complete') != '1':
            raise MigrationError('Existing markets.db has no completed migration; refusing to replace it')
        if not {'migration_source_sha256', 'migration_markets'} <= meta.keys():
            raise MigrationError('Incomplete migration metadata')
        _mark_active(path)
        return MigrationResult(path, False, int(meta['migration_markets']), meta['migration_source_sha256'])


def migrate_market_cache(source, destination, *, clock=utcnow, cancel=None):
    """Run in a worker. Never modify source or replace an existing destination.

    Missing JSON is an empty initial store. A zero-byte file is malformed JSON.
    Once activated, SQLite remains authoritative even if the old backup changes.
    A same-directory hard link atomically publishes without overwriting a winner
    from another process. No reader recognizes unmarked staging databases.
    """
    source, destination = Path(source), Path(destination)
    try:
        _cancelled(cancel)
        if destination.exists():
            return _completed(destination, clock)
        if activation_marker(destination).exists():
            raise MigrationError('Activated markets.db is missing; restore the database')
        digest, rows = _source(source)
        _cancelled(cancel)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.market-migration-', dir=destination.parent) as directory:
            staging = Path(directory) / 'markets.db'
            with MarketStore(staging, clock=clock) as store:
                for row in rows:
                    _cancelled(cancel)
                    # Legacy loading accepts future timestamps; retain them exactly.
                    # Normal live writes still reject them and searches filter them.
                    store.record_observation(row, allow_future=True)
                stats = store.get_stats()
                if (stats.current_markets, stats.observations, stats.snapshots) != (len({r['market_id'] for r in rows if timestamp(r['observed_at']) <= clock()}), len(rows), len(rows)):
                    raise MigrationError('Migrated market counts differ from JSON')
                if stats.commodity_rows != sum(len(r['commodities']) for r in rows):
                    raise MigrationError('Migrated commodity count differs from JSON')
                for row in rows:
                    _cancelled(cancel)
                    header = store._con.execute(
                        'SELECT observation_id FROM market_observations WHERE fid=? AND market_id=?',
                        (row['fid'], row['market_id'].to_bytes(8, 'big'))).fetchone()
                    if _canonical(store.get_observation(row['fid'], header[0])) != _canonical(row):
                        raise MigrationError('Migrated market content differs from JSON')
                if store._con.execute('PRAGMA foreign_key_check').fetchall():
                    raise MigrationError('Migrated foreign-key integrity failed')
                if store._con.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise MigrationError('Migrated database integrity failed')
                _cancelled(cancel)
                # Verify source was not changed/replaced during migration.
                if _source(source)[0] != digest:
                    raise MigrationError('Market JSON changed during migration; retry required')
                with store._transaction(write=True):
                    store._con.execute('ANALYZE')
                    store._con.executemany('INSERT INTO store_meta(key,value) VALUES(?,?)', (
                        ('migration_source_sha256', digest),
                        ('migration_markets', str(len(rows))),
                        ('migration_complete', '1'),
                        ('optimizer_analyzed', '1'),
                    ))
                checkpoint = store._con.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone()
                if checkpoint[0] != 0:
                    raise MigrationError('Migration checkpoint could not finish')
            _cancelled(cancel)
            # Ensure the published file is durable without relying on a sidecar.
            with staging.open('r+b') as stream:
                os.fsync(stream.fileno())
            _cancelled(cancel)
            try:
                os.link(staging, destination)
            except FileExistsError:
                return _completed(destination, clock)
            # Publication is the point of no return: cancellation after this
            # point must not claim that a fully committed DB was not activated.
            if os.name == 'posix':
                fd = os.open(destination.parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
            _mark_active(destination)
            return MigrationResult(destination, True, len(rows), digest)
    except MigrationError:
        raise
    except Exception as exc:
        raise MigrationError(f'Market migration failed; JSON untouched: {exc}') from exc
