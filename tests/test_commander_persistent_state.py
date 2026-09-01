from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication

from cmdrhelper.database import CMDRDatabase, SCHEMA_VERSION
from cmdrhelper.journal_reader import read_latest_state
from cmdrhelper.route_planner.models import GuardianFsdBooster, ShipLoadoutData
from cmdrhelper.state import AppState
from cmdrhelper.ui.commander_view import CommanderView


class MemorySettings:
    def __init__(self):
        self.values = {}

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value


def state_for(database, live_id):
    state = AppState.__new__(AppState)
    QObject.__init__(state)
    state.database = database
    state.settings = MemorySettings()
    state.commander_id = live_id
    state.commander_fid = database._commander_fid(live_id)
    state.commander = ""
    state.viewed_commander_id = None
    state._viewed_commander_user_selected = False
    return state


def write_journal(folder, events):
    path = folder / "Journal.2026-01-01T000000.01.log"
    path.write_text(
        "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8"
    )


def event(kind, second, **values):
    return {
        "timestamp": f"2026-01-01T00:00:{second:02d}Z",
        "event": kind,
        **values,
    }


class CommanderPersistentStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.database = CMDRDatabase(Path(self.tmp.name) / "test.db")
        self.a = self.database.upsert_commander("FID-A", "Alpha")
        self.b = self.database.upsert_commander("FID-B", "Bravo")

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def mission(name, status="Angenommen", terminal_state=""):
        return {
            "mission_id": 77, "name": name, "internal_name": "Mission_Delivery",
            "mission_type": "delivery", "faction": f"{name} Faction",
            "status": status, "destination_system": f"{name} System",
            "destination_station": f"{name} Station", "destination_body": "",
            "expiry": "2026-02-01T00:00:00Z", "reward": 1234,
            "summary": f"{name} summary", "next_step": "Mission prüfen",
            "progress_text": "", "accepted_at": "2026-01-01T00:00:00Z",
            "last_update": "2026-01-02T00:00:00Z",
            "terminal_state": terminal_state,
        }

    def test_same_mission_id_is_separate_and_terminal_history_stays_with_b(self):
        self.database.store_commander_missions(self.a, [self.mission("Alpha")])
        self.database.store_commander_missions(
            self.b, [], [self.mission("Bravo", "Aufgabe erledigt", "completed")]
        )
        a_rows = self.database.commander_missions(self.a)
        b_rows = self.database.commander_missions(self.b)
        self.assertEqual([(row["mission_id"], row["name"]) for row in a_rows], [(77, "Alpha")])
        self.assertTrue(a_rows[0]["is_open"])
        self.assertEqual([(row["mission_id"], row["name"]) for row in b_rows], [(77, "Bravo")])
        self.assertFalse(b_rows[0]["is_open"])
        self.assertEqual(b_rows[0]["terminal_state"], "completed")

    def test_locations_station_and_body_are_separate(self):
        self.database.store_commander_location(self.a, {
            "system_name": "Alpha System", "system_address": 1,
            "station_name": "Alpha Station", "body_name": "",
            "event_timestamp": "T1", "event_type": "Docked",
        })
        self.database.store_commander_location(self.b, {
            "system_name": "Bravo System", "system_address": 2,
            "station_name": "", "body_name": "Bravo A 1",
            "event_timestamp": "T2", "event_type": "Location",
        })
        a = self.database.commander_summary(self.a)["persistent_location"]
        b = self.database.commander_summary(self.b)["persistent_location"]
        self.assertEqual((a["system_name"], a["station_name"], a["body_name"]),
                         ("Alpha System", "Alpha Station", ""))
        self.assertEqual((b["system_name"], b["station_name"], b["body_name"]),
                         ("Bravo System", "", "Bravo A 1"))

    def test_same_ship_id_is_separate_and_offline_b_is_visible_while_a_live(self):
        a_ship = ShipLoadoutData(ship_id=7, ship_type="CobraMkIII", ship_name="A Ship")
        b_ship = ShipLoadoutData(
            ship_id=7, ship_type="Anaconda", ship_name="B Ship", ship_ident="B-7",
            max_jump_range=42.5, unladen_mass=400.0, cargo_capacity=128,
            main_tank_capacity=32.0, reserve_tank_capacity=0.63,
            fsd_item="int_hyperdrive_size6_class5",
            guardian_fsd_boosters=(GuardianFsdBooster("GuardianFSDBooster_Size5", True),),
            loadout_timestamp="T2", loadout_complete=True, loadout_stale=False,
        )
        self.database.store_commander_ship(self.a, a_ship, "T1")
        self.database.store_commander_ship(self.b, b_ship, "T2")
        self.assertEqual(self.database.commander_summary(self.a)["ship"]["ship_name"], "A Ship")
        self.assertEqual(self.database.commander_summary(self.b)["ship"]["ship_name"], "B Ship")

        state = state_for(self.database, self.a)
        view = CommanderView(state)
        state.select_viewed_commander(self.b)
        self.assertEqual(state.commander_id, self.a)
        self.assertEqual(view.values["last_ship"].text(), "B Ship")
        self.assertEqual(view.ship_values["ship_id"].text(), "7")

    def test_carriers_are_separate_and_name_location_update(self):
        self.database.store_commander_carrier(self.a, {
            "carrier_id": 10, "callsign": "AAA-111", "carrier_name": "Alpha Carrier",
            "system_name": "Sol", "system_address": 1, "last_updated": "T1",
        })
        self.database.store_commander_carrier(self.b, {
            "carrier_id": 20, "callsign": "BBB-222", "carrier_name": "Bravo Carrier",
            "system_name": "Achenar", "system_address": 2, "last_updated": "T1",
        })
        self.database.store_commander_carrier(self.b, {
            "carrier_id": 20, "callsign": "BBB-222", "carrier_name": "Bravo Renamed",
            "system_name": "Colonia", "system_address": 3, "last_updated": "T2",
        })
        self.assertEqual(self.database.commander_summary(self.a)["carrier"]["carrier_name"],
                         "Alpha Carrier")
        carrier_b = self.database.commander_summary(self.b)["carrier"]
        self.assertEqual((carrier_b["carrier_name"], carrier_b["system_name"]),
                         ("Bravo Renamed", "Colonia"))

    def test_viewed_commander_does_not_change_default_live_writes(self):
        self.database.set_active_commander(self.a)
        state = state_for(self.database, self.a)
        state.select_viewed_commander(self.b)
        self.database.store_biology(1, 1, species="Live A")
        with self.database._connect() as con:
            self.assertEqual(con.execute("SELECT commander_id FROM biology").fetchall(), [(self.a,)])


