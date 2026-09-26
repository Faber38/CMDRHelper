"""Combine local observations with the existing bounded, RAM-only provider search."""
from dataclasses import replace
from datetime import datetime, timezone

from .commodity_master import lookup_by_id, lookup_by_symbol
from .market_candidates import local_offer, merge_destinations, matches_location
from .market_data import MarketSearchResult, MarketStatus, TradeSide
from .observed_market_cache import ObservedMarketCache


def search_trade(provider, query, side, local_markets=(), distances=None, fid='', *,
                 cancel=None, clock=lambda: datetime.now(timezone.utc)):
    search = provider.search_buy if side == TradeSide.BUY else provider.search_sell
    try:
        result = search(query, cancel=cancel)
    except Exception:
        result = MarketSearchResult(MarketStatus.INVALID_RESPONSE, query=query)
    if (cancel is not None and cancel.is_set()) or result.status == MarketStatus.CANCELLED:
        return MarketSearchResult(MarketStatus.CANCELLED, query=query)
    if result.status == MarketStatus.INVALID_QUERY:
        return result
    now = clock()
    master = (lookup_by_id(query.commodity) if isinstance(query.commodity, int)
              else lookup_by_symbol(query.commodity))
    if master is None:
        return result
    commodity = dict(commodity_id=master.frontier_id, symbol=master.symbol)
    local = [local_offer(s, commodity, (distances or {}).get(s['market_id']), now)
             for s in local_markets if fid and s['fid'] == fid and s['source'] == 'local_elite'
             and ObservedMarketCache.is_valid(s, now, query.max_age)]
    failed = result.status not in (MarketStatus.OK, MarketStatus.NO_RESULTS)
    # As with recommendations, a newer observed empty/non-trading market must
    # supersede an old quote, before price/quantity/location eligibility is tested.
    merged = merge_destinations(local, () if failed else result.offers, now, query.max_age)
    offers = []
    for offer in merged:
        price, amount = ((offer.commander_sell_price, offer.demand) if side == TradeSide.SELL
                         else (offer.commander_buy_price, offer.supply))
        if (offer.commodity_id == master.frontier_id
                and offer.commodity_symbol.casefold() == master.symbol.casefold()
                and price is not None and price > 0
                and amount is not None and amount >= (query.minimum_quantity or 1)
                and matches_location(offer, query)):
            offers.append(offer)
    offers.sort(key=lambda o: ((-o.commander_sell_price if side == TradeSide.SELL else o.commander_buy_price),
                              -o.market_updated_at.timestamp(), o.distance_ly,
                              o.station_name, o.system_name, o.market_id))
    if failed and not offers:
        return result
    limit = min(100, query.limit)
    return replace(result, status=MarketStatus.OK if offers else MarketStatus.NO_RESULTS,
                   offers=tuple(offers[:limit]), query=query,
                   truncated=result.truncated or len(offers) > limit,
                   community_failure=result.status if failed else None)
