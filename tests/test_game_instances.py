from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import unittest
import tempfile
from unittest.mock import patch
from cmdrhelper.game_instances import GameInstance, ProcessSnapshot, confirmed_selection, inspect_instances


class InstanceTests(unittest.TestCase):
    def test_proc_reader_counts_game_not_wrapper_and_preserves_unknown(self):
        with tempfile.TemporaryDirectory() as folder:
            proc = Path(folder)
            (proc/'uptime').write_text('1000 1000')
            for pid, cmd in [('1', b'/game/EliteDangerous64.exe\0'),
                             ('2', b'python\0proton\0/game/EliteDangerous64.exe\0')]:
                entry = proc/pid; entry.mkdir()
                (entry/'cmdline').write_bytes(cmd)
                (entry/'stat').write_text(pid+' (game) '+' '.join(['S']+['0']*18+['100']))
                (entry/'environ').write_bytes(b'WINEPREFIX=/synthetic/prefix\0UNRELATED=not-exported\0')
                (entry/'fd').mkdir()
            result = inspect_instances(proc)
            self.assertTrue(result.available)
            self.assertEqual([p.pid for p in result.instances], [1])
            self.assertEqual(result.instances[0].prefixes, ('/synthetic/prefix',))
            original = Path.read_bytes
            def denied(path):
                if path == proc/'1/cmdline': raise PermissionError()
                return original(path)
            with patch.object(Path, 'read_bytes', denied):
                self.assertFalse(inspect_instances(proc).available)

    def runtime(self, name, fid, status='identified'):
        path = '/synthetic/'+name+'/drive_c/users/user/Saved Games/Frontier Developments/Elite Dangerous'
        row = dict(journal_file=path+'/Journal.test.log', attribution_status=status,
                   fid_seen=fid, commander_id=1 if name == 'steam' else 2,
                   first_event_at='2026-09-14T12:00:00Z')
        return SimpleNamespace(source=SimpleNamespace(id=name, path=path, status='ready', enabled=True),
                               processor=SimpleNamespace(sessions=[row]))

    def test_steam_and_heroic_each_alone(self):
        runtimes = [self.runtime('steam', 'FA'), self.runtime('heroic', 'FB')]
        for runtime in runtimes:
            instance = GameInstance(1, 0, journals=(runtime.processor.sessions[0]['journal_file'],))
            self.assertEqual(confirmed_selection(ProcessSnapshot(True, [instance]), runtimes)[0], runtime.source.id)

    def test_none_multiple_or_unavailable_never_select(self):
        runtime = self.runtime('steam', 'FA')
        instance = GameInstance(1, 0, journals=(runtime.processor.sessions[0]['journal_file'],))
        for snapshot in (ProcessSnapshot(True), ProcessSnapshot(False, [instance]),
                         ProcessSnapshot(True, [instance, instance])):
            self.assertIsNone(confirmed_selection(snapshot, [runtime]))

    def test_missing_conflicting_and_historical_identity_rejected(self):
        for status, fid in [('unknown', None), ('ambiguous', None)]:
            runtime = self.runtime('steam', fid, status)
            instance = GameInstance(1, 0, journals=(runtime.processor.sessions[0]['journal_file'],))
            self.assertIsNone(confirmed_selection(ProcessSnapshot(True, [instance]), [runtime]))
        runtime = self.runtime('steam', 'FA')
        instance = GameInstance(1, datetime.now(timezone.utc).timestamp(), prefixes=('/synthetic/steam',))
        self.assertIsNone(confirmed_selection(ProcessSnapshot(True, [instance]), [runtime]))
