import tempfile
import unittest
from pathlib import Path

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.jump_tip import (
    HierarchicalJumpTip, PRIOR_SYSTEMS, body_potential, evaluate_observations,
    observation, quality_label, shrink, summarize,
)
from cmdrhelper.score_analyzer import ScoreAnalyzer


def body(**changes):
    return dict(dict(body_id=1, name="Test 1", body_type="Planet", star_type="",
                     planet_class="Rocky body", mass_em=1.0, terraformable=False,
                     scanned=1, biological_signals_seen=0), **changes)


def sample(address=1, name="Plio Aip KN-B d13-1", bodies=None, complete=True,
           fss=True, count=None, biology=()):
    bodies = [body()] if bodies is None else bodies
    system = dict(system_address=address, name=name, body_count_seen=len(bodies) if count is None else count,
                  all_bodies_found=complete, fss_discovery_scan_seen=fss,
                  **ScoreAnalyzer.parse_system_name(name))
    return observation(system, bodies, biology, {})


class SemanticNameTests(unittest.TestCase):
    def test_two_numbers(self):
        p = ScoreAnalyzer.parse_system_name("Plio Aip KN-B d13-201")
        self.assertEqual((p["sector"], p["code"], p["mass"], p["boxel_number"], p["system_index"], p["family_key"]),
                         ("Plio Aip", "KN-B", "d", 13, 201, "Plio Aip KN-B d13"))

    def test_implicit_zero_boxel(self):
        p = ScoreAnalyzer.parse_system_name("Floarps PI-B e2")
        self.assertEqual((p["boxel_number"], p["system_index"], p["family_key"]), (0, 2, "Floarps PI-B e0"))
        self.assertEqual(p["family_key"], ScoreAnalyzer.parse_system_name("Floarps PI-B e0-2")["family_key"])
        self.assertEqual((p["number"], p["suffix"]), (2, None))  # Old API stays compatible.

    def test_unsupported_name(self):
        for name in ("Sol", "", "Plio Aip KN-B z13-201", "Plio Aip KN-B d13-201 A", "Plio Aip K-B d13-201"):
            with self.subTest(name=name):
                self.assertIsNone(ScoreAnalyzer.parse_system_name(name))
                self.assertEqual(evaluate_observations(name, [])["reason"], "unsupported_name")


class HierarchyTests(unittest.TestCase):
    def setUp(self):
        self.rows = [sample(1, bodies=[body(planet_class="Water world")]),
                     sample(2, "Plio Aip KN-B d13-2"),
                     sample(3, "Plio Aip AB-C d14-1"),
                     sample(4, "Other Sector AB-C d14-1"),
                     sample(5, "Other Sector AB-C b14-1")]

    def result(self, rows=None, target="Plio Aip KN-B d13-201"):
        return evaluate_observations(target, self.rows if rows is None else rows)

    def test_three_levels_have_correct_membership_and_shrinkage(self):
        r = self.result()
        mass, region, family = r["levels"]
        self.assertEqual([(l["systems"], l["hits"]) for l in r["levels"]], [(4, 1), (3, 1), (2, 1)])
        p = (1 + PRIOR_SYSTEMS * 0.2) / (4 + PRIOR_SYSTEMS)
        self.assertAlmostEqual(mass["adjusted_rate"], p)
        p = (1 + PRIOR_SYSTEMS * p) / (3 + PRIOR_SYSTEMS)
        self.assertAlmostEqual(region["adjusted_rate"], p)
        p = (1 + PRIOR_SYSTEMS * p) / (2 + PRIOR_SYSTEMS)
        self.assertAlmostEqual(family["adjusted_rate"], p)
        self.assertAlmostEqual(r["valuable_rate"], p)
        self.assertEqual(mass["data_quality"], "very_low")
        self.assertLess(family["adjusted_rate"], family["rate"])

    def test_large_groups_can_influence_parent_more(self):
        self.assertAlmostEqual(shrink(1, 25, 0), 0.5)
        self.assertGreater(shrink(1, 100, 0), shrink(1, 2, 0))
        self.assertEqual(shrink(None, 0, 0.3), 0.3)

    def test_empty_local_groups_inherit_instead_of_being_negative(self):
        r = self.result(target="Absent Sector ZZ-Z d99-123")
        self.assertEqual([l["systems"] for l in r["levels"]], [4, 0, 0])
        self.assertIsNone(r["levels"][2]["rate"])
        self.assertEqual(r["levels"][2]["adjusted_rate"], r["levels"][0]["adjusted_rate"])
        self.assertEqual(r["levels"][2]["potential_influence"], 0)

    def test_no_mass_history_is_unavailable(self):
        self.assertEqual(self.result(target="Absent Sector ZZ-Z h1-1")["reason"], "no_mass_observations")

    def test_partial_and_unknown_are_neither_negative_nor_positive_samples(self):
        added = [sample(6, complete=False), sample(7, bodies=[], complete=False, fss=False),
                 sample(8, complete=False, bodies=[body(planet_class="Earthlike body")])]
        r = self.result(self.rows + added)
        self.assertEqual(r["levels"], self.result()["levels"])
        self.assertEqual(r["quality_counts"], {"complete": 5, "partial": 2, "unknown": 1})

    def test_count_alone_cannot_prove_complete(self):
        self.assertFalse(sample(complete=False)["qualified"])
        self.assertFalse(sample(count=3)["qualified"])
        self.assertFalse(sample(bodies=[body(scanned=0)])["qualified"])
        self.assertFalse(sample(bodies=[body(planet_class="")])["qualified"])
        self.assertFalse(sample(bodies=[body(planet_class="Unknown class")])["qualified"])

    def test_belts_and_rings_are_excluded_even_with_legacy_planet_type(self):
        row = sample(bodies=[body(), body(body_id=2, name="Test A Belt Cluster 1"),
                             body(body_id=3, name="Test 1 A Ring")], count=1)
        self.assertTrue(row["qualified"])
        self.assertEqual((row["astronomical_bodies"], row["excluded_non_bodies"]), (1, 2))
        self.assertEqual(row["exploration_potential"], sample()["exploration_potential"])

    def test_mapping_ownership_does_not_change_potential(self):
        a = body(planet_class="Water world", self_mapped=True, was_discovered=False, efficient_mapping=False)
        b = body(planet_class="Water world", self_mapped=False, was_discovered=True, efficient_mapping=True)
        self.assertEqual(body_potential(a), body_potential(b))

    def test_outlier_is_capped_and_does_not_move_median(self):
        rows = [dict(exploration_potential=v, counts={}, valuable_hit=False) for v in [100, 100, 100, 100, 20_700_000]]
        stats = summarize(rows, 200)
        self.assertEqual(stats["median"], 100)
        self.assertEqual(stats["winsorized_mean"], 120)

    def test_endnumber_has_no_influence(self):
        results = [self.result(target=f"Plio Aip KN-B d13-{index}") for index in (109, 201, 227)]
        for r in results:
            r.pop("target")
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[1], results[2])

    def test_explicit_common_exclusions_and_case_insensitive_family(self):
        r = evaluate_observations("plio aip kn-b D13-201", self.rows, excluded_system_addresses=[1])
        self.assertEqual([l["hits"] for l in r["levels"]], [0, 0, 0])
        self.assertEqual([l["systems"] for l in r["levels"]], [3, 2, 1])

    def test_no_qualified_data_is_not_a_weak_recommendation(self):
        r = self.result([sample(complete=False)])
        self.assertFalse(r["ok"])
        self.assertNotIn("recommendation", r)

    def test_data_quality_boundaries(self):
        self.assertEqual([quality_label(n) for n in (0, 4, 5, 24, 25, 49, 50)],
                         ["very_low", "very_low", "low", "low", "usable", "usable", "good"])


