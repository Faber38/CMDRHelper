"""Goods-only action priority: journal facts and the existing shared projection."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from copy import deepcopy
from dataclasses import replace
from string import Formatter
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from cmdrhelper.cargo import normalize_inventory
from cmdrhelper.i18n import tr, set_language, get_language, _TRANSLATIONS
from cmdrhelper.journal_reader import _new_mission, _update_mission_event
from cmdrhelper.mission_manager import normalize_missions, mission_display_step
from cmdrhelper.mission_arrival import ArrivalPosition
from cmdrhelper.ui.mission_cargo import (current_mission_cargo_assessment, mission_cargo_table_text,
    MissionCarrierStock, current_mission_carrier_stock, MissionCargoStock, MissionCargoGroup,
    MissionCargoAction, mission_cargo_recommendation)
from tests import test_mission_cargo_status_carrier as fixtures


def accepted(mid=1, family='Mission_Mining'):
    return _new_mission(dict(event='MissionAccepted',timestamp='2026-11-05T12:00:00Z',
        MissionID=mid,Name=family,Commodity='$Bauxite_Name;',Commodity_Localised='Bauxit',
        Count=45,DestinationSystem='Latola',DestinationStation='Wait Colburn Gateway'))


def mission(mid=1, delivered=0, family='Mission_Mining'):
    raw=accepted(mid,family)
    if delivered is not None:
        _update_mission_event(raw,dict(event='CargoDepot',timestamp='2026-11-05T12:01:00Z',
            MissionID=mid,UpdateType='Deliver',ItemsDelivered=delivered,TotalItemsToDeliver=45))
    return normalize_missions([raw])[0]


class ActionPriorityTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(set_language,get_language());set_language('de')

    def project(self, missions, cargo, **kwargs):
        state=SimpleNamespace(commander_id=1,missions=missions)
        snapshot=None if cargo is None else {'inventory':normalize_inventory(cargo)}
        before=deepcopy((missions,snapshot))
        with patch('cmdrhelper.ui.mission_cargo.published_mission_ship_inventory',return_value=snapshot):
            pink,stocks=current_mission_cargo_assessment(state)
        result=[mission_cargo_table_text(m,stocks.get(m.mission_id),**kwargs) for m in missions]
        self.assertEqual((missions,snapshot),before)
        return result,pink

    def goods(self, amount, mid=None):
        return [dict(Name='bauxite',Count=amount,**({'MissionID':mid} if mid else {}))]

    def test_zero_partial_full_unknown_delivery_and_complete(self):
        m=mission()
        for count,step in ((0,'45 t Bauxit beschaffen/abbauen'),(20,'Weitere 25 t Bauxit beschaffen'),
                           (45,'Passende Fracht vorhanden – zum Missionsziel reisen')):
            result,_=self.project([m],self.goods(count));self.assertEqual(result[0][1],step)
        result,_=self.project([mission(delivered=None)],[])
        self.assertIn('Lieferstand prüfen',result[0][1]);self.assertIn('45 t Bauxit',result[0][1])
        result,_=self.project([m],None,at_destination=True,carrier=MissionCarrierStock(100,'manual'))
        self.assertEqual(result[0][1],'Frachtraum prüfen');self.assertNotIn('45',result[0][1])
        result,_=self.project([mission(delivered=45)],None)
        self.assertEqual(result[0][1],'Belohnung abholen')

    def test_arrival_precedes_procurement_carrier_and_travel_partial_delivery(self):
        position=ArrivalPosition()
        position.feed(dict(event='Docked',StarSystem='Latola',StationName='Wait Colburn Gateway'),1)
        m=mission();self.assertTrue(position.matches(m))
        for count in (20,45):
            result,_=self.project([m],self.goods(count),at_destination=position.matches(m),
                                 carrier=MissionCarrierStock(100,'manual'))
            self.assertEqual(result[0][1],'Bauxit abliefern')
        result,_=self.project([m],[],at_destination=True)
        self.assertEqual(result[0][1],'45 t Bauxit beschaffen/abbauen')
        m=mission(delivered=20)
        result,_=self.project([m],[]);self.assertEqual(result[0][1],'25 t Bauxit beschaffen/abbauen')
        result,_=self.project([m],self.goods(25),at_destination=True)
        self.assertEqual(result[0][1],'Bauxit abliefern')

    def test_carrier_is_separate_current_only_and_never_bypasses_ship_check(self):
        m=mission()
        for quality in ('manual','tracked'):
            carrier=MissionCarrierStock(25,quality)
            result,_=self.project([m],self.goods(20),carrier=carrier)
            self.assertIn('vom eigenen Carrier ins Schiff umladen',result[0][1])
            self.assertEqual(result[0][0],'Vom Carrier umladen')
            for bad in (replace(carrier,stale=True),MissionCarrierStock(),
                        MissionCarrierStock(quality='inconsistent'),replace(carrier,count=0)):
                result,_=self.project([m],self.goods(20),carrier=bad)
                self.assertEqual(result[0][1],'Weitere 25 t Bauxit beschaffen')
            result,_=self.project([m],self.goods(45),carrier=carrier)
            self.assertEqual(result[0][1],tr('missions.cargo_travel'))

    def test_shared_demand_and_explicit_bindings_do_not_reserve_twice(self):
        missions=[mission(),mission(2)]
        result,pink=self.project(missions,self.goods(45))
        self.assertEqual(next(iter(pink.values())).remaining,90)
        self.assertEqual(next(iter(pink.values())).coverable,45)
        for status,step,green,_ in result:
            self.assertEqual(status,'Gemeinsame Fracht vorhanden');self.assertTrue(green)
            self.assertIn('Weitere 45 t Bauxit',step);self.assertIn('Restbedarf: 90 t',step)
            self.assertIn('keine Reservierung',step)
        result,_=self.project(missions,self.goods(90))
        self.assertTrue(all(tr('missions.cargo_travel') in row[1] for row in result))
        result,_=self.project(missions,self.goods(45,1))
        self.assertEqual(result[0][1],tr('missions.cargo_travel'))
        self.assertNotIn('reisen',result[1][1]);self.assertFalse(result[1][2])
        result,_=self.project(missions,self.goods(45,999))
        self.assertTrue(all('90 t Bauxit' in row[1] for row in result))
        result,_=self.project([mission(delivered=None),mission(2)],self.goods(45))
        self.assertTrue(all('Lieferstand prüfen' in row[1] and 'unbekannt' in row[1] for row in result))

    def test_transport_pickup_and_other_types_unchanged(self):
        for delivered in (0,None):
            result,_=self.project([mission(delivered=delivered,family='Mission_Delivery')],[])
            self.assertIn('abholen',result[0][1]);self.assertNotIn('abbauen',result[0][1])
        for family in ('Mission_Courier','Mission_Assassinate','Mission_Salvage'):
            m=mission(family=family)
            with patch('cmdrhelper.ui.mission_cargo.published_mission_ship_inventory',side_effect=AssertionError):
                self.assertEqual(current_mission_cargo_assessment(SimpleNamespace(missions=[m])),({},{}))
            self.assertEqual(mission_cargo_table_text(m,None,at_destination=True)[1],mission_display_step(m))

    def test_structured_actions_and_short_status_in_all_languages(self):
        A = MissionCargoAction
        m = mission()
        cases = [
            (m, MissionCargoStock(None, None, False), {}, A.CHECK, 'check'),
            (m, MissionCargoStock(0, 0, False), {}, A.ACQUIRE, 'acquire'),
            (m, MissionCargoStock(20, 0, False), {}, A.ACQUIRE, 'present'),
            (m, MissionCargoStock(45, 0, False), {}, A.TRAVEL, 'travel'),
            (m, MissionCargoStock(20, 0, False), {'at_destination': True}, A.DELIVER, 'deliver'),
            (m, MissionCargoStock(20, 0, False),
             {'carrier': MissionCarrierStock(25, 'manual')}, A.TRANSFER, 'transfer'),
            (mission(family='Mission_Delivery'), MissionCargoStock(0, 0, False), {}, A.PICKUP, 'pickup'),
            (mission(delivered=45), None, {}, A.REWARD, 'reward'),
            (m, MissionCargoStock(45, 0, True, MissionCargoGroup(90, False)), {}, A.ACQUIRE, 'shared'),
            (m, MissionCargoStock(90, 0, True, MissionCargoGroup(90, False)), {}, A.TRAVEL, 'shared'),
            (m, MissionCargoStock(0, 0, True), {}, A.SHARED, 'acquire'),
            # A confirmed partial delivery must not hide the necessary action.
            (mission(delivered=20), MissionCargoStock(None, None, False), {}, A.CHECK, 'check'),
            (mission(delivered=20), MissionCargoStock(0, 0, False), {}, A.ACQUIRE, 'acquire'),
            (mission(delivered=20), MissionCargoStock(25, 0, False), {}, A.TRAVEL, 'travel'),
            (mission(delivered=None), MissionCargoStock(20, 0, False), {}, A.ACQUIRE, 'present'),
        ]
        for lang, translations in _TRANSLATIONS.items():
            set_language(lang)
            for m, stock, context, action, summary in cases:
                with self.subTest(language=lang, action=action, summary=summary):
                    before = deepcopy(m)
                    result = mission_cargo_recommendation(m, stock, **context)
                    self.assertEqual(result.action, action)
                    key = 'missions.summary_' + summary
                    self.assertIn(key, translations)
                    self.assertEqual(result.status, translations[key])
                    self.assertNotIn('{', result.status)
                    self.assertEqual(m, before)

    def test_all_languages_have_matching_action_placeholders(self):
        keys=[key for key in _TRANSLATIONS['de'] if key.startswith('missions.action_')]
        self.assertEqual(len(keys),9)
        for lang,table in _TRANSLATIONS.items():
            set_language(lang)
            for key in keys:
                self.assertIn(key,table)
                fields=lambda text:{f for _,f,_,_ in Formatter().parse(text) if f}
                self.assertEqual(fields(table[key]),fields(_TRANSLATIONS['de'][key]))
            result,_=self.project([mission()],self.goods(20),at_destination=True)
            self.assertIn(table['missions.action_deliver'].split('{commodity}')[0],result[0][1])
            self.assertNotIn('{',result[0][1])


class ActionUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.MissionStockUiTests.setUpClass()

    def setUp(self):
        self.fx=fixtures.MissionStockUiTests();self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.host=self.fx.host;self.state=self.fx.state
        self.state.missions=[mission()]
        self.host._refresh_missions_table();self.host.missions_table.selectRow(0)
        self.position=ArrivalPosition()
        self.host.mission_arrival.source=Mock()
        self.host.mission_arrival.source.snapshot.side_effect=lambda state:(('test',1,1),self.position,set())

    def action(self):
        text=self.host.missions_table.item(0,4).text()
        self.assertIn(tr('missions.next_step',value=text),self.host.mission_progress_text.text())
        return text

    def cargo(self, count):
        self.fx.fx.cargo([fixtures.existing.fixture.item(count,name='bauxite')])

    def test_signal_arrival_departure_carrier_completion_and_commander_switch(self):
        self.cargo(20)
        self.assertEqual(self.action(),'Weitere 25 t Bauxit beschaffen')
        inv=self.fx.controller._last_inventory
        inv.carrier={'bauxite':25};inv.carrier_records={'bauxite':inv.carrier_records['cobalt']}
        self.fx.controller.ready.emit(inv)
        self.assertIn('umladen',self.action())
        self.state.carrier_snapshot=SimpleNamespace(fid=self.state.commander_fid,carrier_id=999)
        self.fx.controller.ready.emit(inv)
        self.assertNotIn('umladen',self.action())
        self.state.carrier_snapshot=None
        self.fx.controller._dirty=True;self.fx.controller.publicationChanged.emit()
        self.assertNotIn('umladen',self.action())
        self.position.feed(dict(event='Docked',StarSystem='Latola',StationName='Wait Colburn Gateway'),1)
        self.host.mission_arrival.update()
        self.assertEqual(self.action(),'Bauxit abliefern')
        self.position.clear_arrival();self.host.mission_arrival.update()
        self.assertEqual(self.action(),'Weitere 25 t Bauxit beschaffen')
        self.cargo(45);self.assertEqual(self.action(),tr('missions.cargo_travel'))
        self.state.viewed_commander_id=2;self.state.viewedCommanderChanged.emit(2)
        self.assertEqual(self.action(),'Frachtraum prüfen')
        self.state.viewed_commander_id=1;self.state.viewedCommanderChanged.emit(1)
        self.assertEqual(self.action(),tr('missions.cargo_travel'))
        self.state.missions=[mission(delivered=45)];self.state.changed.emit()
        self.assertIn('Belohnung abholen',self.host.mission_progress_text.text())
        self.assertEqual(self.host.missions_table.item(0,4).text(),'Belohnung abholen')

    def test_initial_restored_missions_use_existing_cargo_and_all_languages(self):
        self.cargo(0)
        self.host._refresh_missions_table();self.host.missions_table.selectRow(0)
        self.assertEqual(self.action(),'45 t Bauxit beschaffen/abbauen')
        for lang in _TRANSLATIONS:
            set_language(lang)
            self.host._mission_selection_changed()
            self.assertNotIn('{',self.action())
