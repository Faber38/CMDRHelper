"""Offline provider contracts. All station/market responses are synthetic."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from http.client import IncompleteRead
import io
import json
from threading import Event, Thread
import unittest
from urllib.error import HTTPError, URLError

from cmdrhelper.commodity_master import lookup_by_symbol
from cmdrhelper.market_data import MarketSearch, MarketStatus, PadSize
from cmdrhelper.spansh_market import SpanshMarketProvider


NOW = datetime(2026, 9, 20, 20, 32, tzinfo=timezone.utc)
REFERENCE = 'Preae Aihm EH-D d12-64'


def station(name="Giant's Rest", market_id=1, *, price=63092, age=3600, **extra):
    row = dict(name=name, market_id=market_id, system_name=REFERENCE, system_id64=2210138181099,
               type='Planetary Outpost', distance=50, distance_to_arrival=613,
               has_large_pad=True, large_pads=1, medium_pads=0, small_pads=0,
               market_updated_at=(NOW-timedelta(seconds=age)).isoformat(),
               market=[dict(commodity='Platinum', buy_price=0, supply=0,
                            sell_price=price, demand=6737)])
    row.update(extra)
    return row


def response(*rows, count=None):
    return dict(reference=dict(name=REFERENCE, id64=2210138181099),
                results=list(rows), count=len(rows) if count is None else count)


class Harness:
    def __init__(self, *answers, **options):
        self.answers = list(answers) or [response(station())]
        self.requests, self.waits = [], []
        self.seconds = 1000
        self.now = NOW
        self.provider = SpanshMarketProvider(opener=self.open, clock=lambda: self.seconds,
                                            utcnow=lambda: self.now, sleep=self.sleep, **options)

    def advance(self, seconds):
        self.seconds += seconds
        self.now += timedelta(seconds=seconds)

    def sleep(self, seconds):
        self.waits.append(seconds)
        self.advance(seconds)

    def open(self, request, *, timeout):
        self.requests.append((request, timeout))
        if request.method == 'GET':
            return io.BytesIO(json.dumps({'values': ['Outpost', 'Planetary Outpost',
                                                     'Fleet Carrier', 'Drake-Class Carrier']}).encode())
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        if callable(answer):
            answer = answer(request)
        return io.BytesIO(answer if isinstance(answer, bytes) else json.dumps(answer).encode())

    @property
    def payloads(self):
        return [json.loads(r.data) for r, _ in self.requests if r.method == 'POST']


def query(**changes):
    return MarketSearch('Platinum', REFERENCE, **changes)


def http(code, retry=None, body=b'{}'):
    return HTTPError('https://spansh.co.uk/api/stations/search', code, 'failure',
                     {'Retry-After': retry} if retry is not None else {}, io.BytesIO(body))


class MarketProviderTests(unittest.TestCase):
    def test_sell_request_and_real_context(self):
        h = Harness()
        r = h.provider.search_sell(query(minimum_quantity=101))
        self.assertEqual(r.status, MarketStatus.OK)
        p = h.payloads[0]
        self.assertEqual(p['reference_system'], REFERENCE)
        self.assertEqual(p['filters']['distance'], {'min': 0, 'max': 100})
        self.assertEqual(p['filters']['market'][0], {
            'name': 'Platinum', 'sell_price': {'comparison': '<=>', 'value': [1, 2147483647]},
            'demand': {'comparison': '<=>', 'value': [101, 2147483647]}})
        self.assertEqual(p['sort'], [{'market_sell_price': [{'name': 'Platinum', 'direction': 'desc'}]}])
        self.assertEqual(h.requests[-1][1], 10)

    def test_buy_request(self):
        h = Harness(response())
        self.assertEqual(h.provider.search_buy(query(minimum_quantity=42)).status, MarketStatus.NO_RESULTS)
        p = h.payloads[0]
        self.assertEqual(p['filters']['market'][0]['supply']['value'][0], 42)
        self.assertEqual(p['filters']['market'][0]['buy_price']['value'][0], 1)
        self.assertNotIn('demand', p['filters']['market'][0])
        self.assertEqual(p['sort'], [{'market_buy_price': [{'name': 'Platinum', 'direction': 'asc'}]}])

    def test_giants_rest_price_semantics(self):
        offer = Harness().provider.search_sell(query()).offers[0]
        self.assertEqual((offer.commander_buy_price, offer.commander_sell_price), (0, 63092))
        self.assertEqual((offer.supply, offer.demand), (0, 6737))
        self.assertFalse(hasattr(offer, 'sell_price'))
        self.assertFalse(hasattr(offer, 'buy_price'))

    def test_buy_offer_semantics(self):
        row = station()
        row['market'][0].update(buy_price=100, supply=50, sell_price=90, demand=0)
        r = Harness(response(row)).provider.search_buy(query(minimum_quantity=50))
        self.assertEqual(r.offers[0].commander_buy_price, 100)
        self.assertEqual(r.offers[0].commander_sell_price, 90)

    def test_commodity_master_id_symbol_and_wrapper(self):
        item = lookup_by_symbol('Platinum')
        h = Harness()
        for identity in (item.frontier_id, 'platinum', '$platinum_name;'):
            r = h.provider.search_sell(replace(query(), commodity=identity))
            self.assertEqual(r.offers[0].commodity_id, item.frontier_id)
            self.assertEqual(r.offers[0].commodity_symbol, 'Platinum')
        self.assertEqual(len(h.payloads), 1)

    def test_underscore_symbol_preserved(self):
        item = lookup_by_symbol('M_TissueSample_Fluid')
        row = station()
        row['market'][0]['commodity'] = item.english_name
        h = Harness(response(row))
        r = h.provider.search_sell(replace(query(), commodity='$m_tissuesample_fluid_name;'))
        self.assertEqual(r.offers[0].commodity_symbol, 'M_TissueSample_Fluid')
        self.assertEqual(h.payloads[0]['filters']['market'][0]['name'], item.english_name)

    def test_unknown_future_commodity_preserved_without_http(self):
        h = Harness()
        q = replace(query(), commodity='$Future_Resource_name;')
        r = h.provider.search_sell(q)
        self.assertEqual(r.status, MarketStatus.UNKNOWN_COMMODITY)
        self.assertEqual(r.query.commodity, '$Future_Resource_name;')
        self.assertEqual(h.requests, [])

    def test_unknown_future_row_does_not_replace_requested_commodity(self):
        row = station()
        row['market'].insert(0, dict(commodity='Future Resource', sell_price=999999))
        r = Harness(response(row)).provider.search_sell(query())
        self.assertEqual(r.offers[0].commander_sell_price, 63092)

    def test_age_filter_payload(self):
        h = Harness()
        h.provider.search_sell(query(max_age=timedelta(hours=2)))
        low, high = h.payloads[0]['filters']['market_updated_at']['value']
        self.assertEqual(datetime.fromisoformat(low), NOW-timedelta(hours=2))
        self.assertEqual(datetime.fromisoformat(high), NOW)

    def test_old_high_price_excluded(self):
        h = Harness(response(station(price=999999, age=90000), station('Recent', 2, price=100)))
        self.assertEqual([o.station_name for o in h.provider.search_sell(query()).offers], ['Recent'])

    def test_future_missing_and_naive_market_dates_excluded(self):
        for date in (None, 'invalid', NOW.replace(tzinfo=None).isoformat(), (NOW+timedelta(hours=1)).isoformat()):
            with self.subTest(date=date):
                h = Harness(response(station(market_updated_at=date)))
                self.assertEqual(h.provider.search_sell(query()).offers, ())

    def test_market_and_retrieval_timestamps_distinct(self):
        h = Harness()
        r = h.provider.search_sell(query(include_fleet_carriers=True))
        self.assertEqual(r.offers[0].retrieved_at, NOW)
        self.assertEqual(r.offers[0].market_updated_at, NOW-timedelta(hours=1))

    def test_local_quantity_and_radius_defense(self):
        h = Harness(response(station(distance=101), station('Low demand', 2)))
        r = h.provider.search_sell(query(minimum_quantity=7000))
        self.assertEqual(r.status, MarketStatus.NO_RESULTS)

    def test_positive_price_required(self):
        for price in (0, -1, None, '100', True):
            with self.subTest(price=price):
                self.assertEqual(Harness(response(station(price=price))).provider.search_sell(query()).offers, ())

    def test_carriers_excluded_by_default_server_and_local(self):
        h = Harness(response(station(type='Drake-Class Carrier')))
        self.assertEqual(h.provider.search_sell(query()).offers, ())
        self.assertEqual(h.payloads[0]['filters']['type']['value'], ['Outpost', 'Planetary Outpost'])

    def test_carriers_included_and_access_preserved(self):
        h = Harness(response(station(type='Fleet Carrier', carrier_docking_access='friends')))
        r = h.provider.search_sell(query(include_fleet_carriers=True))
        self.assertTrue(r.offers[0].is_fleet_carrier)
        self.assertEqual(r.offers[0].carrier_docking_access, 'friends')
        self.assertNotIn('type', h.payloads[0]['filters'])
        self.assertEqual(len(h.requests), 1)

    def test_large_pad_filter(self):
        h = Harness()
        self.assertEqual(h.provider.search_sell(query(required_pad=PadSize.LARGE)).offers[0].largest_pad, PadSize.LARGE)
        self.assertEqual(h.payloads[0]['filters']['has_large_pad'], {'value': True})

    def test_medium_includes_large_and_medium(self):
        h = Harness(response(station()), response(station('Medium', 2, has_large_pad=False,
                                                         large_pads=0, medium_pads=1)))
        r = h.provider.search_sell(query(required_pad=PadSize.MEDIUM))
        self.assertEqual({o.largest_pad for o in r.offers}, {PadSize.LARGE, PadSize.MEDIUM})
        self.assertEqual(h.payloads[1]['filters']['medium_pads']['value'][0], 1)

    def test_small_pad_three_branches(self):
        h = Harness(response(station()), response(), response(station('Small', 3, has_large_pad=False,
                                                                     large_pads=0, small_pads=1)))
        r = h.provider.search_sell(query(required_pad=PadSize.SMALL))
        self.assertEqual({o.largest_pad for o in r.offers}, {PadSize.SMALL, PadSize.LARGE})
        self.assertNotIn('medium_pads', h.payloads[2]['filters'])
        self.assertNotIn('has_large_pad', h.payloads[2]['filters'])
        self.assertEqual(h.payloads[2]['filters']['small_pads']['value'][0], 1)

    def test_unknown_pad_any_only(self):
        row = station(has_large_pad=None, large_pads=None, medium_pads=None, small_pads=None)
        self.assertEqual(len(Harness(response(row)).provider.search_sell(query()).offers), 1)
        self.assertEqual(Harness(response(row)).provider.search_sell(query(required_pad=PadSize.LARGE)).offers, ())

    def test_medium_does_not_require_known_large_flag(self):
        row = station(has_large_pad=None, large_pads=None, medium_pads=1)
        h = Harness(response(), response(row))
        r = h.provider.search_sell(query(required_pad=PadSize.MEDIUM))
        self.assertEqual(r.offers[0].largest_pad, PadSize.MEDIUM)
        self.assertNotIn('has_large_pad', h.payloads[1]['filters'])

    def test_star_distance_server_and_local(self):
        h = Harness()
        self.assertEqual(h.provider.search_sell(query(max_distance_to_arrival_ls=500)).offers, ())
        self.assertEqual(h.payloads[0]['filters']['distance_to_arrival']['value'], [0, 500])

    def test_cache_hit_preserves_retrieved_at(self):
        h = Harness()
        first = h.provider.search_sell(query())
        h.advance(60)
        second = h.provider.search_sell(query())
        self.assertTrue(second.from_cache)
        self.assertEqual(first.offers, second.offers)
        self.assertEqual(len(h.payloads), 1)

    def test_cache_expiry(self):
        h = Harness(response(station()), response(station()), cache_ttl=5)
        h.provider.search_sell(query())
        h.advance(5)
        self.assertFalse(h.provider.search_sell(query()).from_cache)
        self.assertEqual(len(h.payloads), 2)

    def test_cache_rechecks_market_age_without_request(self):
        h = Harness(response(station(age=86300)))
        h.provider.search_sell(query())
        h.advance(200)
        r = h.provider.search_sell(query())
        self.assertTrue(r.from_cache)
        self.assertEqual(r.status, MarketStatus.NO_RESULTS)
        self.assertEqual(len(h.payloads), 1)

    def test_all_filter_dimensions_in_cache_key(self):
        changes = [dict(radius_ly=50), dict(minimum_quantity=2), dict(max_age=timedelta(hours=2)),
                   dict(include_fleet_carriers=True), dict(required_pad=PadSize.LARGE),
                   dict(max_distance_to_arrival_ls=100), dict(limit=5), dict(commodity='Gold'),
                   dict(reference_system='Other')]
        for change in changes:
            with self.subTest(change=change):
                h = Harness(response(), response())
                h.provider.search_sell(query())
                h.provider.search_sell(replace(query(), **change))
                self.assertEqual(len(h.payloads), 2)

    def test_buy_sell_separate_cache_keys(self):
        h = Harness(response(), response())
        h.provider.search_sell(query())
        h.provider.search_buy(query())
        self.assertEqual(len(h.payloads), 2)

    def test_cache_capacity(self):
        h = Harness(response(), response(), response(), cache_capacity=1)
        h.provider.search_sell(query())
        h.provider.search_sell(query(radius_ly=50))
        h.provider.search_sell(query())
        self.assertEqual(len(h.payloads), 3)

    def test_no_results_is_successful_empty_and_cached(self):
        h = Harness(response())
        self.assertEqual(h.provider.search_buy(query()).status, MarketStatus.NO_RESULTS)
        self.assertTrue(h.provider.search_buy(query()).from_cache)

    def test_unknown_system_error_and_null_reference(self):
        for answer in ({'error': 'Reference system not found'}, {**response(), 'reference': None},
                       http(400, body=b'{"error":"Unknown reference system"}')):
            with self.subTest(answer=answer):
                self.assertEqual(Harness(answer).provider.search_sell(query()).status, MarketStatus.UNKNOWN_SYSTEM)

    def test_reference_mismatch_is_invalid_response(self):
        data = response()
        data['reference']['name'] = 'Wrong system'
        self.assertEqual(Harness(data).provider.search_sell(query()).status, MarketStatus.INVALID_RESPONSE)

    def test_timeout(self):
        self.assertEqual(Harness(TimeoutError(), retries=0).provider.search_sell(query()).status, MarketStatus.TIMEOUT)

    def test_network_error(self):
        self.assertEqual(Harness(URLError('offline'), retries=0).provider.search_sell(query()).status, MarketStatus.NETWORK_ERROR)

    def test_truncated_http_body_is_network_error(self):
        r = Harness(IncompleteRead(b'{'), retries=0).provider.search_sell(query())
        self.assertEqual(r.status, MarketStatus.NETWORK_ERROR)

    def test_http_error(self):
        r = Harness(http(403)).provider.search_sell(query())
        self.assertEqual((r.status, r.http_status), (MarketStatus.HTTP_ERROR, 403))

    def test_rate_limit_preserved_and_cross_query_cooldown(self):
        h = Harness(http(429, '120'))
        r = h.provider.search_sell(query())
        self.assertEqual((r.status, r.retry_after), (MarketStatus.RATE_LIMIT, '120'))
        self.assertEqual(h.provider.search_buy(query()).status, MarketStatus.RATE_LIMIT)
        self.assertEqual(len(h.payloads), 1)

    def test_retry_after_seconds_honored(self):
        h = Harness(http(429, '3'), response())
        self.assertEqual(h.provider.search_sell(query()).status, MarketStatus.NO_RESULTS)
        self.assertIn(3, h.waits)
        self.assertEqual(len(h.payloads), 2)

    def test_retry_after_date_honored(self):
        h = Harness(http(429, format_datetime(NOW+timedelta(seconds=5))), response())
        self.assertEqual(h.provider.search_sell(query(include_fleet_carriers=True)).status, MarketStatus.NO_RESULTS)
        self.assertIn(5, h.waits)

    def test_invalid_retry_after_does_not_retry_early(self):
        for value in ('invalid', 'NaN', 'Infinity'):
            with self.subTest(value=value):
                h = Harness(http(429, value))
                self.assertEqual(h.provider.search_sell(query()).status, MarketStatus.RATE_LIMIT)
                self.assertEqual(len(h.payloads), 1)

    def test_transient_retry_bounded(self):
        h = Harness(URLError('offline'), URLError('offline'))
        self.assertEqual(h.provider.search_sell(query()).status, MarketStatus.NETWORK_ERROR)
        self.assertEqual(len(h.payloads), 2)

    def test_invalid_json(self):
        self.assertEqual(Harness(b'{broken').provider.search_sell(query()).status, MarketStatus.INVALID_JSON)

    def test_invalid_response(self):
        for data in ([], {}, {'error': 'backend failed'}, {**response(), 'count': True}):
            with self.subTest(data=data):
                self.assertEqual(Harness(data).provider.search_sell(query()).status, MarketStatus.INVALID_RESPONSE)

    def test_invalid_query_no_http(self):
        for changes in (dict(radius_ly=float('nan')), dict(radius_ly=-1), dict(limit=0),
                        dict(minimum_quantity=True), dict(max_age=timedelta(0)), dict(required_pad='large')):
            with self.subTest(changes=changes):
                h = Harness()
                self.assertEqual(h.provider.search_sell(replace(query(), **changes)).status, MarketStatus.INVALID_QUERY)
                self.assertEqual(h.requests, [])

    def test_pagination_limit_and_local_sort(self):
        h = Harness(response(station('Z', 1, price=100), count=3),
                    response(station('A', 2, price=300), count=3),
                    response(station('B', 3, price=200), count=3), page_size=1)
        r = h.provider.search_sell(query(limit=2))
        self.assertEqual([o.station_name for o in r.offers], ['A', 'B'])
        self.assertEqual([p['page'] for p in h.payloads], [0, 1, 2])
        self.assertTrue(r.truncated)

    def test_page_cap_marks_incomplete_results(self):
        h = Harness(*(response(station(market_id=i), count=100) for i in range(1, 4)),
                    page_size=1, max_pages=3)
        r = h.provider.search_sell(query())
        self.assertTrue(r.truncated)
        self.assertEqual(len(h.payloads), 3)

    def test_sort_age_distance_station_tiebreakers(self):
        rows = [station('Far', 1, age=50, distance=90), station('Old', 2, age=100),
                station('Z', 3, age=50, distance=10), station('A', 4, age=50, distance=10)]
        r = Harness(response(*rows)).provider.search_sell(query())
        self.assertEqual([o.station_name for o in r.offers], ['A', 'Z', 'Far', 'Old'])
        for row in rows:
            row['market'][0].update(buy_price=100, supply=50)
        rows[1]['market'][0]['buy_price'] = 1
        r = Harness(response(*rows)).provider.search_buy(query())
        self.assertEqual([o.station_name for o in r.offers], ['Old', 'A', 'Z', 'Far'])

    def test_cancel_before_request(self):
        cancel = Event()
        cancel.set()
        h = Harness()
        self.assertEqual(h.provider.search_sell(query(), cancel=cancel).status, MarketStatus.CANCELLED)
        self.assertEqual(h.requests, [])

    def test_cancel_during_request_discards_results(self):
        cancel = Event()
        def answer(request):
            cancel.set()
            return response(station())
        h = Harness(answer)
        r = h.provider.search_sell(query(include_fleet_carriers=True), cancel=cancel)
        self.assertEqual(r.status, MarketStatus.CANCELLED)
        self.assertEqual(r.offers, ())

    def test_request_interval_between_pages(self):
        h = Harness(response(station(), count=2), response(station(market_id=2), count=2), page_size=1)
        h.provider.search_sell(query())
        self.assertEqual(h.waits, [1, 1])

    def test_errors_not_cached(self):
        h = Harness(http(403), response())
        h.provider.search_sell(query())
        r = h.provider.search_sell(query())
        self.assertEqual(r.status, MarketStatus.NO_RESULTS)
        self.assertFalse(r.from_cache)

    def test_impossible_large_radius_rejected_without_exception(self):
        h = Harness()
        self.assertEqual(h.provider.search_sell(query(radius_ly=10**1000)).status, MarketStatus.INVALID_QUERY)

    def test_duplicate_markets_prefer_newer_report(self):
        h = Harness(response(station(age=100, price=1), station(age=50, price=2)))
        offers = h.provider.search_sell(query()).offers
        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0].commander_sell_price, 2)

    def test_cache_is_per_provider_instance(self):
        one, two = Harness(), Harness()
        one.provider.search_sell(query())
        self.assertFalse(two.provider.search_sell(query()).from_cache)

    def test_page_branches_are_fair_at_request_cap(self):
        h = Harness(*(response(station(), count=100) for _ in range(3)), max_pages=3, page_size=1)
        r = h.provider.search_sell(query(required_pad=PadSize.SMALL))
        self.assertTrue(r.truncated)
        self.assertEqual([p['page'] for p in h.payloads], [0, 0, 0])
        self.assertIn('small_pads', h.payloads[-1]['filters'])

    def test_invalid_empty_page_is_not_no_results(self):
        h = Harness(response(count=5))
        self.assertEqual(h.provider.search_sell(query()).status, MarketStatus.INVALID_RESPONSE)

    def test_provider_unknown_commodity_error(self):
        h = Harness({'error': 'Unknown commodity'})
        self.assertEqual(h.provider.search_sell(query()).status, MarketStatus.UNKNOWN_COMMODITY)

    def test_missing_star_distance_cannot_pass_explicit_filter(self):
        h = Harness(response(station(distance_to_arrival=None)))
        self.assertEqual(h.provider.search_sell(query(max_distance_to_arrival_ls=1000)).offers, ())

    def test_cancel_during_retry_wait(self):
        class CancelOnWait:
            def is_set(self):
                return False
            def wait(self, delay):
                return True
        h = Harness(http(429, '3'))
        r = h.provider.search_sell(query(include_fleet_carriers=True), cancel=CancelOnWait())
        self.assertEqual(r.status, MarketStatus.CANCELLED)
        self.assertEqual(len(h.payloads), 1)

    def test_simultaneous_identical_calls_share_request(self):
        entered, release = Event(), Event()
        results = []
        def slow(request):
            entered.set()
            if not release.wait(2):
                raise TimeoutError()
            return response(station())
        h = Harness(slow)
        def search():
            results.append(h.provider.search_sell(query(include_fleet_carriers=True)))
        first, second = Thread(target=search), Thread(target=search)
        first.start()
        self.assertTrue(entered.wait(2))
        second.start()
        release.set()
        first.join(2)
        second.join(2)
        self.assertFalse(first.is_alive() or second.is_alive())
        self.assertEqual(len(h.payloads), 1)
        self.assertEqual(sorted(r.from_cache for r in results), [False, True])

    def test_malformed_station_type_metadata_is_provider_error(self):
        h = Harness()
        h.provider.opener = lambda request, **kwargs: io.BytesIO(b'{"values": [null]}')
        self.assertEqual(h.provider.search_sell(query()).status, MarketStatus.INVALID_RESPONSE)


if __name__ == '__main__':
    unittest.main()
