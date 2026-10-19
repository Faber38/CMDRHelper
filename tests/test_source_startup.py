"""Startup completion with synthetic sources, settings and databases only."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PySide6.QtCore import QSettings, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.game_instances import ProcessSnapshot
from cmdrhelper.journal_sources import SourceRegistry
from cmdrhelper.state import AppState
from cmdrhelper import startup_runtime
from test_import_catchup import append, event


class SourceStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def start_case(self, count=0, *, disabled=False, missing=False, saved=False,
                   disabled_ids=(), errors=(), slow=0, warm=False, window=False):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        database = CMDRDatabase(root/'test.db')
        settings = QSettings(str(root/'settings.ini'), QSettings.IniFormat)
        registry = SourceRegistry(settings, [])
        for index in range(count):
            folder = root/str(index)
            folder.mkdir()
            if not missing:
                append(folder/'Journal.2026-10-18T120000.01.log',
                       event('Commander', FID=f'TEST-{index}', Name=f'Pilot {index}'),
                       event('Location', StarSystem='Test', SystemAddress=index+1))
            source = registry.add(str(folder))
            if disabled or index in disabled_ids:
                registry.update(source.id, enabled=False)
            if missing:
                folder.rmdir()
        if saved:
            commander = database.upsert_commander('SAVED-FID', 'Saved Pilot')
            settings.setValue('commander_view/fid', 'SAVED-FID')
        for target, value in [
            ('cmdrhelper.state.CMDRDatabase', database),
            ('cmdrhelper.state.QSettings', settings),
            ('cmdrhelper.source_manager.discover', []),
            ('cmdrhelper.source_manager.inspect_instances', ProcessSnapshot(True)),
            ('cmdrhelper.state.AppState._request_startup_stations', None),
            ('cmdrhelper.source_transfers.transfer', {}),
            ('cmdrhelper.observed_market_observer.cache_path', root/'markets.json'),
        ]:
            mock = patch(target, return_value=value)
            mock.start()
            self.addCleanup(mock.stop)
        from cmdrhelper.source_processing import SourceProcessor
        if warm:
            for source in registry.enabled():
                SourceProcessor(database, source.path).process()
        original_process = SourceProcessor.process
        def process(processor, **kwargs):
            if slow:
                time.sleep(slow)
            if int(processor.path.name) in errors:
                raise OSError('synthetic initial import failure')
            return original_process(processor, **kwargs)
        mocked = patch.object(SourceProcessor, 'process', process)
        mocked.start(); self.addCleanup(mocked.stop)
        state = AppState()
        state.bounties._root = root/'bounties'
        state.combat_bonds._root = root/'combat'
        def close():
            state.sources.stop()
            startup_runtime.shutdown(state)
            self.app.processEvents()
        self.addCleanup(close)
        completed, started, progress, visible = [], [], [], []
        state.initializationFinished.connect(completed.append)
        state.initializationStarted.connect(lambda *args: started.append(args))
        state.initializationProgress.connect(lambda *args: progress.append(args))
        host = None
        if window:
            # Real UI slots and dialog, with only the unrelated window contents
            # omitted. Full MainWindow startup is also covered by the UI probe.
            from cmdrhelper.ui.main_window import MainWindow
            host = QMainWindow()
            host.state, host.ui_theme = state, 'dark'
            host._startup_progress_dialog = None
            host._cleanup_parent_backup = Mock()
            state.initializationStarted.connect(lambda *args: MainWindow._initialization_started(host, *args))
            state.initializationProgress.connect(lambda *args: MainWindow._initialization_progress(host, *args))
            state.initializationFinished.connect(lambda *args: MainWindow._initialization_finished(host, *args))
            host.show(); self.addCleanup(host.close)
            pulse = QTimer(host); pulse.setInterval(10)
            pulse.timeout.connect(lambda: visible.append(bool(host._startup_progress_dialog
                and host._startup_progress_dialog.isVisible())))
            pulse.start()
        began = time.monotonic()
        deadline = time.monotonic()+10
        while not getattr(state, "_startup_completed", False) and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(.01)
        self.assertTrue(state._startup_completed)
        expected_failure = bool((errors or missing) and registry.enabled())
        self.assertEqual(state.startup_status, 'critical' if expected_failure else 'success')
        self.assertEqual(len(completed), 1)
        self.assertEqual(bool(completed[0]), expected_failure)
        self.assertEqual(started, [(True, 0)] if registry.enabled() else [])
        self.assertTrue(all(current == total == 0 for current, total, _, _ in progress))
        self.assertFalse(state.sources.running)
        self.assertEqual(state.sources.queue, [])
        self.assertEqual(len(state.sources.runtimes), len(registry.enabled()))
        state.sources._next()
        self.assertEqual(len(completed), 1)  # Completion remains idempotent.
        self.assertEqual(len(started), bool(registry.enabled()))
        if window:
            pulse.stop()
            from cmdrhelper.ui.startup_progress import StartupProgressDialog
            dialogs = host.findChildren(StartupProgressDialog)
            self.assertEqual(len(dialogs), bool(registry.enabled()))
            if dialogs:
                self.assertFalse(dialogs[0].isVisible())
                self.assertFalse(dialogs[0].ships.running)
                self.assertEqual(dialogs[0].status, 'critical' if expected_failure else 'success')
            if expected_failure:
                self.assertTrue(host.statusBar().currentMessage())
            self.assertTrue(host.isEnabled())
            if slow:
                self.assertGreater(sum(visible), 10)
            if not expected_failure and registry.enabled():
                self.assertIn('startup.phase.index', [p[2] for p in progress])
                self.assertIn('startup.phase.history', [p[2] for p in progress])
            state._test_start_elapsed = time.monotonic()-began
        if errors:
            healthy = [s for s in registry.enabled() if int(Path(s.path).name) not in errors]
            self.assertEqual(len(database.list_commanders()), len(healthy))
            return state
        if saved:
            self.assertEqual(state.viewed_commander_id, commander)
            self.assertEqual(state.commander_fid, 'SAVED-FID')
        elif not count or disabled or missing:
            self.assertIsNone(state.viewed_commander_id)
            self.assertFalse(state.commander_fid)
        else:
            # Preserve first-use selection of the first confirmed commander.
            self.assertEqual(state.commander_fid, 'TEST-0')
            self.assertEqual(database.commander_summary(state.viewed_commander_id)['fid'], 'TEST-0')
        expected = 1 if saved else (0 if missing else len(registry.enabled()))
        self.assertEqual(len(database.list_commanders()), expected)
        return state

    def test_no_sources(self):
        self.start_case()

    def test_one_source(self):
        self.start_case(1)

    def test_multiple_sources(self):
        self.start_case(3)

    def test_disabled_sources(self):
        state = self.start_case(2, disabled=True)
        self.assertTrue(all(not s.enabled for s in state.sources.registry.sources))

    def test_unreachable_source(self):
        self.start_case(1, missing=True)

    def test_saved_selection_without_source(self):
        self.start_case(saved=True)

    def test_dialog_without_sources(self):
        self.start_case(window=True)

    def test_dialog_one_source_fast(self):
        self.start_case(1, window=True)

    def test_dialog_two_sources(self):
        self.start_case(2, window=True)

    def test_dialog_ignores_disabled_source(self):
        self.start_case(2, disabled_ids=(1,), window=True)

    def test_dialog_slow_start_stays_responsive(self):
        self.start_case(1, slow=2, window=True)

    def test_dialog_warm_index(self):
        self.start_case(1, warm=True, window=True)

    def test_failed_start_closes_dialog_and_keeps_error(self):
        self.start_case(1, errors=(0,), window=True)

    def test_one_failed_source_does_not_hide_failure_or_block_other_source(self):
        self.start_case(2, errors=(1,), window=True)

    def test_first_source_failure_does_not_stop_second_source(self):
        self.start_case(2, errors=(0,), window=True)

    def test_live_update_does_not_repeat_startup_signals(self):
        state = self.start_case(1, window=True)
        signals = []
        state.initializationStarted.connect(lambda *args: signals.append('started'))
        state.initializationProgress.connect(lambda *args: signals.append('progress'))
        state.initializationFinished.connect(lambda *args: signals.append('finished'))
        runtime = next(iter(state.sources.runtimes.values()))
        append(Path(runtime.processor.sessions[-1]['journal_file']),
               event('Location', StarSystem='Later', SystemAddress=99))
        state.sources.request(runtime.source.id)
        deadline = time.monotonic()+5
        while (state.sources.queue or state.sources.running) and time.monotonic() < deadline:
            self.app.processEvents(); time.sleep(.01)
        self.assertEqual(state.system, 'Later')
        self.assertEqual(signals, [])

    def test_progress_does_not_add_snapshot_replays(self):
        from cmdrhelper.journal_reader import read_latest_state
        with patch('cmdrhelper.journal_reader.read_latest_state', wraps=read_latest_state) as read:
            self.start_case(2, window=True)
            # A cold database also needs the existing full-history repair once
            # per commander. The regular snapshot is built only by each worker.
            self.assertEqual(sum(bool(call.kwargs.get('force_full_history'))
                                 for call in read.call_args_list), 2)
            self.assertEqual(sum(not call.kwargs.get('force_full_history')
                                 for call in read.call_args_list), 2)
