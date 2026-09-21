"""Offline trade UI contracts with synthetic markets and no production state."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import io
import json
from threading import Event, get_ident
import time
import unittest
from unittest.mock import patch

from PySide6.QtCore import QEvent, QObject, QThreadPool, QTimer, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel

from cmdrhelper.commodity_master import all_commodities, lookup_by_symbol
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.market_data import MarketOffer, MarketSearch, MarketSearchResult, MarketStatus, PadSize
from cmdrhelper.spansh_market import SpanshMarketProvider
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.ui.trade_view import TradeView, format_age
from cmdrhelper.ui.commodity_picker import commodity_name, CommodityPicker, COMMODITY_ID_ROLE


PLATINUM = lookup_by_symbol('platinum')


def offer(**changes):
    now = datetime.now(timezone.utc)
    base = MarketOffer(PLATINUM.frontier_id, PLATINUM.symbol, PLATINUM.english_name,
                       'Test System', 123, 'Test Station', 456, 'Outpost', 9, 120,
                       PadSize.LARGE, False, None, 123456, 9000, 0, 50,
                       now - timedelta(minutes=12), now, 'spansh')
    return replace(base, **changes)


class State(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self.system = 'Test Origin'


class Provider:
    def __init__(self, status=MarketStatus.OK, **kwargs):
        self.status, self.kwargs = status, kwargs
        self.queries = []
        self.threads = []
        self.gate = None
        self.entered = Event()

    def search_sell(self, query, *, cancel):
        self.queries.append(query)
        self.threads.append(get_ident())
        self.entered.set()
        if self.gate:
            while not self.gate.wait(.005):
                if cancel.is_set():
                    break
        return MarketSearchResult(self.status, (offer(),) if self.status == MarketStatus.OK else (),
                                  query, **self.kwargs)


class TradeViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        previous = get_language()
        self.addCleanup(set_language, previous)
        set_language('de')
        self.pool = QThreadPool()
        self.provider = Provider()
        self.state = State()
        self.view = TradeView(self.state, provider=self.provider, pool=self.pool)
        self.view.resize(1000, 850)
        self.view.show()
        self.addCleanup(self.cleanup_view)

    def cleanup_view(self):
        self.view.cancel_search()
        self.pool.waitForDone(2000)
        self.app.processEvents()
        self.view.close()
        self.view.deleteLater()
        self.app.processEvents()

    def select(self):
        self.view.commodity.set_commodity(PLATINUM.frontier_id)

    def wait(self):
        deadline = time.monotonic() + 3
        while self.view.worker is not None and time.monotonic() < deadline:
            self.app.processEvents()
            QTest.qWait(5)
        self.assertIsNone(self.view.worker)

    def search(self):
        self.select()
        self.view.search_button.click()
        self.wait()

    def result(self, *offers, **kwargs):
        query = MarketSearch(PLATINUM.frontier_id, 'Test Origin', minimum_quantity=22, limit=100)
        self.view.show_result(MarketSearchResult(MarketStatus.OK, offers, query, **kwargs), query)

    def test_sell_and_buy_tabs_and_initial_table_empty(self):
        self.assertEqual(self.view.tabs.count(), 3)
        self.assertEqual(self.view.tabs.tabText(2), tr('recommend.title'))
        self.assertEqual(self.view.tabs.tabText(0), 'Verkaufen')
        self.assertEqual(self.view.table.rowCount(), 0)
        self.assertEqual(self.view.table.columnCount(), 10)
        self.assertFalse(self.provider.queries)

    def test_sell_results_describe_market_buying_zero_one_many_in_twelve_languages(self):
        expected_de = {0: 'Keine passenden Ankaufsangebote gefunden.',
                       1: '1 Ankaufsangebot gefunden.', 6: '6 Ankaufsangebote gefunden.'}
        for language, translations in _TRANSLATIONS.items():
            set_language(language)
            self.assertTrue(translations['trade.sell_searching'].strip())
            for count in (0, 1, 6):
                with self.subTest(language=language, count=count):
                    rows = tuple(offer(market_id=i) for i in range(count))
                    query = MarketSearch(PLATINUM.frontier_id, 'Test Origin', minimum_quantity=22)
                    result = MarketSearchResult(MarketStatus.OK if count else MarketStatus.NO_RESULTS, rows, query)
                    self.view.show_result(result, query)
                    key = ('trade.sell_no_results' if count == 0 else
                           'trade.sell_success_one' if count == 1 else 'trade.sell_success')
                    self.assertTrue(translations[key].strip())
                    self.assertEqual(self.view.status.text(), translations[key].format(count=count))
                    self.assertNotIn('{count}', self.view.status.text())
                    self.assertEqual(self.view.table.rowCount(), count)
                    if language == 'de':
                        self.assertEqual(self.view.status.text(), expected_de[count])
                    if count:
                        self.assertEqual(self.view.table.item(0, 3).value, rows[0].commander_sell_price)
                        self.assertEqual(self.view.table.item(0, 5).value, rows[0].commander_sell_price * 22)

    def test_market_notice_stays_above_empty_and_populated_results(self):
        self.app.processEvents()
        notice = self.view.market_notice
        self.assertTrue(notice.isVisible())
        self.assertIn('Datenalter', notice.text())
        self.assertTrue(notice.wordWrap())
        for offers in ((), (offer(),)):
            self.result(*offers)
            self.app.processEvents()
            self.assertTrue(notice.isVisible())
            self.assertLess(notice.geometry().bottom(), self.view.table.geometry().top())
            self.assertGreaterEqual(self.view.table.height(), 240)
        self.assertEqual(self.view.table.horizontalHeaderItem(8).text(), tr('trade.age'))
        self.assertTrue(self.view.table.item(0, 8).toolTip())

    def test_german_beer_selection_reaches_unchanged_provider_query(self):
        beer = lookup_by_symbol('Beer')
        self.view.commodity.open_picker()
        picker = self.view.commodity._picker
        picker.search.setText('Bier')
        picker._choose(picker.model.index_for_id(beer.frontier_id))
        self.assertEqual(self.view.commodity.currentText(), 'Bier')
        self.view.start_search()
        self.wait()
        self.assertEqual(self.provider.queries[-1].commodity, beer.frontier_id)

    def test_master_is_complete_and_identity_is_id(self):
        picker = CommodityPicker(parent=self.view)
        self.addCleanup(picker.close)
        self.assertEqual(picker.model.rowCount(), 412)
        self.assertEqual({picker.model.index(i).data(COMMODITY_ID_ROLE) for i in range(412)},
                         {c.frontier_id for c in all_commodities()})
        self.select()
        self.assertEqual(self.view.commodity.currentText(), 'Platin')
        item = next(c for c in all_commodities() if tr('mining.commodity.' + c.symbol.casefold()).startswith('mining.'))
        self.assertEqual(commodity_name(item), item.english_name)

    def test_search_names_english_and_canonical_symbol(self):
        picker = CommodityPicker(parent=self.view)
        self.addCleanup(picker.close)
        item = lookup_by_symbol('methanolmonohydratecrystals')
        for term in ('pLaTin', 'Platinum', commodity_name(item), item.english_name, item.symbol):
            picker.search.setText(term)
            expected = PLATINUM if term in ('pLaTin', 'Platinum') else item
            self.assertTrue(picker.model.index_for_id(expected.frontier_id).isValid())
        self.assertFalse(self.provider.queries)

    def test_unknown_search_and_no_selection_do_not_submit(self):
        self.view.commodity.click()
        picker = self.view.commodity._picker
        picker.search.setText('no such commodity')
        self.assertEqual(picker.model.rowCount(), 0)
        picker.reject()
        self.view.search_button.click()
        self.assertEqual(self.view.status.text(), tr('trade.choose_commodity'))
        self.assertFalse(self.provider.queries)

    def test_unknown_identity_is_rejected(self):
        with patch.object(self.view.commodity, 'currentData', return_value=999999999):
            self.view.search_button.click()
        self.assertEqual(self.view.status.text(), tr('trade.unknown_commodity'))
        self.assertFalse(self.provider.queries)

    def test_picker_selection_flows_to_unchanged_sell_search(self):
        self.view.commodity.click()
        picker = self.view.commodity._picker
        picker.search.setText('Platinum')
        self.app.processEvents()
        index = picker.model.index_for_id(PLATINUM.frontier_id)
        QTest.mouseClick(picker.grid.viewport(), Qt.MouseButton.LeftButton,
                         pos=picker.grid.visualRect(index).center())
        self.assertIsNone(self.view.commodity._picker)
        self.assertEqual(self.view.commodity.currentData(), PLATINUM.frontier_id)
        self.assertFalse(self.provider.queries)
        self.view.search_button.click()
        self.wait()
        self.assertEqual(self.provider.queries[0], MarketSearch(
            PLATINUM.frontier_id, 'Test Origin', minimum_quantity=1, limit=100))
        self.assertEqual(self.view.offers[0].commodity_symbol, PLATINUM.symbol)

    def test_default_query(self):
        self.search()
        q = self.provider.queries[0]
        self.assertEqual(q, MarketSearch(PLATINUM.frontier_id, 'Test Origin', minimum_quantity=1, limit=100))

    def test_quantity_is_positive_integer_and_minimum_demand(self):
        self.view.quantity.setValue(0)
        self.assertEqual(self.view.quantity.value(), 1)
        self.view.quantity.setValue(22)
        self.search()
        self.assertEqual(self.provider.queries[0].minimum_quantity, 22)

    def test_all_radius_options(self):
        for index, radius in enumerate((25, 50, 100, 250, 500)):
            self.view.radius.setCurrentIndex(index)
            self.search()
            self.assertEqual(self.provider.queries[-1].radius_ly, radius)
        self.assertFalse(self.view.radius.isEditable())

    def test_all_age_options(self):
        for index, hours in enumerate((1, 6, 12, 24, 72, 168)):
            self.view.max_age.setCurrentIndex(index)
            self.search()
            self.assertEqual(self.provider.queries[-1].max_age, timedelta(hours=hours))

    def test_all_pad_options(self):
        for index, pad in enumerate(PadSize):
            self.view.pad.setCurrentIndex(index)
            self.search()
            self.assertIs(self.provider.queries[-1].required_pad, pad)

    def test_pad_labels_and_values_in_all_twelve_languages(self):
        self.assertEqual(len(_TRANSLATIONS), 12)
        self.assertEqual(_TRANSLATIONS['de']['trade.pad'], 'Landeplatz')
        self.assertEqual([self.view.pad.itemData(i) for i in range(self.view.pad.count())],
                         [PadSize.ANY, PadSize.SMALL, PadSize.MEDIUM, PadSize.LARGE])
        for language, translations in _TRANSLATIONS.items():
            set_language(language)
            page = TradeView(self.state, provider=self.provider, pool=self.pool)
            try:
                self.assertTrue(translations['trade.pad'].strip())
                self.assertEqual(page.filters.layout().labelForField(page.pad).text(), translations['trade.pad'])
                for index, pad in enumerate(PadSize):
                    self.assertTrue(translations['trade.pad_' + pad.value].strip())
                    self.assertEqual(page.pad.itemText(index), translations['trade.pad_' + pad.value])
                    self.assertIs(PadSize(page.pad.itemData(index)), pad)
            finally:
                page.close()
                page.deleteLater()

    def test_cancel_visibility_for_all_worker_completion_statuses(self):
        self.assertFalse(self.view.cancel_button.isVisible())
        self.select()
        for status in MarketStatus:
            with self.subTest(status=status):
                self.provider.status = status
                self.provider.gate = Event()
                self.view.start_search()
                self.assertTrue(self.view.cancel_button.isVisible())
                self.assertTrue(self.view.cancel_button.isEnabled())
                self.provider.gate.set()
                self.wait()
                self.assertFalse(self.view.cancel_button.isVisible())

    def test_carriers_opt_in_and_clear_label(self):
        self.assertFalse(self.view.carriers.isChecked())
        self.view.carriers.setChecked(True)
        self.search()
        self.assertTrue(self.provider.queries[-1].include_fleet_carriers)
        self.result(offer(is_fleet_carrier=True))
        self.assertEqual(self.view.table.item(0, 9).text(), tr('trade.fleet_carrier'))

    def test_optional_arrival_filter(self):
        self.search()
        self.assertIsNone(self.provider.queries[-1].max_distance_to_arrival_ls)
        self.view.arrival.setText('50000')
        self.search()
        self.assertEqual(self.provider.queries[-1].max_distance_to_arrival_ls, 50000)

    def test_invalid_arrival_never_calls_provider(self):
        self.select()
        for text in ('0', '-1', 'NaN', 'inf', '0.5', '2147483648', '1e4', 'abc', '²'):
            self.view.arrival.setText(text)
            self.view.search_button.click()
            self.assertEqual(self.view.status.text(), tr('trade.invalid_arrival'), text)
        self.assertFalse(self.provider.queries)

    def test_current_system_visible_and_refreshed(self):
        self.state.system = 'Other Test Origin'
        self.state.changed.emit()
        self.assertIn('Other Test Origin', self.view.reference.text())
        self.search()
        self.assertEqual(self.provider.queries[-1].reference_system, 'Other Test Origin')

    def test_no_system_blocks_search(self):
        self.select()
        for value in ('', None, '  ', '–'):
            self.state.system = value
            self.state.changed.emit()
            self.view.search_button.click()
            self.assertEqual(self.view.status.text(), tr('trade.no_system'))
        self.assertFalse(self.provider.queries)

    def test_filters_and_state_updates_never_poll(self):
        self.select()
        self.view.quantity.setValue(25)
        self.view.carriers.setChecked(True)
        self.state.changed.emit()
        QTest.qWait(40)
        self.assertFalse(self.provider.queries)

    def test_filter_change_clears_results_without_search(self):
        self.search()
        self.assertEqual(self.view.table.rowCount(), 1)
        self.view.quantity.setValue(100)
        self.assertEqual(self.view.table.rowCount(), 0)
        self.assertEqual(len(self.provider.queries), 1)

    def test_worker_is_async_responsive_and_single_flight(self):
        self.provider.gate = Event()
        self.select()
        self.view.search_button.click()
        self.assertFalse(self.view.search_button.isEnabled())
        self.assertFalse(self.view.filters.isEnabled())
        self.assertEqual(self.view.status.text(), tr('trade.sell_searching'))
        self.assertTrue(self.provider.entered.wait(1))
        ticks = []
        QTimer.singleShot(0, lambda: ticks.append(True))
        self.app.processEvents()
        self.assertTrue(ticks)
        self.assertNotEqual(self.provider.threads[0], get_ident())
        self.view.start_search()
        self.assertEqual(len(self.provider.queries), 1)
        self.provider.gate.set()
        self.wait()
        self.assertTrue(self.view.search_button.isEnabled())
        self.assertEqual(self.view.table.rowCount(), 1)

    def test_cancel_discards_result_and_can_search_again(self):
        self.provider.gate = Event()
        self.select()
        self.view.search_button.click()
        self.assertTrue(self.provider.entered.wait(1))
        self.view.cancel_button.click()
        self.assertFalse(self.view.cancel_button.isVisible())
        self.wait()
        self.assertFalse(self.view.cancel_button.isVisible())
        self.assertEqual(self.view.status.text(), tr('trade.cancelled'))
        self.assertEqual(self.view.table.rowCount(), 0)
        self.provider.gate.set()
        self.search()
        self.assertEqual(self.view.table.rowCount(), 1)

    def test_system_change_cancels_and_clears_old_results(self):
        self.provider.gate = Event()
        self.select()
        self.view.start_search()
        self.state.system = 'Different Test System'
        self.state.changed.emit()
        self.assertFalse(self.view.cancel_button.isVisible())
        self.wait()
        self.assertFalse(self.view.cancel_button.isVisible())
        self.assertEqual(self.view.table.rowCount(), 0)
        self.assertEqual(self.view.status.text(), tr('trade.cancelled'))

    def test_close_cancels_worker(self):
        self.provider.gate = Event()
        self.select()
        self.view.start_search()
        self.view.close()
        self.wait()
        self.assertEqual(self.view.status.text(), tr('trade.cancelled'))

    def test_destroyed_page_cancels_without_waiting_on_ui(self):
        self.provider.gate = Event()
        page = TradeView(self.state, provider=self.provider, pool=self.pool)
        page.commodity.set_commodity(PLATINUM.frontier_id)
        page.start_search()
        cancel = page.worker.cancel
        self.assertTrue(self.provider.entered.wait(1))
        page.deleteLater()
        self.app.sendPostedEvents(page, QEvent.Type.DeferredDelete)
        self.assertTrue(cancel.is_set())
        self.assertTrue(self.pool.waitForDone(2000))
        self.app.processEvents()

    def test_every_status_is_localized_without_raw_errors(self):
        expected = {
            MarketStatus.NO_RESULTS: 'sell_no_results', MarketStatus.TIMEOUT: 'timeout',
            MarketStatus.NETWORK_ERROR: 'network_error', MarketStatus.RATE_LIMIT: 'rate_limit',
            MarketStatus.HTTP_ERROR: 'network_error', MarketStatus.INVALID_JSON: 'invalid_response',
            MarketStatus.INVALID_RESPONSE: 'invalid_response', MarketStatus.UNKNOWN_SYSTEM: 'unknown_system',
            MarketStatus.UNKNOWN_COMMODITY: 'unknown_commodity', MarketStatus.INVALID_QUERY: 'invalid_query',
            MarketStatus.CANCELLED: 'cancelled',
        }
        for status, key in expected.items():
            self.provider.status = status
            self.search()
            self.assertEqual(self.view.status.text(), tr('trade.' + key))
            self.assertEqual(self.view.table.rowCount(), 0)

    def test_unexpected_worker_exception_is_sanitized(self):
        with patch.object(self.provider, 'search_sell', side_effect=ValueError('secret HTTP traceback')):
            self.search()
        self.assertEqual(self.view.status.text(), tr('trade.invalid_response'))

    def test_truncated_warning_and_visible_limit(self):
        self.result(*(offer(market_id=i) for i in range(105)), truncated=True)
        self.assertEqual(self.view.table.rowCount(), 100)
        self.assertIn(tr('trade.truncated'), self.view.status.text())

    def test_truncated_empty_result_is_not_silently_complete(self):
        self.provider.status = MarketStatus.NO_RESULTS
        self.provider.kwargs['truncated'] = True
        self.search()
        self.assertIn(tr('trade.sell_no_results'), self.view.status.text())
        self.assertIn(tr('trade.truncated'), self.view.status.text())

    def test_sell_price_direction_and_revenue(self):
        self.result(offer(commander_sell_price=9000, commander_buy_price=123456, demand=22))
        self.assertEqual(self.view.table.item(0, 3).value, 9000)
        self.assertEqual(self.view.table.item(0, 5).value, 198000)
        self.assertEqual(self.view.table.item(0, 0).data(Qt.ItemDataRole.UserRole).market_id, 456)

    def test_revenue_requires_sufficient_demand(self):
        for demand in (None, 21):
            self.result(offer(demand=demand))
            self.assertEqual(self.view.table.item(0, 5).text(), '–')

    def test_age_formatting_and_exact_tooltip(self):
        now = datetime.now(timezone.utc)
        for delta, text in ((timedelta(minutes=12), '12 Min.'), (timedelta(hours=2), '2 Std.'),
                            (timedelta(hours=19), '19 Std.'), (timedelta(days=2), '2 Tage')):
            self.assertEqual(format_age(now-delta, now), text)
        item = offer()
        self.result(item)
        self.assertEqual(self.view.table.item(0, 8).text(), '12 Min.')
        self.assertEqual(self.view.table.item(0, 8).toolTip(), item.market_updated_at.isoformat())

    def test_initial_price_descending_and_numeric_sorting(self):
        self.result(offer(commander_sell_price=900, distance_ly=9, demand=90, distance_to_arrival_ls=9),
                    offer(commander_sell_price=10000, distance_ly=100, demand=1000, distance_to_arrival_ls=100))
        self.assertEqual(self.view.table.item(0, 3).value, 10000)
        for column in (2, 3, 4, 5, 6, 8):
            self.view.table.sortItems(column, Qt.SortOrder.AscendingOrder)
            self.assertLessEqual(self.view.table.item(0, column).value, self.view.table.item(1, column).value)
        self.view.table.sortItems(3, Qt.SortOrder.AscendingOrder)
        self.assertEqual(self.view.table.item(0, 0).data(Qt.ItemDataRole.UserRole).commander_sell_price, 900)

    def test_real_provider_cache_and_stale_filter(self):
        requests = []
        now = datetime.now(timezone.utc)
        def open_request(request, **kwargs):
            requests.append(request)
            if request.method == 'GET':
                data = {'values': ['Outpost', 'Fleet Carrier']}
            else:
                def row(age, market_id, carrier=False):
                    return dict(name='Test Station', system_name='Test Market', system_id64=123, market_id=market_id,
                                type='Fleet Carrier' if carrier else 'Outpost', distance=12, distance_to_arrival=200,
                                has_large_pad=True, market_updated_at=(now-timedelta(hours=age)).isoformat(),
                                market=[dict(commodity='Platinum', buy_price=99999, sell_price=8000, demand=30, supply=0)])
                data = dict(reference={'name': self.state.system}, count=3, results=[row(2, 1), row(25, 2), row(2, 3, True)])
            return io.BytesIO(json.dumps(data).encode())
        clock_values = iter(range(0, 10000, 2))
        self.view.provider = SpanshMarketProvider(opener=open_request, clock=lambda: next(clock_values))
        self.search()
        self.assertEqual(len(requests), 2)
        self.assertEqual(self.view.table.rowCount(), 1)
        self.assertEqual(self.view.table.item(0, 3).value, 8000)
        self.search()
        self.assertEqual(len(requests), 2)
        self.assertIn(tr('trade.cached'), self.view.status.text())

    def test_twelve_languages_and_theme_layouts(self):
        font = self.app.font()
        style = self.app.styleSheet()
        self.addCleanup(self.app.setStyleSheet, style)
        self.addCleanup(self.app.setFont, font)
        keys = {k for k in _TRANSLATIONS['en'] if k.startswith('trade.') or k == 'nav.trade'}
        self.assertEqual(len(_TRANSLATIONS), 12)
        for language, translations in _TRANSLATIONS.items():
            self.assertTrue(keys <= translations.keys())
            set_language(language)
            for stylesheet in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                for size in (10, 18):
                    with self.subTest(language=language, light=stylesheet == LIGHT_STYLESHEET, size=size):
                        self.app.setFont(QFont(font.family(), size))
                        self.app.setStyleSheet(stylesheet + f'\nQWidget {{ font-size: {size}pt; }}')
                        view = TradeView(self.state, provider=self.provider, pool=self.pool)
                        view.resize(900, 780)
                        view.show()
                        self.app.processEvents()
                        self.assertEqual(view.tabs.tabText(0), translations['trade.sell'])
                        self.assertGreaterEqual(view.search_button.width(), view.search_button.sizeHint().width())
                        self.assertGreaterEqual(view.carriers.width(), view.carriers.sizeHint().width())
                        for label in view.filters.findChildren(QLabel):
                            self.assertGreaterEqual(label.width(), label.sizeHint().width())
                        self.assertGreater(view.table.viewport().width(), 300)
                        self.assertEqual(view.market_notice.text(), translations['trade.market_notice'])
                        self.assertTrue(view.market_notice.isVisible())
                        self.assertTrue(view.market_notice.wordWrap())
                        self.assertGreaterEqual(view.market_notice.height(),
                                                view.market_notice.heightForWidth(view.market_notice.width()))
                        self.assertLess(view.market_notice.geometry().bottom(), view.table.geometry().top())
                        self.assertGreaterEqual(view.table.height(), 240)
                        self.assertTrue(view.grab().width() > 0)
                        view.close()
                        view.deleteLater()
                        self.app.processEvents()


if __name__ == '__main__':
    unittest.main()
