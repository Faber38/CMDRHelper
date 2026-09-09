import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import csv
import io
import json
import sqlite3
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse
from PySide6.QtWidgets import QApplication
from cmdrhelper.route_planner.models import ShipRouteRequest, CarrierRouteRequest
from cmdrhelper.route_planner.spansh_galaxy_client import SpanshGalaxyClient
from cmdrhelper.route_planner.spansh_client import SpanshFleetCarrierClient, SpanshError
from cmdrhelper.route_planner.system_resolution import resolve_system, valid_id64
from cmdrhelper.route_planner.workers import with_known_system_ids
from cmdrhelper.route_planner.route_planner_view import RoutePlannerView
from cmdrhelper.route_planner.ctsvision_csv import export_ctsvision_csv, HEADER
from cmdrhelper.i18n import tr


def ship_request(**changes):
    return replace(ShipRouteRequest('Sol', 'Alpha Centauri', False, False, False, False, False,
        'optimistic', 144., 0., 4670., 1660.14, 1.14, 6.8, 10.5, 2.5025, .011, 0.), **changes)


class ResolutionTests(unittest.TestCase):
    def variants(self):
        return [(SpanshGalaxyClient(), ship_request(), 'destination'),
                (SpanshFleetCarrierClient(), CarrierRouteRequest('Sol','Alpha Centauri',1000,5000,500), 'destinations')]

    def response(self, url, data=None):
        if '/search/systems?' in url:
            name=parse_qs(urlparse(url).query)['q'][0]
            return {'results':[{'name':name,'id64':1 if name=='Sol' else 2}]}
        if '/system/' in url:
            ident=int(url.rsplit('/',1)[1]);return {'record':{'id64':ident,'name':'Sol' if ident==1 else 'Alpha Centauri'}}
        return {'status':'ok','result':{'jumps':[{'name':'Sol','distance':0,'fuel_used':0},
            {'name':'Alpha Centauri','distance':4.377,'fuel_used':5,'fuel_in_tank':995,'tritium_in_market':5000,'has_icy_ring':False}]}}

    def test_all_known_and_name_combinations_both_routers(self):
        for client, request, target in self.variants():
            for sid,did in ((1,2),(1,None),(None,2),(None,None)):
                with self.subTest(client=type(client),ids=(sid,did)):
                    request=replace(request,source_id64=sid,destination_id64=did)
                    with patch.object(client,'_request_json',side_effect=self.response) as call:
                        route=client.calculate(request)
                    self.assertEqual([j.system for j in route.jumps],['Sol','Alpha Centauri'])
                    calls=call.call_args_list
                    payload=calls[-1].kwargs.get('data') or calls[-1].args[1]
                    self.assertEqual(payload['source'],1);self.assertEqual(payload[target],2)
                    searches=[c for c in calls if '/search/systems?' in c.args[0]]
                    self.assertEqual(len(searches),int(sid is None)+int(did is None))
                    self.assertEqual(len([c for c in calls if '/system/' in c.args[0]]),2)
                    if isinstance(request,ShipRouteRequest):
                        expected=asdict(request)
                        for key in ('source','destination','source_id64','destination_id64'):expected.pop(key)
                        for key,value in expected.items():self.assertEqual(payload[key],value)
                    else:
                        self.assertEqual(payload,dict(source=1,destinations=2,capacity=25000,mass=25000,
                            capacity_used=5000,calculate_starting_fuel=0,fuel_loaded=1000,tritium_stored=5000))

    def test_similar_empty_and_ambiguous_names_rejected_before_submission(self):
        for client,request,_ in self.variants():
            for side in ('source','destination'):
                name=getattr(request,side)
                for results in ([],[{'name':name+' A','id64':3}],
                                [{'name':name,'id64':3},{'name':name,'id64':4}]):
                    def response(url,data=None):
                        if '/search/systems?' in url and parse_qs(urlparse(url).query)['q'][0]==name:
                            return {'results':results}
                        return self.response(url,data)
                    with patch.object(client,'_request_json',side_effect=response) as call:
                        with self.assertRaises(SpanshError) as caught:client.calculate(request)
                    self.assertEqual(caught.exception.code,side+'_unknown')
                    self.assertFalse(any('/route' in c.args[0] for c in call.call_args_list))

    def test_id_and_name_must_match_detail(self):
        for record in ({'id64':2,'name':'Sol'},{'id64':1,'name':'Sol A'}, {'id64':True,'name':'Sol'}):
            with self.assertRaises(SpanshError) as caught:
                resolve_system(Mock(return_value={'record':record}),'Sol',1,'source_unknown')
            self.assertEqual(caught.exception.code,'source_unknown')

    def test_invalid_ids_rejected(self):
        for value in (0,-1,True,'1',1.5,2**64):
            call=Mock()
            with self.assertRaises(SpanshError):resolve_system(call,'Sol',value,'source_unknown')
            call.assert_not_called()

    def test_exact_name_case_and_whitespace(self):
        call=Mock(side_effect=[{'results':[{'name':'Sol','id64':1}]},{'record':{'name':'Sol','id64':1}}])
        self.assertEqual(resolve_system(call,' sol ',None,'source_unknown'),1)

    def test_detail_404_unknown_but_schema_error_distinct(self):
        for client,_,_ in self.variants():
            module=type(client).__module__
            with patch(module+'.urlopen',side_effect=HTTPError('url',404,'missing',{},io.BytesIO(b'{}'))):
                with self.assertRaises(SpanshError) as caught:
                    resolve_system(client._request_json,'Sol',1,'source_unknown')
                self.assertEqual(caught.exception.code,'source_unknown')
        with self.assertRaises(SpanshError) as caught:
            resolve_system(Mock(return_value={}), 'Sol',1,'source_unknown')
        self.assertEqual(caught.exception.code,'invalid_response')

    def test_valid_ids_can_still_have_no_route(self):
        client=SpanshGalaxyClient()
        responses=[{'record':{'name':'Sol','id64':1}}, {'record':{'name':'Alpha Centauri','id64':2}},
                   {'job':'test'}, {'status':'failed','error':'Unable to find route'}]
        with patch.object(client,'_request_json',side_effect=responses):
            with self.assertRaises(SpanshError) as caught:
                client.calculate(ship_request(source_id64=1,destination_id64=2))
        self.assertEqual(caught.exception.code,'no_route')

    def test_stored_ids_both_sides_without_mutating_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'db'
            with sqlite3.connect(path) as c:
                c.execute('CREATE TABLE systems(name TEXT,system_address INTEGER)')
                c.executemany('INSERT INTO systems VALUES (?,?)',[('Sol',1),('Alpha Centauri',2)])
            for _,request,_ in self.variants():
                result=with_known_system_ids(request,path)
                self.assertEqual((result.source_id64,result.destination_id64),(1,2))
                self.assertIsNone(request.source_id64)
                explicit=replace(request,source_id64=99)
                self.assertEqual(with_known_system_ids(explicit,path).source_id64,99)

    def test_carrier_csv_preserved(self):
        client=SpanshFleetCarrierClient()
        with patch.object(client,'_request_json',side_effect=self.response):
            route=client.calculate(CarrierRouteRequest('Sol','Alpha Centauri',1000,5000,500,1,2))
        with tempfile.TemporaryDirectory() as tmp:
            path=export_ctsvision_csv(route,Path(tmp)/'route.csv')
            with path.open(newline='') as f:rows=list(csv.reader(f))
            self.assertEqual(rows[0],list(HEADER))
            self.assertEqual(rows[2],['Alpha Centauri','4.377','','995','5000','5','No','',''])
        self.assertEqual(route.jump_count,1)
        self.assertEqual(route.estimated_tritium,5)

    def test_unresolved_ui_never_shows_ship_advice(self):
        app=QApplication.instance() or QApplication([])
        view=RoutePlannerView();self.addCleanup(view.close)
        for side in ('source','destination'):
            expected=tr('route_planner.system_'+side+'_unresolved')
            view._ship_route_failed(0,side+'_unknown','')
            view._carrier_route_failed(side+'_unknown','')
            self.assertEqual(view.ship_calculation_status.text(),expected)
            self.assertEqual(view.carrier_status.text(),expected)

    def test_view_only_attaches_current_id_to_matching_start(self):
        app=QApplication.instance() or QApplication([])
        state=SimpleNamespace(system='Sol',system_address=1)
        view=RoutePlannerView(state);self.addCleanup(view.close)
        for field in view._ship_auto_fields.values():field.setValue(1)
        view._ship_field_has_value={name:True for name in view._ship_auto_fields}
        view.set_destination_system('Alpha Centauri',2)
        for source,expected in [('Sol',1),('Other',None)]:
            view.ship_start_system.setText(source)
            with patch('cmdrhelper.route_planner.route_planner_view.ShipRouteWorker') as worker, patch.object(view._thread_pool,'start'):
                view._calculate_ship_route()
                request=worker.call_args.args[0]
            self.assertEqual(request.source_id64,expected)
            self.assertEqual(request.destination_id64,2)
        view.ship_destination_system.setText('Other destination')
        with patch('cmdrhelper.route_planner.route_planner_view.ShipRouteWorker') as worker,patch.object(view._thread_pool,'start'):
            view._calculate_ship_route()
            self.assertIsNone(worker.call_args.args[0].destination_id64)
