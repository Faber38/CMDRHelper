"""Fixed EDDiscovery reference results, without deriving expectations from our formula."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from cmdrhelper.valuation import calculate_body_values, apply_values, system_totals
from cmdrhelper.state import AppState
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.journal_reader import read_latest_state


def planet(**extra):
    return dict(dict(name='Reference A 3', body_id=7, planet_class='High metal content body',
                     mass_em=0.785271, terraformable=True, was_discovered=False,
                     was_mapped=False, self_mapped=True, efficient_mapping=True,
                     game_version='4.4.1.1', odyssey=False), **extra)


class ValuationReferenceTests(unittest.TestCase):
    def test_real_bases_and_fd_fss(self):
        for mass, terra, base, fss in ((.538189, False, 14480, 37649),
                                     (.441844, False, 14293, 37164),
                                     (.785271, True, 169822, 441538),
                                     (.191923, True, 155213, 403555)):
            with self.subTest(mass=mass):
                values = calculate_body_values(planet(mass_em=mass, terraformable=terra,
                                                      self_mapped=False))
                self.assertEqual(values['base_value'], base)
                self.assertEqual(values['scan_value'], fss)
                self.assertEqual(values['current_value'], fss)

    def test_all_live_mapping_scenarios(self):
        for mass, pairs in ((.785271, [(735897, 919872), (1787259, 2234074), (2123583, 2654479)]),
                            (.191923, [(672591, 840739), (1633509, 2041887), (1940901, 2426126)])):
            for (discovered, mapped), pair in zip(((True, True), (True, False), (False, False)), pairs):
                for efficient, expected in enumerate(pair):
                    with self.subTest(mass=mass, flags=(discovered,mapped), efficiency=efficient):
                        values = calculate_body_values(planet(mass_em=mass, was_discovered=discovered,
                            was_mapped=mapped, efficient_mapping=bool(efficient)))
                        self.assertEqual(values['current_value'], expected)
                        self.assertEqual(values['possible_value_without_efficiency'], pair[0])

    def test_all_legacy_mapping_scenarios(self):
        for mass, pairs in ((.785271, [(566075, 707593), (1374815, 1718519), (1633526, 2041907)]),
                            (.191923, [(517378, 646722), (1256546, 1570682), (1493001, 1866251)])):
            for (discovered, mapped), pair in zip(((True, True), (True, False), (False, False)), pairs):
                for efficient, expected in enumerate(pair):
                    with self.subTest(mass=mass, flags=(discovered,mapped), efficiency=efficient):
                        values = calculate_body_values(planet(mass_em=mass, game_version='3.8.0',
                            was_discovered=discovered, was_mapped=mapped, efficient_mapping=bool(efficient)))
                        self.assertEqual(values['current_value'], expected)

    def test_legacy_and_odyssey_context(self):
        for version, odyssey, expected in [('3.8.0', False, 2041907),
                                            ('4.0.0', False, 2654479),
                                            ('', True, 2654479), ('', False, 2041907)]:
            with self.subTest(version=version, odyssey=odyssey):
                self.assertEqual(calculate_body_values(planet(game_version=version,
                    odyssey=odyssey))['current_value'], expected)

    def test_minimum_live_bonus_and_order(self):
        body = planet(planet_class='Icy body', mass_em=.0001, terraformable=False,
                      was_discovered=True, was_mapped=True, efficient_mapping=False)
        self.assertEqual(calculate_body_values(body)['current_value'], 2221)
        self.assertEqual(calculate_body_values(dict(body, efficient_mapping=True))['current_value'], 2777)
        self.assertEqual(calculate_body_values(dict(body, game_version='3.8'))['current_value'], 1666)
        # FD must multiply the 555 minimum too.
        body.update(was_discovered=False, was_mapped=False)
        self.assertEqual(calculate_body_values(body)['current_value'], 6252)

    def test_unknown_and_contradictory_flags(self):
        for discovered, mapped, own, expected in ((None,None,False,169822),
                (None,None,True,919872), (None,False,True,2234074),
                (False,None,True,441538), (False,True,False,169822),
                (False,True,True,919872)):
            with self.subTest(flags=(discovered,mapped,own)):
                body = planet(was_discovered=discovered, was_mapped=mapped, self_mapped=own)
                self.assertEqual(calculate_body_values(body)['current_value'],expected)
                self.assertIs(body['was_discovered'], discovered)
                self.assertIs(body['was_mapped'], mapped)

    def test_sales_factor_does_not_change_any_values(self):
        expected = calculate_body_values(planet())
        for factor in (.8866281302746647, .5, 2, float('nan')):
            self.assertEqual(calculate_body_values(planet(), factor), expected)
        callback = Mock(side_effect=AssertionError('must not query learned values'))
        system_totals([planet()], callback)
        callback.assert_not_called()

    def test_saved_positive_caches_recover_and_reuse_across_reload(self):
        original = planet(scan_value=391481, mapped_value=1810413, current_value=1810413)
        state = SimpleNamespace(system_bodies=[dict(original)], database=Mock())
        AppState._refresh_explorer_values(state,set())
        self.assertEqual(state.system_bodies[0]['current_value'],2654479)
        self.assertEqual(state.system_bodies[0]['possible_value_without_efficiency'],2123583)
        state.system_bodies = [dict(original)]  # fresh objects from SQLite
        with patch('cmdrhelper.state.apply_values', wraps=apply_values) as apply:
            AppState._refresh_explorer_values(state,set())
            apply.assert_not_called()
        self.assertEqual(state.system_bodies[0]['possible_value'],2654479)
        state.database.learned_cartography_factor.assert_not_called()
        state.system_bodies[0]['efficient_mapping'] = False
        AppState._refresh_explorer_values(state,set())
        self.assertEqual(state.system_bodies[0]['current_value'],2123583)

    def test_journal_import_reload_and_live_legacy_isolation(self):
        for version, expected in [('4.4.1.1',2654479),('3.8.0',2041907)]:
            with self.subTest(version=version), tempfile.TemporaryDirectory() as tmp:
                folder = Path(tmp)
                events = [dict(event='Fileheader',gameversion=version),
                    dict(event='Commander',FID='F1',Name='Test'),
                    dict(event='LoadGame',FID='F1',Commander='Test',Odyssey=False),
                    dict(event='Location',StarSystem='Reference',SystemAddress=42),
                    dict(event='SAAScanComplete',SystemAddress=42,BodyID=7,BodyName='Reference A 3',
                         ProbesUsed=6,EfficiencyTarget=6),
                    dict(event='Scan',SystemAddress=42,StarSystem='Reference',BodyID=7,
                         BodyName='Reference A 3',PlanetClass='High metal content body',
                         MassEM=.785271,TerraformState='Terraformable',WasDiscovered=False,WasMapped=False)]
                for i,event in enumerate(events):
                    event['timestamp'] = f'2026-09-11T07:00:0{i}Z'
                (folder/'Journal.2026-09-11T070000.01.log').write_text(
                    ''.join(json.dumps(e)+'\n' for e in events))
                data = read_latest_state(folder)
                self.assertEqual(data['system_bodies'][0]['current_value'],expected)
                db = CMDRDatabase(folder/'test.db')
                cid = db.upsert_commander('F1','Test')
                db.import_journal_archive(folder)
                # Active journal index may lag behind already persisted DSS events.
                with db._connect() as con:
                    con.execute("UPDATE journal_sessions SET last_event_at='2026-09-11T07:00:03Z'")
                saved = db.chronicle_system_details(42,cid,scanned_only=True)['bodies'][0]
                self.assertEqual(saved['game_version'],version)
                state = SimpleNamespace(system_bodies=[saved])
                AppState._refresh_explorer_values(state,set())
                self.assertEqual(saved['current_value'],expected)
                self.assertFalse(saved['was_discovered'])
                self.assertFalse(saved['was_mapped'])
                self.assertTrue(saved['self_mapped'])
