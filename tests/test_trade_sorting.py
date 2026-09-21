"""Display-only sorting, using real values and actual Qt header clicks."""
from datetime import datetime, timedelta, timezone
import unittest

from PySide6.QtCore import QPoint, Qt, QEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from cmdrhelper.i18n import get_language, set_language
from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus, PadSize
from cmdrhelper.ui.trade_view import TradeView
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from test_trade_view import State, Provider, offer, PLATINUM

ASC, DESC = Qt.SortOrder.AscendingOrder, Qt.SortOrder.DescendingOrder


class TradeSortingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.language, self.style = get_language(), self.app.styleSheet()
        set_language('de')
        self.state, self.provider = State(), Provider()
        self.view = TradeView(self.state, provider=self.provider)
        self.view.resize(1500, 850)
        self.view.show()
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.view.close()
        self.view.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        set_language(self.language)
        self.app.setStyleSheet(self.style)

    def populate(self, rows):
        self.rows = tuple(rows)
        self.query = MarketSearch(PLATINUM.frontier_id, 'Test Origin', minimum_quantity=22)
        self.result = MarketSearchResult(MarketStatus.OK, self.rows, self.query)
        self.view.show_result(self.result, self.query)
        self.app.processEvents()

    def rebuild_view(self):
        self.view.close()
        self.view.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.view = TradeView(self.state, provider=self.provider)
        self.view.resize(1500, 850)
        self.view.show()

    def identities(self):
        return [self.view.table.item(row, 0).data(Qt.ItemDataRole.UserRole).market_id
                for row in range(self.view.table.rowCount())]

    def assert_order(self, column, direction, expected):
        self.view.table.sortItems(column, direction)
        self.assertEqual(self.identities(), expected)
        header = self.view.table.horizontalHeader()
        self.assertEqual(header.sortIndicatorSection(), column)
        self.assertEqual(header.sortIndicatorOrder(), direction)
        self.assertEqual(self.result.offers, self.rows)
        self.assertEqual(self.view.offers, self.rows)
        self.assertFalse(self.provider.queries)

    def test_numeric_columns_use_unformatted_values_in_both_directions(self):
        for column, field, values in (
            (2, 'distance_ly', [100.0, 0.0, 11.0, 2.5]),
            (3, 'commander_sell_price', [203385, 1467, 4401]),
            (4, 'demand', [1040306, 882, 11235]),
            (5, 'commander_sell_price', [203385, 1467, 4401]),
            (6, 'distance_to_arrival_ls', [11390, 524, 1411]),
        ):
            with self.subTest(column=column):
                self.populate([offer(market_id=i, **{field: value}) for i, value in enumerate(values)])
                ascending = sorted(range(len(values)), key=values.__getitem__)
                self.assert_order(column, ASC, ascending)
                self.assert_order(column, DESC, ascending[::-1])
                if column == 5:
                    self.assertEqual(sorted(self.view.table.item(i, 5).value for i in range(3)),
                                     sorted(v * 22 for v in values))

    def test_pad_order_is_semantic_and_unknown_last_in_both_directions(self):
        for language in ('de', 'en'):
            set_language(language)
            self.rebuild_view()
            self.populate([offer(market_id=i, largest_pad=pad) for i, pad in enumerate(
                [None, PadSize.LARGE, PadSize.SMALL, PadSize.MEDIUM, None])])
            self.assert_order(7, ASC, [2, 3, 1, 0, 4])
            self.assert_order(7, DESC, [1, 3, 2, 0, 4])
            self.assert_order(7, ASC, [2, 3, 1, 0, 4])
            self.click_header(7)
            self.assertEqual(self.identities(), [1, 3, 2, 0, 4])
            self.click_header(7)
            self.assertEqual(self.identities(), [2, 3, 1, 0, 4])

    def test_age_uses_elapsed_time_and_preserves_text_and_utc_tooltip(self):
        now = datetime.now(timezone.utc)
        ages = [timedelta(days=2), timedelta(minutes=12), timedelta(hours=20), timedelta(hours=2)]
        self.populate([offer(market_id=i, market_updated_at=now-age) for i, age in enumerate(ages)])
        before = {self.view.table.item(i, 0).data(Qt.ItemDataRole.UserRole).market_id:
                  (self.view.table.item(i, 8).text(), self.view.table.item(i, 8).toolTip()) for i in range(4)}
        self.assert_order(8, ASC, [1, 3, 2, 0])
        self.assert_order(8, DESC, [0, 2, 3, 1])
        after = {self.view.table.item(i, 0).data(Qt.ItemDataRole.UserRole).market_id:
                 (self.view.table.item(i, 8).text(), self.view.table.item(i, 8).toolTip()) for i in range(4)}
        self.assertEqual(before, after)
        self.assertEqual([before[i][0] for i in range(4)], ['2 Tage', '12 Min.', '20 Std.', '2 Std.'])
        for i in range(4):
            self.assertEqual(before[i][1], (now-ages[i]).isoformat())

    def test_system_and_station_case_insensitive_stable_sort(self):
        for column, field in ((0, 'system_name'), (1, 'station_name')):
            self.populate([offer(market_id=i, **{field: name}) for i, name in enumerate(
                ['beta', 'Alpha', 'alpha', 'Zulu'])])
            self.assert_order(column, ASC, [1, 2, 0, 3])
            self.assert_order(column, DESC, [3, 0, 1, 2])
            self.assert_order(column, ASC, [1, 2, 0, 3])

    def click_header(self, column):
        header = self.view.table.horizontalHeader()
        # Scroll horizontally if necessary without changing the selected row.
        self.view.table.horizontalScrollBar().setValue(0)
        pos = header.sectionViewportPosition(column) + header.sectionSize(column)//2
        if pos >= header.viewport().width():
            self.view.table.horizontalScrollBar().setValue(self.view.table.horizontalScrollBar().maximum())
            pos = header.sectionViewportPosition(column) + header.sectionSize(column)//2
        QTest.mouseClick(header.viewport(), Qt.MouseButton.LeftButton,
                         pos=QPoint(pos, header.height()//2))
        self.app.processEvents()

    def test_headers_initial_price_and_age_first_click_de_en_dark_light(self):
        for language in ('de', 'en'):
            for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                with self.subTest(language=language, light=style == LIGHT_STYLESHEET):
                    set_language(language)
                    self.app.setStyleSheet(style)
                    self.rebuild_view()
                    now = datetime.now(timezone.utc)
                    self.populate([offer(market_id=i, commander_sell_price=price,
                                         market_updated_at=now-timedelta(hours=age))
                                   for i, (price, age) in enumerate([(1467, 2), (203385, 20), (4401, 1)])])
                    self.assertEqual(self.identities(), [1, 2, 0])
                    header = self.view.table.horizontalHeader()
                    self.assertEqual(header.sortIndicatorSection(), 3)
                    self.assertEqual(header.sortIndicatorOrder(), DESC)
                    self.assertTrue(header.isSortIndicatorShown())
                    self.click_header(8)
                    self.assertEqual(header.sortIndicatorOrder(), ASC)
                    self.assertEqual(self.identities(), [2, 0, 1])
                    self.click_header(8)
                    self.assertEqual(header.sortIndicatorOrder(), DESC)
                    self.assertEqual(self.identities(), [1, 0, 2])
                    self.assertFalse(self.view.grab().isNull())
