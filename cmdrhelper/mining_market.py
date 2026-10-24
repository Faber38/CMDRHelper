"""Read actual commander sales from indexed journals; never market offers."""
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

from .journal_files import journal_sort_key
from .material_inventory import frontier_name
from .mining_catalog import MINING_COMMODITIES


@dataclass(frozen=True)
class MiningSale:
    symbol: str
    price: int
    timestamp: datetime
    count: int
    station: str = ''
    system: str = ''


@dataclass(frozen=True)
class MiningPrices:
    quotes: tuple = ()
    status: str = 'ok'


def read_mining_prices(database_path, commander_id, *,
                       commodities=MINING_COMMODITIES, cancel=None, cache=None):
    """Read-only projection using the same verified identity as mining inventory.

    Event UTC time wins; ties use journal filename chronology, resolved path,
    then byte offset. Cache only unchanged files, never the selected result.
    Location is local to each journal and cleared on travel/undocking.
    """
    if not database_path or not Path(database_path).is_file():
        return MiningPrices(status='missing')
    if not commander_id:
        return MiningPrices()
    cache = cache if cache is not None else {}
    with sqlite3.connect(Path(database_path).resolve().as_uri() + '?mode=ro', uri=True) as con:
        commander = con.execute('SELECT fid FROM commanders WHERE id=?', (commander_id,)).fetchone()
        sessions = con.execute('SELECT journal_file,commander_id,fid_seen,attribution_status FROM journal_sessions').fetchall()
    if not commander or not commander[0]:
        return MiningPrices()
    fid = commander[0]
    paths = {}
    for raw, cid, seen, status in sessions:
        paths.setdefault(Path(raw).resolve(), []).append((cid, seen, status))
    wanted = {c.symbol for c in commodities}
    latest = {}
    for path, identities in paths.items():
        if cancel is not None and cancel.is_set():
            return MiningPrices(status='cancelled')
        if any(identity != (commander_id, fid, 'identified') for identity in identities):
            continue
        stat = path.stat()
        signature = (stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
        cached = cache.get(path)
        if cached and cached[0] == signature:
            seen, sales = cached[1:]
        else:
            seen, sales = set(), []
            station = system = ''
            with path.open('rb') as stream:
                while True:
                    if cancel is not None and cancel.is_set():
                        return MiningPrices(status='cancelled')
                    offset = stream.tell()
                    line = stream.readline()
                    if not line or not line.endswith(b'\n'):
                        break
                    try:
                        event = json.loads(line)
                    except (ValueError, UnicodeError):
                        station = system = ''
                        continue
                    if not isinstance(event, dict):
                        continue
                    kind = event.get('event')
                    if kind in ('Commander', 'LoadGame') and event.get('FID'):
                        seen.add(event['FID'])
                    if kind in ('Location', 'FSDJump', 'CarrierJump'):
                        system = event.get('StarSystem') or ''
                        station = event.get('StationName') or ''
                    elif kind == 'Docked':
                        station = event.get('StationName') or ''
                        system = event.get('StarSystem') or system
                    elif kind in ('Undocked', 'SupercruiseEntry', 'StartJump'):
                        station = ''
                        if kind == 'StartJump':
                            system = ''
                    if kind != 'MarketSell':
                        continue
                    price, count = event.get('SellPrice'), event.get('Count')
                    if type(price) is not int or price < 0 or type(count) is not int or count <= 0:
                        continue
                    try:
                        stamp = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                        if stamp.tzinfo is None:
                            continue
                        symbol = frontier_name(event.get('Type'))
                    except (KeyError, ValueError, TypeError, AttributeError):
                        continue
                    sales.append((offset, MiningSale(symbol, price, stamp.astimezone(timezone.utc),
                                                    count, station, system)))
            after = path.stat()
            if signature != (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise OSError('Journal changed during sale read; retry')
            cache[path] = (signature, seen, sales)
        if seen != {fid}:
            continue
        for offset, sale in sales:
            if sale.symbol not in wanted:
                continue
            key = (sale.timestamp, journal_sort_key(path), str(path), offset)
            if sale.symbol not in latest or key > latest[sale.symbol][0]:
                latest[sale.symbol] = (key, sale)
    return MiningPrices(tuple(latest[s][1] for s in sorted(latest)))
