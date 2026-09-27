"""Isolated local-market SQLite store. No observer/UI integration or migration.

Connections belong to the constructing thread. Public calls finish their own
transaction and return owned values, never cursors. Instantiate another store in
another worker; never send a connection across threads. A successful write result
means COMMIT completed, not merely that work was queued.
"""
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from threading import get_ident

from .market_data import TradeSide
from .observed_market_cache import (
    TTL, _identity, timestamp, utcnow, valid_fid, validate_snapshot,
)

SCHEMA_VERSION = 2
APPLICATION_ID = 0x434D484D  # CMHM; deliberately different from cmdrhelper.db.
MAX_PAGE = 500
HISTORY_RETENTION = timedelta(days=30)
EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
ZERO = bytes(8)


def market_store_path():
    """Resolve the proposed location only when explicitly requested; no I/O."""
    from PySide6.QtCore import QStandardPaths
    base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    if not base:
        raise OSError('AppDataLocation unavailable')
    return Path(base) / 'market_cache' / 'markets.db'


def encode_u64(value, minimum=0):
    if type(value) is not int or not minimum <= value < 2**64:
        raise ValueError('Expected an unsigned 64-bit integer')
    return value.to_bytes(8, 'big')


def decode_u64(value):
    if not isinstance(value, bytes) or len(value) != 8:
        raise ValueError('Invalid stored unsigned integer')
    return int.from_bytes(value, 'big')


