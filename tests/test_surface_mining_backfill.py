import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cmdrhelper.database import CMDRDatabase


def event(kind, second, **values):
    return {"timestamp": f"2026-09-03T14:00:{second:02d}Z", "event": kind, **values}


def mining_events(body_id=3, address=18229955074546, copper=1):
    return [
        event("ApproachBody", 0, StarSystem="Prua Hypai NV-E c28-66",
              SystemAddress=address, Body="Prua Hypai NV-E c28-66 2", BodyID=body_id),
        event("LaunchSRV", 1, SRVType="mev_rhino"),
        event("MaterialCollected", 2, Category="Raw", Name="sulphur",
              Name_Localised="Schwefel", Count=7),
        *[event("MiningRefined", 3, Type="$copper_name;",
                Type_Localised="Kupfer") for _ in range(copper)],
        event("DockSRV", 4, SRVType="mev_rhino"),
    ]


class SurfaceMiningBackfillTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.db = CMDRDatabase(self.root / "test.db")
        self.a = self.db.upsert_commander("FID-A", "Alpha")
        self.b = self.db.upsert_commander("FID-B", "Bravo")

    def tearDown(self):
        self.tmp.cleanup()

    def journal(self, name, events, fid="FID-A", status="identified", limit=None):
        path = self.root / name
        chunks = [(json.dumps(item) + "\n").encode() for item in events]
        path.write_bytes(b"".join(chunks))
        offset = sum(len(item) for item in chunks) if limit is None else int(limit)
        session = {
            "journal_file": str(path), "attribution_status": status,
            "fid_seen": fid, "commander_name_seen": fid,
            "file_size": path.stat().st_size, "modified_ns": path.stat().st_mtime_ns,
            "last_read_offset": offset, "last_complete_line_offset": offset,
            "last_indexed_at": "2026-09-03T15:00:00Z",
        }
        self.db.store_journal_session(session)
        with self.db._connect() as con:
            row = con.execute("SELECT commander_id FROM journal_sessions WHERE journal_file=?",
                              (str(path),)).fetchone()
        session["commander_id"] = row[0]
        return path, session, chunks

    def test_historical_backfill_is_idempotent_bounded_and_preserves_offset(self):
        inside = mining_events(copper=56)
        outside = [event("MiningRefined", 9, Type="$copper_name;",
                         Type_Localised="Kupfer")]
        all_events = inside + outside
        limit = sum(len((json.dumps(item) + "\n").encode()) for item in inside)
        path, session, _ = self.journal("a.log", all_events, limit=limit)

        first = self.db.backfill_surface_mining(self.a, [session])
        self.assertEqual(first, {"skipped": False, "journals": 1, "events": 57})
        result = self.db.surface_mining_for_body(18229955074546, 3, self.a)
        self.assertEqual(result["commodities"][0]["quantity"], 56)
        self.assertEqual(result["materials"][0]["quantity"], 7)
        with self.db._connect() as con:
            self.assertEqual(con.execute(
                "SELECT last_read_offset FROM journal_sessions WHERE journal_file=?",
                (str(path),)).fetchone()[0], limit)
            self.assertEqual(con.execute(
                "SELECT revision FROM commander_state_repairs WHERE commander_id=? "
                "AND feature='surface_mining'", (self.a,)).fetchone()[0], 1)

        second = self.db.backfill_surface_mining(self.a, [session])
        self.assertEqual(second, {"skipped": True, "journals": 0, "events": 0})
        self.assertEqual(self.db.surface_mining_for_body(
            18229955074546, 3, self.a)["commodities"][0]["quantity"], 56)

        # New live data after the historical watermark adds normally.
        with self.db._connect() as con:
            con.execute("UPDATE journal_sessions SET last_read_offset=? WHERE journal_file=?",
                        (limit, str(path)))
        self.db.apply_commander_journal_delta(
            self.a, path, mining_events(copper=1), path.stat().st_size + 100
        )
        self.assertEqual(self.db.surface_mining_for_body(
            18229955074546, 3, self.a)["commodities"][0]["quantity"], 57)

    def test_already_processed_events_are_not_counted_twice(self):
        events = mining_events(copper=2)
        path, session, _ = self.journal("processed.log", events, limit=0)
        final_offset = path.stat().st_size
        self.db.apply_commander_journal_delta(self.a, path, events, final_offset)
        session["last_read_offset"] = final_offset
        result = self.db.backfill_surface_mining(self.a, [session])
        self.assertFalse(result["skipped"])
        self.assertEqual(result["events"], 0)
        self.assertEqual(self.db.surface_mining_for_body(
            18229955074546, 3, self.a)["commodities"][0]["quantity"], 2)

    def test_unknown_ambiguous_and_commanders_are_separate(self):
        _, a_session, _ = self.journal("a.log", mining_events(copper=2), fid="FID-A")
        _, b_session, _ = self.journal("b.log", mining_events(copper=3), fid="FID-B")
        _, unknown, _ = self.journal("unknown.log", mining_events(copper=9),
                                     fid="", status="unknown")
        _, ambiguous, _ = self.journal("ambiguous.log", mining_events(copper=9),
                                       fid="FID-A", status="ambiguous")
        sessions = [a_session, b_session, unknown, ambiguous]
        self.db.backfill_surface_mining(self.a, sessions)
        self.db.backfill_surface_mining(self.b, sessions)
        self.assertEqual(self.db.surface_mining_for_body(
            18229955074546, 3, self.a)["commodities"][0]["quantity"], 2)
        self.assertEqual(self.db.surface_mining_for_body(
            18229955074546, 3, self.b)["commodities"][0]["quantity"], 3)
        self.assertFalse(self.db.commander_state_repair_needed(self.a, "surface_mining"))
        self.assertFalse(self.db.commander_state_repair_needed(self.b, "surface_mining"))

    def test_failure_rolls_back_data_and_marker_without_moving_offset(self):
        path, session, _ = self.journal("failure.log", mining_events(copper=2))
        offset = session["last_read_offset"]
        original = self.db._record_surface_mining_event
        calls = 0

        def fail_second(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise RuntimeError("db")
            return original(*args, **kwargs)

        with patch.object(self.db, "_record_surface_mining_event", side_effect=fail_second):
            with self.assertRaises(RuntimeError):
                self.db.backfill_surface_mining(self.a, [session])
        with self.db._connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM surface_mining_commodities").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM surface_mining_materials").fetchone()[0], 0)
            self.assertIsNone(con.execute(
                "SELECT revision FROM commander_state_repairs WHERE commander_id=? "
                "AND feature='surface_mining'", (self.a,)).fetchone())
            self.assertEqual(con.execute(
                "SELECT last_read_offset FROM journal_sessions WHERE journal_file=?",
                (str(path),)).fetchone()[0], offset)


if __name__ == "__main__":
    unittest.main()
