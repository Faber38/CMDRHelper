"""Exact outbound destination contracts; all market data and HTTP are synthetic."""
from dataclasses import replace
from datetime import timedelta
from threading import Event
import unittest
from unittest.mock import patch
from cmdrhelper.market_data import MarketTarget, MarketSearch, MarketSearchResult, MarketStatus, PadSize
from cmdrhelper.market_store import MarketStore
from cmdrhelper.recommendation_market_source import RecommendationStoreSession
from cmdrhelper.trade_recommendations import search_recommendations
from test_trade_recommendations import market, item, offer, NOW, BEER, GOLD, Provider
from test_market_data_provider import Harness, station, response, query
import test_recommendation_store as store_fixtures


class FixedRecommendationTests(unittest.TestCase):
    def search(self, *, target=MarketTarget(2, 200), locals=(), quotes=None, **options):
        q = options.pop('query', MarketSearch('', 'Fixture System', target=target))
        provider = options.pop('provider', Provider(quotes))
        return search_recommendations(market(rows=[item(), item(GOLD)]), locals,
            {s['market_id']: 10 for s in locals}, 100, 10, q, provider, clock=lambda: NOW, **options)

    def test_all_buyable_commodities_only_exact_target_and_correct_prices(self):
        quotes = {c.frontier_id: MarketSearchResult(MarketStatus.OK, (
            offer(master=c), offer(mid=3, master=c, commander_sell_price=50000))) for c in (BEER, GOLD)}
        result = self.search(quotes=quotes)
        self.assertEqual({r.destination.commodity_id for r in result.rows}, {BEER.frontier_id, GOLD.frontier_id})
        self.assertTrue(all((r.destination.market_id,r.buy_price,r.sell_price,r.quantity)==(2,10000,11500,100)
                            for r in result.rows))
        normal = self.search(target=None, quotes=quotes)
        self.assertTrue(all(r.destination.market_id == 3 for r in normal.rows))

    def test_wrong_system_same_name_and_self_destination_never_substitute(self):
        for target in (MarketTarget(2, 999), MarketTarget(1), MarketTarget(55)):
            result = self.search(target=target, quotes={BEER.frontier_id:
                MarketSearchResult(MarketStatus.OK, (offer(), offer(mid=3, commander_sell_price=99999)))})
            self.assertFalse(result.rows)

    def test_newer_local_missing_or_zero_suppresses_community(self):
        for rows in ([], [item(sell=0)], [item(demand=0)]):
            result = self.search(locals=[market(mid=2, system_address=200, rows=rows)],
                quotes={BEER.frontier_id: MarketSearchResult(MarketStatus.OK,
                    (offer(stamp=NOW-timedelta(seconds=1)),))})
            self.assertFalse(result.rows)

    def test_newer_local_changed_system_suppresses_stale_old_location(self):
        result = self.search(locals=[market(mid=2,system_address=999)],
            quotes={BEER.frontier_id:MarketSearchResult(MarketStatus.OK,
                (offer(stamp=NOW-timedelta(seconds=1)),))})
        self.assertFalse(result.rows)

    def test_local_only_no_provider_and_all_filters_apply(self):
        provider = Provider()
        local = market(mid=2, system_address=200)
        self.assertTrue(self.search(locals=[local], local_only=True, provider=provider).rows)
        self.assertFalse(provider.queries)
        base = MarketSearch('', 'Fixture System', target=MarketTarget(2,200))
        for q in (replace(base,radius_ly=1), replace(base, required_pad=PadSize.LARGE),
                  replace(base,max_distance_to_arrival_ls=100)):
            self.assertFalse(self.search(locals=[local], local_only=True, query=q).rows)
        self.assertFalse(self.search(locals=[dict(local,station_type='FleetCarrier')],local_only=True).rows)

    def test_missing_expired_and_future_markets(self):
        for locals in ([], [market(mid=2,system_address=200,stamp=NOW-timedelta(days=2))],
                       [market(mid=2,system_address=200,stamp=NOW+timedelta(seconds=1))]):
            self.assertFalse(self.search(locals=locals,local_only=True).rows)

    def test_newer_community_and_equal_timestamp_prefer_correct_source(self):
        for delta, expected in ((-1,'spansh'),(0,'local_elite'),(1,'local_elite')):
            result = self.search(locals=[market(mid=2,system_address=200, stamp=NOW-timedelta(seconds=1))],
                quotes={BEER.frontier_id:MarketSearchResult(MarketStatus.OK,
                    (offer(stamp=NOW-timedelta(seconds=1+delta)),))})
            self.assertEqual(result.rows[0].destination.provider, expected)

    def test_failed_or_truncated_provider_keeps_only_target_and_marks_partial(self):
        for status,truncated in ((MarketStatus.TIMEOUT,False),(MarketStatus.OK,True)):
            result = self.search(locals=[market(mid=2,system_address=200)],
                quotes={BEER.frontier_id:MarketSearchResult(status, (offer(mid=3),), truncated=truncated)})
            self.assertTrue(result.partial)
            self.assertTrue(all(r.destination.market_id==2 for r in result.rows))

    def test_invalid_identity(self):
        for args in ((None,), (True,), (0,), (-1,), (2**64,), (1,0), (1,True)):
            with self.assertRaises(ValueError):
                MarketTarget(*args)


