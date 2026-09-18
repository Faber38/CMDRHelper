"""Bounded public system knowledge in JSON; this module never opens SQLite."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import logging
import math
import os
from pathlib import Path
import tempfile
from urllib.request import Request, urlopen
from cmdrhelper.belt_projection import is_belt_cluster
from cmdrhelper.version import __version__

logger = logging.getLogger(__name__)
TTL = timedelta(days=7)
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
    if not valid_id(address) or not isinstance(response, dict):
        raise ValueError('Invalid system address/response')
    system = response.get('system')
    if not isinstance(system, dict) or type(system.get('id64')) is not int or system['id64'] != address:
        raise ValueError('Spansh system identity mismatch')
    if not isinstance(system.get('name'), str) or not system['name']:
        raise ValueError('Missing system name')
    stations = []
    def add(raw, parent=None):
        if (not isinstance(raw, dict) or is_carrier(raw.get('type'))
                or (isinstance(raw.get('services'), list) and any(
                    v in ('Fleet Carrier Fuel', 'Fleet Carrier Management') for v in raw['services']))):
            return
        mid = raw.get('id')
        if not valid_id(mid) or not isinstance(raw.get('name'), str) or not raw['name']:
            return
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
    raw_stations = system.get('stations', [])
    bodies = system.get('bodies', [])
    if not isinstance(raw_stations, list) or not isinstance(bodies, list):
        raise ValueError('Invalid station/body list')
    for raw in raw_stations: add(raw)
    for body in bodies:
        if not isinstance(body, dict) or not isinstance(body.get('stations', []), list):
            raise ValueError('Invalid body stations')
        for raw in body.get('stations', []): add(raw, body)
    # Exact repeated records are harmless; contradictory same-ID records are
    # ambiguous and are omitted rather than choosing an arbitrary parent.
    unique, ambiguous = {}, set()
    for row in stations:
        mid = row['market_id']
        if mid in unique and unique[mid] != row: ambiguous.add(mid)
        unique[mid] = row
    result = {'schema_version': 1, 'source': 'spansh', 'system_address': address,
              'system_name': system['name'], 'fetched_at': (now or utcnow()).isoformat(),
              'stations': [row for mid,row in sorted(unique.items()) if mid not in ambiguous]}
    if timestamp(system.get('date')): result['source_updated_at'] = system['date']
    validate(result, address)
    return result


def validate(data, address):
    if not valid_id(address) or not isinstance(data, dict): raise ValueError('Invalid cache')
    required = {'schema_version','source','system_address','system_name','fetched_at','stations'}
    if not required <= data.keys() or data.keys() - (required | {'source_updated_at'}): raise ValueError('Invalid cache fields')
    if type(data['schema_version']) is not int or data['schema_version'] != 1 or data['source'] != 'spansh': raise ValueError('Invalid cache version/source')
    if type(data['system_address']) is not int or data['system_address'] != address: raise ValueError('Cache system mismatch')
    if not isinstance(data['system_name'], str) or not data['system_name'] or not timestamp(data['fetched_at']): raise ValueError('Invalid cache metadata')
    if 'source_updated_at' in data and not timestamp(data['source_updated_at']): raise ValueError('Invalid source date')
    if not isinstance(data['stations'], list) or len(data['stations']) > 5000: raise ValueError('Invalid stations')
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
        age = self.now() - timestamp(data['fetched_at'])
        return timedelta(0) <= age < TTL

    def fetched_today(self, data):
        """Successful persisted fetch on the current local calendar day."""
        return bool(data and timestamp(data['fetched_at']).astimezone().date()
                    == self.now().astimezone().date())

    def write(self, data):
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

    def automatic_allowed(self, address):
        """Attempts, including failures, survive restarts; local calendar day."""
        path = self.root / 'attempts' / self.path(address).name
        try:
            record = json.loads(path.read_text(encoding='utf-8'))
            return not (record.get('system_address') == address
                        and record.get('local_date') == self.now().astimezone().date().isoformat())
        except FileNotFoundError:
            return True
        except (OSError, ValueError, AttributeError):
            # An unreadable protection record must not cause a retry loop.
            return False

    def _mark_automatic(self, address):
        directory = self.root / 'attempts'
        directory.mkdir(parents=True, exist_ok=True)
        record = {'system_address': address, 'local_date': self.now().astimezone().date().isoformat()}
        name = None
        try:
            with tempfile.NamedTemporaryFile(dir=directory, prefix='.attempt-', delete=False) as stream:
                name = stream.name
                stream.write(json.dumps(record).encode('utf-8'))
                stream.flush(); os.fsync(stream.fileno())
            os.replace(name, directory / self.path(address).name)
        finally:
            if name and os.path.exists(name): os.unlink(name)

    def request(self, address, *, manual=False, automatic=False):
        old = self.read(address)
        if manual and self.fetched_today(old): return old, None
        if not manual and old and self.fresh(old): return old, None
        try:
            if automatic:
                if not self.automatic_allowed(address): return old, None
                # Persist BEFORE sending, so failures and interrupted requests count.
                self._mark_automatic(address)
            data = normalize(self.fetch(address), address, self.now())
            self.write(data)
            return data, True
        except Exception:
            logger.warning('Spansh unavailable for system %s; using local knowledge', address, exc_info=True)
            return old, False

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
