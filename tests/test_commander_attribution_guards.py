"""Synthetic source conflicts and legacy credential ownership; no network."""
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.journal_index import scan_journal_folder
from cmdrhelper.journal_reader import read_latest_state, read_journal_delta
import test_edsm_commander_settings as edsm_fixtures
import test_inara_uploader as inara_fixtures


class SourceGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.db = CMDRDatabase(self.folder/'synthetic.db')
        self.path = self.folder/'Journal.2026-10-18T120000.01.log'
        self.append('Commander', FID='F-A', Name='Same')
        self.sessions = scan_journal_folder(self.db, self.folder)
        self.cid = self.sessions[0]['commander_id']
        events, self.offset = read_journal_delta(self.path, 0)
        self.db.apply_commander_journal_delta(self.cid, self.path, events, self.offset)
        self.sessions[0]['last_read_offset'] = self.offset

    def append(self, kind, **fields):
        with self.path.open('a') as f:
            f.write(json.dumps(dict(event=kind, timestamp='2026-10-18T12:00:00Z', **fields))+'\n')

    def conflict(self):
        self.append('Commander', FID='F-B', Name='Same')
        self.append('FSDJump', StarSystem='Foreign', SystemAddress=222)
        self.append('MissionAccepted', MissionID=42, Name='Mission_Delivery')
        self.append('ShipLocker', Components=[dict(Name='graphene', Count=9)])
        self.append('PowerplayMerits', Power='Test Power', Merits=999)

    def test_live_ambiguity_discards_old_internal_id(self):
        self.conflict()
        read_latest_state(self.folder, indexed_sessions=self.sessions, powerplay_history=False)
        self.assertEqual(self.sessions[0]['attribution_status'], 'ambiguous')
        self.assertIsNone(self.sessions[0]['commander_id'])
        self.assertIsNone(self.sessions[0]['fid_seen'])
        self.assertEqual(self.sessions[0]['last_read_offset'], self.offset)

    def test_missing_identity_cannot_inherit_cached_assignment(self):
        self.path.write_text(json.dumps(dict(event='Fileheader'))+'\n')
        read_latest_state(self.folder, indexed_sessions=self.sessions, powerplay_history=False)
        self.assertEqual(self.sessions[0]['attribution_status'], 'unknown')
        self.assertIsNone(self.sessions[0]['commander_id'])
        self.assertIsNone(self.sessions[0]['fid_seen'])

    def test_delta_rejects_conflict_without_writes(self):
        self.conflict()
        events, end = read_journal_delta(self.path, self.offset)
        before = self.db.path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'identity'):
            self.db.apply_commander_journal_delta(self.cid, self.path, events, end, enqueue_inara=True)
        self.assertEqual(self.db.path.read_bytes(), before)
        self.assertEqual(self.db.inara_pending(self.cid), [])

    def test_refresh_rejects_source_before_pp2_delta_and_material_readers(self):
        from cmdrhelper.state import AppState
        from cmdrhelper.material_inventory import MaterialInventoryReader
        from cmdrhelper.odyssey_inventory import OdysseyInventoryReader
        from cmdrhelper.journal_catchup import load_sessions
        class PipelineObserved(Exception):
            pass
        state = SimpleNamespace(journal_folder=self.folder, watcher=SimpleNamespace(_current=self.path),
            _journal_index_sessions=self.sessions, _journal_index_current=str(self.path),
            system='', system_address=None, ship_loadout=None, commander='Same',
            commander_fid='F-A', commander_id=self.cid, changed=Mock(),
            _prepare_indexed_live_state=Mock(), _apply_commander_identity=Mock(return_value=False),
            _inara_identity_matches=Mock(return_value=True),
            _emit_journal_positions=Mock(side_effect=PipelineObserved), database=self.db)
        state._store_latest_journal_session = AppState._store_latest_journal_session.__get__(state)
        self.conflict()
        with patch.object(self.db, 'apply_commander_journal_delta', wraps=self.db.apply_commander_journal_delta) as apply:
            with self.assertRaises(PipelineObserved):
                # Stop only after the real attribution, PP2 and delta pipeline,
                # before unrelated UI/network publication needs a full AppState.
                AppState.refresh(state)
            apply.assert_not_called()
        rows = load_sessions(self.db)
        self.assertIsNone(rows[0]['commander_id'])
        self.assertEqual(rows[0]['attribution_status'], 'ambiguous')
        self.assertEqual(rows[0]['last_read_offset'], self.offset)
        self.assertEqual(self.db.inara_pending(self.cid), [])
        self.assertEqual(self.db.commander_missions(self.cid), [])
        self.assertFalse(MaterialInventoryReader().reconstruct(self.cid, 'F-A', rows).known)
        self.assertFalse(OdysseyInventoryReader().reconstruct(self.cid, 'F-A', rows).known)
        with self.db._connect() as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM pp2_events').fetchone()[0], 0)
        self.assertEqual(state._last_refresh_error, 'journal_identity_conflict')

    def test_unknown_and_mismatched_database_identity_rejected(self):
        self.append('FSDJump', StarSystem='Test', SystemAddress=333)
        events, end = read_journal_delta(self.path, self.offset)
        for status, fid in (('unknown', None), ('ambiguous', None), ('identified', 'F-B'), ('identified', None)):
            with self.db._connect() as con:
                con.execute('UPDATE journal_sessions SET attribution_status=?,fid_seen=?', (status, fid))
            before = self.db.path.read_bytes()
            with self.assertRaisesRegex(ValueError, 'identity'):
                self.db.apply_commander_journal_delta(self.cid, self.path, events, end, enqueue_inara=True)
            self.assertEqual(self.db.path.read_bytes(), before)

    def test_other_source_and_revalidated_source_can_work(self):
        self.conflict()
        scan_journal_folder(self.db, self.folder)
        other = self.folder/'Journal.2026-10-18T130000.01.log'
        other.write_text(json.dumps(dict(event='Commander', FID='F-C', Name='Same'))+'\n')
        indexed = scan_journal_folder(self.db, self.folder)
        target = next(s for s in indexed if s['journal_file'] == str(other))
        events, end = read_journal_delta(other, 0)
        self.db.apply_commander_journal_delta(target['commander_id'], other, events, end)
        # Restoring the synthetic original prefix is not an application repair.
        with self.path.open('r+b') as f: f.truncate(self.offset)
        self.append('FSDJump', StarSystem='Verified', SystemAddress=444)
        indexed = scan_journal_folder(self.db, self.folder)
        source = next(s for s in indexed if s['journal_file'] == str(self.path))
        self.assertEqual(source['attribution_status'], 'identified')
        events, end = read_journal_delta(self.path, self.offset)
        self.db.apply_commander_journal_delta(self.cid, self.path, events, end)
        self.assertEqual(self.db.commander_summary(self.cid)['persistent_location']['system_name'], 'Verified')


