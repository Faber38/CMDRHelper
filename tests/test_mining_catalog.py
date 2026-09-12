"""Pin the project owner's reference snapshot, independently of UI formatting."""
import unittest

from cmdrhelper.mining_catalog import MINING_COMMODITIES, value_class


class MiningCatalogTests(unittest.TestCase):
    def test_exact_supplied_reference_snapshot(self):
        expected = {
            "monazite": 268661,
            "alexandrite": 229207,
            "grandidierite": 213547,
            "iridium": 208463,
            "periclasedunite": 204168,
            "thortveitite": 203892,
            "serendibite": 188438,
            "rhodplumsite": 187921,
            "diamond": 134784,
            "lowtemperaturediamond": 130184,
            "sapphire": 128050,
            "ruby": 110381,
            "helium": 102861,
            "helium3": 96223,
            "bastnasite": 78583,
            "platinum": 70998,
            "osmium": 56471,
            "tritium": 53311,
            "palladium": 52167,
            "gold": 48005,
            "quartzpyroxenite": 46469,
            "deuterium": 40762,
            "magnesite": 38198,
            "silver": 37743,
            "olivine": 31417,
            "samarium": 28362,
            "bertrandite": 18489,
            "tantalum": 14360,
            "thorium": 12297,
            "uranium": 7599,
            "titanium": 4800,
            "uraninite": 3006,
            "haematite": 2800,
            "methanolmonohydratecrystals": 2525,
            "lithium": 2099,
            "copper": 774,
            "water": 496,
        }
        original = [c for c in MINING_COMMODITIES if c.price_source == "project-reference-2026-09-12"]
        self.assertEqual(len(original), 37)
        self.assertEqual({c.symbol: c.average_price for c in original}, expected)
        self.assertNotIn("opal", expected)
        self.assertNotIn("painite", expected)

    def test_expanded_catalog_origins_and_unknown_prices(self):
        catalog = {c.symbol: c for c in MINING_COMMODITIES}
        self.assertEqual(len(catalog), len(MINING_COMMODITIES))
        self.assertEqual(len(catalog), 57)
        self.assertEqual((catalog["jadeite"].average_price, catalog["jadeite"].origin), (41895, "surface"))
        self.assertEqual(value_class(catalog["jadeite"].average_price), "medium")
        self.assertEqual(catalog["platinum"].origin, "both")
        for symbol in ("taaffeite", "moissanite"):
            self.assertEqual(catalog[symbol].origin, "surface")
        for symbol in ("benitoite", "bromellite", "painite", "opal"):
            self.assertEqual(catalog[symbol].origin, "asteroid")
        self.assertEqual({c.origin for c in catalog.values()}, {"surface", "asteroid", "both"})
        for c in catalog.values():
            if c.price_source is None:
                self.assertIsNone(c.average_price)
                self.assertIsNone(value_class(c.average_price))
        self.assertNotIn("cryolite", catalog)  # Extraction economy is not a mining proof.
        self.assertNotIn("pyrophyllite", catalog)
