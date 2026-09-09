from collections import Counter
from dataclasses import FrozenInstanceError, replace
from importlib import import_module
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cmdrhelper import i18n
from cmdrhelper._material_catalog_data import LEGACY_I18N_KEYS
from cmdrhelper.material_catalog import (
    CatalogStock, all_materials, get_material, localized_name,
    materials_by_category, merge_inventory, _validate,
)
from cmdrhelper.material_inventory import MaterialInventory, MaterialInventoryReader, _Reducer
from tools.check_i18n import intentional_english_fallback, load_translation_file


def snapshot(**categories):
    return dict(timestamp="2026-09-08T10:00:00Z", event="Materials",
                **{cat: categories.get(cat, []) for cat in ("Raw", "Manufactured", "Encoded")})


def reduced(*events):
    reducer = _Reducer(1, "F1")
    for offset, event in enumerate(events):
        reducer.apply(event, ("fixture", offset))
    return reducer.result


def indexed(inventory):
    return {row.material.symbol: row for row in merge_inventory(inventory)}


class MaterialCatalogTests(unittest.TestCase):
    def test_catalog_counts_and_distribution(self):
        materials = all_materials()
        self.assertEqual(len(materials), 146)
        self.assertEqual(len({m.symbol for m in materials}), 146)
        self.assertEqual(Counter(m.group for m in materials), dict(standard=108, guardian=13, thargoid=25))
        expected = {"Raw": [7, 7, 7, 7, 0, 0], "Manufactured": [13, 14, 17, 13, 14, 0],
                    "Encoded": [7, 8, 12, 10, 9, 1]}
        for cat, grades in expected.items():
            counts = Counter(m.grade for m in materials_by_category(cat))
            self.assertEqual([counts[g] for g in (1, 2, 3, 4, 5, None)], grades)
        self.assertEqual([len(materials_by_category(c)) for c in expected], [28, 71, 47])
        with self.assertRaises(ValueError):
            materials_by_category("Data")

    def test_identity_validation_and_immutability(self):
        self.assertEqual(get_material("$VANADIUM_Name;"), get_material("vanadium"))
        self.assertIsNone(get_material("Schwefel"))
        self.assertIsNone(get_material("tg_structuraldata02"))
        for m in all_materials():
            self.assertRegex(m.symbol, r"^[a-z0-9_]+$")
            self.assertEqual(m.i18n_key, "body_detail.material." + m.symbol)
        with self.assertRaises(FrozenInstanceError):
            get_material("vanadium").maximum = 42
        with self.assertRaises(ValueError):
            _validate(all_materials()[:-1])
        with self.assertRaises(ValueError):
            _validate(all_materials()[:-1] + (all_materials()[0],))

    def test_explicit_capacities_and_guardian_corrections(self):
        # Independent expected exceptions, not derived from the catalog.
        exceptions = {"ancienthistoricaldata": (1, 150), "ancientculturaldata": (2, 150),
                      "ancientbiologicaldata": (3, 150), "ancientlanguagedata": (4, 150),
                      "ancienttechnologicaldata": (4, 150), "guardian_moduleblueprint": (5, 150),
                      "guardian_weaponblueprint": (5, 150), "guardian_vesselblueprint": (5, 100),
                      "unknowncorechip": (2, 100)}
        for m in all_materials():
            if m.symbol in exceptions:
                self.assertEqual((m.grade, m.maximum), exceptions[m.symbol], m.symbol)
            elif m.symbol == "tg_shipsystemsdata":
                self.assertIsNone(m.grade)
                self.assertIsNone(m.maximum)
            else:
                self.assertEqual(m.maximum, {1: 300, 2: 250, 3: 200, 4: 150, 5: 100}[m.grade], m.symbol)

    def test_new_materials(self):
        additions = {"tg_abrasion03": 1, "tg_causticshard": 2, "unknowncorechip": 2,
                     "tg_causticgeneratorparts": 3, "tg_abrasion02": 3, "tg_causticcrystal": 4,
                     "tg_abrasion01": 5, "tg_shutdowndata": 3, "tg_interdictiondata": 3}
        for symbol, grade in additions.items():
            m = get_material(symbol)
            self.assertEqual((m.grade, m.group), (grade, "thargoid"))

    def test_zero_unknown_and_phase1_identity_preserved(self):
        inventory = reduced(snapshot())
        self.assertEqual(inventory.stocks, {})
        rows = merge_inventory(inventory)
        self.assertTrue(all(row.known and row.count == 0 for row in rows))
        self.assertEqual(inventory.stocks, {})
        self.assertFalse(inventory.material("vanadium").known)
        unknown = MaterialInventory(2, "F2")
        self.assertTrue(all(not r.known and r.count is None and r.percent is None
                            and r.fill_state is None for r in merge_inventory(unknown)))
        inventory.issues.append("unreliable source")
        self.assertTrue(all(not r.known and r.count is None for r in merge_inventory(inventory)))

    def test_category_conflict_is_not_reinterpreted(self):
        inventory = reduced(snapshot(Raw=[dict(Name="dataminedwake", Count=3)]))
        row = indexed(inventory)["dataminedwake"]
        self.assertFalse(row.known)
        self.assertIsNone(row.count)

    def test_percent_boundaries_unknown_capacity_and_over_capacity(self):
        base = CatalogStock(get_material("vanadium"), 1, "F1", "snapshot", 244, True)
        self.assertEqual(base.percent, 97.6)
        for count, expected in [(0, "empty"), (1, "low"), (50, "low"), (51, None),
                                (199, None), (200, "near_full"), (249, "near_full"),
                                (250, "full"), (251, None)]:
            self.assertEqual(replace(base, count=count).fill_state, expected, count)
        self.assertEqual(replace(base, count=251).percent, 100.4)
        for symbol, count in (("guardian_moduleblueprint", 75), ("ancienthistoricaldata", 75),
                              ("unknowncorechip", 50)):
            self.assertEqual(replace(base, material=get_material(symbol), count=count).percent, 50)
        for count in (0, 3, None):
            row = replace(base, material=get_material("tg_shipsystemsdata"), count=count)
            self.assertIsNone(row.percent)
            self.assertIsNone(row.fill_state)

    def test_data_reward_admits_never_owned_encoded_and_excludes_odyssey(self):
        reward = dict(timestamp="2026-09-08T10:01:00Z", event="MissionCompleted", MaterialsReward=[
            dict(Name="$DATAMINEDWAKE_Name;", Category="$microresource_category_data;", Count=3),
            dict(Name="tg_interdictiondata", Category="Data", Count=2),
            dict(Name="settlementdefenceplans", Category="Data", Count=10),
            dict(Name="sulphur", Category="Data", Count=10),
            dict(Name="dataminedwake", Category="Item", Count=10)])
        inventory = reduced(snapshot(), reward)
        self.assertTrue(inventory.known, inventory.issues)
        self.assertEqual(inventory.material("dataminedwake").count, 3)
        self.assertEqual(inventory.material("tg_interdictiondata").count, 2)
        self.assertNotIn("settlementdefenceplans", inventory.stocks)
        self.assertEqual(indexed(inventory)["sulphur"].count, 0)
        self.assertTrue(all(r.count is None for r in merge_inventory(reduced(reward))))

    def test_faber38_catalog_projection(self):
        events = json.loads((Path(__file__).parent / "fixtures/materials_faber38.json").read_text())
        inventory = reduced(*events)
        self.assertTrue(inventory.known, inventory.issues)
        self.assertEqual([len(inventory.by_category(c)) for c in ("Raw", "Manufactured", "Encoded")], [28, 56, 35])
        for symbol, stock in inventory.stocks.items():
            self.assertIsNotNone(get_material(symbol), symbol)
            self.assertEqual(get_material(symbol).category, stock.category)
        rows = indexed(inventory)
        self.assertEqual(len(rows), 146)
        for symbol, count in dict(sulphur=300, vanadium=244, tin=53, molybdenum=63,
                                  niobium=53, yttrium=35, dataminedwake=0).items():
            self.assertEqual(rows[symbol].count, count)
        self.assertEqual(rows["vanadium"].percent, 97.6)
        self.assertEqual(sum(r.count == 0 for r in rows.values()), 28)
        self.assertEqual(sum(s not in inventory.stocks for s in rows), 27)
        self.assertTrue(all(rows[s].count == 0 for s in rows if s not in inventory.stocks))

    def test_two_commanders_shared_catalog_separate_journals_and_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            sessions = []
            for cid, fid, amount, reward in ((1, "F1", 40, 3), (2, "F2", 200, 7)):
                events = [dict(event="Commander", FID=fid),
                          snapshot(Raw=[dict(Name="vanadium", Count=amount)]),
                          dict(event="MissionCompleted", timestamp="2026-09-08T10:01:00Z",
                               MaterialsReward=[dict(Name="dataminedwake", Category="Data", Count=reward)])]
                path = Path(directory) / (fid + ".log")
                path.write_text("".join(json.dumps(e) + "\n" for e in events))
                sessions.append(dict(commander_id=cid, fid_seen=fid, journal_file=str(path), attribution_status="identified"))
            reader = MaterialInventoryReader()
            for cid, fid, amount, reward in ((1, "F1", 40, 3), (2, "F2", 200, 7), (1, "F1", 40, 3)):
                inventory = reader.reconstruct(cid, fid, sessions * 2)
                rows = indexed(inventory)
                self.assertEqual((rows["vanadium"].count, rows["dataminedwake"].count), (amount, reward))
                self.assertTrue(all((r.commander_id, r.fid) == (cid, fid) for r in rows.values()))
                self.assertEqual(rows, indexed(MaterialInventoryReader().reconstruct(cid, fid, sessions)))
                self.assertIs(rows["vanadium"].material, get_material("vanadium"))

    def test_translation_coverage_and_fallback_without_language_mutation(self):
        coverage = dict(en=146, de=146, it=146, fr=135, es=135,
                        no=24, sv=24, fi=24, pl=24, nl=24, tr=24, el=24)
        self.assertEqual(len(LEGACY_I18N_KEYS), 24)
        previous = i18n.get_language()
        self.addCleanup(i18n.set_language, previous)
        i18n.set_language("de")
        for language, expected in coverage.items():
            module = import_module("cmdrhelper.i18n." + language)
            translations, duplicates = load_translation_file(Path(module.__file__))
            self.assertFalse(duplicates)
            self.assertTrue(all(translations.get(k) for k in LEGACY_I18N_KEYS))
            self.assertEqual(sum(bool(translations.get(m.i18n_key)) for m in all_materials()), expected)
            for material in all_materials():
                self.assertEqual(localized_name(material.symbol, language),
                                 translations.get(material.i18n_key, material.english_name))
            i18n.set_language(language)
            self.assertEqual(i18n.tr(get_material("unknowncorechip").i18n_key),
                             localized_name("unknowncorechip", language))
        i18n.set_language("de")
        self.assertEqual(localized_name("unknowncorechip", "fi"), get_material("unknowncorechip").english_name)
        self.assertEqual(localized_name("unknowncorechip", "unsupported"), get_material("unknowncorechip").english_name)
        self.assertEqual(localized_name("sulphur"), "Schwefel")
        self.assertEqual(i18n.get_language(), "de")
        self.assertEqual(i18n.tr_for_language("en", "missing.key"), "missing.key")
        format_key = "test.format"
        with patch.dict(i18n.EN, {format_key: "Language: {language}"}):
            self.assertEqual(i18n.tr(format_key, language="English"), "Language: English")
        with self.assertRaises(KeyError):
            localized_name("unknown_material")

    def test_checker_allows_only_new_material_fallback_with_english(self):
        new = get_material("unknowncorechip").i18n_key
        self.assertTrue(intentional_english_fallback(new, {new: "Tactical Core Chip"}))
        self.assertFalse(intentional_english_fallback(new, {}))
        self.assertFalse(intentional_english_fallback(new, {new: ""}))
        for key in ("body_detail.material.sulphur", "body_detail.material.not_in_catalog", "some.ui.key"):
            self.assertFalse(intentional_english_fallback(key, {key: "text"}))
