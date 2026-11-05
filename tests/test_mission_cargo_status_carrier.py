"""Display projections consume existing stock without altering mission facts."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from string import Formatter
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QObject, Signal, Qt, QEvent
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget
from cmdrhelper.i18n import tr, get_language, set_language, _TRANSLATIONS
from cmdrhelper.models import STATUS_ACCEPTED
from cmdrhelper.mining_controller import mining_publication_context
from cmdrhelper.mining_inventory import MiningInventory
from cmdrhelper.ui.mission_cargo import (MissionCargoStock, mission_cargo_table_text,
                                       mission_carrier_stock_text)
from cmdrhelper.ui.mission_status import MISSION_STATUS_ROLE, MISSION_CARGO_STATUS_ROLE
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.ui.main_window import MainWindow
from tests.test_missions_table_sort import Host
from tests import test_mission_cargo_usability as existing


class PublishedController(QObject):
    ready = Signal(object)
    loading = Signal()
    publicationChanged = Signal()

    def __init__(self):
        super().__init__()
        self._running = self._dirty = self._closed = False
        self._last_inventory = None


def carrier(state, count=25, quality='manual'):
    journal = state._journal_index_sessions[-1]['journal_file']
    return MiningInventory(state.commander_id, state.commander_fid,
        carrier_id=123, carrier={'cobalt':count},
        source_folder=str(Path(journal).absolute().parent), carrier_feed={'path':journal},
        carrier_ledger={'fid':state.commander_fid, 'carrier_id':123},
        carrier_records={'cobalt':{'count':count,'status':quality,
            'confirmed_at':'2026-11-05T10:00:00+00:00'}},
        publication_context=mining_publication_context(state))


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(set_language,get_language()); set_language('de')
        self.mission=existing.mission(delivered_count=0)
        self.state=SimpleNamespace(commander_id=1,viewed_commander_id=1,commander_fid='F1',
            database=SimpleNamespace(path='/tmp/test.db'),_inventory_revisions={'mining':1},
            _journal_index_sessions=[dict(journal_file='/tmp/Journal.log',commander_id=1,
                fid_seen='F1',attribution_status='identified',last_read_offset=100)])
        self.controller=PublishedController()
        self.state.mining_inventory_controller=self.controller
        self.controller._last_inventory=carrier(self.state)

    def test_status_partial_full_unknown_shared_and_delivery_priority(self):
        before=deepcopy(self.mission)
        for amount in (20,45,90):
            status,step,pink,tip=mission_cargo_table_text(self.mission,MissionCargoStock(amount,0,False))
            self.assertEqual(status,f'Fracht vorhanden ({min(amount,45)}/45 t)')
            self.assertTrue(pink)
            self.assertEqual(step, 'Weitere 25 t Kobalt beschaffen' if amount==20 else
                             'Passende Fracht vorhanden – zum Missionsziel reisen')
        unknown=replace(self.mission,delivered_count=None)
        status,step,_,tip=mission_cargo_table_text(unknown,MissionCargoStock(20,0,False))
        self.assertEqual(status,'Fracht vorhanden (20/45 t)')
        self.assertIn('Lieferstand prüfen',step); self.assertIn('Lieferstand unbekannt',tip)
        partial=replace(self.mission,delivered_count=20)
        self.assertEqual(mission_cargo_table_text(partial,MissionCargoStock(25,0,False))[0],
                         'Fracht vorhanden (25/25 t)')
        for stock in (None,MissionCargoStock(None,None,False),MissionCargoStock(0,0,False)):
            self.assertFalse(mission_cargo_table_text(self.mission,stock)[2])
            self.assertNotIn('Fracht vorhanden',mission_cargo_table_text(self.mission,stock)[0])
        shared=MissionCargoStock(45,0,True)
        for m in (self.mission,replace(self.mission,mission_id=2)):
            status,step,_,tip=mission_cargo_table_text(m,shared)
            self.assertIn('gemeinsamer Bestand',status)
            self.assertIn('keine Reservierung',step)
        self.assertFalse(mission_cargo_table_text(self.mission,MissionCargoStock(0,45,False))[2])
        done=replace(self.mission,delivered_count=45,depot_update_type='deliver')
        status,step,pink,_=mission_cargo_table_text(done,shared)
        self.assertIn('Lieferung abgeschlossen',status); self.assertFalse(pink)
        self.assertEqual(self.mission,before)

    def test_carrier_quality_revision_identity_and_no_io(self):
        inv=self.controller._last_inventory
        before=deepcopy(inv)
        with patch('sqlite3.connect',side_effect=AssertionError('No queries')), patch('builtins.open',side_effect=AssertionError('No scans')):
            text=mission_carrier_stock_text(self.state,self.mission)
        self.assertIn('Eigener Carrier 123: 25 t passend',text)
        self.assertIn('Manuell bestätigt',text); self.assertNotIn('Zuletzt bekannt',text)
        self.assertEqual(inv,before)
        self.state._journal_index_sessions[-1]['last_read_offset']=200
        self.assertNotIn('Zuletzt bekannt',mission_carrier_stock_text(self.state,self.mission))
        inv.carrier['cobalt']=inv.carrier_records['cobalt']['count']=0
        self.assertIn('0 t passend',mission_carrier_stock_text(self.state,self.mission))
        inv.carrier['cobalt']=inv.carrier_records['cobalt']['count']=25
        inv.carrier_records['cobalt']['status']='tracked'
        self.assertIn('Aus Transfers fortgeschrieben',mission_carrier_stock_text(self.state,self.mission))
        for field in ('_running','_dirty'):
            setattr(self.controller,field,True)
            self.assertIn('Zuletzt bekannt',mission_carrier_stock_text(self.state,self.mission))
            setattr(self.controller,field,False)
        self.state._inventory_revisions['mining']=2
        self.assertIn('Zuletzt bekannt',mission_carrier_stock_text(self.state,self.mission))
        inv.carrier_records['cobalt']['status']='inconsistent'
        inv.carrier_records['cobalt']['count']=None
        self.assertEqual(mission_carrier_stock_text(self.state,self.mission),'Carrier-Bestand widersprüchlich')
        self.controller._last_inventory=carrier(self.state)
        for field,value in [('commander_id',2),('viewed_commander_id',2),('commander_fid','F2'),
                            ('carrier_snapshot',SimpleNamespace(fid='F1',carrier_id=999))]:
            old=getattr(self.state,field,None); setattr(self.state,field,value)
            self.assertEqual(mission_carrier_stock_text(self.state,self.mission),'Carrier-Bestand unbekannt')
            setattr(self.state,field,old)
        inv=self.controller._last_inventory
        for field,value in [('source_folder','/other'),('carrier_id',999),('publication_context',None),
                            ('carrier_records',{}),('carrier',None)]:
            old=getattr(inv,field); setattr(inv,field,value)
            self.assertEqual(mission_carrier_stock_text(self.state,self.mission),'Carrier-Bestand unbekannt')
            setattr(inv,field,old)
        self.state._journal_index_sessions[-1]['journal_file']='/elsewhere/Journal.log'
        self.assertEqual(mission_carrier_stock_text(self.state,self.mission),'Carrier-Bestand unbekannt')

    def test_all_twelve_languages_and_placeholders(self):
        keys=('cargo_status','cargo_pool','cargo_travel','cargo_get','cargo_get_unknown',
              'carrier_unknown','carrier_inconsistent','carrier_amount','carrier_manual',
              'carrier_tracked','carrier_stale','carrier_scope')
        for language, translations in _TRANSLATIONS.items():
            set_language(language)
            for key in keys:
                key='missions.'+key
                self.assertIn(key,translations)
                fields=lambda t: {f for _,f,_,_ in Formatter().parse(t) if f}
                self.assertEqual(fields(translations[key]),fields(_TRANSLATIONS['de'][key]))
            status,step,_,_=mission_cargo_table_text(self.mission,MissionCargoStock(45,0,False))
            self.assertEqual(status,tr('missions.cargo_status',count='45',total='45'))
            self.assertEqual(step,tr('missions.cargo_travel'))
            text=mission_carrier_stock_text(self.state,self.mission)
            self.assertIn(tr('missions.carrier_amount',count='25',carrier='123'),text)
            self.assertNotIn('{',text)


class MissionStockUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        existing.UsabilityTests.setUpClass()
        cls.app=existing.UsabilityTests.app

    def setUp(self):
        self.fx=existing.UsabilityTests(); self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.state=self.fx.state
        self.state.missions=[existing.mission(status=STATUS_ACCEPTED,delivered_count=0)]
        self.state._inventory_revisions={'mining':1}
        self.controller=PublishedController()
        self.state.mining_inventory_controller=self.controller
        self.controller._last_inventory=carrier(self.state)
        # Build a new page with production signal wiring and an existing publication.
        self.host=Host(state=self.state)
        for name in ('_missions','_card','_save_missions_header_state','_mission_selection_changed','_refresh_missions_table'):
            setattr(self.host,name,getattr(MainWindow,name).__get__(self.host))
        for name in ('_format_reward','_format_expiry','_place_text','_translate_mission_text'):
            setattr(self.host,name,getattr(MainWindow,name))
        with patch('cmdrhelper.ui.bounty_view.BountyView',side_effect=lambda *a:QWidget()), patch('cmdrhelper.ui.combat_bond_view.CombatBondView',side_effect=lambda *a:QWidget()):
            self.host.page=self.host._missions()
        self.addCleanup(self.host.page.deleteLater); self.addCleanup(self.host.page.close)
        self.host._refresh_missions_table(); self.host.missions_table.selectRow(0)

    def test_transfer_delayed_publication_same_amount_completion_and_restart(self):
        table=self.host.missions_table
        item=table.item(0,3)
        self.assertEqual(item.text(),'Fracht vorhanden (45/45 t)')
        self.assertIn('Eigener Carrier 123: 25 t',self.host.mission_progress_text.text())
        # Ship learns of withdrawal before the carrier worker publishes its result.
        self.state._inventory_revisions['mining']=2
        self.controller._dirty=True
        self.controller.publicationChanged.emit()
        self.fx.cargo([existing.fixture.item(55,name='cobalt')])
        text=self.host.mission_progress_text.text()
        self.assertIn('55 t passende Ware',text)
        self.assertIn('Carrier 123: 25 t',text); self.assertIn('Zuletzt bekannt',text)
        self.assertNotIn('80 t',text)
        self.controller._last_inventory=carrier(self.state,15,'tracked')
        self.controller._dirty=False
        self.controller.ready.emit(self.controller._last_inventory)
        text=self.host.mission_progress_text.text()
        self.assertIn('Carrier 123: 15 t',text); self.assertNotIn('Zuletzt bekannt',text)
        self.assertIs(table.item(0,3),item)
        self.state.missions=[existing.mission(status=STATUS_ACCEPTED,delivered_count=45,depot_update_type='deliver')]
        self.state.changed.emit()
        self.assertIn('Lieferung abgeschlossen',item.text())
        self.assertFalse(item.data(MISSION_CARGO_STATUS_ROLE))
        self.assertNotIn('Carrier 123',self.host.mission_progress_text.text())
        self.state.missions=[];self.state.changed.emit()
        self.assertEqual(self.host.mission_progress_text.text(),'')

    def test_no_selection_updates_table_and_commander_invalidation(self):
        self.host.missions_table.clearSelection()
        self.fx.cargo([existing.fixture.item(20,name='cobalt')])
        self.assertEqual(self.host.missions_table.item(0,3).text(),'Fracht vorhanden (20/45 t)')
        self.assertEqual(self.host.missions_table.item(0,4).text(),'Weitere 25 t Kobalt beschaffen')
        self.host.missions_table.selectRow(0)
        self.state.viewed_commander_id=2; self.state.viewedCommanderChanged.emit(2)
        self.assertEqual(self.host.missions_table.item(0,3).text(),tr('mission_state.accepted'))
        self.assertIn('Carrier-Bestand unbekannt',self.host.mission_progress_text.text())

    def test_status_sort_preserves_selected_mission_after_cargo_change(self):
        self.state.missions.append(replace(self.state.missions[0],mission_id=2,
                                          name='Gold mission',commodity_symbol='gold'))
        self.host._refresh_missions_table()
        table=self.host.missions_table
        table.horizontalHeader().sectionClicked.emit(3)
        self.fx.cargo([existing.fixture.item(20,name='cobalt'),existing.fixture.item(45,name='gold')])
        for row in range(2):
            if table.item(row,0).mission.mission_id == 1:
                table.selectRow(row)
        self.fx.cargo([existing.fixture.item(45,name='cobalt'),existing.fixture.item(10,name='gold')])
        self.assertEqual([table.item(row,0).mission.mission_id for row in range(2)],[2,1])
        selected=table.selectionModel().selectedRows()[0].row()
        self.assertEqual(table.item(selected,0).mission.mission_id,1)
        self.assertTrue(table.horizontalHeader().isSortIndicatorShown())
        self.assertIn('45 t Kobalt',self.host.mission_progress_text.text())

    def test_pink_text_preserves_arrival_background_in_both_themes(self):
        table=self.host.missions_table
        self.host.page.resize(1500,800); self.host.page.show()
        arrival=self.host.mission_arrival
        arrival.identity=('source',1,1);arrival.hits={1};arrival.blink={}
        for light,style,pink in ((False,DARK_STYLESHEET,'#ff83c4'),(True,LIGHT_STYLESHEET,'#a32269')):
            self.host.page.setStyleSheet(style)
            arrival.set_light_mode(light); self.host.mission_status_delegate.set_light_mode(light)
            self.app.processEvents()
            item=table.item(0,3)
            self.assertEqual(item.data(MISSION_STATUS_ROLE),STATUS_ACCEPTED)
            for selected in (False,True):
                table.clearSelection()
                if selected: table.selectRow(0)
                rect=table.visualItemRect(item)
                image=table.viewport().grab(rect).toImage()
                target=QColor(pink)
                self.assertTrue(any(max(abs(a-b) for a,b in zip(image.pixelColor(x,y).getRgb()[:3],target.getRgb()[:3]))<20
                    for y in range(image.height()) for x in range(image.width())))
                expected=('#eadca5' if selected else '#fff4cf') if light else ('#514222' if selected else '#302918')
                self.assertEqual(image.pixelColor(image.width()-5,5).name(),expected)
                self.assertTrue(arrival.marked(table.model().index(0,3)))


class PublicationProvenanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tests.test_mining_controller import MiningControllerTests
        MiningControllerTests.setUpClass()

    def setUp(self):
        from tests.test_mining_controller import MiningControllerTests
        self.fx=MiningControllerTests(); self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.fx.state._inventory_revisions={'mining':1}
        self.fx.add_owned_carrier()

    def test_manual_confirmation_transfer_and_restart_publish_matching_revision(self):
        controller, results=self.fx.make_controller()
        self.fx.wait_for(results,1)
        state=self.fx.state
        state.mining_inventory_controller=controller
        self.assertEqual(results[-1].publication_context,mining_publication_context(state))
        controller.confirm_carrier('gold',25,(1,'F1',123))
        m=replace(existing.mission(),commodity_symbol='gold')
        self.assertIn('25 t',mission_carrier_stock_text(state,m))
        self.assertNotIn('Zuletzt bekannt',mission_carrier_stock_text(state,m))
        self.fx.events.extend([dict(event='Docked',MarketID=123,StationType='FleetCarrier'),
            dict(event='CargoTransfer',Transfers=[dict(Type='gold',Count=10,Direction='toship')])])
        self.fx.write()
        state._inventory_revisions['mining']=2
        before=len(results)
        state.changed.emit()
        self.assertIn('Zuletzt bekannt',mission_carrier_stock_text(state,m))
        self.fx.wait_for(results,before+1)
        self.assertIn('15 t',mission_carrier_stock_text(state,m))
        self.assertIn('Aus Transfers fortgeschrieben',mission_carrier_stock_text(state,m))
        self.assertNotIn('Zuletzt bekannt',mission_carrier_stock_text(state,m))
        restarted, restored=self.fx.make_controller()
        state.mining_inventory_controller=restarted
        self.assertEqual(mission_carrier_stock_text(state,m),'Carrier-Bestand unbekannt')
        self.fx.wait_for(restored,1)
        self.assertIn('15 t',mission_carrier_stock_text(state,m))
        self.assertEqual(restored[-1].publication_context,mining_publication_context(state))

    def test_late_result_keeps_start_revision_and_pending_result_is_stale(self):
        controller, results=self.fx.make_controller()
        self.fx.wait_for(results,1)
        state=self.fx.state
        state.mining_inventory_controller=controller
        controller.confirm_carrier('gold',25,(1,'F1',123))
        m=replace(existing.mission(),commodity_symbol='gold')
        jobs=[]
        with patch('cmdrhelper.mining_controller.submit',side_effect=lambda pool,job,**kw:jobs.append(job)):
            state._inventory_revisions['mining']=2
            controller.request(); controller.timer.stop(); controller._start()
            started=mining_publication_context(state)
            state._inventory_revisions['mining']=3
            controller.request(); controller.timer.stop()
            jobs[0].run()  # Deterministic delayed completion, temporary test sources only.
            self.assertEqual(results[-1].publication_context,started)
            self.assertIn('Zuletzt bekannt',mission_carrier_stock_text(state,m))
            controller.timer.stop(); controller._start()
            jobs[1].run()
            self.assertEqual(results[-1].publication_context,mining_publication_context(state))
            self.assertNotIn('Zuletzt bekannt',mission_carrier_stock_text(state,m))
            controller.timer.stop()
