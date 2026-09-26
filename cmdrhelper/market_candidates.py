"""Shared local snapshots and timestamp-based MarketID selection."""

from .market_data import MarketOffer, PadSize, within_market_age
from .observed_market_cache import timestamp


def commodity_key(row):
    return (row.get('commodity_id'), row['symbol'].casefold())


def local_offer(snapshot, commodity, distance, now):
    """A missing/non-buying commodity still supersedes older quotes for this market.

    Phase-6 snapshots do not contain pad or arrival metadata. Never infer them
    from station type. Unknown distance/type remains unknown, not zero/false.
    """
    row = next((r for r in snapshot['commodities'] if commodity_key(r) == commodity_key(commodity)), {})
    kind = snapshot.get('station_type', '')
    return MarketOffer(commodity.get('commodity_id'), commodity['symbol'], commodity['symbol'],
                       snapshot['system_name'], snapshot.get('system_address'),
                       snapshot['station_name'], snapshot['market_id'], kind,
                       distance, None, None, ('carrier' in kind.casefold()) if kind else None,
                       None, row.get('commander_buy_price'), row.get('commander_sell_price', 0),
                       row.get('supply'), row.get('demand', 0), timestamp(snapshot['observed_at']),
                       now, 'local_elite')


def merge_destinations(local, community, now, max_age, *, diagnostics=None):
    """Newest valid quote per MarketID BEFORE profitability/quantity/metadata filters.

    Equal timestamps prefer the witnessed local quote; this is only a tie-break.
    No name-based fallback. Spansh already rejects missing/nonpositive MarketIDs.
    """
    markets = {}
    if diagnostics is not None:
        for name in ('overlapping_market_ids', 'local_won_freshness',
                     'spansh_won_freshness', 'equal_timestamp_merges'):
            setattr(diagnostics, name, 0)
    for offer in (*community, *local):
        if type(offer.market_id) is not int or offer.market_id <= 0:
            continue
        stamp = offer.market_updated_at
        if stamp.tzinfo is None or offer.provider not in ('local_elite', 'spansh'):
            continue
        age = now - stamp
        if not within_market_age(age, max_age):
            continue
        previous = markets.get(offer.market_id)
        if diagnostics is not None and previous is not None and previous.provider != offer.provider:
            diagnostics.overlapping_market_ids += 1
            if stamp == previous.market_updated_at:
                diagnostics.equal_timestamp_merges += 1
            else:
                winner = offer if stamp > previous.market_updated_at else previous
                if winner.provider == 'local_elite':
                    diagnostics.local_won_freshness += 1
                else:
                    diagnostics.spansh_won_freshness += 1
        if previous is None or stamp > previous.market_updated_at or (
                stamp == previous.market_updated_at and offer.provider == 'local_elite'):
            markets[offer.market_id] = offer
    return tuple(markets.values())


def matches_location(offer, query):
    ranks = {None: 0, PadSize.ANY: 0, PadSize.SMALL: 1, PadSize.MEDIUM: 2, PadSize.LARGE: 3}
    return (offer.distance_ly is not None and 0 <= offer.distance_ly <= query.radius_ly
            and (query.include_fleet_carriers or offer.is_fleet_carrier is False)
            and ranks.get(offer.largest_pad, 0) >= ranks[query.required_pad]
            and (query.max_distance_to_arrival_ls is None or offer.distance_to_arrival_ls is not None
                 and 0 <= offer.distance_to_arrival_ls <= query.max_distance_to_arrival_ls))
