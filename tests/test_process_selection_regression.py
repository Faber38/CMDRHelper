"""Local process evidence and selection persistence; no application or network startup."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QSettings
from cmdrhelper.game_instances import GameInstance, ProcessObservation, ProcessSnapshot, inspect_instances
from cmdrhelper.source_manager import SourceManager
from cmdrhelper.journal_reader import read_journal_delta
import test_mission_arrival as arrival_fixtures


class StableProcessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.proc = Path(self.tmp.name)
        (self.proc / 'uptime').write_text('1000.00 1000.00')
        self.entry = self.proc / '12'
        self.entry.mkdir()
        (self.entry / 'cmdline').write_bytes(b'/game/EliteDangerous64.exe\0')
        (self.entry / 'environ').write_bytes(b'')
        (self.entry / 'fd').mkdir()
        self.start(100)

    def start(self, ticks):
        (self.entry / 'stat').write_text('12 (game) ' + ' '.join(['S'] + ['0'] * 18 + [str(ticks)]))

    def test_wall_clock_jitter_does_not_change_identity(self):
        now = datetime(2026, 11, 8, tzinfo=timezone.utc)
        with patch('cmdrhelper.game_instances.datetime') as clock:
            clock.now.side_effect = [now, now + timedelta(milliseconds=1)]
            first, second = (inspect_instances(self.proc).instances[0] for _ in range(2))
        self.assertNotEqual(first.started, second.started)
        self.assertEqual(first.identity, second.identity)
        self.assertEqual(first.identity, (12, 100))
        self.assertIsInstance(first.started, float)

    def test_pid_reuse_exit_and_restart(self):
        first = inspect_instances(self.proc).instances[0]
        self.start(200)
        second = inspect_instances(self.proc).instances[0]
        self.assertNotEqual(first.identity, second.identity)
        (self.entry / 'cmdline').write_bytes(b'other\0')
        self.assertEqual(inspect_instances(self.proc).instances, [])
        (self.entry / 'cmdline').write_bytes(b'EliteDangerous64.exe\0')
        self.start(300)
        third = inspect_instances(self.proc).instances[0]
        self.assertNotEqual(second.identity, third.identity)
        self.entry.rename(self.proc / '13')
        self.assertNotEqual(third.identity, inspect_instances(self.proc).instances[0].identity)

    def test_pid_recycled_during_inspection_is_rejected(self):
        original = Path.read_text
        reads = 0
        def read(path, *args, **kwargs):
            nonlocal reads
            if path == self.entry / 'stat':
                reads += 1
                if reads == 2:
                    self.start(200)
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', read):
            result = inspect_instances(self.proc)
        self.assertFalse(result.available)
        self.assertEqual(result.instances, [])

    def test_existing_constructor_contract(self):
        self.assertEqual(GameInstance(12, 1.5, (), ()).identity, (12, 1.5))
        self.assertEqual(GameInstance(12, 1.5, (), (), 99).identity, (12, 99))

    def test_arrival_reuses_cache_but_invalidates_new_process(self):
        fixture = arrival_fixtures.ArrivalSourceTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        with patch('cmdrhelper.mission_arrival.read_journal_delta', wraps=read_journal_delta) as read:
            identities = []
            for started, ticks in [(1., 100), (1.001, 100), (2., 200)]:
                fixture.mock_process.return_value = ProcessSnapshot(True, [GameInstance(
                    12, started, journals=(str(fixture.path),), start_ticks=ticks)])
                snapshot = fixture.source.snapshot(fixture.state)
                self.assertIsNotNone(snapshot)
                identities.append(snapshot[0])
            self.assertEqual(read.call_count, 2)
            self.assertEqual(identities[0], identities[1])
            self.assertNotEqual(identities[1], identities[2])


class SelectionSettingsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / 'settings.ini')
        self.raw = QSettings(self.path, QSettings.IniFormat)
        self.settings = Mock(wraps=self.raw)
        self.state = NS(viewed_commander_id=1, settings=self.settings,
                        database=NS(list_commanders=lambda: [{'id': 1, 'fid': 'A'}, {'id': 2, 'fid': 'B'}]),
                        follow_live_commander=True, viewedCommanderChanged=Mock())
        self.manager = NS(state=self.state, preferred_source='steam', _process_observation=ProcessObservation())
        self.select(1)
        self.settings.reset_mock()

    def select(self, cid):
        SourceManager._select(self.manager, cid)

    def persisted(self):
        # A separate interpreter avoids QSettings' process-local shared cache.
        script = """import json,sys
