from __future__ import annotations

import unittest
import tempfile
from pathlib import Path

from cmdrhelper.bio_predictor import BioPredictor
from cmdrhelper.database import CMDRDatabase


def finding(index, species, genus=None, **features):
    row = {
        "system_address": index,
        "body_id": 1,
        "genus": genus or species.split()[0],
        "species": species,
        "scan_type": "Analyse",
        "planet_class": "Rocky body",
        "atmosphere": "thin carbon dioxide atmosphere",
        "gravity_g": 0.2,
        "mass_em": 0.02,
        "biological_signals": 1,
        "terraformable": False,
        "volcanism": "",
        "distance_ls": 1000.0,
        "surface_temperature": None,
        "surface_pressure": None,
        "atmosphere_composition": "",
        "primary_star_type": "K",
        "parent_star_id": 0,
    }
    row.update(features)
    return row


class BioPredictorTests(unittest.TestCase):
    def setUp(self):
        rows = []
        rows += [finding(i, "Stratum Tectonicas", planet_class="High metal content body") for i in range(1, 13)]
        rows += [finding(i, "Stratum Paleas") for i in range(20, 27)]
        rows += [finding(i, "Stratum Testis", planet_class="High metal content body") for i in range(30, 35)]
        rows += [finding(i, "Bacterium Informem", planet_class="Icy body",
                         atmosphere="thin nitrogen atmosphere") for i in range(40, 50)]
        rows += [finding(i, "Bacterium Aurasus") for i in range(50, 60)]
        rows += [finding(i, "Bacterium Vesicula", planet_class="Icy body",
                         atmosphere="thin argon atmosphere", biological_signals=2)
                 for i in range(60, 66)]
        rows += [finding(i, "Fonticulua Campestris", planet_class="Icy body",
                         atmosphere="thin argon atmosphere", biological_signals=2)
                 for i in range(60, 66)]
        rows += [finding(80, "Rare Alpha", genus="Rare"),
                 finding(81, "Rare Alpha", genus="Rare"),
                 finding(82, "Rare Beta", genus="Rare"),
                 finding(83, "Rare Beta", genus="Rare"),
                 finding(84, "Rare Gamma", genus="Rare")]
        rows += [finding(90, "Ignored Log", scan_type="Log")]
        rows += [finding(91, "Ignored Sample", scan_type="Sample")]
        self.predictor = BioPredictor(rows)

    @staticmethod
    def body(**overrides):
        value = finding(999, "Unused")
        value.pop("species")
        value.pop("genus")
        value.pop("scan_type")
        value.update(overrides)
        return value

    def names(self, body, known=()):
        return [item.name for item in self.predictor.predict(body, known).candidates]

    def test_tectonicas_ranks_high_on_matching_hmc_and_lower_on_rocky(self):
        matching = self.predictor.predict(self.body(planet_class="High metal content body"))
        tect = next(item for item in matching.candidates if item.name == "Stratum Tectonicas")
        self.assertEqual(matching.candidates[0].name, "Stratum Tectonicas")
        self.assertEqual(tect.confidence, "high")
        rocky = self.predictor.predict(self.body(planet_class="Rocky body"))
        self.assertNotIn("Stratum Tectonicas", [item.name for item in rocky.candidates[:3]])

    def test_paleas_and_informem_match_their_habitats(self):
        self.assertIn("Stratum Paleas", self.names(self.body())[:3])
        nitrogen = self.body(planet_class="Icy body", atmosphere="thin nitrogen atmosphere")
        self.assertEqual(self.names(nitrogen)[0], "Bacterium Informem")

    def test_rare_species_uses_genus_fallback(self):
        names = self.names(self.body())
        self.assertFalse(any(name.startswith("Rare ") for name in names))
        self.assertIn("Rare", names)

    def test_multiple_species_of_same_genus_are_kept(self):
        names = self.names(self.body(planet_class="High metal content body"))
        self.assertIn("Stratum Tectonicas", names)
        self.assertIn("Stratum Testis", names)

    def test_missing_temperature_and_pressure_do_not_block_prediction(self):
        self.assertTrue(self.predictor.predict(self.body()).candidates)

    def test_temperature_and_pressure_affect_similarity_when_both_exist(self):
        historical = finding(200, "Temperature Test", surface_temperature=200.0,
                             surface_pressure=1000.0)
        predictor = BioPredictor([historical] * 3)
        matching, _ = predictor._similarity(
            self.body(surface_temperature=200.0, surface_pressure=1000.0), historical
        )
        different, _ = predictor._similarity(
            self.body(surface_temperature=500.0, surface_pressure=100000.0), historical
        )
        self.assertGreater(matching, different)

    def test_known_species_is_removed_and_progress_distinguishes_scan_steps(self):
        known = [
            {"genus": "Stratum", "species": "Stratum Paleas", "scan_type": "Log"},
            {"genus": "Bacterium", "species": "Bacterium Aurasus", "scan_type": "Sample"},
            {"genus": "Rare", "species": "Rare Gamma", "scan_type": "Analyze"},
        ]
        result = self.predictor.predict(self.body(biological_signals=5), known)
        self.assertNotIn("Stratum Paleas", [item.name for item in result.candidates])
        self.assertEqual((result.identified_count, result.completed_count, result.open_signals), (3, 1, 2))

    def test_signal_count_does_not_limit_candidate_count(self):
        result = self.predictor.predict(self.body(biological_signals=1), limit=8)
        self.assertGreater(len(result.candidates), 1)

    def test_cooccurrence_bonus_is_bounded_and_does_not_change_confidence(self):
        target = self.body(planet_class="Icy body", atmosphere="thin argon atmosphere",
                           biological_signals=2)
        plain = self.predictor.predict(target)
        known = [{"genus": "Bacterium", "species": "Bacterium Vesicula", "scan_type": "Log"}]
        boosted = self.predictor.predict(target, known)
        plain_item = next(item for item in plain.candidates if item.name == "Fonticulua Campestris")
        boosted_item = next(item for item in boosted.candidates if item.name == "Fonticulua Campestris")
        self.assertGreater(boosted_item.score, plain_item.score)
        self.assertLessEqual(boosted_item.score / plain_item.score, 1.15)
        self.assertEqual(boosted_item.confidence, plain_item.confidence)

    def test_too_few_features_returns_no_prediction(self):
        result = self.predictor.predict({"biological_signals": 3})
        self.assertEqual(result.candidates, ())

    def test_database_training_cache_refreshes_for_new_complete_find(self):
        with tempfile.TemporaryDirectory() as directory:
            database = CMDRDatabase(Path(directory) / "bio.db")
            commander = database.upsert_commander("F-A", "Alpha")
            snapshot = {
                "system_address": 1, "system": "Test", "last_timestamp": "T1",
                "system_bodies": [self.body(body_id=1, biological_signals=1)],
            }
            database.store_snapshot(snapshot, commander)
            database.store_biology(1, 1, "Stratum", "Stratum Paleas",
                                   scan_type="Log", timestamp="T1", commander_id=commander)
            first = database.biology_predictor()
            self.assertEqual(database.complete_biology_training_data(), [])
            database.store_biology(1, 1, "Stratum", "Stratum Paleas",
                                   scan_type="Analyze", timestamp="T2", commander_id=commander)
            second = database.biology_predictor()
            self.assertIsNot(first, second)
            self.assertEqual(len(database.complete_biology_training_data()), 1)


if __name__ == "__main__":
    unittest.main()
