"""Transient single-leg recommendations with a fixed local buying or selling market."""
from dataclasses import dataclass, replace, field
from datetime import datetime, timezone
from fractions import Fraction
from functools import partial as bind
from threading import Event
from time import monotonic

from .commodity_master import lookup_by_id, lookup_by_symbol
from .market_data import MarketOffer, MarketSearchResult, MarketStatus, ProviderDiagnostics
from .observed_market_cache import ObservedMarketCache, shared_current
from .market_candidates import commodity_key, local_offer, merge_destinations, matches_location
from .recommendation_diagnostics import (RecommendationDiagnostics, CommodityStep,
    CommodityIdentity, PartialReason, STATUS_REASONS)


class TradeAmounts:
    """Shared arithmetic; the concrete result defines both price roles."""
    @property
    def profit_per_ton(self):
        return self.sell_price - self.buy_price

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
        return self.sell_price * self.quantity


@dataclass(frozen=True)
class Recommendation(TradeAmounts):
    # Keep the complete destination for future route actions; no route integration.
    destination: MarketOffer
    buy_price: int
    quantity: int

    @property
    def sell_price(self):
        return self.destination.commander_sell_price

    @property
    def remote(self):
        return self.destination


@dataclass(frozen=True)
class SupplyRecommendation(TradeAmounts):
    source: MarketOffer
    target: MarketOffer
    quantity: int

    @property
    def buy_price(self):
        return self.source.commander_buy_price

    @property
    def sell_price(self):
        return self.target.commander_sell_price

    @property
    def remote(self):
        return self.source


def refresh_remote(row, now):
    """Refresh local retrieval metadata without changing fixed-market evidence."""
    field_name = 'source' if isinstance(row, SupplyRecommendation) else 'destination'
    return replace(row, **{field_name: replace(row.remote, retrieved_at=now)})


@dataclass(frozen=True)
class RecommendationResult:
    rows: tuple[Recommendation | SupplyRecommendation, ...] = ()
    checked: int = 0
    total: int = 0
    partial: bool = False
    cancelled: bool = False
    cache_hits: int = 0
    diagnostics: RecommendationDiagnostics | None = field(default=None, compare=False)


def buyable(snapshot):
    return [r for r in snapshot['commodities'] if r['commander_buy_price'] > 0 and r['supply'] > 0]

def demanded(snapshot):
    return [r for r in snapshot['commodities'] if r['commander_sell_price'] > 0 and r['demand'] > 0]


def eligible(offer, query):
    return (offer.commander_sell_price is not None and offer.commander_sell_price > 0
            and offer.demand is not None and offer.demand > 0
            and matches_location(offer, query))


def ranking(row):
    o = row.remote
    return (-row.total_profit, -o.market_updated_at.timestamp(), o.distance_ly,
            o.distance_to_arrival_ls if o.distance_to_arrival_ls is not None else float('inf'),
            o.station_name.casefold(), o.system_name.casefold(), o.market_id)


def best_trade(commodity, targets, origin_id, free, margin, query, *, diagnostics=None):
    return _best_trade(commodity, targets, origin_id, free, margin, query, diagnostics=diagnostics)


def best_supply_trade(commodity, sources, target_id, free, margin, query, *, target, diagnostics=None):
    return _best_trade(commodity, sources, target_id, free, margin, query,
                       target=target, diagnostics=diagnostics)


def _best_trade(commodity, offers, fixed_id, free, margin, query, *, target=None, diagnostics=None):
    matches = []
    fixed_price = commodity['commander_buy_price' if target is None else 'commander_sell_price']
    if fixed_price <= 0 or free <= 0:
        return None
    for offer in offers:
        if offer.market_id == fixed_id:
            continue
        valid = (eligible(offer, query) if target is None else
                 offer.commander_buy_price is not None and offer.commander_buy_price > 0
                 and offer.supply is not None and offer.supply > 0 and matches_location(offer, query))
        if not valid:
            continue
        if (offer.commodity_id, offer.commodity_symbol.casefold()) != commodity_key(commodity):
            continue
        quantity = (min(free, commodity['supply'], offer.demand) if target is None else
                    min(free, offer.supply, commodity['demand']))
        row = (Recommendation(offer, fixed_price, quantity) if target is None else
               SupplyRecommendation(offer, target, quantity))
        if quantity > 0 and row.profit_percent >= margin and (target is None or row.profit_per_ton > 0):
            matches.append(row)
            if diagnostics is not None:
                diagnostics.local_candidates += 1
    return min(matches, key=ranking) if matches else None


def search_recommendations(origin, local_markets, distances, free, margin, query, provider,
                           *, cancel=None, progress=None, clock=lambda: datetime.now(timezone.utc),
                           diagnostics=None, diagnostic_progress=None, local_only=False, local_evaluator=None,
                           progress_interval=0):
    """Buy at the current market; preserve the existing outward recommendations."""
    return _search_recommendations(origin, local_markets, distances, free, margin, query, provider,
        cancel=cancel, progress=progress, clock=clock, diagnostics=diagnostics,
        diagnostic_progress=diagnostic_progress, local_only=local_only,
        local_evaluator=local_evaluator, progress_interval=progress_interval)


def search_supply_recommendations(target, local_markets, distances, free, margin, query, provider,
                                  *, quantity=None, **kwargs):
    """Find one best source per demanded commodity for this fixed local target.

    Each row is an alternative, not an allocation in a combined cargo plan.
    """
    if target is not None:
        query = replace(query, reference_system=target['system_name'])
    if quantity is not None:
        if type(quantity) is not int or quantity <= 0 or type(free) is not int:
            free = 0
        else:
            free = min(free, quantity)
    return _search_recommendations(target, local_markets, distances, free, margin, query, provider,
                                   supply=True, **kwargs)


