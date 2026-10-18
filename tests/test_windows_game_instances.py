"""Synthetic Windows API evidence; no native Windows or live files required."""
import ctypes as c
from types import SimpleNamespace
from unittest.mock import Mock, patch
import unittest

from cmdrhelper import game_instances as game
import test_game_instances as base


class WindowsEvidenceTests(unittest.TestCase):
    runtime = base.InstanceTests.runtime

    def setUp(self):
        self.api = Mock()
        self.instance = game.GameInstance(71, 100, windows_started=116444737000000000)
        self.api.instances.return_value = [self.instance]
        self.api.file_users.return_value = {(71, self.instance.windows_started)}
        p = patch.object(game, '_WindowsProcesses', return_value=self.api)
        p.start(); self.addCleanup(p.stop)
        p = patch.object(game, 'os', SimpleNamespace(name='nt'))
        p.start(); self.addCleanup(p.stop)

    def test_inspection_and_direct_source_fid_match(self):
        snapshot = game.inspect_instances()
        rt = self.runtime('windows', 'MEDORA')
        self.assertEqual(game.confirmed_selection(snapshot, [rt]), ('windows', 2, 'MEDORA'))
        self.api.file_users.assert_called_once_with(game.canonical(rt.processor.sessions[-1]['journal_file']))

    def test_no_game_multiple_processes_and_enumeration_failure(self):
        rt = self.runtime('windows', 'MEDORA')
        for instances in ([], [self.instance, self.instance]):
            self.api.instances.return_value = instances
            self.assertIsNone(game.confirmed_selection(game.inspect_instances(), [rt]))
        self.api.file_users.assert_not_called()
        self.api.instances.side_effect = OSError('denied')
        self.assertFalse(game.inspect_instances().available)

    def test_name_only_old_session_pid_reuse_and_failed_resource_query_do_not_select(self):
        rt = self.runtime('windows', 'MEDORA')
        snapshot = game.inspect_instances()
        for users in (set(), {(99, self.instance.windows_started)}, {(71, self.instance.windows_started - 1)}):
            self.api.file_users.return_value = users
            self.assertIsNone(game.confirmed_selection(snapshot, [rt]))
        self.api.file_users.side_effect = OSError('cannot query')
        self.assertIsNone(game.confirmed_selection(snapshot, [rt]))

    def test_unknown_conflicting_disabled_or_multiple_matching_sources(self):
        snapshot = game.inspect_instances()
        for status in ('unknown', 'ambiguous'):
            self.assertIsNone(game.confirmed_selection(snapshot, [self.runtime('windows', None, status)]))
        rt = self.runtime('windows', 'MEDORA'); rt.source.enabled = False
        self.assertIsNone(game.confirmed_selection(snapshot, [rt]))
        self.api.file_users.assert_not_called()
        rt.source.enabled = True
        self.assertIsNone(game.confirmed_selection(snapshot, [rt, self.runtime('other', 'OTHER')]))

    def test_only_latest_session_is_used_not_historical_fid(self):
        rt = self.runtime('windows', 'MEDORA')
        old = dict(rt.processor.sessions[0], fid_seen='NANJAN', journal_file='/old/Journal.old.log')
        rt.processor.sessions.insert(0, old)
        self.assertEqual(game.confirmed_selection(game.inspect_instances(), [rt])[2], 'MEDORA')
        self.assertNotIn('/old/Journal.old.log', str(self.api.file_users.call_args_list))

    def test_stale_snapshot_rechecks_count_exit_and_process_identity(self):
        snapshot = game.inspect_instances()
        rt = self.runtime('windows', 'MEDORA')
        other = game.GameInstance(72, 100, windows_started=999)
        recycled = game.GameInstance(71, 100, windows_started=999)
        for current in ([], [self.instance, other], [other], [recycled]):
            self.api.instances.return_value = current
            self.assertIsNone(game.confirmed_selection(snapshot, [rt]))
        self.api.instances.side_effect = OSError('process list unavailable')
        self.assertIsNone(game.confirmed_selection(snapshot, [rt]))

    def test_second_process_starts_during_journal_resource_lookup(self):
        snapshot = game.inspect_instances()
        def resource_lookup(path):
            self.api.instances.return_value = [self.instance, game.GameInstance(72, 100, windows_started=999)]
            return {(self.instance.pid, self.instance.windows_started)}
        self.api.file_users.side_effect = resource_lookup
        self.assertIsNone(game.confirmed_selection(snapshot, [self.runtime('windows', 'MEDORA')]))


