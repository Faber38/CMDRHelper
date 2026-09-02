import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtTest import QTest
    from cmdrhelper.ui.startup_progress import StartupProgressDialog
except ImportError:
    QApplication = None


@unittest.skipIf(QApplication is None, "PySide6 ist nicht installiert")
class StartupProgressDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_real_numbers_and_percent(self):
        dialog = StartupProgressDialog(light=False)
        dialog.set_progress(1842, 3865, "startup.phase.index", "Journal.log")
        self.assertEqual(dialog.progress.value(), 48)
        self.assertIn("1842", dialog.count_label.text())
        self.assertIn("3865", dialog.count_label.text())
        self.assertEqual(dialog.file_label.text(), "Journal.log")

    def test_animation_runs_while_event_loop_remains_responsive(self):
        dialog = StartupProgressDialog()
        dialog.begin(100)
        before = dialog.ships.animation_ticks
        QTest.qWait(130)
        self.assertGreater(dialog.ships.animation_ticks, before)
        dialog.reject()

    def test_success_closes_and_error_can_be_closed(self):
        dialog = StartupProgressDialog()
        dialog.begin(10)
        dialog.finish("")
        QTest.qWait(150)
        self.assertFalse(dialog.isVisible())
        failed = StartupProgressDialog(light=True)
        failed.begin(10)
        failed.finish("Testfehler")
        self.assertFalse(failed.ships.running)
        self.assertTrue(failed.close_button.isVisible())
        self.assertTrue(failed.ships.light)
        failed.reject()


if __name__ == "__main__":
    unittest.main()
