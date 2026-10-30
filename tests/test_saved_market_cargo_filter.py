"""Saved market filtering uses verified ship cargo, never historical totals."""
from types import SimpleNamespace
import unittest
from unittest.mock import patch, Mock

from PySide6.QtCore import Signal, Qt, QSettings
from PySide6.QtTest import QTest
from cmdrhelper.cargo import cargo_snapshot
from cmdrhelper.ship_cargo import ShipCargoTracker
from cmdrhelper.i18n import _TRANSLATIONS, tr, set_language
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.ui.trade_view import TradeView
import test_saved_markets as saved
from test_saved_markets import State, Fixture, MATE, ui, MarketStore
from test_trade_view import State as TradeState
from cmdrhelper.commodity_master import lookup_by_symbol


class CargoState(State):
    cargoSnapshotChanged = Signal(object)
    viewedCommanderChanged = Signal(object)
    shipLoadoutChanged = Signal(object)


class CargoFilterTests(Fixture, unittest.TestCase):
    setUpClass = saved.ViewTests.__dict__['setUpClass']
    cleanup = saved.ViewTests.cleanup
    wait = saved.ViewTests.wait
    select = saved.ViewTests.select

    def setUp(self):
        with patch('test_saved_markets.State', CargoState):
            saved.ViewTests.setUp(self)
        self.select(MATE)
        self.view._snapshot['commodities'] = [dict(
            commodity_id=lookup_by_symbol(name).frontier_id, symbol=name,
            commander_buy_price=10, commander_sell_price=9, supply=20, demand=30)
            for name in ('Gold', 'Beer', 'Platinum')]
        self.view._render_goods()
        self.state.commander_id = self.state.viewed_commander_id = 1
        self.state.commander_fid = 'TEST-CARGO'
        self.state._journal_index_sessions = [dict(journal_file='synthetic-journal',
            commander_id=1, fid_seen='TEST-CARGO', attribution_status='identified')]
        self.state.ship_loadout = SimpleNamespace(ship_id=7, ship_type='cobra',
            loadout_complete=True, loadout_stale=False, cargo_capacity=100,
            loadout_timestamp='2026-01-01T00:00:02Z')
        self.tracker = ShipCargoTracker()
        self.seq = 0
        self.feed('LoadGame', Ship='cobra', ShipID=7)
        self.feed('Loadout', Ship='cobra', ShipID=7)
        self.state._cargo_status = None
        self.cargo(Gold=2, Beer=1)
        self.view.cargo_only.setChecked(True)

    def feed(self, kind, **fields):
        self.seq += 1
        e = dict(event=kind, timestamp=f'2026-01-01T00:00:{self.seq:02d}Z', **fields)
        self.tracker.apply(e, self.state.commander_fid, 'synthetic-journal')
        self.state.ship_cargo_context = self.tracker.context
        return e

    def cargo(self, vessel='Ship', **goods):
        e = self.feed('Cargo', Vessel=vessel, Count=sum(goods.values()),
                      Inventory=[dict(Name=n, Count=q) for n,q in goods.items()])
        self.state.cargo_snapshot = cargo_snapshot(e, fid=self.state.commander_fid,
            ship_id=7 if vessel=='Ship' else None, cargo_capacity=100)
        self.state.cargo_snapshot['context'] = dict(self.tracker.last_cargo_context)
        self.state.cargoSnapshotChanged.emit(self.state.cargo_snapshot)

    def test_confirmed_intersection_and_no_io_or_selection_change(self):
        v=self.view
        self.assertEqual(v.goods_proxy.rowCount(),2)
        with patch.object(MarketStore,'get_current',side_effect=AssertionError('no DB read')), \
             patch.object(ui,'read_markets',side_effect=AssertionError('no reload')):
            v.mining_only.setChecked(True)
            self.assertEqual(v.goods_proxy.rowCount(),1)
            v.goods_search.setText('Bier')
            self.assertEqual(v.goods_proxy.rowCount(),0)
            v.mining_only.setChecked(False)
            self.assertEqual(v.goods_proxy.rowCount(),1)
            v.goods_search.clear()
            self.cargo(Gold=1)
            self.assertEqual(v.goods_proxy.rowCount(),1)
        self.assertEqual(v._selected_id,MATE)
        self.assertFalse(v.cargo_notice.isVisible())

    def test_confirmed_empty_is_not_unknown(self):
        self.cargo()
        self.assertEqual(self.view.goods_proxy.rowCount(),0)
        self.assertEqual(self.view.cargo_notice.text(),tr('browse.cargo_empty'))
        self.state.cargo_snapshot=None
        self.state.cargoSnapshotChanged.emit(None)
        self.assertGreater(self.view.goods_proxy.rowCount(),0)
        self.assertEqual(self.view.cargo_notice.text(),tr('browse.cargo_unavailable'))
        self.assertTrue(self.view.cargo_only.isChecked())

    def test_mutations_pause_until_confirmed_and_keep_mining_filter(self):
        self.view.mining_only.setChecked(True)
        for kind in ('CargoTransfer','CollectCargo','MiningRefined'):
            with self.subTest(kind=kind):
                self.feed(kind)
                self.state.changed.emit()
                self.assertIsNone(self.view.goods_proxy.cargo_ids)
                self.assertTrue(self.view.goods_proxy.mining)
                self.assertTrue(self.view.cargo_notice.isVisible())
                self.cargo(Beer=1)
                self.assertEqual(self.view.goods_proxy.rowCount(),0)
                self.assertFalse(self.view.cargo_notice.isVisible())

    def test_context_switches_pause_and_recover(self):
        changes=[('commander_fid','OTHER'),('commander_id',2),('viewed_commander_id',2),
                 ('_cargo_blocked',True)]
        for field,value in changes:
            with self.subTest(field=field):
                old=getattr(self.state,field,None)
                setattr(self.state,field,value);self.state.changed.emit()
                self.assertIsNone(self.view.goods_proxy.cargo_ids)
                setattr(self.state,field,old);self.state.changed.emit()
                self.assertEqual(self.view.goods_proxy.rowCount(),2)
        self.state.sources=object();self.state._source_live_context=False
        self.state.changed.emit();self.assertIsNone(self.view.goods_proxy.cargo_ids)
        self.state._source_live_context=True
        self.state.changed.emit();self.assertEqual(self.view.goods_proxy.rowCount(),2)
        self.state._journal_index_sessions[0]['journal_file']='different-source'
        self.state.changed.emit();self.assertIsNone(self.view.goods_proxy.cargo_ids)
        self.state._journal_index_sessions[0]['journal_file']='synthetic-journal'
        self.state.ship_loadout.ship_id=8
        self.state.shipLoadoutChanged.emit(self.state.ship_loadout)
        self.assertIsNone(self.view.goods_proxy.cargo_ids)
        self.state.ship_loadout.ship_id=7
        self.state.ship_loadout.loadout_stale=True
        self.state.shipLoadoutChanged.emit(self.state.ship_loadout)
        self.assertIsNone(self.view.goods_proxy.cargo_ids)
        self.state.ship_loadout.loadout_stale=False
        self.state.shipLoadoutChanged.emit(self.state.ship_loadout)
        self.assertEqual(self.view.goods_proxy.rowCount(),2)

    def test_srv_carrier_and_old_cached_inventory_are_not_used(self):
        self.state.ship_inventory=self.state.cargo_snapshot
        self.state.carrier_snapshot={'inventory':[{'frontier_name':'Gold','count':20}]}
        self.cargo(vessel='SRV',Gold=2)
        self.assertIsNone(self.view.goods_proxy.cargo_ids)
        self.assertTrue(self.view.cargo_notice.isVisible())
        self.cargo(Beer=1)
        self.assertEqual(self.view.goods_proxy.rowCount(),1)
        self.view.mining_only.setChecked(True)
        self.assertEqual(self.view.goods_proxy.rowCount(),0)

    def test_conflicting_status_stays_unknown_after_status_disappears(self):
        with patch('cmdrhelper.ship_cargo.status_ship_count',return_value=99):
            self.state.changed.emit()
        self.assertIsNone(self.view.goods_proxy.cargo_ids)
        self.state.changed.emit()
        self.assertIsNone(self.view.goods_proxy.cargo_ids)
        self.cargo(Gold=1)
        self.assertEqual(self.view.goods_proxy.rowCount(),1)

    def test_names_tokens_unknown_and_no_display_name_guessing(self):
        self.cargo(**{'$gOlD_name;':1,'BEER':1})
        self.assertEqual(self.view.goods_proxy.rowCount(),2)
        self.cargo(UncataloguedCommodity=1)
        self.state.cargo_snapshot['inventory'][0]['display_name']='Gold'
        self.state.changed.emit()
        self.assertIsNone(self.view.goods_proxy.cargo_ids)
        self.assertEqual(self.view.cargo_notice.text(),tr('browse.cargo_identity_unknown'))
        self.cargo(Gold=1)
        self.assertEqual(self.view.goods_proxy.rowCount(),1)

    def test_market_reload_sort_and_checkbox_off_preserve_other_filters(self):
        self.view.goods_table.sortByColumn(2,Qt.DescendingOrder)
        self.view._render_goods()
        self.assertEqual(self.view.goods_proxy.rowCount(),2)
        self.assertEqual(self.view.goods_table.horizontalHeader().sortIndicatorSection(),2)
        self.view.cargo_only.setChecked(False)
        self.assertEqual(self.view.goods_proxy.rowCount(),3)
        self.assertFalse(self.view.cargo_notice.isVisible())
        self.view.mining_only.setChecked(True)
        mining=self.view.goods_proxy.rowCount()
        self.state.cargo_snapshot=None
        self.view.cargo_only.setChecked(True)
        self.assertEqual(self.view.goods_proxy.rowCount(),mining)
        self.assertTrue(self.view.cargo_only.isChecked())

    def test_twelve_languages_both_themes_and_keyboard(self):
        for lang,table in _TRANSLATIONS.items():
            for key in ('only','unavailable','empty','identity_unknown'):
                self.assertTrue(table.get('browse.cargo_'+key),lang)
            set_language(lang)
            self.view.cargo_only.setText(tr('browse.cargo_only'))
            self.view.mining_only.setText(tr('browse.mining'))
            for width in (900,1400):
                self.view.resize(width,900)
                self.app.processEvents()
                self.assertFalse(self.view.cargo_only.geometry().intersects(
                    self.view.mining_only.geometry()),lang)
                self.assertGreaterEqual(self.view.cargo_only.width(),
                                        self.view.cargo_only.sizeHint().width(),lang)
        for theme in (DARK_STYLESHEET,LIGHT_STYLESHEET):
            self.view.setStyleSheet(theme)
            self.view.cargo_only.setFocus()
            QTest.keyClick(self.view.cargo_only,Qt.Key_Space)
            self.assertFalse(self.view.cargo_only.isChecked())
            QTest.keyClick(self.view.cargo_only,Qt.Key_Space)
            self.assertTrue(self.view.cargo_only.isChecked())
            self.assertEqual(self.view.goods_proxy.rowCount(),2)

    def test_new_market_detail_uses_latest_cargo_and_no_empty_hold_message(self):
        self.cargo(Beer=1)
        self.select(2)  # This saved market has no Beer offer.
        self.assertEqual(self.view.goods_proxy.rowCount(),0)
        self.assertFalse(self.view.cargo_notice.isVisible())
        self.state.cargo_snapshot=None
        self.state.cargoSnapshotChanged.emit(None)
        self.assertEqual(self.view.goods_proxy.rowCount(),1)
        self.assertTrue(self.view.cargo_only.isChecked())

    def test_status_only_total_cannot_manufacture_composition(self):
        self.state.ship_cargo_total={'count':0,'source':'status'}
        self.state.cargo_snapshot=None
        with patch('cmdrhelper.ship_cargo.status_ship_count',return_value=0):
            self.state.changed.emit()
        self.assertIsNone(self.view.goods_proxy.cargo_ids)
        self.assertEqual(self.view.goods_proxy.rowCount(),3)
        self.assertEqual(self.view.cargo_notice.text(),tr('browse.cargo_unavailable'))

    def test_radius_values_defaults_all_four_views_no_settings_writes(self):
        settings=QSettings(str(self.root/'trade.ini'), QSettings.IniFormat)
        settings.setValue('favorites/max_distance_ly',250)
        settings.setValue('favorites/distance_filter_enabled',True)
        previous={key:settings.value(key) for key in settings.allKeys()}
        state=TradeState();state.settings=settings
        trade=TradeView(state,provider=Mock(),pool=Mock())
        try:
            for index in (0,1,2,3):
                trade.tabs.setCurrentIndex(index)
                view=trade if index<2 else (trade.recommendations if index==2 else trade.supply_recommendations)
                self.assertEqual([view.radius.itemData(i) for i in range(view.radius.count())],
                                 [20,25,30,50,100,250,500])
                self.assertEqual(view.radius.currentData(),100)
            for index in (0,1):
                trade.tabs.setCurrentIndex(index)
                if index==0:trade.radius.setCurrentIndex(trade.radius.findData(250))
                self.assertEqual(trade.radius.currentData(),250)
            self.assertEqual({key:settings.value(key) for key in settings.allKeys()},previous)
        finally:
            trade.close();trade.deleteLater();self.app.processEvents()
