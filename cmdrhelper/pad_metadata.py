"""Read-only station pad evidence, incrementally cached in worker memory.

No network, price changes or database migration. Journal tails are read once
per process; unchanged journals and cached Spansh files are never reread.
"""
import json
from pathlib import Path
from threading import Lock

from .market_data import PadSize
from .observed_market_cache import timestamp


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
    def __init__(self):
        self.lock = Lock()
        self.files = {}

    def read(self, journal_folder=None, spansh_folder=None, cancel=None):
        from .trade_market_source import TradeReadCancelled
        def check():
            if cancel is not None and cancel.is_set():
                raise TradeReadCancelled()
        with self.lock:
            paths = []
            if journal_folder:
                paths += [(p, 'journal') for p in Path(journal_folder).glob('Journal.*.log')]
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
                    offset, context, rows = 0, {}, {}
                    if source == 'journal' and old and old[0][0] == sig[0] and old[0][1] < sig[1]:
                        offset, context, rows = old[1], dict(old[2]), dict(old[3])
                    if source == 'journal':
                        with path.open('rb') as stream:
                            stream.seek(offset)
                            while True:
                                check()
                                line = stream.readline()
                                if not line or not line.endswith(b'\n'):
                                    break
                                offset = stream.tell()
                                try:
                                    e = json.loads(line)
                                except ValueError:
                                    continue
                                kind = e.get('event')
                                if kind in ('Fileheader', 'LoadGame', 'Shutdown'):
                                    context = {}
                                if kind in ('Location', 'FSDJump', 'CarrierJump', 'Docked'):
                                    context = {k: e[k] for k in ('StarSystem', 'SystemAddress') if k in e}
                                if kind in ('Docked', 'DockingRequested'):
                                    self._record(rows, dict(context, **e), source)
                    else:
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
                    self.files[path] = (sig, offset, context, rows)
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
            return result

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


def read_pad_metadata(journal_folder=None, spansh_folder=None, cancel=None):
    key = (str(journal_folder), str(spansh_folder))
    with _lock:
        resolver = _resolvers.setdefault(key, PadMetadata())
    return resolver.read(journal_folder, spansh_folder, cancel)
