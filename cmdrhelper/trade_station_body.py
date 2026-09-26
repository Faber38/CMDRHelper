"""Read-only body labels for trade bookmarks, using existing local station facts."""
from cmdrhelper.spansh_cache import TYPES, validate
from cmdrhelper.stations import ORBITAL_TYPES, load_stations


def known_station_body(state, offer):
    """Resolve an explicit parent only; never infer it from station names/BodyID."""
    if state is None or offer.is_fleet_carrier or TYPES.get(offer.station_type, offer.station_type) in (
            ORBITAL_TYPES | {'Outpost', 'FleetCarrier', 'MegaShip'}):
        return ''
    address = offer.system_id64
    bodies, stations = [], []
    database = getattr(state, 'database', None)
    if database is not None:
        with database._connect() as con:
            if address is None:
                matches = con.execute('SELECT system_address FROM systems WHERE name=?',
                                      (offer.system_name,)).fetchall()
                if len(matches) != 1:
                    return ''
                address = matches[0][0]
            cursor = con.execute('''SELECT body_id,name,short_name,body_type,star_type,planet_class
                                    FROM bodies WHERE system_address=?''', (address,))
            bodies = [dict(zip((d[0] for d in cursor.description), row)) for row in cursor.fetchall()]
            stations = load_stations(con, address, bodies, getattr(state, 'commander_id', None))
    elif address is not None and address == getattr(state, 'system_address', None):
        bodies = getattr(state, 'system_bodies', [])
        stations = getattr(state, 'system_stations', [])
    if address is None:
        return ''
    candidates = [s for s in stations if s.get('market_id') == offer.market_id
                  and s.get('station_name') == offer.station_name]
    spansh = getattr(state, 'spansh_stations', None)
    # cached() reads memory/disk only; neither request() nor refresh_system() is used.
    cached = spansh.cached(address) if spansh is not None else None
    if cached:
        try:
            validate(cached, address)
        except ValueError:
            cached = None
        if cached and cached['system_name'] == offer.system_name:
            candidates.extend(s for s in cached['stations'] if s['market_id'] == offer.market_id
                              and s['station_name'] == offer.station_name)
    names, parents = set(), set()
    for station in candidates:
        if station.get('is_planetary') in (False, 0):
            return ''
        if station.get('is_planetary') not in (True, 1):
            continue
        parent, name = station.get('parent_body_id'), station.get('body_name')
        if parent is None or not isinstance(name, str) or not name.strip():
            continue
        # Reject conflicting parent facts, including a cache contradicting local bodies.
        body = next((b for b in bodies if b.get('body_id') == parent), None)
        if body and body.get('name') != name:
            return ''
        names.add(name)
        parents.add(parent)
    if len(names) != 1 or len(parents) != 1:
        return ''
    name = names.pop()
    body = next((b for b in bodies if b.get('name') == name
                 and b.get('body_id') in parents), None)
    if body and body.get('short_name'):
        name = body['short_name']
    # Same exact system-prefix abbreviation as the Stations view's parent_label().
    prefix = offer.system_name + ' '
    return name[len(prefix):] if name.startswith(prefix) else name
