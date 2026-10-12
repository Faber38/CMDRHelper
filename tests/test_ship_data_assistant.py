"""Assistant persistence and UI tests use isolated settings, never the user profile."""
import copy
from dataclasses import replace
import json
from pathlib import Path
from unittest.mock import Mock, patch
import unittest

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QDialog, QMessageBox

from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.route_planner.manual_ship_data import (FIELDS, ManualShipData,
    LIVE_SECONDS, parse_number, scope)
from cmdrhelper.route_planner.models import GuardianFsdBooster
from cmdrhelper.route_planner.ship_data_dialog import ShipDataDialog, text
from cmdrhelper.route_planner.spansh_galaxy_client import SpanshGalaxyClient
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
import test_ship_route_inputs as route_tests
from test_ship_route_inputs import EXPECTED


class ShipDataAssistantTests(unittest.TestCase):
    poll = route_tests.ShipRouteInputsTests.poll
    view = route_tests.ShipRouteInputsTests.view

    def setUp(self):
        route_tests.ShipRouteInputsTests.setUp(self)
        self.now = 1000.
        self.state.commander = 'Test Commander'
        self.settings_path = self.folder / 'settings.ini'
        self.settings = QSettings(str(self.settings_path), QSettings.IniFormat)
        self.state.settings = self.settings
        self.store = ManualShipData(self.settings, clock=lambda: self.now)
        self.state._ship_route_manual_data = self.store

    def dialog(self):
        v = self.view()
        d = ShipDataDialog(self.state, self.store, v)
        self.addCleanup(d.close)
        return d

    def unknown_fsd(self):
        self.state.ship_loadout.fsd_item = 'int_hyperdrive_test_size7_class5'
        self.state.ship_loadout.fsd_optimal_mass = None

    def test_missing_fields_are_editable_and_automatic_fields_readonly(self):
        cases = {
            'tank_size': lambda l: setattr(l, 'main_tank_capacity', None),
            'cargo': lambda l: setattr(l, 'cargo', None),
            'reserve_size': lambda l: setattr(l, 'reserve_fuel', None),
            'base_mass': lambda l: setattr(l, 'unladen_mass', None),
            'optimal_mass': lambda l: self.unknown_fsd(),
            'fuel_power': lambda l: self.unknown_fsd(),
            'fuel_multiplier': lambda l: self.unknown_fsd(),
            'max_fuel_per_jump': lambda l: self.unknown_fsd(),
            'internal_tank_size': lambda l: setattr(l, 'reserve_tank_capacity', None),
            'range_boost': lambda l: setattr(l, 'guardian_fsd_boosters',
                (GuardianFsdBooster('unknown_guardian', True),)),
        }
        original = copy.deepcopy(self.state.ship_loadout)
        for field, change in cases.items():
            with self.subTest(field=field):
                self.state.ship_loadout = copy.deepcopy(original)
                change(self.state.ship_loadout)
                d = self.dialog()
                self.assertIn(field, d.editors)
                self.assertFalse(d.editors[field].isReadOnly())
                self.assertEqual(d.form.rowCount(), 10)
                d.close()
        self.state.ship_loadout = original
        d = self.dialog()
        self.assertNotIn('optimal_mass', d.editors)

    def test_decimal_point_comma_and_zero(self):
        for raw, expected in [('0,013', .013), ('0.013', .013), (' 2,75 ', 2.75), ('1e-3', .001)]:
            self.assertEqual(parse_number(raw, 'fuel_multiplier'), expected)
        self.assertEqual(parse_number('0', 'cargo'), 0)
        self.assertEqual(parse_number('0,0', 'reserve_size'), 0)
        self.assertIsNone(parse_number('', 'cargo'))

    def test_invalid_numbers_and_ranges_are_not_corrected(self):
        for raw in ('nan', 'inf', '1e999', '1.000,5', '1,000.5', '1 000', 'abc', '-1', '0', '101'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_number(raw, 'fuel_multiplier')

    def test_inline_validation_preserves_invalid_text(self):
        self.unknown_fsd()
        d = self.dialog()
        d.editors['fuel_multiplier'].setText('12,3,4')
        d.save()
        self.assertTrue(d.errors['fuel_multiplier'].text())
        self.assertEqual(d.editors['fuel_multiplier'].text(), '12,3,4')
        self.assertFalse(self.settings.contains(self.store.key(self.state)))

    def test_reserve_and_cargo_dependencies(self):
        d = self.dialog()
        d.editors['reserve_size'].setText('2')
        d.editors['cargo'].setText('577')
        _, errors = d.validate()
        self.assertEqual(errors, {'reserve_size':'reserve', 'cargo':'cargo'})
        d.save()
        self.assertEqual(d.result(), QDialog.Rejected)

    def test_save_load_and_helper_restart(self):
        self.unknown_fsd()
        self.store.save(self.state, {'fuel_power':2.75, 'fuel_multiplier':.013})
        another = ManualShipData(QSettings(str(self.settings_path), QSettings.IniFormat))
        values, sources, _ = another.resolve(self.state)
        self.assertEqual(values['fuel_multiplier'], .013)
        self.assertEqual(sources['fuel_multiplier'], 'manual')
        self.assertEqual(values['fuel_power'], 2.75)

    def test_commander_and_ship_isolation(self):
        self.unknown_fsd()
        self.store.save(self.state, {'fuel_multiplier':.013})
        for field, value in [('commander_fid','OTHER'), ('ship_id',45)]:
            state = copy.copy(self.state)
            state.ship_loadout = copy.deepcopy(self.state.ship_loadout)
            setattr(state.ship_loadout if field == 'ship_id' else state, field, value)
            with self.subTest(field=field):
                self.assertIsNone(self.store.resolve(state)[0]['fuel_multiplier'])
                self.store.save(state, {'fuel_multiplier':.012})
                self.store.delete(state)
                self.assertEqual(self.store.resolve(self.state)[0]['fuel_multiplier'], .013)

    def test_fsd_switch_retains_but_does_not_apply_old_data(self):
        self.unknown_fsd()
        self.store.save(self.state, {'fuel_multiplier':.013})
        self.state.ship_loadout.fsd_item = 'another_unknown_fsd'
        values, _, records = self.store.resolve(self.state)
        self.assertIsNone(values['fuel_multiplier'])
        self.assertEqual(records['fuel_multiplier']['value'], .013)
        d = self.dialog()
        self.assertIn('fuel_multiplier', d.confirmations)
        d.save()
        self.assertIsNone(self.store.resolve(self.state)[0]['fuel_multiplier'])
        d = self.dialog()
        d.confirmations['fuel_multiplier'].setChecked(True)
        d.save()
        self.assertEqual(self.store.resolve(self.state)[0]['fuel_multiplier'], .013)

    def test_engineering_change_invalidates_only_affected_fsd_values(self):
        self.unknown_fsd()
        self.store.save(self.state, {'optimal_mass':4650., 'fuel_multiplier':.013, 'max_fuel_per_jump':13.1})
        self.state.ship_loadout.fsd_engineering_level = 4
        values, _, _ = self.store.resolve(self.state)
        self.assertIsNone(values['optimal_mass'])
        self.assertIsNone(values['max_fuel_per_jump'])
        self.assertEqual(values['fuel_multiplier'], .013)

    def test_automatic_data_has_priority_and_preserves_saved_value(self):
        self.store.save(self.state, {'optimal_mass':3000.})
        values, sources, records = self.store.resolve(self.state)
        self.assertEqual(values['optimal_mass'], 4650.)
        self.assertEqual(sources['optimal_mass'], 'automatic')
        self.assertEqual(records['optimal_mass']['value'], 3000.)
        d = self.dialog()
        self.assertEqual(d.editors['optimal_mass'].text(), '3000.0')
        self.assertIn('3000', self.view().ship_optimal_mass.toolTip())

    def test_live_values_expire_and_are_not_persisted(self):
        self.store.save(self.state, {'cargo':0., 'reserve_size':1.11})
        self.assertEqual(self.store.resolve(self.state)[0]['cargo'], 0.)
        raw = json.loads(self.settings.value(self.store.key(self.state), '{}'))
        self.assertNotIn('cargo', raw)
        self.assertNotIn('reserve_size', raw)
        self.now += LIVE_SECONDS
        self.assertIsNone(self.store.resolve(self.state)[0]['cargo'])
        self.assertIsNone(self.store.resolve(self.state)[0]['reserve_size'])

    def test_live_values_not_restored_after_restart(self):
        self.store.save(self.state, {'cargo':0., 'reserve_size':1.11})
        restarted = ManualShipData(QSettings(str(self.settings_path), QSettings.IniFormat))
        self.assertIsNone(restarted.resolve(self.state)[0]['cargo'])
        self.assertIsNone(restarted.resolve(self.state)[0]['reserve_size'])

    def test_live_session_generation_vehicle_and_ship_changes(self):
        for mutation in (
            lambda: self.state.ship_cargo_context.update(generation=999),
            lambda: self.state.ship_cargo_context.update(session_generation=999),
            lambda: self.state.ship_cargo_context.update(vessel='SRV'),
            lambda: self.state.ship_cargo_context.update(vessel=None),
            lambda: setattr(self.state.ship_loadout, 'ship_id', 45),
            lambda: setattr(self.state, 'commander_fid', 'OTHER'),
        ):
            original = copy.deepcopy(self.state.ship_cargo_context)
            self.store.save(self.state, {'cargo':0., 'reserve_size':1.11})
            mutation()
            self.assertIsNone(self.store.resolve(self.state)[0]['reserve_size'])
            self.state.ship_cargo_context = original
            self.state.ship_loadout.ship_id = 44
            self.state.commander_fid = 'F_TEST_PANTHER'

    def test_new_telemetry_permanently_displaces_manual_live_values(self):
        self.store.save(self.state, {'cargo':2., 'reserve_size':.3})
        self.poll()
        values, sources, _ = self.store.resolve(self.state)
        self.assertEqual(values['cargo'], 0.)
        self.assertEqual(sources['reserve_size'], 'automatic')
        self.state.ship_loadout.cargo = None
        self.state.ship_loadout.reserve_fuel = None
        self.assertIsNone(self.store.resolve(self.state)[0]['cargo'])
        self.assertIsNone(self.store.resolve(self.state)[0]['reserve_size'])

    def test_edit_and_clear_individual_saved_values(self):
        self.unknown_fsd()
        self.store.save(self.state, {'fuel_power':2.75, 'fuel_multiplier':.013})
        d = self.dialog()
        d.editors['fuel_power'].setText('2,6')
        d.editors['fuel_multiplier'].clear()
        d.save()
        self.assertEqual(d.result(), QDialog.Accepted)
        values, _, records = self.store.resolve(self.state)
        self.assertEqual(values['fuel_power'], 2.6)
        self.assertNotIn('fuel_multiplier', records)

    def test_delete_confirmation_names_ship_and_can_be_cancelled(self):
        self.unknown_fsd()
        self.store.save(self.state, {'fuel_multiplier':.013})
        d = self.dialog()
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.No) as prompt:
            d.delete()
        self.assertIn('Test Commander', prompt.call_args.args[2])
        self.assertIn('44', prompt.call_args.args[2])
        self.assertTrue(self.store.records(self.state))
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes):
            d.delete()
        self.assertFalse(self.store.records(self.state))

    def test_context_changed_while_dialog_open_does_not_save(self):
        self.unknown_fsd()
        d = self.dialog()
        d.editors['fuel_multiplier'].setText('.013')
        self.state.ship_loadout.ship_id = 45
        d.save()
        self.assertEqual(d.message.text(), text('changed'))
        self.assertFalse(self.store.records(self.state))

    def test_live_context_changed_while_dialog_open_does_not_save(self):
        d = self.dialog()
        d.editors['cargo'].setText('0')
        self.state.ship_cargo_context['generation'] += 1
        d.save()
        self.assertEqual(d.message.text(), text('changed'))

    def test_missing_identity_and_missing_fsd_are_not_guessed(self):
        self.state.commander_fid = ''
        d = self.dialog()
        self.assertFalse(d.save_button.isEnabled())
        self.state.commander_fid = 'F_TEST_PANTHER'
        self.state.ship_loadout.fsd_item = None
        self.state.ship_loadout.fsd_optimal_mass = None
        d = self.dialog()
        d.editors['fuel_multiplier'].setText('.013')
        self.assertIn('fuel_multiplier', d.validate()[1])

    def test_settings_failure_does_not_close_dialog(self):
        self.unknown_fsd()
        d = self.dialog()
        d.editors['fuel_multiplier'].setText('.013')
        with patch.object(self.store, '_write', side_effect=OSError('disk full')):
            d.save()
        self.assertEqual(d.result(), QDialog.Rejected)
        self.assertEqual(d.editors['fuel_multiplier'].text(), '.013')
        self.assertEqual(d.message.text(), text('save_error'))

    def test_apply_button_keeps_persistent_values_and_resets_form_override(self):
        self.unknown_fsd()
        self.store.save(self.state, {'max_fuel_per_jump':13.1})
        v = self.view()
        v.ship_max_fuel.setValue(41.)
        self.assertEqual(v.ship_max_fuel.toolTip(), text('form'))
        v.ship_apply_loadout_button.click()
        self.assertEqual(v.ship_max_fuel.value(), 13.1)
        self.assertTrue(self.store.records(self.state))
        self.assertEqual(v.ship_max_fuel.toolTip().splitlines()[0], text('manual'))

    def test_timer_expires_live_values_in_form(self):
        self.store.save(self.state, {'cargo':0., 'reserve_size':1.11})
        v = self.view()
        self.assertNotIn('cargo', v._missing_ship_input_fields())
        self.now += LIVE_SECONDS
        v._manual_input_timer.timeout.emit()
        self.assertIn('cargo', v._missing_ship_input_fields())
        self.assertIn('reserve_size', v._missing_ship_input_fields())

    def test_expiry_blocks_calculation_before_timer_tick(self):
        self.store.save(self.state, {'cargo':0., 'reserve_size':1.11})
        v = self.view()
        self.now += LIVE_SECONDS
        with patch('cmdrhelper.route_planner.route_planner_view.ShipRouteWorker') as worker:
            v._calculate_ship_route()
            worker.assert_not_called()

    def test_dialog_expiry_then_cancel_cannot_leave_stale_route_values(self):
        self.store.save(self.state, {'cargo':0., 'reserve_size':1.11})
        v = self.view()
        self.now += LIVE_SECONDS
        d = ShipDataDialog(self.state, self.store, v)
        d.reject()
        self.assertFalse(self.store.live)
        with patch('cmdrhelper.route_planner.route_planner_view.ShipRouteWorker') as worker:
            v._calculate_ship_route()
            worker.assert_not_called()
        self.assertIn('cargo', v._missing_ship_input_fields())

    def test_ship_switch_resets_unsaved_form_overrides(self):
        v = self.view()
        v.ship_max_fuel.setValue(41.)
        self.state.ship_loadout.ship_id = 45
        v._ship_loadout_changed()
        self.assertEqual(v.ship_max_fuel.value(), 13.1)
        self.assertNotIn('max_fuel_per_jump', v._ship_manual_overrides)

    def test_leaving_and_restoring_old_context_does_not_resurrect_live_values(self):
        self.store.save(self.state, {'cargo':0., 'reserve_size':1.11})
        self.state.commander_fid = 'OTHER'
        self.store.resolve(self.state)
        self.state.commander_fid = 'F_TEST_PANTHER'
        self.assertIsNone(self.store.resolve(self.state)[0]['cargo'])

    def test_assistant_button_applies_saved_values_after_accept(self):
        self.unknown_fsd()
        v = self.view()
        def complete(dialog):
            dialog.editors['fuel_multiplier'].setText('0,013')
            dialog.save()
            return dialog.result()
        with patch.object(ShipDataDialog, 'exec', new=complete):
            v.ship_complete_data_button.click()
        self.assertEqual(v.ship_fuel_multiplier.value(), .013)
        self.assertEqual(v.ship_fuel_multiplier.toolTip().splitlines()[0], text('manual'))

    def test_deleted_entry_does_not_affect_other_ship(self):
        self.unknown_fsd()
        self.store.save(self.state, {'fuel_multiplier':.013})
        other = copy.copy(self.state)
        other.ship_loadout = replace(self.state.ship_loadout, ship_id=45)
        self.store.save(other, {'fuel_multiplier':.012})
        self.store.delete(self.state)
        self.assertFalse(self.settings.contains(self.store.key(self.state)))
        self.assertEqual(self.store.resolve(other)[0]['fuel_multiplier'], .012)

    def test_settings_sync_failure_restores_previous_data(self):
        self.unknown_fsd()
        self.store.save(self.state, {'fuel_multiplier':.013})
        with patch.object(self.settings, 'status', return_value=QSettings.AccessError):
            with self.assertRaises(OSError):
                self.store.save(self.state, {'fuel_multiplier':.012})
        self.assertEqual(self.store.records(self.state)['fuel_multiplier']['value'], .013)

    def test_partial_save_does_not_claim_ready_or_send_request(self):
        self.unknown_fsd()
        self.store.save(self.state, {'fuel_multiplier':.013})
        v = self.view()
        self.assertEqual(v.ship_loadout_status.text(), text('incomplete'))
        with patch('cmdrhelper.route_planner.route_planner_view.ShipRouteWorker') as worker:
            v._calculate_ship_route()
            worker.assert_not_called()

    def test_complete_supplemented_request_with_mock(self):
        self.unknown_fsd()
        self.store.save(self.state, {key:EXPECTED[key] for key in
            ('optimal_mass', 'max_fuel_per_jump', 'fuel_power', 'fuel_multiplier', 'cargo', 'reserve_size')})
        v = self.view()
        self.assertEqual(v.ship_loadout_status.text(), text('ready'))
        with patch('cmdrhelper.route_planner.route_planner_view.ShipRouteWorker') as worker:
            v._thread_pool = Mock()
            v._calculate_ship_route()
            request = worker.call_args.args[0]
        def response(url, data=None):
            if data is not None:
                for name, expected in EXPECTED.items():
                    self.assertAlmostEqual(data[name], expected, places=8, msg=name)
                return {'result':{'jumps':[{'name':request.source}, {'name':'Ngurii'}]}}
            if '/search/systems?' in url:
                return {'results':[{'name':'Ngurii', 'id64':2}]}
            sid = int(url.rsplit('/', 1)[1])
            return {'record':{'name':'Ngurii' if sid == 2 else request.source, 'id64':sid}}
        client = SpanshGalaxyClient()
        with patch.object(client, '_request_json', side_effect=response):
            route = client.calculate(request)
        self.assertEqual(route.jumps[-1].system, 'Ngurii')

    def test_all_twelve_languages_and_both_themes(self):
        original_language = get_language()
        self.addCleanup(set_language, original_language)
        reference = {k for k in _TRANSLATIONS['en'] if k.startswith('route_planner.assistant_')}
        for lang, table in _TRANSLATIONS.items():
            with self.subTest(lang=lang):
                self.assertTrue(reference <= table.keys())
                for key in reference:
                    self.assertTrue(table[key].strip())
                    if lang != 'en':
                        self.assertNotEqual(table[key], _TRANSLATIONS['en'][key], key)
                set_language(lang)
                for stylesheet in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                    d = self.dialog()
                    d.setStyleSheet(stylesheet)
                    d.show()
                    self.app.processEvents()
                    self.assertEqual(d.windowTitle(), table['route_planner.assistant_title'])
                    self.assertFalse(d.grab().isNull())
                    d.close()


if __name__ == '__main__':
    unittest.main()
