"""Synthetic cobalt lifecycle across existing trade, mining and mission widgets."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from copy import deepcopy
from string import Formatter
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import QWidget, QStyleOptionViewItem
from cmdrhelper.cargo import normalize_inventory
from cmdrhelper.commodity_master import lookup_by_symbol
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.models import Mission
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.mining_view import MiningView
from cmdrhelper.ui.mission_cargo import (current_mission_cargo_assessment,
    mission_cargo_stock_text, POSSIBLE_MISSION_CARGO_ROLE, MissionCargoStock, MissionCargoGroup)
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests import test_mission_cargo as fixture
from tests.test_missions_table_sort import Host


def mission(mid=1, **kwargs):
    return Mission(mission_id=mid, name='Cobalt mission', internal_name='Mission_Mining',
                   commodity_symbol='cobalt', required_count=45, **kwargs)


class AssessmentTests(unittest.TestCase):
    def test_gate_unknown_zero_mixed_and_shared(self):
        state = SimpleNamespace(missions=[], commander_id=1)
        with patch('cmdrhelper.ui.mission_cargo.published_mission_ship_inventory') as read:
            self.assertEqual(current_mission_cargo_assessment(state), ({}, {}))
            read.assert_not_called()
            state.missions = [mission()]
            read.return_value = None
            self.assertIsNone(current_mission_cargo_assessment(state)[1][1].available)
            read.return_value = {'inventory': []}
            self.assertEqual(current_mission_cargo_assessment(state)[1][1].available, 0)
            state.missions.append(mission(2, delivered_count=0))
            read.return_value = {'inventory': normalize_inventory([
                {'Name':'cobalt','Count':10,'MissionID':1},
                {'Name':'cobalt','Count':20,'MissionID':99},
                {'Name':'cobalt','Count':15}])}
            before = deepcopy((state.missions, read.return_value))
            pink, stock = current_mission_cargo_assessment(state)
            self.assertEqual(stock[1], MissionCargoStock(15,10,True,MissionCargoGroup(90,True,10)))
            self.assertEqual(stock[2], MissionCargoStock(15,0,True,MissionCargoGroup(90,True,10)))
            self.assertEqual(next(iter(pink.values())).available,15)
            self.assertEqual(next(iter(pink.values())).coverable,15)
            self.assertEqual((state.missions, read.return_value),before)
            state.viewed_commander_id = 2
            read.reset_mock()
            self.assertIsNone(current_mission_cargo_assessment(state)[1][1].available)
            read.assert_not_called()
            state.missions = [mission(delivered_count=45)]
            self.assertEqual(current_mission_cargo_assessment(state), ({}, {}))
            read.assert_not_called()

    def test_explicit_only_and_malformed_binding_never_become_free_stock(self):
        state = SimpleNamespace(missions=[mission()], commander_id=1)
        with patch('cmdrhelper.ui.mission_cargo.published_mission_ship_inventory') as read:
            for mid, assigned in ((1,45),(99,0)):
                read.return_value = {'inventory': normalize_inventory([
                    {'Name':'cobalt','Count':45,'MissionID':mid}])}
                pink,stock = current_mission_cargo_assessment(state)
                self.assertFalse(pink)
                self.assertEqual(stock[1],MissionCargoStock(0,assigned,False))
            for bound in ({1:46},{1:-1},'invalid'):
                read.return_value = {'inventory':[{'frontier_name':'cobalt','count':45,'mission_counts':bound}]}
                pink,stock = current_mission_cargo_assessment(state)
                self.assertFalse(pink)
                self.assertIsNone(stock[1].available)


class UsabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.MissionCargoViewTests.setUpClass()
        cls.app = fixture.MissionCargoViewTests.app

    def setUp(self):
        self.addCleanup(set_language,get_language())
        self.fx = fixture.MissionCargoViewTests(); self.fx.setUp()
        self.addCleanup(self.fx.doCleanups)
        self.state, self.trade, self.market = self.fx.state, self.fx.trade, self.fx.market
        self.state.settings = QSettings(str(self.fx.fixture.tmp.name) + "/usability.ini", QSettings.IniFormat)
        self.state.missions = [mission()]
        self.market._snapshot['commodities'] = [dict(commodity_id=lookup_by_symbol('cobalt').frontier_id,
            symbol='cobalt',commander_buy_price=10,commander_sell_price=9,supply=20,demand=30)]
        self.market._render_goods()
        self.fx.cargo([fixture.item(45,name='cobalt')])  # Valid stock predates the new views.
        controller = self.state.mining_inventory_controller
        with patch('cmdrhelper.mining_market_controller.MiningMarketController'):
            self.mining = MiningView(self.state.settings, state=self.state, controller=controller)
        self.addCleanup(self.mining.deleteLater)
        self.addCleanup(self.mining.close)
        self.host = Host(state=self.state)
        for name in ('_missions','_card','_save_missions_header_state','_mission_selection_changed','_refresh_missions_table'):
            setattr(self.host,name,getattr(MainWindow,name).__get__(self.host))
        for name in ('_format_reward','_format_expiry','_place_text','_translate_mission_text'):
            setattr(self.host,name,getattr(MainWindow,name))
        self.state.refresh = Mock()
        self.state.bounties = self.state.combat_bonds = None
        with patch('cmdrhelper.ui.bounty_view.BountyView',side_effect=lambda *a:QWidget()), patch('cmdrhelper.ui.combat_bond_view.CombatBondView',side_effect=lambda *a:QWidget()):
            self.host.page = self.host._missions()
        self.addCleanup(self.host.page.deleteLater)
        self.addCleanup(self.host.page.close)
        self.host._refresh_missions_table()
        self.host.missions_table.selectRow(0)

    def cargo(self, rows=None):
        self.fx.cargo(rows if rows is not None else [fixture.item(45,name='cobalt')])

    def pink(self):
        return [self.trade.cargo_list.item(0).data(POSSIBLE_MISSION_CARGO_ROLE),
                self.market.goods_model.index(0,0).data(POSSIBLE_MISSION_CARGO_ROLE),
                self.mining.items['cobalt'].data(0,POSSIBLE_MISSION_CARGO_ROLE)]

    def text(self):
        return self.host.mission_progress_text.text()

    def test_cobalt_acceptance_partial_delivery_completion_and_removal(self):
        self.state.missions=[]
        self.cargo()
        self.assertFalse(any(self.pink()))
        self.state.missions=[mission()]
        self.state.changed.emit()  # Already-known cargo, no new cargo event.
        self.assertTrue(all(self.pink()))
        self.assertIn('45 t passende Ware im Schiff vorhanden',self.text())
        self.assertIn('Lieferstand unbekannt',self.text())
        self.assertIn('Annahme der Ware durch Elite noch nicht bestätigt',self.text())
        self.state.missions=[mission(delivered_count=20, depot_update_type='deliver')]
        self.state.changed.emit()  # Mission object replaced while selected row is unchanged.
        self.assertIn('25 t fehlen',self.text())
        self.cargo([fixture.item(25,name='cobalt')])
        self.assertIn('25 t passende Ware',self.text())
        self.state.missions=[mission(delivered_count=45, depot_update_type='deliver')]
        self.state.changed.emit()  # Same cargo amount must still remove every pink badge.
        self.assertFalse(any(self.pink()))
        self.assertNotIn('passende Ware',self.text())
        self.assertIn('Lieferung abgeschlossen',self.text())
        self.state.missions=[]
        self.state.changed.emit()
        self.assertEqual(self.text(),'')

    def test_invalidation_identity_ship_and_initial_restored_view(self):
        # Construction uses restored open missions and existing valid inventory,
        # without waiting for another Cargo event.
        self.assertTrue(all(self.pink()))
        self.assertIn('45 t passende Ware',self.text())
        self.host._refresh_missions_table(); self.host.missions_table.selectRow(0)
        self.assertIn('45 t passende Ware',self.text())
        for attr,value,signal,payload in (
            ('viewed_commander_id',2,'viewedCommanderChanged',2),
            ('commander_fid','OTHER','shipLoadoutChanged',None)):
            old=getattr(self.state,attr)
            setattr(self.state,attr,value); getattr(self.state,signal).emit(payload)
            self.assertFalse(any(self.pink()))
            self.assertIn('Schiffsbestand unbekannt',self.text())
            setattr(self.state,attr,old); getattr(self.state,signal).emit(payload)
            self.assertTrue(all(self.pink()))
        self.state.missions=[]; self.state.changed.emit()
        with patch('cmdrhelper.ui.mission_cargo.published_mission_ship_inventory',side_effect=AssertionError):
            self.mining._refresh_mission_cargo()
            self.host._mission_selection_changed()

    def test_mining_only_signals_update_details_and_preserve_sale_search(self):
        from dataclasses import replace
        controller=self.state.mining_inventory_controller
        inventory=controller._last_inventory
        before=deepcopy(self.state.missions)
        self.state.cargo_snapshot=None
        with patch.object(self.trade,'_invalidate_results',side_effect=AssertionError('symbol refresh')):
            controller.ready.emit(replace(inventory,ship={'cobalt':20}))
            self.assertIn('20 t passende Ware',self.text())
            self.assertEqual(self.market.goods_model.index(0,0).data(POSSIBLE_MISSION_CARGO_ROLE).total,20)
            self.assertEqual(self.mining.items['cobalt'].data(0,POSSIBLE_MISSION_CARGO_ROLE).total,20)
            # The existing selling list still has 45 t: do not attach a 20 t
            # badge to that row or change the running search's inputs.
            self.assertIsNone(self.trade.cargo_list.item(0).data(POSSIBLE_MISSION_CARGO_ROLE))
            controller.loading.emit()
            self.assertIn('Schiffsbestand unbekannt',self.text())
            controller.ready.emit(inventory)
            self.assertIn('45 t passende Ware',self.text())
            self.assertTrue(all(self.pink()))
        self.assertEqual(self.state.missions,before)

    def test_pending_offers_without_ids_keep_the_selected_details(self):
        offers = [Mission(name=name, summary=name, extra={'pending_offer':True})
                  for name in ('First offer','Second offer')]
        self.state.missions=offers
        self.host._refresh_missions_table()
        for row in range(2):
            if self.host.missions_table.item(row,0).mission is offers[1]:
                self.host.missions_table.selectRow(row)
                break
        with patch('cmdrhelper.ui.mission_cargo.published_mission_ship_inventory',side_effect=AssertionError):
            self.host._mission_selection_changed()
        self.assertEqual(self.host.mission_detail_title.text(),'Second offer')
        self.assertEqual(self.host.mission_detail_text.text(),'Second offer')

    def test_same_quantity_binding_changes_preserve_mining_table(self):
        item=self.mining.items['cobalt']
        self.mining.tree.setCurrentItem(item)
        before=[(item.text(c),item.data(c,Qt.UserRole),item.foreground(c)) for c in range(8)]
        order=[self.mining.tree.topLevelItem(i).text(0) for i in range(self.mining.tree.topLevelItemCount())]
        self.cargo([fixture.item(10,1,name='cobalt'), fixture.item(20,99,name='cobalt'), fixture.item(15,name='cobalt')])
        self.assertTrue(all(self.pink()))
        self.assertIn('25 t passende Ware',self.text())
        self.assertIn('10 t dieser Mission',self.text())
        self.cargo([fixture.item(45,99,name='cobalt')])
        self.assertFalse(any(self.pink()))
        self.assertIn('0 t passende Ware',self.text())
        self.assertIs(self.mining.tree.currentItem(),item)
        self.assertEqual(before,[(item.text(c),item.data(c,Qt.UserRole),item.foreground(c)) for c in range(8)])
        self.assertEqual(order,[self.mining.tree.topLevelItem(i).text(0) for i in range(self.mining.tree.topLevelItemCount())])

    def test_themes_languages_decoration_and_market_hint(self):
        self.cargo()
        item=self.mining.items['cobalt']
        values=[(item.text(c),item.data(c,Qt.UserRole),item.foreground(c)) for c in range(8)]
        keys=['missions.cargo_available','missions.cargo_unknown','missions.cargo_assigned',
              'missions.cargo_shared','missions.cargo_unconfirmed','browse.select','browse.selection_hint']
        for lang,table in _TRANSLATIONS.items():
            set_language(lang)
            for key in keys:
                self.assertIn(key,table)
                fields=lambda text: {f for _,f,_,_ in Formatter().parse(text) if f}
                self.assertEqual(fields(table[key]),fields(_TRANSLATIONS['de'][key]))
            self.host._mission_selection_changed()
            self.assertIn(tr('missions.cargo_available',count='45'),self.text())
            self.assertIn(tr('missions.delivery_unknown'),self.text())
            self.market._clear_detail()
            self.assertEqual(self.market.detail_header.text(),tr('browse.select'))
            self.assertEqual(self.market.selection_hint.text(),tr('browse.selection_hint'))
            self.assertIn(tr('missions.cargo_shared'),mission_cargo_stock_text(MissionCargoStock(15,10,True)))
            for theme in (DARK_STYLESHEET,LIGHT_STYLESHEET):
                self.mining.setStyleSheet(theme)
                index=self.mining.tree.indexFromItem(item,0)
                option=QStyleOptionViewItem(); option.initFrom(self.mining.tree)
                self.mining.carrier_delegate.initStyleOption(option,index)
                self.assertFalse(option.icon.isNull())
                self.mining.tree.viewport().grab()
            self.mining._refresh_mission_cargo()
            self.assertIn(tr('trade.possible_cargo_warning'),item.toolTip(0))
        self.assertEqual(values,[(item.text(c),item.data(c,Qt.UserRole),item.foreground(c)) for c in range(8)])
        set_language('de')
        self.market._clear_detail()
        self.assertFalse(self.market.selection_hint.isHidden())
        self.assertEqual(self.market.detail_header.text(),'Bitte zuerst einen gespeicherten Markt auswählen.')
        self.assertEqual(self.market.selection_hint.text(),tr('browse.selection_hint'))
        with patch.object(self.market,'_start'):
            self.market._load_detail(123)
        self.assertTrue(self.market.selection_hint.isHidden())
        self.assertEqual(self.market._selected_id,123)
