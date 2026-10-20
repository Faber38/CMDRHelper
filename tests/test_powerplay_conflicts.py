"""Unoccupied journal evidence, compact rendering and snapshot transitions."""
from copy import deepcopy
import unittest
from PySide6.QtCore import QLocale
from cmdrhelper import i18n
from cmdrhelper.powerplay import PowerplayState
from cmdrhelper.ui.powerplay_system import conflict_participants, SystemPresentation
from cmdrhelper.ui.powerplay_portraits import portrait_key
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests import test_powerplay as base

# Read-only transcription of Khawathlang FSDJump, journal line 836.
REAL = dict(event='FSDJump', timestamp='2026-10-19T14:11:20Z',
            StarSystem='Khawathlang', SystemAddress=5069269444049,
            PowerplayState='Unoccupied',
            Powers=['Aisling Duval', 'Edmund Mahon', 'Yuri Grom', 'Zemina Torval', 'Nakato Kaine'],
            PowerplayConflictProgress=[dict(Power=p, ConflictProgress=v) for p,v in
                [('Aisling Duval', .267450), ('Edmund Mahon', .023333),
                 ('Yuri Grom', .003700), ('Zemina Torval', .002092), ('Nakato Kaine', .342333)]])


class ConflictDataTests(unittest.TestCase):
    def test_union_duplicates_invalid_and_stable_sort(self):
        data = dict(Powers=['Only', 'Zero', 'Missing', 'Same', 'Same', None],
                    PowerplayConflictProgress=[dict(Power=p, ConflictProgress=v) for p,v in
                        [('Zulu', .5), ('Alpha', .5), ('Same', .2), ('Same', .2),
                         ('Zero', 0), ('Missing', None), ('Bad', '0.4'), ('Bool', True),
                         ('Negative', -1), ('Nan', float('nan')), ('Inf', float('inf'))]])
        rows = conflict_participants(data)
        self.assertEqual(rows[:4], [('Alpha', .5), ('Zulu', .5), ('Same', .2), ('Zero', 0)])
        self.assertEqual(rows[4:], [(p, None) for p in ['Bad', 'Bool', 'Inf', 'Missing', 'Nan', 'Negative', 'Only']])
        data['PowerplayConflictProgress'].append(dict(Power='Same', ConflictProgress=.3))
        self.assertIsNone(dict(conflict_participants(data))['Same'])


