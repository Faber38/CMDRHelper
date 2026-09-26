"""Destination bookmarks across searches, duplicate rows and all three tabs."""
from dataclasses import replace
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QStyleOptionViewItem, QStyle

from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus, PadSize
from cmdrhelper.trade_recommendations import Recommendation
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
import test_trade_system_copy as copy_tests
from test_trade_recommendations import BEER, offer
import unittest


class RememberedTargetTests(unittest.TestCase):
    setUpClass = copy_tests.TradeSystemCopyTests.__dict__['setUpClass']
    setUp = copy_tests.TradeSystemCopyTests.setUp
    tearDown = copy_tests.TradeSystemCopyTests.tearDown
    populate = copy_tests.TradeSystemCopyTests.populate
    geometry = copy_tests.TradeSystemCopyTests.geometry
    click = copy_tests.TradeSystemCopyTests.click

    def panel(self, tab):
        return (self.view.remembered_panel if tab == 2
                else self.trade.remembered_lists[self.trade.side])

    def marks(self, tab):
        return [self.table.item(i, 0 if tab == 2 else 10)
                for i in range(self.table.rowCount())]

    def render(self, tab, offers):
        if tab == 2:
            self.view.render(tuple(Recommendation(o, 10000, 10) for o in offers))
        else:
            query = MarketSearch(BEER.frontier_id, self.state.system, minimum_quantity=1)
            self.trade.show_result(MarketSearchResult(MarketStatus.OK, offers, query), query)

    def test_multiple_targets_sort_scroll_copy_and_individual_removal(self):
        for tab in range(3):
            self.populate(tab, ['Sol', 'Achenar'])
            panel = self.panel(tab)
            for mark in self.marks(tab):
                mark.setCheckState(Qt.Checked)
            before = dict(panel.targets)
            self.assertEqual(len(before), 2)
            self.assertEqual(len(panel.text().splitlines()), 2)
            for order in (Qt.AscendingOrder, Qt.DescendingOrder):
                self.table.sortItems(self.column, order)
                self.table.verticalScrollBar().setValue(1)
                self.assertTrue(all(m.checkState() == Qt.Checked for m in self.marks(tab)))
                self.assertTrue(all(not self.table.isRowHidden(i) for i in range(2)))
                self.click(0)
                self.assertEqual(panel.targets, before)
            self.marks(tab)[0].setCheckState(Qt.Unchecked)
            self.assertEqual(len(panel.targets), 1)
            self.marks(tab)[1].setCheckState(Qt.Unchecked)
            self.assertFalse(panel.targets)
            self.assertTrue(panel.isHidden())

    def test_duplicates_last_uncheck_and_reappearance(self):
        for tab in range(3):
            self.populate(tab, ['Sol', 'Sol', 'Other'])
            panel = self.panel(tab)
            marks = self.marks(tab)
            same = [m for m in marks if m.data(Qt.UserRole + 2)[0] == 'Sol']
            same[0].setCheckState(Qt.Checked)
            self.assertEqual(same[1].checkState(), Qt.Unchecked)
            same[1].setCheckState(Qt.Checked)
            self.assertEqual(len(panel.targets), 1)
            same[0].setCheckState(Qt.Unchecked)
            self.assertEqual(len(panel.targets), 1)
            same[1].setCheckState(Qt.Unchecked)
            self.assertFalse(panel.targets)
            same[0].setCheckState(Qt.Checked)
            self.populate(tab, ['Other'])
            self.assertEqual(len(panel.targets), 1)
            self.assertEqual(self.marks(tab)[0].checkState(), Qt.Unchecked)
            self.populate(tab, ['Sol', 'Sol'])
            self.assertTrue(all(m.checkState() == Qt.Checked for m in self.marks(tab)))
            self.marks(tab)[0].setCheckState(Qt.Unchecked)
            self.assertEqual(len(panel.targets), 1)
            self.marks(tab)[1].setCheckState(Qt.Unchecked)
            self.assertFalse(panel.targets)

    def test_identity_only_system_station_and_separate_tabs(self):
        panels = []
        for tab in range(3):
            self.populate(tab, ['Sol'])
            self.marks(tab)[0].setCheckState(Qt.Checked)
            panels.append(self.panel(tab))
            base = offer(system_name='Sol', station_name='Station only', largest_pad=PadSize.LARGE,
                         commander_buy_price=10000, supply=100)
            # Changed market ID, commodity, prices and quantities still identify the same target.
            self.render(tab, (replace(base, market_id=999, commodity_symbol='Gold'),
                              replace(base, station_name='Second station'),
                              replace(base, system_name='Second system')))
            self.assertEqual(sum(m.checkState() == Qt.Checked for m in self.marks(tab)), 1)
            self.assertEqual(self.panel(tab).text(), 'Sol · Station only · Groß')
        self.assertEqual(len({id(p) for p in panels}), 3)
        self.marks(2)[0].setCheckState(Qt.Checked)
        panels[2].clear()
        self.assertEqual([len(p.targets) for p in panels], [1, 1, 0])

    def test_valid_new_search_keeps_targets_all_tabs(self):
        for tab in range(3):
            self.populate(tab, ['Sol'])
            self.marks(tab)[0].setCheckState(Qt.Checked)
            panel = self.panel(tab)
            before = dict(panel.targets)
            view = self.view if tab == 2 else self.trade
            if tab != 2:
                self.trade.commodity.set_commodity(BEER.frontier_id)
            with patch.object(self.pool, 'start') as start:
                view.start_search()
                start.assert_called_once()
            self.assertEqual(panel.targets, before)
            view.destroyed.disconnect(view._cancel_event.set)
            view.worker = None
            view._cancel_event = None
            self.populate(tab, ['Sol'])
            self.assertEqual(self.marks(tab)[0].checkState(), Qt.Checked)

    def test_themes_large_font_wrapping_and_checkbox_mouse(self):
        previous = self.app.styleSheet()
        self.addCleanup(self.app.setStyleSheet, previous)
        for sheet in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            for size in (10, 18, 24):
                self.app.setStyleSheet(sheet + f'\nQWidget {{ font-size: {size}pt; }}')
                self.trade.resize(480, 950)
                for tab in range(3):
                    self.populate(tab, ['Long system ' * 12], station_name='Long station ' * 12)
                    mark = self.marks(tab)[0]
                    index = self.table.indexFromItem(mark)
                    self.table.scrollTo(index)
                    self.app.processEvents()
                    option = QStyleOptionViewItem()
                    option.initFrom(self.table)
                    self.table.itemDelegate().initStyleOption(option, index)
                    option.rect = self.table.visualRect(index)
                    rect = self.table.style().subElementRect(QStyle.SE_ItemViewItemCheckIndicator, option, self.table)
                    QTest.mouseClick(self.table.viewport(), Qt.LeftButton, pos=rect.center())
                    self.assertEqual(mark.checkState(), Qt.Checked)
                    panel = self.panel(tab)
                    QTest.qWait(20)
                    self.app.processEvents()
                    self.assertTrue(panel.isVisible())
                    self.assertLessEqual(panel.width(), panel.parentWidget().width())
                    for entry, label, button, copy_button in panel.entries.values():
                        self.assertGreaterEqual(label.height(), label.heightForWidth(label.width()))
                        self.assertEqual(label.font().pointSize(), size)
                        self.assertTrue(entry.rect().contains(button.geometry()))
                        self.assertTrue(entry.rect().contains(copy_button.geometry()))
                        self.assertGreater(copy_button.x(), label.geometry().right())
                        self.assertGreater(button.x(), copy_button.geometry().right())
                        self.assertEqual(copy_button.text(), '⧉')
                        self.assertEqual(copy_button.font().pointSize(), size)
                        before = dict(panel.targets)
                        copy_button.click()
                        self.assertEqual(self.app.clipboard().text(), 'Long system ' * 12)
                        self.assertEqual(panel.targets, before)
                        self.assertEqual(mark.checkState(), Qt.Checked)
                        self.assertEqual(button.text(), '✕')
                        self.assertEqual(button.toolTip(), 'Gemerktes Ziel entfernen')
                    self.assertEqual(panel.heading.text(), 'Gemerkte Ziele')
                    panel.grab()
                    copied = self.app.clipboard().text()
                    button.click()
                    self.assertEqual(self.app.clipboard().text(), copied)
                    self.assertEqual(mark.checkState(), Qt.Unchecked)
                    self.assertFalse(panel.targets)

    def test_remove_button_syncs_all_duplicate_rows_and_preserves_other_tabs(self):
        panels = []
        for tab in range(3):
            self.populate(tab, ['Sol', 'Sol', 'Other'])
            for mark in self.marks(tab):
                mark.setCheckState(Qt.Checked)
            panels.append(self.panel(tab))
        for tab in range(3):
            self.populate(tab, ['Sol', 'Sol', 'Other'])
            self.table.sortItems(self.column, Qt.AscendingOrder)
            before = [dict(p.targets) for p in panels]
            self.app.clipboard().setText('Clipboard unchanged')
            panels[tab].entries[('Sol', 'Station only')][2].click()
            self.assertEqual(self.app.clipboard().text(), 'Clipboard unchanged')
            self.assertEqual(set(panels[tab].targets), {('Other', 'Station only')})
            self.assertEqual(set(panels[tab].entries), {('Other', 'Station only')})
            self.assertNotIn(('Sol', 'Station only'), panels[tab].body_labels)
            self.assertEqual(self.table.rowCount(), 3)
            for mark in self.marks(tab):
                expected = mark.data(Qt.UserRole + 2)[0] == 'Other'
                self.assertEqual(mark.checkState() == Qt.Checked, expected)
                for column in range(self.table.columnCount()):
                    self.assertEqual(self.table.item(mark.row(), column).data(Qt.UserRole + 1), expected)
            for other in range(3):
                if other != tab:
                    self.assertEqual(panels[other].targets, before[other])
            # A removed target remains unchecked when later searches rediscover it.
            self.populate(tab, ['Sol', 'Other'])
            for mark in self.marks(tab):
                self.assertEqual(mark.checkState() == Qt.Checked,
                                 mark.data(Qt.UserRole + 2)[0] == 'Other')

    def test_remove_absent_target_after_new_search_and_last_entry(self):
        for tab in range(3):
            self.populate(tab, ['Sol', 'Other'])
            for mark in self.marks(tab):
                mark.setCheckState(Qt.Checked)
            panel = self.panel(tab)
            self.populate(tab, ['Other'])
            panel.entries[('Sol', 'Station only')][2].click()
            self.assertEqual(len(panel.targets), 1)
            self.assertEqual(self.marks(tab)[0].checkState(), Qt.Checked)
            self.populate(tab, [])
            panel.entries[('Other', 'Station only')][2].click()
            self.assertFalse(panel.targets)
            self.assertFalse(panel.entries)
            self.assertTrue(panel.isHidden())
            self.populate(tab, ['Sol', 'Other'])
            self.assertTrue(all(m.checkState() == Qt.Unchecked for m in self.marks(tab)))

    def test_remove_tooltip_available_in_all_languages(self):
        from cmdrhelper.i18n import _TRANSLATIONS
        for language, translations in _TRANSLATIONS.items():
            self.assertTrue(translations.get('trade.remove_remembered_target'), language)

    def test_bookmark_copy_exact_names_independent_of_marks_and_remove_all_tabs(self):
        from PySide6.QtTest import QSignalSpy
        from cmdrhelper.i18n import tr
        names = ['HIP 67115', '银河 Δοκιμή İı Å <System> ' * 15]
        for tab in range(3):
            self.populate(tab, names + [names[0]])
            for mark in self.marks(tab):
                mark.setCheckState(Qt.Checked)
            panel = self.panel(tab)
            before = dict(panel.targets)
            before_bodies = dict(panel.body_labels)
            marks = [m.checkState() for m in self.marks(tab)]
            changed = QSignalSpy(self.table.itemChanged)
            for name in names:
                copy_button = panel.entries[(name, 'Station only')][3]
                self.assertEqual(copy_button.toolTip(), tr('recommend.copy_system'))
                self.app.clipboard().setText('old clipboard')
                QTest.mouseClick(copy_button, Qt.LeftButton)
                self.assertEqual(self.app.clipboard().text(), name)
                self.assertEqual(panel.targets, before)
                self.assertEqual(panel.body_labels, before_bodies)
                self.assertEqual([m.checkState() for m in self.marks(tab)], marks)
                self.assertEqual(changed.count(), 0)
            # Removal still clears every duplicate checkbox and leaves copied text alone.
            panel.entries[(names[0], 'Station only')][2].click()
            self.assertEqual(self.app.clipboard().text(), names[1])
            self.assertEqual(set(panel.targets), {(names[1], 'Station only')})
            for mark in self.marks(tab):
                self.assertEqual(mark.checkState() == Qt.Checked,
                                 mark.data(Qt.UserRole + 2)[0] == names[1])

    def test_bookmark_copy_survives_new_search_without_matching_results(self):
        for tab in range(3):
            self.populate(tab, ['HIP 67115', '银河 Δοκιμή'])
            for mark in self.marks(tab):
                mark.setCheckState(Qt.Checked)
            panel = self.panel(tab)
            before = dict(panel.targets)
            self.populate(tab, ['Different system'])
            for name in ('HIP 67115', '银河 Δοκιμή'):
                panel.entries[(name, 'Station only')][3].click()
                self.assertEqual(self.app.clipboard().text(), name)
                self.assertEqual(panel.targets, before)
                self.assertEqual(self.marks(tab)[0].checkState(), Qt.Unchecked)
            self.populate(tab, [])
            panel.entries[('HIP 67115', 'Station only')][3].click()
            self.assertEqual(self.app.clipboard().text(), 'HIP 67115')
            self.assertEqual(panel.targets, before)
