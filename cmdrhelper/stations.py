"""Conservative facility facts. Station BodyID is never a celestial parent ID."""
import hashlib
import json
from collections import defaultdict

from cmdrhelper.belt_projection import is_belt_cluster

EVENTS = {'Docked', 'Location', 'CarrierJump', 'CarrierLocation', 'ApproachSettlement'}
FIELDS = ('identity', 'event_type', 'system_address', 'station_name', 'station_type',
          'market_id', 'body_id', 'body_name', 'parent_body_id', 'is_planetary',
          'latitude', 'longitude', 'last_seen', 'source')
SURFACE_TYPES = {'SurfaceStation', 'CraterOutpost', 'CraterPort', 'OnFootSettlement'}
ORBITAL_TYPES = {'Coriolis', 'Orbis', 'Ocellus', 'Dodec', 'Bernal', 'AsteroidBase'}


def observation(event):
    kind = event.get('event')
    address = event.get('SystemAddress')
    if kind not in EVENTS or type(address) is not int:
        return None
    market = event.get('CarrierID') if kind == 'CarrierLocation' else event.get('MarketID')
    market = market if type(market) is int and market > 0 else None
    name = event.get('Name') if kind == 'ApproachSettlement' else event.get('StationName')
    if kind != 'CarrierLocation' and not name:
        return None
    if kind == 'Location' and not event.get('Docked'):
        return None
    station_type = 'FleetCarrier' if kind == 'CarrierLocation' else event.get('StationType')
    body_id = event.get('BodyID')
    body_id = body_id if type(body_id) is int and body_id >= 0 else None
    body_name = event.get('BodyName') or event.get('Body')
    parent = body_id if (kind in ('ApproachSettlement', 'CarrierLocation')
                        or event.get('BodyType') in ('Planet', 'Star')) else None
    planetary = (True if kind == 'ApproachSettlement' or station_type in SURFACE_TYPES
                 else False if station_type in ORBITAL_TYPES | {'Outpost', 'FleetCarrier', 'MegaShip'}
                 else None)
    # No invented settlement subtype: ApproachSettlement also describes surface ports.
    latitude, longitude = event.get('Latitude'), event.get('Longitude')
    if market is not None:
        identity = f'market:{market}'
    elif kind == 'ApproachSettlement' and body_id is not None and all(
            type(v) in (int, float) for v in (latitude, longitude)):
        identity = 'surface:' + hashlib.sha256(json.dumps(
            [address, body_id, latitude, longitude, name], ensure_ascii=False).encode()).hexdigest()
    else:
        return None  # FSS names and station proximity alone cannot establish identity.
    return dict(zip(FIELDS, (identity, kind, address, name, station_type, market,
                            body_id, body_name, parent, planetary, latitude, longitude,
                            str(event.get('timestamp') or ''), 'Journal')))


def store_observation(con, row):
    if row is None or not row['last_seen']:
        return
    columns = ','.join(FIELDS)
    updates = ','.join(f'{key}=excluded.{key}' for key in FIELDS[2:])
    con.execute(f'''INSERT INTO station_observations({columns})
        VALUES({','.join('?' for _ in FIELDS)})
        ON CONFLICT(identity,event_type) DO UPDATE SET {updates}
        WHERE excluded.last_seen >= station_observations.last_seen''',
        tuple(row[key] for key in FIELDS))


def project_stations(rows, address, bodies, owned_carrier=None):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['identity']].append(row)
    result = []
    body_by_id = {b.get('body_id'): b for b in bodies}
    for identity, facts in grouped.items():
        station = {}
        for fact in sorted(facts, key=lambda r: (r['last_seen'], r['event_type'])):
            if station.get('system_address') != fact['system_address']:
                station = {}  # Movement invalidates every previous body/coordinate fact.
            if fact['event_type'] in ('CarrierLocation', 'CarrierJump'):
                for key in ('parent_body_id', 'body_name', 'body_id', 'latitude', 'longitude'):
                    station.pop(key, None)
            station.update({k: v for k, v in fact.items() if v is not None})
        if station.get('system_address') != address:
            continue
        if station.get('station_type') == 'FleetCarrier':
            if not owned_carrier or station.get('market_id') != owned_carrier.get('carrier_id'):
                continue
            if (owned_carrier.get('last_updated', '') >= station['last_seen']
                    and owned_carrier.get('system_address') != address):
                continue
            station['station_name'] = owned_carrier.get('carrier_name') or station.get('station_name')
        parent = station.get('parent_body_id')
        body = body_by_id.get(parent)
        # Require the actual system model; never resolve by short/partial names.
        if body is None or is_belt_cluster(body) or (body.get('body_type') not in ('Star', 'Planet')
                            and not body.get('star_type') and not body.get('planet_class')):
            station['parent_body_id'] = None
        elif station.get('body_name') and station['body_name'] != body.get('name'):
            station['parent_body_id'] = None
        else:
            station['body_name'] = body.get('name')
        station.setdefault('station_name', str(station.get('market_id') or identity))
        result.append(station)
    return sorted(result, key=lambda s: (str(s.get('station_name') or '').casefold(), s['identity']))


def load_stations(con, address, bodies, commander_id=None):
    if address is None:
        return []
    # All facts for candidates, including newer facts in OTHER systems (carriers).
    cursor = con.execute('''SELECT * FROM station_observations WHERE identity IN
        (SELECT identity FROM station_observations WHERE system_address=?)''', (address,))
    rows = [dict(zip((d[0] for d in cursor.description), r)) for r in cursor.fetchall()]
    carrier_row = con.execute('''SELECT carrier_id,carrier_name,system_address,last_updated
        FROM commander_carriers WHERE commander_id=?''', (commander_id,)).fetchone()
    carrier = dict(zip(('carrier_id', 'carrier_name', 'system_address', 'last_updated'), carrier_row)) if carrier_row else None
    return project_stations(rows, address, bodies, carrier)


def plan_backfill(con, commander_id):
    from cmdrhelper.backfill_support import committed_journals
    latest = {}
    for _, events in committed_journals(con, commander_id, relevant_events=EVENTS):
        for event in events:
            row = observation(event)
            if row and row['last_seen']:
                key = row['identity'], row['event_type']
                if key not in latest or row['last_seen'] >= latest[key]['last_seen']:
                    latest[key] = row
    return {'stations': list(latest.values())}
