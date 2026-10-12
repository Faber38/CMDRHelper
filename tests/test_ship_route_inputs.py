"""Real 2026-10-11 Panther Loadout; isolated Status files and mocked transport."""
import copy
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.parse import parse_qs

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication

from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.journal_reader import _loadout_from_event
from cmdrhelper.route_planner.fsd_specs import derive_ship_route_technical_data, lookup_fsd_spec
from cmdrhelper.route_planner.models import ShipLoadoutData
from cmdrhelper.route_planner.route_planner_view import RoutePlannerView
from cmdrhelper.route_planner.ship_inputs import status_reserve_fuel
from cmdrhelper.route_planner.spansh_galaxy_client import SpanshGalaxyClient, SpanshError
from cmdrhelper.ship_cargo import ShipCargoTracker, current_ship_cargo
from cmdrhelper.state import AppState
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET

FIXTURE = Path(__file__).parent / 'fixtures/panther_7a_sco_loadout.json'
ITEM = 'int_hyperdrive_overcharge_size7_class5'
NOW = datetime(2026, 10, 11, 14, 57, 55, tzinfo=timezone.utc)
EXPECTED = dict(tank_size=128., cargo=0., base_mass=1857.209976,
                internal_tank_size=1.11, reserve_size=1.11, optimal_mass=4650.,
                max_fuel_per_jump=13.1, fuel_power=2.75,
                fuel_multiplier=.013, range_boost=10.5)


def event(kind, timestamp='2026-10-11T14:53:45Z', **fields):
    return dict(event=kind, timestamp=timestamp, **fields)


def status(**fields):
    return dict(event('Status', '2026-10-11T14:57:54Z',
                      Fuel=dict(FuelMain=128., FuelReservoir=1.11),
                      Cargo=0., Flags=151060493, Flags2=0), **fields)


