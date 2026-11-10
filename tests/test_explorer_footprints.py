"""Real map painting, marker hit testing and the shared vector legend."""
import os
import tempfile
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QRectF, QSettings, Qt, QEvent
from PySide6.QtGui import QImage, QPainter, QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QToolTip, QLabel
from cmdrhelper.ui.system_view import SystemMapWidget
from cmdrhelper.ui.footfall_icon import FootfallIcon, footfall_color, paint_footprints
from cmdrhelper.i18n import set_language, get_language
from tests.test_explorer_table_ux import ExplorerWindow
from qt_widget_cleanup import destroy_widget


class FootprintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.addCleanup(set_language, get_language()); set_language('de')
        self.errors = []
        self.addCleanup(setattr, sys, 'excepthook', sys.excepthook)
        sys.excepthook = lambda *args: self.errors.append(args)

    def tearDown(self):
        self.assertEqual(self.errors, [], 'Unhandled Qt callback exception')

    def test_true_only_correct_body_themes_and_hover(self):
        widget = SystemMapWidget()
        self.addCleanup(destroy_widget, widget)
        bodies = [dict(body_id=i, name='Planet '+str(i), body_type='Planet',
                       landable=True, terraformable=True, was_discovered=False,
                       was_mapped=False, self_mapped=True, first_footfall=value)
                  for i, value in enumerate((True, False, None, 1))]
        for light in (False, True):
            widget.set_light_mode(light)
            for width in (640, 1400):
                widget.set_system('Example', bodies); widget.resize(width, 400)
                widget.show(); self.app.processEvents(); widget.grab()
                self.assertEqual(len(widget._footfall_rects), 1)
                rect, body = widget._footfall_rects[0]
                self.assertEqual(body['body_id'], 0)
                tile = next(r for r, b in widget._body_rects if b['body_id'] == 0)
                self.assertTrue(tile.contains(rect))
                # Rightmost footprint slot leaves all other markers to its left.
                self.assertGreater(rect.left(), tile.center().x())
                picture = widget.grab().toImage()
                colors = {picture.pixelColor(x,y).name()
                          for x in range(int(rect.left()), int(rect.right()))
                          for y in range(int(rect.top()), int(rect.bottom()))}
                self.assertIn(footfall_color(light).name(), colors)
                with patch.object(QToolTip, 'showText') as tip:
                    point = rect.center()
                    QApplication.sendEvent(widget, QMouseEvent(QEvent.MouseMove, point,
                        widget.mapToGlobal(point.toPoint()), Qt.NoButton, Qt.NoButton, Qt.NoModifier))
                    self.app.processEvents()
                    self.assertEqual(tip.call_args.args[1], 'Erstbetretung')
                # False after a refresh must clear old hit targets too.
                widget.set_system('Example', [dict(bodies[0], first_footfall=False)])
                widget.grab()
                self.assertEqual(widget._footfall_rects, [])

    def test_vector_device_pixel_ratios(self):
        for light in (False, True):
            for ratio in (1, 1.5, 2):
                image = QImage(int(24*ratio), int(24*ratio), QImage.Format_ARGB32)
                image.setDevicePixelRatio(ratio); image.fill(Qt.transparent)
                painter = QPainter(image)
                paint_footprints(painter, QRectF(2,2,20,20), light); painter.end()
                pixels = [image.pixelColor(x,y) for x in range(image.width()) for y in range(image.height())]
                self.assertTrue(any(c.alpha()==255 and c.name()==footfall_color(light).name() for c in pixels))
                self.assertEqual(image.pixelColor(0,0).alpha(), 0)

    def test_legend_shared_icon_and_label_in_both_themes(self):
        with tempfile.TemporaryDirectory() as tmp:
            for theme in ('dark', 'light'):
                w = ExplorerWindow(QSettings(str(Path(tmp)/(theme+'.ini')), QSettings.IniFormat), theme=theme)
                try:
                    w.resize(720,700); w.show(); self.app.processEvents()
                    icon = w.footfall_legend_icon
                    self.assertIsInstance(icon, FootfallIcon)
                    self.assertEqual(icon.toolTip(), 'Erstbetretung')
                    self.assertEqual(icon.light, theme=='light')
                    self.assertTrue(any(label.text()=='Erstbetretung' for label in w.findChildren(QLabel)))
                    self.assertFalse(icon.geometry().isEmpty())
                finally:
                    # Allow the existing width-fit singleShot callback to finish.
                    QTest.qWait(20)
                    destroy_widget(w, close=False)
