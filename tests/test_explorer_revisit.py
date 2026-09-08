"""Explorer revisit regression: live > saved own scans > external metadata."""
import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtWidgets import QApplication

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.online_services import _normalize_edsm_body
from cmdrhelper.state import AppState
from cmdrhelper.ui.system_view import SystemMapWidget


class ExplorerRevisitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = CMDRDatabase(Path(self.tmp.name) / 'test.db')
        self.a = self.db.upsert_commander('F-A', 'Alpha')
        self.b = self.db.upsert_commander('F-B', 'Bravo')
        self.state = SimpleNamespace(database=self.db, commander_id=self.a,
            viewed_commander_id=self.b, system_address=7432700939515, edsm_enabled=True)
        self.saved = [
            dict(body_id=1, name='Example A', body_type='Star', star_type='A', stellar_mass=1.7),
            dict(body_id=2, name='Example B', body_type='Star', star_type='K', stellar_mass=0.68),
            *[dict(body_id=i, name=f'Example B {i-7}', body_type='Planet',
                   planet_class='High metal content body', mass_em=0.5) for i in range(8, 12)],
        ]
        for body in self.saved:
            body.update(scan_value=12345, mapped_value=45678, current_value=12345,
                        was_discovered=False, was_mapped=False, self_mapped=True)
        self.store(self.a, self.saved)

    def store(self, commander, bodies, address=7432700939515):
        self.db.store_snapshot(dict(system_address=address, system='Example',
            last_timestamp='2026-09-04T11:52:35Z', system_bodies=bodies), commander)

    def load(self, current=()):
        self.state.system_bodies = AppState._own_explorer_bodies(self.state, list(current))
        return self.state.system_bodies

    def test_revisit_restores_own_scans_values_and_assets(self):
        bodies = self.load()
        self.assertEqual([b['body_id'] for b in bodies], [1, 2, 8, 9, 10, 11])
        widget = SystemMapWidget()
        self.addCleanup(widget.close)
        for body, asset in zip(bodies, ['star_a.png', 'star_k.png'] + ['planet_hmc.png'] * 4):
            self.assertTrue(body['journal_scanned'])
            self.assertEqual(body['source'], 'Journal')
            self.assertEqual(body['scan_value'], 12345)
            self.assertEqual(body['mapped_value'], 45678)
            self.assertEqual(widget._body_image_name(body), asset)
            self.assertIsNotNone(widget._body_pixmap(body))

    def test_live_values_lead_and_missing_fields_are_filled_without_mutating_input(self):
        live = dict(body_id=8, planet_class='Water world', scan_value=999,
                    mapped_value=0, self_mapped=False, mass_em=None, materials={})
        before = copy.deepcopy(live)
        body = next(b for b in self.load([live]) if b['body_id'] == 8)
        for key in ('planet_class', 'scan_value', 'mapped_value', 'materials'):
            self.assertEqual(body[key], live[key])
        self.assertTrue(body['self_mapped'])  # A new Scan cannot undo past own mapping.
        self.assertEqual(body['mass_em'], 0.5)
        self.assertEqual(live, before)

    def test_edsm_only_fills_gaps_and_never_replaces_own_origin(self):
        self.load()
        external = dict(body_id=1, name='Example A', star_type='A (Blue-White) Star',
                        scan_value=500, was_discovered=True, surface_temperature=8000,
                        journal_scanned=False, source='EDSM')
        AppState._merge_edsm_into_system(self.state, {'bodies': [external]})
        body = self.state.system_bodies[0]
        self.assertEqual(body['source'], 'Journal')
        self.assertTrue(body['journal_scanned'])
        self.assertTrue(body['edsm_known'])
        self.assertEqual(body['scan_value'], 12345)
        self.assertFalse(body['was_discovered'])
        self.assertEqual(body['surface_temperature'], 8000)
        self.assertEqual(body['star_type'], 'A')

    def test_external_classes_are_canonical_for_api_and_existing_cache(self):
        cases = [('Star', 'A (Blue-White) Star', 'A', 'star_a.png'),
                 ('Star', 'K (Yellow-Orange) Star', 'K', 'star_k.png'),
                 ('Planet', 'High metal content world', 'High metal content body', 'planet_hmc.png')]
        self.state.system_bodies = []
        for i, (kind, external, canonical, asset) in enumerate(cases):
            field = 'star_type' if kind == 'Star' else 'planet_class'
            api = _normalize_edsm_body(dict(bodyId=i, type=kind, subType=external), 'Example')
            self.assertEqual(api[field], canonical)
            cache = {**api, field: external}
            AppState._merge_edsm_into_system(self.state, {'bodies': [cache]})
            body = self.state.system_bodies[-1]
            self.assertEqual(body[field], canonical)
            self.assertEqual(SystemMapWidget._body_image_name(body), asset)
            self.assertFalse(body['journal_scanned'])
            self.assertEqual(body['source'], 'EDSM')
        AppState._merge_edsm_into_system(self.state, {'bodies': []})
        self.assertTrue(all(b['source'] == 'EDSM' for b in self.state.system_bodies))
        self.assertGreater(self.state.system_bodies[-1]['scan_value'], 500)

    def test_active_commander_and_system_are_strictly_isolated(self):
        self.store(self.b, [dict(body_id=90, name='Bravo only', scan_value=777)])
        self.store(self.a, [dict(body_id=91, name='Other system')], address=42)
        self.assertNotIn(90, [b['body_id'] for b in self.load()])
        self.assertNotIn(91, [b['body_id'] for b in self.load()])
        self.state.commander_id = self.b
        self.state.viewed_commander_id = self.a
        self.assertEqual([b['body_id'] for b in self.load()], [90])
        self.state.commander_id = None
        self.assertEqual(self.load(), [])

    def test_non_scan_personal_records_are_not_claimed_as_scans(self):
        with self.db._connect() as con:
            con.execute('UPDATE commander_bodies SET scanned=0 WHERE body_id=1')
        self.assertNotIn(1, [b['body_id'] for b in self.load()])


if __name__ == '__main__':
    unittest.main()
