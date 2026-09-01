from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from cmdrhelper.database import CMDRDatabase, SCHEMA_VERSION
from cmdrhelper.journal_reader import classify_journal_file, read_latest_state


def write_journal(folder: Path, name: str, events: list[dict]) -> Path:
    path = folder / name
    path.write_text(
        "".join(json.dumps(event) + "\n" for event in events),
        encoding="utf-8",
    )
    return path


def identity_event(event="Commander", fid="F-A", name="Alpha", second=0):
    data = {
        "timestamp": f"2026-01-01T00:00:{second:02d}Z",
        "event": event,
        "FID": fid,
    }
    data["Name" if event == "Commander" else "Commander"] = name
    return data


class JournalClassificationTests(unittest.TestCase):
    def test_commander_and_load_game_identify_a_session(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            commander = classify_journal_file(write_journal(
                folder, "Journal.2026-01-01T000000.01.log",
                [identity_event()],
            ))
            load_game = classify_journal_file(write_journal(
                folder, "Journal.2026-01-01T000100.01.log",
                [identity_event("LoadGame", "F-B", "Bravo")],
            ))

        self.assertEqual(
            (commander["attribution_status"], commander["fid_seen"]),
            ("identified", "F-A"),
        )
        self.assertEqual(
            (load_game["attribution_status"], load_game["fid_seen"]),
            ("identified", "F-B"),
        )

    def test_same_fid_and_renamed_commander_remains_identified(self):
        with tempfile.TemporaryDirectory() as directory:
            session = classify_journal_file(write_journal(
                Path(directory), "Journal.2026-01-01T000000.01.log",
                [
                    identity_event(name="Old Name"),
                    identity_event("LoadGame", name="New Name", second=1),
                ],
            ))

        self.assertEqual(session["attribution_status"], "identified")
        self.assertEqual(session["fids_seen"], ["F-A"])
        self.assertEqual(session["commander_name_seen"], "New Name")

    def test_missing_fid_or_identity_event_is_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            no_fid = classify_journal_file(write_journal(
                folder, "Journal.2026-01-01T000000.01.log",
                [{"timestamp": "2026-01-01T00:00:00Z", "event": "Commander", "Name": "Alpha"}],
            ))
            no_identity = classify_journal_file(write_journal(
                folder, "Journal.2026-01-01T000100.01.log",
                [{"timestamp": "2026-01-01T00:01:00Z", "event": "Fileheader"}],
            ))

        self.assertEqual(no_fid["attribution_status"], "unknown")
        self.assertIsNone(no_fid["fid_seen"])
        self.assertEqual(no_identity["attribution_status"], "unknown")

    def test_two_different_fids_in_one_file_are_ambiguous(self):
        with tempfile.TemporaryDirectory() as directory:
            session = classify_journal_file(write_journal(
                Path(directory), "Journal.2026-01-01T000000.01.log",
                [identity_event(fid="F-A"), identity_event(fid="F-B", second=1)],
            ))

        self.assertEqual(session["attribution_status"], "ambiguous")
        self.assertEqual(session["fids_seen"], ["F-A", "F-B"])
        self.assertIsNone(session["fid_seen"])
        self.assertIsNone(session["commander_id"])

    def test_identity_is_not_inherited_across_file_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            first = write_journal(
                folder, "Journal.2026-01-01T000000.01.log", [identity_event()]
            )
            second = write_journal(
                folder, "Journal.2026-01-01T000100.01.log",
                [{
                    "timestamp": "2026-01-01T00:01:00Z",
                    "event": "Commander",
                    "Name": "Unverified Name",
                }],
            )
            first_session = classify_journal_file(first)
            second_session = classify_journal_file(second)
            state = read_latest_state(folder)

        self.assertEqual(first_session["attribution_status"], "identified")
        self.assertEqual(second_session["attribution_status"], "unknown")
        self.assertEqual(
            state["latest_journal_session"]["attribution_status"], "unknown"
        )
        # Die letzte eindeutige Live-Identität bleibt separat erhalten.
        self.assertEqual(state["commander_fid"], "F-A")
        self.assertEqual(state["commander"], "Alpha")

    def test_two_files_with_different_fids_remain_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            first = write_journal(
                folder, "Journal.2026-01-01T000000.01.log",
                [identity_event(fid="F-A", name="Same Name")],
            )
            second = write_journal(
                folder, "Journal.2026-01-01T000100.01.log",
                [identity_event(fid="F-B", name="Same Name")],
            )
            sessions = [classify_journal_file(first), classify_journal_file(second)]
            state = read_latest_state(folder)

        self.assertEqual([item["fid_seen"] for item in sessions], ["F-A", "F-B"])
        self.assertEqual(state["commander_fid"], "F-B")


class JournalSessionDatabaseTests(unittest.TestCase):
    def test_identified_sessions_resolve_commanders_by_fid(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            database = CMDRDatabase(folder / "test.db")
            first = classify_journal_file(write_journal(
                folder, "Journal.2026-01-01T000000.01.log",
                [identity_event(name="Old Name")],
            ))
            second = classify_journal_file(write_journal(
                folder, "Journal.2026-01-01T000100.01.log",
                [identity_event("LoadGame", name="New Name")],
            ))
            database.store_journal_session(first)
            database.store_journal_session(second)

            with database._connect() as con:
                commanders = con.execute(
                    "SELECT id, fid, current_name FROM commanders"
                ).fetchall()
                session_ids = con.execute(
                    "SELECT commander_id FROM journal_sessions ORDER BY journal_file"
                ).fetchall()

        self.assertEqual(len(commanders), 1)
        self.assertEqual(commanders[0][1:], ("F-A", "New Name"))
        self.assertEqual(session_ids, [(commanders[0][0],), (commanders[0][0],)])

    def test_unknown_and_ambiguous_never_get_commander_assignment(self):
        with tempfile.TemporaryDirectory() as directory:
            database = CMDRDatabase(Path(directory) / "test.db")
            for status in ("unknown", "ambiguous"):
                database.store_journal_session({
                    "journal_file": f"{status}.log",
                    "attribution_status": status,
                    "fid_seen": "SHOULD-NOT-BE-USED",
                    "commander_name_seen": "Name",
                })

            with database._connect() as con:
                sessions = con.execute(
                    "SELECT commander_id, fid_seen, commander_name_seen "
                    "FROM journal_sessions ORDER BY journal_file"
                ).fetchall()
                commander_count = con.execute("SELECT COUNT(*) FROM commanders").fetchone()[0]

        self.assertEqual(sessions, [(None, None, None), (None, None, None)])
        self.assertEqual(commander_count, 0)

    def test_v1_to_v2_migration_is_additive_and_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "v1.db"
            database = CMDRDatabase(path)
            with database._connect() as con:
                con.execute("INSERT INTO systems (system_address, name) VALUES (42, 'Kept')")
                con.execute(
                    "INSERT INTO commanders (fid, current_name) VALUES ('F-KEPT', 'Kept')"
                )
                con.execute("DROP TABLE journal_sessions")
                con.execute("PRAGMA user_version = 1")

            CMDRDatabase(path)
            CMDRDatabase(path)

            with sqlite3.connect(path) as con:
                self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
                self.assertEqual(
                    con.execute("SELECT system_address, name FROM systems").fetchall(),
                    [(42, "Kept")],
                )
                self.assertEqual(
                    con.execute("SELECT COUNT(*) FROM journal_sessions").fetchone()[0], 0
                )
                self.assertEqual(
                    con.execute("SELECT fid, current_name FROM commanders").fetchall(),
                    [("F-KEPT", "Kept")],
                )
                foreign_keys = con.execute(
                    "PRAGMA foreign_key_list(journal_sessions)"
                ).fetchall()
                self.assertTrue(any(row[2] == "commanders" for row in foreign_keys))


if __name__ == "__main__":
    unittest.main()
