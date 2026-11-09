"""Bounded public system knowledge in JSON; this module never opens SQLite."""
from cmdrhelper import performance_profile as profile
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError
import json
import logging
import math
import os
from pathlib import Path
import tempfile
from threading import RLock, Lock
from urllib.request import Request, urlopen
from cmdrhelper.belt_projection import is_belt_cluster
from cmdrhelper.version import __version__

logger = logging.getLogger(__name__)
_write_locks = {}
_write_guard = Lock()

def _cache_lock(root, address):
    with _write_guard:
        return _write_locks.setdefault((str(Path(root).resolve()), address), RLock())

TTL = timedelta(days=90)
ERROR_PAUSE = timedelta(minutes=5)
MAX_RESPONSE = 16 * 1024 * 1024
MAX_CACHE = 2 * 1024 * 1024
ENDPOINT = 'https://spansh.co.uk/api/dump/'
SERVICES = {
    'Market': 'market', 'Shipyard': 'shipyard', 'Outfitting': 'outfitting',
    'Material Trader': 'material_trader', 'Universal Cartographics': 'cartographics',
    'Vista Genomics': 'vista', 'Pioneer Supplies': 'pioneer', 'Bartender': 'bartender',
    'Apex Interstellar': 'apex', 'Frontline Solutions': 'frontline',
    'Interstellar Factors': 'factors', 'Interstellar Factors Contact': 'factors',
    'Repair': 'repair', 'Refuel': 'refuel', 'Restock': 'restock', 'Search and Rescue': 'rescue',
}
TYPES = {'Dodec Starport': 'Dodec', 'Coriolis Starport': 'Coriolis', 'Orbis Starport': 'Orbis',
         'Ocellus Starport': 'Ocellus', 'Planetary Port': 'CraterPort',
         'Planetary Outpost': 'CraterOutpost', 'Settlement': 'OnFootSettlement',
         'Megaship': 'MegaShip'}
SURFACE_TYPES = {'Planetary Port', 'Planetary Outpost', 'Settlement', 'Planetary Construction Depot'}
TEXT_FIELDS = {'station_name', 'station_type', 'source_type', 'body_name', 'allegiance',
               'government', 'controlling_faction', 'primary_economy', 'secondary_economy',
               'station_updated_at'}
INT_FIELDS = {'market_id', 'parent_body_id', 'parent_body_id64'}
NUM_FIELDS = {'distance_ls', 'latitude', 'longitude'}
STATION_FIELDS = TEXT_FIELDS | INT_FIELDS | NUM_FIELDS | {'is_planetary', 'economies', 'landing_pads', 'services'}


def utcnow():
    return datetime.now(timezone.utc)


def valid_id(value):
    return type(value) is int and 0 < value < 2**64


def timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except (ValueError, OverflowError):
        return None


def number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        return False


def is_carrier(kind):
    return 'carrier' in str(kind or '').casefold()


def cache_directory():
    from PySide6.QtCore import QStandardPaths
    base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    if not base:
        raise OSError('No writable application data location')
    return Path(base) / 'external' / 'spansh'


