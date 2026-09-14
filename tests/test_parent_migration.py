"""Safety contract for the opt-in 3.4.1 migration, using disposable databases."""
import json
from contextlib import ExitStack
from types import SimpleNamespace
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QEventLoop, QTimer
from PySide6.QtWidgets import QApplication, QDialog
from cmdrhelper.database import CMDRDatabase
from cmdrhelper import parent_migration as m
from cmdrhelper.ui.parent_migration import ParentMigrationDialog


class MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root / 'cmdrhelper.db'
        db = CMDRDatabase(self.path)
        commander = db.upsert_commander('migration-test', 'Test')
        db.store_snapshot(dict(system_address=123, system='Example', system_bodies=[
            dict(body_id=0, name='Root', parent_id=None, parent_star_id=None),
            dict(body_id=1, name='Planet', parent_id=0, parent_star_id=0),
            dict(body_id=2, name='Moon', parent_id=0, parent_star_id=0),
            dict(body_id=3, name='No journal', parent_id=0, parent_star_id=0),
        ]), commander)
        self.folder = self.root / 'journals'
        self.folder.mkdir()
        self.journal = self.folder / 'Journal.2026-09-01T010000.01.log'
        self.events = [dict(event='Scan', SystemAddress=123, BodyID=2,
                            Parents=[{'Planet': 1}, {'Star': 0}])]
        self.write_events()
        with sqlite3.connect(self.path) as con:
            con.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        self.before = self.snapshot()
        self.hash = m.digest(self.journal)

    def write_events(self):
        self.journal.write_text('\n'.join(json.dumps(e) for e in self.events)+'\n')

    def snapshot(self):
        with m.readonly(self.path) as con:
            return m.fingerprint(con)

    def run_migration(self, **kwargs):
        kwargs.setdefault('process_check', lambda: False)
        return m.migrate(self.path, self.folder, **kwargs)

    def assert_unchanged(self):
        self.assertEqual(self.snapshot(), self.before)
        self.assertTrue(m.migration_required(self.path))
        self.assertEqual(m.digest(self.journal), self.hash)

    def release(self, version='3.4.3'):
        return dict(ok=True, version=version, published_at='2026-09-14T12:00:00Z')

    def test_actual_startup_gate_uses_db_marker_in_future_release(self):
        from cmdrhelper import app as entry
        for migrated in (False, True):
            if migrated:
                self.run_migration()
            before = self.snapshot()
            files = set(self.root.iterdir())
            for attempt in range(2):
                with ExitStack() as stack:
                    stack.enter_context(patch.object(entry.sys, 'excepthook'))
                    stack.enter_context(patch.object(entry, '__version__', '3.4.3'))
                    stack.enter_context(patch.object(entry, 'configure_logging', return_value='isolated'))
                    qt = stack.enter_context(patch.object(entry, 'QApplication'))
                    qt.return_value.exec.return_value = 0
                    settings = stack.enter_context(patch.object(entry, 'QSettings'))
                    settings.return_value.value.side_effect = lambda key, default='': default
                    stack.enter_context(patch.object(entry, 'QLockFile'))
                    stack.enter_context(patch.object(entry, 'set_language'))
                    stack.enter_context(patch.object(entry, 'consume_update_status', return_value=None))
                    state = stack.enter_context(patch.object(entry, 'AppState'))
                    stack.enter_context(patch.object(entry, 'MainWindow'))
                    stack.enter_context(patch.object(entry, '_resize_initial_window'))
                    stack.enter_context(patch('cmdrhelper.database.default_database_path', return_value=self.path))
                    stack.enter_context(patch('cmdrhelper.journal_reader.default_journal_paths', return_value=[self.folder]))
                    dialog = stack.enter_context(patch('cmdrhelper.ui.parent_migration.ParentMigrationDialog'))
                    dialog.return_value.exec.return_value = QDialog.Rejected
                    if migrated:
                        with self.assertRaises(SystemExit):
                            entry.run()
                        dialog.assert_not_called()
                        state.assert_called_once()
                    else:
                        entry.run()
                        dialog.assert_called_once()
                        state.assert_not_called()
                self.assertEqual(self.snapshot(), before)
                self.assertEqual(set(self.root.iterdir()), files)

    def test_ui_cleanup_waits_for_startup_and_publication_in_either_order(self):
        from cmdrhelper.ui.main_window import MainWindow
        for release_first in (False, True):
            host = SimpleNamespace(state=SimpleNamespace(database=SimpleNamespace(path=self.path)),
                                   _startup_progress_dialog=None)
            host._cleanup_parent_backup = lambda: MainWindow._cleanup_parent_backup(host)
            with patch('cmdrhelper.parent_migration.cleanup_backup') as cleanup:
                if release_first:
                    host._parent_backup_release = self.release()
                    host._cleanup_parent_backup()
                    cleanup.assert_not_called()
                MainWindow._initialization_finished(host, '')
                if not release_first:
                    self.assertIsNone(cleanup.call_args.kwargs['release'])
                    host._parent_backup_release = self.release()
                    host._cleanup_parent_backup()
                self.assertEqual(cleanup.call_args.kwargs['release'], self.release())
                self.assertTrue(cleanup.call_args.kwargs['startup_succeeded'])

    def test_legacy_committed_metadata_can_be_retired(self):
        with patch.object(m, '__version__', '3.4.1'):
            backup = Path(self.run_migration()['backup'])
        # The original 3.4.1 sidecar equals the metadata committed with COMPLETE.
        legacy = backup.with_suffix('.db.json').read_text(encoding='utf-8')
        with sqlite3.connect(self.path) as con:
            con.execute('UPDATE app_meta SET value=? WHERE key=?', (legacy, m.BACKUP_KEY))
        self.assertTrue(m.cleanup_backup(self.path, '3.4.3', startup_succeeded=True, release=self.release()))
        self.assertFalse(backup.exists())

    def test_direct_upgrade_and_same_release_retention(self):
        for version in ('3.4.3', '3.5.0'):
            with self.subTest(version=version), patch.object(m, '__version__', version):
                self.assertTrue(m.migration_required(self.path))
                result = self.run_migration()
                backup = Path(result['backup'])
                with m.readonly(self.path) as con:
                    meta = json.loads(con.execute('SELECT value FROM app_meta WHERE key=?', (m.BACKUP_KEY,)).fetchone()[0])
                self.assertEqual(meta['release'], version)
                self.assertTrue(meta['completed'])
                self.assertFalse(m.migration_required(self.path))
                self.assertFalse(m.cleanup_backup(self.path, version, startup_succeeded=True, release=self.release(version)))
                self.assertTrue(backup.exists())
                # Reset only the disposable fixture for the next simulated release.
                with sqlite3.connect(self.path) as con:
                    con.execute('DELETE FROM app_meta WHERE key=?', (m.MIGRATION_KEY,))

    def test_later_published_successful_start_cleans_verified_backup(self):
        with patch.object(m, '__version__', '3.4.1'):
            result = self.run_migration()
        backup = Path(result['backup'])
        before = self.snapshot()
        for version, success, release in (
            ('3.4.3', False, self.release()),
            ('3.4.3', True, None),
            ('3.4.3-dev', True, self.release('3.4.3-dev')),
            ('3.4.3', True, dict(self.release(), prerelease=True)),
            ('3.4.3', True, dict(self.release(), published_at='invalid')),
            ('3.4.3', True, self.release('3.5.0')),
        ):
            self.assertFalse(m.cleanup_backup(self.path, version, startup_succeeded=success, release=release))
            self.assertTrue(backup.exists())
            self.assertEqual(self.snapshot(), before)
        self.assertTrue(m.cleanup_backup(self.path, '3.4.3', startup_succeeded=True, release=self.release()))
        self.assertFalse(backup.exists())
        self.assertFalse(backup.with_suffix('.db.json').exists())
        self.assertFalse(m.migration_required(self.path))

    def test_unknown_metadata_and_foreign_paths_retain_backup(self):
        backup = Path(self.run_migration()['backup'])
        with m.readonly(self.path) as con:
            original = json.loads(con.execute('SELECT value FROM app_meta WHERE key=?', (m.BACKUP_KEY,)).fetchone()[0])
        variants = [{}, dict(original, release='unknown'), dict(original, completed=False),
                    dict(original, path=r'C:\\Users\\Pilot\\backup.db'),
                    dict(original, path='/another-machine/backup.db')]
        for key in ('release', 'created_utc', 'sha256', 'purpose'):
            variant = dict(original)
            del variant[key]
            variants.append(variant)
        for meta in variants:
            with sqlite3.connect(self.path) as con:
                con.execute('UPDATE app_meta SET value=? WHERE key=?', (json.dumps(meta), m.BACKUP_KEY))
            self.assertFalse(m.cleanup_backup(self.path, '3.5.0', startup_succeeded=True, release=self.release('3.5.0')))
            self.assertTrue(backup.exists())

    def test_failed_backup_cannot_be_cleaned_by_later_release(self):
        def broken(con, candidates):
            m.apply_candidates(con, candidates)
            raise RuntimeError('simulated failure')
        with self.assertRaises(m.MigrationError) as error:
            self.run_migration(repair=broken)
        self.assertTrue(error.exception.restored)
        self.assert_unchanged()
        self.assertFalse(m.cleanup_backup(self.path, '3.4.3', startup_succeeded=True, release=self.release()))
        self.assertEqual(len(list(self.root.glob('cmdrhelper_pre_parent_repair_*.db'))), 1)

    def test_cancel_is_readonly_without_backup(self):
        db_hash = m.digest(self.path)
        files = set(self.root.iterdir())
        dialog = ParentMigrationDialog(self.path, self.folder)
        QTimer.singleShot(0, dialog.cancel_button.click)
        self.assertEqual(dialog.exec(), QDialog.Rejected)
        self.assertIsNone(dialog.worker)
        self.assertEqual(set(self.root.iterdir()), files)
        self.assertEqual(m.digest(self.path), db_hash)
        self.assert_unchanged()

    def test_game_running_no_backup_or_changes(self):
        with self.assertRaises(m.MigrationError) as error:
            self.run_migration(process_check=lambda: True)
        self.assertEqual(error.exception.key, 'active')
        self.assertFalse(list(self.root.glob('*pre_parent*')))
        self.assert_unchanged()

    def test_changed_journal_inventory_does_not_start(self):
        expected = m.inventory(self.folder)
        self.journal.write_text(self.journal.read_text() + '\n')
        self.hash = m.digest(self.journal)
        with self.assertRaises(m.MigrationError) as error:
            self.run_migration(expected_inventory=expected)
        self.assertEqual(error.exception.key, 'active')
        self.assertFalse(list(self.root.glob('*pre_parent*')))
        self.assert_unchanged()

    def test_change_during_preflight_does_not_start(self):
        original = m.collect_candidates
        def changing(*args, **kwargs):
            result = original(*args, **kwargs)
            self.journal.write_text(self.journal.read_text() + '\n')
            self.hash = m.digest(self.journal)
            return result
        with patch.object(m, 'collect_candidates', changing):
            with self.assertRaises(m.MigrationError) as error:
                self.run_migration()
        self.assertEqual(error.exception.key, 'active')
        self.assertFalse(list(self.root.glob('*pre_parent*')))
        self.assert_unchanged()

    def test_verified_backup_success_allowed_fields_idempotence_and_marker(self):
        with m.readonly(self.path) as con:
            protected = m.fingerprint(con, protected=True)
        phases = []
        result = self.run_migration(progress=phases.append)
        self.assertEqual(phases, list(range(6)))
        self.assertEqual((result['systems'], result['bodies'], result['fields']), (1, 1, 1))
        self.assertEqual(result['remaining'], 0)
        backup = Path(result['backup'])
        with m.readonly(backup) as con:
            self.assertEqual(m.fingerprint(con), self.before)
        metadata = json.loads(backup.with_suffix('.db.json').read_text())
        self.assertEqual(metadata['sha256'], m.digest(backup))
        self.assertEqual(metadata['size'], backup.stat().st_size)
        self.assertTrue(metadata['byte_equal'])
        with sqlite3.connect(self.path) as con:
            self.assertEqual(m.fingerprint(con, protected=True), protected)
            m.check_integrity(con)
            second = m.apply_candidates(con, m.collect_candidates([self.journal])[0])
            self.assertEqual(second['fields'], 0)
            self.assertEqual(second['metadata'], 0)
            self.assertEqual(con.execute('SELECT value FROM app_meta WHERE key=?', (m.MIGRATION_KEY,)).fetchone(), (m.COMPLETE,))
        self.assertFalse(m.migration_required(self.path))
        CMDRDatabase(self.path)
        self.assertTrue(backup.exists())
        self.assertEqual(m.digest(self.journal), self.hash)

    def test_backup_failure_does_not_repair(self):
        with patch.object(m, 'verify_backup', side_effect=OSError('injected backup failure')):
            with self.assertRaises(m.MigrationError) as error:
                self.run_migration()
        self.assertEqual(error.exception.key, 'backup_error')
        self.assert_unchanged()

    def test_backup_byte_mismatch_detected(self):
        a, b = self.root/'a', self.root/'b'
        a.write_bytes(b'ab'); b.write_bytes(b'ac')
        with self.assertRaises(m.MigrationError):
            m.verify_backup(a, b)

    def test_repair_failure_rolls_back_and_retains_backup(self):
        def broken(con, candidates):
            m.apply_candidates(con, candidates)
            raise RuntimeError('injected repair failure')
        with self.assertRaises(m.MigrationError) as error:
            self.run_migration(repair=broken)
        self.assertTrue(error.exception.restored)
        self.assertTrue(list(self.root.glob('*pre_parent*.db')))
        self.assert_unchanged()
        self.assertEqual(self.run_migration()['fields'], 1)

    def test_integrity_failure_rolls_back(self):
        def broken(con):
            raise m.MigrationError('integrity_error')
        with self.assertRaises(m.MigrationError) as error:
            self.run_migration(integrity=broken)
        self.assertTrue(error.exception.restored)
        self.assert_unchanged()

    def test_unrelated_change_rejected(self):
        def broken(con, candidates):
            result = m.apply_candidates(con, candidates)
            con.execute("UPDATE commanders SET current_name='unexpected'")
            return result
        with self.assertRaises(m.MigrationError) as error:
            self.run_migration(repair=broken)
        self.assertTrue(error.exception.restored)
        self.assert_unchanged()

    def test_missing_journals_remain_pending(self):
        self.journal.unlink()
        with self.assertRaises(m.MigrationError) as error:
            self.run_migration()
        self.assertEqual(error.exception.key, 'missing')
        self.assertEqual(self.snapshot(), self.before)
        self.assertTrue(m.migration_required(self.path))
        self.assertFalse(list(self.root.glob('*pre_parent*')))

    def test_partial_history_no_unknown_bodies_or_guessed_parents(self):
        self.events += [dict(event='Scan', SystemAddress=123, BodyID=99, Parents=[{'Star': 0}])]
        self.write_events()
        self.run_migration()
        with m.readonly(self.path) as con:
            self.assertEqual(con.execute('SELECT body_id,parent_id FROM bodies ORDER BY body_id').fetchall(),
                             [(0, None), (1, 0), (2, 1), (3, 0)])

    def test_conflicting_parents_no_guess(self):
        self.events.append(dict(self.events[0], Parents=[{'Planet': 77}]))
        self.write_events()
        with self.assertRaises(m.MigrationError) as error:
            self.run_migration()
        self.assertEqual(error.exception.key, 'missing')
        self.assertEqual(self.snapshot(), self.before)
        self.assertTrue(m.migration_required(self.path))

    def test_backup_restores_when_transaction_was_lost(self):
        def broken(con, candidates):
            m.apply_candidates(con, candidates)
            # Simulate losing transaction safety; production repair never commits.
            con.commit()
            raise RuntimeError('injected lost transaction')
        with self.assertRaises(m.MigrationError) as error:
            self.run_migration(repair=broken)
        self.assertTrue(error.exception.restored)
        self.assert_unchanged()

    def test_incorrect_repair_fails_idempotence_check(self):
        def broken(con, candidates):
            result = m.apply_candidates(con, candidates)
            con.execute('UPDATE bodies SET parent_id=0 WHERE body_id=2')
            return result
        with self.assertRaises(m.MigrationError) as error:
            self.run_migration(repair=broken)
        self.assertTrue(error.exception.restored)
        self.assert_unchanged()

    def test_foreign_key_violation_is_detected(self):
        with sqlite3.connect(self.path) as con:
            con.execute('PRAGMA foreign_keys=OFF')
            con.execute('UPDATE bodies SET system_address=999 WHERE body_id=2')
        with m.readonly(self.path) as con:
            with self.assertRaises(m.MigrationError):
                m.check_integrity(con)

    def test_journal_change_after_backup_rolls_back(self):
        def phase(step):
            if step == 3:
                self.journal.write_text(self.journal.read_text() + '\n')
                self.hash = m.digest(self.journal)
        with self.assertRaises(m.MigrationError) as error:
            self.run_migration(progress=phase)
        self.assertEqual(error.exception.key, 'active')
        self.assertTrue(error.exception.restored)
        self.assert_unchanged()

    def test_backup_includes_committed_wal_pages(self):
        con = sqlite3.connect(self.path)
        self.addCleanup(con.close)
        con.execute('PRAGMA journal_mode=WAL')
        con.execute("UPDATE commanders SET current_name='Committed WAL state'")
        con.commit()
        self.assertGreater(Path(str(self.path) + '-wal').stat().st_size, 0)
        before = self.snapshot()
        result = self.run_migration()
        with m.readonly(result['backup']) as backup:
            self.assertEqual(m.fingerprint(backup), before)

    def test_busy_database_does_not_start_repair(self):
        con = sqlite3.connect(self.path)
        self.addCleanup(con.close)
        con.execute('BEGIN IMMEDIATE')
        with self.assertRaises(m.MigrationError):
            self.run_migration()
        con.rollback()
        self.assertFalse(list(self.root.glob('*pre_parent*')))
        self.assert_unchanged()

    def test_full_dialog_worker_success_and_reopen_gate(self):
        dialog = ParentMigrationDialog(self.path, self.folder)
        loop = QEventLoop()
        timer = QTimer(); timer.setSingleShot(True); timer.timeout.connect(loop.quit)
        dialog.show()
        dialog.start_button.click()
        self.assertTrue(dialog.ships.running)
        dialog.worker.completed.connect(loop.quit)
        timer.start(15000)
        loop.exec()
        self.assertTrue(dialog.succeeded, dialog.outcome.text())
        self.assertFalse(dialog.ships.running)
        self.assertIn('✓', dialog.steps.text())
        dialog.start_button.click()
        self.assertEqual(dialog.result(), QDialog.Accepted)
        self.assertFalse(m.migration_required(self.path))


if __name__ == '__main__':
    unittest.main()
