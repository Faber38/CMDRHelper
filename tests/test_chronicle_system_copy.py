"""Silent copying of the system heading in the actual chronicle detail window."""
import os
import unittest
from unittest.mock import Mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel, QToolButton

from cmdrhelper.ui.main_window import ChronicleSystemWindow


class ChronicleSystemCopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_left_click_copies_exact_heading_silently(self):
        clipboard = self.app.clipboard()
        self.addCleanup(clipboard.setText, clipboard.text())
        for name in ("Dryio Flyuae YM-A d14-446", "Fol Prou EL-Y f2858", "Sol"):
            with self.subTest(system=name):
                body_callback = Mock()
                window = ChronicleSystemWindow(name, [], "", body_callback)
                self.addCleanup(window.close)
                window.show()
                self.app.processEvents()
                title = window.findChild(QLabel, "sectionTitle")
                copy_button = window.findChild(QToolButton, "chronicleCopySystemName")
                self.assertEqual(title.cursor().shape(), Qt.PointingHandCursor)
                self.assertEqual(copy_button.cursor().shape(), Qt.PointingHandCursor)
                self.assertEqual(copy_button.text(), "⧉")
                self.assertEqual(copy_button.toolTip(), "")
                self.assertEqual(copy_button.x() - (title.x() + title.width()), 4)
                self.assertLessEqual(title.width(), title.sizeHint().width())
                clipboard.setText("unchanged")
                QTest.mouseClick(title, Qt.RightButton)
                self.assertEqual(clipboard.text(), "unchanged")
                self.assertEqual(copy_button.text(), "⧉")
                visible_before = {w for w in self.app.topLevelWidgets() if w.isVisible()}
                QTest.mouseClick(title, Qt.LeftButton)
                self.app.processEvents()
                self.assertEqual(clipboard.text(), name)
                self.assertEqual(title.text(), name)
                self.assertEqual(copy_button.text(), "✓")
                clipboard.setText("unchanged")
                QTest.mouseClick(copy_button, Qt.RightButton)
                self.assertEqual(clipboard.text(), "unchanged")
                QTest.mouseClick(copy_button, Qt.LeftButton)
                self.app.processEvents()
                self.assertEqual(clipboard.text(), name)
                self.assertEqual(copy_button.text(), "✓")
                self.assertEqual(
                    {w for w in self.app.topLevelWidgets() if w.isVisible()}, visible_before)
                self.assertIsNone(self.app.activePopupWidget())
                body_callback.assert_not_called()
                window.close()

    def test_feedback_timer_restarts_on_repeated_clicks(self):
        clipboard = self.app.clipboard()
        self.addCleanup(clipboard.setText, clipboard.text())
        name = "Fol Prou EL-Y f2858"
        window = ChronicleSystemWindow(name, [], "", Mock())
        self.addCleanup(window.close)
        window.show()
        self.app.processEvents()
        title = window.findChild(QLabel, "sectionTitle")
        copy_button = window.findChild(QToolButton, "chronicleCopySystemName")
        timer = window._copy_feedback_timer
        self.assertTrue(timer.isSingleShot())
        self.assertEqual(timer.interval(), 700)
        expirations = []
        timer.timeout.connect(lambda: expirations.append(True))

        QTest.mouseClick(title, Qt.LeftButton)
        self.assertEqual(copy_button.text(), "✓")
        QTest.qWait(450)
        for target in (copy_button, title, copy_button):
            QTest.mouseClick(target, Qt.LeftButton)
        QTest.qWait(350)  # Past the first deadline, before the restarted one.
        self.assertEqual(copy_button.text(), "✓")
        self.assertEqual(expirations, [])
        QTest.qWait(450)
        self.assertEqual(copy_button.text(), "⧉")
        self.assertEqual(expirations, [True])
        self.assertFalse(timer.isActive())
        self.assertEqual(title.text(), name)
        self.assertEqual(clipboard.text(), name)
        self.assertEqual(copy_button.toolTip(), "")