def normalize(response, address, now=None):
    """The dump nests surface stations under explicit bodyId/id64 parents.

    The dump's station `id` is the numeric market identifier. System-level
    stations carry no parent; distance or names must never supply one.
    """
    if not valid_id(address) or not isinstance(response, dict) or response.get('error'):
        raise ValueError('Invalid system address/response')
    system = response.get('system')
    if not isinstance(system, dict) or type(system.get('id64')) is not int or system['id64'] != address:
        raise ValueError('Spansh system identity mismatch')
    if not isinstance(system.get('name'), str) or not system['name'].strip():
        raise ValueError('Missing system name')
    if system.get('date') is not None and not timestamp(system['date']):
        raise ValueError('Invalid system timestamp')
    stations = []
    def add(raw, parent=None):
        if not isinstance(raw, dict):
            raise ValueError('Invalid station record')
        if (is_carrier(raw.get('type'))
                or (isinstance(raw.get('services'), list) and any(
                    v in ('Fleet Carrier Fuel', 'Fleet Carrier Management') for v in raw['services']))):
            return
        mid = raw.get('id')
        if not valid_id(mid) or not isinstance(raw.get('name'), str) or not raw['name'].strip():
            raise ValueError('Invalid station identity')
        if raw.get('type') is not None and not isinstance(raw['type'], str):
            raise ValueError('Invalid station type')
        for key in ('distanceToArrival', 'latitude', 'longitude'):
            if raw.get(key) is not None and not number(raw[key]):
                raise ValueError('Invalid station number')
        for key in ('services',):
            if raw.get(key) is not None and (not isinstance(raw[key], list)
                    or any(not isinstance(v, str) for v in raw[key])):
                raise ValueError('Invalid station services')
        for key in ('economies', 'landingPads'):
            if raw.get(key) is not None and (not isinstance(raw[key], dict)
                    or any(not isinstance(k, str) or not number(v) or v < 0
                           for k, v in raw[key].items())):
                raise ValueError('Invalid station mapping')
        if raw.get('updateTime') is not None and not timestamp(raw['updateTime']):
            raise ValueError('Invalid station timestamp')
        for key in ('allegiance', 'government', 'controllingFaction', 'primaryEconomy', 'secondaryEconomy'):
            if raw.get(key) is not None and not isinstance(raw[key], str):
                raise ValueError('Invalid station text')
        if raw.get('isPlanetary') is not None and type(raw['isPlanetary']) is not bool:
            raise ValueError('Invalid surface flag')
        if isinstance(raw.get('landingPads'), dict) and any(
                type(v) is not int for k, v in raw['landingPads'].items()
                if k in ('large', 'medium', 'small')):
            raise ValueError('Invalid pad count')
        row = {'market_id': mid, 'station_name': raw['name']}
        for source, dest in [('type','source_type'), ('allegiance','allegiance'),
                             ('government','government'), ('controllingFaction','controlling_faction'),
                             ('primaryEconomy','primary_economy'), ('secondaryEconomy','secondary_economy')]:
            if isinstance(raw.get(source), str) and raw[source]: row[dest] = raw[source]
        if row.get('source_type'):
            row['station_type'] = TYPES.get(row['source_type'], row['source_type'])
        for source, dest in [('distanceToArrival','distance_ls'), ('latitude','latitude'), ('longitude','longitude')]:
            if number(raw.get(source)): row[dest] = raw[source]
        if timestamp(raw.get('updateTime')): row['station_updated_at'] = raw['updateTime']
        if type(raw.get('isPlanetary')) is bool:
            row['is_planetary'] = raw['isPlanetary']
        elif raw.get('type') in SURFACE_TYPES:
            row['is_planetary'] = True
        if isinstance(parent, dict) and parent.get('type') in ('Star', 'Planet'):
            bid = parent.get('bodyId')
            if type(bid) is int and 0 <= bid < 512: row['parent_body_id'] = bid
            if valid_id(parent.get('id64')): row['parent_body_id64'] = parent['id64']
            if isinstance(parent.get('name'), str): row['body_name'] = parent['name']
        if isinstance(raw.get('economies'), dict):
            row['economies'] = {k:v for k,v in raw['economies'].items() if isinstance(k,str) and number(v) and v >= 0}
        if isinstance(raw.get('landingPads'), dict):
            row['landing_pads'] = {k:v for k,v in raw['landingPads'].items()
                                   if k in ('large','medium','small') and type(v) is int and v >= 0}
        if isinstance(raw.get('services'), list):
            row['services'] = sorted({SERVICES[v] for v in raw['services'] if isinstance(v,str) and v in SERVICES})
        stations.append(row)
    raw_stations = system.get('stations')
    bodies = system.get('bodies')
    if not isinstance(raw_stations, list) or not isinstance(bodies, list):
        raise ValueError('Invalid station/body list')
    for raw in raw_stations: add(raw)
    for body in bodies:
        if not isinstance(body, dict) or not isinstance(body.get('stations'), list):
            raise ValueError('Invalid body stations')
        for raw in body.get('stations', []): add(raw, body)
    # Exact duplicates are harmless. A contradictory dump must not replace
    # previously complete knowledge or renew its successful-check timestamp.
    unique, ambiguous = {}, set()
    for row in stations:
        mid = row['market_id']
        if mid in unique and unique[mid] != row: ambiguous.add(mid)
        unique[mid] = row
    if ambiguous:
        raise ValueError('Conflicting station identities')
    result = {'schema_version': 1, 'source': 'spansh', 'system_address': address,
              'system_name': system['name'], 'fetched_at': (now or utcnow()).isoformat(),
              'stations': [row for mid,row in sorted(unique.items()) if mid not in ambiguous]}
    if timestamp(system.get('date')): result['source_updated_at'] = system['date']
    coords = system.get('coords')
    if isinstance(coords, dict) and all(number(coords.get(k)) for k in ('x','y','z')):
        result['coordinates'] = {k: coords[k] for k in ('x','y','z')}
    validate(result, address)
    return result


