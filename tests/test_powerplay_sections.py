"""PP2 disclosure controls, using synthetic state and isolated QSettings."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import subprocess
import sys
from unittest.mock import patch

from PySide6.QtCore import QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QStackedWidget, QWidget

from cmdrhelper.help_content import HELP_LANGUAGES
from cmdrhelper.i18n import set_language
from cmdrhelper.powerplay import PowerplayState, decode_powers_cache
from cmdrhelper.ui.powerplay_view import PowerplayView
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests.test_powerplay import ViewState, cache_bytes, event


class SectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = str(Path(tmp.name) / 'settings.ini')
        self.state = ViewState()
        self.state.settings = QSettings(self.path, QSettings.IniFormat)
        self.loader = patch('cmdrhelper.ui.powerplay_view.PowersCache.load',
                            return_value=decode_powers_cache(cache_bytes()))
        self.loader.start()
        self.addCleanup(self.loader.stop)
        set_language('de')
        self.addCleanup(set_language, 'de')
        self.stack = QStackedWidget()
        self.view = PowerplayView(self.state)
        self.stack.addWidget(self.view)
        self.stack.resize(1400, 1000)
        self.stack.show()
        self.addCleanup(self.stack.deleteLater)
        self.addCleanup(self.stack.close)
        self.settle()

    def settle(self):
        for _ in range(6):
            self.app.processEvents()

    def test_default_independent_toggles_and_height_reclaimed(self):
        self.assertEqual(self.state.settings.allKeys(), [])
        cards = dict(system=self.view.system_card, actions=self.view.action_section,
                     cargo=self.view.cargo_card)
        positions = (self.view.columns.getItemPosition(0), self.view.columns.getItemPosition(1))
        parents = {k: card.parentWidget() for k, card in cards.items()}
        for key, heading in self.view.section_headings.items():
            self.assertFalse(heading.button.isChecked())
            self.assertEqual(heading.button.arrowType(), Qt.RightArrow)
            self.assertTrue(heading.body.isHidden())
            closed = cards[key].sizeHint().height()
            QTest.mouseClick(heading.label, Qt.LeftButton)
            self.settle()
            self.assertTrue(heading.body.isVisible())
            self.assertEqual(heading.button.arrowType(), Qt.DownArrow)
            self.assertGreater(cards[key].sizeHint().height(), closed)
            heading.button.click()
            self.settle()
            self.assertEqual(cards[key].sizeHint().height(), closed)
            self.assertLess(cards[key].height(), closed + 3)
        for heading in self.view.section_headings.values():
            heading.button.click()
        self.settle()
        self.assertTrue(all(h.body.isVisible() for h in self.view.section_headings.values()))
        self.assertTrue(self.view.personal_card.isVisible())
        self.assertTrue(self.view.recent_section.isVisible())
        self.assertEqual(positions, (self.view.columns.getItemPosition(0), self.view.columns.getItemPosition(1)))
        self.assertEqual(parents, {k: card.parentWidget() for k, card in cards.items()})
        self.assertEqual((self.view.columns.columnStretch(0), self.view.columns.columnStretch(1)), (2, 3))

    def test_page_switch_and_new_view_restore_without_writing(self):
        self.view.section_headings['system'].button.click()
        self.view.section_headings['cargo'].button.click()
        self.view.section_headings['actions'].button.click()
        self.view.section_headings['actions'].button.click()
        expected = {'system': True, 'actions': False, 'cargo': True}
        for name in ('Navigation', 'Explorer', 'Other'):
            page = QWidget(objectName=name)
            self.stack.addWidget(page)
            self.stack.setCurrentWidget(page)
            self.stack.setCurrentWidget(self.view)
            self.settle()
            self.assertEqual({k: h.button.isChecked() for k, h in self.view.section_headings.items()}, expected)
        self.stack.close()
        settings = QSettings(self.path, QSettings.IniFormat)
        for k, value in expected.items():
            self.assertEqual(settings.value('pp2/sections/' + k + '_expanded', type=bool), value)
        self.state.settings = settings
        before = Path(self.path).read_bytes()
        with patch.object(settings, 'setValue', wraps=settings.setValue) as write:
            restored = PowerplayView(self.state)
            self.addCleanup(restored.deleteLater)
            self.assertEqual({k: h.button.isChecked() for k, h in restored.section_headings.items()}, expected)
            write.assert_not_called()
        self.assertEqual(Path(self.path).read_bytes(), before)
        restart = subprocess.run([sys.executable, '-B', '-c', '''
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from cmdrhelper.ui.powerplay_view import PowerplayView
from tests.test_powerplay import ViewState
app = QApplication([])
state = ViewState()
state.settings = QSettings(sys.argv[1], QSettings.IniFormat)
view = PowerplayView(state)
assert {k: h.button.isChecked() for k, h in view.section_headings.items()} == {
    'system': True, 'actions': False, 'cargo': True}
''', self.path], capture_output=True, text=True, timeout=15)
        self.assertEqual(restart.returncode, 0, restart.stderr)

    def test_closed_sections_receive_commander_system_and_cargo_updates(self):
        self.state.powerplay = PowerplayState()
        self.state.powerplay.apply(event('Powerplay', Power='Test Power', Rank=9, Merits=12345))
        self.state.powerplay.apply(event('FSDJump', StarSystem='New system',
            ControllingPower='Test Power', PowerplayState='Fortified', PowerplayStateReinforcement=4321))
        self.state.system = 'New system'
        self.state.ship_cargo_total = {'count': 0}
        self.state.changed.emit()
        self.state.cargoSnapshotChanged.emit({})
        self.assertIn('12.345', self.view.personal['merits'].text())
        self.assertIn('Kopfgeldjagd', self.view.actions.text())
        self.assertTrue(all(h.body.isHidden() for h in self.view.section_headings.values()))
        expected = (self.view.actions.text(), self.view.cargo.text(),
                    self.view.system_labels['system_name'].text())
        self.assertIn('4.321', self.view.system_presentation.strengths['reinforcement'].text())
        for heading in self.view.section_headings.values():
            heading.button.click()
        self.settle()
        self.assertEqual(expected, (self.view.actions.text(), self.view.cargo.text(),
                                   self.view.system_labels['system_name'].text()))
        self.assertIn('New system', expected[2])
        self.assertIn('Keine PP2-Artikel', expected[1])
        cargo_heading = self.view.section_headings['cargo']
        cargo_heading.button.click()
        self.state.powerplay.apply(event('PowerplayCollect', Power='Test Power',
            Type='testcargo', Type_Localised='Aktueller Artikel', Count=7))
        self.state.ship_cargo_total = {'count': 7}
        self.state.ship_inventory = {'inventory': [dict(frontier_name='testcargo',
            display_name='Aktueller Artikel', count=7)]}
        self.state.cargoSnapshotChanged.emit({})
        cargo_heading.button.setFocus()
        QTest.keyClick(cargo_heading.button, Qt.Key_Space)
        self.assertTrue(cargo_heading.button.isChecked())
        self.assertIn('Aktueller Artikel', self.view.cargo.text())
        self.assertIn('7', self.view.cargo.text())

    def test_collapsed_conflict_keeps_existing_spanning_position(self):
        self.state.powerplay.apply(event('FSDJump', StarSystem='Here',
            PowerplayState='Unoccupied', Powers=['Test Power', 'Other', 'Third']))
        self.state.changed.emit()
        self.settle()
        heading = self.view.section_headings['system']
        index = self.view.columns.indexOf(self.view.system_card)
        self.assertEqual(self.view.columns.getItemPosition(index), (1, 0, 1, 2))
        closed = self.view.system_card.height()
        heading.button.click()
        self.settle()
        self.assertGreater(self.view.system_card.height(), closed)
        heading.button.click()
        self.settle()
        self.assertEqual(self.view.system_card.height(), closed)
        self.assertEqual(self.view.columns.getItemPosition(index), (1, 0, 1, 2))
        self.assertTrue(self.view.recent_section.isVisible())

    def test_themes_languages_and_chronicle_docking(self):
        for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            for language in HELP_LANGUAGES:
                with self.subTest(language=language, theme=theme[:20]):
                    set_language(language)
                    view = PowerplayView(self.state)
                    view.setStyleSheet(theme)
                    view.resize(1200, 900)
                    view.show()
                    for heading in view.section_headings.values():
                        heading.button.setChecked(True)
                        heading.button.setChecked(False)
                        self.assertTrue(heading.label.text())
                        self.assertTrue(heading.body.isHidden())
                    self.settle()
                    self.assertTrue(view.personal_card.isVisible())
                    self.assertTrue(view.recent.isVisible())
                    self.assertEqual(view.horizontalScrollBar().maximum(), 0)
                    view.close()
                    view.deleteLater()
        self.view.detach_chronicle()
        self.assertTrue(self.view.recent.isVisible())
        self.view.chronicle_window.close()
        self.assertFalse(self.view.chronicle_detached)
        self.assertTrue(self.view.recent.isVisible())