class LegacyGuardTests(unittest.TestCase):
    def fixture(self, service, fid='F-A', status='identified'):
        case = (edsm_fixtures.EDSMCommanderSettingsTests if service == 'edsm'
                else inara_fixtures.InaraCommanderSettingsTests)()
        case.setUp()
        self.addCleanup(case.tearDown)
        case.state._journal_index_sessions = [dict(attribution_status=status, fid_seen='F-A', commander_id=1)]
        for key,value in (('commander','Alpha'),('api_key','synthetic-secret'),('enabled',True)):
            case.settings.setValue(service+'/'+key,value)
        if fid is not None:
            case.settings.setValue(service+'/commander_fid',fid)
        return case

    @staticmethod
    def values(settings):
        return {k:settings.value(k) for k in settings.allKeys()}

    def test_inara_rejects_foreign_or_missing_proof_without_mutation(self):
        for fid,status in (('F-B','identified'),(None,'identified'),('F-A','ambiguous'),('F-A','unknown')):
            case=self.fixture('inara',fid,status)
            before=self.values(case.settings)
            case.state._migrate_legacy_inara_settings()
            self.assertEqual(self.values(case.settings),before)

    def test_edsm_same_name_is_not_identity_proof(self):
        for fid,status in ((None,'identified'),('F-B','identified'),('F-A','ambiguous')):
            case=self.fixture('edsm',fid,status)
            case.settings.setValue('edsm_upload/initialized',True)
            case.settings.setValue('edsm_upload/positions/synthetic',123)
            before=self.values(case.settings)
            case.state._migrate_legacy_edsm_settings()
            self.assertEqual(self.values(case.settings),before)

    def test_matching_proof_migrates_both_services(self):
        for service in ('edsm','inara'):
            case=self.fixture(service)
            getattr(case.state,'_migrate_legacy_'+service+'_settings')()
            self.assertEqual(case.settings.value(service+'/commanders/F-A/api_key'),'synthetic-secret')

    def test_matching_fid_survives_rename_but_requires_live_proof(self):
        for service in ('edsm', 'inara'):
            case = self.fixture(service)
            case.state.commander = 'Renamed'
            before = self.values(case.settings)
            case.state._journal_index_sessions = []
            getattr(case.state, '_migrate_legacy_'+service+'_settings')()
            self.assertEqual(self.values(case.settings), before)
            case.state._journal_index_sessions = [dict(attribution_status='identified', fid_seen='F-A')]
            with patch('cmdrhelper.state.threading.Thread', side_effect=AssertionError('unexpected upload')):
                getattr(case.state, '_migrate_legacy_'+service+'_settings')()
            self.assertEqual(case.settings.value(service+'/commanders/F-A/api_key'), 'synthetic-secret')

    def test_existing_positions_or_conflicting_upload_fid_refuse_migration(self):
        for key, value in (('edsm_upload/commanders/F-A/positions/synthetic', 456),
                           ('edsm_upload/commander_fid', 'F-B')):
            case = self.fixture('edsm')
            case.settings.setValue('edsm_upload/initialized', True)
            case.settings.setValue('edsm_upload/positions/synthetic', 123)
            case.settings.setValue(key, value)
            before = self.values(case.settings)
            self.assertFalse(case.state._migrate_legacy_edsm_settings())
            self.assertEqual(self.values(case.settings), before)

    def test_incomplete_upload_state_and_missing_live_fid_are_retained(self):
        case = self.fixture('edsm')
        case.settings.setValue('edsm_upload/positions/synthetic', 123)
        before = self.values(case.settings)
        self.assertFalse(case.state._migrate_legacy_edsm_settings())
        self.assertEqual(self.values(case.settings), before)
        self.assertEqual(case.state._legacy_migration_rejections['edsm'], 'incomplete_upload_state')
        for service in ('edsm', 'inara'):
            case = self.fixture(service)
            case.state.commander_fid = ''
            before = self.values(case.settings)
            getattr(case.state, '_migrate_legacy_'+service+'_settings')()
            self.assertEqual(self.values(case.settings), before)
            self.assertEqual(case.state._legacy_migration_rejections[service], 'missing_fid_proof')

    def test_existing_destination_is_never_overwritten(self):
        for service in ('edsm','inara'):
            case=self.fixture(service)
            prefix=service+'/commanders/F-A'
            case.settings.setValue(prefix+'/api_key','existing-synthetic-secret')
            case.settings.setValue('edsm_upload/commanders/F-A/positions/synthetic',456)
            case.settings.setValue('edsm_upload/positions/synthetic',123)
            case.settings.setValue('edsm_upload/initialized',True)
            getattr(case.state,'_migrate_legacy_'+service+'_settings')()
            self.assertEqual(case.settings.value(prefix+'/api_key'),'existing-synthetic-secret')
            self.assertEqual(int(case.settings.value('edsm_upload/commanders/F-A/positions/synthetic')),456)