def validate(data, address):
    if not valid_id(address) or not isinstance(data, dict): raise ValueError('Invalid cache')
    required = {'schema_version','source','system_address','system_name','fetched_at','stations'}
    if not required <= data.keys() or data.keys() - (required | {'source_updated_at', 'coverage', 'coordinates'}): raise ValueError('Invalid cache fields')
    if type(data['schema_version']) is not int or data['schema_version'] != 1 or data['source'] != 'spansh': raise ValueError('Invalid cache version/source')
    if type(data['system_address']) is not int or data['system_address'] != address: raise ValueError('Cache system mismatch')
    if not isinstance(data['system_name'], str) or not data['system_name'] or not timestamp(data['fetched_at']): raise ValueError('Invalid cache metadata')
    if 'source_updated_at' in data and not timestamp(data['source_updated_at']): raise ValueError('Invalid source date')
    if not isinstance(data['stations'], list) or len(data['stations']) > 5000: raise ValueError('Invalid stations')
    if data.get('coverage', 'full') not in ('full', 'partial'): raise ValueError('Invalid cache coverage')
    if 'coordinates' in data:
        coords = data['coordinates']
        if (not isinstance(coords, dict) or set(coords) != {'x','y','z'}
                or not all(number(v) for v in coords.values())): raise ValueError('Invalid coordinates')
    seen = set()
    for row in data['stations']:
        if not isinstance(row, dict) or row.keys() - STATION_FIELDS: raise ValueError('Invalid station fields')
        mid = row.get('market_id')
        if not valid_id(mid) or mid in seen or not row.get('station_name'): raise ValueError('Invalid station identity')
        seen.add(mid)
        for key,value in row.items():
            if key in TEXT_FIELDS and (not isinstance(value,str) or len(value)>1024): raise ValueError('Invalid station text')
            if key in INT_FIELDS and (type(value) is not int or value < (0 if key == 'parent_body_id' else 1) or value >= 2**64): raise ValueError('Invalid station ID')
            if key in NUM_FIELDS and not number(value): raise ValueError('Invalid station number')
        if 'station_updated_at' in row and not timestamp(row['station_updated_at']): raise ValueError('Invalid station date')
        if 'is_planetary' in row and type(row['is_planetary']) is not bool: raise ValueError('Invalid surface flag')
        if 'services' in row and (not isinstance(row['services'],list) or any(type(v) is not str or v not in SERVICES.values() for v in row['services'])): raise ValueError('Invalid services')
        for field in ('economies','landing_pads'):
            if field in row:
                if not isinstance(row[field],dict): raise ValueError('Invalid station mapping')
                for key,value in row[field].items():
                    if not isinstance(key,str) or not number(value) or value < 0: raise ValueError('Invalid station mapping value')
                    if field == 'landing_pads' and (key not in ('large','medium','small') or type(value) is not int): raise ValueError('Invalid pad count')
    return data


def fetch_system(address):
    if not valid_id(address): raise ValueError('Invalid system address')
    request = Request(ENDPOINT + str(address), headers={'User-Agent':f'CMDRHelper/{__version__}', 'Accept':'application/json'})
    with urlopen(request, timeout=15) as response:
        payload = response.read(MAX_RESPONSE + 1)
    if len(payload) > MAX_RESPONSE: raise ValueError('Spansh response too large')
    return json.loads(payload)


