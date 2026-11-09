"""Qt ownership regressions; no database, worker jobs or production settings."""
import sys
import tempfile
import traceback
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QSettings, Qt, Signal
from PySide6.QtWidgets import QApplication, QWidget
from shiboken6 import isValid

from cmdrhelper.mining_controller import MiningInventoryController


class State(QObject):
    journalIndexReady = Signal(object)
    databaseImportFinished = Signal(object, str)
    changed = Signal()


class MiningLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.errors = []
        self.hook = patch.object(sys, 'excepthook', self.capture)
        self.hook.start()
        self.addCleanup(self.check_callbacks)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = State()
        self.state.settings = QSettings(self.tmp.name + '/settings.ini', QSettings.IniFormat)

    def capture(self, kind, value, tb):
        self.errors.append(''.join(traceback.format_exception(kind, value, tb)))

    def check_callbacks(self):
        try:
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
            self.app.processEvents()
        finally:
            self.hook.stop()
        self.assertEqual(self.errors, [], '\n'.join(self.errors))

    def destroy(self, parent):
        parent.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_parent_destroyed_before_deferred_start_repeated(self):
        for _ in range(20):
            parent = QObject()
            controller = MiningInventoryController(self.state, parent)
            self.destroy(parent)
            self.assertFalse(isValid(controller.cargo_retry))
            self.app.processEvents()

    def test_signals_after_destruction_and_queued_delivery(self):
        parent = QObject()
        controller = MiningInventoryController(self.state, parent)
        self.app.processEvents()
        controller.timer.stop()
        self.state.journalIndexReady.connect(controller._force_request, Qt.QueuedConnection)
        self.state.journalIndexReady.emit(None)
        self.destroy(parent)
        self.state.journalIndexReady.emit(None)
        self.state.databaseImportFinished.emit(None, '')
        self.state.changed.emit()
        self.app.processEvents()

    def test_window_destruction_cancels_start(self):
        window = QWidget()
        window.setAttribute(Qt.WA_DeleteOnClose)
        controller = MiningInventoryController(self.state, window)
        window.show()
        window.close()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.assertFalse(isValid(controller))
        self.app.processEvents()

    def test_close_before_start_and_late_manual_request(self):
        parent = QObject()
        controller = MiningInventoryController(self.state, parent)
        self.assertTrue(controller.close())
        self.state.journalIndexReady.emit(None)
        self.state.databaseImportFinished.emit(None, '')
        controller.refresh_now()
        self.app.processEvents()
        self.assertFalse(controller.timer.isActive())
        self.assertFalse(controller.cargo_retry.isActive())
        self.assertFalse(controller._manual_pending)
        self.destroy(parent)

    def test_force_and_retry_arguments_preserved(self):
        parent = QObject()
        controller = MiningInventoryController(self.state, parent)
        self.app.processEvents()
        controller.timer.stop()
        with patch.object(controller, 'request') as request:
            self.state.journalIndexReady.emit(None)
            request.assert_called_once_with(force=True)
            request.reset_mock()
            self.state.databaseImportFinished.emit(None, '')
            request.assert_called_once_with(force=True)
            request.reset_mock()
            controller.cargo_retry.timeout.emit()
            request.assert_called_once_with(force=True, cargo_retry=True)
        self.destroy(parent)
