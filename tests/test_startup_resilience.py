"""Synthetic startup regressions; never instantiate the production AppState."""
import io
import json
import logging
import os
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Qt
from PySide6.QtTest import QTest
from cmdrhelper import startup_runtime as runtime
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.state import AppState
from cmdrhelper.journal_index import scan_journal_folder
from cmdrhelper.startup_repairs import run_startup_repairs
from cmdrhelper.unsold_cartography import plan_cartography_repair
from cmdrhelper.backfill_support import IncompleteRepair
from cmdrhelper.ui.startup_progress import StartupProgressDialog
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.logging_config import PrivacyFormatter


class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def state(self):
        state = AppState.__new__(AppState)
        QObject.__init__(state)
        state.database = Mock()
        state.journal_folder = Path('/synthetic-not-read')
        state.watcher = Mock()
        state._database_import_running = False
        state._repair_indexed_commander_state = Mock()
        return state

    def wait(self, condition):
        for _ in range(300):
            if condition():
                return
            QTest.qWait(10)
        self.fail('worker did not finish')

    def test_thread_start_failure_finishes_critical(self):
        state = self.state()
        completed = []
        state.initializationFinished.connect(completed.append)
        with patch('cmdrhelper.startup_runtime.threading.Thread.start', side_effect=RuntimeError('injected')):
            state._start_initial_journal_index()
        self.assertFalse(state._initial_journal_index_running)
        self.assertEqual(state.startup_status, 'critical')
        self.assertEqual(completed, ['injected'])

    def test_index_failure_retained_sessions_are_delivered(self):
        state = self.state()
        cursor = state.database._connect.return_value.execute.return_value
        cursor.description = [('journal_file',)]
        cursor.fetchall.return_value = [('synthetic',)]
        ready = []
        state.journalIndexReady.connect(ready.append)
        with patch('cmdrhelper.journal_index.journal_index_plan', side_effect=OSError('injected')), \
             patch('cmdrhelper.startup_repairs.run_startup_repairs', return_value=[]):
            state._start_initial_journal_index()
            self.wait(lambda: bool(ready))
        self.assertEqual(ready, [[{'journal_file': 'synthetic'}]])
        self.assertIn('journal_index', state.startup_issues)
        state.database._connect.return_value.close.assert_called_once()

    def test_index_and_fallback_failure_finish(self):
        state = self.state()
        state.database._connect.side_effect = OSError('fallback')
        completed = []
        state.initializationFinished.connect(completed.append)
        with patch('cmdrhelper.journal_index.journal_index_plan', side_effect=OSError('index')), \
             patch('cmdrhelper.startup_repairs.run_startup_repairs', return_value=[]):
            state._start_initial_journal_index()
            self.wait(lambda: bool(completed))
        self.assertEqual(completed, ['fallback'])
        self.assertFalse(state._initial_journal_index_running)
        self.assertEqual(state.startup_status, 'critical')

    def test_shutdown_during_index_suppresses_delivery(self):
        state = self.state()
        entered = threading.Event()
        def scan(*args, **kwargs):
            entered.set()
            kwargs['cancel'].wait(2)
            runtime.check(state)
        ready = []
        state.journalIndexReady.connect(ready.append)
        with patch('cmdrhelper.journal_index.journal_index_plan', return_value=(1,1)), \
             patch('cmdrhelper.journal_index.scan_journal_folder', side_effect=scan):
            state._start_initial_journal_index()
            self.assertTrue(entered.wait(1))
            self.assertTrue(runtime.shutdown(state, timeout=2))
        QTest.qWait(20)
        self.assertFalse(state._initial_journal_index_running)
        self.assertEqual(ready, [])
        state._repair_indexed_commander_state.assert_not_called()

    def test_unavailable_qt_signal_is_not_retried_as_index_failure(self):
        state = SimpleNamespace(journalIndexReady=Mock())
        state.journalIndexReady.emit.side_effect = RuntimeError('deleted object')
        self.assertFalse(runtime.emit(state, 'journalIndexReady', []))
        self.assertEqual(state.startup_status, 'critical')

    def test_real_deleted_qt_source_is_contained(self):
        import shiboken6
        state = self.state()
        shiboken6.delete(state)
        self.assertFalse(runtime.emit(state, 'journalIndexReady', []))
        self.assertEqual(state.startup_status, 'critical')

    def test_partial_completion_is_once_and_keeps_components(self):
        state = self.state()
        completed = []
        state.initializationFinished.connect(completed.append)
        runtime.issue(state, 'station_pads', OSError('private'))
        runtime.complete(state)
        runtime.complete(state)
        self.assertEqual(completed, [''])
        self.assertEqual(state.startup_status, 'partial')
        self.assertEqual(state.startup_issues, ['station_pads'])

    def test_update_does_not_launch_installer_before_worker_exit(self):
        host = SimpleNamespace(state=self.state(), _update_download_failed=Mock(),
                               _finish_update_download_ui=Mock())
        with patch('cmdrhelper.startup_runtime.shutdown', return_value=False), \
             patch('cmdrhelper.ui.main_window.QTimer.singleShot') as timer, \
             patch('cmdrhelper.ui.main_window.launch_installer') as launch:
            MainWindow._launch_prepared_update(host, Path('/synthetic.zip'), '3.9.5')
        launch.assert_not_called()
        timer.assert_called_once()

    def test_update_wait_is_bounded(self):
        host = SimpleNamespace(state=self.state(), _update_download_failed=Mock(),
                               _resume_after_update_failure=Mock(), _update_shutdown_polls=299)
        with patch('cmdrhelper.startup_runtime.shutdown', return_value=False), \
             patch('cmdrhelper.ui.main_window.QTimer.singleShot') as timer, \
             patch('cmdrhelper.ui.main_window.launch_installer') as launch:
            MainWindow._launch_prepared_update(host, Path('/synthetic.zip'), '3.9.5')
        launch.assert_not_called()
        host._update_download_failed.assert_called_once()
        self.assertEqual(timer.call_args.args, (1000, host._resume_after_update_failure))

    def test_invisible_index_still_reports_partial_completion(self):
        from PySide6.QtWidgets import QWidget
        host = QWidget()
        host.state = SimpleNamespace(startup_issues=['station_pads'])
        host.ui_theme = 'light'
        host._startup_progress_dialog = None
        host._cleanup_parent_backup = Mock()
        try:
            MainWindow._initialization_finished(host, '')
            self.assertEqual(host._startup_progress_dialog.status, 'partial')
            self.assertFalse(host._startup_progress_dialog.ships.running)
            self.assertFalse(host._parent_backup_startup_succeeded)
        finally:
            host.close()

    def test_dialog_four_states_all_languages_and_themes(self):
        from cmdrhelper.i18n import _TRANSLATIONS, set_language
        from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
        previous_style = self.app.styleSheet()
        try:
            for language, table in _TRANSLATIONS.items():
                with self.subTest(language=language):
                    self.assertIn('startup.partial', table)
                    set_language(language)
                    for light in (False, True):
                        self.app.setStyleSheet(LIGHT_STYLESHEET if light else DARK_STYLESHEET)
                        dialog = StartupProgressDialog(light=light)
                        dialog.begin(2)
                        self.assertEqual(dialog.status, 'running')
                        dialog.finish('', ['Pads'])
                        self.assertEqual(dialog.status, 'partial')
                        self.assertFalse(dialog.ships.running)
                        self.assertEqual(dialog.progress.value(), 100)
                        self.assertIn('Pads', dialog.count_label.text())
                        self.assertFalse(dialog.isModal())
                        self.assertTrue(dialog.close_button.isVisible())
                        dialog.set_progress(0, 0, 'startup.phase.history')
                        self.assertEqual(dialog.progress.maximum(), 100)
                        dialog.begin(2)
                        dialog.finish('critical')
                        self.assertEqual(dialog.status, 'critical')
                        dialog.begin(2)
                        dialog.finish()
                        self.assertEqual(dialog.status, 'success')
                        self.assertFalse(dialog.isVisible())
        finally:
            self.app.setStyleSheet(previous_style)
            set_language('de')


class CartographyTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.db = CMDRDatabase(self.root/'test.db')
        self.path = self.root/'Journal.2026-10-13T000000.01.log'
        self.events = [dict(event='LoadGame', FID='F-test', Commander='Synthetic'),
                       dict(event='Location', SystemAddress=1, StarSystem='Synthetic'),
                       dict(event='SAAScanComplete', SystemAddress=1, BodyID=2, ProbesUsed=2, EfficiencyTarget=4)]
        self.scan = dict(event='Scan', SystemAddress=1, BodyID=2, BodyName='Synthetic 2',
                         PlanetClass='Rocky body', MassEM=1, WasDiscovered=True, WasMapped=False)

    def store(self):
        self.path.write_text(''.join(json.dumps(dict(e, timestamp=f'2026-10-13T00:00:{i:02}Z'))+'\n'
                                    for i,e in enumerate(self.events)))
        self.cid = scan_journal_folder(self.db, self.root)[0]['commander_id']
        with self.db._connect() as con:
            con.execute('UPDATE journal_sessions SET last_read_offset=?,last_complete_line_offset=?',
                        (self.path.stat().st_size, self.path.stat().st_size))

    def plan(self):
        with self.db._connect() as con:
            return plan_cartography_repair(con, self.cid)

    def test_later_scan_resolves_mapping_and_keeps_probe_evidence(self):
        self.events.append(self.scan)
        self.store()
        claim = self.plan()['claims'][0]
        self.assertTrue(claim['self_mapped'])
        self.assertTrue(claim['efficient_mapping'])
        self.assertEqual(claim['probes_used'], 2)
        self.assertEqual(claim['mapped_at'], '2026-10-13T00:00:02Z')
        self.assertEqual(claim['scanned_at'], '2026-10-13T00:00:03Z')

    def test_late_scan_after_system_change_keeps_mapping_system(self):
        self.events += [dict(event='Location', SystemAddress=99, StarSystem='Elsewhere'), self.scan]
        self.store()
        claim = self.plan()['claims'][0]
        self.assertEqual(claim['system_address'], 1)
        self.assertEqual(claim['system_name'], 'Synthetic')

    def test_sale_clears_pending_mapping(self):
        self.events += [dict(event='SellExplorationData'), self.scan]
        self.store()
        self.assertFalse(self.plan()['claims'][0]['self_mapped'])

    def test_nav_beacon_supplies_facts_without_creating_scan_claim(self):
        self.events.append(dict(self.scan, ScanType='NavBeaconDetail'))
        self.store()
        claim = self.plan()['claims'][0]
        self.assertTrue(claim['self_mapped'])
        self.assertEqual(claim['scanned_at'], '')

    def test_same_size_edit_with_unchanged_metadata_retries(self):
        self.store()
        run_startup_repairs(self.db.path)
        before = self.path.stat()
        original_stat = Path.stat
        self.path.write_text(self.path.read_text().replace('"BodyID": 2', '"BodyID": 3'))
        def stat(path, *args, **kwargs):
            return before if path == self.path else original_stat(path, *args, **kwargs)
        with patch.object(Path, 'stat', stat), \
             patch('cmdrhelper.unsold_cartography.plan_cartography_repair', wraps=plan_cartography_repair) as planner:
            result = run_startup_repairs(self.db.path)
        planner.assert_called_once()
        self.assertFalse(next(r for r in result if r['feature']=='unsold_cartography').get('retry_deferred', False))

    def test_incomplete_is_preserved_skipped_then_retried_on_source_change(self):
        self.store()
        with self.assertRaises(IncompleteRepair):
            self.plan()
        first = run_startup_repairs(self.db.path)
        cart = next(r for r in first if r['feature']=='unsold_cartography')
        self.assertEqual(cart['status'], 'incomplete')
        self.assertTrue(any(r['status']=='complete' for r in first if r['feature']!='unsold_cartography'))
        with patch('cmdrhelper.unsold_cartography.plan_cartography_repair', side_effect=AssertionError('must skip')):
            second = run_startup_repairs(self.db.path)
        self.assertTrue(next(r for r in second if r['feature']=='unsold_cartography')['retry_deferred'])
        self.events.append(self.scan)
        self.store()
        third = run_startup_repairs(self.db.path)
        self.assertEqual(next(r for r in third if r['feature']=='unsold_cartography')['status'], 'complete')
        with self.db._connect() as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], 23)


