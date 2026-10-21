"""General PP2 guidance, without asserting local activity availability."""
import copy
from importlib import import_module
import unittest

from cmdrhelper.help_content import HELP_LANGUAGES
from cmdrhelper.i18n import set_language, tr
from cmdrhelper.powerplay import PowerplayState, context
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests import test_powerplay_ethos as ethos


class GeneralActivityTests(unittest.TestCase):
    setUpClass = classmethod(ethos.EthosViewTests.setUpClass.__func__)
    setUp = ethos.EthosViewTests.setUp

    def unoccupied(self, powers=None):
        self.state.powerplay.system = dict(StarSystem='Here', PowerplayState='Unoccupied')
        if powers is not None:
            self.state.powerplay.system['Powers'] = powers
        self.view.render()

    def test_clear_category_retains_existing_list(self):
        self.unoccupied(['Nakato Kaine'])
        self.assertEqual(context(self.state.powerplay), ('unoccupied', 'acquisition'))
        self.assertEqual(self.view.mode.text(), tr('pp2.mode.acquisition'))
        self.assertIn('✓ Kopfgeldjagd', self.view.actions.text().splitlines())
        self.assertNotIn(tr('pp2.general.hint'), self.view.actions.text())
        self.assertFalse(self.view.notice.isHidden())

    def assert_hint(self):
        self.assertEqual(self.view.mode.text(), tr('pp2.general.label'))
        self.assertEqual(self.view.actions.text(), tr('pp2.general.hint'))
        self.assertEqual(self.view.actions.toolTip(), '')
        self.assertTrue(self.view.notice.isHidden())
        self.assertNotIn('★', self.view.actions.text())
        self.assertNotIn('✓', self.view.actions.text())
        self.assertNotIn('\n', self.view.actions.text())

    def test_ambiguous_participants_do_not_select_conflict(self):
        for powers in (['Nakato Kaine', 'Edmund Mahon'], ['Edmund Mahon'],
                       ['Edmund Mahon', 'Aisling Duval'], [], None):
            with self.subTest(powers=powers):
                self.unoccupied(powers)
                self.assertEqual(context(self.state.powerplay), ('unoccupied', None))
                self.assert_hint()
        self.assertEqual(self.view.actions.text(),
                         'Andere KDTN abfangen, die hier Aktionen ausführen, '
                         'um den Fortschritt einer anderen Macht zu verlangsamen.')

    def test_no_system_name_or_unoccupied_only_rule(self):
        for name in ('HIP 61173', 'Sol', 'Another system'):
            for status, owner in (('Unoccupied', ''), ('Unknown', ''),
                                  ('Unoccupied', 'Other'), ('Fortified', '')):
                with self.subTest(name=name, status=status, owner=owner):
                    self.state.system = name
                    self.state.powerplay.system = dict(StarSystem=name,
                        PowerplayState=status, ControllingPower=owner)
                    self.view.render()
                    self.assertIsNone(context(self.state.powerplay)[1])
                    self.assert_hint()

    def test_missing_cache_or_categories_do_not_hide_general_hint(self):
        self.powers['Nakato Kaine']['ethos'] = {'acquisition': []}
        self.unoccupied()
        self.assert_hint()
        for cache in (None, {}):
            self.view.cache.load.return_value = cache
            self.view.render()
            self.assert_hint()
        # A known category still requires its existing cache evidence.
        self.view.cache.load.return_value = None
        self.unoccupied(['Nakato Kaine'])
        self.assertEqual(self.view.actions.text(), tr('pp2.no_data'))
        self.assertEqual(self.view.notice.text(), tr('pp2.cache_unavailable'))
        self.assertFalse(self.view.notice.isHidden())

    def test_switches_refresh_closed_area_and_clear_stale_guidance(self):
        self.view.show()
        self.app.processEvents()
        heading = self.view.section_headings['actions']
        heading.button.setChecked(False)
        self.unoccupied()
        self.assertTrue(heading.body.isHidden())
        self.state.powerplay = PowerplayState(power='Edmund Mahon', system=dict(
            StarSystem='Here', PowerplayState='Unoccupied'))
        self.state.changed.emit()
        self.assertIn('Edmund Mahon', self.view.action_heading.text())
        self.assert_hint()
        self.state.powerplay.system.update(Powers=['Edmund Mahon'])
        self.state.changed.emit()
        self.assertIn('✓ Seltene Waren verkaufen · ★ Ethos', self.view.actions.text())
        self.assertFalse(self.view.notice.isHidden())
        self.assertTrue(heading.body.isHidden())
        self.state.powerplay.system.pop('Powers')
        self.state.changed.emit()
        self.assert_hint()
        self.state.system = 'Elsewhere'
        self.state.changed.emit()
        self.assertEqual(self.view.actions.text(), tr('pp2.context_unknown'))
        self.assertEqual(self.view.actions.toolTip(), '')
        self.state.powerplay.system = dict(StarSystem='Elsewhere', PowerplayState='Unoccupied')
        self.state.powerplay.power = ''
        self.state.changed.emit()
        self.assertIn(tr('pp2.need_power'), self.view.actions.text())
        self.assertNotIn('•', self.view.actions.text())
        self.assertTrue(heading.body.isHidden())
        heading.button.setChecked(True)
        self.assertIn(tr('pp2.need_power'), self.view.actions.text())

    def test_twelve_languages_both_themes_and_read_only_state(self):
        self.unoccupied()
        before = copy.deepcopy(self.state.powerplay)
        cache_before = copy.deepcopy(self.powers)
        self.view.section_headings['actions'].button.setChecked(True)
        for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.view.setStyleSheet(style)
            for language in HELP_LANGUAGES:
                with self.subTest(language=language, style=style[:20]):
                    set_language(language)
                    catalog = import_module('cmdrhelper.i18n.' + language).TRANSLATIONS
                    self.view.render()
                    self.view.resize(1050, 900)
                    self.view.show()
                    self.app.processEvents()
                    self.assertEqual(self.view.actions.text(), catalog['pp2.general.hint'])
                    self.assertEqual(self.view.mode.text(), catalog['pp2.general.label'])
                    self.assertFalse(self.view.actions.grab().isNull())
                    self.assertEqual(self.view.horizontalScrollBar().maximum(), 0)
        self.assertEqual(self.state.powerplay, before)
        self.assertEqual(self.powers, cache_before)


if __name__ == '__main__':
    unittest.main()
