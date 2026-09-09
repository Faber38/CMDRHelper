"""Keyless, UI-independent search for known engineering material traders.

Only SpanshMaterialTraderClient knows Spansh's wire format. No access assurance
is inferred from absent metadata. Arrival distance deliberately has no unit.
"""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from enum import Enum
import math
from threading import RLock
import time
from urllib.parse import urlencode
from urllib.request import Request
import json

from cmdrhelper.spansh_transport import TransportError, request_json


class TraderType(str, Enum):
    RAW = 'Raw'
    MANUFACTURED = 'Manufactured'
    ENCODED = 'Encoded'


class SearchStatus(str, Enum):
    FOUND = 'found'
    NOT_FOUND = 'not_found'
    SEARCH_LIMIT = 'search_limit'
    INVALID_INPUT = 'invalid_input'
    REFERENCE_UNKNOWN = 'reference_unknown'
    NETWORK_ERROR = 'network_error'
    HTTP_ERROR = 'http_error'
    TIMEOUT = 'timeout'
    INVALID_JSON = 'invalid_json'
    SCHEMA_ERROR = 'schema_error'
    DETAIL_VALIDATION_FAILED = 'detail_validation_failed'


@dataclass(frozen=True)
class Coordinates:
    x: float
    y: float
    z: float

    def __post_init__(self):
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
               for v in (self.x, self.y, self.z)):
            raise ValueError('Coordinates must be finite numbers')

    def distance_to(self, other):
        return math.dist((self.x, self.y, self.z), (other.x, other.y, other.z))


@dataclass(frozen=True)
class TraderStation:
    trader_type: TraderType
    system_name: str
    station_name: str
    system_id64: int
    market_id: int
    coordinates: Coordinates
    station_type: str
    distance_ly: float | None = None
    arrival_distance_raw: float | None = None
    arrival_distance_unit: str = 'unknown'
    planetary: bool | None = None
    large_pad: bool | None = None
    large_pads: int | None = None
    medium_pads: int | None = None
    small_pads: int | None = None
    source_updated_at: str | None = None
    retrieved_at: datetime | None = None
    permit_required: bool | None = None
    permit_name: str | None = None
    docking_access: str | None = None
    station_state: str | None = None
    faction_state: str | None = None
    access_verified: bool = False


@dataclass(frozen=True)
class CandidatePage:
    stations: tuple[TraderStation, ...]
    exhausted: bool
    malformed_count: int = 0


@dataclass(frozen=True)
class TraderSearchResult:
    status: SearchStatus
    station: TraderStation | None = None
    http_status: int | None = None
    from_cache: bool = False


class TraderSearchError(Exception):
    def __init__(self, status, *, http_status=None):
        super().__init__(status.value)
        self.status, self.http_status = status, http_status


def is_fleet_carrier(station_type):
    """Fail closed for carrier variants, without using station names."""
    normalized = ''.join(c for c in station_type.casefold() if c.isalnum())
    return 'carrier' in normalized


def _text(value):
    return value.strip() if isinstance(value, str) and value.strip() else None


def _integer(value):
    return value if type(value) is int and value >= 0 else None


def _number(value):
    return float(value) if type(value) in (int, float) and math.isfinite(value) and value >= 0 else None


def _boolean(value):
    return value if type(value) is bool else None


