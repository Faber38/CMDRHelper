"""EDSM presentation only: private settings, no network or journal watcher."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette
from PySide6.QtWidgets import (QApplication, QLabel, QFormLayout, QWidget,
                             QScrollArea, QPushButton, QLineEdit, QComboBox)
from cmdrhelper.i18n import tr, get_language, set_language, _TRANSLATIONS
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests.test_popup_ui_settings import PopupUiSettingsTests


class EdsmUiStatusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.addCleanup(set_language, get_language())
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        self.helper = PopupUiSettingsTests()
        self.helper.setUpClass(); self.helper.setUp()
        self.addCleanup(self.helper.doCleanups)
        self.main = self.helper.main()
        self.state = self.main.state
        self.configs = {'F-A': {'last_test_status': ''}, 'F-B': {'last_test_status': ''}}
        self.state.commander_fid = 'F-A'
        self.state.edsm_enabled = False
        self.state.edsm_receive_enabled = False
        self.state.edsm_upload_status = 'disabled'
        self.state.edsm_settings_for_fid = lambda fid: self.configs[fid]
        def save(fid, ok, text):
            self.configs[fid]['last_test_status'] = ('ok' if ok else 'error') + '|' + text
        self.state.set_edsm_test_status = save
        for target in ('cmdrhelper.edsm_uploader.urlopen', 'cmdrhelper.online_services.urlopen'):
            guard = patch(target, side_effect=AssertionError('No requests allowed'))
            guard.start(); self.addCleanup(guard.stop)

    def test_existing_label_and_four_combinations(self):
        label = self.main.edsm_upload_label
        self.assertIsNotNone(label.parentWidget())
        for send in (False, True):
            for receive in (False, True):
                self.state.edsm_enabled = send
                self.state.edsm_receive_enabled = receive
                self.main._refresh_edsm_status()
                key = 'topbar.edsm_waiting' if send else 'topbar.edsm_receiving' if receive else 'topbar.edsm_off'
                self.assertEqual(label.text(), tr(key))
                self.assertIn(tr('settings.edsm_send') + (': ✓' if send else ': –'), label.toolTip())
                self.assertIn(tr('settings.edsm_receive') + (': ✓' if receive else ': –'), label.toolTip())

    def test_off_overrides_stale_success_and_error(self):
        for status in ('ok', 'error'):
            self.state.edsm_upload_status = status
            self.configs['F-A']['last_test_status'] = status+'|Synthetic'
            self.main._refresh_edsm_status()
            self.assertEqual(self.main.edsm_upload_label.text(), tr('topbar.edsm_off'))
            self.assertEqual(self.main.edsm_upload_label.objectName(), 'muted')

    def test_connection_test_refreshes_only_active_commander_without_upload_claim(self):
        self.state.edsm_receive_enabled = True
        page = QWidget(); self.addCleanup(page.deleteLater)
        self.main._add_edsm_transfer_controls(QFormLayout(page))
        self.main.edsm_receive_check.setChecked(True)
        self.main.edsm_test_button = QPushButton()
        self.main.edsm_test_status = QLabel()
        self.main.edsm_commander_edit = QLineEdit('Synthetic')
        self.main.edsm_api_key_edit = QLineEdit('SYNTHETIC')
        self.main.edsm_commander_combo = QComboBox()
        self.main.edsm_commander_combo.addItem('Alpha', 'F-A')
        self.main.edsm_commander_combo.addItem('Beta', 'F-B')
        for ok in (True, False):
            with patch('cmdrhelper.ui.main_window.test_edsm_connection', return_value=(ok, 'Synthetic')) as fetch:
                self.main._test_edsm_connection()
                fetch.assert_called_once()
            self.assertEqual(self.state.edsm_upload_status, 'disabled')
            self.assertEqual(self.main.edsm_upload_label.objectName(), 'statusOk' if ok else 'statusWarn')
            self.assertIn(tr('topbar.edsm_connection_ok' if ok else 'topbar.edsm_connection_error'), self.main.edsm_upload_label.toolTip())
            self.assertNotEqual(self.main.edsm_upload_label.text(), tr('topbar.edsm_transmitting'))
        self.main.edsm_commander_combo.setCurrentIndex(1)
        with patch('cmdrhelper.ui.main_window.test_edsm_connection', return_value=(True, 'Synthetic')):
            self.main._test_edsm_connection()
        self.assertEqual(self.main.edsm_upload_label.objectName(), 'statusWarn')
        self.state.commander_fid = 'F-B'
        self.main._refresh_edsm_status()
        self.assertEqual(self.main.edsm_upload_label.objectName(), 'statusOk')

    def test_upload_and_receive_errors_respect_switches(self):
        self.state.edsm_enabled = True
        for status, style in [('error', 'statusWarn'), ('ok', 'statusOk'), ('waiting', 'muted')]:
            self.state.edsm_upload_status = status
            self.main._refresh_edsm_status()
            self.assertEqual(self.main.edsm_upload_label.objectName(), style)
            self.assertNotEqual(self.main.edsm_upload_label.text(), tr('topbar.edsm_transmitting'))
        self.state.edsm_enabled = False
        self.state.edsm_receive_enabled = True
        self.state.edsm_source_status = 'Synthetic receive error'
        self.main._refresh_edsm_status()
        self.assertEqual(self.main.edsm_upload_label.objectName(), 'statusWarn')
        self.state.edsm_source_status = 'EDSM'
        self.main._refresh_edsm_status()
        self.assertEqual(self.main.edsm_upload_label.objectName(), 'muted')

    def test_hint_all_languages_themes_narrow_layout_and_large_font(self):
        self.assertEqual(len(_TRANSLATIONS), 12)
        for lang in _TRANSLATIONS:
            set_language(lang)
            for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                with self.subTest(language=lang, theme=style[:20]):
                    self.app.setStyleSheet(style)
                    scroll = QScrollArea(); scroll.setWidgetResizable(True)
                    page = QWidget(); form = QFormLayout(page)
                    font = QFont(page.font()); font.setPointSize(18); page.setFont(font)
                    self.main._add_edsm_transfer_controls(form)
                    hint = self.main.edsm_upload_hint
                    self.assertEqual(hint.text(), _TRANSLATIONS[lang]['settings.edsm_other_uploader_hint'])
                    self.assertTrue(hint.wordWrap())
                    self.assertEqual(form.getWidgetPosition(self.main.edsm_transfer_row)[0]+1,
                                     form.getWidgetPosition(hint)[0])
                    self.assertTrue(self.main.edsm_enabled_check.isEnabled())
                    self.main.edsm_enabled_check.setChecked(True)
                    self.assertTrue(self.main.edsm_enabled_check.isChecked())
                    scroll.setWidget(page); scroll.resize(360, 260); scroll.show()
                    self.app.processEvents()
                    scroll.ensureWidgetVisible(hint)
                    self.app.processEvents()
                    expected_color = '#f0ad4e' if style == DARK_STYLESHEET else '#b36a00'
                    self.assertEqual(hint.palette().color(QPalette.WindowText).name(), expected_color)
                    send = self.main.edsm_enabled_check
                    receive = self.main.edsm_receive_check
                    receive.setChecked(False)
                    self.assertTrue(send.isChecked())
                    receive.setChecked(True)
                    send.setChecked(False)
                    self.assertTrue(receive.isChecked())
                    wrapped = False
                    for width in (180, 1100, 360, 180):
                        scroll.resize(width, 260)
                        self.app.processEvents()
                        self.app.processEvents()
                        self.assertFalse(send.geometry().intersects(receive.geometry()))
                        for check in (send, receive):
                            self.assertGreaterEqual(check.width(), check.minimumSizeHint().width())
                        required = send.minimumWidth() + receive.minimumWidth() + 20
                        if self.main.edsm_transfer_row.width() >= required:
                            self.assertEqual(send.y(), receive.y())
                            self.assertLess(send.geometry().right(), receive.x())
                        else:
                            self.assertGreater(receive.y(), send.y())
                            wrapped = True
                    self.assertTrue(wrapped)
                    self.assertGreater(hint.width(), 0)
                    self.assertGreaterEqual(hint.height(), hint.heightForWidth(hint.width()))
                    self.assertFalse(scroll.grab().isNull())
                    scroll.close(); scroll.deleteLater()

    def test_real_refresh_calls_status_renderer_and_settings_use_controls(self):
        import inspect
        self.assertIn('self._refresh_edsm_status()', inspect.getsource(MainWindow.refresh_all))
        self.assertIn('self._add_edsm_transfer_controls(edsm_form)', inspect.getsource(MainWindow._settings))
