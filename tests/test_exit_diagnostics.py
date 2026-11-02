"""Synthetic exit snapshots/ZIPs. No shutdown fixes or real network calls."""
import io
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from PySide6.QtCore import QThreadPool, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from cmdrhelper import diagnostics as d, exit_diagnostics as ed
from cmdrhelper.logging_config import PrivacyFormatter
from cmdrhelper.market_writer import MarketWriteWorker
from cmdrhelper.observed_market_observer import ObservedMarketObserver
from cmdrhelper.ui.diagnostics_panel import DiagnosticsPanel
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language
import test_safe_exit as safe_exit
from test_market_store import observation, commodity, NOW


class ExitDiagnosticsTests(unittest.TestCase):
    setUpClass = classmethod(safe_exit.SafeExitTests.setUpClass.__func__)
    wait = safe_exit.SafeExitTests.wait
    work = safe_exit.SafeExitTests.work

    def setUp(self):
        safe_exit.SafeExitTests.setUp(self)
        session = patch.object(d, '_last_successful_export_at', None)
        session.start()
        self.addCleanup(session.stop)

    def cleanup(self):
        QTest.qWait(30)  # Let the dialog's queued geometry callbacks finish.
        safe_exit.SafeExitTests.cleanup(self)

    def cancel(self):
        QTest.qWait(30)
        self.w._exit_controller.cancel()

    def export(self, label):
        path = self.root / (label + '.zip')
        d.create_package(path, folder=self.root, state=self.w.state,
                         exit_controller=getattr(self.w, '_exit_controller', None))
        with ZipFile(path) as archive:
            self.assertIsNone(archive.testzip())
            data = json.loads(archive.read('exit_diagnostics.json'))
            text = '\n'.join(archive.read(n).decode() for n in archive.namelist())
            for secret in ('F_PRIVATE_TEST', 'Private Commander', 'Bearer SECRET', str(self.root)):
                self.assertNotIn(secret, text)
        # Optional retained copies for the review report, all synthetic.
        evidence = os.environ.get('EXIT_DIAGNOSTICS_EVIDENCE')
        if evidence:
            Path(evidence, label + '.zip').write_bytes(path.read_bytes())
        return data

    def writer(self):
        writer = MarketWriteWorker(self.root/'legacy.json', self.root/'markets.db', clock=lambda: NOW)
        self.addCleanup(writer.close)
        observer = ObservedMarketObserver()
        observer.writer = writer
        self.w.state.observed_markets = observer
        return writer, observer

    def test_normal_exit_and_cancel(self):
        job, release = self.work()
        self.w.close()
        c = self.w._exit_controller
        self.assertEqual(self.export('running')['workers']['running'], 1)
        self.cancel()
        self.assertEqual(self.export('cancelled')['phase'], 'idle')
        release.set()
        self.wait(lambda: not self.gate.pending())
        self.assertTrue(self.w.close())
        self.assertEqual(self.export('finished')['phase'], 'finished')

    def test_completed_worker_result_pending(self):
        job, release = self.work()
        release.set()
        self.assertTrue(QThreadPool.globalInstance().waitForDone(2000))
        self.w.close()
        data = self.export('result-pending')
        self.assertEqual(data['workers']['running'], 0)
        self.assertEqual(data['workers']['result_pending'], 1)
        self.assertIn('result_pending', data['reasons'])
        self.wait(lambda: not self.w.isVisible())
        self.assertEqual(self.export('result-applied')['pending_count'], 0)

    def test_initialization_failed_queue_empty(self):
        (self.root/'legacy.json').write_text('{')
        writer, observer = self.writer()
        with self.assertRaises(Exception):
            writer.ready.result(timeout=3)
        self.w.close()
        data = self.export('initialization-failed')
        self.assertEqual(data['phase'], 'draining')
        self.assertEqual(data['market']['pending'], 0)
        self.assertEqual(data['market']['initialization_failed'], 1)
        self.assertIn('market_initialization_failed', data['reasons'])
        self.assertFalse(self.w._exit_controller.approved)  # Preflight has not polled yet.

    def test_conflicting_write_discard_remains_visible_after_exit(self):
        writer, observer = self.writer()
        writer.ready.result(timeout=3)
        writer.record(observation()).result(timeout=3)
        bad = observation(rows=[commodity(buy=999)])
        for _ in range(3):
            future = writer.record(bad)
            with self.assertRaises(Exception):
                future.result(timeout=3)
        observer._writes = [(bad, future)]
        self.w.close()
        c = self.w._exit_controller
        c.timer.stop()
        data = self.export('write-failed')
        self.assertEqual(data['market']['write_failed'], 1)
        self.assertEqual(data['market']['result_pending'], 1)
        self.assertIn('market_write_failed', data['reasons'])
        c.timer.start()
        self.wait(lambda:not self.w.isVisible())
        data = self.export('write-discarded')
        self.assertEqual(data['phase'], 'finished')
        self.assertEqual(data['market']['discarded_writes'], 1)
        self.assertIn('market_observation_conflict', data['reasons'])
        self.assertIn('market_write_discarded', data['reasons'])
        self.assertIsNotNone(writer.last_error)
        self.assertTrue(c.approved)

    def test_expired_capture_logs_and_throttling(self):
        observer = ObservedMarketObserver(monotonic=lambda: 20)
        observer.pending = ({'event': 'Market', 'MarketID': 1}, {'FID': 'F_PRIVATE_TEST'}, 15)
        self.w.state.observed_markets = observer
        self.w.close()
        c = self.w._exit_controller
        c.timer.stop()
        data = self.export('capture-expired')
        self.assertEqual(data['market']['captures_expired'], 1)
        self.assertEqual(data['workers']['running'], 0)
        self.assertEqual(data['pending_count'], 1)
        self.assertIn('market_capture_expired', data['reasons'])
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(PrivacyFormatter('%(asctime)s %(levelname)-8s [privacy-v1] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        logger = ed.logger
        old_level = logger.level
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        try:
            with patch.object(ed.time, 'monotonic', return_value=1000):
                ed.record(c, force=True)
            initial = stream.getvalue()
            self.assertIn('market_capture_expired', initial)
            self.assertNotIn('[redacted]', initial)
            for tick in range(1001, 1030):
                with patch.object(ed.time, 'monotonic', return_value=tick):
                    ed.record(c)
            self.assertEqual(stream.getvalue(), initial)
            with patch.object(ed.time, 'monotonic', return_value=1030):
                ed.record(c)
            self.assertGreater(len(stream.getvalue()), len(initial))
            self.cancel()
            self.assertIn('cancelled', stream.getvalue())
        finally:
            logger.removeHandler(handler)
            logger.setLevel(old_level)
        (self.root/'cmdrhelper.log').write_text(stream.getvalue())
        self.export('after-blockage-with-log')
        self.assertIsNotNone(observer.pending)  # Diagnostic reads never expire it.

    def test_export_failure_does_not_mark_session_and_new_process_resets(self):
        with patch.object(d, '_last_successful_export_at', None):
            self.assertFalse(d.exported_this_session())
            with patch.object(d.os, 'link', side_effect=OSError('Private Commander Bearer SECRET')):
                with self.assertRaises(OSError):
                    self.export('publish-failed')
            self.assertFalse(d.exported_this_session())
            self.export('session-first')
            self.assertTrue(d.exported_this_session())
            first_time = d._last_successful_export_at
            with patch.object(d.os, 'link', side_effect=OSError('synthetic failure')):
                with self.assertRaises(OSError):
                    self.export('publish-failed-again')
            self.assertEqual(d._last_successful_export_at, first_time)
            fresh = subprocess.check_output([sys.executable, '-c',
                'import json,sys; from cmdrhelper import diagnostics as d; '
                'print(json.dumps([d._SESSION_ID, d.exported_this_session()])); '
                'd.create_package(sys.argv[1], folder=sys.argv[2])',
                str(self.root/'new-process.zip'), str(self.root)], text=True)
            session, repeated = json.loads(fresh)
            self.assertNotEqual(session, d._SESSION_ID)
            self.assertFalse(repeated)
            with ZipFile(self.root/'new-process.zip') as archive:
                info = json.loads(archive.read('system_info.json'))
                self.assertEqual(info['session_id'], session)
                self.assertFalse(info['repeated_in_session'])
                self.assertIsNone(info['previous_successful_export_at'])

    def test_repeat_notice_survives_recreated_panel_and_blocked_exit_can_export(self):
        with patch.object(d, '_last_successful_export_at', None):
            self.export('notice-first')
            for _ in range(2):
                panel = DiagnosticsPanel(self.w.state, self.w)
                with patch('cmdrhelper.ui.diagnostics_panel.QMessageBox.information') as notice, \
                     patch('cmdrhelper.ui.diagnostics_panel.QFileDialog.getSaveFileName') as choose:
                    panel.create()
                    notice.assert_called_once()
                    choose.assert_not_called()
                panel.deleteLater()
            observer = ObservedMarketObserver(monotonic=lambda: 20)
            observer.pending = ({'event': 'Market'}, {}, 15)
            self.w.state.observed_markets = observer
            self.w.close()
            self.w._exit_controller.timer.stop()
            self.w.state.database = type('DB', (), {'path': None})()
            self.w.state.journal_folder = None
            panel = DiagnosticsPanel(self.w.state, self.w)
            target = self.root/'during-blockage.zip'
            with patch('cmdrhelper.ui.diagnostics_panel.QMessageBox.information') as notice, \
                 patch('cmdrhelper.ui.diagnostics_panel.QFileDialog.getSaveFileName', return_value=(str(target), '')), \
                 patch.object(d, 'log_folder', return_value=self.root):
                panel.create()
                self.assertEqual(notice.call_count, 2)  # Advice + successful export.
            with ZipFile(target) as archive:
                self.assertEqual(json.loads(archive.read('exit_diagnostics.json'))['phase'], 'draining')
                self.assertTrue(json.loads(archive.read('system_info.json'))['repeated_in_session'])
            evidence = os.environ.get('EXIT_DIAGNOSTICS_EVIDENCE')
            if evidence:
                Path(evidence, target.name).write_bytes(target.read_bytes())
            self.cancel()

    def test_unknown_diagnostic_failure_preserves_zip_export_privacy(self):
        with patch.object(ed, 'snapshot', side_effect=RuntimeError('Private Commander Bearer SECRET')):
            data = self.export('diagnostic-unavailable')
        self.assertEqual(data['reasons'], ['diagnostic_unavailable'])

    def test_transfer_journal_and_checkpoint_states_without_private_payloads(self):
        from cmdrhelper.exit_tasks import start_thread
        release = threading.Event()
        self.releases.append(release)
        thread = threading.Thread(target=lambda: release.wait(4), name='CMDRHelper-Inara-Upload')
        start_thread(thread)
        state = self.w.state
        state._inara_upload_running = True
        state._edsm_upload_running = False
        state._initial_journal_index_running = True
        state._database_import_running = True
        state._journal_catchup_running = True
        state.sources = SimpleNamespace(running=True, _ingesting=True, projecting=True,
            queue=['Private Commander'], runtimes={'F_PRIVATE_TEST': SimpleNamespace(
                watcher=None, transfer_error='Bearer SECRET', startup_transfer_deferred=True)})
        state.mining_inventory_controller = SimpleNamespace(_running=False, _dirty=True,
            _exit_write_error=True, timer=QTimer(), cargo_retry=QTimer())
        # Snapshot-only: this fixture deliberately does not implement source control.
        data = self.export('transfer-journal')
        self.assertEqual(data['workers']['python_running'], 1)
        self.assertEqual(data['categories']['inara']['python_running'], 1)
        self.assertTrue(data['transfers']['inara_running'])
        self.assertFalse(data['transfers']['edsm_running'])
        self.assertEqual(data['transfers']['source_errors'], 1)
        self.assertEqual(data['transfers']['source_deferred'], 1)
        self.assertTrue(data['journal']['index_running'])
        self.assertTrue(data['journal']['import_running'])
        self.assertTrue(data['journal']['catchup_running'])
        self.assertEqual(data['journal']['queued'], 1)
        self.assertTrue(data['mining']['dirty'])
        self.assertTrue(data['mining']['failed'])
        self.assertIn('mining_checkpoint_failed', data['reasons'])
        del state.sources
        del state.mining_inventory_controller
        release.set()
        thread.join(2)
        self.assertFalse(thread.is_alive())

    def test_restart_notice_has_direct_translation_in_all_twelve_languages(self):
        language = get_language()
        self.addCleanup(set_language, language)
        with patch.object(d, '_last_successful_export_at', 'synthetic-success'):
            for lang, table in _TRANSLATIONS.items():
                with self.subTest(language=lang):
                    set_language(lang)
                    panel = DiagnosticsPanel(self.w.state, self.w)
                    with patch('cmdrhelper.ui.diagnostics_panel.QMessageBox.information') as notice, \
                         patch('cmdrhelper.ui.diagnostics_panel.QFileDialog.getSaveFileName') as choose:
                        panel.create()
                        self.assertEqual(notice.call_args.args[2], table['diagnostics.restart_required'])
                        self.assertIn('CMDRHelper', notice.call_args.args[2])
                        self.assertNotIn('Windows', notice.call_args.args[2])
                        choose.assert_not_called()
                    panel.deleteLater()

    def test_logging_rejects_payloads_in_new_fields(self):
        from cmdrhelper.logging_config import _technical_fields
        self.assertEqual(_technical_fields(dict(exit_category='Private Commander',
            exit_event='Bearer SECRET', phase='F_PRIVATE_TEST', wait_seconds='/private/path',
            reason='Private Commander', source_errors='Bearer SECRET')), {})

    def test_repeated_settings_failure_is_throttled_and_visible_in_zip(self):
        job, release = self.work()
        self.w.close()
        c = self.w._exit_controller
        c.timer.stop()
        with patch.object(c, 'check_settings', side_effect=OSError('Bearer SECRET')), \
             patch.object(ed.time, 'monotonic', return_value=1000), \
             patch.object(ed, 'log_event') as log:
            for _ in range(30):
                self.assertFalse(c.finish())
            self.assertEqual(sum(call.kwargs.get('exit_event') == 'settings_failed' for call in log.call_args_list), 1)
        self.assertIn('settings_save_failed', self.export('settings-failed')['reasons'])
        self.cancel()
        self.assertNotIn('settings_save_failed', self.export('settings-cancelled')['reasons'])


if __name__ == '__main__':
    unittest.main()
