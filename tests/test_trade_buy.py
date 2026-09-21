"""Purchase UI contracts with synthetic offers and isolated, transient state."""
from datetime import datetime, timedelta, timezone
from dataclasses import replace
from threading import Event, get_ident
import time
import unittest
from unittest.mock import patch

from PySide6.QtCore import QEvent, QThreadPool, QTimer, Qt, QPoint
from PySide6.QtGui import QFont
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLabel

from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.help_content import help_topic
from cmdrhelper.market_data import MarketSearch, MarketSearchResult, MarketStatus, PadSize, TradeSide
from cmdrhelper.ui.trade_view import TradeView
from cmdrhelper.ui.commodity_picker import CommodityField
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from test_trade_view import State, offer, PLATINUM
from test_market_data_provider import Harness, response as provider_response, station


def response(*rows):
    result = provider_response(*rows)
    result['reference']['name'] = 'Test Origin'
    return result


def buy_offer(**changes):
    return offer(commander_buy_price=1467, commander_sell_price=203385, supply=200, demand=0, **changes)


class BuyProvider:
    def __init__(self):
        self.calls = []
        self.gate = Event()
        self.gate.set()
        self.status = MarketStatus.OK
        self.rows = (buy_offer(),)
        self.truncated = False
        self.threads = []

    def _search(self, side, query, cancel):
        self.calls.append((side, query))
        self.threads.append(get_ident())
        while not self.gate.wait(.005):
            if cancel.is_set():
                break
        return MarketSearchResult(self.status, self.rows if self.status == MarketStatus.OK else (),
                                  query, truncated=self.truncated)

    def search_buy(self, query, *, cancel):
        return self._search(TradeSide.BUY, query, cancel)

    def search_sell(self, query, *, cancel):
        return self._search(TradeSide.SELL, query, cancel)


class BuyTradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.language, self.style, self.font = get_language(), self.app.styleSheet(), self.app.font()
        set_language('de')
        self.pool = QThreadPool()
        self.state, self.provider = State(), BuyProvider()
        self.view = TradeView(self.state, provider=self.provider, pool=self.pool)
        self.view.resize(1200, 1000)
        self.view.show()
        self.view.tabs.setCurrentIndex(1)
        self.app.processEvents()
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.view.cancel_search()
        self.provider.gate.set()
        self.pool.waitForDone(2000)
        self.app.processEvents()
        self.view.close()
        self.view.deleteLater()
        self.app.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        set_language(self.language)
        self.app.setStyleSheet(self.style)
        self.app.setFont(self.font)

    def wait(self):
        deadline = time.monotonic()+3
        while self.view.worker is not None and time.monotonic()<deadline:
            self.app.processEvents()
            QTest.qWait(5)
        self.assertIsNone(self.view.worker)

    def search(self):
        self.view.commodity.set_commodity(PLATINUM.frontier_id)
        self.view.start_search()
        self.wait()

    def populate(self, rows, **kwargs):
        query = MarketSearch(PLATINUM.frontier_id, 'Test Origin', minimum_quantity=22)
        self.view.show_result(MarketSearchResult(MarketStatus.OK, tuple(rows), query, **kwargs), query)

    def ids(self):
        return [self.view.table.item(i, 0).data(Qt.ItemDataRole.UserRole).market_id
                for i in range(self.view.table.rowCount())]

    def test_two_real_tabs_reuse_one_picker_form_table_and_notice(self):
        self.assertEqual([self.view.tabs.tabText(i) for i in range(2)], ['Verkaufen','Einkaufen'])
        original = (self.view.commodity, self.view.filters, self.view.table, self.view.market_notice)
        self.assertIsInstance(self.view.commodity, CommodityField)
        self.assertEqual(len(self.view.findChildren(CommodityField)), 1)
        self.assertTrue(self.view.commodity.isVisible())
        self.assertEqual(self.view.table.horizontalHeaderItem(4).text(), 'Angebot')
        self.assertEqual(self.view.table.horizontalHeaderItem(5).text(), 'Gesamtkosten')
        for tab in (0,1,0,1):
            self.view.tabs.setCurrentIndex(tab)
            self.app.processEvents()
            self.assertEqual(original, (self.view.commodity,self.view.filters,self.view.table,self.view.market_notice))
            self.assertTrue(self.view.market_notice.isVisible())
        self.assertFalse(self.provider.calls)

    def test_filters_preserved_and_forwarded_to_buy_request(self):
        self.view.commodity.set_commodity(PLATINUM.frontier_id)
        self.view.quantity.setValue(100)
        self.view.radius.setCurrentIndex(3)
        self.view.max_age.setCurrentIndex(1)
        self.view.pad.setCurrentIndex(2)
        self.view.carriers.setChecked(True)
        self.view.arrival.setText('1411')
        self.populate([buy_offer()])
        self.assertEqual(self.view.table.rowCount(), 1)
        for tab in (0, 1):
            self.view.tabs.setCurrentIndex(tab)
            self.assertEqual(self.view.table.rowCount(), 0)
            self.assertEqual(self.view.offers, ())
            self.assertEqual((self.view.commodity.currentData(), self.view.quantity.value(),
                              self.view.radius.currentData(), self.view.max_age.currentData(),
                              PadSize(self.view.pad.currentData()), self.view.carriers.isChecked(),
                              self.view.arrival.text()),
                             (PLATINUM.frontier_id, 100, 250, 6, PadSize.MEDIUM, True, '1411'))
        self.search()
        side,q=self.provider.calls[-1]
        self.assertIs(side,TradeSide.BUY)
        self.assertEqual((q.commodity,q.minimum_quantity,q.radius_ly,q.max_age,q.required_pad,
                          q.include_fleet_carriers,q.max_distance_to_arrival_ls,q.reference_system),
                         (PLATINUM.frontier_id,100,250,timedelta(hours=6),PadSize.MEDIUM,True,1411,'Test Origin'))

    def test_buy_defaults_and_positive_integer_quantity(self):
        self.assertEqual(self.view.quantity.minimum(),1)
        self.view.quantity.setValue(0)
        self.search()
        q=self.provider.calls[-1][1]
        self.assertEqual((q.minimum_quantity,q.radius_ly,q.max_age,q.required_pad,q.include_fleet_carriers,q.max_distance_to_arrival_ls,q.limit),
                         (1,100,timedelta(hours=24),PadSize.ANY,False,None,100))

    def test_purchase_price_supply_and_total_cost_never_use_sell_price_or_demand(self):
        self.view.quantity.setValue(100)
        self.search()
        self.assertEqual(self.view.table.item(0,3).value,1467)
        self.assertEqual(self.view.table.item(0,4).value,200)
        self.assertEqual(self.view.table.item(0,5).value,146700)
        self.assertEqual(self.view.status.text(),'1 Verkaufsangebot gefunden.')
        self.assertNotIn('Ankaufsangebot',self.view.status.text())

    def test_insufficient_missing_supply_or_invalid_buy_price_never_appears(self):
        base=buy_offer()
        rows=[replace(base,supply=x) for x in (None,0,21)]+[replace(base,commander_buy_price=x) for x in (None,0)]
        self.populate(rows)
        self.assertEqual(self.view.table.rowCount(),0)
        self.assertEqual(self.view.status.text(),tr('trade.buy_no_results'))
        self.populate([replace(base,supply=22)])
        self.assertEqual(self.view.table.rowCount(),1)

    def test_lowest_price_initial_and_numeric_sorting_all_columns(self):
        for column,field,values in ((2,'distance_ly',[100,0,11,2.5]),(3,'commander_buy_price',[203385,1467,4401]),
                                     (4,'supply',[1040306,882,11235]),(5,'commander_buy_price',[203385,1467,4401]),
                                     (6,'distance_to_arrival_ls',[11390,524,1411])):
            self.populate([replace(buy_offer(market_id=i),**{field:v}) for i,v in enumerate(values)])
            self.assertEqual(self.view.table.horizontalHeader().sortIndicatorOrder(),Qt.SortOrder.AscendingOrder)
            expected=sorted(range(len(values)),key=values.__getitem__)
            for direction,order in ((Qt.SortOrder.AscendingOrder,expected),(Qt.SortOrder.DescendingOrder,expected[::-1])):
                self.view.table.sortItems(column,direction)
                self.assertEqual(self.ids(),order)

    def test_text_pad_and_age_sorting_header_click_and_timestamp_tooltip(self):
        now=datetime.now(timezone.utc)
        names=['beta','Alpha','alpha','Zulu'];pads=[None,PadSize.LARGE,PadSize.SMALL,PadSize.MEDIUM]
        ages=[timedelta(days=2),timedelta(minutes=12),timedelta(hours=20),timedelta(hours=2)]
        self.populate([buy_offer(market_id=i,system_name=names[i],station_name=names[i],largest_pad=pads[i],market_updated_at=now-ages[i]) for i in range(4)])
        for column,asc,desc in ((0,[1,2,0,3],[3,0,1,2]),(1,[1,2,0,3],[3,0,1,2]),(7,[2,3,1,0],[1,3,2,0]),(8,[1,3,2,0],[0,2,3,1])):
            self.view.table.sortItems(column,Qt.SortOrder.AscendingOrder);self.assertEqual(self.ids(),asc)
            self.view.table.sortItems(column,Qt.SortOrder.DescendingOrder);self.assertEqual(self.ids(),desc)
        self.view.table.sortItems(3,Qt.SortOrder.AscendingOrder)
        header=self.view.table.horizontalHeader()
        self.view.table.horizontalScrollBar().setValue(self.view.table.horizontalScrollBar().maximum())
        pos=QPoint(header.sectionViewportPosition(8)+header.sectionSize(8)//2,header.height()//2)
        QTest.mouseClick(header.viewport(),Qt.MouseButton.LeftButton,pos=pos)
        self.assertEqual(self.ids(),[1,3,2,0])
        self.assertEqual(self.view.table.item(0,8).text(),'12 Min.')
        self.assertEqual(self.view.table.item(0,8).toolTip(),(now-ages[1]).isoformat())

    def test_worker_is_async_single_flight_and_cancel_visible_only_while_running(self):
        self.provider.gate.clear()
        self.view.commodity.set_commodity(PLATINUM.frontier_id)
        self.assertFalse(self.view.cancel_button.isVisible())
        self.view.start_search()
        self.assertTrue(self.view.cancel_button.isVisible())
        self.assertFalse(self.view.search_button.isEnabled())
        self.view.start_search()
        ticks=[];QTimer.singleShot(0,lambda:ticks.append(True))
        self.app.processEvents();self.assertTrue(ticks)
        self.provider.gate.set();self.wait()
        self.assertEqual(len(self.provider.calls),1)
        self.assertNotEqual(self.provider.threads[0],get_ident())
        self.assertFalse(self.view.cancel_button.isVisible())

    def test_cancel_discards_buy_results(self):
        self.provider.gate.clear();self.view.commodity.set_commodity(PLATINUM.frontier_id)
        self.view.start_search();self.view.cancel_button.click();self.wait()
        self.assertEqual(self.view.table.rowCount(),0)
        self.assertEqual(self.view.status.text(),tr('trade.cancelled'))
        self.assertFalse(self.view.cancel_button.isVisible())

    def test_system_change_cancels_buy_search(self):
        self.provider.gate.clear();self.view.commodity.set_commodity(PLATINUM.frontier_id)
        self.view.start_search();self.state.system='New Test Origin';self.state.changed.emit();self.wait()
        self.assertEqual(self.view.table.rowCount(),0)
        self.assertFalse(self.view.cancel_button.isVisible())

    def test_tab_switch_generation_rejects_late_success_even_after_switching_back(self):
        class PendingPool:
            def start(self,worker):self.worker=worker
        pending=PendingPool();self.view.pool=pending
        self.view.commodity.set_commodity(PLATINUM.frontier_id)
        for start,other in ((0,1),(1,0)):
            self.view.tabs.setCurrentIndex(start);self.view.start_search();old=pending.worker
            self.view.tabs.setCurrentIndex(other)
            self.assertTrue(old.cancel.is_set());self.assertFalse(self.view.cancel_button.isVisible())
            self.view.tabs.setCurrentIndex(start)
            self.view.start_search();self.assertIs(pending.worker,old)
            old.signals.finished.emit(MarketSearchResult(MarketStatus.OK,(buy_offer(),),old.query))
            self.assertIsNone(self.view.worker)
            self.assertEqual(self.view.table.rowCount(),0)
            self.assertEqual(self.view.status.text(),tr('trade.ready'))
            self.assertTrue(self.view.search_button.isEnabled())

    def test_no_selection_or_system_blocks_requests(self):
        self.view.start_search();self.assertEqual(self.view.status.text(),tr('trade.choose_commodity'))
        self.view.commodity.set_commodity(PLATINUM.frontier_id)
        self.state.system='';self.state.changed.emit();self.view.start_search()
        self.assertEqual(self.view.status.text(),tr('trade.no_system'));self.assertFalse(self.provider.calls)

    def test_error_statuses_zero_one_many_and_truncated(self):
        for status,key in ((MarketStatus.NO_RESULTS,'buy_no_results'),(MarketStatus.TIMEOUT,'timeout'),
                           (MarketStatus.NETWORK_ERROR,'network_error'),(MarketStatus.HTTP_ERROR,'network_error'),
                           (MarketStatus.RATE_LIMIT,'rate_limit'),(MarketStatus.INVALID_JSON,'invalid_response'),
                           (MarketStatus.INVALID_RESPONSE,'invalid_response'),(MarketStatus.CANCELLED,'cancelled')):
            self.provider.status=status;self.search()
            self.assertEqual(self.view.status.text(),tr('trade.'+key));self.assertFalse(self.view.cancel_button.isVisible())
        self.provider.status=MarketStatus.OK;self.provider.rows=tuple(buy_offer(market_id=i) for i in range(105));self.provider.truncated=True
        self.search();self.assertEqual(self.view.table.rowCount(),100)
        self.assertIn('100 Verkaufsangebote gefunden.',self.view.status.text())
        self.assertIn(tr('trade.truncated'),self.view.status.text())

    def test_buy_exception_is_sanitized(self):
        with patch.object(self.provider,'search_buy',side_effect=ValueError('private server text')):self.search()
        self.assertEqual(self.view.status.text(),tr('trade.invalid_response'))

    def test_real_provider_buy_cache_supply_and_sell_separation(self):
        row=station();row['market'][0].update(buy_price=1467,supply=100,sell_price=203385,demand=200)
        h=Harness(response(row),response(row));self.view.provider=h.provider
        self.view.quantity.setValue(100);self.search();first=len(h.requests)
        self.assertEqual(self.view.table.item(0,3).value,1467)
        market_filter=h.payloads[0]['filters']['market'][0]
        self.assertEqual(market_filter['supply']['value'][0],100)
        self.assertEqual(market_filter['buy_price']['value'][0],1)
        self.assertNotIn('demand',market_filter)
        self.search();self.assertEqual(len(h.requests),first);self.assertIn(tr('trade.cached'),self.view.status.text())
        self.view.tabs.setCurrentIndex(0);self.search();self.assertGreater(len(h.requests),first)
        self.assertEqual(self.view.table.item(0,3).value,203385)
        self.assertIn('Ankaufsangebot',self.view.status.text())
        count=len(h.requests);self.view.tabs.setCurrentIndex(1);self.search();self.assertEqual(len(h.requests),count)

    def test_buy_provider_pad_carrier_age_and_arrival_filters(self):
        base=station();base['market'][0].update(buy_price=100,supply=100)
        from copy import deepcopy
        variants=[]
        for name,changes in [('Large',{}),('Medium',dict(has_large_pad=False,large_pads=0,medium_pads=1)),
                             ('Small',dict(has_large_pad=False,large_pads=0,small_pads=1)),
                             ('Carrier',dict(type='Fleet Carrier')),('Distant',dict(distance_to_arrival=10000)),
                             ('Old',dict(market_updated_at='2020-01-01T00:00:00+00:00'))]:
            r=deepcopy(base);r.update(name=name,market_id=len(variants)+1,**changes);variants.append(r)
        for pad,expected,branches in ((PadSize.ANY,{'Large','Medium','Small'},1),(PadSize.SMALL,{'Large','Medium','Small'},3),
                                      (PadSize.MEDIUM,{'Large','Medium'},2),(PadSize.LARGE,{'Large'},1)):
            h=Harness(*(response(*variants) for _ in range(branches)))
            q=MarketSearch(PLATINUM.frontier_id,'Test Origin',minimum_quantity=100,required_pad=pad,max_distance_to_arrival_ls=1000)
            r=h.provider.search_buy(q);self.assertEqual({o.station_name for o in r.offers},expected)
        h=Harness(response(*variants));q=replace(q,required_pad=PadSize.ANY,include_fleet_carriers=True)
        self.assertIn('Carrier',{o.station_name for o in h.provider.search_buy(q).offers})

    def test_twelve_languages_help_themes_large_font_and_notice(self):
        for lang,translations in _TRANSLATIONS.items():
            set_language(lang)
            for style in (DARK_STYLESHEET,LIGHT_STYLESHEET):
                for size in (10,18):
                    with self.subTest(language=lang,size=size,light=style==LIGHT_STYLESHEET):
                        self.app.setFont(QFont(self.font.family(),size))
                        self.app.setStyleSheet(style+f'\nQWidget {{font-size: {size}pt;}}')
                        page=TradeView(self.state,provider=self.provider,pool=self.pool)
                        page.resize(1100,1000);page.tabs.setCurrentIndex(1);page.show();self.app.processEvents()
                        self.assertEqual(page.tabs.tabText(1),translations['trade.buy'])
                        self.assertTrue(page.market_notice.isVisible())
                        self.assertEqual(page.market_notice.text(),translations['trade.market_notice'])
                        self.assertEqual(page.search_button.toolTip(),translations['trade.buy_help'])
                        self.assertGreaterEqual(page.search_button.width(),page.search_button.sizeHint().width())
                        self.assertGreaterEqual(page.table.height(),240)
                        for count in (0,1,3):
                            rows=tuple(buy_offer(market_id=i) for i in range(count))
                            q=MarketSearch(PLATINUM.frontier_id,'Test Origin',minimum_quantity=1)
                            page.show_result(MarketSearchResult(MarketStatus.OK if count else MarketStatus.NO_RESULTS,rows,q),q)
                            key='trade.buy_no_results' if count==0 else 'trade.buy_success_one' if count==1 else 'trade.buy_success'
                            self.assertEqual(page.status.text(),translations[key].format(count=count))
                        from importlib import import_module
                        body=import_module('cmdrhelper.help_content.'+lang).HELP_TOPICS['trade'][1]
                        self.assertIn(translations['trade.buy'],body)
                        self.assertIn('×',body)
                        self.assertFalse(page.grab().isNull())
                        page.close();page.deleteLater();self.app.sendPostedEvents(None,QEvent.Type.DeferredDelete)
