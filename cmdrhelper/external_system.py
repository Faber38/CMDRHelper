"""Read-only, transient system search. No AppState, migrations or cache writes."""
from copy import deepcopy
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
from urllib.request import Request

from .body_classes import canonical_body_classes
from .body_parents import parent_metadata
from .spansh_cache import fetch_system, normalize, merge_stations, valid_id, timestamp
from .spansh_transport import request_json, TransportError
from .route_planner.system_resolution import resolve_system, SpanshError
from .stations import load_stations
from .version import __version__


def numeric(value):
    return type(value) in (int, float) and math.isfinite(value)


def text(value):
    return isinstance(value, str) and 0 < len(value.strip()) <= 1024


def name_key(value):
    return str(value).strip().casefold()


def adapt_spansh(raw, address):
    station_cache = normalize(raw, address)  # pure validation/normalization, no persistence
    system = raw['system']
    rows = system.get('bodies')
    if not isinstance(rows, list) or len(rows) > 5000:
        raise ValueError('Invalid bodies')
    bodies, seen, issues = [], set(), []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Invalid body')
        bid = row.get('bodyId')
        if type(bid) is not int or not 0 <= bid < 512 or bid in seen:
            raise ValueError('Invalid or duplicate BodyID')
        if not text(row.get('name')) or row.get('type') not in ('Star', 'Planet', 'Barycentre', 'Belt Cluster'):
            raise ValueError('Invalid body identity/type')
        seen.add(bid)
        body = dict(body_id=bid, name=row['name'], body_type=row['type'], source='Spansh')
        if 'id64' in row:
            if not valid_id(row['id64']):
                raise ValueError('Invalid body id64')
            body['body_id64'] = row['id64']
        if text(row.get('subType')):
            body['star_type' if row['type'] == 'Star' else 'planet_class'] = row['subType']
        for src, dst in [('isLandable', 'landable'), ('mainStar', 'main_star')]:
            if type(row.get(src)) is bool:
                body[dst] = row[src]
        for src, dst in [('gravity', 'gravity_g'), ('surfaceTemperature', 'surface_temperature'),
                         ('surfacePressure', 'surface_pressure'), ('distanceToArrival', 'distance_ls'),
                         ('earthMasses', 'mass_em'), ('solarMasses', 'stellar_mass'),
                         ('semiMajorAxis', 'semi_major_axis')]:
            if numeric(row.get(src)) and row[src] >= 0:
                body[dst] = row[src]
        for src, dst in [('atmosphereType', 'atmosphere'), ('volcanismType', 'volcanism')]:
            if text(row.get(src)):
                body[dst] = row[src]
        if isinstance(row.get('materials'), dict):
            materials = row['materials']
            if materials and all(text(k) and numeric(v) and 0 <= v <= 100 for k, v in materials.items()):
                body['materials'] = deepcopy(materials)
                # Do not claim a percentage unit without a verified Spansh unit contract.
                body['material_unit'] = 'unverified'
        if 'parents' in row:
            parents = parent_metadata(row['parents'], 'EDSM')  # shared strict syntax validator only
            if parents:
                body.update(parent_path=parents['parent_path'], parent_source='Spansh')
            else:
                issues.append(bid)
        signals = row.get('signals')
        if isinstance(signals, dict) and isinstance(signals.get('signals'), dict):
            counts = signals['signals']
            body['signal_counts'] = {k:v for k,v in counts.items() if text(k) and type(v) is int and v >= 0}
            if timestamp(signals.get('updateTime')):
                body['signals_updated_at'] = signals['updateTime']
            for src, dst in [('$SAA_SignalType_Geological;', 'geological_signals'),
                             ('$PlanetaryMiningLocation_Name;', 'planetary_mining_signals')]:
                if type(counts.get(src)) is int and counts[src] >= 0:
                    body[dst] = counts[src]
        body['updated_at'] = row.get('updateTime') if timestamp(row.get('updateTime')) else None
        bodies.append(canonical_body_classes(body))
    count = system.get('bodyCount')
    count = count if type(count) is int and count >= 0 else None
    return dict(system=system['name'], system_address=address, bodies=bodies,
                body_count=count, coordinates=station_cache.get('coordinates'),
                station_cache=station_cache, partial=bool(issues) or count is None or count != len(bodies),
                fetched_at=station_cache['fetched_at'], source_updated_at=station_cache.get('source_updated_at'))


