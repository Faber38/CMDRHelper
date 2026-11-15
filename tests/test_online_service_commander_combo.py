from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                               QFormLayout, QStyle, QStyleOptionComboBox)
from PySide6.QtTest import QTest
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET

from cmdrhelper.ui.main_window import OnlineServiceCommanderComboBox


class OnlineServiceCommanderComboTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    @staticmethod
    def _window_with_combo(text):
        window = QMainWindow()
        page = QWidget()
        layout = QVBoxLayout(page)
        combo = OnlineServiceCommanderComboBox()
        combo.addItem(text, "FID-LONG")
        combo.setItemData(
            0, f"{text} (FID-LONG)", Qt.ItemDataRole.ToolTipRole
        )
        combo._sync_current_tooltip()
        layout.addWidget(combo)
        window.setCentralWidget(page)
        return window, combo

    def test_long_commander_does_not_expand_main_window_minimum_width(self):
        short_window, short_combo = self._window_with_combo("Alpha — configured")
        long_name = "Commander " + ("Extremely-Long-Name-" * 40)
        long_window, long_combo = self._window_with_combo(
            f"{long_name} — configured"
        )

        self.assertEqual(
            long_window.minimumSizeHint().width(),
            short_window.minimumSizeHint().width(),
        )
        self.assertEqual(
            long_combo.sizeAdjustPolicy(),
            OnlineServiceCommanderComboBox.SizeAdjustPolicy
            .AdjustToMinimumContentsLengthWithIcon,
        )
        self.assertEqual(long_combo.minimumContentsLength(), 12)
        self.assertEqual(
            long_combo.sizePolicy().horizontalPolicy(),
            long_combo.sizePolicy().Policy.Expanding,
        )
        self.assertIn(long_name, long_combo.toolTip())
        self.assertIn("FID-LONG", long_combo.toolTip())

    def test_popup_shows_full_names_and_stays_on_screen(self):
        window, combo = self._window_with_combo("A" * 500)
        window.setGeometry(100, 100, 420, 160)
        combo.setFixedWidth(260)
        window.centralWidget().layout().setAlignment(
            combo, Qt.AlignmentFlag.AlignRight
        )
        window.show()
        self.app.processEvents()
        combo.showPopup()
        self.app.processEvents()
        try:
            combo_global = combo.mapToGlobal(combo.rect().topLeft())
            popup_geometry = combo.view().window().geometry()
            main_geometry = window.frameGeometry()
            screen_geometry = window.screen().availableGeometry()
            visible_right = screen_geometry.right()

            self.assertGreater(
                combo_global.x() + combo.width(),
                window.frameGeometry().center().x(),
            )
            self.assertLessEqual(popup_geometry.right(), visible_right)
            self.assertGreaterEqual(
                popup_geometry.left(),
                screen_geometry.left(),
            )
            self.assertGreater(popup_geometry.width(), combo.width())
            self.assertGreater(combo.view().horizontalScrollBar().maximum(), 0)
            self.assertEqual(combo.itemText(0), "A" * 500)
            self.assertEqual(
                popup_geometry.top(), combo_global.y() + combo.height()
            )
            self.assertEqual(
                combo.view().textElideMode(), Qt.TextElideMode.ElideNone
            )
            self.assertEqual(
                combo.view().horizontalScrollBarPolicy(),
                Qt.ScrollBarPolicy.ScrollBarAsNeeded,
            )
        finally:
            combo.hidePopup()
            window.close()

    def test_compact_form_arrow_and_selection_across_themes_and_fonts(self):
        for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            for font_size in (9, 16, 24):
                for width in (360, 1000):
                    with self.subTest(font_size=font_size, width=width, dark=theme == DARK_STYLESHEET):
                        window = QWidget()
                        window.setStyleSheet(theme + f"\nQComboBox, QListView {{ font-size: {font_size}pt; }}")
                        font = window.font()
                        font.setPointSize(font_size)
                        window.setFont(font)
                        form = QFormLayout(window)
                        combo = OnlineServiceCommanderComboBox()
                        name = "Commander " + "Long-Name-" * 50
                        combo.addItem(name, "F-A")
                        combo.addItem("Bravo", "F-B")
                        form.addRow("Commander:", combo)
                        window.resize(width, 160)
                        window.show()
                        self.app.processEvents()
                        try:
                            self.assertLessEqual(combo.width(), combo.maximumWidth())
                            self.assertLessEqual(combo.geometry().right(), window.width())
                            self.assertLessEqual(window.minimumSizeHint().width(), 360)
                            option = QStyleOptionComboBox()
                            combo.initStyleOption(option)
                            arrow = combo.style().subControlRect(
                                QStyle.CC_ComboBox, option, QStyle.SC_ComboBoxArrow, combo)
                            self.assertTrue(combo.rect().contains(arrow))
                            combo.grab()  # Exercise the eliding paint path.
                            QTest.mouseClick(combo, Qt.LeftButton, pos=arrow.center())
                            self.app.processEvents()
                            self.assertTrue(combo.view().isVisible())
                            QTest.qWait(QApplication.doubleClickInterval() + 20)
                            index = combo.model().index(1, 0)
                            point = combo.view().visualRect(index).intersected(combo.view().viewport().rect()).center()
                            QTest.mouseMove(combo.view().viewport(), point)
                            QTest.qWait(30)
                            QTest.mouseClick(combo.view().viewport(), Qt.LeftButton, pos=point)
                            self.assertEqual(combo.currentData(), "F-B")
                            self.assertEqual(combo.itemText(0), name)
                        finally:
                            combo.hidePopup()
                            window.close()

    def test_edsm_and_inara_use_the_same_constrained_combo_class(self):
        edsm = OnlineServiceCommanderComboBox()
        inara = OnlineServiceCommanderComboBox()
        self.assertEqual(edsm.sizeAdjustPolicy(), inara.sizeAdjustPolicy())
        self.assertEqual(edsm.minimumContentsLength(), inara.minimumContentsLength())
        self.assertEqual(
            edsm.sizePolicy().horizontalPolicy(),
            inara.sizePolicy().horizontalPolicy(),
        )


if __name__ == "__main__":
    unittest.main()
