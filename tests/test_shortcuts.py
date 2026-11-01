"""Local shortcut lifecycle and actual Qt delivery; no production settings or services."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
import unittest
import shutil
import subprocess
from types import SimpleNamespace

from PySide6.QtCore import Qt, QSettings, QTimer
from PySide6.QtGui import QKeySequence
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton,
    QLineEdit, QTextEdit, QSpinBox, QComboBox, QDialog, QMenu, QKeySequenceEdit,
    QDialogButtonBox, QMessageBox, QVBoxLayout, QCheckBox)
from cmdrhelper.shortcuts import ShortcutManager, ACTIONS, PREFIX, validate_combination
from cmdrhelper.global_hotkey import GlobalHotkey, SETTING
from cmdrhelper.ui.shortcut_settings import ShortcutSettings
from cmdrhelper.i18n import _TRANSLATIONS, set_language, get_language, tr
from cmdrhelper.help_content import help_topic
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class ShortcutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.settings = QSettings(str(Path(self.tmp.name)/'settings.ini'), QSettings.IniFormat)
        self.window = QMainWindow()
        self.button = QPushButton('Focus')
        self.window.setCentralWidget(self.button)
        self.backend = Mock()
        self.backend.register.side_effect = iter(range(1, 100))
        self.hotkey = GlobalHotkey(self.settings, backend_factory=lambda callback: self.backend)
        self.callbacks = {key: Mock() for key in ACTIONS}
        self.manager = ShortcutManager(self.window, self.settings, self.hotkey, self.callbacks)
        self.manager.load()
        self.addCleanup(self.cleanup)
        self.addCleanup(set_language, get_language())
        self.activate_window()

    def cleanup(self):
        self.hotkey.close()
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def activate_window(self):
        self.window.showNormal(); self.window.raise_(); self.window.activateWindow()
        self.button.setFocus()
        self.assertTrue(QTest.qWaitForWindowActive(self.window, 3000))

    def press(self, widget=None, key=Qt.Key_F8):
        QTest.keyClick(widget or self.button, key, Qt.ControlModifier)
        self.app.processEvents()

    def bind(self, action='open_trade', value='Ctrl+F8'):
        self.assertTrue(self.manager.set_binding(action, value), self.manager.error)

    def test_empty_default_and_local_qt_delivery_change_remove(self):
        self.assertFalse(any(self.manager.bindings.values()))
        self.backend.register.assert_not_called()
        self.bind()
        shortcut = self.manager.shortcuts['open_trade']
        self.assertEqual(shortcut.context(), Qt.WindowShortcut)
        self.assertFalse(shortcut.autoRepeat())
        self.press(); self.callbacks['open_trade'].assert_called_once_with()
        self.bind(value='Ctrl+F9')
        self.press(); self.callbacks['open_trade'].assert_called_once()
        self.press(key=Qt.Key_F9); self.assertEqual(self.callbacks['open_trade'].call_count, 2)
        self.bind(value=''); self.press(key=Qt.Key_F9)
        self.assertEqual(self.callbacks['open_trade'].call_count, 2)

    def test_restart_portable_language_commander_independent(self):
        self.bind()
        self.assertEqual(self.settings.value(PREFIX+'open_trade'), 'Ctrl+F8')
        self.manager.settings = QSettings(self.settings.fileName(), QSettings.IniFormat)
        for lang in _TRANSLATIONS:
            set_language(lang)
            self.window.commander_fid = 'Different-'+lang
            self.manager.load()
            self.assertEqual(self.manager.bindings['open_trade'], 'Ctrl+F8')
        self.press(); self.callbacks['open_trade'].assert_called_once()

    def test_conflicts_both_directions_and_failed_change_preserves_old(self):
        self.bind()
        self.assertFalse(self.manager.set_binding('open_explorer', 'Ctrl+F8'))
        self.assertFalse(self.hotkey.set_hotkey('Ctrl+F8'))
        self.backend.register.assert_not_called()
        self.assertTrue(self.hotkey.set_hotkey('Ctrl+F9'))
        self.assertFalse(self.manager.set_binding('open_trade', 'Ctrl+F9'))
        self.assertEqual(self.manager.bindings['open_trade'], 'Ctrl+F8')
        self.assertEqual(self.settings.value(PREFIX+'open_trade'), 'Ctrl+F8')
        self.assertFalse(self.hotkey.set_hotkey('Ctrl+F8'))
        self.assertEqual(self.hotkey.active, 'Ctrl+F9')
        self.backend.register.side_effect = RuntimeError('reserved by desktop')
        self.assertFalse(self.hotkey.set_hotkey('Ctrl+F11'))
        self.assertEqual(self.hotkey.active, 'Ctrl+F9')

    def test_failed_global_registration_still_reserves_saved_binding(self):
        self.settings.setValue(SETTING, 'Ctrl+F8')
        self.backend.register.side_effect = RuntimeError('busy')
        self.assertFalse(self.hotkey.load())
        self.assertFalse(self.manager.set_binding('open_trade', 'Ctrl+F8'))
        self.assertTrue(self.hotkey.set_hotkey(''))
        self.bind()

    def test_legacy_global_binding_retained_but_new_reserved_binding_rejected(self):
        self.settings.setValue(SETTING, 'Alt+F9')
        self.assertTrue(self.hotkey.load())
        self.assertEqual(self.hotkey.active, 'Alt+F9')
        self.assertFalse(self.hotkey.set_hotkey('Ctrl+X'))
        self.assertEqual(self.hotkey.active, 'Alt+F9')
        self.assertTrue(self.hotkey.set_hotkey(''))

    def test_protected_combinations_and_single_sequence(self):
        for value in ('X', 'Shift+X', 'Ctrl+X', 'Ctrl+Shift+V', 'Ctrl+A', 'Ctrl+Z',
                      'Ctrl+Left', 'Ctrl+Alt+Q', 'Meta+E', 'Alt+F4', 'Alt+Tab',
                      'Return', 'Escape', 'Tab', 'Delete', 'F1', 'F10', 'Ctrl+F4',
                      'Ctrl+F8, Ctrl+F9', 'nonsense'):
            with self.subTest(value=value):
                self.assertFalse(self.manager.set_binding('open_trade', value))
        for value in ('Ctrl+E', 'Ctrl+M', 'Ctrl+Q', 'F8', 'Ctrl+Shift+F9'):
            self.assertEqual(validate_combination(value), value)

    def test_invalid_duplicates_rejected_and_quit_can_be_removed(self):
        for a,v in (('open_trade','Ctrl+F8'), ('open_explorer','Ctrl+F8'),
                    ('quit','Ctrl+Q'), ('open_materials','Ctrl+X')):
            self.settings.setValue(PREFIX+a,v)
        self.manager.load()
        self.assertEqual(self.manager.bindings["quit"],"Ctrl+Q")
        self.assertEqual(len(self.manager.errors),3)
        self.assertFalse(self.manager.set_binding('open_powerplay','Ctrl+F8'))
        self.assertFalse(self.hotkey.set_hotkey('Ctrl+F8'))
        self.assertEqual(self.settings.value(PREFIX+'quit'),'Ctrl+Q')
        self.assertTrue(self.manager.set_binding('quit',''))
        self.assertEqual(self.settings.value(PREFIX+'quit'),'')

    def test_storage_failure_keeps_active_binding(self):
        self.bind()
        with patch.object(self.settings,'status',return_value=QSettings.AccessError):
            self.assertFalse(self.manager.set_binding('open_trade','Ctrl+F9'))
        self.assertEqual(self.manager.bindings['open_trade'],'Ctrl+F8')
        self.assertEqual(self.settings.value(PREFIX+'open_trade'),'Ctrl+F8')

    def test_global_storage_failure_keeps_old_registration_and_settings(self):
        self.assertTrue(self.hotkey.set_hotkey('Ctrl+F8'))
        token=self.hotkey.token
        with patch.object(self.settings,'status',return_value=QSettings.AccessError):
            self.assertFalse(self.hotkey.set_hotkey('Ctrl+F9'))
        self.assertEqual(self.hotkey.active,'Ctrl+F8')
        self.assertEqual(self.hotkey.token,token)
        self.assertEqual(self.settings.value(SETTING),'Ctrl+F8')
        self.assertNotIn((token,), [call.args for call in self.backend.unregister.call_args_list])

    def test_capture_suppresses_local_and_native_global_dispatch(self):
        self.bind()
        called = Mock(); self.hotkey.activated.connect(called)
        with self.manager.recording():
            self.press(); self.hotkey._dispatch()
            self.callbacks['open_trade'].assert_not_called(); called.assert_not_called()
        self.hotkey._dispatch(); called.assert_called_once()
        self.press(); self.callbacks['open_trade'].assert_called_once()

    def test_existing_global_editor_uses_shared_capture_and_conflict_rules(self):
        widget=ShortcutSettings(self.manager,self.window)
        self.bind()
        fired=Mock(); self.hotkey.activated.connect(fired)
        def fill():
            dialog=self.app.activeModalWidget()
            edit=dialog.findChild(QKeySequenceEdit)
            self.hotkey._dispatch(); fired.assert_not_called()
            edit.setKeySequence(QKeySequence('Ctrl+F8'))
            dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.Save).click()
            self.assertTrue(dialog.isVisible())
            self.assertFalse(self.hotkey.active)
            edit.setKeySequence(QKeySequence('Ctrl+F9'))
            dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.Save).click()
        QTimer.singleShot(20,fill); widget.global_settings.choose()
        self.assertEqual(self.hotkey.active,'Ctrl+F9')
        self.hotkey._dispatch(); fired.assert_called_once()

    def test_native_x11_keys_and_existing_global_backend(self):
        if self.app.platformName() != 'xcb' or not shutil.which('xdotool'):
            self.skipTest('Requires a real X11 desktop and xdotool')
        native=GlobalHotkey(self.settings)
        self.addCleanup(native.close)
        fired=Mock(); native.activated.connect(fired)
        self.assertTrue(native.set_hotkey('Ctrl+Shift+F12'),native.error)
        self.bind(value='Ctrl+Shift+F7')
        self.activate_window()
        subprocess.run(['xdotool','key','--clearmodifiers','ctrl+shift+F7'],check=True,timeout=5)
        QTest.qWait(150)
        self.callbacks['open_trade'].assert_called_once()
        other=QWidget(); self.addCleanup(other.close)
        other.show(); other.raise_(); other.activateWindow()
        self.assertTrue(QTest.qWaitForWindowActive(other,3000))
        subprocess.run(['xdotool','key','--clearmodifiers','ctrl+shift+F7'],check=True,timeout=5)
        subprocess.run(['xdotool','key','--clearmodifiers','ctrl+shift+F12'],check=True,timeout=5)
        QTest.qWait(150)
        self.callbacks['open_trade'].assert_called_once()
        fired.assert_called_once()
        with self.manager.recording():
            # Exercise the real native backend with the same capture gate.
            native.suspended += 1
            try:
                subprocess.run(['xdotool','key','--clearmodifiers','ctrl+shift+F12'],check=True,timeout=5)
                QTest.qWait(150)
            finally:
                native.suspended -= 1
        fired.assert_called_once()
        native.close()
        subprocess.run(['xdotool','key','--clearmodifiers','ctrl+shift+F12'],check=True,timeout=5)
        QTest.qWait(100)
        fired.assert_called_once()

    def test_text_entry_dialog_popup_and_foreign_window_block(self):
        self.bind()
        for editor in (QLineEdit(self.window), QTextEdit(self.window),
                       QSpinBox(self.window), QComboBox(self.window)):
            if isinstance(editor,QComboBox): editor.setEditable(True)
            editor.show(); editor.setFocus(); QTest.qWait(10)
            self.press(editor); self.callbacks['open_trade'].assert_not_called()
            editor.hide(); editor.deleteLater()
        self.activate_window()
        dialog=QDialog(self.window); dialog.setModal(True); dialog.show(); QTest.qWait(20)
        self.press(dialog); self.callbacks['open_trade'].assert_not_called(); dialog.close()
        self.activate_window()
        menu=QMenu(self.window); menu.addAction('Popup'); menu.popup(self.window.pos())
        QTest.qWait(20); self.press(menu); self.callbacks['open_trade'].assert_not_called(); menu.close()
        other=QWidget(); other.show(); other.activateWindow(); QTest.qWait(30)
        self.press(other); self.callbacks['open_trade'].assert_not_called(); other.close()
        self.activate_window(); self.press(); self.callbacks['open_trade'].assert_called_once()

    def test_quit_delegates_to_shared_close_after_focus_change(self):
        editor=QLineEdit(self.window); editor.setText('unsaved credentials')
        self.window.pending_worker=Mock(); self.window.pending_transaction=Mock()
        self.button.setFocus()
        self.assertTrue(self.manager.set_binding('quit','Ctrl+Q'))
        self.manager.activate('quit')
        self.callbacks['quit'].assert_called_once()
        self.assertTrue(self.window.isVisible())
        self.assertEqual(editor.text(),'unsaved credentials')
        self.window.pending_worker.assert_not_called()

    def test_editor_records_changes_cancel_remove_and_confirmed_reset(self):
        widget=ShortcutSettings(self.manager, self.window)
        self.assertTrue(widget.rows['quit'][1].isEnabled())
        def fill():
            dialog=self.app.activeModalWidget()
            edit=dialog.findChild(QKeySequenceEdit)
            edit.setFocus(); QTest.keyClick(edit,Qt.Key_F8,Qt.ControlModifier)
            self.assertEqual(edit.maximumSequenceLength(),1)
            self.callbacks['open_trade'].assert_not_called()
            dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.Save).click()
        QTimer.singleShot(20,fill); widget.choose('open_trade')
        self.assertEqual(self.manager.bindings['open_trade'],'Ctrl+F8')
        def cancel(): self.app.activeModalWidget().reject()
        QTimer.singleShot(20,cancel); widget.choose('open_trade')
        self.assertEqual(self.manager.bindings['open_trade'],'Ctrl+F8')
        self.assertTrue(self.hotkey.set_hotkey('Ctrl+F9'))
        with patch.object(QMessageBox,'question',return_value=QMessageBox.No): widget.reset()
        self.assertEqual(self.manager.bindings['open_trade'],'Ctrl+F8')
        with patch.object(QMessageBox,'question',return_value=QMessageBox.Yes): widget.reset()
        self.assertFalse(any(self.manager.bindings.values()))
        self.assertEqual(self.hotkey.active,'Ctrl+F9')
        self.bind(); widget.rows['open_trade'][2].click()
        self.assertFalse(self.manager.bindings['open_trade'])

    def test_twelve_languages_help_and_both_themes(self):
        self.addCleanup(self.app.setStyleSheet,self.app.styleSheet())
        for language,translations in _TRANSLATIONS.items():
            set_language(language)
            for key in ('title','help','voiceattack','allowed','reserved','conflict','quit_disabled',
                        'save_failed','set','change','remove','reset','reset_confirm'):
                self.assertTrue(translations['shortcuts.'+key])
            self.assertIn(tr('shortcuts.voiceattack'),help_topic('settings',language).text)
            for style in (DARK_STYLESHEET,LIGHT_STYLESHEET):
                self.app.setStyleSheet(style)
                widget=ShortcutSettings(self.manager)
                widget.resize(600,800); widget.show(); self.app.processEvents()
                self.assertEqual(len(widget.rows),6)
                self.assertTrue(widget.rows['quit'][1].isEnabled())
                widget.close(); widget.deleteLater()


class MainWindowShortcutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def test_real_settings_section_and_unsaved_online_input(self):
        from cmdrhelper.ui.main_window import MainWindow
        with TemporaryDirectory() as tmp:
            w=MainWindow.__new__(MainWindow); QMainWindow.__init__(w)
            settings=QSettings(str(Path(tmp)/'keys.ini'),QSettings.IniFormat)
            w.state=SimpleNamespace(settings=settings,commander_fid='',edsm_api_key='',
                database=SimpleNamespace(list_commanders=lambda: []),
                databaseImportProgress=Mock(),databaseImportFinished=Mock())
            w.ui_theme='dark'
            hotkey=GlobalHotkey(settings,backend_factory=Mock())
            w.shortcut_manager=ShortcutManager(w,settings,hotkey,{'quit':w.close})
            def controls(_form):
                w.edsm_receive_check=QCheckBox()
                w.edsm_enabled_check=QCheckBox()
            try:
                with patch('cmdrhelper.ui.diagnostics_panel.DiagnosticsPanel',side_effect=lambda *a,**k: QWidget()), \
                        patch.object(w,'_load_selected_edsm_settings'), \
                        patch.object(w,'_load_selected_inara_settings'), \
                        patch.object(w,'_add_edsm_transfer_controls',side_effect=controls), \
                        patch.object(w,'_refresh_database_status'):
                    page=w._settings()
                w.setCentralWidget(page); w.show(); w.activateWindow()
                self.assertTrue(QTest.qWaitForWindowActive(w,3000))
                self.assertEqual(len(page.findChildren(ShortcutSettings)),1)
                self.assertIs(w.quick_favorite_settings,w.shortcut_settings.global_settings)
                w.edsm_api_key_edit.setText('unsaved synthetic value')
                w.shortcut_settings.reset_button.setFocus()
                self.assertTrue(w.shortcut_manager.set_binding('quit','Ctrl+Q'))
                QTest.keyClick(w.shortcut_settings.reset_button,Qt.Key_Q,Qt.ControlModifier)
                self.assertTrue(w.isVisible())
                self.assertEqual(w.edsm_api_key_edit.text(),'unsaved synthetic value')
                self.assertEqual(w._exit_controller.phase,'drafts')
                w._exit_controller.cancel()
            finally:
                w.hide(); hotkey.close(); w.deleteLater(); self.app.processEvents()

    def test_actual_main_navigation_and_original_exit_button(self):
        from tests.test_context_help import ContextHelpTests
        case=ContextHelpTests('test_material_navigation_is_appended_without_moving_existing_pages')
        case.app=self.app
        try:
            case.setUp()
            w=case.window
            with TemporaryDirectory() as tmp:
                w.shortcut_manager.settings=QSettings(str(Path(tmp)/'keys.ini'),QSettings.IniFormat)
                w.show(); w.activateWindow(); QTest.qWait(60)
                for action, index in [('open_explorer',w.PAGE_EXPLORER),('open_trade',w.PAGE_TRADE),
                        ('open_materials',w.PAGE_MATERIALS),('open_powerplay',w.PAGE_PP2),
                        ('open_navigator',w.PAGE_NAVIGATION)]:
                    self.assertTrue(w.shortcut_manager.set_binding(action,'Ctrl+F8'))
                    w.exit_button.setFocus()
                    QTest.keyClick(w.exit_button,Qt.Key_F8,Qt.ControlModifier)
                    self.assertEqual(w.pages.currentIndex(),index)
                    self.assertTrue(w.shortcut_manager.set_binding(action,''))
                self.assertEqual(w.navigation_tabs.currentIndex(),1)
                w.navigation_dock.detach()
                shell=w.navigation_dock.window
                w.activateWindow(); w.exit_button.setFocus(); QTest.qWait(40)
                self.assertTrue(w.shortcut_manager.set_binding('open_navigator','Ctrl+F8'))
                QTest.keyClick(w.exit_button,Qt.Key_F8,Qt.ControlModifier)
                self.assertIs(w.navigation_dock.window,shell)
                self.assertTrue(shell.isVisible())
                w.exit_button.click()
                self.assertFalse(w.isVisible()); self.assertFalse(shell.isVisible())
                self.assertIsNotNone(w.state.settings.value('main_window/geometry'))
        finally:
            case.doCleanups()
