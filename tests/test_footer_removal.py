"""Footer-free startup, real source retries and privacy-safe diagnostic ZIPs.

All databases, journals, settings and logs are disposable synthetic fixtures.
CMDRHELPER_FOOTER_TEST_ARTIFACTS optionally retains the verified synthetic ZIP.
"""
from collections import Counter
import errno
import json
import logging
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from zipfile import ZipFile

from PySide6.QtCore import QEvent, QSettings
from PySide6.QtWidgets import QApplication, QMainWindow, QStatusBar
from cmdrhelper import startup_runtime as startup
from cmdrhelper.diagnostics import create_package
from cmdrhelper.global_hotkey import GlobalHotkey
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.journal_catchup import JournalConflict
from cmdrhelper.logging_config import PrivacyFormatter
from cmdrhelper.source_manager import SourceManager, SourceRuntime
from cmdrhelper.source_processing import SourceProcessor
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
import test_source_manager as source_fixture
import test_repair_failure_management as repair_fixture
import test_popup_ui_settings as popup_fixture


class FooterRemovalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.logger = logging.getLogger('cmdrhelper')
        previous = self.logger.handlers[:], self.logger.level, self.logger.propagate
        self.handler = logging.FileHandler(self.root / 'cmdrhelper.log', encoding='utf-8')
        self.handler.setFormatter(PrivacyFormatter(
            '%(asctime)s %(levelname)-8s [privacy-v1] %(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        self.logger.handlers = [self.handler]
        self.logger.setLevel(logging.INFO); self.logger.propagate = False
        def restore():
            self.handler.close()
            self.logger.handlers, level, self.logger.propagate = previous
            self.logger.setLevel(level)
        self.addCleanup(restore)
        language = get_language(); self.addCleanup(set_language, language); set_language('de')

    def log_text(self):
        self.handler.flush()
        return (self.root / 'cmdrhelper.log').read_text()

    def keep(self, window):
        def close():
            window.close(); window.deleteLater()
            self.app.sendPostedEvents(None, QEvent.DeferredDelete)
        self.addCleanup(close)
        return window

    def host(self, state):
        w = self.keep(QMainWindow())
        w.state, w.ui_theme = state, 'dark'
        w._startup_progress_dialog = None
        w._cleanup_parent_backup = Mock()
        w.resize(900, 650); w.show()
        return w

    def source_case(self, failures=None, repairs=None):
        f = source_fixture.ManagerTests(); f.app = self.app
        self.addCleanup(f.doCleanups)
        original_process = SourceProcessor.process
        attempts = Counter()
        def process(processor, **kwargs):
            name = processor.path.name
            attempts[name] += 1
            error = failures(name, attempts[name]) if failures else None
            if error is not None:
                raise error
            result = original_process(processor, **kwargs)
            if repairs:
                processor.repair_results = repairs
            return result
        p = patch.object(SourceProcessor, 'process', process); p.start(); self.addCleanup(p.stop)
        finished, hosts = [], []
        drain = f.drain
        def hooked_drain():
            if not hosts:
                host = self.host(f.state); hosts.append(host)
                f.state.initializationFinished.connect(finished.append)
                f.state.initializationStarted.connect(lambda *a: MainWindow._initialization_started(host, *a))
                f.state.initializationProgress.connect(lambda *a: MainWindow._initialization_progress(host, *a))
                f.state.initializationFinished.connect(lambda *a: MainWindow._initialization_finished(host, *a))
            drain()
        f.drain = hooked_drain
        f.setUp()
        self.app.processEvents()
        return f, hosts[0], finished, attempts

    def test_normal_start_no_footer_and_backup_success(self):
        f, w, finished, _ = self.source_case()
        self.assertEqual(finished, [''])
        self.assertEqual(f.state.startup_status, 'success')
        self.assertTrue(w._parent_backup_startup_succeeded)
        self.assertIsNone(w.findChild(QStatusBar))
        self.assertFalse(w._startup_progress_dialog.isVisible())
        self.assertFalse(w._startup_progress_dialog.ships.running)

    def test_pending_start_auto_retry_does_not_repeat_completion_or_show_error(self):
        f, w, finished, attempts = self.source_case(lambda name, n:
            startup.JournalPending('journal_changed_during_read') if name == 'Steam' and n == 1 else None)
        self.assertEqual(len(finished), 1)
        self.assertIn('journal_changed_during_read', finished[0])  # Technical state retained.
        self.assertEqual(f.state.startup_status, 'critical')
        self.assertFalse(f.state.sources.startup_requires_action)
        self.assertFalse(w._parent_backup_startup_succeeded)
        self.assertFalse(w._startup_progress_dialog.isVisible())
        self.assertFalse(w._startup_progress_dialog.ships.running)
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(.01)  # Let the Python source worker run as well as Qt.
            if attempts['Steam'] > 1 and all(rt.source.status == 'ready' for rt in f.state.sources.runtimes.values()):
                break
        self.assertGreater(attempts['Steam'], 1)
        self.assertTrue(all(rt.source.status == 'ready' for rt in f.state.sources.runtimes.values()),
                        (dict(attempts), [(rt.source.status, rt.last_failure_diagnostic)
                                         for rt in f.state.sources.runtimes.values()], self.log_text()))
        self.assertEqual(len(finished), 1)
        self.assertEqual(f.state.startup_status, 'critical')
        self.assertIsNone(w.findChild(QStatusBar))
        self.assertFalse(w._startup_progress_dialog.isVisible())
        self.assertEqual(sum('component=source' in line and 'journal_changed_during_read' in line
                             for line in self.log_text().splitlines()), 1)
        w._cleanup_parent_backup.assert_called_once()
        archive = create_package(self.root / 'retry.zip', database=f.db.path,
                                 journals=f.folders[0], folder=self.root)
        with ZipFile(archive) as z:
            self.assertIn('reason=journal_changed_during_read', z.read('cmdrhelper.log').decode())
        target = os.environ.get('CMDRHELPER_FOOTER_TEST_ARTIFACTS')
        if target:
            folder = Path(target); folder.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(archive, folder / 'retry-diagnostics.zip')

    def test_access_error_remains_visible_without_raw_payload(self):
        f, w, finished, _ = self.source_case(lambda name, n:
            PermissionError(errno.EACCES, 'PRIVATE-COMMANDER F123456 /secret/journal') if name == 'Steam' else None)
        self.assertTrue(f.state.sources.startup_requires_action)
        self.assertEqual(len(finished), 1)
        self.assertTrue(w._startup_progress_dialog.isVisible())
        self.assertTrue(w._startup_progress_dialog.close_button.isVisible())
        self.assertFalse(w._startup_progress_dialog.ships.running)
        self.assertFalse(w._parent_backup_startup_succeeded)
        text = w._startup_progress_dialog.count_label.text()
        self.assertIn(tr('startup.action_required'), text)
        self.assertNotIn('PermissionError', text)
        self.assertNotIn('PRIVATE', text)
        self.assertIsNone(w.findChild(QStatusBar))

    def test_later_fatal_source_is_not_masked_by_first_retryable_error(self):
        f, w, finished, _ = self.source_case(lambda name, n:
            startup.JournalPending('journal_changed_during_read') if name == 'Steam' else
            sqlite3.OperationalError('PRIVATE database unavailable'))
        self.assertIn('journal_changed_during_read', finished[0])
        self.assertTrue(f.state.sources.startup_requires_action)
        self.assertTrue(w._startup_progress_dialog.isVisible())
        self.assertEqual(len(finished), 1)

    def test_historical_partial_closes_progress_preserves_status_and_backup(self):
        results = [dict(feature='biology_findings', status='failed'),
                   dict(feature='stations', status='failed'),
                   dict(feature='unsold_cartography', status='incomplete')]
        f, w, finished, _ = self.source_case(repairs=results)
        self.assertEqual(finished, [''])
        self.assertEqual(f.state.startup_status, 'partial')
        self.assertEqual(f.state.startup_issues, ['history', 'unsold_cartography'])
        self.assertEqual(w._startup_progress_dialog.status, 'partial')
        self.assertFalse(w._startup_progress_dialog.isVisible())
        self.assertFalse(w._startup_progress_dialog.ships.running)
        self.assertFalse(w._parent_backup_startup_succeeded)
        self.assertIsNone(w.findChild(QStatusBar))
        lines = self.log_text().splitlines()
        self.assertEqual(sum('component=history' in l and 'status=partial' in l for l in lines), 1)
        self.assertEqual(sum('component=unsold_cartography' in l and 'status=partial' in l for l in lines), 1)

    def test_only_known_pending_exceptions_are_silent_and_logs_are_deduplicated(self):
        rt = SourceRuntime(SimpleNamespace(path='/PRIVATE/source'), None, None, 1)
        for error, retryable in (
            (startup.JournalPending('journal_changed_during_read'), True),
            (startup.JournalPending('partial_final_line'), True),
            (startup.JournalPending('catchup_budget'), True),
            (startup.JournalPending('journal_identity_changed'), True),
            (startup.JournalPending('journal_replaced_or_truncated'), False),
            (startup.JournalPending('journal_legacy_prefix_unverified'), False),
            (JournalConflict('PRIVATE prefix changed'), False),
            (ValueError('journal_changed_during_read'), False),
            (sqlite3.OperationalError('PRIVATE'), False)):
            before = self.log_text().count('component=source')
            for _ in range(10):
                SourceManager._record_failure(None, rt, error)
            self.assertEqual(rt.failure_retryable, retryable)
            self.assertEqual(self.log_text().count('component=source'), before + 1)

    def test_diagnostic_zip_contains_source_hotkey_and_real_repair_failure_without_payloads(self):
        rt = SourceRuntime(SimpleNamespace(path='/PRIVATE/source/F123456'), None, None, 1)
        SourceManager._record_failure(None, rt, startup.JournalPending('journal_changed_during_read'))
        SourceManager._record_failure(None, rt, PermissionError(errno.EACCES, 'PRIVATE-PAYLOAD /secret F123456'))
        settings = QSettings(str(self.root / 'settings.ini'), QSettings.IniFormat)
        backend = Mock(); backend.register.side_effect = RuntimeError('PRIVATE-HOTKEY /secret F123456')
        hotkey = GlobalHotkey(settings, backend_factory=lambda callback: backend)
        self.addCleanup(hotkey.close)
        for _ in range(10):
            self.assertFalse(hotkey.set_hotkey('Ctrl+F8'))
        self.assertEqual(self.log_text().count('reason=hotkey_registration_failed'), 1)
        self.assertTrue(hotkey.set_hotkey(''))
        self.assertFalse(hotkey.set_hotkey('Ctrl+F8'))
        self.assertEqual(self.log_text().count('reason=hotkey_registration_failed'), 2)
        repair = repair_fixture.RepairFailureManagementTests()
        self.addCleanup(repair.doCleanups); repair.setUp()
        repair.corrupt(b'{"PRIVATE-JOURNAL":broken}\n')
        self.assertTrue(all(row['status'] == 'failed' for row in repair.run_repairs()))
        self.handler.flush()
        archive = create_package(self.root / 'diagnostics.zip', database=repair.db.path,
                                 journals=repair.path.parent, folder=self.root)
        with ZipFile(archive) as z:
            log = z.read('cmdrhelper.log').decode()
            all_text = '\n'.join(z.read(n).decode() for n in z.namelist())
            for expected in ('reason=journal_changed_during_read', 'component=source', 'errno=13',
                             'PermissionError', 'reason=hotkey_registration_failed', 'component=hotkey',
                             'reason=repair_json_syntax', 'source_ref=', 'line_number=3'):
                self.assertIn(expected, log)
            for forbidden in ('PRIVATE', 'F123456', '/secret', str(repair.path), str(repair.db.path),
                              str(self.root), 'Ctrl+F8'):
                self.assertNotIn(forbidden, all_text)
            self.assertEqual(set(z.namelist()), {'cmdrhelper.log', 'system_info.json',
                             'diagnose_summary.txt', 'odyssey_display_diagnostics.json',
                             'exit_diagnostics.json'})
        target = os.environ.get('CMDRHELPER_FOOTER_TEST_ARTIFACTS')
        if target:
            folder = Path(target); folder.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(archive, folder / 'verified-diagnostics.zip')
            (folder / 'zip-check.json').write_text(json.dumps(dict(
                verified=True, platform=self.app.platformName(),
                source_reason=True, hotkey_reason=True, repair_reason=True,
                private_payloads=False, repeated_hotkey_failures_logged_once=True), indent=2))

    def test_mainwindow_hotkey_failure_themes_menus_geometry_without_statusbar(self):
        f = popup_fixture.PopupUiSettingsTests(); f.app = self.app
        self.addCleanup(f.doCleanups); f.setUp()
        f.settings.setValue('quick_favorite/hotkey', 'Ctrl+F8')
        with patch('cmdrhelper.global_hotkey.create_backend', side_effect=RuntimeError('PRIVATE')):
            # Replace the captured default factory without registering a real shortcut.
            original = GlobalHotkey.__init__
            def init(hotkey, settings, parent=None, **kw):
                original(hotkey, settings, parent, backend_factory=Mock(side_effect=RuntimeError('PRIVATE')))
            with patch.object(GlobalHotkey, '__init__', init):
                w = f.main()
        w.resize(1400, 1000); w.show()
        for _ in range(10):
            self.app.processEvents(); time.sleep(.01)
        geometry = w.geometry()
        for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            w.setStyleSheet(style)
            for page in (w.PAGE_OVERVIEW, w.PAGE_EXPLORER, w.PAGE_TRADE, w.PAGE_SETTINGS):
                w._show_page(page); self.app.processEvents()
                self.assertIsNone(w.findChild(QStatusBar))
                self.assertEqual(w.geometry(), geometry)
        self.assertTrue(w._quick_favorite_hotkey.error)
        self.assertIn('reason=hotkey_registration_failed', self.log_text())
        self.assertTrue(w._quick_favorite_hotkey.set_hotkey(''))
        self.assertIsNone(w.findChild(QStatusBar))

    def test_critical_without_progress_uses_safe_dialog_all_languages(self):
        state = SimpleNamespace(startup_issues=[], sources=None)
        w = self.host(state)
        for lang, table in _TRANSLATIONS.items():
            set_language(lang)
            self.assertTrue(table.get('startup.action_required'))
            with patch('cmdrhelper.ui.main_window.QMessageBox.warning') as warning:
                MainWindow._initialization_finished(w, 'PRIVATE raw journal_changed_during_read')
            self.assertEqual(warning.call_count, 1)
            self.assertIn(table['startup.action_required'], warning.call_args.args[2])
            self.assertNotIn('PRIVATE', warning.call_args.args[2])
            self.assertNotIn('journal_changed_during_read', warning.call_args.args[2])
            self.assertIsNone(w.findChild(QStatusBar))
