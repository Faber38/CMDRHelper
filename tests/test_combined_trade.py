"""Synthetic buy/sell matrix. No network, production cache or application state."""
from dataclasses import replace
from datetime import timedelta
from threading import Event
from unittest.mock import Mock
import unittest

from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus, TradeSide, PadSize
from cmdrhelper.trade_search import search_trade
from test_trade_recommendations import market, item, offer, NOW, BEER, FID


class TradeMatrix:
    side = TradeSide.SELL

    def search(self, local=None, community=None, status=None, query=None, distances=None, **kwargs):
        self.provider = Mock()
        self.response = MarketSearchResult(status or (MarketStatus.OK if community else MarketStatus.NO_RESULTS),
                                          tuple(community or ()), truncated=kwargs.pop('truncated', False))
        self.provider.search_sell.return_value = self.provider.search_buy.return_value = self.response
        if kwargs.pop('raises', False):
            self.provider.search_sell.side_effect = self.provider.search_buy.side_effect = ValueError('private')
        return search_trade(self.provider, query or MarketSearch(BEER.frontier_id, 'Fixture', minimum_quantity=10, limit=100),
                            self.side, [market()] if local is None else local,
                            {1: 0} if distances is None else distances, kwargs.pop('fid', FID), clock=lambda: NOW, **kwargs)

    def quote(self, **kw):
        return offer(commander_buy_price=10000, supply=100, **kw)

    def test_only_spansh(self):
        self.assertEqual(self.search(local=[], community=[self.quote()]).offers[0].provider, 'spansh')

    def test_only_local_including_current_station(self):
        self.assertEqual(self.search().offers[0].market_id, 1)
        self.assertEqual(self.search().offers[0].provider, 'local_elite')

    def test_both(self):
        self.assertEqual({o.market_id for o in self.search(community=[self.quote()]).offers}, {1,2})

    def test_local_newer(self):
        r = self.search(community=[self.quote(mid=1, stamp=NOW-timedelta(seconds=1), retrieved_at=NOW+timedelta(days=1))])
        self.assertEqual([o.provider for o in r.offers], ['local_elite'])

    def test_spansh_newer(self):
        r = self.search(local=[market(stamp=NOW-timedelta(seconds=1))], community=[self.quote(mid=1)])
        self.assertEqual([o.provider for o in r.offers], ['spansh'])

    def test_tie_local(self):
        self.assertEqual([o.provider for o in self.search(community=[self.quote(mid=1)]).offers], ['local_elite'])

    def test_same_names_other_ids(self):
        r = self.search(local=[market(), market(mid=2)], distances={1:0,2:1})
        self.assertEqual(len(r.offers), 2)

    def test_quantity(self):
        for n, expected in ((9, False), (10, True)):
            row = item(**({'demand': n} if self.side == TradeSide.SELL else {'supply': n}))
            self.assertEqual(bool(self.search(local=[market(rows=[row])]).offers), expected)

    def test_zero_price(self):
        row = item(**({'sell': 0} if self.side == TradeSide.SELL else {'buy': 0}))
        self.assertFalse(self.search(local=[market(rows=[row])]).offers)

    def test_missing_commodity_supersedes_old_quote(self):
        self.assertFalse(self.search(local=[market(rows=[])], community=[self.quote(mid=1, stamp=NOW-timedelta(seconds=1))]).offers)

    def test_ttl(self):
        for delta, expected in ((timedelta(hours=24), True), (timedelta(hours=24, seconds=-1), True), (timedelta(seconds=-1), False)):
            self.assertEqual(bool(self.search(local=[market(stamp=NOW-delta)]).offers), expected)

    def test_local_uses_long_user_age(self):
        q = MarketSearch(BEER.frontier_id, 'Fixture', max_age=timedelta(hours=72))
        self.assertTrue(self.search(local=[market(stamp=NOW-timedelta(hours=24))], query=q).offers)

    def test_merge_before_visible_limit(self):
        quotes = [replace(self.quote(mid=i), commander_sell_price=30000-i,
                          commander_buy_price=100+i,
                          market_updated_at=NOW-timedelta(seconds=1)) for i in range(1,101)]
        # The new local quote at ID 1 is worse; ID 101 must move into the top 100.
        local = [market(), market(mid=101, rows=[item(buy=500, sell=20000)])]
        r = self.search(local=local, community=quotes, distances={1:0,101:5})
        self.assertEqual(len(r.offers), 100)
        self.assertIn(101, [o.market_id for o in r.offers])
        self.assertNotIn(1, [o.market_id for o in r.offers])

    def test_user_age(self):
        for hours, expected in ((1, True), (2, False)):
            q = MarketSearch(BEER.frontier_id, 'Fixture', max_age=timedelta(hours=1))
            self.assertEqual(bool(self.search(local=[market(stamp=NOW-timedelta(hours=hours))],query=q).offers), expected)

    def test_spansh_age_not_local_ttl(self):
        q = MarketSearch(BEER.frontier_id, 'Fixture', max_age=timedelta(hours=72))
        self.assertTrue(self.search(local=[], community=[self.quote(stamp=NOW-timedelta(hours=24))], query=q).offers)

    def test_radius(self):
        for value, expected in ((100, True),(101, False),(None, False),(-1, False)):
            self.assertEqual(bool(self.search(distances={1:value}).offers), expected)

    def test_pad_missing(self):
        for pad in PadSize:
            self.assertEqual(bool(self.search(query=MarketSearch(BEER.frontier_id,'Fixture',required_pad=pad)).offers), pad == PadSize.ANY)

    def test_carrier_and_unknown_type(self):
        for kind in ('FleetCarrier', ''):
            self.assertFalse(self.search(local=[market(station_type=kind)]).offers)
            self.assertTrue(self.search(local=[market(station_type=kind)],query=MarketSearch(BEER.frontier_id,'Fixture',include_fleet_carriers=True)).offers)

    def test_arrival_missing(self):
        self.assertFalse(self.search(query=MarketSearch(BEER.frontier_id,'Fixture',max_distance_to_arrival_ls=1000)).offers)

    def test_common_sort_and_top_100(self):
        quotes = [replace(self.quote(mid=i), commander_sell_price=1000+i, commander_buy_price=20000+i) for i in range(2,102)]
        r = self.search(community=quotes)
        self.assertEqual(len(r.offers), 100)
        self.assertEqual(r.offers[0].provider, 'local_elite')
        prices = [o.commander_sell_price if self.side == TradeSide.SELL else o.commander_buy_price for o in r.offers]
        self.assertEqual(prices, sorted(prices, reverse=self.side == TradeSide.SELL))
        self.assertTrue(r.truncated)
        self.assertIsNone(r.community_failure)
        method = self.provider.search_sell if self.side == TradeSide.SELL else self.provider.search_buy
        self.assertEqual(method.call_args.args[0].limit, 100)
        # Only the 100 delivered provider candidates participate; no refill.
        method.assert_called_once()

    def test_failure_with_local(self):
        for status in (MarketStatus.NETWORK_ERROR, MarketStatus.TIMEOUT, MarketStatus.RATE_LIMIT, MarketStatus.INVALID_RESPONSE, MarketStatus.UNKNOWN_SYSTEM):
            r = self.search(status=status)
            self.assertEqual(r.status, MarketStatus.OK)
            self.assertEqual(r.community_failure, status)
            self.assertTrue(r.offers)
            self.assertFalse(r.truncated)

    def test_failure_without_local(self):
        r = self.search(local=[], status=MarketStatus.NETWORK_ERROR)
        self.assertIs(r, self.response)
        self.assertEqual(r.status, MarketStatus.NETWORK_ERROR)

    def test_exception_retains_local(self):
        self.assertEqual(self.search(raises=True).community_failure, MarketStatus.INVALID_RESPONSE)

    def test_fid_and_source(self):
        self.assertFalse(self.search(local=[market(fid='OTHER')]).offers)
        self.assertFalse(self.search(fid='').offers)
        self.assertFalse(self.search(local=[market(source='spansh')]).offers)

    def test_cancel_discards_local(self):
        cancel = Event(); cancel.set()
        r = self.search(cancel=cancel)
        self.assertEqual(r.status, MarketStatus.CANCELLED)
        self.assertFalse(r.offers)

    def test_truncated_independent(self):
        r = self.search(truncated=True, status=MarketStatus.TIMEOUT)
        self.assertTrue(r.truncated)
        self.assertEqual(r.community_failure, MarketStatus.TIMEOUT)


class SellTests(TradeMatrix, unittest.TestCase):
    side = TradeSide.SELL


class BuyTests(TradeMatrix, unittest.TestCase):
    side = TradeSide.BUY
