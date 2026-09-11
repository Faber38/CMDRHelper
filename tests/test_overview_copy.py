"""Mouse interaction and clipboard feedback in the actual overview table."""
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import Qt, QSettings, QPoint
from PySide6.QtGui import QPalette
from PySide6.QtTest import QTest, QSignalSpy
from PySide6.QtWidgets import QApplication, QTableWidgetItem

from cmdrhelper.i18n import get_language, set_language, tr, _TRANSLATIONS
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from test_overview_column_widths import OverviewWindow


SYSTEM = 'Plio Aip UA-D c26-13'


class OverviewCopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(set_language, get_language())
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        self.addCleanup(self.app.clipboard().setText, self.app.clipboard().text())
        set_language('de')
        self.window = OverviewWindow(QSettings(str(Path(self.temp.name) / 'ui.ini'), QSettings.IniFormat))
        self.addCleanup(self.window.close)
        self.table = self.window.recent_systems_table
        self.hint = self.window.recent_systems_copy_hint
        self.timer = self.window.recent_systems_copy_timer
        self.addCleanup(self.timer.stop)
        self.window.state.database.recent_system_visits = lambda limit: [
            dict(visited_at='2026-09-10T10:11:12Z', system_name=SYSTEM),
            dict(visited_at='2026-09-09T08:09:10Z', system_name='Sol'),
            dict(visited_at='', system_name=''),
        ]
        self.window._refresh_recent_systems()
        self.window.resize(900, 800)
        self.window.show()
        self.app.processEvents()
        self.app.clipboard().setText('unchanged')

    def click(self, row=0, column=1, button=Qt.LeftButton):
        rect = self.table.visualItemRect(self.table.item(row, column))
        # Far from the text: the complete cell must work.
        QTest.mouseClick(self.table.viewport(), button, pos=QPoint(rect.right() - 6, rect.center().y()))
        self.app.processEvents()

    def test_click_copies_exact_system(self):
        self.click()
        self.assertEqual(self.app.clipboard().text(), SYSTEM)
        self.assertEqual(self.hint.text(), '✓ Kopiert: ' + SYSTEM)
        self.assertTrue(self.timer.isActive())
        self.assertEqual(self.timer.interval(), 1500)

    def test_click_in_time_column_copies_only_system(self):
        self.click(column=0)
        self.assertEqual(self.app.clipboard().text(), SYSTEM)

    def test_selection_is_preserved_for_entire_row(self):
        self.click(row=1, column=0)
        self.assertEqual(self.table.currentRow(), 1)
        self.assertEqual({(i.row(), i.column()) for i in self.table.selectedIndexes()}, {(1, 0), (1, 1)})
        self.assertEqual(self.app.clipboard().text(), 'Sol')

    def test_empty_placeholder_row_does_not_copy_or_confirm(self):
        self.click(row=2)
        self.assertEqual(self.app.clipboard().text(), 'unchanged')
        self.assertEqual(self.hint.text(), '')
        self.assertFalse(self.timer.isActive())

    def test_heading_without_system_metadata_does_not_copy(self):
        self.table.setItem(0, 1, QTableWidgetItem('Group heading'))
        self.click(column=0)
        self.assertEqual(self.app.clipboard().text(), 'unchanged')
        self.assertEqual(self.hint.text(), '')

    def test_missing_item_and_invalid_row_do_not_copy(self):
        self.table.takeItem(0, 1)
        self.click(column=0)
        self.window._copy_recent_system(-1, 0)
        self.window._copy_recent_system(99, 0)
        self.assertEqual(self.app.clipboard().text(), 'unchanged')
        self.assertFalse(self.timer.isActive())

    def test_invalid_metadata_does_not_copy(self):
        for value in ('', '  ', '–', None, 123):
            with self.subTest(value=value):
                self.table.item(0, 1).setData(Qt.UserRole, value)
                self.click()
                self.assertEqual(self.app.clipboard().text(), 'unchanged')
                self.assertEqual(self.hint.text(), '')

    def test_blank_viewport_and_header_do_not_copy(self):
        QTest.mouseClick(self.table.viewport(), Qt.LeftButton,
                         pos=QPoint(20, self.table.viewport().height() - 10))
        QTest.mouseClick(self.table.horizontalHeader().viewport(), Qt.LeftButton, pos=QPoint(20, 10))
        self.assertEqual(self.app.clipboard().text(), 'unchanged')

    def test_right_click_and_keyboard_selection_do_not_copy(self):
        self.click(button=Qt.RightButton)
        self.table.setFocus()
        QTest.keyClick(self.table, Qt.Key_Down)
        self.assertEqual(self.app.clipboard().text(), 'unchanged')
        self.assertFalse(self.timer.isActive())

    def test_double_click_signal_and_selection_still_work(self):
        spy = QSignalSpy(self.table.cellDoubleClicked)
        self.click()
        rect = self.table.visualItemRect(self.table.item(0, 1))
        QTest.mouseDClick(self.table.viewport(), Qt.LeftButton, pos=rect.center())
        self.assertEqual(spy.count(), 1)
        self.assertEqual(spy.at(0), [0, 1])
        self.assertEqual(self.table.currentRow(), 0)
        self.assertEqual(self.app.clipboard().text(), SYSTEM)

    def test_confirmation_expires_and_repeated_copy_restarts_timer(self):
        before = self.table.geometry()
        self.click()
        QTest.qWait(850)
        self.click(row=1)
        self.assertEqual(self.hint.text(), '✓ Kopiert: Sol')
        self.assertGreater(self.timer.remainingTime(), 1300)
        QTest.qWait(850)
        self.assertEqual(self.hint.text(), '✓ Kopiert: Sol')
        QTest.qWait(850)
        self.assertEqual(self.hint.text(), '')
        self.assertFalse(self.timer.isActive())
        self.assertEqual(self.table.geometry(), before)
        self.assertEqual(self.table.currentRow(), 1)

    def test_plain_text_confirmation_and_long_name_do_not_resize_layout(self):
        name = '<b>System & test</b> ' + 'long ' * 70
        self.table.item(0, 1).setData(Qt.UserRole, name)
        before = self.table.geometry()
        size = self.window.size()
        self.click()
        self.assertEqual(self.app.clipboard().text(), name)
        self.assertEqual(self.hint.textFormat(), Qt.PlainText)
        self.assertEqual(self.hint.text(), '✓ Kopiert: ' + name)
        self.assertEqual(self.table.geometry(), before)
        self.assertEqual(self.window.size(), size)

    def test_feedback_colors_follow_dark_and_light(self):
        self.click()
        for sheet, color in ((DARK_STYLESHEET, '#79d45a'), (LIGHT_STYLESHEET, '#37852d')):
            self.app.setStyleSheet(sheet)
            self.app.processEvents()
            self.assertEqual(self.hint.palette().color(QPalette.WindowText).name(), color)

    def test_all_twelve_languages_have_tooltip_and_confirmation(self):
        self.assertEqual(len(_TRANSLATIONS), 12)
        for language, translations in _TRANSLATIONS.items():
            with self.subTest(language=language):
                set_language(language)
                self.assertTrue(translations['overview.copy_system_tooltip'])
                self.assertIn('{system}', translations['overview.system_copied'])
                self.click()
                self.assertEqual(self.hint.text(), tr('overview.system_copied', system=SYSTEM))
                self.assertTrue(self.hint.text().startswith('✓ '))
                self.assertTrue(self.hint.text().endswith(SYSTEM))
        set_language('de')
        self.assertEqual(self.table.toolTip(),
                         'Klick auf ein System kopiert den Systemnamen in die Zwischenablage.')
