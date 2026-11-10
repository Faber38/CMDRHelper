"""Real BIO table layout, decoration and refresh regression checks."""
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from PySide6.QtCore import QEvent, QSettings, Qt
from PySide6.QtGui import QHelpEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QStyle, QStyleOptionViewItem, QStyledItemDelegate

from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.ui.footfall_icon import footfall_color
from test_explorer_table_ux import ExplorerWindow
from qt_widget_cleanup import destroy_widget


class BioBodyFootfallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(set_language, get_language())
        self.errors = []
        self.hook = patch.object(sys, 'excepthook', lambda *args: self.errors.append(args))
        self.hook.start()
        self.window = ExplorerWindow(QSettings(self.tmp.name + '/ui.ini', QSettings.IniFormat))
        self.window.resize(1200, 800)
        self.window.show()
        self.window.explorer_tabs.setCurrentIndex(2)
        self.window.pages = SimpleNamespace(currentIndex=lambda: self.window.PAGE_EXPLORER)
        self.table = self.window.explorer_bio_table
        self.delegate = self.table.itemDelegateForColumn(0)
        QTest.qWait(20)

    def tearDown(self):
        QTest.qWait(20)
        destroy_widget(self.window, close=False)
        self.hook.stop()
        self.assertEqual(self.errors, [])

    def refresh(self, bodies):
        self.window.state.system_bodies = bodies
        self.window._explorer_dirty_tabs = {2}
        self.window._refresh_visible_details()
        self.app.processEvents()

    def option(self, row, delegate=None):
        index = self.table.model().index(row, 0)
        option = QStyleOptionViewItem()
        option.widget = self.table
        option.rect = self.table.visualRect(index)
        (delegate or self.delegate).initStyleOption(option, index)
        return index, option

    def has_icon(self, row):
        index, option = self.option(row)
        return not option.icon.isNull()

    def test_exact_true_and_correct_body_without_changing_values_or_widths(self):
        bodies = [dict(short_name=str(i), body_id=i, biological_signals=1,
                       geological_signals=2, planetary_mining_signals=3,
                       planet_class='Water world', **flag)
                  for i, flag in enumerate([{'first_footfall': True},
                                            {'first_footfall': False}, {},
                                            {'first_footfall': 1}])]
        widths = [self.table.columnWidth(c) for c in range(11)]
        self.refresh(bodies)
        for row in range(4):
            index, option = self.option(row)
            self.assertEqual(not option.icon.isNull(), index.data(Qt.UserRole)['body_id'] == 0)
        before = [[self.table.item(r, c).text() for c in range(11)] for r in range(4)]
        default = QStyledItemDelegate(self.table)
        self.table.setItemDelegateForColumn(0, default)
        self.refresh(bodies)
        self.assertEqual(before, [[self.table.item(r, c).text() for c in range(11)] for r in range(4)])
        self.assertEqual(widths, [self.table.columnWidth(c) for c in range(11)])

    def test_long_names_themes_scaling_and_translated_tooltip(self):
        name = 'A very long planet name ' * 12
        self.refresh([dict(short_name=name, biological_signals=1, first_footfall=True)])
        for light in (False, True):
            self.window.ui_theme = 'light' if light else 'dark'
            for ratio in (1.0, 1.5, 2.0):
                with patch.object(self.table, 'devicePixelRatioF', return_value=ratio):
                    index, option = self.option(0)
                icon = self.table.style().subElementRect(QStyle.SE_ItemViewItemDecoration, option, self.table)
                text = self.table.style().subElementRect(QStyle.SE_ItemViewItemText, option, self.table)
                self.assertFalse(icon.intersects(text))
                self.assertEqual(option.textElideMode, Qt.ElideRight)
                image = option.icon.pixmap(option.decorationSize, ratio).toImage()
                self.assertTrue(any(image.pixelColor(x, y) == footfall_color(light)
                                    for x in range(image.width()) for y in range(image.height())))
        for language, catalog in _TRANSLATIONS.items():
            set_language(language)
            self.assertIn('footfall.label', catalog)
            index, option = self.option(0)
            icon = self.table.style().subElementRect(QStyle.SE_ItemViewItemDecoration, option, self.table)
            event = QHelpEvent(QEvent.ToolTip, icon.center(), self.table.viewport().mapToGlobal(icon.center()))
            with patch('cmdrhelper.ui.bio_body_delegate.QToolTip.showText') as show:
                self.assertTrue(self.delegate.helpEvent(event, self.table, option, index))
                self.assertEqual(show.call_args.args[1], tr('footfall.label'))
            text = self.table.style().subElementRect(QStyle.SE_ItemViewItemText, option, self.table)
            event = QHelpEvent(QEvent.ToolTip, text.center(), self.table.viewport().mapToGlobal(text.center()))
            with patch('cmdrhelper.ui.bio_body_delegate.QToolTip.showText') as show:
                self.delegate.helpEvent(event, self.table, option, index)
                self.assertEqual(show.call_args.args[1], name)

    def test_existing_refresh_path_updates_and_removes_icons_on_context_change(self):
        for signal in ('biological_signals', 'geological_signals', 'planetary_mining_signals'):
            body = dict(short_name='3', body_id=7, first_footfall=False, **{signal: 1})
            self.refresh([body])
            self.assertFalse(self.has_icon(0))
            body['first_footfall'] = True
            self.refresh([body])
            self.assertTrue(self.has_icon(0))
            # Stored bodies replace the same list when a commander/system loads.
            self.window.state.commander_id = 2
            self.refresh([dict(short_name='3', body_id=7, **{signal: 1})])
            self.assertFalse(self.has_icon(0))
            self.window.state.system = 'Other system'
            self.refresh([dict(short_name='8', body_id=9, first_footfall=True, **{signal: 1})])
            self.assertTrue(self.has_icon(0))
            self.assertEqual(self.option(0)[0].data(Qt.UserRole)['body_id'], 9)
            self.refresh([])
            self.assertEqual(self.table.rowCount(), 0)


if __name__ == '__main__':
    unittest.main()
