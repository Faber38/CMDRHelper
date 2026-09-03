from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.journal_index import scan_journal_folder
from cmdrhelper.journal_reader import read_journal_delta, read_latest_state
from cmdrhelper.route_planner.models import ShipLoadoutData


def event(kind, second, **values):
    return {"timestamp": f"2026-01-01T00:00:{second:02d}Z", "event": kind, **values}


class CommanderJournalDeltaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.db = CMDRDatabase(self.folder / "state.db")
        self.commander = self.db.upsert_commander("FID-A", "Alpha")
        self.path = self.folder / "Journal.2026-01-01T000000.01.log"

    def tearDown(self):
        self.temp.cleanup()

    def write(self, events, append=False, complete=True):
        raw = "".join(json.dumps(item) + "\n" for item in events)
        if not complete:
            raw = raw.rstrip("\n")
        with self.path.open("a" if append else "w", encoding="utf-8") as handle:
            handle.write(raw)

    def indexed(self):
        session = scan_journal_folder(self.db, self.folder)[0]
        self.assertEqual(session["commander_id"], self.commander)
        return session

    def apply(self, session):
        events, offset = read_journal_delta(self.path, session["last_read_offset"])
        self.db.apply_commander_journal_delta(
            self.commander, self.path, events, offset
        )
        session["last_read_offset"] = offset
        return events, offset

    def test_analyse_is_idempotent_and_sale_removes_only_matching_species(self):
        self.write([
            event("LoadGame", 0, FID="FID-A", Commander="Alpha"),
            event("Location", 1, StarSystem="Test", SystemAddress=42),
            event("ScanOrganic", 2, SystemAddress=42, Body=1, ScanType="Analyse",
                  Genus_Localised="Stratum", Species_Localised="Stratum Tectonicas"),
        ])
        session = self.indexed()
        self.apply(session)
        self.assertEqual(self.db.commander_summary(self.commander)["unsold_biology"]["findings"], 1)
        events, _ = self.apply(session)
        self.assertEqual(events, [])
        self.assertEqual(self.db.commander_summary(self.commander)["unsold_biology"]["findings"], 1)

        self.write([event("SellOrganicData", 3, BioData=[{
            "Species_Localised": "Stratum Tectonicas"
        }])], append=True)
        session = scan_journal_folder(self.db, self.folder)[0]
        self.apply(session)
        self.assertEqual(self.db.commander_summary(self.commander)["unsold_biology"]["findings"], 0)

    def test_persistent_cartography_survives_empty_delta_and_sale_clears_all(self):
        self.write([
            event("LoadGame", 0, FID="FID-A", Commander="Alpha"),
            event("Location", 1, StarSystem="Test", SystemAddress=42),
            event("Scan", 2, SystemAddress=42, BodyID=1, BodyName="Test 1",
                  PlanetClass="Rocky body", WasDiscovered=False, WasMapped=False),
        ])
        session = self.indexed()
        self.apply(session)
        self.assertEqual(self.db.commander_summary(self.commander)["unsold_cartography"]["bodies"], 1)
        self.apply(session)
        self.assertEqual(self.db.commander_summary(self.commander)["unsold_cartography"]["bodies"], 1)
        self.write([event("MultiSellExplorationData", 3,
                          Discovered=[{"SystemName": "Test"}])], append=True)
        session = scan_journal_folder(self.db, self.folder)[0]
        self.apply(session)
        self.assertEqual(self.db.commander_summary(self.commander)["unsold_cartography"]["bodies"], 0)

    def test_live_cartography_watermark_nav_beacon_mapping_and_commander_separation(self):
        other = self.db.upsert_commander("FID-B", "Bravo")
        self.db.store_commander_unsold_data(
            other, [], [{
                "system_address": 99, "body_id": 1, "system_name": "Other",
                "body_name": "Other 1", "scanned_at": "2025", "mapped_at": "",
                "self_mapped": False, "estimated_value": 10,
                "planet_class": "Rocky body", "terraformable": False,
            }], cartography_factor_func=lambda *_: 1.0,
        )
        self.write([
            event("LoadGame", 0, FID="FID-A", Commander="Alpha"),
            event("Location", 1, StarSystem="First", SystemAddress=41),
            event("Scan", 2, SystemAddress=41, BodyID=1, BodyName="First 1",
                  ScanType="Detailed", PlanetClass="Rocky body"),
            event("Location", 3, StarSystem="Second", SystemAddress=42),
            event("Scan", 4, SystemAddress=42, BodyID=1, BodyName="Second 1",
                  ScanType="Detailed", PlanetClass="Rocky body"),
            event("MultiSellExplorationData", 5,
                  Discovered=[{"SystemName": "First", "NumBodies": 1}]),
            event("Location", 6, StarSystem="Beacon", SystemAddress=43),
            event("Scan", 7, SystemAddress=43, BodyID=1, BodyName="Beacon 1",
                  ScanType="NavBeaconDetail", PlanetClass="Rocky body"),
            event("Location", 8, StarSystem="After", SystemAddress=44),
            event("Scan", 9, SystemAddress=44, BodyID=1, BodyName="After 1",
                  ScanType="Detailed", PlanetClass="Rocky body"),
        ])
        self.apply(self.indexed())
        self.assertEqual(self.db.commander_summary(self.commander)["unsold_cartography"]["bodies"], 1)
        self.assertEqual(self.db.commander_summary(other)["unsold_cartography"]["bodies"], 1)

        # Ein Mapping nach der Verkaufs-Watermark erfasst nur den neuen
        # Mapping-Mehrwert des zuvor verkauften Scans.
        self.db.store_snapshot({
            "system_address": 42, "system": "Second", "last_timestamp": "2026",
            "system_bodies": [{
                "body_id": 1, "name": "Second 1", "body_type": "Planet",
                "planet_class": "Rocky body", "terraformable": False,
                "scan_value": 100, "mapped_value": 500, "current_value": 500,
            }],
        }, self.commander)
        self.write([event("SAAScanComplete", 10, SystemAddress=42, BodyID=1,
                          BodyName="Second 1")], append=True)
        session = scan_journal_folder(self.db, self.folder)[0]
        self.apply(session)
        with self.db._connect() as con:
            rows = con.execute(
                "SELECT system_address,raw_estimated_value,self_mapped "
                "FROM commander_unsold_cartography WHERE commander_id=? "
                "ORDER BY system_address", (self.commander,),
            ).fetchall()
        self.assertEqual([(row[0], row[2]) for row in rows], [(42, 1), (44, 0)])
        self.assertEqual(rows[0][1], 400)
        self.assertEqual(self.db.commander_summary(other)["unsold_cartography"]["bodies"], 1)

        rebuilt = read_latest_state(self.folder, force_full_history=True)
        rebuilt_rows = sorted(
            (row["system_address"], int(row["self_mapped"]))
            for row in rebuilt["unsold_cartography"]
        )
        self.assertEqual(rebuilt_rows, [(42, 1), (44, 0)])

    def test_mission_terminal_events_change_only_the_matching_commander_row(self):
        other = self.db.upsert_commander("FID-B", "Bravo")
        self.db.store_commander_missions(other, [{"mission_id": 7, "name": "Bravo"}])
        self.write([
            event("LoadGame", 0, FID="FID-A", Commander="Alpha"),
            event("MissionAccepted", 1, MissionID=7, Name="Mission_Delivery"),
        ])
        session = self.indexed()
        self.apply(session)
        self.assertTrue(self.db.commander_missions(self.commander)[0]["is_open"])
        self.write([event("MissionCompleted", 2, MissionID=7, Reward=10)], append=True)
        session = scan_journal_folder(self.db, self.folder)[0]
        self.apply(session)
        self.assertFalse(self.db.commander_missions(self.commander)[0]["is_open"])
        self.assertTrue(self.db.commander_missions(other)[0]["is_open"])

    def test_failed_and_abandoned_are_persisted_independently(self):
        self.write([
            event("LoadGame", 0, FID="FID-A", Commander="Alpha"),
            event("MissionAccepted", 1, MissionID=1, Name="Mission_One"),
            event("MissionAccepted", 2, MissionID=2, Name="Mission_Two"),
            event("MissionFailed", 3, MissionID=1),
            event("MissionAbandoned", 4, MissionID=2),
        ])
        self.apply(self.indexed())
        rows = {row["mission_id"]: row for row in self.db.commander_missions(self.commander)}
        self.assertEqual(rows[1]["terminal_state"], "failed")
        self.assertEqual(rows[2]["terminal_state"], "abandoned")
        self.assertFalse(rows[1]["is_open"])
        self.assertFalse(rows[2]["is_open"])

    def test_absent_events_preserve_location_ship_carrier_and_wealth(self):
        self.db.store_commander_location(self.commander, {
            "system_name": "Old", "system_address": 1, "station_name": "",
            "body_name": "", "event_timestamp": "2025", "event_type": "Location"})
        self.db.store_commander_ship(self.commander, ShipLoadoutData(
            ship_id=5, ship_type="Anaconda", modules=({"Slot": "MainEngines"},),
            loadout_complete=True, loadout_stale=False), "2025")
        self.db.store_commander_carrier(self.commander, {
            "carrier_id": 9, "callsign": "AAA-111", "carrier_name": "Mine",
            "system_name": "Old", "system_address": 1, "last_updated": "2025"})
        self.db.store_commander_wealth(self.commander, {
            "credits": 123, "event_timestamp": "2025", "source_event": "LoadGame"})
        self.write([event("Commander", 0, FID="FID-A", Name="Alpha")])
        session = self.indexed()
        self.apply(session)
        summary = self.db.commander_summary(self.commander)
        self.assertEqual(summary["persistent_location"]["system_name"], "Old")
        self.assertEqual(summary["ship"]["modules"], [{"Slot": "MainEngines"}])
        self.assertEqual(summary["carrier"]["carrier_name"], "Mine")
        self.assertEqual(summary["wealth"]["credits"], 123)

    def test_new_location_and_credits_update_without_degrading_complete_modules(self):
        self.db.store_commander_ship(self.commander, ShipLoadoutData(
            ship_id=5, ship_type="Anaconda", modules=({"Slot": "MainEngines"},),
            loadout_complete=True, loadout_stale=False), "2025")
        self.write([
            event("LoadGame", 0, FID="FID-A", Commander="Alpha", Credits=999,
                  Ship="Anaconda", ShipID=5),
            event("FSDJump", 1, StarSystem="New", SystemAddress=99),
        ])
        self.apply(self.indexed())
        summary = self.db.commander_summary(self.commander)
        self.assertEqual(summary["persistent_location"]["system_name"], "New")
        self.assertEqual(summary["wealth"]["credits"], 999)
        self.assertEqual(summary["ship"]["modules"], [{"Slot": "MainEngines"}])
        self.assertTrue(summary["ship"]["loadout_complete"])

    def test_offset_moves_after_commit_but_not_on_error_or_partial_line(self):
        self.write([event("LoadGame", 0, FID="FID-A", Commander="Alpha", Credits=5)])
        session = self.indexed()
        events, offset = read_journal_delta(self.path, 0)
        with patch.object(self.db, "store_commander_wealth", side_effect=RuntimeError("db")):
            with self.assertRaises(RuntimeError):
                self.db.apply_commander_journal_delta(
                    self.commander, self.path, events, offset)
        with self.db._connect() as con:
            self.assertEqual(con.execute("SELECT last_read_offset FROM journal_sessions").fetchone()[0], 0)
        self.db.apply_commander_journal_delta(self.commander, self.path, events, offset)
        with self.db._connect() as con:
            self.assertEqual(con.execute("SELECT last_read_offset FROM journal_sessions").fetchone()[0], offset)
        self.write([event("Location", 1, StarSystem="Partial")], append=True, complete=False)
        events, new_offset = read_journal_delta(self.path, offset)
        self.assertEqual(events, [])
        self.assertEqual(new_offset, offset)

    def test_new_empty_session_does_not_close_mission_from_previous_session(self):
        self.write([
            event("LoadGame", 0, FID="FID-A", Commander="Alpha"),
            event("MissionAccepted", 1, MissionID=44, Name="Mission_Old"),
        ])
        first = self.indexed()
        self.apply(first)
        second = self.folder / "Journal.2026-01-01T000100.01.log"
        second.write_text(json.dumps(event(
            "LoadGame", 2, FID="FID-A", Commander="Alpha"
        )) + "\n", encoding="utf-8")
        session = scan_journal_folder(self.db, self.folder)[-1]
        events, offset = read_journal_delta(second, session["last_read_offset"])
        self.db.apply_commander_journal_delta(self.commander, second, events, offset)
        mission = self.db.commander_missions(self.commander)[0]
        self.assertEqual(mission["mission_id"], 44)
        self.assertTrue(mission["is_open"])

    def test_saa_scan_complete_uses_commander_cached_body_values(self):
        self.db.store_snapshot({
            "system_address": 42,
            "system": "Test",
            "last_timestamp": "2026-01-01T00:00:00Z",
            "system_bodies": [{
                "body_id": 1,
                "name": "Test 1",
                "body_type": "Planet",
                "planet_class": "Rocky body",
                "terraformable": False,
                "scan_value": 100,
                "mapped_value": 500,
                "current_value": 500,
            }],
        }, self.commander)
        self.db.apply_commander_journal_delta(self.commander, self.path, [{
            "timestamp": "2026-01-01T00:00:01Z",
            "event": "SAAScanComplete",
            "SystemAddress": 42,
            "BodyID": 1,
            "BodyName": "Test 1",
        }], 0)
        with self.db._connect() as con:
            columns = {row[1] for row in con.execute("PRAGMA table_info(bodies)")}
            cached = con.execute(
                "SELECT scan_value_cached,mapped_value_cached FROM commander_bodies "
                "WHERE commander_id=? AND system_address=42 AND body_id=1",
                (self.commander,),
            ).fetchone()
            unsold = con.execute(
                "SELECT raw_estimated_value,self_mapped "
                "FROM commander_unsold_cartography WHERE commander_id=? "
                "AND system_address=42 AND body_id=1",
                (self.commander,),
            ).fetchone()
        self.assertNotIn("scan_value", columns)
        self.assertNotIn("mapped_value", columns)
        self.assertEqual(cached, (100, 500))
        self.assertEqual(unsold, (400, 1))

    def test_repair_marker_is_feature_specific_and_failure_is_atomic(self):
        self.write([
            event("LoadGame", 0, FID="FID-A", Commander="Alpha"),
            event("Location", 1, StarSystem="Test", SystemAddress=42),
            event("ScanOrganic", 2, SystemAddress=42, Body=1, ScanType="Analyse",
                  Genus_Localised="Stratum", Species_Localised="Stratum Tectonicas"),
        ])
        sessions = scan_journal_folder(self.db, self.folder)
        with self.db._connect() as con:
            con.execute(
                "INSERT INTO commander_state_repairs"
                "(commander_id,feature,revision,repaired_at) VALUES(?,?,1,?)",
                (self.commander, "unsold", "2025"),
            )
        # Revision 1 enthält noch die alte namensbasierte UC-Semantik.
        self.assertTrue(self.db.commander_state_repair_needed(self.commander, "unsold"))
        with patch.object(self.db, "store_commander_missions", side_effect=RuntimeError("db")):
            with self.assertRaises(RuntimeError):
                self.db.repair_commander_state(
                    self.folder, sessions, self.commander,
                    features=("unsold", "missions"),
                )
        self.assertEqual(self.db.commander_summary(self.commander)["unsold_biology"]["findings"], 0)
        self.assertTrue(self.db.commander_state_repair_needed(self.commander, "unsold"))
        self.db.repair_commander_state(
            self.folder, sessions, self.commander, features=("unsold",)
        )
        self.assertFalse(self.db.commander_state_repair_needed(self.commander, "unsold"))
        self.assertTrue(self.db.commander_state_repair_needed(self.commander, "missions"))


if __name__ == "__main__":
    unittest.main()
