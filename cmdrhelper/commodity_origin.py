"""Read-only location evidence for catalog origins; never market availability."""
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
import sqlite3

from .commodity_master import all_commodities
from .spansh_cache import SystemCache


@dataclass(frozen=True)
class CommodityOrigin:
    market_id: int
    station_name: str | None = None
    system_name: str | None = None
    system_address: int | None = None
    coordinates: tuple | None = None
    distance_ly: float | None = None
    conflict: bool = False
    station_type: str = ""
    distance_to_arrival_ls: float | None = None


def _signature(path):
    try:
        s = Path(path).stat()
        return s.st_ino, s.st_size, s.st_mtime_ns
    except (OSError, TypeError):
        return None


def _connect(path):
    con = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True, timeout=.25)
    con.execute('PRAGMA query_only=ON')
    return con


class OriginResolver:
    """Worker-owned, small static origin index; cache files parsed only on change."""
    def __init__(self, database_path=None, market_path=None, spansh_folder=None):
        self.database_path, self.market_path, self.spansh_folder = database_path, market_path, spansh_folder
        self.ids = {c.origin_market_id for c in all_commodities() if c.origin_market_id is not None}
        self._db_rows = {}
        self._files = {}
        self._coordinates = {}
        self._stations = {}

    def _database_rows(self, path, market=False):
        if path is None:
            return []
        signature = (_signature(path), _signature(str(path) + '-wal'))
        old = self._db_rows.get((str(path), market))
        if old and old[0] == signature:
            return old[1]
        rows = []
        marks = ','.join('?' for _ in self.ids)
        try:
            with closing(_connect(path)) as con:
                if market:
                    rows = [(int.from_bytes(mid, 'big'), station, system,
                             int.from_bytes(address, 'big') if address else None)
                            for mid, station, system, address in con.execute(
                        'SELECT m.market_id,m.station_name,m.system_name,m.system_address '
                        'FROM current_markets c JOIN market_observations m USING(observation_id) '
                        f'WHERE c.market_id IN ({marks})', [i.to_bytes(8, 'big') for i in self.ids])]
                else:
                    # Persisted station evidence only, never journals or migrations.
                    for sql, args in [(
                        'SELECT o.market_id,o.station_name,s.name,o.system_address '
                        'FROM station_observations o JOIN systems s USING(system_address) '
                        f'WHERE o.market_id IN ({marks})', list(self.ids)), (
                        'SELECT market_id,station_name,system_name,system_address '
                        f'FROM station_pad_evidence WHERE market_id IN ({marks})',
                        [i.to_bytes(8, 'big') for i in self.ids])]:
                        try:
                            for mid, station, system, address in con.execute(sql, args):
                                rows.append((int.from_bytes(mid, 'big') if isinstance(mid, bytes) else mid,
                                             station, system, int.from_bytes(address, 'big')
                                             if isinstance(address, bytes) else address))
                        except sqlite3.Error:
                            continue
        except (OSError, sqlite3.Error, ValueError):
            return []
        self._db_rows[(str(path), market)] = (signature, rows)
        return rows

    def locations(self):
        rows = self._database_rows(self.database_path) + self._database_rows(self.market_path, True)
        if self.spansh_folder is not None:
            cache = SystemCache(root=self.spansh_folder)
            paths = set(Path(self.spansh_folder).glob('*.json'))
            for path in paths:
                signature = _signature(path)
                old = self._files.get(path)
                if old and old[0] == signature:
                    rows.extend(old[1])
                    continue
                entries = []
                station_metadata = {}
                coordinates = None
                try:
                    data = cache.read(int(path.stem))
                    if data:
                        station_metadata = {r['market_id']: r for r in data['stations']
                                            if r['market_id'] in self.ids}
                        coordinates = data.get('coordinates')
                        entries = [(r['market_id'], r['station_name'], data['system_name'], data['system_address'])
                                   for r in data['stations'] if r['market_id'] in self.ids]
                    if signature != _signature(path):
                        continue
                    self._stations[path] = station_metadata
                    self._files[path] = (signature, entries)
                    self._coordinates[path] = coordinates
                    rows.extend(entries)
                except (OSError, ValueError, TypeError):
                    continue
            self._files = {p: row for p, row in self._files.items() if p in paths}
            self._coordinates = {p: row for p, row in self._coordinates.items() if p in paths}
            self._stations = {p: row for p, row in self._stations.items() if p in paths}
        grouped = {mid: [] for mid in self.ids}
        for mid, station, system, address in rows:
            if mid in grouped and isinstance(station, str) and station.strip() and isinstance(system, str) and system.strip():
                grouped[mid].append((station, system, address))
        result = {}
        for mid, evidence in grouped.items():
            names = {(s.casefold(), y.casefold()) for s, y, _ in evidence}
            addresses = {a for _, _, a in evidence if a is not None}
            conflict = len(names) > 1 or len(addresses) > 1
            if evidence and not conflict:
                station, system, _ = evidence[0]
                address = next(iter(addresses), None)
                metadata = next((v.get(mid, {}) for p, v in self._stations.items()
                                 if p in self._files and p.stem == str(address)), {})
                result[mid] = CommodityOrigin(mid, station, system, address,
                    station_type=metadata.get('station_type', ''),
                    distance_to_arrival_ls=metadata.get('distance_ls'))
            else:
                result[mid] = CommodityOrigin(mid, conflict=conflict)
        return result

    def resolve_many(self, reference_name='', reference_address=None):
        """One location pass and one coordinate connection for the entire catalogue."""
        from dataclasses import replace
        from .material_traders import Coordinates
        from .ui.favorites_view import stored_coordinates
        origins = self.locations()
        con = None
        try:
            if self.database_path is not None:
                try:
                    con = _connect(self.database_path)
                except (OSError, sqlite3.Error, ValueError):
                    pass
            def stored(address, name):
                try:
                    return stored_coordinates(con, address, name) if con else None
                except (sqlite3.Error, ValueError):
                    return None
            reference = stored(reference_address, reference_name)
            def cached(address):
                coords = next((v for p, v in self._coordinates.items()
                               if p.stem == str(address) and v), None)
                return Coordinates(**coords) if coords else None
            reference = reference or cached(reference_address)
            for mid, origin in origins.items():
                if not origin.system_name:
                    continue
                target = stored(origin.system_address, origin.system_name) or cached(origin.system_address)
                distance = reference.distance_to(target) if reference and target else None
                origins[mid] = replace(origin, coordinates=(target.x, target.y, target.z) if target else None,
                                       distance_ly=distance)
        finally:
            if con is not None:
                con.close()
        return origins

    def resolve(self, market_id, reference_name='', reference_address=None):
        from dataclasses import replace
        origin = self.locations().get(market_id, CommodityOrigin(market_id))
        if origin.system_name and self.database_path is not None:
            from .ui.favorites_view import stored_coordinates
            try:
                with closing(_connect(self.database_path)) as con:
                    target = stored_coordinates(con, origin.system_address, origin.system_name)
                    reference = stored_coordinates(con, reference_address, reference_name)
                    if target:
                        origin = replace(origin, coordinates=(target.x, target.y, target.z),
                                         distance_ly=reference.distance_to(target) if reference else None)
            except (OSError, sqlite3.Error, ValueError):
                pass
        if origin.station_name and origin.system_address is not None:
            from .material_traders import Coordinates
            coords = next((v for p, v in self._coordinates.items()
                           if p.stem == str(origin.system_address)), None)
            if coords and origin.coordinates is None:
                target = Coordinates(**coords)
                distance = None
                if self.database_path is not None:
                    try:
                        with closing(_connect(self.database_path)) as con:
                            reference = stored_coordinates(con, reference_address, reference_name)
                            if reference: distance = reference.distance_to(target)
                    except (OSError, sqlite3.Error, ValueError):
                        pass
                origin = replace(origin, coordinates=(target.x, target.y, target.z), distance_ly=distance)
        return origin
