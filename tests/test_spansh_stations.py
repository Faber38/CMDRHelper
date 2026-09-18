"""Small live-only external station cache: no real network or user DB writes."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import ast
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from PySide6.QtCore import QSettings, QStandardPaths, QThreadPool
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMainWindow
from cmdrhelper.spansh_cache import (SystemCache, normalize, validate, merge_stations, fetch_system,
                                     cache_directory, SERVICES, MAX_RESPONSE)
from cmdrhelper.spansh_stations import SpanshStations, LiveEntryGate
from cmdrhelper.state import AppState
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.system_overview import SystemOverviewView
from cmdrhelper.ui.station_details import StationDetailDialog

NOW = datetime(2026,9,16,12,0,tzinfo=timezone.utc)
BODIES = [dict(body_id=0,name='Test',body_type='Star',star_type='G'),
          dict(body_id=1,name='Test 1',body_type='Planet',parent_id=0),
          dict(body_id=2,name='Test 2',body_type='Planet',parent_id=0)]


def raw(address=1):
    return {'system':{'id64':address,'name':'Test','date':'2026-06-01T00:00:00Z',
        'stations':[{'id':100,'name':'Port','type':'Dodec Starport','distanceToArrival':100,
            'allegiance':'Federation','government':'Democracy','controllingFaction':'Faction',
            'primaryEconomy':'Industrial','secondaryEconomy':'Refinery',
            'economies':{'Industrial':210,'Refinery':40},
            'landingPads':{'large':2,'medium':0,'small':3},
            'services':list(SERVICES)+['Unknown service'],
            'updateTime':'2026-05-01T00:00:00Z',
            'market':[{'price':999,'supply':999}], 'outfitting':[{'price':99}], 'shipyard':['Ship']}],
        'bodies':[{'bodyId':1,'id64':36028797018963969,'name':'Test 1','type':'Planet',
            'stations':[{'id':101,'name':'Surface','type':'Planetary Outpost','latitude':1,'longitude':2}]}]}}


def journal(mid=100, parent=None):
    return dict(identity=f'market:{mid}',market_id=mid,station_name='Journal name',station_type='Dodec',
                parent_body_id=parent,source='Journal',system_address=1,last_seen='2026-01-01T00:00:00Z')


def event(address=2, kind='FSDJump', when=None):
    return dict(event=kind,SystemAddress=address,StarSystem='Test',timestamp=(when or NOW+timedelta(seconds=1)).isoformat())


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.fetch=Mock(side_effect=lambda address: raw(address))
        self.cache=SystemCache(self.temp.name,fetch=self.fetch,now=lambda:NOW)

    def test_missing_cache_fetch_once_and_fresh_no_network(self):
        first=self.cache.visit(1);self.assertEqual(first,self.cache.visit(1))
        self.fetch.assert_called_once_with(1)
        self.assertEqual([p.name for p in Path(self.temp.name).iterdir()],['1.json'])

    def test_old_cache_only_updated_by_visit(self):
        old=normalize(raw(),1,NOW-timedelta(days=31));self.cache.write(old)
        self.assertEqual(self.cache.read(1),old);self.fetch.assert_not_called()
        self.assertNotEqual(self.cache.visit(1)['fetched_at'],old['fetched_at'])
        self.fetch.assert_called_once_with(1)

    def test_exact_7_days_expired_and_future_fetch_time_not_fresh(self):
        for age in (timedelta(days=7),timedelta(days=-1)):
            self.assertFalse(self.cache.fresh(normalize(raw(),1,NOW-age)))

    def test_offline_uses_old_cache_and_empty_system_is_safe(self):
        old=normalize(raw(),1,NOW-timedelta(days=31));self.cache.write(old)
        self.fetch.side_effect=OSError('offline')
        self.assertEqual(self.cache.visit(1),old)
        self.assertIsNone(self.cache.visit(2))

    def test_corrupt_json_ignored_then_next_visit_retries(self):
        self.cache.path(1).write_text('{broken')
        self.assertIsNone(self.cache.read(1));self.fetch.assert_not_called()
        self.assertEqual(self.cache.visit(1)['system_address'],1)

    def test_cache_schema_source_id_and_types_validated(self):
        good=normalize(raw(),1,NOW)
        mutations=[('schema_version',2),('schema_version',True),('source','journal'),
                   ('system_address',2),('system_address',True),('stations',{}),('fetched_at','yesterday')]
        for key,value in mutations:
            bad=deepcopy(good);bad[key]=value
            self.cache.path(1).write_text(json.dumps(bad))
            self.assertIsNone(self.cache.read(1),(key,value))
        for key,value in [('market_id',True),('landing_pads',{'large':-1}),('services',['unlisted']),
                          ('distance_ls',float('nan')),('parent_body_id','1'),('station_name',100),
                          ('economies',[]),('is_planetary',1),('station_updated_at','broken')]:
            bad=deepcopy(good);bad['stations'][0][key]=value
            with self.assertRaises(ValueError):validate(bad,1)

    def test_address_mismatch_never_cached(self):
        self.fetch.side_effect=None;self.fetch.return_value=raw(2)
        self.assertIsNone(self.cache.visit(1));self.assertFalse(self.cache.path(1).exists())
        for value in ('../../db',True,-1,0,1.5,2**64):
            with self.assertRaises(ValueError):self.cache.path(value)

    def test_atomic_replace_keeps_previous_file_on_failure(self):
        old=normalize(raw(),1,NOW-timedelta(days=40));self.cache.write(old)
        with patch('cmdrhelper.spansh_cache.os.replace',side_effect=OSError('interrupted')):
            with self.assertRaises(OSError):self.cache.write(normalize(raw(),1,NOW))
        self.assertEqual(self.cache.read(1),old)
        self.assertEqual([p.name for p in Path(self.temp.name).iterdir()],['1.json'])

    def test_unavailable_user_directory_does_not_block_optional_feature(self):
        with patch('cmdrhelper.spansh_cache.cache_directory', side_effect=OSError('no user directory')):
            cache=SystemCache(fetch=self.fetch,now=lambda:NOW)
            self.assertIsNone(cache.read(1))
            self.assertIsNone(cache.visit(1))

    def test_cache_whitelist_excludes_market_inventory_and_keeps_dates_pads_services(self):
        data=normalize(raw(),1,NOW);row=data['stations'][0]
        self.assertFalse({'market','shipyard','outfitting'} & row.keys())
        self.assertEqual(row['landing_pads'],{'large':2,'medium':0,'small':3})
        self.assertEqual(set(row['services']),set(SERVICES.values()))
        self.assertEqual(row['economies']['Industrial'],210)
        self.assertNotEqual(data['source_updated_at'],data['fetched_at'])
        self.assertNotEqual(data['source_updated_at'],row['station_updated_at'])

    def test_structured_body_is_parent_not_distance_or_station_name(self):
        data=normalize(raw(),1,NOW)
        self.assertNotIn('parent_body_id',data['stations'][0])
        self.assertEqual(data['stations'][1]['parent_body_id'],1)
        self.assertEqual(data['stations'][1]['parent_body_id64'],36028797018963969)

    def test_carriers_removed_and_duplicate_names_not_merged(self):
        response=raw();response['system']['stations'] += [
            dict(id=102,name='Port',type='Outpost'),dict(id=103,name='Carrier',type='Drake-Class Carrier')]
        data=normalize(response,1,NOW)
        self.assertEqual([s['market_id'] for s in data['stations']],[100,101,102])

    def test_ambiguous_duplicate_market_facts_omitted(self):
        response=raw();response['system']['stations'].append(dict(id=100,name='Conflicting',type='Outpost'))
        self.assertEqual([s['market_id'] for s in normalize(response,1,NOW)['stations']],[101])

    def test_request_contains_only_public_id_and_fixed_headers(self):
        with patch('cmdrhelper.spansh_cache.urlopen',return_value=io.BytesIO(json.dumps(raw()).encode())) as transport:
            fetch_system(1)
        request=transport.call_args.args[0]
        self.assertEqual(request.full_url,'https://spansh.co.uk/api/dump/1')
        self.assertIsNone(request.data)
        self.assertEqual(set(k.lower() for k in request.headers),{'user-agent','accept'})
        self.assertEqual(transport.call_args.kwargs['timeout'],15)

    def test_linux_windows_paths_use_qt_user_data(self):
        for root in ('/home/user/.local/share/CMDRHelper/CMDRHelper', 'C:/Users/User/AppData/Roaming/CMDRHelper/CMDRHelper'):
            with patch.object(QStandardPaths,'writableLocation',return_value=root) as location:
                self.assertEqual(cache_directory(),Path(root)/'external'/'spansh')
                location.assert_called_once_with(QStandardPaths.AppDataLocation)

    def test_ignore_and_release_exclude_local_caches(self):
        import subprocess
        result=subprocess.run(['git','check-ignore','data/external/spansh/1.json'],capture_output=True)
        self.assertEqual(result.returncode,0)
        script=Path('create_release.sh').read_text()
        self.assertIn('Never copy the developer\'s data directory',script)
        self.assertIn('mkdir -p -- "$payload/data"',script)
        self.assertNotIn('cp -a -- data',script)


class MergeTests(unittest.TestCase):
    def test_same_market_merges_and_journal_input_stays_unchanged(self):
        own=[journal()];before=deepcopy(own)
        merged=merge_stations(own,normalize(raw(),1,NOW),BODIES,1)
        self.assertEqual(own,before);self.assertEqual(len(merged),2)
        row=next(s for s in merged if s['market_id']==100)
        self.assertEqual(row['station_name'],'Journal name')
        self.assertEqual(row['source'],'Journal + Spansh')

    def test_explicit_parent_fills_journal_gap(self):
        merged=merge_stations([journal(101)],normalize(raw(),1,NOW),BODIES,1)
        row=next(s for s in merged if s['market_id']==101)
        self.assertEqual(row['parent_body_id'],1);self.assertEqual(row['parent_source'],'Spansh')

    def test_parent_conflict_preserves_journal_and_is_recorded(self):
        row=next(s for s in merge_stations([journal(101,2)],normalize(raw(),1,NOW),BODIES,1) if s['market_id']==101)
        self.assertEqual(row['parent_body_id'],2);self.assertEqual(row['spansh_conflicts']['parent_body_id'],1)

    def test_missing_body_or_name_disagreement_stays_unknown(self):
        data=normalize(raw(),1,NOW)
        for bodies in ([],[dict(body_id=1,name='Wrong',body_type='Planet')]):
            row=next(s for s in merge_stations([],data,bodies,1) if s['market_id']==101)
            self.assertIsNone(row['parent_body_id'])

    def test_own_carrier_never_enriched_and_external_carrier_never_added(self):
        own=dict(journal(),station_type='FleetCarrier')
        data=normalize(raw(),1,NOW)
        data['stations'][1]['station_type']='FleetCarrier'
        merged=merge_stations([own],data,BODIES,1)
        self.assertEqual(merged,[own])

    def test_no_sql_in_cache_or_merge(self):
        with patch('sqlite3.connect',side_effect=AssertionError('No external SQLite')):
            self.assertEqual(len(merge_stations([],normalize(raw(),1,NOW),BODIES,1)),2)
        for filename in ('cmdrhelper/spansh_cache.py','cmdrhelper/spansh_stations.py'):
            text=Path(filename).read_text()
            self.assertNotIn('import sqlite3',text)
            self.assertNotIn('station_observations',text)


class LiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.settings=QSettings(str(Path(self.temp.name)/'settings.ini'),QSettings.IniFormat)
        self.fetch=Mock(side_effect=lambda address:raw(address))
        self.cache=SystemCache(Path(self.temp.name)/'cache',self.fetch,lambda:NOW)
        self.pool=Mock()
        self.controller=SpanshStations(self.settings,cache=self.cache,pool=self.pool,now=lambda:NOW)
        self.controller.set_enabled(True)
        self.controller.observe([], 'FID', 1, live=False)
    def arrive(self,address=2,kind='FSDJump'):
        self.controller.observe([event(address,kind)],'FID',address,live=True)
    def run_worker(self):self.pool.start.call_args.args[0].run()

    def test_new_live_jump_one_async_fetch_and_no_repeat_refresh_fetch(self):
        self.arrive();self.fetch.assert_not_called();self.pool.start.assert_called_once()
        self.run_worker();self.arrive();self.fetch.assert_called_once_with(2)

    def test_carrier_jump_and_safe_location_change(self):
        for kind,address in [('CarrierJump',2),('Location',3)]:self.arrive(address,kind);self.run_worker()
        self.assertEqual(self.fetch.call_count,2)

    def test_startup_historical_and_commander_switch_never_fetch(self):
        self.controller.observe([event(2)],'FID',2,live=False)
        self.controller.observe([event(3,when=NOW-timedelta(days=1))],'FID',3,live=True)
        self.controller.observe([event(4)],'OTHER',4,live=True)
        self.pool.start.assert_not_called();self.fetch.assert_not_called()

    def test_fresh_cache_skips_worker_stale_refreshes_only_on_revisit(self):
        self.cache.write(normalize(raw(2),2,NOW));self.arrive(2);self.pool.start.assert_not_called()
        self.cache.write(normalize(raw(3),3,NOW-timedelta(days=31)))
        self.controller.cached(3);self.pool.start.assert_not_called()
        self.arrive(3);self.run_worker();self.fetch.assert_called_once_with(3)

    def test_off_and_toggle_on_do_not_fetch_current_system(self):
        self.controller.set_enabled(False);self.arrive()
        self.controller.set_enabled(True);self.pool.start.assert_not_called()
        self.arrive(3);self.run_worker();self.fetch.assert_called_once_with(3)

    def test_default_is_opt_in(self):
        other=QSettings(str(Path(self.temp.name)/'other.ini'),QSettings.IniFormat)
        self.assertFalse(SpanshStations(other,cache=self.cache,pool=self.pool).active)

    def test_queued_old_system_is_cancelled_and_late_result_not_painted(self):
        updates=[];self.controller.updated.connect(updates.append)
        self.arrive(2);worker=self.pool.start.call_args.args[0]
        self.arrive(3);worker.run();self.fetch.assert_not_called();self.assertEqual(updates,[])
        self.controller._finished(0,2,normalize(raw(2),2,NOW));self.assertEqual(updates,[])

    def test_worker_in_real_thread_keeps_gui_responsive(self):
        import threading
        started=threading.Event();release=threading.Event();done=[]
        def fetch(address):started.set();release.wait(2);return raw(address)
        cache=SystemCache(Path(self.temp.name)/'thread-cache',fetch,lambda:NOW)
        controller=SpanshStations(self.settings,cache=cache,now=lambda:NOW)
        controller.observe([],'FID',1);controller.updated.connect(done.append)
        controller.observe([event(2)],'FID',2,live=True)
        self.assertTrue(started.wait(1));QTest.qWait(20);self.assertFalse(done)
        release.set();controller.pool.waitForDone(2000);self.app.processEvents()
        self.assertEqual(done,[2])

    def test_completed_worker_repaints_only_current_station_model(self):
        state=SimpleNamespace(system_address=1,system_bodies=BODIES,_journal_system_stations=[journal()],
            spansh_stations=SimpleNamespace(cached=lambda address:normalize(raw(),address,NOW)),
            stationModelChanged=Mock(),changed=Mock(),refresh=Mock())
        state.station_display_model=lambda *args:AppState.station_display_model(state,*args)
        AppState._spansh_stations_updated(state,2);state.stationModelChanged.emit.assert_called_once_with(2)
        state.stationModelChanged.emit.reset_mock()
        AppState._spansh_stations_updated(state,1);state.stationModelChanged.emit.assert_called_once_with(1)
        state.refresh.assert_not_called();state.changed.emit.assert_not_called()

    def test_no_archive_startup_trigger_wiring(self):
        source=Path('cmdrhelper/state.py').read_text()
        tree=ast.parse(source)
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='AppState')
        network_calls=[]
        for method in cls.body:
            if isinstance(method,ast.FunctionDef):
                for node in ast.walk(method):
                    if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='observe' and isinstance(node.func.value,ast.Name) and node.func.value.id=='spansh':network_calls.append(method.name)
        self.assertEqual(network_calls,['refresh'])
        self.assertIn("live=bool(identified and getattr(self, '_watcher_live_refresh', False))",source)
        self.assertNotIn('spansh',Path('cmdrhelper/database.py').read_text().lower())


class DetailsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def tearDown(self):
        for w in self.app.topLevelWidgets():w.close()
        self.app.processEvents()

    def test_details_services_pads_sources_and_independent_dates(self):
        row=next(s for s in merge_stations([journal()],normalize(raw(),1,NOW),BODIES,1) if s['market_id']==100)
        dialog=StationDetailDialog(row,'Test');dialog.show();self.app.processEvents()
        self.assertIn('Journal + Spansh',dialog.info.text())
        self.assertIn('L: 2',dialog.external_info.text());self.assertIn('M: 0',dialog.external_info.text())
        self.assertEqual(len(dialog.service_labels),len(set(SERVICES.values())))
        self.assertIn('2026-05-01',dialog.external_dates.text())
        self.assertIn('2026-06-01',dialog.external_dates.text())
        self.assertIn('2026-09-16',dialog.external_dates.text())
        self.assertNotIn('%',dialog.external_info.text())
        self.assertNotIn('Unknown service',[x.text() for x in dialog.service_labels])
        for light in (True,False):
            from cmdrhelper.ui.station_details import apply_theme
            apply_theme(dialog,light);self.assertFalse(dialog.grab().isNull())

    def test_scene_update_preserves_zoom_and_open_detail(self):
        view=SystemOverviewView('Test',BODIES,stations=[journal()]);view.show()
        detail=StationDetailDialog(journal(),'Test',view);detail.show()
        view.scale(1.5,1.5)
        view.set_stations(merge_stations([journal()],normalize(raw(),1,NOW),BODIES,1))
        self.assertEqual(view.transform().m11(),1.5);self.assertTrue(detail.isVisible())


class RefreshTests(unittest.TestCase):
    """Refresh-specific checks, with the same isolated controller fixture."""
    setUpClass = classmethod(LiveTests.setUpClass.__func__)
    setUp = LiveTests.setUp
    arrive = LiveTests.arrive
    run_worker = LiveTests.run_worker

    def test_six_days_fresh_seven_days_expired(self):
        self.cache.write(normalize(raw(2),2,NOW-timedelta(days=6)))
        self.arrive(2);self.pool.start.assert_not_called()
        self.cache.write(normalize(raw(3),3,NOW-timedelta(days=7)))
        self.arrive(3);self.run_worker();self.fetch.assert_called_once_with(3)

    def test_failed_a_b_a_and_restart_persist_day_guard(self):
        self.fetch.side_effect=OSError('offline')
        self.arrive(2);self.run_worker();self.arrive(3);self.run_worker()
        self.arrive(2);self.run_worker()
        self.assertEqual(self.fetch.call_count,2)
        restarted=SystemCache(self.cache.root,self.fetch,lambda:NOW)
        self.assertEqual(restarted.request(2,automatic=True),(None,None))
        self.assertEqual(self.fetch.call_count,2)
        self.assertTrue(restarted.automatic_allowed(4))

    def test_next_local_calendar_day_allows_retry(self):
        local=datetime.now().astimezone().tzinfo
        clock=[datetime(2026,9,16,23,50,tzinfo=local)]
        self.cache.now=lambda:clock[0]
        self.fetch.side_effect=OSError('offline')
        self.cache.request(2,automatic=True)
        clock[0]+=timedelta(minutes=20)
        self.cache.request(2,automatic=True)
        self.assertEqual(self.fetch.call_count,2)

    def test_success_next_day_still_fresh(self):
        self.cache.request(2,automatic=True)
        self.cache.now=lambda:NOW+timedelta(days=1)
        self.cache.request(2,automatic=True)
        self.fetch.assert_called_once_with(2)

    def test_manual_bypasses_freshness_and_failed_day_guard(self):
        self.cache.write(normalize(raw(2),2,NOW-timedelta(days=8)))
        self.fetch.side_effect=OSError('offline')
        self.cache.request(2,automatic=True)
        self.cache.write(normalize(raw(2),2,NOW-timedelta(days=1)))
        self.fetch.side_effect=lambda address:raw(address)
        self.assertTrue(self.controller.refresh_system(2));self.run_worker()
        self.assertFalse(self.controller.refresh_system(2))
        self.assertEqual(self.fetch.call_count,2)

    def test_manual_without_cache_then_repeat_keeps_files_and_model_untouched(self):
        self.assertTrue(self.controller.refresh_system(2));self.run_worker()
        cache_path = self.cache.path(2)
        before = (cache_path.read_bytes(), cache_path.stat().st_mtime_ns)
        self.pool.reset_mock(); self.fetch.reset_mock()
        updated, skipped = [], []
        self.controller.updated.connect(updated.append)
        self.controller.alreadyUpdated.connect(skipped.append)
        for _ in range(3): self.assertFalse(self.controller.refresh_system(2))
        self.assertEqual(skipped, [2, 2, 2]); self.assertEqual(updated, [])
        self.pool.start.assert_not_called(); self.fetch.assert_not_called()
        self.assertEqual((cache_path.read_bytes(), cache_path.stat().st_mtime_ns), before)
        self.assertFalse((self.cache.root/'attempts').exists())

    def test_automatic_success_blocks_manual_even_after_restart_without_writes(self):
        self.cache.request(2, automatic=True)
        paths = [self.cache.path(2), self.cache.root/'attempts'/'2.json']
        before = [(p.read_bytes(), p.stat().st_mtime_ns) for p in paths]
        self.fetch.reset_mock()
        restarted = SpanshStations(self.settings, cache=self.cache, pool=self.pool)
        self.assertFalse(restarted.refresh_system(2))
        self.assertEqual(self.cache.request(2, manual=True)[1], None)
        self.assertEqual([(p.read_bytes(), p.stat().st_mtime_ns) for p in paths], before)
        self.pool.start.assert_not_called(); self.fetch.assert_not_called()

    def test_failed_manual_with_yesterdays_cache_allows_immediate_retry(self):
        self.cache.write(normalize(raw(2),2,NOW-timedelta(days=1)))
        old = self.cache.path(2).read_bytes()
        self.fetch.side_effect = OSError('offline')
        for _ in range(2):
            self.assertTrue(self.controller.refresh_system(2));self.run_worker()
            self.assertEqual(self.cache.path(2).read_bytes(), old)
        self.assertEqual(self.fetch.call_count, 2)
        self.assertFalse((self.cache.root/'attempts').exists())

    @unittest.skipUnless(hasattr(time, 'tzset'), 'Requires local timezone switching')
    def test_manual_local_midnight_and_utc_date_difference(self):
        self.addCleanup(time.tzset)
        with patch.dict(os.environ, {'TZ': 'Europe/Berlin'}):
            time.tzset()
            # 23:55 local -> 00:10 local, still the same UTC date.
            clock = [datetime(2026,9,16,21,55,tzinfo=timezone.utc)]
            self.cache.now = lambda: clock[0]
            self.assertTrue(self.controller.refresh_system(2));self.run_worker()
            clock[0] += timedelta(minutes=15)
            self.assertTrue(self.controller.refresh_system(2));self.run_worker()
            # Different UTC dates, but still the same local day: blocked.
            clock[0] = datetime(2026,9,17,0,10,tzinfo=timezone.utc)
            self.assertFalse(self.controller.refresh_system(2))
            self.assertEqual(self.fetch.call_count, 2)
        time.tzset()

    def test_queued_manual_rechecks_cache_without_merge_or_error(self):
        self.assertTrue(self.controller.refresh_system(2))
        self.cache.write(normalize(raw(2),2,NOW))
        updated, completed, skipped = [], [], []
        self.controller.updated.connect(updated.append)
        self.controller.completed.connect(lambda *args: completed.append(args))
        self.controller.alreadyUpdated.connect(skipped.append)
        self.run_worker()
        self.fetch.assert_not_called()
        self.assertEqual(updated, []); self.assertEqual(completed, [])
        self.assertEqual(skipped, [2]); self.assertFalse(self.controller.busy(2))

    def test_already_today_translation_in_all_twelve_languages(self):
        from cmdrhelper.i18n import _TRANSLATIONS
        self.assertEqual(len(_TRANSLATIONS), 12)
        for language, table in _TRANSLATIONS.items():
            self.assertTrue(table['spansh.refresh_already_today'].strip(), language)

    def test_parallel_same_id_block_even_across_generation(self):
        self.assertTrue(self.controller.refresh_system(2))
        self.assertFalse(self.controller.refresh_system(2))
        self.controller.set_enabled(False);self.controller.set_enabled(True)
        self.assertFalse(self.controller.refresh_system(2))
        self.assertTrue(self.controller.refresh_system(3))
        self.assertEqual(self.pool.start.call_count,2)

    def test_manual_off_does_not_fetch_or_show_cache(self):
        self.cache.write(normalize(raw(2),2,NOW))
        self.controller.set_enabled(False)
        self.assertFalse(self.controller.refresh_system(2))
        self.assertIsNone(self.controller.cached(2))
        self.fetch.assert_not_called()

    def test_invalid_response_and_offline_preserve_file(self):
        self.cache.write(normalize(raw(2),2,NOW-timedelta(days=8)))
        old=self.cache.path(2).read_bytes()
        for response in [OSError('offline'), {'system':{'id64':999}}]:
            self.fetch.side_effect=response if isinstance(response,Exception) else None
            self.fetch.return_value=response
            data,success=self.cache.request(2,manual=True)
            self.assertFalse(success);self.assertIsNotNone(data)
            self.assertEqual(self.cache.path(2).read_bytes(),old)

    def test_mark_failure_prevents_unguarded_network(self):
        with patch.object(self.cache,'_mark_automatic',side_effect=OSError('read-only')):
            self.assertEqual(self.cache.request(2,automatic=True),(None,False))
        self.fetch.assert_not_called()

    def test_button_busy_success_and_failure_current_display_only(self):
        from cmdrhelper.ui.system_overview import SystemOverviewDialog
        from cmdrhelper.i18n import tr
        dialog=SystemOverviewDialog('Test',BODIES,system_address=8,spansh=self.controller)
        updates=[];self.controller.updated.connect(updates.append)
        self.cache.write(normalize(raw(8),8,NOW-timedelta(days=1)))
        dialog.spansh_button.click()
        self.assertFalse(dialog.spansh_button.isEnabled())
        dialog.spansh_button.click();self.pool.start.assert_called_once()
        self.run_worker()
        self.fetch.assert_called_once_with(8);self.assertEqual(updates,[8])
        self.assertTrue(dialog.spansh_button.isEnabled())
        self.assertEqual(dialog.spansh_status.text(),tr('spansh.refresh_success'))
        dialog.spansh_button.click()
        self.assertTrue(dialog.spansh_button.isEnabled())
        self.assertEqual(dialog.spansh_status.text(),tr('spansh.refresh_already_today'))
        self.fetch.assert_called_once_with(8);self.pool.start.assert_called_once()
        self.assertEqual(updates, [8])
        self.cache.now=lambda:NOW+timedelta(days=1)
        self.fetch.side_effect=OSError('offline')
        dialog.spansh_button.click();self.run_worker()
        self.assertEqual(dialog.spansh_status.text(),tr('spansh.refresh_failed'))
        self.assertIsNotNone(self.cache.read(8));self.assertTrue(dialog.spansh_button.isEnabled())
        self.controller.set_enabled(False);self.assertFalse(dialog.spansh_button.isEnabled())
        dialog.close()


    def test_open_overview_refresh_after_commander_has_left_system(self):
        preview=SimpleNamespace(bodies=BODIES,set_stations=Mock())
        overview=SimpleNamespace(system_address=8,commander_id=1,preview=preview)
        db=SimpleNamespace(system_stations=Mock(return_value=[journal()]))
        window=SimpleNamespace(state=SimpleNamespace(system_address=9,database=db),
            _system_overview_window=overview,_chronicle_system_window=None,
            _station_display_model=Mock(return_value=['merged']))
        MainWindow._station_model_updated(window,8)
        db.system_stations.assert_called_once_with(8,BODIES,1)
        preview.set_stations.assert_called_once_with(['merged'])
