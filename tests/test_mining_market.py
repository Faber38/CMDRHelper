"""Mining supplementary prices: temporary synthetic stores, Qt workers, no network."""
from datetime import timedelta
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from threading import Event, get_ident
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PySide6.QtCore import QObject, QSettings, Signal, QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from cmdrhelper.market_store import MarketStore
from cmdrhelper.mining_catalog import MINING_COMMODITIES
from cmdrhelper.mining_market import MiningPrices, read_mining_prices
from cmdrhelper.ui.mining_view import MiningView
from cmdrhelper.ui.market_age import MarketAgeCombo
from test_market_store import NOW, GOLD, observation, commodity


class State(QObject):
    observedMarketsChanged=Signal()
    viewedCommanderChanged=Signal(object)
    commanderIdentityChanged=Signal(object,str,str)


class Inventory(QObject):
    loading=Signal()
    ready=Signal(object)
    refreshFinished=Signal(str)
    def refresh_now(self):pass


class MiningMarketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        temp=TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name);self.path=self.root/'markets.db'
        self.now=NOW
        self.store=MarketStore(self.path,clock=lambda:self.now)
        self.addCleanup(self.store.close)
        self.settings=QSettings(str(self.root/'settings.ini'),QSettings.IniFormat)
        self.settings.setValue('trade/max_age_hours',1)

    def put(self, mid=1, fid='CMDR1', sell=100, demand=10, stamp=NOW):
        self.store.record_observation(observation(mid=mid,fid=fid,stamp=stamp,
                                                  rows=[commodity(GOLD,buy=999999,sell=sell,demand=demand)]))

    def read(self, age=timedelta(hours=1)):
        return read_mining_prices(self.path,age,clock=lambda:self.now)

    def wait(self, predicate):
        limit=time.monotonic()+5
        while not predicate() and time.monotonic()<limit:QTest.qWait(5)
        self.assertTrue(predicate())

    def view(self):
        state=State();state.settings=self.settings
        state.commander_id=1;state.viewed_commander_id=2;state.commander_fid='ACTIVE_OTHER'
        state.observed_markets=SimpleNamespace(writer=SimpleNamespace(destination=self.path))
        view=MiningView(self.settings,state=state,controller=Inventory())
        view.market_controller.clock=lambda:self.now;view._market_clock=lambda:self.now
        self.addCleanup(view.deleteLater);self.addCleanup(view.close)
        self.addCleanup(view.market_controller.pool.waitForDone)
        return state,view

    def test_no_price_missing_db_and_reference_catalog_unchanged(self):
        before=tuple(MINING_COMMODITIES)
        self.assertEqual(self.read().quotes,())
        missing=read_mining_prices(self.root/'missing.db',timedelta(hours=1))
        self.assertEqual(missing.status,'missing');self.assertFalse((self.root/'missing.db').exists())
        self.assertEqual(tuple(MINING_COMMODITIES),before)

    def test_one_and_multiple_stations_use_sell_not_buy_and_positive_demand(self):
        self.put(sell=100)
        quote=self.read().quotes[0]
        self.assertEqual(quote.commodity.commander_sell_price,100)
        self.assertEqual(quote.header.system_name,'Synthetic System')
        self.assertEqual(quote.header.station_name,'Synthetic Port')
        self.assertEqual(quote.header.observed_at,NOW)
        self.assertEqual(quote.commodity.demand,10)
        self.put(mid=2,fid='CMDR2',sell=300)
        self.put(mid=3,sell=900,demand=0)
        quote=self.read().quotes[0]
        self.assertEqual((quote.header.market_id,quote.header.fid,quote.commodity.commander_sell_price),(2,'CMDR2',300))

    def test_demand_unknown_is_not_invented_or_treated_as_stock(self):
        with self.assertRaises(ValueError):self.put(demand=None)
        self.assertEqual(self.read().quotes,())
        self.put(demand=0)
        self.assertEqual(self.read().quotes,())

    def test_age_exact_boundary_older_and_unlimited(self):
        self.put(stamp=NOW-timedelta(hours=1),sell=100)
        self.put(mid=2,fid='CMDR2',stamp=NOW-timedelta(hours=1,microseconds=1),sell=999)
        self.assertEqual(self.read().quotes[0].header.market_id,1)
        self.now+=timedelta(microseconds=1)
        self.assertEqual(self.read().quotes,())
        self.assertEqual(self.read(None).quotes[0].header.market_id,2)

    def test_one_batch_57_identities_and_no_full_snapshots(self):
        rows=[dict(commodity_id=None,symbol=c.symbol,commander_buy_price=1,commander_sell_price=100,
                   supply=99,demand=10) for c in MINING_COMMODITIES]
        self.store.record_observation(observation(rows=rows))
        original=MarketStore.best_sell_prices;calls=[]
        def batch(store,refs,**kwargs):
            calls.append((len(refs),kwargs));return original(store,refs,**kwargs)
        with patch.object(MarketStore,'best_sell_prices',batch),patch.object(MarketStore,'_payload',side_effect=AssertionError('No full load')):
            result=self.read()
        self.assertEqual(len(calls),1);self.assertEqual(calls[0][0],57)
        self.assertEqual(calls[0][1]['scope'],'current');self.assertEqual(len(result.quotes),57)

    def test_ui_reference_and_stock_unaffected_tooltip_and_commander_switch_shared(self):
        self.put(fid='CMDR1',sell=120000)
        state,view=self.view();view.show()
        self.wait(lambda:bool(view.own_market_prices))
        item=view.items['gold']
        self.assertEqual(item.data(5,Qt.UserRole),48005)
        self.assertEqual(item.data(7,Qt.UserRole),120000)
        self.assertIsNone(item.data(4,Qt.UserRole))
        self.assertIn('Synthetic System',item.toolTip(7));self.assertIn('Synthetic Port',item.toolTip(7))
        state.viewed_commander_id=3;state.viewedCommanderChanged.emit(3)
        self.wait(lambda:bool(view.own_market_prices))
        self.assertEqual(item.data(7,Qt.UserRole),120000)
        combo=MarketAgeCombo(state);self.addCleanup(combo.deleteLater)
        combo.setCurrentIndex(combo.findData(6))
        self.wait(lambda:bool(view.own_market_prices))
        self.assertEqual(view.market_controller._args[1],timedelta(hours=6))

    def test_read_error_visible_without_losing_reference_prices(self):
        state,view=self.view()
        with patch('cmdrhelper.mining_market_controller.read_mining_prices',side_effect=sqlite3.OperationalError('synthetic failure')):
            with self.assertLogs('cmdrhelper.mining_market_controller',level='ERROR'):
                view.show();self.wait(lambda:view._market_status=='error')
        self.assertEqual(view.items['gold'].data(5,Qt.UserRole),48005)
        self.assertIsNone(view.items['gold'].data(7,Qt.UserRole))
        self.assertIn('Lesefehler',view.notice.text())

    def test_slow_worker_keeps_gui_live_and_discards_old_age_generation(self):
        self.put(stamp=NOW-timedelta(hours=2))
        self.settings.setValue('trade/max_age_hours',6)
        state,view=self.view();entered=Event();release=Event();ticks=[];threads=[]
        original=read_mining_prices
        def blocked(*args,**kwargs):
            threads.append(get_ident())
            result=original(*args,**kwargs)
            if len(threads)==1:
                entered.set();release.wait(5)
            return result
        timer=QTimer();timer.setInterval(5);timer.timeout.connect(lambda:ticks.append(1));timer.start()
        try:
            with patch('cmdrhelper.mining_market_controller.read_mining_prices',blocked):
                view.show();self.wait(entered.is_set)
                QTest.qWait(30);self.assertGreater(len(ticks),2)
                self.settings.setValue('trade/max_age_hours',1);view.market_controller.request()
                release.set()
                self.wait(lambda:len(threads)==2 and not view.market_controller._running)
                self.assertFalse(view.own_market_prices)
                self.assertTrue(all(t!=get_ident() for t in threads))
        finally:release.set();timer.stop()

    def test_expired_display_is_cleared_without_gui_sql(self):
        self.put(stamp=NOW-timedelta(minutes=59))
        state,view=self.view();view.show();self.wait(lambda:bool(view.own_market_prices))
        self.now+=timedelta(minutes=1,microseconds=1)
        with patch.object(MarketStore,'__init__',side_effect=AssertionError('No GUI SQL')):
            view._render_market_prices()
        self.assertIsNone(view.items['gold'].data(7,Qt.UserRole))

    def test_previous_column_layout_preserved_with_new_column_appended(self):
        previous=list(MiningView.COLUMNS[:-1]);widths=[350,70,71,72,73,170,160]
        self.settings.setValue('materials/mining/columns',dict(version=1,columns=previous,
            widths=widths,order=[6,0,1,2,3,4,5]))
        view=MiningView(self.settings);self.addCleanup(view.deleteLater)
        self.assertEqual([view.tree.header().logicalIndex(i) for i in range(7)],[6,0,1,2,3,4,5])
        self.assertEqual(view.tree.header().logicalIndex(7),7)
