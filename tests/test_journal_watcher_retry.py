"""Retry timing and committed offsets after a failed SQLite transaction."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.journal_index import scan_journal_folder
from cmdrhelper.journal_reader import read_journal_delta
from cmdrhelper.journal_watcher import JournalWatcher


class JournalWatcherRetryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        self.path = self.folder / 'Journal.2026-01-01T000000.01.log'
        self.path.write_text('{}\n')
        self.watcher = JournalWatcher()
        self.watcher.set_folder(self.folder)
        self.emissions = []
        self.watcher.journalChanged.connect(lambda: self.emissions.append(True))
        self.clock = patch('cmdrhelper.journal_watcher.time.monotonic', return_value=100)
        self.now = self.clock.start()
        self.addCleanup(self.clock.stop)

    def test_backoff_caps_and_resets_without_acknowledging_failure(self):
        now = 100
        for delay in (2, 4, 8, 16, 32, 60, 60):
            self.now.return_value = now
            before = len(self.emissions)
            self.watcher.check_now()
            self.assertEqual(len(self.emissions), before + 1)
            self.watcher.refresh_finished(False)
            self.assertIsNone(self.watcher._sig)
            # Growing input must not bypass backoff for an uncommitted batch.
            with self.path.open('a') as handle:
                handle.write('{}\n')
            self.now.return_value = now + delay - 0.01
            self.watcher.check_now()
            self.assertEqual(len(self.emissions), before + 1)
            now += delay
        self.now.return_value = now
        self.watcher.check_now()
        self.watcher.refresh_finished(True)
        self.assertIsNotNone(self.watcher._sig)
        before = len(self.emissions)
        self.path.write_text('{}\n')
        self.watcher.check_now()
        self.assertEqual(len(self.emissions), before + 1)
        self.watcher.refresh_finished(False)
        self.now.return_value = now + 2
        self.watcher.check_now()
        self.assertEqual(len(self.emissions), before + 2)

    def test_folder_switch_clears_backoff(self):
        self.watcher.check_now()
        self.watcher.refresh_finished(False)
        self.watcher.set_folder(self.folder)
        self.watcher.check_now()
        self.assertEqual(len(self.emissions), 2)

    def test_failed_persistence_replays_whole_batch_then_commits(self):
        db = CMDRDatabase(self.folder / 'state.db')
        commander = db.upsert_commander('FID-A', 'Synthetic')
        events = [
            {'event': 'LoadGame', 'FID': 'FID-A', 'Commander': 'Synthetic'},
            {'event': 'Location', 'StarSystem': 'Test', 'SystemAddress': 42},
            {'event': 'Missions', 'Active': [{'MissionID': 2**63}]},
        ]
        for e in events:
            e['timestamp'] = '2026-01-01T00:00:00Z'
        self.path.write_text(''.join(json.dumps(e) + '\n' for e in events))
        scan_journal_folder(db, self.folder)

        def refresh():
            session = scan_journal_folder(db, self.folder)[0]
            batch, offset = read_journal_delta(self.path, session['last_read_offset'])
            try:
                db.apply_commander_journal_delta(commander, self.path, batch, offset)
            except sqlite3.OperationalError:
                self.watcher.refresh_finished(False)
            else:
                self.watcher.refresh_finished(True)

        self.watcher.journalChanged.connect(refresh)
        with patch.object(db, 'store_commander_missions', side_effect=sqlite3.OperationalError('synthetic failure')):
            self.watcher.check_now()
        self.assertEqual(scan_journal_folder(db, self.folder)[0]['last_read_offset'], 0)
        self.assertFalse(db.commander_summary(commander)['persistent_location'])
        self.assertIsNone(self.watcher._sig)
        self.now.return_value = 102
        self.watcher.check_now()
        self.assertEqual(scan_journal_folder(db, self.folder)[0]['last_read_offset'], self.path.stat().st_size)
        self.assertEqual(db.commander_missions(commander)[0]['mission_id'], 2**63)
        self.assertEqual(db.commander_summary(commander)['persistent_location']['system_name'], 'Test')
        self.assertIsNotNone(self.watcher._sig)
