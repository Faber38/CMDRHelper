"""Bounded local Elite observations, independent of Qt, SQLite and Spansh.

Only normalize_observation accepts Frontier input. Persisted snapshots are also
validated on every load/write; localized strings never establish identity.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import logging
import os
from pathlib import Path
import re
import tempfile

from .commodity_master import lookup_by_id, lookup_by_symbol
from .odyssey_sidecars import signature, _unique_object

from .market_data import within_market_age
from .station_types import normalize_station_type

logger = logging.getLogger(__name__)

TTL = timedelta(hours=24)
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_SIDECAR_BYTES = 4 * 1024 * 1024
MAX_MARKETS = 2048  # Across all commanders; no eviction of valid markets.
MAX_COMMODITIES = 2048
SCHEMA_VERSION = 1


def utcnow():
    return datetime.now(timezone.utc)


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('Missing timestamp')
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timestamp requires offset')
    return parsed.astimezone(timezone.utc)


def valid_fid(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,128}', value) is not None


def _text(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 512:
        raise ValueError('Invalid text field')
    return value


def _integer(value, minimum=0):
    if type(value) is not int or not minimum <= value < 2**64:
        raise ValueError('Invalid integer field')
    return value


def _json(raw):
    def reject(value):
        raise ValueError('Non-JSON numeric constant')
    return json.loads(raw, object_pairs_hook=_unique_object, parse_constant=reject)


def read_market(path):
    """Bounded stable read; never modify a game file."""
    path = Path(path)
    before = signature(path)
    if before[2] > MAX_SIDECAR_BYTES:
        raise ValueError('Market sidecar size limit')
    with path.open('rb') as stream:
        raw = stream.read(MAX_SIDECAR_BYTES + 1)
    if len(raw) != before[2] or signature(path) != before:
        raise OSError('Market sidecar changed during read')
    return _json(raw), before


def _identity(commodity_id, symbol):
    _text(symbol)
    if commodity_id is not None:
        _integer(commodity_id, 1)
    by_id, by_symbol = lookup_by_id(commodity_id), lookup_by_symbol(symbol)
    if by_id is not None and by_id != by_symbol:
        raise ValueError('Commodity ID/symbol conflict')
    if by_symbol is not None and commodity_id not in (None, by_symbol.frontier_id):
        raise ValueError('Commodity symbol/ID conflict')
    known = by_id or by_symbol
    return (known.frontier_id, known.symbol) if known else (commodity_id, symbol)


def validate_snapshot(value):
    if not isinstance(value, dict) or value.get('source') != 'local_elite' or not valid_fid(value.get('fid')):
        raise ValueError('Invalid local market source/context')
    result = dict(fid=value['fid'], source='local_elite',
                  market_id=_integer(value.get('market_id'), 1),
                  station_name=_text(value.get('station_name')),
                  system_name=_text(value.get('system_name')),
                  observed_at=timestamp(value.get('observed_at')).isoformat())
    if 'system_address' in value:
        result['system_address'] = _integer(value['system_address'], 1)
    if 'station_type' in value:
        result['station_type'] = _text(value['station_type'])
    rows = value.get('commodities')
    if not isinstance(rows, list) or len(rows) > MAX_COMMODITIES:
        raise ValueError('Invalid commodities/limit')
    result['commodities'] = []
    ids, symbols = set(), set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid commodity')
        cid, symbol = _identity(row.get('commodity_id'), row.get('symbol'))
        key = symbol.casefold()
        if key in symbols or cid is not None and cid in ids:
            raise ValueError('Duplicate commodity')
        symbols.add(key)
        if cid is not None:
            ids.add(cid)
        item = dict(commodity_id=cid, symbol=symbol)
        for name in ('commander_buy_price', 'commander_sell_price', 'supply', 'demand'):
            item[name] = _integer(row.get(name))
        for name in ('localized_name', 'category'):
            if name in row:
                item[name] = _text(row[name])
        result['commodities'].append(item)
    return result


def normalize_observation(event, sidecar, *, fid, mtime, now, context=None):
    """Require an exact journal witness, never use file mtime as observed_at.

    mtime is a plausibility guard (2 s filesystem granularity), not an identity.
    The observer separately proves this event is newly appended after arming.
    """
    if not isinstance(event, dict) or not isinstance(sidecar, dict) or not valid_fid(fid):
        raise ValueError('Missing market witness/context')
    if event.get('event') != 'Market' or sidecar.get('event') != 'Market':
        raise ValueError('Not a local Market event')
    stamp = timestamp(event.get('timestamp'))
    if stamp != timestamp(sidecar.get('timestamp')) or not timedelta(0) <= now - stamp < TTL:
        raise ValueError('Market timestamp mismatch/expired/future')
    if mtime < stamp.timestamp() - 2 or mtime > now.timestamp() + 2:
        raise ValueError('Market file time inconsistent')
    context = context or {}
    for obj in (event, sidecar, context):
        if 'FID' in obj and obj['FID'] != fid:
            raise ValueError('Commander context mismatch')
    for name in ('MarketID', 'StationName', 'StarSystem'):
        if event.get(name) != sidecar.get(name) or name in context and event.get(name) != context[name]:
            raise ValueError('Market identity mismatch: ' + name)
    result = dict(fid=fid, source='local_elite', market_id=event.get('MarketID'),
                  station_name=event.get('StationName'), system_name=event.get('StarSystem'),
                  observed_at=stamp.isoformat(), commodities=[])
    for name, dest in (('SystemAddress', 'system_address'), ('StationType', 'station_type')):
        values = [obj[name] for obj in (event, sidecar, context) if name in obj]
        if values:
            comparable = ([normalize_station_type(value) for value in values]
                          if name == 'StationType' else values)
            if any(value != comparable[0] for value in comparable):
                raise ValueError('Market context mismatch: ' + name)
            result[dest] = values[0]
    rows = sidecar.get('Items')
    if not isinstance(rows, list) or len(rows) > MAX_COMMODITIES:
        raise ValueError('Invalid market Items/limit')
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid market Item')
        item = dict(commodity_id=row.get('id'), symbol=row.get('Name'),
                    commander_buy_price=row.get('BuyPrice'), commander_sell_price=row.get('SellPrice'),
                    supply=row.get('Stock'), demand=row.get('Demand'))
        for name, dest in (('Name_Localised', 'localized_name'), ('Category', 'category')):
            if name in row:
                item[dest] = row[name]
        result['commodities'].append(item)
    return validate_snapshot(result)


def shared_current(rows, now=None):
    """One complete latest observation per MarketID; deterministic ties by FID."""
    winners = {}
    for row in rows:
        if row.get('source') != 'local_elite' or (now is not None and timestamp(row['observed_at']) > now):
            continue
        previous = winners.get(row['market_id'])
        if (previous is None or timestamp(row['observed_at']) > timestamp(previous['observed_at'])
                or (timestamp(row['observed_at']) == timestamp(previous['observed_at'])
                    and row['fid'] < previous['fid'])):
            winners[row['market_id']] = row
    return tuple(winners.values())


def cache_path():
    # Same cross-platform AppData convention as the existing snapshot managers.
    from PySide6.QtCore import QStandardPaths
    base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    if not base:
        raise OSError('AppDataLocation unavailable')
    return Path(base) / 'market_cache' / 'observed_markets.json'


class ObservedMarketCache:
    """Single-process cache, partitioned by FID. API returns defensive copies.

    Invalid disk content is ignored in full and diagnosed, not partially trusted.
    A later valid observation can replace it. Failed writes never advance memory.
    """
    def __init__(self, path, *, clock=utcnow, on_changed=None, load=True):
        self.path, self.clock = Path(path), clock
        self.on_changed = None
        self._markets = {}
        self.last_error = None
        if load:
            self._load()
        self.on_changed = on_changed

    @staticmethod
    def age(snapshot, now=None):
        return (now if now is not None else utcnow()) - timestamp(snapshot['observed_at'])

    @classmethod
    def is_valid(cls, snapshot, now=None, max_age=TTL):
        return within_market_age(cls.age(snapshot, now), max_age)

    def _load(self):
        try:
            with self.path.open('rb') as stream:
                raw = stream.read(MAX_FILE_BYTES + 1)
            if len(raw) > MAX_FILE_BYTES:
                raise ValueError('Market cache size limit')
            data = _json(raw)
            if not isinstance(data, dict) or type(data.get('version')) is not int or data['version'] != SCHEMA_VERSION:
                raise ValueError('Invalid market cache version')
            rows = data.get('markets')
            if not isinstance(rows, list) or len(rows) > MAX_MARKETS:
                raise ValueError('Invalid markets/limit')
            loaded = {}
            for row in rows:
                snapshot = validate_snapshot(row)
                key = snapshot['fid'], snapshot['market_id']
                if key in loaded:
                    raise ValueError('Duplicate market identity')
                loaded[key] = snapshot
            self._markets = loaded
        except FileNotFoundError:
            pass
        except (OSError, ValueError, TypeError, OverflowError, RecursionError) as exc:
            self._markets = {}
            self._error(exc)

    def _error(self, exc):
        self.last_error = str(exc)
        logger.warning('Observed market cache: %s', exc)

    def _write(self, markets):
        temporary = None
        try:
            if len(markets) > MAX_MARKETS:
                raise ValueError('Market count limit')
            raw = json.dumps(dict(version=SCHEMA_VERSION, markets=list(markets.values())),
                             ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf-8')
            if len(raw) > MAX_FILE_BYTES:
                raise ValueError('Market cache size limit')
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=self.path.parent, prefix='.observed-', suffix='.tmp', delete=False) as stream:
                temporary = stream.name
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            self._markets = markets
            self.last_error = None
        except (OSError, ValueError) as exc:
            self._error(exc)
            return False
        finally:
            if temporary is not None:
                try:
                    Path(temporary).unlink(missing_ok=True)
                except OSError:
                    logger.warning('Cannot remove temporary observed market file')
        # Notify only after the atomic commit and temporary-file handling.
        if self.on_changed is not None:
            self.on_changed()
        return True

    def cleanup(self):
        # Age is a search criterion, not a retention policy.
        return True

    def put(self, snapshot):
        if getattr(self, 'sqlite_writer_enabled', False):
            self._error('Use MarketWriteWorker; JSON migration source is read-only')
            return False
        try:
            snapshot = validate_snapshot(snapshot)
            if not self.is_valid(snapshot, self.clock(), None):
                raise ValueError('Observation from future')
            markets = dict(self._markets)
            key = snapshot['fid'], snapshot['market_id']
            previous = markets.get(key)
            if previous and timestamp(previous['observed_at']) >= timestamp(snapshot['observed_at']):
                if previous != snapshot and previous['observed_at'] == snapshot['observed_at']:
                    raise ValueError('Ambiguous observations at same timestamp')
                return self.cleanup()
            markets[key] = snapshot
            return self._write(markets)
        except (ValueError, TypeError, OverflowError) as exc:
            self._error(exc)
            return False

    def storage_stats(self):
        """Unique stored stations across commanders and actual bytes on disk.

        Read metadata only; neither age filtering nor cache mutation is involved.
        """
        writer = getattr(self, 'store_writer', None)
        if writer is not None and writer.authoritative:
            from .market_store import market_storage_bytes
            if writer.last_error:
                raise RuntimeError(writer.last_error)
            if not writer.activated:
                raise RuntimeError('markets.db initialization pending')
            return writer.station_count, market_storage_bytes(writer.destination)
        try:
            size = self.path.stat().st_size
        except FileNotFoundError:
            return 0, 0
        return len({row['market_id'] for row in self._markets.values()}), size

    def all(self, fid, max_age=TTL):
        if hasattr(self, '_store_headers'):
            raise RuntimeError('Market prices require MarketStore; only headers are cached')
        if not valid_fid(fid):
            return []
        now = self.clock()
        return deepcopy([row for (owner, _), row in self._markets.items()
                         if owner == fid and self.is_valid(row, now, max_age)])

    def shared(self, max_age=TTL):
        if hasattr(self, '_store_headers'):
            raise RuntimeError('Market prices require MarketStore')
        return deepcopy([r for r in shared_current(self._markets.values(), self.clock())
                         if self.is_valid(r, self.clock(), max_age)])

    def get_header(self, market_id, max_age=TTL):
        """O(1) metadata-only view; never copy a commodity list or query a DB."""
        rows = getattr(self, '_store_headers', None)
        row = (rows.get(market_id) if rows is not None else
               next((r for r in shared_current(self._markets.values(), self.clock()) if r['market_id'] == market_id), None))
        if row is None or not self.is_valid(row, self.clock(), max_age):
            return None
        return {k: v for k, v in row.items() if k != 'commodities'}

    def install_headers(self, headers):
        self.last_error = None
        self._store_headers = headers
        # All production price readers use SQLite now. Retain identity/status
        # metadata, release the legacy JSON payload after successful activation.
        self._markets = headers
        if self.on_changed is not None:
            self.on_changed()

    def apply_committed_header(self, snapshot):
        key = snapshot['market_id']
        headers = dict(getattr(self, '_store_headers', {}))
        previous = headers.get(key)
        if (previous is None or timestamp(previous['observed_at']) < timestamp(snapshot['observed_at'])
                or (previous['observed_at'] == snapshot['observed_at'] and snapshot['fid'] < previous['fid'])):
            headers[key] = {k: v for k, v in snapshot.items() if k != 'commodities'}
            self.install_headers(headers)

    def get(self, fid, market_id, max_age=TTL):
        return next((row for row in self.all(fid, max_age) if row['market_id'] == market_id), None)

    def find(self, fid, system_name, station_name):
        return [row for row in self.all(fid) if row['system_name'].casefold() == system_name.casefold()
                and row['station_name'].casefold() == station_name.casefold()]
