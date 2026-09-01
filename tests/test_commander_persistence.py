from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cmdrhelper.database import (
    CMDRDatabase,
    CommanderMigrationError,
    PERSONAL_TABLES,
    SCHEMA_VERSION,
)


LEGACY_PERSONAL_SCHEMA = """
CREATE TABLE system_visits (id INTEGER PRIMARY KEY AUTOINCREMENT, system_address INTEGER NOT NULL,
 system_name TEXT NOT NULL DEFAULT '', visited_at TEXT NOT NULL DEFAULT '', x REAL, y REAL, z REAL,
 UNIQUE(system_address, visited_at));
CREATE TABLE biology (system_address INTEGER NOT NULL, body_id INTEGER NOT NULL,
 genus TEXT NOT NULL DEFAULT '', species TEXT NOT NULL DEFAULT '', variant TEXT NOT NULL DEFAULT '',
 scan_type TEXT NOT NULL DEFAULT '', first_seen TEXT NOT NULL DEFAULT '', last_seen TEXT NOT NULL DEFAULT '',
 PRIMARY KEY(system_address, body_id, genus, species, variant));
CREATE TABLE geology (system_address INTEGER NOT NULL, body_id INTEGER NOT NULL,
 name TEXT NOT NULL DEFAULT '', raw_name TEXT NOT NULL DEFAULT '', source TEXT NOT NULL DEFAULT '',
 first_seen TEXT NOT NULL DEFAULT '', last_seen TEXT NOT NULL DEFAULT '',
 PRIMARY KEY(system_address, body_id, name, source));
CREATE TABLE codex_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, system_address INTEGER,
 system_name TEXT NOT NULL DEFAULT '', category TEXT NOT NULL DEFAULT '', subcategory TEXT NOT NULL DEFAULT '',
 name TEXT NOT NULL DEFAULT '', raw_name TEXT NOT NULL DEFAULT '', nearest_destination TEXT NOT NULL DEFAULT '',
 region TEXT NOT NULL DEFAULT '', event_type TEXT NOT NULL DEFAULT '', first_seen TEXT NOT NULL DEFAULT '',
 last_seen TEXT NOT NULL DEFAULT '', UNIQUE(system_address, category, subcategory, name, nearest_destination, event_type));
CREATE TABLE cartography_sales (id INTEGER PRIMARY KEY AUTOINCREMENT, journal_file TEXT NOT NULL DEFAULT '',
 event_timestamp TEXT NOT NULL DEFAULT '', event_type TEXT NOT NULL DEFAULT '', base_value INTEGER NOT NULL DEFAULT 0,
 bonus INTEGER NOT NULL DEFAULT 0, total_earnings INTEGER NOT NULL DEFAULT 0, estimated_total INTEGER NOT NULL DEFAULT 0,
 correction_factor REAL, body_count INTEGER NOT NULL DEFAULT 0, first_seen TEXT NOT NULL DEFAULT '',
 UNIQUE(journal_file, event_timestamp, event_type));
CREATE TABLE journal_imports (journal_file TEXT PRIMARY KEY, file_size INTEGER NOT NULL DEFAULT 0,
 modified_ns INTEGER NOT NULL DEFAULT 0, last_import TEXT NOT NULL DEFAULT '');
CREATE TABLE bio_value_journal_scans (journal_file TEXT PRIMARY KEY, file_size INTEGER NOT NULL DEFAULT 0,
 modified_ns INTEGER NOT NULL DEFAULT 0, last_scan TEXT NOT NULL DEFAULT '');
CREATE TABLE cartography_value_journal_scans (journal_file TEXT PRIMARY KEY, file_size INTEGER NOT NULL DEFAULT 0,
 modified_ns INTEGER NOT NULL DEFAULT 0, last_scan TEXT NOT NULL DEFAULT '');
CREATE INDEX idx_system_visits_time ON system_visits(visited_at);
CREATE INDEX idx_geology_body ON geology(system_address, body_id);
CREATE INDEX idx_codex_system ON codex_entries(system_address);
CREATE INDEX idx_codex_name ON codex_entries(name);
"""