class ConflictViewTests(unittest.TestCase):
    setUpClass = classmethod(base.PowerplayViewTests.setUpClass.__func__)
    setUp = base.PowerplayViewTests.setUp

    def render_event(self, event):
        self.state.system = event['StarSystem']
        self.state.powerplay.apply(event)
        self.view.render()
        return self.view.system_presentation

    def test_original_portraits_values_cp_and_snapshot_unchanged(self):
        before = deepcopy(REAL)
        display = self.render_event(REAL)
        self.assertEqual(display.labels['status'].text(), 'Nicht besetzt')
        self.assertTrue(display.controlled.isHidden())
        self.assertFalse(display.conflicts.isHidden())
        self.assertEqual([r.power for r in display.conflict_rows],
                         ['Nakato Kaine', 'Aisling Duval', 'Edmund Mahon', 'Yuri Grom', 'Zemina Torval'])
        expected = {e['Power']:e['ConflictProgress'] for e in REAL['PowerplayConflictProgress']}
        for row in display.conflict_rows:
            self.assertEqual(row.progress, expected[row.power])
            self.assertEqual(row.portrait.key, portrait_key(row.power))
            self.assertFalse(row.portrait.pixmap().isNull())
            self.assertIn(QLocale('de').toString(row.progress, 'g', 7), row.value.text())
            self.assertEqual(row.cp.text(), 'CP nicht verfügbar')
        self.assertEqual(display.conflict_rows[0].power_color, '#a6ff00')
        self.assertEqual(display.conflict_rows[1].power_color, '#00b9ef')
        self.assertIsNone(display.conflict_rows[2].power_color)
        self.assertEqual(REAL, before)

    def test_conflict_uses_central_arissa_alias(self):
        images = []
        for name in ('A. Lavigny-Duval', 'Arissa Lavigny-Duval'):
            display = self.render_event(dict(REAL, Powers=[name],
                PowerplayConflictProgress=[dict(Power=name, ConflictProgress=.2)]))
            row = display.conflict_rows[0]
            self.assertEqual(row.portrait.key, 'arissa_lavigny_duval')
            self.assertFalse(row.portrait.pixmap().isNull())
            images.append(row.portrait.pixmap().toImage())
        self.assertEqual(images[0], images[1])

    def test_single_missing_and_system_commander_changes(self):
        display = self.render_event(dict(REAL, Powers=['Only'], PowerplayConflictProgress=[]))
        self.assertEqual(len(display.conflict_rows), 1)
        self.assertIn('Unbekannt', display.conflict_rows[0].value.text())
        display = self.render_event(REAL)
        self.render_event(base.event('FSDJump', StarSystem='Next', PowerplayState='Exploited',
                                    ControllingPower='Other', PowerplayStateControlProgress=.2))
        self.assertTrue(display.conflicts.isHidden())
        self.assertEqual(display.conflict_rows, [])
        self.assertFalse(display.controlled.isHidden())
        self.assertNotIn('PowerplayConflictProgress', self.state.powerplay.system)
        self.render_event(REAL)
        self.assertEqual(len(display.conflict_rows), 5)
        self.render_event(base.event('FSDJump', StarSystem='Empty', PowerplayState='Unoccupied'))
        self.assertEqual(display.conflict_rows, [])
        self.render_event(REAL)
        self.state.powerplay = PowerplayState()  # Runtime reset on commander selection.
        self.state.system = ''
        self.view.render()
        self.assertEqual(display.conflict_rows, [])
        self.assertTrue(display.conflicts.isHidden())

    def test_twelve_languages_both_themes_narrow_window(self):
        self.addCleanup(i18n.set_language, 'de')
        for language in i18n._TRANSLATIONS:
            i18n.set_language(language)
            for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                self.view.setStyleSheet(theme)
                display = self.render_event(REAL)
                for width in (480, 1200):
                    self.view.resize(width, 1000)
                    self.app.processEvents()
                    with self.subTest(language=language, width=width):
                        self.assertEqual(self.view.horizontalScrollBar().maximum(), 0)
                        for row in display.conflict_rows:
                            self.assertGreater(row.bar.width(), 0)
                            self.assertLessEqual(row.geometry().right(), display.conflicts.width())
                            self.assertEqual(row.cp.text(), i18n.tr('pp2.conflict.cp_unavailable'))
                        self.assertFalse(display.grab().isNull())  # In memory only.

    def test_isolated_conflicts_wrap_at_narrow_width_in_all_languages(self):
        self.addCleanup(i18n.set_language, 'de')
        display = SystemPresentation()
        self.addCleanup(display.close)
        display.show()
        for language in i18n._TRANSLATIONS:
            i18n.set_language(language)
            locale = QLocale(language)
            for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                display.setStyleSheet(theme)
                display.render(REAL, 'Khawathlang', 'unoccupied',
                               lambda v: locale.toString(v, 'g', 7))
                for width in (240, 300, 360):
                    display.resize(width, max(display.sizeHint().height(), display.heightForWidth(width)))
                    self.app.processEvents()
                    with self.subTest(language=language, width=width):
                        self.assertEqual(display.width(), width)
                        for row in display.conflict_rows:
                            for text in (row.name, row.cp, row.value):
                                self.assertGreater(text.width(), 0)
                                self.assertGreaterEqual(text.height(), text.heightForWidth(text.width()))
                            self.assertLessEqual(row.geometry().right(), width)
                        self.assertFalse(display.grab().isNull())
