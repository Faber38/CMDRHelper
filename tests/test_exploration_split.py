from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cmdrhelper.database import CMDRDatabase, CommanderMigrationError, SCHEMA_VERSION
from cmdrhelper.journal_reader import read_latest_state


LEGACY_EXPLORATION_SCHEMA = """
CREATE TABLE systems (
 system_address INTEGER PRIMARY KEY, name TEXT NOT NULL DEFAULT '',
 first_seen TEXT NOT NULL DEFAULT '', last_seen TEXT NOT NULL DEFAULT '',
 body_count INTEGER NOT NULL DEFAULT 0, all_bodies_found INTEGER NOT NULL DEFAULT 0,
 x REAL, y REAL, z REAL);
CREATE TABLE bodies (
 system_address INTEGER NOT NULL, body_id INTEGER NOT NULL,
 name TEXT NOT NULL DEFAULT '', short_name TEXT NOT NULL DEFAULT '',
 body_type TEXT NOT NULL DEFAULT '', star_type TEXT NOT NULL DEFAULT '',
 planet_class TEXT NOT NULL DEFAULT '', parent_id INTEGER, mass_em REAL,
 stellar_mass REAL, gravity_g REAL, distance_ls REAL,
 landable INTEGER NOT NULL DEFAULT 0, terraformable INTEGER NOT NULL DEFAULT 0,
 was_discovered INTEGER, was_mapped INTEGER, self_mapped INTEGER NOT NULL DEFAULT 0,
 efficient_mapping INTEGER NOT NULL DEFAULT 0, atmosphere TEXT NOT NULL DEFAULT '',
 volcanism TEXT NOT NULL DEFAULT '', biological_signals INTEGER NOT NULL DEFAULT 0,
 geological_signals INTEGER NOT NULL DEFAULT 0, scan_value INTEGER NOT NULL DEFAULT 0,
 mapped_value INTEGER NOT NULL DEFAULT 0, current_value INTEGER NOT NULL DEFAULT 0,
 high_value INTEGER NOT NULL DEFAULT 0, first_seen TEXT NOT NULL DEFAULT '',
 last_seen TEXT NOT NULL DEFAULT '', PRIMARY KEY(system_address, body_id));
"""


def make_v3(path: Path) -> None:
    CMDRDatabase(path)
    con = sqlite3.connect(path)
    try:
        con.execute("PRAGMA foreign_keys=OFF")
        con.execute("DROP TABLE commander_bodies")
        con.execute("DROP TABLE commander_systems")
        con.execute("DROP TABLE bodies")
        con.execute("DROP TABLE systems")
        con.executescript(LEGACY_EXPLORATION_SCHEMA)
        con.execute("PRAGMA user_version=3")
        con.commit()
    finally:
        con.close()


def write_journal(path: Path, events: list[dict]) -> None:
    path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")


