import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cmdrhelper.database import CMDRDatabase, SCHEMA_VERSION
from cmdrhelper.ui.main_window import MainWindow


def event(kind, second, **values):
    return {
        "timestamp": f"2026-09-03T20:00:{second:02d}Z",
        "event": kind,
        **values,
    }


class SurfaceMiningHistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = CMDRDatabase(Path(self.tmp.name) / "test.db")
        self.commander = self.db.upsert_commander("F123", "Miner", "2026-09-03T19:00:00Z")
        self.other = self.db.upsert_commander("F999", "Other", "2026-09-03T19:00:00Z")
        self.journal = Path(self.tmp.name) / "Journal.2026-09-03T190000.01.log"
        self.db.store_journal_session({
            "journal_file": str(self.journal), "attribution_status": "identified",
            "fid_seen": "F123", "commander_name_seen": "Miner",
        })

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def context(body_id=7, address=42):
        return [
            event("Location", 0, StarSystem="Real System", SystemAddress=address,
                  Body="Real System A 1", BodyID=body_id, Docked=False),
            event("Touchdown", 1, StarSystem="Real System", SystemAddress=address,
                  Body="Real System A 1", BodyID=body_id),
            event("LaunchSRV", 2, SRVType="mev_rhino", SRVType_Localised="SRV Rhino"),
        ]

    def apply(self, events, offset, commander=None, journal=None):
        self.db.apply_commander_journal_delta(
            commander or self.commander, journal or self.journal, events, offset
        )

    def test_schema_and_real_56_copper_cycle_with_byproducts(self):
        self.assertEqual(SCHEMA_VERSION, 14)
        counts = {
            "sulphur": 7, "iron": 6, "phosphorus": 6, "niobium": 3,
            "nickel": 3, "tungsten": 3, "vanadium": 2, "selenium": 1,
            "molybdenum": 1, "cadmium": 1, "tin": 1, "chromium": 1,
        }
        events = self.context()
        events += [event("MiningRefined", 3, Type="$copper_name;",
                         Type_Localised="Kupfer") for _ in range(56)]
        for name, count in counts.items():
            events += [event("MaterialCollected", 4, Category="Raw",
                             Name=f"${name}_name;", Name_Localised=name.title(), Count=1)
                       for _ in range(count)]
        events += [event("DockSRV", 5, SRVType="mev_rhino")]
        self.apply(events, 1000)
        result = self.db.surface_mining_for_body(42, 7, self.commander)
        self.assertEqual([(x["frontier_name"], x["quantity"])
                          for x in result["commodities"]], [("copper", 56)])
        self.assertEqual({x["frontier_name"]: x["quantity"]
                          for x in result["materials"]}, counts)

        # Derselbe bereits bestätigte Bytebereich ist vollständig idempotent.
        self.apply(events, 1000)
        self.assertEqual(self.db.surface_mining_for_body(42, 7, self.commander)
                         ["commodities"][0]["quantity"], 56)

    def test_adds_sessions_and_separates_body_commander_and_commodity(self):
        self.apply(self.context() + [
            event("MiningRefined", 3, Type="$copper_name;", Type_Localised="Kupfer"),
            event("MiningRefined", 4, Type="$helium3_name;", Type_Localised="Helium-3"),
        ], 10)
        self.apply([event("MiningRefined", 5, Type="$copper_name;",
                          Type_Localised="Kupfer")], 20)
        self.assertEqual({x["frontier_name"]: x["quantity"] for x in
                          self.db.surface_mining_for_body(42, 7, self.commander)["commodities"]},
                         {"copper": 2, "helium3": 1})

        other_journal = Path(self.tmp.name) / "other.log"
        self.db.store_journal_session({"journal_file": str(other_journal),
            "attribution_status": "identified", "fid_seen": "F999"})
        self.apply(self.context(body_id=8) + [event(
            "MiningRefined", 6, Type="$copper_name;", Type_Localised="Kupfer")],
            30, journal=other_journal)
        self.apply(self.context() + [event(
            "MiningRefined", 7, Type="$copper_name;", Type_Localised="Kupfer")],
            40, commander=self.other, journal=other_journal)
        self.assertEqual(self.db.surface_mining_for_body(42, 8, self.commander)
                         ["commodities"][0]["quantity"], 1)
        self.assertEqual(self.db.surface_mining_for_body(42, 7, self.other)
                         ["commodities"][0]["quantity"], 1)

    def test_material_outside_rhino_context_and_scan_materials_are_separate(self):
        self.apply(self.context() + [
            event("DockSRV", 3, SRVType="mev_rhino"),
            event("MaterialCollected", 4, Name="$iron_name;", Name_Localised="Eisen"),
        ], 10)
        self.assertEqual(self.db.surface_mining_for_body(42, 7, self.commander)["materials"], [])
        with self.db._connect() as con:
            con.execute("INSERT INTO systems(system_address,name) VALUES(42,'Real System')")
            con.execute("INSERT INTO bodies(system_address,body_id,name) VALUES(42,7,'Body')")
            con.execute("INSERT INTO materials VALUES(42,7,'iron',18.3)")
            self.assertEqual(con.execute("SELECT COUNT(*) FROM surface_mining_materials").fetchone()[0], 0)

    def test_material_collected_uses_its_real_count(self):
        self.apply(self.context() + [event(
            "MaterialCollected", 3, Category="Raw", Name="$sulphur_name;",
            Name_Localised="Schwefel", Count=7)], 10)
        self.assertEqual(self.db.surface_mining_for_body(42, 7, self.commander)
                         ["materials"][0]["quantity"], 7)

    def test_db_failure_rolls_back_mutation_and_offset(self):
        events = self.context() + [event(
            "MiningRefined", 3, Type="$copper_name;", Type_Localised="Kupfer")]
        with patch.object(self.db, "_record_surface_mining_event",
                          side_effect=RuntimeError("db")):
            with self.assertRaises(RuntimeError):
                self.apply(events, 55)
        with self.db._connect() as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM surface_mining_commodities").fetchone()[0], 0)
            self.assertEqual(con.execute("SELECT last_read_offset FROM journal_sessions").fetchone()[0], 0)

    def test_archive_import_records_and_deduplicates_mining_events(self):
        archive = Path(self.tmp.name) / "archive"
        archive.mkdir()
        journal = archive / "Journal.2026-09-03T190000.01.log"
        events = [event("Commander", 0, FID="F123", Name="Miner")]
        events += self.context()
        events += [event("MiningRefined", 3, Type="$copper_name;",
                         Type_Localised="Kupfer") for _ in range(56)]
        journal.write_text("".join(json.dumps(item) + "\n" for item in events),
                           encoding="utf-8")
        self.db.import_journal_archive(archive)
        self.assertEqual(self.db.surface_mining_for_body(42, 7, self.commander)
                         ["commodities"][0]["quantity"], 56)
        self.db.import_journal_archive(archive)
        self.assertEqual(self.db.surface_mining_for_body(42, 7, self.commander)
                         ["commodities"][0]["quantity"], 56)

    def test_tooltip_uses_only_personal_finds(self):
        body = {"planetary_mining_signals": 24,
                "materials": {"iron": 18.3}, "surface_mining_commodities": []}
        self.assertNotIn("18", MainWindow._explorer_planetary_mining_tooltip(body))
        body["surface_mining_commodities"] = [
            {"display_name": "Kupfer", "quantity": 56}
        ]
        tooltip = MainWindow._explorer_planetary_mining_tooltip(body)
        self.assertIn("24", tooltip)
        self.assertIn("Kupfer 56 t", tooltip)


if __name__ == "__main__":
    unittest.main()
