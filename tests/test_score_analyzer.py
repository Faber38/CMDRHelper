"""Planet-target queries against the actual split exploration schema."""
import tempfile
import unittest
from pathlib import Path

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.score_analyzer import ScoreAnalyzer


class PlanetTargetRegressionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.database = CMDRDatabase(Path(temporary.name) / "scores.db")
        self.commander = self.database.upsert_commander("FID-A", "Alpha")
        other = self.database.upsert_commander("FID-B", "Beta")
        self.database.active_commander_id = self.commander
        with self.database._connect() as con:
            for address in (1, 2, 3):
                con.execute(
                    "INSERT INTO systems(system_address,name) VALUES(?,?)",
                    (address, f"Plio Aip KN-B d13-{address}"),
                )
                con.execute(
                    "INSERT INTO commander_systems(commander_id,system_address) VALUES(?,?)",
                    (self.commander if address != 3 else other, address),
                )
            classes = [
                ("Water world", 0), ("Water world", 1),
                ("Earthlike body", 0), ("Earth-like world", 0),
                ("Ammonia world", 0), ("High metal content body", 1),
                ("Rocky body", 1), ("High metal content body", 0),
            ]
            for body_id, (planet_class, terraformable) in enumerate(classes):
                con.execute(
                    """INSERT INTO bodies(system_address,body_id,planet_class,terraformable)
                       VALUES(1,?,?,?)""", (body_id, planet_class, terraformable),
                )
                # The same observation by another commander must not double counts.
                for commander in (self.commander, other):
                    if commander == other:
                        con.execute(
                            "INSERT OR IGNORE INTO commander_systems(commander_id,system_address) VALUES(?,1)",
                            (other,),
                        )
                    con.execute(
                        "INSERT INTO commander_bodies(commander_id,system_address,body_id) VALUES(?,1,?)",
                        (commander, body_id),
                    )
            # Global bodies / another commander's observations are not personal hits.
            for address in (2, 3):
                con.execute(
                    """INSERT INTO bodies(system_address,body_id,planet_class,terraformable)
                       VALUES(?,0,'Water world',1)""", (address,),
                )
                con.execute(
                    "INSERT OR IGNORE INTO commander_systems(commander_id,system_address) VALUES(?,?)",
                    (other, address),
                )
                con.execute(
                    "INSERT INTO commander_bodies(commander_id,system_address,body_id) VALUES(?,?,0)",
                    (other, address),
                )
        self.analyzer = ScoreAnalyzer(self.database)

    def assert_target(self, target, expected_count):
        rows = self.analyzer._target_system_rows(target)
        self.assertEqual(
            [(row["system_address"], row["target_hit"], row["target_count"]) for row in rows],
            [(1, 1, expected_count), (2, 0, 0)],
        )
        result = self.analyzer.jump_recommendations(target, min_samples=2)
        self.assertEqual((result["systems"], result["hits"], result["finds"]),
                         (2, 1, expected_count))
        self.assertEqual(result["baseline"], 0.5)
        self.assertEqual(len(result["recommendations"]), 1)
        row = result["recommendations"][0]
        self.assertEqual((row["key"], row["systems"], row["hits"], row["finds"]),
                         ("KN-B d", 2, 1, expected_count))
        self.assertEqual((row["rate"], row["score"], row["stars"]), (0.5, 50, 2))

    def test_valuable(self):
        self.assert_target("valuable", 7)

    def test_terraformable(self):
        self.assert_target("terraformable", 3)

    def test_water_world(self):
        self.assert_target("water_world", 2)

    def test_earthlike(self):
        self.assert_target("earthlike", 2)

    def test_ammonia_world(self):
        self.assert_target("ammonia_world", 1)


if __name__ == "__main__":
    unittest.main()
