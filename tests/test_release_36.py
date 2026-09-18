"""Release 3.6 migration safety; isolated databases only."""
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from cmdrhelper.database import CMDRDatabase, CommanderMigrationError


class Release36MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'upgrade.db'
        CMDRDatabase(self.path)
        with sqlite3.connect(self.path) as con:
            for table in ('station_observations', 'commander_ship_sales', 'commander_deleted_ships'):
                con.execute('DROP TABLE ' + table)
            con.execute('PRAGMA user_version=17')

    def test_upgrade_preserves_verified_schema17_backup_and_is_idempotent(self):
        db = CMDRDatabase(self.path)
        backups = list(self.path.parent.glob('*.pre-v20-*.bak'))
        self.assertEqual(len(backups), 1)
        with sqlite3.connect(backups[0]) as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], 17)
            self.assertEqual(con.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
        with db._connect() as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], 20)
            self.assertEqual(con.execute('PRAGMA foreign_keys').fetchone()[0], 1)
            self.assertEqual(con.execute('PRAGMA foreign_key_check').fetchall(), [])
        CMDRDatabase(self.path)
        self.assertEqual(list(self.path.parent.glob('*.pre-v20-*.bak')), backups)

    def test_backup_failure_aborts_before_schema_changes(self):
        with patch.object(CMDRDatabase, '_create_migration_backup', side_effect=CommanderMigrationError('test')):
            with self.assertRaises(CommanderMigrationError):
                CMDRDatabase(self.path)
        with sqlite3.connect(self.path) as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], 17)
            self.assertIsNone(con.execute("SELECT name FROM sqlite_master WHERE name='station_observations'").fetchone())

    def test_partial_upgrade_is_backed_up_before_remaining_migrations(self):
        for version in (18, 19):
            with sqlite3.connect(self.path) as con:
                con.execute(f'PRAGMA user_version={version}')
            CMDRDatabase(self.path)
            backup = sorted(self.path.parent.glob('*.pre-v20-*.bak'))[-1]
            with sqlite3.connect(backup) as con:
                self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], version)
