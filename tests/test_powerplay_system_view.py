"""Compact system display: exact journal facts, no inferred game mechanics."""
from copy import deepcopy
import unittest
from cmdrhelper.ui.powerplay_system import STAGES, STAGE_COLORS, SystemControlBar, marker_positions
from cmdrhelper import i18n
from PySide6.QtGui import QColor
from cmdrhelper.ui.styles import DARK_STYLESHEET,LIGHT_STYLESHEET
from tests import test_powerplay as base


class SystemViewTests(unittest.TestCase):
    setUpClass=classmethod(base.PowerplayViewTests.setUpClass.__func__)

    def setUp(self):
        base.PowerplayViewTests.setUp(self)
        self.state.system='Yama'
        self.state.powerplay.power='Nakato Kaine'
        self.state.powerplay.system=dict(StarSystem='Yama',ControllingPower='Nakato Kaine',
            PowerplayState='Stronghold',PowerplayStateControlProgress=.257749,
            PowerplayStateReinforcement=2207,PowerplayStateUndermining=1458)
        self.view.render()
        self.display=self.view.system_presentation

    def test_real_yama_and_underlying_values_unchanged(self):
        before=deepcopy(self.state.powerplay.system)
        self.view.render()
        self.assertEqual(self.state.powerplay.system,before)
        self.assertEqual(self.display.labels['system_name'].text(),'Yama')
        self.assertEqual(self.display.labels['status'].text(),'Hochburg')
        self.assertEqual(self.display.labels['owner'].text(),'Nakato Kaine')
        self.assertEqual(self.display.labels['relationship'].text(),'Eigene Macht')
        self.assertEqual(self.display.strengths['reinforcement'].text(),'2.207 CP')
        self.assertEqual(self.display.strengths['undermining'].text(),'1.458 CP')
        self.assertIn('0,257749',self.display.metrics.text())
        self.assertNotIn('%',self.display.metrics.text())
        self.assertIn('0.257749',self.display.metrics.toolTip())
        self.assertGreater(self.display.control_bar.yellow_position,self.display.control_bar.white_position)

    def test_stages_and_unknown_never_mapped_to_known(self):
        for status in (*STAGES,'FutureState',''):
            self.state.powerplay.system['PowerplayState']=status;self.view.render()
            white = self.display.control_bar.white_position
            if status in STAGES:
                index = STAGES.index(status)
                self.assertLessEqual(index/4, white)
                self.assertLessEqual(white, (index+1)/4)
            else:
                self.assertIsNone(white)
                self.assertIsNone(self.display.control_bar.yellow_position)
            if status not in STAGES:self.assertEqual(self.display.labels['status'].text(),'Unbekannt')
            self.assertTrue(self.display.labels['status'].toolTip())
        self.state.powerplay.system['PowerplayState']='POWERPLAY_STATE_UNOCCUPIED';self.view.render()
        self.assertEqual(self.display.labels['status'].text(),'Nicht besetzt')

    def test_zero_missing_and_large_values(self):
        for reinforcement,undermining,balance in [(0,0,0),(2207,0,1),(0,1458,-1),(None,1458,None),(2207,None,None),(None,None,None)]:
            self.state.powerplay.system.update(PowerplayStateReinforcement=reinforcement,PowerplayStateUndermining=undermining)
            self.view.render()
            bar = self.display.control_bar
            if balance is not None:
                delta = bar.yellow_position-bar.white_position
                self.assertEqual((delta > 0)-(delta < 0), (balance > 0)-(balance < 0))
            for key,value in [('reinforcement',reinforcement),('undermining',undermining)]:
                if value is None:self.assertEqual(self.display.strengths[key].text(),'Unbekannt')
                if value==0:self.assertEqual(self.display.strengths[key].text(),'0 CP')
        self.state.powerplay.system.update(PowerplayStateReinforcement=9223372036854775807,PowerplayStateUndermining=9223372036854775807)
        self.view.render()
        self.assertEqual(self.display.strengths['reinforcement'].text(),'9.223.372.036.854.775.807 CP')
        self.assertEqual(self.display.control_bar.white_position,self.display.control_bar.yellow_position)

    def test_invalid_cp_values_show_unknown_without_mutating_snapshot(self):
        for value in (-1, True, '64', float('inf'), float('nan'), 2**80):
            self.state.powerplay.system.update(PowerplayStateReinforcement=value,
                                              PowerplayStateUndermining=value)
            self.view.render()
            for widget in self.display.strengths.values():
                self.assertEqual(widget.text(), 'Unbekannt')
            self.assertIsNotNone(self.display.control_bar.yellow_position)

    def test_opponent_keeps_raw_value_roles_and_tooltips(self):
        self.state.powerplay.system['ControllingPower']='Edmund Mahon';self.view.render()
        self.assertEqual(self.display.labels['relationship'].text(),'Gegnerische Macht')
        self.assertEqual(self.display.strengths['reinforcement'].text(),'2.207 CP')
        self.assertEqual(self.display.strengths['undermining'].text(),'1.458 CP')
        self.assertIn('kontrollierenden Macht',self.display.strengths['reinforcement'].toolTip())
        self.assertIn('Reinforcement',self.display.strengths['reinforcement'].toolTip())
        self.assertIn('Undermining',self.display.strengths['undermining'].toolTip())
        self.assertIn('keine Prozentumrechnung',self.display.metrics.toolTip())
        self.assertIn('Näherungen', self.display.control_bar.toolTip())

    def test_unoccupied_conflict_values_are_preserved(self):
        self.state.powerplay.system.update(PowerplayState='Unoccupied',PowerplayConflictProgress=[dict(Power='Nakato Kaine',ConflictProgress=.25)])
        self.view.render()
        self.assertEqual(self.display.conflict_rows[0].power, 'Nakato Kaine')
        self.assertIn('0,25', self.display.conflict_rows[0].value.text())

    def test_responsive_themes_and_stale_system(self):
        for theme in (DARK_STYLESHEET,LIGHT_STYLESHEET):
            self.view.setStyleSheet(theme)
            for width in (1200,480,360):
                self.view.resize(width,1000);self.app.processEvents()
                self.assertEqual(self.view.horizontalScrollBar().maximum(),0)
                self.assertGreater(self.display.control_bar.width(), 0)
        self.state.system='Next';self.view.render()
        self.assertEqual(self.display.labels['status'].text(),'Unbekannt')
        self.assertEqual(self.display.strengths['reinforcement'].text(),'Unbekannt')
        self.assertIsNone(self.display.control_bar.white_position)
        self.assertIsNone(self.display.control_bar.yellow_position)


