"""Unoccupied journal evidence, compact rendering and snapshot transitions."""
from copy import deepcopy
import unittest
from unittest.mock import patch
from PySide6.QtCore import QEvent, QLocale, QPoint
from PySide6.QtGui import QHelpEvent, QPalette, QColor
from cmdrhelper import i18n
from cmdrhelper.powerplay import PowerplayState
from cmdrhelper.ui.powerplay_system import (
    conflict_participants, approximate_conflict_cp, SystemPresentation, ConflictRow,
    CONFLICT_MARKERS, conflict_marker_x,
)
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
    def test_empirical_cp_examples_and_invalid_values(self):
        for progress, cp in ((.082367, 9884), (.342333, 41080),
                             (.267450, 32094), (.213492, 25619), (0, 0), (1.5, 180000)):
            self.assertEqual(approximate_conflict_cp(progress), cp)
        for value in (None, True, '0.2', -1, float('nan'), float('inf'), 1e308):
            self.assertIsNone(approximate_conflict_cp(value))

    def test_aliases_are_one_participant_and_disagreement_is_unknown(self):
        data = dict(Powers=['A. Lavigny-Duval', 'Arissa Lavigny-Duval'],
                    PowerplayConflictProgress=[dict(Power='Arissa Lavigny-Duval', ConflictProgress=.2)])
        self.assertEqual(conflict_participants(data), [('A. Lavigny-Duval', .2)])
        data['PowerplayConflictProgress'].append(dict(Power='A. Lavigny-Duval', ConflictProgress=.3))
        self.assertEqual(conflict_participants(data), [('A. Lavigny-Duval', None)])

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
            self.assertEqual(row.cp.text(), '≈ ' + QLocale('de').toString(approximate_conflict_cp(row.progress)) + ' CP')
            self.assertEqual(row.bar.value(), round(row.progress / 1.5 * 10000))
            self.assertIn(repr(row.progress), row.cp.toolTip())
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
        self.state.powerplay.power = 'Arissa Lavigny-Duval'
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
                        self.assertEqual(display.own_power_row.value.text(), i18n.tr('pp2.conflict.no_presence'))
                        self.assertTrue(display.own_power_row.bar.isHidden())
                        self.assertEqual(display.own_power_row.portrait.key, 'arissa_lavigny_duval')
                        for row in display.conflict_rows:
                            self.assertGreater(row.bar.width(), 0)
                            self.assertLessEqual(row.geometry().right(), display.conflicts.width())
                            self.assertTrue(row.cp.text().startswith('≈ '))
                            self.assertIn(repr(row.progress), row.bar.toolTip())
                        self.assertFalse(display.grab().isNull())  # In memory only.

    def test_theme_contrast_and_painted_bar(self):
        for theme, dark in ((DARK_STYLESHEET, True), (LIGHT_STYLESHEET, False)):
            self.view.setStyleSheet(theme)
            display = self.render_event(dict(REAL, Powers=['Edmund Mahon', 'Aisling Duval'],
                PowerplayConflictProgress=[dict(Power=p, ConflictProgress=.25)
                                           for p in ('Edmund Mahon', 'Aisling Duval')]))
            self.view.resize(1400, 1000)
            for _ in range(3):
                self.app.processEvents()
            for row in display.conflict_rows:
                if row.power == 'Edmund Mahon':
                    lightness = row.name.palette().color(QPalette.WindowText).lightness()
                    self.assertGreater(lightness, 128) if dark else self.assertLess(lightness, 128)
                else:
                    image = row.bar.grab().toImage()
                    self.assertEqual(image.pixelColor(image.width() // 8, image.height() // 2),
                                     QColor('#00b9ef'))
                    self.assertEqual(image.pixelColor(image.width() * 3 // 4, image.height() // 2),
                                     QColor('#101820'))
                pixmap = row.portrait.pixmap()
                self.assertAlmostEqual(pixmap.width() / pixmap.height(), .75, delta=.03)
                self.assertGreater(row.thresholds.y(), row.bar.geometry().bottom())
                self.assertGreater(row.value.y(), row.thresholds.geometry().bottom())

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
                               lambda v: locale.toString(v) if type(v) is int else locale.toString(v, 'g', 7))
                for width in (240, 300, 360):
                    display.resize(width, max(display.sizeHint().height(), display.heightForWidth(width)))
                    self.app.processEvents()
                    with self.subTest(language=language, width=width):
                        self.assertEqual(display.width(), width)
                        for row in display.conflict_rows:
                            for text in (row.name, row.cp, row.value, row.thresholds):
                                self.assertGreater(text.width(), 0)
                                self.assertGreaterEqual(text.height(), text.heightForWidth(text.width()))
                            self.assertLessEqual(row.geometry().right(), width)
                        self.assertFalse(display.grab().isNull())

    def test_reference_alternatives_and_commander_changes(self):
        self.state.powerplay.power = 'Nakato Kaine'
        first = base.event('FSDJump', StarSystem='HIP 64726', PowerplayState='Unoccupied',
                           Powers=['Edmund Mahon'], PowerplayConflictProgress=[
                               dict(Power='Edmund Mahon', ConflictProgress=.082367)])
        display = self.render_event(first)
        self.assertEqual([r.power for r in display.conflict_rows], ['Edmund Mahon'])
        self.assertEqual(display.conflict_rows[0].cp.text(), '≈ 9.884 CP')
        self.assertEqual(display.conflict_rows[0].bar.value(), 549)
        self.assertIsNone(display.conflict_rows[0].power_color)
        own = display.own_power_row
        self.assertEqual(own.power, 'Nakato Kaine')
        self.assertEqual(own.value.text(), 'Keine Präsenz')
        self.assertTrue(own.cp.isHidden())
        self.assertTrue(own.bar.isHidden())
        self.assertTrue(own.thresholds.isHidden())
        self.assertEqual(own.portrait.key, 'nakato_kaine')
        second = base.event('FSDJump', StarSystem='HIP 65963', PowerplayState='Unoccupied',
                            Powers=['Nakato Kaine'], PowerplayConflictProgress=[
                                dict(Power='Nakato Kaine', ConflictProgress=.213492)])
        self.render_event(second)
        self.assertEqual(len(display.conflict_rows), 1)
        self.assertEqual(display.conflict_rows[0].cp.text(), '≈ 25.619 CP')
        self.assertIsNone(display.own_power_row)
        self.state.powerplay.power = 'Edmund Mahon'
        self.view.render()
        self.assertEqual(display.own_power_row.power, 'Edmund Mahon')
        self.state.powerplay.power = ''
        self.view.render()
        self.assertIsNone(display.own_power_row)
        self.assertIn('06.10.26', self.view.observed.text())
        self.state.powerplay.power = 'A. Lavigny-Duval'
        self.render_event(dict(second, Powers=['Arissa Lavigny-Duval'],
                               PowerplayConflictProgress=[]))
        self.assertIsNone(display.own_power_row)
        self.assertEqual(display.conflict_rows[0].cp.text(), i18n.tr('pp2.conflict.cp_unavailable'))

    def test_provisional_scale_examples(self):
        for cp, fill in ((0, 0), (34037, 1891), (35223, 1957),
                         (36000, 2000), (45148, 2508), (2894, 161), (25619, 1423), (41080, 2282),
                         (120000, 6667), (122512, 6806), (180000, 10000),
                         (240000, 10000)):
            with self.subTest(cp=cp):
                row = ConflictRow('Nakato Kaine', cp / 120000, str)
                self.addCleanup(row.close)
                self.assertEqual(row.cp_value, cp)
                self.assertEqual(row.bar.value(), fill)
        display = self.render_event(dict(REAL, StarSystem='Col 285 Sector GS-I c10-5',
            Powers=['Nakato Kaine'], PowerplayConflictProgress=[
                dict(Power='Nakato Kaine', ConflictProgress=1.020933)]))
        self.assertEqual(display.conflict_rows[0].cp_value, 122512)
        self.assertEqual(display.conflict_rows[0].bar.value(), 6806)

    def test_cp_boundaries_and_reference_sides(self):
        fractions = {key: fraction for key, fraction, _ in CONFLICT_MARKERS}
        self.assertEqual(fractions['boundary'], .2)
        self.assertAlmostEqual(fractions['minimum'], 2 / 3)
        for cp, key, side in ((34037, 'boundary', -1), (35223, 'boundary', -1),
                              (36000, 'boundary', 0), (45148, 'boundary', 1),
                              (120000, 'minimum', 0), (122512, 'minimum', 1)):
            with self.subTest(cp=cp):
                row = ConflictRow('Nakato Kaine', cp / 120000, str)
                self.addCleanup(row.close)
                delta = row.bar.value() / row.bar.maximum() - fractions[key]
                if side == 0:
                    # QProgressBar resolves the fill to 0.01 percentage points.
                    self.assertAlmostEqual(delta, 0, delta=.00005)
                else:
                    self.assertEqual(1 if delta > 0 else -1, side)
                self.assertEqual(row.cp_value, cp)

    def test_reference_fill_extends_beyond_minimum_marker(self):
        minimum = dict((key, fraction) for key, fraction, _ in CONFLICT_MARKERS)['minimum']
        self.assertAlmostEqual(minimum, 2 / 3)
        for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            row = ConflictRow('Nakato Kaine', 1.020933, str)
            self.addCleanup(row.close)
            row.setStyleSheet(row.styleSheet() + theme)
            row.show()
            for width in (360, 900):
                row.resize(width, row.sizeHint().height())
                self.app.processEvents()
                image = row.bar.grab().toImage()
                # Sample between the minimum and fill end, clear of the white marker.
                x = int(image.width() * .675)
                self.assertEqual(image.pixelColor(x, image.height() // 2), QColor('#a6ff00'))
                self.assertEqual(image.pixelColor(round(image.width() * .72), image.height() // 2),
                                 QColor('#101820'))
                self.assertGreater(row.bar.value() / row.bar.maximum(), minimum)
                self.assertEqual(row.cp_value, 122512)

    def test_progress_is_absolute_clipped_and_independent_of_merits(self):
        self.state.powerplay.power = 'Nakato Kaine'
        source = dict(REAL, PowerplayConflictProgress=[
            dict(Power='Nakato Kaine', ConflictProgress=1.25),
            dict(Power='Aisling Duval', ConflictProgress=.25)])
        display = self.render_event(source)
        before = [(r.power, r.cp.text(), r.bar.value()) for r in display.conflict_rows]
        self.assertEqual(display.conflict_rows[0].bar.value(), 8333)
        self.assertEqual(display.conflict_rows[0].cp_value, 150000)
        self.assertEqual(display.conflict_rows[1].bar.value(), 1667)
        self.state.powerplay.merits = 987654321
        self.view.render()
        self.assertEqual(before, [(r.power, r.cp.text(), r.bar.value()) for r in display.conflict_rows])
        for value in (None, -1, float('nan'), float('inf'), '0.2', True):
            display = self.render_event(dict(REAL, Powers=['Nakato Kaine'],
                PowerplayConflictProgress=[dict(Power='Nakato Kaine', ConflictProgress=value)]))
            row = display.conflict_rows[0]
            self.assertIsNone(row.cp_value)
            self.assertEqual(row.bar.value(), 0)
            self.assertEqual(row.cp.text(), i18n.tr('pp2.conflict.cp_unavailable'))

    def test_long_names_and_threshold_markers_all_languages_themes(self):
        self.addCleanup(i18n.set_language, 'de')
        for language in i18n._TRANSLATIONS:
            i18n.set_language(language)
            for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                row = ConflictRow('A very long power name ' * 6, .342333,
                                  lambda v: QLocale(language).toString(v))
                row.setStyleSheet(row.styleSheet() + theme)
                row.show()
                try:
                    for width in (240, 360, 480, 900, 240):
                        row.resize(width, row.sizeHint().height())
                        for _ in range(3):
                            self.app.processEvents()
                        row.resize(width, max(row.sizeHint().height(), row.heightForWidth(width)))
                        self.app.processEvents()
                        with self.subTest(language=language, width=width):
                            self.assertEqual(row.width(), width)
                            for text in (row.name, row.cp, row.value, row.thresholds):
                                self.assertGreaterEqual(text.height(), text.heightForWidth(text.width()))
                            self.assertEqual(row.bar.width(), row.thresholds.width())
                            self.assertEqual(row.bar.x(), row.thresholds.x())
                            for (key, fraction, _), icon, caption in zip(
                                    CONFLICT_MARKERS, row.thresholds.symbols, row.thresholds.captions):
                                self.assertEqual(caption.text(), i18n.tr('pp2.conflict.' + key))
                                self.assertEqual(icon.toolTip(), i18n.tr('pp2.conflict.' + key + '_help'))
                                self.assertEqual(caption.toolTip(), icon.toolTip())
                                self.assertTrue(row.thresholds.rect().contains(icon.geometry()))
                                self.assertAlmostEqual(icon.geometry().center().x(),
                                    fraction * (row.bar.width() - 1), delta=2)
                                if not caption.isHidden():
                                    self.assertGreaterEqual(caption.width(), caption.sizeHint().width())
                                    self.assertTrue(row.thresholds.rect().contains(caption.geometry()))
                            if width == 240:
                                self.assertTrue(row.thresholds.compact)
                            self.assertFalse(row.thresholds.symbols[0].geometry().intersects(
                                row.thresholds.symbols[1].geometry()))
                            self.assertLessEqual(row.value.geometry().bottom(), row.height())
                            self.assertFalse(row.grab().isNull())
                finally:
                    row.close()

    def test_painted_positions_and_line_tooltips_without_changing_fill(self):
        self.assertEqual([fraction for _, fraction, _ in CONFLICT_MARKERS], [36000 / 180000, 120000 / 180000])
        for width in (120, 240, 480, 900):
            row = ConflictRow('Unknown', .5, str)
            self.addCleanup(row.close)
            row.resize(width + 100, row.sizeHint().height())
            row.show()
            self.app.processEvents()
            width = row.bar.width()
            image = row.bar.grab().toImage()
            self.assertEqual(row.bar.value(), 3333)
            self.assertEqual(row.cp_value, 60000)
            for key, fraction, _ in CONFLICT_MARKERS:
                x = conflict_marker_x(width, fraction)
                self.assertAlmostEqual(x / (width - 1), fraction)
                # Verify actual white painted dashes rather than just the formula.
                colors = [image.pixelColor(px, y) for px in range(round(x)-1, round(x)+2)
                          for y in range(2, 22)]
                self.assertTrue(any(min(c.red(), c.green(), c.blue()) > 200 for c in colors))
                point = QPoint(round(x), 10)
                event = QHelpEvent(QEvent.ToolTip, point, row.bar.mapToGlobal(point))
                with patch('cmdrhelper.ui.powerplay_system.QToolTip.showText') as show:
                    self.app.sendEvent(row.bar, event)
                    self.assertEqual(show.call_args.args[1], i18n.tr('pp2.conflict.' + key + '_help'))

    def test_zero_missing_and_overfull_have_same_visual_markers(self):
        for progress, fill, cp in ((None, 0, None), (0, 0, 0), (1.25, 8333, 150000), (2, 10000, 240000)):
            row = ConflictRow('Unknown', progress, str)
            self.addCleanup(row.close)
            row.show()
            self.app.processEvents()
            self.assertEqual(row.bar.value(), fill)
            self.assertEqual(row.cp_value, cp)
            image = row.bar.grab().toImage()
            for _, fraction, _ in CONFLICT_MARKERS:
                x = round(conflict_marker_x(image.width(), fraction))
                colors = [image.pixelColor(px, y) for px in range(x - 1, x + 2)
                          for y in range(2, 22)]
                self.assertTrue(any(min(c.red(), c.green(), c.blue()) > 200 for c in colors))
            self.assertTrue(row.thresholds.isVisible())
            self.assertTrue(all(icon.isVisible() for icon in row.thresholds.symbols))
