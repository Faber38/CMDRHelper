import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from PySide6.QtWidgets import QApplication
from cmdrhelper.i18n import tr, get_language, set_language
from cmdrhelper.route_planner.spansh_client import SpanshError, SpanshFleetCarrierClient
from cmdrhelper.route_planner.spansh_galaxy_client import SpanshGalaxyClient, ROUTE_URL, RESULT_URL
from cmdrhelper.route_planner.route_planner_view import RoutePlannerView

MODULE = 'cmdrhelper.route_planner.spansh_galaxy_client.urlopen'
FAILURE = b'{"error":"Unable to find route","status":"failed"}'


class ShipRouteErrorTests(unittest.TestCase):
    def error(self, body, status=500):
        return HTTPError(RESULT_URL.format(job='test'), status, 'failure', {}, io.BytesIO(body))

    def test_structured_500_result_is_no_route_and_specific_ui_message(self):
        with patch(MODULE, side_effect=self.error(FAILURE)):
            with self.assertRaises(SpanshError) as caught:
                SpanshGalaxyClient()._poll('test')
        self.assertEqual(caught.exception.code, 'no_route')
        app = QApplication.instance() or QApplication([])
        view = RoutePlannerView()
        self.addCleanup(view.close)
        view._ship_route_failed(view._ship_generation, caught.exception.code, '')
        text = view.ship_calculation_status.text()
        self.assertTrue(text.startswith(tr('route_planner.ship_error_no_route')))
        self.assertIn(tr('route_planner.ship_no_route_help'), text)
        self.assertIn(tr('route_planner.ship_loadout_apply'), text)
        self.assertIn(tr('route_planner.ship_use_supercharge'), text)
        self.assertNotIn('500', text)
        self.assertNotIn('Unable to find route', text)
        self.assertTrue(view.ship_calculation_status.wordWrap())
        self.assertNotEqual(view.ship_calculation_status.text(), tr('route_planner.error_server'))

    def test_unusable_or_unrelated_500_remains_server_error(self):
        bodies = [b'', b'<html>Server error</html>', b'broken json', b'[]',
                  b'{"error":"Unable to find route"}',
                  b'{"status":"failed","error":"Internal error"}',
                  b'{"status":"ok","error":"Unable to find route"}']
        for body in bodies:
            with self.subTest(body=body), patch(MODULE, side_effect=self.error(body)):
                with self.assertRaises(SpanshError) as caught:
                    SpanshGalaxyClient()._poll('test')
                self.assertEqual(caught.exception.code, 'server_error')

    def test_submission_error_not_reclassified_as_result(self):
        with patch(MODULE, side_effect=self.error(FAILURE)):
            with self.assertRaises(SpanshError) as caught:
                SpanshGalaxyClient()._request_json(ROUTE_URL, {'source': 'Sol'})
            self.assertEqual(caught.exception.code, 'server_error')

    def test_timeout_network_and_invalid_json_remain_distinct(self):
        for error, code in [(TimeoutError(), 'timeout'), (URLError('offline'), 'unreachable')]:
            with patch(MODULE, side_effect=error):
                with self.assertRaises(SpanshError) as caught: SpanshGalaxyClient()._poll('test')
                self.assertEqual(caught.exception.code, code)
        with patch(MODULE, return_value=io.BytesIO(b'invalid')):
            with self.assertRaises(SpanshError) as caught: SpanshGalaxyClient()._poll('test')
            self.assertEqual(caught.exception.code, 'invalid_response')

    def test_successful_route_unchanged(self):
        data = {'status': 'ok', 'result': {'jumps': [
            {'name': 'Sol', 'id64': 1, 'distance': 0},
            {'name': 'Alpha Centauri', 'id64': 2, 'distance': 4.377}]}}
        with patch(MODULE, return_value=io.BytesIO(json.dumps(data).encode())):
            client = SpanshGalaxyClient()
            route = client._parse_route(client._poll('test'))
        self.assertEqual([j.system for j in route.jumps], ['Sol', 'Alpha Centauri'])
        self.assertEqual(route.jumps[1].distance, 4.377)

    def test_structured_failure_with_http_200(self):
        with patch(MODULE, return_value=io.BytesIO(FAILURE)):
            with self.assertRaises(SpanshError) as caught: SpanshGalaxyClient()._poll('test')
        self.assertEqual(caught.exception.code, 'no_route')

    def test_carrier_classification_unchanged(self):
        with patch('cmdrhelper.route_planner.spansh_client.urlopen', side_effect=self.error(FAILURE)):
            with self.assertRaises(SpanshError) as caught:
                SpanshFleetCarrierClient()._request_json(RESULT_URL.format(job='test'))
        self.assertEqual(caught.exception.code, 'server_error')

    def test_localized_help_and_separate_other_errors(self):
        app = QApplication.instance() or QApplication([])
        previous = get_language()
        self.addCleanup(set_language, previous)
        view = RoutePlannerView()
        self.addCleanup(view.close)
        for language in ('de', 'en', 'fr', 'it', 'no', 'sv', 'fi', 'pl', 'nl', 'es', 'tr', 'el'):
            set_language(language)
            view._ship_route_failed(0, 'no_route', 'HTTP 500 Unable to find route')
            text = view.ship_calculation_status.text()
            self.assertIn(tr('route_planner.ship_no_route_tip',
                             apply=tr('route_planner.ship_loadout_apply'),
                             supercharge=tr('route_planner.ship_use_supercharge')), text)
            self.assertNotIn('HTTP', text)
            self.assertNotIn('500', text)
            self.assertNotIn('{apply}', text)
            for code, key in [('server_error', 'error_server'), ('timeout', 'error_timeout'),
                              ('unreachable', 'error_unreachable'), ('invalid_response', 'error_invalid_response')]:
                view._ship_route_failed(0, code, 'raw exception HTTP 500')
                self.assertEqual(view.ship_calculation_status.text(), tr('route_planner.' + key))
