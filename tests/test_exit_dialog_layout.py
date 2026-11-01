"""Waiting-dialog geometry and delayed work, using isolated settings only."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import unittest

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMainWindow, QDialogButtonBox
from cmdrhelper.ui.exit_controller import ExitDialog
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr


class ExitDialogLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_languages_themes_fonts_status_changes_and_screen_bounds(self):
        language, style = get_language(), self.app.styleSheet()
        self.addCleanup(set_language, language)
        self.addCleanup(self.app.setStyleSheet, style)
        results = []
        for theme, sheet in [('dark', DARK_STYLESHEET), ('light', LIGHT_STYLESHEET)]:
            for font_size in (12, 18, 24):
                self.app.setStyleSheet(sheet + f'\nQWidget {{ font-size: {font_size}px; }}')
                for language in _TRANSLATIONS:
                    with self.subTest(theme=theme, font=font_size, language=language):
                        set_language(language)
                        window = QMainWindow()
                        window.resize(700, 450)
                        window.move(-80, -60)  # Partly off-screen owner must not hide the dialog.
                        window.show()
                        controller = SimpleNamespace(window=window, cancel=Mock(), poll=Mock())
                        dialog = ExitDialog(controller)
                        try:
                            dialog.show()
                            QTest.qWait(30)
                            sizes = []
                            for key in ('exit.wait', 'exit.wait_count', 'exit.wait_long', 'exit.write_failed', 'exit.wait'):
                                dialog.message.setText(tr(key, count=7))
                                QTest.qWait(15)
                                self.check_geometry(dialog)
                                sizes.append((dialog.width(), dialog.height()))
                                results.append(dict(theme=theme, font=font_size, language=language,
                                                    key=key, width=dialog.width(), height=dialog.height(),
                                                    scrolling=dialog.message_area.verticalScrollBar().maximum() > 0))
                                output = os.environ.get('CMDRHELPER_EXIT_LAYOUT_MEASUREMENTS')
                                if output and language == 'de' and font_size == 12 and key == 'exit.wait_long':
                                    dialog.grab().save(str(Path(output).with_name(Path(output).stem + '-' + theme + '.png')))
                            # X11 decorations can arrive after the first show event.
                            frame = dialog.frameGeometry()
                            self.assertLessEqual(abs(sizes[0][0] - sizes[-1][0]),
                                                 max(2, frame.width() - dialog.width()))
                            self.assertLessEqual(abs(sizes[0][1] - sizes[-1][1]),
                                                 max(2, frame.height() - dialog.height()))
                            dialog.message.setText(('Long status / ' * 1000) + '<not markup>')
                            QTest.qWait(15)
                            self.check_geometry(dialog)
                            self.assertEqual(dialog.message.textFormat(), Qt.PlainText)
                            self.assertGreater(dialog.message_area.verticalScrollBar().maximum(), 0)
                            dialog.buttons.button(QDialogButtonBox.Cancel).click()
                            controller.cancel.assert_called_once()
                        finally:
                            dialog.hide(); dialog.deleteLater()
                            window.hide(); window.deleteLater()
                            self.app.processEvents()
        output = os.environ.get('CMDRHELPER_EXIT_LAYOUT_MEASUREMENTS')
        if output:
            Path(output).write_text(json.dumps(results, indent=2))

    def check_geometry(self, dialog):
        screen = dialog.screen().availableGeometry()
        self.assertTrue(screen.contains(dialog.frameGeometry()), (screen, dialog.frameGeometry()))
        self.assertGreaterEqual(dialog.width(), min(450, screen.width() - 32))
        area = dialog.message_area
        label = dialog.message
        self.assertGreaterEqual(label.height(), label.heightForWidth(label.width()))
        self.assertEqual(area.horizontalScrollBar().maximum(), 0)
        self.assertGreater(area.viewport().height(), 0)
        self.assertGreaterEqual(label.width(), area.viewport().width())
        for button in dialog.buttons.buttons():
            self.assertGreaterEqual(button.width(), button.sizeHint().width())
            self.assertGreaterEqual(button.height(), button.sizeHint().height())
            self.assertTrue(dialog.rect().contains(button.mapTo(dialog, button.rect().bottomRight())))

    def test_real_wait_dialog_delayed_work_cancel_repeat_and_auto_close(self):
        from tests.test_safe_exit import SafeExitTests
        case = SafeExitTests('test_wait_dialog_repeated_shortcut_cannot_skip_running_worker')
        case.app = self.app
        try:
            case.setUp()
            case.w.resize(900, 650)
            self.assertTrue(case.w.shortcut_manager.set_binding('quit', 'Ctrl+Q'))
            _, release = case.work()
            self.assertFalse(case.w.close())
            controller = case.w._exit_controller
            dialog = controller.dialog
            QTest.qWait(250)  # Only the test holds work back; no production delay.
            self.check_geometry(dialog)
            dialog.activateWindow()
            QTest.qWait(30)
            QTest.keyClick(dialog, Qt.Key_Q, Qt.ControlModifier)
            self.assertIs(controller.dialog, dialog)
            self.assertTrue(case.w.isVisible())
            dialog.buttons.button(QDialogButtonBox.Cancel).click()
            self.assertEqual(controller.phase, 'idle')
            self.assertTrue(case.w.isVisible())
            self.assertFalse(case.w.close())
            QTest.qWait(50)
            release.set()
            case.wait(lambda: not case.w.isVisible(), timeout=2000)
            self.assertIsNone(controller.dialog)
        finally:
            case.doCleanups()
