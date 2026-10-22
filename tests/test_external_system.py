"""Offline search/merge/UI regression tests; only disposable databases are written."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QTabWidget, QVBoxLayout
from cmdrhelper.database import CMDRDatabase, SCHEMA_VERSION
from cmdrhelper.external_system import adapt_spansh, combine_bodies, search_system, local_bodies, edsm_snapshot, open_local
from cmdrhelper.route_planner.system_resolution import SpanshError
from cmdrhelper.ui.external_system_search import ExternalSystemSearch, ExternalSystemWindow, ExternalBodyDetail
from cmdrhelper.ui.system_overview import build_layout
from cmdrhelper.i18n import _TRANSLATIONS, set_language, tr

ADDRESS=4202348677483


def tai():
    # Reduced synthetic response matching the observed Tai Qing structure and physical values.
    bodies=[dict(bodyId=0,id64=ADDRESS,name='Tai Qing',type='Star',subType='M (Red dwarf) Star',mainStar=True,surfaceTemperature=2904)]
    for bid,name,kind,land,g,temp,atm in [
        (6,'1','High metal content world',True,.209837565,131.115372,None),
        (7,'2','High metal content world',True,.213958397,111.132889,None),
        (8,'3','High metal content world',True,.173500255,93.911842,None),
        (9,'4','Icy body',False,.333718670,163.648666,'Thick Methane'),
        (10,'5','Icy body',True,.368052921,50.57056,'Thin Neon'),
        (11,'6','Icy body',True,.305979912,38.49297,None),
        (12,'6 a','Icy body',True,.074162639,38.467144,None)]:
        bodies.append(dict(bodyId=bid,id64=(bid<<55)+ADDRESS,name='Tai Qing '+name,type='Planet',
            subType=kind,isLandable=land,gravity=g,surfaceTemperature=temp,atmosphereType=atm,
            volcanismType='No volcanism',parents=([{'Planet':11}] if bid==12 else [])+[{'Star':0}],
            signals={'signals':{'$SAA_SignalType_Human;':4}},
            **({'materials':{'Iron':21.183895}} if land else {})))
    bodies[1]['stations']=[dict(id=100,name='Surface',type='Settlement')]
    return {'system':dict(id64=ADDRESS,name='Tai Qing',bodyCount=8,coords=dict(x=-78.53125,y=53.625,z=41.40625),
                         bodies=bodies,stations=[dict(id=101,name='Orbital',type='Outpost')])}


def request(url):
    if '/search/systems?' in url:
        return {'results':[{'id64':ADDRESS,'name':'Tai Qing'}]}
    return {'record':{'id64':ADDRESS,'name':'Tai Qing'}}


class AdapterTests(unittest.TestCase):
    def test_tai_eight_six_landable_types_gravity_and_hierarchy(self):
        raw=tai(); before=deepcopy(raw);m=adapt_spansh(raw,ADDRESS);b=m['bodies']
        self.assertEqual(len(b),8);self.assertEqual(sum(x.get('landable') is True for x in b),6)
        self.assertEqual(sum(x.get('planet_class')=='High metal content body' for x in b),3)
        self.assertEqual(sum(x.get('planet_class')=='Icy body' for x in b),4)
        self.assertEqual(b[-1]['parent_path'],[{'Planet':11},{'Star':0}])
        self.assertTrue(b[0]['main_star']);self.assertAlmostEqual(b[1]['gravity_g'],.209837565)
        self.assertEqual(raw,before);self.assertFalse(m['partial'])
        nodes=build_layout(b)
        self.assertEqual(nodes[('body',12)].parent,('body',11))
        self.assertEqual(nodes[('body',6)].parent,('body',0))

    def test_missing_unknown_not_zero(self):
        raw=tai();r=raw['system']['bodies'][1]
        for key in ('isLandable','gravity','materials','parents'):r.pop(key)
        b=adapt_spansh(raw,ADDRESS)['bodies'][1]
        for key in ('landable','gravity_g','materials','parent_path','atmosphere','geological_signals','planetary_mining_signals'):
            self.assertNotIn(key,b)

    def test_bad_optional_values_and_invalid_parent(self):
        raw=tai();r=raw['system']['bodies'][1]
        r.update(isLandable='yes',gravity=float('nan'),materials={'Iron':-1},parents=[{'Star':True}])
        m=adapt_spansh(raw,ADDRESS);self.assertTrue(m['partial'])
        for key in ('landable','gravity_g','materials','parent_path'):self.assertNotIn(key,m['bodies'][1])

    def test_duplicate_mismatch_invalid_bodies_rejected(self):
        for mutate in (lambda s:s.update(id64=1),lambda s:s.update(bodies=None),
                       lambda s:s['bodies'].append(deepcopy(s['bodies'][0])),
                       lambda s:s['bodies'][0].update(bodyId=True)):
            raw=tai();mutate(raw['system'])
            with self.assertRaises(ValueError):adapt_spansh(raw,ADDRESS)

    def test_partial_count_and_no_invented_bodies(self):
        raw=tai();raw['system']['bodyCount']=12
        m=adapt_spansh(raw,ADDRESS);self.assertTrue(m['partial']);self.assertEqual(len(m['bodies']),8)

    def test_multiple_stars_moon_submoon_missing_parent_cycle(self):
        raw=tai();rows=raw['system']['bodies']
        rows.extend([dict(bodyId=20,name='Companion',type='Star',subType='K (Yellow-Orange) Star',parents=[{'Star':0}]),
                     dict(bodyId=21,name='Unrelated label',type='Planet',parents=[{'Star':20}]),
                     dict(bodyId=22,name='Submoon',type='Planet',parents=[{'Planet':12},{'Planet':11},{'Star':0}])])
        nodes=build_layout(adapt_spansh(raw,ADDRESS)['bodies'])
        self.assertEqual(nodes[('body',21)].parent,('body',20));self.assertEqual(nodes[('body',22)].parent,('body',12))
        rows[-1]['parents']=[{'Planet':99}];self.assertIn(('body',99),build_layout(adapt_spansh(raw,ADDRESS)['bodies']))
        rows[-1]['parents']=[{'Planet':21}];rows[-2]['parents']=[{'Planet':22}]
        self.assertTrue(build_layout(adapt_spansh(raw,ADDRESS)['bodies']))

    def test_only_explicit_mining_and_geo_counts(self):
        raw=tai();r=raw['system']['bodies'][1]
        r['signals']['signals'].update({'$SAA_SignalType_Geological;':2,'$PlanetaryMiningLocation_Name;':3})
        b=adapt_spansh(raw,ADDRESS)['bodies'][1]
        self.assertEqual(b['geological_signals'],2);self.assertEqual(b['planetary_mining_signals'],3)
        self.assertNotIn('planetary_mining_signals',adapt_spansh(tai(),ADDRESS)['bodies'][1])

    def test_station_parent_carrier_and_duplicate_rules(self):
        raw=tai();raw['system']['stations'] += [dict(id=102,name='Carrier',type='Fleet Carrier'),dict(id=101,name='Orbital',type='Outpost')]
        m=search_system('Tai Qing',request=request,fetch=lambda a:raw)
        self.assertEqual(len(m['stations']),2)
        self.assertEqual({s['market_id']:s['parent_body_id'] for s in m['stations']},{100:6,101:None})


class LocalMergeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'test.db';CMDRDatabase(self.path)
        with sqlite3.connect(self.path) as c:
            c.execute("INSERT INTO commanders(id,fid,current_name) VALUES(1,'A','Alpha'),(2,'B','Beta')")
            c.execute("INSERT INTO systems(system_address,name,body_count) VALUES(?,'Tai Qing',8)",(ADDRESS,))
            for cid in (1,2):c.execute('INSERT INTO commander_systems(commander_id,system_address) VALUES(?,?)',(cid,ADDRESS))
            for bid in (6,7):
                c.execute("INSERT INTO bodies(system_address,body_id,name,body_type,planet_class,landable,gravity_g,parent_id) VALUES(?,?,?,'Planet','High metal content body',1,.5,0)",(ADDRESS,bid,'Tai Qing '+str(bid-5)))
                c.execute("INSERT INTO commander_bodies(commander_id,system_address,body_id,scanned,self_mapped,last_seen) VALUES(?,?,?,1,?,'2026-10-01T00:00:00Z')",(bid-5,ADDRESS,bid,bid==7))
        self.before=self.path.read_bytes()

    def edsm(self, address=ADDRESS):
        data={'system':'Tai Qing','system_address':address,'bodies':[dict(body_id=6,name='Tai Qing 1',body_type='Planet',landable=True,atmosphere='No atmosphere',source='EDSM',journal_scanned=True,self_mapped=True)]}
        p=Path(self.tmp.name)/(hashlib.sha256(b'Tai Qing').hexdigest()[:24]+'.json')
        p.write_text(json.dumps(dict(system='Tai Qing',data=data,fetched_at='2026-10-22T00:00:00Z')))
        return p

    def test_all_sources_priority_conflicts_attribution_no_writes(self):
        self.edsm()
        m=search_system('Tai Qing',self.path,request=request,fetch=lambda a:tai(),edsm_root=self.tmp.name)
        self.assertEqual(len(m['bodies']),8);self.assertTrue(m['edsm_used'])
        b=next(b for b in m['bodies'] if b['body_id']==6)
        self.assertEqual(b['gravity_g'],.5);self.assertEqual(b['provenance']['gravity_g'],'Local')
        self.assertTrue(b['conflicts']['gravity_g']);self.assertEqual(b['atmosphere'],'No atmosphere')
        self.assertEqual(b['observations'][0]['current_name'],'Alpha')
        b2=next(b for b in m['bodies'] if b['body_id']==7)
        self.assertEqual(b2['observations'][0]['current_name'],'Beta');self.assertTrue(b2['observations'][0]['self_mapped'])
        for b in m['bodies']:
            self.assertFalse(b['journal_scanned']);self.assertNotIn('self_mapped',b);self.assertNotIn('was_discovered',b)
        self.assertEqual(self.path.read_bytes(),self.before)
        with open_local(self.path) as c:
            self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0],23)
            with self.assertRaises(sqlite3.OperationalError):c.execute("UPDATE systems SET name='bad'")

    def test_local_only_network_failure_keeps_view_partial(self):
        m=search_system('Tai Qing',self.path,request=Mock(side_effect=OSError('offline')),edsm_root=self.tmp.name)
        self.assertEqual(len(m['bodies']),2);self.assertTrue(m['partial']);self.assertTrue(m['warning'])
        self.assertEqual(self.path.read_bytes(),self.before)

    def test_local_system_without_scans_still_opens_offline(self):
        with sqlite3.connect(self.path) as c:
            c.execute('DELETE FROM commander_bodies');c.execute('DELETE FROM bodies')
        m=search_system('Tai Qing',self.path,request=Mock(side_effect=OSError('offline')),edsm_root=self.tmp.name)
        self.assertEqual(m['bodies'],[]);self.assertEqual(m['body_count'],8)
        self.assertTrue(m['partial']);self.assertEqual(m['sources'],'Local')

    def test_edsm_only_verified_cache_no_second_provider(self):
        self.edsm();m=search_system('Tai Qing',None,request=Mock(side_effect=OSError('offline')),edsm_root=self.tmp.name)
        self.assertEqual(m['sources'],'EDSM');self.assertEqual(len(m['bodies']),1)

    def test_legacy_and_wrong_identity_cache_not_merged(self):
        p=self.edsm();d=json.loads(p.read_text());d['data'].pop('system_address');p.write_text(json.dumps(d))
        self.assertIsNone(edsm_snapshot('Tai Qing',self.tmp.name))
        self.edsm(7)
        m=search_system('Tai Qing',self.path,request=request,fetch=lambda a:tai(),edsm_root=self.tmp.name)
        self.assertFalse(m['edsm_used'])

    def test_identity_conflict_no_duplicate_or_field_leak(self):
        first=[dict(body_id=1,name='One',source='Local',gravity_g=1)]
        second=[dict(body_id=1,name='Other',source='Spansh',atmosphere='Bad')]
        before=deepcopy((first,second));b=combine_bodies(first,second)
        self.assertEqual(len(b),1);self.assertNotIn('atmosphere',b[0]);self.assertIn('name',b[0]['conflicts'])
        self.assertEqual((first,second),before)

    def test_lower_priority_parent_path_cannot_replace_local_parent(self):
        b=combine_bodies([dict(body_id=1,name='One',source='Local',parent_id=0)],
                         [dict(body_id=1,name='One',source='Spansh',parent_path=[{'Star':9}])])[0]
        self.assertEqual(b['parent_id'],0);self.assertNotIn('parent_path',b);self.assertIn('parent_path',b['conflicts'])

    def test_compatible_external_path_completes_local_hierarchy(self):
        body=combine_bodies([dict(body_id=1,name='One',source='Local',parent_id=0)],
                            [dict(body_id=1,name='One',source='Spansh',parent_path=[{'Star':0}])],
                            [dict(body_id=1,name='One',source='EDSM',parent_path=[{'Star':0}],parent_id=0,parent_star_id=0)])[0]
        self.assertEqual(body['parent_path'],[{'Star':0}]);self.assertEqual(body['parent_star_id'],0)
        self.assertFalse(body['conflicts'])

    def test_both_commanders_same_body_keep_both_proofs(self):
        with sqlite3.connect(self.path) as c:
            c.execute('INSERT INTO commander_bodies(commander_id,system_address,body_id,self_mapped) VALUES(2,?,6,1)',(ADDRESS,))
        b=local_bodies(self.path,ADDRESS)[0]
        self.assertEqual([r['current_name'] for r in b['observations']],['Alpha','Beta'])


    def test_material_gaps_keep_per_element_provenance_and_units(self):
        local=[dict(body_id=1,name='One',source='Local',materials={'Iron':20},material_unit='percent')]
        spansh=[dict(body_id=1,name='One',source='Spansh',materials={'Iron':21,'Nickel':10},material_unit='unverified')]
        body=combine_bodies(local,spansh)[0]
        self.assertEqual(body['materials'],{'Iron':20,'Nickel':10})
        self.assertEqual(body['material_units'],{'Iron':'percent','Nickel':'unverified'})
        self.assertEqual(body['material_sources'],{'Iron':'Local','Nickel':'Spansh'})
        self.assertEqual(body['conflicts']['materials.Iron'][0]['value'],21)

    def test_local_geology_and_mining_count_without_scan(self):
        with sqlite3.connect(self.path) as c:
            c.execute("INSERT INTO bodies(system_address,body_id,planetary_mining_signals) VALUES(?,20,3)",(ADDRESS,))
            c.execute("INSERT INTO geology(commander_id,system_address,body_id,name,raw_name,source,first_seen,last_seen) VALUES(1,?,6,'Geyser','Geyser','Journal','','')",(ADDRESS,))
        bodies=local_bodies(self.path,ADDRESS)
        self.assertEqual(bodies[-1]['planetary_mining_signals'],3)
        self.assertEqual(bodies[0]['geology'][0]['current_name'],'Alpha')
        self.assertNotIn('landable',bodies[-1])


class SearchTests(unittest.TestCase):
    def test_spansh_only_uses_existing_resolver_and_single_dump(self):
        fetch=Mock(return_value=tai());m=search_system('Tai Qing',request=request,fetch=fetch)
        fetch.assert_called_once_with(ADDRESS);self.assertEqual(m['sources'],'Spansh')

    def test_unknown_ambiguous_and_partial_names_never_dump(self):
        for matches in ([],[dict(name='Tai Qing extended',id64=ADDRESS)],
                        [dict(name='Tai Qing',id64=ADDRESS),dict(name='Tai Qing',id64=7)]):
            fetch=Mock()
            with self.assertRaises(SpanshError):search_system('Tai Qing',request=lambda u:{'results':matches},fetch=fetch)
            fetch.assert_not_called()

    def test_network_error_and_bad_dump_no_retry(self):
        for data in ({}, {'system':{'id64':1}}):
            fetch=Mock(return_value=data)
            with self.assertRaises(SpanshError):search_system('Tai Qing',request=request,fetch=fetch)
            self.assertEqual(fetch.call_count,1)
        req=Mock(side_effect=TimeoutError())
        with self.assertRaises(SpanshError):search_system('Tai Qing',request=req)
        self.assertEqual(req.call_count,1)


class FakePool:
    def __init__(self):self.jobs=[]
    def start(self,job):self.jobs.append(job)


class WindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.owner=QWidget();self.owner.ui_theme='dark';self.owner.commander_id=1;self.owner.system_address=1
        self.pool=FakePool();self.model=search_system('Tai Qing',request=request,fetch=lambda a:tai())
        self.provider=Mock(return_value=self.model)
        self.search=ExternalSystemSearch(self.owner,None,provider=self.provider,pool=self.pool)
    def tearDown(self):
        for w in list(self.search.windows):w.close()
        self.owner.close();self.owner.deleteLater();self.app.processEvents()

    def test_button_enter_latest_only_and_old_job_skips_network(self):
        self.search.edit.setText('Earlier');self.search.button.click()
        self.search.edit.setText('Tai Qing');self.search.edit.returnPressed.emit()
        self.assertEqual(len(self.pool.jobs),2)
        self.pool.jobs[0].run();self.assertEqual(self.provider.call_count,0)
        self.pool.jobs[1].run();self.assertEqual(len(self.search.windows),1)
        self.search.finished(1,self.model,'');self.assertEqual(len(self.search.windows),1)

    def test_repeated_same_pending_search_coalesces_then_can_refresh(self):
        self.search.edit.setText('Tai Qing');self.search.start_search();self.search.start_search()
        self.assertEqual(len(self.pool.jobs),1)
        self.pool.jobs[0].run();self.search.start_search()
        self.assertEqual(len(self.pool.jobs),2)

    def test_switch_system_commander_and_tab_during_request_keeps_result(self):
        self.search.edit.setText('Tai Qing');self.search.start_search()
        self.owner.commander_id=2;self.owner.system_address=123
        self.pool.jobs[0].run();w=self.search.windows[0]
        self.assertTrue(w.isVisible());self.assertEqual(w.system_address,ADDRESS)
        tabs=QTabWidget(self.owner);tabs.addTab(QWidget(),'Explorer');tabs.addTab(QWidget(),'PP2')
        tabs.setCurrentIndex(1);self.search.hide();self.owner.commander_id=3
        self.assertTrue(w.isVisible());self.assertEqual(w.model['bodies'],self.model['bodies'])

    def test_window_flags_resize_zoom_details_both_themes(self):
        for light in (False,True):
            w=ExternalSystemWindow(self.model,self.owner,light=light);w.show();self.app.processEvents()
            self.assertFalse(w.isModal());self.assertFalse(w.windowFlags() & Qt.WindowStaysOnTopHint)
            w.resize(1200,800);self.assertEqual(w.width(),1200)
            self.assertEqual(len(w.preview.bodies),8)
            self.assertEqual(sum(bool(i.landable_text) for i in w.preview.items_by_key.values()),6)
            w.preview.fit_system();w.preview.reset_zoom();w.set_light_mode(not light)
            w.preview.bodyClicked.emit(w.preview.bodies[1]);self.assertEqual(len(w.details),1)
            self.assertTrue(w.details[0].isVisible());w.close();self.app.processEvents()

    def test_external_landability_labels_geometry_and_personal_view_unchanged(self):
        from cmdrhelper.ui.system_overview import SystemOverviewView, build_layout
        from PySide6.QtGui import QImage, QPainter
        for light in (False,True):
            bodies=deepcopy(self.model['bodies'])
            bodies[2].pop('landable')
            before=deepcopy(bodies)
            view=SystemOverviewView('Tai Qing',bodies,light=light)
            view.resize(1100,700);view.show();self.app.processEvents()
            for bid,expected in ((6,True),(7,False),(9,False),(12,True),(0,False)):
                item=view.items_by_key[('body',bid)]
                self.assertEqual(bool(item.landable_text),expected)
                if expected:
                    self.assertEqual(item.landable_text,'✓ '+tr('body_detail.landable'))
                    rect=item.landability_rect()
                    self.assertGreater(rect.top(),82+item.node.diameter/2+7+22+31)
                    self.assertTrue(item.boundingRect().contains(rect))
            rects=[item.sceneBoundingRect() for item in view.items_by_key.values()]
            for i,rect in enumerate(rects):
                for other in rects[i+1:]:self.assertFalse(rect.intersects(other))
            for zoom in (.6,1.,1.8):
                view.resetTransform();view.scale(zoom,zoom)
                image=QImage(view.size(),QImage.Format_ARGB32);image.fill(Qt.transparent)
                painter=QPainter(image);view.render(painter);painter.end()
                self.assertFalse(image.isNull())
            self.assertEqual(bodies,before)
            personal=deepcopy(bodies)
            for b in personal:b.pop('external_view',None)
            personal_view=SystemOverviewView('Tai Qing',personal,light=light)
            for item in personal_view.items_by_key.values():
                self.assertFalse(item.landable_text)
                self.assertEqual(item.node.height,82+item.node.diameter/2+66)
            view.close();personal_view.close()

    def test_details_unknown_material_units_no_personal_claim(self):
        b=self.model['bodies'][1];w=ExternalBodyDetail(b,self.owner)
        labels='\n'.join(x.text() for x in w.findChildren(QLabel))
        self.assertIn(tr('common.unknown'),labels);self.assertIn(tr('external.units'),labels)
        self.assertNotIn('21.183895 %',labels);self.assertNotIn(tr('body_detail.self_scanned'),labels)
        self.assertNotIn(tr('body_detail.values'),labels);w.close()

    def test_attributed_proofs_stay_neutral_after_commander_switch(self):
        b=deepcopy(self.model['bodies'][1]);b['observations']=[dict(commander_id=1,current_name='Alpha',scanned=True),dict(commander_id=2,current_name='Beta',self_mapped=True)]
        w=ExternalBodyDetail(b,self.owner);self.owner.commander_id=2
        labels='\n'.join(x.text() for x in w.findChildren(QLabel))
        self.assertIn('Alpha (#1)',labels);self.assertIn('Beta (#2)',labels)
        self.assertNotIn(tr('body_detail.self_scanned'),labels);w.close()

    def test_failure_message_and_main_window_remains_enabled(self):
        self.provider.side_effect=SpanshError('system_unknown')
        self.search.edit.setText('Missing');self.search.start_search();self.pool.jobs[0].run()
        self.assertEqual(self.search.status.text(),tr('external.unknown'));self.assertTrue(self.owner.isEnabled())

    def test_twelve_languages_complete(self):
        keys={k for k in _TRANSLATIONS['en'] if k.startswith('external.')}
        self.assertEqual(len(_TRANSLATIONS),12)
        for lang,translations in _TRANSLATIONS.items():
            self.assertTrue(keys <= translations.keys(),lang)
            set_language(lang)
            self.assertNotEqual(tr('external.search'),'external.search')
            self.assertNotEqual(tr('external.title'),'external.title')
            self.assertNotEqual(tr('body_detail.landable'),'body_detail.landable')
            self.assertIn('Spansh',tr('external.source',source='Spansh'))
        set_language('de')

    def test_gui_does_not_call_network_synchronously(self):
        self.search.edit.setText('Tai Qing');self.search.start_search()
        self.provider.assert_not_called();self.assertEqual(len(self.pool.jobs),1)

    def test_real_thread_delivery(self):
        pool=QThreadPool();pool.setMaxThreadCount(1)
        self.search.pool=pool;self.search.edit.setText('Tai Qing');self.search.start_search()
        pool.waitForDone(3000);self.app.processEvents()
        self.assertEqual(len(self.search.windows),1)

    def test_real_explorer_search_row_and_enter_wiring(self):
        from PySide6.QtCore import QSettings
        from tests.test_explorer_table_ux import ExplorerWindow
        with tempfile.TemporaryDirectory() as directory:
            owner=ExplorerWindow(QSettings(str(Path(directory)/'ui.ini'),QSettings.IniFormat))
            owner.show();self.app.processEvents()
            search=owner.external_system_search
            page=owner.centralWidget()
            self.assertEqual(page.layout().indexOf(search),1)
            self.assertLess(page.layout().indexOf(search),page.layout().indexOf(owner.explorer_tabs.parentWidget()))
            self.assertEqual(search.heading.text(),tr('external.title'))
            search.provider=self.provider;search.pool=self.pool
            search.edit.setText('Tai Qing');search.edit.setFocus()
            QTest.keyClick(search.edit,Qt.Key_Return)
            self.assertEqual(len(self.pool.jobs),1)
            self.pool.jobs[0].run()
            window=search.windows[0]
            owner.explorer_tabs.setCurrentIndex(2)
            self.assertTrue(window.isVisible())
            window.close();owner.close();owner.deleteLater();self.app.processEvents()

    def test_material_conflicts_do_not_display_unverified_shares(self):
        body=combine_bodies([dict(body_id=1,name='One',source='Local',materials={'Iron':20},material_unit='percent')],
                            [dict(body_id=1,name='One',source='Spansh',materials={'Iron':21.123456},material_unit='unverified')])[0]
        window=ExternalBodyDetail(body,self.owner)
        labels='\n'.join(x.text() for x in window.findChildren(QLabel))
        self.assertIn('20.00 %',labels);self.assertNotIn('21.123456',labels)
        self.assertIn(tr('external.units'),labels);window.close()

    def test_protected_modules_have_no_new_imports(self):
        for filename in ('database.py','state.py','journal_reader.py','online_services.py'):
            self.assertNotIn('external_system',Path('cmdrhelper',filename).read_text())
        self.assertEqual(SCHEMA_VERSION,23)