class FixedStoreTests(unittest.TestCase):
    setUp = store_fixtures.RecommendationStoreTests.setUp
    put = store_fixtures.RecommendationStoreTests.put
    compare = store_fixtures.RecommendationStoreTests.compare

    def test_target_beyond_101_locals_and_database_filter(self):
        for mid in range(2,110):
            self.put(market(mid=mid,rows=[item(sell=15000),item(GOLD,sell=15000)]))
        q = replace(self.query,target=MarketTarget(109,100))
        original = MarketStore.query_current_candidates
        calls = []
        def tracked(store,*args,**kwargs):
            calls.append(kwargs)
            return original(store,*args,**kwargs)
        with patch.object(MarketStore,'query_current_candidates',tracked):
            result = self.compare(query=q, local_only=True)
        self.assertEqual(len(result.rows),2)
        self.assertTrue(all(r.destination.market_id==109 for r in result.rows))
        self.assertTrue(all(c['market_ids']==(109,) and c['system_address']==100 for c in calls))
        self.assertEqual(result.diagnostics.local_target_markets,1)

    def test_moved_station_evidence_still_suppresses_older_quote(self):
        self.put(market(mid=2, system_address=999))
        quotes = {BEER.frontier_id:MarketSearchResult(MarketStatus.OK,
            (offer(system_id64=100, stamp=NOW-timedelta(seconds=1)),))}
        self.assertFalse(self.compare(quotes,query=replace(self.query,target=MarketTarget(2,100))).rows)

    def test_store_freshness_empty_overlap_and_identity(self):
        self.put(market(mid=2, rows=[]))
        quotes = {BEER.frontier_id:MarketSearchResult(MarketStatus.OK,(
            offer(system_id64=100,stamp=NOW-timedelta(seconds=1)),))}
        self.assertFalse(self.compare(quotes,query=replace(self.query,target=MarketTarget(2,100))).rows)
        self.assertFalse(self.compare(quotes,query=replace(self.query,target=MarketTarget(2,999))).rows)


class FixedProviderTests(unittest.TestCase):
    def test_server_filters_before_limit_and_local_validation(self):
        h = Harness(response(station(market_id=7),station(market_id=8,price=999999)))
        q = query(target=MarketTarget(7,2210138181099),limit=1)
        result = h.provider.search_sell(q)
        self.assertEqual([o.market_id for o in result.offers],[7])
        self.assertFalse(result.truncated)
        self.assertEqual(h.payloads[0]['filters']['market_id'],{'value':'7'})
        self.assertEqual(h.payloads[0]['filters']['system_id64'],{'value':'2210138181099'})
        self.assertEqual(h.payloads[0]['reference_system'],q.reference_system)

    def test_wrong_system_rejected_no_other_station(self):
        h = Harness(response(station(market_id=7,system_id64=999),station(market_id=8)))
        self.assertEqual(h.provider.search_sell(query(target=MarketTarget(7,2210138181099))).status,
                         MarketStatus.NO_RESULTS)

    def test_normal_query_unchanged_and_target_cache_isolated(self):
        h = Harness(response(station(market_id=7)),response(station(market_id=8)),response(station()))
        a,b = query(target=MarketTarget(7)),query(target=MarketTarget(8))
        self.assertFalse(h.provider.search_sell(a).from_cache)
        self.assertTrue(h.provider.search_sell(a).from_cache)
        self.assertEqual(h.provider.search_sell(b).offers[0].market_id,8)
        h.provider.search_sell(query())
        self.assertNotIn('market_id',h.payloads[-1]['filters'])
        self.assertEqual(len(h.payloads),3)

    def test_page_limit_still_reported_for_unexpected_provider_response(self):
        h = Harness(*(response(station(market_id=7),count=4) for _ in range(3)),
                    max_pages=3,page_size=1)
        result = h.provider.search_sell(query(target=MarketTarget(7)))
        self.assertTrue(result.truncated)
        self.assertTrue(result.diagnostics.page_limit_reached)
