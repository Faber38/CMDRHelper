"""Transport fixtures copied from the locally observed 2026-10-06 journal.

Only the initial personal snapshot and Cargo inventories are supplied by the
test: the real journal records Cargo counts separately from Cargo.json.
"""
import json
from pathlib import Path
import tempfile
import unittest

from cmdrhelper.cargo import normalize_inventory
from cmdrhelper.journal_reader import read_latest_state, classify_journal_file
from cmdrhelper.powerplay import PowerplayState, onboard_articles, decode_powers_cache
from tests.test_powerplay import event, cache_bytes
from tests import test_powerplay as base_tests
from tests import test_ship_cargo as helpers
from cmdrhelper.ship_cargo import current_ship_inventory


def real_events():
    return json.loads((Path(__file__).parent / 'fixtures/powerplay_transport.json').read_text())


def inventory(name='kainemisinformation', count=10):
    return dict(inventory=normalize_inventory([dict(Name=name, Count=count)]))


def powers(name='Nakato Kaine'):
    return decode_powers_cache(cache_bytes([dict(id=1, name=name, ethos={}, commodities=dict(
        acquisition='KaineLobbyingMaterial', reinforcement='KaineAidSupplies',
        undermining='KaineMisinformation'))]))


class TransportTests(unittest.TestCase):
    def test_real_sequence_and_context(self):
        data = PowerplayState()
        data.apply(event('Powerplay', Power='Nakato Kaine', Merits=9183))
        for row in real_events():
            data.apply(row)
        self.assertEqual([a.event for a in data.recent], [
            'PowerplayCollect', 'PowerplayDeliver', 'PowerplayMerits', 'PowerplayMerits'])
        collect, deliver, first, second = data.recent
        self.assertEqual((collect.count, collect.commodity, collect.name),
                         (10, 'kainemisinformation', 'Kaine-Fehlinformationen'))
        self.assertEqual((collect.system, collect.station), ('', ''))
        self.assertEqual((deliver.system, deliver.station), ('HIP 70049', 'Mille Enterprise'))
        self.assertEqual((first.gained, first.total, second.gained, second.total), (3600, 12783, 48, 12831))
        self.assertEqual(data.merits, 12831)
        self.assertNotIn('assignment', repr(data).lower())
        self.assertNotIn('completed', repr(data).lower())

    def test_generic_cache_mapping_and_localized_name(self):
        data = PowerplayState(power='Edmund Mahon')
        cache = decode_powers_cache(cache_bytes([dict(id=5, name='Edmund Mahon', ethos={}, commodities=dict(
            acquisition='AllianceTradeAgreements', reinforcement='AllianceLegaslativeContracts',
            undermining='AllianceLegaslativeRecords'))]))
        for category, name in cache['Edmund Mahon']['commodities'].items():
            rows = onboard_articles(data, inventory(name.lower()), cache)
            self.assertEqual((rows[0]['category'], rows[0]['power']), (category, 'Edmund Mahon'))
        data.apply(real_events()[0])
        self.assertEqual(onboard_articles(data, inventory(), cache)[0]['name'], 'Kaine-Fehlinformationen')
        # A different selected power must not inherit Nakato's usage mapping.
        data.power = 'Absent'
        self.assertIsNone(onboard_articles(data, inventory(), cache)[0]['category'])

    def test_unknown_articles_missing_cache_and_ambiguous_mapping(self):
        data = PowerplayState(power='Nakato Kaine')
        self.assertEqual(onboard_articles(data, inventory('gold'), powers()), [])
        data.apply(event('PowerplayCollect', Power='Nakato Kaine', Type='futureitem', Count=2))
        row = onboard_articles(data, inventory('futureitem', 2), None)[0]
        self.assertEqual(row['name'], 'futureitem')
        self.assertIsNone(row['category'])
        self.assertEqual(onboard_articles(data, None, powers()), [])
        self.assertEqual(onboard_articles(data, inventory(count=0), powers()), [])
        cache = powers()
        cache['Nakato Kaine']['commodities']['acquisition'] = 'KaineMisinformation'
        self.assertIsNone(onboard_articles(data, inventory(), cache)[0]['category'])

    def test_context_never_inherits_old_station_or_session(self):
        for transition in [event('Undocked'), event('SupercruiseEntry'),
                           event('FSDJump', StarSystem='Next'), event('LoadGame'),
                           event('Fileheader'), event('Location', StarSystem='Next')]:
            with self.subTest(transition=transition):
                data = PowerplayState()
                data.apply(event('Docked', StarSystem='Old', StationName='Old Station'))
                data.apply(transition)
                data.apply(real_events()[4])
                self.assertEqual(data.recent[-1].station, '')
                if transition['event'] in ('LoadGame', 'Fileheader'):
                    self.assertEqual(data.recent[-1].system, '')

    def test_collect_captures_context_without_later_mutation(self):
        data = PowerplayState()
        data.apply(event('Location', StarSystem='Origin', Docked=True, StationName='Contact Station'))
        data.apply(real_events()[0])
        data.apply(real_events()[2])
        self.assertEqual((data.recent[0].station, data.recent[0].system), ('Contact Station', 'Origin'))
        self.assertEqual(data.system['StarSystem'], 'HIP 70049')

    def test_missing_localization_and_malformed_transport(self):
        data = PowerplayState()
        data.apply(event('PowerplayCollect', Power='P', Type='item', Count=1))
        data.apply(event('PowerplayMerits', Power='P', MeritsGained=1, TotalMerits=1))
        self.assertEqual(data.recent[0].name, 'item')
        for count in [-1, True, '10', None]:
            data.apply(event('PowerplayDeliver', Power='P', Type='item', Count=count))
        self.assertEqual(len(data.recent), 2)

    def test_indexed_startup_and_repeated_live_reads(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            path = folder/'Journal.2026-10-06T151935.01.log'
            rows = [event('Commander', FID='test', Name='Test'),
                    event('Powerplay', Power='Nakato Kaine', Merits=9183)] + real_events()[:2]
            path.write_text(''.join(json.dumps(e)+'\n' for e in rows))
            sessions = [classify_journal_file(path)]
            self.assertEqual(read_latest_state(folder, indexed_sessions=sessions)['powerplay'].recent[0].event,
                             'PowerplayCollect')
            with path.open('a') as f:
                f.write(''.join(json.dumps(e)+'\n' for e in real_events()[2:]))
            first = read_latest_state(folder, indexed_sessions=sessions)['powerplay']
            second = read_latest_state(folder, indexed_sessions=sessions)['powerplay']
            self.assertEqual(first, second)
            self.assertEqual(first.merits, 12831)
            self.assertEqual(len(first.recent), 4)
            self.assertEqual(read_latest_state(folder)['powerplay'], first)

    def test_history_bounded_without_merging_same_second(self):
        data = PowerplayState()
        for i in range(30):
            data.apply(event('PowerplayMerits', Power='P', MeritsGained=i, TotalMerits=i))
        self.assertEqual(len(data.recent), 24)
        self.assertEqual(data.recent[0].gained, 6)


class TransportViewTests(unittest.TestCase):
    setUpClass = classmethod(base_tests.PowerplayViewTests.setUpClass.__func__)
    setUp = base_tests.PowerplayViewTests.setUp

    def test_confirmed_zero_total_removes_stale_article_and_unknown_use_is_visible(self):
        self.loader.return_value = None
        self.state.powerplay.apply(event('PowerplayCollect', Power='Test Power', Type='newitem', Count=2))
        self.state.ship_inventory = inventory('newitem', 2)
        self.state.cargoSnapshotChanged.emit(None)
        self.assertIn('newitem', self.view.cargo.text())
        self.assertIn('Verwendung: Unbekannt', self.view.cargo.text())
        self.state.ship_cargo_total = dict(count=0)
        self.state.cargoSnapshotChanged.emit(None)
        self.assertNotIn('newitem', self.view.cargo.text())

    def test_live_transport_sidecar_signal_and_neutral_credits(self):
        self.loader.return_value = powers()
        self.state.powerplay = PowerplayState(power='Nakato Kaine', merits=9183)
        self.state.powerplay.apply(real_events()[0])
        self.state.changed.emit()
        self.assertIn('10 × Kaine-Fehlinformationen', base_tests.table_text(self.view))
        self.assertEqual(self.view.recent.item(0, 1).text(), 'PP2-Aufnahme')
        self.assertIn('nicht bestätigt', self.view.cargo.text())
        self.state.ship_inventory = inventory()
        self.state.cargoSnapshotChanged.emit(self.state.ship_inventory)
        self.assertIn('Kaine-Fehlinformationen', self.view.cargo.text())
        self.assertIn('UNDERMINING', self.view.cargo.text())
        for row in real_events()[2:-1]:
            self.state.powerplay.apply(row)
            self.state.changed.emit()
        text = base_tests.table_text(self.view)
        self.assertIn('Mille Enterprise · HIP 70049', text)
        self.assertEqual(self.view.recent.item(0, 1).text(), 'PP2-Abgabe')
        self.assertEqual(self.view.recent.item(0, 3).text(), '+3.600 / +48')
        self.assertEqual(text.count('+3.600'), 1)
        self.assertEqual(self.view.personal['merits'].text(), '12.831')
        for forbidden in ('Assignment', 'abgeschlossen', 'Belohnung'):
            self.assertNotIn(forbidden, text)
        self.state.ship_inventory = inventory(count=0)
        self.state.cargoSnapshotChanged.emit(self.state.ship_inventory)
        self.assertNotIn('Kaine-Fehlinformationen', self.view.cargo.text())
        self.assertIn('Keine PP2-Artikel', self.view.cargo.text())


class TransportCargoIntegrationTests(unittest.TestCase):
    setUp = helpers.ShipCargoTests.setUp
    replay = helpers.ShipCargoTests.replay

    def test_real_count_only_cargo_requires_matching_sidecar_then_clears(self):
        fixture = real_events()
        rows = [helpers.loadout(), fixture[0], fixture[1]]
        sidecar = dict(fixture[1], Inventory=[dict(Name='kainemisinformation', Count=10,
                       Name_Localised='Kaine-Fehlinformationen', Stolen=0)])
        s, _ = self.replay(rows)
        self.assertIsNone(current_ship_inventory(s))
        (self.folder/'Cargo.json').write_text(json.dumps(sidecar))
        s, data = self.replay(rows)
        self.assertEqual(onboard_articles(data['powerplay'], current_ship_inventory(s), powers())[0]['count'], 10)
        s, _ = self.replay(rows + fixture[2:-1])
        self.assertIsNone(current_ship_inventory(s))
        (self.folder/'Cargo.json').write_text(json.dumps(dict(fixture[-1], Inventory=[])))
        s, data = self.replay(rows + fixture[2:])
        self.assertEqual(current_ship_inventory(s)['inventory'], [])
        self.assertEqual(onboard_articles(data['powerplay'], current_ship_inventory(s), powers()), [])
