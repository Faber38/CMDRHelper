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

    def test_upload_only_matrix(self):
        label = self.main.edsm_upload_label
        cases = [('ok', 3, 'success', 'statusOk'),
                 ('ok', 0, 'unknown', 'muted'),
                 ('unknown', 0, 'unknown', 'muted'),
                 ('waiting', 0, 'waiting', 'statusWarn'),
                 ('running', 3, 'waiting', 'statusWarn'),
                 ('error', 3, 'error', 'statusError')]
        self.state.edsm_settings_for_fid = Mock(side_effect=AssertionError('No connection test read'))
        for enabled in (False, True):
            for upload, count, key, style in cases:
                for receive in ('EDSM', 'Cache', 'Zeitüberschreitung bei der EDSM-Anfrage.', ''):
                    with self.subTest(enabled=enabled, upload=upload, count=count, receive=receive):
                        self.state.edsm_enabled = enabled
                        self.state.edsm_receive_enabled = True
                        self.state.edsm_source_status = receive
                        self.state.edsm_upload_status = upload
                        self.state.edsm_upload_details = {'confirmed': count}
                        self.main._refresh_edsm_status()
                        self.assertEqual(label.text(), tr('topbar.edsm_' + (key if enabled else 'off')))
                        self.assertEqual(label.objectName(), style if enabled else 'muted')
                        for excluded in ('receive', 'test', 'cache'):
                            self.assertNotIn(tr('edsm_service.' + excluded), label.toolTip())

    def test_connection_test_is_diagnostic_only(self):
        page = QWidget(); self.addCleanup(page.deleteLater)
        self.main._add_edsm_transfer_controls(QFormLayout(page))
        self.main.edsm_receive_check.setChecked(True)
        self.main._refresh_edsm_status()
        self.main.edsm_test_button = QPushButton()
        self.main.edsm_test_status = QLabel()
        self.main.edsm_commander_edit = QLineEdit('Synthetic')
        self.main.edsm_api_key_edit = QLineEdit('SYNTHETIC')
        self.main.edsm_commander_combo = QComboBox()
        self.main.edsm_commander_combo.addItem('Alpha', 'F-A')
        self.main.edsm_commander_combo.addItem('Beta', 'F-B')
        for index in (0, 1):
            self.main.edsm_commander_combo.setCurrentIndex(index)
            for ok in (False, True):
                with patch('cmdrhelper.ui.main_window.test_edsm_connection', return_value=(ok, 'Synthetic')) as fetch:
                    self.main._test_edsm_connection()
                    fetch.assert_called_once()
                self.assertEqual(self.main.edsm_upload_label.text(), tr('topbar.edsm_off'))
                self.assertNotIn('Synthetic', self.main.edsm_upload_label.toolTip())

    def test_queued_upload_start_and_results_refresh_original_fid(self):
        import threading
        from PySide6.QtCore import QObject
        from cmdrhelper.source_manager import SourceManager
        from cmdrhelper.edsm_upload_status import publish
        manager = SourceManager.__new__(SourceManager)
        QObject.__init__(manager)
        self.addCleanup(manager.deleteLater)
        state = SimpleNamespace(commander_fid='A', edsm_enabled=True,
            _edsm_runtime_by_fid={}, changed=Mock(), _startup_cancel=threading.Event())
        manager.state = state
        manager.runtimes = {'steam': SimpleNamespace(generation=1)}
        manager.edsmUploadChanged.connect(manager._edsm_upload_changed, Qt.QueuedConnection)
        publish(state)
        manager.edsmUploadChanged.emit('steam', 1, 'A', {'running': True})
        self.assertEqual(state.edsm_upload_status, 'unknown')
        self.app.processEvents()
        self.assertEqual(state.edsm_upload_status, 'running')
        manager.edsmUploadChanged.emit('steam', 1, 'A',
            {'events_confirmed': 2, 'confirmation_complete': True})
        state.commander_fid = 'B'; publish(state)
        self.app.processEvents()
        self.assertEqual(state.edsm_upload_status, 'unknown')
        state.commander_fid = 'A'; publish(state)
        self.assertEqual(state.edsm_upload_status, 'ok')
        self.assertEqual(state.edsm_upload_details['confirmed'], 2)

    def test_only_allowlisted_error_details_reach_tooltip(self):
        self.state.edsm_enabled = self.state.edsm_receive_enabled = True
        self.state.edsm_upload_status = 'error'
        messages = [
            'EDSM nicht erreichbar: SECRET_TOKEN /home/private/journal.log',
            'https://user:password@example.invalid/?apiKey=SECRET_TOKEN',
            'Authorization: Bearer SECRET_TOKEN',
            r'C:\Users\Private\SECRET_TOKEN.log',
            '<img src="https://example.invalid/SECRET_TOKEN">',
            'EDSM HTTP-Fehler 500. SECRET_TOKEN',
            'SECRET_TOKEN',
        ]
        self.configs['F-A']['last_test_status'] = 'error|SECRET_TEST /private/path'
        for message in messages:
            with self.subTest(message=message):
                self.state.edsm_upload_message = self.state.edsm_source_status = message
                self.state.edsm_upload_details = {'errors': (message,)}
                self.main._refresh_edsm_status()
                tip = self.main.edsm_upload_label.toolTip()
                for secret in ('SECRET', 'password', '/home', '/private', 'C:\\', 'https:', '<img', 'Bearer'):
                    self.assertNotIn(secret, tip)
                self.assertNotIn(tr('edsm_service.timeout'), tip)
        from cmdrhelper.ui.edsm_status import error_detail
        for message, key, kwargs in [
            ('EDSM HTTP-Fehler 429.', 'http', {'code': 429}),
            ('EDSM: Upload abgelehnt (Code 203)', 'api', {'code': 203}),
            ('EDSM hat nicht alle Ereignisse bestätigt.', 'partial_reply', {}),
            ('EDSM hat keine gültige JSON-Antwort geliefert.', 'invalid_reply', {}),
            ('EDSM nicht erreichbar.', 'transport', {}),
            ('anything else', 'unknown_error', {}),
        ]:
            self.assertEqual(error_detail(message), tr('edsm_service.' + key, **kwargs))

    def test_status_translations_and_theme_colors(self):
        self.state.edsm_enabled = True
        self.state.edsm_upload_details = {'confirmed': 4}
        keys = [k for k in _TRANSLATIONS['en'] if k.startswith(('edsm_service.', 'topbar.edsm_'))]
        for language in _TRANSLATIONS:
            set_language(language)
            for key in keys:
                self.assertTrue(_TRANSLATIONS[language][key].strip(), (language, key))
            for sheet, colors in [(DARK_STYLESHEET, ('#79d45a', '#f0ad4e', '#ff6b6b')),
                                  (LIGHT_STYLESHEET, ('#37852d', '#b36a00', '#b83232'))]:
                self.app.setStyleSheet(sheet)
                for upload, color in zip(('ok', 'running', 'error'), colors):
                    self.state.edsm_upload_status = upload
                    self.main._refresh_edsm_status()
                    label = self.main.edsm_upload_label
                    label.ensurePolished()
                    self.assertEqual(label.palette().color(QPalette.WindowText).name(), color)
                    self.assertEqual(label.textFormat(), Qt.PlainText)
                    self.assertIn(tr('edsm_service.confirmed', count=4), label.toolTip())

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
