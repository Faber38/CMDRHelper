"""Rendered pencil colours, hit-tested hover/help, and unchanged table actions."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QEvent, QPoint, QSettings, Qt
from PySide6.QtGui import QColor, QHelpEvent, QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QToolTip

from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.mining_inventory import MiningInventory
from cmdrhelper.ui.carrier_edit_marker import marker_color
from cmdrhelper.ui.cursors import install_cursor_policy
from cmdrhelper.ui.mining_carrier_dialog import CarrierStockDialog
from cmdrhelper.ui.mining_view import MiningView
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from test_mining_view import RefreshController


class CarrierMarkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.owns_policy = not hasattr(cls.app, "_cmdrhelper_cursor_policy")
        cls.policy = install_cursor_policy(cls.app)

    @classmethod
    def tearDownClass(cls):
        if cls.owns_policy:
            cls.app.removeEventFilter(cls.policy)
            del cls.app._cmdrhelper_cursor_policy
            cls.policy.deleteLater()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(set_language, get_language())
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        set_language("de")
        self.settings = QSettings(str(Path(self.tmp.name) / "settings.ini"), QSettings.IniFormat)
        self.controller = RefreshController()
        self.view = MiningView(self.settings, controller=self.controller)
        self.addCleanup(self.view.deleteLater)
        self.addCleanup(self.view.close)
        self.view.resize(1300, 700)
        self.view.show()
        self.inventory = MiningInventory(1, "F1", srv={}, ship={"gold": 60}, carrier={"gold": 504},
            carrier_id=123, carrier_feed={"path": "test"})
        self.controller.ready.emit(self.inventory)
        self.view.search.setText("gold")
        self.app.processEvents()

    def move(self, widget, point):
        self.app.sendEvent(widget, QMouseEvent(QEvent.MouseMove, point, widget.mapToGlobal(point),
                                             Qt.NoButton, Qt.NoButton, Qt.NoModifier))
        self.app.processEvents()

    def assert_painted(self, viewport, rect, expected):
        image = viewport.grab().toImage()
        scale = image.devicePixelRatio()
        target = QColor(expected)
        pixels = [image.pixelColor(x, y)
                  for x in range(max(0, int(rect.left()*scale)), min(image.width(), int((rect.right()+1)*scale)))
                  for y in range(max(0, int(rect.top()*scale)), min(image.height(), int((rect.bottom()+1)*scale)))]
        distance = min(sum(abs(a-b) for a,b in zip(color.getRgb()[:3], target.getRgb()[:3])) for color in pixels)
        self.assertLess(distance, 35, f"No rendered {expected} pencil in {rect}")

    def test_header_and_cell_pencils_render_gold_and_brighter_hover_in_both_themes(self):
        header = self.view.tree.header()
        index = self.view.tree.indexFromItem(self.view.items["gold"], 3)
        for light, style, idle, hover in ((False, DARK_STYLESHEET, "#FFD54F", "#FFECB3"),
                                          (True, LIGHT_STYLESHEET, "#8A6100", "#B07D00")):
            self.app.setStyleSheet(style)
            self.view.set_light_mode(light)
            self.app.processEvents()
            for viewport, rect in ((header.viewport(), header.marker_rect()),
                                   (self.view.tree.viewport(), self.view.carrier_delegate.marker_rect(index))):
                self.move(viewport, QPoint(1, 1))
                self.assert_painted(viewport, rect, idle)
                self.move(viewport, rect.center())
                self.assertEqual(viewport.cursor().shape(), Qt.PointingHandCursor)
                self.assert_painted(viewport, rect, hover)
                self.app.sendEvent(viewport, QEvent(QEvent.Leave))
                self.assert_painted(viewport, rect, idle)
            self.assertEqual(marker_color(light).name(), idle.lower())
            self.assertGreater(marker_color(light, True).lightness(), marker_color(light).lightness())
        # The numeric carrier value remains independent of the pencil colour.
        self.assertEqual(self.view.items["gold"].data(3, Qt.UserRole), 504)

    def test_exact_edit_tooltip_in_all_languages_header_and_cell(self):
        header = self.view.tree.header()
        index = self.view.tree.indexFromItem(self.view.items["gold"], 3)
        for language in _TRANSLATIONS:
            set_language(language)
            for viewport, rect in ((header.viewport(), header.marker_rect()),
                                   (self.view.tree.viewport(), self.view.carrier_delegate.marker_rect(index))):
                point = rect.center()
                with patch.object(QToolTip, "showText") as show:
                    self.app.sendEvent(viewport, QHelpEvent(QEvent.ToolTip, point, viewport.mapToGlobal(point)))
                    self.assertEqual(show.call_args.args[1], tr("mining.carrier_edit"))
        set_language("de")
        self.assertEqual(tr("mining.carrier_edit"), "Carrier-Bestand bearbeiten")

    def test_sorting_double_click_and_disabled_cursor_are_unchanged(self):
        header = self.view.tree.header()
        QTest.mouseClick(header.viewport(), Qt.LeftButton, pos=header.marker_rect().center())
        self.assertEqual(header.sortIndicatorSection(), 3)
        QTest.mouseClick(header.viewport(), Qt.LeftButton, pos=header.marker_rect().center())
        order = header.sortIndicatorOrder()
        QTest.mouseClick(header.viewport(), Qt.LeftButton, pos=header.marker_rect().center())
        self.assertNotEqual(header.sortIndicatorOrder(), order)
        calls = []
        self.controller.confirm_carrier = lambda *args: calls.append(args)
        item = self.view.items["gold"]
        index = self.view.tree.indexFromItem(item, 3)
        position = self.view.carrier_delegate.marker_rect(index).center()
        with patch.object(CarrierStockDialog, "exec", return_value=QDialog.Accepted):
            QTest.mouseClick(self.view.tree.viewport(), Qt.LeftButton, pos=position)
            self.assertFalse(calls)
            QTest.mouseDClick(self.view.tree.viewport(), Qt.LeftButton, pos=position)
            QTest.mouseRelease(self.view.tree.viewport(), Qt.LeftButton, pos=position)
        self.assertEqual(calls, [("gold", None, (1, "F1", 123))])
        self.view.tree.setEnabled(False)
        self.move(header.viewport(), header.marker_rect().center())
        self.assertEqual(header.viewport().cursor().shape(), Qt.ArrowCursor)
        self.move(self.view.tree.viewport(), position)
        self.assertEqual(self.view.tree.viewport().cursor().shape(), Qt.ArrowCursor)
