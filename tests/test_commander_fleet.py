from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from cmdrhelper.database import CMDRDatabase, SCHEMA_VERSION
from cmdrhelper.journal_reader import read_latest_state
from cmdrhelper.route_planner.models import ShipLoadoutData


def event(kind, second, **values):
    return {"timestamp": f"2026-02-01T00:00:{second:02d}Z", "event": kind, **values}


class CommanderFleetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "fleet.db"
        self.db = CMDRDatabase(self.path)
        self.a = self.db.upsert_commander("FID-A", "Alpha")
        self.b = self.db.upsert_commander("FID-B", "Bravo")

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def ship(ship_id, name, ship_type="CobraMkIII", stale=False):
        return ShipLoadoutData(
            ship_id=ship_id, ship_name=name, ship_type=ship_type,
            ship_ident=f"ID-{ship_id}", max_jump_range=20.5,
            loadout_timestamp=f"L-{ship_id}", loadout_complete=not stale,
            loadout_stale=stale,
        )

    def test_multiple_ships_and_same_id_are_separate(self):
        self.db.store_commander_ship(self.a, self.ship(1, "A One"), "T1")
        self.db.store_commander_ship(self.a, self.ship(2, "A Two"), "T2")
        self.db.store_commander_ship(self.b, self.ship(1, "B One", "Anaconda"), "T3")
        self.assertEqual([s["ship_name"] for s in self.db.commander_ships(self.a)],
                         ["A Two", "A One"])
        self.assertEqual([s["ship_name"] for s in self.db.commander_ships(self.b)], ["B One"])
        self.assertEqual(sum(s["is_current"] for s in self.db.commander_ships(self.a)), 1)

    def test_return_updates_existing_ship_and_sorting_is_deterministic(self):
        self.db.store_commander_ship(self.a, self.ship(1, "Zulu"), "T1")
        self.db.store_commander_ship(self.a, self.ship(2, "Alpha"), "T2")
        updated = self.ship(1, "Zulu", stale=True)
        self.db.store_commander_ship(self.a, updated, "T3", location={
            "system_name": "Colonia", "system_address": 99, "station_name": "Jaques Station"
        })
        ships = self.db.commander_ships(self.a)
        self.assertEqual([(s["ship_id"], s["is_current"]) for s in ships], [(1, True), (2, False)])
        self.assertTrue(ships[0]["loadout_stale"])
        self.assertEqual(ships[0]["system_name"], "Colonia")
        self.assertEqual(len(ships), 2)

    def test_fleet_parser_keeps_switches_and_locations_with_active_ship(self):
        folder = Path(self.tmp.name) / "journals"
        folder.mkdir()
        events = [
            event("LoadGame", 0, FID="FID-A", Commander="Alpha", ShipID=1,
                  Ship="CobraMkIII", ShipName="One"),
            event("Loadout", 1, ShipID=1, Ship="CobraMkIII", ShipName="One", Modules=[]),
            event("FSDJump", 2, StarSystem="Sol", SystemAddress=1),
            event("ShipyardSwap", 3, ShipID=2, ShipType="Anaconda"),
            event("Loadout", 4, ShipID=2, Ship="Anaconda", ShipName="Two", Modules=[]),
            event("Docked", 5, StarSystem="Colonia", SystemAddress=2, StationName="Jaques"),
            event("ModuleBuy", 6, ShipID=2),
            event("ShipyardSwap", 7, ShipID=1, ShipType="CobraMkIII"),
            event("Loadout", 8, ShipID=1, Ship="CobraMkIII", ShipName="One Updated", Modules=[]),
        ]
        (folder / "Journal.2026-02-01T000000.01.log").write_text(
            "".join(json.dumps(item) + "\n" for item in events), encoding="utf-8"
        )
        state = read_latest_state(folder)
        fleet = {item["loadout"].ship_id: item for item in state["fleet_ships"]}
        self.assertEqual(set(fleet), {1, 2})
        self.assertTrue(fleet[1]["is_current"])
        self.assertFalse(fleet[2]["is_current"])
        self.assertEqual(fleet[1]["loadout"].ship_name, "One Updated")
        self.assertEqual(fleet[2]["location"]["system_name"], "Colonia")
        self.assertEqual(fleet[1]["location"]["system_name"], "Colonia")

    def test_missing_values_do_not_leak_between_ships(self):
        self.db.store_commander_ship(self.a, self.ship(1, "Complete"), "T1")
        self.db.store_commander_ship(
            self.a, ShipLoadoutData(ship_id=2, ship_name="Sparse"), "T2"
        )
        sparse = self.db.commander_last_ship(self.a)
        self.assertEqual(sparse["ship_name"], "Sparse")
        self.assertIsNone(sparse["max_jump_range"])
        self.assertEqual(sparse["system_name"], "")

    def test_v6_ship_snapshot_migrates_to_v7_fleet(self):
        self.db.store_commander_ship(self.a, self.ship(5, "Legacy"), "T5")
        with sqlite3.connect(self.path) as con:
            con.execute("ALTER TABLE commander_ships RENAME TO commander_ships_v7_test")
            con.execute("""CREATE TABLE commander_ships (
                commander_id INTEGER PRIMARY KEY, ship_id INTEGER, ship_type TEXT NOT NULL DEFAULT '',
                ship_name TEXT NOT NULL DEFAULT '', ship_ident TEXT NOT NULL DEFAULT '',
                last_seen TEXT NOT NULL DEFAULT '', loadout_timestamp TEXT NOT NULL DEFAULT '',
                max_jump_range REAL, unladen_mass REAL, cargo_capacity INTEGER,
                main_tank_capacity REAL, reserve_tank_capacity REAL, fsd_item TEXT NOT NULL DEFAULT '',
                guardian_fsd_boosters TEXT NOT NULL DEFAULT '[]',
                loadout_complete INTEGER NOT NULL DEFAULT 0, loadout_stale INTEGER NOT NULL DEFAULT 1)
            """)
            con.execute("""INSERT INTO commander_ships SELECT commander_id,ship_id,ship_type,
                ship_name,ship_ident,last_seen,loadout_timestamp,max_jump_range,unladen_mass,
                cargo_capacity,main_tank_capacity,reserve_tank_capacity,fsd_item,
                guardian_fsd_boosters,loadout_complete,loadout_stale
                FROM commander_ships_v7_test""")
            con.execute("DROP TABLE commander_ships_v7_test")
            con.execute("PRAGMA user_version=6")
        migrated = CMDRDatabase(self.path)
        self.assertEqual(SCHEMA_VERSION, 7)
        self.assertEqual(migrated.commander_last_ship(self.a)["ship_name"], "Legacy")


if __name__ == "__main__":
    unittest.main()
