"""Shared published ship stock: synthetic reducer events and real market signals."""
import os, unittest
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from copy import deepcopy
from dataclasses import replace
from unittest.mock import patch
import test_saved_market_cargo_filter as fixtures
from cmdrhelper.mining_inventory import MiningReducer
from cmdrhelper.ship_cargo import ShipCargoTracker
from cmdrhelper.cargo import cargo_snapshot
from cmdrhelper.models import Mission
from cmdrhelper.ui.mission_cargo import (current_mission_cargo, current_possible_mission_cargo,
    current_mission_cargo_assessment, published_mission_ship_inventory)
from cmdrhelper.commodity_master import lookup_by_symbol
from cmdrhelper.inventory_invalidation import event_kinds

def item(name,count,mid=None):
    return dict(Name=name,Count=count,**({'MissionID':mid} if mid else {}))

class SharedMissionStockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): fixtures.CargoFilterTests.setUpClass()
    def setUp(self):
        self.f=fixtures.CargoFilterTests(); self.addCleanup(self.f.doCleanups); self.f.setUp()
        self.s=self.f.state; self.v=self.f.view; self.c=self.s.mining_inventory_controller
        self.s.missions=[]
        self.f.tracker=ShipCargoTracker(); self.r=MiningReducer(1,self.s.commander_fid)
        self.event('LoadGame',FID=self.s.commander_fid,Ship='cobra',ShipID=7)
        self.event('Loadout',Ship='cobra',ShipID=7)
    def event(self,kind,**fields):
        e=self.f.feed(kind,**fields)
        self.r.apply(e,('synthetic-journal',self.f.seq))
        if kind=='Cargo':
            snap=cargo_snapshot(e,fid=self.s.commander_fid,ship_id=7,cargo_capacity=100)
            snap['context']=dict(self.f.tracker.last_cargo_context)
            self.s.cargo_snapshot=snap
            self.s.cargoSnapshotChanged.emit(snap)
        else: self.s.changed.emit()
        self.c.ready.emit(self.r.result)
        if self.s.missions:
            stocks = current_mission_cargo_assessment(self.s)[1]
            for mission in self.s.missions:
                stock = stocks.get(mission.mission_id)
                if stock is not None and self.r.result.ship is not None:
                    expected = self.r.result.ship.get(mission.commodity_symbol, 0)
                    self.assertEqual(stock.available + stock.assigned, expected)
        return e
    def cargo(self,*rows,vessel='Ship'):
        self.event('Cargo',Vessel=vessel,Count=sum(x['Count'] for x in rows),Inventory=list(rows))
    def mission(self):
        self.s.missions=[Mission(mission_id=42,internal_name='Mission_Mining',commodity_symbol='gold',required_count=10,delivered_count=0)]
        self.s.changed.emit()
    def visible(self):
        return {self.v.goods_proxy.index(i,0).data() for i in range(self.v.goods_proxy.rowCount())}
    def badges(self):
        row=next(x for x in self.v.goods_model.rows if x['commodity_id']==lookup_by_symbol('gold').frontier_id)
        return bool(row.get('mission_cargo')),bool(row.get('possible_mission_cargo'))
    def test_1_no_mission_and_empty(self):
        self.cargo(item('gold',2),item('beer',1)); self.assertEqual(self.visible(),{'Gold','Bier'})
        self.assertEqual(self.badges(),(False,False))
        self.cargo(); self.assertEqual(self.visible(),set())
    def test_2_active_mission_mixed_and_filter_independent(self):
        self.cargo(item('gold',2,42),item('gold',3),item('beer',1))
        before=self.visible(); self.mission()
        self.assertEqual(self.visible(),before); self.assertEqual(self.badges(),(True,True))
        snapshot=deepcopy(self.r.result)
        self.v._cargo_changed(); self.assertEqual(self.r.result,snapshot)
    def test_3_fresh_snapshots_add_remove_and_badges(self):
        self.mission(); self.cargo(item('gold',2,42)); self.assertEqual(self.badges(),(True,False))
        self.cargo(item('gold',3),item('beer',1)); self.assertEqual(self.badges(),(False,True)); self.assertEqual(self.visible(),{'Gold','Bier'})
        self.cargo(item('beer',1)); self.assertEqual(self.visible(),{'Bier'}); self.assertEqual(self.badges(),(False,False))
    def test_4_rhino_preserves_pink_without_inventing_blue(self):
        self.mission(); self.cargo(item('gold',2,42),item('gold',3)); self.assertEqual(self.badges(),(True,True))
        self.event('LaunchSRV',ID=57,SRVType='mev_rhino',PlayerControlled=True)
        self.cargo(item('beer',4),vessel='SRV')
        self.assertEqual(self.r.result.ship,{'gold':5}); self.assertEqual(self.visible(),{'Gold'})
        self.assertEqual(self.badges(),(False,True))
        self.event('CargoTransfer',Transfers=[dict(Type='beer',Count=4,Direction='toship')])
        self.assertEqual(self.r.result.ship,{'gold':5,'beer':4}); self.assertEqual(self.visible(),{'Gold','Bier'})
    def test_5_tracked_buy_sell_keep_pink(self):
        self.mission(); self.cargo(item('gold',3)); self.assertEqual(self.badges(),(False,True))
        self.event('MarketBuy',Type='beer',Count=2)
        self.assertEqual(self.visible(),{'Gold','Bier'}); self.assertEqual(self.badges(),(False,True))
        self.event('MarketSell',Type='beer',Count=2)
        self.assertEqual(self.visible(),{'Gold'})
    def test_6_publication_signals_refresh_badges(self):
        self.mission(); self.cargo(item('gold',2,42),item('gold',3))
        self.assertEqual(self.badges(),(True,True))
        self.s.cargo_snapshot=None
        self.c.publicationChanged.emit()
        self.assertEqual(self.badges(),(False,True))
        self.c.loading.emit()
        self.assertEqual(self.badges(),(False,False))
        self.c.ready.emit(self.r.result)
        self.assertEqual(self.badges(),(False,True))
    def test_7_completion_preserves_normal_stock_and_removes_badges(self):
        self.mission(); self.cargo(item('gold',2,42),item('gold',3),item('beer',1))
        self.s.missions=[]
        self.event('MissionCompleted',MissionID=42,Name='Mission_Mining',Reward=100)
        self.assertEqual(self.badges(),(False,False)); self.assertEqual(self.visible(),{'Gold','Bier'})
        self.assertEqual(self.r.result.ship,{'gold':5,'beer':1})
        self.cargo(item('gold',3),item('beer',1)); self.assertEqual(self.badges(),(False,False))
        self.assertEqual(self.visible(),{'Gold','Bier'})
        self.assertIn('mining',event_kinds([dict(event='MissionCompleted')]))
    def test_8_completion_with_commodity_invalidates_as_existing_rule(self):
        self.mission(); self.cargo(item('gold',3),item('beer',1)); self.s.missions=[]
        self.event('MissionCompleted',MissionID=42,Commodity='gold',Count=2)
        self.assertIsNone(self.r.result.ship); self.assertIsNone(self.v.goods_proxy.cargo_ids)
        self.cargo(item('gold',1),item('beer',1)); self.assertEqual(self.visible(),{'Gold','Bier'})

    def test_9_metadata_rejection_never_hides_published_stock(self):
        self.mission(); self.cargo(item('gold',2,42),item('gold',3))
        original=deepcopy(self.s.cargo_snapshot)
        for key,value in (('fid','OTHER'),('ship_id',8),('generation',-1),
                          ('session_generation',-1),('journal','other-journal'),
                          ('vessel','SRV'),('timestamp','old')):
            with self.subTest(key=key):
                self.s.cargo_snapshot=deepcopy(original)
                self.s.cargo_snapshot['context'][key]=value
                self.c.publicationChanged.emit()
                self.assertEqual(self.badges(),(False,True))
                self.assertEqual(self.visible(),{'Gold'})
        for bound in ({42:6},{42:-1},{True:2},{'42':2}):
            self.s.cargo_snapshot=deepcopy(original)
            self.s.cargo_snapshot['inventory'][0]['mission_counts']=bound
            self.c.publicationChanged.emit()
            self.assertEqual(self.badges(),(False,True))
        self.s.cargo_snapshot=original
        self.c.ready.emit(self.r.result)
        self.assertEqual(self.badges(),(True,True))

    def test_10_quality_empty_and_recovery(self):
        self.mission(); self.cargo(item('gold',3))
        for quality in ('confirmed','tracked','stale','unknown','inconsistent'):
            with self.subTest(quality=quality):
                self.r.result.vehicle_records['Ship']['quality']=quality
                self.c.publicationChanged.emit()
                stock=current_mission_cargo_assessment(self.s)[1][42]
                valid=quality in ('confirmed','tracked')
                self.assertEqual(stock.available,3 if valid else None)
                self.assertEqual(self.badges(),(False,valid))
                self.assertEqual(self.v.goods_proxy.cargo_ids is not None,valid)
        self.cargo()
        self.assertEqual(self.visible(),set())
        self.assertEqual(current_mission_cargo_assessment(self.s)[1][42].available,0)
        self.assertEqual(self.badges(),(False,False))

    def test_11_acceptance_shared_stock_no_double_count_and_gate(self):
        self.cargo(item('gold',3))
        with patch('cmdrhelper.ui.mission_cargo.published_mission_ship_inventory',
                   side_effect=AssertionError('no cargo check without eligible mission')):
            self.assertEqual(current_possible_mission_cargo(self.s),{})
        self.event('MissionAccepted',MissionID=42)
        self.mission()
        self.s.missions.append(replace(self.s.missions[0],mission_id=43))
        before=deepcopy(self.s.missions)
        self.s.changed.emit()
        pink,stocks=current_mission_cargo_assessment(self.s)
        detail=pink[lookup_by_symbol('gold').frontier_id]
        self.assertEqual((detail.available,detail.coverable,detail.remaining),(3,3,20))
        self.assertEqual(stocks[42].group.need,20)
        self.assertEqual(self.s.missions,before)

    def test_12_ship_and_commander_switch(self):
        self.mission(); self.cargo(item('gold',2,42),item('gold',3))
        self.event('ShipyardSwap',StoreShipID=7,ShipID=8,ShipType='python')
        self.assertEqual(self.visible(),{'Gold'})
        self.assertEqual(self.badges(),(False,True))
        self.s.commander_id=self.s.viewed_commander_id=2
        self.s.commander_fid='SECOND'
        self.c.loading.emit()  # Controller clears its publication on owner change.
        self.assertEqual(self.badges(),(False,False))
        self.assertIsNone(published_mission_ship_inventory(self.s))
        other=replace(self.r.result,commander_id=2,fid='SECOND',ship={'beer':1})
        self.c.ready.emit(other)
        self.assertEqual(self.visible(),{'Bier'})
        self.assertEqual(self.badges(),(False,False))

    def test_13_republication_no_io_no_mutation_and_no_selection_reset(self):
        from PySide6.QtCore import Qt
        self.mission(); self.cargo(item('gold',2,42),item('gold',3),item('beer',1))
        self.v.goods_table.sortByColumn(2,Qt.DescendingOrder)
        self.v.goods_table.selectRow(0)
        selected=self.v.goods_table.currentIndex().data()
        before=deepcopy(self.r.result)
        with patch('builtins.open',side_effect=AssertionError('no IO')), \
             patch('cmdrhelper.ship_cargo.current_ship_inventory',side_effect=AssertionError('no second assessment')):
            self.s.cargo_snapshot=None
            self.c.publicationChanged.emit()
            self.assertEqual(self.badges(),(False,True))
            self.c.ready.emit(self.r.result)
        self.assertEqual(self.r.result,before)
        self.assertEqual(self.v.goods_table.currentIndex().data(),selected)
        self.assertEqual(self.v.goods_table.horizontalHeader().sortIndicatorSection(),2)

if __name__ == '__main__':
    unittest.main(verbosity=2)