@contextmanager
def open_local(path):
    con = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    try:
        con.execute('PRAGMA query_only=ON')
        con.execute('BEGIN')
        yield con
    finally:
        con.close()


def local_identity(path, name):
    if not path or not Path(path).is_file():
        return None
    with open_local(path) as con:
        rows = con.execute('SELECT system_address,name FROM systems WHERE name=? COLLATE NOCASE', (name.strip(),)).fetchall()
        if len(rows) == 1 and valid_id(rows[0]['system_address']):
            return rows[0]['system_address']
    return None


def local_bodies(path, address):
    """Global physical facts; personal evidence stays attributed to its commander."""
    if not path or not Path(path).is_file():
        return []
    with open_local(path) as con:
        rows = con.execute('SELECT * FROM bodies WHERE system_address=? ORDER BY body_id', (address,)).fetchall()
        result = []
        for row in rows:
            body = {k: v for k, v in dict(row).items() if v is not None and v != ''}
            if not text(body.get('name')):
                body['name'] = ''  # a placeholder is not a named/typed physical observation
            evidence = [dict(r) for r in con.execute('''SELECT cb.commander_id,c.current_name,
                cb.scanned,cb.self_mapped,cb.first_seen,cb.last_seen,cb.mapped_at,
                cb.geological_signals_seen FROM commander_bodies cb JOIN commanders c ON c.id=cb.commander_id
                WHERE cb.system_address=? AND cb.body_id=? ORDER BY cb.commander_id''', (address, row['body_id']))]
            # Defaults on placeholders are not negative physical observations.
            if not body.get('body_type') and not body.get('planet_class') and not body.get('star_type'):
                body = dict(body_id=row['body_id'], name=body['name'])
                if row['planetary_mining_signals'] is not None:
                    body['planetary_mining_signals'] = row['planetary_mining_signals']
            else:
                for key in ('landable', 'terraformable'):
                    if key in body:
                        body[key] = bool(body[key])
            body.pop('geological_signals', None)
            geo = [e['geological_signals_seen'] for e in evidence if e['geological_signals_seen'] > 0]
            if geo:
                body['geological_signals'] = max(geo)
            body['observations'] = evidence
            body['geology'] = [dict(r) for r in con.execute('''SELECT g.name,g.raw_name,g.source,
                g.first_seen,g.last_seen,g.commander_id,c.current_name FROM geology g
                JOIN commanders c ON c.id=g.commander_id WHERE g.system_address=? AND g.body_id=?''',
                (address,row['body_id']))]
            body['materials'] = dict(con.execute('SELECT material_name,percentage FROM materials WHERE system_address=? AND body_id=?', (address,row['body_id'])).fetchall())
            if body['materials']:
                body['material_unit'] = 'percent'
            ancestry = con.execute('SELECT value FROM app_meta WHERE key=?', (f'body_parents.v1:{address}:{row["body_id"]}',)).fetchone()
            if ancestry:
                try:
                    stored = json.loads(ancestry[0])
                    parents = parent_metadata(stored.get('parent_path'), stored.get('parent_source'))
                    if parents:
                        body.update(parents)
                except (ValueError, TypeError):
                    pass
            body['mining_findings'] = []
            for table in ('surface_mining_commodities', 'surface_mining_materials'):
                body['mining_findings'].extend(dict(r, kind=table) for r in con.execute(f'''SELECT c.current_name,
                    m.commander_id,m.display_name,m.frontier_name,m.quantity FROM {table} m
                    JOIN commanders c ON c.id=m.commander_id WHERE system_address=? AND body_id=?''', (address,row['body_id'])))
            body['source'] = 'Local'
            body['updated_at'] = max((e['last_seen'] for e in evidence), default=None)
            result.append(canonical_body_classes(body))
    return result


