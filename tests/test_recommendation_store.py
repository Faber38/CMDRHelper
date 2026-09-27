"""Synthetic parity and bounded-read regression checks for recommendations."""
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
import unittest
from unittest.mock import patch
from cmdrhelper.market_store import MarketStore
from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus, PadSize
from cmdrhelper.recommendation_market_source import RecommendationStoreSession
from cmdrhelper.trade_market_source import TradeMarketSource
from cmdrhelper.trade_recommendations import search_recommendations
from test_trade_recommendations import market, item, offer, NOW, FID, BEER, GOLD, Provider


class RecommendationStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/'markets.db'
        self.store = MarketStore(self.path, clock=lambda: NOW)
        self.addCleanup(self.store.close)
        self.source = TradeMarketSource(self.path, FID, 'Fixture System', 100)
        self.query = MarketSearch('', 'Fixture System', limit=100)
        self.rows = {}
        self.put(market(rows=[item(GOLD), item()]))

    def put(self, row):
        self.store.record_observation(row)
        key = row['fid'], row['market_id']
        if key not in self.rows or self.rows[key]['observed_at'] < row['observed_at']:
            self.rows[key] = row

    def compare(self, responses=None, query=None, local_only=False, free=100, margin=10):
        query = query or self.query
        origin = self.rows[(FID,1)]
        rows = list(self.rows.values())
        old = search_recommendations(origin, rows, {r['market_id']:0 for r in rows}, free, margin,
            query, Provider(responses), clock=lambda:NOW, local_only=local_only)
        header = {k:v for k,v in origin.items() if k != 'commodities'}
        with RecommendationStoreSession(self.source, header, query, clock=lambda:NOW,cancel=Event()) as session:
            new = search_recommendations(session.origin, (), {}, free, margin, query,
                Provider(responses), clock=lambda:NOW, local_only=local_only, local_evaluator=session)
            self.assertLessEqual(sum(len(v[0]) for v in session.memo.values()), 2*101)
        self.assertEqual(new, old)
        return new

    def test_semantics_missing_zero_quantities_sources_and_order_ties(self):
        self.put(market(mid=2,stamp=NOW-timedelta(hours=1),rows=[item(GOLD),item()]))
        self.put(market(mid=2,rows=[]))
        self.put(market(mid=3,rows=[item(GOLD,buy=0,sell=12000,demand=8),item(buy=0,sell=12000,demand=8)]))
        self.put(market(mid=4,rows=[item(sell=0,demand=0)]))
        self.put(market(fid='OTHER',mid=3,rows=[item(sell=999999)]))
        for delta in (-1,0,1):
            responses={c.frontier_id:MarketSearchResult(MarketStatus.OK,(
                offer(mid=2,master=c,stamp=NOW-timedelta(seconds=delta)),
                offer(mid=3,master=c,stamp=NOW-timedelta(seconds=delta)))) for c in (GOLD,BEER)}
            self.compare(responses)
        for free in (0,1,8,100):
            for margin in (0,10,1000):
                self.compare(local_only=True,free=free,margin=margin)

    def test_ages_metadata_and_provider_failure(self):
        for mid,seconds in enumerate((-1,0,1),2):
            self.put(market(mid=mid,stamp=NOW-timedelta(hours=24,seconds=seconds),
                            station_type='CraterPort',rows=[item(GOLD),item()]))
        for age in (timedelta(hours=24),None):
            for pad in PadSize:
                self.compare(query=replace(self.query,max_age=age,required_pad=pad))
        for status in (MarketStatus.TIMEOUT, MarketStatus.NO_RESULTS, MarketStatus.RATE_LIMIT):
            self.compare({GOLD.frontier_id:MarketSearchResult(status)})
        self.compare(local_only=True)

    def test_101st_candidate_survives_100_newer_unprofitable_quotes(self):
        for mid in range(2,105):
            self.put(market(mid=mid,stamp=NOW-timedelta(hours=1),
                           rows=[item(sell=15000-mid),item(GOLD,sell=15000-mid)]))
        responses={c.frontier_id:MarketSearchResult(MarketStatus.OK,
            tuple(offer(mid=i,master=c,commander_sell_price=1) for i in range(2,102))) for c in (GOLD,BEER)}
        result=self.compare(responses)
        self.assertEqual({r.destination.market_id for r in result.rows},{102})

    def test_origin_once_buyable_once_and_no_repeat_candidate_queries(self):
        self.put(market(mid=2,rows=[item(GOLD),item()]))
        origin=self.rows[(FID,1)]
        header={k:v for k,v in origin.items() if k!='commodities'}
        from cmdrhelper.trade_recommendations import buyable
        original=MarketStore.get_current
        calls=[]
        def get(store,*args,**kwargs):
            calls.append(args)
            return original(store,*args,**kwargs)
        with patch.object(MarketStore,'get_current',get), patch('cmdrhelper.trade_recommendations.buyable',wraps=buyable) as bought:
            with RecommendationStoreSession(self.source,header,self.query,clock=lambda:NOW,cancel=Event()) as session:
                statements=[]
                session.store._con.set_trace_callback(statements.append)
                search_recommendations(session.origin,(),{},100,10,self.query,Provider(),clock=lambda:NOW,
                    local_evaluator=session, progress=lambda r:None)
                candidates=[s for s in statements if 'LEFT JOIN commodity_observations' in s]
                self.assertEqual(len(candidates),2)
            self.assertEqual(len(calls),1)
            self.assertEqual(bought.call_count,1)

    def test_progress_is_bounded_even_many_buyable_items(self):
        updates=[]
        self.put(market(mid=2,rows=[item(),item(GOLD)]))
        origin=self.rows[(FID,1)]
        with RecommendationStoreSession(self.source,origin,self.query,clock=lambda:NOW,cancel=Event()) as session:
            search_recommendations(session.origin,(),{},100,10,self.query,Provider(),clock=lambda:NOW,
                local_evaluator=session,progress=updates.append,progress_interval=60,local_only=True)
        self.assertLessEqual(len(updates),2)

    def test_dynamic_age_boundary_recomputes_only_when_needed(self):
        from cmdrhelper.recommendation_diagnostics import CommodityStep,CommodityIdentity
        self.put(market(mid=2,stamp=NOW-timedelta(hours=24),rows=[item(sell=99999)]))
        self.put(market(mid=3,stamp=NOW,rows=[item(sell=12000)]))
        origin=self.rows[(FID,1)]
        with RecommendationStoreSession(self.source,origin,self.query,clock=lambda:NOW,cancel=Event()) as session:
            step=CommodityStep(CommodityIdentity(BEER.frontier_id,BEER.symbol))
            session.target_count(NOW)
            self.assertEqual(session.evaluate(item(),(),NOW,step,100,10,self.query).destination.market_id,2)
            later=NOW+timedelta(microseconds=1)
            session.target_count(later)
            self.assertEqual(session.evaluate(item(),(),later,step,100,10,self.query).destination.market_id,3)

    def test_newer_ineligible_spansh_reveals_next_local_candidate(self):
        self.put(market(mid=2,stamp=NOW-timedelta(hours=1),rows=[item(sell=99999)]))
        self.put(market(mid=3,stamp=NOW-timedelta(hours=1),rows=[item(sell=12000)]))
        responses={BEER.frontier_id:MarketSearchResult(MarketStatus.OK,(
            offer(mid=2,commander_sell_price=999999,largest_pad=None,is_fleet_carrier=True),))}
        result=self.compare(responses)
        self.assertEqual(result.rows[0].destination.market_id,3)

    def test_header_only_production_projection_never_reads_target_payloads(self):
        from cmdrhelper.market_writer import MarketWriteWorker
        from cmdrhelper.observed_market_cache import ObservedMarketCache
        from cmdrhelper.market_migration import migrate_market_cache
        # A separate properly activated empty store, followed by worker writes.
        source=Path(self.temp.name)/'source.json'
        path=Path(self.temp.name)/'worker.db'
        migrate_market_cache(source,path,clock=lambda:NOW)
        with MarketStore(path,clock=lambda:NOW) as store:
            store.record_observation(market())
        cache=ObservedMarketCache(source,clock=lambda:NOW)
        with patch.object(MarketStore,'_payload',side_effect=AssertionError('No full projection')):
            worker=MarketWriteWorker(source,path,clock=lambda:NOW,
                                    on_loaded=cache.install_headers,on_committed=cache.apply_committed_header)
            try:
                worker.ready.result(timeout=5)
            finally:
                worker.close()
        self.assertNotIn('commodities',cache.get_header(1))
        self.assertTrue(all('commodities' not in row for row in cache._markets.values()))


    def test_cached_spansh_winner_retains_original_retrieval_time(self):
        from cmdrhelper.recommendation_diagnostics import CommodityStep,CommodityIdentity
        self.put(market(mid=2,stamp=NOW-timedelta(hours=1),rows=[item(sell=12000)]))
        origin=self.rows[(FID,1)]
        community=(offer(mid=2,commander_sell_price=30000,retrieved_at=NOW-timedelta(seconds=10)),)
        with RecommendationStoreSession(self.source,origin,self.query,clock=lambda:NOW,cancel=Event()) as session:
            step=CommodityStep(CommodityIdentity(BEER.frontier_id,BEER.symbol))
            session.target_count(NOW)
            first=session.evaluate(item(),community,NOW,step,100,10,self.query)
            second=session.evaluate(item(),community,NOW+timedelta(seconds=1),step,100,10,self.query)
            self.assertEqual(second,first)
            self.assertEqual(second.destination.provider,'spansh')



if __name__=='__main__':
    unittest.main()
