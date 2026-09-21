"""Synthetic single-leg recommendations; no live market/network data."""
from dataclasses import replace
from datetime import timedelta
from fractions import Fraction
from threading import Event
import unittest

from cmdrhelper.commodity_master import lookup_by_symbol
from cmdrhelper.market_data import MarketOffer, MarketSearch, MarketSearchResult, MarketStatus, PadSize
from cmdrhelper.trade_recommendations import (buyable, local_offer, merge_destinations, best_trade,
                                             search_recommendations, Recommendation, ranking)
from test_observed_market_cache import NOW, FID, snapshot

BEER = lookup_by_symbol('Beer')
GOLD = lookup_by_symbol('Gold')


def item(master=BEER, buy=10000, supply=1200, sell=11500, demand=190):
    return dict(commodity_id=master.frontier_id, symbol=master.symbol,
                commander_buy_price=buy, commander_sell_price=sell, supply=supply, demand=demand)


def market(mid=1, stamp=NOW, fid=FID, rows=None, **changes):
    result = snapshot(stamp, mid=mid, fid=fid)
    result.update(system_address=100, station_type='Coriolis', commodities=[item()] if rows is None else rows)
    result.update(changes)
    return result


def offer(mid=2, master=BEER, stamp=NOW, **changes):
    result = MarketOffer(master.frontier_id, master.symbol, master.english_name,
        'Synthetic Target', 200, 'Synthetic Port', mid, 'Coriolis', 10, 200,
        PadSize.LARGE, False, None, 0, 11500, 0, 190, stamp, NOW, 'spansh')
    return replace(result, **changes)


class Provider:
    def __init__(self, results=None):
        self.queries = []
        self.results = results or {}
    def search_sell(self, q, *, cancel):
        self.queries.append(q)
        value = self.results.get(q.commodity, MarketSearchResult(MarketStatus.NO_RESULTS))
        if isinstance(value, Exception):
            raise value
        return value