class PersistentJournalTests(unittest.TestCase):
    def test_terminal_mission_is_exposed_for_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            write_journal(folder, [
                event("Commander", 0, FID="FID-A", Name="Alpha"),
                event("MissionAccepted", 1, MissionID=77, Name="Mission_Delivery"),
                event("MissionCompleted", 2, MissionID=77, Reward=5000),
            ])
            state = read_latest_state(folder)
        self.assertEqual(state["missions"], [])
        self.assertEqual(state["mission_terminal_updates"][0]["terminal_state"], "completed")
        self.assertEqual(state["mission_terminal_updates"][0]["reward"], 5000)

    def test_only_carrierstats_proves_ownership_and_foreign_updates_are_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            write_journal(folder, [
                event("Commander", 0, FID="FID-A", Name="Alpha"),
                event("CarrierJump", 1, MarketID=999, StarSystem="Foreign"),
                event("CarrierStats", 2, CarrierID=10, Callsign="AAA-111", Name="Owned"),
                event("CarrierLocation", 3, CarrierID=999, StarSystem="Still Foreign"),
                event("CarrierNameChange", 4, CarrierID=10, Callsign="AAA-111", Name="Renamed"),
                event("CarrierLocation", 5, CarrierID=10, StarSystem="Colonia", SystemAddress=42),
            ])
            state = read_latest_state(folder)
        self.assertEqual(state["owned_carrier"]["carrier_id"], 10)
        self.assertEqual(state["owned_carrier"]["carrier_name"], "Renamed")
        self.assertEqual(state["owned_carrier"]["system_name"], "Colonia")
        self.assertEqual(state["owned_carrier"]["system_address"], 42)

    def test_foreign_carrier_without_stats_is_not_owned(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            write_journal(folder, [
                event("Commander", 0, FID="FID-A", Name="Alpha"),
                event("CarrierJump", 1, MarketID=999, StarSystem="Foreign"),
                event("CarrierLocation", 2, CarrierID=999, StarSystem="Foreign"),
            ])
            state = read_latest_state(folder)
        self.assertIsNone(state["owned_carrier"])


class SchemaV5Tests(unittest.TestCase):
    def test_v4_to_v5_is_additive(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "v4.db"
            database = CMDRDatabase(path)
            commander_id = database.upsert_commander("FID-A", "Alpha")
            with database._connect() as con:
                for table in ("commander_missions", "commander_locations",
                              "commander_ships", "commander_carriers"):
                    con.execute(f"DROP TABLE {table}")
                con.execute("PRAGMA user_version=4")
            CMDRDatabase(path)
            with sqlite3.connect(path) as con:
                self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
                self.assertEqual(con.execute("SELECT fid FROM commanders WHERE id=?",
                                             (commander_id,)).fetchone(), ("FID-A",))
                tables = {row[0] for row in con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertTrue({"commander_missions", "commander_locations",
                             "commander_ships", "commander_carriers"} <= tables)


if __name__ == "__main__":
    unittest.main()
