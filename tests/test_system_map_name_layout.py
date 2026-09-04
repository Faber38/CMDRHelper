import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRectF
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import QApplication

from cmdrhelper.ui.system_view import SystemMapWidget


class SystemMapNameLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.widget = SystemMapWidget()
        self.widget.resize(900, 360)
        font = QFont("DejaVu Sans", 10)
        font.setBold(True)
        self.metrics = QFontMetrics(font)

    def test_real_central_star_name_is_shown_completely(self):
        name = "Prua Hypai HI-G b58-12"
        rect, visible = self.widget._body_name_layout(
            {"body_id": 0, "body_type": "Star", "star_type": "M"},
            377.5, 16, name, self.metrics,
        )
        self.assertEqual(visible, name)
        self.assertGreater(rect.width(), self.widget.BODY_W)
        self.assertGreaterEqual(rect.width() - 12,
                                self.metrics.horizontalAdvance(name))

    def test_wide_font_metrics_do_not_clip_stellar_name(self):
        name = "Prua Hypai HI-G b58-12"
        rect, visible = self.widget._body_name_layout(
            {"body_type": "Star", "star_type": "M"},
            377.5, 16, name, self.metrics,
        )
        self.assertEqual(visible, name)
        self.assertGreaterEqual(rect.width() - 12,
                                self.metrics.horizontalAdvance(name))

    def test_extremely_long_stellar_name_is_elided(self):
        name = "Prua " + "Hypai " * 100
        rect, visible = self.widget._body_name_layout(
            {"body_type": "Star", "star_type": "M"},
            377.5, 16, name, self.metrics,
        )
        self.assertNotEqual(visible, name)
        self.assertTrue(visible.endswith("…"))
        self.assertLessEqual(rect.width(),
                             self.widget.width() - 2 * self.widget.MARGIN_X)

    def test_stellar_text_rect_stays_inside_map_edges(self):
        body = {"body_type": "Star", "star_type": "M"}
        for x in (-40, self.widget.width() - 40):
            rect, _ = self.widget._body_name_layout(
                body, x, 16, "A deliberately broad central star name",
                self.metrics,
            )
            self.assertGreaterEqual(rect.left(), self.widget.MARGIN_X)
            self.assertLessEqual(rect.right(),
                                 self.widget.width() - self.widget.MARGIN_X)

    def test_planet_name_layout_remains_fixed(self):
        rect, visible = self.widget._body_name_layout(
            {"body_type": "Planet", "star_type": ""},
            42.25, 16, "1", self.metrics,
        )
        self.assertEqual(visible, "1")
        self.assertEqual(rect, QRectF(42.25, 85, self.widget.BODY_W, 20))


if __name__ == "__main__":
    unittest.main()
