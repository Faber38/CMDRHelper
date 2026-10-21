"""Rendered marker intervals, including fractional pixels and display scaling."""
import math
import unittest
from cmdrhelper.ui.powerplay_system import SystemControlBar, marker_positions
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests import test_powerplay as base


class MarkerTintTests(unittest.TestCase):
    setUpClass = classmethod(base.PowerplayViewTests.setUpClass.__func__)

    def setUp(self):
        self.bar = SystemControlBar()
        self.addCleanup(self.bar.close)
        self.bar.show()

    def capture(self, white, yellow):
        self.bar.white_position, self.bar.yellow_position = white, yellow
        self.bar.update()
        return self.bar.grab().toImage()

    def test_colors_clipping_boundaries_and_unchanged_positions(self):
        for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.bar.setStyleSheet(theme)
            for width in (40, 180, 360, 1200):
                self.bar.resize(width, self.bar.height())
                self.app.processEvents()
                left, span, segment = self.bar.geometry_for_width(width)
                baseline = self.capture(None, None)
                dpi = baseline.devicePixelRatio()
                y = round(18 * dpi)
                # Both directions, same stage, multiple stages and both edges.
                for white, yellow in ((.45,.3), (.3,.45), (.1,.9), (.9,.1), (0,1), (1,0)):
                    with self.subTest(width=width, white=white, yellow=yellow):
                        image = self.capture(white, yellow)
                        self.assertEqual((self.bar.white_position, self.bar.yellow_position), (white,yellow))
                        start, end = (left+span*min(white,yellow))*dpi, (left+span*max(white,yellow))*dpi
                        tint = (255,0,0) if white > yellow else (0,128,255)
                        checked = 0
                        for x in range(image.width()):
                            old, new = baseline.pixelColor(x,y), image.pixelColor(x,y)
                            if x+1 <= start or x >= end:
                                self.assertEqual(new,old)
                            elif x > start+1 and x < end-2 and all(abs(x-(left+i*segment)*dpi)>2 for i in range(5)):
                                for actual, original, channel in zip(new.getRgb()[:3],old.getRgb()[:3],tint):
                                    self.assertAlmostEqual(actual, (original*127+channel*128)/255, delta=2)
                                checked += 1
                        if width >= 180:
                            self.assertGreater(checked,0)
                        # Stage separators are painted over the tint.
                        for i in range(4):
                            x = round((left+i*segment)*dpi)
                            self.assertEqual(image.pixelColor(x,round(33*dpi)),
                                             baseline.pixelColor(x,round(33*dpi)))
                            if start+2 < x < end-3:
                                self.assertTrue(any(image.pixelColor(px,y) != image.pixelColor(x+round(2*dpi),y)
                                                    for px in range(x-1,x+2)))

    def test_equal_missing_unknown_and_tiny_interval(self):
        self.bar.resize(480, self.bar.height())
        baseline = self.capture(None,None)
        dpi = baseline.devicePixelRatio()
        y = round(18*dpi)
        for white,yellow in ((.4,.4),(.4,None),(None,.4),(None,None)):
            image = self.capture(white,yellow)
            self.assertEqual([image.pixelColor(x,y) for x in range(image.width())],
                             [baseline.pixelColor(x,y) for x in range(image.width())])
        for status in ('unknown','unoccupied'):
            self.bar.set_values(status,.5,100,0)
            self.assertIsNone(self.bar.yellow_position)
        left,span,_ = self.bar.geometry_for_width(self.bar.width())
        white=.4
        yellow=white + .5/(span*dpi)  # Half a physical pixel, no artificial widening.
        image=self.capture(white,yellow)
        changed=[x for x in range(image.width()) if image.pixelColor(x,y)!=baseline.pixelColor(x,y)]
        self.assertTrue(changed)
        self.assertTrue(all(math.floor((left+span*white)*dpi) <= x <= math.ceil((left+span*yellow)*dpi) for x in changed))

    def test_real_position_calculation_not_modified_by_painting(self):
        for args in [('fortified',.212125,73681,0),('exploited',.456767,64,6595),
                     ('stronghold',12.617802,12844156,476354),('exploited',-1e308,0,0)]:
            expected=marker_positions(*args)
            self.bar.set_values(*args)
            self.bar.grab()
            self.assertEqual((self.bar.white_position,self.bar.yellow_position),expected)