class ExplorationMigrationTests(unittest.TestCase):
    def test_v3_to_v4_preserves_global_and_personal_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy.db"
            make_v3(path)
            with sqlite3.connect(path) as con:
                commander_id = con.execute(
                    "INSERT INTO commanders(fid,current_name) VALUES('F-A','Alpha')"
                ).lastrowid
                con.execute(
                    "INSERT INTO systems VALUES(42,'System','FIRST','LAST',9,1,1.0,2.0,3.0)"
                )
                con.execute("""INSERT INTO bodies VALUES(
                    42,7,'Body','7','Planet','','Water world',0,1.5,NULL,0.8,123.0,
                    1,1,0,0,1,1,'Argon','Geysers',4,2,100,200,300,1,'BFIRST','BLAST')""")
                before_systems = con.execute("SELECT COUNT(*) FROM systems").fetchone()[0]
                before_bodies = con.execute("SELECT COUNT(*) FROM bodies").fetchone()[0]

            database = CMDRDatabase(path)
            with database._connect() as con:
                self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
                self.assertEqual(con.execute("SELECT COUNT(*) FROM systems").fetchone()[0], before_systems)
                self.assertEqual(con.execute("SELECT COUNT(*) FROM bodies").fetchone()[0], before_bodies)
                self.assertEqual(
                    con.execute("SELECT system_address,name,body_count,x,y,z FROM systems").fetchone(),
                    (42, "System", 9, 1.0, 2.0, 3.0),
                )
                self.assertEqual(
                    con.execute("SELECT first_seen,last_seen,body_count_seen,all_bodies_found FROM commander_systems").fetchone(),
                    ("FIRST", "LAST", 9, 1),
                )
                self.assertEqual(
                    con.execute("""SELECT first_seen,last_seen,was_discovered_at_scan,
                        was_mapped_at_scan,self_mapped,efficient_mapping,
                        biological_signals_seen,geological_signals_seen,
                        scan_value_cached,mapped_value_cached,current_value_cached,high_value_cached
                        FROM commander_bodies""").fetchone(),
                    ("BFIRST", "BLAST", 0, 0, 1, 1, 4, 2, 100, 200, 300, 1),
                )
                columns = {row[1] for row in con.execute("PRAGMA table_info(bodies)")}
                self.assertIn("radius_m", columns)
                self.assertNotIn("self_mapped", columns)
                self.assertFalse(con.execute("PRAGMA foreign_key_check").fetchall())
            self.assertTrue(list(Path(directory).glob("legacy.db.pre-v4-*.bak")))
            CMDRDatabase(path)

    def test_multiple_commanders_abort_without_guessing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "multi.db"
            make_v3(path)
            with sqlite3.connect(path) as con:
                con.execute("INSERT INTO commanders(fid) VALUES('F-A')")
                con.execute("INSERT INTO commanders(fid) VALUES('F-B')")
                con.execute("INSERT INTO systems(system_address,name) VALUES(1,'Kept')")
            with self.assertRaises(CommanderMigrationError):
                CMDRDatabase(path)
            with sqlite3.connect(path) as con:
                self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], 3)
                self.assertIn("first_seen", {r[1] for r in con.execute("PRAGMA table_info(systems)")})

    def test_backup_failure_prevents_v4_migration(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "backup.db"
            make_v3(path)
            with sqlite3.connect(path) as con:
                con.execute("INSERT INTO commanders(fid) VALUES('F-A')")
                con.execute("INSERT INTO systems(system_address,name) VALUES(1,'Kept')")
            database = object.__new__(CMDRDatabase)
            database.path = path
            database.active_commander_id = None
            with patch.object(database, "_create_migration_backup", side_effect=CommanderMigrationError("backup")):
                with self.assertRaises(CommanderMigrationError):
                    database.ensure_schema_v4()
            with sqlite3.connect(path) as con:
                self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], 3)


class ExplorationPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "test.db"
        self.database = CMDRDatabase(self.path)
        self.a = self.database.upsert_commander("F-A", "Alpha")
        self.b = self.database.upsert_commander("F-B", "Bravo")

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def snapshot(**body_overrides):
        body = {
            "body_id": 7, "name": "Shared 7", "short_name": "7",
            "body_type": "Planet", "planet_class": "Water world",
            "radius_m": 12345.0, "biological_signals": 1,
            "geological_signals": 2, "was_discovered": False,
            "was_mapped": False, "self_mapped": False,
            "efficient_mapping": False, "scan_value": 10,
            "mapped_value": 20, "current_value": 30, "high_value": False,
        }
        body.update(body_overrides)
        return {
            "system_address": 42, "system": "Shared", "last_timestamp": "T",
            "star_pos": [1, 2, 3], "system_body_count": 1,
            "fss_discovery_scan_seen": True, "system_all_bodies_found": False,
            "system_bodies": [body],
        }

    def test_two_commanders_have_independent_exploration_state(self):
        self.database.store_snapshot(
            self.snapshot(self_mapped=True, efficient_mapping=True,
                          first_footfall=True, scan_value=111,
                          biological_signals=4), self.a)
        b_data = self.snapshot(was_discovered=True, was_mapped=True,
                               self_mapped=False, efficient_mapping=False,
                               scan_value=222, biological_signals=2)
        b_data["system_all_bodies_found"] = True
        self.database.store_snapshot(b_data, self.b)

        with self.database._connect() as con:
            systems = con.execute(
                "SELECT commander_id,all_bodies_found FROM commander_systems ORDER BY commander_id"
            ).fetchall()
            bodies = con.execute("""SELECT commander_id,self_mapped,efficient_mapping,
                was_discovered_at_scan,was_mapped_at_scan,first_footfall,scan_value_cached,
                biological_signals_seen FROM commander_bodies ORDER BY commander_id""").fetchall()
            global_body = con.execute(
                "SELECT radius_m,biological_signals,geological_signals FROM bodies"
            ).fetchone()
        self.assertEqual(systems, [(self.a, 0), (self.b, 1)])
        self.assertEqual(bodies[0], (self.a, 1, 1, 0, 0, 1, 111, 4))
        self.assertEqual(bodies[1], (self.b, 0, 0, 1, 1, 0, 222, 2))
        self.assertEqual(global_body, (12345.0, 4, 2))

        self.assertTrue(self.database.chronicle_system_details(42, self.a)["bodies"][0]["self_mapped"])
        self.assertFalse(self.database.chronicle_system_details(42, self.b)["bodies"][0]["self_mapped"])

        a_body = self.database.chronicle_system_details(42, self.a)["bodies"][0]
        b_body = self.database.chronicle_system_details(42, self.b)["bodies"][0]
        self.assertEqual(a_body["biological_signals"], 4)
        self.assertEqual(b_body["biological_signals"], 2)
        self.assertEqual(len(self.database.search_chronicle("bio", self.a)), 1)
        self.assertEqual(len(self.database.search_chronicle("bio", self.b)), 1)

    def test_global_signal_facts_do_not_leak_into_commander_reads(self):
        self.database.store_snapshot(
            self.snapshot(biological_signals=4, geological_signals=2), self.a
        )
        self.database.store_snapshot(
            self.snapshot(biological_signals=0, geological_signals=0), self.b
        )

        with self.database._connect() as con:
            self.assertEqual(
                con.execute(
                    "SELECT biological_signals,geological_signals FROM bodies"
                ).fetchone(),
                (4, 2),
            )

        b_body = self.database.chronicle_system_details(42, self.b)["bodies"][0]
        self.assertEqual(b_body["biological_signals"], 0)
        self.assertEqual(b_body["geological_signals"], 0)
        self.assertEqual(self.database.search_chronicle("bio", self.b), [])
        self.assertEqual(self.database.search_chronicle("geo", self.b), [])

    def test_unknown_and_ambiguous_write_only_global_facts(self):
        folder = Path(self.tmp.name) / "journals"
        folder.mkdir()
        base = {"timestamp": "2026-01-01T00:00:00Z"}
        write_journal(folder / "Journal.2026-01-01T000000.01.log", [
            {**base, "event": "Location", "StarSystem": "Unknown", "SystemAddress": 50, "StarPos": [5, 6, 7]},
            {**base, "event": "Scan", "SystemAddress": 50, "BodyID": 1,
             "BodyName": "Unknown 1", "PlanetClass": "Rocky body", "Radius": 999.0,
             "WasDiscovered": False, "WasMapped": False},
        ])
        write_journal(folder / "Journal.2026-01-01T000100.01.log", [
            {**base, "event": "Commander", "Name": "Alpha", "FID": "F-A"},
            {**base, "event": "LoadGame", "Commander": "Bravo", "FID": "F-B"},
            {**base, "event": "Location", "StarSystem": "Ambiguous", "SystemAddress": 51},
        ])
        self.database.import_journal_archive(folder)
        with self.database._connect() as con:
            self.assertEqual(con.execute("SELECT name FROM systems WHERE system_address=50").fetchone(), ("Unknown",))
            self.assertEqual(con.execute("SELECT radius_m FROM bodies WHERE system_address=50").fetchone(), (999.0,))
            self.assertEqual(con.execute("SELECT COUNT(*) FROM commander_systems").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM commander_bodies").fetchone()[0], 0)

    def test_identified_archive_persists_conservative_first_footfall(self):
        folder = Path(self.tmp.name) / "footfall"
        folder.mkdir()
        base = {"timestamp": "2026-01-01T00:00:00Z"}
        write_journal(folder / "Journal.2026-01-01T000000.01.log", [
            {**base, "event": "Commander", "Name": "Alpha", "FID": "F-A"},
            {**base, "event": "Location", "StarSystem": "Foot", "SystemAddress": 60},
            {**base, "event": "Scan", "SystemAddress": 60, "BodyID": 2,
             "BodyName": "Foot 2", "WasFootfalled": False},
            {**base, "event": "Disembark", "SystemAddress": 60, "BodyID": 2, "OnPlanet": True},
        ])
        self.database.import_journal_archive(folder)
        with self.database._connect() as con:
            row = con.execute(
                "SELECT commander_id,first_footfall FROM commander_bodies"
            ).fetchone()
        self.assertEqual(row, (self.a, 1))

    def test_archive_body_events_create_and_later_complete_safe_parents(self):
        folder = Path(self.tmp.name) / "body-parents"
        folder.mkdir()
        complete = self.snapshot(
            body_id=4, name="Complete Body", planet_class="Water world",
            radius_m=123456.0, landable=True, biological_signals=0,
            geological_signals=0,
        )
        complete.update({"system_address": 61, "system": "Parent Test"})
        self.database.store_snapshot(complete, self.a)
        base = {
            "timestamp": "2026-01-01T00:00:00Z",
            "SystemAddress": 61,
        }
        write_journal(folder / "Journal.2026-01-01T000000.01.log", [
            {**base, "event": "Commander", "Name": "Alpha", "FID": "F-A"},
            {**base, "event": "Location", "StarSystem": "Parent Test"},
            {**base, "event": "SAASignalsFound", "BodyID": 1,
             "Signals": [{"Type": "$SAA_SignalType_Biological;", "Count": 2}]},
            {**base, "event": "FSSBodySignals", "BodyID": 2,
             "Signals": [{"Type": "$SAA_SignalType_Geological;", "Count": 3}]},
            {**base, "event": "SAAScanComplete", "BodyID": 3,
             "ProbesUsed": 4, "EfficiencyTarget": 6},
            {**base, "event": "SAASignalsFound", "BodyID": 4,
             "Signals": [{"Type": "$SAA_SignalType_Biological;", "Count": 1}]},
            {**base, "event": "Scan", "BodyID": 1, "BodyName": "Later Scan",
             "PlanetClass": "Rocky body", "Radius": 654321.0},
        ])

        self.database.import_journal_archive(folder)

        with self.database._connect() as con:
            bodies = {
                row[0]: row[1:]
                for row in con.execute("""SELECT body_id,name,planet_class,radius_m,landable,
                    biological_signals,geological_signals FROM bodies
                    WHERE system_address=61 ORDER BY body_id""")
            }
            personal = {
                row[0]: row[1:]
                for row in con.execute("""SELECT body_id,self_mapped,efficient_mapping,
                    probes_used,efficiency_target,biological_signals_seen,
                    geological_signals_seen FROM commander_bodies
                    WHERE commander_id=? AND system_address=61 ORDER BY body_id""", (self.a,))
            }
            self.assertEqual(con.execute("PRAGMA foreign_key_check").fetchall(), [])

        self.assertEqual(bodies[1], ("Later Scan", "Rocky body", 654321.0, 0, 2, 0))
        self.assertEqual(bodies[2], ("", "", None, 0, 0, 3))
        self.assertEqual(bodies[3], ("", "", None, 0, 0, 0))
        self.assertEqual(bodies[4], ("Complete Body", "Water world", 123456.0, 1, 1, 0))
        self.assertEqual(personal[1][4:], (2, 0))
        self.assertEqual(personal[2][4:], (0, 3))
        self.assertEqual(personal[3][:4], (1, 1, 4, 6))

    def test_archive_placeholder_body_state_is_separate_per_commander(self):
        folder = Path(self.tmp.name) / "two-commanders"
        folder.mkdir()
        shared = {
            "SystemAddress": 62,
            "BodyID": 8,
            "Signals": [{"Type": "$SAA_SignalType_Biological;", "Count": 1}],
        }
        write_journal(folder / "Journal.2026-01-01T000000.01.log", [
            {"timestamp": "2026-01-01T00:00:00Z", "event": "Commander",
             "Name": "Alpha", "FID": "F-A"},
            {"timestamp": "2026-01-01T00:00:01Z", "event": "Location",
             "StarSystem": "Shared Parent", "SystemAddress": 62},
            {"timestamp": "2026-01-01T00:00:02Z", "event": "SAASignalsFound", **shared},
        ])
        write_journal(folder / "Journal.2026-01-02T000000.01.log", [
            {"timestamp": "2026-01-02T00:00:00Z", "event": "Commander",
             "Name": "Bravo", "FID": "F-B"},
            {"timestamp": "2026-01-02T00:00:01Z", "event": "Location",
             "StarSystem": "Shared Parent", "SystemAddress": 62},
            {"timestamp": "2026-01-02T00:00:02Z", "event": "FSSBodySignals",
             **shared, "Signals": [{"Type": "$SAA_SignalType_Biological;", "Count": 3}]},
        ])

        self.database.import_journal_archive(folder)

        with self.database._connect() as con:
            rows = con.execute("""SELECT commander_id,biological_signals_seen
                FROM commander_bodies WHERE system_address=62 AND body_id=8
                ORDER BY commander_id""").fetchall()
            self.assertEqual(con.execute("PRAGMA foreign_key_check").fetchall(), [])
        self.assertEqual(rows, [(self.a, 1), (self.b, 3)])

    def test_live_scan_persists_habitat_fields_and_primary_star(self):
        folder = Path(self.tmp.name) / "live"
        folder.mkdir()
        base = {"timestamp": "2026-01-01T00:00:00Z", "SystemAddress": 70}
        composition = [
            {"Name": "CarbonDioxide", "Percent": 98.4},
            {"Name": "SulphurDioxide", "Percent": 1.6},
        ]
        write_journal(folder / "Journal.2026-01-01T000000.01.log", [
            {**base, "event": "Commander", "Name": "Alpha", "FID": "F-A"},
            {**base, "event": "Location", "StarSystem": "Habitat"},
            {**base, "event": "Scan", "BodyID": 0, "BodyName": "Habitat",
             "StarType": "K", "Radius": 700000000.0},
            {**base, "event": "Scan", "BodyID": 3, "BodyName": "Habitat 3",
             "PlanetClass": "Rocky body", "Parents": [{"Star": 0}],
             "Radius": 1234567.0, "SurfaceTemperature": 211.5,
             "SurfacePressure": 1234.5, "AtmosphereComposition": composition},
        ])
        state = read_latest_state(folder)
        self.database.store_snapshot(state, self.a)
        with self.database._connect() as con:
            row = con.execute("""SELECT parent_star_id,radius_m,surface_temperature,
                surface_pressure,atmosphere_composition FROM bodies WHERE body_id=3""").fetchone()
            system = con.execute(
                "SELECT primary_star_id,primary_star_type FROM systems WHERE system_address=70"
            ).fetchone()
        self.assertEqual(row[:4], (0, 1234567.0, 211.5, 1234.5))
        self.assertEqual(json.loads(row[4]), composition)
        self.assertEqual(system, (0, "K"))

    def test_archive_import_persists_habitat_fields(self):
        folder = Path(self.tmp.name) / "archive-habitat"
        folder.mkdir()
        base = {"timestamp": "2026-01-01T00:00:00Z", "SystemAddress": 71}
        write_journal(folder / "Journal.2026-01-01T000000.01.log", [
            {**base, "event": "Commander", "Name": "Alpha", "FID": "F-A"},
            {**base, "event": "Location", "StarSystem": "Archive"},
            {**base, "event": "Scan", "BodyID": 0, "BodyName": "Archive", "StarType": "M"},
            {**base, "event": "Scan", "BodyID": 5, "BodyName": "Archive 5",
             "PlanetClass": "Icy body", "Parents": [{"Planet": 4}, {"Star": 0}],
             "Radius": 765432.0, "SurfaceTemperature": 99.25,
             "SurfacePressure": 42.0,
             "AtmosphereComposition": [{"Name": "Argon", "Percent": 100.0}]},
        ])
        self.database.import_journal_archive(folder)
        with self.database._connect() as con:
            row = con.execute("""SELECT parent_id,parent_star_id,radius_m,
                surface_temperature,surface_pressure,atmosphere_composition
                FROM bodies WHERE system_address=71 AND body_id=5""").fetchone()
        self.assertEqual(row[:5], (4, 0, 765432.0, 99.25, 42.0))
        self.assertEqual(json.loads(row[5]), [{"Name": "Argon", "Percent": 100.0}])

    def test_missing_and_later_complete_scans_merge_without_data_loss(self):
        first = self.snapshot(
            parent_star_id=0, radius_m=1000.0, surface_temperature=180.0,
            surface_pressure=12.0,
            atmosphere_composition='[{"Name":"Neon","Percent":100.0}]',
        )
        self.database.store_snapshot(first, self.a)
        self.database.store_snapshot(self.snapshot(radius_m=None), self.a)
        self.database.store_snapshot(self.snapshot(
            radius_m=1100.0, surface_temperature=181.0,
            surface_pressure=13.0,
            atmosphere_composition='[{"Name":"Neon","Percent":99.0}]',
        ), self.a)
        with self.database._connect() as con:
            row = con.execute("""SELECT parent_star_id,radius_m,surface_temperature,
                surface_pressure,atmosphere_composition FROM bodies WHERE system_address=42""").fetchone()
        self.assertEqual(row, (0, 1100.0, 181.0, 13.0,
                               '[{"Name":"Neon","Percent":99.0}]'))


if __name__ == "__main__":
    unittest.main()