class ShipRouteInputsTests(unittest.TestCase):
    def setUp(self):
        self.raw = json.loads(FIXTURE.read_text())
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        self.path = self.folder / 'Journal.test-panther.log'
        self.path.write_text(json.dumps(self.raw) + '\n')
        self.tracker = ShipCargoTracker()
        for e in (event('LoadGame', '2026-10-11T11:18:26Z', Ship='UtilitySuit_Class5'),
                  event('ShipyardSwap', ShipID=44, ShipType='panthermkii'), self.raw):
            self.tracker.apply(e, 'F_TEST_PANTHER', self.path)
        self.state = SimpleNamespace(
            ship_loadout=_loadout_from_event(self.raw, ShipLoadoutData()),
            ship_cargo_context=self.tracker.context, ship_cargo_total=None,
            commander_id=1, commander_fid='F_TEST_PANTHER', active_srv_type='',
            _cargo_status=status(), cargo_snapshot=None, journal_folder=self.folder,
            _journal_index_sessions=[dict(attribution_status='identified', commander_id=1,
                fid_seen='F_TEST_PANTHER', journal_file=str(self.path),
                last_complete_line_offset=self.path.stat().st_size,
                last_read_offset=self.path.stat().st_size)],
            cargoSnapshotChanged=Mock(), shipRouteInputsChanged=Mock(),
            system='Col 285 Sector HS-I c10-6', system_address=1733254320866,
        )
        self.clock = patch('cmdrhelper.ship_cargo.utc_now', return_value=NOW)
        self.clock.start()
        self.addCleanup(self.clock.stop)
        # Any unexpected real HTTP call in these tests is an error.
        network = patch('cmdrhelper.route_planner.spansh_galaxy_client.urlopen',
                        side_effect=AssertionError('Unexpected network call'))
        network.start()
        self.addCleanup(network.stop)

    def poll(self, data=None):
        (self.folder / 'Status.json').write_text(json.dumps(status() if data is None else data))
        AppState._poll_ship_cargo(self.state)

    def view(self):
        self.app = QApplication.instance() or QApplication([])
        v = RoutePlannerView(self.state)
        self.addCleanup(v.close)
        v.ship_destination_system.setText('Ngurii')
        return v

    def request(self):
        self.poll()
        v = self.view()
        with patch('cmdrhelper.route_planner.route_planner_view.ShipRouteWorker') as worker:
            v._thread_pool = Mock()
            v._calculate_ship_route()
            self.assertEqual(worker.call_count, 1)
            return worker.call_args.args[0]

    def test_exact_catalog_identity_and_values(self):
        spec = lookup_fsd_spec(ITEM)
        self.assertEqual((spec.item, spec.size, spec.rating, spec.variant), (ITEM, 7, 'A', 'SCO'))
        self.assertEqual((spec.optimal_mass, spec.max_fuel_per_jump, spec.fuel_power,
                          spec.fuel_multiplier), (3000., 13.1, 2.75, .013))
        self.assertIsNone(lookup_fsd_spec(ITEM + '_other_variant'))

    def test_real_engineering_values_are_final_not_applied_twice(self):
        loadout = self.state.ship_loadout
        self.assertEqual((loadout.fsd_blueprint, loadout.fsd_engineering_level,
                          loadout.fsd_engineering_quality), ('FSD_LongRange', 5, 1.))
        for _ in range(2):
            technical = derive_ship_route_technical_data(loadout)
            self.assertEqual(technical.optimal_mass, 4650.)
            self.assertEqual(technical.max_fuel_per_jump, 13.1)
        mass = next(m for m in loadout.fsd_engineering_modifiers if m['Label'] == 'Mass')
        self.assertEqual((mass['OriginalValue'], mass['Value']), (80., 104.))

    def test_explicit_max_fuel_modifier_overrides_catalog(self):
        self.raw['Modules'][0]['Engineering']['Modifiers'].append(
            dict(Label='MaxFuelPerJump', Value=14., OriginalValue=13.1))
        loadout = _loadout_from_event(self.raw, ShipLoadoutData())
        self.assertEqual(derive_ship_route_technical_data(loadout).max_fuel_per_jump, 14.)

    def test_guardian_booster_on_and_off(self):
        self.assertEqual(derive_ship_route_technical_data(self.state.ship_loadout).range_boost, 10.5)
        self.raw['Modules'][1]['On'] = False
        loadout = _loadout_from_event(self.raw, ShipLoadoutData())
        self.assertEqual(derive_ship_route_technical_data(loadout).range_boost, 0.)

    def test_standard_fsd_without_engineering(self):
        self.raw['Modules'][0] = dict(Slot='FrameShiftDrive', Item='int_hyperdrive_size5_class5', On=True)
        loadout = _loadout_from_event(self.raw, ShipLoadoutData())
        technical = derive_ship_route_technical_data(loadout)
        self.assertEqual((technical.optimal_mass, technical.max_fuel_per_jump,
                          technical.fuel_multiplier), (1050., 5., .012))
        self.assertIsNone(loadout.fsd_blueprint)

    def test_status_poll_fills_real_panther_and_emits_update(self):
        self.poll()
        technical = derive_ship_route_technical_data(self.state.ship_loadout)
        self.assertTrue(technical.complete)
        for name, value in EXPECTED.items():
            self.assertAlmostEqual(getattr(technical, name), value, places=8, msg=name)
        self.state.shipRouteInputsChanged.emit.assert_called_once_with(self.state.ship_loadout)

    def test_reserve_only_status_change_updates_form(self):
        self.poll()
        v = self.view()
        # The lightweight test signal records emission; deliver it like Qt does.
        self.state.shipRouteInputsChanged.emit.side_effect = v._ship_route_inputs_changed
        self.poll(status(Fuel={'FuelReservoir':.25}, timestamp='2026-10-11T14:57:55Z'))
        self.assertEqual(v.ship_reserve_size.value(), .25)
        self.assertEqual(v.ship_cargo.value(), 0)

    def test_reserve_capacity_is_not_used_as_fill_level(self):
        self.poll(status(Fuel={'FuelMain':128., 'FuelReservoir':.4}))
        technical = derive_ship_route_technical_data(self.state.ship_loadout)
        self.assertEqual((technical.internal_tank_size, technical.reserve_size), (1.11, .4))
        self.poll(status(Fuel={'FuelMain':128.}))
        self.assertIsNone(self.state.ship_loadout.reserve_fuel)

    def test_invalid_reserve_is_unknown(self):
        for value in (None, True, '1.11', -1, 1.12, float('nan'), float('inf')):
            with self.subTest(value=value):
                self.assertIsNone(status_reserve_fuel(self.state, status(Fuel={'FuelReservoir':value})))

    def test_zero_cargo_is_confirmed_and_missing_is_not_zero(self):
        self.poll()
        self.assertEqual(self.state.ship_loadout.cargo, 0)
        self.poll(status(Cargo=None))
        self.assertIsNone(self.state.ship_loadout.cargo)
        self.assertFalse(derive_ship_route_technical_data(self.state.ship_loadout).complete)

    def test_existing_journal_cargo_resolver_is_reused(self):
        self.tracker.apply(event('Cargo', '2026-10-11T14:54:00Z', Vessel='Ship', Count=7),
                           'F_TEST_PANTHER', self.path)
        self.poll(status(Cargo=None))
        self.assertEqual(self.state.ship_loadout.cargo, 7)
        self.assertEqual(self.state.ship_loadout.cargo, current_ship_cargo(self.state)['count'])

    def test_stale_status_and_future_status_rejected(self):
        for stamp in ('2026-10-11T14:54:00Z', '2026-10-11T14:58:01Z', 'invalid'):
            with self.subTest(stamp=stamp):
                self.poll(status(timestamp=stamp))
                self.assertIsNone(self.state.ship_loadout.reserve_fuel)
                self.assertIsNone(self.state.ship_loadout.cargo)

    def test_identical_confirmed_status_can_be_retained_but_changed_fuel_cannot(self):
        self.poll()
        with patch('cmdrhelper.ship_cargo.utc_now', return_value=NOW + timedelta(minutes=10)):
            self.poll()
            self.assertEqual(self.state.ship_loadout.reserve_fuel, 1.11)
            self.poll(status(Fuel={'FuelReservoir':.5}))
            self.assertIsNone(self.state.ship_loadout.reserve_fuel)

    def test_switch_away_and_back_invalidates_old_status_even_same_ship(self):
        self.poll()
        for sid in (38, 44):
            self.tracker.apply(event('ShipyardSwap', '2026-10-11T14:57:54Z', ShipID=sid),
                               'F_TEST_PANTHER', self.path)
        self.tracker.apply(self.raw, 'F_TEST_PANTHER', self.path)
        self.poll()
        self.assertIsNone(self.state.ship_loadout.reserve_fuel)
        self.assertIsNone(self.state.ship_loadout.cargo)

    def test_commander_session_and_ship_mismatches_rejected(self):
        mutations = [lambda s: setattr(s, 'commander_fid', 'OTHER'),
                     lambda s: setattr(s, 'commander_id', 2),
                     lambda s: s._journal_index_sessions[-1].update(fid_seen='OTHER'),
                     lambda s: s._journal_index_sessions[-1].update(journal_file='other.log'),
                     lambda s: setattr(s.ship_loadout, 'ship_id', 38),
                     lambda s: s.ship_cargo_context.update(session_start='2026-10-11T14:58:00Z'),
                     lambda s: setattr(s.ship_loadout, 'loadout_stale', True)]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                state = copy.deepcopy(self.state)
                mutation(state)
                self.assertIsNone(status_reserve_fuel(state, status()))
                self.assertIsNone(current_ship_cargo(state))

    def test_new_loadgame_same_journal_invalidates_confirmation(self):
        self.poll()
        self.tracker.apply(event('LoadGame', '2026-10-11T14:57:54Z', Ship='panthermkii', ShipID=44),
                           'F_TEST_PANTHER', self.path)
        self.poll()
        self.assertIsNone(self.state.ship_loadout.reserve_fuel)

    def test_new_ship_accepts_only_its_later_status(self):
        self.poll()
        self.tracker.apply(event('ShipyardSwap', '2026-10-11T14:57:54Z', ShipID=45),
                           'F_TEST_PANTHER', self.path)
        raw = dict(self.raw, ShipID=45, timestamp='2026-10-11T14:57:54Z')
        self.tracker.apply(raw, 'F_TEST_PANTHER', self.path)
        self.state.ship_loadout = _loadout_from_event(raw, self.state.ship_loadout)
        self.poll()
        self.assertIsNone(self.state.ship_loadout.reserve_fuel)
        self.poll(status(timestamp='2026-10-11T14:57:55Z', Fuel={'FuelReservoir':.2}))
        self.assertEqual(self.state.ship_loadout.reserve_fuel, .2)
        self.assertEqual(self.state.ship_loadout.cargo, 0)

    def test_on_foot_srv_and_fighter_contexts_rejected(self):
        for kind, fields in [('Disembark', {}), ('LaunchSRV', {}), ('LaunchFighter', {})]:
            with self.subTest(kind=kind):
                tracker = copy.deepcopy(self.tracker)
                tracker.apply(event(kind), 'F_TEST_PANTHER', self.path)
                state = copy.deepcopy(self.state)
                state.ship_cargo_context = tracker.context
                self.assertIsNone(status_reserve_fuel(state, status()))
                self.assertIsNone(current_ship_cargo(state))
        for fields in (dict(Flags2=1), dict(Flags=1 << 26), dict(Flags=1 << 25)):
            self.assertIsNone(status_reserve_fuel(self.state, status(**fields)))

    def test_pending_journal_bytes_block_route_telemetry(self):
        self.poll()
        self.path.write_text(self.path.read_text() + '{}\n')
        self.poll()
        self.assertIsNone(self.state.ship_loadout.reserve_fuel)
        self.assertIsNone(self.state.ship_loadout.cargo)

    def test_stored_module_json_reconstructs_same_engineering(self):
        live = self.state.ship_loadout
        row = asdict(live)
        for name in tuple(row):
            if name.startswith('fsd_') and name != 'fsd_item':
                del row[name]
        stored = AppState._stored_ship_loadout(row)
        for name in asdict(live):
            if name.startswith('fsd_') or name in ('modules', 'guardian_fsd_boosters'):
                self.assertEqual(getattr(stored, name), getattr(live, name), name)
        self.assertEqual(derive_ship_route_technical_data(stored).optimal_mass, 4650.)
        self.assertIsNone(stored.cargo)
        self.assertIsNone(stored.reserve_fuel)

    def test_stored_legacy_row_without_modules_does_not_invent_engineering(self):
        stored = AppState._stored_ship_loadout(dict(ship_id=44, fsd_item=ITEM))
        self.assertIsNone(stored.fsd_optimal_mass)
        self.assertEqual(stored.fsd_item, ITEM)

    def test_button_resets_wrong_manual_fuel_and_uses_current_values(self):
        self.poll()
        v = self.view()
        v.ship_max_fuel.setValue(41.)
        v._ship_loadout_changed()
        self.assertEqual(v._ship_input_value('max_fuel_per_jump'), 41.)
        v.ship_apply_loadout_button.click()
        self.assertFalse(v._ship_manual_overrides)
        self.assertEqual(v.ship_max_fuel.value(), 13.1)
        self.assertEqual(v._ship_input_value('fuel_multiplier'), .013)
        self.assertAlmostEqual(v._ship_input_value('base_mass'), 1857.209976, places=8)

    def test_button_clears_manual_values_when_automatic_data_missing(self):
        v = self.view()
        v.ship_cargo.setValue(0)
        v.ship_reserve_size.setValue(1.11)
        v.ship_apply_loadout_button.click()
        self.assertIn('cargo', v._missing_ship_input_fields())
        self.assertIn('reserve_size', v._missing_ship_input_fields())

    def test_distinct_missing_module_catalog_and_live_messages(self):
        v = self.view()
        for item, key in [(None, 'unknown_fsd'), ('unknown_hyperdrive', 'missing_fsd_specs'),
                          (ITEM, 'missing_live_data')]:
            self.state.ship_loadout.fsd_item = item
            v._ship_loadout_changed()
            self.assertEqual(v.ship_loadout_status.text(), tr('route_planner.ship_loadout_' + key))
            self.assertEqual(v.ship_loadout_status.toolTip(), item or '')

    def test_missing_fields_block_worker_and_network(self):
        self.poll()
        v = self.view()
        with patch('cmdrhelper.route_planner.route_planner_view.ShipRouteWorker') as worker:
            for field in EXPECTED:
                with self.subTest(field=field):
                    v._ship_field_has_value[field] = False
                    v._calculate_ship_route()
                    worker.assert_not_called()
                    v._ship_field_has_value[field] = True

    def test_invalid_engineering_never_reports_complete_or_starts_worker(self):
        self.poll()
        v = self.view()
        with patch('cmdrhelper.route_planner.route_planner_view.ShipRouteWorker') as worker:
            for value in (0, -1, float('nan'), float('inf')):
                self.state.ship_loadout.fsd_optimal_mass = value
                v._ship_loadout_changed()
                self.assertIn('optimal_mass', v._missing_ship_input_fields())
                self.assertNotEqual(v.ship_loadout_status.text(), tr('route_planner.ship_loadout_complete'))
                v._calculate_ship_route()
            worker.assert_not_called()

    def test_invalid_request_values_block_even_system_lookup(self):
        request = self.request()
        client = SpanshGalaxyClient()
        with patch.object(client, '_request_json') as transport:
            for field in EXPECTED:
                for value in (None, float('nan'), float('inf'), -1, True):
                    with self.subTest(field=field, value=value):
                        with self.assertRaises(SpanshError) as caught:
                            client.calculate(replace(request, **{field:value}))
                        self.assertEqual(caught.exception.code, 'invalid_input')
            transport.assert_not_called()

    def test_full_precision_request_and_encoded_mock_route(self):
        request = self.request()
        for key, value in EXPECTED.items():
            self.assertAlmostEqual(getattr(request, key), value, places=8, msg=key)
        payloads = []
        def response(http_request, **kwargs):
            if http_request.data is not None:
                payloads.append(parse_qs(http_request.data.decode()))
                data = {'result':{'jumps':[{'name':request.source}, {'name':'Ngurii'}]}}
            elif '/search/systems?' in http_request.full_url:
                data = {'results':[{'name':'Ngurii', 'id64':2}]}
            else:
                ident = int(http_request.full_url.rsplit('/', 1)[1])
                data = {'record':{'id64':ident, 'name':request.source if ident != 2 else 'Ngurii'}}
            return io.BytesIO(json.dumps(data).encode())
        with patch('cmdrhelper.route_planner.spansh_galaxy_client.urlopen', side_effect=response):
            route = SpanshGalaxyClient().calculate(request)
        self.assertEqual([jump.system for jump in route.jumps], [request.source, 'Ngurii'])
        self.assertEqual(len(payloads), 1)
        for key, value in EXPECTED.items():
            self.assertAlmostEqual(float(payloads[0][key][0]), value, places=8, msg=key)
        self.assertEqual(payloads[0]['fuel_multiplier'], ['0.013'])

    def test_twelve_languages_and_both_themes(self):
        language = get_language()
        self.addCleanup(set_language, language)
        v = self.view()
        self.assertEqual(len(_TRANSLATIONS), 12)
        for stylesheet in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            v.setStyleSheet(stylesheet)
            v.resize(1200, 850)
            v.show()
            for lang, table in _TRANSLATIONS.items():
                set_language(lang)
                for item, key in [('unknown_drive', 'ship_loadout_missing_fsd_specs'),
                                  (ITEM, 'ship_loadout_missing_live_data')]:
                    with self.subTest(lang=lang, key=key, dark=stylesheet is DARK_STYLESHEET):
                        self.assertTrue(table['route_planner.' + key])
                        self.state.ship_loadout.fsd_item = item
                        v._ship_loadout_changed()
                        self.app.processEvents()
                        self.assertEqual(v.ship_loadout_status.text(), table['route_planner.' + key])
                        self.assertTrue(v.ship_loadout_status.wordWrap())
                        self.assertFalse(v.grab().isNull())


if __name__ == '__main__':
    unittest.main()
