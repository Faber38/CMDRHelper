from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication, QScrollArea, QToolButton

from cmdrhelper.database import CMDRDatabase, SCHEMA_VERSION
from cmdrhelper.journal_reader import read_latest_state
from cmdrhelper.route_planner.models import ShipLoadoutData
from cmdrhelper.state import AppState
from cmdrhelper.ui.commander_view import CommanderView


def event(kind, second, **values):
    return {"timestamp": f"2026-02-01T00:00:{second:02d}Z", "event": kind, **values}


class CommanderFleetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

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

    def _view(self, live_id=None):
        state = AppState.__new__(AppState)
        QObject.__init__(state)
        state.database = self.db
        state.commander_id = live_id
        state.commander_fid = self.db._commander_fid(live_id) if live_id else ""
        state.commander = ""
        state.viewed_commander_id = self.a
        state._viewed_commander_user_selected = True

        class Settings:
            def value(self, _key, default=None): return default
            def setValue(self, _key, _value): pass

        state.settings = Settings()
        return CommanderView(state)

    def test_many_ships_use_a_vertical_scroll_area(self):
        for ship_id in range(1, 18):
            self.db.store_commander_ship(self.a, self.ship(ship_id, f"Ship {ship_id}"),
                                         f"T{ship_id:02d}")
        view = self._view(self.a)
        view.resize(600, 360)
        view.tabs.setCurrentIndex(4)
        view.show()
        self.app.processEvents()
        self.assertIsInstance(view.fleet_scroll, QScrollArea)
        self.assertTrue(view.fleet_scroll.widgetResizable())
        initial_maximum = view.fleet_scroll.verticalScrollBar().maximum()
        self.assertGreater(initial_maximum, 0)
        buttons = view.fleet_container.findChildren(QToolButton)
        buttons[-1].setChecked(True)
        self.app.processEvents()
        self.assertGreater(view.fleet_scroll.verticalScrollBar().maximum(), initial_maximum)
        view.close()

    def test_live_and_location_colors_are_stable_and_grouped(self):
        sol = {"system_name": "Sol", "system_address": 1, "station_name": "Galileo"}
        colonia = {"system_name": "Colonia", "system_address": 2, "station_name": "Jaques"}
        self.db.store_commander_ship(self.a, self.ship(1, "Sol One"), "T1", location=sol)
        self.db.store_commander_ship(self.a, self.ship(2, "Colonia"), "T2", location=colonia)
        self.db.store_commander_ship(self.a, self.ship(3, "Sol Live"), "T3", location=sol)
        self.db.store_commander_ship(
            self.a, ShipLoadoutData(ship_id=4, ship_name="Unknown"), "T0", is_current=False
        )
        view = self._view(self.a)
        self.assertTrue(view.current_ship_card.property("liveShip"))
        ships = self.db.commander_ships(self.a)
        colors = {}
        for ship in ships:
            live = bool(ship["is_current"])
            card = view._fleet_ship_widget(ship, is_live=live)
            colors[ship["ship_id"]] = card.property("fleetColor")
            if live:
                self.assertTrue(card.property("liveShip"))
                self.assertEqual(view._fleet_color(ship, True).hue(), 125)
        self.assertEqual(colors[1], view._fleet_color(
            next(ship for ship in ships if ship["ship_id"] == 3), False
        ).name())
        self.assertNotEqual(colors[1], colors[2])
        self.assertNotEqual(colors[3], colors[1])
        self.assertEqual(colors[4], "")
        sol_ship = next(ship for ship in ships if ship["ship_id"] == 1)
        self.assertEqual(view._fleet_color(sol_ship, False).name(),
                         view._fleet_color(dict(sol_ship), False).name())

    def test_offline_current_ship_is_not_live_green(self):
        self.db.store_commander_ship(self.a, self.ship(1, "Offline"), "T1", location={
            "system_name": "Sol", "system_address": 1, "station_name": "Galileo"
        })
        view = self._view(self.b)
        ship = self.db.commander_last_ship(self.a)
        card = view._fleet_ship_widget(ship, is_live=False)
        self.assertFalse(card.property("liveShip"))
        self.assertNotEqual(view._fleet_color(ship, False).hue(), 125)


if __name__ == "__main__":
    unittest.main()