def edsm_snapshot(name, root=None):
    """Read without creating the legacy cache directory. Never fetch EDSM."""
    if root is None:
        base = Path(os.environ.get('LOCALAPPDATA', str(Path.home()/'AppData'/'Local'))) if os.name == 'nt' else Path(os.environ.get('XDG_CACHE_HOME', str(Path.home()/'.cache')))
        root = base/'CMDRHelper'/'edsm'
    path = Path(root)/(hashlib.sha256(name.strip().encode('utf-8')).hexdigest()[:24]+'.json')
    try:
        if path.stat().st_size > 16*1024*1024:
            return None
        payload = json.loads(path.read_text(encoding='utf-8'))
        data = payload['data']
        address = data.get('system_address', data.get('id64'))
        if (not valid_id(address) or name_key(payload.get('system')) != name_key(name)
                or name_key(data.get('system')) != name_key(name) or not isinstance(data.get('bodies'), list)):
            return None
        bodies, seen = [], set()
        allowed = {'body_id','name','body_type','star_type','planet_class','gravity_g','distance_ls',
                   'mass_em','stellar_mass','landable','atmosphere','volcanism','materials'}
        for row in data['bodies']:
            if (not isinstance(row, dict) or type(row.get('body_id')) is not int
                    or not 0 <= row['body_id'] < 512 or row['body_id'] in seen or not text(row.get('name'))):
                return None
            seen.add(row['body_id'])
            b = {k: deepcopy(v) for k,v in row.items() if k in allowed and v is not None}
            for key in ('gravity_g','distance_ls','mass_em','stellar_mass'):
                if key in b and (not numeric(b[key]) or b[key] < 0):
                    b.pop(key)
            if type(b.get('landable')) is not bool:
                b.pop('landable', None)
            if not isinstance(b.get('materials'), dict) or not all(text(k) and numeric(v) and 0 <= v <= 100 for k,v in b['materials'].items()):
                b.pop('materials',None)
            if b.get('materials'):
                b['material_unit'] = 'percent'
            for key in ('body_type','star_type','planet_class','atmosphere','volcanism'):
                if key in b and not text(b[key]):
                    b.pop(key)
            parents = parent_metadata(row.get('parent_path'), row.get('parent_source'))
            if parents:
                b.update(parents)
            b.update(source='EDSM', updated_at=None, fetched_at=payload.get('fetched_at'))
            bodies.append(canonical_body_classes(b))
        return dict(system=name, system_address=address, bodies=bodies)
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None


def combine_bodies(*sources):
    """Priority is explicit (local, Spansh, EDSM); preserve every source snapshot."""
    result = {}
    metadata = {'source','updated_at','fetched_at','observations','mining_findings','material_unit'}
    for bodies in sources:
        for raw in bodies:
            b = deepcopy(raw)
            bid = b['body_id']
            current = result.setdefault(bid, {'body_id':bid,'provenance':{},'conflicts':{},'source_records':[]})
            current['source_records'].append(b)
            source = b.get('source','')
            if current.get('name') and b.get('name') and name_key(current['name']) != name_key(b['name']):
                current['conflicts'].setdefault('name', []).append(dict(source=source,value=b['name'],updated_at=b.get('updated_at')))
                continue  # conflicting identity: never fill from this record
            hierarchy = ('parent_path','parent_id','parent_star_id','parent_source')
            existing_hierarchy = any(current.get(k) is not None for k in hierarchy[:3])
            incoming_path = parent_metadata(b.get('parent_path'), 'EDSM')
            if (existing_hierarchy and not current.get('parent_path') and incoming_path
                    and all(current.get(k) is None or current[k] == incoming_path.get(k)
                            for k in ('parent_id', 'parent_star_id'))):
                current['parent_path'] = incoming_path['parent_path']
                current['parent_source'] = source
                current['provenance']['parent_path'] = source
            chosen_path = parent_metadata(current.get('parent_path'), 'EDSM')
            for key,value in b.items():
                if key in metadata:
                    continue
                if value is None or value == '' or value == {} or value == []:
                    continue
                if key == 'materials':
                    target = current.setdefault('materials', {})
                    units = current.setdefault('material_units', {})
                    origins = current.setdefault('material_sources', {})
                    for material, amount in value.items():
                        if material not in target:
                            target[material] = amount
                            units[material] = b.get('material_unit', 'unverified')
                            origins[material] = source
                        elif target[material] != amount:
                            current['conflicts'].setdefault('materials.' + material, []).append(
                                dict(source=source,value=amount,unit=b.get('material_unit','unverified'),updated_at=b.get('updated_at')))
                    current['provenance'].setdefault('materials', source)
                    continue
                if key in hierarchy and existing_hierarchy:
                    if key in ('parent_id', 'parent_star_id') and current.get(key) is None and chosen_path.get(key) == value:
                        current[key] = value
                        current['provenance'][key] = source
                        continue
                    if key != 'parent_source' and current.get(key) != value:
                        current['conflicts'].setdefault(key, []).append(dict(source=source,value=value,updated_at=b.get('updated_at')))
                    continue
                if key not in current or current[key] is None or current[key] == '':
                    current[key] = value
                    current['provenance'][key] = source
                elif current[key] != value:
                    current['conflicts'].setdefault(key, []).append(dict(source=source,value=value,updated_at=b.get('updated_at')))
            for key in ('observations','mining_findings'):
                if key in b:
                    current[key] = b[key]
    for body in result.values():
        body['external_view'] = True
        # Personal proofs are ONLY in attributed observations, never renderer flags.
        body['journal_scanned'] = False
        body['source'] = ' / '.join(dict.fromkeys(r['source'] for r in body['source_records']))
    return sorted(result.values(), key=lambda b:b['body_id'])


