import json
import random
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from cmdrhelper.body_parents import parent_metadata
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.online_services import _normalize_edsm_body
from cmdrhelper.journal_reader import read_latest_state
from cmdrhelper.state import AppState
from cmdrhelper.belt_projection import project_belts

ADDRESS = 5474145570075
NAME = 'Plio Aihm UC-V d2-159'
EVENTS = json.loads((Path(__file__).parent / 'fixtures/plio_parent_scans.json').read_text())
EXPECTED = {17: 15, 23: 20, 28: 25, 29: 25,
            **dict.fromkeys(range(34, 40), 31), **dict.fromkeys([*range(43, 50), 51], 41)}


class ParentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = CMDRDatabase(self.root / 'test.db')
        self.commander = self.db.upsert_commander('F-test', 'Test')

    def journal(self, events):
        path = self.root / 'Journal.2026-06-01T083000.01.log'
        prefix = [dict(event='Commander', FID='F-test', Name='Test', timestamp='2026-06-01T06:00:00Z'),
                  dict(event='Location', StarSystem=NAME, SystemAddress=ADDRESS, timestamp='2026-06-01T06:00:01Z')]
        path.write_text('\n'.join(json.dumps(e) for e in prefix + events) + '\n')
        return path

    def load(self):
        return self.db.chronicle_system_details(ADDRESS, self.commander)['bodies']

    def store(self, bodies):
        self.db.store_snapshot(dict(system_address=ADDRESS, system=NAME,
                                    system_bodies=bodies), self.commander)

    def test_normalization(self):
        for parents, direct, star in [([], None, None), ([{'Star': 0}], 0, 0),
                ([{'Planet': 20}, {'Null': 19}, {'Star': 0}], 20, 0),
                ([{'Star': 15}, {'Star': 0}], 15, 15),
                ([{'Ring': 5}, {'Star': 0}], 0, 0), ([{'Null': 1}], None, None)]:
            with self.subTest(parents=parents):
                edsm = _normalize_edsm_body(dict(bodyId=23, name='Example', parents=parents), 'Example')
                self.assertEqual(edsm['parent_id'], direct)
                self.assertEqual(edsm['parent_star_id'], star)
        self.assertEqual(parent_metadata(None, 'Journal'), {})
        self.assertEqual(parent_metadata([{'Planet': -1}], 'Journal'), {})

    def test_plio_journal_database_reload_and_priority(self):
        self.journal(EVENTS)
        data = read_latest_state(self.root)
        bodies = data['system_bodies']
        self.assertEqual(len(bodies), 37)
        self.assertEqual({e['BodyID'] for e in EVENTS if e['event']=='ScanBaryCentre'}, {1,19,30})
        self.db.store_snapshot(data, self.commander)
        loaded = self.load()
        by_id = {b['body_id']: b for b in loaded}
        for event in EVENTS:
            if event['event'] == 'Scan' and 'Parents' in event:
                expected = parent_metadata(event['Parents'], 'Journal')
                for key, value in expected.items():
                    self.assertEqual(by_id[event['BodyID']][key], value)
        for body_id, parent in EXPECTED.items():
            self.assertEqual(by_id[body_id]['parent_id'], parent)
        self.assertEqual(by_id[17]['parent_star_id'], 15)
        self.assertEqual(len(project_belts(loaded)), 29)
        incoming = _normalize_edsm_body(dict(bodyId=17, name=NAME+' 4 a', parents=[{'Star':0}]), NAME)
        state = SimpleNamespace(edsm_enabled=True, system_bodies=loaded)
        AppState._merge_edsm_into_system(state, dict(bodies=[incoming]))
        self.assertEqual(by_id[17]['parent_id'], 15)
        self.store([incoming])
        self.assertEqual(next(b for b in self.load() if b['body_id']==17)['parent_id'], 15)
        self.db = CMDRDatabase(self.root / 'test.db')
        self.assertEqual(next(b for b in self.load() if b['body_id']==17)['parent_star_id'], 15)

    def test_repair_order_independence_and_idempotence(self):
        bodies = [dict(body_id=e['BodyID'], name=e['BodyName'], parent_id=0, parent_star_id=0)
                  for e in EVENTS if e['event']=='Scan']
        self.store(bodies)
        shuffled = list(EVENTS)
        random.Random(42).shuffle(shuffled)
        path = self.journal(shuffled)
        changes = self.db.repair_system_parents(ADDRESS, [path])
        self.assertEqual({c['body_id'] for c in changes}, set(EXPECTED))
        self.assertEqual(self.db.repair_system_parents(ADDRESS, [path]), [])
        for b in self.load():
            if b['body_id'] in EXPECTED:
                self.assertEqual(b['parent_id'], EXPECTED[b['body_id']])

    def test_edsm_can_correct_unverified_but_legacy_cache_cannot(self):
        state = SimpleNamespace(edsm_enabled=True, system_bodies=[dict(body_id=17,parent_id=0)])
        incoming = _normalize_edsm_body(dict(bodyId=17,name=NAME+' 4 a',parents=[{'Star':15},{'Star':0}]), NAME)
        AppState._merge_edsm_into_system(state, dict(bodies=[incoming]))
        self.assertEqual(state.system_bodies[0]['parent_id'], 15)
        AppState._merge_edsm_into_system(state, dict(bodies=[dict(body_id=17,parent_id=0)]))
        self.assertEqual(state.system_bodies[0]['parent_id'], 15)
        self.store([incoming])
        self.store([dict(body_id=17,parent_id=0)])
        self.assertEqual(self.load()[0]['parent_id'], 15)

    def test_conflicting_or_other_system_repair_does_not_guess(self):
        self.store([dict(body_id=17,parent_id=15)])
        base=dict(event='Scan',SystemAddress=ADDRESS,BodyID=17,Parents=[{'Star':0}])
        other=dict(base,Parents=[{'Star':99}])
        path=self.journal([base,other,dict(base,SystemAddress=123)])
        self.assertEqual(self.db.repair_system_parents(ADDRESS,[path]), [])
        self.assertEqual(self.load()[0]['parent_id'],15)

    def test_simple_systems_restart_and_source_precedence(self):
        self.store([
            dict(body_id=0, name='Root', body_type='Star', **parent_metadata([], 'Journal')),
            dict(body_id=1, name='Planet', **parent_metadata([{'Star':0}], 'Journal')),
            dict(body_id=2, name='Moon', **parent_metadata([{'Planet':1},{'Star':0}], 'Journal')),
            dict(body_id=3, name='Binary', **parent_metadata([{'Null':4}], 'Journal')),
            dict(body_id=5, name='Unknown', parent_id=None),
        ])
        self.store([dict(body_id=2, **parent_metadata([{'Star':0}], 'EDSM'))])
        self.db = CMDRDatabase(self.root / 'test.db')
        self.assertEqual({b['body_id']:b['parent_id'] for b in self.load()},
                         {0:None,1:0,2:1,3:None,5:None})

    def test_shuffled_journal_retains_parents(self):
        events = list(EVENTS)
        random.Random(9).shuffle(events)
        self.journal(events)
        bodies = read_latest_state(self.root)['system_bodies']
        self.assertEqual(len(bodies),37)
        by_id = {b['body_id']:b for b in bodies}
        for body_id,parent in EXPECTED.items():
            self.assertEqual(by_id[body_id]['parent_id'],parent)

    def test_legacy_cache_new_body_has_unknown_parent(self):
        state = SimpleNamespace(edsm_enabled=True, system_bodies=[])
        AppState._merge_edsm_into_system(state, dict(bodies=[dict(body_id=17,parent_id=0)]))
        self.assertIsNone(state.system_bodies[0].get('parent_id'))

    def test_verified_no_stellar_parent_is_not_filled_from_old_value(self):
        self.store([dict(body_id=17,parent_id=0,parent_star_id=0)])
        state=SimpleNamespace(database=self.db,commander_id=self.commander,system_address=ADDRESS)
        current=dict(body_id=17,**parent_metadata([{'Null':19}], 'Journal'))
        merged=AppState._own_explorer_bodies(state,[current])[0]
        self.assertIsNone(merged['parent_id'])
        self.assertIsNone(merged['parent_star_id'])

    def test_repair_changes_only_ancestry(self):
        self.store([dict(body_id=17,name=NAME+' 4 a',parent_id=0,mass_em=2.5,
                         planet_class='Earthlike body',self_mapped=True)])
        with self.db._connect() as con:
            before = con.execute('SELECT * FROM bodies').fetchone()
            columns = [r[1] for r in con.execute('PRAGMA table_info(bodies)')]
            personal = con.execute('SELECT * FROM commander_bodies').fetchall()
        self.db.repair_system_parents(ADDRESS,[self.journal(EVENTS)])
        with self.db._connect() as con:
            after = con.execute('SELECT * FROM bodies').fetchone()
            self.assertEqual(personal,con.execute('SELECT * FROM commander_bodies').fetchall())
        self.assertEqual([v for k,v in zip(columns,before) if k not in ('parent_id','parent_star_id')],
                         [v for k,v in zip(columns,after) if k not in ('parent_id','parent_star_id')])
