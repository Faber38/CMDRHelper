"""EDSM planet names resolve to journal classes and existing Explorer assets."""
import copy
import os
import unittest
from types import SimpleNamespace

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication

from cmdrhelper.body_classes import canonical_body_classes
from cmdrhelper.online_services import _normalize_edsm_body
from cmdrhelper.state import AppState
from cmdrhelper.ui.system_view import SystemMapWidget
from cmdrhelper.valuation import BODY_VALUES


# EDSM's planet catalogue: https://www.edsm.net/en/faq/bodies/planets
CASES = [
    ('Gas giant with water-based life', 'Gas giant with water based life', 'gas_giant_water_life.png'),
    ('Gas giant with ammonia-based life', 'Gas giant with ammonia based life', 'gas_giant_ammonia_life.png'),
    *[(f'Class {kind} gas giant', f'Sudarsky class {kind} gas giant', f'gas_giant_class_{i}.png')
      for i, kind in enumerate(('I', 'II', 'III', 'IV', 'V'), 1)],
    ('Water world', 'Water world', 'planet_water_world.png'),
    ('Earth-like world', 'Earthlike body', 'planet_earthlike.png'),
    ('Ammonia world', 'Ammonia world', 'planet_ammonia_world.png'),
    ('High metal content world', 'High metal content body', 'planet_hmc.png'),
    ('Metal-rich body', 'Metal rich body', 'planet_metal_rich.png'),
    ('Rocky body', 'Rocky body', 'planet_rocky.png'),
    ('Icy body', 'Icy body', 'planet_icy.png'),
    ('Rocky Ice world', 'Rocky ice body', 'planet_rocky_ice.png'),
    ('Helium-rich gas giant', 'Helium rich gas giant', 'gas_giant_helium_rich.png'),
    ('Helium gas giant', 'Helium gas giant', 'gas_giant_helium.png'),
    ('Water giant', 'Water giant', 'water_giant.png'),
    # Additional names already supported locally.
    ('Rocky world', 'Rocky body', 'planet_rocky.png'),
    ('Rocky ice body', 'Rocky ice body', 'planet_rocky_ice.png'),
    ('Water giant with life', 'Water giant with life', 'water_giant_life.png'),
]


class EdsmPlanetClassesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_api_and_old_cache_select_existing_assets(self):
        widget = SystemMapWidget()
        self.addCleanup(widget.close)
        for external, canonical, asset in CASES:
            for light in (False, True):
                with self.subTest(external=external, light=light):
                    widget.set_light_mode(light)
                    raw = dict(bodyId=3, type='Planet', subType=external)
                    before = copy.deepcopy(raw)
                    api = _normalize_edsm_body(raw, 'Example')
                    self.assertEqual(raw, before)
                    self.assertEqual(api['planet_class'], canonical)
                    for body in (api, {**api, 'planet_class': external}):
                        before_body = copy.deepcopy(body)
                        state = SimpleNamespace(edsm_enabled=True, system_bodies=[])
                        AppState._merge_edsm_into_system(state, {'bodies': [body]})
                        merged = state.system_bodies[0]
                        self.assertEqual(body, before_body)
                        self.assertEqual(merged['planet_class'], canonical)
                        self.assertEqual(widget._body_image_name(merged), asset)
                        pixmap = widget._body_pixmap(merged)
                        self.assertIsNotNone(pixmap)
                        self.assertFalse(pixmap.isNull())

    def test_all_journal_classes_remain_unchanged(self):
        self.assertEqual({c for _, c, _ in CASES}, set(BODY_VALUES))
        for _, canonical, asset in CASES:
            with self.subTest(canonical=canonical):
                body = dict(body_type='Planet', star_type='', planet_class=canonical)
                self.assertEqual(canonical_body_classes(body), body)
                self.assertEqual(SystemMapWidget._body_image_name(body), asset)

    def test_unknown_classes_keep_fallback(self):
        widget = SystemMapWidget()
        self.addCleanup(widget.close)
        for unknown in ('Unknown future planet', 'Class VI gas giant', ''):
            with self.subTest(unknown=unknown):
                api = _normalize_edsm_body(dict(type='Planet', subType=unknown), 'Example')
                state = SimpleNamespace(edsm_enabled=True, system_bodies=[])
                AppState._merge_edsm_into_system(state, {'bodies': [api]})
                body = state.system_bodies[0]
                self.assertEqual(body['planet_class'], unknown)
                self.assertIsNone(widget._body_image_name(body))
                self.assertIsNone(widget._body_pixmap(body))
                self.assertEqual(widget._body_color(body), widget._body_color(
                    dict(body_type='Planet', planet_class=unknown)))

    def test_mixed_system_preserves_journal_classes_and_observations(self):
        own = [dict(body_id=i, name=f'Example {i}', body_type='Planet',
                    planet_class=canonical, source='Journal', journal_scanned=True,
                    was_discovered=False, current_value=123)
               for i, (_, canonical, _) in enumerate(CASES, 1)]
        # Existing journal values also retain the legacy UI-supported spelling.
        own.append(dict(body_id=100, name='Example 100', body_type='Planet',
                        planet_class='Class I gas giant', source='Journal', journal_scanned=True))
        before = copy.deepcopy(own)
        external = [_normalize_edsm_body(
            dict(bodyId=i, name=f'Example {i}', type='Planet', subType=external), 'Example')
            for i, (external, _, _) in enumerate(CASES, 1)]
        external.extend([
            _normalize_edsm_body(dict(bodyId=100, type='Planet', subType='Class I gas giant'), 'Example'),
            # Simulate old cached EDSM data for the two originally missing images.
            dict(body_id=101, body_type='Planet', planet_class=CASES[0][0]),
            dict(body_id=102, body_type='Planet', planet_class=CASES[1][0]),
        ])
        state = SimpleNamespace(edsm_enabled=True, system_bodies=own)
        AppState._merge_edsm_into_system(state, {'bodies': external})
        self.assertEqual(state.edsm_added_count, 2)
        for original, merged in zip(before, state.system_bodies):
            self.assertEqual({key: merged[key] for key in original}, original)
        for body, (_, canonical, asset) in zip(state.system_bodies[-2:], CASES[:2]):
            self.assertEqual(body['source'], 'EDSM')
            self.assertFalse(body['journal_scanned'])
            self.assertTrue(body['edsm_known'])
            self.assertEqual(body['planet_class'], canonical)
            self.assertEqual(SystemMapWidget._body_image_name(body), asset)
