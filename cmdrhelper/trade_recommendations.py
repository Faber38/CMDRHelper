"""Transient single-leg recommendations. Buy locally; compare destination timestamps."""
from dataclasses import dataclass, replace, field
from datetime import datetime, timezone
from fractions import Fraction
from threading import Event

from .commodity_master import lookup_by_id, lookup_by_symbol
from .market_data import MarketOffer, MarketSearchResult, MarketStatus, ProviderDiagnostics
from .observed_market_cache import ObservedMarketCache
from .market_candidates import commodity_key, local_offer, merge_destinations, matches_location
from .recommendation_diagnostics import (RecommendationDiagnostics, CommodityStep,
    CommodityIdentity, PartialReason, STATUS_REASONS)


@dataclass(frozen=True)
class Recommendation:
    # Keep the complete destination for future route actions; no route integration.
    destination: MarketOffer
    buy_price: int
    quantity: int

    @property
    def profit_per_ton(self):
        return self.destination.commander_sell_price - self.buy_price

    @property
    def profit_percent(self):
        return Fraction(100 * self.profit_per_ton, self.buy_price)

    @property
    def total_profit(self):
        return self.profit_per_ton * self.quantity

    @property
    def purchase_cost(self):
        return self.buy_price * self.quantity

    @property
    def sale_revenue(self):
        return self.destination.commander_sell_price * self.quantity


@dataclass(frozen=True)
class RecommendationResult:
    rows: tuple[Recommendation, ...] = ()
    checked: int = 0
    total: int = 0
    partial: bool = False
    cancelled: bool = False
    cache_hits: int = 0
    diagnostics: RecommendationDiagnostics | None = field(default=None, compare=False)


def buyable(snapshot):
    return [r for r in snapshot['commodities'] if r['commander_buy_price'] > 0 and r['supply'] > 0]

def eligible(offer, query):
    return (offer.commander_sell_price is not None and offer.commander_sell_price > 0
            and offer.demand is not None and offer.demand > 0
            and matches_location(offer, query))


def ranking(row):
    o = row.destination
    return (-row.total_profit, -o.market_updated_at.timestamp(), o.distance_ly,
            o.distance_to_arrival_ls if o.distance_to_arrival_ls is not None else float('inf'),
            o.station_name.casefold(), o.system_name.casefold(), o.market_id)


def best_trade(commodity, targets, origin_id, free, margin, query, *, diagnostics=None):
    matches = []
    buy = commodity['commander_buy_price']
    if buy <= 0 or free <= 0:
        return None
    for offer in targets:
        if offer.market_id == origin_id or not eligible(offer, query):
            continue
        if (offer.commodity_id, offer.commodity_symbol.casefold()) != commodity_key(commodity):
            continue
        quantity = min(free, commodity['supply'], offer.demand)
        row = Recommendation(offer, buy, quantity)
        if quantity > 0 and row.profit_percent >= margin:
            matches.append(row)
            if diagnostics is not None:
                diagnostics.local_candidates += 1
    return min(matches, key=ranking) if matches else None


