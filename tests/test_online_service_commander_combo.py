from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

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

    def test_popup_is_constrained_to_combo_width_and_elides_long_text(self):
        window, combo = self._window_with_combo("A" * 500)
        window.resize(420, 160)
        window.show()
        self.app.processEvents()
        combo.showPopup()
        self.app.processEvents()
        try:
            self.assertLessEqual(combo.view().width(), combo.width())
            self.assertLessEqual(combo.view().window().width(), combo.width())
            self.assertEqual(
                combo.view().textElideMode(), Qt.TextElideMode.ElideRight
            )
            self.assertEqual(
                combo.view().horizontalScrollBarPolicy(),
                Qt.ScrollBarPolicy.ScrollBarAlwaysOff,
            )
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
