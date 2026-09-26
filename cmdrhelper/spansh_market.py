"""Spansh adapter for bounded market searches; memory only, synchronous/cancellable."""
from collections import OrderedDict
from dataclasses import replace, asdict
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from http.client import HTTPException
import json
import math
from threading import Lock, local
from types import SimpleNamespace
import time
from urllib.request import Request

from .commodity_master import lookup_by_id, lookup_by_symbol
from .market_data import (MarketOffer, MarketSearch, MarketSearchResult, MarketStatus,
                          PadSize, TradeSide, ProviderDiagnostics, within_market_age)
from .spansh_transport import TransportError, request_json

DEFAULT_CACHE_TTL = 300
_MAX = 2147483647


class _Failure(Exception):
    def __init__(self, status, http_status=None, retry_after=None):
        self.status, self.http_status, self.retry_after = status, http_status, retry_after


def _number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value) and value >= 0
    except OverflowError:
        return False


def _integer(value):
    return value if type(value) is int and value >= 0 else None


def _timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return stamp.astimezone(timezone.utc) if stamp.tzinfo else None
    except ValueError:
        return None


def _carrier(kind):
    return 'carrier' in kind.casefold()


def _pad(row):
    if row.get('has_large_pad') is True or (_integer(row.get('large_pads')) or 0) > 0:
        return PadSize.LARGE
    if (_integer(row.get('medium_pads')) or 0) > 0:
        return PadSize.MEDIUM
    if (_integer(row.get('small_pads')) or 0) > 0:
        return PadSize.SMALL
    return None


def _range(low, high=_MAX):
    return {'comparison': '<=>', 'value': [low, high]}


def _valid_query(q):
    return (isinstance(q, MarketSearch) and isinstance(q.reference_system, str)
            and bool(q.reference_system.strip()) and _number(q.radius_ly)
            and (q.minimum_quantity is None or
                 type(q.minimum_quantity) is int and 1 <= q.minimum_quantity <= _MAX)
            and (q.max_age is None or isinstance(q.max_age, timedelta) and q.max_age.total_seconds() > 0)
            and type(q.include_fleet_carriers) is bool and isinstance(q.required_pad, PadSize)
            and (q.max_distance_to_arrival_ls is None or _number(q.max_distance_to_arrival_ls))
            and type(q.limit) is int and 1 <= q.limit <= 100)


