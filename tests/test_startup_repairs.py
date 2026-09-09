"""Actual startup hook, revision transactions and retained historical coverage."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.journal_index import scan_journal_folder
from cmdrhelper.startup_repairs import FEATURES, repair_status, run_startup_repairs
from cmdrhelper.state import AppState
import cmdrhelper.startup_repairs as repairs


class StartupRepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.db = CMDRDatabase(self.folder/'test.db')
        self.cid = self.db.upsert_commander('F-A', 'Alpha')
        self.file = self.folder/'Journal.2026-09-08T000000.01.log'

    def seed(self, kinds=('bio','visits','mapping')):
        events = [dict(event='Commander', FID='F-A', Name='Alpha'),
            dict(event='Location', StarSystem='A', SystemAddress=1),
            dict(event='Location', StarSystem='A', SystemAddress=1),
            dict(event='FSDJump', StarSystem='B', SystemAddress=2),
            dict(event='FSDJump', StarSystem='A', SystemAddress=1),
            dict(event='ScanOrganic', ScanType='Analyse', SystemAddress=1, Body=24,
                 Genus='Genus', Species='Species', Variant='Variant'),
            dict(event='SAAScanComplete', SystemAddress=1, BodyID=24, BodyName='A 1',
                 ProbesUsed=3, EfficiencyTarget=4)]
        events.insert(1, dict(event='Scan', SystemAddress=1, BodyID=24, BodyName='A 1',
                              PlanetClass='Rocky body', MassEM=1, WasDiscovered=True, WasMapped=False))
        for i,e in enumerate(events):e['timestamp']=f'2026-09-08T00:00:{i:02}Z'
        self.file.write_text(''.join(json.dumps(e)+'\n' for e in events))
        scan_journal_folder(self.db,self.folder)
        self.db.store_snapshot(dict(system_address=1,system='A',last_timestamp='2026-09-08T00:00:07Z',
            system_bodies=[dict(body_id=24,name='A 1',body_type='Planet',self_mapped=True,
                                efficient_mapping=True,was_discovered=True,was_mapped=False)]),self.cid)
        with self.db._connect() as con:
            con.execute('update journal_sessions set last_read_offset=?,last_complete_line_offset=?',
                        (self.file.stat().st_size,self.file.stat().st_size))
        run_startup_repairs(self.db.path)
        with self.db._connect() as con:
            con.execute('delete from commander_state_repairs where feature in (?,?,?,?)',FEATURES)
            if 'bio' in kinds:con.execute('delete from biology')
            if 'visits' in kinds:
                con.execute('delete from system_visits')
                con.execute('''insert into system_visits(commander_id,system_address,system_name,visited_at)
                    values(?,1,'A','2026-09-08T00:00:01Z'),(?,1,'A','2026-09-08T00:00:02Z')''',(self.cid,self.cid))
            if 'mapping' in kinds:
                con.execute('update commander_bodies set mapped_at=NULL,probes_used=NULL,efficiency_target=NULL')

    def snapshot(self):
        with self.db._connect() as con:
            return {t:con.execute('select * from '+t).fetchall() for t in
                    ('biology','system_visits','commander_bodies','commander_state_repairs')}

    def status(self,feature):
        with self.db._connect() as con:return repair_status(con,self.cid,feature)

    def startup(self):
        state=SimpleNamespace(database=self.db,journal_folder=self.folder,
            initializationStarted=Mock(),initializationProgress=Mock(),initializationFinished=Mock(),
            journalIndexReady=Mock())
        state._repair_indexed_commander_state = lambda sessions, folder: (
            AppState._repair_indexed_commander_state(state, sessions, folder)
        )
        state._latest_identified_index_session = lambda sessions: (
            AppState._latest_identified_index_session(state, sessions)
        )
        state._read_latest_position_event = AppState._read_latest_position_event
        with patch('cmdrhelper.state.threading.Thread') as thread:
            thread.side_effect=lambda **kw: SimpleNamespace(start=kw['target'])
            AppState._start_initial_journal_index(state)
        self.assertTrue(state.journalIndexReady.emit.called)
        return state

    def test_fresh_installation_marks_empty_revisions_without_backup(self):
        with self.db._connect() as con:
            self.assertEqual(repair_status(con,self.cid,FEATURES[0]),'not_run')
        with patch('cmdrhelper.startup_repairs.create_repair_backup') as backup:
            results=run_startup_repairs(self.db.path)
        self.assertEqual([r['status'] for r in results],['complete']*len(FEATURES))
        backup.assert_not_called()

    def test_old_schema_actual_startup_all_gaps_and_second_start(self):
        self.seed()
        with self.db._connect() as con:
            for name in ('status','attempted_revision','last_attempt_at','last_error'):
                con.execute('alter table commander_state_repairs drop column '+name)
            con.execute('alter table journal_sessions drop column repair_read_offset')
            con.execute('alter table journal_sessions drop column repair_commander_id')
            con.execute('pragma user_version=15')
        self.db=CMDRDatabase(self.db.path)
        with self.db._connect() as con:self.assertEqual(con.execute('pragma user_version').fetchone()[0],17)
        self.startup()
        data=self.snapshot()
        self.assertEqual(len(data['biology']),1)
        with self.db._connect() as con:
            self.assertEqual(con.execute('select system_address from system_visits order by visited_at').fetchall(),[(1,),(2,),(1,)])
            self.assertEqual(con.execute('select mapped_at,probes_used,efficiency_target,self_mapped,efficient_mapping from commander_bodies').fetchone(),('2026-09-08T00:00:07Z',3,4,1,1))
        self.assertTrue(list(self.folder.glob('*.pre-startup-repairs-*.bak')))
        self.assertTrue(all(self.status(f)=='complete' for f in FEATURES))
        with patch('cmdrhelper.startup_repairs._plan',side_effect=AssertionError('no second scan')):
            self.startup()
        self.assertEqual(data,self.snapshot())

    def test_only_bio_gap(self):
        self.seed(('bio',));self.assertEqual([r['changed'] for r in run_startup_repairs(self.db.path)],[1,0,0,0])

    def test_only_visits_gap(self):
        self.seed(('visits',));self.assertEqual([r['changed'] for r in run_startup_repairs(self.db.path)],[0,3,0,0])

    def test_only_mapping_gap(self):
        self.seed(('mapping',));self.assertEqual([r['changed'] for r in run_startup_repairs(self.db.path)],[0,0,1,0])

    def test_missing_journal_is_incomplete_and_retried(self):
        self.seed();text=self.file.read_text();self.file.unlink()
        self.startup()
        self.assertTrue(all(self.status(f)=='incomplete' for f in FEATURES))
        self.file.write_text(text)
        self.startup()
        self.assertTrue(all(self.status(f)=='complete' for f in FEATURES))

    def test_corrupt_journal_is_failed_not_complete(self):
        self.seed();text=self.file.read_text();self.file.write_text(text.replace('ScanOrganic','ScanOrgani!').replace('"Variant"','!Variant!'))
        self.startup()
        self.assertTrue(all(self.status(f)=='failed' for f in FEATURES))

    def test_unreadable_journal_is_failed_and_startup_continues(self):
        self.seed()
        original=Path.open
        def blocked(path,*args,**kwargs):
            if path==self.file:raise PermissionError('test unreadable history')
            return original(path,*args,**kwargs)
        with patch.object(Path,'open',blocked):self.startup()
        self.assertTrue(all(self.status(f)=='failed' for f in FEATURES))

    def test_abort_rolls_back_data_and_success_revision(self):
        self.seed();before=self.snapshot();original=repairs._apply
        def interrupted(con,cid,feature,plan):
            original(con,cid,feature,plan)
            raise KeyboardInterrupt('test abort after writes')
        with patch.object(repairs,'_apply',interrupted):
            with self.assertRaises(KeyboardInterrupt):run_startup_repairs(self.db.path)
        after=self.snapshot()
        for table in ('biology','system_visits','commander_bodies'):self.assertEqual(before[table],after[table])
        self.assertEqual(self.status(FEATURES[0]),'failed')
        with self.db._connect() as con:self.assertEqual(con.execute('select revision from commander_state_repairs where feature=?',(FEATURES[0],)).fetchone()[0],0)
        self.assertTrue(all(r['status']=='complete' for r in run_startup_repairs(self.db.path)))

    def test_backup_failure_does_not_change_data_or_mark_success(self):
        self.seed();before=self.snapshot()
        with self.db._connect() as con:
            con.execute('UPDATE commander_unsold_cartography SET estimated_value=0')
        with patch.object(repairs,'create_repair_backup',side_effect=OSError('disk full')):
            run_startup_repairs(self.db.path)
        after=self.snapshot()
        for table in ('biology','system_visits','commander_bodies'):self.assertEqual(before[table],after[table])
        self.assertTrue(all(self.status(f)=='failed' for f in FEATURES))

    def test_correct_data_and_other_commander_are_preserved(self):
        self.seed(());other=self.db.upsert_commander('F-B','Bravo')
        before=self.snapshot()
        self.assertTrue(all(r['changed']==0 for r in run_startup_repairs(self.db.path)))
        after=self.snapshot()
        for table in ('biology','system_visits','commander_bodies'):self.assertEqual(before[table],after[table])
        with self.db._connect() as con:
            self.assertFalse(con.execute('select 1 from biology where commander_id=?',(other,)).fetchone())

    def test_wrong_identity_is_rejected(self):
        self.seed();self.file.write_text(self.file.read_text().replace('F-A','F-X'))
        results=run_startup_repairs(self.db.path)
        self.assertTrue(all(r['status']=='failed' for r in results))

    def test_missing_mapping_evidence_remains_incomplete(self):
        self.seed(('mapping',))
        text=self.file.read_text().replace('"ProbesUsed": 3','"UnusedKeyX": 3')
        self.file.write_text(text)
        with self.db._connect() as con:
            con.execute('update journal_sessions set last_read_offset=?',(self.file.stat().st_size,))
        results=run_startup_repairs(self.db.path)
        self.assertEqual(next(r for r in results if r['feature']=='mapping_metadata')['status'],'incomplete')
        with self.db._connect() as con:
            self.assertEqual(con.execute('select mapped_at,probes_used,efficiency_target from commander_bodies').fetchone(),('2026-09-08T00:00:07Z',None,4))

    def test_missing_import_without_session_is_not_silently_ignored(self):
        self.seed()
        with self.db._connect() as con:
            con.execute("insert into journal_imports(commander_id,journal_file,file_size,modified_ns,last_import) values(?, 'lost.log', 42, 0, '')",(self.cid,))
        self.assertTrue(all(r['status']=='incomplete' for r in run_startup_repairs(self.db.path)))

    def test_truncation_cannot_erase_pending_repair_coverage(self):
        self.seed();original=self.file.read_text()
        self.file.write_text(original.splitlines()[0]+'\n')
        self.startup()
        self.assertTrue(all(self.status(f)=='failed' for f in FEATURES))
        self.startup()
        self.assertTrue(all(self.status(f)=='failed' for f in FEATURES))
        self.file.write_text(original)
        self.startup()
        self.assertTrue(all(self.status(f)=='complete' for f in FEATURES))

    def test_menu_only_legacy_import_requires_no_guessed_commander(self):
        self.seed()
        menu=self.folder/'Journal.2026-09-07T000000.01.log'
        menu.write_text('{"event":"Fileheader"}\n{"event":"Shutdown"}\n')
        with self.db._connect() as con:
            con.execute("insert into journal_imports(commander_id,journal_file,file_size,modified_ns,last_import) values(?,?,?,0,'')",
                        (self.cid,str(menu),menu.stat().st_size))
        self.assertTrue(all(r['status']=='complete' for r in run_startup_repairs(self.db.path)))

    def test_hard_process_exit_rolls_back_data_and_marker(self):
        self.seed();before=self.snapshot()
        script = """
