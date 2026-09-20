"""Pinned offline identity snapshot and lossless resolver boundaries."""
from collections import Counter
from dataclasses import FrozenInstanceError, replace
import hashlib
import json
import unittest

from cmdrhelper._commodity_master_data import COMMODITIES, UPSTREAM_REVISION, SOURCE_FILES
from cmdrhelper.commodity_master import (
    CATEGORIES, _build_indexes, all_commodities,
    lookup_by_id, lookup_by_symbol, resolve_symbol,
)
from cmdrhelper.mining_catalog import MINING_COMMODITIES


class CommodityMasterTests(unittest.TestCase):
    def test_exact_snapshot_content(self):
        raw = json.dumps(COMMODITIES, ensure_ascii=False, separators=(',', ':')).encode()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         'faf08355c9808bd30016d5032c2cac76336b52292a7e311bd925513b067ac7ca')
        self.assertEqual(UPSTREAM_REVISION, 'c35612952dd6a547d1a7ac4cffab9c7051e86579')
        self.assertEqual({s[0] for s in SOURCE_FILES}, {'commodity.csv', 'rare_commodity.csv'})

    def test_unique_ids_and_symbols(self):
        items = all_commodities()
        self.assertEqual(len(items), 412)
        self.assertEqual(len({c.frontier_id for c in items}), 412)
        self.assertEqual(len({c.symbol for c in items}), 412)
        self.assertEqual(len({c.symbol.casefold() for c in items}), 412)

    def test_categories(self):
        self.assertEqual(Counter(c.category for c in all_commodities()), {
            'Chemicals': 20, 'Consumer Items': 33, 'Foods': 51,
            'Industrial Materials': 10, 'Legal Drugs': 36, 'Machinery': 28,
            'Medicines': 16, 'Metals': 29, 'Minerals': 39, 'NonMarketable': 1,
            'Salvage': 99, 'Slavery': 3, 'Technology': 20, 'Textiles': 13,
            'Waste': 4, 'Weapons': 10,
        })
        self.assertEqual({c.category for c in all_commodities()}, CATEGORIES)

    def test_rare_membership(self):
        self.assertEqual(sum(c.rare for c in all_commodities()), 142)
        self.assertEqual(sum(not c.rare for c in all_commodities()), 270)
        self.assertTrue(lookup_by_symbol('LavianBrandy').rare)
        self.assertTrue(lookup_by_symbol('PersonalGifts').rare)
        self.assertFalse(lookup_by_symbol('platinum').rare)

    def test_mining_links_preserve_existing_evidence(self):
        linked = {c.symbol.casefold(): c for c in all_commodities() if c.mining_origins}
        self.assertEqual(set(linked), {c.symbol for c in MINING_COMMODITIES})
        self.assertEqual(len(linked), 57)
        for old in MINING_COMMODITIES:
            expected = ('surface', 'asteroid') if old.origin == 'both' else (old.origin,)
            self.assertEqual(linked[old.symbol].mining_origins, expected)
        self.assertEqual(Counter(c.mining_origins for c in linked.values()),
                         {('surface',): 22, ('asteroid',): 17, ('surface', 'asteroid'): 18})
        self.assertEqual(sum('surface' in c.mining_origins for c in linked.values()), 40)
        self.assertEqual(sum('asteroid' in c.mining_origins for c in linked.values()), 35)

    def test_known_symbol_forms_resolve_to_exact_upstream(self):
        for value in ('platinum', 'Platinum', 'PLATINUM', '$platinum_name;',
                      '$Platinum_Name;', ' platinum '):
            with self.subTest(value=value):
                self.assertEqual(resolve_symbol(value), 'Platinum')
                self.assertIs(lookup_by_symbol(value), lookup_by_id(128049152))

    def test_every_symbol_and_wrapper_is_unambiguous(self):
        for item in all_commodities():
            for value in (item.symbol, item.symbol.lower(), item.symbol.upper(),
                          '$' + item.symbol.lower() + '_name;'):
                with self.subTest(value=value):
                    self.assertIs(lookup_by_symbol(value), item)
                    self.assertEqual(resolve_symbol(value), item.symbol)

    def test_tissue_sample_underscores_and_case_survive(self):
        item = lookup_by_id(128922517)
        self.assertEqual(item.symbol, 'M_TissueSample_Fluid')
        for value in ('m_tissuesample_fluid', '$m_tissuesample_fluid_name;'):
            self.assertEqual(resolve_symbol(value), item.symbol)
        for value in ('mtissuesamplefluid', 'M TissueSample Fluid'):
            self.assertIsNone(lookup_by_symbol(value))
            self.assertEqual(resolve_symbol(value), value)

    def test_upstream_spelling_is_not_corrected(self):
        self.assertEqual(lookup_by_id(129022087).symbol, 'UnocuppiedEscapePod')
        self.assertEqual(resolve_symbol('unocuppiedescapepod'), 'UnocuppiedEscapePod')
        self.assertEqual(resolve_symbol('UnoccupiedEscapePod'), 'UnoccupiedEscapePod')
        self.assertIsNone(lookup_by_symbol('UnoccupiedEscapePod'))

    def test_unknown_input_is_preserved_verbatim(self):
        for value in ('UnknownGoods', '$Future_Mineral_Name;', ' future_Goods ', '',
                      '$platinum_name', 'platinum_name;', '$platinum;', 'Platin', '0'):
            with self.subTest(value=value):
                self.assertIsNone(lookup_by_symbol(value))
                self.assertEqual(resolve_symbol(value), value)

    def test_diagnostic_sensor(self):
        item = lookup_by_symbol('$DiagnosticSensor_Name;')
        self.assertEqual(item.frontier_id, 128673875)
        self.assertEqual(item.symbol, 'DiagnosticSensor')
        self.assertEqual(item.english_name, 'Hardware Diagnostic Sensor')

    def test_drones_are_limpets_without_display_name_identity(self):
        item = lookup_by_symbol('drones')
        self.assertEqual(item.frontier_id, 128066403)
        self.assertEqual(item.symbol, 'Drones')
        self.assertEqual(item.english_name, 'Limpets')
        self.assertEqual(item.category, 'NonMarketable')
        self.assertFalse(hasattr(item, 'marketable'))
        self.assertFalse(hasattr(item, 'average_price'))
        self.assertIsNone(lookup_by_symbol('Limpets'))
        self.assertEqual(resolve_symbol('Limpets'), 'Limpets')

    def test_invalid_ids_and_input_types(self):
        for value in (True, False, 128049152.0, '128049152', None, -1, 0):
            self.assertIsNone(lookup_by_id(value))
        for value in (None, 0, False):
            self.assertIsNone(lookup_by_symbol(value))
            with self.assertRaises(TypeError):
                resolve_symbol(value)

    def test_ambiguous_definitions_are_rejected(self):
        item = lookup_by_symbol('platinum')
        for other in (replace(item, symbol='Other'),
                      replace(item, frontier_id=999, symbol='platinum')):
            with self.assertRaises(ValueError):
                _build_indexes((item, other))
        with self.assertRaises(ValueError):
            _build_indexes((replace(item, category='UnknownCategory'),))

    def test_definitions_and_indexes_are_immutable(self):
        self.assertIsInstance(all_commodities(), tuple)
        with self.assertRaises(FrozenInstanceError):
            lookup_by_symbol('platinum').symbol = 'changed'
        by_id, by_symbol = _build_indexes(all_commodities())
        with self.assertRaises(TypeError):
            by_id[1] = lookup_by_symbol('platinum')
        with self.assertRaises(TypeError):
            by_symbol['platinum'] = None
