from collections import Counter
from copy import deepcopy
from dataclasses import FrozenInstanceError, fields, replace
import json
from pathlib import Path
import tempfile
import unittest

from cmdrhelper import i18n
from cmdrhelper.odyssey_catalog import (
    OdysseyDefinition, _validate, all_materials, capacity, get_material,
    localized_name, materials_by_category, merge_inventory, translation_coverage,
)
from cmdrhelper.odyssey_inventory import OdysseyInventoryReader, OdysseyReducer
from tests.test_odyssey_inventory import event, item, snapshot


def inventory(*records, commander=1, fid='F1'):
    reducer = OdysseyReducer(commander, fid)
    for index, record in enumerate(records):
        reducer.apply(record, ('test', index))
    return reducer.result


class OdysseyCatalogTests(unittest.TestCase):
    def test_exact_identities_and_categories(self):
        self.assertEqual(len(all_materials()), 223)
        self.assertEqual(len({m.symbol for m in all_materials()}), 223)
        expected = dict(Items=61, Components=33, Data=123, Consumables=6)
        self.assertEqual(Counter(m.category for m in all_materials()), expected)
        for cat, count in expected.items():
            self.assertEqual(len(materials_by_category(cat)), count)

    def test_exclusions_and_canonical_lookup(self):
        for name in ('powermegashipdata', 'UNKNOWN', 'None', 'geographicaldata', '', None):
            self.assertIsNone(get_material(name))
        self.assertIs(get_material('$Graphene_Name;'), get_material('graphene'))
        self.assertIsNone(get_material('surveillancelogs'))
        self.assertIsNotNone(get_material('surveilleancelogs'))
        with self.assertRaises(ValueError):
            materials_by_category('Encoded')

    def test_component_subgroups(self):
        self.assertEqual(Counter(m.subgroup for m in materials_by_category('Components')),
                         dict(Chemicals=10, Circuits=12, Tech=11))
        self.assertTrue(all(m.subgroup is None for m in all_materials() if m.category != 'Components'))

    def test_engineering_flags_exact(self):
        self.assertEqual(sum(m.engineering_relevant for m in all_materials()), 98)
        self.assertEqual(Counter(f for m in all_materials() for f in m.engineering_flags),
                         dict(suit_upgrade=7, weapon_upgrade=9, suit_modification=50,
                              weapon_modification=46, engineer_unlock=19))
        self.assertEqual(get_material('graphene').engineering_flags, {'suit_upgrade'})
        self.assertEqual(get_material('manufacturinginstructions').engineering_flags,
                         {'suit_upgrade', 'weapon_upgrade', 'engineer_unlock'})
        self.assertFalse(get_material('largecapacitypowerregulator').engineering_relevant)
        self.assertFalse(get_material('healthpack').engineering_relevant)

    def test_powerinventory_and_special_groups(self):
        m = get_material('powerinventory')
        self.assertEqual((m.category, m.name_en, m.special_group),
                         ('Items', 'Inventory Record', 'powerplay'))
        self.assertFalse(m.engineering_relevant)
        self.assertEqual(Counter(m.special_group for m in all_materials()),
                         dict(standard=196, powerplay=22, thargoid_spire=2, operations=2, unica=1))
        for name, group in [('biomechanicalcomponent', 'thargoid_spire'),
                            ('sabotagedcomponent', 'thargoid_spire'),
                            ('operationsstrikedata', 'operations'),
                            ('operationscounterattackdata', 'operations'), ('nm_seed', 'unica')]:
            self.assertEqual(get_material(name).special_group, group)
            self.assertEqual(get_material(name).availability_status, 'context_dependent')

    def test_upload_usage_does_not_imply_mission(self):
        expected = {'spyware', 'virus', 'powerpreparationspyware', 'powerspyware',
                    'operationscounterattackdata'}
        self.assertEqual({m.symbol for m in all_materials() if 'upload' in m.usage_tags}, expected)
        names = {f.name for f in fields(OdysseyDefinition)}
        self.assertFalse(names & {'mission', 'mission_id', 'MissionID', 'mission_status', 'maximum'})

    def test_definitions_are_immutable(self):
        m = get_material('graphene')
        with self.assertRaises(FrozenInstanceError):
            m.name_en = 'changed'
        with self.assertRaises(AttributeError):
            m.engineering_flags.add('changed')

    def test_validation_rejects_corruption(self):
        entries = list(all_materials())
        entries[0] = entries[1]
        with self.assertRaises(ValueError): _validate(entries)
        entries = list(all_materials())
        entries[0] = replace(entries[0], i18n_key='wrong')
        with self.assertRaises(ValueError): _validate(entries)

    def test_locker_category_limits(self):
        for cat in ('Items', 'Components', 'Data'):
            self.assertEqual(capacity('ShipLocker', cat), 1000)
            self.assertEqual(capacity('ShipLocker', cat, extra_backpack=True), 1000)
        with self.assertRaises(ValueError): capacity('Total', 'Data')

    def test_backpack_limits_and_modifier(self):
        for suit, values in dict(maverick=(40, 60, 20), artemis=(20, 40, 10),
                                 dominator=(10, 20, 10), flight_suit=(5, 10, 10)).items():
            for cat, expected in zip(('Items', 'Components', 'Data'), values):
                with self.subTest(suit=suit, category=cat):
                    self.assertEqual(capacity('Backpack', cat, suit=suit), expected)
                    self.assertEqual(capacity('Backpack', cat, suit=suit, extra_backpack=True), 2*expected)

    def test_unknown_capacities(self):
        for container in ('ShipLocker', 'Backpack'):
            for suit in (None, 'maverick', 'artemis', 'dominator', 'flight_suit'):
                self.assertIsNone(capacity(container, 'Consumables', suit=suit, extra_backpack=True))
        self.assertIsNone(capacity('Backpack', 'Data'))
        self.assertIsNone(capacity('Backpack', 'Data', suit='unconfirmed'))
        self.assertIsNone(capacity('Backpack', 'Data', suit='maverick', extra_backpack=None))
        with self.assertRaises(ValueError): capacity('ShipLocker', 'Encoded')

    def test_exact_translation_coverage(self):
        self.assertEqual(translation_coverage(), dict(en=223, de=221, es=223, it=217, fr=205,
                         no=0, sv=0, fi=0, pl=0, nl=0, tr=0, el=0))
        for m in all_materials():
            self.assertEqual(localized_name(m.symbol, 'en'), m.name_en)
            self.assertTrue(localized_name(m.symbol, 'es'))

    def test_missing_languages_fall_back_to_english(self):
        for lang in ('no', 'sv', 'fi', 'pl', 'nl', 'tr', 'el', 'unknown'):
            for m in all_materials():
                self.assertEqual(localized_name(m.symbol, lang), m.name_en)

    def test_german_gaps_use_english(self):
        self.assertEqual(localized_name('operationsstrikedata', 'de'), 'Researcher Location Data')
        self.assertEqual(localized_name('operationscounterattackdata', 'de'), 'Facilities Intelligence Report')
        self.assertEqual(localized_name('powerinventory', 'de'), 'Inventaraufzeichnung')
        self.assertEqual(localized_name('graphene', 'de'), 'Graphen')

    def test_partial_language_fallback(self):
        for symbol in ('biologicalweapondata', 'biometricdata', 'digitaldesigns',
                       'operationsstrikedata', 'operationscounterattackdata', 'nm_seed'):
            self.assertEqual(localized_name(symbol, 'it'), get_material(symbol).name_en)
        self.assertEqual(localized_name('powerinventory', 'fr'), 'Inventory Record')

    def test_current_language_without_i18n_mutation(self):
        before = deepcopy(i18n._TRANSLATIONS)
        old = i18n.get_language()
        try:
            i18n.set_language('de')
            self.assertEqual(localized_name('graphene'), 'Graphen')
            self.assertEqual(localized_name('graphene', 'en'), 'Graphene')
            self.assertEqual(i18n.get_language(), 'de')
            self.assertEqual(i18n._TRANSLATIONS, before)
        finally:
            i18n.set_language(old)

    def test_projection_retains_mission_owner_stolen_and_normal_stacks(self):
        r = inventory(snapshot('ShipLocker', Items=[
            dict(Name='vehicleschematic', Count=2, OwnerID=0, Stolen=False),
            dict(Name='vehicleschematic', Count=1, OwnerID=99, MissionID=42, Stolen=True)]),
            snapshot('Backpack'), event('MissionCompleted', 1, MissionID=42))
        before = deepcopy(r)
        rows = merge_inventory(r, 'de')
        original = [row for row in rows if row.observed]
        self.assertEqual([row.stock for row in original], list(r.rows))
        self.assertEqual(r, before)
        self.assertEqual(len(rows), 224)
        missions = [row for row in rows if row.matches_filter('mission')]
        self.assertEqual(len(missions), 1)
        self.assertEqual((missions[0].key.mission_id, missions[0].key.owner_id,
                          missions[0].key.stolen, missions[0].stock.mission_status),
                         (42, 99, True, 'completed'))
        self.assertEqual(missions[0].stock.total, 1)

    def test_no_invented_normal_stack_for_mission_only_identity(self):
        r = inventory(snapshot('ShipLocker', Items=[item('vehicleschematic', 1, MissionID=42)]),
                      snapshot('Backpack'))
        rows = [x for x in merge_inventory(r) if x.key.name == 'vehicleschematic']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].key.mission_id, 42)

    def test_known_zero_and_all_filters(self):
        r = inventory(snapshot('ShipLocker', Components=[item('graphene', 3)]),
                      snapshot('Backpack', Consumables=[item('healthpack', 2)]))
        rows = merge_inventory(r)
        by_name = {row.key.name: row for row in rows}
        self.assertEqual(len(rows), 223)
        self.assertTrue(all(row.matches_filter('all') for row in rows))
        self.assertEqual(sum(row.matches_filter('empty') for row in rows), 221)
        self.assertEqual(sum(row.matches_filter('engineering') for row in rows), 98)
        self.assertTrue(by_name['healthpack'].matches_filter('backpack'))
        self.assertFalse(by_name['healthpack'].matches_filter('locker'))
        self.assertTrue(by_name['graphene'].matches_filter('locker'))
        self.assertFalse(any(row.matches_filter('mission') for row in rows))
        self.assertFalse(by_name['healthpack'].matches_filter('engineering'))
        with self.assertRaises(ValueError): by_name['graphene'].matches_filter('full')

    def test_unknown_and_incoherent_counts_not_zero(self):
        for r in (inventory(), inventory(snapshot('ShipLocker'), snapshot('Backpack', 2))):
            rows = merge_inventory(r)
            self.assertEqual(len(rows), 223)
            self.assertTrue(all(row.stock.total is None for row in rows))
            self.assertFalse(any(row.matches_filter('empty') for row in rows))

    def test_future_symbol_and_category_conflict_preserved(self):
        r = inventory(snapshot('ShipLocker', Items=[item('futurething', 3, Name_Localised='Future item'),
                      item('graphene', 2)]), snapshot('Backpack'))
        rows = merge_inventory(r, include_absent=False)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row.definition is None for row in rows))
        self.assertEqual(next(row.name for row in rows if row.key.name == 'futurething'), 'Future item')
        self.assertEqual(sum(row.stock.total for row in rows), 5)

    def test_real_faber38_reader_and_projection(self):
        fixture = Path(__file__).parent / 'fixtures/odyssey_faber38.json'
        records = json.loads(fixture.read_text())
        reader = OdysseyInventoryReader()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'Journal.log'
            path.write_text(''.join(json.dumps(e)+'\n' for e in
                            [event('Commander', FID='FTEST0001')] + records))
            sessions = [dict(journal_file=str(path), commander_id=1, fid_seen='FTEST0001',
                             attribution_status='identified')]
            for cutoff in ('2026-09-08T14:58:01Z', None):
                r = reader.reconstruct(1, 'FTEST0001', sessions, until=cutoff)
                rows = merge_inventory(r, 'de')
                self.assertEqual(len({row.key.name for row in rows if row.observed}), 131)
                self.assertTrue(all(row.definition for row in rows))
                self.assertEqual(sum(row.stock.total for row in rows), 3139)
                self.assertEqual(r.total_count, 3139)
                self.assertEqual(len(rows), 223)
                mission = next(row for row in rows if row.key.mission_id == 1064707191)
                self.assertEqual((mission.key.name, mission.stock.total, mission.stock.mission_status),
                                 ('vehicleschematic', 1, 'completed'))

    def test_two_commanders_shared_reader_no_mixing(self):
        reader = OdysseyInventoryReader()
        with tempfile.TemporaryDirectory() as directory:
            sessions = []
            for cmd, records in [(1, [snapshot('ShipLocker', Items=[item('vehicleschematic', 1, MissionID=42)]),
                                     snapshot('Backpack'), event('BuyMicroResources', 1,
                                     Name='graphene', Category='Component', Count=3)]),
                                 (2, [snapshot('ShipLocker', Data=[item('manufacturinginstructions', 8)]),
                                     snapshot('Backpack', Consumables=[item('healthpack', 2)]),
                                     event('BackpackChange', 1, Removed=[item('healthpack', 1, Type='Consumable')])])]:
                path = Path(directory) / f'Journal{cmd}.log'
                path.write_text(''.join(json.dumps(e)+'\n' for e in
                                [event('Commander', FID=f'F{cmd}')] + records))
                sessions.append(dict(journal_file=str(path), commander_id=cmd, fid_seen=f'F{cmd}',
                                     attribution_status='identified'))
            a = merge_inventory(reader.reconstruct(1, 'F1', sessions), 'de')
            b = merge_inventory(reader.reconstruct(2, 'F2', sessions), 'en')
            self.assertEqual(sum(x.stock.total for x in a), 4)
            self.assertEqual(sum(x.stock.total for x in b), 9)
            self.assertFalse(any(x.key.mission_id for x in b))
            self.assertEqual(a, merge_inventory(reader.reconstruct(1, 'F1', sessions), 'de'))
            self.assertTrue(all(x.commander_id == 1 and x.fid == 'F1' for x in a))
            self.assertTrue(all(x.commander_id == 2 and x.fid == 'F2' for x in b))
