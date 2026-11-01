"""Presentation batches never authorize actions or retain a selection."""
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from cmdrhelper import game_instances as game


class ProcessObservationTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.
        self.observation = game.ProcessObservation(clock=lambda: self.now)
        self.state = SimpleNamespace(sources=SimpleNamespace(_process_observation=self.observation))
        self.scan = Mock(return_value=game.ProcessSnapshot(True))

    def read(self):
        return game.presentation_instances(self.state, self.scan)

    def test_independent_queries_are_fresh_but_nested_subscribers_share_one_scan(self):
        self.read(); self.read()
        self.assertEqual(self.scan.call_count, 2)
        with self.observation.batch():
            for _ in range(4):
                with self.observation.batch():
                    self.read()
            self.assertEqual(self.scan.call_count, 3)
        self.read()
        self.assertEqual(self.scan.call_count, 4)
        self.assertIsNone(self.observation._snapshot)

    def test_start_exit_and_pid_reuse_are_visible_in_next_batch(self):
        running = game.GameInstance(7, 100)
        reused = game.GameInstance(7, 200)
        for instances in ([], [running], [], [reused], []):
            self.scan.return_value = game.ProcessSnapshot(True, instances)
            with self.observation.batch():
                self.assertEqual(self.read().instances, instances)
                self.assertEqual(self.read().instances, instances)
        self.assertEqual(self.scan.call_count, 5)

    def test_slow_or_reentrant_batch_expires_without_sliding_age(self):
        with self.observation.batch():
            self.read()
            self.now = .09
            self.read()
            self.assertEqual(self.scan.call_count, 1)
            self.now = .101
            self.scan.return_value = game.ProcessSnapshot(False)
            with self.observation.batch():
                self.assertFalse(self.read().available)
            self.assertEqual(self.scan.call_count, 2)

    def test_expired_refresh_failure_cannot_retain_positive_evidence(self):
        self.scan.return_value = game.ProcessSnapshot(True, [game.GameInstance(1, 0)])
        with self.observation.batch():
            self.read(); self.now = 1
            self.scan.side_effect = OSError('unavailable')
            with self.assertRaises(OSError):
                self.read()
            self.assertIsNone(self.observation._snapshot)
            self.scan.side_effect = None
            self.scan.return_value = game.ProcessSnapshot(False)
            self.assertFalse(self.read().available)
        self.assertIsNone(self.observation._snapshot)

    def test_exception_unwinds_and_returned_snapshot_cannot_mutate_batch(self):
        with self.assertRaises(ValueError):
            with self.observation.batch():
                first = self.read()
                first.instances.append(game.GameInstance(99, 0)); first.available = False
                self.assertEqual(self.read(), game.ProcessSnapshot(True))
                raise ValueError('subscriber failed')
        self.assertIsNone(self.observation._snapshot)
        self.read()
        self.assertEqual(self.scan.call_count, 2)

    def test_worker_does_not_reuse_gui_snapshot(self):
        with self.observation.batch():
            self.read()
            results = []
            def worker():
                with self.observation.batch():
                    results.append(self.read())
            thread = threading.Thread(target=worker); thread.start(); thread.join()
            self.assertEqual(results, [game.ProcessSnapshot(True)])
            self.read()
        self.assertEqual(self.scan.call_count, 2)

    def test_source_invalidation_discards_observation(self):
        with self.observation.batch():
            self.read(); self.observation.clear(); self.read()
        self.assertEqual(self.scan.call_count, 2)

    def test_selection_is_recomputed_for_source_and_commander_changes(self):
        path = '/synthetic/Journal.test.log'
        row = dict(journal_file=path, commander_id=1, fid_seen='A', attribution_status='identified')
        rt = SimpleNamespace(source=SimpleNamespace(id='direct', enabled=True, status='ready', path='/synthetic'),
                             processor=SimpleNamespace(sessions=[row]))
        self.scan.return_value = game.ProcessSnapshot(True, [game.GameInstance(9, 0, journals=(path,))])
        with self.observation.batch():
            self.assertEqual(game.confirmed_selection(self.read(), [rt]), ('direct', 1, 'A'))
            row.update(commander_id=2, fid_seen='B')
            self.assertEqual(game.confirmed_selection(self.read(), [rt]), ('direct', 2, 'B'))
            rt.source.enabled = False
            self.assertIsNone(game.confirmed_selection(self.read(), [rt]))
        self.assertEqual(self.scan.call_count, 1)

    @unittest.skipUnless(os.name == 'posix', 'Linux /proc or POSIX process guard')
    def test_raw_inspection_bypasses_stale_empty_presentation_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            proc = Path(directory); (proc/'uptime').write_text('1000 1000')
            with self.observation.batch():
                self.assertFalse(self.read().instances)
                entry = proc/'7'; entry.mkdir()
                (entry/'cmdline').write_bytes(b'/Frontier/EliteDangerous64.exe\0')
                (entry/'stat').write_text('7 (game) '+' '.join(['S']+['0']*18+['100']))
                (entry/'environ').write_bytes(b'')
                (entry/'fd').mkdir()
                self.assertEqual([p.pid for p in game.inspect_instances(proc).instances], [7])
                (entry/'cmdline').write_bytes(b'/usr/bin/sleep\0')
                self.assertEqual(game.inspect_instances(proc).instances, [])

    def test_migration_guard_ignores_empty_ui_observation_without_touching_database(self):
        from cmdrhelper import parent_migration as migration
        with self.observation.batch():
            self.read()
            # No migration is performed: rejection must precede every DB/file operation.
            with patch.object(migration, 'inventory') as inventory:
                current_check = Mock(return_value=True)
                with self.assertRaises(migration.MigrationError) as error:
                    migration.migrate('/not-opened.db', '/not-opened', process_check=current_check)
                self.assertEqual(error.exception.key, 'active')
                current_check.assert_called_once_with()
                inventory.assert_not_called()

    @unittest.skipUnless(os.name == 'posix', 'Linux /proc or POSIX process guard')
    def test_update_wait_does_not_use_empty_ui_observation_as_exit_permission(self):
        from cmdrhelper import update
        with self.observation.batch():
            self.read()
            with patch.object(update, '_pid_exists', return_value=True) as current:
                with self.assertRaises(RuntimeError):
                    update._wait_for_parent_exit(123, timeout=0)
                self.assertGreaterEqual(current.call_count, 1)


    @unittest.skipUnless(os.name == 'posix', 'Linux /proc or POSIX process guard')
    def test_steam_heroic_and_direct_frontier_with_real_synthetic_proc_reader(self):
        for installation, environment in (
                ('steam', b'STEAM_COMPAT_DATA_PATH=/synthetic/steam\0'),
                ('heroic', b'WINEPREFIX=/synthetic/heroic\0'),
                ('frontier', b'')):
            with self.subTest(installation=installation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); proc = root/'proc'; proc.mkdir()
                (proc/'uptime').write_text('1000 1000')
                journal = root/'Journal.test.log'; journal.write_text('')
                def process(pid):
                    entry = proc/str(pid); entry.mkdir()
                    (entry/'cmdline').write_bytes(b'/game/EliteDangerous64.exe\0')
                    (entry/'stat').write_text(str(pid)+' (game) '+' '.join(['S']+['0']*18+['100']))
                    (entry/'environ').write_bytes(environment)
                    (entry/'fd').mkdir(); (entry/'fd'/'3').symlink_to(journal)
                process(7)
                rt = SimpleNamespace(source=SimpleNamespace(id=installation, enabled=True,
                    status='ready', path=str(root)), processor=SimpleNamespace(sessions=[dict(
                    journal_file=str(journal), commander_id=1, fid_seen='A', attribution_status='identified')]))
                scan = Mock(side_effect=lambda: game.inspect_instances(proc))
                with self.observation.batch():
                    for _ in range(3):
                        result = self.observation.read(scan)
                        self.assertEqual(game.confirmed_selection(result, [rt]), (installation, 1, 'A'))
                    expected = () if installation == 'frontier' else (
                        '/synthetic/steam/pfx' if installation == 'steam' else '/synthetic/heroic',)
                    self.assertEqual(result.instances[0].prefixes, expected)
                self.assertEqual(scan.call_count, 1)
                process(8)
                with self.observation.batch():
                    self.assertIsNone(game.confirmed_selection(self.observation.read(scan), [rt]))
                original = Path.read_bytes
                def denied(path):
                    if path == proc/'7'/'cmdline':
                        raise PermissionError('synthetic unavailable process')
                    return original(path)
                with patch.object(Path, 'read_bytes', denied), self.observation.batch():
                    self.assertFalse(self.observation.read(scan).available)

    @unittest.skipUnless(os.name == 'posix', 'Linux /proc or POSIX process guard')
    def test_default_migration_process_guard_is_fresh_inside_presentation_batch(self):
        from cmdrhelper import parent_migration as migration
        with tempfile.TemporaryDirectory() as directory:
            proc = Path(directory); entry = proc/'7'; entry.mkdir()
            (entry/'cmdline').write_bytes(b'/game/EliteDangerous64.exe\0')
            def path(value):
                return proc if value == '/proc' else Path(value)
            with self.observation.batch(), patch.object(migration, 'Path', path), \
                 patch.object(migration, 'inventory') as inventory:
                self.assertFalse(self.read().instances)
                self.assertTrue(migration.elite_running())
                with self.assertRaises(migration.MigrationError) as error:
                    migration.migrate('/not-opened.db', '/not-opened')
                self.assertEqual(error.exception.key, 'active')
                inventory.assert_not_called()

    @unittest.skipUnless(os.name == 'posix', 'Linux /proc or POSIX process guard')
    def test_update_access_denied_is_not_exit_even_with_cached_no_game(self):
        from cmdrhelper import update
        with self.observation.batch(), patch.object(update.os, 'kill', side_effect=PermissionError):
            self.read()
            self.assertTrue(update._pid_exists(123))


