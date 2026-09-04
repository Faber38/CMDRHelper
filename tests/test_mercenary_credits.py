from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from cmdrhelper.database import CMDRDatabase


class MercenaryCreditsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = CMDRDatabase(self.root / "test.db")
        self.a = self.db.upsert_commander("FID-A", "Alpha")
        self.b = self.db.upsert_commander("FID-B", "Bravo")

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def snapshot(timestamp="2026-09-04T11:25:39Z", **overrides):
        result = dict(current=1275, total_earned=25, total_spent=220,
                      spent_on_gear=0, spent_on_engineering=220,
                      event_timestamp=timestamp, source_event="Statistics")
        result.update(overrides)
        return result

    def test_complete_snapshot_and_two_commanders_are_separate(self):
        self.db.store_commander_mercenary_credits(self.a, self.snapshot())
        self.db.store_commander_mercenary_credits(
            self.b, self.snapshot(current=7, total_spent=1)
        )
        self.assertEqual(self.db.commander_summary(self.a)["mercenary_credits"], {
            **self.snapshot(),
        })
        self.assertEqual(
            self.db.commander_summary(self.b)["mercenary_credits"]["current"], 7
        )

    def test_partial_snapshot_preserves_missing_values(self):
        self.db.store_commander_mercenary_credits(self.a, self.snapshot())
        self.db.store_commander_mercenary_credits(self.a, {
            "current": 1300, "event_timestamp": "2026-09-05T00:00:00Z",
        })
        stored = self.db.commander_summary(self.a)["mercenary_credits"]
        self.assertEqual(stored["current"], 1300)
        self.assertEqual(stored["total_earned"], 25)
        self.assertEqual(stored["spent_on_engineering"], 220)

    def test_older_snapshot_does_not_overwrite_newer(self):
        self.db.store_commander_mercenary_credits(self.a, self.snapshot())
        self.assertFalse(self.db.store_commander_mercenary_credits(
            self.a, self.snapshot("2026-09-03T00:00:00Z", current=1)
        ))
        self.assertEqual(
            self.db.commander_summary(self.a)["mercenary_credits"]["current"], 1275
        )

    def _session(self, name, status, commander_id, events):
        path = self.root / name
        path.write_text("".join(json.dumps(event) + "\n" for event in events),
                        encoding="utf-8")
        size = path.stat().st_size
        with self.db._connect() as con:
            con.execute("""INSERT INTO journal_sessions(
                journal_file,commander_id,attribution_status,file_size,modified_ns,
                last_read_offset,last_complete_line_offset)
                VALUES(?,?,?,?,0,?,?)""",
                (str(path), commander_id, status, size, size, size))
        return {"journal_file": str(path), "commander_id": commander_id,
                "attribution_status": status}

    def test_backfill_is_idempotent_and_ignores_unknown_ambiguous(self):
        stats = {"timestamp": "2026-09-04T11:25:39Z", "event": "Statistics",
                 "Bank_Account": {
                     "MercCoins_Current": 1275, "MercCoins_Total_Earned": 25,
                     "MercCoins_Total_Spent": 220,
                     "MercCoins_Spent_On_MercGear": 0,
                     "MercCoins_Spent_On_Engineering": 220,
                 }}
        identified = self._session("identified.log", "identified", self.a, [stats])
        unknown = self._session("unknown.log", "unknown", None, [
            {**stats, "Bank_Account": {"MercCoins_Current": 9999}}
        ])
        ambiguous = self._session("ambiguous.log", "ambiguous", None, [
            {**stats, "Bank_Account": {"MercCoins_Current": 8888}}
        ])
        before = sqlite3.connect(self.db.path).execute(
            "SELECT last_read_offset FROM journal_sessions WHERE journal_file=?",
            (identified["journal_file"],),
        ).fetchone()[0]
        first = self.db.backfill_mercenary_credits(
            self.a, [identified, unknown, ambiguous]
        )
        second = self.db.backfill_mercenary_credits(
            self.a, [identified, unknown, ambiguous]
        )
        self.assertFalse(first["skipped"])
        self.assertTrue(second["skipped"])
        self.assertEqual(
            self.db.commander_summary(self.a)["mercenary_credits"]["current"], 1275
        )
        after = sqlite3.connect(self.db.path).execute(
            "SELECT last_read_offset FROM journal_sessions WHERE journal_file=?",
            (identified["journal_file"],),
        ).fetchone()[0]
        self.assertEqual(after, before)

    def test_live_statistics_snapshot_is_imported(self):
        path = self.root / "live.log"
        path.write_text("", encoding="utf-8")
        with self.db._connect() as con:
            con.execute("""INSERT INTO journal_sessions(
                journal_file,commander_id,attribution_status,last_read_offset)
                VALUES(?,?,'identified',0)""", (str(path), self.a))
        event = {"timestamp": "2026-09-04T11:25:39Z", "event": "Statistics",
                 "Bank_Account": {"MercCoins_Current": 1275}}
        self.db.apply_commander_journal_delta(self.a, str(path), [event], 10)
        self.assertEqual(
            self.db.commander_summary(self.a)["mercenary_credits"]["current"], 1275
        )

    def test_live_statistics_from_non_identified_session_is_ignored(self):
        event = {"timestamp": "2026-09-04T11:25:39Z", "event": "Statistics",
                 "Bank_Account": {"MercCoins_Current": 1275}}
        for status in ("unknown", "ambiguous"):
            path = self.root / f"{status}-live.log"
            path.write_text("", encoding="utf-8")
            with self.db._connect() as con:
                con.execute("""INSERT INTO journal_sessions(
                    journal_file,commander_id,attribution_status,last_read_offset)
                    VALUES(?,?,?,0)""", (str(path), self.a, status))
            self.db.apply_commander_journal_delta(self.a, str(path), [event], 10)
        self.assertIsNone(self.db.commander_summary(self.a)["mercenary_credits"])


if __name__ == "__main__":
    unittest.main()
