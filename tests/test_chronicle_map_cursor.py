import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent, QWheelEvent
from PySide6.QtWidgets import QApplication

from cmdrhelper.ui.chronicle_view import ChronicleMapWidget


class ChronicleMapCursorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.widget = ChronicleMapWidget()
        self.addCleanup(self.widget.close)
        self.widget.resize(800, 600)
        self.widget.set_systems([
            dict(system_address=1, name="Alpha", x=-100, y=0, z=0),
            dict(system_address=2, name="Beta", x=100, y=0, z=0),
        ], [dict(commander_id=1, system_addresses=[1, 2])])
        self.widget.yaw = self.widget.pitch = 0
        self.widget.scale = 1
        self.widget._center = (0, 0, 0)
        self.point = self.widget._project(self.widget.systems[0])[0]

    def mouse(self, kind, pos, button=Qt.NoButton, buttons=Qt.NoButton):
        event = QMouseEvent(kind, pos, pos, button, buttons, Qt.NoModifier)
        QApplication.sendEvent(self.widget, event)

    def move(self, pos):
        self.mouse(QEvent.MouseMove, pos)

    def test_exact_hit_boundary_including_highlighted_points_and_themes(self):
        for light in (False, True):
            self.widget.set_light_mode(light)
            for highlight in ("ordinary", "current", "selected"):
                self.widget.set_current_system("Alpha" if highlight == "current" else "")
                self.widget.selected_address = 1 if highlight == "selected" else None
                for offset, expected in ((0, Qt.PointingHandCursor),
                                         (11.99, Qt.PointingHandCursor),
                                         (12, Qt.ArrowCursor), (13, Qt.ArrowCursor)):
                    with self.subTest(light=light, highlight=highlight, offset=offset):
                        self.move(self.point + QPointF(offset, 0))
                        self.assertEqual(self.widget.cursor().shape(), expected)

    def test_route_axis_free_space_and_leave_use_normal_cursor(self):
        first, second = self.widget.route_segments()[0][1:]
        midpoint = (self.widget._project(first)[0] + self.widget._project(second)[0]) / 2
        axis = self.widget._project_xyz(0, 100, 0)[0]
        for pos in (midpoint, axis, QPointF(20, 20)):
            self.move(self.point)
            self.move(pos)
            self.assertEqual(self.widget.cursor().shape(), Qt.ArrowCursor)
            self.assertEqual(self.widget.hover_index, -1)
        self.move(self.point)
        QApplication.sendEvent(self.widget, QEvent(QEvent.Leave))
        self.assertEqual(self.widget.cursor().shape(), Qt.ArrowCursor)

    def test_point_click_still_selects_and_emits_system(self):
        clicked = []
        self.widget.systemClicked.connect(clicked.append)
        self.move(self.point)
        self.assertEqual(self.widget.hover_index, 0)
        self.mouse(QEvent.MouseButtonPress, self.point, Qt.LeftButton, Qt.LeftButton)
        self.mouse(QEvent.MouseButtonRelease, self.point, Qt.LeftButton)
        self.assertEqual(clicked, [self.widget.systems[0]])
        self.assertEqual(self.widget.selected_address, 1)
        self.assertEqual(self.widget.cursor().shape(), Qt.PointingHandCursor)

    def test_rotate_pan_and_zoom_remain_functional(self):
        clicked = []
        self.widget.systemClicked.connect(clicked.append)
        start, end = QPointF(30, 30), QPointF(50, 40)
        self.mouse(QEvent.MouseButtonPress, start, Qt.LeftButton, Qt.LeftButton)
        self.mouse(QEvent.MouseMove, end, buttons=Qt.LeftButton)
        self.mouse(QEvent.MouseButtonRelease, end, Qt.LeftButton)
        self.assertAlmostEqual(self.widget.yaw, 20 * 0.008)
        self.assertAlmostEqual(self.widget.pitch, 10 * 0.008)
        pan = QPointF(self.widget.pan)
        self.mouse(QEvent.MouseButtonPress, start, Qt.RightButton, Qt.RightButton)
        self.mouse(QEvent.MouseMove, end, buttons=Qt.RightButton)
        self.mouse(QEvent.MouseButtonRelease, end, Qt.RightButton)
        self.assertEqual(self.widget.pan, pan + end - start)
        scale = self.widget.scale
        QApplication.sendEvent(self.widget, QWheelEvent(
            end, end, QPoint(), QPoint(0, 120), Qt.NoButton,
            Qt.NoModifier, Qt.NoScrollPhase, False,
        ))
        self.assertAlmostEqual(self.widget.scale, scale * 1.16)
        scale = self.widget.scale
        self.mouse(QEvent.MouseButtonPress, QPointF(100, 100), Qt.MiddleButton, Qt.MiddleButton)
        self.mouse(QEvent.MouseMove, QPointF(500, 400), buttons=Qt.MiddleButton)
        self.mouse(QEvent.MouseButtonRelease, QPointF(500, 400), Qt.MiddleButton)
        self.assertGreater(self.widget.scale, scale)
        self.assertEqual(clicked, [])


if __name__ == "__main__":
    unittest.main()
