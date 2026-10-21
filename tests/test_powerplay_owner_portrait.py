"""Small controlling-power portraits; synthetic state and read-only assets."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from cmdrhelper.help_content import HELP_LANGUAGES
from cmdrhelper.i18n import set_language, tr
from cmdrhelper.powerplay import PowerplayState
from cmdrhelper.ui.powerplay_portraits import PowerPortrait, portrait_key
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests import test_powerplay_system_view as system_tests


class OwnerPortraitTests(unittest.TestCase):
    setUpClass = classmethod(system_tests.SystemViewTests.setUpClass.__func__)
    setUp = system_tests.SystemViewTests.setUp

    def owner(self, name):
        self.state.powerplay.system['ControllingPower'] = name
        self.view.render()
        for _ in range(4):
            self.app.processEvents()
        return self.display.owner_portrait

    def test_own_foreign_and_all_twelve_assets(self):
        portrait = self.owner('Nakato Kaine')
        self.assertTrue(portrait.isHidden())
        for name in ('Aisling Duval', 'Archon Delaine', 'Arissa Lavigny-Duval',
                     'Denton Patreus', 'Edmund Mahon', 'Felicia Winters', 'Li Yong-Rui',
                     'Pranav Antal', 'Yuri Grom', 'Zemina Torval', 'Jerome Archer', 'Nakato Kaine'):
            self.state.powerplay.power = 'Edmund Mahon' if name == 'Nakato Kaine' else 'Nakato Kaine'
            portrait = self.owner(name)
            self.assertIsInstance(portrait, PowerPortrait)
            self.assertFalse(portrait.isHidden())
            self.assertEqual((portrait.width(), portrait.height()), (42, 56))
            self.assertEqual(portrait.key, portrait_key(name))
            self.assertFalse(portrait.pixmap().isNull())
            self.assertLessEqual(portrait.pixmap().width(), portrait.contentsRect().width())
            self.assertLessEqual(portrait.pixmap().height(), portrait.contentsRect().height())
        self.owner('Edmund Mahon')
        self.assertTrue(portrait.isHidden())
        self.assertFalse(self.display.owner_separator.isHidden())

    def test_alias_and_missing_asset(self):
        portrait = self.owner('A. Lavigny-Duval')
        image = portrait.pixmap().toImage()
        self.owner('Arissa Lavigny-Duval')
        self.assertEqual(image, portrait.pixmap().toImage())
        self.state.powerplay.power = 'A. Lavigny-Duval'
        self.view.render()
        self.assertTrue(portrait.isHidden())
        self.state.powerplay.power = 'Nakato Kaine'
        with TemporaryDirectory() as folder, patch(
                'cmdrhelper.ui.powerplay_portraits.POWERPLAY_ASSET_DIR', Path(folder)):
            self.owner('Edmund Mahon')
            self.assertEqual(portrait.text(), tr('pp2.portrait.placeholder'))
            self.assertTrue(portrait.pixmap().isNull())
            self.assertEqual(portrait.key, 'edmund_mahon')

    def test_unknown_unoccupied_stale_and_switches(self):
        portrait = self.owner('Edmund Mahon')
        self.state.powerplay.power = ''
        self.view.render()
        self.assertTrue(portrait.isHidden())
        self.state.powerplay.power = 'Nakato Kaine'
        self.owner('')
        self.assertTrue(portrait.isHidden())
        self.owner('Edmund Mahon')
        self.state.powerplay.system.update(PowerplayState='Unoccupied',
            Powers=['Edmund Mahon', 'Nakato Kaine'])
        self.view.render()
        self.assertTrue(portrait.isHidden())
        self.assertFalse(self.display.conflicts.isHidden())
        self.assertEqual(len(self.display.conflict_rows), 2)
        self.state.powerplay.system['PowerplayState'] = 'Fortified'
        self.state.system = 'New system'
        self.state.changed.emit()
        self.assertTrue(portrait.isHidden())
        self.assertEqual(portrait.key, '')
        self.state.powerplay.system['StarSystem'] = 'New system'
        self.state.changed.emit()
        self.assertFalse(portrait.isHidden())
        self.state.powerplay = PowerplayState(power='Edmund Mahon',
                                             system=deepcopy(self.state.powerplay.system))
        self.state.changed.emit()
        self.assertTrue(portrait.isHidden())

    def test_closed_updates_and_preserved_columns(self):
        heading = self.view.section_headings['system']
        positions = [self.view.columns.getItemPosition(i) for i in range(self.view.columns.count())]
        heading.button.setChecked(False)
        portrait = self.owner('Edmund Mahon')
        self.assertTrue(heading.body.isHidden())
        self.assertEqual(portrait.key, 'edmund_mahon')
        heading.button.setChecked(True)
        self.assertTrue(portrait.isVisible())
        self.assertEqual(positions, [self.view.columns.getItemPosition(i)
                                   for i in range(self.view.columns.count())])

    def test_themes_languages_widths_and_unchanged_values(self):
        self.addCleanup(set_language, 'de')
        self.owner('Arissa Lavigny-Duval')
        before = deepcopy(self.state.powerplay)
        bar = self.display.control_bar
        markers = (bar.white_position, bar.yellow_position)
        for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.view.setStyleSheet(style)
            for language in HELP_LANGUAGES:
                set_language(language)
                for width in (360, 480, 1200):
                    with self.subTest(language=language, width=width, style=style[:20]):
                        self.view.resize(width, 900)
                        # Some existing translations already overflow at 360 px.
                        # Compare against the unchanged own-power row at this width.
                        self.owner('Nakato Kaine')
                        baseline_overflow = self.view.horizontalScrollBar().maximum()
                        self.owner('Arissa Lavigny-Duval')
                        portrait = self.display.owner_portrait
                        name = self.display.labels['owner']
                        relationship = self.display.labels['relationship']
                        self.assertLessEqual(self.view.horizontalScrollBar().maximum(), baseline_overflow)
                        self.assertGreaterEqual(name.x(), portrait.x() + portrait.width())
                        self.assertGreaterEqual(relationship.y(), name.y() + name.height())
                        self.assertGreaterEqual(name.height(), name.heightForWidth(name.width()))
                        self.assertGreaterEqual(relationship.height(), relationship.heightForWidth(relationship.width()))
                        self.assertFalse(portrait.grab().isNull())
        self.assertEqual(markers, (bar.white_position, bar.yellow_position))
        self.assertEqual(before, self.state.powerplay)


if __name__ == '__main__':
    unittest.main()
