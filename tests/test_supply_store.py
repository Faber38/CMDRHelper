"""BUY selection has the same bounded reads and freshness rules as recommendations."""
from dataclasses import replace
from datetime import timedelta
from threading import Event
import unittest
from unittest.mock import patch

from cmdrhelper.market_data import MarketSearchResult, MarketStatus
from cmdrhelper.market_store import MarketStore, StaleReadError
from cmdrhelper.recommendation_market_source import RecommendationStoreSession
from cmdrhelper.recommendation_diagnostics import CommodityStep, CommodityIdentity
from cmdrhelper.trade_recommendations import search_supply_recommendations
import test_recommendation_store as fixtures
from test_trade_recommendations import market, item, NOW, FID, BEER, GOLD
from test_supply_recommendations import BuyProvider, source


class SupplyStoreTests(unittest.TestCase):
    setUp = fixtures.RecommendationStoreTests.setUp
    put = fixtures.RecommendationStoreTests.put

    def compare(self, responses=None, query=None, local_only=False, free=100, margin=10, quantity=70):
        query = query or self.query
        origin = self.rows[(FID, 1)]
        rows = list(self.rows.values())
        expected = search_supply_recommendations(origin, rows, {r['market_id']:0 for r in rows},
            free, margin, query, BuyProvider(responses), clock=lambda:NOW,
            local_only=local_only, quantity=quantity)
        header = {k:v for k,v in origin.items() if k != 'commodities'}
        with RecommendationStoreSession(self.source, header, query, clock=lambda:NOW,
                                         cancel=Event(), supply=True) as session:
            actual = search_supply_recommendations(session.origin, (), {}, free, margin, query,
                BuyProvider(responses), clock=lambda:NOW, local_only=local_only,
                local_evaluator=session, quantity=quantity)
            self.assertLessEqual(sum(len(v[0]) for v in session.memo.values()), 202)
        self.assertEqual(actual, expected)
        return actual

    def test_parity_empty_zero_foreign_observer_quantity_and_filters(self):
        self.put(market(mid=2, stamp=NOW-timedelta(hours=1)))
        self.put(market(mid=2, rows=[]))
        self.put(market(mid=3, rows=[item(buy=0), item(GOLD, supply=0)]))
        self.put(market(mid=4, fid='OTHER', rows=[item(supply=5), item(GOLD, buy=10100)]))
        quotes = {BEER.frontier_id: MarketSearchResult(MarketStatus.OK,
                  (source(mid=2, stamp=NOW-timedelta(minutes=1)),))}
        r = self.compare(quotes)
        self.assertEqual({x.source.market_id for x in r.rows}, {4})
        self.assertEqual(next(x.quantity for x in r.rows if x.source.commodity_id==BEER.frontier_id), 5)
        self.assertTrue(self.compare(local_only=True).rows)
        self.assertFalse(self.compare(query=replace(self.query, max_distance_to_arrival_ls=100)).rows)

    def test_101st_local_survives_100_newer_unprofitable_quotes(self):
        for mid in range(2, 103):
            self.put(market(mid=mid, stamp=NOW-timedelta(minutes=1), rows=[item(buy=10000+mid)]))
        quotes = tuple(replace(source(mid=mid), commander_buy_price=20000) for mid in range(2,102))
        result = self.compare({BEER.frontier_id: MarketSearchResult(MarketStatus.OK, quotes)})
        self.assertEqual(result.rows[0].source.market_id, 102)

    def test_more_than_100_provider_overrides_streams_correctly(self):
        for mid in range(2, 105):
            self.put(market(mid=mid, stamp=NOW-timedelta(minutes=1), rows=[item(buy=10000+mid)]))
        quotes = tuple(replace(source(mid=mid), commander_buy_price=20000) for mid in range(2,104))
        r = self.compare({BEER.frontier_id: MarketSearchResult(MarketStatus.OK, quotes)})
        self.assertEqual(r.rows[0].source.market_id, 104)

    def test_full_local_pagination_before_profit_ranking(self):
        for mid in range(2, 504):
            self.put(market(mid=mid, rows=[item(buy=1, supply=1)]))
        self.put(market(mid=504, rows=[item(buy=10000, supply=500)]))
        self.assertEqual(self.compare(local_only=True).rows[0].source.market_id, 504)

    def test_target_once_no_other_full_payloads_and_reused_queries(self):
        self.put(market(mid=2, rows=[item(), item(GOLD)]))
        header = self.rows[(FID,1)]
        calls = []
        original = MarketStore._payload
        def payload(store, snapshot):
            calls.append(snapshot)
            return original(store, snapshot)
        with patch.object(MarketStore, '_payload', payload):
            with RecommendationStoreSession(self.source, header, self.query,
                    clock=lambda:NOW, cancel=Event(), supply=True) as session:
                statements = []
                session.store._con.set_trace_callback(statements.append)
                search_supply_recommendations(session.origin, (), {}, 100, 10, self.query,
                    BuyProvider(), clock=lambda:NOW, local_evaluator=session, progress=lambda _: None)
                queries = [s for s in statements if 'LEFT JOIN commodity_observations' in s]
                self.assertEqual(len(queries), 2)
                self.assertTrue(all('commander_buy_price>' in s for s in queries))
        self.assertEqual(len(calls), 1)

    def test_source_expiry_recalculates_and_target_mismatch_rejected(self):
        self.put(market(mid=2, stamp=NOW-timedelta(hours=24), rows=[item(buy=9000)]))
        self.put(market(mid=3, rows=[item()]))
        header = self.rows[(FID,1)]
        with RecommendationStoreSession(self.source, header, self.query,
                clock=lambda:NOW, cancel=Event(), supply=True) as session:
            step = CommodityStep(CommodityIdentity(BEER.frontier_id, BEER.symbol))
            session.target_count(NOW)
            self.assertEqual(session.evaluate(item(), (), NOW, step, 100, 10, self.query).source.market_id, 2)
            later = NOW+timedelta(microseconds=1)
            session.target_count(later)
            self.assertEqual(session.evaluate(item(), (), later, step, 100, 10, self.query).source.market_id, 3)
        with RecommendationStoreSession(self.source, dict(header, station_name='Wrong'), self.query,
                clock=lambda:NOW, cancel=Event(), supply=True) as session:
            self.assertIsNone(session.origin)

    def test_revision_change_cannot_publish_mixed_snapshot(self):
        header = self.rows[(FID,1)]
        with RecommendationStoreSession(self.source, header, self.query,
                clock=lambda:NOW, cancel=Event(), supply=True) as session:
            session.target_count(NOW)
            self.put(market(mid=2))
            with self.assertRaises(StaleReadError):
                session.target_count(NOW)

    def test_provider_failure_preserves_locals_and_future_data_rejected(self):
        self.put(market(mid=2))
        r = self.compare({BEER.frontier_id:MarketSearchResult(MarketStatus.TIMEOUT)})
        self.assertTrue(r.rows)
        self.assertTrue(r.partial)
        r = self.compare({BEER.frontier_id:MarketSearchResult(MarketStatus.OK,
            (source(stamp=NOW+timedelta(seconds=1)),))})
        self.assertEqual(r.rows[0].source.provider, 'local_elite')
