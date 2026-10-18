"""Synthetic metadata regressions; never open personal journals or settings."""
import hashlib
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
import test_import_catchup as catchup_tests
from test_import_catchup import append, event
from cmdrhelper.journal_index import scan_journal_folder
from cmdrhelper.journal_catchup import capture, catch_up, load_sessions
from cmdrhelper.state import AppState

class MetadataTests(unittest.TestCase):
    setUp = catchup_tests.ImportCatchupTests.setUp

    def row(self):
        return load_sessions(self.db)[0]

    def live(self):
        class Observed(Exception):
            pass
        sessions = scan_journal_folder(self.db, self.folder) if not hasattr(self, 'sessions') else self.sessions
        self.sessions = sessions
        state = SimpleNamespace(journal_folder=self.folder, watcher=SimpleNamespace(_current=self.path),
            _journal_index_sessions=sessions, _journal_index_current=str(self.path),
            system='', system_address=None, ship_loadout=None, commander='Test',
            commander_fid='F1', commander_id=self.cid, changed=Mock(),
            _prepare_indexed_live_state=Mock(), _apply_commander_identity=Mock(return_value=False),
            _inara_identity_matches=Mock(return_value=False),
            _emit_journal_positions=Mock(side_effect=Observed), database=self.db)
        state._store_latest_journal_session = AppState._store_latest_journal_session.__get__(state)
        try:
            AppState.refresh(state)
        except Observed:
            return
        self.fail('live pipeline stopped before publication: ' + state._last_refresh_error)

    def test_live_growth_and_restart(self):
        self.sessions = scan_journal_folder(self.db, self.folder)
        append(self.path, event('Location', StarSystem='SyntheticNext', SystemAddress=123))
        self.live()
        size = self.path.stat().st_size
        row = self.row()
        self.assertEqual((row['file_size'], row['last_complete_line_offset'], row['last_read_offset']), (size, size, size))
        self.assertEqual(row['modified_ns'], self.path.stat().st_mtime_ns)
        self.assertFalse(row['sha256']) # no obsolete hash; full hashing belongs to the index
        self.assertEqual(self.db.commander_summary(self.cid)['persistent_location']['system_name'], 'SyntheticNext')
        scan_journal_folder(self.db, self.folder)
        self.assertEqual(self.row()['sha256'], hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertEqual(self.row()['last_read_offset'], size)

    def test_catchup_without_new_events(self):
        # Reproduce the already committed cursor with stale index metadata.
        from cmdrhelper.journal_reader import read_journal_delta
        old = self.row()['last_read_offset']
        append(self.path, event('Location', StarSystem='SyntheticNext', SystemAddress=123))
        events, end = read_journal_delta(self.path, old)
        self.db.apply_commander_journal_delta(self.cid, self.path, events, end)
        context = capture(self.db, self.folder)
        catch_up(self.db, context)
        self.assertEqual(self.row()['file_size'], end)
        self.assertEqual(self.row()['last_complete_line_offset'], end)
        catch_up(self.db, context)
        self.assertEqual(self.row()['last_read_offset'], end)
        self.assertEqual(self.db.inara_pending(self.cid), [])

    def test_partial_tail_live_and_completion(self):
        self.sessions = scan_journal_folder(self.db, self.folder)
        append(self.path, event('Location', StarSystem='Partial', SystemAddress=124))
        complete = self.path.stat().st_size
        with self.path.open('ab') as stream:
            stream.write(b'{"event":"Music"')
        self.live()
        row = self.row()
        self.assertEqual(row['file_size'], self.path.stat().st_size)
        self.assertEqual(row['last_complete_line_offset'], complete)
        self.assertEqual(row['last_read_offset'], complete)
        self.assertIsNone(row['sha256'])
        with self.path.open('ab') as stream:
            stream.write(b'}\n')
        self.live()
        self.assertEqual(self.row()['last_read_offset'], self.path.stat().st_size)

    def test_metadata_transaction_rolls_back_with_facts(self):
        self.sessions = scan_journal_folder(self.db, self.folder)
        before = self.row()
        append(self.path, event('Location', StarSystem='Rollback', SystemAddress=125))
        with self.db._connect() as con:
            con.execute("""CREATE TRIGGER fail_cursor BEFORE UPDATE OF last_read_offset
                ON journal_sessions BEGIN SELECT RAISE(ABORT,'synthetic failure'); END""")
        with self.assertRaises(AssertionError):
            self.live()
        after = self.row()
        for key in ('file_size','modified_ns','sha256','last_complete_line_offset','last_read_offset'):
            self.assertEqual(after[key], before[key], key)
        self.assertNotEqual((self.db.commander_summary(self.cid).get('persistent_location') or {}).get('system_name'), 'Rollback')

    def test_changed_file_after_classification_refuses_metadata(self):
        from cmdrhelper.journal_reader import read_latest_state, verified_live_metadata
        sessions = scan_journal_folder(self.db, self.folder)
        read_latest_state(self.folder, indexed_sessions=sessions)
        old = self.row()
        append(self.path, event('Music'))
        with self.assertRaises(OSError):
            verified_live_metadata(self.path, sessions[-1], old['last_read_offset'])
        self.assertEqual(self.row(), old)

    def test_catchup_metadata_does_not_replay_outbox_or_touch_settings(self):
        from cmdrhelper.journal_reader import read_journal_delta
        from cmdrhelper.edsm_uploader import EDSMJournalUploader
        start = self.row()['last_read_offset']
        append(self.path, event('Location', StarSystem='Outbox', SystemAddress=126))
        events, end = read_journal_delta(self.path, start)
        self.db.apply_commander_journal_delta(self.cid, self.path, events, end, enqueue_inara=True)
        def outbox():
            with self.db._connect() as con:
                return con.execute('SELECT * FROM inara_outbox').fetchall()
        before = outbox()
        self.assertTrue(before)
        context = capture(self.db, self.folder)
        with patch.object(self.db, 'apply_commander_journal_delta', side_effect=AssertionError('replay')), \
                patch.object(EDSMJournalUploader, '_set_position', side_effect=AssertionError('EDSM cursor')):
            catch_up(self.db, context)
            catch_up(self.db, context)
        self.assertEqual(outbox(), before)
        self.assertEqual(self.row()['last_read_offset'], end)

    def test_partial_catchup_never_stores_prefix_as_full_file_hash(self):
        from cmdrhelper.startup_runtime import JournalPending
        context = capture(self.db, self.folder)
        append(self.path, event('Music'))
        end = self.path.stat().st_size
        with self.path.open('ab') as stream:
            stream.write(b'{')
        with self.assertRaises(JournalPending):
            catch_up(self.db, context)
        self.assertEqual(self.row()['file_size'], end + 1)
        self.assertEqual(self.row()['last_complete_line_offset'], end)
        self.assertEqual(self.row()['last_read_offset'], end)
        self.assertIsNone(self.row()['sha256'])

    def test_change_during_live_read_is_rejected(self):
        from cmdrhelper.journal_reader import _live_complete_events, _LIVE_LINE_CACHE
        from pathlib import Path
        _LIVE_LINE_CACHE.clear()
        before = self.path.stat()
        after = SimpleNamespace(st_dev=before.st_dev, st_ino=before.st_ino,
            st_size=before.st_size+1, st_mtime_ns=before.st_mtime_ns, st_ctime_ns=before.st_ctime_ns)
        with patch.object(Path, 'stat', side_effect=[before, after]):
            with self.assertRaises(OSError):
                _live_complete_events(self.path)
        self.assertNotIn(str(self.path), _LIVE_LINE_CACHE)

    def test_catchup_shortcut_does_not_bless_invalid_committed_source(self):
        before = self.row()
        with self.path.open('ab') as stream:
            stream.write(b'null\n')
        end = self.path.stat().st_size
        # Model a historical committed cursor, not a new import of invalid JSON.
        self.db.apply_commander_journal_delta(self.cid, self.path, [], end)
        catch_up(self.db, capture(self.db, self.folder))
        self.assertEqual(self.row()['file_size'], before['file_size'])
        self.assertEqual(self.row()['last_read_offset'], end)
