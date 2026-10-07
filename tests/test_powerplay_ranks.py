"""Rank configuration copied from the local German PP2 cache, 2026-10-06."""
import json
from pathlib import Path
import struct
import unittest
from cmdrhelper.powerplay import _crypt, decode_powers_cache


def rank_document():
    return json.loads((Path(__file__).parent/'fixtures/powerplay_ranks_20261006.json').read_text())


def encoded(document):
    payload=json.dumps(document).encode()
    header=struct.pack('<IBH',3,1,6)+b'german'
    header+=struct.pack('<H',14)+b'api.orerve.net'+struct.pack('<HHI',0,65535,len(payload))
    return _crypt(header+payload)


class RankCacheTests(unittest.TestCase):
    def test_real_root_thresholds_are_not_power_fields(self):
        doc=rank_document()
        powers=decode_powers_cache(encoded(doc))
        self.assertEqual(powers.rank_thresholds,dict(rankTwo=2000,rankThree=3000,rankFour=4000,rankFive=6000,aboveRankFive=8000))
        self.assertNotIn('rankThresholds',powers['Nakato Kaine'])
        self.assertEqual(powers['Nakato Kaine']['perks'],doc['powers'][0]['perks'])

    def test_missing_rank_config_preserves_other_power_features(self):
        doc=rank_document();del doc['rankThresholds']
        powers=decode_powers_cache(encoded(doc))
        self.assertIsNone(powers.rank_thresholds)
        self.assertIn('Edmund Mahon',powers)


class RankProgressTests(unittest.TestCase):
    def setUp(self):
        from cmdrhelper.powerplay_rank import rank_progress
        self.calculate=rank_progress
        self.powers=decode_powers_cache(encoded(rank_document()))

    def progress(self,merits,rank=None,power='Nakato Kaine'):
        return self.calculate(power,rank,merits,self.powers)

    def test_cumulative_early_thresholds_and_rank_zero(self):
        for total,rank,lower,upper in [(0,1,0,2000),(1999,1,0,2000),(2000,2,2000,5000),
                (5000,3,5000,9000),(9000,4,9000,15000),(15000,5,15000,23000),(23000,6,23000,31000)]:
            p=self.progress(total,rank)
            self.assertEqual((p.calculated,p.lower,p.upper,p.status),(rank,lower,upper,'confirmed'))
        fresh=self.progress(0,0)
        self.assertEqual((fresh.confirmed,fresh.calculated,fresh.needed,fresh.status),(0,1,2000,'pending'))

    def test_real_rank_five_and_progress(self):
        p=self.progress(16726,5)
        self.assertEqual((p.confirmed,p.calculated,p.lower,p.upper,p.needed,p.earned,p.span,p.status),
                         (5,5,15000,23000,6274,1726,8000,'confirmed'))
        self.assertAlmostEqual(p.earned/p.span*100,21.575)

    def test_pending_confirmed_and_contradictory_rank(self):
        p=self.progress(13336,0)
        self.assertEqual((p.confirmed,p.calculated,p.needed,p.status),(0,4,1664,'pending'))
        self.assertEqual(self.progress(16726,0).status,'pending')
        self.assertEqual(self.progress(16726,5).status,'confirmed')
        self.assertEqual(self.progress(16726,6).status,'conflict')
        self.assertEqual(self.progress(16726).status,'unconfirmed')

    def test_high_ranks_continue_after_100_without_finite_maximum(self):
        for rank,total in [(97,751000),(98,759000),(99,767000),(100,775000),(101,783000),(102,791000)]:
            p=self.progress(total,rank)
            self.assertEqual((p.calculated,p.lower,p.upper,p.earned),(rank,total,total+8000,0))
            self.assertEqual(p.status,'confirmed' if rank<=100 else 'beyond100')
        self.assertEqual(self.progress(783000,100).status,'pending')
        self.assertIsNotNone(self.progress(2**63-1,100))

    def test_actual_cache_values_drive_calculation(self):
        self.powers.rank_thresholds=dict(rankTwo=100,rankThree=200,rankFour=300,rankFive=400,aboveRankFive=500)
        p=self.progress(1200,5)
        self.assertEqual((p.lower,p.upper,p.needed),(1000,1500,300))

    def test_invalid_missing_cache_and_merits(self):
        for powers in (None,{}, {'Nakato Kaine':{}}):
            self.assertIsNone(self.calculate('Nakato Kaine',5,16726,powers))
        for bad in (None,{},[],dict(rankTwo=2000),dict(self.powers.rank_thresholds,aboveRankFive=0),
                    dict(self.powers.rank_thresholds,rankTwo=True),dict(self.powers.rank_thresholds,rankFive=-1)):
            powers=decode_powers_cache(encoded(rank_document()));powers.rank_thresholds=bad
            self.assertIsNone(self.calculate('Nakato Kaine',5,16726,powers))
        for total in (None,True,-1,1.5):self.assertIsNone(self.progress(total,5))
        self.assertIsNone(self.progress(16726,5,'Missing power'))

    def test_power_change_and_totalmerits_never_summed(self):
        from cmdrhelper.powerplay import PowerplayState
        s=PowerplayState()
        s.apply(dict(event='PowerplayRank',Power='Nakato Kaine',Rank=5))
        for gained,total in [(3600,16726),(99999,16727),(1,16700)]:
            s.apply(dict(event='PowerplayMerits',Power='Nakato Kaine',MeritsGained=gained,TotalMerits=total))
            self.assertEqual(self.progress(s.merits,s.rank).earned,total-15000)
        s.apply(dict(event='PowerplayDefect',Power='Edmund Mahon'))
        self.assertIsNone(self.calculate(s.power,s.rank,s.merits,self.powers))
        s.apply(dict(event='PowerplayRank',Power='Edmund Mahon',Rank=2))
        s.apply(dict(event='PowerplayMerits',Power='Edmund Mahon',MeritsGained=10,TotalMerits=2100))
        p=self.calculate(s.power,s.rank,s.merits,self.powers)
        self.assertEqual((p.confirmed,p.calculated,p.needed),(2,2,2900))


class RankViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        from unittest.mock import patch
        from tests.test_powerplay import ViewState
        from cmdrhelper.ui.powerplay_view import PowerplayView
        from cmdrhelper.i18n import set_language
        from cmdrhelper.powerplay import PowerplayState
        set_language('de')
        self.state=ViewState();self.state.powerplay=PowerplayState()
        self.state.powerplay.apply(dict(event='PowerplayRank',Power='Nakato Kaine',Rank=0))
        self.state.powerplay.apply(dict(event='PowerplayMerits',Power='Nakato Kaine',TotalMerits=13336,MeritsGained=1))
        self.view=PowerplayView(self.state)
        self.view.resize(1200,900);self.view.show();self.addCleanup(self.view.close)
        self.powers=decode_powers_cache(encoded(rank_document()))
        loader=patch.object(self.view.cache,'load',return_value=self.powers)
        self.loader=loader.start();self.addCleanup(loader.stop)
        self.view.render()

    def test_pending_rank_remains_zero_until_elite_confirms(self):
        self.assertEqual(self.view.personal['rank'].text(),'0')
        self.assertIn('Rang 4',self.view.rank_summary.text())
        self.assertIn('ausstehend',self.view.rank_summary.text())
        self.assertTrue(self.view.rank_bar.isHidden())
        self.state.powerplay.apply(dict(event='PowerplayMerits',Power='Nakato Kaine',TotalMerits=16726,MeritsGained=99999))
        self.state.changed.emit()
        self.assertEqual(self.view.personal['rank'].text(),'0')
        self.state.powerplay.apply(dict(event='PowerplayRank',Power='Nakato Kaine',Rank=5))
        self.state.changed.emit()
        self.assertEqual(self.view.personal['rank'].text(),'5')
        self.assertEqual(self.view.personal['merits'].text(),'16.726')
        self.assertIn('6 bei 23.000',self.view.rank_summary.text())
        self.assertIn('6.274',self.view.rank_summary.text())
        self.assertNotIn('ausstehend',self.view.rank_summary.text())
        self.assertFalse(self.view.rank_bar.isHidden())
        self.assertIn('21,6 %',self.view.rank_bar.format())
        self.assertIn('1.726 / 8.000',self.view.rank_bar.toolTip())
        self.assertNotIn('controlled_rebuy',self.view.rank_summary.text())

    def test_missing_cache_conflict_and_power_switch_clear_progress(self):
        self.state.powerplay.rank=6;self.state.powerplay.merits=16726
        self.view.render()
        self.assertIn('widersprechen',self.view.rank_summary.text())
        self.assertEqual(self.view.personal['rank'].text(),'6')
        self.assertTrue(self.view.rank_bar.isHidden())
        self.loader.return_value=None;self.view.render()
        self.assertIn('nicht verfügbar',self.view.rank_summary.text())
        self.assertNotIn('23.000',self.view.rank_summary.text())
        self.loader.return_value=self.powers
        self.state.powerplay.apply(dict(event='PowerplayDefect',Power='Edmund Mahon'))
        self.view.render()
        self.assertTrue(self.view.rank_bar.isHidden())
        self.assertIn('nicht verfügbar',self.view.rank_summary.text())

    def test_100_plus_without_invented_rank_number_or_maximum(self):
        self.state.powerplay.rank=100;self.state.powerplay.merits=775000
        self.view.render()
        self.assertIn('100+ bei 783.000',self.view.rank_summary.text())
        self.state.powerplay.merits=783000;self.view.render()
        self.assertEqual(self.view.personal['rank'].text(),'100')
        self.assertIn('100+',self.view.rank_summary.text())
        self.assertIn('791.000',self.view.rank_summary.text())
        self.assertNotIn('101',self.view.rank_summary.text())
        self.assertNotIn('Maximalrang',self.view.rank_summary.text())
        self.assertTrue(self.view.rank_bar.isHidden())

    def test_progress_remains_compact_in_both_themes(self):
        from cmdrhelper.ui.styles import DARK_STYLESHEET,LIGHT_STYLESHEET
        self.state.powerplay.rank=5;self.state.powerplay.merits=16726;self.view.render()
        for theme in (DARK_STYLESHEET,LIGHT_STYLESHEET):
            self.view.setStyleSheet(theme)
            for width in (1200,480,360):
                self.view.resize(width,900);self.app.processEvents()
                self.assertEqual(self.view.horizontalScrollBar().maximum(),0)
                self.assertLess(self.view.personal_card.height(),self.view.height()/3)