def make_v2(path: Path) -> None:
    CMDRDatabase(path)
    con = sqlite3.connect(path)
    try:
        con.execute("PRAGMA foreign_keys=OFF")
        for table in PERSONAL_TABLES:
            con.execute(f"DROP TABLE {table}")
        con.executescript(LEGACY_PERSONAL_SCHEMA)
        con.execute("PRAGMA user_version=2")
        con.commit()
    finally:
        con.close()


def write_journal(path: Path, events: list[dict]) -> None:
    path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")


class CommanderPersistenceMigrationTests(unittest.TestCase):
    def test_v2_single_commander_preserves_rows_and_foreign_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.db"
            make_v2(path)
            with sqlite3.connect(path) as con:
                commander_id = con.execute(
                    "INSERT INTO commanders(fid, current_name) VALUES ('F-A', 'Alpha')"
                ).lastrowid
                con.execute("INSERT INTO system_visits(system_address, visited_at) VALUES(42, 'T')")
                con.execute("INSERT INTO biology(system_address, body_id, species) VALUES(42, 1, 'Bio')")
                con.execute("INSERT INTO geology(system_address, body_id, name, source) VALUES(42, 1, 'Geo', 'Codex')")
                con.execute("INSERT INTO codex_entries(system_address, name) VALUES(42, 'Codex')")
                sale_id = con.execute(
                    "INSERT INTO cartography_sales(journal_file, event_timestamp, event_type) VALUES('a.log','T','Sale')"
                ).lastrowid
                con.execute(
                    "INSERT INTO cartography_sale_bodies(sale_id, system_address, body_id) VALUES(?,?,?)",
                    (sale_id, 42, 1),
                )
                con.execute("INSERT INTO journal_imports(journal_file) VALUES('a.log')")
                con.execute("INSERT INTO bio_value_journal_scans(journal_file) VALUES('a.log')")
                con.execute("INSERT INTO cartography_value_journal_scans(journal_file) VALUES('a.log')")
                before = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in PERSONAL_TABLES}

            database = CMDRDatabase(path)
            database.set_active_commander(commander_id)
            with database._connect() as con:
                after = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in PERSONAL_TABLES}
                self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
                self.assertEqual(before, after)
                self.assertFalse(con.execute("PRAGMA foreign_key_check").fetchall())
                self.assertEqual(con.execute("SELECT commander_id FROM biology").fetchone()[0], commander_id)
                self.assertEqual(con.execute("SELECT COUNT(*) FROM cartography_sale_bodies").fetchone()[0], 1)
            self.assertTrue(list(Path(directory).glob("legacy.db.pre-v3-*.bak")))
            CMDRDatabase(path)

    def test_ambiguous_commanders_abort_without_schema_change(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ambiguous.db"
            make_v2(path)
            with sqlite3.connect(path) as con:
                con.execute("INSERT INTO commanders(fid) VALUES('F-A')")
                con.execute("INSERT INTO commanders(fid) VALUES('F-B')")
                con.execute("INSERT INTO biology(system_address, body_id, species) VALUES(1, 1, 'Kept')")

            with self.assertRaises(CommanderMigrationError):
                CMDRDatabase(path)
            with sqlite3.connect(path) as con:
                self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], 2)
                self.assertNotIn("commander_id", {r[1] for r in con.execute("PRAGMA table_info(biology)")})
                self.assertEqual(con.execute("SELECT species FROM biology").fetchall(), [("Kept",)])

    def test_backup_failure_prevents_migration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "backup.db"
            make_v2(path)
            with sqlite3.connect(path) as con:
                con.execute("INSERT INTO commanders(fid) VALUES('F-A')")
                con.execute("INSERT INTO biology(system_address, body_id, species) VALUES(1, 1, 'Kept')")
            database = object.__new__(CMDRDatabase)
            database.path = path
            database.active_commander_id = None
            with patch.object(database, "_create_migration_backup", side_effect=CommanderMigrationError("backup")):
                with self.assertRaises(CommanderMigrationError):
                    database.ensure_schema_v3()
            with sqlite3.connect(path) as con:
                self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], 2)
                self.assertEqual(con.execute("SELECT COUNT(*) FROM biology").fetchone()[0], 1)


class CommanderPersistenceFunctionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "test.db"
        self.database = CMDRDatabase(self.path)
        self.a = self.database.upsert_commander("F-A", "Same")
        self.b = self.database.upsert_commander("F-B", "Same")

    def tearDown(self):
        self.tmp.cleanup()

    def test_duplicate_personal_keys_and_filtered_reads(self):
        for commander_id in (self.a, self.b):
            self.database.store_visit(42, "Shared", "T", commander_id=commander_id)
            self.database.store_biology(42, 1, species="Bio", commander_id=commander_id)
            self.database.store_geology(42, 1, name="Geo", source="Codex", commander_id=commander_id)
            self.database.store_codex_entry(42, name="Codex", commander_id=commander_id)
        with self.database._connect() as con:
            for table in ("system_visits", "biology", "geology", "codex_entries"):
                self.assertEqual(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], 2)
            for commander_id in (self.a, self.b):
                con.execute(
                    """INSERT INTO cartography_sales
                       (commander_id, journal_file, event_timestamp, event_type)
                       VALUES(?, 'same.log', 'T', 'Sale')""",
                    (commander_id,),
                )
                con.execute(
                    "INSERT INTO journal_imports(commander_id, journal_file) VALUES(?, 'same.log')",
                    (commander_id,),
                )
                con.execute(
                    "INSERT INTO bio_value_journal_scans(commander_id, journal_file) VALUES(?, 'same.log')",
                    (commander_id,),
                )
                con.execute(
                    "INSERT INTO cartography_value_journal_scans(commander_id, journal_file) VALUES(?, 'same.log')",
                    (commander_id,),
                )
            self.assertEqual(con.execute("SELECT COUNT(*) FROM cartography_sales").fetchone()[0], 2)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM journal_imports").fetchone()[0], 2)
        self.assertEqual(len(self.database.biology_for_body(42, 1, self.a)), 1)
        self.assertEqual(len(self.database.biology_for_body(42, 1, self.b)), 1)
        self.assertEqual(len(self.database.geology_for_body(42, 1, self.a)), 1)
        self.assertEqual(len(self.database.recent_system_visits(commander_id=self.a)), 1)

        self.database.store_biology(42, 2, species="Only A", commander_id=self.a)
        self.assertEqual(len(self.database.biology_for_body(42, 2, self.a)), 1)
        self.assertEqual(self.database.biology_for_body(42, 2, self.b), [])

    def test_archive_attribution_persists_only_identified_personal_data(self):
        folder = Path(self.tmp.name) / "journals"
        folder.mkdir()
        base = {"timestamp": "2026-01-01T00:00:00Z"}
        write_journal(folder / "Journal.2026-01-01T000000.01.log", [
            {**base, "event": "Commander", "Name": "Same", "FID": "F-A"},
            {**base, "event": "Location", "StarSystem": "Shared", "SystemAddress": 42},
            {**base, "event": "ScanOrganic", "SystemAddress": 42, "BodyID": 1, "Species_Localised": "A Bio"},
        ])
        write_journal(folder / "Journal.2026-01-01T000100.01.log", [
            {**base, "event": "Location", "StarSystem": "Unknown", "SystemAddress": 43},
            {**base, "event": "ScanOrganic", "SystemAddress": 43, "BodyID": 1, "Species_Localised": "Unknown Bio"},
        ])
        write_journal(folder / "Journal.2026-01-01T000200.01.log", [
            {**base, "event": "Commander", "Name": "Same", "FID": "F-A"},
            {**base, "event": "LoadGame", "Commander": "Same", "FID": "F-B"},
            {**base, "event": "Location", "StarSystem": "Ambiguous", "SystemAddress": 44},
        ])

        self.database.import_journal_archive(folder)
        with self.database._connect() as con:
            self.assertEqual(con.execute("SELECT commander_id, system_address FROM system_visits").fetchall(), [(self.a, 42)])
            self.assertEqual(con.execute("SELECT commander_id, species FROM biology").fetchall(), [(self.a, "A Bio")])
            self.assertEqual(con.execute("SELECT commander_id FROM journal_imports").fetchall(), [(self.a,)])
            statuses = dict(con.execute("SELECT journal_file, attribution_status FROM journal_sessions"))
        self.assertEqual(sorted(statuses.values()), ["ambiguous", "identified", "unknown"])


if __name__ == "__main__":
    unittest.main()
