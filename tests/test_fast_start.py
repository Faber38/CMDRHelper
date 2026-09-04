from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QObject

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.route_planner.models import ShipLoadoutData
from cmdrhelper.state import AppState


class _WatcherStub:
    def __init__(self, current):
        self._current = current


class FastStartCommanderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.db = CMDRDatabase(self.folder / "state.db")
        self.alpha = self.db.upsert_commander("FID-A", "Alpha")
        self.bravo = self.db.upsert_commander("FID-B", "Bravo")
        self.db.store_commander_location(self.bravo, {
            "system_name": "Colonia",
            "system_address": 42,
            "station_name": "Jaques Station",
            "body_name": "",
            "event_timestamp": "2026-01-01T00:00:00Z",
            "event_type": "Location",
        })
        self.db.store_commander_ship(
            self.bravo,
            ShipLoadoutData(
                ship_id=51,
                ship_type="lakonminer",
                ship_name="Erft-Büffel",
                loadout_complete=True,
                loadout_stale=False,
            ),
            "2026-01-01T00:00:00Z",
        )
        self.db.store_commander_missions(self.bravo, [{
            "mission_id": 7,
            "name": "Fast start mission",
            "status": "Angenommen",
        }])
        with self.db._connect() as con:
            con.execute("""
                INSERT INTO commander_unsold_biology(
                    commander_id,system_address,body_id,genus,species,variant,
                    scan_type,estimated_base_value)
                VALUES(?,?,?,?,?,?,?,?)
            """, (self.bravo, 42, 1, "Genus", "Species", "Variant",
                  "Analyse", 1000))
            con.execute("""
                INSERT INTO commander_unsold_cartography(
                    commander_id,system_address,body_id,system_name,body_name,
                    estimated_value,raw_estimated_value)
                VALUES(?,?,?,?,?,?,?)
            """, (self.bravo, 42, 1, "Colonia", "Colonia 1", 2000, 2000))

    def tearDown(self):
        self.temp.cleanup()

    def state(self, sessions):
        state = AppState.__new__(AppState)
        QObject.__init__(state)
        state.database = self.db
        state._journal_index_sessions = list(sessions)
        state._journal_index_current = (
            str(sessions[-1]["journal_file"]) if sessions else None
        )
        state.commander = ""
        state.commander_id = None
        state.commander_fid = ""
        state.viewed_commander_id = None
        state._viewed_commander_user_selected = False
        state.system = ""
        state.system_address = None
        state.station = ""
        state.body = ""
        state.ship = ""
        state.ship_loadout = ShipLoadoutData()
        state.last_timestamp = ""
        state.missions = []
        state.mission_reset_at = None
        state.journal_files = 0
        state.connected = False
        state.unsold_cartography_value = 0
        state.unsold_cartography_count = 0
        state.unsold_bio_value = 0
        state.unsold_bio_first_logged_value = 0
        state.unsold_bio_count = 0
        state.unsold_bio_unknown = []
        state._last_refresh_error = ""
        return state

    def sessions(self, current_path=None):
        first = self.folder / "Journal.2026-01-01T000000.01.log"
        second = current_path or self.folder / "Journal.2026-01-01T000100.01.log"
        return [
            {
                "journal_file": str(first),
                "commander_id": self.alpha,
                "fid_seen": "FID-A",
                "commander_name_seen": "Alpha",
                "attribution_status": "identified",
                "last_read_offset": 0,
            },
            {
                "journal_file": str(second),
                "commander_id": self.bravo,
                "fid_seen": "FID-B",
                "commander_name_seen": "Bravo",
                "attribution_status": "identified",
                "last_read_offset": 0,
            },
        ]

    def test_index_baseline_restores_latest_commander_without_delta_events(self):
        sessions = self.sessions()
        # Eine neuere unbekannte Datei darf die letzte belegte Identität nicht
        # verdrängen.
        sessions.append({
            "journal_file": str(self.folder / "Journal.2026-01-01T000200.01.log"),
            "commander_id": None,
            "fid_seen": None,
            "commander_name_seen": None,
            "attribution_status": "unknown",
            "last_read_offset": 0,
        })
        state = self.state(sessions)

        active = state._prepare_indexed_live_state()

        self.assertEqual(active["commander_id"], self.bravo)
        self.assertEqual((state.commander_id, state.commander_fid, state.commander),
                         (self.bravo, "FID-B", "Bravo"))
        self.assertEqual((state.journal_files, state.connected), (3, True))
        self.assertEqual((state.system, state.station), ("Colonia", "Jaques Station"))
        self.assertEqual((state.ship_loadout.ship_id, state.ship), (51, "Erft-Büffel"))
        self.assertEqual([mission.mission_id for mission in state.missions], [7])
        self.assertEqual((state.unsold_bio_count, state.unsold_cartography_count), (1, 1))

    def test_delta_failure_preserves_index_identity_and_journal_count(self):
        current = self.folder / "Journal.2026-01-01T000100.01.log"
        current.write_text("{}\n", encoding="utf-8")
        sessions = self.sessions(current)
        state = self.state(sessions)
        state.journal_folder = self.folder
        state.watcher = _WatcherStub(current)

        def fail_after_identity(*_args, **_kwargs):
            self.assertEqual(state.commander_id, self.bravo)
            self.assertEqual(state.commander_fid, "FID-B")
            raise RuntimeError("delta persistence failed")

        with patch(
            "cmdrhelper.state.read_latest_state",
            return_value={
                "commander_fid": "FID-B",
                "commander_identity_name": "Bravo",
                "commander_identity_timestamp": "2026-01-01T00:00:00Z",
                "latest_journal_session": sessions[-1],
            },
        ), patch(
            "cmdrhelper.journal_reader.read_journal_delta",
            return_value=([{"event": "Test"}], 3),
        ), patch.object(
            self.db, "apply_commander_journal_delta", side_effect=fail_after_identity
        ), self.assertLogs("cmdrhelper.state", level="ERROR"):
            self.assertFalse(state.refresh())

        self.assertEqual((state.commander_id, state.commander), (self.bravo, "Bravo"))
        self.assertEqual((state.journal_files, state.connected), (2, True))
        self.assertEqual((state.system, state.ship_loadout.ship_id), ("Colonia", 51))
        self.assertIn("RuntimeError", state._last_refresh_error)


if __name__ == "__main__":
    unittest.main()
