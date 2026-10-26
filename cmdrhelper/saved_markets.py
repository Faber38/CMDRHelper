"""Read-only saved-market browsing. No observers, journal sync or network I/O."""
from concurrent.futures import TimeoutError
from contextlib import closing
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3

from .market_store import MarketStore, StaleReadError
from .observed_market_cache import timestamp, utcnow
from .pad_metadata import largest_pad, matching_pad


class ReadCancelled(Exception):
    pass


def check_cancel(cancel):
    if cancel is not None and cancel.is_set():
        raise ReadCancelled()


@dataclass(frozen=True)
class SavedMarketSource:
    market_path: Path | None
    database_path: Path | None = None
    station_folder: Path | None = None
    ready: object = None

    def wait_ready(self, cancel):
        if self.ready is not None:
            while True:
                check_cancel(cancel)
                try:
                    self.ready.result(timeout=.05)
                    break
                except TimeoutError:
                    if self.ready.done():
                        raise
        check_cancel(cancel)


def source_from_state(state):
    """Paths only: never instantiate the observer's lazy, writable cache."""
    observer = getattr(state, 'observed_markets', None)
    writer = getattr(observer, 'writer', None)
    cache = getattr(observer, '_cache', None)
    if cache is None and observer is not None:
        cache = vars(observer).get('cache')
    market = (Path(writer.destination) if writer is not None else
              Path(cache.path).parent / 'markets.db' if cache is not None else None)
    database = getattr(state, 'database', None)
    path = getattr(database, 'path', None)
    return SavedMarketSource(market, Path(path) if path else None,
        market.parent.parent / 'external' / 'spansh' if market else None,
        writer.ready if writer is not None and not writer.activated else None)


def _connect(path):
    con = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True, timeout=.25)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA query_only=ON')
    return con


def _coordinates(con, address=None, name=''):
    from .ui.favorites_view import stored_coordinates
    return stored_coordinates(con, address, name)


def read_reference(source, name, cancel=None):
    check_cancel(cancel)
    if source.database_path is None or not source.database_path.is_file() or not name.strip():
        return None
    with closing(_connect(source.database_path)) as con:
        return _coordinates(con, name=name.strip())


def _metadata(source, headers, cancel):
    coordinates, pads, local = {}, {}, set()
    incomplete = False
    if source.database_path is not None and source.database_path.is_file():
        with closing(_connect(source.database_path)) as con:
            con.execute('BEGIN')
            try:
                systems = {}
                for h in headers:
                    check_cancel(cancel)
                    key = (h.system_address, h.system_name)
                    if key not in systems:
                        systems[key] = _coordinates(con, *key)
                    coordinates[h.market_id] = systems[key]
            except sqlite3.Error:
                incomplete = True
            # Read committed pad evidence across commanders. Do NOT call
            # station_pad_store.read_local(): that synchronizes/writes journals.
            try:
                ids = [h.market_id for h in headers]
                evidence = {}
                for start in range(0, len(ids), 400):
                    check_cancel(cancel)
                    batch = ids[start:start + 400]
                    rows = con.execute('SELECT * FROM station_pad_evidence WHERE market_id IN (' +
                        ','.join('?' for _ in batch) + ')', [i.to_bytes(8, 'big') for i in batch])
                    for row in rows:
                        mid = int.from_bytes(row['market_id'], 'big')
                        local.add(mid)
                        stamp = timestamp(row['observed_at'])
                        value = dict(station_name=row['station_name'], system_name=row['system_name'],
                            system_address=int.from_bytes(row['system_address'], 'big') if row['system_address'] else None,
                            pad=largest_pad(dict(small=row['small_pads'], medium=row['medium_pads'], large=row['large_pads'])))
                        old = evidence.get(mid)
                        if old is None or stamp > old[0]:
                            evidence[mid] = (stamp, value)
                        elif stamp == old[0] and value != old[1]:
                            evidence[mid] = (stamp, None)  # Ambiguous same-time evidence.
                pads = {mid: value for mid, (_, value) in evidence.items() if value is not None}
            except (sqlite3.Error, ValueError, TypeError):
                # Failed local evidence must not silently become external truth.
                incomplete = True
                local = {h.market_id for h in headers}
                pads = {}
    if source.station_folder is not None and source.station_folder.is_dir():
        from .spansh_cache import MAX_CACHE, validate
        wanted = {h.market_id for h in headers} - local
        external = {}
        if wanted:
            for path in sorted(source.station_folder.glob('*.json')):
                check_cancel(cancel)
                try:
                    if path.stat().st_size > MAX_CACHE:
                        continue
                    data = json.loads(path.read_text())
                    validate(data, int(path.stem))
                    for row in data['stations']:
                        mid = row['market_id']
                        if mid not in wanted:
                            continue
                        stamp = timestamp(row.get('station_updated_at') or data['fetched_at'])
                        value = dict(station_name=row['station_name'], system_name=data['system_name'],
                            system_address=data['system_address'], pad=largest_pad(row.get('landing_pads')))
                        old = external.get(mid)
                        if old is None or stamp > old[0]:
                            external[mid] = (stamp, value)
                        elif stamp == old[0] and value != old[1]:
                            external[mid] = (stamp, None)
                except (OSError, ValueError, TypeError, KeyError):
                    continue
            pads.update({mid: value for mid, (_, value) in external.items() if value is not None})
    return [dict(header=h, coordinates=coordinates.get(h.market_id),
                 pad=matching_pad(pads, h.market_id, h.station_name, h.system_name, h.system_address))
            for h in headers], incomplete


def read_markets(source, cancel=None, *, clock=utcnow):
    source.wait_ready(cancel)
    if source.market_path is None or not source.market_path.is_file():
        return [], False
    # Retry a bounded number of times when a concurrent commit changes a page.
    for attempt in range(3):
        try:
            with MarketStore(source.market_path, read_only=True, clock=clock) as store:
                headers, cursor, revision = [], None, None
                while True:
                    check_cancel(cancel)
                    page = store.query_current_candidates(max_age=None, limit=500,
                        cursor=cursor, expected_revision=revision)
                    headers.extend(item.header for item in page.items)
                    revision, cursor = page.revision, page.next_cursor
                    if cursor is None:
                        break
            try:
                return _metadata(source, headers, cancel)
            except (sqlite3.Error, OSError):
                # Optional station metadata must not hide a readable market.
                return [dict(header=h, coordinates=None, pad=None) for h in headers], True
        except StaleReadError:
            if attempt == 2:
                raise


def read_market(source, market_id, cancel=None, *, clock=utcnow):
    source.wait_ready(cancel)
    if source.market_path is None or not source.market_path.is_file():
        return None
    with MarketStore(source.market_path, read_only=True, clock=clock) as store:
        check_cancel(cancel)
        return store.get_current(market_id, max_age=None)