class SpanshMarketProvider:
    provider = 'spansh'
    base_url = 'https://spansh.co.uk/api'

    def __init__(self, *, opener=None, timeout=10, retries=1, cache_ttl=DEFAULT_CACHE_TTL,
                 cache_capacity=32, page_size=50, max_pages=6, request_interval=1,
                 clock=time.monotonic, utcnow=lambda: datetime.now(timezone.utc), sleep=time.sleep):
        if (not _number(timeout) or not 0 < timeout <= 30 or retries not in (0, 1)
                or not _number(cache_ttl) or not _number(request_interval) or request_interval < 1
                or type(cache_capacity) is not int or not 1 <= cache_capacity <= 128
                or type(page_size) is not int or not 1 <= page_size <= 100
                or type(max_pages) is not int or not 3 <= max_pages <= 12):
            raise ValueError('Invalid bounded market provider configuration')
        self.opener, self.timeout, self.retries = opener, timeout, retries
        self.cache_ttl, self.cache_capacity = cache_ttl, cache_capacity
        self.page_size, self.max_pages = page_size, max_pages
        self.request_interval = request_interval
        self.clock, self.utcnow, self.sleep = clock, utcnow, sleep
        self._cache = OrderedDict()
        self._station_types = None
        self._last_request = None
        self._rate_limit_until = 0
        self._retry_after = None
        self._lock = Lock()
        self._diagnostics = local()

    def search_sell(self, query, *, cancel=None):
        return self._search(query, TradeSide.SELL, cancel)

    def search_buy(self, query, *, cancel=None):
        return self._search(query, TradeSide.BUY, cancel)

    @staticmethod
    def _cancel(cancel):
        if cancel is not None and cancel.is_set():
            raise _Failure(MarketStatus.CANCELLED)

    def _wait(self, delay, cancel):
        self._cancel(cancel)
        if cancel is not None:
            if cancel.wait(max(0, delay)):
                raise _Failure(MarketStatus.CANCELLED)
        elif delay > 0:
            self.sleep(delay)

    def _request(self, path, payload, cancel):
        req = Request(self.base_url + path,
                      data=json.dumps(payload, allow_nan=False).encode() if payload is not None else None,
                      headers={'Content-Type': 'application/json', 'Accept': 'application/json',
                               'User-Agent': 'CMDRHelper/market-data'},
                      method='POST' if payload is not None else 'GET')
        for attempt in range(self.retries + 1):
            self._cancel(cancel)
            if self.clock() < self._rate_limit_until:
                raise _Failure(MarketStatus.RATE_LIMIT, 429, self._retry_after)
            if self._last_request is not None:
                self._wait(self.request_interval - (self.clock() - self._last_request), cancel)
            self._last_request = self.clock()
            try:
                try:
                    diagnostics = getattr(self._diagnostics, 'current', None)
                    if diagnostics is not None and attempt > 0:
                        diagnostics.retries += 1
                    data = request_json(req, timeout=self.timeout, opener=self.opener, diagnostics=diagnostics)
                except HTTPException as exc:
                    # urllib can surface truncated HTTP bodies outside OSError.
                    raise TransportError('network_error') from exc
                self._cancel(cancel)
                if not isinstance(data, dict):
                    raise _Failure(MarketStatus.INVALID_RESPONSE)
                if data.get('error'):
                    self._api_error(data)
                return data
            except TransportError as exc:
                if isinstance(exc.response_json, dict) and exc.status in (400, 404, 422):
                    self._api_error(exc.response_json, exc.status)
                transient = exc.code in ('timeout', 'network_error') or exc.status in (429, 500, 502, 503, 504)
                delay = 2.0
                if exc.retry_after:
                    try:
                        parsed = float(exc.retry_after)
                        delay = max(delay, parsed) if math.isfinite(parsed) else float('inf')
                    except ValueError:
                        try:
                            delay = max(delay, (parsedate_to_datetime(exc.retry_after) - self.utcnow()).total_seconds())
                        except (ValueError, TypeError, OverflowError):
                            # Do not retry early when an unparseable limit was supplied.
                            delay = float('inf')
                if exc.status == 429:
                    self._retry_after = exc.retry_after
                    self._rate_limit_until = self.clock() + (delay if math.isfinite(delay) else 30)
                if attempt < self.retries and transient and math.isfinite(delay) and delay <= 30:
                    self._wait(delay, cancel)
                    continue
                status = MarketStatus.RATE_LIMIT if exc.status == 429 else MarketStatus(exc.code)
                raise _Failure(status, exc.status, exc.retry_after) from exc

    @staticmethod
    def _api_error(data, http_status=None):
        message = str(data.get('error', '')).casefold()
        if any(word in message for word in ('unknown', 'not found', 'could not find', 'invalid')):
            if 'system' in message or 'reference' in message:
                raise _Failure(MarketStatus.UNKNOWN_SYSTEM, http_status)
            if 'commodity' in message:
                raise _Failure(MarketStatus.UNKNOWN_COMMODITY, http_status)
        if message:
            raise _Failure(MarketStatus.HTTP_ERROR if http_status else MarketStatus.INVALID_RESPONSE, http_status)

    def _types(self, cancel):
        # Discover the provider's actual type vocabulary; no guessed exclusion operator.
        if self._station_types is None:
            values = self._request('/stations/field_values/type', None, cancel).get('values')
            if not isinstance(values, list) or not values or not all(isinstance(v, str) for v in values):
                raise _Failure(MarketStatus.INVALID_RESPONSE)
            self._station_types = tuple(v for v in values if not _carrier(v))
            if not self._station_types:
                self._station_types = None
                raise _Failure(MarketStatus.INVALID_RESPONSE)
        return self._station_types

    def _filters(self, q, item, side, now, cancel):
        price, amount = ('sell_price', 'demand') if side == TradeSide.SELL else ('buy_price', 'supply')
        filters = {'distance': {'min': 0, 'max': q.radius_ly},
                   'market': [{'name': item.english_name, price: _range(1),
                               amount: _range(q.minimum_quantity or 1)}]}
        if q.max_age is not None:
            try:
                earliest = now - q.max_age
            except OverflowError:
                raise _Failure(MarketStatus.INVALID_QUERY)
            filters['market_updated_at'] = _range(earliest.isoformat(), now.isoformat())
        if not q.include_fleet_carriers:
            filters['type'] = {'value': list(self._types(cancel))}
        if q.max_distance_to_arrival_ls is not None:
            filters['distance_to_arrival'] = _range(0, q.max_distance_to_arrival_ls)
        # Spansh's filters are conjunctive. Branches implement pad OR; overlaps
        # are deduplicated by market ID. Do not require absent smaller-pad fields.
        branches = [{}]
        if q.required_pad != PadSize.ANY:
            branches = [{'has_large_pad': {'value': True}}]
            if q.required_pad in (PadSize.MEDIUM, PadSize.SMALL):
                branches.append({'medium_pads': _range(1)})
            if q.required_pad == PadSize.SMALL:
                branches.append({'small_pads': _range(1)})
        return [{**filters, **branch} for branch in branches], price

    def _normalize(self, row, item, retrieved):
        if not isinstance(row, dict):
            raise _Failure(MarketStatus.INVALID_RESPONSE)
        market = row.get('market')
        if not isinstance(market, list):
            raise _Failure(MarketStatus.INVALID_RESPONSE)
        matches = [m for m in market if isinstance(m, dict) and m.get('commodity') == item.english_name]
        if len(matches) != 1:
            return None
        m = matches[0]
        stamp = _timestamp(row.get('market_updated_at'))
        if (not stamp or not all(isinstance(row.get(k), str) and row[k].strip()
                                for k in ('system_name', 'name', 'type'))
                or not (_integer(row.get('system_id64')) or 0)
                or not (_integer(row.get('market_id')) or 0) or not _number(row.get('distance'))):
            return None
        arrival = row.get('distance_to_arrival')
        access = row.get('carrier_docking_access')
        return MarketOffer(item.frontier_id, item.symbol, item.english_name,
                           row['system_name'], row['system_id64'], row['name'], row['market_id'], row['type'],
                           row['distance'], arrival if _number(arrival) else None, _pad(row),
                           _carrier(row['type']), access if isinstance(access, str) else None,
                           _integer(m.get('buy_price')), _integer(m.get('sell_price')),
                           _integer(m.get('supply')), _integer(m.get('demand')), stamp, retrieved, self.provider)

    @staticmethod
    def _eligible(offer, q, side, now):
        price, amount = ((offer.commander_sell_price, offer.demand) if side == TradeSide.SELL
                         else (offer.commander_buy_price, offer.supply))
        ranks = {None: 0, PadSize.ANY: 0, PadSize.SMALL: 1, PadSize.MEDIUM: 2, PadSize.LARGE: 3}
        return (price is not None and price > 0 and amount is not None and amount >= (q.minimum_quantity or 1)
                and within_market_age(now - offer.market_updated_at, q.max_age)
                and offer.distance_ly <= q.radius_ly
                and (q.include_fleet_carriers or not offer.is_fleet_carrier)
                and ranks[offer.largest_pad] >= ranks[q.required_pad]
                and (q.max_distance_to_arrival_ls is None or offer.distance_to_arrival_ls is not None
                     and offer.distance_to_arrival_ls <= q.max_distance_to_arrival_ls))

    def _result(self, offers, q, side, truncated, cached=False):
        now = self.utcnow()
        offers = [o for o in offers if self._eligible(o, q, side, now)]
        offers.sort(key=lambda o: ((-o.commander_sell_price if side == TradeSide.SELL else o.commander_buy_price),
                                  -o.market_updated_at.timestamp(), o.distance_ly,
                                  o.station_name, o.system_name, o.market_id))
        diagnostics = getattr(self._diagnostics, 'current', None)
        if diagnostics is not None:
            diagnostics.page_limit_reached = bool(truncated)
            diagnostics.result_limit_reached = len(offers) > q.limit
            diagnostics.cache_hits = int(cached)
        return MarketSearchResult(MarketStatus.OK if offers else MarketStatus.NO_RESULTS,
                                  tuple(offers[:q.limit]), q, truncated=truncated or len(offers) > q.limit,
                                  from_cache=cached)

    def _search(self, q, side, cancel):
        # Per-thread scope prevents queued Sell/Buy/Recommendation calls from
        # attributing another worker's requests to this commodity.
        diagnostics = SimpleNamespace(**asdict(ProviderDiagnostics(
            page_limit=self.max_pages, result_limit=getattr(q, 'limit', 0))))
        self._diagnostics.current = diagnostics
        try:
            result = self._search_impl(q, side, cancel)
            if result.http_status is not None:
                diagnostics.last_http_status = result.http_status
            if result.retry_after is not None:
                diagnostics.retry_after = result.retry_after
            return replace(result, diagnostics=ProviderDiagnostics(**vars(diagnostics)))
        except Exception as exc:
            # Preserve counters even when the caller's existing exception guard
            # handles an unexpected commodity failure. Do not change propagation.
            exc.market_diagnostics = ProviderDiagnostics(**vars(diagnostics))
            raise
        finally:
            del self._diagnostics.current

    def _search_impl(self, q, side, cancel):
        if not _valid_query(q):
            return MarketSearchResult(MarketStatus.INVALID_QUERY, query=q)
        item = lookup_by_id(q.commodity) if type(q.commodity) is int else lookup_by_symbol(q.commodity)
        if item is None:
            return MarketSearchResult(MarketStatus.UNKNOWN_COMMODITY, query=q)
        acquired = False
        try:
            self._cancel(cancel)
            while not acquired:
                acquired = self._lock.acquire(timeout=0.1)
                self._cancel(cancel)
            key = (self.provider, side, replace(q, commodity=item.frontier_id,
                                              reference_system=q.reference_system.strip()))
            cached = self._cache.get(key)
            if cached and 0 <= self.clock() - cached[0] < self.cache_ttl:
                self._cache.move_to_end(key)
                return self._result(cached[1], q, side, cached[2], True)
            now = self.utcnow()
            filters, price = self._filters(q, item, side, now, cancel)
            pages = [0] * len(filters)
            active = list(range(len(filters)))
            offers = {}
            # Round-robin ensures all pad branches get a page before further pagination.
            for _ in range(self.max_pages):
                if not active:
                    break
                branch = active.pop(0)
                page = pages[branch]
                payload = {'reference_system': q.reference_system.strip(), 'filters': filters[branch],
                           'sort': [{'market_' + price: [{'name': item.english_name,
                                    'direction': 'desc' if side == TradeSide.SELL else 'asc'}]}],
                           'size': self.page_size, 'page': page}
                self._diagnostics.current.pages_started += 1
                data = self._request('/stations/search', payload, cancel)
                retrieved = self.utcnow()
                if 'reference' in data and data['reference'] is None:
                    raise _Failure(MarketStatus.UNKNOWN_SYSTEM)
                reference, rows, count = data.get('reference'), data.get('results'), data.get('count')
                if (not isinstance(reference, dict) or not isinstance(reference.get('name'), str)
                        or reference['name'].casefold() != q.reference_system.strip().casefold()
                        or not isinstance(rows, list) or _integer(count) is None):
                    raise _Failure(MarketStatus.INVALID_RESPONSE)
                if len(rows) > self.page_size or (not rows and page * self.page_size < count):
                    raise _Failure(MarketStatus.INVALID_RESPONSE)
                for row in rows:
                    offer = self._normalize(row, item, retrieved)
                    if offer is not None and self._eligible(offer, q, side, retrieved):
                        previous = offers.get(offer.market_id)
                        if previous is None or offer.market_updated_at > previous.market_updated_at:
                            offers[offer.market_id] = offer
                pages[branch] += 1
                self._diagnostics.current.pages_completed += 1
                if pages[branch] * self.page_size < count:
                    active.append(branch)
            self._cancel(cancel)
            values = tuple(offers.values())
            self._cache[key] = (self.clock(), values, bool(active))
            self._cache.move_to_end(key)
            while len(self._cache) > self.cache_capacity:
                self._cache.popitem(last=False)
            return self._result(values, q, side, bool(active))
        except _Failure as exc:
            return MarketSearchResult(exc.status, query=q, http_status=exc.http_status,
                                      retry_after=exc.retry_after)
        finally:
            if acquired:
                self._lock.release()
