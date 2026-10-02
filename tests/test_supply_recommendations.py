"""Fixed-target trading, using only synthetic observations and fake providers."""
from dataclasses import replace
from datetime import timedelta
from fractions import Fraction
from threading import Event
import unittest

from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus, PadSize
from cmdrhelper.recommendation_diagnostics import PartialReason
from cmdrhelper.trade_recommendations import search_supply_recommendations, search_recommendations, ranking
from test_trade_recommendations import market, item, offer, BEER, GOLD, NOW, Provider


def source(mid=2, **changes):
    values = dict(commander_buy_price=10000, supply=200)
    values.update(changes)
    return offer(mid=mid, **values)


class BuyProvider(Provider):
    def search_buy(self, q, *, cancel):
        return super().search_sell(q, cancel=cancel)

    def search_sell(self, *args, **kwargs):
        raise AssertionError('Fixed-target search must use BUY')


class SupplyTests(unittest.TestCase):
    def search(self, locals=(), quotes=(), **changes):
        args = dict(target=market(), local_markets=locals,
                    distances={s['market_id']: 0 for s in locals}, free=280, quantity=100,
                    margin=10, query=MarketSearch('', 'Wrong reference'),
                    provider=BuyProvider({BEER.frontier_id: MarketSearchResult(MarketStatus.OK, quotes)}),
                    clock=lambda: NOW)
        args.update(changes)
        return search_supply_recommendations(**args)

    def test_roles_formula_fixed_target_and_reference(self):
        provider = BuyProvider({BEER.frontier_id: MarketSearchResult(MarketStatus.OK, (source(),))})
        row = self.search(provider=provider).rows[0]
        self.assertEqual(row.target.market_id, 1)
        self.assertEqual(row.source.market_id, 2)
        self.assertEqual((row.buy_price, row.sell_price, row.profit_per_ton), (10000, 11500, 1500))
        self.assertEqual((row.quantity, row.total_profit, row.profit_percent), (100, 150000, Fraction(15)))
        self.assertEqual((row.purchase_cost, row.sale_revenue), (1000000, 1150000))
        q = provider.queries[0]
        self.assertEqual((q.reference_system, q.minimum_quantity, q.limit), ('Fixture System', 1, 100))

    def test_all_demanded_not_buyable_and_one_query_each(self):
        target = market(rows=[item(buy=0, supply=0), item(GOLD, buy=0, supply=0)])
        p = BuyProvider()
        result = self.search(target=target, provider=p)
        self.assertEqual(result.total, 2)
        self.assertEqual([q.commodity for q in p.queries], [BEER.frontier_id, GOLD.frontier_id])
        for bad in (item(sell=0), item(demand=0)):
            p = BuyProvider()
            self.assertEqual(self.search(target=market(rows=[bad]), provider=p).total, 0)
            self.assertFalse(p.queries)

    def test_all_four_quantity_bounds_and_invalid_quantity(self):
        for chosen, free, supply, demand, expected in ((7,100,100,100,7), (100,8,100,100,8),
                (100,100,9,100,9), (100,100,100,10,10)):
            row = self.search(quotes=(replace(source(), supply=supply),), quantity=chosen, free=free,
                              target=market(rows=[item(demand=demand)])).rows[0]
            self.assertEqual(row.quantity, expected)
        for quantity in (0, -1, True, 1.5):
            self.assertFalse(self.search(quotes=(source(),), quantity=quantity).rows)
        for free in (0, None, True):
            self.assertFalse(self.search(quotes=(source(),), free=free).rows)

    def test_strict_profit_margin_and_outward_zero_profit_unchanged(self):
        for buy in (0, None, 11500, 12000):
            self.assertFalse(self.search(quotes=(replace(source(), commander_buy_price=buy),), margin=0).rows)
        for supply in (0, None):
            self.assertFalse(self.search(quotes=(replace(source(), supply=supply),)).rows)
        for sell, expected in ((10999, False), (11000, True)):
            r = self.search(target=market(rows=[item(sell=sell)]), quotes=(source(),))
            self.assertEqual(bool(r.rows), expected)
        old = search_recommendations(market(rows=[item(buy=11500)]), (), {}, 100, 0,
            MarketSearch('', 'Fixture System'), Provider({BEER.frontier_id:
            MarketSearchResult(MarketStatus.OK, (offer(),))}), clock=lambda: NOW)
        self.assertEqual(old.rows[0].profit_per_ton, 0)

    def test_target_never_source_and_identity_exact(self):
        for quote in (source(mid=1), replace(source(), commodity_id=GOLD.frontier_id),
                      replace(source(), commodity_symbol='different')):
            self.assertFalse(self.search(quotes=(quote,)).rows)
        self.assertFalse(self.search(locals=[market()], local_only=True).rows)

    def test_total_profit_beats_price_and_rows_are_alternatives(self):
        cheap = replace(source(), commander_buy_price=1, supply=1)
        larger = source(mid=3)
        r = self.search(quotes=(cheap, larger))
        self.assertEqual([x.source.market_id for x in r.rows], [3])
        locals = [market(mid=4, rows=[item(), item(GOLD)])]
        r = self.search(locals=locals, target=market(rows=[item(), item(GOLD)]), local_only=True)
        self.assertEqual([x.quantity for x in r.rows], [100, 100])

    def test_existing_tiebreak_order_applies_to_source(self):
        base = source()
        variants = [replace(base, market_updated_at=NOW-timedelta(seconds=1)),
                    replace(base, distance_ly=11), replace(base, distance_to_arrival_ls=201),
                    replace(base, distance_to_arrival_ls=None), replace(base, station_name='Z'),
                    replace(base, system_name='Z'), replace(base, market_id=3)]
        for other in variants:
            a = self.search(quotes=(base,)).rows[0]
            b = self.search(quotes=(other,)).rows[0]
            self.assertLess(ranking(a), ranking(b))

    def test_local_only_shared_observers_no_provider_or_partial(self):
        p = BuyProvider()
        r = self.search(locals=[market(mid=2, fid='F_OTHER')], provider=p, local_only=True)
        self.assertEqual(r.rows[0].source.provider, 'local_elite')
        self.assertFalse(p.queries)
        self.assertFalse(r.partial)
        self.assertEqual((r.cache_hits, r.diagnostics.http_requests, r.diagnostics.spansh_commodities_started), (0,0,0))
        self.assertTrue(r.diagnostics.local_only)
        self.assertFalse(self.search(locals=[market(mid=2, source='spansh')], local_only=True).rows)

    def test_mixed_freshness_newer_and_equal_local_zero_or_empty(self):
        for rows in ([], [item(buy=0)], [item(supply=0)]):
            for stamp in (NOW, NOW-timedelta(seconds=1)):
                self.assertFalse(self.search(locals=[market(mid=2, rows=rows)],
                                            quotes=(replace(source(), market_updated_at=stamp),)).rows)
        older = market(mid=2, stamp=NOW-timedelta(seconds=1), rows=[])
        self.assertEqual(self.search(locals=[older], quotes=(source(),)).rows[0].source.provider, 'spansh')
        newer_local = market(mid=2, rows=[item(buy=10500)])
        r = self.search(locals=[newer_local], quotes=(source(),), margin=0)
        self.assertEqual(r.rows[0].buy_price, 10500)

    def test_filters_and_unknown_metadata(self):
        base = MarketSearch('', 'Fixture System')
        cases = [(replace(source(), distance_ly=None), base),
                 (replace(source(), distance_ly=101), base),
                 (replace(source(), largest_pad=None), replace(base, required_pad=PadSize.LARGE)),
                 (replace(source(), is_fleet_carrier=True), base),
                 (replace(source(), is_fleet_carrier=None), base),
                 (replace(source(), distance_to_arrival_ls=None), replace(base, max_distance_to_arrival_ls=500)),
                 (replace(source(), distance_to_arrival_ls=501), replace(base, max_distance_to_arrival_ls=500))]
        for quote, query in cases:
            self.assertFalse(self.search(quotes=(quote,), query=query).rows)
        self.assertTrue(self.search(quotes=(replace(source(), is_fleet_carrier=True),),
                                   query=replace(base, include_fleet_carriers=True)).rows)
        self.assertTrue(self.search(quotes=(replace(source(), distance_ly=100),)).rows)
        self.assertTrue(self.search(locals=[market(mid=2)], local_only=True).rows)
        self.assertFalse(self.search(locals=[market(mid=2)], local_only=True,
                                    query=replace(base, max_distance_to_arrival_ls=500)).rows)

    def test_age_boundaries_no_limit_and_missing_target(self):
        for stamp, allowed in ((NOW-timedelta(hours=24), True),
                               (NOW-timedelta(hours=24, microseconds=1), False),
                               (NOW+timedelta(microseconds=1), False)):
            self.assertEqual(bool(self.search(quotes=(replace(source(), market_updated_at=stamp),)).rows), allowed)
        self.assertTrue(self.search(quotes=(replace(source(), market_updated_at=NOW-timedelta(days=90)),),
                                   query=MarketSearch('', 'Fixture System', max_age=None)).rows)
        for target in (None, market(stamp=NOW-timedelta(days=2))):
            p = BuyProvider()
            r = self.search(target=target, provider=p)
            self.assertFalse(r.rows)
            self.assertEqual(r.diagnostics.partial_reason, PartialReason.CONTEXT_CHANGED)
            self.assertFalse(p.queries)

    def test_unknown_commodity_local_and_mixed(self):
        unknown = dict(item(), commodity_id=199999999, symbol='$future_supply;')
        for local_only in (True, False):
            p = BuyProvider()
            r = self.search(target=market(rows=[unknown]), locals=[market(mid=2, rows=[unknown])],
                            provider=p, local_only=local_only)
            self.assertTrue(r.rows)
            self.assertEqual(r.partial, not local_only)
            self.assertFalse(p.queries)

    def test_local_preview_partial_errors_limits_and_cancel(self):
        for response in (MarketSearchResult(MarketStatus.TIMEOUT), RuntimeError('offline'),
                         MarketSearchResult(MarketStatus.OK, (source(),), truncated=True)):
            p = BuyProvider({BEER.frontier_id: response})
            progress = []
            r = self.search(locals=[market(mid=3)], provider=p, progress=progress.append)
            self.assertTrue(progress[0].rows)
            self.assertTrue(r.rows)
            self.assertTrue(r.partial)
        cancel = Event()
        r = self.search(locals=[market(mid=3)], cancel=cancel, progress=lambda _: cancel.set())
        self.assertTrue(r.cancelled)
        self.assertFalse(r.rows)

    def test_local_only_cancel_and_empty_are_complete(self):
        p = BuyProvider()
        r = self.search(provider=p, local_only=True)
        self.assertFalse(r.rows)
        self.assertFalse(r.partial)
        self.assertEqual((r.checked, r.total), (1, 1))
        cancel = Event()
        r = self.search(locals=[market(mid=3)], local_only=True, cancel=cancel,
                        progress=lambda _: cancel.set())
        self.assertTrue(r.cancelled)
        self.assertFalse(r.rows)

    def test_target_expiring_during_last_provider_call_is_partial(self):
        time = [NOW]
        class Expiring(BuyProvider):
            def search_buy(self, q, *, cancel):
                time[0] += timedelta(days=2)
                return MarketSearchResult(MarketStatus.OK, (source(stamp=time[0]),))
        r = self.search(provider=Expiring(), clock=lambda:time[0])
        self.assertFalse(r.rows)
        self.assertTrue(r.partial)
        self.assertEqual(r.diagnostics.partial_reason, PartialReason.CONTEXT_CHANGED)
