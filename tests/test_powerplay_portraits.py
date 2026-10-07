"""Portrait layout and optional local assets; no game/database writes."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage
from cmdrhelper.ui.powerplay_portraits import PowerPortrait, portrait_key
from tests import test_powerplay_ranks as ranks


class PortraitViewTests(unittest.TestCase):
    setUpClass=classmethod(ranks.RankViewTests.setUpClass.__func__)
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        assets=patch('cmdrhelper.ui.powerplay_portraits.POWERPLAY_ASSET_DIR',Path(temporary.name))
        assets.start();self.addCleanup(assets.stop)
        ranks.RankViewTests.setUp(self)

    def ready_rank(self):
        self.state.powerplay.rank=5;self.state.powerplay.merits=16726
        self.view.render();self.app.processEvents()

    def test_placeholder_and_generic_power_keys(self):
        self.assertEqual(self.view.portrait.size().width(),84)
        self.assertEqual(self.view.portrait.size().height(),112)
        self.assertTrue(self.view.portrait.text())
        self.assertEqual(self.view.portrait.key,'nakato_kaine')
        self.state.powerplay.power='Edmund Mahon';self.view.render()
        self.assertEqual(self.view.portrait.key,'edmund_mahon')
        self.assertEqual(portrait_key('Li Yong-Rui'),'li_yong_rui')
        self.assertNotIn('/',portrait_key('../../Unknown Power'))
        self.assertEqual(portrait_key(''),'')

    def test_desktop_portrait_information_and_bounded_bar(self):
        self.ready_rank()
        self.view.resize(1400,900);self.app.processEvents()
        self.assertFalse(self.view._portrait_stacked)
        self.assertGreater(self.view.personal_info.x(),self.view.portrait.x()+self.view.portrait.width())
        self.assertGreaterEqual(self.view.rank_bar.width(),350)
        self.assertLessEqual(self.view.rank_bar.width(),420)
        self.assertLess(self.view.rank_bar.width(),self.view.personal_info.width())
        for text in ('15.000','23.000','21,6 %'):
            self.assertIn(text,self.view.rank_bar.format())
        self.assertEqual(self.view.personal['rank'].text(),'5')
        self.assertEqual(self.view.personal['merits'].text(),'16.726')
        self.assertIn('6.274',self.view.rank_summary.text())
        self.assertIn('1.726 / 8.000',self.view.rank_bar.toolTip())

    def test_narrow_stacking_and_bar_does_not_overflow(self):
        self.ready_rank()
        for width in (480,360,1200):
            self.view.resize(width,900);self.app.processEvents()
            self.assertLessEqual(self.view.rank_bar.width(),420)
            self.assertLessEqual(self.view.rank_bar.width(),self.view.personal_info.width())
            self.assertEqual(self.view.horizontalScrollBar().maximum(),0)
            if self.view._portrait_stacked:
                self.assertGreaterEqual(self.view.personal_info.y(),self.view.portrait.y()+self.view.portrait.height())
        self.assertEqual(self.view.personal_grid.count(),2)

    def test_missing_corrupt_and_available_portrait_preserve_aspect_ratio(self):
        with tempfile.TemporaryDirectory() as folder, patch('cmdrhelper.ui.powerplay_portraits.POWERPLAY_ASSET_DIR',Path(folder)):
            portrait=PowerPortrait();self.addCleanup(portrait.close)
            portrait.set_power('Nakato Kaine')
            self.assertTrue(portrait.text())
            path=Path(folder)/'nakato_kaine.png'
            path.write_text('not an image')
            portrait.set_power('Nakato Kaine')
            self.assertTrue(portrait.text())
            image=QImage(200,100,QImage.Format_RGB32);image.fill(Qt.gray);image.save(str(path))
            portrait.set_power('Nakato Kaine')
            pixmap=portrait.pixmap()
            self.assertFalse(pixmap.isNull())
            self.assertAlmostEqual(pixmap.width()/pixmap.height(),2,delta=.05)
            self.assertLessEqual(pixmap.width(),portrait.contentsRect().width())
            self.assertLessEqual(pixmap.height(),portrait.contentsRect().height())
            self.assertFalse(portrait.hasScaledContents())
            portrait.set_power('Edmund Mahon')
            self.assertTrue(portrait.text())

    def test_no_power_asset_is_distinct_from_unknown_and_missing_power_portrait(self):
        with tempfile.TemporaryDirectory() as folder, patch('cmdrhelper.ui.powerplay_portraits.POWERPLAY_ASSET_DIR',Path(folder)):
            image=QImage(84,112,QImage.Format_RGB32);image.fill(Qt.gray)
            image.save(str(Path(folder)/'noMacht.png'))
            self.state.powerplay.apply(dict(event='PowerplayLeave'))
            self.view.render()
            portrait=self.view.portrait
            self.assertEqual(portrait.key,'noMacht')
            self.assertFalse(portrait.pixmap().isNull())
            self.state.powerplay.membership_known=False;self.view.render()
            self.assertEqual(portrait.key,'')
            self.assertTrue(portrait.text())
            self.state.powerplay.power='Nakato Kaine';self.view.render()
            self.assertEqual(portrait.key,'nakato_kaine')
            self.assertTrue(portrait.text())
            (Path(folder)/'noMacht.png').write_text('broken')
            portrait.set_power('',membership_known=True)
            self.assertEqual(portrait.key,'noMacht')
            self.assertTrue(portrait.text())
