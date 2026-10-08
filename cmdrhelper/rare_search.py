"""Catalogue origins in a radius, independent of transient market availability."""
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import logging
import sqlite3

from .commodity_master import all_commodities
from .commodity_origin import CommodityOrigin
from .market_candidates import local_offer, matches_location, merge_destinations
from .market_data import MarketOffer, MarketStatus, PadSize
from .pad_metadata import matching_pad, read_pad_metadata


@dataclass(frozen=True)
class RareDestination(CommodityOrigin):
    commodity_id: int | None = None
    commodity_symbol: str = ''
    largest_pad: PadSize | None = None
    confirmed: MarketOffer | None = None
    remembered_commodities: tuple = ()

    @property
    def system_id64(self):
        return self.system_address

    @property
    def is_fleet_carrier(self):
        # The catalogue identifies static origin stations; this is not a market claim.
        return 'carrier' in self.station_type.casefold()


@dataclass(frozen=True)
class RareSearchResult:
    rows: tuple = ()
    unresolved: tuple = ()
    status: MarketStatus = MarketStatus.OK
    lookup_ids: tuple = ()


def search_rare_origins(resolver, query, reference_address=None, *, source=None,
                        community=(), local_only=False, cancel=None, now=None):
    """Resolve each station once. Read each eligible market snapshot once, no network."""
    from .market_store import MarketStore
    from .trade_market_source import TradeReadCancelled
    now = now or datetime.now(timezone.utc)
    def check():
        if cancel is not None and cancel.is_set():
            raise TradeReadCancelled()
    check()
    origins = resolver.resolve_many(query.reference_system, reference_address)
    metadata = (source.pad_metadata(cancel) if source else
                read_pad_metadata(spansh_folder=resolver.spansh_folder, cancel=cancel))
    rows, unresolved, lookup_ids = [], set(), set()
    for master in all_commodities():
        if not master.rare:
            continue
        check()
        origin = origins.get(master.origin_market_id)
        if origin is None or not origin.station_name or origin.distance_ly is None:
            if origin is not None:
                unresolved.add(origin.market_id)
                if not origin.conflict and (not origin.station_name or origin.coordinates is None):
                    lookup_ids.add(origin.market_id)
            continue
        row = RareDestination(**vars(origin), commodity_id=master.frontier_id,
            commodity_symbol=master.symbol, remembered_commodities=(master.frontier_id,),
            largest_pad=matching_pad(metadata, origin.market_id,
                origin.station_name, origin.system_name, origin.system_address))
        if row.distance_ly <= query.radius_ly and (
                (query.required_pad != PadSize.ANY and row.largest_pad is None)
                or (query.max_distance_to_arrival_ls is not None and row.distance_to_arrival_ls is None)):
            lookup_ids.add(row.market_id)
        if matches_location(row, query):
            rows.append(row)
    snapshots = {}
    if source is not None and rows:
        try:
            cache = source.fallback_cache(cancel)
            ids = {row.market_id for row in rows}
            if cache is not None:
                snapshots = {s['market_id']: s for s in cache.shared(query.max_age) if s['market_id'] in ids}
            elif source.path is not None:
                with MarketStore(source.path, read_only=True, clock=lambda: now) as store:
                    for mid in ids:
                        check()
                        snapshot = store.get_current(mid, max_age=query.max_age)
                        if snapshot is not None:
                            snapshots[mid] = snapshot
        except (OSError, sqlite3.Error, RuntimeError, ValueError):
            # Unavailable market storage must not hide independently known origins.
            logging.getLogger(__name__).debug('Rare market evidence unavailable', exc_info=True)
    result = []
    for row in rows:
        check()
        snapshot = snapshots.get(row.market_id)
        local = [local_offer(snapshot, dict(commodity_id=row.commodity_id, symbol=row.commodity_symbol),
                             row.distance_ly, now)] if snapshot else []
        quotes = [o for o in community if not local_only and o.market_id == row.market_id
                  and o.commodity_id == row.commodity_id
                  and o.commodity_symbol.casefold() == row.commodity_symbol.casefold()]
        merged = merge_destinations(local, quotes, now, query.max_age)
        offer = next((o for o in merged if o.system_name.casefold() == row.system_name.casefold()
                      and o.station_name.casefold() == row.station_name.casefold()
                      and (o.system_id64 is None or row.system_id64 is None or o.system_id64 == row.system_id64)
                      and (not local_only or o.provider == 'local_elite')
                      and o.commander_buy_price is not None and o.commander_buy_price > 0
                      and o.supply is not None and o.supply > 0
                      and (query.include_fleet_carriers or o.is_fleet_carrier is not True)), None)
        result.append(replace(row, confirmed=offer))
    result.sort(key=lambda r: (r.distance_ly, r.system_name, r.station_name, r.commodity_symbol))
    return RareSearchResult(tuple(result), tuple(sorted(unresolved)), lookup_ids=tuple(sorted(lookup_ids)))