class SourceBatchIntegrationTests(unittest.TestCase):
    """Real source signals: reuse ends before the next independent GUI action."""
    @classmethod
    def setUpClass(cls):
        from test_source_manager import ManagerTests
        ManagerTests.setUpClass()

    def test_publication_shares_evidence_but_reselection_and_reconcile_invalidate(self):
        from test_source_manager import ManagerTests
        from cmdrhelper.screenshot_sources import live_context
        from cmdrhelper.mission_arrival import ArrivalSource
        fixture = ManagerTests(); fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        state = fixture.state; manager = state.sources
        runtime = next(iter(manager.runtimes.values()))
        cid = runtime.processor.sessions[-1]['commander_id']
        state.select_viewed_commander(cid)
        scan = Mock(return_value=game.ProcessSnapshot(True))
        with patch('cmdrhelper.mission_arrival.inspect_instances', scan), \
             patch('cmdrhelper.screenshot_sources.inspect_instances', scan):
            arrival = ArrivalSource()
            # Subscribers intentionally query the same evidence repeatedly.
            def subscriber():
                arrival.snapshot(state); live_context(state)
            state.changed.connect(subscriber)
            try:
                manager._publish_local(runtime.source.id, runtime.generation,
                                       runtime.processor.sessions, '')
                self.assertEqual(scan.call_count, 1)
                self.assertIsNone(manager._process_observation._snapshot)
                subscriber()
                self.assertEqual(scan.call_count, 3)
                with manager._process_observation.batch():
                    live_context(state)
                    manager._select(cid)
                    live_context(state)
                    self.assertEqual(scan.call_count, 5)
                    manager.reconcile()
                    live_context(state)
                    self.assertEqual(scan.call_count, 6)
            finally:
                state.changed.disconnect(subscriber)


if __name__ == '__main__':
    unittest.main()