from PySide6.QtCore import QSettings
s=QSettings(sys.argv[1],QSettings.IniFormat)
print(json.dumps([s.value('commander_view/'+k,type=t) for k,t in
 [('viewed_commander_id',int),('fid',str),('follow_live',bool),('source_id',str)]]))
"""
        return json.loads(subprocess.check_output([sys.executable, '-B', '-c', script, self.path], text=True))

    def test_unchanged_selection_neither_writes_nor_syncs(self):
        for _ in range(3):
            self.select(1)
        self.settings.setValue.assert_not_called()
        self.settings.sync.assert_not_called()
        self.state.viewedCommanderChanged.emit.assert_not_called()
        self.assertEqual(self.persisted(), [1, 'A', True, 'steam'])

    def test_commander_source_and_follow_changes_persist(self):
        self.manager.preferred_source = 'heroic'
        self.state.follow_live_commander = False
        self.select(2)
        self.assertEqual(self.settings.setValue.call_count, 4)
        self.settings.sync.assert_called_once_with()
        self.state.viewedCommanderChanged.emit.assert_called_once_with(2)
        self.assertEqual(self.persisted(), [2, 'B', False, 'heroic'])

    def test_source_and_follow_change_without_commander_change(self):
        for source, follow in [('heroic', True), ('heroic', False), ('steam', True)]:
            self.manager.preferred_source = source
            self.state.follow_live_commander = follow
            self.select(1)
            self.assertEqual(self.persisted(), [1, 'A', follow, source])
        self.state.viewedCommanderChanged.emit.assert_not_called()
        self.assertEqual(self.settings.sync.call_count, 3)

    def test_current_settings_changes_are_not_hidden_by_cached_selection(self):
        other = QSettings(self.path, QSettings.IniFormat)
        other.setValue('commander_view/source_id', 'external')
        self.select(1)
        self.settings.setValue.assert_called_once_with('commander_view/source_id', 'steam')
        self.settings.sync.assert_called_once_with()
        self.assertEqual(self.persisted(), [1, 'A', True, 'steam'])

    def test_reloaded_ini_strings_do_not_cause_rewrite(self):
        # Write externally, then read in a genuinely new process.
        script = """import sys
from types import SimpleNamespace as NS
from unittest.mock import Mock
from PySide6.QtCore import QSettings
from cmdrhelper.source_manager import SourceManager
from cmdrhelper.game_instances import ProcessObservation
s=Mock(wraps=QSettings(sys.argv[1],QSettings.IniFormat))
state=NS(settings=s,viewed_commander_id=1,follow_live_commander=True,
 database=NS(list_commanders=lambda:[{'id':1,'fid':'A'}]),viewedCommanderChanged=Mock())
SourceManager._select(NS(state=state,preferred_source='steam',_process_observation=ProcessObservation()),1)
assert s.setValue.call_count == s.sync.call_count == 0
"""
        subprocess.run([sys.executable, '-B', '-c', script, self.path], check=True)

    def test_missing_key_and_previous_sync_error_are_not_skipped(self):
        self.raw.remove('commander_view/follow_live')
        self.select(1)
        self.settings.setValue.assert_called_once_with('commander_view/follow_live', True)
        self.settings.reset_mock()
        self.settings.status.return_value = QSettings.AccessError
        self.select(1)
        self.settings.setValue.assert_not_called()
        self.settings.sync.assert_called_once_with()
