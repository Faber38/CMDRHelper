"""Small real-sidecar regressions for the own-carrier accounting rule."""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QSettings
from cmdrhelper.odyssey_carrier import OdysseyCarrierStore, material_amounts
from cmdrhelper.odyssey_inventory import OdysseyReducer
from cmdrhelper.odyssey_sidecars import OdysseySidecars
from cmdrhelper.odyssey_tracking import CarrierProjection, OdysseyCarrierTracking, personal_delta


class TrackingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.path = self.root/'Journal.2026-09-15T060000.01.log'
        self.db = self.root/'test.db'
        with sqlite3.connect(self.db) as con:
            con.executescript('CREATE TABLE commanders(id INTEGER,fid TEXT);'
                              "INSERT INTO commanders VALUES(1,'F1');"
                              'CREATE TABLE commander_carriers(commander_id INTEGER,carrier_id INTEGER);'
                              'INSERT INTO commander_carriers VALUES(1,123);')
        self.settings = QSettings(str(self.root/'stock.ini'), QSettings.IniFormat)
        self.store = OdysseyCarrierStore(self.settings)
        self.store.confirm('F1',123,'Components','chemicalcatalyst',0)
        self.state = SimpleNamespace(settings=self.settings, database=SimpleNamespace(path=self.db),
            commander_id=1, commander_fid='F1', odysseySidecarsChanged=Mock(),
            watcher=SimpleNamespace(odyssey_sidecars=OdysseySidecars()), refresh=Mock())
        self.tracker = OdysseyCarrierTracking(self.state)
        self.clock = 0
        self.append('Commander',FID='F1')
        self.append('Docked',StationType='FleetCarrier',MarketID=123)
        self.snapshot(7)

    def append(self, kind, **fields):
        self.clock += 1
        event = dict(event=kind,timestamp=f'2026-09-15T06:{self.clock//60:02}:{self.clock%60:02}Z',**fields)
        with self.path.open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(event)+'\n')
        return event

    def poll(self):
        self.state.watcher.odyssey_sidecars.poll(self.path)
        self.tracker.poll()

    def snapshot(self, amount, *, extra=None, write=True):
        event=self.append('ShipLocker')
        event.update(Items=[],Components=[dict(Name='chemicalcatalyst',Count=amount)],Data=[],Consumables=[])
        for cat,items in (extra or {}).items():
            event[cat].extend(items)
        if write:
            (self.root/'ShipLocker.json').write_text(json.dumps(event),encoding='utf-8')
        self.poll()
        return event

    def record(self, cat='Components',name='chemicalcatalyst'):
        return self.store.load('F1',123)['records'][f'{cat}/{name}']

    def test_real_roundtrip_and_exactly_once(self):
        self.snapshot(3)
        self.assertEqual((self.record()['current_amount'],self.record()['status']),(4,'tracked'))
        before=deepcopy(self.store.load('F1',123))
        self.poll();self.poll()
        self.assertEqual(self.store.load('F1',123),before)
        self.snapshot(7)
        self.assertEqual(self.record()['current_amount'],0)
        self.assertEqual(self.record()['last_confirmed_amount'],0)
        self.state.refresh.assert_not_called()

    def test_real_carrier_embark_flags_keep_docked_identity_and_zero_anchor(self):
        carrier=1234567890
        with sqlite3.connect(self.db) as con:
            con.execute('UPDATE commander_carriers SET carrier_id=?',(carrier,))
        self.append('Docked',StationType='FleetCarrier',MarketID=carrier,
                    StationName='TST-001',Taxi=False,Multicrew=False)
        # Actual journal shape from 2026-09-15: no MarketID/StationType here.
        for kind in ('Disembark','Embark'):
            self.append(kind,SRV=False,Taxi=False,Multicrew=False,ID=12,
                        OnStation=False,OnPlanet=True,SystemAddress=5474145570075,
                        BodyID=37,Body='Plio Aihm UC-V d2-159 7 d')
        self.snapshot(7)
        self.assertTrue(self.tracker.engine.present)
        record=lambda:self.store.load('F1',carrier)['records']['Components/chemicalcatalyst']
        for starting in (0,10):
            with self.subTest(starting=starting):
                self.store.confirm('F1',carrier,'Components','chemicalcatalyst',starting)
                self.tracker.reanchor()
                self.assertEqual(self.tracker.engine.anchor['amounts']['Components/chemicalcatalyst'],7)
                self.snapshot(3)
                self.assertEqual((record()['current_amount'],record()['status']),(starting+4,'tracked'))
                self.assertEqual(record()['last_confirmed_amount'],starting)
                self.poll()
                self.assertEqual(record()['current_amount'],starting+4)
                self.snapshot(7)
                self.assertEqual(record()['current_amount'],starting)
        self.append('SellMicroResources',MarketID=carrier,Price=1600,
                    MicroResources=[dict(Name='chemicalcatalyst',Category='Component',Count=4)])
        self.snapshot(3)
        self.assertEqual(record()['current_amount'],10)
        self.append('BuyMicroResources',MarketID=carrier,Price=1600,
                    MicroResources=[dict(Name='chemicalcatalyst',Category='Component',Count=4)])
        self.snapshot(7)
        self.assertEqual(record()['current_amount'],10)

    def test_ambiguous_embark_cannot_create_presence_or_override_exit(self):
        carrier=1234567890
        ambiguous=dict(event='Disembark',SRV=False,Taxi=False,Multicrew=False,
                       OnStation=False,OnPlanet=True)
        for transition in ({'event':'Undocked'}, {'event':'StartJump'},
                           {'event':'Location','Docked':True,'StationType':'Outpost','MarketID':42}):
            engine=CarrierProjection(carrier)
            engine.event(ambiguous)
            self.assertFalse(engine.present)
            engine.event(dict(event='Docked',StationType='FleetCarrier',MarketID=carrier))
            engine.event(transition)
            engine.event(ambiguous)
            self.assertFalse(engine.present)
        for contradiction in ({'MarketID':42}, {'StationType':'Outpost'}):
            engine=CarrierProjection(carrier)
            engine.event(dict(event='Docked',StationType='FleetCarrier',MarketID=carrier))
            engine.event(dict(ambiguous,**contradiction))
            self.assertFalse(engine.present)

    def test_missing_location_fields_preserve_persisted_own_carrier_marker(self):
        self.assertEqual(self.tracker.engine.location_state,'OWN_CARRIER')
        for kind in ('Disembark','Embark'):
            self.append(kind) # no MarketID, OnStation, SRV, Taxi or Multicrew
            self.poll()
            self.assertEqual(self.tracker.engine.location_state,'OWN_CARRIER')
        self.store.confirm('F1',123,'Components','chemicalcatalyst',0)
        self.assertEqual(self.store.load('F1',123)['tracking']['location_state'],'OWN_CARRIER')
        self.tracker.reanchor()
        self.snapshot(7) # container change establishes a fresh personal baseline
        saved=self.store.load('F1',123)['tracking']
        self.assertEqual((saved['location_state'],saved['location_market_id']),('OWN_CARRIER',123))
        self.snapshot(3)
        self.assertEqual(self.record()['current_amount'],4)
        self.snapshot(7)
        self.assertEqual(self.record()['current_amount'],0)
        self.append('Undocked')
        self.poll()
        self.assertEqual(self.store.load('F1',123)['tracking']['location_state'],'OTHER_LOCATION')
        self.append('Embark')
        self.snapshot(3)
        self.assertEqual(self.record()['current_amount'],0)

    def test_existing_seven_anchor_survives_bare_embark_and_harmless_tail(self):
        self.append('ReceiveText',Message='unrelated journal event')
        self.poll()
        self.store.confirm('F1',123,'Components','chemicalcatalyst',0)
        self.tracker.reanchor()
        for kind in ('Disembark','Embark'):
            self.append(kind,OnStation=False,OnPlanet=True)
            self.poll()
        self.assertEqual(self.tracker.engine.anchor['amounts']['Components/chemicalcatalyst'],7)
        self.snapshot(3)
        self.assertEqual(self.record()['current_amount'],4)
        self.snapshot(7)
        self.assertEqual(self.record()['current_amount'],0)

    def restart_capture(self):
        self.state.watcher.odyssey_sidecars=OdysseySidecars()
        self.tracker=OdysseyCarrierTracking(self.state)
        self.poll()

    def index_row(self,path,fid='F1'):
        stat=path.stat()
        return dict(journal_file=str(path),fid_seen=fid,attribution_status='identified',
                    file_size=stat.st_size,modified_ns=stat.st_mtime_ns)

    def test_late_helper_start_replays_moves_and_never_books_offline_delta(self):
        self.snapshot(3) # stored carrier 4, old locker 3
        self.append('Undocked')
        self.append('FSDJump')
        self.append('Docked',StationType='Outpost',MarketID=456)
        self.append('Disembark',OnPlanet=True,OnStation=False)
        self.restart_capture()
        self.assertEqual(self.tracker.engine.location_state,'STATION')
        self.assertEqual(self.record()['current_amount'],4)
        self.append('Undocked')
        self.append('Docked',StationType='FleetCarrier',MarketID=123)
        self.append('Disembark',OnPlanet=True,OnStation=False)
        # Simulate an overwritten snapshot while Helper is stopped.
        new=self.append('ShipLocker')
        new.update(Items=[],Components=[dict(Name='chemicalcatalyst',Count=7)],Data=[],Consumables=[])
        (self.root/'ShipLocker.json').write_text(json.dumps(new))
        self.restart_capture()
        self.assertEqual(self.tracker.engine.location_state,'OWN_CARRIER')
        self.assertEqual(self.record()['current_amount'],4) # no retrospective -4
        self.assertEqual(self.tracker.engine.anchor['amounts']['Components/chemicalcatalyst'],7)
        self.store.confirm('F1',123,'Components','chemicalcatalyst',0)
        self.tracker.reanchor()
        self.snapshot(3)
        self.assertEqual(self.record()['current_amount'],4)
        self.snapshot(7)
        self.assertEqual(self.record()['current_amount'],0)

    def test_late_start_across_indexed_rotation_reconstructs_only_location(self):
        previous=self.path
        self.state._journal_index_sessions=[self.index_row(previous)]
        self.path=self.root/'Journal.2026-09-15T070000.02.log'
        self.append('Commander',FID='F1')
        self.append('Disembark',OnPlanet=True,OnStation=False)
        self.state.watcher.odyssey_sidecars=OdysseySidecars()
        self.tracker=OdysseyCarrierTracking(self.state)
        self.snapshot(7)
        self.assertEqual(self.tracker.engine.location_state,'OWN_CARRIER')
        with patch('cmdrhelper.journal_reader.read_journal_delta',side_effect=AssertionError('no historical live rescan')):
            self.snapshot(3)
            self.assertEqual(self.record()['current_amount'],4)
            self.snapshot(7)
            self.assertEqual(self.record()['current_amount'],0)
        # A later definite station always wins over the old carrier marker.
        self.append('Undocked')
        self.append('Docked',StationType='Outpost',MarketID=456)
        self.restart_capture()
        self.assertEqual(self.tracker.engine.location_state,'STATION')
        middle=self.path
        self.state._journal_index_sessions=[self.index_row(previous),self.index_row(middle)]
        self.path=self.root/'Journal.2026-09-15T080000.03.log'
        self.append('Commander',FID='F1')
        self.append('Disembark')
        self.restart_capture()
        self.assertEqual(self.tracker.engine.location_state,'STATION')
        # A different commander in the predecessor cannot lend its location.
        self.state._journal_index_sessions=[self.index_row(previous),self.index_row(middle,'F2')]
        self.path=self.root/'Journal.2026-09-15T090000.04.log'
        self.append('Commander',FID='F1')
        self.restart_capture()
        self.assertEqual(self.tracker.engine.location_state,'UNKNOWN')

    def test_location_state_changes_only_with_new_place_evidence(self):
        engine=CarrierProjection(1234567890)
        engine.event(dict(event='Docked',StationType='FleetCarrier',MarketID=1234567890))
        for event in ({'event':'Location'}, {'event':'Embark'},
                      {'event':'Disembark','OnStation':False,'OnPlanet':True},
                      {'event':'Embark','Taxi':True}, {'event':'Disembark','SRV':True},
                      {'event':'Embark','Multicrew':True}):
            engine.event(event)
            self.assertEqual(engine.location_state,'OWN_CARRIER')
        for event,state in [
                ({'event':'Docked','StationType':'FleetCarrier','MarketID':456},'OTHER_CARRIER'),
                ({'event':'Docked','StationType':'Outpost','MarketID':42},'STATION'),
                ({'event':'Embark'},'STATION'),
                ({'event':'StartJump','Taxi':True},'OTHER_LOCATION'),
                ({'event':'Disembark'},'OTHER_LOCATION')]:
            engine.event(event)
            self.assertEqual(engine.location_state,state)

    def test_sales_purchases_and_mixed_transfer(self):
        self.append('SellMicroResources',Name='chemicalcatalyst',Category='Component',Count=4,Price=1600,MarketID=123)
        self.snapshot(3)
        self.assertEqual(self.record()['current_amount'],0)
        self.append('BuyMicroResources',Name='chemicalcatalyst',Category='Component',Count=4,Price=1600,MarketID=123)
        self.snapshot(7)
        self.assertEqual(self.record()['current_amount'],0)
        self.append('SellMicroResources',Name='chemicalcatalyst',Category='Component',Count=4)
        self.snapshot(1)
        self.assertEqual(self.record()['current_amount'],2)

    def test_trade_and_explicit_upgrade_and_reward_amounts(self):
        self.store.confirm('F1',123,'Components','graphene',0)
        self.append('TradeMicroResources',Offered=[dict(Name='chemicalcatalyst',Category='Component',Count=2)],
                    Received='graphene',Category='Component',Count=1)
        self.snapshot(5,extra={'Components':[dict(Name='graphene',Count=1)]})
        self.assertEqual(self.record()['current_amount'],0)
        self.assertEqual(self.record(name='graphene')['current_amount'],0)
        for kind in ('UpgradeSuit','UpgradeWeapon'):
            with self.subTest(kind=kind):
                delta=personal_delta(dict(event=kind,Resources=[dict(Name='chemicalcatalyst',Category='Component',Count=2)]))
                self.assertEqual(delta,{'Components/chemicalcatalyst':-2})
        self.assertEqual(personal_delta(dict(event='MissionCompleted',MaterialsReward=[
            dict(Name='chemicalcatalyst',Category='Component',Count=2)])),{'Components/chemicalcatalyst':2})

    def test_normal_station_foreign_carrier_unknown_and_return(self):
        for station,market in [('Coriolis',123),('FleetCarrier',456),(None,None)]:
            with self.subTest(station=station):
                if station is None:
                    self.append('Undocked') # an empty Location cannot erase a witnessed stay
                self.append('Location',Docked=True,StationType=station,MarketID=market)
                self.snapshot(1)
                self.assertEqual(self.record()['current_amount'],0)
                self.append('Docked',StationType='FleetCarrier',MarketID=123)
                self.snapshot(7)  # fresh arrival baseline, never count travel delta
                self.assertEqual(self.record()['current_amount'],0)
        self.snapshot(3)
        self.assertEqual(self.record()['current_amount'],4)

    def test_backpack_actions_and_market_data_alone_do_not_book(self):
        for kind in ('BackpackChange','CollectItems','UseConsumable','FCMaterials','CarrierTradeOrder'):
            self.append(kind,Name='chemicalcatalyst',Count=4,Stock=900,Demand=900)
            self.poll()
        self.assertEqual(self.record()['current_amount'],0)
        self.snapshot(7)
        self.assertEqual(self.record()['current_amount'],0)

    def test_unknown_baseline_never_invents_stock(self):
        self.store.confirm('F1',123,'Components','chemicalcatalyst',None)
        self.tracker.reanchor()
        self.snapshot(3)
        self.assertIsNone(self.record()['current_amount'])

    def test_negative_and_multi_material_interval_fail_together(self):
        self.store.confirm('F1',123,'Components','graphene',10)
        self.snapshot(7,extra={'Components':[dict(Name='graphene',Count=0)]})
        self.snapshot(8,extra={'Components':[dict(Name='graphene',Count=1)]})
        for name in ('chemicalcatalyst','graphene'):
            record=self.record(name=name)
            self.assertEqual(record['status'],'inconsistent')
            self.assertIsNone(record['current_amount'])
        self.assertEqual(self.record(name='graphene')['last_confirmed_amount'],10)

    def test_shared_capacity_not_per_category(self):
        self.store.confirm('F1',123,'Items','push',500)
        self.store.confirm('F1',123,'Data','covertops',499)
        self.snapshot(6) # 1000 known across categories
        self.assertEqual(self.record()['current_amount'],1)
        self.snapshot(5) # 1001 -> inconsistent, no clamp
        self.assertEqual(self.record()['status'],'inconsistent')
        self.assertEqual(self.record()['uncertainty_reason'],'capacity')

    def test_multiple_materials_success(self):
        self.store.confirm('F1',123,'Components','graphene',4)
        self.snapshot(5,extra={'Components':[dict(Name='graphene',Count=2)]})
        self.assertEqual(self.record()['current_amount'],2)
        self.assertEqual(self.record(name='graphene')['current_amount'],2)

    def test_helper_restart_keeps_stock_and_rebases(self):
        self.snapshot(3)
        self.state.watcher.odyssey_sidecars=OdysseySidecars()
        self.tracker=OdysseyCarrierTracking(self.state)
        self.snapshot(7)
        self.assertEqual(self.record()['current_amount'],4)
        self.snapshot(3)
        self.assertEqual(self.record()['current_amount'],8)

    def test_rotation_elite_restart_and_commander_change(self):
        self.snapshot(3)
        self.path=self.root/'Journal.2026-09-15T070000.01.log'
        self.append('Commander',FID='F1')
        self.append('Location',Docked=True,StationType='FleetCarrier',MarketID=123)
        self.snapshot(7)
        self.assertEqual(self.record()['current_amount'],4)
        self.append('LoadGame',FID='F1')
        self.snapshot(1)
        self.assertEqual(self.record()['current_amount'],4)
        self.append('Commander',FID='F2')
        self.state.commander_fid='F2'
        self.snapshot(0)
        self.assertEqual(self.record()['current_amount'],4)

    def test_manual_confirmation_reanchors_and_wins(self):
        self.snapshot(3)
        self.store.confirm('F1',123,'Components','chemicalcatalyst',9)
        self.tracker.reanchor()
        self.poll()
        self.assertEqual(self.record()['current_amount'],9)
        self.snapshot(7)
        self.assertEqual(self.record()['current_amount'],5)
        self.assertEqual(self.record()['last_confirmed_amount'],9)

    def test_manual_confirmation_during_pending_snapshot_preserves_exit(self):
        self.snapshot(3,write=False)
        self.append('Undocked')
        self.poll()
        self.store.confirm('F1',123,'Components','chemicalcatalyst',9)
        self.tracker.reanchor()
        self.snapshot(7)
        self.snapshot(3)
        self.assertEqual(self.record()['current_amount'],9)

    def test_late_sidecar_and_two_fast_triggers(self):
        event=self.snapshot(3,write=False)
        self.assertEqual(self.record()['current_amount'],0)
        (self.root/'ShipLocker.json').write_text(json.dumps(event))
        self.poll()
        self.assertEqual(self.record()['current_amount'],4)
        self.snapshot(5,write=False)
        self.snapshot(7)
        self.assertEqual(self.record()['current_amount'],0) # observed endpoints: 3 -> 7, one net booking

    def test_unknown_explicit_event_blocks_transfer(self):
        self.append('NewMicroResourceAction',Name='chemicalcatalyst',Count=4)
        self.snapshot(3)
        self.assertEqual(self.record()['status'],'inconsistent')

    def test_save_failure_does_not_publish_or_advance_and_retry_is_once(self):
        before=deepcopy(self.store.load('F1',123))
        with patch.object(self.tracker.store,'save',side_effect=OSError('injected')):
            self.snapshot(3)
        self.assertEqual(self.store.load('F1',123),before)
        self.poll()
        self.assertEqual(self.record()['current_amount'],4)
        self.poll()
        self.assertEqual(self.record()['current_amount'],4)

    def test_qsettings_sync_error_restores_cached_ledger(self):
        before=deepcopy(self.store.load('F1',123))
        updated=deepcopy(before)
        updated['records']['Components/chemicalcatalyst']['current_amount']=4
        with patch.object(self.settings,'status',return_value=QSettings.Status.AccessError):
            with self.assertRaises(OSError):self.store.save('F1',123,updated)
        self.assertEqual(self.settings.value(self.store.key('F1',123)),before)

    def test_live_watcher_tracks_without_any_odyssey_view(self):
        from PySide6.QtWidgets import QApplication
        from cmdrhelper.journal_watcher import JournalWatcher
        app=QApplication.instance() or QApplication([])
        watcher=JournalWatcher()
        watcher.set_folder(self.root)
        self.state.watcher=watcher
        self.tracker=OdysseyCarrierTracking(self.state)
        watcher.odysseyTrackingUpdated.connect(self.tracker.poll)
        watcher.check_now();watcher.refresh_finished(True)
        event=self.append('ShipLocker')
        event.update(Items=[],Components=[dict(Name='chemicalcatalyst',Count=3)],Data=[],Consumables=[])
        watcher.check_now();watcher.refresh_finished(True)
        self.assertEqual(self.record()['current_amount'],0)
        (self.root/'ShipLocker.json').write_text(json.dumps(event))
        watcher.check_now()
        self.assertEqual(self.record()['current_amount'],4)
        self.state.refresh.assert_not_called()
        watcher.timer.stop()

    def test_embark_taxi_and_contradicting_market_end_the_interval(self):
        self.append('Disembark',OnStation=True,MarketID=123,Taxi=False,Multicrew=False)
        self.snapshot(3) # container redistribution is a new baseline
        self.assertEqual(self.record()['current_amount'],0)
        self.snapshot(1)
        self.assertEqual(self.record()['current_amount'],2)
        self.append('Embark',OnStation=True,MarketID=123,Taxi=True)
        self.snapshot(7)
        self.assertEqual(self.record()['current_amount'],2)
        self.append('Docked',StationType='FleetCarrier',MarketID=123)
        self.snapshot(7)
        self.append('BuyMicroResources',Name='chemicalcatalyst',Category='Component',Count=4,MarketID=456)
        self.snapshot(11)
        self.assertEqual(self.record()['current_amount'],2)

    def test_location_on_foot_requires_owned_numeric_market(self):
        self.append('Location',OnFoot=True,Docked=False,StationType='FleetCarrier',MarketID=123)
        self.snapshot(7)
        self.snapshot(3)
        self.assertEqual(self.record()['current_amount'],4)
        self.append('Location',OnFoot=True,Docked=False,StationType='FleetCarrier',MarketID=456)
        self.snapshot(7)
        self.assertEqual(self.record()['current_amount'],4)

    def test_total_20_plus_0_plus_34(self):
        reducer=OdysseyReducer(1,'F1')
        for kind in ('ShipLocker','Backpack'):
            reducer.apply(dict(event=kind,timestamp='2026-09-15T06:00:00Z',Items=[],Components=[],Consumables=[],
                               Data=[dict(Name='nocdata',Count=20)] if kind=='ShipLocker' else []), kind)
        inventory=reducer.result
        inventory.carrier_id=123
        inventory.carrier_records={'Data/nocdata':dict(current_amount=34,status='tracked')}
        self.assertEqual(material_amounts(inventory,'Data','nocdata'),(20,0,34,54))
        for status in ('unknown','inconsistent','pending'):
            inventory.carrier_records['Data/nocdata']['status']=status
            self.assertEqual(material_amounts(inventory,'Data','nocdata'),(20,0,None,None))
