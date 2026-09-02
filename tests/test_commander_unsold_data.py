from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from cmdrhelper.database import CMDRDatabase, SCHEMA_VERSION
from cmdrhelper.journal_reader import read_latest_state


def event(kind, second, **values):
    return {"timestamp": f"2026-01-01T00:00:{second:02d}Z", "event": kind, **values}


def write_journal(folder, events, stamp="2026-01-01T000000"):
    path = Path(folder) / f"Journal.{stamp}.01.log"
    path.write_text("".join(json.dumps(item) + "\n" for item in events), encoding="utf-8")


class CommanderUnsoldDataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "test.db"
        self.db = CMDRDatabase(self.path)
        self.a = self.db.upsert_commander("FID-A", "Alpha")
        self.b = self.db.upsert_commander("FID-B", "Bravo")

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def bio(address, species="Stratum Tectonicas", scan_type="Analyse"):
        return {"system_address": address, "body_id": 1, "system_name": f"S{address}",
                "body_name": f"S{address} 1", "genus": "Stratum", "species": species,
                "variant": "", "scan_type": scan_type,
                "timestamp": "2026-01-01T00:00:03Z"}

    @staticmethod
    def cart(address, mapped=False):
        return {"system_address": address, "body_id": 1, "system_name": f"S{address}",
                "body_name": f"S{address} 1", "scanned_at": "2026-01-01T00:00:02Z",
                "mapped_at": "2026-01-01T00:00:03Z" if mapped else "",
                "self_mapped": mapped, "planet_class": "Rocky body",
                "terraformable": False, "estimated_value": 1234}

    def store(self, commander, bio=(), cart=()):
        self.db.store_commander_unsold_data(
            commander, bio, cart, learned_bio_values={},
            cartography_factor_func=lambda *_: 1.0,
        )

    def test_schema_wealth_and_missing_value_are_commander_specific(self):
        self.assertEqual(SCHEMA_VERSION, 12)
        self.db.store_commander_wealth(self.a, {"credits": 1234567,
            "event_timestamp": "2026-01-01T00:00:00Z", "source_event": "LoadGame"})
        self.assertEqual(self.db.commander_summary(self.a)["wealth"]["credits"], 1234567)
        self.assertIsNone(self.db.commander_summary(self.b)["wealth"])
        self.db.store_commander_wealth(self.b, {"credits": 88,
            "event_timestamp": "2026-01-02T00:00:00Z", "source_event": "LoadGame"})
        self.assertEqual(self.db.commander_summary(self.a)["wealth"]["credits"], 1234567)

    def test_biology_completion_separation_sale_and_restart(self):
        self.store(self.a, [self.bio(10), self.bio(11, scan_type="Sample")])
        self.store(self.b, [self.bio(20, species="Aleoida Arcus")])
        self.assertEqual(self.db.commander_summary(self.a)["unsold_biology"]["findings"], 1)
        self.assertEqual(self.db.commander_summary(self.b)["unsold_biology"]["findings"], 1)
        self.store(self.a)  # autoritativer Stand nach SellOrganicData
        reopened = CMDRDatabase(self.path)
        self.assertEqual(reopened.commander_summary(self.a)["unsold_biology"]["findings"], 0)
        self.assertEqual(reopened.commander_summary(self.b)["unsold_biology"]["findings"], 1)

    def test_cartography_mapping_sale_separation_and_restart(self):
        self.store(self.a, cart=[self.cart(10)])
        self.store(self.b, cart=[self.cart(20, mapped=True)])
        b_before = self.db.commander_summary(self.b)["unsold_cartography"]
        self.assertEqual((b_before["systems"], b_before["bodies"]), (1, 1))
        self.store(self.a)  # autoritativer Stand nach Sell/MultiSellExplorationData
        reopened = CMDRDatabase(self.path)
        self.assertEqual(reopened.commander_summary(self.a)["unsold_cartography"]["bodies"], 0)
        self.assertEqual(reopened.commander_summary(self.b)["unsold_cartography"], b_before)

    def test_summary_for_offline_commander_never_falls_back(self):
        self.store(self.a, [self.bio(10)], [self.cart(10)])
        b = self.db.commander_summary(self.b)
        self.assertEqual(b["unsold_biology"]["findings"], 0)
        self.assertEqual(b["unsold_cartography"]["bodies"], 0)
        self.assertIsNone(b["wealth"])

    def test_reader_uses_loadgame_credits_and_complete_scans_only(self):
        folder = Path(self.tmp.name) / "journals"
        folder.mkdir()
        write_journal(folder, [
            event("LoadGame", 0, FID="FID-A", Commander="Alpha", Credits=987654),
            event("Location", 1, StarSystem="Test", SystemAddress=42),
            event("Scan", 2, SystemAddress=42, BodyID=1, BodyName="Test 1",
                  PlanetClass="Rocky body", WasDiscovered=False, WasMapped=False),
            event("ScanOrganic", 3, SystemAddress=42, BodyID=1, ScanType="Sample",
                  Genus="Stratum", Species="Stratum Tectonicas"),
            event("ScanOrganic", 4, SystemAddress=42, BodyID=1, ScanType="Analyse",
                  Genus="Stratum", Species="Stratum Tectonicas"),
            event("SAAScanComplete", 5, SystemAddress=42, BodyID=1,
                  ProbesUsed=2, EfficiencyTarget=4),
        ])
        state = read_latest_state(folder)
        self.assertEqual(state["wealth"], {"credits": 987654,
            "event_timestamp": "2026-01-01T00:00:00Z", "source_event": "LoadGame"})
        self.assertEqual(len(state["unsold_biology"]), 1)
        self.assertEqual(len(state["unsold_cartography"]), 1)
        self.assertTrue(state["unsold_cartography"][0]["self_mapped"])

    def test_unknown_and_ambiguous_sessions_produce_no_personal_open_data(self):
        folder = Path(self.tmp.name) / "sessions"
        folder.mkdir()
        write_journal(folder, [
            event("ScanOrganic", 1, SystemAddress=1, BodyID=1, ScanType="Analyse",
                  Genus="Stratum", Species="Stratum Tectonicas"),
        ])
        write_journal(folder, [
            event("Commander", 0, FID="FID-A", Name="Alpha"),
            event("Commander", 1, FID="FID-B", Name="Bravo"),
            event("Scan", 2, SystemAddress=2, BodyID=1, BodyName="X 1",
                  PlanetClass="Rocky body"),
        ], "2026-01-01T000100")
        state = read_latest_state(folder)
        self.assertEqual(state["unsold_biology"], [])
        self.assertEqual(state["unsold_cartography"], [])
        self.assertIsNone(state["wealth"])

    def test_v5_copy_migrates_additively(self):
        with sqlite3.connect(self.path) as con:
            con.execute("PRAGMA user_version=5")
            con.execute("DROP TABLE commander_wealth")
            con.execute("DROP TABLE commander_unsold_biology")
            con.execute("DROP TABLE commander_unsold_cartography")
        CMDRDatabase(self.path)
        with sqlite3.connect(self.path) as con:
            self.assertEqual(con.execute("PRAGMA user_version").fetchone()[0], SCHEMA_VERSION)
            self.assertEqual(con.execute("SELECT current_name FROM commanders WHERE id=?",
                                         (self.a,)).fetchone()[0], "Alpha")


if __name__ == "__main__":
    unittest.main()
