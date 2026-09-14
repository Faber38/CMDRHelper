"""Focused P1 regressions: real SQLite, real journals and a Qt heartbeat."""
import json
import os
import sqlite3
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QObject, QTimer, Qt
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.journal_catchup import capture, catch_up, load_sessions, validate_input
from cmdrhelper.journal_index import scan_journal_folder
from cmdrhelper.journal_reader import read_journal_delta
from cmdrhelper.journal_watcher import JournalWatcher
from cmdrhelper.state import AppState


def event(kind, **values):
    return dict(event=kind, timestamp='2026-09-14T12:00:00Z', **values)


def append(path, *events):
    with path.open('ab') as stream:
        for item in events:
            stream.write(json.dumps(item).encode() + b'\n')


class ImportCatchupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.db = CMDRDatabase(self.folder / 'state.db')
        self.path = self.folder / 'Journal.2026-09-14T120000.01.log'
        append(self.path, event('LoadGame', FID='F1', Commander='Test', Ship='CobraMkIII'))
        self.cid = scan_journal_folder(self.db, self.folder)[0]['commander_id']
        events, offset = read_journal_delta(self.path, 0)
        self.db.apply_commander_journal_delta(self.cid, self.path, events, offset)

    def offset(self, path=None):
        return next(row['last_read_offset'] for row in load_sessions(self.db)
                    if row['journal_file'] == str(path or self.path))

    def test_growth_multiple_rotations_commander_switch_and_retry_once(self):
        context = capture(self.db, self.folder)
        append(self.path, event('Location', StarSystem='A', SystemAddress=10))
        second = self.folder / 'Journal.2026-09-14T130000.01.log'
        third = self.folder / 'Journal.2026-09-14T140000.01.log'
        append(second, event('LoadGame', FID='F1', Commander='Test'),
               event('Location', StarSystem='B', SystemAddress=20))
        append(third, event('LoadGame', FID='F2', Commander='Other'),
               event('Location', StarSystem='C', SystemAddress=30))
        # The importer may already have indexed all new sessions. They must
        # still be recognized against the pre-import baseline.
        self.db.import_journal_archive(self.folder)
        with patch.object(self.db, 'apply_commander_journal_delta',
                          wraps=self.db.apply_commander_journal_delta) as apply:
            catch_up(self.db, context)
            self.assertEqual([Path(c.args[1]) for c in apply.call_args_list],
                             [self.path, second, third])
            catch_up(self.db, context)
            self.assertEqual(apply.call_count, 3)
        self.assertEqual(self.db.commander_summary(self.cid)['persistent_location']['system_name'], 'B')
        for path in (self.path, second, third):
            self.assertEqual(self.offset(path), path.stat().st_size)

    def test_partial_tail_stops_before_next_file_and_is_not_acknowledged(self):
        context = capture(self.db, self.folder)
        old = self.offset()
        line = json.dumps(event('Location', StarSystem='A', SystemAddress=10)).encode()
        with self.path.open('ab') as stream:
            stream.write(line)
        second = self.folder / 'Journal.2026-09-14T130000.01.log'
        append(second, event('LoadGame', FID='F1', Commander='Test'))
        with self.assertRaises(OSError):
            catch_up(self.db, context)
        self.assertEqual(self.offset(), old)
        self.assertEqual(len(load_sessions(self.db)), 1)
        with self.path.open('ab') as stream:
            stream.write(b'\n')
        catch_up(self.db, context)
        self.assertEqual(self.offset(second), second.stat().st_size)

    def test_persistence_failure_rolls_back_cursor_and_index_signature(self):
        context = capture(self.db, self.folder)
        before = load_sessions(self.db)[0]
        append(self.path, event('Missions', Active=[{'MissionID': 2**63}]))
        with patch.object(self.db, 'store_commander_missions', side_effect=sqlite3.OperationalError('test')):
            with self.assertRaises(sqlite3.OperationalError):
                catch_up(self.db, context)
        after = load_sessions(self.db)[0]
        for field in ('last_read_offset', 'sha256', 'file_size', 'modified_ns'):
            self.assertEqual(before[field], after[field])
        catch_up(self.db, context)
        self.assertEqual(self.db.commander_missions(self.cid)[0]['mission_id'], 2**63)

    def test_replacement_and_truncation_fail_closed(self):
        original = self.path.read_bytes()
        for raw in (b'{}\n', original.replace(b'F1', b'F2')):
            with self.subTest(raw=raw):
                self.path.write_bytes(original)
                context = capture(self.db, self.folder)
                old = self.offset()
                self.path.write_bytes(raw)
                with self.assertRaises(RuntimeError):
                    catch_up(self.db, context)
                self.assertEqual(self.offset(), old)

    def test_archive_and_catchup_do_not_double_count_surface_mining(self):
        context = capture(self.db, self.folder)
        append(self.path,
               event('Location', StarSystem='A', SystemAddress=10, BodyID=7, Body='A 1'),
               event('Touchdown', SystemAddress=10, BodyID=7, Body='A 1'),
               event('LaunchSRV', SRVType='mev_rhino', PlayerControlled=True),
               event('MiningRefined', Type='gold'))
        self.db.import_journal_archive(self.folder)
        catch_up(self.db, context)
        self.assertEqual(self.db.surface_mining_for_body(10, 7, self.cid)['commodities'][0]['quantity'], 1)

    def test_import_index_cannot_reset_offset_on_replacement(self):
        context = capture(self.db, self.folder)
        old = load_sessions(self.db)[0]
        self.path.write_bytes(b'{}\n')
        with self.assertRaises(RuntimeError):
            self.db.import_journal_archive(self.folder,
                validate_input=lambda path: validate_input(context, path))
        current = load_sessions(self.db)[0]
        for field in ('last_read_offset', 'sha256', 'fid_seen'):
            self.assertEqual(current[field], old[field])

    def test_catchup_growth_does_not_claim_archive_completion(self):
        context = capture(self.db, self.folder)
        self.db.import_journal_archive(self.folder)
        archived_size = self.path.stat().st_size
        self.assertEqual(load_sessions(self.db)[0]['fully_imported'], 1)
        append(self.path, event('Location', StarSystem='A', SystemAddress=10))
        catch_up(self.db, context)
        self.assertEqual(load_sessions(self.db)[0]['fully_imported'], 0)
        with self.db._connect() as con:
            self.assertEqual(con.execute('SELECT file_size FROM journal_imports').fetchone()[0], archived_size)

    def test_watcher_notices_late_tail_in_rotated_pause_file(self):
        second = self.folder / 'Journal.2026-09-14T130000.01.log'
        append(second, event('LoadGame', FID='F1', Commander='Test'))
        watcher = JournalWatcher()
        watcher.set_folder(self.folder)
        st = self.path.stat()
        watcher._catchup_signatures = {str(self.path):
            (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns)}
        watcher.check_now()
        watcher.refresh_finished(True)
        signature = watcher._sig
        append(self.path, event('Location', StarSystem='A', SystemAddress=10))
        watcher.check_now()
        self.assertTrue(watcher._catchup_requested)
        self.assertTrue(watcher._refresh_in_progress)
        self.assertEqual(watcher._sig, signature)
        watcher.refresh_finished(False)
        self.assertEqual(watcher._retry_delay, 2)
        self.assertEqual(watcher._sig, signature)

    def test_real_archive_lock_never_blocks_gui_watcher_and_catches_up(self):
        state = AppState.__new__(AppState)
        QObject.__init__(state)
        state.database = self.db
        state.journal_folder = self.folder
        state._database_import_running = False
        state._initialization_visible = False
        state._journal_catchup = None
        state.commander_id = self.cid
        state.commander_fid = 'F1'
        state._inara_identity_matches = Mock(return_value=False)
        state._run_journal_learning = Mock()
        state.refresh = Mock(return_value=True)
        state.watcher = JournalWatcher(state)
        state.watcher.set_folder(self.folder)
        state.watcher.journalChanged.connect(state._refresh_from_watcher)
        state.journalCatchupReady.connect(state._finish_journal_catchup, Qt.QueuedConnection)
        entered, release = threading.Event(), threading.Event()
        original_connect = self.db._connect
        inserts = [0]
        def connect():
            con = original_connect()
            if threading.current_thread().name == 'CMDRHelper-Database-Import':
                def trace(sql):
                    if 'INSERT INTO systems (' in sql:
                        inserts[0] += 1
                        if inserts[0] == 2:
                            entered.set()
                            release.wait(10)
                con.set_trace_callback(trace)
            return con
        append(self.path, event('Location', StarSystem='A', SystemAddress=10),
               event('Location', StarSystem='B', SystemAddress=20))
        ticks = []
        timer = QTimer()
        timer.setInterval(10)
        timer.timeout.connect(lambda: ticks.append(time.monotonic()))
        timer.start()
        try:
            with patch.object(self.db, '_connect', side_effect=connect):
                state.import_journal_archive()
                deadline = time.monotonic() + 5
                while not entered.is_set() and time.monotonic() < deadline:
                    QTest.qWait(10)
                self.assertTrue(entered.is_set())
                append(self.path, event('Location', StarSystem='C', SystemAddress=30))
                state.watcher.check_now()
                self.assertFalse(state.refresh.called)
                self.assertIsNone(state.watcher._sig)
                QTest.qWait(120)
                self.assertGreaterEqual(len(ticks), 5)
                self.assertLess(max(b-a for a,b in zip(ticks,ticks[1:])), 0.5)
                release.set()
                deadline = time.monotonic() + 5
                while (state._database_import_running or state._journal_catchup_running) and time.monotonic() < deadline:
                    QTest.qWait(10)
                self.assertFalse(state._database_import_running)
                self.assertFalse(state._journal_catchup_running)
                self.assertEqual(self.offset(), self.path.stat().st_size)
                self.assertTrue(state.refresh.called)
        finally:
            release.set()
            timer.stop()


if __name__ == '__main__':
    unittest.main()
