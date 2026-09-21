"""German offline names preserve identities and the other eleven locales."""
import csv
from dataclasses import replace
from pathlib import Path
import unittest

from cmdrhelper._commodity_localization_de import GERMAN_NAMES
from cmdrhelper.commodity_localization import commodity_name
from cmdrhelper.commodity_master import all_commodities, lookup_by_id, lookup_by_symbol, CommodityDefinition
from cmdrhelper.i18n import _TRANSLATIONS, tr_for_language


class CommodityLocalizationTests(unittest.TestCase):
    def test_all_curated_names_have_exact_master_identity_and_provenance(self):
        self.assertEqual(len(all_commodities()), 412)
        self.assertEqual(len(GERMAN_NAMES), 354)
        with (Path(__file__).resolve().parents[1] / 'docs/commodity-localization-sources.csv').open() as source:
            provenance = list(csv.DictReader(source))
        self.assertEqual(len(provenance), 354)
        by_id = {int(row['frontier_id']): row for row in provenance}
        for identifier, symbol, name, source in GERMAN_NAMES:
            item = lookup_by_id(identifier)
            self.assertEqual(item.symbol, symbol)
            self.assertIs(lookup_by_symbol(symbol), item)
            self.assertEqual(commodity_name(item, 'de'), name)
            self.assertEqual(by_id[identifier]['de'], name)
            self.assertEqual(by_id[identifier]['symbol'], symbol)
            self.assertTrue(by_id[identifier]['review'])
            self.assertEqual(by_id[identifier]['license'], 'Apache-2.0')
            self.assertIn(source, ('EDDI', 'EDDiscovery'))

    def test_german_coverage_and_curated_fallback(self):
        maintained = {row[0] for row in GERMAN_NAMES}
        maintained.update(c.frontier_id for c in all_commodities() if c.mining_origins)
        self.assertEqual(len(maintained), 411)
        missing = [c for c in all_commodities() if c.frontier_id not in maintained]
        self.assertEqual([c.symbol for c in missing], ['CuratedCommodity'])
        self.assertEqual(missing[0].frontier_id, 129045961)
        self.assertEqual(commodity_name(missing[0], 'de'), 'Curated Commodity Package')

    def test_only_requested_mining_corrections(self):
        for symbol, name in [('Cobalt', 'Kobalt'), ('Praseodymium', 'Praseodym'), ('PericlaseDunite', 'Periklas-Dunit')]:
            self.assertEqual(commodity_name(lookup_by_symbol(symbol), 'de'), name)
            self.assertEqual(_TRANSLATIONS['de']['mining.commodity.' + symbol.casefold()], name)

    def test_other_languages_keep_existing_mining_and_english_fallback(self):
        for language in _TRANSLATIONS:
            if language == 'de':
                continue
            for item in all_commodities():
                key = 'mining.commodity.' + item.symbol.casefold()
                expected = tr_for_language(language, key) if item.mining_origins else item.english_name
                self.assertEqual(commodity_name(item, language), expected)

    def test_unknown_future_goods_and_mismatched_identity(self):
        future = CommodityDefinition(999999999, 'Future_TestCommodity', 'Future Commodity', 'Salvage', False)
        self.assertEqual(commodity_name(future, 'de'), 'Future Commodity')
        self.assertEqual(commodity_name(replace(future, english_name=''), 'de'), 'Future Test Commodity')
        beer = lookup_by_symbol('Beer')
        self.assertEqual(commodity_name(replace(future, frontier_id=beer.frontier_id), 'de'), 'Future Commodity')

    def test_names_do_not_change_master_metadata(self):
        before = tuple(all_commodities())
        for item in before:
            for language in _TRANSLATIONS:
                commodity_name(item, language)
        self.assertEqual(all_commodities(), before)
        self.assertEqual(sum(c.rare for c in before), 142)
        self.assertEqual(sum(bool(c.mining_origins) for c in before), 57)