class RecommendationTests(unittest.TestCase):
    def setUp(self):
        self.query = MarketSearch(BEER.frontier_id, 'Fixture System')

    def best(self, targets=None, commodity=None, **changes):
        args = dict(commodity=commodity or item(), targets=targets or [offer()], origin_id=1,
                    free=280, margin=10, query=self.query)
        args.update(changes)
        return best_trade(**args)

    def search(self, origin=None, locals=(), provider=None, **changes):
        args = dict(origin=origin or market(), local_markets=locals,
                    distances={s['market_id']: 5 for s in locals}, free=280, margin=10,
                    query=self.query, provider=provider or Provider(), clock=lambda: NOW)
        args.update(changes)
        return search_recommendations(**args)

    def test_exact_margin_boundary_and_formulas(self):
        self.assertIsNone(self.best([offer(commander_sell_price=10999)]))
        row = self.best([offer(commander_sell_price=11000)])
        self.assertEqual(row.profit_percent, Fraction(10))
        self.assertEqual(row.profit_per_ton, 1000)
        self.assertEqual(row.quantity, 190)
        self.assertEqual(row.total_profit, 190000)
        self.assertEqual(row.purchase_cost, 1900000)
        self.assertEqual(row.sale_revenue, 2090000)
        self.assertEqual(self.best().profit_percent, 15)
        self.assertIsNone(self.best(margin=20))
        for price in (0, 9000, 10000):
            self.assertIsNone(self.best([offer(commander_sell_price=price)]))
        self.assertIsNotNone(self.best([offer(commander_sell_price=10000)], margin=0))

    def test_quantity_all_three_limits(self):
        for free, supply, demand, expected in ((280,1200,190,190),(280,150,20000,150),(20,100,100,20)):
            self.assertEqual(self.best([offer(demand=demand)],item(supply=supply),free=free).quantity,expected)
        for free, supply, demand in ((0,100,100),(100,0,100),(100,100,0)):
            self.assertIsNone(self.best([offer(demand=demand)],item(supply=supply),free=free))

    def test_only_locally_buyable_and_current_market_not_target(self):
        origin=market(rows=[item(),item(GOLD,buy=0),dict(item(),supply=0)])
        self.assertEqual(len(buyable(origin)),1)
        self.assertIsNone(self.best([offer(mid=1)]))
        self.assertIsNone(self.best(commodity=item(buy=0)))

    def test_second_local_target_and_unknown_future_commodity(self):
        result=self.search(locals=[market(mid=2)])
        self.assertEqual(len(result.rows),1)
        self.assertEqual(result.rows[0].destination.provider,'local_elite')
        unknown=dict(item(),commodity_id=199999999,symbol='$future_fixture_name;')
        provider=Provider()
        result=self.search(market(rows=[unknown]),[market(mid=2,rows=[unknown])],provider)
        self.assertEqual(len(result.rows),1)
        self.assertFalse(provider.queries)
        self.assertTrue(result.partial)

    def test_fid_source_and_local_ttl(self):
        for target in (market(mid=2,fid='F_OTHER'),market(mid=2,source='spansh'),
                       market(mid=2,stamp=NOW-timedelta(hours=24))):
            self.assertFalse(self.search(locals=[target]).rows)
        self.assertTrue(self.search(locals=[market(mid=2,stamp=NOW-timedelta(hours=24,seconds=-1))]).rows)
        self.assertFalse(self.search(origin=market(stamp=NOW-timedelta(hours=24)),locals=[market(mid=2)]).rows)

    def test_local_missing_metadata_and_distance(self):
        target=market(mid=2)
        for query,dist in ((self.query,None),(self.query,101),
                (replace(self.query,required_pad=PadSize.SMALL),5),
                (replace(self.query,max_distance_to_arrival_ls=500),5)):
            self.assertFalse(self.search(locals=[target],query=query,distances={2:dist}).rows)
        for kind in ('FleetCarrier',''):
            target=market(mid=2,station_type=kind)
            self.assertFalse(self.search(locals=[target]).rows)
            self.assertTrue(self.search(locals=[target],query=replace(self.query,include_fleet_carriers=True)).rows)

    def test_spansh_filters(self):
        for changes in ({'distance_ly':101},{'demand':0},{'commander_sell_price':0},
                        {'is_fleet_carrier':True},{'distance_ly':None}):
            self.assertIsNone(self.best([offer(**changes)]))
        self.assertIsNone(self.best([offer(largest_pad=PadSize.SMALL)],
                         query=replace(self.query,required_pad=PadSize.LARGE)))
        self.assertIsNone(self.best([offer(distance_to_arrival_ls=None)],
                         query=replace(self.query,max_distance_to_arrival_ls=1000)))
        self.assertIsNone(self.best([offer(distance_to_arrival_ls=1001)],
                         query=replace(self.query,max_distance_to_arrival_ls=1000)))

    def test_merge_newer_source_and_timestamp_tie(self):
        local=offer(provider='local_elite',stamp=NOW-timedelta(minutes=8))
        remote=offer(stamp=NOW-timedelta(hours=6))
        for a,b,winner in ((local,remote,local),(replace(local,market_updated_at=NOW-timedelta(hours=2)),
             replace(remote,market_updated_at=NOW-timedelta(minutes=15)),None)):
            rows=merge_destinations([a],[b],NOW,timedelta(hours=24))
            self.assertEqual(len(rows),1)
            self.assertEqual(rows[0],winner or b)
        remote=replace(remote,market_updated_at=local.market_updated_at,retrieved_at=NOW+timedelta(days=2))
        self.assertEqual(merge_destinations([local],[remote],NOW,timedelta(hours=24)),(local,))
        self.assertEqual(merge_destinations([], [remote],NOW,timedelta(hours=24)),(remote,))
        self.assertEqual(merge_destinations([local],[],NOW,timedelta(hours=24)),(local,))

    def test_invalid_identity_timestamps_and_source_discarded(self):
        for changes in ({'market_id':None},{'market_id':0},{'market_id':True},
                        {'market_updated_at':NOW.replace(tzinfo=None)},
                        {'market_updated_at':NOW+timedelta(seconds=1)},
                        {'market_updated_at':NOW-timedelta(hours=25)}, {'provider':'other'}):
            self.assertFalse(merge_destinations([], [offer(**changes)],NOW,timedelta(hours=24)))
        self.assertFalse(merge_destinations([offer(provider='local_elite',stamp=NOW-timedelta(hours=24))],
                                            [],NOW,timedelta(days=7)))

    def test_newer_zero_demand_or_missing_local_row_supersedes_old_spansh(self):
        provider=Provider({BEER.frontier_id:MarketSearchResult(MarketStatus.OK,(offer(stamp=NOW-timedelta(hours=1)),))})
        for rows in ([],[item(demand=0)],[item(sell=0)]):
            self.assertFalse(self.search(locals=[market(mid=2,rows=rows)],provider=provider).rows)

    def test_best_total_not_best_unit_price_and_one_per_commodity(self):
        low=offer(mid=2,commander_sell_price=11000,demand=280)
        high=offer(mid=3,commander_sell_price=15000,demand=1)
        self.assertEqual(self.best([high,low]).destination.market_id,2)
        provider=Provider({BEER.frontier_id:MarketSearchResult(MarketStatus.OK,(high,low)),
                           GOLD.frontier_id:MarketSearchResult(MarketStatus.OK,(offer(mid=4,master=GOLD),))})
        result=self.search(origin=market(rows=[item(),item(GOLD)]),provider=provider)
        self.assertEqual(len(result.rows),2)
        self.assertEqual(len({r.destination.commodity_id for r in result.rows}),2)

    def test_tiebreaks_in_order(self):
        a=offer(mid=2)
        variants=[replace(a,market_id=3,market_updated_at=NOW-timedelta(seconds=1)),
                  replace(a,market_id=3,distance_ly=11),
                  replace(a,market_id=3,distance_to_arrival_ls=201),
                  replace(a,market_id=3,station_name='ZZZ'),replace(a,market_id=3)]
        for b in variants:
            for candidates in ([b,a],[a,b]):
                self.assertEqual(self.best(candidates).destination,a)

    def test_sequential_queries_progress_cache_hits_and_cancel(self):
        provider=Provider({BEER.frontier_id:MarketSearchResult(MarketStatus.OK,(offer(),),from_cache=True)})
        updates=[]
        result=self.search(origin=market(rows=[item(),item(GOLD)]),provider=provider,progress=updates.append)
        self.assertEqual(result.cache_hits,1)
        self.assertEqual(len(provider.queries),2)
        self.assertEqual([r.checked for r in updates],[0,1,2])
        self.assertTrue(all(q.minimum_quantity==1 and q.limit==100 for q in provider.queries))
        cancel=Event();provider.queries.clear()
        def progress(r):
            if r.checked==1:cancel.set()
        result=self.search(origin=market(rows=[item(),item(GOLD)]),provider=provider,cancel=cancel,progress=progress)
        self.assertTrue(result.cancelled)
        self.assertFalse(result.rows)
        self.assertEqual(len(provider.queries),1)

    def test_local_first_and_newer_spansh_replaces_preview(self):
        updates=[]
        local=market(mid=2,stamp=NOW-timedelta(minutes=5),rows=[item(sell=12000)])
        provider=Provider({BEER.frontier_id:MarketSearchResult(MarketStatus.OK,(offer(),))})
        result=self.search(locals=[local],provider=provider,progress=updates.append)
        self.assertEqual(updates[0].rows[0].destination.provider,'local_elite')
        self.assertEqual(result.rows[0].destination.provider,'spansh')

    def test_partial_failure_truncated_and_exception_keep_successes(self):
        for error in (MarketStatus.TIMEOUT,MarketStatus.NETWORK_ERROR,MarketStatus.RATE_LIMIT,
                      MarketStatus.INVALID_RESPONSE,RuntimeError('synthetic')):
            bad=error if isinstance(error,Exception) else MarketSearchResult(error)
            provider=Provider({BEER.frontier_id:MarketSearchResult(MarketStatus.OK,(offer(),)),GOLD.frontier_id:bad})
            result=self.search(origin=market(rows=[item(),item(GOLD)]),provider=provider)
            self.assertTrue(result.partial)
            self.assertEqual(len(result.rows),1)
        provider=Provider({BEER.frontier_id:MarketSearchResult(MarketStatus.OK,(offer(),),truncated=True)})
        self.assertTrue(self.search(provider=provider).partial)

    def test_expired_quotes_during_search_not_returned(self):
        times=iter([NOW]+[NOW+timedelta(days=1)]*10)
        self.assertFalse(self.search(locals=[market(mid=2)],clock=lambda:next(times)).rows)

    def test_cancel_at_last_progress_and_nonlocal_origin(self):
        cancel=Event()
        result=self.search(locals=[market(mid=2)],cancel=cancel,
                           progress=lambda r:cancel.set() if r.checked==1 else None)
        self.assertTrue(result.cancelled)
        self.assertFalse(result.rows)
        provider=Provider()
        self.assertFalse(self.search(origin=market(source='spansh'),provider=provider).rows)
        self.assertFalse(provider.queries)