class SystemCache:
    def __init__(self, root=None, fetch=fetch_system, now=utcnow):
        self._root = Path(root) if root is not None else None
        self.fetch, self.now = fetch, now
        self._attempts = {}

    @property
    def root(self):
        if self._root is None:
            self._root = cache_directory()
        return self._root

    def path(self, address):
        if not valid_id(address): raise ValueError('Invalid system address')
        return self.root / f'{address}.json'

    def read(self, address):
        try:
            with self.path(address).open('rb') as stream: raw = stream.read(MAX_CACHE + 1)
            if len(raw) > MAX_CACHE: raise ValueError('Cache too large')
            return validate(json.loads(raw), address)
        except FileNotFoundError:
            return None
        except (OSError, ValueError, TypeError):
            logger.debug('Ignoring invalid Spansh cache for %s', address, exc_info=True)
            return None

    def fresh(self, data):
        if data.get('coverage', 'full') != 'full': return False
        age = self.now() - timestamp(data['fetched_at'])
        return timedelta(0) <= age < TTL

    def merge_lookup(self, data):
        """Merge selected stations without renewing a full dump's freshness."""
        validate(data, data.get('system_address'))
        if data.get('coverage') != 'partial': raise ValueError('Expected partial lookup')
        address = data['system_address']
        with _cache_lock(self.root, address):
            old = self.read(address)
            if old is None:
                self.write(data)
                return
            if old['system_name'].casefold() != data['system_name'].casefold():
                raise ValueError('Conflicting system identity')
            if old.get('coordinates') and data.get('coordinates') and old['coordinates'] != data['coordinates']:
                raise ValueError('Conflicting system coordinates')
            merged = deepcopy(old)
            by_id = {r['market_id']: r for r in merged['stations']}
            for row in data['stations']:
                previous = by_id.get(row['market_id'])
                if previous and previous['station_name'].casefold() != row['station_name'].casefold():
                    raise ValueError('Conflicting station identity')
                if previous:
                    # Keep dump-only parent/body information. Older lookup metadata
                    # cannot replace a newer station record.
                    before = timestamp(previous.get('station_updated_at'))
                    after = timestamp(row.get('station_updated_at'))
                    if before and (not after or after < before): continue
                    previous.update(row)
                else:
                    by_id[row['market_id']] = deepcopy(row)
            merged['stations'] = [by_id[mid] for mid in sorted(by_id)]
            if 'coordinates' in data: merged['coordinates'] = deepcopy(data['coordinates'])
            # In particular, never replace fetched_at / source_updated_at of a
            # full dump with the time a single station was looked up.
            self.write(merged)

    def write(self, data):
        with _cache_lock(self.root, data.get('system_address')):
            self._write(data)

    def _write(self, data):
        validate(data, data.get('system_address'))
        payload = json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(',',':')).encode('utf-8')
        if len(payload) > MAX_CACHE: raise ValueError('Cache too large')
        self.root.mkdir(parents=True, exist_ok=True)
        name = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.root, prefix='.spansh-', suffix='.tmp', delete=False) as stream:
                name = stream.name
                stream.write(payload); stream.flush(); os.fsync(stream.fileno())
            os.replace(name, self.path(data['system_address']))
        finally:
            if name and os.path.exists(name): os.unlink(name)

    def attempt(self, address):
        """Bounded retry metadata, independent of successful station knowledge.

        Legacy local_date records never impose a calendar-day restriction.
        Memory is also the fallback when persisting a failure is unavailable.
        """
        if address in self._attempts:
            return self._attempts[address]
        try:
            path = self.root / 'attempts' / self.path(address).name
            record = json.loads(path.read_text(encoding='utf-8'))
            if (isinstance(record, dict) and record.get('system_address') == address
                    and record.get('kind') in ('error', 'server')
                    and (record.get('retry_not_before') is None
                         or timestamp(record['retry_not_before']))):
                return record
        except (OSError, ValueError, TypeError):
            pass
        return {}

    def server_wait(self, address):
        record = self.attempt(address)
        until = timestamp(record.get('retry_not_before'))
        return record if record.get('kind') == 'server' and until and self.now() < until else None

    def automatic_allowed(self, address):
        until = timestamp(self.attempt(address).get('retry_not_before'))
        return until is None or self.now() >= until

    def _store_attempt(self, address, record):
        self._attempts[address] = record
        name = None
        try:
            directory = self.root / 'attempts'
            target = directory / self.path(address).name
            if not record:
                target.unlink(missing_ok=True)
                return
            directory.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=directory, prefix='.attempt-', delete=False) as stream:
                name = stream.name
                stream.write(json.dumps(record).encode('utf-8'))
                stream.flush(); os.fsync(stream.fileno())
            os.replace(name, target)
        except OSError:
            logger.warning('Spansh retry metadata could not be persisted')
        finally:
            if name and os.path.exists(name): os.unlink(name)

    def _record_error(self, address, exc):
        kind, until = 'error', self.now() + ERROR_PAUSE
        if isinstance(exc, HTTPError):
            value = exc.headers.get('Retry-After') if exc.headers else None
            server_until = None
            if value:
                try:
                    seconds = int(value)
                    if seconds >= 0:
                        server_until = self.now() + timedelta(seconds=seconds)
                except (ValueError, OverflowError):
                    try:
                        server_until = parsedate_to_datetime(value)
                        if server_until.tzinfo is None: server_until = None
                    except (ValueError, TypeError, OverflowError):
                        pass
            if exc.code == 429 or server_until is not None:
                # No invented server deadline when Retry-After is absent/invalid.
                kind, until = 'server', server_until
        self._store_attempt(address, dict(system_address=address, kind=kind,
            retry_not_before=until.isoformat() if until else None))

    @profile.measure('spansh.request')
    def request(self, address, *, manual=False, automatic=False):
        old = self.read(address)
        if profile.ENABLED:
            profile.event('spansh.lookup', trigger='manual' if manual else 'automatic' if automatic else 'other',
                cache_age_seconds=max(0, (self.now()-timestamp(old['fetched_at'])).total_seconds()) if old else 0)
        if not manual and old and self.fresh(old):
            if profile.ENABLED: profile.event('spansh.result', outcome='cache_hit')
            return old, None
        if self.server_wait(address):
            if profile.ENABLED: profile.event('spansh.result', outcome='server_wait')
            return old, None
        if automatic and not self.automatic_allowed(address):
            if profile.ENABLED: profile.event('spansh.result', outcome='error_pause')
            return old, None
        try:
            data = normalize(
                profile.call('spansh.fetch', self.fetch, address) if profile.ENABLED else self.fetch(address),
                address, self.now())
            self.write(data)
        except Exception as exc:
            self._record_error(address, exc)
            if profile.ENABLED:
                profile.event('spansh.result', outcome='error',
                              http_status=exc.code if isinstance(exc, HTTPError) else 0)
            logger.warning('Spansh unavailable for system %s; using local knowledge', address, exc_info=True)
            return old, False
        self._store_attempt(address, {})
        if profile.ENABLED: profile.event('spansh.result', outcome='success', count=len(data['stations']))
        return data, True

    def visit(self, address):
        return self.request(address)[0]


