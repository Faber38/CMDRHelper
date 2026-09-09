import copy
import io
import json
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError

from cmdrhelper.material_traders import (
    Coordinates, MaterialTraderSearchService, SearchStatus, SpanshMaterialTraderClient,
    TraderType, is_fleet_carrier,
)
from cmdrhelper.route_planner.spansh_client import SpanshFleetCarrierClient, SpanshError
from cmdrhelper.route_planner.spansh_galaxy_client import SpanshGalaxyClient
from unittest.mock import patch


def record(kind='Raw', market=1, **extra):
    return dict(system_name='Test', name='Station', system_id64=42, market_id=market,
                system_x=3, system_y=4, system_z=0, type='Coriolis Starport',
                material_trader=kind, services=[{'name': 'Material Trader'}],
                distance_to_arrival=327.5, updated_at='2026-09-09 00:00:00+00',
                **extra)


def page(*records, count=None):
    return dict(results=list(records), count=len(records) if count is None else count)


class TraderTests(unittest.TestCase):
    def service(self, responses, **options):
        self.requests = []
        self.sleeps = []
        def opener(request, **kwargs):
            self.requests.append(request)
            value = responses.pop(0)
            if isinstance(value, Exception):
                raise value
            return io.BytesIO(value if isinstance(value, bytes) else json.dumps(value).encode())
        client = SpanshMaterialTraderClient(opener=opener, sleep=self.sleeps.append, **options)
        return MaterialTraderSearchService(client)

    def find(self, service, kind='Raw'):
        return service.find_nearest(kind, coordinates=Coordinates(0, 0, 0))

    def check_type(self, kind):
        station = record(kind)
        result = self.find(self.service([page(station), {'record': station}]), kind)
        self.assertEqual(result.status, SearchStatus.FOUND)
        self.assertEqual(result.station.trader_type.value, kind)
        payload = json.loads(self.requests[0].data)
        self.assertEqual(payload['filters'], {'material_trader': {'value': [kind]}})
        self.assertEqual(self.requests[1].full_url, 'https://spansh.co.uk/api/station/1')

    def test_raw(self): self.check_type('Raw')
    def test_manufactured(self): self.check_type('Manufactured')
    def test_encoded(self): self.check_type('Encoded')

    def test_wrong_type_is_rejected(self):
        result = self.find(self.service([page(record('Encoded'))]))
        self.assertEqual(result.status, SearchStatus.NOT_FOUND)
        self.assertEqual(len(self.requests), 1)

    def test_missing_unknown_type_not_accepted(self):
        for kind in (None, '', 'raw', 'Other'):
            with self.subTest(kind=kind):
                result = self.find(self.service([page(record(kind))]))
                self.assertEqual(result.status, SearchStatus.SCHEMA_ERROR)

    def test_carrier_exclusion(self):
        for name in ('Drake-Class Carrier', 'Fleet Carrier', 'FleetCarrier', 'Squadron Carrier'):
            self.assertTrue(is_fleet_carrier(name))
            r = record(); r['type'] = name
            self.assertEqual(self.find(self.service([page(r)])).status, SearchStatus.NOT_FOUND)
        self.assertFalse(is_fleet_carrier('Mega ship'))

    def test_invalid_candidates_skipped(self):
        invalid = record(market=2); invalid.pop('system_x')
        valid = record()
        result = self.find(self.service([page(record('Encoded', market=3), invalid, valid), {'record': valid}]))
        self.assertEqual(result.status, SearchStatus.FOUND)

    def test_required_fields(self):
        for key in ('system_name', 'name', 'system_id64', 'market_id', 'type', 'system_x'):
            r = record(); r.pop(key)
            self.assertEqual(self.find(self.service([page(r)])).status, SearchStatus.SCHEMA_ERROR)

    def test_local_distance_and_order_ignore_source_distance(self):
        far = record(market=2); far.update(system_x=100, distance=0)
        near = record(); near['distance'] = 9999
        result = self.find(self.service([page(far, near), {'record': near}]))
        self.assertEqual(result.station.distance_ly, 5)
        self.assertEqual(result.station.market_id, 1)

    def test_detail_is_authoritative_for_metadata(self):
        r = record(); detail = copy.deepcopy(r)
        detail.update(distance_to_arrival=600, updated_at='2026-09-09 01:00:00+00', has_large_pad=True,
                      large_pads=9, medium_pads=18, small_pads=17, is_planetary=False,
                      state='Damaged', docking_access='unknown', system_needs_permit=True)
        result = self.find(self.service([page(r), {'record': detail}]))
        self.assertEqual(result.station.arrival_distance_raw, 600)
        self.assertEqual(result.station.source_updated_at, detail['updated_at'])
        self.assertTrue(result.station.large_pad)
        self.assertEqual(result.station.large_pads, 9)
        self.assertEqual(result.station.medium_pads, 18)
        self.assertEqual(result.station.small_pads, 17)
        self.assertFalse(result.station.planetary)
        self.assertFalse(result.station.access_verified)
        self.assertTrue(result.station.permit_required)
        self.assertEqual(result.station.station_state, 'Damaged')
        self.assertIsNotNone(result.station.retrieved_at.tzinfo)

    def test_detail_changes_invalidate_candidate(self):
        for key, value in [('material_trader', 'Encoded'), ('type', 'Drake-Class Carrier'),
                           ('services', []), ('market_id', 9), ('system_id64', 99),
                           ('system_x', 10), ('system_name', 'Other')]:
            with self.subTest(key=key):
                r = record(); detail = dict(r); detail[key] = value
                result = self.find(self.service([page(r), {'record': detail}]))
                self.assertEqual(result.status, SearchStatus.DETAIL_VALIDATION_FAILED)

    def test_next_candidate_after_failed_detail(self):
        r, next_r = record(), record(market=2)
        detail = dict(r); detail['material_trader'] = 'Encoded'
        result = self.find(self.service([page(r, next_r), {'record': detail}, {'record': next_r}]))
        self.assertEqual(result.station.market_id, 2)

    def test_missing_detail_record(self):
        self.assertEqual(self.find(self.service([page(record()), {'record': None}])).status,
                         SearchStatus.DETAIL_VALIDATION_FAILED)
        self.assertEqual(self.find(self.service([page(record()), {}])).status, SearchStatus.SCHEMA_ERROR)

    def test_detail_404(self):
        error = HTTPError('url', 404, 'gone', {}, io.BytesIO(b''))
        self.assertEqual(self.find(self.service([page(record()), error])).status,
                         SearchStatus.DETAIL_VALIDATION_FAILED)

    def test_timeout_and_bounded_retry(self):
        result = self.find(self.service([TimeoutError(), TimeoutError()]))
        self.assertEqual(result.status, SearchStatus.TIMEOUT)
        self.assertEqual(len(self.requests), 2)
        self.assertIn(2.0, self.sleeps)

    def test_network_error_not_empty_result(self):
        result = self.find(self.service([URLError('offline'), URLError('offline')]))
        self.assertEqual(result.status, SearchStatus.NETWORK_ERROR)

    def test_url_wrapped_timeout(self):
        self.assertEqual(self.find(self.service([URLError(TimeoutError())], retries=0)).status, SearchStatus.TIMEOUT)

    def test_http_failure_not_retried(self):
        error = HTTPError('url', 403, 'blocked', {}, io.BytesIO(b''))
        result = self.find(self.service([error]))
        self.assertEqual((result.status, result.http_status), (SearchStatus.HTTP_ERROR, 403))
        self.assertEqual(len(self.requests), 1)

    def test_rate_limit_retry_after(self):
        error = HTTPError('url', 429, 'limited', {'Retry-After': '5'}, io.BytesIO(b''))
        result = self.find(self.service([error, page()]))
        self.assertEqual(result.status, SearchStatus.NOT_FOUND)
        self.assertIn(5, self.sleeps)

    def test_long_retry_after_aborts(self):
        error = HTTPError('url', 429, 'limited', {'Retry-After': '120'}, io.BytesIO(b''))
        result = self.find(self.service([error]))
        self.assertEqual(result.status, SearchStatus.HTTP_ERROR)
        self.assertEqual(len(self.requests), 1)

    def test_invalid_json(self):
        self.assertEqual(self.find(self.service([b'{not JSON'])).status, SearchStatus.INVALID_JSON)
        self.assertEqual(len(self.requests), 1)

    def test_schema_errors(self):
        for value in ([], {}, {'results': None, 'count': 0}, {'results': [], 'count': '0'}):
            self.assertEqual(self.find(self.service([value])).status, SearchStatus.SCHEMA_ERROR)

    def test_empty_search(self):
        self.assertEqual(self.find(self.service([page()])).status, SearchStatus.NOT_FOUND)

    def test_pagination_and_search_limit(self):
        wrong = [record('Encoded', market=i) for i in range(10)]
        result = self.find(self.service([page(*wrong, count=100)] * 3))
        self.assertEqual(result.status, SearchStatus.SEARCH_LIMIT)
        self.assertEqual([json.loads(r.data)['page'] for r in self.requests], [0, 1, 2])

    def test_valid_candidate_on_second_page(self):
        wrong = [record('Encoded', market=i) for i in range(10)]
        r = record()
        result = self.find(self.service([page(*wrong, count=11), page(r, count=11), {'record': r}]))
        self.assertEqual(result.status, SearchStatus.FOUND)

    def test_detail_limit(self):
        records = [record(market=i) for i in range(9)]
        result = self.find(self.service([page(*records)] + [{'record': None}] * 5))
        self.assertEqual(result.status, SearchStatus.DETAIL_VALIDATION_FAILED)
        self.assertEqual(len(self.requests), 6)

    def test_cache_expiry_and_original_retrieval_time(self):
        r = record(); service = self.service([page(r), {'record': r}, page(r), {'record': r}])
        now = [0]; service.clock = lambda: now[0]
        first = self.find(service)
        now[0] = 299
        cached = self.find(service)
        self.assertTrue(cached.from_cache)
        self.assertEqual(cached.station.retrieved_at, first.station.retrieved_at)
        now[0] = 300
        self.assertFalse(self.find(service).from_cache)
        self.assertEqual(len(self.requests), 4)

    def test_cache_separates_types_and_origins(self):
        service = self.service([page()] * 4)
        for kind in TraderType: self.find(service, kind)
        service.find_nearest('Raw', coordinates=Coordinates(1, 0, 0))
        self.assertEqual(len(self.requests), 4)

    def test_errors_not_cached(self):
        service = self.service([b'bad', page()])
        self.assertEqual(self.find(service).status, SearchStatus.INVALID_JSON)
        self.assertEqual(self.find(service).status, SearchStatus.NOT_FOUND)

    def test_cache_is_bounded(self):
        service = self.service([page()] * 40)
        for i in range(40): service.find_nearest('Raw', coordinates=Coordinates(i, 0, 0))
        self.assertEqual(len(service._cache), 32)

    def test_missing_coordinates_and_name(self):
        service = self.service([])
        self.assertEqual(service.find_nearest('Raw').status, SearchStatus.INVALID_INPUT)
        for values in ((None, 0, 0), (float('nan'), 0, 0), (True, 0, 0)):
            with self.assertRaises(ValueError): Coordinates(*values)

    def test_system_name_resolution(self):
        r = record()
        service = self.service([{'results': [{'name': 'Sol', 'id64': 1}]},
                                {'record': {'name': 'Sol', 'x': 0, 'y': 0, 'z': 0}}, page(r), {'record': r}])
        self.assertEqual(service.find_nearest('Raw', system_name='Sol').station.distance_ly, 5)

    def test_unknown_reference(self):
        service = self.service([{'results': []}])
        self.assertEqual(service.find_nearest('Raw', system_name='Missing').status, SearchStatus.REFERENCE_UNKNOWN)

    def test_reference_without_coords(self):
        service = self.service([{'results': [{'name': 'Sol', 'id64': 1}]}, {'record': {'name': 'Sol'}}])
        self.assertEqual(service.find_nearest('Raw', system_name='Sol').status, SearchStatus.SCHEMA_ERROR)

    def test_request_contains_no_commander_or_inventory(self):
        service = self.service([page()])
        service.find_nearest('Raw', system_name='Local only', coordinates=Coordinates(0, 0, 0))
        payload = json.loads(self.requests[0].data)
        self.assertEqual(set(payload), {'filters', 'sort', 'size', 'page', 'reference_coords'})
        self.assertEqual(set(payload['filters']), {'material_trader'})
        self.assertNotIn('Local only', self.requests[0].data.decode())
        self.assertNotIn('Authorization', self.requests[0].headers)

    def test_arrival_unit_stays_unknown(self):
        r = record()
        result = self.find(self.service([page(r), {'record': r}]))
        self.assertEqual(result.station.arrival_distance_unit, 'unknown')
        self.assertEqual(result.station.arrival_distance_raw, 327.5)
        self.assertIsNone(result.station.large_pad)
        self.assertIsNone(result.station.permit_required)

    def test_real_arrival_references_preserve_raw_values_without_inference(self):
        fixture = json.loads((Path(__file__).parent / 'fixtures/material_trader_arrival_reference.json').read_text())
        for observation in fixture['observations']:
            r = record(market=observation['market_id'])
            r['distance_to_arrival'] = observation['spansh_raw']
            result = self.find(self.service([page(r), {'record': r}]))
            self.assertEqual(result.station.arrival_distance_raw, observation['spansh_raw'])
            self.assertEqual(result.station.arrival_distance_unit, fixture['arrival_unit'])

    def test_no_qt_dependency(self):
        import subprocess
        import sys
        subprocess.run([sys.executable, '-B', '-c',
                        "import sys; import cmdrhelper.material_traders; "
                        "assert not any(n.startswith('PySide6') for n in sys.modules)"], check=True)

    def test_unknown_optional_values_remain_unknown(self):
        r = record(has_large_pad='false', large_pads=-1, is_planetary=1)
        result = self.find(self.service([page(r), {'record': r}]))
        self.assertIsNone(result.station.large_pad)
        self.assertIsNone(result.station.large_pads)
        self.assertIsNone(result.station.planetary)

    def test_detail_transport_failure_remains_transport_failure(self):
        result = self.find(self.service([page(record()), TimeoutError()], retries=0))
        self.assertEqual(result.status, SearchStatus.TIMEOUT)

    def test_invalid_trader_type_does_not_request(self):
        self.assertEqual(self.find(self.service([]), 'Other').status, SearchStatus.INVALID_INPUT)
        self.assertEqual(self.requests, [])


