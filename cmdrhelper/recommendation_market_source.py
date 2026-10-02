"""Worker-owned recommendation reads with bounded per-commodity ranking caches."""
from concurrent.futures import TimeoutError
from contextlib import ExitStack, closing
from dataclasses import replace
from fractions import Fraction
from functools import partial
from heapq import nsmallest
import math
from pathlib import Path
import sqlite3

from .market_candidates import local_offer, merge_destinations, commodity_key
from .market_data import TradeSide
from .market_store import MarketStore, CommodityRef, StaleReadError, _datetime
from .trade_market_source import TradeReadCancelled
from .trade_recommendations import best_trade, best_supply_trade, ranking, refresh_remote


class RecommendationStoreSession:
    """One full fixed market, <=101 profitable local alternatives per relevant item.

    A bounded provider result can displace at most 100 local markets. Keeping
    101 ranked locals therefore preserves the exact surviving best choice.
    A provider breaking that limit gets a fresh streamed selection, never an
    incorrect truncated answer. Missing local commodities are fetched for every
    community MarketID before merging, independently of price/quantity filters.
    """
    def __init__(self, source, origin_header, query, *, clock, cancel, supply=False):
        self.source, self.header, self.query = source, origin_header, query
        self.clock, self.cancel = clock, cancel
        self.supply = supply
        self.stack = ExitStack()
        self.memo, self.distances, self.evaluated = {}, {}, {}
        self.now = clock()
        self.deadline = None
        self.count = None
        self.count_time = None

    def check(self):
        if self.cancel.is_set():
            raise TradeReadCancelled()

    def __enter__(self):
        try:
            self.pads = self.source.pad_metadata(self.cancel)
            ready = (None if self.source.writer is not None and self.source.writer.activated
                     else self.source.ready)
            while ready is not None:
                self.check()
                try:
                    ready.result(timeout=.05)
                    break
                except TimeoutError:
                    if ready.done():
                        raise
            self.check()
            self.store = self.stack.enter_context(MarketStore(self.source.path, read_only=True, clock=lambda: self.now))
            self.store._con.set_progress_handler(lambda: int(self.cancel.is_set()), 1000)
            with self.store._transaction():
                self.revision = self.store._revision()
            self.origin = self.store.get_current(self.header['market_id'], self.query.max_age)
            if self.origin is not None and any(self.origin.get(k) != self.header.get(k)
                    for k in ('fid', 'market_id', 'station_name', 'system_name', 'observed_at')):
                self.origin = None
            self.coordinates = None
            self.reference = None
            if self.source.coordinates_path is not None:
                self.coordinates = self.stack.enter_context(closing(sqlite3.connect(
                    Path(self.source.coordinates_path).resolve().as_uri()+'?mode=ro', uri=True, timeout=.25)))
                self.coordinates.set_progress_handler(lambda: int(self.cancel.is_set()), 1000)
                from .ui.favorites_view import stored_coordinates
                self.reference = stored_coordinates(self.coordinates, self.header.get('system_address'),
                                                     self.header['system_name'])
            return self
        except BaseException:
            self.stack.close()
            raise

    def __exit__(self, *args):
        return self.stack.__exit__(*args)

    def target_count(self, now):
        self.check()
        self.now = now
        with self.store._transaction():
            if self.store._revision() != self.revision:
                raise StaleReadError('Recommendation market revision changed')
            if (self.count is not None and now >= self.count_time
                    and (self.deadline is None or now <= self.deadline)):
                return self.count
            self.memo.clear()
            self.evaluated.clear()
            low, high = self.store._range(self.query.max_age)
            sql = 'SELECT COUNT(*),MIN(observed_at) FROM current_markets WHERE observed_at<=?'
            args = [high]
            if low is not None:
                sql += ' AND observed_at>=?'
                args.append(low)
            sql += ' AND market_id<>?'
            args.append(self.header['market_id'].to_bytes(8, 'big'))
            if self.query.target is not None:
                sql += ' AND market_id=?'
                args.append(self.query.target.market_id.to_bytes(8, 'big'))
                if self.query.target.system_id64 is not None:
                    sql += ' AND system_address=?'
                    args.append(self.query.target.system_id64.to_bytes(8, 'big'))
            count, oldest = self.store._con.execute(sql, args).fetchone()
            self.count, self.count_time = count, now
            self.deadline = (_datetime(oldest)+self.query.max_age
                             if oldest is not None and self.query.max_age is not None else None)
            return count

    def _offer(self, candidate, item, now):
        from .pad_metadata import matching_pad
        h, v = candidate.header, candidate.commodity
        key = (h.system_address, h.system_name)
        if key not in self.distances:
            distance = None
            if self.coordinates is not None:
                from .ui.favorites_view import stored_coordinates
                target = stored_coordinates(self.coordinates, h.system_address, h.system_name)
                distance = self.reference.distance_to(target) if self.reference and target else None
            if self.header.get('system_address') is not None and h.system_address == self.header['system_address']:
                distance = 0.0
            self.distances[key] = distance
        rows = [] if v is None else [dict(commodity_id=v.commodity_id, symbol=v.symbol,
            commander_buy_price=v.commander_buy_price, commander_sell_price=v.commander_sell_price,
            supply=v.supply, demand=v.demand)]
        return local_offer(dict(commodities=rows, system_name=h.system_name, system_address=h.system_address,
            station_name=h.station_name, market_id=h.market_id, station_type=h.station_type or '',
            observed_at=h.observed_at.isoformat(),
            largest_pad=matching_pad(self.pads, h.market_id, h.station_name,
                                    h.system_name, h.system_address)), item, self.distances[key], now)

    def _candidates(self, item, now, *, identity_evidence=False, **filters):
        self.now = now
        if self.query.target is not None:
            target = self.query.target
            if 'market_ids' in filters and target.market_id not in filters['market_ids']:
                return
            filters['market_ids'] = (target.market_id,)
            if target.system_id64 is not None and not identity_evidence:
                filters['system_address'] = target.system_id64
        cursor = None
        while True:
            self.check()
            page = self.store.query_current_candidates(CommodityRef(item.get('commodity_id'), item['symbol']), max_age=self.query.max_age,
                cursor=cursor, limit=500, expected_revision=self.revision, **filters)
            for candidate in page.items:
                self.check()
                yield self._offer(candidate, item, now)
            cursor = page.next_cursor
            if cursor is None:
                break

    def evaluate(self, item, community, now, step, free, margin, query):
        self.check()
        key = commodity_key(item)
        select = (partial(best_supply_trade, target=local_offer(self.origin, item, 0.0, now))
                  if self.supply else best_trade)
        side = TradeSide.BUY if self.supply else TradeSide.SELL
        step.search_started = True
        previous = self.evaluated.get(key)
        if previous is not None and previous[0] is community and now >= previous[2] and (
                previous[3] is None or now <= previous[3]):
            result = previous[1]
            if result is not None and result.remote.provider == 'local_elite':
                return refresh_remote(result, now)
            return result
        if key not in self.memo:
            threshold = (None if self.supply else
                         math.ceil(Fraction(item['commander_buy_price']) * (100+Fraction(margin))/100))
            count = [0]
            def profitable():
                if threshold is not None and threshold >= 2**64:
                    return
                for offer in self._candidates(item, now, side=side, min_sell_price=threshold):
                    row = select(item, (offer,), self.header['market_id'], free, margin, query)
                    if row is not None:
                        count[0] += 1
                        yield row
            retained = nsmallest(101, profitable(), key=ranking)
            self.memo[key] = (retained, count[0])
        retained, count = self.memo[key]
        step.local_combinations_checked = self.count
        step.local_candidates = count
        step.local_completed = True
        # Reuse ranked local outcomes, but refresh retrieved_at like the legacy path.
        locals_ranked = [refresh_remote(r, now) for r in retained]
        ids = tuple(dict.fromkeys(o.market_id for o in community if type(o.market_id) is int and o.market_id > 0))
        local_overlaps = []
        for offset in range(0, len(ids), 500):
            local_overlaps.extend(self._candidates(item, now, market_ids=ids[offset:offset+500], identity_evidence=True))
        merged = merge_destinations(local_overlaps, community, now, query.max_age, diagnostics=step)
        overridden = {o.market_id for o in merged if o.provider == 'spansh'}
        if len(overridden) > 100:
            # Nonconforming providers remain correct without an unbounded cache.
            possible = (select(item, (o,), self.header['market_id'], free, margin, query)
                        for o in self._candidates(item, now, side=side)
                        if o.market_id not in overridden)
            local_best = min((r for r in possible if r is not None), key=ranking, default=None)
        else:
            local_best = next((r for r in locals_ranked if r.remote.market_id not in overridden), None)
        merged_best = select(item, merged, self.header['market_id'], free, margin, query)
        result = min((r for r in (local_best, merged_best) if r is not None), key=ranking, default=None)
        deadlines = []
        if query.max_age is not None:
            deadlines.extend(o.market_updated_at+query.max_age for o in community)
        deadlines.extend(o.market_updated_at for o in community if o.market_updated_at > now)
        self.evaluated[key] = (community, result, now, min(deadlines) if deadlines else None)
        return result