def _micros(value):
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError('Expected a timezone-aware datetime')
    delta = value.astimezone(timezone.utc) - EPOCH
    return (delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds


def _datetime(value):
    return EPOCH + timedelta(microseconds=value)


class StoreFormatError(ValueError):
    """Unknown database identity/version; never silently adopt or replace it."""


class ObservationConflict(ValueError):
    """The same FID/market/timestamp has contradictory content or context."""


class StaleReadError(RuntimeError):
    """The requested revision changed between pages; restart the query."""


class CleanupCancelled(RuntimeError):
    """Cleanup was cancelled before commit; every deletion was rolled back."""


def _assert_not_gui_thread():
    # Do not introduce a Qt dependency or instantiate an application. If the
    # host has Qt loaded, explicitly reject its application/GUI thread.
    qt = sys.modules.get('PySide6.QtCore')
    app = qt.QCoreApplication.instance() if qt is not None else None
    if app is not None and qt.QThread.currentThread() == app.thread():
        raise RuntimeError('MarketStore cleanup must run outside the GUI thread')


@dataclass(frozen=True)
class CommodityRef:
    commodity_id: int | None
    symbol: str

    def __post_init__(self):
        cid, symbol = _identity(self.commodity_id, self.symbol)
        object.__setattr__(self, 'commodity_id', cid)
        object.__setattr__(self, 'symbol', symbol)


@dataclass(frozen=True)
class MarketHeader:
    observation_id: int
    snapshot_id: int
    fid: str
    market_id: int
    observed_at: datetime
    station_name: str
    system_name: str
    system_address: int | None
    station_type: str | None
    commodity_count: int
    source: str = 'local_elite'


@dataclass(frozen=True)
class CommodityValue:
    commodity_id: int | None
    symbol: str
    commander_buy_price: int
    commander_sell_price: int
    supply: int
    demand: int
    localized_name: str | None = None
    category: str | None = None


@dataclass(frozen=True)
class MarketCandidate:
    header: MarketHeader
    commodity: CommodityValue | None
    scope: str = 'current'


@dataclass(frozen=True)
class HistoryCursor:
    observed_at_us: int
    observation_id: int


@dataclass(frozen=True)
class MarketPage:
    items: tuple
    next_cursor: int | HistoryCursor | None
    revision: int


@dataclass(frozen=True)
class WriteResult:
    observation_id: int
    snapshot_id: int
    inserted: bool
    snapshot_reused: bool
    current_changed: bool
    revision: int


@dataclass(frozen=True)
class CleanupResult:
    observations_removed: int
    snapshots_removed: int
    commodity_rows_removed: int
    commodity_keys_removed: int
    revision: int
    cutoff: datetime


@dataclass(frozen=True)
class StoreStats:
    stations: int
    current_markets: int
    observations: int
    snapshots: int
    commodity_rows: int
    revision: int
    main_bytes: int
    wal_bytes: int
    shm_bytes: int

    @property
    def total_bytes(self):
        return self.main_bytes + self.wal_bytes + self.shm_bytes


# Fixed-width big-endian BLOBs sort exactly as uint64, including values above
# SQLite's signed INTEGER range. Every comparison binds the same BLOB encoding.
_U64 = "BLOB NOT NULL CHECK(typeof({0})='blob' AND length({0})=8)"
_OPTIONAL_U64 = "BLOB CHECK({0} IS NULL OR (typeof({0})='blob' AND length({0})=8))"
_SCHEMA = f"""
CREATE TABLE stations (
    market_id {_U64.format('market_id')} PRIMARY KEY CHECK(market_id > X'0000000000000000')
);
CREATE TABLE commodity_keys (
    commodity_key INTEGER PRIMARY KEY,
    frontier_id {_OPTIONAL_U64.format('frontier_id')},
    symbol_key TEXT NOT NULL,
    CHECK(frontier_id IS NULL OR frontier_id > X'0000000000000000')
);
CREATE UNIQUE INDEX commodity_known ON commodity_keys(frontier_id, symbol_key)
    WHERE frontier_id IS NOT NULL;
CREATE UNIQUE INDEX commodity_unknown ON commodity_keys(symbol_key)
    WHERE frontier_id IS NULL;
CREATE TABLE market_snapshots (
    snapshot_id INTEGER PRIMARY KEY,
    fid TEXT NOT NULL,
    market_id {_U64.format('market_id')} REFERENCES stations(market_id),
    content_hash BLOB NOT NULL CHECK(length(content_hash)=32),
    commodity_count INTEGER NOT NULL CHECK(commodity_count BETWEEN 0 AND 2048),
    UNIQUE(fid, market_id, content_hash),
    UNIQUE(snapshot_id, fid, market_id)
);
CREATE TABLE commodity_observations (
    snapshot_id INTEGER NOT NULL REFERENCES market_snapshots(snapshot_id) ON DELETE CASCADE,
    commodity_key INTEGER NOT NULL REFERENCES commodity_keys(commodity_key),
    ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
    symbol TEXT NOT NULL,
    commander_buy_price {_U64.format('commander_buy_price')},
    commander_sell_price {_U64.format('commander_sell_price')},
    supply {_U64.format('supply')},
    demand {_U64.format('demand')},
    localized_name TEXT,
    category TEXT,
    PRIMARY KEY(snapshot_id, commodity_key),
    UNIQUE(snapshot_id, ordinal)
);
CREATE INDEX commodity_sell ON commodity_observations
    (commodity_key, commander_sell_price DESC, snapshot_id);
CREATE INDEX commodity_buy ON commodity_observations
    (commodity_key, commander_buy_price, snapshot_id);
CREATE TABLE market_observations (
    observation_id INTEGER PRIMARY KEY,
    snapshot_id INTEGER NOT NULL,
    fid TEXT NOT NULL,
    market_id {_U64.format('market_id')},
    observed_at INTEGER NOT NULL,
    recorded_at INTEGER NOT NULL,
    station_name TEXT NOT NULL,
    system_name TEXT NOT NULL,
    system_address {_OPTIONAL_U64.format('system_address')},
    station_type TEXT,
    source TEXT NOT NULL CHECK(source='local_elite'),
    FOREIGN KEY(snapshot_id, fid, market_id)
        REFERENCES market_snapshots(snapshot_id, fid, market_id),
    UNIQUE(fid, market_id, observed_at),
    UNIQUE(observation_id, fid, market_id, observed_at)
);
CREATE INDEX observation_age ON market_observations(fid, observed_at DESC);
CREATE INDEX observation_retention ON market_observations(observed_at, observation_id);
CREATE INDEX observation_snapshot ON market_observations(snapshot_id, observed_at DESC);
CREATE TABLE current_markets (
    fid TEXT NOT NULL,
    market_id {_U64.format('market_id')},
    observation_id INTEGER NOT NULL UNIQUE,
    observed_at INTEGER NOT NULL,
    system_address {_OPTIONAL_U64.format('system_address')},
    system_name_key TEXT NOT NULL,
    PRIMARY KEY(market_id),
    FOREIGN KEY(observation_id, fid, market_id, observed_at)
        REFERENCES market_observations(observation_id, fid, market_id, observed_at)
);
CREATE INDEX current_age ON current_markets(observed_at DESC, market_id);
CREATE INDEX current_system ON current_markets(system_address, market_id);
CREATE INDEX current_system_name ON current_markets(system_name_key, market_id);
CREATE INDEX current_station ON current_markets(market_id, fid);
CREATE TABLE store_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
INSERT INTO store_meta VALUES('revision', '0');
INSERT INTO store_meta VALUES('history_retention_days', '30');
"""
_HEADER_COLUMNS = 'o.*, s.commodity_count'
_HEADERS = f"SELECT {_HEADER_COLUMNS} FROM current_markets c JOIN market_observations o ON o.observation_id=c.observation_id JOIN market_snapshots s ON s.snapshot_id=o.snapshot_id"
_VALUES = """SELECT v.*, k.frontier_id FROM commodity_observations v
    JOIN commodity_keys k ON k.commodity_key=v.commodity_key"""


class MarketStore:
    def __init__(self, path, *, clock=utcnow, read_only=False, busy_timeout_ms=250):
        if type(busy_timeout_ms) is not int or not 0 <= busy_timeout_ms <= 30_000:
            raise ValueError('Invalid busy timeout')
        self.path = Path(path).resolve()
        self.clock, self.read_only = clock, read_only
        self._owner, self._closed = get_ident(), False
        if not read_only:
            self.path.parent.mkdir(parents=True, exist_ok=True)
        uri = self.path.as_uri() + ('?mode=ro' if read_only else '?mode=rwc')
        self._con = sqlite3.connect(uri, uri=True, isolation_level=None,
                                    timeout=busy_timeout_ms / 1000)
        self._con.row_factory = sqlite3.Row
        try:
            self._con.execute('PRAGMA foreign_keys=ON')
            self._con.execute('PRAGMA synchronous=FULL')
            if read_only:
                self._verify_format()
                self._con.execute('PRAGMA query_only=ON')
            else:
                with self._transaction(write=True):
                    app_id = self._con.execute('PRAGMA application_id').fetchone()[0]
                    version = self._con.execute('PRAGMA user_version').fetchone()[0]
                    objects = self._con.execute("SELECT 1 FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' LIMIT 1").fetchone()
                    if app_id == 0 and version == 0 and objects is None:
                        for statement in _SCHEMA.split(';'):
                            if statement.strip():
                                self._con.execute(statement)
                        self._con.execute(f'PRAGMA application_id={APPLICATION_ID}')
                        self._con.execute(f'PRAGMA user_version={SCHEMA_VERSION}')
                    if app_id == APPLICATION_ID and version == 1:
                        self._upgrade_v1()
                    self._verify_format()
                if self._con.execute('PRAGMA journal_mode=WAL').fetchone()[0] != 'wal':
                    raise StoreFormatError('WAL unavailable')
        except BaseException:
            self._con.close()
            self._closed = True
            raise

    def _upgrade_v1(self):
        """Transactional SQL-only rebuild of current pointers; preserve all history."""
        self._verify_format(version=1)
        for name in ('current_age', 'current_system', 'current_system_name', 'current_station'):
            self._con.execute('DROP INDEX ' + name)
        self._con.execute('ALTER TABLE current_markets RENAME TO current_markets_v1')
        for statement in _SCHEMA[_SCHEMA.index('CREATE TABLE current_markets'): _SCHEMA.index('CREATE TABLE store_meta')].split(';'):
            if statement.strip():
                self._con.execute(statement)
        self._con.create_function('market_casefold', 1, str.casefold, deterministic=True)
        try:
            self._con.execute('''INSERT INTO current_markets
                (fid,market_id,observation_id,observed_at,system_address,system_name_key)
                SELECT fid,market_id,observation_id,observed_at,system_address,market_casefold(system_name) FROM (
                    SELECT o.*, ROW_NUMBER() OVER (PARTITION BY market_id
                        ORDER BY observed_at DESC, fid ASC) AS rank FROM market_observations o
                    WHERE observed_at<=?) WHERE rank=1''', (_micros(self.clock()),))
        finally:
            self._con.create_function('market_casefold', 1, None)
        self._con.execute('DROP TABLE current_markets_v1')
        self._con.execute("UPDATE store_meta SET value=CAST(value AS INTEGER)+1 WHERE key='revision'")
        self._con.execute(f'PRAGMA user_version={SCHEMA_VERSION}')

    def _verify_format(self, *, version=SCHEMA_VERSION):
        if (self._con.execute('PRAGMA application_id').fetchone()[0] != APPLICATION_ID
                or self._con.execute('PRAGMA user_version').fetchone()[0] != version):
            raise StoreFormatError('Not a supported MarketStore database')
        required = {'stations', 'commodity_keys', 'market_snapshots', 'commodity_observations',
                    'market_observations', 'current_markets', 'store_meta'}
        tables = {r[0] for r in self._con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not required <= tables:
            raise StoreFormatError('Incomplete MarketStore schema')

    def _check_thread(self):
        if self._closed or self._owner != get_ident():
            raise sqlite3.ProgrammingError('MarketStore is closed or belongs to another thread')

    @contextmanager
    def _transaction(self, *, write=False):
        self._check_thread()
        if write and self.read_only:
            raise sqlite3.OperationalError('MarketStore is read-only')
        self._con.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
        try:
            yield
            self._con.execute('COMMIT')
        except BaseException:
            if self._con.in_transaction:
                self._con.execute('ROLLBACK')
            raise

    def close(self):
        if not self._closed:
            self._check_thread()
            self._con.close()
            self._closed = True

    def __enter__(self):
        self._check_thread()
        return self

    def __exit__(self, *_):
        self.close()

    def _revision(self):
        return int(self._con.execute("SELECT value FROM store_meta WHERE key='revision'").fetchone()[0])

    @staticmethod
    def _fid(fid):
        if not valid_fid(fid):
            raise ValueError('Invalid FID')
        return fid

    def _range(self, max_age, since=None):
        now = _micros(self.clock())
        low = None
        if max_age is not None:
            if not isinstance(max_age, timedelta) or max_age < timedelta(0):
                raise ValueError('Invalid maximum age')
            low = now - ((max_age.days * 86400 + max_age.seconds) * 1_000_000 + max_age.microseconds)
        if since is not None:
            value = _micros(since)
            low = max(low, value) if low is not None else value
        return low, now

    @staticmethod
    def _header(row):
        return MarketHeader(row['observation_id'], row['snapshot_id'], row['fid'],
            decode_u64(row['market_id']), _datetime(row['observed_at']), row['station_name'],
            row['system_name'], decode_u64(row['system_address']) if row['system_address'] is not None else None,
            row['station_type'], row['commodity_count'])

    @staticmethod
    def _value(row):
        return CommodityValue(decode_u64(row['frontier_id']) if row['frontier_id'] is not None else None,
            row['symbol'], *(decode_u64(row[k]) for k in
                ('commander_buy_price', 'commander_sell_price', 'supply', 'demand')),
            row['localized_name'], row['category'])

    def _commodity_id(self, ref, *, create=False):
        if not isinstance(ref, CommodityRef):
            raise TypeError('Expected CommodityRef')
        cid = encode_u64(ref.commodity_id, 1) if ref.commodity_id is not None else None
        symbol = ref.symbol.casefold()
        if cid is None:
            sql, args = 'frontier_id IS NULL AND symbol_key=?', (symbol,)
        else:
            sql, args = 'frontier_id=? AND symbol_key=?', (cid, symbol)
        row = self._con.execute('SELECT commodity_key FROM commodity_keys WHERE ' + sql, args).fetchone()
        if row:
            return row[0]
        if not create:
            return None
        return self._con.execute('INSERT INTO commodity_keys(frontier_id,symbol_key) VALUES(?,?)',
                                 (cid, symbol)).lastrowid

    def _payload(self, snapshot_id):
        values = self._con.execute(_VALUES + ' WHERE v.snapshot_id=? ORDER BY v.ordinal', (snapshot_id,))
        rows = []
        for value in values:
            item = self._value(value)
            row = dict(commodity_id=item.commodity_id, symbol=item.symbol,
                       commander_buy_price=item.commander_buy_price, commander_sell_price=item.commander_sell_price,
                       supply=item.supply, demand=item.demand)
            for name in ('localized_name', 'category'):
                if getattr(item, name) is not None:
                    row[name] = getattr(item, name)
            rows.append(row)
        return rows

    def _snapshot(self, header):
        result = dict(fid=header.fid, source='local_elite', market_id=header.market_id,
                      station_name=header.station_name, system_name=header.system_name,
                      observed_at=header.observed_at.isoformat(), commodities=self._payload(header.snapshot_id))
        if header.system_address is not None:
            result['system_address'] = header.system_address
        if header.station_type is not None:
            result['station_type'] = header.station_type
        return result

    def record_observation(self, observation, *, allow_future=False):
        self._check_thread()
        value = validate_snapshot(observation)
        stamp, now = _micros(timestamp(value['observed_at'])), _micros(self.clock())
        if stamp > now and not allow_future:
            raise ValueError('Observation from future')
        # Canonical ordering makes list order irrelevant to snapshot reuse.
        rows = sorted(value['commodities'], key=lambda r:
                      (r['commodity_id'] is not None, r['commodity_id'] or 0, r['symbol'].casefold()))
        digest = hashlib.sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True,
                                separators=(',', ':'), allow_nan=False).encode('utf-8')).digest()
        fid, mid = value['fid'], encode_u64(value['market_id'], 1)
        address = encode_u64(value['system_address'], 1) if 'system_address' in value else None
        context = (value['station_name'], value['system_name'], address, value.get('station_type'))
        with self._transaction(write=True):
            old = self._con.execute('SELECT * FROM market_observations WHERE fid=? AND market_id=? AND observed_at=?',
                                    (fid, mid, stamp)).fetchone()
            existing = self._con.execute('SELECT snapshot_id FROM market_snapshots WHERE fid=? AND market_id=? AND content_hash=?',
                                         (fid, mid, digest)).fetchone()
            reused = existing is not None
            if existing and self._payload(existing[0]) != rows:
                raise ObservationConflict('Snapshot hash collision')
            if old:
                if (not existing or old['snapshot_id'] != existing[0]
                        or tuple(old[k] for k in ('station_name', 'system_name', 'system_address', 'station_type')) != context):
                    raise ObservationConflict('Conflicting observation at the same timestamp')
                return WriteResult(old['observation_id'], old['snapshot_id'], False, True, False, self._revision())
            self._con.execute('INSERT OR IGNORE INTO stations(market_id) VALUES(?)', (mid,))
            if existing:
                sid = existing[0]
            else:
                sid = self._con.execute('INSERT INTO market_snapshots(fid,market_id,content_hash,commodity_count) VALUES(?,?,?,?)',
                                        (fid, mid, digest, len(rows))).lastrowid
                entries = []
                for ordinal, row in enumerate(rows):
                    key = self._commodity_id(CommodityRef(row['commodity_id'], row['symbol']), create=True)
                    entries.append((sid, key, ordinal, row['symbol'],
                        *(encode_u64(row[k]) for k in ('commander_buy_price', 'commander_sell_price', 'supply', 'demand')),
                        row.get('localized_name'), row.get('category')))
                self._con.executemany('INSERT INTO commodity_observations VALUES(?,?,?,?,?,?,?,?,?,?)', entries)
            oid = self._con.execute('''INSERT INTO market_observations
                (snapshot_id,fid,market_id,observed_at,recorded_at,station_name,system_name,system_address,station_type,source)
                VALUES(?,?,?,?,?,?,?,?,?, 'local_elite')''', (sid, fid, mid, stamp, now, *context)).lastrowid
            current = self._con.execute('''INSERT INTO current_markets
                (fid,market_id,observation_id,observed_at,system_address,system_name_key) VALUES(?,?,?,?,?,?)
                ON CONFLICT(market_id) DO UPDATE SET fid=excluded.fid, observation_id=excluded.observation_id,
                observed_at=excluded.observed_at,system_address=excluded.system_address,system_name_key=excluded.system_name_key
                WHERE excluded.observed_at > current_markets.observed_at
                    OR (excluded.observed_at = current_markets.observed_at AND excluded.fid < current_markets.fid)''',
                (fid, mid, oid, stamp, address, value['system_name'].casefold())).rowcount > 0 if stamp <= now else False
            self._con.execute("UPDATE store_meta SET value=CAST(value AS INTEGER)+1 WHERE key='revision'")
            if current:
                self._con.execute("INSERT OR REPLACE INTO store_meta(key,value) VALUES(?,?)",
                    (f"current_order:{value['fid']}:{value['market_id']}",
                     json.dumps([[r['commodity_id'], r['symbol'].casefold()] for r in value['commodities']])))
            revision = self._revision()
        return WriteResult(oid, sid, True, reused, current, revision)

    def get_current(self, market_id, max_age=TTL):
        sql, args = self._headers_query((market_id,), max_age)
        with self._transaction():
            row = self._con.execute(sql, args).fetchone()
            if row is None:
                return None
            result = self._snapshot(self._header(row))
            ordering = self._con.execute('SELECT value FROM store_meta WHERE key=?',
                (f"current_order:{row['fid']}:{market_id}",)).fetchone()
            if ordering:
                positions = {tuple(key): i for i, key in enumerate(json.loads(ordering[0]))}
                result['commodities'].sort(key=lambda r: positions.get(
                    (r['commodity_id'], r['symbol'].casefold()), len(positions)))
            return result

    def _headers_query(self, market_ids, max_age):
        ids = []
        for mid in market_ids:
            if len(ids) == MAX_PAGE:
                raise ValueError('Too many market IDs; request bounded batches')
            ids.append(encode_u64(mid, 1))
        low, now = self._range(max_age)
        sql = _HEADERS + ' WHERE c.observed_at<=?'
        args = [now]
        if low is not None:
            sql += ' AND c.observed_at>=?'
            args.append(low)
        sql += ' AND c.market_id IN (' + ','.join('?' for _ in ids) + ') ORDER BY c.market_id'
        return sql, (*args, *ids)

    def get_current_headers(self, market_ids, max_age=TTL):
        sql, args = self._headers_query(market_ids, max_age)
        with self._transaction():
            return tuple(self._header(r) for r in self._con.execute(sql, args))

    def _candidate_query(self, commodity, max_age, side, min_quantity, limit, cursor,
                         system_address, system_name, market_ids=None, min_sell_price=None):
        if type(limit) is not int or not 1 <= limit <= MAX_PAGE:
            raise ValueError('Invalid page size')
        if side is not None and not isinstance(side, TradeSide):
            raise ValueError('Expected TradeSide')
        if side is not None and commodity is None:
            raise ValueError('A side requires a commodity')
        amount = encode_u64(min_quantity, 1)
        low, now = self._range(max_age)
        params = []
        sql = _HEADERS
        if commodity is not None:
            key = self._commodity_id(commodity)
            sql = sql.replace('SELECT ' + _HEADER_COLUMNS,
                              'SELECT ' + _HEADER_COLUMNS + ',v.*,k.frontier_id')
            sql += ' LEFT JOIN commodity_observations v ON v.snapshot_id=o.snapshot_id AND v.commodity_key=?'
            sql += ' LEFT JOIN commodity_keys k ON k.commodity_key=v.commodity_key'
            params.append(key)
        sql += ' WHERE c.observed_at<=?'
        params.append(now)
        if low is not None:
            sql += ' AND c.observed_at>=?'
            params.append(low)
        if cursor is not None:
            sql += ' AND c.market_id>?'
            params.append(encode_u64(cursor, 1))
        if system_address is not None:
            sql += ' AND c.system_address=?'
            params.append(encode_u64(system_address, 1))
        if system_name is not None:
            sql += ' AND c.system_name_key=?'
            params.append(system_name.casefold())
        if market_ids is not None:
            ids = []
            for mid in market_ids:
                if len(ids) >= MAX_PAGE:
                    raise ValueError('Too many market IDs')
                ids.append(encode_u64(mid, 1))
            sql += ' AND c.market_id IN (' + ','.join('?' for _ in ids) + ')'
            params.extend(ids)
        if min_sell_price is not None:
            if commodity is None:
                raise ValueError('A minimum price requires a commodity')
            sql += ' AND v.commander_sell_price>=?'
            params.append(encode_u64(min_sell_price))
        if side is not None:
            price, quantity = (('commander_buy_price', 'supply') if side == TradeSide.BUY
                               else ('commander_sell_price', 'demand'))
            sql += f' AND v.{price}>? AND v.{quantity}>=?'
            params.extend((ZERO, amount))
        return sql + ' ORDER BY c.market_id LIMIT ?', (*params, limit + 1)

    def query_current_candidates(self, commodity=None, *, max_age=TTL, side=None,
                                 min_quantity=1, limit=100, cursor=None, system_address=None,
                                 system_name=None, expected_revision=None, market_ids=None, min_sell_price=None):
        """MarketID-ordered pages, not a prematurely truncated price ranking.

        side=None preserves missing/non-trading commodities as freshness evidence.
        BUY/SELL explicitly request only positive-price, sufficient-quantity rows.
        commodity=None returns headers only. Revision guards allow restart if a
        concurrent commit changes the store between pages.
        """
        with self._transaction():
            revision = self._revision()
            if expected_revision is not None and revision != expected_revision:
                raise StaleReadError('MarketStore changed between pages')
            sql, params = self._candidate_query(commodity, max_age, side, min_quantity,
                                                limit, cursor, system_address, system_name, market_ids, min_sell_price)
            rows = self._con.execute(sql, params).fetchall()
            items = tuple(MarketCandidate(self._header(r), self._value(r)
                          if commodity is not None and r['commodity_key'] is not None else None) for r in rows[:limit])
            next_cursor = items[-1].header.market_id if len(rows) > limit else None
            return MarketPage(items, next_cursor, revision)

    def get_history(self, fid, market_id, since=None, cursor=None, *, limit=100, expected_revision=None):
        """Last 30 days, newest first; use get_observation for rows.

        The last-known snapshot may be older; get_current(..., max_age=None)
        retrieves it independently of the historical window and cleanup.
        """
        self._fid(fid)
        if type(limit) is not int or not 1 <= limit <= MAX_PAGE:
            raise ValueError('Invalid page size')
        low, now = self._range(HISTORY_RETENTION, since)
        sql = f'''SELECT {_HEADER_COLUMNS} FROM market_observations o JOIN market_snapshots s
            ON s.snapshot_id=o.snapshot_id WHERE o.fid=? AND o.market_id=? AND o.observed_at<=?'''
        args = [fid, encode_u64(market_id, 1), now]
        if low is not None:
            sql += ' AND o.observed_at>=?'
            args.append(low)
        if cursor is not None:
            if not isinstance(cursor, HistoryCursor):
                raise TypeError('Expected HistoryCursor')
            sql += ' AND (o.observed_at,o.observation_id)<(?,?)'
            args.extend((cursor.observed_at_us, cursor.observation_id))
        sql += ' ORDER BY o.observed_at DESC,o.observation_id DESC LIMIT ?'
        with self._transaction():
            revision = self._revision()
            if expected_revision is not None and revision != expected_revision:
                raise StaleReadError('MarketStore changed between history pages')
            rows = self._con.execute(sql, (*args, limit + 1)).fetchall()
            items = tuple(self._header(r) for r in rows[:limit])
            next_cursor = HistoryCursor(rows[limit-1]['observed_at'], items[-1].observation_id) if len(rows) > limit else None
            return MarketPage(items, next_cursor, revision)

    def get_observation(self, fid, observation_id):
        """Read one historical observation; ID never bypasses FID isolation."""
        self._fid(fid)
        if type(observation_id) is not int or observation_id <= 0:
            raise ValueError('Invalid observation ID')
        with self._transaction():
            row = self._con.execute(f'''SELECT {_HEADER_COLUMNS} FROM market_observations o
                JOIN market_snapshots s ON s.snapshot_id=o.snapshot_id
                WHERE o.fid=? AND o.observation_id=?''', (fid, observation_id)).fetchone()
            return self._snapshot(self._header(row)) if row else None

    def _best_query(self, key, scope, max_age, since, min_demand, *, time_range=None):
        if scope not in ('current', 'last_known', 'history'):
            raise ValueError('Invalid price scope')
        low, now = time_range if time_range is not None else self._range(max_age, since)
        sql = f'''SELECT {_HEADER_COLUMNS},v.*,k.frontier_id FROM commodity_observations v
            JOIN commodity_keys k ON k.commodity_key=v.commodity_key
            JOIN market_snapshots s ON s.snapshot_id=v.snapshot_id
            JOIN market_observations o ON o.snapshot_id=s.snapshot_id'''
        if scope != 'history':
            sql += ' JOIN current_markets c ON c.observation_id=o.observation_id'
        sql += ' WHERE v.commodity_key=? AND o.observed_at<=? AND v.commander_sell_price>? AND v.demand>=?'
        args = [key, now, ZERO, encode_u64(min_demand, 1)]
        if low is not None:
            sql += ' AND o.observed_at>=?'
            args.append(low)
        return sql + ' ORDER BY v.commander_sell_price DESC,o.observed_at DESC,o.market_id LIMIT 1', args

    def best_sell_prices(self, commodities, *, scope='current', max_age=TTL, since=None, min_demand=1):
        """One shared qualified best quote per identity; no quote is not zero.

        current: latest per market within the search age. last_known: latest per
        market regardless of age (since is disallowed). history: at most 30 days,
        even before an explicit cleanup. Fixed Mining references do not belong
        to this store. History reports the actual confirming visit and location.
        """
        refs = {}
        for count, ref in enumerate(commodities, 1):
            if count > 128:
                raise ValueError('Too many commodities; request bounded batches')
            if not isinstance(ref, CommodityRef):
                raise TypeError('Expected CommodityRef')
            refs[ref] = None
        with self._transaction():
            result = []
            if scope == 'last_known':
                if since is not None:
                    raise ValueError('last_known does not accept a historical cutoff')
                max_age = None
            elif scope == 'history':
                if max_age is not None and (not isinstance(max_age, timedelta) or max_age < timedelta(0)):
                    raise ValueError('Invalid maximum age')
                max_age = min(max_age, HISTORY_RETENTION) if max_age is not None else HISTORY_RETENTION
            time_range = self._range(max_age, since)
            # Validate even an empty commodity request.
            self._best_query(None, scope, max_age, since, min_demand, time_range=time_range)
            for ref in refs:
                sql, args = self._best_query(self._commodity_id(ref), scope, max_age, since,
                                              min_demand, time_range=time_range)
                row = self._con.execute(sql, args).fetchone()
                if row:
                    result.append(MarketCandidate(self._header(row), self._value(row), scope))
            return tuple(result)

    def cleanup(self, *, cancel=None):
        """Explicit worker-only, atomic retention; never invoked by a read/write.

        Preserve the shared current observation of every MarketID, however old. Delete
        additional observations strictly older than 30 days, then only payloads
        with no remaining observation references. FK constraints additionally
        protect current observations and referenced snapshots.
        """
        self._check_thread()
        _assert_not_gui_thread()
        cutoff = _micros(self.clock() - HISTORY_RETENTION)

        def check_cancel():
            if cancel is not None and cancel.is_set():
                raise CleanupCancelled('Cleanup cancelled before commit')

        check_cancel()
        try:
            with self._transaction(write=True):
                self._con.set_progress_handler(lambda: int(cancel is not None and cancel.is_set()), 1000)
                try:
                    removed_observations = self._con.execute('''DELETE FROM market_observations
                        WHERE observed_at < ? AND NOT EXISTS
                        (SELECT 1 FROM current_markets c WHERE c.observation_id=market_observations.observation_id)''',
                        (cutoff,)).rowcount
                    check_cancel()
                    removed_rows = self._con.execute('''SELECT COALESCE(SUM(commodity_count),0)
                        FROM market_snapshots s WHERE NOT EXISTS
                        (SELECT 1 FROM market_observations o WHERE o.snapshot_id=s.snapshot_id)''').fetchone()[0]
                    removed_snapshots = self._con.execute('''DELETE FROM market_snapshots
                        WHERE NOT EXISTS (SELECT 1 FROM market_observations o
                        WHERE o.snapshot_id=market_snapshots.snapshot_id)''').rowcount
                    check_cancel()
                    removed_keys = self._con.execute('''DELETE FROM commodity_keys WHERE NOT EXISTS
                        (SELECT 1 FROM commodity_observations v WHERE v.commodity_key=commodity_keys.commodity_key)''').rowcount
                    if removed_observations or removed_snapshots or removed_keys:
                        self._con.execute("UPDATE store_meta SET value=CAST(value AS INTEGER)+1 WHERE key='revision'")
                    revision = self._revision()
                    check_cancel()
                finally:
                    # ROLLBACK must not itself be interrupted by the handler.
                    self._con.set_progress_handler(None, 0)
        except sqlite3.OperationalError as exc:
            if getattr(exc, 'sqlite_errorcode', None) == sqlite3.SQLITE_INTERRUPT:
                raise CleanupCancelled('Cleanup interrupted; transaction rolled back') from exc
            raise
        return CleanupResult(removed_observations, removed_snapshots, removed_rows,
                             removed_keys, revision, _datetime(cutoff))

    def storage_stats(self):
        """Small indexed aggregate; call on the owning worker, never the GUI."""
        with self._transaction():
            count = self._con.execute(
                'SELECT COUNT(*) FROM stations').fetchone()[0]
        return count, market_storage_bytes(self.path)

    def get_stats(self):
        with self._transaction():
            counts = [self._con.execute('SELECT COUNT(*) FROM ' + name).fetchone()[0]
                      for name in ('stations', 'current_markets', 'market_observations',
                                   'market_snapshots', 'commodity_observations')]
            revision = self._revision()
        sizes = []
        for suffix in ('', '-wal', '-shm'):
            try:
                sizes.append(Path(str(self.path) + suffix).stat().st_size)
            except FileNotFoundError:
                sizes.append(0)
        return StoreStats(*counts, revision, *sizes)


def market_storage_bytes(path):
    """Actual file lengths, including uncheckpointed WAL and its shared index."""
    total = 0
    for suffix in ('', '-wal', '-shm'):
        try:
            total += Path(str(path) + suffix).stat().st_size
        except FileNotFoundError:
            if not suffix:
                raise
    return total
