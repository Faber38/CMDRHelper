"""EDSM star classes use journal assets, including bodies from older caches."""
import copy
import os
import unittest
from types import SimpleNamespace

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication

from cmdrhelper.online_services import _normalize_edsm_body
from cmdrhelper.state import AppState
from cmdrhelper.ui.system_view import SystemMapWidget


class EdsmStarClassesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_api_and_old_cache_select_journal_assets(self):
        cases = [
            ('T (Brown dwarf) Star', 'T', 'star_t.png'),
            ('L (Brown dwarf) Star', 'L', 'star_l.png'),
            ('Y (Brown dwarf) Star', 'Y', 'star_y.png'),
            ('T Tauri Star', 'TTS', 'star_t_tauri.png'),
            ('Herbig Ae/Be Star', 'AeBe', 'star_herbig_aebe.png'),
            ('M (Red dwarf) Star', 'M', 'star_m.png'),
            ('K (Yellow-Orange) Star', 'K', 'star_k.png'),
            ('A (Blue-White) Star', 'A', 'star_a.png'),
            ('O (Blue-White) Star', 'O', 'star_o.png'),
            ('B (Blue-White) Star', 'B', 'star_b.png'),
            ('F (White) Star', 'F', 'star_f.png'),
            ('G (White-Yellow) Star', 'G', 'star_g.png'),
            ('K (Yellow-Orange giant) Star', 'K_OrangeGiant', 'star_k_orange_giant.png'),
            ('M (Red giant) Star', 'M_RedGiant', 'star_m_red_giant.png'),
            ('M (Red super giant) Star', 'M_RedSuperGiant', 'star_m_red_super_giant.png'),
            ('B (Blue-White super giant) Star', 'B_BlueWhiteSuperGiant', 'star_b_blue_white_super_giant.png'),
            ('A (Blue-White super giant) Star', 'A_BlueWhiteSuperGiant', 'star_a_blue_white_super_giant.png'),
            ('F (White super giant) Star', 'F_WhiteSuperGiant', 'star_f_white_super_giant.png'),
            ('G (White-Yellow super giant) Star', 'G_WhiteSuperGiant', 'star_g_white_super_giant.png'),
            ('Neutron Star', 'N', 'star_neutron.png'),
            ('Black Hole', 'H', 'black_hole.png'),
            ('Supermassive Black Hole', 'SupermassiveBlackHole', 'black_hole_supermassive.png'),
            ('Wolf-Rayet Star', 'W', 'star_w_wolf_rayet.png'),
            ('Wolf-Rayet N Star', 'WN', 'star_wn_wolf_rayet.png'),
            ('Wolf-Rayet NC Star', 'WNC', 'star_wnc_wolf_rayet.png'),
            ('Wolf-Rayet C Star', 'WC', 'star_wc_wolf_rayet.png'),
            ('Wolf-Rayet O Star', 'WO', 'star_wo_wolf_rayet.png'),
            ('MS-type Star', 'MS', 'star_ms.png'),
            ('S-type Star', 'S', 'star_s.png'),
            *[(f'{kind} Star', kind, f'star_{kind.lower()}_carbon.png')
              for kind in ('C', 'CS', 'CN', 'CJ', 'CHd')],
            *[(f'White Dwarf ({kind}) Star', kind, 'star_white_dwarf.png')
              for kind in ('D', 'DA', 'DAB', 'DAO', 'DAZ', 'DAV', 'DB', 'DBZ',
                           'DBV', 'DO', 'DOV', 'DQ', 'DC', 'DCV', 'DX')],
            ('Unknown future Star', 'Unknown future Star', None),
        ]
        widget = SystemMapWidget()
        self.addCleanup(widget.close)
        for external, canonical, asset in cases:
            for light in (False, True):
                with self.subTest(external=external, light=light):
                    widget.set_light_mode(light)
                    api = _normalize_edsm_body(
                        dict(bodyId=3, type='Star', subType=external), 'Example')
                    self.assertEqual(api['body_type'], 'Star')
                    self.assertEqual(api['star_type'], canonical)
                    for body in (api, {**api, 'star_type': external}):
                        state = SimpleNamespace(edsm_enabled=True, system_bodies=[])
                        AppState._merge_edsm_into_system(state, {'bodies': [body]})
                        merged = state.system_bodies[0]
                        self.assertEqual(merged['star_type'], canonical)
                        self.assertEqual(widget._body_image_name(merged), asset)
                        self.assertEqual(widget._body_image_name(
                            dict(body_type='Star', star_type=canonical)), asset)
                        if asset:
                            self.assertIsNotNone(widget._body_pixmap(merged))
                        else:
                            self.assertIsNone(widget._body_pixmap(merged))
                            self.assertEqual(widget._body_color(merged).name(), '#f6c86a')

    def test_mixed_system_preserves_journal_and_adds_edsm_star(self):
        own = [dict(body_id=i, name=f'Example {name}', body_type='Star',
                    star_type='M', source='Journal', journal_scanned=True,
                    was_discovered=False, current_value=123)
               for i, name in enumerate(('A', 'B'), 1)]
        before = copy.deepcopy(own)
        external = [_normalize_edsm_body(
            dict(bodyId=i, name=f'Example {name}', type='Star', subType=kind), 'Example')
            for i, name, kind in ((1, 'A', 'M (Red dwarf) Star'),
                                  (2, 'B', 'M (Red dwarf) Star'),
                                  (3, 'C', 'T (Brown dwarf) Star'))]
        state = SimpleNamespace(edsm_enabled=True, system_bodies=own)
        AppState._merge_edsm_into_system(state, {'bodies': external, 'body_count': 3})
        self.assertEqual(state.edsm_body_count, 3)
        self.assertEqual(state.edsm_added_count, 1)
        self.assertEqual(sum(b['journal_scanned'] for b in state.system_bodies), 2)
        for original, merged in zip(before, state.system_bodies):
            self.assertEqual({key: merged[key] for key in original}, original)
        added = state.system_bodies[2]
        self.assertEqual(added['source'], 'EDSM')
        self.assertFalse(added['journal_scanned'])
        self.assertTrue(added['edsm_known'])
        self.assertEqual([SystemMapWidget._body_image_name(b) for b in state.system_bodies],
                         ['star_m.png', 'star_m.png', 'star_t.png'])