class ControlBarTests(unittest.TestCase):
    setUpClass = classmethod(base.PowerplayViewTests.setUpClass.__func__)

    def test_reference_cases_keep_direction_and_stage(self):
        cases = [('stronghold', .555674, 152249, 40375, 1),
                 ('exploited', .456767, 64, 6595, -1),
                 ('fortified', .212125, 73681, 0, 1)]
        for status, p, r, u, direction in cases:
            with self.subTest(status=status):
                white, yellow = marker_positions(status, p, r, u)
                lo = STAGES.index(status)/4
                self.assertTrue(lo <= white <= lo+.25)
                self.assertTrue(lo <= yellow <= lo+.25)
                self.assertEqual((yellow > white)-(yellow < white), direction)

    def test_missing_invalid_and_extreme_values(self):
        for status in STAGES:
            for p in (None, '0.5', True, float('nan'), float('inf'), -float('inf'), 2**80):
                with self.subTest(status=status, progress=p):
                    white, yellow = marker_positions(status, p, 5, 2)
                    self.assertIsNotNone(white)
                    self.assertIsNone(yellow)
            for p in (-1e308, -1, 0, .5, 1, 1.5, 12.617802, 1e308):
                for r, u in ((0,0), (5,2), (2,5), (5,5), (None,2), (-1,0),
                             ('bad',0), (True,0), (float('nan'),1), (1e308,0)):
                    white, yellow = marker_positions(status, p, r, u)
                    self.assertTrue(0 <= white <= 1)
                    if status == 'unoccupied':
                        self.assertIsNone(yellow)
                    else:
                        self.assertTrue(0 <= yellow <= 1)
        self.assertEqual(marker_positions('unknown', .5, 1, 0), (None,None))
        self.assertEqual(marker_positions('exploited', 0, 0, 0), (.25,.25))
        self.assertEqual(marker_positions('stronghold', 12.617802, 0, 0), (1,1))
        self.assertEqual(marker_positions('exploited', -1e308, 0, 0), (.25,0))
        white, yellow = marker_positions('stronghold', 12.617802, 12844156, 476354)
        self.assertAlmostEqual(white, .8125)
        self.assertEqual(yellow, 1)

    def test_all_languages_themes_widths_and_painted_regions(self):
        self.addCleanup(i18n.set_language, 'de')
        bar = SystemControlBar()
        self.addCleanup(bar.close)
        bar.show()
        for language in i18n._TRANSLATIONS:
            i18n.set_language(language)
            for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                bar.setStyleSheet(theme)
                bar.set_values('fortified', .212125, 73681, 0)
                self.assertEqual(bar.stage_names, [i18n.tr('pp2.status.'+s) for s in STAGES])
                self.assertEqual(bar.legend_names, [i18n.tr('pp2.system.status_marker'),
                                                    i18n.tr('pp2.system.cycle_marker')])
                for width in (40, 180, 280, 480, 1200):
                    with self.subTest(language=language, width=width, theme=theme[:20]):
                        bar.resize(width, bar.height())
                        self.app.processEvents()
                        self.assertEqual(bar.width(), width)
                        self.assertEqual(bar.height(), bar.content_height(width))
                        left, span, segment = bar.geometry_for_width(width)
                        for position in (bar.white_position, bar.yellow_position):
                            x = left + span*position
                            self.assertTrue(0 <= x <= width)
                        # Actual offscreen rendering, never saved as an image file.
                        image = bar.grab().toImage()
                        self.assertFalse(image.isNull())
                        scale = image.devicePixelRatio()
                        for index, color in enumerate(STAGE_COLORS):
                            x = round((left+(index+.5)*segment)*scale)
                            self.assertEqual(image.pixelColor(x, round(24*scale)).name(), QColor(color).name())

    def test_edge_markers_stay_inside_widget(self):
        bar = SystemControlBar()
        self.addCleanup(bar.close)
        for width in (1, 8, 40, 360):
            bar.resize(width, bar.height())
            for status, p in (('exploited', -1e308), ('stronghold', 1e308)):
                bar.set_values(status, p, 0, 0)
                left, span, _ = bar.geometry_for_width(width)
                radius = min(7., max(0., left-2))
                for position in (bar.white_position, bar.yellow_position):
                    x = left+span*position
                    self.assertGreaterEqual(x-radius, 0)
                    self.assertLessEqual(x+radius, width)
                self.assertFalse(bar.grab().isNull())
