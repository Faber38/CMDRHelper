"""Only temporary synthetic stores; never read a player's journals or settings."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
from threading import Event, get_ident
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PySide6.QtCore import QObject, Signal, QThreadPool, QEvent, Qt, QLocale
from PySide6.QtWidgets import QApplication
from cmdrhelper import saved_markets as reader
from cmdrhelper.commodity_master import lookup_by_symbol
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.market_data import PadSize
from cmdrhelper.market_store import MarketStore, MarketPage, StaleReadError
from cmdrhelper.station_pad_store import create_schema
from cmdrhelper.ui import saved_markets_view as ui
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET

NOW = datetime(2026, 10, 26, 12, tzinfo=timezone.utc)
MATE = 4224637699


def observation(mid, *, count=1, age=48, fid='F_SYNTHETIC_A', name=None, kind='Coriolis'):
    return dict(fid=fid, market_id=mid, station_name=name or f'Port {mid}',
        system_name=f'System {mid % 3}', system_address=100 + mid % 3,
        station_type=kind, observed_at=(NOW - timedelta(hours=age)).isoformat(), source='local_elite',
        commodities=[dict(commodity_id=900000000+i, symbol=f'fixture_{i}', localized_name=f'Ware {i:03}',
            commander_buy_price=i * 1001, commander_sell_price=i * 29, supply=i * 20, demand=i * 5)
            for i in range(count)])


class Fixture:
    def make_fixture(self, count=4):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.market = self.root / 'market_cache' / 'markets.db'
        self.database = self.root / 'main.db'
        self.folder = self.root / 'external' / 'spansh'
        self.folder.mkdir(parents=True)
        with MarketStore(self.market, clock=lambda: NOW) as store:
            for mid in range(1, count):
                store.record_observation(observation(mid, age=1 if mid == 1 else 48,
                    fid='F_SYNTHETIC_B' if mid == 2 else 'F_SYNTHETIC_A',
                    kind='SurfaceStation' if mid == 2 else 'FleetCarrier' if mid == 3 else 'Coriolis'))
            store.record_observation(observation(MATE, count=369, name='Mate City', kind='Outpost'))
        with sqlite3.connect(self.database) as con:
            con.execute('CREATE TABLE systems (system_address INTEGER PRIMARY KEY, name TEXT, x REAL,y REAL,z REAL)')
            con.executemany('INSERT INTO systems VALUES(?,?,?,?,?)',
                [(100, 'System 0', 0,0,0), (101, 'System 1', 3,4,0), (102, 'System 2', 6,8,0),
                 (999, 'No coords', None,None,None)])
            create_schema(con)
            con.execute('PRAGMA user_version=23')
            for mid, sizes in ((1,(1,0,0)),(2,(1,1,0)),(3,(1,1,1)),(MATE,(3,1,0))):
                row = observation(mid)
                con.execute('INSERT INTO station_pad_evidence VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                    (mid, mid.to_bytes(8,'big'), row['system_address'].to_bytes(8,'big'),row['system_name'],
                     'Mate City' if mid == MATE else row['station_name'],row['station_type'],*sizes,
                     'local_elite','Docked',NOW.isoformat(),0))
        self.source = reader.SavedMarketSource(self.market, self.database, self.folder)


class ReaderTests(Fixture, unittest.TestCase):
    def setUp(self):
        self.make_fixture(110)

    def test_110_headers_no_payloads_and_mate_369_independent_of_commander(self):
        before = [hashlib.sha256(p.read_bytes()).digest() for p in (self.market, self.database)]
        with patch.object(MarketStore, '_payload', side_effect=AssertionError('headers only')), \
             patch('cmdrhelper.station_pad_store.read_local', side_effect=AssertionError('No journal synchronization')):
            rows, incomplete = reader.read_markets(self.source, clock=lambda: NOW)
        self.assertEqual(len(rows), 110)
        self.assertFalse(incomplete)
        self.assertEqual({r['header'].fid for r in rows}, {'F_SYNTHETIC_A','F_SYNTHETIC_B'})
        self.assertEqual({r['pad'] for r in rows}, {None, PadSize.SMALL, PadSize.MEDIUM, PadSize.LARGE})
        mate = reader.read_market(self.source, MATE, clock=lambda: NOW)
        self.assertEqual(mate['station_name'], 'Mate City')
        self.assertEqual(len(mate['commodities']), 369)
        self.assertEqual(mate['commodities'][0]['demand'], 0)
        self.assertEqual(before, [hashlib.sha256(p.read_bytes()).digest() for p in (self.market,self.database)])
        stronghold = reader.read_market(self.source, 2, clock=lambda: NOW)
        self.assertEqual(stronghold['station_type'], 'SurfaceStation')

    def test_pagination_revision_retry_no_duplicates(self):
        # Exercise real pagination above MAX_PAGE and one concurrent-change retry.
        with MarketStore(self.market, clock=lambda: NOW) as store:
            for mid in range(110, 506):
                store.record_observation(observation(mid))
        original = MarketStore.query_current_candidates
        calls, failed = [], [False]
        def query(store, **kwargs):
            calls.append(kwargs)
            if kwargs['cursor'] is not None and not failed[0]:
                failed[0] = True
                raise StaleReadError('synthetic concurrent commit')
            return original(store, **kwargs)
        with patch.object(MarketStore, 'query_current_candidates', query):
            rows, _ = reader.read_markets(self.source, clock=lambda: NOW)
        self.assertEqual(len(rows), 506)
        self.assertEqual(len({r['header'].market_id for r in rows}), 506)
        self.assertTrue(any(c['expected_revision'] is not None for c in calls))
        with patch.object(MarketStore, 'query_current_candidates', side_effect=StaleReadError('busy')) as query:
            with self.assertRaises(StaleReadError): reader.read_markets(self.source)
            self.assertEqual(query.call_count, 3)

    def test_missing_empty_and_cancelled(self):
        self.assertEqual(reader.read_markets(replace(self.source,market_path=self.root/'absent.db')), ([],False))
        self.assertIsNone(reader.read_market(self.source,999999,clock=lambda:NOW))
        with MarketStore(self.root/'empty.db'): pass
        self.assertEqual(reader.read_markets(reader.SavedMarketSource(self.root/'empty.db'))[0], [])
        cancel=Event();cancel.set()
        with self.assertRaises(reader.ReadCancelled): reader.read_markets(self.source,cancel)

    def test_empty_commodity_snapshot_and_no_lazy_cache_or_network(self):
        with MarketStore(self.market, clock=lambda:NOW) as store:
            store.record_observation(observation(700, count=0))
        with patch('urllib.request.urlopen',side_effect=AssertionError('No network')):
            self.assertEqual(reader.read_market(self.source,700,clock=lambda:NOW)['commodities'],[])
            self.assertEqual(len(reader.read_markets(self.source,clock=lambda:NOW)[0]),111)
        class UninitializedObserver:
            writer = None
            _cache = None
            @property
            def cache(self):
                raise AssertionError('Do not create a writable cache')
        source=reader.source_from_state(SimpleNamespace(observed_markets=UninitializedObserver()))
        self.assertIsNone(source.market_path)

    def test_coordinates_missing_ambiguous_and_reference(self):
        self.assertEqual(reader.read_reference(self.source,'System 1').distance_to(
                         reader.read_reference(self.source,'System 0')), 5)
        self.assertIsNone(reader.read_reference(self.source,'No coords'))
        self.assertIsNone(reader.read_reference(self.source,'Not stored'))
        with sqlite3.connect(self.database) as con:
            con.execute('INSERT INTO systems VALUES(500,"System 1",1,2,3)')
            con.execute('UPDATE systems SET x=NULL WHERE system_address=102')
        self.assertIsNone(reader.read_reference(self.source,'System 1'))
        rows,_=reader.read_markets(self.source,clock=lambda:NOW)
        self.assertIsNone(next(r for r in rows if r['header'].market_id==2)['coordinates'])

    def test_unreadable_optional_metadata_does_not_hide_markets(self):
        broken=self.root/'broken.db';broken.write_text('not a database')
        rows,incomplete=reader.read_markets(replace(self.source,database_path=broken),clock=lambda:NOW)
        self.assertEqual(len(rows),110)
        self.assertTrue(incomplete)
        self.assertTrue(all(r['coordinates'] is None and r['pad'] is None for r in rows))

    def test_pad_identity_conflict_and_external_fallback(self):
        with sqlite3.connect(self.database) as con:
            con.execute('UPDATE station_pad_evidence SET station_name="Other" WHERE market_id=?',((2).to_bytes(8,'big'),))
        external=dict(schema_version=1,source='spansh',system_name='System 1',system_address=101,
            fetched_at=NOW.isoformat(),stations=[dict(market_id=4,station_name='Port 4',
                landing_pads=dict(small=1,medium=0,large=1))])
        (self.folder/'101.json').write_text(json.dumps(external))
        rows,_=reader.read_markets(self.source,clock=lambda:NOW)
        by_id={r['header'].market_id:r for r in rows}
        self.assertIsNone(by_id[2]['pad'])
        self.assertEqual(by_id[4]['pad'],PadSize.LARGE)
        # Conflicting equal-time local evidence must remain unknown.
        with sqlite3.connect(self.database) as con:
            con.execute('INSERT INTO station_pad_evidence SELECT 999,market_id,system_address,system_name,station_name,station_type,1,1,1,source,event_type,observed_at,event_offset FROM station_pad_evidence WHERE market_id=?',((1).to_bytes(8,'big'),))
        rows,_=reader.read_markets(self.source,clock=lambda:NOW)
        self.assertIsNone(next(r for r in rows if r['header'].market_id==1)['pad'])


class State(QObject):
    observedMarketsChanged = Signal()
    commanderIdentityChanged = Signal(object,str,str)
    changed = Signal()
    system = 'System 0'
    station = ''
    commander_fid = 'F_OTHER'


class ViewTests(Fixture, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.make_fixture()
        language=get_language();self.addCleanup(set_language,language)
        set_language('de')
        self.state=State()
        self.state.database=SimpleNamespace(path=self.database)
        self.state.observed_markets=SimpleNamespace(_cache=SimpleNamespace(path=self.market.parent/'legacy.json'),writer=None,context={})
        self.pool=QThreadPool();self.pool.setMaxThreadCount(3)
        self.view=ui.SavedMarketsView(self.state,pool=self.pool,clock=lambda:NOW)
        self.addCleanup(self.cleanup)
        self.view.resize(1400,900)
        self.view.show()
        self.wait()

    def cleanup(self):
        self.view.cancel_reads()
        self.pool.waitForDone(5000)
        self.app.processEvents()
        self.view.close();self.view.deleteLater()
        self.app.sendPostedEvents(None,QEvent.DeferredDelete)

    def wait(self):
        until=time.monotonic()+5
        while self.view._jobs and time.monotonic()<until:
            self.app.processEvents();time.sleep(.002)
        self.app.processEvents()
        self.assertFalse(self.view._jobs,'worker did not finish')

    def select(self, mid):
        for index,row in enumerate(self.view.markets_model.rows):
            if row['header'].market_id==mid:
                proxy=self.view.markets_proxy.mapFromSource(self.view.markets_model.index(index,0))
                self.assertTrue(proxy.isValid())
                self.view.markets_table.setCurrentIndex(proxy)
                self.wait();return
        self.fail('missing MarketID')

    def test_lazy_selection_market_change_commander_and_no_docking(self):
        self.assertEqual(self.view.goods_model.rowCount(),0)
        self.assertEqual(self.view.markets_proxy.rowCount(),4)
        self.select(MATE)
        self.assertEqual(self.view.goods_model.rowCount(),369)
        self.assertIn('Mate City',self.view.detail_header.text())
        self.assertIn('local_elite',self.view.detail_header.text())
        self.assertIn('älter als 24 h',self.view.detail_header.text())
        with patch.object(MarketStore,'get_current',side_effect=AssertionError('No reread')):
            self.state.commander_fid='F_NEW';self.state.system='On a planet'
            self.state.commanderIdentityChanged.emit(3,'F_NEW','Other');self.state.changed.emit()
            self.app.processEvents()
        self.assertEqual(self.view._selected_id,MATE)
        self.assertEqual(self.state.observed_markets.context,{})
        self.select(2)
        self.assertIn('SurfaceStation',self.view.detail_header.text())
        self.assertEqual(self.view.goods_model.rowCount(),1)

    def test_search_station_system_marketid_and_filters_without_io(self):
        with patch.object(MarketStore,'__init__',side_effect=AssertionError('Filters are in memory')):
            for query,count in [('mate',1),('System 1',2),(str(MATE),1),('none',0),('',4)]:
                self.view.search.setText(query);self.assertEqual(self.view.markets_proxy.rowCount(),count)
            self.view.age.setCurrentIndex(self.view.age.findData(24))
            self.assertEqual(self.view.markets_proxy.rowCount(),1)
            self.view.age.setCurrentIndex(0)
            self.view.radius.setValue(5)
            self.assertEqual(self.view.markets_proxy.rowCount(),3)
            self.view.radius.setValue(0)
            for pad,count in [('S',1),('M',2),('L',1),('?',0),('',4)]:
                self.view.pad.setCurrentIndex(self.view.pad.findData(pad))
                self.assertEqual(self.view.markets_proxy.rowCount(),count)
            self.view.markets_table.sortByColumn(1,Qt.DescendingOrder)
            names=[self.view.markets_proxy.index(i,1).data() for i in range(4)]
            self.assertEqual(names,sorted(names,key=str.casefold,reverse=True))
            self.view.clock=lambda:NOW+timedelta(days=2)
            self.view.age.setCurrentIndex(self.view.age.findData(24))
            self.assertEqual(self.view.markets_proxy.rowCount(),0)

    def test_reference_change_missing_coordinates_preserves_selection(self):
        self.select(MATE)
        with patch.object(MarketStore,'__init__',side_effect=AssertionError('Reference must not reread markets')):
            self.view.reference.setText('System 2');self.view.change_reference();self.wait()
            self.assertEqual(next(r for r in self.view.markets_model.rows if r['header'].market_id==2)['distance'],0)
            self.view.reference.setText('No coords');self.view.change_reference();self.wait()
            self.assertTrue(all(r['display'][3]=='—' for r in self.view.markets_model.rows))
            self.view.radius.setValue(1);self.assertEqual(self.view.markets_proxy.rowCount(),0)
            self.view.radius.setValue(0)
            self.state.system='System 0';self.view.hide();self.view.show();self.wait()
            self.assertEqual(self.view.reference.text(),'No coords')
            self.assertEqual(self.view._selected_id,MATE)

    def test_numeric_sort_zero_unknown_stable_names_and_mining(self):
        self.select(MATE)
        rows=[]
        for symbol,buy,demand,name in [('Platinum',1000,0,'same'),('Gold',9,None,'same'),('Beer',20,2000,'zeta')]:
            master=lookup_by_symbol(symbol)
            rows.append(dict(commodity_id=master.frontier_id,symbol=master.symbol,
                commander_buy_price=buy,commander_sell_price=buy,supply=demand,demand=demand))
        self.view._snapshot['commodities']=rows
        self.view._render_goods()
        for col in (1,2,3,4):
            for order in (Qt.AscendingOrder,Qt.DescendingOrder):
                self.view.goods_table.sortByColumn(col,order)
                values=[self.view.goods_proxy.index(i,col).data(Qt.UserRole) for i in range(3)]
                known=[v for v in values if v is not None]
                self.assertEqual(known,sorted(known,reverse=order==Qt.DescendingOrder))
        values=[row['display'][4] for row in self.view.goods_model.rows]
        self.assertIn('0',values);self.assertIn('—',values)
        self.view.mining_only.setChecked(True)
        self.assertEqual(self.view.goods_proxy.rowCount(),2)
        self.view.goods_search.setText('Platin')
        self.assertEqual(self.view.goods_proxy.rowCount(),1)
        self.view.mining_only.setChecked(False);self.view.goods_search.clear()
        # Equal keys retain source order in both directions (Qt stable sort).
        repeated=[dict(values=('same',i,0,0,0),display=('same',str(i),'0','0','0'),search='same',mining=False) for i in range(3)]
        self.view.goods_model.replace(repeated)
        for order in (Qt.AscendingOrder,Qt.DescendingOrder):
            self.view.goods_table.sortByColumn(0,order)
            self.assertEqual([self.view.goods_proxy.index(i,1).data(Qt.UserRole) for i in range(3)],[0,1,2])
        self.assertEqual(ui.quantity_text(2**64-1,QLocale('de')),'18.446.744.073.709.551.615')

    def test_fast_switch_discards_late_worker_and_worker_is_off_gui(self):
        gate,entered=Event(),Event();self.addCleanup(gate.set)
        original=ui.read_market;threads=[]
        def delayed(source,mid,cancel=None,**kw):
            threads.append(get_ident())
            if mid==MATE:
                entered.set();gate.wait(2)
            return original(source,mid,cancel,**kw)
        with patch.object(ui,'read_market',delayed):
            self.view._load_detail(MATE)
            self.assertTrue(entered.wait(1))
            self.view._load_detail(2)
            gate.set();self.wait()
        self.assertTrue(all(t!=get_ident() for t in threads))
        self.assertEqual(self.view._selected_id,2)
        self.assertEqual(self.view._snapshot['market_id'],2)

    def test_refresh_replaces_selected_market_and_missing_details(self):
        self.select(MATE)
        with MarketStore(self.market,clock=lambda:NOW) as store:
            store.record_observation(observation(MATE,count=2,name='Mate City',age=0))
        self.state.observedMarketsChanged.emit();self.wait()
        self.assertEqual(self.view.goods_model.rowCount(),2)
        self.view._load_detail(99999);self.wait()
        self.assertEqual(self.view.detail_header.text(),tr('browse.missing'))
        self.assertEqual(self.view.goods_model.rowCount(),0)

    def test_empty_and_error_states_do_not_keep_old_market(self):
        self.select(MATE)
        with patch.object(ui,'read_markets',return_value=([],False)):
            self.view.reload();self.wait()
        self.assertEqual(self.view.status.text(),tr('browse.empty'))
        self.assertIsNone(self.view._selected_id)
        self.assertEqual(self.view.goods_model.rowCount(),0)
        with patch.object(ui,'read_markets',side_effect=OSError('synthetic unreadable database')):
            with self.assertLogs('cmdrhelper.ui.saved_markets_view',level='ERROR'):
                self.view.reload();self.wait()
        self.view.reference.setText('System 1');self.view.change_reference();self.wait()
        self.assertEqual(self.view.status.text(),tr('browse.error'))

    def test_carrier_moved_after_headers_does_not_inherit_old_distance_or_pad(self):
        self.select(3)
        self.view._snapshot.update(system_name='New system',system_address=900)
        self.view._render_detail()
        self.assertIn('Landeplatz: —',self.view.detail_header.text())
        self.assertIn('Entfernung (Lj): —',self.view.detail_header.text())

    def test_twelve_languages_themes_and_responsive_layout(self):
        style=self.app.styleSheet();self.addCleanup(self.app.setStyleSheet,style)
        keys={k for k in _TRANSLATIONS['en'] if k.startswith('browse.')}
        for lang,translations in _TRANSLATIONS.items():
            self.assertTrue(keys <= translations.keys())
            set_language(lang)
            for theme in (DARK_STYLESHEET,LIGHT_STYLESHEET):
                self.app.setStyleSheet(theme)
                view=ui.SavedMarketsView(self.state,clock=lambda:NOW)
                # No production access: injected state contains only temp paths.
                for width in (480,1400):
                    view.resize(width,650);view.show();self.app.processEvents()
                    self.assertEqual(view.width(),width)
                    self.assertEqual(view.height(),650)
                    self.assertEqual(view.splitter.orientation(),Qt.Horizontal if width>=1050 else Qt.Vertical)
                    a,b=view.splitter.widget(0),view.splitter.widget(1)
                    self.assertFalse(a.geometry().intersects(b.geometry()))
                    self.assertNotIn('browse.',view.notice.text())
                    self.assertEqual(view.markets_table.palette().alternateBase().color().lightness()<128,
                                     theme==DARK_STYLESHEET)
                view.cancel_reads();view.pool.waitForDone(5000);self.app.processEvents()
                view.close();view.deleteLater();self.app.sendPostedEvents(None,QEvent.DeferredDelete)

    def test_fifth_trade_tab_preserves_existing_form_and_tabs(self):
        from cmdrhelper.ui.trade_view import TradeView
        from cmdrhelper.observed_market_cache import ObservedMarketCache
        cache = ObservedMarketCache(self.market.parent/'legacy.json', clock=lambda:NOW)
        self.state.observed_markets.cache = cache
        self.state.observed_markets._cache = cache
        trade=TradeView(self.state,pool=self.pool)
        try:
            self.assertEqual(trade.tabs.count(),5)
            self.assertEqual(trade.tabs.tabText(4),'Markt ansehen')
            old_parent=trade._scroll.parent()
            trade.tabs.setCurrentIndex(4)
            self.assertIs(trade._scroll.parent(),old_parent)
            self.assertIs(trade.tabs.widget(3),trade.supply_recommendations)
            trade.tabs.setCurrentIndex(1)
            self.assertIs(trade._scroll.parent(),trade.tabs.widget(1))
        finally:
            trade.saved_markets.cancel_reads();self.pool.waitForDone(5000)
            trade.close();trade.deleteLater();self.app.sendPostedEvents(None,QEvent.DeferredDelete)
