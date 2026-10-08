"""Demand-only MarketID lookup; no trading, journal ingestion or database writes."""
from collections import defaultdict
import logging
from PySide6.QtCore import QObject, QRunnable, QThreadPool, QTimer, Signal, Slot
from .spansh_cache import (SERVICES, TYPES, is_carrier, number, timestamp, valid_id,
                           validate)
from .spansh_market import SpanshMarketProvider

BATCH_SIZE = 5  # Live-verified ID-list size; do not assume larger server limits.


def lookup_documents(response, requested, now):
    """Whitelist identity metadata. Missing/contradictory IDs stay unresolved."""
    if (not isinstance(response, dict) or type(response.get('count')) is not int
            or not 0 <= response['count'] <= BATCH_SIZE
            or not isinstance(response.get('results'), list)
            or len(response['results']) != response['count']):
        raise ValueError('Incomplete or invalid identity response')
    records, rejected = {}, set()
    for raw in response['results']:
        if not isinstance(raw, dict): continue
        mid = raw.get('market_id')
        if not valid_id(mid) or mid not in requested: continue
        try:
            address = raw.get('system_id64')
            if not valid_id(address): raise ValueError('Invalid system identity')
            if any(not isinstance(raw.get(k), str) or not raw[k].strip() or len(raw[k]) > 1024
                   for k in ('name', 'system_name', 'type')):
                raise ValueError('Missing station identity')
            if is_carrier(raw['type']): raise ValueError('Carrier is not a static origin')
            row = dict(market_id=mid, station_name=raw['name'], source_type=raw['type'],
                       station_type=TYPES.get(raw['type'], raw['type']))
            if number(raw.get('distance_to_arrival')) and raw['distance_to_arrival'] >= 0:
                row['distance_ls'] = raw['distance_to_arrival']
            if 'updated_at' in raw:
                if not timestamp(raw['updated_at']): raise ValueError('Invalid timestamp')
                row['station_updated_at'] = raw['updated_at']
            pads = {}
            for size in ('small', 'medium', 'large'):
                key = size + '_pads'
                if key in raw:
                    if type(raw[key]) is not int or raw[key] < 0: raise ValueError('Invalid pads')
                    pads[size] = raw[key]
            if pads: row['landing_pads'] = pads
            if 'services' in raw:
                services = raw['services']
                if (not isinstance(services, list) or any(not isinstance(s, dict)
                        or not isinstance(s.get('name'), str) for s in services)):
                    raise ValueError('Invalid services')
                if any(s['name'] in ('Fleet Carrier Fuel','Fleet Carrier Management') for s in services):
                    raise ValueError('Carrier services')
                row['services'] = sorted({SERVICES[s['name']] for s in services if s['name'] in SERVICES})
            coords = None
            if any('system_' + k in raw for k in ('x','y','z')):
                if not all(number(raw.get('system_' + k)) for k in ('x','y','z')):
                    raise ValueError('Invalid coordinates')
                coords = {k: raw['system_' + k] for k in ('x','y','z')}
            record = (address, raw['system_name'], coords, row)
            if mid in records and records[mid] != record: rejected.add(mid)
            records[mid] = record
        except (ValueError, TypeError):
            rejected.add(mid)
    grouped = defaultdict(list)
    for mid, record in records.items():
        if mid not in rejected: grouped[record[0]].append(record)
    documents = []
    for address, rows in grouped.items():
        if len({r[1].casefold() for r in rows}) != 1: continue
        coords = [r[2] for r in rows if r[2] is not None]
        if coords and any(c != coords[0] for c in coords): continue
        data = dict(schema_version=1, source='spansh', coverage='partial', system_address=address,
                    system_name=rows[0][1], fetched_at=now.isoformat(), stations=[r[3] for r in rows])
        if coords: data['coordinates'] = coords[0]
        validate(data, address)
        documents.append(data)
    return documents


class LookupSignals(QObject):
    finished = Signal(object)


class LookupWorker(QRunnable):
    def __init__(self, provider, cache, ids):
        super().__init__()
        self.provider, self.cache, self.ids = provider, cache, tuple(ids)
        self.signals = LookupSignals()

    @Slot()
    def run(self):
        addresses = []
        try:
            response = self.provider._request('/stations/search', {
                'filters': {'market_id': {'value': [str(i) for i in self.ids]}},
                'size': BATCH_SIZE, 'page': 0}, None)
            for data in lookup_documents(response, set(self.ids), self.cache.now()):
                try:
                    self.cache.merge_lookup(data)
                    addresses.append(data['system_address'])
                except (OSError, ValueError):
                    continue
        except Exception:
            # Failure stays session-cached in the coordinator. Shopping is independent.
            logging.getLogger(__name__).debug('Origin lookup failed', exc_info=True)
        self.signals.finished.emit(addresses)


class OriginLookup(QObject):
    updated = Signal(object)
    settled = Signal()

    def __init__(self, cache, parent=None, *, provider=None, pool=None):
        super().__init__(parent)
        self.cache = cache
        self.provider = provider if provider is not None else SpanshMarketProvider()
        self.pool = pool if pool is not None else QThreadPool(self)
        if pool is None: self.pool.setMaxThreadCount(1)
        self.pending, self.attempted = set(), set()
        self.worker = None
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(150)  # Coalesce simultaneous UI demand; not polling.
        self.timer.timeout.connect(self.flush)

    def request(self, market_id):
        if not valid_id(market_id) or market_id in self.attempted: return
        self.pending.add(market_id)
        if self.worker is None and not self.timer.isActive(): self.timer.start()

    @Slot()
    def flush(self):
        if self.worker is not None or not self.pending: return
        ids = sorted(self.pending)[:BATCH_SIZE]
        self.pending.difference_update(ids)
        self.attempted.update(ids)  # Also covers unknown IDs, failures and in-flight requests.
        self.worker = LookupWorker(self.provider, self.cache, ids)
        self.worker.signals.finished.connect(self._finished)
        self.pool.start(self.worker)

    @Slot(object)
    def _finished(self, addresses):
        self.worker = None
        for address in addresses: self.updated.emit(address)
        if self.pending: self.timer.start()
        else: self.settled.emit()