import os, sys
import cmdrhelper.startup_repairs as repairs
original = repairs._apply
def crash(con, cid, feature, plan):
    original(con, cid, feature, plan)
    os._exit(23)
repairs._apply = crash
repairs.run_startup_repairs(sys.argv[1])
"""
        result=subprocess.run([sys.executable,'-c',script,str(self.db.path)],check=False)
        self.assertEqual(result.returncode,23)
        after=self.snapshot()
        for table in ('biology','system_visits','commander_bodies'):
            self.assertEqual(before[table],after[table])
        self.assertEqual(self.status('biology_findings'),'failed')
        self.assertEqual(self.status('system_visits'),'not_run')
        self.assertTrue(all(r['status']=='complete' for r in run_startup_repairs(self.db.path)))

    def test_two_commanders_keep_distinct_mapping_and_bio_facts(self):
        self.seed();other=self.db.upsert_commander('F-B','Bravo')
        other_file=self.folder/'Journal.2026-09-09T000000.01.log'
        text=self.file.read_text().replace('F-A','F-B').replace('Alpha','Bravo').replace('"ProbesUsed": 3','"ProbesUsed": 5').replace('"EfficiencyTarget": 4','"EfficiencyTarget": 6')
        other_file.write_text(text)
        scan_journal_folder(self.db,self.folder)
        self.db.store_snapshot(dict(system_address=1,system='A',system_bodies=[
            dict(body_id=24,name='A 1',self_mapped=True)]),other)
        with self.db._connect() as con:
            con.execute('update journal_sessions set last_read_offset=? where commander_id=?',
                        (other_file.stat().st_size,other))
        run_startup_repairs(self.db.path)
        with self.db._connect() as con:
            self.assertEqual(con.execute('select commander_id,probes_used,efficiency_target from commander_bodies order by commander_id').fetchall(),[(self.cid,3,4),(other,5,6)])
            self.assertEqual(con.execute('select commander_id,count(*) from biology group by commander_id order by commander_id').fetchall(),[(self.cid,1),(other,1)])

    def test_no_journal_folder_still_records_missing_history(self):
        self.seed();self.file.unlink()
        state=SimpleNamespace(database=self.db,journal_folder=None,initializationFinished=Mock())
        with patch('cmdrhelper.state.threading.Thread') as thread:
            thread.side_effect=lambda **kw: SimpleNamespace(start=kw['target'])
            AppState._start_initial_journal_index(state)
        state.initializationFinished.emit.assert_called_once_with('')
        self.assertTrue(all(self.status(f)=='incomplete' for f in FEATURES))

    def test_schema_migration_is_atomic_and_retryable(self):
        with self.db._connect() as con:
            for name in ('status','attempted_revision','last_attempt_at','last_error'):
                con.execute('alter table commander_state_repairs drop column '+name)
            con.execute('alter table journal_sessions drop column repair_read_offset')
            con.execute('alter table journal_sessions drop column repair_commander_id')
            con.execute('pragma user_version=15')
        class BrokenConnection(sqlite3.Connection):
            def execute(self, statement, *args):
                result=super().execute(statement,*args)
                if statement.startswith('ALTER TABLE commander_state_repairs'):
                    raise RuntimeError('simulated interruption during migration')
                return result
        broken=sqlite3.connect(self.db.path,factory=BrokenConnection)
        self.addCleanup(broken.close)
        with patch.object(self.db,'_connect',return_value=broken):
            with self.assertRaises(RuntimeError):self.db._maybe_migrate_v16()
        with self.db._connect() as con:
            self.assertEqual(con.execute('pragma user_version').fetchone()[0],15)
            self.assertNotIn('status',{r[1] for r in con.execute('pragma table_info(commander_state_repairs)')})
        self.db=CMDRDatabase(self.db.path)
        with self.db._connect() as con:self.assertEqual(con.execute('pragma user_version').fetchone()[0],17)