class RouteTransportRegressionTests(unittest.TestCase):
    def clients(self):
        return [('cmdrhelper.route_planner.spansh_client', SpanshFleetCarrierClient()),
                ('cmdrhelper.route_planner.spansh_galaxy_client', SpanshGalaxyClient())]

    def test_form_transport_preserved(self):
        for module, client in self.clients():
            with patch(module + '.urlopen', return_value=io.BytesIO(b'{"ok":true}')) as opener:
                self.assertEqual(client._request_json('https://spansh.co.uk/api/test', {'source': 'Sol A'}), {'ok': True})
                self.assertEqual(opener.call_args.args[0].data, b'source=Sol+A')
                self.assertEqual(opener.call_args.kwargs['timeout'], 15)

    def test_existing_error_codes_preserved(self):
        for module, client in self.clients():
            for failure, code in [(TimeoutError(), 'timeout'), (URLError('offline'), 'unreachable'),
                                  (HTTPError('url', 503, 'down', {}, io.BytesIO(b'')), 'server_error')]:
                with patch(module + '.urlopen', side_effect=failure):
                    with self.assertRaises(SpanshError) as caught: client._request_json('https://spansh.co.uk/api/test')
                    self.assertEqual(caught.exception.code, code)
            with patch(module + '.urlopen', return_value=io.BytesIO(b'invalid')):
                with self.assertRaises(SpanshError) as caught: client._request_json('https://spansh.co.uk/api/test')
                self.assertEqual(caught.exception.code, 'invalid_response')

    def test_galaxy_list_response_preserved(self):
        with patch('cmdrhelper.route_planner.spansh_galaxy_client.urlopen', return_value=io.BytesIO(b'["Sol"]')):
            self.assertEqual(SpanshGalaxyClient()._request_json('https://spansh.co.uk/api/systems', expected_type=list), ['Sol'])
