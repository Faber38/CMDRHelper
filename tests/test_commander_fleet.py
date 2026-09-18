from __future__ import annotations

import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Qt, QPoint
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
        self.assertEqual(SCHEMA_VERSION, 20)
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
        view = CommanderView(state)
        view.show()
        def dispose_view():
            from PySide6.QtCore import QCoreApplication, QEvent
            view.close()
            view.deleteLater()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.addCleanup(dispose_view)
        return view

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

    def _sale_chain(self):
        return [
            {"event": "Commander", "FID": "FID-A", "Name": "Alpha", "timestamp": "2026-07-19T16:49:00Z"},
            {"event": "ShipyardSwap", "ShipID": 23, "ShipType": "type9", "timestamp": "2026-07-19T16:49:10Z"},
            {"event": "Loadout", "ShipID": 23, "Ship": "type9", "ShipName": "[EOT] = Betonmischer =", "ShipIdent": "FAB-38", "Modules": [], "timestamp": "2026-07-19T16:53:14Z"},
            {"event": "ShipyardSwap", "ShipID": 36, "ShipType": "sidewinder", "StoreShipID": 23, "timestamp": "2026-07-19T16:53:35Z"},
            {"event": "ShipyardSell", "SellShipID": 23, "ShipType": "type9", "timestamp": "2026-07-19T16:53:56Z"},
            {"event": "StoredShips", "ShipsHere": [{"ShipID": 4, "ShipType": "asp", "Name": "[EOT] = Erft-Habicht ="}], "timestamp": "2026-07-19T16:53:58Z"},
        ]

    def _write_sale_journal(self, events, name="Journal.2026-07-19T084810.01.log"):
        folder = Path(self.tmp.name) / "sale-journals"
        folder.mkdir(exist_ok=True)
        path = folder / name
        path.write_text("".join(json.dumps(item) + "\n" for item in events))
        return path

    def test_confirmed_sale_events_use_only_documented_id_fields(self):
        from cmdrhelper.ship_ownership import ship_sale
        for kind, field in (("ShipyardSell", "SellShipID"), ("SellShipOnRebuy", "SellShipId"),
                            ("ShipyardBuy", "SellShipID"), ("ShipyardSwap", "SellShipID")):
            result = ship_sale(event(kind, 1, **{field: 23}))
            self.assertEqual(result["ship_id"], 23)
            self.assertEqual(result["event_type"], kind)
            self.assertIsNone(ship_sale(event(kind, 1, ShipID=23, StoreShipID=23)))
        for kind in ("SellShip", "SellStoredShip", "Died", "Resurrect", "ShipyardTransfer"):
            self.assertIsNone(ship_sale(event(kind, 1, SellShipID=23)))
        for sid in (None, True, -1, "23"):
            self.assertIsNone(ship_sale(event("ShipyardSell", 1, SellShipID=sid)))
        self.assertIsNone(ship_sale({"event": "ShipyardSell", "SellShipID": 23}))

    def test_betonmischer_sale_reconstruction_updates_fleet_and_keeps_other_data_and_images(self):
        from cmdrhelper.fleet_reconstruction import reconstruct_fleet
        images, settings, root, source = self._personal_image_environment()
        self._deletion_fleet()
        personal = images.import_ship_image(settings, "FID-A", 23, source)
        path = self._write_sale_journal(self._sale_chain())
        original = path.read_bytes()
        with self.db._connect() as con:
            before = [line for line in con.iterdump() if "commander_ships" not in line and "commander_ship_sales" not in line]
        fleet = reconstruct_fleet([path], "FID-A")
        self.assertNotIn(23, {item["loadout"].ship_id for item in fleet})
        self.assertIn(4, {item["loadout"].ship_id for item in fleet})
        self.db.rebuild_commander_fleet(self.a, fleet)
        self.assertNotIn(23, {item["ship_id"] for item in self.db.commander_ships(self.a)})
        self.assertIn(4, {item["ship_id"] for item in self.db.commander_ships(self.a)})
        self.assertIn(23, {item["ship_id"] for item in self.db.commander_ships(self.b)})
        self.assertEqual(self._deleted_ids(self.a), [])
        self.assertTrue(personal.exists())
        self.assertEqual(images.personal_ship_image(settings, "FID-A", 23), personal)
        self.assertEqual(path.read_bytes(), original)
        with self.db._connect() as con:
            after = [line for line in con.iterdump() if "commander_ships" not in line and "commander_ship_sales" not in line]
        self.assertEqual(before, after)
        view = self._view(self.a, settings=settings)
        self.assertEqual(view.fleet_title.text(), tr("commander_view.fleet.title", count=3))
        self.assertNotIn(23, self._fleet_order(view))
        self.assertEqual(self.db.commander_last_ship(self.a)["ship_id"], 36)

    def test_sale_catchup_rotation_restart_and_old_observations_cannot_resurrect(self):
        from cmdrhelper.journal_catchup import capture, catch_up
        chain = self._sale_chain()
        first = self._write_sale_journal(chain[:4])
        folder = first.parent
        context = capture(self.db, folder)
        catch_up(self.db, context)
        self.assertIn(23, {s["ship_id"] for s in self.db.commander_ships(self.a)})
        second = self._write_sale_journal([chain[0], *chain[4:]], "Journal.2026-07-19T170000.01.log")
        catch_up(self.db, context)
        self.assertNotIn(23, {s["ship_id"] for s in self.db.commander_ships(self.a)})
        self.db = CMDRDatabase(self.path)
        old = [chain[2], event("StoredShips", 1, ShipsHere=[{"ShipID": 23, "ShipType": "type9"}])]
        self.db.apply_commander_journal_delta(self.a, "old-sales-replay.log", old, 100)
        self.db.apply_commander_journal_delta(self.a, "module-after-sale.log", [dict(chain[2]),
            {"event": "ModuleBuy", "ShipID": 23, "timestamp": "2026-07-20T00:00:00Z"}], 100)
        self.assertNotIn(23, {s["ship_id"] for s in self.db.commander_ships(self.a)})
        self.assertEqual(self._deleted_ids(self.a), [])
        self.assertTrue(first.exists() and second.exists())

    def test_later_confirmed_ownership_is_allowed_but_older_sale_cannot_remove_it(self):
        chain = self._sale_chain()
        self.db.apply_commander_journal_delta(self.a, "initial-sale.log", chain, 100)
        later = dict(chain[2], timestamp="2026-07-20T00:00:00Z")
        self.db.apply_commander_journal_delta(self.a, "later-ownership.log", [later], 100)
        self.assertIn(23, {s["ship_id"] for s in self.db.commander_ships(self.a)})
        self.db.apply_commander_journal_delta(self.a, "old-sale-again.log", [chain[4]], 100)
        self.assertIn(23, {s["ship_id"] for s in self.db.commander_ships(self.a)})
        self.db.apply_commander_journal_delta(self.a, "second-sale.log", [dict(chain[4], timestamp="2026-07-21T00:00:00Z")], 100)
        self.assertNotIn(23, {s["ship_id"] for s in self.db.commander_ships(self.a)})

    def test_buy_swap_and_rebuy_sales_and_shipyard_new_are_applied(self):
        for kind, field in (("ShipyardBuy", "SellShipID"), ("ShipyardSwap", "SellShipID"), ("SellShipOnRebuy", "SellShipId")):
            cid = self.db.upsert_commander("FID-" + kind, kind)
            self.db.store_commander_ship(cid, self.ship(23, "Old"), "2026-01-01T00:00:00Z")
            sale = event(kind, 1, **{field: 23, "ShipType": "asp"})
            if kind == "ShipyardSwap": sale["ShipID"] = 4
            events = [sale]
            if kind == "ShipyardBuy": events.append(event("ShipyardNew", 2, NewShipID=4, ShipType="asp"))
            self.db.apply_commander_journal_delta(cid, kind + ".log", events, 100)
            ids = {s["ship_id"] for s in self.db.commander_ships(cid)}
            self.assertNotIn(23, ids)
            if kind != "SellShipOnRebuy": self.assertIn(4, ids)
            self.assertEqual(self._deleted_ids(cid), [])

    def test_rebuild_sales_only_and_manual_markers_remain_distinct(self):
        from cmdrhelper.fleet_reconstruction import reconstruct_fleet
        self._deletion_fleet()
        self.db.delete_commander_ship(self.a, 23)
        self.db.delete_commander_ship(self.b, 23)
        chain = self._sale_chain()
        path = self._write_sale_journal([chain[0], chain[4]])
        self.db.apply_commander_journal_delta(self.a, str(path), [chain[4]], 100)
        self.assertEqual(self._deleted_ids(self.a), [23])
        fleet = reconstruct_fleet([path], "FID-A")
        self.assertEqual(len(fleet), 0)
        self.db.rebuild_commander_fleet(self.a, fleet)
        self.assertEqual(self._deleted_ids(self.a), [])
        self.assertEqual(self._deleted_ids(self.b), [23])
        self.assertNotIn(23, {s["ship_id"] for s in self.db.commander_ships(self.a)})
        self.db.apply_commander_journal_delta(self.a, "after-rebuild-old.log", [chain[2]], 100)
        self.assertNotIn(23, {s["ship_id"] for s in self.db.commander_ships(self.a)})

    def test_sale_and_journal_cursor_rollback_together_on_error(self):
        self._deletion_fleet()
        with self.db._connect() as con:
            con.execute("CREATE TRIGGER block_sale BEFORE DELETE ON commander_ships BEGIN SELECT RAISE(ABORT,'test'); END")
        with self.assertRaises(sqlite3.Error):
            self.db.apply_commander_journal_delta(self.a, "sale-fails.log", [self._sale_chain()[4]], 100)
        with self.db._connect() as con:
            self.assertEqual(con.execute("SELECT * FROM commander_ship_sales").fetchall(), [])
            self.assertEqual(con.execute("SELECT * FROM journal_sessions WHERE journal_file='sale-fails.log'").fetchall(), [])
        self.assertIn(23, {s["ship_id"] for s in self.db.commander_ships(self.a)})

    def test_runtime_reader_and_shuffled_archive_observe_sale_order(self):
        from cmdrhelper.fleet_reconstruction import reconstruct_fleet
        chain = self._sale_chain()
        path = self._write_sale_journal(chain)
        runtime = read_latest_state(path.parent)
        self.assertNotIn(23, {s["loadout"].ship_id for s in runtime["fleet_ships"]})
        self.assertEqual(runtime["ship_loadout"].ship_id, 36)
        # An old ownership event in a later-named journal must still precede the sale.
        old_path = self._write_sale_journal([chain[0], chain[2]], "Journal.2026-07-22T000000.01.log")
        fleet = reconstruct_fleet([old_path, path], "FID-A")
        self.assertNotIn(23, {s["loadout"].ship_id for s in fleet})

    def test_fleet_marker_migration_is_additive_and_idempotent(self):
        self._deletion_fleet()
        before = self.db.commander_ships(self.a)
        with self.db._connect() as con:
            con.execute("DROP TABLE commander_deleted_ships")
            con.execute("PRAGMA user_version=17")
        self.db = CMDRDatabase(self.path)
        self.assertEqual(self.db.commander_ships(self.a), before)
        self.assertEqual(self._deleted_ids(self.a), [])
        self.db.delete_commander_ship(self.a, 23)
        self.db = CMDRDatabase(self.path)
        self.assertEqual(self._deleted_ids(self.a), [23])
        with self.db._connect() as con:
            self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
            self.assertEqual(con.execute("PRAGMA foreign_key_check").fetchall(), [])

    def test_delete_commit_settings_and_file_failures_restore_all_resources(self):
        from contextlib import contextmanager
        from unittest.mock import patch
        from PySide6.QtCore import QSettings
        from cmdrhelper.ui.fleet_actions import reversible_image_removal
        images, settings, root, source = self._personal_image_environment()
        self._deletion_fleet()
        image = images.import_ship_image(settings, "FID-A", 23, source)
        original = image.read_bytes()
        connect = self.db._connect
        @contextmanager
        def failed_commit():
            con = connect()
            try:
                yield con
                con.rollback()
                raise sqlite3.OperationalError("Simulated commit failure")
            finally:
                con.close()
        with self.assertRaises(sqlite3.Error):
            with reversible_image_removal(settings, "FID-A", 23) as cleanup:
                with patch.object(self.db, "_connect", side_effect=failed_commit):
                    self.db.delete_commander_ship(self.a, 23, before_commit=cleanup)
        self.assertEqual(self._deleted_ids(self.a), [])
        self.assertEqual(image.read_bytes(), original)
        self.assertEqual(images.personal_ship_image(settings, "FID-A", 23), image)
        for failure in (patch.object(settings, "status", side_effect=[QSettings.AccessError, QSettings.NoError]),
                        patch.object(Path, "unlink", side_effect=PermissionError("locked image"))):
            with failure, self.assertRaises(OSError):
                with reversible_image_removal(settings, "FID-A", 23) as cleanup:
                    self.db.delete_commander_ship(self.a, 23, before_commit=cleanup)
            self.assertEqual(self._deleted_ids(self.a), [])
            self.assertEqual(len(self.db.commander_ships(self.a)), 3)
            self.assertEqual(image.read_bytes(), original)
            self.assertEqual(images.personal_ship_image(settings, "FID-A", 23), image)

    def test_rebuild_preserves_explicit_live_ship_even_with_newer_archive_facts(self):
        from cmdrhelper.fleet_reconstruction import reconstruct_fleet
        self._deletion_fleet()
        path, _ = self._fleet_journal(Path(self.tmp.name) / "journals")
        fleet = reconstruct_fleet([path], "FID-A")
        self.db.rebuild_commander_fleet(self.a, fleet, live_ship_id=4)
        self.assertEqual(self.db.commander_last_ship(self.a)["ship_id"], 4)
        with self.assertRaisesRegex(ValueError, "active_ship"):
            self.db.delete_commander_ship(self.a, 4)

    def test_rebuild_identity_isolation_and_publish_failure_preserve_markers(self):
        from cmdrhelper.fleet_reconstruction import reconstruct_fleet
        self._deletion_fleet()
        self.db.delete_commander_ship(self.a, 23)
        folder = Path(self.tmp.name) / "journals"
        own, _ = self._fleet_journal(folder)
        other, _ = self._fleet_journal(folder, "FID-B", "Journal.2026-02-02T000000.01.log")
        other.write_text(other.read_text().replace("Betonmischer", "Other commander"))
        fleet = reconstruct_fleet([own, other], "FID-A")
        self.assertEqual(next(i["loadout"].ship_name for i in fleet if i["loadout"].ship_id == 23), "Betonmischer")
        before = self.db.commander_ships(self.a)
        with self.db._connect() as con:
            con.execute("CREATE TRIGGER fail_rebuild BEFORE INSERT ON commander_ships BEGIN SELECT RAISE(ABORT,'test'); END")
        with self.assertRaises(sqlite3.Error):
            self.db.rebuild_commander_fleet(self.a, fleet)
        self.assertEqual(self.db.commander_ships(self.a), before)
        self.assertEqual(self._deleted_ids(self.a), [23])

    def _deletion_fleet(self):
        for cid in (self.a, self.b):
            for sid in (23, 4, 1):
                ship = self.ship(sid, f"Ship {sid}", "type9" if sid == 23 else "asp")
                ship.ship_ident = "FAB-38"
                self.db.store_commander_ship(cid, ship, f"2026-01-0{3 if sid == 1 else 2}T00:00:00Z")

    def _deleted_ids(self, commander_id):
        with self.db._connect() as con:
            return [r[0] for r in con.execute("SELECT ship_id FROM commander_deleted_ships WHERE commander_id=?", (commander_id,))]

    def _fleet_journal(self, folder, fid="FID-A", filename="Journal.2026-02-01T000000.01.log"):
        folder.mkdir(exist_ok=True)
        events = [event("Commander", 0, FID=fid, Name="Alpha"),
                  event("LoadGame", 1, FID=fid, ShipID=23, Ship="type9", ShipIdent="FAB-38"),
                  event("Loadout", 2, ShipID=23, Ship="type9", ShipName="Betonmischer", ShipIdent="FAB-38", Modules=[]),
                  event("Loadout", 3, ShipID=4, Ship="asp", ShipName="Erft-Habicht", ShipIdent="FAB-38", Modules=[]),
                  event("Loadout", 4, ShipID=1, Ship="cobramkv", ShipName="Current", Modules=[]),
                  event("Scan", 5, BodyID=123, BodyName="Must not import"),
                  event("MissionAccepted", 6, MissionID=456)]
        path = folder / filename
        path.write_text("".join(json.dumps(e)+"\n" for e in events))
        return path, events

    def test_manual_deletion_is_atomic_scoped_and_survives_startup_and_catchup(self):
        from cmdrhelper.journal_catchup import capture, catch_up
        self._deletion_fleet()
        self.db.delete_commander_ship(self.a, 23)
        self.assertEqual(self._deleted_ids(self.a), [23])
        self.assertEqual({s["ship_id"] for s in self.db.commander_ships(self.a)}, {1, 4})
        self.assertIn(23, {s["ship_id"] for s in self.db.commander_ships(self.b)})
        self.db = CMDRDatabase(self.path)
        self.db.store_commander_ship(self.a, self.ship(23, "Historical"), "2026-01-01T00:00:00Z")
        self.db.store_commander_fleet(self.a, [{"loadout": self.ship(23, "Historical"), "is_current": True}])
        folder = Path(self.tmp.name) / "journals"
        path, events = self._fleet_journal(folder)
        original = path.read_bytes()
        catch_up(self.db, capture(self.db, folder))
        self.assertEqual(self._deleted_ids(self.a), [23])
        self.assertNotIn(23, {s["ship_id"] for s in self.db.commander_ships(self.a)})
        self.assertEqual(path.read_bytes(), original)
        with self.db._connect() as con:
            self.assertTrue(con.execute("SELECT last_read_offset FROM journal_sessions WHERE journal_file=?", (str(path),)).fetchone()[0])

    def test_manual_deletion_guards_active_and_rolls_back_sql_and_image_failures(self):
        from unittest.mock import patch
        from cmdrhelper.ui.fleet_actions import reversible_image_removal
        images, settings, root, source = self._personal_image_environment()
        self._deletion_fleet()
        original = images.import_ship_image(settings, "FID-A", 23, source)
        content = original.read_bytes()
        with self.assertRaisesRegex(ValueError, "active_ship"):
            self.db.delete_commander_ship(self.a, 1)
        with self.assertRaisesRegex(ValueError, "active_ship"):
            self.db.delete_commander_ship(self.a, 23, live_ship_id=23)
        with self.db._connect() as con:
            con.execute("CREATE TRIGGER fail_fleet_delete BEFORE DELETE ON commander_ships BEGIN SELECT RAISE(ABORT,'test'); END")
        with self.assertRaises(sqlite3.Error):
            self.db.delete_commander_ship(self.a, 23)
        self.assertEqual(self._deleted_ids(self.a), [])
        with self.db._connect() as con:
            con.execute("DROP TRIGGER fail_fleet_delete")
        with self.assertRaises(OSError):
            with reversible_image_removal(settings, "FID-A", 23) as remove:
                def fail_after_cleanup():
                    remove()
                    raise OSError("Simulated persistence failure")
                self.db.delete_commander_ship(self.a, 23, before_commit=fail_after_cleanup)
        self.assertEqual(original.read_bytes(), content)
        self.assertEqual(images.personal_ship_image(settings, "FID-A", 23), original)
        self.assertEqual(self._deleted_ids(self.a), [])
        self.assertEqual(len(self.db.commander_ships(self.a)), 3)

    def test_delete_ui_cancel_confirm_counts_images_and_sort_filter(self):
        from unittest.mock import patch
        from PySide6.QtWidgets import QPushButton
        images, settings, root, source = self._personal_image_environment()
        self._deletion_fleet()
        equipped = self.ship(23, "Ship 23", "type9", modules=({"Slot": "FighterBay01", "Item": "int_fighterbay_size5_class1"},))
        equipped.ship_ident = "FAB-38"
        self.db.store_commander_ship(self.a, equipped, "2026-01-02T00:00:00Z", is_current=False)
        target = images.import_ship_image(settings, "FID-A", 23, source)
        other = images.import_ship_image(settings, "FID-A", 4, source)
        foreign = images.import_ship_image(settings, "FID-B", 23, source)
        view = self._view(self.a, settings=settings)
        self._select_sort(view, "name", "descending")
        view.fleet_filter_combo.setCurrentIndex(view.fleet_filter_combo.findData("fighter_hangar"))
        ship = next(s for s in self.db.commander_ships(self.a) if s["ship_id"] == 23)
        before = self.db.commander_ships(self.a)
        with patch.object(view, "_confirm_fleet_action", return_value=False):
            view._delete_ship(self.a, "FID-A", ship)
        self.assertEqual(self.db.commander_ships(self.a), before)
        self.assertTrue(target.exists())
        self.assertEqual(self._deleted_ids(self.a), [])
        with patch.object(view, "_confirm_fleet_action", return_value=True):
            view._delete_ship(self.a, "FID-A", ship)
        self.assertEqual(view.fleet_title.text(), tr("commander_view.fleet.title_filtered", visible=0, total=2))
        self.assertEqual(view.fleet_sort_combo.currentData(), "name")
        self.assertEqual(view.fleet_sort_direction_combo.currentData(), "descending")
        self.assertEqual(view.fleet_filter_combo.currentData(), "fighter_hangar")
        self.assertFalse(target.exists())
        self.assertTrue(other.exists() and foreign.exists())
        self.assertIsNone(images.personal_ship_image(settings, "FID-A", 23))
        view.fleet_filter_combo.setCurrentIndex(view.fleet_filter_combo.findData("all"))
        cards = [view.fleet_layout.itemAt(i).widget() for i in range(view.fleet_layout.count())]
        active = next(c for c in cards if c and c.property("shipId") == 1)
        self.assertFalse(active.findChild(QPushButton, "deleteFleetShip").isEnabled())

    def test_fleet_confirmation_defaults_to_cancel_and_requires_explicit_action(self):
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QMessageBox
        view = self._view(self.a)
        observed = []
        def click(cancel):
            dialog = self.app.activeModalWidget()
            observed.append(dialog.defaultButton().text())
            target = dialog.defaultButton() if cancel else next(b for b in dialog.buttons() if dialog.buttonRole(b) == QMessageBox.DestructiveRole)
            target.click()
        QTimer.singleShot(0, lambda: click(True))
        self.assertFalse(view._confirm_fleet_action("Title", "Body", "Delete", True))
        QTimer.singleShot(0, lambda: click(False))
        self.assertTrue(view._confirm_fleet_action("Title", "Body", "Delete", True))
        self.assertEqual(observed, [tr("migration.cancel")] * 2)

    def test_rebuild_is_fleet_only_preserves_other_markers_and_deleted_images(self):
        from cmdrhelper.fleet_reconstruction import reconstruct_fleet
        from cmdrhelper.ui.fleet_actions import reversible_image_removal
        images, settings, root, source = self._personal_image_environment()
        self._deletion_fleet()
        personal = images.import_ship_image(settings, "FID-A", 23, source)
        with reversible_image_removal(settings, "FID-A", 23) as cleanup:
            self.db.delete_commander_ship(self.a, 23, before_commit=cleanup)
        self.db.delete_commander_ship(self.b, 23)
        path, events = self._fleet_journal(Path(self.tmp.name) / "journals")
        def unrelated():
            with self.db._connect() as con:
                return [line for line in con.iterdump() if not any(t in line for t in ("commander_ships", "commander_deleted_ships"))]
        before = unrelated()
        original = path.read_bytes()
        fleet = reconstruct_fleet([path], "FID-A")
        self.db.rebuild_commander_fleet(self.a, fleet)
        self.assertEqual(unrelated(), before)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual(self._deleted_ids(self.a), [])
        self.assertEqual(self._deleted_ids(self.b), [23])
        self.assertEqual({s["ship_id"] for s in self.db.commander_ships(self.a)}, {1, 4, 23})
        self.assertEqual(self.db.commander_last_ship(self.a)["ship_id"], 1)
        self.assertFalse(personal.exists())
        self.assertIsNone(images.personal_ship_image(settings, "FID-A", 23))
        view = self._view(self.a, settings=settings)
        from cmdrhelper.ui.ship_widgets import ShipImage
        card = next(view.fleet_layout.itemAt(i).widget() for i in range(view.fleet_layout.count()) if view.fleet_layout.itemAt(i).widget() and view.fleet_layout.itemAt(i).widget().property("shipId") == 23)
        self.assertEqual(card.findChild(ShipImage)._source_path.name, "standart.png")

    def test_rebuild_ui_cancel_async_confirm_and_read_failure(self):
        from unittest.mock import patch
        from PySide6.QtTest import QTest
        self._deletion_fleet()
        self.db.delete_commander_ship(self.a, 23)
        view = self._view(self.a)
        folder = Path(self.tmp.name) / "journals"
        path, events = self._fleet_journal(folder)
        view.state.journal_folder = folder
        with patch.object(view, "_confirm_fleet_action", return_value=False):
            view._request_fleet_rebuild()
        self.assertEqual(self._deleted_ids(self.a), [23])
        with patch.object(view, "_confirm_fleet_action", return_value=True):
            view._request_fleet_rebuild()
        for _ in range(200):
            if view._fleet_rebuild_id is None: break
            QTest.qWait(10)
        self.assertIsNone(view._fleet_rebuild_id)
        self.assertEqual(self._deleted_ids(self.a), [])
        self.assertEqual(view.fleet_action_status.text(), tr("commander_view.fleet.rebuild.done"))
        self.db.delete_commander_ship(self.a, 23)
        path.write_text("broken json\n")
        with patch.object(view, "_confirm_fleet_action", return_value=True):
            view._request_fleet_rebuild()
        for _ in range(200):
            if view._fleet_rebuild_id is None: break
            QTest.qWait(10)
        self.assertEqual(self._deleted_ids(self.a), [23])
        self.assertEqual(view.fleet_action_status.text(), tr("commander_view.fleet.rebuild.error"))

    def test_only_new_confirmed_live_activation_can_lift_deletion(self):
        from datetime import datetime, timezone, timedelta
        self._deletion_fleet()
        self.db.delete_commander_ship(self.a, 23)
        old = event("Loadout", 1, ShipID=23, Ship="type9", Modules=[])
        self.db.apply_commander_journal_delta(self.a, "old.log", [old], 10, live_current=True)
        self.assertEqual(self._deleted_ids(self.a), [23])
        now = datetime.now(timezone.utc)
        with self.db._connect() as con:
            con.execute("UPDATE commander_deleted_ships SET deleted_at=?", ((now-timedelta(seconds=10)).isoformat(),))
        new = dict(old, timestamp=now.isoformat())
        self.db.apply_commander_journal_delta(self.a, "history.log", [new], 10)
        self.assertEqual(self._deleted_ids(self.a), [23])
        self.db.apply_commander_journal_delta(self.a, "live.log", [new], 10, live_current=True)
        self.assertEqual(self._deleted_ids(self.a), [])
        self.assertEqual(self.db.commander_last_ship(self.a)["ship_id"], 23)
        with self.assertRaisesRegex(ValueError, "active_ship"):
            self.db.delete_commander_ship(self.a, 23)

    def test_standard_ship_image_priority_and_emergency_placeholder(self):
        from unittest.mock import patch
        from cmdrhelper.ui import ship_assets as assets
        images, settings, root, source = self._personal_image_environment()
        asset_root = Path(self.tmp.name)
        standard = asset_root / "standart.png"
        standard.write_bytes(source.read_bytes())
        personal = images.import_ship_image(settings, "FID-A", 12, source)
        with patch.object(assets, "SHIP_ASSET_DIR", asset_root):
            self.assertEqual(assets.ship_preview("cobramkv", 72, 52)[1], standard)
            specific = asset_root / "cobramkv.png"
            specific.write_bytes(source.read_bytes())
            self.assertEqual(assets.ship_preview("cobramkv", 72, 52)[1], specific)
            self.assertEqual(assets.ship_preview("cobramkv", 72, 52, personal_path=personal)[1], personal)
            specific.write_bytes(b"broken type image")
            self.assertEqual(assets.ship_preview("cobramkv", 72, 52)[1], standard)
            standard.write_bytes(b"broken standard image")
            self.assertEqual(assets.ship_preview("cobramkv", 72, 52), (None, None))
            standard.unlink()
            self.assertEqual(assets.ship_preview("cobramkv", 72, 52), (None, None))

    def test_bundled_standard_image_active_list_remove_and_double_click(self):
        from PySide6.QtTest import QTest
        from cmdrhelper.ui.ship_assets import SHIP_ASSET_DIR
        from cmdrhelper.ui.ship_widgets import ShipImage, ShipImageViewer
        images, settings, root, source = self._personal_image_environment()
        standard = SHIP_ASSET_DIR / "standart.png"
        self.assertTrue(standard.is_file())
        self.db.store_commander_ship(self.a, self.ship(12, "Standardmotiv", "unknown_no_asset"), "T1")
        view = self._view(self.a, settings=settings)
        view.tabs.setCurrentIndex(4)
        self.app.processEvents()
        def assert_source(expected):
            self.assertEqual(view.current_ship_image._source_path, expected)
            picture = view.fleet_layout.itemAt(0).widget().findChild(ShipImage)
            self.assertEqual(picture._source_path, expected)
            self.assertTrue(picture.property("hasShipImage"))
        assert_source(standard)
        personal = images.import_ship_image(settings, "FID-A", 12, source)
        view._refresh_ship_for_current_commander()
        assert_source(personal)
        view._remove_ship_image("FID-A", 12)
        assert_source(standard)
        QTest.mouseDClick(view.current_ship_image, Qt.LeftButton)
        self.app.processEvents()
        viewer = view.findChild(ShipImageViewer)
        self.assertIsNotNone(viewer)
        self.assertTrue(viewer.isVisible())
        self.assertEqual(viewer.windowTitle(), "Standardmotiv")
        viewer.close()

    def test_personal_ship_image_viewer_uses_full_source_and_preserves_settings(self):
        from PySide6.QtGui import QImage
        from PySide6.QtTest import QTest
        from cmdrhelper.ui.ship_widgets import ShipImage, ShipImageViewer
        images, settings, root, source = self._personal_image_environment()
        full_image = QImage(1600, 900, QImage.Format_RGB32)
        full_image.fill(QColor("gray"))
        full_image.save(str(source), "PNG")
        images.import_ship_image(settings, "FID-A", 12, source)
        self.db.store_commander_ship(self.a, self.ship(12, "Erft-Krähe", "cobramkv"), "T1")
        before = {key: settings.value(key) for key in settings.allKeys()}
        view = self._view(self.a, settings=settings)
        view.tabs.setCurrentIndex(4)
        self.app.processEvents()
        card = view.fleet_layout.itemAt(0).widget()
        picture = card.findChild(ShipImage)
        header = card.findChild(QToolButton)
        QTest.mouseClick(picture, Qt.LeftButton)
        self.assertFalse(header.isChecked())
        self.assertEqual(view.findChildren(ShipImageViewer), [])
        for thumbnail in (picture, view.current_ship_image):
            QTest.mouseDClick(thumbnail, Qt.LeftButton)
            self.app.processEvents()
            viewer = next(window for window in view.findChildren(ShipImageViewer) if window.isVisible())
            self.assertEqual(viewer.windowTitle(), "Erft-Krähe")
            self.assertEqual(viewer.canvas.image.size(), full_image.size())
            self.assertGreater(viewer.canvas.image.width(), thumbnail.pixmap().width())
            self.assertTrue(view.screen().availableGeometry().contains(viewer.geometry()))
            for width, height in ((600, 500), (900, 300)):
                viewer.resize(width, height)
                self.app.processEvents()
                rect = viewer.canvas.image_rect()
                self.assertTrue(viewer.canvas.rect().contains(rect))
                self.assertAlmostEqual(rect.width() / rect.height(), 1600 / 900, delta=.02)
                self.assertTrue(rect.width() == viewer.canvas.width() or rect.height() == viewer.canvas.height())
                viewer.grab()
            QTest.keyClick(viewer, Qt.Key_Escape)
            self.assertFalse(viewer.isVisible())
        self.assertFalse(header.isChecked())
        self.assertEqual({key: settings.value(key) for key in settings.allKeys()}, before)

    def test_type_image_viewer_uses_displayed_fallback_and_closes(self):
        from unittest.mock import patch
        from PySide6.QtGui import QImage
        from PySide6.QtTest import QTest
        from cmdrhelper.ui import ship_assets
        from cmdrhelper.ui.ship_widgets import ShipImageViewer
        images, settings, root, source = self._personal_image_environment()
        personal = images.import_ship_image(settings, "FID-A", 12, source)
        personal.write_bytes(b"broken personal image")
        image = QImage(500, 1000, QImage.Format_RGB32)
        image.fill(QColor("gray"))
        image.save(str(Path(self.tmp.name) / "cobramkv.png"))
        self.db.store_commander_ship(self.a, self.ship(12, "Portrait", "cobramkv"), "T1")
        with patch.object(ship_assets, "SHIP_ASSET_DIR", Path(self.tmp.name)):
            view = self._view(self.a, settings=settings)
        QTest.mouseDClick(view.current_ship_image, Qt.LeftButton)
        self.app.processEvents()
        viewer = view.findChild(ShipImageViewer)
        self.assertIsNotNone(viewer)
        self.assertEqual(viewer.canvas.image.size(), image.size())
        self.assertEqual(viewer.windowTitle(), "Portrait")
        self.assertAlmostEqual(viewer.canvas.image_rect().width() / viewer.canvas.image_rect().height(), .5, delta=.01)
        viewer.close()
        self.assertFalse(viewer.isVisible())

    def test_image_viewer_placeholder_missing_file_and_right_click_do_nothing(self):
        from unittest.mock import patch
        from cmdrhelper.ui import ship_assets
        asset_patch = patch.object(ship_assets, "SHIP_ASSET_DIR", Path(self.tmp.name))
        asset_patch.start()
        self.addCleanup(asset_patch.stop)
        from PySide6.QtTest import QTest
        from cmdrhelper.ui.ship_widgets import ShipImageViewer
        images, settings, root, source = self._personal_image_environment()
        self.db.store_commander_ship(self.a, self.ship(12, "Empty", "unknown_no_asset"), "T1")
        view = self._view(self.a, settings=settings)
        picture = view.current_ship_image
        QTest.mouseDClick(picture, Qt.LeftButton)
        self.assertEqual(view.findChildren(ShipImageViewer), [])
        saved = images.import_ship_image(settings, "FID-A", 12, source)
        view._refresh_ship_for_current_commander()
        QTest.mouseDClick(picture, Qt.RightButton)
        self.assertEqual(view.findChildren(ShipImageViewer), [])
        saved.unlink()
        QTest.mouseDClick(picture, Qt.LeftButton)
        self.assertEqual(view.findChildren(ShipImageViewer), [])

    def test_image_viewer_geometry_handles_small_and_offset_screens(self):
        from PySide6.QtCore import QSize, QRect
        from cmdrhelper.ui.ship_widgets import ShipImageViewer
        for screen in (QRect(0, 0, 800, 600), QRect(1920, 40, 1280, 984),
                       QRect(-2560, -300, 2560, 1400), QRect(0, 0, 300, 200)):
            for image_size in (QSize(8000, 4500), QSize(200, 400), QSize(40, 20)):
                geometry = ShipImageViewer.initial_geometry(image_size, screen)
                self.assertTrue(screen.contains(geometry))
                self.assertLessEqual(abs(geometry.center().x() - screen.center().x()), 1)
                self.assertLessEqual(abs(geometry.center().y() - screen.center().y()), 1)

    def test_personal_image_platform_path_semantics(self):
        from pathlib import PureWindowsPath, PurePosixPath
        from unittest.mock import patch
        from cmdrhelper.ui import personal_ship_images as images
        for factory, location in (
            (PurePosixPath, "/home/Langer Benutzer Ä/local app/CMDRHelper"),
            (PureWindowsPath, r"C:\Users\Langer Benutzer Ä\AppData\Roaming\CMDRHelper"),
            (PureWindowsPath, "D:/Profile/Ünicode User/CMDRHelper"),
        ):
            with patch.object(images.QStandardPaths, "writableLocation", return_value=location) as query, \
                    patch.object(images, "Path", factory):
                result = images.ship_images_directory()
                self.assertEqual(result, factory(location) / "ship_images")
                self.assertTrue(result.is_absolute())
                query.assert_called_once_with(images.QStandardPaths.AppDataLocation)
        with patch.object(images.QStandardPaths, "writableLocation", return_value=""):
            with self.assertRaises(OSError):
                images.ship_images_directory()

    def test_carrier_image_identity_copy_removal_and_ship_isolation(self):
        images, settings, root, source = self._personal_image_environment()
        original = source.read_bytes()
        ship = images.import_ship_image(settings, "FID-A", 42, source)
        carrier = images.import_carrier_image(settings, "FID-A", 42, source)
        other = images.import_carrier_image(settings, "FID-B", 42, source)
        second = images.import_carrier_image(settings, "FID-A", 43, source)
        self.assertEqual(carrier.parent, root / "carrier_images")
        self.assertEqual(settings.value(images._settings_key("FID-A", 42, "carrier")), carrier.name)
        self.assertNotIn(str(source), str([settings.value(k) for k in settings.allKeys()]))
        self.assertEqual(images.personal_carrier_image(settings, "FID-A", 42), carrier)
        images.remove_carrier_image(settings, "FID-A", 42)
        self.assertFalse(carrier.exists())
        self.assertIsNone(images.personal_carrier_image(settings, "FID-A", 42))
        for path in (ship, other, second):
            self.assertTrue(path.exists())
        self.assertEqual(source.read_bytes(), original)

    def test_carrier_image_ui_select_remove_viewer_and_no_tracking_changes(self):
        from unittest.mock import patch
        from PySide6.QtGui import QImage
        from PySide6.QtTest import QTest
        from cmdrhelper.ui.ship_assets import resolve_standard_ship_image
        from cmdrhelper.ui.ship_widgets import ShipImageViewer
        images, settings, root, source = self._personal_image_environment()
        image = QImage(1600, 900, QImage.Format_RGB32)
        image.fill(QColor("gray"))
        image.save(str(source), "PNG")
        self.db.store_commander_carrier(self.a, {"carrier_id": 42, "carrier_name": "[EOT] = RHEIN-ERFT =", "callsign": "ABC-123", "system_name": "Sol", "last_updated": "2026-09-16"})
        view = self._view(self.a, settings=settings)
        view.tabs.setCurrentIndex(4)
        # WAL checkpoints can change the physical DB bytes after read-only UI
        # queries. Compare the complete logical data, including tracking tables.
        with self.db._connect() as con:
            before = tuple(con.iterdump())
        self.assertEqual(view.carrier_image._source_path, resolve_standard_ship_image())
        self.assertTrue(view.carrier_select_image.isEnabled())
        self.assertFalse(view.carrier_remove_image.isEnabled())
        with patch("cmdrhelper.ui.commander_view.QFileDialog.getOpenFileName", return_value=("", "")):
            view.carrier_select_image.click()
        self.assertIsNone(images.personal_carrier_image(settings, "FID-A", 42))
        with patch("cmdrhelper.ui.commander_view.QFileDialog.getOpenFileName", return_value=(str(source), "")) as dialog:
            view.carrier_select_image.click()
            self.assertNotIn("options", dialog.call_args.kwargs)
        personal = images.personal_carrier_image(settings, "FID-A", 42)
        self.assertEqual(view.carrier_image._source_path, personal)
        for expected_size in (image.size(), None):
            QTest.mouseDClick(view.carrier_image, Qt.LeftButton)
            self.app.processEvents()
            viewer = next(w for w in view.findChildren(ShipImageViewer) if w.isVisible())
            self.assertEqual(viewer.windowTitle(), "[EOT] = RHEIN-ERFT =")
            if expected_size:
                self.assertEqual(viewer.canvas.image.size(), expected_size)
            QTest.keyClick(viewer, Qt.Key_Escape)
            self.assertFalse(viewer.isVisible())
            view.carrier_remove_image.click()
            self.assertEqual(view.carrier_image._source_path, resolve_standard_ship_image())
        self.assertFalse(personal.exists())
        self.assertTrue(source.exists())
        with self.db._connect() as con:
            self.assertEqual(tuple(con.iterdump()), before)

    def test_carrier_fallback_never_uses_ship_type_and_handles_broken_images(self):
        from unittest.mock import patch
        from cmdrhelper.ui import ship_assets as assets
        from cmdrhelper.ui.ship_widgets import ShipImage, ShipImageViewer
        from PySide6.QtTest import QTest
        images, settings, root, source = self._personal_image_environment()
        with patch.object(assets, "SHIP_ASSET_DIR", source.parent), \
                patch.object(assets, "resolve_ship_image", side_effect=AssertionError("No ship types for carriers")):
            widget = ShipImage(144, 100, preview_resolver=assets.carrier_preview)
            self.addCleanup(widget.deleteLater)
            widget.set_ship("cobramkv", source, "Carrier")
            self.assertEqual(widget._source_path, source)
            for content in (None, b"broken"):
                if content:
                    (source.parent / "standart.png").write_bytes(content)
                widget.set_ship("cobramkv")
                self.assertFalse(widget.property("hasShipImage"))
                QTest.mouseDClick(widget, Qt.LeftButton)
                self.assertEqual(widget.findChildren(ShipImageViewer), [])

    def test_carrier_without_identity_disables_image_actions(self):
        images, settings, root, source = self._personal_image_environment()
        view = self._view(self.a, settings=settings)
        self.assertFalse(view.carrier_select_image.isEnabled())
        self.assertFalse(view.carrier_remove_image.isEnabled())
        self.assertIsNone(view._carrier_image_identity)

    def test_carrier_image_paths_updates_and_translations(self):
        from pathlib import PureWindowsPath, PurePosixPath
        from unittest.mock import patch
        from cmdrhelper.i18n import _TRANSLATIONS
        from cmdrhelper.update import _managed_file_manifest, _remove_new_managed_files
        images, settings, root, source = self._personal_image_environment()
        for factory, location in ((PurePosixPath, "/home/Benutzer Ä/app data"), (PureWindowsPath, r"D:\Users\Benutzer Ä\AppData\Roaming\CMDRHelper")):
            with patch.object(images.QStandardPaths, "writableLocation", return_value=location), patch.object(images, "Path", factory):
                self.assertEqual(images.carrier_images_directory(), factory(location) / "carrier_images")
        saved = images.import_carrier_image(settings, "FID-A", 42, source)
        install = Path(self.tmp.name) / "install"
        install.mkdir()
        self.assertEqual(_managed_file_manifest(install), set())
        _remove_new_managed_files(install, set())
        self.assertTrue(saved.is_file())
        self.assertNotIn(Path(__file__).resolve().parents[1], saved.parents)
        self.assertEqual(len(_TRANSLATIONS), 12)
        for language, texts in _TRANSLATIONS.items():
            for key in ("commander_view.carrier.image.select", "commander_view.carrier.image.error", "commander_view.ship.image.remove"):
                self.assertTrue(texts.get(key), language)

    def _personal_image_environment(self):
        from unittest.mock import patch
        from PySide6.QtCore import QSettings
        from PySide6.QtGui import QImage
        from cmdrhelper.ui import personal_ship_images as images
        root = Path(self.tmp.name) / "Benutzer Ä mit Leerzeichen" / "AppData"
        patcher = patch.object(images.QStandardPaths, "writableLocation", return_value=str(root))
        patcher.start()
        self.addCleanup(patcher.stop)
        settings = QSettings(str(Path(self.tmp.name) / "settings.ini"), QSettings.IniFormat)
        source = Path(self.tmp.name) / "Mein Schiff Ü.PNG"
        image = QImage(100, 50, QImage.Format_RGB32)
        image.fill(QColor("gray"))
        self.assertTrue(image.save(str(source), "PNG"))
        return images, settings, root, source

    def test_personal_image_import_is_private_relative_and_commander_scoped(self):
        images, settings, root, source = self._personal_image_environment()
        result = images.import_ship_image(settings, "FID-A", 12, source)
        self.assertEqual(result.parent, root / "ship_images")
        self.assertNotIn(Path(__file__).resolve().parents[1], result.parents)
        self.assertEqual(result.suffix, ".png")
        self.assertEqual(settings.value(images._settings_key("FID-A", 12)), result.name)
        self.assertNotIn(str(source), str([settings.value(key) for key in settings.allKeys()]))
        source.unlink()  # The source may disappear after import.
        self.assertEqual(images.personal_ship_image(settings, "FID-A", 12), result)
        self.assertIsNone(images.personal_ship_image(settings, "FID-B", 12))
        self.assertIsNone(images.personal_ship_image(settings, "FID-A", 13))
        images.remove_ship_image(settings, "FID-A", 12)
        self.assertFalse(result.exists())
        self.assertIsNone(images.personal_ship_image(settings, "FID-A", 12))

    def test_personal_image_extensions_and_failed_import_preserve_previous(self):
        from PySide6.QtGui import QImage, QImageWriter
        images, settings, root, source = self._personal_image_environment()
        original = source.read_bytes()
        self.assertIn(b"png", [bytes(fmt) for fmt in QImageWriter.supportedImageFormats()])
        for suffix in (".JPG", ".jPeG", ".PNG", ".WebP"):
            selected = source.with_suffix(suffix)
            selected.write_bytes(original)  # Reader validates content, not just suffix.
            self.assertIn("*" + suffix, images.IMAGE_NAME_PATTERNS.split())
            result = images.import_ship_image(settings, "FID-A", 12, selected)
            self.assertFalse(QImage(str(result)).isNull())
        selected.write_bytes(b"invalid")
        with self.assertRaises(ValueError):
            images.import_ship_image(settings, "FID-A", 12, selected)
        self.assertEqual(images.personal_ship_image(settings, "FID-A", 12), result)
        self.assertTrue(result.is_file())
        self.assertEqual(len(list((root / "ship_images").glob("*.png"))), 1)

    def test_personal_image_rejects_unsafe_references_and_write_failure(self):
        from unittest.mock import patch
        images, settings, root, source = self._personal_image_environment()
        for reference in (str(source), r"C:\Users\Me\photo.PNG", "../photo.png", r"..\photo.png"):
            settings.setValue(images._settings_key("FID-A", 12), reference)
            self.assertIsNone(images.personal_ship_image(settings, "FID-A", 12))
        with patch.object(images.QSaveFile, "open", return_value=False):
            with self.assertRaises(OSError):
                images.import_ship_image(settings, "FID-A", 12, source)
        self.assertTrue(source.is_file())
        self.assertEqual(list((root / "ship_images").iterdir()), [])

    def test_personal_image_ui_dialog_cancel_select_remove_and_fallback(self):
        from unittest.mock import patch
        from cmdrhelper.ui import ship_assets
        from cmdrhelper.ui.ship_widgets import ShipImage
        images, settings, root, source = self._personal_image_environment()
        self.db.store_commander_ship(self.a, self.ship(12, "Cobra", "cobramkv"), "T1")
        before = self.db.commander_ships(self.a)
        view = self._view(self.a, settings=settings)
        with patch("cmdrhelper.ui.commander_view.QFileDialog.getOpenFileName", return_value=("", "")):
            view._select_ship_image("FID-A", 12)
        self.assertIsNone(images.personal_ship_image(settings, "FID-A", 12))
        with patch("cmdrhelper.ui.commander_view.QFileDialog.getOpenFileName", return_value=(str(source), "")) as dialog:
            view._select_ship_image("FID-A", 12)
            self.assertNotIn("options", dialog.call_args.kwargs)  # Native default.
        self.assertTrue(view.current_ship_image.property("hasShipImage"))
        card = view.fleet_layout.itemAt(0).widget()
        self.assertTrue(card.findChild(ShipImage).property("hasShipImage"))
        with patch.object(ship_assets, "SHIP_ASSET_DIR", Path(self.tmp.name)):
            (Path(self.tmp.name) / "cobramkv.png").write_bytes(source.read_bytes())
            view._remove_ship_image("FID-A", 12)
            self.assertTrue(view.current_ship_image.property("hasShipImage"))
        self.assertEqual(self.db.commander_ships(self.a), before)

    def test_personal_images_outside_updater_manifest_and_translated(self):
        from cmdrhelper.update import _managed_file_manifest, _remove_new_managed_files
        from cmdrhelper.i18n import _TRANSLATIONS
        images, settings, root, source = self._personal_image_environment()
        saved = images.import_ship_image(settings, "FID-A", 12, source)
        install = Path(self.tmp.name) / "installation"
        install.mkdir()
        (install / "main.py").write_text("# test")
        manifest = _managed_file_manifest(install)
        self.assertEqual(manifest, {"main.py"})
        _remove_new_managed_files(install, set())
        self.assertTrue(saved.is_file())
        for language, translations in _TRANSLATIONS.items():
            for key in ("select", "remove", "filter", "error"):
                self.assertTrue(translations.get("commander_view.ship.image." + key), language)

    def test_local_ship_image_resolver_and_names(self):
        from unittest.mock import patch
        from cmdrhelper.ui import ship_assets as assets
        root = Path(self.tmp.name) / "ships"
        root.mkdir()
        image = root / "cobramkv.png"
        image.write_bytes(b"invalid")
        with patch.object(assets, "SHIP_ASSET_DIR", root):
            self.assertEqual(assets.resolve_ship_image(" CobraMkV "), image)
            self.assertEqual(assets.resolve_ship_image("Cobra Mk V"), image)
            for value in ("../cobramkv", "/cobramkv", "", None, "mandalay"):
                self.assertIsNone(assets.resolve_ship_image(value))
            (root / "mandalay.png").symlink_to(Path(self.tmp.name) / "outside.png")
            (Path(self.tmp.name) / "outside.png").write_bytes(b"invalid")
            self.assertIsNone(assets.resolve_ship_image("mandalay"))
        self.assertEqual(assets.ship_display_name("cobramkv"), "Cobra Mk V")
        self.assertEqual(assets.ship_display_name("mandalay"), "Mandalay")
        self.assertEqual(assets.ship_display_name("panthermkii"), "Panther Clipper Mk II")
        self.assertEqual(assets.ship_display_name("smallcombat01_nx"), "smallcombat01_nx")

    def test_ship_thumbnail_cache_and_invalid_image_fallback(self):
        from unittest.mock import patch
        from PySide6.QtGui import QImage
        from cmdrhelper.ui import ship_assets as assets
        from cmdrhelper.ui.ship_widgets import ShipImage
        root = Path(self.tmp.name)
        image = QImage(200, 100, QImage.Format_RGB32)
        image.fill(QColor("gray"))
        self.assertTrue(image.save(str(root / "cobramkv.png")))
        assets._thumbnail.cache_clear()
        with patch.object(assets, "SHIP_ASSET_DIR", root):
            first = assets.ship_pixmap("cobramkv", 72, 52)
            self.assertIsNotNone(first)
            self.assertIs(first, assets.ship_pixmap("CobraMkV", 72, 52))
            self.assertEqual(assets._thumbnail.cache_info().hits, 1)
            self.assertEqual(first.width(), 72)
            self.assertEqual(first.height(), 36)
            widget = ShipImage(72, 52)
            widget.set_ship("cobramkv")
            self.assertTrue(widget.property("hasShipImage"))
            (root / "cobramkv.png").write_bytes(b"broken image")
            widget.set_ship("cobramkv")
            self.assertFalse(widget.property("hasShipImage"))
            widget.set_ship("mandalay")
            self.assertFalse(widget.property("hasShipImage"))
            widget.grab()  # Also exercise placeholder painting.
        assets._thumbnail.cache_clear()

    def test_ship_presentation_resizes_and_does_not_modify_data(self):
        from unittest.mock import patch
        from cmdrhelper.ui import ship_assets
        asset_patch = patch.object(ship_assets, "SHIP_ASSET_DIR", Path(self.tmp.name))
        asset_patch.start()
        self.addCleanup(asset_patch.stop)
        from PySide6.QtTest import QTest
        from cmdrhelper.ui.ship_widgets import ElidedShipLabel, ShipImage
        long_name = "[EOT] = Erft-Krähe = " * 12
        long_location = "Plio Aihm UC-V d2-159 / Ridorana Forge " * 12
        self.db.store_commander_ship(self.a, self.ship(12, long_name, "cobramkv"), "T1",
                                     location={"system_name": long_location})
        before = self.db.commander_ships(self.a)
        view = self._view(self.a)
        view.tabs.setCurrentIndex(4)
        for width, height in ((1920, 1080), (600, 500)):
            view.resize(width, height)
            self.app.processEvents()
            card = view.fleet_layout.itemAt(0).widget()
            header = card.findChild(QToolButton)
            self.assertLess(header.height(), 110)
            self.assertLessEqual(view.fleet_scroll.widget().width(),
                                 view.fleet_scroll.viewport().width())
            self.assertFalse(card.findChild(ShipImage).property("hasShipImage"))
            labels = header.findChildren(ElidedShipLabel)
            self.assertEqual(labels[0].toolTip(), long_name)
            self.assertIn(long_location, labels[-1].toolTip())
            self.assertTrue(header.rect().contains(labels[0].mapTo(header, labels[0].rect().topRight())))
            QTest.mouseClick(header, Qt.LeftButton, pos=labels[0].mapTo(header, labels[0].rect().center()))
            self.assertTrue(header.isChecked())
            picture = header.findChild(ShipImage)
            QTest.mouseClick(header, Qt.LeftButton, pos=picture.mapTo(header, picture.rect().center()))
            self.assertFalse(header.isChecked())
            QTest.mouseClick(header, Qt.LeftButton, pos=header.rect().topRight() + QPoint(-12, 25))
            self.assertTrue(header.isChecked())
            QTest.keyClick(header, Qt.Key_Space)
            self.assertFalse(header.isChecked())
            self.assertIn(long_location, header.toolTip())
            view.grab()
        self.assertEqual(view.current_ship_values["type"].text(), "Cobra Mk V")
        self.assertEqual(view.current_ship_values["name"].toolTip(), long_name)
        self.assertEqual(view.current_ship_values["ship_id"].text(), "12")
        self.assertEqual(self.db.commander_ships(self.a), before)

    def test_active_and_fleet_ship_use_same_local_asset(self):
        from unittest.mock import patch
        from PySide6.QtGui import QImage
        from cmdrhelper.ui import ship_assets as assets
        from cmdrhelper.ui.ship_widgets import ShipImage
        root = Path(self.tmp.name)
        image = QImage(100, 50, QImage.Format_RGB32)
        image.fill(QColor("gray"))
        image.save(str(root / "cobramkv.png"))
        self.db.store_commander_ship(self.a, self.ship(12, "Cobra", "cobramkv"), "T1")
        with patch.object(assets, "SHIP_ASSET_DIR", root):
            view = self._view(self.a)
            self.assertTrue(view.current_ship_image.property("hasShipImage"))
            self.assertTrue(view.fleet_container.findChild(ShipImage).property("hasShipImage"))
            view._refresh_ship(None)
            self.assertFalse(view.current_ship_image.property("hasShipImage"))
            self.assertEqual(view.current_ship_status.text(), "–")

    def test_ship_presentation_reuses_translations_in_all_languages(self):
        from cmdrhelper.i18n import _TRANSLATIONS
        for language, translations in _TRANSLATIONS.items():
            for key in ("commander_view.field.status", "commander_view.fleet.current_marker",
                        "commander_view.ship.location", "commander_view.ship.ship_type",
                        "commander_view.ship.ship_id"):
                self.assertTrue(translations.get(key), (language, key))
        self.assertEqual(len(_TRANSLATIONS), 12)

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
