"""Regression coverage for persisted stays and bounded journal recovery."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.journal_index import scan_journal_folder
from cmdrhelper.journal_reader import read_journal_delta
from cmdrhelper.visits_backfill import backfill_visits


def position(kind, second, address):
    return dict(event=kind, timestamp=f"2026-09-07T12:00:{second:02d}Z",
                SystemAddress=address, StarSystem=f"System {address}",
                StarPos=[address, 2, 3])


class SystemVisitsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.db = CMDRDatabase(self.folder / "test.db")
        self.a = self.db.upsert_commander("FID-A", "Alpha")
        self.b = self.db.upsert_commander("FID-B", "Beta")
        self.path = self.folder / "Journal.2026-09-07T120000.01.log"

    def journal(self, events):
        identity = dict(event="LoadGame", timestamp="2026-09-07T12:00:00Z",
                        FID="FID-A", Commander="Alpha")
        self.path.write_text("".join(json.dumps(e) + "\n" for e in [identity, *events]))
        scan_journal_folder(self.db, self.folder)
        return read_journal_delta(self.path, 0)

    def visits(self, commander=None):
        return self.db.recent_system_visits(100, commander_id=commander or self.a)

    def test_each_position_type_persists_time_identity_and_coordinates(self):
        events, offset = self.journal([position(kind, i, i) for i, kind in
            enumerate(("Location", "FSDJump", "CarrierJump"), 1)])
        self.db.apply_commander_journal_delta(self.a, self.path, events, offset)
        self.assertEqual([r["system_address"] for r in self.visits()], [3, 2, 1])
        for row in self.visits():
            address = row["system_address"]
            self.assertEqual(row["system_name"], f"System {address}")
            self.assertEqual(row["visited_at"], position("Location", address, address)["timestamp"])
            self.assertEqual((row["x"], row["y"], row["z"]), (address, 2, 3))
        self.assertEqual(self.visits(self.b), [])
        self.db.apply_commander_journal_delta(self.a, self.path, events, offset)
        self.assertEqual(len(self.visits()), 3)
        # Replaying overlapping data with a newer offset is also harmless.
        self.db.apply_commander_journal_delta(self.a, self.path, events, offset + 1)
        self.assertEqual(len(self.visits()), 3)

    def test_stays_across_batches_and_true_return(self):
        for i, address in enumerate([1, 1, 1, 2, 1, 1], 1):
            self.db.apply_commander_journal_delta(
                self.a, self.path, [position("Location", i, address)], i)
        self.assertEqual([r["system_address"] for r in self.visits()], [1, 2, 1])
        self.assertEqual([r["visited_at"] for r in self.visits()],
                         [position("Location", i, 1)["timestamp"] for i in [5, 4, 1]])
        self.db.apply_commander_journal_delta(
            self.b, self.folder / "other.log", [position("Location", 2, 1)], 1)
        self.assertEqual(len(self.visits(self.b)), 1)

    def test_visit_failure_rolls_back_location_and_offset(self):
        events, offset = self.journal([position("Location", 1, 1)])
        with patch("cmdrhelper.system_visits.apply_visit_plan", side_effect=RuntimeError("failure")):
            with self.assertRaises(RuntimeError):
                self.db.apply_commander_journal_delta(self.a, self.path, events, offset)
        with self.db._connect() as con:
            self.assertEqual(con.execute("SELECT last_read_offset FROM journal_sessions").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT count(*) FROM commander_locations").fetchone()[0], 0)
        self.assertEqual(self.visits(), [])

    def test_backfill_bounded_idempotent_and_only_visits_changed(self):
        events, offset = self.journal([position("Location", i, a)
                                      for i, a in enumerate([1, 1, 2, 3, 1, 1], 1)])
        with self.db._connect() as con:
            con.execute("UPDATE journal_sessions SET last_read_offset=?", (offset,))
            # Old writer stored repeated Location events, but missed the middle delta.
            for i in [1, 2, 6]:
                e = position("Location", i, 1)
                con.execute("INSERT INTO system_visits(commander_id,system_address,system_name,visited_at) VALUES(?,?,?,?)",
                            (self.a, 1, "System 1", e["timestamp"]))
        with self.path.open("a") as handle:
            handle.write(json.dumps(position("FSDJump", 7, 4)) + "\n")
        preview = backfill_visits(self.db.path, self.a)
        self.assertEqual(len(preview["missing"]), 3)
        self.assertEqual(len(preview["redundant_ids"]), 2)
        self.assertEqual(len(self.visits()), 3)
        result = backfill_visits(self.db.path, self.a, apply=True)
        self.assertEqual(result["inserted"], 3)
        self.assertTrue(Path(result["backup"]).exists())
        self.assertEqual([r["system_address"] for r in reversed(self.visits())], [1, 2, 3, 1])
        second = backfill_visits(self.db.path, self.a, apply=True)
        self.assertEqual((second["inserted"], second["removed"], second["backup"]), (0, 0, None))
        with sqlite3.connect(result["backup"]) as before, self.db._connect() as after:
            for (table,) in before.execute("SELECT name FROM sqlite_master WHERE type='table'"):
                if table not in ("system_visits", "sqlite_sequence"):
                    self.assertEqual(before.execute(f'SELECT * FROM "{table}"').fetchall(),
                                     after.execute(f'SELECT * FROM "{table}"').fetchall(), table)

    def test_backfill_rejects_identity_mismatch_and_truncated_prefix(self):
        _, offset = self.journal([position("Location", 1, 1)])
        with self.db._connect() as con:
            con.execute("UPDATE journal_sessions SET last_read_offset=?", (offset,))
        original = self.path.read_text()
        self.path.write_text(original.replace("FID-A", "FID-B"))
        with self.assertRaisesRegex(ValueError, "identity"):
            backfill_visits(self.db.path, self.a, apply=True)
        self.path.write_text(original[:-1])
        with self.assertRaisesRegex(ValueError, "incomplete"):
            backfill_visits(self.db.path, self.a, apply=True)
        self.assertEqual(self.visits(), [])

    def test_archive_and_reimport_preserve_stays_and_return(self):
        self.journal([position(kind, i, a) for i, (kind, a) in enumerate([
            ("Location", 1), ("Location", 1), ("FSDJump", 2),
            ("CarrierJump", 1), ("Location", 1)], 1)])
        self.db.import_journal_archive(self.folder)
        self.assertEqual([r["system_address"] for r in self.visits()], [1, 2, 1])
        self.db.import_journal_archive(self.folder)
        self.assertEqual(len(self.visits()), 3)
        self.assertEqual(backfill_visits(self.db.path, self.a)["missing"], [])

    def test_older_batch_merges_in_chronological_order(self):
        self.db.store_visit(1, "A", "2026-09-07T12:00:05Z", commander_id=self.a)
        events, offset = self.journal([position("Location", 1, 1), position("FSDJump", 3, 2)])
        self.db.apply_commander_journal_delta(self.a, self.path, events, offset)
        self.assertEqual([r["system_address"] for r in self.visits()], [1, 2, 1])