class BioTests(unittest.TestCase):
    def entry(self, **changes):
        return dict(dict(body_id=1, genus="Bacterium", species="Bacterium Aurasus", variant="",
                         scan_type="Analyse"), **changes)

    def test_unexamined_bio_is_unknown_not_zero(self):
        row = sample()
        self.assertEqual(row["bio"]["state"], "unknown")
        self.assertIsNone(row["bio"]["comparable_base_value"])
        r = evaluate_observations(row["name"], [row])
        self.assertIsNone(r["levels"][0]["bio"]["median_base_value"])
        self.assertIsNone(r["weight_comparison"][1]["potential_index"])

    def test_signals_without_analyses_and_partial_sampling(self):
        row = sample(bodies=[body(biological_signals_seen=2)])
        self.assertEqual(row["bio"]["state"], "signals_only")
        self.assertIsNone(row["bio"]["comparable_base_value"])
        row = sample(bodies=[body(biological_signals_seen=2)], biology=[self.entry()])
        self.assertEqual(row["bio"]["state"], "analyses_present")
        self.assertIsNone(row["bio"]["comparable_base_value"])

    def test_only_covered_known_signals_provide_conditional_value(self):
        row = sample(bodies=[body(biological_signals_seen=1)], biology=[self.entry()])
        self.assertEqual(row["bio"]["state"], "known_signals_analysed")
        self.assertGreater(row["bio"]["comparable_base_value"], 0)
        for entry in [self.entry(scan_type="Sample"), self.entry(species="Unknown organism")]:
            self.assertIsNone(sample(bodies=[body(biological_signals_seen=1)], biology=[entry])["bio"]["comparable_base_value"])

    def test_weight_alternatives_are_diagnostic_only(self):
        rows = [sample(i, bodies=[body(biological_signals_seen=1)], biology=[self.entry()]) for i in range(5)]
        r = evaluate_observations(rows[0]["name"], rows)
        self.assertEqual(r["weights"], {"cartography": 1.0, "biology": 0.0})
        self.assertTrue(all(v["potential_index"] is not None for v in r["weight_comparison"]))
        self.assertEqual(r["weight_comparison"][1]["status"], "diagnostic_selection_biased")


class DatabaseIntegrationTests(unittest.TestCase):
    def test_personal_observations_are_isolated_and_api_does_not_write(self):
        with tempfile.TemporaryDirectory() as directory:
            db = CMDRDatabase(Path(directory) / "test.db")
            a, b = db.upsert_commander("A", "Alpha"), db.upsert_commander("B", "Beta")
            db.active_commander_id = a
            for commander, address, cls in [(a, 1, "Rocky body"), (b, 2, "Earthlike body")]:
                db.store_snapshot(dict(system_address=address, system=f"Plio Aip KN-B d13-{address}",
                                       system_body_count=1, system_all_bodies_found=True,
                                       fss_discovery_scan_seen=True, system_bodies=[body(planet_class=cls)]), commander)
            with db._connect() as con:
                before = list(con.iterdump())
            api = HierarchicalJumpTip(db)
            self.assertEqual(len(api.observations()), 1)
            r = api.evaluate("Plio Aip KN-B d13-201")
            self.assertEqual(r["levels"][0]["hits"], 0)
            db.active_commander_id = b
            self.assertEqual(api.evaluate("Plio Aip KN-B d13-201")["levels"][0]["hits"], 1)
            with db._connect() as con:
                self.assertEqual(list(con.iterdump()), before)


if __name__ == "__main__":
    unittest.main()
