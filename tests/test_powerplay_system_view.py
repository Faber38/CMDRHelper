"""Compact system display: exact journal facts, no inferred game mechanics."""
from copy import deepcopy
import unittest
from cmdrhelper.ui.powerplay_system import STAGES
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
        self.assertEqual(self.display.strengths['reinforcement'].text(),'2.207')
        self.assertEqual(self.display.strengths['undermining'].text(),'1.458')
        self.assertIn('0,257749',self.display.metrics.text())
        self.assertNotIn('%',self.display.metrics.text())
        self.assertIn('0.257749',self.display.metrics.toolTip())
        self.assertGreater(self.display.contest.balance,0)

    def test_stages_and_unknown_never_mapped_to_known(self):
        for status in (*STAGES,'FutureState',''):
            self.state.powerplay.system['PowerplayState']=status;self.view.render()
            selected=[key for key,value in self.display.stages.items() if '▲' in value.text()]
            self.assertEqual(selected,[status] if status in STAGES else [])
            if status not in STAGES:self.assertEqual(self.display.labels['status'].text(),'Unbekannt')
            self.assertTrue(self.display.labels['status'].toolTip())
        self.state.powerplay.system['PowerplayState']='POWERPLAY_STATE_UNOCCUPIED';self.view.render()
        self.assertEqual(self.display.labels['status'].text(),'Nicht besetzt')

    def test_zero_missing_and_large_values(self):
        for reinforcement,undermining,balance in [(0,0,0),(2207,0,1),(0,1458,-1),(None,1458,None),(2207,None,None),(None,None,None)]:
            self.state.powerplay.system.update(PowerplayStateReinforcement=reinforcement,PowerplayStateUndermining=undermining)
            self.view.render()
            self.assertEqual(self.display.contest.balance,balance)
            for key,value in [('reinforcement',reinforcement),('undermining',undermining)]:
                if value is None:self.assertEqual(self.display.strengths[key].text(),'Unbekannt')
                if value==0:self.assertEqual(self.display.strengths[key].text(),'0')
        self.state.powerplay.system.update(PowerplayStateReinforcement=9223372036854775807,PowerplayStateUndermining=9223372036854775807)
        self.view.render()
        self.assertEqual(self.display.strengths['reinforcement'].text(),'9.223.372.036.854.775.807')
        self.assertEqual(self.display.contest.balance,0)

    def test_opponent_keeps_raw_value_roles_and_tooltips(self):
        self.state.powerplay.system['ControllingPower']='Edmund Mahon';self.view.render()
        self.assertEqual(self.display.labels['relationship'].text(),'Gegnerische Macht')
        self.assertEqual(self.display.strengths['reinforcement'].text(),'2.207')
        self.assertEqual(self.display.strengths['undermining'].text(),'1.458')
        self.assertIn('kontrollierenden Macht',self.display.strengths['reinforcement'].toolTip())
        self.assertIn('Reinforcement',self.display.strengths['reinforcement'].toolTip())
        self.assertIn('Undermining',self.display.strengths['undermining'].toolTip())
        self.assertIn('keine Prozentumrechnung',self.display.metrics.toolTip())
        self.assertTrue(all(s.toolTip() for s in self.display.stages.values()))

    def test_unoccupied_conflict_values_are_preserved(self):
        self.state.powerplay.system.update(PowerplayState='Unoccupied',PowerplayConflictProgress=[dict(Power='Nakato Kaine',ConflictProgress=.25)])
        self.view.render()
        self.assertIn('Nakato Kaine: 0,25',self.display.metrics.text())

    def test_responsive_themes_and_stale_system(self):
        for theme in (DARK_STYLESHEET,LIGHT_STYLESHEET):
            self.view.setStyleSheet(theme)
            for width in (1200,480,360):
                self.view.resize(width,1000);self.app.processEvents()
                self.assertEqual(self.view.horizontalScrollBar().maximum(),0)
                self.assertTrue(all(s.width()>0 for s in self.display.stages.values()))
        self.state.system='Next';self.view.render()
        self.assertEqual(self.display.labels['status'].text(),'Unbekannt')
        self.assertEqual(self.display.strengths['reinforcement'].text(),'Unbekannt')
        self.assertIsNone(self.display.contest.balance)
