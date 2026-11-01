"""Buffered UI preferences retain the existing verified exit boundary."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from cmdrhelper.ui.preferences import set_preference
from cmdrhelper.ui.material_view import MaterialView
from cmdrhelper.ui.exit_controller import ExitController
from test_material_view import StubController
from material_ui_cleanup import cleanup_material_view


class PreferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / 'settings.ini')
        self.settings = QSettings(self.path, QSettings.IniFormat)

    def disk_values(self):
        code = "import json,sys; from PySide6.QtCore import QSettings; s=QSettings(sys.argv[1],QSettings.IniFormat); print(json.dumps({k:s.value(k) for k in s.allKeys() if k.startswith('materials/')}))"
        return json.loads(subprocess.check_output([sys.executable, '-c', code, self.path], text=True))

    def test_identical_values_do_not_dirty_settings_or_sync(self):
        self.settings.setValue('materials/category', 'Raw')
        self.settings.sync()
        with patch.object(self.settings, 'setValue', wraps=self.settings.setValue) as write, patch.object(self.settings, 'sync') as sync:
            for _ in range(20):
                set_preference(self.settings, 'materials/category', 'Raw')
            write.assert_not_called()
            sync.assert_not_called()

    def test_changes_are_immediately_visible_and_exit_sync_persists_latest_value(self):
        for value in ['Raw', 'Encoded', 'Mining']:
            set_preference(self.settings, 'materials/category', value)
            self.assertEqual(self.settings.value('materials/category'), value)
        ExitController.check_settings(SimpleNamespace(state=SimpleNamespace(settings=self.settings)))
        self.assertEqual(self.disk_values()['materials/category'], 'Mining')

    def test_event_loop_flushes_without_new_cache_or_timer(self):
        set_preference(self.settings, 'materials/filter', 'low')
        self.app.processEvents()
        self.assertEqual(self.disk_values()['materials/filter'], 'low')

    def test_material_handler_writes_only_changed_key_without_forcing_sync(self):
        self.settings.setValue('materials/category', 'Raw')
        self.settings.setValue('materials/filter', 'all')
        self.settings.sync()
        view = MaterialView(SimpleNamespace(settings=self.settings), controller=StubController())
        self.addCleanup(cleanup_material_view, view)
        with patch.object(self.settings, 'setValue', wraps=self.settings.setValue) as write, patch.object(self.settings, 'sync') as sync:
            view.tabs.setCurrentIndex(1)
            write.assert_called_once_with('materials/category', 'Manufactured')
            sync.assert_not_called()
        self.assertEqual(self.settings.value('materials/filter'), 'all')

    def test_regular_main_window_close_flushes_pending_preference(self):
        from test_safe_exit import SafeExitTests
        fixture = SafeExitTests()
        fixture.setUpClass()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        set_preference(fixture.settings, 'materials/category', 'Mining')
        self.assertTrue(fixture.w.close())
        self.path = fixture.settings.fileName()
        self.assertEqual(self.disk_values()['materials/category'], 'Mining')

    def test_sync_error_is_not_success_and_prevents_exit(self):
        from test_safe_exit import SafeExitTests
        class FailedSettings(QSettings):
            def status(self):
                return QSettings.AccessError
        fixture = SafeExitTests()
        fixture.setUpClass()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        failed = FailedSettings(self.path, QSettings.IniFormat)
        fixture.w.state.settings = failed
        set_preference(failed, 'materials/category', 'Mining')
        with self.assertRaises(OSError):
            ExitController.check_settings(SimpleNamespace(state=fixture.w.state))
        self.assertFalse(fixture.w.close())
        self.assertFalse(fixture.w._exit_controller.approved)
        self.assertTrue(fixture.w.isVisible())
