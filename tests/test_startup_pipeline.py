"""Startup orchestration with real Qt delivery and isolated worker IO."""
import os
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Qt, QTimer
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtTest import QTest

from cmdrhelper.state import AppState
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.startup_progress import StartupProgressDialog


class StartupPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def wait_for(self, condition):
        deadline = time.monotonic() + 3
        while not condition() and time.monotonic() < deadline:
            QTest.qWait(10)
        self.assertTrue(condition())

    def state(self):
        state = AppState.__new__(AppState)
        QObject.__init__(state)
        state.journal_folder = Path('/isolated-journals')
        state.database = Mock()
        state.database.commander_state_repair_needed.side_effect = (
            lambda cid, feature: feature in ('unsold', 'missions', 'position_gap')
        )
        state._prepare_indexed_live_state = Mock(return_value=None)
        state._repair_latest_position_gap = Mock()
        state.refresh = Mock(return_value=True)
        state.watcher = Mock()
        state._database_import_running = False
        state._initialization_visible = True
        state._run_journal_learning = Mock()
        state.journalIndexReady.connect(state._finish_initial_journal_index, Qt.QueuedConnection)
        return state

    def test_one_dialog_reused_for_index_and_history_and_closed(self):
        host = QWidget()
        host.ui_theme = 'dark'
        host._startup_progress_dialog = None
        try:
            MainWindow._initialization_started(host, True, 3881)
            dialog = host._startup_progress_dialog
            dialog.set_progress(3881, 3881, 'startup.phase.index')
            self.assertEqual(dialog.progress.value(), 100)
            MainWindow._initialization_started(host, True, 0)
            self.assertIs(dialog, host._startup_progress_dialog)
            self.assertEqual(len(host.findChildren(StartupProgressDialog)), 1)
            self.assertEqual(dialog.progress.maximum(), 0)
            dialog.set_progress(0, 0, 'startup.phase.history')
            MainWindow._initialization_started(host, True, 42)
            self.assertIs(dialog, host._startup_progress_dialog)
            MainWindow._initialization_finished(host, '')
            self.assertFalse(dialog.isVisible())
        finally:
            host.close()

    def run_pipeline(self, repair_error=False, adoption_error=False):
        state = self.state()
        entered, release = threading.Event(), threading.Event()
        repair_threads, adopt_threads, finished, progress = [], [], [], []
        position_threads = []

        def read_position(session):
            position_threads.append(threading.get_ident())
            return True, {"event": "Location", "StarSystem": "Test"}

        state._read_latest_position_event = Mock(side_effect=read_position)
        sessions = [dict(commander_id=7, fid_seen='F7', attribution_status='identified',
                         journal_file='/isolated-journals/Journal.log', last_read_offset=1)]

        def repair(*args, **kwargs):
            repair_threads.append(threading.get_ident())
            entered.set()
            if not release.wait(3):
                raise RuntimeError('test release timeout')
            if repair_error:
                raise RuntimeError('Historie defekt')

        def adopt(**kwargs):
            adopt_threads.append(threading.get_ident())
            if adoption_error:
                raise RuntimeError('Übernahme defekt')

        def scan(*args, **kwargs):
            kwargs['progress_callback'](3881, 3881, 'Journal.log')
            return sessions

        def archive(*args, **kwargs):
            kwargs['progress_callback'](1, 1, 'Schreibe Datenbank …')
            return dict(imported_journals=1, skipped_journals=0)

        state.database.repair_commander_state.side_effect = repair
        state.database.import_journal_archive.side_effect = archive
        state._prepare_indexed_live_state.side_effect = adopt
        state.initializationFinished.connect(finished.append)
        state.initializationProgress.connect(lambda *args: progress.append(args))
        timer_ticks = []
        timer = QTimer()
        timer.setInterval(5)
        timer.timeout.connect(lambda: timer_ticks.append(True))
        with patch('cmdrhelper.journal_index.journal_index_plan', return_value=(3881, 3881)), \
             patch('cmdrhelper.journal_index.scan_journal_folder', side_effect=scan), \
             patch('cmdrhelper.startup_repairs.run_startup_repairs'):
            timer.start()
            try:
                state._start_initial_journal_index()
                self.wait_for(entered.is_set)
                self.wait_for(lambda: len(timer_ticks) >= 3)
                self.assertEqual(adopt_threads, [])
                self.assertFalse(state.database.import_journal_archive.called)
                # Manual import must not race the historical startup repair.
                state.import_journal_archive(automatic=False)
                self.assertFalse(state.database.import_journal_archive.called)
                release.set()
                self.wait_for(lambda: bool(finished))
                self.wait_for(lambda: not state._database_import_running)
            finally:
                release.set()
                timer.stop()
        self.assertNotEqual(repair_threads, [threading.get_ident()])
        self.assertEqual(adopt_threads, [threading.get_ident()])
        self.assertEqual(position_threads, repair_threads)
        self.assertEqual(state._journal_index_sessions, sessions)
        self.assertEqual(len(finished), 1)
        index = next(i for i, p in enumerate(progress) if p[:2] == (3881, 3881))
        self.assertEqual(progress[index + 1][:3], (0, 0, 'startup.phase.history'))
        if adoption_error:
            self.assertIn('Übernahme defekt', finished[0])
            state.database.import_journal_archive.assert_not_called()
        else:
            self.assertEqual(finished, ['Historie defekt' if repair_error else ''])
            state._repair_latest_position_gap.assert_called_once_with(
                None, prepared=(True, {'event': 'Location', 'StarSystem': 'Test'}))
            state.database.import_journal_archive.assert_called_once()
            state._run_journal_learning.assert_called_once()
            self.assertEqual(progress[-1][:2], (0, 0))
        state.database.repair_commander_state.assert_called_once_with(
            state.journal_folder, sessions, 7, features=['unsold', 'missions'])
        state.watcher.start.assert_called_once()

    def test_history_runs_off_gui_then_adopts_and_imports(self):
        self.run_pipeline()

    def test_repair_error_is_reported_after_archive_without_stranding_start(self):
        self.run_pipeline(repair_error=True)

    def test_adoption_error_finishes_and_starts_watcher(self):
        self.run_pipeline(adoption_error=True)

    def test_archive_failure_unlocks_dialog(self):
        state = self.state()
        state.database.import_journal_archive.side_effect = RuntimeError('Archiv defekt')
        dialog = StartupProgressDialog()
        dialog.begin()
        state.initializationFinished.connect(dialog.finish)
        state.import_journal_archive(automatic=True)
        self.wait_for(dialog.close_button.isVisible)
        self.assertFalse(dialog.ships.running)
        self.assertIn('Archiv defekt', dialog.count_label.text())
        dialog.close_button.click()
        self.assertFalse(dialog.isVisible())
        self.wait_for(lambda: not state._database_import_running)


if __name__ == '__main__':
    unittest.main()
