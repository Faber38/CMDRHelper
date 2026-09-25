"""Inline copy controls in the real overview, with isolated settings/data."""
import unittest

from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QHelpEvent
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QStyleOptionViewItem, QToolButton, QToolTip

from cmdrhelper.i18n import _TRANSLATIONS
from cmdrhelper.ui.main_window import ChronicleSystemWindow
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
import test_overview_copy as overview_tests

SYSTEM = overview_tests.SYSTEM


class RecentSystemCopyIconTests(unittest.TestCase):
    setUpClass = classmethod(overview_tests.OverviewCopyTests.setUpClass.__func__)
    setUp = overview_tests.OverviewCopyTests.setUp

    def geometry(self, row):
        index = self.table.model().index(row, 1)
        option = QStyleOptionViewItem()
        option.initFrom(self.table)
        option.font = self.table.font()
        self.table.itemDelegateForColumn(1).initStyleOption(option, index)
        option.rect = self.table.visualRect(index)
        rect, text = self.table.itemDelegateForColumn(1).copy_rect(option, index)
        return rect, text, option

    def click_icon(self, row):
        rect, _, _ = self.geometry(row)
        self.assertFalse(rect.isEmpty())
        QTest.mouseClick(self.table.viewport(), Qt.LeftButton, pos=rect.center())
        self.app.processEvents()

    def populate(self, names):
        self.window.state.database.recent_system_visits = lambda limit: [
            dict(visited_at='2026-09-24T12:34:56Z', system_name=name) for name in names
        ]
        self.window._refresh_recent_systems()
        self.app.processEvents()

    def test_one_and_multiple_entries_after_refresh(self):
        for names in (['Sol'], ['Sol', SYSTEM, '银河 Δοκιμή İı Å'], ['New system', 'Achenar']):
            self.populate(names)
            self.assertEqual(self.table.rowCount(), len(names))
            for row, name in enumerate(names):
                self.click_icon(row)
                self.assertEqual(self.app.clipboard().text(), name)

    def test_symbol_click_does_not_emit_row_actions_or_change_selection(self):
        self.table.selectRow(1)
        clicked = QSignalSpy(self.table.cellClicked)
        doubled = QSignalSpy(self.table.cellDoubleClicked)
        copied = QSignalSpy(self.window.recent_systems_copy_delegate.copyRequested)
        self.click_icon(0)
        self.assertEqual(self.app.clipboard().text(), SYSTEM)
        self.assertEqual(copied.count(), 1)
        QTest.mouseDClick(self.table.viewport(), Qt.LeftButton, pos=self.geometry(0)[0].center())
        self.assertEqual(clicked.count(), 0)
        self.assertEqual(doubled.count(), 0)
        self.assertEqual(self.table.currentRow(), 1)

    def test_name_click_and_double_click_keep_normal_actions(self):
        clicked = QSignalSpy(self.table.cellClicked)
        doubled = QSignalSpy(self.table.cellDoubleClicked)
        rect = self.table.visualItemRect(self.table.item(1, 1))
        point = QPoint(rect.left() + 8, rect.center().y())
        QTest.mouseClick(self.table.viewport(), Qt.LeftButton, pos=point)
        QTest.mouseDClick(self.table.viewport(), Qt.LeftButton, pos=point)
        self.assertEqual(clicked.count(), 1)
        self.assertEqual(doubled.count(), 1)
        self.assertEqual(self.table.currentRow(), 1)
        self.assertEqual(self.app.clipboard().text(), 'Sol')

    def test_placeholder_and_right_click_do_not_copy(self):
        self.assertTrue(self.geometry(2)[0].isEmpty())
        QTest.mouseClick(self.table.viewport(), Qt.RightButton, pos=self.geometry(0)[0].center())
        self.assertEqual(self.app.clipboard().text(), 'unchanged')

    def test_drag_away_cancels_copy_and_hover_cursor(self):
        rect = self.geometry(0)[0]
        QTest.mouseMove(self.table.viewport(), rect.center())
        self.assertEqual(self.table.viewport().cursor().shape(), Qt.PointingHandCursor)
        QTest.mousePress(self.table.viewport(), Qt.LeftButton, pos=rect.center())
        point = QPoint(5, rect.center().y())
        QTest.mouseMove(self.table.viewport(), point)
        QTest.mouseRelease(self.table.viewport(), Qt.LeftButton, pos=point)
        self.assertEqual(self.app.clipboard().text(), 'unchanged')
        self.assertNotEqual(self.table.viewport().cursor().shape(), Qt.PointingHandCursor)

    def test_dark_light_font_and_width_matrix(self):
        long_name = '银河 Eorl Auwsy BA-A g98 ' * 12
        self.populate(['Sol', long_name])
        for sheet in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            for points in (10, 18, 24):
                self.app.setStyleSheet(sheet + self.window._font_stylesheet_suffix(size=points))
                for width in (440, 900):
                    with self.subTest(theme=sheet[:30], points=points, width=width):
                        self.window.resize(width, 800)
                        self.table.setFixedWidth(width - 40)
                        self.app.processEvents()
                        before = self.table.horizontalScrollBar().maximum()
                        for row, name in enumerate(('Sol', long_name)):
                            rect, text, option = self.geometry(row)
                            self.assertTrue(option.rect.contains(rect))
                            self.assertGreaterEqual(rect.height(), option.fontMetrics.height())
                            text_right = option.rect.left() + 3 + option.fontMetrics.horizontalAdvance(text)
                            self.assertEqual(rect.left() - text_right, 4)
                            if row == 1:
                                self.assertNotEqual(text, name)
                                self.assertIn('…', text)
                            self.click_icon(row)
                            self.assertEqual(self.app.clipboard().text(), name)
                        self.assertEqual(self.table.horizontalScrollBar().maximum(), before)
                        self.assertEqual(before, 0)
                        self.table.grab()  # Exercise actual painting for every combination.

    def test_tooltip_key_is_present_in_all_twelve_languages(self):
        self.assertEqual(len(_TRANSLATIONS), 12)
        for translations in _TRANSLATIONS.values():
            self.assertTrue(translations['recommend.copy_system'])
        point = self.geometry(0)[0].center()
        event = QHelpEvent(QEvent.ToolTip, point, self.table.viewport().mapToGlobal(point))
        self.app.sendEvent(self.table.viewport(), event)
        self.assertEqual(QToolTip.text(), 'System kopieren')
        QToolTip.hideText()

    def test_chronicle_button_appearance_and_copy_unchanged(self):
        window = ChronicleSystemWindow('银河 Sol', [], '', lambda *_: None)
        self.addCleanup(window.close)
        window.show()
        self.app.processEvents()
        button = window.findChild(QToolButton, 'chronicleCopySystemName')
        self.assertEqual(button.text(), '⧉')
        self.assertTrue(button.autoRaise())
        self.assertEqual(button.toolTip(), '')
        self.assertEqual(self.window.recent_systems_copy_delegate._button.text(), button.text())
        QTest.mouseClick(button, Qt.LeftButton)
        self.assertEqual(self.app.clipboard().text(), '银河 Sol')
        self.assertEqual(button.text(), '✓')
