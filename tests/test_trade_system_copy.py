"""Inline system copying in sell, buy and recommendation results; synthetic data only."""
import unittest

from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QHelpEvent
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QAbstractItemView, QStyleOptionViewItem, QToolTip

from cmdrhelper.i18n import tr
from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus
from cmdrhelper.trade_recommendations import Recommendation
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
import test_recommendations_view as recommendation_tests
from test_trade_recommendations import BEER, offer


class TradeSystemCopyTests(unittest.TestCase):
    setUpClass = classmethod(recommendation_tests.RecommendationViewTests.setUpClass.__func__)
    setUp = recommendation_tests.RecommendationViewTests.setUp
    tearDown = recommendation_tests.RecommendationViewTests.tearDown

    def populate(self, tab, names, station_name="Station only", **changes):
        self.trade.tabs.setCurrentIndex(tab)
        offers = tuple(offer(mid=i+2, system_name=name, station_name=station_name,
                             commander_buy_price=10000, commander_sell_price=12000+i,
                             supply=100, demand=100, **changes) for i, name in enumerate(names))
        if tab == 2:
            self.view.render(tuple(Recommendation(o, 10000, 10) for o in offers))
            self.table, self.column = self.view.table, 9
        else:
            query = MarketSearch(BEER.frontier_id, self.state.system, minimum_quantity=1)
            self.trade.show_result(MarketSearchResult(MarketStatus.OK, offers, query), query)
            self.table, self.column = self.trade.table, 0
        self.app.processEvents()

    def geometry(self, row):
        index = self.table.model().index(row, self.column)
        self.app.processEvents()
        self.table.scrollTo(index)
        self.app.processEvents()
        # Scroll horizontally as a user would; Qt's style can choose pixel or item scrolling.
        position = (self.table.horizontalHeader().sectionPosition(self.column)
                    if self.table.horizontalScrollMode() == QAbstractItemView.ScrollPerPixel
                    else self.column)
        self.table.horizontalScrollBar().setValue(0)
        self.table.horizontalScrollBar().setValue(position)
        option = QStyleOptionViewItem()
        option.initFrom(self.table)
        option.font = self.table.font()
        delegate = self.table.itemDelegateForColumn(self.column)
        delegate.initStyleOption(option, index)
        option.rect = self.table.visualRect(index)
        rect, text = delegate.copy_rect(option, index)
        return rect, text, option

    def click(self, row):
        rect, _, _ = self.geometry(row)
        self.assertFalse(rect.isEmpty())
        self.assertTrue(self.table.viewport().rect().contains(rect),
                        (self.table.viewport().rect(), rect))
        QTest.mouseClick(self.table.viewport(), Qt.LeftButton, pos=rect.center())
        self.app.processEvents()

    def test_exact_names_refresh_and_sorting_all_views(self):
        for tab in range(3):
            for names in (['Sol'], ['Sol', '银河 Δοκιμή İı Å', 'Long System ' * 20],
                          [], ['Replacement', 'Achenar']):
                with self.subTest(tab=tab, names=names):
                    self.populate(tab, names)
                    for order in (Qt.AscendingOrder, Qt.DescendingOrder):
                        self.table.sortItems(self.column, order)
                        self.assertEqual(self.table.rowCount(), len(names))
                        for row in range(len(names)):
                            expected = self.table.item(row, self.column).text()
                            self.app.clipboard().setText('old clipboard\nStation only')
                            self.click(row)
                            self.assertEqual(self.app.clipboard().text(), expected)

    def test_icon_consumes_actions_but_normal_cells_still_work(self):
        for tab in range(3):
            with self.subTest(tab=tab):
                self.populate(tab, ['Sol', 'Achenar'])
                self.table.selectRow(1)
                selected = self.table.selectionModel().selectedIndexes()
                clicked = QSignalSpy(self.table.cellClicked)
                doubled = QSignalSpy(self.table.cellDoubleClicked)
                changed = QSignalSpy(self.table.itemChanged)
                self.click(0)
                QTest.mouseDClick(self.table.viewport(), Qt.LeftButton,
                                 pos=self.geometry(0)[0].center())
                self.assertEqual(clicked.count(), 0)
                self.assertEqual(doubled.count(), 0)
                self.assertEqual(changed.count(), 0)
                self.assertEqual(self.table.selectionModel().selectedIndexes(), selected)
                self.assertFalse(self.view.remembered_flights)
                rect, _, option = self.geometry(0)
                point = QPoint(option.rect.left()+5, rect.center().y())
                QTest.mouseClick(self.table.viewport(), Qt.LeftButton, pos=point)
                QTest.mouseDClick(self.table.viewport(), Qt.LeftButton, pos=point)
                self.assertEqual(clicked.count(), 1)
                self.assertEqual(doubled.count(), 1)
                self.assertEqual(self.table.currentRow(), 0)

    def test_hover_tooltip_and_remembered_style(self):
        for tab in range(3):
            self.populate(tab, ['Sol'])
            point = self.geometry(0)[0].center()
            QTest.mouseMove(self.table.viewport(), QPoint(1, 1))
            QTest.mouseMove(self.table.viewport(), point)
            self.assertEqual(self.table.viewport().cursor().shape(), Qt.PointingHandCursor)
            event = QHelpEvent(QEvent.ToolTip, point, self.table.viewport().mapToGlobal(point))
            self.app.sendEvent(self.table.viewport(), event)
            self.assertEqual(QToolTip.text(), tr('recommend.copy_system'))
            QToolTip.hideText()
            self.app.clipboard().setText('unchanged')
            QTest.mouseClick(self.table.viewport(), Qt.RightButton, pos=point)
            self.assertEqual(self.app.clipboard().text(), 'unchanged')
        self.table.item(0, 0).setCheckState(Qt.Checked)
        remembered = dict(self.view.remembered_flights)
        _, _, option = self.geometry(0)
        native = QStyleOptionViewItem(option)
        self.table.itemDelegate().initStyleOption(native, self.table.model().index(0, 9))
        self.assertEqual(option.backgroundBrush, native.backgroundBrush)
        self.click(0)
        self.assertEqual(self.view.remembered_flights, remembered)

    def test_theme_font_narrow_width_matrix(self):
        previous = self.app.styleSheet()
        self.addCleanup(self.app.setStyleSheet, previous)
        for sheet in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            for points in (10, 18, 24):
                self.app.setStyleSheet(sheet + f'\nQWidget {{ font-size: {points}pt; }}')
                self.trade.resize(480, 950)
                for tab in range(3):
                    with self.subTest(light=sheet == LIGHT_STYLESHEET, points=points, tab=tab):
                        self.populate(tab, ['Sol', '银河 Eorl Auwsy BA-A g98 ' * 12],
                                      station_name='银河 <Station> Δοκιμή ' * 12)
                        self.table.setFixedWidth(410)
                        self.table.setColumnWidth(self.column, 240)
                        self.app.processEvents()
                        for row in range(2):
                            rect, text, option = self.geometry(row)
                            self.assertTrue(option.rect.contains(rect))
                            self.assertGreaterEqual(rect.height(), option.fontMetrics.height())
                            text_right = option.rect.left()+3+option.fontMetrics.horizontalAdvance(text)
                            self.assertEqual(rect.left()-text_right, 4)
                            name = self.table.item(row, self.column).text()
                            if len(name) > 100:
                                self.assertIn('…', text)
                            self.click(row)
                            self.assertEqual(self.app.clipboard().text(), name)
                        self.table.grab()
