"""Silent copying of the system heading in the actual chronicle detail window."""
import os
import unittest
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel

from cmdrhelper.ui.main_window import ChronicleSystemWindow


class ChronicleSystemCopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_left_click_copies_exact_heading_silently(self):
        clipboard = self.app.clipboard()
        self.addCleanup(clipboard.setText, clipboard.text())
        for name in ("Dryio Flyuae YM-A d14-446", "Sol"):
            with self.subTest(system=name):
                body_callback = Mock()
                window = ChronicleSystemWindow(name, [], "", body_callback)
                self.addCleanup(window.close)
                window.show()
                self.app.processEvents()
                title = window.findChild(QLabel, "sectionTitle")
                self.assertEqual(title.cursor().shape(), Qt.PointingHandCursor)
                clipboard.setText("unchanged")
                QTest.mouseClick(title, Qt.RightButton)
                self.assertEqual(clipboard.text(), "unchanged")
                visible_before = {w for w in self.app.topLevelWidgets() if w.isVisible()}
                QTest.mouseClick(title, Qt.LeftButton)
                self.app.processEvents()
                self.assertEqual(clipboard.text(), name)
                self.assertEqual(title.text(), name)
                self.assertEqual(
                    {w for w in self.app.topLevelWidgets() if w.isVisible()}, visible_before)
                self.assertIsNone(self.app.activePopupWidget())
                body_callback.assert_not_called()
                window.close()
