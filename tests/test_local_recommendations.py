"""Local-only recommendations: synthetic markets, provider calls are forbidden."""
from dataclasses import replace
from datetime import timedelta
from threading import Event
from unittest.mock import Mock, patch
import unittest

from cmdrhelper.commodity_master import all_commodities
from cmdrhelper.market_data import MarketSearch, PadSize
from cmdrhelper.recommendation_diagnostics import PartialReason
from cmdrhelper.recommendation_diagnostic_text import format_recommendation_diagnostic
from cmdrhelper.trade_recommendations import search_recommendations
from test_trade_recommendations import market, item, NOW, BEER, GOLD


class LocalRecommendationTests(unittest.TestCase):
    def search(self, **changes):
        provider=Mock()
        provider.search_sell.side_effect=AssertionError('Local-only must not call any provider')
        args=dict(origin=market(),local_markets=[market(),market(mid=2)],distances={1:0,2:5},
                  free=280,margin=10,query=MarketSearch('', 'Fixture System'),provider=provider,
                  local_only=True,clock=lambda:NOW)
        args.update(changes)
        with patch('cmdrhelper.spansh_transport.urlopen',side_effect=AssertionError('No network')) as network:
            result=search_recommendations(**args)
        provider.search_sell.assert_not_called();network.assert_not_called()
        self.assertTrue(result.diagnostics.local_only)
        self.assertEqual((result.diagnostics.spansh_commodities_started,
                          result.diagnostics.spansh_commodities_completed,
                          result.diagnostics.spansh_commodities_failed,
                          result.diagnostics.http_requests,result.diagnostics.cache_hits), (0,0,0,0,0))
        return result

    def test_two_markets_local_target_prices_quantity_and_gain(self):
        result=self.search()
        self.assertEqual(len(result.rows),1)
        row=result.rows[0]
        self.assertEqual(row.destination.market_id,2)
        self.assertEqual(row.destination.provider,'local_elite')
        self.assertEqual((row.quantity,row.profit_per_ton,row.profit_percent,row.total_profit),
                         (190,1500,15,285000))
        self.assertFalse(result.partial)
        self.assertEqual(result.diagnostics.partial_reason,PartialReason.NONE)
        self.assertIn('local_only=true',format_recommendation_diagnostic(result.diagnostics))

    def test_52_local_steps_complete_without_community_or_partial(self):
        rows=[item(c) for c in all_commodities()[:52]]
        updates=[]
        r=self.search(origin=market(rows=rows),local_markets=[market(mid=2,rows=rows)],progress=updates.append)
        d=r.diagnostics
        self.assertEqual((d.planned_commodities,d.checked_commodities,d.successful_commodities,
                          d.failed_commodities,d.skipped_commodities),(52,52,52,0,0))
        self.assertEqual(d.local_commodities_completed,52)
        self.assertEqual(d.partial_reason,PartialReason.NONE)
        self.assertFalse(d.partial)
        self.assertEqual(len(r.rows),52)
        self.assertEqual([v.diagnostics.checked_commodities for v in updates],list(range(53)))
        self.assertTrue(all(row.destination.provider=='local_elite' for row in r.rows))

    def test_current_market_other_fid_and_other_source_never_targets(self):
        for target in (market(),market(mid=2,fid='F_OTHER'),market(mid=2,source='spansh')):
            self.assertFalse(self.search(local_markets=[target]).rows)

    def test_ttl_exact_boundary_and_user_target_age(self):
        for hours,expected in ((5,True),(10,False),(24,False)):
            r=self.search(local_markets=[market(mid=2,stamp=NOW-timedelta(hours=hours))],
                          query=MarketSearch('', 'Fixture System',max_age=timedelta(hours=6)))
            self.assertEqual(bool(r.rows),expected)
        self.assertTrue(self.search(local_markets=[market(mid=2,stamp=NOW-timedelta(hours=24,seconds=-1))]).rows)
        self.assertFalse(self.search(local_markets=[market(mid=2,stamp=NOW-timedelta(hours=24))]).rows)

    def test_radius_unknown_distance_pad_and_arrival_filter(self):
        for distance in (150,None):
            self.assertFalse(self.search(distances={2:distance}).rows)
        for pad in (PadSize.SMALL,PadSize.MEDIUM,PadSize.LARGE):
            self.assertFalse(self.search(query=MarketSearch('', 'Fixture System',required_pad=pad)).rows)
        self.assertFalse(self.search(query=MarketSearch('', 'Fixture System',max_distance_to_arrival_ls=500)).rows)

    def test_carrier_and_unknown_station_type(self):
        for kind in ('FleetCarrier',''):
            targets=[market(mid=2,station_type=kind)]
            self.assertFalse(self.search(local_markets=targets).rows)
            self.assertTrue(self.search(local_markets=targets,
                query=MarketSearch('', 'Fixture System',include_fleet_carriers=True)).rows)

    def test_buyability_demand_and_minimum_margin(self):
        for row in (item(sell=0),item(demand=0)):
            self.assertFalse(self.search(local_markets=[market(mid=2,rows=[row])]).rows)
        for row in (item(buy=0),item(supply=0)):
            r=self.search(origin=market(rows=[row]))
            self.assertFalse(r.rows);self.assertEqual(r.diagnostics.planned_commodities,0)
        self.assertFalse(self.search(margin=20).rows)
        self.assertTrue(self.search(local_markets=[market(mid=2,rows=[item(sell=11000)])]).rows)
        self.assertFalse(self.search(local_markets=[market(mid=2,rows=[item(sell=10999)])]).rows)

    def test_quantity_each_bound_and_total_gain(self):
        for free,supply,demand,expected in ((280,1200,190,190),(280,150,20000,150),(20,100,100,20)):
            r=self.search(free=free,origin=market(rows=[item(supply=supply)]),
                          local_markets=[market(mid=2,rows=[item(demand=demand)])])
            self.assertEqual(r.rows[0].quantity,expected)
            self.assertEqual(r.rows[0].total_profit,1500*expected)

    def test_unknown_future_commodity_is_fully_local_not_an_error(self):
        unknown=dict(item(),commodity_id=199999999,symbol='FutureSynthetic')
        r=self.search(origin=market(rows=[unknown]),local_markets=[market(mid=2,rows=[unknown])])
        self.assertEqual(len(r.rows),1)
        self.assertFalse(r.partial)
        self.assertEqual(r.diagnostics.successful_commodities,1)
        self.assertEqual(r.diagnostics.provider_error_count,0)

    def test_no_targets_is_complete_and_sorting_best_target_unchanged(self):
        self.assertFalse(self.search(local_markets=[]).partial)
        r=self.search(origin=market(rows=[item(),item(GOLD)]),
            local_markets=[market(mid=2,rows=[item(),item(GOLD,sell=14000)])])
        self.assertEqual([row.destination.commodity_id for row in r.rows],[GOLD.frontier_id,BEER.frontier_id])
        self.assertGreater(r.rows[0].total_profit,r.rows[1].total_profit)

    def test_local_cancel_between_commodities(self):
        token=Event()
        def progress(r):
            if r.checked==1:token.set()
        r=self.search(origin=market(rows=[item(),item(GOLD)]),cancel=token,progress=progress)
        self.assertTrue(r.cancelled)
        self.assertEqual(r.diagnostics.partial_reason,PartialReason.CANCELLED)
        self.assertEqual(r.diagnostics.checked_commodities,1)


if __name__=='__main__':unittest.main()