class NativeBindingTests(unittest.TestCase):
    def setUp(self):
        self.kernel, self.rm = Mock(), Mock()
        loader = patch.object(c, 'WinDLL', create=True, side_effect=[self.kernel, self.rm])
        loader.start(); self.addCleanup(loader.stop)
        self.api = game._WindowsProcesses()
        self.kernel.CreateToolhelp32Snapshot.return_value = 90
        self.kernel.OpenProcess.return_value = 91
        self.kernel.GetExitCodeProcess.side_effect = lambda handle, status: self.assign(status, 259)
        self.kernel.GetProcessTimes.side_effect = self.times
        self.rm.RmStartSession.return_value = 0
        self.rm.RmRegisterResources.return_value = 0
        self.rm.RmEndSession.return_value = 0

    @staticmethod
    def assign(pointer, value):
        pointer._obj.value = value
        return 1

    def times(self, handle, created, *others):
        created._obj.low, created._obj.high = 123, 456
        return 1

    def enumerate(self, names, error=18):
        remaining = iter(names)
        def next_entry(handle, pointer):
            name = next(remaining, None)
            if name is None: return 0
            pointer._obj.exe, pointer._obj.pid = name, 71
            return 1
        self.kernel.Process32FirstW.side_effect = next_entry
        self.kernel.Process32NextW.side_effect = next_entry
        with patch.object(c, 'get_last_error', create=True, return_value=error):
            return self.api.instances()

    def test_toolhelp_names_times_and_handle_cleanup(self):
        rows = self.enumerate(['EDLaunch.exe', 'EliteDangerous64.exe', 'EliteDangerous.exe'])
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row.windows_started == 123 + (456 << 32) for row in rows))
        self.assertEqual(self.kernel.CloseHandle.call_count, 3)
        self.assertEqual(self.kernel.OpenProcess.call_args.args[0], 0x1000)
        self.assertEqual(self.enumerate([]), [])

    def test_enumeration_and_access_errors_are_not_no_game(self):
        with self.assertRaises(OSError): self.enumerate([], error=5)
        self.kernel.OpenProcess.return_value = None
        with self.assertRaises(OSError): self.enumerate(['EliteDangerous64.exe'])
        self.kernel.CloseHandle.assert_called_with(90)

    def test_restart_manager_resource_returns_pid_and_exact_creation_time(self):
        def get_list(session, needed, count, rows, reasons):
            if rows is None:
                needed._obj.value = 1
                return 234
            rows[0].process.pid = 71
            rows[0].process.started.low = 123
            rows[0].process.started.high = 456
            count._obj.value = 1
            return 0
        self.rm.RmGetList.side_effect = get_list
        self.assertEqual(self.api.file_users('C:\\Saved Games\\Journal.current.log'), {(71, 123 + (456 << 32))})
        args = self.rm.RmRegisterResources.call_args.args
        self.assertEqual(args[1], 1)
        self.assertEqual(args[2][0], 'C:\\Saved Games\\Journal.current.log')
        self.rm.RmEndSession.assert_called_once()
        self.rm.RmShutdown.assert_not_called()
        self.rm.RmRestart.assert_not_called()

    def test_restart_manager_empty_error_and_changing_list_close_session(self):
        for codes in ([0], [5], [234, 234]):
            self.rm.RmGetList.side_effect = codes
            self.rm.RmEndSession.reset_mock()
            if codes == [0]: self.assertEqual(self.api.file_users('synthetic'), set())
            else:
                with self.assertRaises(OSError): self.api.file_users('synthetic')
            self.rm.RmEndSession.assert_called_once()
