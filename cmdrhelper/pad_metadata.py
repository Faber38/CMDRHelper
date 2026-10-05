"""Persisted local pad evidence with a process-local Spansh projection cache."""
import json
import logging
import sqlite3
from pathlib import Path
from threading import Lock

from .market_data import PadSize
from .observed_market_cache import timestamp


def station_pad_counts(station):
    """Concrete resolved counts, or the station's already cached Spansh evidence."""
    pads = station.get('pad_counts', (station.get('spansh') or {}).get('landing_pads'))
    if not isinstance(pads, dict) or any(
            type(pads.get(k)) is not int or pads[k] < 0 for k in ('small', 'medium', 'large')):
        return None
    return {k: pads[k] for k in ('large', 'medium', 'small')}


def resolve_station_pad_counts(stations, system_name, system_address,
                               database_path=None, journal_folder=None):
    """Batch read committed evidence only; never import journals or fetch caches.

    Use the same newest-local/identity rules as matching_pad and read_local.
    Query only the requested MarketIDs, scoped to the configured journal folder.
    """
    stations = list(stations)
    ids = sorted({s['market_id'] for s in stations
                  if type(s.get('market_id')) is int and 0 < s['market_id'] < 2**64})
    local = {}
    if ids and database_path is not None and journal_folder is not None:
        try:
            con = sqlite3.connect(Path(database_path).resolve().as_uri() + '?mode=ro', uri=True)
            try:
                con.row_factory = sqlite3.Row
                for start in range(0, len(ids), 400):
                    batch = ids[start:start + 400]
                    rows = con.execute('''SELECT e.*, j.journal_path FROM station_pad_evidence e
                        JOIN station_pad_journals j ON j.id=e.journal_id
                        WHERE j.folder=? AND e.market_id IN (''' + ','.join('?' for _ in batch) + ''')
                        ORDER BY j.journal_path''',
                        [str(Path(journal_folder).resolve())] + [i.to_bytes(8, 'big') for i in batch])
                    for row in rows:
                        mid = int.from_bytes(row['market_id'], 'big')
                        stamp = timestamp(row['observed_at'])
                        if mid in local and stamp <= local[mid]['timestamp']:
                            continue
                        address = row['system_address']
                        local[mid] = dict(station_name=row['station_name'], system_name=row['system_name'],
                            system_address=int.from_bytes(address, 'big') if address else None,
                            timestamp=stamp, pad=dict(large=row['large_pads'], medium=row['medium_pads'],
                                                     small=row['small_pads']))
            finally:
                con.close()
        except (sqlite3.Error, OSError, ValueError):
            logging.getLogger(__name__).exception('Lokale Stations-Padbelege konnten nicht gelesen werden')
            # Do not present external evidence as authoritative after a failed local read.
            return [dict(s, pad_counts=None) for s in stations]
    result = []
    for station in stations:
        mid = station.get('market_id')
        pads = (matching_pad(local, mid, station.get('station_name'), system_name, system_address)
                if mid in local else station_pad_counts(station))
        result.append(dict(station, pad_counts=pads))
    return result


def largest_pad(pads):
    if not isinstance(pads, dict) or any(
            type(pads.get(k)) is not int or pads[k] < 0 for k in ('small', 'medium', 'large')):
        return None
    return next((size for size in (PadSize.LARGE, PadSize.MEDIUM, PadSize.SMALL)
                 if pads[size.value] > 0), None)


def matching_pad(metadata, market_id, station_name, system_name, system_address=None):
    row = metadata.get(market_id)
    if (row is None or row['station_name'] != station_name or row['system_name'] != system_name
            or (system_address is not None and row.get('system_address') is not None
                and system_address != row['system_address'])):
        return None
    return row['pad']


class PadMetadata:
    def __init__(self, database_path=None):
        self.database_path = database_path
        self.lock = Lock()
        self.files = {}

    def read(self, journal_folder=None, spansh_folder=None, cancel=None):
        from .trade_market_source import TradeReadCancelled
        def check():
            if cancel is not None and cancel.is_set():
                raise TradeReadCancelled()
        while not self.lock.acquire(timeout=.05):
            check()
        try:
            check()
            local = {}
            if journal_folder:
                if self.database_path is None:
                    raise RuntimeError('Local pad metadata database is not configured')
                from .station_pad_store import read_local
                local = read_local(self.database_path, journal_folder, cancel)
            paths = []
            if spansh_folder:
                paths += [(p, 'spansh') for p in Path(spansh_folder).glob('*.json')]
            records = []
            for path, source in sorted(paths):
                check()
                try:
                    st = path.stat()
                    sig = (st.st_ino, st.st_size, st.st_mtime_ns)
                    old = self.files.get(path)
                    if old is not None and old[0] == sig:
                        records.extend(old[3].values())
                        continue
                    rows = {}
                    from .spansh_cache import validate
                    data = json.loads(path.read_text())
                    validate(data, int(path.stem))
                    for row in data.get('stations', []):
                        self._record(rows, dict(MarketID=row.get('market_id'),
                            StationName=row.get('station_name'), StarSystem=data.get('system_name'),
                            SystemAddress=data.get('system_address'), LandingPads=row.get('landing_pads'),
                            timestamp=row.get('station_updated_at') or data.get('fetched_at')), source)
                    after = path.stat()
                    if sig != (after.st_ino, after.st_size, after.st_mtime_ns):
                        continue
                    self.files[path] = (sig, 0, {}, rows)
                    records.extend(rows.values())
                except (OSError, ValueError, TypeError, AttributeError):
                    continue
            active = {p for p, _ in paths}
            self.files = {p: v for p, v in self.files.items() if p in active}
            result = {}
            for row in records:
                previous = result.get(row['market_id'])
                key = (row['source'] == 'journal', row['timestamp'])
                if previous is None or key > (previous['source'] == 'journal', previous['timestamp']):
                    result[row['market_id']] = row
            result.update(local)
            return result
        finally:
            self.lock.release()

    @staticmethod
    def _record(rows, event, source):
        mid = event.get('MarketID')
        if type(mid) is not int or mid <= 0:
            return
        if any(not isinstance(event.get(k), str) or not event[k].strip()
               for k in ('StationName', 'StarSystem')):
            return
        raw = event.get('LandingPads')
        pads = {k.lower(): v for k, v in raw.items()} if isinstance(raw, dict) else None
        if not isinstance(pads, dict) or any(type(pads.get(k)) is not int or pads[k] < 0
                                             for k in ('small', 'medium', 'large')):
            return
        pad = largest_pad(pads)
        try:
            stamp = timestamp(event.get('timestamp'))
        except (ValueError, TypeError):
            return
        if mid not in rows or stamp >= rows[mid]['timestamp']:
            rows[mid] = dict(market_id=mid, station_name=event['StationName'],
                system_name=event['StarSystem'], system_address=event.get('SystemAddress'),
                pad=pad, source=source, timestamp=stamp)


_resolvers = {}
_lock = Lock()


def read_pad_metadata(journal_folder=None, spansh_folder=None, cancel=None, database_path=None):
    key = (str(database_path), str(journal_folder), str(spansh_folder))
    with _lock:
        resolver = _resolvers.setdefault(key, PadMetadata(database_path))
    return resolver.read(journal_folder, spansh_folder, cancel)