def search_request(url):
    request = Request(url, headers={'User-Agent':f'CMDRHelper/{__version__}', 'Accept':'application/json'})
    try:
        data = request_json(request, timeout=15)
    except TransportError as exc:
        raise SpanshError(exc.code) from exc
    if not isinstance(data,dict):
        raise SpanshError('invalid_response')
    return data


def search_system(name, database_path=None, *, request=search_request, fetch=fetch_system, edsm_root=None):
    name = name.strip()
    if not name:
        raise SpanshError('system_unknown')
    local_address = local_identity(database_path, name)
    edsm = edsm_snapshot(name, edsm_root)
    known = local_address or (edsm['system_address'] if edsm else None)
    external, error = None, None
    try:
        address = resolve_system(request, name, known, 'system_unknown')
        external = adapt_spansh(fetch(address), address)
        if name_key(external['system']) != name_key(name):
            raise ValueError('System name mismatch')
    except Exception as exc:
        external = None
        error = getattr(exc, 'code', 'invalid_response' if isinstance(exc, ValueError) else 'network_error')
        if known is None:
            raise SpanshError(error) from exc
        address = known
    local = local_bodies(database_path, address)
    edsm_bodies = edsm['bodies'] if edsm and edsm['system_address'] == address else []
    bodies = combine_bodies(local, external['bodies'] if external else [], edsm_bodies)
    if not external and not bodies and local_address is None and edsm is None:
        raise SpanshError(error or 'system_unknown')
    journal_stations = {}
    local_system = None
    if database_path and Path(database_path).is_file():
        with open_local(database_path) as con:
            row = con.execute('SELECT name,body_count,x,y,z FROM systems WHERE system_address=?', (address,)).fetchone()
            local_system = dict(row) if row else None
            ids = [r[0] for r in con.execute('SELECT id FROM commanders')]
            for cid in ids or [None]:
                for station in load_stations(con,address,bodies,cid):
                    journal_stations[station['identity']] = station
    stations = merge_stations(list(journal_stations.values()), external['station_cache'] if external else None, bodies, address)
    model = {k:v for k,v in (external or {}).items() if k != 'station_cache'}
    if not external and local_system:
        model['body_count'] = local_system['body_count']
        model['coordinates'] = {k:local_system[k] for k in ('x','y','z')}
    model.update(system=external['system'] if external else name, system_address=address, bodies=bodies,
                 stations=stations, warning=error, edsm_used=bool(edsm_bodies),
                 partial=not external or external['partial'] or external['body_count'] != len(bodies),
                 sources=' / '.join(s for s, present in [('Local',local or journal_stations or local_system),('Spansh',external),('EDSM',edsm_bodies)] if present))
    return model
