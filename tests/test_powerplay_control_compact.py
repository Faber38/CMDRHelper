"""Compact control graphic: real widget height, wrapping and unchanged state."""
from copy import deepcopy
import unittest
from PySide6.QtCore import QRect
from PySide6.QtGui import QFontMetrics
from cmdrhelper.help_content import HELP_LANGUAGES
from cmdrhelper.i18n import set_language
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests import test_powerplay_system_view as system_tests


class CompactControlTests(unittest.TestCase):
    setUpClass = classmethod(system_tests.SystemViewTests.setUpClass.__func__)
    setUp = system_tests.SystemViewTests.setUp

    @staticmethod
    def previous_height(bar, width):
        metrics = QFontMetrics(bar.font())
        def height(text, available):
            return metrics.boundingRect(QRect(0, 0, max(1, int(available)), 10000),
                                        bar.text_flags, text).height()
        _, span, segment = bar.geometry_for_width(width)
        return (64 + max(height(t, segment - 4) for t in bar.stage_names)
                + sum(max(18, height(t, span - 24)) for t in bar.legend_names))

    def test_height_and_wrapping_in_all_languages_and_themes(self):
        self.addCleanup(set_language, 'de')
        bar = self.display.control_bar
        for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.view.setStyleSheet(theme)
            for language in HELP_LANGUAGES:
                set_language(language)
                for status in ('Exploited', 'Fortified', 'Stronghold'):
                    self.state.powerplay.system['PowerplayState'] = status
                    self.view.render()
                    for width in (180, 280, 480, 1200):
                        with self.subTest(language=language, status=status, width=width):
                            # Test the graphic independently of the outer layout.
                            expected = bar.content_height(width)
                            previous = self.previous_height(bar, width)
                            self.assertLess(expected, previous)
                            if width == 1200:
                                self.assertAlmostEqual(expected / previous, .75, delta=.07)
                            _, span, segment = bar.geometry_for_width(width)
                            self.assertEqual(segment * 4, span)
                            captions = max(bar.text_height(t, segment - 3) for t in bar.stage_names)
                            # Caption bottom precedes the first legend; all rows fit.
                            bottom = 40.5 + captions + sum(
                                max(13.5, bar.text_height(t, span - 18)) for t in bar.legend_names)
                            self.assertLessEqual(bottom, expected)
                    self.assertEqual(bar.height(), bar.content_height(bar.width()))

    def test_reclaims_height_without_changing_other_elements(self):
        self.state.powerplay.system['ControllingPower'] = 'Edmund Mahon'
        self.view.render()
        for _ in range(4):
            self.app.processEvents()
        before = deepcopy(self.state.powerplay)
        bar = self.display.control_bar
        positions = (bar.white_position, bar.yellow_position)
        fonts = {key: value.font() for key, value in self.display.labels.items()}
        portrait = self.display.owner_portrait
        self.assertEqual((portrait.width(), portrait.height()), (42, 56))
        compact_height = bar.height()
        old_height = self.previous_height(bar, bar.width())
        self.assertLess(compact_height, old_height)
        # Layout size hints must reclaim the same space as the widget itself.
        compact_hint = self.display.sizeHint().height()
        bar.drawing_scale = 1.0
        self.addCleanup(setattr, bar, 'drawing_scale', .75)
        self.view.render()
        for _ in range(4):
            self.app.processEvents()
        old_hint = self.display.sizeHint().height()
        self.assertEqual(old_hint - compact_hint, old_height - compact_height)
        bar.drawing_scale = .75
        self.view.render()
        self.assertEqual(bar.height(), compact_height)
        heading = self.view.section_headings['system']
        heading.button.setChecked(False)
        self.view.render()
        heading.button.setChecked(True)
        self.assertEqual(bar.height(), compact_height)
        self.assertEqual((bar.white_position, bar.yellow_position), positions)
        self.assertEqual(self.state.powerplay, before)
        self.assertEqual(fonts, {key: value.font() for key, value in self.display.labels.items()})


if __name__ == '__main__':
    unittest.main()