def merge_stations(journal, cache, bodies, address):
    """Presentation-only merge. Inputs stay untouched; Journal always wins."""
    result = deepcopy(journal)
    if not cache: return result
    try: validate(cache, address)
    except ValueError: return result
    by_market = {s.get('market_id'):s for s in result if valid_id(s.get('market_id'))}
    body_ids = {b.get('body_id'):b for b in bodies if not is_belt_cluster(b)
                and (b.get('body_type') in ('Star','Planet') or b.get('star_type') or b.get('planet_class'))}
    for ext in cache['stations']:
        if is_carrier(ext.get('station_type')) or is_carrier(ext.get('source_type')): continue
        existing = by_market.get(ext['market_id'])
        if existing and is_carrier(existing.get('station_type')): continue
        parent = ext.get('parent_body_id')
        if parent not in body_ids: parent = None
        if parent is not None and ext.get('body_name') and ext['body_name'] != body_ids[parent].get('name'): parent = None
        provenance = {**deepcopy(ext), 'fetched_at':cache['fetched_at']}
        if cache.get('source_updated_at'): provenance['source_updated_at'] = cache['source_updated_at']
        if existing is None:
            row = dict(identity=f"market:{ext['market_id']}", system_address=address,
                       market_id=ext['market_id'], station_name=ext['station_name'], source='Spansh',
                       parent_body_id=parent, spansh=provenance)
            for key in ('station_type','is_planetary'):
                if key in ext: row[key] = ext[key]
            if parent is not None: row['body_name'] = body_ids[parent].get('name')
            result.append(row); by_market[ext['market_id']] = row
        else:
            existing['source'] = 'Journal + Spansh'
            existing['spansh'] = provenance
            conflicts = {}
            journal_parent = existing.get('parent_body_id')
            if journal_parent is not None and ext.get('parent_body_id') is not None and journal_parent != ext['parent_body_id']:
                conflicts['parent_body_id'] = ext['parent_body_id']
            elif journal_parent is None and parent is not None:
                existing['parent_body_id'] = parent
                existing['body_name'] = body_ids[parent].get('name')
                existing['parent_source'] = 'Spansh'
            if existing.get('station_type') and ext.get('station_type') and existing['station_type'] != ext['station_type']:
                conflicts['station_type'] = ext['station_type']
            elif not existing.get('station_type') and ext.get('station_type'):
                existing['station_type'] = ext['station_type']
            if conflicts:
                existing['spansh_conflicts'] = conflicts
                logger.debug('Journal/Spansh disagreement for MarketID %s: %s', ext['market_id'], conflicts)
    return sorted(result, key=lambda s:(str(s.get('station_name','')).casefold(),s['identity']))
