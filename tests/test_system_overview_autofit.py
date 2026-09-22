"""One-shot overview fitting, with isolated settings and no station requests."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from shiboken6 import isValid
from PySide6.QtCore import QEvent, QPoint, QPointF, QSettings, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from cmdrhelper.i18n import get_language, set_language, tr
from cmdrhelper.help_content import HELP_LANGUAGES
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.ui.system_overview import SystemOverviewDialog

SETTING = 'system_overview/auto_fit'
BODIES = [dict(body_id=0, name='Test', body_type='Star', star_type='G')] + [
    dict(body_id=i, parent_id=0, name=f'Test {i}', body_type='Planet',
         planet_class='Rocky body') for i in range(1, 15)
]


class OverviewAutoFitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.ini = str(Path(temp.name) / 'overview.ini')
        self.settings = QSettings(self.ini, QSettings.IniFormat)
        self.addCleanup(set_language, get_language())
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())

    def dialog(self, *, settings=None, show=True, **kwargs):
        dialog = SystemOverviewDialog('Test', BODIES, settings=settings or self.settings, **kwargs)
        self.addCleanup(lambda: dialog.close() if isValid(dialog) else None)
        dialog.preview.fit_system = Mock(wraps=dialog.preview.fit_system)
        if show:
            dialog.show()
            self.app.processEvents()
            self.app.processEvents()
        return dialog

    def test_default_on_fits_once_after_show_with_real_layout(self):
        dialog = self.dialog(show=False)
        self.assertTrue(dialog.auto_fit_checkbox.isChecked())
        dialog.preview.fit_system.assert_not_called()
        dimensions = []
        fit = dialog.preview.fit_system._mock_wraps
        def checked_fit():
            dimensions.append((dialog.isVisible(), dialog.preview.viewport().size(),
                               dialog.preview.sceneRect()))
            fit()
        dialog.preview.fit_system.side_effect = checked_fit
        dialog.show()
        for _ in range(3):
            self.app.processEvents()
        dialog.preview.fit_system.assert_called_once_with()
        self.assertTrue(dimensions[0][0])
        self.assertGreater(dimensions[0][1].width(), 500)
        self.assertGreater(dimensions[0][2].width(), dimensions[0][1].width())
        self.assertLess(dialog.preview.transform().m11(), 1)
        bounds = dialog.preview.mapFromScene(dialog.preview.sceneRect()).boundingRect()
        self.assertLessEqual(bounds.width(), dialog.preview.viewport().width())
        self.assertLessEqual(bounds.height(), dialog.preview.viewport().height())
        dialog.hide()
        dialog.show()
        self.app.processEvents()
        dialog.preview.fit_system.assert_called_once_with()

    def test_off_on_open_never_fits(self):
        self.settings.setValue(SETTING, False)
        dialog = self.dialog()
        self.assertFalse(dialog.auto_fit_checkbox.isChecked())
        dialog.preview.fit_system.assert_not_called()
        self.assertEqual(dialog.preview.transform().m11(), 1)

    def test_toggle_on_fits_once_off_preserves_zoom(self):
        self.settings.setValue(SETTING, False)
        dialog = self.dialog()
        dialog.auto_fit_checkbox.setChecked(True)
        dialog.preview.fit_system.assert_called_once_with()
        dialog.preview.scale(1.2, 1.2)
        zoom = dialog.preview.transform()
        dialog.auto_fit_checkbox.setChecked(False)
        self.app.processEvents()
        self.assertEqual(dialog.preview.transform(), zoom)
        dialog.preview.fit_system.assert_called_once_with()

    def test_manual_zoom_scroll_resize_and_buttons_remain_independent(self):
        dialog = self.dialog()
        view = dialog.preview
        wheel = QWheelEvent(QPointF(50, 50), QPointF(50, 50), QPoint(), QPoint(0, 120),
                            Qt.NoButton, Qt.ControlModifier, Qt.ScrollPhase.NoScrollPhase, False)
        before = view.transform()
        QApplication.sendEvent(view.viewport(), wheel)
        self.assertNotEqual(before, view.transform())
        zoom = view.transform()
        view.horizontalScrollBar().setValue(view.horizontalScrollBar().maximum())
        self.app.processEvents()
        self.assertEqual(view.horizontalScrollBar().value(), view.horizontalScrollBar().maximum())
        dialog.resize(dialog.width() + 100, dialog.height() + 100)
        for _ in range(3):
            self.app.processEvents()
        self.assertEqual(view.transform(), zoom)
        view.fit_system.assert_called_once_with()
        QTest.mouseClick(dialog.reset_button, Qt.LeftButton)
        self.assertEqual(view.transform().m11(), 1)
        QTest.mouseClick(dialog.fit_button, Qt.LeftButton)
        self.assertLess(view.transform().m11(), 1)
        # Checkbox OFF does not disable either manual action.
        dialog.auto_fit_checkbox.setChecked(False)
        QTest.mouseClick(dialog.reset_button, Qt.LeftButton)
        self.assertEqual(view.transform().m11(), 1)
        QTest.mouseClick(dialog.fit_button, Qt.LeftButton)
        self.assertLess(view.transform().m11(), 1)
        self.app.processEvents()
        self.assertEqual(view.fit_system.call_count, 3)  # one automatic and two manual fits

    def test_global_preference_survives_reinstantiation_and_multiple_windows(self):
        first = self.dialog()
        first.auto_fit_checkbox.setChecked(False)
        second = self.dialog(settings=QSettings(self.ini, QSettings.IniFormat), commander_id='synthetic-b')
        self.assertFalse(second.auto_fit_checkbox.isChecked())
        second.preview.fit_system.assert_not_called()
        second.auto_fit_checkbox.setChecked(True)
        second.preview.fit_system.assert_called_once_with()
        third = self.dialog(settings=QSettings(self.ini, QSettings.IniFormat), system_address=42)
        self.assertTrue(third.auto_fit_checkbox.isChecked())
        third.preview.fit_system.assert_called_once_with()
        self.assertFalse(first.auto_fit_checkbox.isChecked())
        self.assertTrue(QSettings(self.ini, QSettings.IniFormat).value(SETTING, type=bool))

    def test_persisted_false_string_is_not_truthy(self):
        self.settings.setValue(SETTING, 'false')
        dialog = self.dialog()
        self.assertFalse(dialog.auto_fit_checkbox.isChecked())
        dialog.preview.fit_system.assert_not_called()

    def test_all_languages_themes_and_font_sizes_fit_controls(self):
        for language in HELP_LANGUAGES:
            set_language(language)
            for light, style in ((False, DARK_STYLESHEET), (True, LIGHT_STYLESHEET)):
                for size in (10, 18, 24):
                    with self.subTest(language=language, light=light, size=size):
                        self.app.setStyleSheet(style + f'\nQWidget {{ font-size: {size}pt; }}')
                        dialog = self.dialog(light=light)
                        check = dialog.auto_fit_checkbox
                        self.assertEqual(check.text(), tr('explorer.overview_auto_fit'))
                        self.assertEqual(check.toolTip(), tr('explorer.overview_auto_fit_hint'))
                        self.assertGreaterEqual(check.width(), check.sizeHint().width())
                        for widget in (check, dialog.reset_button, dialog.fit_button, dialog.spansh_button):
                            self.assertTrue(dialog.rect().contains(widget.geometry()))
                        self.assertLessEqual(dialog.width(), 1100)
                        self.assertFalse(dialog.grab().isNull())
                        capture = os.environ.get('CMDR_BLOCK4_CAPTURES')
                        if capture and language in ('de', 'en', 'fr', 'el') and size == 24:
                            dialog.grab().save(str(Path(capture) / f'overview-{language}-{light}-{size}.png'))
                        dialog.close()
                        dialog.deleteLater()
                        self.app.sendPostedEvents(None, QEvent.DeferredDelete)