def _search_recommendations(origin, local_markets, distances, free, margin, query, provider,
                           *, cancel=None, progress=None, clock=lambda: datetime.now(timezone.utc),
                           diagnostics=None, diagnostic_progress=None, local_only=False, local_evaluator=None,
                           progress_interval=0, supply=False):
    """Evaluate locals first, then one sequential provider query per relevant item.

    Use the existing provider's lock, request spacing, page bounds and RAM cache.
    Unknown future commodities are evaluated locally without pointless HTTP calls.
    Results are best within this bounded search, never a claim of global optimum.
    """
    local_markets = shared_current(local_markets, clock())
    if query.target is not None:
        # Keep newer same-MarketID evidence even if its system has changed:
        # it must suppress stale community quotes before location filtering.
        local_markets = tuple(s for s in local_markets if s['market_id'] == query.target.market_id)
    cancel = cancel or Event()
    diagnostic = diagnostics if diagnostics is not None else RecommendationDiagnostics()
    diagnostic.local_only = local_only

    last_progress = [float('-inf')]
    def due():
        tick = monotonic()
        if tick - last_progress[0] < progress_interval:
            return False
        last_progress[0] = tick
        return True

    provider_announced = [False]
    def publish():
        if diagnostic_progress and (not provider_announced[0] or due()):
            provider_announced[0] = True
            diagnostic_progress(diagnostic.snapshot())

    def output(rows=(), checked=0, total=0, partial=False, cancelled=False, cache_hits=0,
               *, final=True, reason=None):
        if supply and origin is not None and not ObservedMarketCache.is_valid(origin, clock(), query.max_age):
            rows, partial, reason = (), True, PartialReason.CONTEXT_CHANGED
        diagnostic.partial = partial
        diagnostic.local_recommendations = sum(r.remote.provider == 'local_elite' for r in rows)
        if cancelled:
            reason = getattr(cancel, 'reason', PartialReason.CANCELLED)
        snapshot = (diagnostic.finish(partial=partial, cancelled=cancelled, reason=reason)
                    if final else diagnostic.snapshot())
        return RecommendationResult(rows, checked, total, partial, cancelled, cache_hits, snapshot)

    if supply and (origin is None or not ObservedMarketCache.is_valid(origin, clock(), query.max_age)):
        return output(partial=True, reason=PartialReason.CONTEXT_CHANGED)
    if origin.get('source') != 'local_elite':
        return output()
    items = demanded(origin) if supply else buyable(origin)
    diagnostic.steps = [CommodityStep(CommodityIdentity(i.get('commodity_id'), i['symbol'])) for i in items]
    diagnostic.aggregate()
    quotes = {}
    checked, partial, cache_hits = 0, False, 0

    def calculate():
        now = clock()
        if not ObservedMarketCache.is_valid(origin, now, query.max_age):
            return ()
        rows = []
        diagnostic.local_target_markets = (local_evaluator.target_count(now) if local_evaluator is not None else len({s['market_id'] for s in local_markets
            if s['market_id'] != origin['market_id']
            and s['source'] == 'local_elite' and ObservedMarketCache.is_valid(s, now, query.max_age)}))
        for item_index, (item, step) in enumerate(zip(items, diagnostic.steps), 1):
            if local_only and cancel.is_set():
                return ()
            step.search_started = True
            select = (bind(best_supply_trade, target=local_offer(origin, item, 0.0, now))
                      if supply else best_trade)
            if local_evaluator is not None:
                row = local_evaluator.evaluate(item, quotes.get(commodity_key(item), ()), now,
                                               step, free, margin, query)
            else:
                local = [local_offer(s, item, distances.get(s['market_id']), now) for s in local_markets
                         if s['source'] == 'local_elite'
                         and ObservedMarketCache.is_valid(s, now, query.max_age)]
                targets = [o for o in local if o.market_id != origin['market_id']]
                step.local_combinations_checked = len(targets)
                step.local_candidates = 0
                # Diagnostic-only count, using exactly the existing eligibility/formula.
                select(item, targets, origin['market_id'], free, margin, query, diagnostics=step)
                step.local_completed = True
                try:
                    merged = merge_destinations(local, quotes.get(commodity_key(item), ()), now,
                                                query.max_age, diagnostics=step)
                except Exception:
                    diagnostic.merge_errors += 1
                    diagnostic.reason(PartialReason.OTHER, step)
                    raise
                row = select(item, merged, origin['market_id'], free, margin, query)
            if row is not None:
                rows.append(row)
            if local_only:
                step.checked = step.successful = True
                diagnostic.current_commodity = diagnostic.last_completed_commodity = step.commodity
                if progress and not cancel.is_set() and due():
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
    if progress and not cancel.is_set() and due():
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
                search = provider.search_buy if supply else provider.search_sell
                result = search(q, cancel=cancel)
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
            quotes[commodity_key(item)] = (result.offers if query.target is None else
                tuple(o for o in result.offers if query.target.matches(o)))
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
        if progress and not cancel.is_set() and due():
            progress(output(calculate(), checked, len(items), partial, cache_hits=cache_hits, final=False))
    if cancel.is_set():
        return output(cancelled=True)
    return output(calculate(), checked, len(items), partial, cache_hits=cache_hits)
