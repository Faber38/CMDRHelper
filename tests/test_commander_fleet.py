from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication, QScrollArea, QToolButton

from cmdrhelper.database import CMDRDatabase, SCHEMA_VERSION
from cmdrhelper.i18n import tr
from cmdrhelper.journal_reader import read_latest_state
from cmdrhelper.route_planner.models import ShipLoadoutData
from cmdrhelper.ship_identity import is_definite_non_ship
from cmdrhelper.ship_equipment import analyze_ship_modules
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
    def ship(ship_id, name, ship_type="CobraMkIII", stale=False, *,
             jump_range=20.5, cargo_capacity=None, unladen_mass=None, modules=()):
        return ShipLoadoutData(
            ship_id=ship_id, ship_name=name, ship_type=ship_type,
            ship_ident=f"ID-{ship_id}", max_jump_range=jump_range,
            cargo_capacity=cargo_capacity, unladen_mass=unladen_mass,
            modules=tuple(modules),
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

    def test_v6_ship_snapshot_migrates_to_current_fleet_schema(self):
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
        self.assertEqual(SCHEMA_VERSION, 12)
        legacy = migrated.commander_last_ship(self.a)
        self.assertEqual(legacy["ship_name"], "Legacy")
        self.assertEqual(legacy["modules"], [])
        self.assertEqual(CMDRDatabase(self.path).commander_last_ship(self.a)["ship_name"],
                         "Legacy")

    def _view(self, live_id=None, viewed_id=None, settings=None):
        state = AppState.__new__(AppState)
        QObject.__init__(state)
        state.database = self.db
        state.commander_id = live_id
        state.commander_fid = self.db._commander_fid(live_id) if live_id else ""
        state.commander = ""
        state.viewed_commander_id = self.a if viewed_id is None else viewed_id
        state._viewed_commander_user_selected = True

        class Settings:
            def __init__(self): self.values = {}
            def value(self, key, default=None): return self.values.get(key, default)
            def setValue(self, key, value): self.values[key] = value

        state.settings = settings or Settings()
        return CommanderView(state)

    @staticmethod
    def _fleet_order(view):
        return [
            view.fleet_layout.itemAt(index).widget().property("shipId")
            for index in range(view.fleet_layout.count())
            if view.fleet_layout.itemAt(index).widget() is not None
        ]

    @staticmethod
    def _select_sort(view, sort_key, direction=None):
        view.fleet_sort_combo.setCurrentIndex(view.fleet_sort_combo.findData(sort_key))
        if direction is not None:
            view.fleet_sort_direction_combo.setCurrentIndex(
                view.fleet_sort_direction_combo.findData(direction)
            )

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

    def test_numeric_fleet_sorting_and_missing_values(self):
        self.db.store_commander_ship(
            self.a, self.ship(1, "Medium", jump_range=30, cargo_capacity=64,
                              unladen_mass=400), "T1"
        )
        self.db.store_commander_ship(
            self.a, self.ship(2, "Largest", jump_range=50, cargo_capacity=128,
                              unladen_mass=800), "T2"
        )
        self.db.store_commander_ship(
            self.a, self.ship(3, "Smallest", jump_range=10, cargo_capacity=8,
                              unladen_mass=100), "T3"
        )
        self.db.store_commander_ship(
            self.a, self.ship(4, "Missing", jump_range=None), "T4", is_current=False
        )
        view = self._view(self.a)

        self._select_sort(view, "jump_range")
        self.assertEqual(self._fleet_order(view), [2, 1, 3, 4])
        self._select_sort(view, "cargo")
        self.assertEqual(self._fleet_order(view), [2, 1, 3, 4])
        self._select_sort(view, "mass", "ascending")
        self.assertEqual(self._fleet_order(view), [3, 1, 2, 4])
        self._select_sort(view, "mass", "descending")
        self.assertEqual(self._fleet_order(view), [2, 1, 3, 4])

    def test_loadout_equipment_is_detected_and_persisted_as_raw_modules(self):
        modules = [
            {"Slot": "PlanetaryVehicleHangar", "Item": "int_buggybay_size4_class2"},
            {"Slot": "PlanetaryVehicleHangar_Buggy", "Item": "TestBuggy"},
            {"Slot": "PlanetaryVehicleHangar_Buggy02", "Item": "Combat_Multicrew_SRV_01"},
            {"Slot": "PlanetaryVehicleHangar_Buggy03", "Item": "Lander01"},
            {"Slot": "FighterBay", "Item": "int_fighterbay_size6_class1"},
            {"Slot": "FighterBay01", "Item": "independent_fighter"},
            {"Slot": "ShieldGenerator", "Item": "int_shieldgenerator_size5_class5",
             "Engineering": {"BlueprintName": "Reinforced", "Level": 5}},
            {"Slot": "TinyHardpoint1", "Item": "hpt_shieldbooster_size0_class5"},
            {"Slot": "MediumHardpoint1", "Item": "hpt_multicannon_gimbal_medium"},
            {"Slot": "Slot03_Size2", "Item": "int_hullreinforcement_size2_class2"},
            {"Slot": "Slot04_Size2", "Item": "int_modulereinforcement_size2_class2"},
            {"Slot": "Slot05_Size4", "Item": "int_passengercabin_size4_class3"},
        ]
        folder = Path(self.tmp.name) / "equipment-journal"
        folder.mkdir()
        (folder / "Journal.2026-02-01T000000.01.log").write_text(
            "".join(json.dumps(item) + "\n" for item in (
                event("LoadGame", 0, FID="FID-A", Commander="Alpha", ShipID=7,
                      Ship="CobraMkIII", ShipName="Equipped"),
                event("Loadout", 1, ShipID=7, Ship="CobraMkIII",
                      ShipName="Equipped", Modules=modules),
            )),
            encoding="utf-8",
        )
        parsed = read_latest_state(folder)["ship_loadout"]
        equipment = analyze_ship_modules(parsed.modules)
        self.assertTrue(equipment["vehicle_hangar"])
        self.assertEqual(equipment["vehicles"], {
            "scarab": 1, "scorpion": 1, "nomad": 1,
        })
        self.assertTrue(equipment["fighter_hangar"])
        self.assertEqual(equipment["fighters"], 1)
        self.assertEqual(equipment["shield_boosters"], 1)
        self.assertEqual(equipment["weapons"], 1)
        self.assertEqual(equipment["hull_reinforcements"], 1)
        self.assertEqual(equipment["module_reinforcements"], 1)
        self.assertEqual(equipment["passenger_cabins"], 1)

        self.db.store_commander_ship(self.a, parsed, "T1")
        stored = self.db.commander_ships(self.a)[0]
        self.assertEqual(stored["modules"], modules)
        self.assertEqual(analyze_ship_modules(stored["modules"]), equipment)
        self.db.store_commander_ship(
            self.a, ShipLoadoutData(ship_id=7, loadout_stale=True), "T2"
        )
        self.assertEqual(self.db.commander_ships(self.a)[0]["modules"], modules)

    def test_equipment_filters_and_expansion_are_commander_scoped(self):
        vehicle_hangar = (
            {"Slot": "FighterBay01", "Item": "int_mkiilargebuggybay_size4_class3"},
        )
        fighter_hangar = (
            {"Slot": "FighterBay01", "Item": "int_fighterbay_size5_class1"},
        )
        fighter_hangar_mk2 = (
            {"Slot": "Slot02_Size6", "Item": "int_fighterbaymk2_size6_class1_free"},
        )
        self.db.store_commander_ship(
            self.a, self.ship(1, "Vehicle Hangar", modules=vehicle_hangar), "T1"
        )
        self.db.store_commander_ship(
            self.a, self.ship(2, "Fighter Hangar", modules=fighter_hangar), "T2"
        )
        self.db.store_commander_ship(
            self.a, self.ship(3, "Fighter Hangar Mk II", modules=fighter_hangar_mk2), "T3"
        )
        self.db.store_commander_ship(self.a, self.ship(5, "Plain"), "T5")
        self.db.store_commander_ship(
            self.b, self.ship(6, "Foreign", modules=vehicle_hangar), "T6"
        )
        view = self._view(live_id=self.b, viewed_id=self.a)
        self.assertEqual(
            [view.fleet_filter_combo.itemData(index)
             for index in range(view.fleet_filter_combo.count())],
            ["all", "vehicle_hangar", "fighter_hangar"],
        )
        self.assertEqual(
            view.fleet_title.text(), tr("commander_view.fleet.title", count=4)
        )

        first_card = view.fleet_layout.itemAt(0).widget()
        first_card.findChild(QToolButton).setChecked(True)
        view.fleet_filter_combo.setCurrentIndex(
            view.fleet_filter_combo.findData("vehicle_hangar")
        )
        self.assertEqual(self._fleet_order(view), [1])
        self.assertEqual(
            view.fleet_title.text(),
            tr("commander_view.fleet.title_filtered", visible=1, total=4),
        )
        view.fleet_filter_combo.setCurrentIndex(
            view.fleet_filter_combo.findData("fighter_hangar")
        )
        self.assertEqual(self._fleet_order(view), [3, 2])
        view.fleet_filter_combo.setCurrentIndex(view.fleet_filter_combo.findData("all"))
        self.assertEqual(set(self._fleet_order(view)), {1, 2, 3, 5})
        self.assertEqual(
            view.fleet_title.text(), tr("commander_view.fleet.title", count=4)
        )
        restored = next(
            view.fleet_layout.itemAt(index).widget()
            for index in range(view.fleet_layout.count() - 1)
            if view.fleet_layout.itemAt(index).widget().property("shipId") == 5
        )
        self.assertTrue(restored.findChild(QToolButton).isChecked())

    def test_vehicle_hangar_detection_depends_on_item_not_slot(self):
        old = analyze_ship_modules([
            {"Slot": "Slot04_Size4", "Item": "int_buggybay_size4_class2"}
        ])
        large = analyze_ship_modules([
            {"Slot": "FighterBay01", "Item": "int_mkiilargebuggybay_size4_class3"}
        ])
        slot_only = analyze_ship_modules([
            {"Slot": "FighterBay01", "Item": "unrelated_module"}
        ])
        self.assertTrue(old["vehicle_hangar"])
        self.assertTrue(large["vehicle_hangar"])
        self.assertFalse(slot_only["vehicle_hangar"])

    def test_name_location_and_deterministic_tie_breakers(self):
        self.db.store_commander_ship(self.a, self.ship(9, "Zulu", "ZuluType"), "T1", location={
            "system_name": "Sol", "system_address": 1, "station_name": "Galileo"
        })
        self.db.store_commander_ship(self.a, self.ship(3, "Alpha", "AlphaType"), "T2", location={
            "system_name": "Colonia", "system_address": 2, "station_name": "Jaques"
        })
        self.db.store_commander_ship(self.a, self.ship(2, "Alpha", "AlphaType"), "T3", location={
            "system_name": "Colonia", "system_address": 2, "station_name": "Jaques"
        })
        self.db.store_commander_ship(
            self.a, self.ship(4, "Unknown", ""), "T4", is_current=False
        )
        view = self._view(self.a)
        self._select_sort(view, "name")
        self.assertEqual(self._fleet_order(view), [2, 3, 4, 9])
        self._select_sort(view, "type")
        self.assertEqual(self._fleet_order(view), [2, 3, 9, 4])
        self._select_sort(view, "location")
        self.assertEqual(self._fleet_order(view), [2, 3, 9, 4])

    def test_sorting_preserves_live_color_location_colors_and_expansion(self):
        sol = {"system_name": "Sol", "system_address": 1, "station_name": "Galileo"}
        self.db.store_commander_ship(
            self.a, self.ship(1, "Cargo", cargo_capacity=256), "T1", location=sol
        )
        self.db.store_commander_ship(
            self.a, self.ship(2, "Live", cargo_capacity=4), "T2", location=sol
        )
        view = self._view(self.a)
        cards = {
            view.fleet_layout.itemAt(index).widget().property("shipId"):
                view.fleet_layout.itemAt(index).widget()
            for index in range(view.fleet_layout.count() - 1)
        }
        cards[1].findChild(QToolButton).setChecked(True)
        location_color = cards[1].property("fleetColor")

        self._select_sort(view, "cargo")
        self.assertEqual(self._fleet_order(view), [1, 2])
        sorted_cards = {
            view.fleet_layout.itemAt(index).widget().property("shipId"):
                view.fleet_layout.itemAt(index).widget()
            for index in range(view.fleet_layout.count() - 1)
        }
        self.assertFalse(sorted_cards[1].property("liveShip"))
        self.assertEqual(sorted_cards[1].property("fleetColor"), location_color)
        self.assertTrue(sorted_cards[1].findChild(QToolButton).isChecked())
        self.assertEqual(sorted_cards[1].findChild(QToolButton).arrowType(), Qt.DownArrow)
        self.assertTrue(sorted_cards[2].property("liveShip"))
        self.assertEqual(QColor(sorted_cards[2].property("fleetColor")).hue(), 125)

    def test_sort_settings_are_restored(self):
        class Settings:
            def __init__(self): self.values = {}
            def value(self, key, default=None): return self.values.get(key, default)
            def setValue(self, key, value): self.values[key] = value

        settings = Settings()
        view = self._view(self.a, settings=settings)
        self._select_sort(view, "mass", "ascending")
        restored = self._view(self.a, settings=settings)
        self.assertEqual(restored.fleet_sort_combo.currentData(), "mass")
        self.assertEqual(restored.fleet_sort_direction_combo.currentData(), "ascending")

    def test_offline_commander_sorting_keeps_fleet_scoped(self):
        self.db.store_commander_ship(self.a, self.ship(1, "Alpha Ship"), "T1")
        self.db.store_commander_ship(self.b, self.ship(2, "Bravo Ship"), "T2")
        view = self._view(live_id=self.b, viewed_id=self.a)
        self._select_sort(view, "name")
        self.assertEqual(self._fleet_order(view), [1])

    def test_only_confirmed_non_ships_are_rejected_without_positive_ship_list(self):
        for ship_id, ship_type in enumerate((
            "ExplorationSuit_Class3", "ExplorationSuit_Class5",
            "UtilitySuit_Class5", "TacticalSuit_Class5",
            "TestBuggy", "Combat_Multicrew_SRV_01", "Lander01", "mev_rhino",
        ), start=100):
            self.assertTrue(is_definite_non_ship(ship_type))
            self.db.store_commander_ship(
                self.a, self.ship(ship_id, ship_type, ship_type), f"X{ship_id}"
            )
        for ship_id, ship_type in enumerate((
            "sidewinder", "explorer_nx", "typex", "mediumtransport01",
            "future_rare_ship_99", "lakonminer",
        ), start=200):
            self.assertFalse(is_definite_non_ship(ship_type))
            self.db.store_commander_ship(
                self.a, self.ship(ship_id, ship_type, ship_type), f"Y{ship_id}"
            )
        self.assertEqual(
            {ship["ship_type"] for ship in self.db.commander_ships(self.a)},
            {"sidewinder", "explorer_nx", "typex", "mediumtransport01",
             "future_rare_ship_99", "lakonminer"},
        )

    def test_suit_and_srv_loadgame_keep_mother_ship_and_its_location(self):
        folder = Path(self.tmp.name) / "vehicle-journals"
        folder.mkdir()

        def write(stamp, events):
            (folder / f"Journal.{stamp}.01.log").write_text(
                "".join(json.dumps(item) + "\n" for item in events), encoding="utf-8"
            )

        write("2026-02-01T000000", [
            event("LoadGame", 0, FID="FID-A", Commander="Alpha", ShipID=7,
                  Ship="explorer_nx", ShipName="Mother"),
            event("Loadout", 1, ShipID=7, Ship="explorer_nx", ShipName="Mother", Modules=[]),
            event("Location", 2, StarSystem="Sol", SystemAddress=1),
        ])
        write("2026-02-01T000100", [
            event("LoadGame", 3, FID="FID-A", Commander="Alpha", ShipID=4293000003,
                  Ship="ExplorationSuit_Class3", Ship_Localised="$ExplorationSuit_Class1_Name;"),
            event("Location", 4, StarSystem="Achenar", SystemAddress=2, OnFoot=True),
            event("LaunchSRV", 5, SRVType="combat_multicrew_srv_01", ID=30,
                  PlayerControlled=True),
            event("Location", 6, StarSystem="Colonia", SystemAddress=3),
        ])
        state = read_latest_state(folder)
        self.assertEqual(state["ship_loadout"].ship_id, 7)
        self.assertEqual(state["ship_loadout"].ship_type, "explorer_nx")
        self.assertEqual(len(state["fleet_ships"]), 1)
        self.assertEqual(state["fleet_ships"][0]["location"]["system_name"], "Sol")

    def test_non_ship_loadgame_variants_never_create_a_fleet_ship(self):
        cases = (
            ("ExplorationSuit_Class3", "$ExplorationSuit_Class1_Name;", 4293000003),
            ("ExplorationSuit_Class5", "$ExplorationSuit_Class1_Name;", 4293000002),
            ("UtilitySuit_Class5", "$UtilitySuit_Class1_Name;", 4293000001),
            ("TacticalSuit_Class5", "$TacticalSuit_Class1_Name;", 4293000005),
            ("TestBuggy", "SRV Scarab", 27),
            ("Combat_Multicrew_SRV_01", "Scorpion (SRV)", 30),
            ("Lander01", "Nomad", 41),
            ("mev_rhino", "SRV Rhino", 52),
        )
        for index, (ship_type, localized, ship_id) in enumerate(cases):
            with self.subTest(ship_type=ship_type):
                folder = Path(self.tmp.name) / f"non-ship-{index}"
                folder.mkdir()
                (folder / "Journal.2026-02-01T000000.01.log").write_text(
                    json.dumps(event("LoadGame", 0, FID="FID-A", Commander="Alpha",
                                     Ship=ship_type, Ship_Localised=localized,
                                     ShipID=ship_id)) + "\n",
                    encoding="utf-8",
                )
                state = read_latest_state(folder)
                self.assertIsNone(state["ship_loadout"].ship_id)
                self.assertEqual(state["fleet_ships"], [])

    def test_on_foot_srv_fighter_and_taxi_events_do_not_replace_ship(self):
        folder = Path(self.tmp.name) / "temporary-vehicles"
        folder.mkdir()
        events = [
            event("LoadGame", 0, FID="FID-A", Commander="Alpha", ShipID=8, Ship="typex"),
            event("Loadout", 1, ShipID=8, Ship="typex", Modules=[]),
            event("Location", 2, StarSystem="Sol", SystemAddress=1),
            event("Disembark", 3, SRV=False, Taxi=False, Multicrew=False, OnPlanet=True),
            event("Embark", 4, SRV=False, Taxi=True, Multicrew=False),
            event("FSDJump", 5, StarSystem="Achenar", SystemAddress=2),
            event("LaunchFighter", 6, Loadout="galactic", ID=41, PlayerControlled=True),
            event("DockFighter", 7, ID=41),
            event("LaunchSRV", 8, SRVType="lander01", ID=41, PlayerControlled=True),
            event("DockSRV", 9, SRVType="lander01", ID=41),
            event("LaunchSRV", 10, SRVType="mev_rhino", SRVType_Localised="SRV Rhino",
                  ID=52, PlayerControlled=True, Loadout="advanced"),
            event("DockSRV", 11, SRVType="mev_rhino", SRVType_Localised="SRV Rhino", ID=52),
        ]
        (folder / "Journal.2026-02-01T000000.01.log").write_text(
            "".join(json.dumps(item) + "\n" for item in events), encoding="utf-8"
        )
        state = read_latest_state(folder)
        self.assertEqual([item["loadout"].ship_type for item in state["fleet_ships"]], ["typex"])

    def test_cleanup_removes_only_certain_legacy_rows_and_restores_current(self):
        self.db.store_commander_ship(self.a, self.ship(1, "Rare", "unknown_future_ship"), "T1")
        template = """INSERT INTO commander_ships(
            commander_id,ship_id,ship_type,ship_name,ship_ident,first_seen,last_seen,
            loadout_timestamp,system_name,station_name,fsd_item,guardian_fsd_boosters,
            loadout_complete,loadout_stale,is_current)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        with self.db._connect() as con:
            con.execute("UPDATE commander_ships SET is_current=0 WHERE commander_id=?", (self.a,))
            for ship_id, ship_type in ((30, "TestBuggy"), (31, "Combat_Multicrew_SRV_01"),
                                       (4293000003, "ExplorationSuit_Class3")):
                con.execute(template, (self.a, ship_id, ship_type, "", "", "T2", "T2",
                                       "", "Sol", "", "", "[]", 0, 1,
                                       int(ship_id == 4293000003)))
        self.assertEqual(self.db.cleanup_non_ship_fleet_rows(), 3)
        ships = self.db.commander_ships(self.a)
        self.assertEqual([(ship["ship_type"], ship["is_current"]) for ship in ships],
                         [("unknown_future_ship", True)])


if __name__ == "__main__":
    unittest.main()
