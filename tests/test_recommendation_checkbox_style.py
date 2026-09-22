"""Paint-only checks for the recommendation table's remember column."""
import os
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QEvent, QRect, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import (QApplication, QStyle, QStyledItemDelegate,
                              QStyleOptionViewItem, QTableWidget, QTableWidgetItem)

from cmdrhelper.ui.recommendations_view import RememberedRecommendationDelegate
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class RecommendationCheckboxStyleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.stylesheet = self.app.styleSheet()
        self.table = QTableWidget(1, 2)
        self.table.horizontalHeader().setMinimumSectionSize(30)
        self.table.setColumnWidth(0, 30)
        self.table.setColumnWidth(1, 120)
        for column in range(2):
            item = QTableWidgetItem()
            item.setCheckState(Qt.CheckState.Unchecked)
            self.table.setItem(0, column, item)
        self.delegate = RememberedRecommendationDelegate(self.table)
        self.native = QStyledItemDelegate(self.table)
        self.table.setItemDelegate(self.delegate)

    def tearDown(self):
        self.table.close()
        self.table.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.app.setStyleSheet(self.stylesheet)

    def render(self, *, checked=False, extra=QStyle.StateFlag.State_None,
               enabled=True, column=0, native=False):
        item = self.table.item(0, column)
        item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
        item.setData(Qt.ItemDataRole.UserRole + 1, checked and column == 0)
        option = QStyleOptionViewItem()
        option.initFrom(self.table)
        option.widget = self.table
        option.rect = QRect(0, 0, self.table.columnWidth(column), self.table.rowHeight(0))
        option.state &= ~(QStyle.StateFlag.State_MouseOver | QStyle.StateFlag.State_HasFocus
                          | QStyle.StateFlag.State_Selected)
        option.state |= extra
        if not enabled:
            option.state &= ~QStyle.StateFlag.State_Enabled
        index = self.table.model().index(0, column)
        delegate = self.native if native else self.delegate
        geometry = QStyleOptionViewItem(option)
        delegate.initStyleOption(geometry, index)
        indicator = self.table.style().subElementRect(
            QStyle.SubElement.SE_ItemViewItemCheckIndicator, geometry, self.table)
        image = QImage(option.rect.size(), QImage.Format.Format_ARGB32)
        image.fill(option.palette.base().color())
        painter = QPainter(image)
        delegate.paint(painter, option, index)
        painter.end()
        return image, indicator, delegate.sizeHint(option, index)

    @staticmethod
    def orange_pixels(image):
        return sum(20 <= image.pixelColor(x, y).hue() <= 50
                   and image.pixelColor(x, y).saturation() > 140
                   for x in range(image.width()) for y in range(image.height()))

    def test_states_in_both_themes_and_font_sizes(self):
        for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            for size in (10, 18, 24):
                self.app.setStyleSheet(theme + f'\nQWidget {{ font-size: {size}pt; }}')
                self.table.show()
                self.app.processEvents()
                with self.subTest(light=theme == LIGHT_STYLESHEET, size=size):
                    plain, rect, hint = self.render()
                    checked, _, _ = self.render(checked=True)
                    orange = self.orange_pixels(plain.copy(rect))
                    self.assertGreater(orange, 8)
                    self.assertGreater(self.orange_pixels(checked.copy(rect)), orange)
                    self.assertNotEqual(plain, checked)
                    # The checked glyph contains a dark tick against the accent fill.
                    inner = checked.copy(rect.adjusted(3, 3, -3, -3))
                    dark = sum(inner.pixelColor(x, y).lightness() < 35
                               for x in range(inner.width()) for y in range(inner.height()))
                    self.assertGreater(dark, 2)
                    for state in (QStyle.StateFlag.State_MouseOver, QStyle.StateFlag.State_HasFocus):
                        for on in (False, True):
                            emphasized, _, _ = self.render(checked=on, extra=state)
                            normal = checked if on else plain
                            self.assertNotEqual(emphasized.copy(rect), normal.copy(rect))
                    for on in (False, True):
                        disabled, _, _ = self.render(checked=on, enabled=False)
                        self.assertEqual(self.orange_pixels(disabled.copy(rect)), 0)
                        self.assertNotEqual(disabled.copy(rect), (checked if on else plain).copy(rect))

    def test_native_geometry_and_other_columns_are_unchanged(self):
        for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            for size in (10, 24):
                self.app.setStyleSheet(theme + f'\nQWidget {{ font-size: {size}pt; }}')
                self.table.show()
                self.app.processEvents()
                height = self.table.rowHeight(0)
                for on in (False, True):
                    _, rect, hint = self.render(checked=on)
                    _, native_rect, native_hint = self.render(checked=on, native=True)
                    self.assertEqual(rect, native_rect)
                    self.assertEqual(hint, native_hint)
                    self.assertEqual(self.table.rowHeight(0), height)
                    actual, _, _ = self.render(checked=on, column=1)
                    expected, _, _ = self.render(checked=on, column=1, native=True)
                    self.assertEqual(actual, expected)
                self.assertEqual(self.table.columnWidth(0), 30)

    def test_remembered_row_highlight_and_check_state_survive_painting(self):
        for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.app.setStyleSheet(theme)
            self.table.show()
            self.app.processEvents()
            image, _, _ = self.render(checked=True, extra=QStyle.StateFlag.State_Selected)
            option = QStyleOptionViewItem()
            option.initFrom(self.table)
            option.state |= QStyle.StateFlag.State_Selected
            self.delegate.initStyleOption(option, self.table.model().index(0, 0))
            self.assertFalse(option.state & QStyle.StateFlag.State_Selected)
            self.assertNotEqual(option.backgroundBrush.color(), option.palette.base().color())
            self.assertEqual(image.pixelColor(image.width() - 4, image.height() // 2),
                             option.backgroundBrush.color())
            self.assertEqual(self.table.item(0, 0).checkState(), Qt.CheckState.Checked)
            self.assertTrue(self.table.item(0, 0).data(Qt.ItemDataRole.UserRole + 1))
