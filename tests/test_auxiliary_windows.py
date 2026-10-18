"""Modeless window ownership using synthetic UI state and in-memory settings."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import subprocess
import sys
import unittest

from PySide6.QtCore import QCoreApplication, QEvent, Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QDialog
from shiboken6 import isValid

from cmdrhelper.ui.help_dialog import HelpDialog
from cmdrhelper.ui.main_window import ChronicleSystemWindow, ChronicleSearchHelpDialog
from cmdrhelper.ui.system_overview import SystemOverviewDialog
from cmdrhelper.ui.station_details import StationDetailDialog, StationSelectionDialog
from cmdrhelper.ui.ship_widgets import ShipImageViewer
from tests import test_live_window_focus as live_tests


class AuxiliaryWindowTests(unittest.TestCase):
    setUpClass = classmethod(live_tests.LiveWindowFocusTests.setUpClass.__func__)
    setUp = live_tests.LiveWindowFocusTests.setUp
    cleanup_windows = live_tests.LiveWindowFocusTests.cleanup_windows
    windows = live_tests.LiveWindowFocusTests.windows
    refresh = live_tests.LiveWindowFocusTests.refresh

    def test_live_windows_remain_independent_and_update_while_main_minimized(self):
        self.main.show()
        self.refresh()
        windows = self.windows()
        for window in windows:
            self.assertEqual(window.windowType(), Qt.Window)
            self.assertIsNone(window.windowHandle().transientParent())
            self.assertIs(window.parentWidget(), self.main)
        self.main.showMinimized()
        self.app.processEvents()
        for window in windows:
            self.assertTrue(window.isVisible())
            self.assertFalse(window.isMinimized())
            self.assertTrue(window.isEnabled())
        self.snapshot.update(count=7, inventory=[{'Name': 'gold', 'Count': 7}])
        self.refresh()
        self.assertEqual(windows[0]._last_snapshot['count'], 7)
        self.assertEqual(windows[0].table.rowCount(), 1)
        windows[0].showMinimized()
        self.app.processEvents()
        self.refresh()
        self.assertTrue(windows[0].isMinimized())
        self.assertFalse(windows[1].isMinimized())
        self.main.showNormal()
        self.app.processEvents()
        self.assertTrue(windows[0].isMinimized())
        windows[0].showNormal()
        windows[0].close()
        self.assertFalse(windows[0].isVisible())
        self.assertTrue(windows[1].isVisible())
        self.assertTrue(self.main.isVisible())
        windows[0].show()
        self.assertTrue(windows[0].isVisible())
        self.assertIsNone(windows[0].windowHandle().transientParent())
        self.main.close()
        self.assertTrue(all(not w.isVisible() for w in windows))

    def test_other_modeless_windows_and_nested_ownership(self):
        self.main.show()
        station = {'station_name': 'Synthetic Station', 'station_type': 'Coriolis'}
        image = QImage(20, 20, QImage.Format_RGB32)
        image.fill(Qt.black)
        windows = [HelpDialog('overview', self.main),
                   ChronicleSearchHelpDialog({}, None, self.main),
                   ChronicleSystemWindow('Synthetic', [], '', lambda body: None, self.main),
                   SystemOverviewDialog('Synthetic', [], parent=self.main),
                   StationDetailDialog(station, 'Synthetic', self.main),
                   StationSelectionDialog([station], 'Synthetic', self.main),
                   ShipImageViewer(image, 'Synthetic', self.main)]
        for window in windows:
            window.show()
        nested = HelpDialog('overview', windows[-1])
        nested.show()
        self.assertIs(nested.parentWidget(), self.main)
        windows[-1].close()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.assertTrue(nested.isVisible())
        self.main.showMinimized()
        self.app.processEvents()
        for window in windows[:-1] + [nested]:
            self.assertTrue(window.isVisible())
            self.assertFalse(window.isMinimized())
            self.assertIsNone(window.windowHandle().transientParent())
        self.main.showNormal()
        for window in windows[:-1] + [nested]:
            window.showMinimized()
            self.app.processEvents()
            self.assertFalse(self.main.isMinimized())
            self.assertTrue(window.isMinimized())
            self.assertTrue(all(not other.isMinimized() for other in windows[:-1] + [nested]
                                if other is not window))
            window.showNormal()
        self.main.close()
        self.assertTrue(all(not isValid(w) or not w.isVisible() for w in windows + [nested]))

    def test_modal_dialog_keeps_its_owner_and_modality(self):
        self.main.show()
        dialog = QDialog(self.main)
        dialog.setModal(True)
        dialog.show()
        self.assertTrue(dialog.isModal())
        self.assertEqual(dialog.windowType(), Qt.Dialog)
        self.assertIs(dialog.windowHandle().transientParent(), self.main.windowHandle())
        dialog.close()
        self.main.close()

    def test_main_close_exits_real_event_loop_with_auxiliary_open(self):
        code = '''
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QTimer
from cmdrhelper.ui.main_window import MainWindow, CargoLiveWindow
from tests.test_cargo_live import _Settings
app = QApplication([])
main = MainWindow.__new__(MainWindow)
QMainWindow.__init__(main)
main.show()
cargo = CargoLiveWindow(_Settings(), main)
cargo.show()
QTimer.singleShot(50, main.close)
QTimer.singleShot(3000, lambda: app.exit(99))
result = app.exec()
assert not cargo.isVisible()
raise SystemExit(result)
'''
        result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
