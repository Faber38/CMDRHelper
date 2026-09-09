import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtCore import QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QTabBar

from cmdrhelper.ui.material_view import MaterialView
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from test_material_view import StubController


class MaterialCategoryTabTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        previous = self.app.styleSheet()
        self.addCleanup(self.app.setStyleSheet, previous)
        self.settings = QSettings(str(Path(self.tmp.name) / 'ui.ini'), QSettings.Format.IniFormat)
        self.view = MaterialView(SimpleNamespace(settings=self.settings), controller=StubController(), odyssey_controller=StubController())
        self.view.resize(1000, 650)
        self.view.show()
        self.addCleanup(self.view.close)

    def theme(self, light):
        self.app.setStyleSheet(LIGHT_STYLESHEET if light else DARK_STYLESHEET)
        self.view.set_light_mode(light)
        self.app.processEvents()

    def assert_only_active_border(self):
        tabs = self.view.tabs
        image = tabs.grab().toImage()
        for i in range(4):
            rect = tabs.tabRect(i)
            pixel = image.pixelColor(rect.center().x(), rect.top() + 1)
            if i == tabs.currentIndex():
                self.assertEqual(pixel, tabs.active_border_color)
            else:
                self.assertNotEqual(pixel, tabs.active_border_color)

    def test_mouse_switch_moves_border_immediately_across_all_four_tabs_and_themes(self):
        for light in (False, True):
            self.theme(light)
            self.assertEqual(self.view.tabs.active_border_color.name(), '#9a620e' if light else '#c57a00')
            for index in (0, 1, 2, 3, 0):
                QTest.mouseClick(self.view.tabs, Qt.MouseButton.LeftButton, pos=self.view.tabs.tabRect(index).center())
                self.assertEqual(self.view.tabs.currentIndex(), index)
                if index < 3:
                    self.assertEqual(len(self.view.items), (28, 71, 47)[index])
                else:
                    self.assertEqual(len(self.view.odyssey.items), 61)
                self.assert_only_active_border()

    def test_keyboard_switching_keeps_native_behavior(self):
        for light in (False, True):
            self.theme(light)
            self.view.tabs.setCurrentIndex(0)
            self.view.tabs.setFocus()
            for index in (1, 2):
                QTest.keyClick(self.view.tabs, Qt.Key.Key_Right)
                self.assertEqual(self.view.tabs.currentIndex(), index)
                self.assert_only_active_border()
            QTest.keyClick(self.view.tabs, Qt.Key.Key_Left)
            self.assertEqual(self.view.tabs.currentIndex(), 1)
            self.assert_only_active_border()

    def test_native_labels_sizes_and_inactive_rendering_unchanged(self):
        tabs = self.view.tabs
        plain = QTabBar()
        self.addCleanup(plain.close)
        plain.setExpanding(tabs.expanding())
        plain.setUsesScrollButtons(tabs.usesScrollButtons())
        for index in range(4):
            plain.addTab(tabs.tabText(index))
        plain.resize(tabs.size())
        plain.show()
        for light in (False, True):
            self.theme(light)
            plain.resize(tabs.size())
            for selected in range(4):
                tabs.setCurrentIndex(selected)
                plain.setCurrentIndex(selected)
                plain.clearFocus()
                tabs.clearFocus()
                self.app.processEvents()
                self.assertEqual(tabs.sizeHint(), plain.sizeHint())
                custom_image, plain_image = tabs.grab().toImage(), plain.grab().toImage()
                for index in range(4):
                    self.assertEqual(tabs.tabRect(index), plain.tabRect(index))
                    self.assertEqual(tabs.tabText(index), plain.tabText(index))
                    if index != selected:
                        # The inset border must not repaint adjacent inactive tabs.
                        rect = tabs.tabRect(index).adjusted(2, 2, -2, -2)
                        self.assertEqual(custom_image.copy(rect).convertToFormat(QImage.Format.Format_RGB32),
                                         plain_image.copy(rect).convertToFormat(QImage.Format.Format_RGB32))

    def test_saved_active_category_and_live_theme_switch(self):
        self.view.tabs.setCurrentIndex(2)
        restarted = MaterialView(SimpleNamespace(settings=self.settings), controller=StubController(), odyssey_controller=StubController())
        self.addCleanup(restarted.close)
        self.assertEqual(restarted.tabs.currentIndex(), 2)
        for light in (True, False):
            self.theme(light)
            self.assertEqual(self.view.tabs.currentIndex(), 2)
            self.assert_only_active_border()