class SpanshMaterialTraderClient:
    """Synchronous adapter. Run outside the GUI thread; never sends user identity.

    One retry at most, only for transient transport failures. A long Retry-After
    aborts this attempt instead of retrying earlier than requested by the server.
    """
    BASE_URL = 'https://spansh.co.uk/api'

    def __init__(self, *, opener=None, timeout=10, retries=1, sleep=time.sleep,
                 clock=time.monotonic, utcnow=lambda: datetime.now(timezone.utc)):
        if not 0 < timeout <= 30 or retries not in (0, 1):
            raise ValueError('Use a timeout <=30 seconds and at most one retry')
        self.opener, self.timeout, self.retries = opener, timeout, retries
        self.sleep, self.clock, self.utcnow = sleep, clock, utcnow
        self._last_request = None

    def _request(self, path, payload=None):
        request = Request(self.BASE_URL + path,
                          data=json.dumps(payload, allow_nan=False).encode() if payload is not None else None,
                          headers={'Content-Type': 'application/json', 'Accept': 'application/json',
                                   'User-Agent': 'CMDRHelper/material-traders'},
                          method='POST' if payload is not None else 'GET')
        for attempt in range(self.retries + 1):
            if self._last_request is not None:
                self.sleep(max(0, 1 - (self.clock() - self._last_request)))
            self._last_request = self.clock()
            try:
                data = request_json(request, timeout=self.timeout, opener=self.opener)
                if not isinstance(data, dict) or data.get('error'):
                    raise TraderSearchError(SearchStatus.SCHEMA_ERROR)
                return data
            except TransportError as exc:
                transient = exc.code in ('network_error', 'timeout') or (
                    exc.code == 'http_error' and exc.status in (429, 500, 502, 503, 504))
                delay = 2.0
                if exc.retry_after:
                    try:
                        delay = max(delay, float(exc.retry_after))
                    except ValueError:
                        try:
                            delay = max(delay, (parsedate_to_datetime(exc.retry_after) - self.utcnow()).total_seconds())
                        except (TypeError, ValueError, OverflowError):
                            pass
                if attempt < self.retries and transient and math.isfinite(delay) and delay <= 30:
                    self.sleep(delay)
                    continue
                raise TraderSearchError(SearchStatus(exc.code), http_status=exc.status) from exc

    def resolve_reference(self, name):
        data = self._request('/search/systems?' + urlencode({'q': name}))
        results = data.get('results')
        if not isinstance(results, list):
            raise TraderSearchError(SearchStatus.SCHEMA_ERROR)
        matches = [r for r in results if isinstance(r, dict) and
                   _text(r.get('name')) and r['name'].strip().casefold() == name.casefold()]
        if not matches:
            raise TraderSearchError(SearchStatus.REFERENCE_UNKNOWN)
        if len(matches) != 1 or _integer(matches[0].get('id64')) is None:
            raise TraderSearchError(SearchStatus.SCHEMA_ERROR)
        record = self._request('/system/' + str(matches[0]['id64'])).get('record')
        if not isinstance(record, dict) or str(record.get('name', '')).casefold() != name.casefold():
            raise TraderSearchError(SearchStatus.SCHEMA_ERROR)
        try:
            return Coordinates(record['x'], record['y'], record['z'])
        except (KeyError, ValueError, TypeError):
            raise TraderSearchError(SearchStatus.SCHEMA_ERROR) from None

    def _station(self, record):
        if not isinstance(record, dict):
            raise ValueError('Station is not an object')
        required = [_text(record.get(k)) for k in ('system_name', 'name', 'type')]
        ids = [_integer(record.get(k)) for k in ('system_id64', 'market_id')]
        if not all(required) or None in ids:
            raise ValueError('Station identity missing')
        coords = Coordinates(record.get('system_x'), record.get('system_y'), record.get('system_z'))
        return TraderStation(
            trader_type=TraderType(record.get('material_trader')),
            system_name=required[0], station_name=required[1], station_type=required[2],
            system_id64=ids[0], market_id=ids[1], coordinates=coords,
            arrival_distance_raw=_number(record.get('distance_to_arrival')),
            planetary=_boolean(record.get('is_planetary')),
            large_pad=_boolean(record.get('has_large_pad')),
            large_pads=_integer(record.get('large_pads')), medium_pads=_integer(record.get('medium_pads')),
            small_pads=_integer(record.get('small_pads')), source_updated_at=_text(record.get('updated_at')),
            retrieved_at=self.utcnow(), permit_required=_boolean(record.get('system_needs_permit')),
            permit_name=_text(record.get('system_permit_name')),
            docking_access=_text(record.get('docking_access') or record.get('carrier_docking_access')),
            station_state=_text(record.get('state')), faction_state=_text(record.get('controlling_minor_faction_state')))

    def search_page(self, reference, trader_type, page, size):
        data = self._request('/stations/search', {
            'filters': {'material_trader': {'value': [trader_type.value]}},
            'sort': [{'distance': {'direction': 'asc'}}], 'size': size, 'page': page,
            'reference_coords': {'x': reference.x, 'y': reference.y, 'z': reference.z}})
        records, count = data.get('results'), _integer(data.get('count'))
        if not isinstance(records, list) or count is None or len(records) > size:
            raise TraderSearchError(SearchStatus.SCHEMA_ERROR)
        stations, malformed = [], 0
        for record in records:
            try:
                station = self._station(record)
            except (ValueError, TypeError):
                malformed += 1
                continue
            if station.trader_type == trader_type and not is_fleet_carrier(station.station_type):
                stations.append(station)
        return CandidatePage(tuple(stations), len(records) < size or (page + 1) * size >= count, malformed)

    def station_detail(self, candidate, trader_type):
        try:
            data = self._request('/station/' + str(candidate.market_id))
        except TraderSearchError as exc:
            if exc.http_status == 404:
                raise TraderSearchError(SearchStatus.DETAIL_VALIDATION_FAILED) from exc
            raise
        if 'record' not in data:
            raise TraderSearchError(SearchStatus.SCHEMA_ERROR)
        try:
            station = self._station(data['record'])
            services = data['record'].get('services')
            if (station.market_id != candidate.market_id or station.system_id64 != candidate.system_id64
                    or station.coordinates != candidate.coordinates
                    or station.system_name != candidate.system_name
                    or station.trader_type != trader_type or is_fleet_carrier(station.station_type)
                    or not isinstance(services, list)
                    or not any(isinstance(s, dict) and s.get('name') == 'Material Trader' for s in services)):
                raise ValueError('Station no longer matches')
            return station
        except (ValueError, TypeError):
            raise TraderSearchError(SearchStatus.DETAIL_VALIDATION_FAILED) from None


