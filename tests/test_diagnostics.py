"""Privacy, bounded storage and user-controlled diagnostics on disposable files."""
import io
import json
import logging
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication

from cmdrhelper import diagnostics as d, logging_config as lc
from cmdrhelper.i18n import tr, set_language
from cmdrhelper.ui.diagnostics_panel import DiagnosticsPanel
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class DiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.logs = self.root / 'logs'
        self.logs.mkdir()
        self.db = self.root / 'private.db'
        with sqlite3.connect(self.db) as con:
            con.execute('CREATE TABLE secret (fid TEXT)')
            con.execute("INSERT INTO secret VALUES ('F999999')")
        self.journals = self.root / 'Private Commander'
        self.journals.mkdir()
        (self.journals / 'Journal.2026-09-14T010000.01.log').write_text('private journal')
        self.state = SimpleNamespace(database=SimpleNamespace(path=self.db), journal_folder=self.journals)
        self.logger = logging.getLogger('cmdrhelper.diagnostic_test')
        self.old_handlers, self.old_level, self.old_propagate = self.logger.handlers[:], self.logger.level, self.logger.propagate
        self.logger.handlers = []
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        self.stream = io.StringIO()
        handler = logging.StreamHandler(self.stream)
        handler.setFormatter(lc.PrivacyFormatter('%(asctime)s %(levelname)-8s [privacy-v1] %(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        self.logger.addHandler(handler)
        self.addCleanup(self.restore_logger)

    def restore_logger(self):
        self.logger.handlers = self.old_handlers
        self.logger.setLevel(self.old_level)
        self.logger.propagate = self.old_propagate

    def test_rotation_and_reconfiguration(self):
        root = logging.getLogger()
        old_handlers, old_level = root.handlers[:], root.level
        root.handlers = []
        import threading
        old_thread_hook = threading.excepthook
        try:
            with patch.object(lc, 'log_folder', return_value=self.logs), patch.object(lc, 'LOG_MAX_BYTES', 300):
                path = lc.configure_logging()
                self.assertEqual(lc.configure_logging(), path)
                self.assertEqual(len(root.handlers), 1)
                for _ in range(80):
                    logging.getLogger('cmdrhelper.rotation').info('Rotation test event with bounded content')
                files = list(self.logs.iterdir())
                self.assertEqual(len(files), 5)
                self.assertTrue(all(p.stat().st_size <= 300 for p in files))
        finally:
            for handler in root.handlers:
                handler.close()
            root.handlers = old_handlers
            root.setLevel(old_level)
            threading.excepthook = old_thread_hook

    def test_log_write_failure_does_not_expose_raw_record(self):
        handler = lc.PrivacyRotatingFileHandler(self.logs/'cmdrhelper.log', maxBytes=1024, backupCount=4)
        handler.setFormatter(lc.PrivacyFormatter('%(message)s'))
        record = logging.LogRecord('cmdrhelper.test', logging.ERROR, __file__, 1,
                                   'Request failed: %s', ('private-api-token',), None)
        try:
            with patch.object(handler, 'shouldRollover', side_effect=OSError('private-api-token')), patch('sys.stderr', new_callable=io.StringIO) as stderr:
                handler.emit(record)
                self.assertNotIn('private-api-token',stderr.getvalue())
                self.assertIn('unavailable',stderr.getvalue())
        finally:
            handler.close()

    def test_legacy_updater_log_is_bounded_and_redacted_in_cli(self):
        from cmdrhelper import update
        with patch.object(lc, 'LOG_MAX_BYTES', 200), patch.object(update, '__name__', '__main__'):
            for _ in range(40):
                update._log_update(self.root, 'ROLLBACK: private token and Commander Alice')
        files = list((self.root/'backup').glob('update.log*'))
        self.assertEqual(len(files), 2)
        self.assertTrue(all(path.stat().st_size <= 200 for path in files))
        text = ''.join(path.read_text() for path in files)
        self.assertIn('rollback',text)
        self.assertNotIn('private token',text)
        self.assertNotIn('Alice',text)

    def test_start_fields_and_privacy(self):
        info = d.system_info(self.db, self.journals)
        lc.log_event(self.logger, 'Application started', version=info['version'], os=info['os'], python=info['python'],
                     fid='F999999', commander='Private Commander', token='secret-token')
        self.logger.warning('Request failed: %s', {'Commander': 'Private Commander', 'Authorization': 'Bearer secret-token', 'Latitude': 23.98765})
        self.logger.error('Failure: %s', 'unlabelled-secret')
        text = self.stream.getvalue()
        for value in ('version=', 'os=', 'python='):
            self.assertIn(value, text)
        for value in ('F999999', 'Private Commander', 'secret-token', '23.98765', 'unlabelled-secret'):
            self.assertNotIn(value, text)

    def test_traceback_chain_without_payload_or_source(self):
        try:
            try:
                raise ValueError('unlabelled-token-and-private-note')
            except ValueError as exc:
                raise RuntimeError('Commander: Private Commander') from exc
        except RuntimeError:
            self.logger.exception('Operation failed')
        text = self.stream.getvalue()
        self.assertIn('Traceback', text)
        self.assertIn('test_traceback_chain_without_payload_or_source', text)
        self.assertIn('ValueError', text)
        self.assertIn('RuntimeError', text)
        self.assertNotIn('unlabelled-token', text)
        self.assertNotIn('Private Commander', text)
        self.assertNotIn(str(self.root), text)

    def test_structured_redaction_urls_and_platform_paths(self):
        value = lc.sanitize({'Authorization':'Bearer abc', 'nested':{'api_key':'key','OAuthToken':'token','FID':'F999999'},
                             'url':'https://alice:password@example.com/secret?access_token=abc#token'})
        text = json.dumps(value)
        for forbidden in ('Bearer abc','"key"','"token"','F999999','alice','password','access_token','secret?'):
            self.assertNotIn(forbidden, text)
        for path in (r'C:\Users\PrivateName\logs\cmdrhelper.log', '/home/PrivateName/logs/cmdrhelper.log'):
            self.assertNotIn('PrivateName', lc.sanitize(path))
        self.assertNotIn('secret', lc.sanitize('{"unknown": "secret"}'))

    def test_zip_allowlist_and_technical_info_no_payloads(self):
        self.logger.warning('Safe warning')
        (self.logs / 'cmdrhelper.log').write_text(self.stream.getvalue())
        (self.logs / 'cmdrhelper.log.2').write_text('2026-09-13 01:02:03 WARNING Commander: PRIVATE LEGACY TOKEN\nsecret continuation\n')
        for name in ('database.db', 'Journal.secret.log', 'favorites.zip', 'image.png', 'cmdrhelper.log.99'):
            (self.logs / name).write_text('PRIVATE PAYLOAD')
        before = self.db.read_bytes()
        path = d.create_package(self.root/'report.zip', database=self.db, journals=self.journals, folder=self.logs)
        with ZipFile(path) as archive:
            self.assertEqual(set(archive.namelist()), {'cmdrhelper.log','cmdrhelper.log.2','system_info.json','diagnose_summary.txt'})
            info = json.loads(archive.read('system_info.json'))
            self.assertTrue(info['database_reachable'])
            self.assertTrue(info['journal_folder_reachable'])
            self.assertEqual(info['journal_files'], 1)
            self.assertEqual(info['database_size'], len(before))
            content = b''.join(archive.read(name) for name in archive.namelist()).decode()
            for forbidden in ('PRIVATE', 'F999999', str(self.root), 'secret continuation'):
                self.assertNotIn(forbidden, content)
            self.assertIn('Safe warning', content)
        self.assertEqual(self.db.read_bytes(), before)
        self.assertEqual((self.journals/'Journal.2026-09-14T010000.01.log').read_text(), 'private journal')

    def test_missing_logs_and_unreachable_sources(self):
        path = d.create_package(self.root/'empty.zip', database=self.root/'absent.db', journals=self.root/'absent', folder=self.logs)
        with ZipFile(path) as archive:
            self.assertEqual(len(archive.namelist()),2)
            info = json.loads(archive.read('system_info.json'))
            self.assertFalse(info['database_reachable'])
            self.assertFalse(info['journal_folder_reachable'])
        self.assertFalse((self.root/'absent.db').exists())

    def test_symlink_not_collected(self):
        (self.logs/'cmdrhelper.log').symlink_to(self.db)
        path = d.create_package(self.root/'report.zip', folder=self.logs)
        with ZipFile(path) as archive:
            self.assertNotIn('cmdrhelper.log',archive.namelist())

    def test_atomic_failure_and_no_unasked_overwrite(self):
        path = self.root/'report.zip'
        path.write_bytes(b'original')
        with self.assertRaises(FileExistsError):
            d.create_package(path, folder=self.logs)
        with patch.object(ZipFile,'writestr',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                d.create_package(path, folder=self.logs, overwrite=True)
            with self.assertRaises(OSError):
                d.create_package(self.root/'new.zip',folder=self.logs)
        self.assertEqual(path.read_bytes(), b'original')
        self.assertFalse((self.root/'new.zip').exists())
        self.assertFalse(list(self.root.glob('.cmdrhelper-diagnose-*')))

    def test_panel_themes_missing_log_cancel_and_native_url(self):
        for stylesheet in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            panel = DiagnosticsPanel(self.state)
            panel.setStyleSheet(stylesheet)
            panel.show()
            self.app.processEvents()
            with patch('cmdrhelper.ui.diagnostics_panel.log_folder', return_value=self.logs), patch('cmdrhelper.ui.diagnostics_panel.QMessageBox.information') as message, patch('cmdrhelper.ui.diagnostics_panel.QDesktopServices.openUrl',return_value=True) as open_url:
                panel.open_log()
                message.assert_called_once()
                open_url.assert_not_called()
                (self.logs/'cmdrhelper.log').write_text('')
                panel.open_log()
                url = open_url.call_args.args[0]
                self.assertTrue(url.isLocalFile())
                self.assertEqual(Path(url.toLocalFile()),self.logs/'cmdrhelper.log')
                (self.logs/'cmdrhelper.log').unlink()
            with patch('cmdrhelper.ui.diagnostics_panel.QFileDialog.getSaveFileName',return_value=('','')), patch('cmdrhelper.ui.diagnostics_panel.create_package') as create:
                panel.create()
                create.assert_not_called()
            self.assertTrue(panel.open_button.isEnabled())
            panel.close()

    def test_panel_export_success_and_error(self):
        panel = DiagnosticsPanel(self.state)
        target = str(self.root/'chosen.zip')
        with patch('cmdrhelper.diagnostics.log_folder',return_value=self.logs), patch('cmdrhelper.ui.diagnostics_panel.QFileDialog.getSaveFileName',return_value=(target,'')), patch('cmdrhelper.ui.diagnostics_panel.QMessageBox.information') as success:
            panel.create()
            self.assertTrue(Path(target).is_file())
            self.assertIn(target,success.call_args.args[2])
        with patch('cmdrhelper.ui.diagnostics_panel.QFileDialog.getSaveFileName',return_value=(target,'')), patch('cmdrhelper.ui.diagnostics_panel.create_package',side_effect=OSError('secret')), patch('cmdrhelper.ui.diagnostics_panel.QMessageBox.warning') as failure:
            panel.create()
            self.assertNotIn('secret',failure.call_args.args[2])
        self.assertTrue(panel.create_button.isEnabled())
        panel.close()

    def test_external_messages_and_dynamic_types_are_omitted(self):
        record = logging.LogRecord('thirdparty','ERROR',__file__,1,'Private Commander Bearer-secret',(),None)
        self.assertNotIn('Private Commander',lc.PrivacyFormatter('%(message)s').format(record))
        self.logger.info('Identifiers: %d', 999999)
        self.logger.info('Data: %s', {'Note':'private note','inventory':{'gold':99}})
        self.logger.info('{"event":"Location","Commander":"Private Commander"}')
        lc.log_event(self.logger,'Technical event',version='F999999',phase='PrivateCommander',mode='secret')
        text=self.stream.getvalue()
        for value in ('999999','private note','gold','Private Commander','PrivateCommander','secret'):
            self.assertNotIn(value,text)

    def test_all_languages_and_help(self):
        import importlib
        languages = ('de','en','el','es','fi','fr','it','nl','no','pl','sv','tr')
        try:
            for lang in languages:
                set_language(lang)
                for key in ('title','open','create','info','unavailable','failed','saved','summary'):
                    self.assertNotEqual(tr('diagnostics.'+key),'diagnostics.'+key)
                summary=tr('diagnostics.summary',version='test',platform='test',count=0,period='–',warnings='–')
                self.assertNotIn('{',summary)
                help_text = importlib.import_module('cmdrhelper.help_content.'+lang).HELP_TOPICS['settings'][1]
                for name in ('cmdrhelper.log','system_info.json','diagnose_summary.txt'):
                    self.assertIn(name,help_text)
        finally:
            set_language('de')


if __name__ == '__main__':
    unittest.main()
