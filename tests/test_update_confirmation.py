import json
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPalette
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMessageBox, QTextBrowser

from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.release_summaries import RELEASE_SUMMARIES, release_summary
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.ui.update_confirmation import UpdateConfirmationBox


def metadata(items):
    return '<!-- cmdrhelper-update-summary\n' + json.dumps(items) + '\n-->'


class UpdateConfirmationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.language = get_language()
        self.stylesheet = self.app.styleSheet()
        set_language('de')

    def tearDown(self):
        set_language(self.language)
        self.app.setStyleSheet(self.stylesheet)

    def box(self, version='3.2', notes=''):
        window = SimpleNamespace(_release_requires_database_update=MainWindow._release_requires_database_update)
        with patch('cmdrhelper.ui.main_window.__version__', '3.1'):
            text = MainWindow._update_question_text(window, {'release_notes': notes}, version)
        box = UpdateConfirmationBox(None, tr('settings.update_available_title'), text, version, notes)
        self.addCleanup(box.close)
        return box

    def test_unknown_version_without_notes_has_original_question_and_buttons(self):
        box = self.box('4.0')
        self.assertIsNone(box.findChild(QTextBrowser))
        self.assertIn('Installiert: 3.1', box.text())
        self.assertIn('Verfügbar: 4.0', box.text())
        self.assertEqual(box.standardButtons(), QMessageBox.Yes | QMessageBox.No)
        self.assertEqual(box.defaultButton(), box.button(QMessageBox.Yes))

    def test_all_languages_and_themes_show_six_points_and_reachable_buttons(self):
        self.assertEqual(len(_TRANSLATIONS), 12)
        for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.app.setStyleSheet(theme)
            for language, table in _TRANSLATIONS.items():
                with self.subTest(language=language, dark=theme == DARK_STYLESHEET):
                    set_language(language)
                    for key in ('settings.update_changes', 'settings.update_new_in_version', *RELEASE_SUMMARIES['3.2']):
                        self.assertTrue(table[key].strip())
                    box = self.box()
                    box.show()
                    self.app.processEvents()
                    self.assertIn('3.1', box.text())
                    self.assertIn('3.2', box.text())
                    self.assertTrue(box.changes.isVisible())
                    self.assertIn(tr('settings.update_new_in_version', version='3.2'), box.changes.toPlainText())
                    for item in release_summary('3.2'):
                        self.assertIn(item, box.changes.toPlainText())
                    self.assertLessEqual(box.changes.height(), 200)
                    for answer in (QMessageBox.Yes, QMessageBox.No):
                        button = box.button(answer)
                        self.assertTrue(button.isVisible())
                        self.assertTrue(box.rect().contains(button.mapTo(box, button.rect().bottomRight())))
                        self.assertGreater(button.mapTo(box, button.rect().topLeft()).y(), box.changes.geometry().bottom())
                    palette = box.changes.palette()
                    fg = palette.color(QPalette.Text)
                    bg = palette.color(QPalette.Base)
                    def luminance(color):
                        values = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in (color.redF(), color.greenF(), color.blueF())]
                        return sum(v * w for v, w in zip(values, (.2126, .7152, .0722)))
                    light, dark = sorted((luminance(fg), luminance(bg)), reverse=True)
                    self.assertGreaterEqual((light + .05) / (dark + .05), 4.5)
                    box.close()

    def test_external_summary_is_localized_limited_escaped_and_scrollable(self):
        notes = metadata({'de': ['<b>Text</b> ' * 300] * 8, 'en': ['English point']})
        box = self.box('4.0', notes)
        box.show()
        self.app.processEvents()
        self.assertEqual(len(release_summary('4.0', notes)), 6)
        self.assertIn('<b>Text</b>', box.changes.toPlainText())
        self.assertGreater(box.changes.verticalScrollBar().maximum(), 0)
        self.assertLessEqual(box.changes.height(), 200)
        QTimer.singleShot(0, lambda: QTest.mouseClick(box.button(QMessageBox.No), Qt.LeftButton))
        self.assertEqual(box.exec(), QMessageBox.No)
        set_language('en')
        self.assertEqual(release_summary('4.0', notes), ['English point'])

    def test_v321_summary_is_localized_and_contains_only_windows_fixes(self):
        keys = RELEASE_SUMMARIES['3.2.1']
        self.assertEqual(len(keys), 4)
        self.assertTrue(all(key.startswith('release.3_2_1.') for key in keys))
        self.assertTrue(set(keys).isdisjoint(RELEASE_SUMMARIES['3.2']))
        for language, table in _TRANSLATIONS.items():
            with self.subTest(language=language):
                set_language(language)
                self.assertTrue(all(table[key].strip() for key in keys))
                summary = release_summary('v3.2.1')
                self.assertEqual(summary, [table[key] for key in keys])
                self.assertNotRegex(' '.join(summary), r'Materials|Odyssey|EDSM|ID64|Explorer|Spansh')
                box = self.box('3.2.1')
                for item in summary:
                    self.assertIn(item, box.changes.toPlainText())
        set_language('de')
        self.assertEqual(release_summary('3.2.1')[0], 'Windows-Update verbessert')
        self.assertIn('Neustart', release_summary('3.2.1')[1])
        self.assertIn('CMDRHelper läuft bereits', release_summary('3.2.1')[2])
        self.assertIn(r'\n\n', release_summary('3.2.1')[3])

    def test_invalid_or_missing_language_falls_back_without_changelog(self):
        for notes in ('# Full history\n- Old change', '<!-- cmdrhelper-update-summary broken -->', metadata({'de': [42]}), metadata({'de': []}), metadata({'en': ['English']})):
            self.assertEqual(len(release_summary('v3.2', notes)), 6)
            self.assertEqual(release_summary('4.0', notes), [])

    def test_yes_no_enter_escape_and_window_close(self):
        for version in ('3.2', '4.0'):
            for action, expected in (('yes', QMessageBox.Yes), ('no', QMessageBox.No), ('enter', QMessageBox.Yes), ('escape', QMessageBox.No), ('close', QMessageBox.No)):
                with self.subTest(version=version, action=action):
                    box = self.box(version)
                    def choose():
                        if action == 'close':
                            box.close()
                        elif action in ('enter', 'escape'):
                            QTest.keyClick(box, Qt.Key_Return if action == 'enter' else Qt.Key_Escape)
                        else:
                            QTest.mouseClick(box.button(expected), Qt.LeftButton)
                    QTimer.singleShot(0, choose)
                    self.assertEqual(box.exec(), expected)

    def test_main_window_manual_and_automatic_only_install_on_yes(self):
        for automatic in (False, True):
            for answer in (QMessageBox.Yes, QMessageBox.No):
                result = {'ok': True, 'version': '3.2', 'release_notes': ''}
                window = SimpleNamespace(
                    _update_notice_shown=False, _release_update_worker=Mock(),
                    _set_update_status=Mock(), _update_question_text=Mock(return_value='question'),
                    _install_update=Mock(),
                )
                with patch('cmdrhelper.ui.main_window.UpdateConfirmationBox') as dialog, patch('cmdrhelper.ui.main_window.QTimer.singleShot'), patch('cmdrhelper.ui.main_window.__version__', '3.1'):
                    dialog.return_value.exec.return_value = answer
                    MainWindow._update_check_finished(window, result, automatic)
                    dialog.assert_called_once()
                    self.assertEqual(window._install_update.call_count, int(answer == QMessageBox.Yes))
                    if answer == QMessageBox.Yes:
                        window._install_update.assert_called_once_with(result)
                    if automatic:
                        MainWindow._update_check_finished(window, result, automatic)
                        dialog.assert_called_once()