def search_recommendations(origin, local_markets, distances, free, margin, query, provider,
                           *, cancel=None, progress=None, clock=lambda: datetime.now(timezone.utc),
                           diagnostics=None, diagnostic_progress=None, local_only=False):
    """Evaluate locals first, then ONE sequential sell query per known buyable item.

    Use the existing provider's lock, request spacing, page bounds and RAM cache.
    Unknown future commodities are evaluated locally without pointless HTTP calls.
    Results are best within this bounded search, never a claim of global optimum.
    """
    cancel = cancel or Event()
    diagnostic = diagnostics if diagnostics is not None else RecommendationDiagnostics()
    diagnostic.local_only = local_only

    def publish():
        if diagnostic_progress:
            diagnostic_progress(diagnostic.snapshot())

    def output(rows=(), checked=0, total=0, partial=False, cancelled=False, cache_hits=0,
               *, final=True, reason=None):
        diagnostic.partial = partial
        diagnostic.local_recommendations = sum(r.destination.provider == 'local_elite' for r in rows)
        if cancelled:
            reason = getattr(cancel, 'reason', PartialReason.CANCELLED)
        snapshot = (diagnostic.finish(partial=partial, cancelled=cancelled, reason=reason)
                    if final else diagnostic.snapshot())
        return RecommendationResult(rows, checked, total, partial, cancelled, cache_hits, snapshot)

    if origin.get('source') != 'local_elite':
        return output()
    items = buyable(origin)
    diagnostic.steps = [CommodityStep(CommodityIdentity(i.get('commodity_id'), i['symbol'])) for i in items]
    diagnostic.aggregate()
    quotes = {}
    checked, partial, cache_hits = 0, False, 0

    def calculate():
        now = clock()
        if not ObservedMarketCache.is_valid(origin, now, query.max_age):
            return ()
        rows = []
        diagnostic.local_target_markets = len({s['market_id'] for s in local_markets
            if s['market_id'] != origin['market_id'] and s['fid'] == origin['fid']
            and s['source'] == 'local_elite' and ObservedMarketCache.is_valid(s, now, query.max_age)})
        for item_index, (item, step) in enumerate(zip(items, diagnostic.steps), 1):
            if local_only and cancel.is_set():
                return ()
            step.search_started = True
            local = [local_offer(s, item, distances.get(s['market_id']), now) for s in local_markets
                     if s['fid'] == origin['fid'] and s['source'] == 'local_elite'
                     and ObservedMarketCache.is_valid(s, now, query.max_age)]
            targets = [o for o in local if o.market_id != origin['market_id']]
            step.local_combinations_checked = len(targets)
            step.local_candidates = 0
            # Diagnostic-only count, using exactly the existing eligibility/formula.
            best_trade(item, targets, origin['market_id'], free, margin, query, diagnostics=step)
            step.local_completed = True
            try:
                merged = merge_destinations(local, quotes.get(commodity_key(item), ()), now,
                                            query.max_age, diagnostics=step)
            except Exception:
                diagnostic.merge_errors += 1
                diagnostic.reason(PartialReason.OTHER, step)
                raise
            row = best_trade(item, merged, origin['market_id'], free, margin, query)
            if row is not None:
                rows.append(row)
            if local_only:
                step.checked = step.successful = True
                diagnostic.current_commodity = diagnostic.last_completed_commodity = step.commodity
                if progress and not cancel.is_set():
                    progress(output(tuple(sorted(rows, key=ranking)),
                                    item_index, len(items), final=False))
        return tuple(sorted(rows, key=ranking))

    if type(free) is not int or free <= 0 or not 0 <= margin <= 1000:
        return output()
    if local_only:
        if cancel.is_set():
            return output(cancelled=True)
        if not ObservedMarketCache.is_valid(origin, clock(), query.max_age):
            return output(partial=True, reason=PartialReason.CONTEXT_CHANGED)
        if progress:
            progress(output((), 0, len(items), final=False))
        rows = calculate()
        if cancel.is_set():
            return output(cancelled=True)
        if not ObservedMarketCache.is_valid(origin, clock(), query.max_age):
            return output(partial=True, reason=PartialReason.CONTEXT_CHANGED)
        return output(rows, len(items), len(items))
    if progress and not cancel.is_set():
        progress(output(calculate(), 0, len(items), final=False))
    for item, step in zip(items, diagnostic.steps):
        if cancel.is_set():
            return output(cancelled=True)
        if not ObservedMarketCache.is_valid(origin, clock(), query.max_age):
            return output(partial=True, reason=PartialReason.CONTEXT_CHANGED)
        step.search_started = True
        diagnostic.current_commodity = step.commodity
        master = lookup_by_id(item.get('commodity_id')) or lookup_by_symbol(item['symbol'])
        if master is None:
            partial = True
            step.failed = True
            diagnostic.reason(PartialReason.COMMODITY_ERROR, step)
        else:
            q = replace(query, commodity=master.frontier_id, minimum_quantity=1, limit=100)
            step.spansh_started = True
            publish()
            try:
                result = provider.search_sell(q, cancel=cancel)
            except Exception as exc:
                diagnostic.reason(PartialReason.COMMODITY_ERROR, step)
                result = MarketSearchResult(MarketStatus.INVALID_RESPONSE, query=q,
                                            diagnostics=getattr(exc, 'market_diagnostics', None))
            step.spansh_completed = True
            step.provider_status = result.status
            step.truncated = result.truncated
            step.provider = result.diagnostics or ProviderDiagnostics(
                cache_hits=int(result.from_cache), last_http_status=result.http_status,
                retry_after=result.retry_after)
            if cancel.is_set() or result.status == MarketStatus.CANCELLED:
                return output(cancelled=True)
            step.checked = True
            step.successful = result.status in (MarketStatus.OK, MarketStatus.NO_RESULTS) and not result.truncated
            step.failed = result.status not in (MarketStatus.OK, MarketStatus.NO_RESULTS)
            diagnostic.last_completed_commodity = step.commodity
            if step.failed:
                diagnostic.reason(STATUS_REASONS.get(result.status, PartialReason.OTHER), step)
            if result.truncated:
                if step.provider.page_limit_reached:
                    diagnostic.reason(PartialReason.PROVIDER_PAGE_LIMIT, step)
                if step.provider.result_limit_reached:
                    diagnostic.reason(PartialReason.PROVIDER_RESULT_LIMIT, step)
                if not (step.provider.page_limit_reached or step.provider.result_limit_reached):
                    diagnostic.reason(PartialReason.PROVIDER_TRUNCATED, step)
            quotes[commodity_key(item)] = result.offers
            cache_hits += int(result.from_cache)
            partial |= result.truncated or result.status not in (MarketStatus.OK, MarketStatus.NO_RESULTS)
            if result.status in (MarketStatus.RATE_LIMIT, MarketStatus.UNKNOWN_SYSTEM,
                                 MarketStatus.NETWORK_ERROR, MarketStatus.TIMEOUT, MarketStatus.HTTP_ERROR):
                return output(calculate(), checked + 1, len(items), partial=True,
                                            cache_hits=cache_hits)
        checked += 1
        step.checked = True
        diagnostic.last_completed_commodity = step.commodity
        diagnostic.partial = partial
        if progress and not cancel.is_set():
            progress(output(calculate(), checked, len(items), partial, cache_hits=cache_hits, final=False))
    if cancel.is_set():
        return output(cancelled=True)
    return output(calculate(), checked, len(items), partial, cache_hits=cache_hits)
