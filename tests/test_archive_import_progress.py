"""Archive progress must be independent of the journal index's progress."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.journal_index import scan_journal_folder
from cmdrhelper.journal_reader import read_journal_delta


def position(kind, second, address):
    return dict(event=kind, timestamp=f"2026-09-09T00:00:{second:02d}Z",
                SystemAddress=address, StarSystem=f"Archive {address}",
                StarPos=[address, 2, 3])


class ArchiveImportProgressTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.db = CMDRDatabase(self.folder / "archive.db")
        self.commander = self.db.upsert_commander("FID-A", "Alpha")
        self.other = self.db.upsert_commander("FID-B", "Beta")
        self.db.active_commander_id = self.commander
        self.path = self.folder / "Journal.2026-09-09T000000.01.log"
        self.append([
            dict(event="LoadGame", timestamp="2026-09-09T00:00:00Z",
                 FID="FID-A", Commander="Alpha"),
            position("Location", 1, 1),
            dict(event="Scan", timestamp="2026-09-09T00:00:02Z",
                 SystemAddress=1, BodyID=0, BodyName="Archive 1 A", StarType="K"),
        ])
        self.assertEqual(self.db.import_journal_archive(self.folder)["imported_journals"], 1)
        self.original_mark = self.marker()
        self.assertEqual(self.session()["fully_imported"], 1)

    def append(self, events, path=None):
        with (path or self.path).open("a", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(event) + "\n")

    def marker(self):
        with self.db._connect() as con:
            return con.execute(
                "SELECT file_size,modified_ns,last_import FROM journal_imports "
                "WHERE commander_id=? AND journal_file=?",
                (self.commander, str(self.path)),
            ).fetchone()

    def session(self):
        with self.db._connect() as con:
            con.row_factory = sqlite3.Row
            return dict(con.execute("SELECT * FROM journal_sessions WHERE journal_file=?",
                                    (str(self.path),)).fetchone())

    def personal_systems(self, commander=None):
        with self.db._connect() as con:
            return [r[0] for r in con.execute(
                "SELECT system_address FROM commander_systems WHERE commander_id=? "
                "ORDER BY system_address", (commander or self.commander,),
            )]

    def snapshot(self):
        with self.db._connect() as con:
            return {table: con.execute(f"SELECT * FROM {table} ORDER BY 1,2").fetchall()
                    for table in ("systems", "bodies", "commander_systems",
                                  "commander_bodies", "system_visits", "journal_imports")}

    def preindex_append(self, events):
        self.append(events)
        scan_journal_folder(self.db, self.folder)
        session, = scan_journal_folder(self.db, self.folder)
        self.assertTrue(session["unchanged"])
        self.assertFalse(session["fully_imported"])
        self.assertEqual(self.marker(), self.original_mark)
        self.assertLess(self.marker()[0], self.path.stat().st_size)

    def assert_imported_append(self, kind):
        self.preindex_append([position(kind, 3, 2)])
        result = self.db.import_journal_archive(self.folder)
        self.assertEqual(result["imported_journals"], 1)
        self.assertEqual(self.personal_systems(), [1, 2])
        self.assertEqual(self.personal_systems(self.other), [])
        visits = self.db.recent_system_visits(commander_id=self.commander)
        self.assertEqual([r["system_address"] for r in visits], [2, 1])
        self.assertEqual((visits[0]["x"], visits[0]["y"], visits[0]["z"]), (2, 2, 3))
        self.assertEqual(self.marker()[:2],
                         (self.path.stat().st_size, self.path.stat().st_mtime_ns))
        self.assertEqual(self.session()["fully_imported"], 1)
        self.assertEqual(self.session()["commander_id"], self.commander)
        before = self.snapshot()
        self.assertEqual(self.db.import_journal_archive(self.folder)["imported_journals"], 0)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.session()["fully_imported"], 1)

    def test_preindexed_location_after_partial_archive_import(self):
        self.assert_imported_append("Location")

    def test_preindexed_fsd_jump_after_partial_archive_import(self):
        self.assert_imported_append("FSDJump")

    def test_preindexed_carrier_jump_after_partial_archive_import(self):
        self.assert_imported_append("CarrierJump")

    def test_existing_live_visits_are_not_duplicated_by_archive_replay(self):
        self.preindex_append([position("FSDJump", 3, 2), position("CarrierJump", 4, 1)])
        events, offset = read_journal_delta(self.path, 0)
        self.db.apply_commander_journal_delta(self.commander, self.path, events, offset)
        before = self.db.recent_system_visits(commander_id=self.commander)
        self.assertEqual([r["system_address"] for r in before], [1, 2, 1])
        self.assertEqual(self.db.import_journal_archive(self.folder)["imported_journals"], 1)
        self.assertEqual(self.db.recent_system_visits(commander_id=self.commander), before)
        self.assertEqual(self.personal_systems(), [1, 2])

    def test_failed_write_does_not_advance_archive_marker(self):
        self.preindex_append([position("FSDJump", 3, 2)])
        with self.db._connect() as con:
            con.execute("""CREATE TRIGGER reject_new_system BEFORE INSERT ON systems
                           WHEN NEW.system_address=2
                           BEGIN SELECT RAISE(ABORT, 'test failure'); END""")
        before = self.snapshot()
        with self.assertRaisesRegex(sqlite3.IntegrityError, "test failure"):
            self.db.import_journal_archive(self.folder)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.session()["fully_imported"], 0)
        with self.db._connect() as con:
            con.execute("DROP TRIGGER reject_new_system")
        self.assertEqual(self.db.import_journal_archive(self.folder)["imported_journals"], 1)
        self.assertEqual(self.personal_systems(), [1, 2])
        self.assertEqual(self.session()["fully_imported"], 1)

    def test_foreign_session_stays_with_its_own_commander(self):
        foreign = self.folder / "Journal.2026-09-09T010000.01.log"
        self.append([dict(event="LoadGame", timestamp="2026-09-09T01:00:00Z",
                          FID="FID-B", Commander="Beta"), position("Location", 3, 20)], foreign)
        self.db.import_journal_archive(self.folder)
        self.append([position("CarrierJump", 4, 21)], foreign)
        scan_journal_folder(self.db, self.folder)
        self.assertEqual(self.db.import_journal_archive(self.folder)["imported_journals"], 1)
        self.assertEqual(self.personal_systems(), [1])
        self.assertEqual(self.personal_systems(self.other), [20, 21])
        with self.db._connect() as con:
            self.assertEqual(con.execute(
                "SELECT commander_id FROM journal_imports WHERE journal_file=?",
                (str(foreign),),
            ).fetchall(), [(self.other,)])

    def test_ambiguous_extension_is_not_assigned_or_marked_imported(self):
        self.preindex_append([
            dict(event="Commander", timestamp="2026-09-09T00:00:03Z",
                 FID="FID-B", Name="Beta"), position("FSDJump", 4, 2),
        ])
        self.db.import_journal_archive(self.folder)
        self.assertEqual(self.session()["attribution_status"], "ambiguous")
        self.assertEqual(self.session()["fully_imported"], 0)
        self.assertEqual(self.marker(), self.original_mark)
        self.assertEqual(self.personal_systems(), [1])
        self.assertEqual(self.personal_systems(self.other), [])
        self.assertEqual(len(self.db.recent_system_visits(commander_id=self.commander)), 1)

    def test_unknown_session_has_no_personal_data_or_archive_marker(self):
        unknown = self.folder / "Journal.2026-09-09T020000.01.log"
        self.append([position("Location", 3, 30)], unknown)
        scan_journal_folder(self.db, self.folder)
        self.db.import_journal_archive(self.folder)
        self.assertEqual(self.personal_systems(), [1])
        self.assertEqual(self.personal_systems(self.other), [])
        with self.db._connect() as con:
            self.assertEqual(con.execute(
                "SELECT attribution_status,commander_id,fully_imported FROM journal_sessions "
                "WHERE journal_file=?", (str(unknown),),
            ).fetchone(), ("unknown", None, 0))
            self.assertEqual(con.execute("SELECT * FROM journal_imports WHERE journal_file=?",
                                         (str(unknown),)).fetchall(), [])


if __name__ == "__main__":
    unittest.main()
