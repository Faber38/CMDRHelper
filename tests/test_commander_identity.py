from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from cmdrhelper.database import CMDRDatabase, SCHEMA_VERSION
from cmdrhelper.journal_reader import read_latest_state


class CommanderSchemaTests(unittest.TestCase):
    def test_legacy_database_is_extended_without_changing_existing_data(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.db"
            with sqlite3.connect(path) as con:
                con.execute(
                    "CREATE TABLE systems (system_address INTEGER PRIMARY KEY, name TEXT)"
                )
                con.execute("INSERT INTO systems VALUES (42, 'Test System')")

            CMDRDatabase(path)

            with sqlite3.connect(path) as con:
                self.assertEqual(
                    con.execute("SELECT system_address, name FROM systems").fetchall(),
                    [(42, "Test System")],
                )
                self.assertEqual(
                    con.execute("PRAGMA user_version").fetchone()[0],
                    SCHEMA_VERSION,
                )
                columns = {
                    row[1] for row in con.execute("PRAGMA table_info(commanders)")
                }
                self.assertEqual(
                    columns,
                    {"id", "fid", "current_name", "first_seen", "last_seen"},
                )

                for table in ("systems", "bodies", "materials"):
                    table_columns = {
                        row[1]
                        for row in con.execute(f"PRAGMA table_info({table})")
                    }
                    self.assertNotIn("commander_id", table_columns)

                for table in (
                    "biology", "geology", "system_visits", "codex_entries",
                    "cartography_sales", "journal_imports",
                    "bio_value_journal_scans", "cartography_value_journal_scans",
                ):
                    table_columns = {
                        row[1]
                        for row in con.execute(f"PRAGMA table_info({table})")
                    }
                    self.assertIn("commander_id", table_columns)

            # Wiederholtes Öffnen ist eine sichere No-op-Migration.
            CMDRDatabase(path)
            with sqlite3.connect(path) as con:
                self.assertEqual(
                    con.execute("SELECT system_address, name FROM systems").fetchall(),
                    [(42, "Test System")],
                )

    def test_fid_is_unique_and_name_is_updated(self):
        with tempfile.TemporaryDirectory() as directory:
            database = CMDRDatabase(Path(directory) / "identity.db")
            first_id = database.upsert_commander("F123", "Old Name", "2026-01-01T00:00:00Z")
            second_id = database.upsert_commander("F123", "New Name", "2026-02-01T00:00:00Z")

            self.assertEqual(first_id, second_id)
            with database._connect() as con:
                rows = con.execute(
                    "SELECT fid, current_name, first_seen, last_seen FROM commanders"
                ).fetchall()
            self.assertEqual(
                rows,
                [("F123", "New Name", "2026-01-01T00:00:00Z", "2026-02-01T00:00:00Z")],
            )

    def test_same_name_with_different_fids_creates_two_commanders(self):
        with tempfile.TemporaryDirectory() as directory:
            database = CMDRDatabase(Path(directory) / "identity.db")
            first_id = database.upsert_commander("F-A", "Same Name")
            second_id = database.upsert_commander("F-B", "Same Name")
            self.assertNotEqual(first_id, second_id)
            with database._connect() as con:
                self.assertEqual(con.execute("SELECT COUNT(*) FROM commanders").fetchone()[0], 2)

    def test_empty_fid_does_not_create_commander(self):
        with tempfile.TemporaryDirectory() as directory:
            database = CMDRDatabase(Path(directory) / "identity.db")
            self.assertIsNone(database.upsert_commander("", "Name"))
            with database._connect() as con:
                self.assertEqual(con.execute("SELECT COUNT(*) FROM commanders").fetchone()[0], 0)


class JournalIdentityTests(unittest.TestCase):
    def _read_events(self, events):
        with tempfile.TemporaryDirectory() as directory:
            journal = Path(directory) / "Journal.2026-01-01T000000.01.log"
            journal.write_text(
                "".join(json.dumps(event) + "\n" for event in events),
                encoding="utf-8",
            )
            return read_latest_state(Path(directory))

    def test_commander_event_exposes_fid(self):
        data = self._read_events([{
            "timestamp": "2026-01-01T00:00:00Z", "event": "Commander",
            "Name": "Alpha", "FID": "F-A",
        }])
        self.assertEqual((data["commander"], data["commander_fid"]), ("Alpha", "F-A"))

    def test_load_game_event_exposes_fid(self):
        data = self._read_events([{
            "timestamp": "2026-01-01T00:00:00Z", "event": "LoadGame",
            "Commander": "Bravo", "FID": "F-B",
        }])
        self.assertEqual((data["commander"], data["commander_fid"]), ("Bravo", "F-B"))

    def test_event_without_fid_does_not_expose_identity(self):
        data = self._read_events([{
            "timestamp": "2026-01-01T00:00:00Z", "event": "LoadGame",
            "Commander": "No Fid",
        }])
        self.assertEqual(data["commander_fid"], "")


class AppStateIdentityTests(unittest.TestCase):
    def _state(self):
        # Die Identitätsmethode benötigt bewusst nur diese Laufzeitfelder.
        try:
            from cmdrhelper.state import AppState
        except ModuleNotFoundError as exc:
            if exc.name != "PySide6":
                raise

            class DummySignal:
                def __init__(self, *args):
                    pass

            class DummyQObject:
                pass

            class DummyQSettings:
                pass

            class DummyQTimer:
                pass

            qtcore = types.ModuleType("PySide6.QtCore")
            qtcore.Signal = DummySignal
            qtcore.QObject = DummyQObject
            qtcore.QSettings = DummyQSettings
            qtcore.QTimer = DummyQTimer
            pyside = types.ModuleType("PySide6")
            pyside.QtCore = qtcore
            sys.modules["PySide6"] = pyside
            sys.modules["PySide6.QtCore"] = qtcore
            from cmdrhelper.state import AppState

        state = SimpleNamespace()
        state.database = Mock()
        state.database.upsert_commander.side_effect = [1, 1, 2]
        state.commander_id = None
        state.commander_fid = ""
        state.commanderIdentityChanged = Mock()
        state._apply_commander_identity = AppState._apply_commander_identity.__get__(state)
        state._store_latest_journal_session = (
            AppState._store_latest_journal_session.__get__(state)
        )
        return state

    def test_fid_switch_is_detected_but_name_change_is_not(self):
        state = self._state()
        state._apply_commander_identity({
            "commander_fid": "F-A", "commander_identity_name": "Alpha"
        })
        state._apply_commander_identity({
            "commander_fid": "F-A", "commander_identity_name": "Alpha Renamed"
        })
        state._apply_commander_identity({
            "commander_fid": "F-B", "commander_identity_name": "Bravo"
        })

        self.assertEqual(state.commanderIdentityChanged.emit.call_count, 2)
        self.assertEqual(state.commander_id, 2)
        self.assertEqual(state.commander_fid, "F-B")

    def test_missing_fid_does_not_change_active_identity(self):
        state = self._state()
        state._apply_commander_identity({"commander": "Name only"})
        state.database.upsert_commander.assert_not_called()
        self.assertEqual(state.commander_fid, "")

    def test_unknown_historical_session_does_not_clear_live_commander(self):
        state = self._state()
        state._apply_commander_identity({
            "commander_fid": "F-A", "commander_identity_name": "Alpha"
        })
        state._store_latest_journal_session({
            "latest_journal_session": {
                "journal_file": "unknown.log",
                "attribution_status": "unknown",
            }
        })

        self.assertEqual(state.commander_id, 1)
        self.assertEqual(state.commander_fid, "F-A")
        state.database.store_journal_session.assert_called_once()


if __name__ == "__main__":
    unittest.main()