class DiagnosticTests(unittest.TestCase):
    def test_safe_reason_and_windows_code_without_payload(self):
        output = io.StringIO()
        handler = logging.StreamHandler(output)
        handler.setFormatter(PrivacyFormatter('%(message)s'))
        logger = runtime.logger
        old = logger.handlers[:], logger.propagate
        logger.handlers, logger.propagate = [handler], False
        try:
            exc = OSError(13, 'C:/Private/F999999/Journal.log secret')
            exc.winerror = 32
            runtime.diagnostic('station_pads', 'history', exc, reason='pad_signature_mismatch')
            runtime.diagnostic('F999999', 'Private', reason='secret')
        finally:
            logger.handlers, logger.propagate = old
        text = output.getvalue()
        self.assertIn('reason=pad_signature_mismatch', text)
        self.assertIn('winerror=32', text)
        self.assertIn('errno=13', text)
        for secret in ('Private', 'F999999', 'Journal.log', 'secret'):
            self.assertNotIn(secret, text)


class LiveReadTests(unittest.TestCase):
    def test_changed_batch_and_truncation_have_distinct_reasons(self):
        from cmdrhelper.live_journal import journal_batch, read_bytes
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'Journal.synthetic.log'
            path.write_bytes(b'{"event":"Noise"}\n')
            with journal_batch():
                read_bytes(path)
                with path.open('ab') as stream:
                    stream.write(b'{"event":"Noise"}\n')
                with self.assertRaises(runtime.JournalPending) as caught:
                    read_bytes(path)
                self.assertEqual(caught.exception.reason, 'journal_changed_during_read')
            with journal_batch():
                read_bytes(path)
                path.write_bytes(b'')
                with self.assertRaises(runtime.JournalPending) as caught:
                    read_bytes(path)
                self.assertEqual(caught.exception.reason, 'journal_replaced_or_truncated')
            with journal_batch():
                self.assertEqual(read_bytes(path), b'')

    def test_operating_system_error_keeps_error_code(self):
        from cmdrhelper.live_journal import read_bytes
        with patch.object(Path, 'stat', side_effect=PermissionError(13, 'synthetic')):
            with self.assertRaises(PermissionError) as caught:
                read_bytes(Path('/synthetic'))
        self.assertEqual(caught.exception.errno, 13)

    def test_material_warning_categories_do_not_change_calculation(self):
        from cmdrhelper.material_inventory import _Reducer
        reducer = _Reducer(1, 'synthetic')
        stamp = '2026-10-13T00:00:00Z'
        reducer.apply(dict(event='Materials', Raw=[dict(Name='iron', Count=1)],
                           Manufactured=[], Encoded=[], timestamp=stamp), 'snapshot')
        with patch('cmdrhelper.material_inventory.diagnostic') as diagnostic:
            reducer.apply(dict(event='MaterialDiscarded', Name='iron', Category='Raw', Count=2,
                               timestamp=stamp), 'underflow')
            self.assertFalse(reducer.result.material('iron').known)
            reducer.apply(dict(event='MaterialCollected', Name='iron', Category='Raw', Count=1,
                               timestamp=stamp), 'unknown')
            reducer.apply(dict(event='MaterialCollected', Name='iron', Category='Raw', Count=-1,
                               timestamp=stamp), 'invalid')
        self.assertEqual([call.kwargs['reason'] for call in diagnostic.call_args_list],
                         ['material_underflow', 'material_unknown', 'material_invalid_event'])
