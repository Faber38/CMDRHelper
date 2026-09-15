"""Focused regression for personal sidecars; no carrier transfer inference."""
import json
from pathlib import Path
import sqlite3
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from PySide6.QtCore import QSettings, Signal
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit

from cmdrhelper.odyssey_inventory import OdysseyInventoryReader
from cmdrhelper.odyssey_sidecars import OdysseySidecars, read_snapshot
from cmdrhelper.odyssey_controller import OdysseyController
from cmdrhelper.journal_watcher import JournalWatcher
from cmdrhelper.ui.odyssey_view import OdysseyView
from test_material_view import State
from test_odyssey_inventory import event, item, snapshot


class LiveState(State):
    odysseySidecarsChanged = Signal()


class SidecarTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.path = self.folder/'Journal.2026-09-08T145800.01.log'
        self.path.write_text(json.dumps(event('Commander',FID='F1'))+'\n')
        self.sessions = [self.session(self.path)]
        self.capture = OdysseySidecars()
        self.reader = OdysseyInventoryReader()

    @staticmethod
    def session(path, fid='F1', cid=1):
        return dict(journal_file=str(path),commander_id=cid,fid_seen=fid,attribution_status='identified')

    def append(self,*events):
        with self.path.open('a') as stream:
            for e in events:
                stream.write(json.dumps(e)+'\n')

    def sidecar(self, kind, second, **categories):
        value = snapshot(kind,second,**categories)
        (self.folder/(kind+'.json')).write_text(json.dumps(value))
        return value

    def read(self, **options):
        self.capture.poll(self.path)
        return self.reader.reconstruct(1,'F1',self.sessions,sidecars=self.capture.export(),**options)

    def initial(self):
        self.append(snapshot('ShipLocker',1,Components=[item('chemicalcatalyst',7)]),snapshot('Backpack',1))

    def test_real_transfer_7_3_7_and_data_44_with_empty_backpack(self):
        self.initial()
        self.assertEqual(self.read().count('chemicalcatalyst','ShipLocker'),7)
        for second, amount in ((2,3),(3,7)):
            self.append(event('ShipLocker',second),event('Backpack',second))
            self.sidecar('ShipLocker',second,Components=[item('chemicalcatalyst',amount)],
                         Data=[item('chemicalexperimentdata',44)])
            self.sidecar('Backpack',second)
            result = self.read()
            self.assertEqual(result.count('chemicalcatalyst','ShipLocker'),amount)
            self.assertEqual(result.count('chemicalexperimentdata','ShipLocker'),44)
            self.assertEqual(result.count('chemicalexperimentdata','Backpack'),0)
            self.assertTrue(result.known)

    def test_delayed_write_then_fast_second_trigger_and_ambiguous_same_second(self):
        self.initial()
        self.read()
        self.append(event('ShipLocker',2))
        pending = self.read().containers['ShipLocker']
        self.assertTrue(pending.valid)
        self.assertEqual(pending.awaiting_snapshot,event('ShipLocker',2)['timestamp'])
        self.assertEqual(sum(s.count for s in pending.stacks.values()),7)
        (self.folder/'ShipLocker.json').write_text('{"event":"ShipLocker"')
        self.assertIsNone(self.read().count('chemicalcatalyst','ShipLocker'))
        self.sidecar('ShipLocker',2,Components=[item('chemicalcatalyst',3)])
        self.capture.poll(self.path)
        # A completed sidecar uses the cached journal plan without historical I/O.
        with patch.object(self.reader,'_signature',side_effect=AssertionError('historical scan')):
            result=self.reader.reconstruct(1,'F1',self.sessions,sidecars=self.capture.export(),sidecar_only=True)
        self.assertEqual(result.count('chemicalcatalyst','ShipLocker'),3)
        self.append(event('ShipLocker',3),event('ShipLocker',4))
        self.sidecar('ShipLocker',3,Components=[item('chemicalcatalyst',99)])
        self.assertIsNone(self.read().count('chemicalcatalyst','ShipLocker'))
        self.sidecar('ShipLocker',4,Components=[item('chemicalcatalyst',7)])
        self.assertEqual(self.read().count('chemicalcatalyst','ShipLocker'),7)
        self.append(event('ShipLocker',5),event('ShipLocker',5))
        self.sidecar('ShipLocker',5,Components=[item('chemicalcatalyst',9)])
        self.assertIsNone(self.read().count('chemicalcatalyst','ShipLocker'))

    def test_invalid_snapshots_missing_files_and_known_empty_backpack(self):
        self.append(event('ShipLocker',1),event('Backpack',1))
        self.assertIsNone(self.read().count('graphene','Backpack'))
        good=snapshot('Backpack',1)
        invalid=[{},dict(good,event='ShipLocker'),dict(good,timestamp='bad'),
                 {k:v for k,v in good.items() if k!='Data'},dict(good,Data={}),
                 dict(good,Components=[item('graphene',True)]),
                 dict(good,Components=[item('graphene',-1)]),
                 dict(good,Components=[item('graphene',1.5)]),
                 dict(good,Data=[item('graphene',1)]),
                 dict(good,Data=[item('bad name',1)]),
                 dict(good,Data=[item('chemicalexperimentdata',1,Category='Component')])]
        path=self.folder/'Backpack.json'
        for value in invalid:
            with self.subTest(value=value):
                path.write_text(json.dumps(value))
                with self.assertRaises(ValueError): read_snapshot(path,'Backpack')
                self.assertIsNone(self.read().count('graphene','Backpack'))
        self.sidecar('Backpack',1)
        self.assertEqual(self.read().count('graphene','Backpack'),0)

    def test_signature_change_during_read_rejected_and_retried(self):
        self.append(event('ShipLocker',1))
        self.sidecar('ShipLocker',1,Components=[item('chemicalcatalyst',3)])
        original=Path.read_bytes
        def changing(path):
            raw=original(path)
            path.write_bytes(raw+b' ')
            return raw
        with patch.object(Path,'read_bytes',changing):
            self.capture.poll(self.path)
            self.assertEqual(self.capture.export()['snapshots'],[])
        self.assertEqual(self.read().count('chemicalcatalyst','ShipLocker'),3)

    def test_startup_rotation_commander_identity_and_journal_witness(self):
        self.append(event('ShipLocker',1),event('Backpack',1))
        self.sidecar('ShipLocker',1,Data=[item('chemicalexperimentdata',44)])
        self.sidecar('Backpack',1)
        self.assertEqual(self.read().count('chemicalexperimentdata','ShipLocker'),44)
        evidence=self.capture.export()
        original=self.path.read_text()
        self.path.write_text(original.replace('Commander','LoadGame',1))
        # A matching timestamp alone is insufficient after journal replacement.
        result=self.reader.reconstruct(1,'F1',self.sessions,sidecars=evidence)
        self.assertIsNone(result.count('chemicalexperimentdata','ShipLocker'))
        self.read()  # recapture the stable new prefix
        self.path=self.folder/'Journal.2026-09-08T145810.01.log'
        self.path.write_text(json.dumps(event('Fileheader',10))+'\n')
        self.capture.poll(self.path)
        self.assertIsNone(self.capture.export()['fid'])
        self.append(event('Commander',11,FID='F1'))
        self.sessions.append(self.session(self.path))
        self.assertEqual(self.read().count('chemicalexperimentdata','ShipLocker'),44)
        self.path=self.folder/'Journal.2026-09-08T145820.01.log'
        self.path.write_text(json.dumps(event('Commander',20,FID='F2'))+'\n'+json.dumps(event('ShipLocker',21))+'\n')
        self.capture.poll(self.path)
        self.assertEqual(self.capture.export()['snapshots'],[])
        result=self.reader.reconstruct(2,'F2',[self.session(self.path,'F2',2)],sidecars=self.capture.export())
        self.assertIsNone(result.count('chemicalexperimentdata','ShipLocker'))

    def test_journal_grows_while_sidecar_is_read(self):
        self.append(event('ShipLocker',1))
        self.sidecar('ShipLocker',1,Components=[item('chemicalcatalyst',3)])
        original=Path.read_bytes
        def append_trigger(path):
            raw=original(path)
            self.append(event('ShipLocker',2))
            return raw
        with patch.object(Path,'read_bytes',append_trigger):
            self.capture.poll(self.path)
        self.assertEqual(self.capture.export()['snapshots'],[])
        self.sidecar('ShipLocker',2,Components=[item('chemicalcatalyst',7)])
        self.assertEqual(self.read().count('chemicalcatalyst','ShipLocker'),7)

    def test_capture_before_lazy_view_and_late_update_without_global_refresh(self):
        app=QApplication.instance() or QApplication([])
        self.append(event('ShipLocker',1),event('Backpack',1))
        self.sidecar('ShipLocker',1,Data=[item('chemicalexperimentdata',44)])
        self.sidecar('Backpack',1)
        watcher=JournalWatcher()
        watcher.set_folder(self.folder)
        notifications=[]
        watcher.journalChanged.connect(lambda:notifications.append(True))
        watcher.check_now();watcher.refresh_finished(True)
        self.assertEqual(len(watcher.odyssey_sidecars.export()['snapshots']),2)
        state=LiveState()
        state.watcher=watcher
        state.commander_id=state.viewed_commander_id=1
        state.commander_fid='F1'
        state.settings=QSettings(str(self.folder/'settings.ini'),QSettings.IniFormat)
        state.refresh=Mock(side_effect=AssertionError('global refresh'))
        state.database=SimpleNamespace(path=self.folder/'test.db')
        with sqlite3.connect(state.database.path) as con:
            con.execute('CREATE TABLE commanders(id INTEGER, fid TEXT, current_name TEXT)')
            con.execute('INSERT INTO commanders VALUES(1,"F1","Test")')
            con.execute('CREATE TABLE commander_carriers(commander_id INTEGER, carrier_id INTEGER)')
            con.execute('INSERT INTO commander_carriers VALUES(1,123)')
            con.execute('CREATE TABLE journal_sessions(commander_id INTEGER, fid_seen TEXT, journal_file TEXT, attribution_status TEXT)')
            con.execute('INSERT INTO journal_sessions VALUES(1,"F1",?,"identified")',(str(self.path),))
        watcher.odysseySidecarsChanged.connect(state.odysseySidecarsChanged.emit)
        watcher.journalChanged.connect(state.changed.emit)
        controller=OdysseyController(state)
        view=OdysseyView(state,QLineEdit(),controller=controller)
        def cleanup():
            controller.timer.stop();controller.pool.waitForDone();app.processEvents()
            controller.timer.stop();view.close();controller.deleteLater();app.processEvents()
        self.addCleanup(cleanup)
        def wait(predicate):
            deadline=time.monotonic()+5
            while not predicate() and time.monotonic()<deadline: QTest.qWait(10)
            self.assertTrue(predicate())
        wait(lambda:view.inventory.known)
        view.tabs.setCurrentIndex(2)
        row=lambda:next(v for k,v in view.items.items() if k.name=='chemicalexperimentdata')
        self.assertEqual([row().text(i) for i in (1,2,3,4)],['44','0','—','—'])
        controller.confirm_carrier('Data','chemicalexperimentdata',6,(1,'F1',123))
        self.assertEqual(row().text(4),'50')
        saved=state.settings.value(controller.carrier_store.key('F1',123))
        self.append(event('ShipLocker',2),event('Backpack',2))
        watcher.check_now();watcher.refresh_finished(True)
        wait(lambda:view.inventory.containers['ShipLocker'].awaiting_snapshot is not None)
        count=len(notifications)
        self.sidecar('ShipLocker',2,Data=[item('chemicalexperimentdata',45)])
        self.sidecar('Backpack',2)
        watcher.check_now()
        wait(lambda:view.inventory.count('chemicalexperimentdata','ShipLocker')==45)
        self.assertEqual(len(notifications),count)
        self.assertEqual(row().text(4),'51')
        self.assertEqual(view._capacity.known_amount,6)
        self.assertEqual(state.settings.value(controller.carrier_store.key('F1',123)),saved)
        state.refresh.assert_not_called()
