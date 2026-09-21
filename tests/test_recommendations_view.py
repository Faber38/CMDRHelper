"""Offline Qt recommendations, using synthetic current journal/cargo/cache context."""
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from threading import Event, get_ident
from types import SimpleNamespace
import tempfile
import time
import unittest
from unittest.mock import patch

from PySide6.QtCore import QObject, Signal, QThreadPool, QEvent, Qt
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtTest import QTest

from cmdrhelper.i18n import set_language, get_language, tr, _TRANSLATIONS
from cmdrhelper.help_content import help_topic
from cmdrhelper.observed_market_cache import ObservedMarketCache
from cmdrhelper.route_planner.models import ShipLoadoutData
from cmdrhelper.ui.trade_view import TradeView
from cmdrhelper.ui.recommendations_view import current_market, ship_space, local_distances
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.market_data import MarketSearchResult, MarketStatus, PadSize
from cmdrhelper.trade_recommendations import Recommendation, RecommendationResult
from cmdrhelper.recommendation_diagnostics import PartialReason, RecommendationDiagnostics
from test_trade_recommendations import market, item, offer, BEER, GOLD, NOW, FID


class State(QObject):
    changed=Signal()
    observedMarketsChanged=Signal()
    commanderIdentityChanged=Signal(object,str,str)
    cargoSnapshotChanged=Signal(object)
    shipLoadoutChanged=Signal(object)


class AsyncProvider:
    def __init__(self):
        self.calls=[]
        self.threads=[]
        self.gate=Event();self.gate.set()
    def search_sell(self,q,*,cancel):
        self.calls.append(q);self.threads.append(get_ident())
        while not self.gate.wait(.005):
            if cancel.is_set():return MarketSearchResult(MarketStatus.CANCELLED)
        return MarketSearchResult(MarketStatus.OK,(offer(master=BEER if q.commodity==BEER.frontier_id else GOLD),))


class RecommendationViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.now=NOW
        self.language=get_language();set_language('de')
        self.state=State();s=self.state
        s.commander_fid=FID;s.system='Fixture System';s.station='Fixture Port';s.ship='Synthetic Ship'
        s.ship_loadout=ShipLoadoutData(ship_id=7,ship_name='Synthetic Ship',ship_type='anaconda',
                                      cargo_capacity=300,loadout_complete=True,loadout_stale=False)
        s.cargo_snapshot=dict(fid=FID,vessel='Ship',ship_id=7,count=20,capacity=300,timestamp=NOW.isoformat(),
                             inventory=[dict(count=15,is_drones=False),dict(count=5,is_drones=True)])
        self.cache=ObservedMarketCache(Path(self.tmp.name)/'cache.json',clock=lambda:self.now,
                                       on_changed=s.observedMarketsChanged.emit)
        self.cache.put(market())
        s.observed_markets=SimpleNamespace(cache=self.cache,context=dict(FID=FID,MarketID=1,
                            StationName=s.station,StarSystem=s.system))
        self.pool=QThreadPool();self.provider=AsyncProvider()
        self.trade=TradeView(s,provider=self.provider,pool=self.pool)
        self.view=self.trade.recommendations
        self.trade.resize(1100,900);self.trade.show();self.trade.tabs.setCurrentIndex(2)
        self.app.processEvents()

    def tearDown(self):
        self.view.cancel_search();self.provider.gate.set();self.pool.waitForDone(2000)
        self.app.processEvents();self.trade.close();self.trade.deleteLater()
        self.app.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        self.tmp.cleanup();set_language(self.language)

    def wait(self):
        deadline=time.monotonic()+3
        while self.view.worker is not None and time.monotonic()<deadline:
            self.app.processEvents();QTest.qWait(5)
        self.assertIsNone(self.view.worker)

    def search(self):self.view.start_search();self.wait()

    def test_tab_question_defaults_origin_ship_and_no_automatic_search(self):
        self.assertEqual(self.trade.tabs.tabText(2),'Empfehlungen')
        self.assertIn('mindestens 10 %',self.view.explanation.text())
        self.view.margin.setValue(20)
        self.assertIn('mindestens 20 %',self.view.explanation.text())
        self.assertIn('Fixture Port',self.view.origin_label.text())
        self.assertIn('Elite lokal',self.view.origin_label.text())
        self.assertIn('Synthetic Ship',self.view.ship_label.text())
        self.assertIn('280 t',self.view.ship_label.text())
        self.assertFalse(self.provider.calls)
        self.assertEqual(self.view.radius.currentData(),100)
        self.assertEqual(self.view.max_age.currentData(),24)
        self.assertFalse(self.view.carriers.isChecked())

    def test_current_market_exact_identity_and_fid(self):
        self.cache.put(market(mid=2))
        self.assertEqual(current_market(self.state)['market_id'],1)
        for key,value in (('FID','F_OTHER'),('MarketID',999),('StationName','Other'),('StarSystem','Other')):
            old=self.state.observed_markets.context[key]
            self.state.observed_markets.context[key]=value
            self.assertIsNone(current_market(self.state))
            self.state.observed_markets.context[key]=old
        self.state.station='Other';self.assertIsNone(current_market(self.state))

    def test_expired_origin_no_fallback_and_unknown_market(self):
        self.now=NOW+timedelta(hours=24,seconds=-1)
        self.assertIsNotNone(current_market(self.state))
        self.now+=timedelta(seconds=1)
        self.view.refresh()
        self.assertIsNone(self.view.origin)
        self.assertIn('Öffne in Elite',self.view.origin_label.text())
        self.view.start_search();self.assertFalse(self.provider.calls)

    def test_ship_space_includes_all_cargo_and_requires_identity(self):
        self.assertEqual(ship_space(self.state),('Synthetic Ship',280))
        s=self.state.cargo_snapshot
        for key,value in (('fid','F_OTHER'),('ship_id',99),('vessel','SRV'),('count',None)):
            old=s[key];s[key]=value
            self.assertIsNone(ship_space(self.state)[1]);s[key]=old
        self.state.ship_loadout.cargo_capacity=None
        self.view.refresh();self.assertIn('unbekannt',self.view.ship_label.text())
        self.assertFalse(self.view.search_button.isEnabled())
        self.state.ship_loadout.cargo_capacity=20
        self.view.refresh();self.assertEqual(self.view.free,0)
        self.assertIn('Kein freier',self.view.ship_label.text())
        self.assertFalse(self.view.search_button.isEnabled())

    def test_async_results_source_table_and_threshold(self):
        self.search()
        self.assertEqual(self.view.table.rowCount(),1)
        self.assertTrue(all(t!=get_ident() for t in self.provider.threads))
        self.assertEqual(self.view.table.item(0,13).text(),'Spansh')
        self.assertEqual(self.view.rows[0].total_profit,285000)
        self.assertFalse(self.view.cancel_button.isVisible())
        self.view.margin.setValue(20);self.search()
        self.assertFalse(self.view.rows)

    def test_local_preview_and_no_network_on_open(self):
        self.cache.put(market(mid=3))
        self.assertFalse(self.provider.calls)
        self.provider.gate.clear();self.view.start_search()
        deadline=time.monotonic()+1
        while not self.view.rows and time.monotonic()<deadline:
            self.app.processEvents();QTest.qWait(5)
        self.assertEqual(self.view.rows[0].destination.provider,'local_elite')
        self.assertEqual(self.view.table.item(0,13).text(),'Elite lokal')
        self.assertIn('Prüfe Waren',self.view.status.text())
        self.assertTrue(self.view.cancel_button.isVisible())
        self.view.cancel_search();self.wait();self.assertFalse(self.view.rows)

    def test_queued_results_discarded_after_all_context_changes(self):
        actions=[lambda:setattr(self.state,'system','Other System'),
                 lambda:setattr(self.state,'station','Other Station'),
                 lambda:setattr(self.state,'commander_fid','F_OTHER'),
                 lambda:self.state.cargo_snapshot.update(count=250)]
        for action in actions:
            self.state.system='Fixture System';self.state.station='Fixture Port';self.state.commander_fid=FID
            self.state.cargo_snapshot['count']=20;self.view.refresh()
            self.provider.gate.clear();self.view.start_search()
            action();self.state.changed.emit()
            self.provider.gate.set();self.wait()
            self.assertFalse(self.view.rows)
            self.assertEqual(self.view.last_run.partial_reason,PartialReason.CONTEXT_CHANGED)
            self.assertTrue(self.view.progress_bar.isHidden())
            self.assertEqual(self.view.progress_bar.value(),0)
            calls=len(self.provider.calls);self.app.processEvents();self.assertEqual(len(self.provider.calls),calls)

    def test_market_update_invalidates_finished_and_running_results(self):
        self.search();self.assertTrue(self.view.rows)
        for running in (False,True):
            if running:self.provider.gate.clear();self.view.start_search()
            self.now+=timedelta(seconds=1)
            self.cache.put(market(stamp=self.now))
            self.assertFalse(self.view.rows)
            if running:self.provider.gate.set();self.wait();self.assertFalse(self.view.rows)

    def test_cargo_signal_invalidates_and_updates_free(self):
        self.search();self.state.cargo_snapshot['count']=200
        self.state.cargoSnapshotChanged.emit(self.state.cargo_snapshot)
        self.assertEqual(self.view.free,100);self.assertFalse(self.view.rows)
        self.assertEqual(len(self.provider.calls),1)

    def test_tab_switch_and_cancel_late_output(self):
        for switch in (False,True):
            self.trade.tabs.setCurrentIndex(2);self.provider.gate.clear();self.view.start_search()
            if switch:self.trade.tabs.setCurrentIndex(0)
            else:self.view.cancel_button.click()
            self.provider.gate.set();self.wait();self.assertFalse(self.view.rows)
            self.assertEqual(self.view.last_run.partial_reason,
                             PartialReason.CONTEXT_CHANGED if switch else PartialReason.CANCELLED)
            self.assertTrue(self.view.progress_bar.isHidden())
            self.assertEqual(self.view.progress_bar.value(),0)

    def test_diagnostics_current_and_last_run_and_partial_message(self):
        self.search()
        previous=self.view.last_run
        self.assertFalse(previous.partial)
        self.assertIsNone(self.view.current_run)
        self.assertIn('1 von 1 Waren geprüft',self.view.status.text())
        self.provider.gate.clear();self.view.start_search()
        deadline=time.monotonic()+1
        while (self.view.current_run is None or self.view.current_run.spansh_commodities_started==0) and time.monotonic()<deadline:
            self.app.processEvents();QTest.qWait(5)
        self.assertIs(self.view.last_run,previous)
        self.assertEqual(self.view.current_run.spansh_commodities_started,1)
        self.assertEqual(self.view.current_run.spansh_commodities_completed,0)
        self.assertIn('0 von 1',self.view.status.text())
        self.view.cancel_search();self.wait()
        self.assertEqual(self.view.last_run.partial_reason,PartialReason.CANCELLED)
        self.assertIsNone(self.view.current_run)
        self.cache.put(market(mid=2))
        with patch.object(self.provider,'search_sell',return_value=MarketSearchResult(MarketStatus.TIMEOUT)):
            self.search()
        self.assertIn('Unvollständige Suche: 1 von 1 Waren geprüft.',self.view.status.text())
        self.assertIn('Zeitlimit',self.view.status.text())
        self.assertIn('Spansh: 1 begonnen, 1 abgeschlossen',self.view.status.toolTip())
        self.assertEqual(self.view.last_run.partial_reason,PartialReason.PROVIDER_TIMEOUT)
        self.assertEqual(self.view.table.rowCount(),1)
        self.assertEqual(self.view.rows[0].destination.provider,'local_elite')

    def test_unknown_distance_excluded_and_same_system_zero(self):
        self.assertEqual(local_distances(self.state,market(),[market(mid=2)]),{2:0.0})
        self.assertEqual(local_distances(self.state,market(),[market(mid=2,system_address=200)]),{})
        import sqlite3
        con=sqlite3.connect(':memory:')
        con.execute('CREATE TABLE systems (system_address INTEGER,name TEXT,x REAL,y REAL,z REAL)')
        con.executemany('INSERT INTO systems VALUES (?,?,?,?,?)',[(100,'Fixture System',0,0,0),(200,'Target',3,4,0)])
        self.state.database=SimpleNamespace(_connect=lambda:con)
        self.assertEqual(local_distances(self.state,market(),[market(mid=2,system_address=200)]),{2:5.0})
        con.close()

    def test_numeric_sorting_all_columns_and_source_age(self):
        a=Recommendation(offer(mid=2,commander_sell_price=11000,demand=10,distance_ly=2,
                 distance_to_arrival_ls=20,largest_pad=PadSize.SMALL),10000,10)
        b=Recommendation(offer(mid=3,master=GOLD,commander_sell_price=15000,demand=100,
                 distance_ly=100,distance_to_arrival_ls=100,largest_pad=PadSize.LARGE,
                 stamp=NOW-timedelta(hours=2),provider='local_elite'),9000,100)
        self.view.render((a,b));table=self.view.table
        self.assertEqual(table.item(0,1).data(Qt.ItemDataRole.UserRole),b)
        for column in (2,3,4,5,6,7,10,11,14):
            table.sortItems(column,Qt.SortOrder.AscendingOrder)
            self.assertLessEqual(table.item(0,column).value,table.item(1,column).value)
        table.sortItems(12,Qt.SortOrder.AscendingOrder)
        self.assertEqual(table.item(0,12).rank,1)
        table.sortItems(12,Qt.SortOrder.DescendingOrder)
        self.assertEqual(table.item(0,12).rank,3)
        table.sortItems(13,Qt.SortOrder.AscendingOrder)
        self.assertEqual(table.item(0,13).text(),'Elite lokal')
        table.sortItems(13,Qt.SortOrder.DescendingOrder)
        self.assertEqual(table.item(0,13).text(),'Spansh')

    def test_potential_profit_position_format_sort_and_unchanged_values(self):
        table=self.view.table
        self.assertEqual([table.horizontalHeaderItem(i).text() for i in range(1,5)],
                         [tr('trade.commodity'),'Möglicher Gewinn',tr('recommend.profit_percent'),tr('trade.quantity')])
        values=(0,7,535020,1916970,6826500,9876543210)
        rows=tuple(Recommendation(offer(mid=i+2,commander_sell_price=10000+profit),10000,1)
                   for i,profit in enumerate(values))
        self.view.render(rows)
        self.assertEqual(self.view.rows,rows)
        self.assertEqual(table.horizontalHeader().sortIndicatorSection(),2)
        self.assertEqual(table.horizontalHeader().sortIndicatorOrder(),Qt.SortOrder.DescendingOrder)
        self.assertEqual([table.item(i,2).value for i in range(len(rows))],list(reversed(values)))
        for order,expected in ((Qt.SortOrder.AscendingOrder,list(values)),
                               (Qt.SortOrder.DescendingOrder,list(reversed(values)))):
            table.sortItems(2,order)
            self.assertEqual([table.item(i,2).value for i in range(len(rows))],expected)
            for index,profit in enumerate(expected):
                cell=table.item(index,2)
                self.assertEqual(cell.text(),format(profit,',').replace(',','.')+' Cr')
                self.assertTrue(cell.font().bold())
                row=table.item(index,1).data(Qt.ItemDataRole.UserRole)
                self.assertEqual(cell.value,row.total_profit)
                self.assertEqual(cell.value,row.profit_per_ton*row.quantity)
                self.assertEqual(table.item(index,3).value,row.profit_percent)
                self.assertEqual(table.item(index,4).value,row.quantity)
                self.assertEqual(table.item(index,5).value,row.buy_price)
                self.assertEqual(table.item(index,6).value,row.destination.commander_sell_price)
                self.assertEqual(table.item(index,7).value,row.profit_per_ton)
                self.assertEqual(table.item(index,8).text(),row.destination.station_name)
                self.assertEqual(table.item(index,9).text(),row.destination.system_name)

    def test_potential_profit_visible_desktop_all_languages_and_themes(self):
        from PySide6.QtCore import QLocale
        from cmdrhelper.ui.recommendations_view import RecommendationsView
        style=self.app.styleSheet()
        try:
            for lang in ('de','en','el','es','fi','fr','it','nl','no','pl','sv','tr'):
                set_language(lang)
                for theme in (DARK_STYLESHEET,LIGHT_STYLESHEET):
                    for size in (10,18):
                        with self.subTest(lang=lang,size=size,theme=theme==DARK_STYLESHEET):
                            self.app.setStyleSheet(theme+f'\nQWidget {{ font-size: {size}pt; }}')
                            view=RecommendationsView(self.state,self.provider,self.pool)
                            view.resize(1100,900);view.show()
                            row=Recommendation(offer(commander_sell_price=32755),10000,300)
                            view.render((row,));self.app.processEvents()
                            table=view.table
                            self.assertEqual(table.horizontalHeaderItem(2).text(),tr('recommend.total_profit'))
                            self.assertEqual(table.item(0,2).text(),QLocale(lang).toString(row.total_profit)+' Cr')
                            self.assertEqual(table.horizontalScrollBar().value(),0)
                            # All four decision columns fit without scrolling, including large fonts.
                            for column in range(5):
                                rect=table.visualItemRect(table.item(0,column))
                                self.assertGreaterEqual(rect.left(),0)
                                self.assertLessEqual(rect.right(),table.viewport().width())
                            view.close();view.deleteLater()
                            self.app.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        finally:self.app.setStyleSheet(style)

    def test_search_button_scoped_border_hover_focus_disabled_and_large_font(self):
        from PySide6.QtGui import QImage, QPainter
        from PySide6.QtWidgets import QPushButton, QStyle, QStyleOptionButton
        button=self.view.search_button
        self.assertEqual(button.objectName(),'recommendationSearch')
        self.assertNotEqual(self.view.cancel_button.objectName(),'recommendationSearch')
        plain=QPushButton('Synthetic action',button.parentWidget())
        def render(control,flags):
            control.setEnabled(bool(flags & QStyle.State_Enabled))
            control.ensurePolished()
            control.resize(control.sizeHint().expandedTo(button.sizeHint()))
            option=QStyleOptionButton();control.initStyleOption(option);option.state=flags
            image=QImage(control.size(),QImage.Format_ARGB32);image.fill(Qt.transparent)
            painter=QPainter(image)
            control.style().drawControl(QStyle.CE_PushButton,option,painter,control)
            painter.end()
            return image
        for theme,border,hover,disabled,background in (
                (DARK_STYLESHEET,'#c49a3c','#f0c65b','#28323b','#111820'),
                (LIGHT_STYLESHEET,'#a57b1c','#c18e1c','#bfc7ce','#ffffff')):
            for size in (10,18):
                self.view.setStyleSheet(theme+f'\nQWidget {{ font-size: {size}pt; }}')
                for flags,color in ((QStyle.State_Enabled,border),
                        (QStyle.State_Enabled|QStyle.State_MouseOver,hover),
                        (QStyle.State_Enabled|QStyle.State_HasFocus,hover),
                        (QStyle.State_None,disabled),
                        (QStyle.State_MouseOver|QStyle.State_HasFocus,disabled)):
                    with self.subTest(size=size,color=color,flags=flags):
                        image=render(button,flags)
                        middle=image.width()//2
                        self.assertEqual(image.pixelColor(middle,0).name(),color)
                        if flags & QStyle.State_Enabled and flags & QStyle.State_HasFocus:
                            self.assertEqual(image.pixelColor(middle,1).name(),color)
                        if not flags & QStyle.State_Enabled:
                            self.assertEqual(image.pixelColor(middle,2).name(),background)
                        else:
                            other=render(plain,flags & ~QStyle.State_HasFocus)
                            self.assertEqual(image.pixelColor(middle,3),other.pixelColor(other.width()//2,3))
                            self.assertEqual(other.pixelColor(other.width()//2,0).name(),disabled)
                        self.assertGreaterEqual(button.width(),button.fontMetrics().horizontalAdvance(button.text())+14)
        self.assertFalse(self.provider.calls)
        plain.deleteLater()
        self.view.refresh()

    def test_primary_button_keeps_existing_click_and_enable_behavior(self):
        self.assertTrue(self.view.search_button.isEnabled())
        self.provider.gate.clear()
        self.view.search_button.click()
        self.assertIsNotNone(self.view.worker)
        self.assertFalse(self.view.search_button.isEnabled())
        self.provider.gate.set();self.wait()
        self.assertTrue(self.view.search_button.isEnabled())
        self.assertEqual(len(self.provider.calls),1)
        self.state.cargo_snapshot['count']=300
        self.view.refresh()
        self.assertFalse(self.view.search_button.isEnabled())
        self.view.search_button.click()
        self.assertEqual(len(self.provider.calls),1)

    def start_controlled_progress(self):
        # No worker execution/network: deliver the existing structured signals explicitly.
        with patch.object(self.pool,'start') as start:
            self.view.start_search()
            start.assert_called_once()
        return self.view.worker

    def test_progress_idle_start_unknown_then_real_counts(self):
        bar=self.view.progress_bar
        self.assertTrue(bar.isHidden())
        worker=self.start_controlled_progress()
        self.assertFalse(bar.isHidden())
        self.assertEqual((bar.minimum(),bar.maximum()),(0,0))
        self.assertTrue(self.view.cancel_button.isVisible())
        self.assertFalse(self.view.search_button.isEnabled())
        for checked in (0,1,18,51,52):
            diagnostic=RecommendationDiagnostics(planned_commodities=52,checked_commodities=checked)
            worker.signals.diagnostic.emit(diagnostic)
            self.assertEqual((bar.minimum(),bar.maximum(),bar.value()),(0,52,checked))
            self.assertAlmostEqual(bar.value()/bar.maximum()*100,checked/52*100)
            self.assertIn(f'{checked} von 52',self.view.status.text())
            self.assertIn(f'{checked} von 52',bar.accessibleName())
        self.assertFalse(self.provider.calls)
        worker.signals.finished.emit(RecommendationResult(checked=52,total=52,diagnostics=diagnostic))
        self.assertTrue(bar.isHidden())
        self.assertEqual(bar.value(),bar.maximum())

    def test_progress_uses_diagnostic_counts_not_legacy_result_fields(self):
        worker=self.start_controlled_progress()
        d=RecommendationDiagnostics(planned_commodities=52,checked_commodities=18)
        worker.signals.progress.emit(RecommendationResult(checked=99,total=100,diagnostics=d))
        self.assertEqual((self.view.progress_bar.value(),self.view.progress_bar.maximum()),(18,52))
        self.assertIn('18 von 52',self.view.status.text())
        worker.signals.finished.emit(RecommendationResult(checked=18,total=52,partial=True,diagnostics=d))

    def test_progress_completion_reaches_maximum_before_hiding(self):
        worker=self.start_controlled_progress();bar=self.view.progress_bar
        worker.signals.diagnostic.emit(RecommendationDiagnostics(planned_commodities=52,checked_commodities=51))
        values=[]
        bar.valueChanged.connect(lambda value:values.append((value,bar.isVisible())))
        worker.signals.finished.emit(RecommendationResult(checked=52,total=52,
            diagnostics=RecommendationDiagnostics(planned_commodities=52,checked_commodities=52)))
        self.assertIn((52,True),values)
        self.assertEqual((bar.value(),bar.maximum()),(52,52))
        self.assertTrue(bar.isHidden())
        self.assertFalse(self.view.cancel_button.isVisible())
        self.assertIn('52 von 52 Waren geprüft',self.view.status.text())

    def test_partial_timeout_rate_limit_never_forced_to_100(self):
        for reason in (PartialReason.OTHER,PartialReason.PROVIDER_TIMEOUT,PartialReason.PROVIDER_RATE_LIMIT):
            worker=self.start_controlled_progress();bar=self.view.progress_bar
            d=RecommendationDiagnostics(planned_commodities=52,checked_commodities=18,
                                        partial=True,partial_reason=reason)
            worker.signals.progress.emit(RecommendationResult(checked=18,total=52,partial=True,diagnostics=d))
            values=[];bar.valueChanged.connect(values.append)
            worker.signals.finished.emit(RecommendationResult(checked=18,total=52,partial=True,diagnostics=d))
            bar.valueChanged.disconnect(values.append)
            self.assertEqual((bar.value(),bar.maximum()),(18,52))
            self.assertNotIn(52,values)
            self.assertTrue(bar.isHidden())
            self.assertIn('Unvollständige Suche: 18 von 52',self.view.status.text())
            self.assertEqual(self.view.last_run.partial_reason,reason)

    def test_progress_cancel_context_and_old_signals_are_ignored(self):
        for reason in (PartialReason.CANCELLED,PartialReason.CONTEXT_CHANGED):
            worker=self.start_controlled_progress();bar=self.view.progress_bar
            d=RecommendationDiagnostics(planned_commodities=52,checked_commodities=18)
            worker.signals.diagnostic.emit(d)
            if reason==PartialReason.CANCELLED:self.view.cancel_search()
            else:self.view.invalidate()
            self.assertTrue(bar.isHidden())
            self.assertEqual(bar.value(),0)
            late=RecommendationDiagnostics(planned_commodities=52,checked_commodities=52)
            worker.signals.diagnostic.emit(late)
            worker.signals.progress.emit(RecommendationResult(checked=52,total=52,diagnostics=late))
            self.assertTrue(bar.isHidden());self.assertEqual(bar.value(),0)
            worker.signals.finished.emit(RecommendationResult(cancelled=True,diagnostics=d))
            self.assertEqual(self.view.last_run.partial_reason,reason)
            new_worker=self.start_controlled_progress()
            current=RecommendationDiagnostics(planned_commodities=3,checked_commodities=1)
            new_worker.signals.diagnostic.emit(current)
            # A previous worker must not overwrite or finish the new run.
            worker.signals.diagnostic.emit(late)
            worker.signals.progress.emit(RecommendationResult(diagnostics=late))
            worker.signals.finished.emit(RecommendationResult(diagnostics=late))
            self.assertIs(self.view.worker,new_worker)
            self.assertEqual((bar.value(),bar.maximum()),(1,3))
            new_worker.signals.finished.emit(RecommendationResult(checked=1,total=3,partial=True,diagnostics=current))

    def test_empty_known_plan_is_not_indeterminate(self):
        worker=self.start_controlled_progress()
        worker.signals.diagnostic.emit(RecommendationDiagnostics())
        self.assertGreater(self.view.progress_bar.maximum(),0)
        self.assertEqual(self.view.progress_bar.value(),0)
        self.assertIn('0 von 0',self.view.status.text())
        worker.signals.finished.emit(RecommendationResult(diagnostics=RecommendationDiagnostics()))
        self.assertTrue(self.view.progress_bar.isHidden())

    def test_progress_bar_theme_fill_is_scoped(self):
        from PySide6.QtGui import QImage, QPainter
        from PySide6.QtWidgets import QStyle, QStyleOptionProgressBar
        bar=self.view.progress_bar
        for theme,color in ((DARK_STYLESHEET,'#c57a00'),(LIGHT_STYLESHEET,'#c56f00')):
            self.view.setStyleSheet(theme)
            bar.ensurePolished();bar.resize(200,10)
            bar.setRange(0,52);bar.setValue(18)
            option=QStyleOptionProgressBar();bar.initStyleOption(option)
            image=QImage(bar.size(),QImage.Format_ARGB32);image.fill(Qt.transparent)
            painter=QPainter(image)
            bar.style().drawControl(QStyle.CE_ProgressBar,option,painter,bar);painter.end()
            self.assertEqual(image.pixelColor(20,5).name(),color)
            self.assertNotEqual(image.pixelColor(180,5).name(),color)

    def test_copy_diagnostic_disabled_until_completed_and_preserves_results(self):
        from cmdrhelper.recommendation_diagnostic_text import format_recommendation_diagnostic
        button=self.view.copy_diagnostic_button
        self.assertFalse(button.isEnabled())
        self.assertNotEqual(button.objectName(),'recommendationSearch')
        with patch.object(QApplication,'clipboard') as clipboard:
            self.view.copy_diagnostic()
            clipboard.assert_not_called()
            self.search()
            self.assertTrue(button.isEnabled())
            rows=self.view.rows;message=self.view.status.text();calls=len(self.provider.calls)
            button.click()
            clipboard.return_value.setText.assert_called_once_with(
                format_recommendation_diagnostic(self.view.last_run))
            self.assertEqual(self.view.copy_notice.text(),tr('recommend.diagnostic_copied'))
            self.assertEqual(self.view.rows,rows)
            self.assertEqual(self.view.status.text(),message)
            self.assertEqual(len(self.provider.calls),calls)
            self.assertTrue(self.view.copy_notice_timer.isSingleShot())
            self.view.copy_notice_timer.timeout.emit()
            self.assertEqual(self.view.copy_notice.text(),'')

    def test_copy_uses_real_isolated_qt_clipboard(self):
        if QApplication.platformName()!='offscreen':
            self.skipTest('Do not replace the desktop clipboard during automated tests')
        clipboard=QApplication.clipboard()
        old=clipboard.text()
        try:
            clipboard.setText('synthetic clipboard sentinel')
            self.search()
            self.view.copy_diagnostic_button.click()
            text=clipboard.text()
            self.assertTrue(text.startswith('CMDRHelper trade recommendation diagnostic\n'))
            self.assertIn('planned_commodities=1\n',text)
            self.assertIn('spansh_commodities_completed=1\n',text)
            self.assertIn('partial_reason=NONE\n',text)
            self.assertIn('cache_hits=0\n',text)
            self.assertNotIn(FID,text)
            self.assertNotIn('Synthetic Ship',text)
        finally:clipboard.setText(old)

    def test_copy_partial_and_next_completed_run_replaces_previous(self):
        with patch.object(QApplication,'clipboard') as clipboard:
            with patch.object(self.provider,'search_sell',return_value=MarketSearchResult(MarketStatus.TIMEOUT)):
                self.search()
            old=self.view.last_run
            self.assertTrue(self.view.copy_diagnostic_button.isEnabled())
            self.view.copy_diagnostic_button.click()
            text=clipboard.return_value.setText.call_args.args[0]
            self.assertIn('partial=true',text)
            self.assertIn('partial_reason=PROVIDER_TIMEOUT',text)
            self.provider.gate.clear();self.view.start_search()
            self.view.copy_diagnostic_button.click()
            self.assertEqual(clipboard.return_value.setText.call_args.args[0],text)
            self.assertIs(self.view.last_run,old)
            self.provider.gate.set();self.wait()
            self.assertIsNot(self.view.last_run,old)
            self.view.copy_diagnostic_button.click()
            new=clipboard.return_value.setText.call_args.args[0]
            self.assertIn('partial=false',new)
            self.assertIn('partial_reason=NONE',new)
            self.assertNotEqual(new,text)

    def test_copy_completed_cancel_and_context_diagnostic(self):
        for reason in (PartialReason.CANCELLED,PartialReason.CONTEXT_CHANGED):
            self.provider.gate.clear();self.view.start_search()
            if reason==PartialReason.CANCELLED:self.view.cancel_search()
            else:self.view.cancel_for_context()
            self.provider.gate.set();self.wait()
            self.assertTrue(self.view.copy_diagnostic_button.isEnabled())
            with patch.object(QApplication,'clipboard') as clipboard:
                self.view.copy_diagnostic_button.click()
                text=clipboard.return_value.setText.call_args.args[0]
                self.assertIn('cancelled=true',text)
                self.assertIn('partial_reason='+reason.value,text)
                self.assertIn('context_changed='+str(reason==PartialReason.CONTEXT_CHANGED).lower(),text)

    def test_gold_ui_query_validates_like_sell_and_old_string_is_rejected(self):
        from dataclasses import fields
        from cmdrhelper.spansh_market import SpanshMarketProvider, _valid_query
        from cmdrhelper.trade_recommendations import search_recommendations
        self.now+=timedelta(seconds=1)
        self.cache.put(market(stamp=self.now,rows=[item(GOLD)]))
        for index,pad in enumerate(PadSize):
            self.view.pad.setCurrentIndex(index)
            worker=self.start_controlled_progress()
            queries=[]
            class Capture:
                def search_sell(self,q,*,cancel):
                    queries.append(q)
                    return MarketSearchResult(MarketStatus.NO_RESULTS)
            search_recommendations(*worker.args[:6],Capture(),clock=lambda:self.now)
            q=queries[0]
            self.assertEqual(q.commodity,128049154)
            self.assertIs(type(q.required_pad),PadSize)
            self.assertEqual(q.required_pad,pad)
            self.assertTrue(_valid_query(q))
            # Reconstruct the exact pre-fix Qt conversion, without changing validation.
            raw=self.view.pad.currentData()
            self.assertIs(type(raw),str)
            legacy=replace(q,required_pad=raw)
            self.assertFalse(_valid_query(legacy))
            with patch('cmdrhelper.spansh_transport.urlopen',side_effect=AssertionError('No network')) as network:
                rejected=SpanshMarketProvider().search_sell(legacy)
            self.assertEqual(rejected.status,MarketStatus.INVALID_QUERY)
            self.assertEqual(rejected.diagnostics.http_requests,0)
            network.assert_not_called()
            worker.signals.finished.emit(RecommendationResult(diagnostics=RecommendationDiagnostics(finished_at=self.now)))
            self.trade.tabs.setCurrentIndex(0)
            self.trade.commodity.set_commodity(GOLD.frontier_id)
            self.trade.pad.setCurrentIndex(index)
            with patch.object(self.pool,'start'):self.trade.start_search()
            sell=self.trade._query
            self.assertTrue(_valid_query(sell))
            for field in fields(q):
                self.assertEqual(getattr(q,field.name),getattr(sell,field.name),field.name)
                self.assertIs(type(getattr(q,field.name)),type(getattr(sell,field.name)),field.name)
            # Release the manually held Sell worker through its existing completion signal.
            self.trade.worker.signals.finished.emit(MarketSearchResult(MarketStatus.NO_RESULTS,query=sell))
            self.trade.tabs.setCurrentIndex(2)

    def test_52_real_ui_request_forms_reach_fake_transport_after_pad_fix(self):
        import io,json
        from cmdrhelper.commodity_master import all_commodities
        from cmdrhelper.spansh_market import SpanshMarketProvider, _valid_query
        from cmdrhelper.trade_recommendations import search_recommendations
        definitions=[GOLD]+[c for c in all_commodities() if c!=GOLD][:51]
        self.now+=timedelta(seconds=1)
        self.cache.put(market(stamp=self.now,rows=[item(c) for c in definitions]))
        worker=self.start_controlled_progress()
        args=worker.args
        seconds=[1000.0];requests=[];queries=[]
        class OfflineCancel(Event):
            def wait(self,timeout=None):
                seconds[0]+=timeout or 0
                return self.is_set()
        def opener(request,*,timeout):
            requests.append(request)
            data=({'values':['Coriolis','Fleet Carrier']} if request.method=='GET' else
                  {'reference':{'name':'Fixture System'},'results':[],'count':0})
            return io.BytesIO(json.dumps(data).encode())
        class CheckedProvider(SpanshMarketProvider):
            def search_sell(self,q,**kwargs):
                queries.append(q)
                return super().search_sell(q,**kwargs)
        provider=CheckedProvider(opener=opener,clock=lambda:seconds[0],utcnow=lambda:self.now)
        with patch('cmdrhelper.spansh_transport.urlopen',side_effect=AssertionError('No internet')) as network:
            legacy_args=(*args[:5],replace(args[5],required_pad=self.view.pad.currentData()))
            before=search_recommendations(*legacy_args,provider,cancel=OfflineCancel(),clock=lambda:self.now)
            self.assertEqual(before.diagnostics.failed_commodities,52)
            self.assertEqual(before.diagnostics.http_requests,0)
            self.assertEqual(before.diagnostics.partial_reason,PartialReason.OTHER)
            self.assertTrue(all(s.provider_status==MarketStatus.INVALID_QUERY for s in before.diagnostics.steps))
            self.assertFalse(requests)
            queries.clear()
            after=search_recommendations(*args[:6],provider,cancel=OfflineCancel(),clock=lambda:self.now)
            network.assert_not_called()
        self.assertEqual(len(queries),52)
        self.assertTrue(all(_valid_query(q) for q in queries))
        self.assertTrue(all(q.minimum_quantity==1 and q.limit==100 for q in queries))
        self.assertEqual(queries[0].commodity,GOLD.frontier_id)
        self.assertEqual(after.diagnostics.successful_commodities,52)
        self.assertEqual(after.diagnostics.failed_commodities,0)
        self.assertFalse(after.partial)
        self.assertEqual(after.diagnostics.spansh_commodities_completed,52)
        self.assertEqual(after.diagnostics.http_requests,len(requests))
        self.assertEqual(len(requests),53)  # one metadata GET plus 52 synthetic market POSTs
        self.assertTrue(all(s.provider_status==MarketStatus.NO_RESULTS for s in after.diagnostics.steps))
        worker.signals.finished.emit(after)

    def test_local_only_checkbox_default_notice_retention_and_zero_provider_calls(self):
        self.assertFalse(self.view.local_only.isChecked())
        self.assertEqual(self.view.notice.text(),tr('recommend.notice'))
        self.cache.put(market(mid=2))
        self.view.local_only.setChecked(True)
        self.assertEqual(self.view.local_only.text(),'Nur eigene Marktdaten')
        self.assertIn('24 Stunden',self.view.local_only.toolTip())
        self.assertEqual(self.view.notice.text(),tr('recommend.local_notice'))
        with patch.object(self.provider,'search_sell',side_effect=AssertionError('No provider')) as provider:
            self.search();provider.assert_not_called()
        self.assertEqual(len(self.view.rows),1)
        self.assertEqual(self.view.table.item(0,13).text(),'Elite lokal')
        self.assertEqual(self.view.table.item(0,2).value,285000)
        d=self.view.last_run
        self.assertTrue(d.local_only)
        self.assertEqual((d.planned_commodities,d.checked_commodities,d.successful_commodities),(1,1,1))
        self.assertEqual((d.http_requests,d.spansh_commodities_started,d.spansh_commodities_completed,
                          d.spansh_commodities_failed),(0,0,0,0))
        self.assertFalse(d.partial)
        self.assertEqual(self.view.progress_bar.value(),self.view.progress_bar.maximum())
        with patch.object(QApplication,'clipboard') as clipboard:
            self.view.copy_diagnostic_button.click()
            self.assertIn('local_only=true',clipboard.return_value.setText.call_args.args[0])
        self.trade.tabs.setCurrentIndex(0);self.trade.tabs.setCurrentIndex(2)
        self.assertTrue(self.view.local_only.isChecked())
        self.view.local_only.setChecked(False)
        self.assertEqual(self.view.notice.text(),tr('recommend.notice'))
        self.search();self.assertEqual(len(self.provider.calls),1)
        self.assertFalse(self.view.last_run.local_only)

    def test_current_market_status_missing_marketid_fid_source_and_in_flight(self):
        badge=self.view.market_read_status
        self.assertEqual(badge.status,'read');self.assertTrue(badge.property('observed'))
        self.state.observed_markets.context['MarketID']=999
        self.state.changed.emit()
        self.assertEqual(badge.status,'open');self.assertFalse(badge.property('observed'))
        self.assertIn('Fixture Port',self.view.origin_label.text())
        self.assertEqual(badge.text(),'Warenmarkt öffnen')
        self.cache.put(market(mid=999,fid='F_OTHER'))
        self.assertEqual(badge.status,'open')
        self.state.observed_markets.context['MarketID']=1
        with patch.object(self.cache,'get',return_value=market(source='spansh')):
            self.state.changed.emit();self.assertEqual(badge.status,'open')
        self.state.observed_markets.context={'FID':FID}  # observer clears docking identity on departure
        self.state.changed.emit()
        self.assertTrue(badge.isHidden())
        self.assertIsNone(self.view.origin)
        self.assertFalse(self.view.search_button.isEnabled())

    def test_current_market_status_ttl_exact_boundary_no_polling_and_refresh(self):
        badge=self.view.market_read_status
        self.now=NOW+timedelta(hours=24,seconds=-1)
        self.state.changed.emit();self.assertEqual(badge.status,'read')
        self.now+=timedelta(seconds=1)
        self.cache.all(FID)  # normal cache cleanup signal drives the view
        self.assertEqual(badge.status,'expired')
        self.assertEqual(badge.text(),'Marktstand veraltet')
        self.assertIn('erneut',badge.toolTip())
        self.assertIsNone(self.view.origin)
        self.assertFalse(self.view.search_button.isEnabled())
        self.state.changed.emit();self.assertEqual(badge.status,'expired')
        self.cache.put(market(stamp=self.now))
        self.assertEqual(badge.status,'read')
        self.assertEqual(self.view.origin['observed_at'],self.now.isoformat())
        self.assertEqual(len(self.cache.all(FID)),1)

    def test_current_market_same_station_reobserved_age_and_commander_switch(self):
        self.now+=timedelta(minutes=10);self.state.changed.emit()
        old=self.view.origin_label.text()
        self.cache.put(market(stamp=self.now))
        self.assertEqual(self.view.market_read_status.status,'read')
        self.assertNotEqual(self.view.origin_label.text(),old)
        self.assertEqual(len(self.cache.all(FID)),1)
        self.state.commander_fid='F_OTHER'
        self.state.observed_markets.context['FID']='F_OTHER'
        self.state.commanderIdentityChanged.emit(2,'F_OTHER','Synthetic Commander')
        self.assertEqual(self.view.market_read_status.status,'open')
        self.cache.put(market(fid='F_OTHER',stamp=self.now))
        self.assertEqual(self.view.market_read_status.status,'read')
        self.state.station='Synthetic New Port'
        self.state.observed_markets.context.update(MarketID=44,StationName=self.state.station)
        self.state.changed.emit();self.assertEqual(self.view.market_read_status.status,'open')
        self.cache.put(market(mid=44,fid='F_OTHER',station_name=self.state.station,stamp=self.now))
        self.assertEqual(self.view.market_read_status.status,'read')

    def test_synthetic_market_event_observer_signal_updates_status(self):
        import json,os
        from cmdrhelper.observed_market_observer import ObservedMarketObserver
        from test_observed_market_cache import event,sidecar
        root=Path(self.tmp.name)
        journal=root/'Journal.2026-01-02T120000.01.log'
        journal.write_text(json.dumps(dict(event='LoadGame',FID=FID))+'\n')
        observer=ObservedMarketObserver(self.cache,clock=lambda:self.now)
        observer.set_folder(root);observer.consume([journal])
        self.state.observed_markets=observer
        def append(row):
            with journal.open('a') as stream:stream.write(json.dumps(row)+'\n')
            observer.consume([journal])
        append(dict(event(),event='Docked'))
        self.state.changed.emit()
        self.assertEqual(self.view.market_read_status.status,'open')
        path=root/'Market.json';path.write_text(json.dumps(sidecar()))
        os.utime(path,(self.now.timestamp(),self.now.timestamp()))
        append(event())
        # No view.refresh() or page switch: successful atomic cache write emits the update.
        self.assertEqual(self.view.market_read_status.status,'read')
        self.assertEqual(self.view.origin['market_id'],123)
        append(dict(event='Undocked',timestamp=self.now.isoformat()))
        self.state.changed.emit()
        self.assertTrue(self.view.market_read_status.isHidden())

    def test_painted_market_badge_dark_light_and_no_emoji(self):
        from PySide6.QtGui import QColor
        badge=self.view.market_read_status
        for theme,color in ((DARK_STYLESHEET,'#79bd8a'),(LIGHT_STYLESHEET,'#247a41')):
            self.view.setStyleSheet(theme);badge.set_status('read');self.app.processEvents()
            image=badge.grab().toImage()
            top=max(2,int((badge.fontMetrics().height()-12)/2))
            pixels={image.pixelColor(x,y).name() for x in range(3,14) for y in range(top+1,top+12)}
            self.assertIn(color,pixels)
            self.assertIn('#ffffff',pixels)
            self.assertEqual(badge.text(),tr('recommend.market_read'))
            badge.set_status('open');self.assertFalse(badge.property('observed'))
            self.app.processEvents()
            image=badge.grab().toImage()
            pixels={image.pixelColor(x,y).name() for x in range(3,14) for y in range(top+1,top+12)}
            self.assertNotIn(color,pixels)

    def test_twelve_languages_help_dark_light_large_and_narrow(self):
        style=self.app.styleSheet()
        long_station='Synthetic Long Station Name ' * 6
        self.now+=timedelta(seconds=1)
        self.state.station=long_station
        self.state.observed_markets.context['StationName']=long_station
        self.cache.put(market(stamp=self.now,station_name=long_station))
        try:
            for lang in ('de','en','el','es','fi','fr','it','nl','no','pl','sv','tr'):
                set_language(lang)
                text=help_topic('trade',lang).text
                self.assertIn('MarketID',text)
                self.assertIn(_TRANSLATIONS[lang]['recommend.title'],text)
                self.assertIn(_TRANSLATIONS[lang]['recommend.local_only'],text)
                for theme in (DARK_STYLESHEET,LIGHT_STYLESHEET):
                    for size in (10,18):
                        self.app.setStyleSheet(theme+f'\nQWidget {{ font-size: {size}pt; }}')
                        # Recreate to verify all labels, not just dynamic ones.
                        from cmdrhelper.ui.recommendations_view import RecommendationsView
                        view=RecommendationsView(self.state,self.provider,self.pool)
                        view.resize(620,900);view.show()
                        from cmdrhelper.ui.recommendations_view import diagnostic_reason_text
                        view.status.setText(tr('recommend.partial_counts',checked=18,total=52,
                            reason=diagnostic_reason_text(PartialReason.PROVIDER_TIMEOUT)))
                        view.progress_bar.show()
                        view.update_progress_bar(RecommendationDiagnostics(planned_commodities=52,checked_commodities=18))
                        self.app.processEvents()
                        self.assertEqual(view.progress_bar.height(),10)
                        self.assertLessEqual(view.progress_bar.width(),view.width())
                        self.assertIn('18',view.status.text())
                        self.assertIn('52',view.status.text())
                        self.assertEqual(view.local_only.text(),tr('recommend.local_only'))
                        view.local_only.setChecked(True)
                        self.assertEqual(view.notice.text(),tr('recommend.local_notice'))
                        self.assertEqual(view.market_read_status.text(),tr('recommend.market_read'))
                        self.assertIn(long_station,view.origin_label.text())
                        self.assertTrue(view.market_read_status.property('observed'))
                        self.assertGreaterEqual(view.market_read_status.height(),
                                                view.market_read_status.heightForWidth(view.market_read_status.width()))
                        self.assertEqual(view.search_button.text(),tr('recommend.search'))
                        self.assertEqual(view.copy_diagnostic_button.text(),tr('recommend.copy_diagnostic'))
                        view.last_run=RecommendationDiagnostics(finished_at=NOW)
                        view.copy_diagnostic_button.setEnabled(True)
                        with patch.object(QApplication,'clipboard'):
                            view.copy_diagnostic_button.click()
                        self.app.processEvents()
                        self.assertEqual(view.copy_notice.text(),tr('recommend.diagnostic_copied'))
                        self.assertLessEqual(view.copy_diagnostic_button.width(),view.width())
                        for label in (view.explanation,view.origin_label,view.ship_label,view.notice,view.status):
                            self.assertNotIn('recommend.',label.text())
                            self.assertGreaterEqual(label.height(),label.heightForWidth(label.width()))
                        self.assertGreaterEqual(view.table.height(),240)
                        view.close();view.deleteLater();self.app.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        finally:self.app.setStyleSheet(style)

    def mark_rows(self):
        from cmdrhelper.commodity_master import lookup_by_symbol
        return (Recommendation(offer(mid=2,master=lookup_by_symbol('Silver'),
                    system_name='Synthetic Silver System',station_name='Silver Port'),10000,10),
                Recommendation(offer(mid=3,master=GOLD,system_name='Synthetic Gold System',
                    station_name='Gold Port'),10000,20))

    def mark_item(self, row):
        from cmdrhelper.ui.recommendations_view import recommendation_identity
        return next(self.view.table.item(i,0) for i in range(self.view.table.rowCount())
                    if recommendation_identity(self.view.table.item(i,0).data(Qt.ItemDataRole.UserRole))
                    == recommendation_identity(row))

    def test_remember_single_toggle_and_identity_survives_sort_focus_scroll(self):
        from cmdrhelper.ui.recommendations_view import recommendation_identity
        silver,gold=self.mark_rows();self.view.render((silver,gold))
        self.assertFalse(self.view.copy_system_button.isEnabled())
        self.assertIsNone(self.view.remembered_identity)
        self.mark_item(silver).setCheckState(Qt.CheckState.Checked)
        for column in (2,3,8,9):
            for order in (Qt.SortOrder.AscendingOrder,Qt.SortOrder.DescendingOrder):
                self.view.table.sortItems(column,order)
                self.view.table.clearSelection();self.view.search_button.setFocus()
                self.view.table.horizontalScrollBar().setValue(500)
                self.app.processEvents()
                item=self.mark_item(silver)
                self.assertEqual(item.checkState(),Qt.CheckState.Checked)
                self.assertEqual(self.view.remembered_identity,recommendation_identity(silver))
                for c in range(15):
                    self.assertTrue(self.view.table.item(item.row(),c).data(Qt.ItemDataRole.UserRole+1))
        self.mark_item(gold).setCheckState(Qt.CheckState.Checked)
        self.assertEqual(self.mark_item(silver).checkState(),Qt.CheckState.Unchecked)
        self.assertEqual(self.mark_item(gold).checkState(),Qt.CheckState.Checked)
        self.mark_item(gold).setCheckState(Qt.CheckState.Unchecked)
        self.assertIsNone(self.view.remembered_identity)
        self.assertFalse(self.view.copy_system_button.isEnabled())

    def test_remember_keyboard_and_mouse_toggle(self):
        from PySide6.QtWidgets import QStyleOptionViewItem,QStyle
        self.view.render(self.mark_rows());table=self.view.table
        item=table.item(0,0);table.scrollToItem(item);table.setCurrentItem(item)
        self.app.processEvents()
        option=QStyleOptionViewItem();option.initFrom(table)
        table.itemDelegate().initStyleOption(option,table.indexFromItem(item))
        option.rect=table.visualItemRect(item)
        rect=table.style().subElementRect(QStyle.SubElement.SE_ItemViewItemCheckIndicator,option,table)
        QTest.mouseClick(table.viewport(),Qt.MouseButton.LeftButton,pos=rect.center())
        self.assertEqual(item.checkState(),Qt.CheckState.Checked)
        QTest.keyClick(table,Qt.Key.Key_Space)
        self.assertEqual(item.checkState(),Qt.CheckState.Unchecked)

    def test_remember_new_search_and_commander_clear(self):
        for change in ('search','commander'):
            with self.subTest(change=change):
                self.state.station='Fixture Port';self.state.commander_fid=FID
                self.view.refresh()
                self.view.render(self.mark_rows());self.view.table.item(0,0).setCheckState(Qt.CheckState.Checked)
                if change=='search':
                    self.view.start_search();self.wait()
                else:
                    signal={'station':self.state.changed,'commander':self.state.commanderIdentityChanged,
                            'cargo':self.state.cargoSnapshotChanged,'market':self.state.observedMarketsChanged}[change]
                    if change=='station':self.state.station='Changed Port';signal.emit()
                    elif change=='commander':self.state.commander_fid='F_OTHER';signal.emit(None,'','')
                    elif change=='cargo':self.state.cargo_snapshot['count']+=1;signal.emit(None)
                    else:signal.emit()
                self.assertIsNone(self.view.remembered_identity)
                self.assertFalse(self.view.copy_system_button.isEnabled())

    def test_remember_copy_exact_system_both_modes_and_render_replacement(self):
        for local in (False,True):
            self.view.local_only.setChecked(local)
            rows=tuple(replace(row,destination=replace(row.destination,provider='local_elite' if local else 'Spansh'))
                       for row in self.mark_rows())
            self.view.render(rows);self.mark_item(rows[0]).setCheckState(Qt.CheckState.Checked)
            identity=self.view.remembered_identity
            with patch.object(QApplication,'clipboard') as clipboard:
                self.view.copy_system_button.click()
                clipboard.return_value.setText.assert_called_once_with('Synthetic Silver System')
            self.assertEqual(self.view.copy_notice.text(),tr('recommend.system_copied'))
            self.assertEqual(self.view.remembered_identity,identity)
            self.view.render(tuple(reversed(rows)))
            self.assertEqual(self.view.remembered_identity,identity)
            self.view.render((rows[1],))
            self.assertEqual(self.view.remembered_identity,identity)
            self.assertIsNotNone(self.view.remembered_flight)

    def test_remember_highlight_themes_fonts_languages(self):
        from PySide6.QtWidgets import QStyleOptionViewItem,QStyle
        from cmdrhelper.ui.recommendations_view import RecommendationsView
        style=self.app.styleSheet()
        try:
            for lang in ('de','en','el','es','fi','fr','it','nl','no','pl','sv','tr'):
                set_language(lang)
                for theme in (DARK_STYLESHEET,LIGHT_STYLESHEET):
                    for size in (10,18):
                        self.app.setStyleSheet(theme+f'\nQWidget {{ font-size: {size}pt; }}')
                        view=RecommendationsView(self.state,self.provider,self.pool)
                        view.resize(700,900);view.show()
                        long_rows=tuple(replace(row,destination=replace(row.destination,
                            station_name='Long Synthetic Station Name '*4,
                            system_name='Long Synthetic System Name '*4)) for row in self.mark_rows())
                        view.render(long_rows);self.app.processEvents()
                        view.table.item(0,0).setCheckState(Qt.CheckState.Checked)
                        option=QStyleOptionViewItem();option.initFrom(view.table)
                        option.state|=QStyle.StateFlag.State_Selected
                        view.table.itemDelegate().initStyleOption(option,view.table.model().index(0,1))
                        self.assertFalse(option.state & QStyle.StateFlag.State_Selected)
                        self.assertNotEqual(option.backgroundBrush.color(),option.palette.base().color())
                        self.assertEqual(view.copy_system_button.text(),tr('recommend.copy_system'))
                        self.assertEqual(view.table.horizontalHeaderItem(0).toolTip(),tr('recommend.remember'))
                        self.assertLess(view.table.columnWidth(0),50)
                        with patch.object(QApplication,'clipboard'):
                            view.copy_system_button.click()
                        self.assertEqual(view.copy_notice.text(),tr('recommend.system_copied'))
                        view.invalidate()
                        self.assertEqual(view.table.rowCount(),0)
                        self.assertEqual(view.remembered_label.text(),tr('recommend.remembered_flight'))
                        self.assertFalse(view.remembered_panel.isHidden())
                        self.assertIn(str(view.remembered_flight.station_name),view.remembered_details.text())
                        self.assertIn(tr('recommend.total_profit'),view.remembered_profit.text())
                        self.app.processEvents()
                        self.assertEqual(view.remove_remembered_button.text(),tr('recommend.remove_remembered'))
                        self.assertIs(view.copy_system_button.parentWidget(),view.remembered_panel)
                        self.assertLessEqual(view.remembered_panel.width(),view.width())
                        for label in (view.remembered_details,view.remembered_profit):
                            self.assertGreaterEqual(label.height(),label.heightForWidth(label.width()))
                        self.assertLessEqual(view.copy_system_button.width(),view.width())
                        view.close();view.deleteLater();self.app.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        finally:self.app.setStyleSheet(style)

    def test_remembered_flight_survives_purchase_travel_docking_and_market(self):
        silver,gold=self.mark_rows()
        self.state.ship_loadout.cargo_capacity=1110
        self.state.cargo_snapshot['count']=0
        self.view.refresh();self.assertEqual(self.view.free,1110)
        self.view.render((silver,gold));self.mark_item(silver).setCheckState(Qt.CheckState.Checked)
        flight=self.view.remembered_flight
        self.assertEqual((flight.commodity_symbol,flight.commodity_name,flight.station_name,
                          flight.system_name,flight.total_profit),
                         ('Silver','Silber','Silver Port','Synthetic Silver System',silver.total_profit))
        self.state.cargo_snapshot['count']=1110
        self.state.cargoSnapshotChanged.emit(None)
        self.assertEqual(self.view.free,0)
        self.assertEqual(self.view.rows,())
        self.assertFalse(self.view.search_button.isEnabled())
        self.assertEqual(self.view.table.rowCount(),0)
        self.assertIn('Silber',self.view.remembered_details.text())
        self.assertEqual(self.view.remembered_profit.text(),'Möglicher Gewinn: 15.000 Cr')
        self.assertIn('Silver Port',self.view.remembered_details.text())
        self.assertIn('Synthetic Silver System',self.view.remembered_details.text())
        self.assertFalse(self.view.remembered_panel.isHidden())
        self.view.start_search()  # Full cargo: must not discard the flight.
        self.assertIs(self.view.remembered_flight,flight)
        for system,station in (('Fixture System',''),('Transit System',''),
                               ('Synthetic Silver System',''),('Synthetic Silver System','Silver Port')):
            self.state.system=system;self.state.station=station
            self.state.observed_markets.context={}
            self.state.changed.emit()
            self.assertIs(self.view.remembered_flight,flight)
            self.assertEqual(self.view.table.rowCount(),0)
            self.assertEqual(self.view.rows,())
        self.cache.put(market(mid=2,station_name='Silver Port',system_name='Synthetic Silver System'))
        self.state.observed_markets.context=dict(FID=FID,MarketID=2,StationName='Silver Port',StarSystem='Synthetic Silver System')
        self.state.observedMarketsChanged.emit()
        self.assertEqual(self.view.origin['market_id'],2)
        self.assertIs(self.view.remembered_flight,flight)
        with patch.object(QApplication,'clipboard') as clipboard:
            self.view.copy_system_button.click()
            clipboard.return_value.setText.assert_called_once_with('Synthetic Silver System')
        self.assertIs(self.view.remembered_flight,flight)
        self.view.remove_remembered_button.click()
        self.assertIsNone(self.view.remembered_flight)
        self.assertEqual(self.view.table.rowCount(),0)
        self.assertFalse(self.view.copy_system_button.isEnabled())

    def test_detached_flight_new_search_guard_commander_and_no_persistence(self):
        from cmdrhelper.ui.recommendations_view import RecommendationsView
        for local in (False,True):
            self.view.local_only.setChecked(local)
            self.view.render(self.mark_rows());self.view.table.item(0,0).setCheckState(Qt.CheckState.Checked)
            flight=self.view.remembered_flight
            self.view.arrival.setText('invalid')
            self.view.start_search()
            self.assertIs(self.view.remembered_flight,flight)
            self.view.arrival.clear()
            self.view.start_search();self.wait()
            self.assertIsNone(self.view.remembered_flight)
        self.view.render(self.mark_rows());self.view.table.item(0,0).setCheckState(Qt.CheckState.Checked)
        self.view.invalidate()
        self.state.commander_fid=''
        self.state.changed.emit()
        self.assertIsNotNone(self.view.remembered_flight)  # Unknown is not a confirmed other commander.
        other=RecommendationsView(self.state,self.provider,self.pool)
        self.assertIsNone(other.remembered_flight)
        other.close();other.deleteLater()
        self.state.commander_fid='F_DIFFERENT'
        self.state.commanderIdentityChanged.emit(None,'','')
        self.assertIsNone(self.view.remembered_flight)
        self.assertEqual(self.view.table.rowCount(),0)
        self.assertFalse(self.view.copy_system_button.isEnabled())

    def test_remembered_flight_repeated_purchase_invalidations_and_queued_signals(self):
        from PySide6.QtCore import QTimer
        silver,gold=self.mark_rows()
        self.state.ship_loadout.cargo_capacity=1110
        self.state.cargo_snapshot['count']=0
        self.view.refresh()
        self.view.render((silver,gold))
        self.mark_item(silver).setCheckState(Qt.CheckState.Checked)
        flight=self.view.remembered_flight
        self.state.cargo_snapshot['count']=1110
        steps=(lambda:self.state.cargoSnapshotChanged.emit(self.state.cargo_snapshot),
               self.state.changed.emit, self.view.invalidate, self.view.invalidate,
               self.state.observedMarketsChanged.emit, self.view.refresh)
        for queued in (False,True):
            for step in steps:
                if queued:
                    QTimer.singleShot(0,step)
                    self.app.processEvents()
                else:step()
                self.app.processEvents()
                self.assertIs(self.view.remembered_flight,flight)
                self.assertEqual(self.view.rows,())
                self.assertEqual(self.view.table.rowCount(),0)
                self.assertIn('Silber',self.view.remembered_details.text())
                self.assertEqual(self.view.remembered_profit.text(),'Möglicher Gewinn: 15.000 Cr')
                self.assertIn(flight.station_name,self.view.remembered_details.text())
                self.assertIn(flight.system_name,self.view.remembered_details.text())
                self.assertTrue(self.view.copy_system_button.isEnabled())
                self.assertFalse(self.view.remembered_panel.isHidden())
        with patch.object(QApplication,'clipboard') as clipboard:
            self.view.copy_system_button.click()
            clipboard.return_value.setText.assert_called_once_with(flight.system_name)
        self.view.remove_remembered_button.click()
        self.assertEqual(self.view.table.rowCount(),0)
        self.assertIsNone(self.view.remembered_flight)
        self.assertFalse(self.view.copy_system_button.isEnabled())

    def test_remembered_flight_real_state_cargo_application_and_followup_refreshes(self):
        from cmdrhelper.state import AppState
        silver,gold=self.mark_rows()
        self.view.render((silver,gold))
        self.mark_item(silver).setCheckState(Qt.CheckState.Checked)
        flight=self.view.remembered_flight
        self.state.journal_folder=Path(self.tmp.name)
        full=dict(self.state.cargo_snapshot,count=300,timestamp='2026-09-01T12:01:00Z')
        trigger=dict(Vessel='Ship',Count=300,timestamp=full['timestamp'])
        session=dict(attribution_status='identified',commander_id=1,fid_seen=FID)
        with patch('cmdrhelper.state.read_cargo_snapshot',return_value=full):
            AppState._apply_live_cargo_snapshot(self.state,dict(last_cargo_event=trigger),session)
        self.state.changed.emit()
        self.state.shipLoadoutChanged.emit(self.state.ship_loadout)
        self.state.observedMarketsChanged.emit()
        self.app.processEvents()
        self.assertEqual(self.view.free,0)
        self.assertEqual(self.view.rows,())
        self.assertIs(self.view.remembered_flight,flight)
        self.assertEqual(self.view.table.rowCount(),0)
        self.assertIn('Silber',self.view.remembered_details.text())
        self.assertTrue(self.view.copy_system_button.isEnabled())

    def test_separate_flight_panel_selection_replacement_remove_and_frozen_profit(self):
        for local in (False,True):
            self.view.remove_remembered()
            self.view.local_only.setChecked(local)
            self.assertTrue(self.view.remembered_panel.isHidden())
            silver,gold=(replace(row,destination=replace(row.destination,
                        provider='local_elite' if local else 'spansh')) for row in self.mark_rows())
            self.view.render((silver,gold))
            self.mark_item(silver).setCheckState(Qt.CheckState.Checked)
            self.assertFalse(self.view.remembered_panel.isHidden())
            self.assertEqual(self.view.remembered_details.text(),
                             'Silber · Silver Port · Synthetic Silver System')
            self.assertEqual(self.view.remembered_profit.text(),'Möglicher Gewinn: 15.000 Cr')
            self.mark_item(gold).setCheckState(Qt.CheckState.Checked)
            self.assertEqual(self.mark_item(silver).checkState(),Qt.CheckState.Unchecked)
            self.assertEqual(self.view.remembered_details.text(),
                             'Gold · Gold Port · Synthetic Gold System')
            profit=self.view.remembered_profit.text()
            self.view.render((silver,replace(gold,buy_price=9000)))
            self.assertEqual(self.view.remembered_profit.text(),profit)
            self.view.remove_remembered_button.click()
            self.assertTrue(self.view.remembered_panel.isHidden())
            self.assertEqual(self.view.table.rowCount(),2)
            self.assertFalse(self.view.copy_system_button.isEnabled())
            for i in range(2):
                self.assertEqual(self.view.table.item(i,0).checkState(),Qt.CheckState.Unchecked)
                self.assertFalse(self.view.table.item(i,1).data(Qt.ItemDataRole.UserRole+1))
            self.mark_item(silver).setCheckState(Qt.CheckState.Checked)
            self.mark_item(silver).setCheckState(Qt.CheckState.Unchecked)
            self.assertTrue(self.view.remembered_panel.isHidden())

    def test_switch_mixed_to_local_only_clears_results_keeps_flight_and_skips_provider(self):
        self.cache.put(market(mid=3,rows=[item(sell=11000)]))
        self.search()
        self.assertTrue(any(r.destination.provider=='spansh' for r in self.view.rows))
        self.view.table.item(0,0).setCheckState(Qt.CheckState.Checked)
        flight=self.view.remembered_flight
        self.view.local_only.setChecked(True)
        self.assertEqual(self.view.table.rowCount(),0)
        self.assertEqual(self.view.rows,())
        self.assertIs(self.view.remembered_flight,flight)
        self.assertFalse(self.view.remembered_panel.isHidden())
        self.assertIsNone(self.view.worker)
        with patch.object(self.provider,'search_sell',side_effect=AssertionError('No community')) as provider:
            self.view.start_search()
            self.assertIsNone(self.view.remembered_flight)
            self.assertTrue(self.view.worker.local_only)
            self.wait()
            provider.assert_not_called()
        self.assertTrue(self.view.rows)
        self.assertTrue(all(r.destination.provider=='local_elite' for r in self.view.rows))
        d=self.view.last_run
        self.assertTrue(d.local_only)
        self.assertEqual((d.spansh_commodities_started,d.spansh_commodities_completed,
                          d.spansh_commodities_failed,d.http_requests,d.cache_hits),(0,0,0,0,0))
        self.assertFalse(d.partial)
        self.assertEqual(d.partial_reason,PartialReason.NONE)
        with patch.object(QApplication,'clipboard') as clipboard:
            self.view.copy_diagnostic_button.click()
            text=clipboard.return_value.setText.call_args.args[0]
            for value in ('local_only=true','http_requests=0','cache_hits=0','partial=false','partial_reason=NONE'):
                self.assertIn(value,text)
        self.view.local_only.setChecked(False)
        self.assertEqual(self.view.table.rowCount(),0)
        self.search()
        self.assertTrue(any(r.destination.provider=='spansh' for r in self.view.rows))

    def test_local_only_worker_rejects_foreign_sources_before_ui_delivery(self):
        from cmdrhelper.ui.recommendations_view import RecommendationWorker
        from cmdrhelper.market_data import MarketSearch
        for intermediate in (False,True):
            worker=RecommendationWorker(market(),[],{},280,10,MarketSearch('', 'Fixture System'),
                                        self.provider,lambda:NOW,local_only=True)
            bad=RecommendationResult(rows=(Recommendation(offer(),10000,10),))
            results=[];updates=[]
            worker.signals.finished.connect(results.append)
            worker.signals.progress.connect(updates.append)
            def corrupted_backend(*args,**kwargs):
                if intermediate:kwargs['progress'](bad)
                return bad
            with patch('cmdrhelper.ui.recommendations_view.search_recommendations',side_effect=corrupted_backend):
                worker.run()
            self.assertEqual(updates,[])
            self.assertEqual(len(results),1)
            self.assertEqual(results[0].rows,())
            self.assertTrue(results[0].partial)
            self.assertEqual(results[0].diagnostics.partial_reason,PartialReason.OTHER)