class MaterialTraderSearchService:
    """Bounded search of the source's nearest candidates, with a small TTL cache.

    Source ordering is used only to obtain candidates; their local distances decide
    detail-check order. A limit without a usable result is never NOT_FOUND.
    """
    CACHE_TTL_SECONDS = 300
    CACHE_CAPACITY = 32
    PAGE_SIZE = 10
    MAX_PAGES = 3
    MAX_DETAILS = 5

    def __init__(self, client=None, *, clock=time.monotonic):
        self.client = client or SpanshMaterialTraderClient()
        self.clock, self._cache, self._lock = clock, OrderedDict(), RLock()

    def find_nearest(self, trader_type, *, system_name=None, coordinates=None):
        try:
            trader_type = TraderType(trader_type)
        except (ValueError, TypeError):
            return TraderSearchResult(SearchStatus.INVALID_INPUT)
        name = _text(system_name)
        if coordinates is not None and not isinstance(coordinates, Coordinates):
            return TraderSearchResult(SearchStatus.INVALID_INPUT)
        if coordinates is None and not name:
            return TraderSearchResult(SearchStatus.INVALID_INPUT)
        # Exact coordinates avoid reusing a distance calculated for another origin.
        key = (coordinates if coordinates is not None else name.casefold(), trader_type)
        with self._lock:
            cached = self._cache.get(key)
            if cached and self.clock() - cached[0] < self.CACHE_TTL_SECONDS:
                self._cache.move_to_end(key)
                return replace(cached[1], from_cache=True)
            self._cache.pop(key, None)
            try:
                reference = coordinates or self.client.resolve_reference(name)
                result = self._search(reference, trader_type)
            except TraderSearchError as exc:
                result = TraderSearchResult(exc.status, http_status=exc.http_status)
            if result.status in (SearchStatus.FOUND, SearchStatus.NOT_FOUND):
                self._cache[key] = (self.clock(), result)
                while len(self._cache) > self.CACHE_CAPACITY:
                    self._cache.popitem(last=False)
            return result

    def _search(self, reference, trader_type):
        candidates, malformed, exhausted = {}, 0, False
        for page in range(self.MAX_PAGES):
            batch = self.client.search_page(reference, trader_type, page, self.PAGE_SIZE)
            malformed += batch.malformed_count
            for station in batch.stations:
                candidates[station.market_id] = station
            exhausted = batch.exhausted
            if exhausted:
                break
        ordered = sorted(candidates.values(), key=lambda s: (reference.distance_to(s.coordinates), s.market_id))
        failed = False
        for candidate in ordered[:self.MAX_DETAILS]:
            try:
                station = self.client.station_detail(candidate, trader_type)
                distance = reference.distance_to(station.coordinates)
                if not math.isfinite(distance):
                    raise TraderSearchError(SearchStatus.SCHEMA_ERROR)
                return TraderSearchResult(SearchStatus.FOUND, replace(station, distance_ly=distance))
            except TraderSearchError as exc:
                if exc.status != SearchStatus.DETAIL_VALIDATION_FAILED:
                    raise
                failed = True
        if failed:
            return TraderSearchResult(SearchStatus.DETAIL_VALIDATION_FAILED)
        if malformed:
            return TraderSearchResult(SearchStatus.SCHEMA_ERROR)
        return TraderSearchResult(SearchStatus.NOT_FOUND if exhausted else SearchStatus.SEARCH_LIMIT)
