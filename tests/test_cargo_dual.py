"""Two-hold presentation uses published data only; Qt callbacks are test failures."""
from copy import deepcopy
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import sys
import traceback
import unittest
from unittest.mock import patch
from PySide6.QtCore import QCoreApplication, QEvent, QSettings
from PySide6.QtWidgets import QApplication, QWidget
from shiboken6 import isValid
from cmdrhelper.i18n import set_language, _TRANSLATIONS
from cmdrhelper.mining_inventory import MiningInventory
from cmdrhelper.mining_controller import mining_publication_context
from cmdrhelper.route_planner.models import ShipLoadoutData
from cmdrhelper.ui.cargo_window_data import holds
from cmdrhelper.ui.main_window import CargoLiveWindow


class DualCargoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        set_language('de')
        self.errors = []
        self.hook = patch.object(sys, 'excepthook', lambda *e: self.errors.append(''.join(traceback.format_exception(*e))))
        self.hook.start()
        self.addCleanup(self.finish)
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.settings = QSettings(self.tmp.name+'/ui.ini', QSettings.IniFormat)
        folder = self.tmp.name
        session = dict(journal_file=folder+'/Journal.test.log', commander_id=1, fid_seen='TEST', attribution_status='identified')
        origin = dict(fid='TEST', journal=session['journal_file'], session_start='test', session_generation=1, vessel='SRV', active=True)
        self.state = NS(commander_id=1, viewed_commander_id=1, commander_fid='TEST',
            database=NS(path=folder+'/unused.db'), _journal_index_sessions=[session],
            _inventory_revisions={'mining':1}, active_srv_type='RHINO',
            ship_loadout=ShipLoadoutData(ship_id=7, ship_type='cobra', ship_name='ERFT-NOMADE',
                cargo_capacity=397, loadout_complete=True, loadout_stale=False),
            ship_cargo_context=origin, _cargo_refresh_data=({},session),
            cargo_snapshot=dict(context=dict(origin), fid='TEST', vessel='SRV', vehicle_name='RHINO',
                count=67, capacity=72, inventory=[dict(frontier_name='gold', count=67)]))
        self.inv = MiningInventory(1,'TEST',ship={'gold':200,'unlisted_cargo':50},ship_id=7,
            ship_type='cobra', source_folder=folder, vehicle_records={'Ship':dict(quality='confirmed',confirmed_at='2026-11-09T12:00:00Z')})
        self.inv.publication_context = mining_publication_context(self.state)
        self.controller = NS(_last_inventory=self.inv,_closed=False,_dirty=False,_running=False)
        self.state.mining_inventory_controller = self.controller
        self.parent = QWidget()
        self.window = CargoLiveWindow(self.settings,self.parent)
        self.addCleanup(self.destroy)

    def destroy(self):
        if isValid(self.parent):
            self.parent.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
        self.app.processEvents()

    def finish(self):
        self.hook.stop()
        self.assertEqual(self.errors,[])

    def show(self):
        self.window.present_state(self.state)
        self.app.processEvents()
        return self.window.ship_panel,self.window.srv_panel

    def test_two_independent_holds_all_symbols_and_transfer(self):
        ship,srv=self.show()
        self.assertEqual(ship.summary_label.text(),'250 / 397 t')
        self.assertEqual(srv.summary_label.text(),'67 / 72 t')
        self.assertEqual((ship.fill_bar.value(),srv.fill_bar.value()),(63,93))
        self.assertEqual(ship.table.rowCount(),2)
        self.assertIn('ERFT-NOMADE',ship.title_label.text())
        item=ship.table.item(0,0)
        self.inv.ship['gold']+=10
        self.state.cargo_snapshot['count']-=10
        self.state.cargo_snapshot['inventory'][0]['count']-=10
        self.show()
        self.assertEqual(ship.summary_label.text(),'260 / 397 t')
        self.assertEqual(srv.summary_label.text(),'57 / 72 t')
        self.assertIs(ship.table.item(0,0),item)
        self.assertNotIn('frei',ship.summary_label.text())

    def test_zero_unknown_and_invalid_capacity(self):
        self.inv.ship={}
        self.state.ship_loadout.cargo_capacity=None
        ship,_=self.show()
        self.assertEqual(ship.summary_label.text(),'0 / – t')
        self.assertTrue(ship.fill_bar.isHidden())
        self.inv.ship=None
        self.show()
        self.assertEqual(ship.summary_label.text(),'– / – t')
        self.assertEqual(ship.table.rowCount(),0)
        self.state.ship_loadout.cargo_capacity=397
        self.state.ship_loadout.loadout_complete=False
        self.show()
        self.assertEqual(ship.summary_label.text(),'– / 397 t')
        self.assertTrue(ship.quality_label.text())

    def test_stale_ship_after_srv_restart_and_stale_loadout(self):
        self.inv.vehicle_records['Ship'].update(last_confirmed=deepcopy(self.inv.ship),ship_id=7,
            ship_type='cobra',source_folder=self.tmp.name)
        self.inv.ship=None
        self.state.ship_loadout.loadout_stale=True
        ship,_=self.show()
        self.assertEqual(ship.summary_label.text(),'250 / 397 t')
        self.assertIn('2026-11-09T12:00:00Z',ship.quality_label.text())
        self.assertIn('Kapazität zuletzt bekannt',ship.quality_label.text())

    def test_tracked_quality_remains_the_mining_quality_while_pending(self):
        self.inv.vehicle_records['Ship']['quality']='tracked'
        ship,_=self.show()
        self.assertEqual(ship.quality_label.text(),'')
        self.state._inventory_revisions['mining']=2
        self.controller._dirty=True
        self.show()
        self.assertEqual(ship.quality_label.text(),'')

    def test_metadata_and_selection_do_not_refilter_published_quantities(self):
        for mutate in (lambda: setattr(self.state,'viewed_commander_id',2),
                       lambda: setattr(self.state,'commander_fid','OTHER'),
                       lambda: setattr(self.state.ship_loadout,'ship_id',9),
                       lambda: self.state._journal_index_sessions[-1].update(journal_file='/different/Journal.log')):
            before=deepcopy(self.state)
            mutate()
            self.assertEqual(holds(self.state)[0]['count'],250)
            self.state=before

    def test_no_srv_or_foreign_srv_snapshot(self):
        self.state.active_srv_type=''
        _,srv=self.show()
        self.assertEqual(srv.quality_label.text(),'Kein SRV aktiv')
        self.assertEqual(srv.summary_label.text(),'– / – t')
        self.state.active_srv_type='Scarab'
        self.show()
        self.assertEqual(srv.table.rowCount(),0)

    def test_close_reopen_geometry_and_parent_lifetime(self):
        self.show()
        self.window.resize(710,360)
        self.window.move(80,90)
        self.app.processEvents()
        self.window.close()
        self.show()
        self.assertFalse(self.window.isVisible())
        self.window.show()
        self.assertTrue(self.window.isVisible())
        geometry=self.window.size()
        restored=CargoLiveWindow(self.settings,self.parent)
        self.assertEqual(restored.size(),geometry)
        restored.close()
        self.destroy()
        self.assertFalse(isValid(self.window))

    def test_translations(self):
        for table in _TRANSLATIONS.values():
            for key in ('cargo.live.holds','cargo.live.no_srv','cargo.live.capacity_stale'):
                self.assertTrue(table[key])

    def test_real_signal_signatures_update_and_disconnect_with_host(self):
        from PySide6.QtCore import QObject, Signal
        from cmdrhelper.ui.main_window import MainWindow
        class State(QObject):
            cargoSnapshotChanged = Signal(object)
            shipLoadoutChanged = Signal(object)
            commanderIdentityChanged = Signal(object,str,str)
            viewedCommanderChanged = Signal(object)
        class Controller(QObject):
            ready = Signal(object)
            loading = Signal()
            publicationChanged = Signal()
        class Sources(QObject):
            changed = Signal()
        class Host(QWidget):
            _cargo_mining_ready = MainWindow._cargo_mining_ready
            _cargo_mining_loading = MainWindow._cargo_mining_loading
            _connect_cargo_live_signals = MainWindow._connect_cargo_live_signals
            _refresh_cargo_live_window = MainWindow._refresh_cargo_live_window
            _refresh_cargo_holds = MainWindow._refresh_cargo_holds
            _cargo_live_window_enabled = MainWindow._cargo_live_window_enabled
        state=State()
        for key,value in vars(self.state).items():
            setattr(state,key,value)
        state.settings=self.settings
        self.settings.setValue('cargo_live/enabled',True)
        controller=Controller()
        for key,value in vars(self.controller).items():
            setattr(controller,key,value)
        state.mining_inventory_controller=controller
        state.sources=Sources()
        state._source_live_context=True
        host=Host(self.parent)
        host.state=state
        host._cargo_live_window=None
        host._navigation_hud=None
        host._connect_cargo_live_signals()
        controller.ready.emit(self.inv)
        window=host._cargo_live_window
        self.assertEqual(window.ship_panel.summary_label.text(),'250 / 397 t')
        controller._dirty=True
        controller.publicationChanged.emit()
        self.assertEqual(window.ship_panel.quality_label.text(),'')
        controller._last_inventory=None
        controller.loading.emit()
        self.assertEqual(window.ship_panel.table.rowCount(),0)
        controller._last_inventory=self.inv
        controller.ready.emit(self.inv)
        controller._dirty=False
        state.ship_loadout.cargo_capacity=400
        state.shipLoadoutChanged.emit(state.ship_loadout)
        self.assertEqual(window.ship_panel.summary_label.text(),'250 / 400 t')
        state.cargo_snapshot['count']=0
        state.cargo_snapshot['inventory']=[]
        state.cargoSnapshotChanged.emit(state.cargo_snapshot)
        self.assertEqual(window.srv_panel.summary_label.text(),'0 / 72 t')
        state.viewed_commander_id=2
        state.viewedCommanderChanged.emit(2)
        self.assertEqual(window.ship_panel.table.rowCount(),2)
        controller.loading.emit()
        self.assertEqual(window.ship_panel.table.rowCount(),0)
        controller.ready.emit(self.inv)
        state.viewed_commander_id=1
        state.commanderIdentityChanged.emit(1,'TEST','Test')
        self.assertEqual(window.ship_panel.table.rowCount(),2)
        state._source_live_context=False
        state.sources.changed.emit()
        # Mining's published ship stock does not require a live SRV context.
        self.assertEqual(window.ship_panel.table.rowCount(),2)
        self.assertEqual(window.srv_panel.table.rowCount(),0)
        self.destroy()
        controller.ready.emit(self.inv)
        state.cargoSnapshotChanged.emit(None)
        self.app.processEvents()
        self.assertFalse(isValid(window))

    def test_repeated_window_destruction_and_invalid_amount(self):
        for _ in range(10):
            owner=QWidget()
            window=CargoLiveWindow(self.settings,owner)
            window.present_state(self.state)
            window.srv_panel.set_snapshot(dict(count=-1,capacity=72))
            self.assertEqual(window.srv_panel.summary_label.text(),'– / 72 t')
            self.assertTrue(window.srv_panel.fill_bar.isHidden())
            owner.deleteLater()
            QCoreApplication.sendPostedEvents(None,QEvent.DeferredDelete)
            self.app.processEvents()
            self.assertFalse(isValid(window))

    def test_live_palladium_stale_without_current_loadout(self):
        self.inv.ship=None
        self.inv.srv={'palladium':12,'thorium':11}
        self.inv.vehicle_records['Ship'].update(last_confirmed={'palladium':81},
            ship_id=7,ship_type='cobra',source_folder=self.tmp.name)
        self.state.cargo_snapshot.update(count=23,inventory=[
            dict(frontier_name='palladium',count=12),dict(frontier_name='thorium',count=11)])
        for loadout in (None,ShipLoadoutData(),ShipLoadoutData(ship_id=7)):
            with self.subTest(loadout=loadout):
                self.state.ship_loadout=loadout
                self.assertEqual(self.inv.displayed_stock('Ship','palladium'),(81,'stale'))
                ship,srv=self.show()
                self.assertEqual(ship.summary_label.text(),'81 / – t')
                self.assertEqual(ship.table.item(0,0).text(),'Palladium')
                self.assertEqual(ship.table.item(0,1).text(),'81 t')
                self.assertTrue(ship.quality_label.text())
                self.assertEqual(srv.summary_label.text(),'23 / 72 t')
                self.assertEqual([srv.table.item(i,1).text() for i in range(2)],['12 t','11 t'])
                self.window.close(); self.window.show(); self.show()
                self.assertEqual(ship.table.item(0,1).text(),'81 t')

    def test_stock_quality_without_loadout_and_matching_known_capacity(self):
        for quality in ('confirmed','tracked','unknown'):
            with self.subTest(quality=quality):
                self.inv.vehicle_records['Ship']['quality']=quality
                self.state.ship_loadout=None
                ship,_=self.show()
                self.assertEqual(ship.summary_label.text(),'250 / – t')
        self.inv.vehicle_records['Ship']['quality']='confirmed'
        self.state.ship_loadout=ShipLoadoutData(ship_id=7,cargo_capacity=397)
        ship,_=self.show()
        self.assertEqual(ship.summary_label.text(),'250 / 397 t')
        self.assertTrue(ship.quality_label.text())

    def test_publication_metadata_does_not_override_the_mining_projection(self):
        self.state.ship_loadout=None
        self.state._journal_index_sessions[-1]['journal_file']=self.tmp.name+'/Journal.new.log'
        ship,_=self.show()
        self.assertEqual(ship.summary_label.text(),'250 / – t')
        self.inv.publication_context=(2,'OTHER')+self.inv.publication_context[2:]
        self.show()
        self.assertEqual(ship.table.rowCount(),2)

    def test_mining_table_and_open_cargo_receive_identical_ready_payload(self):
        from PySide6.QtCore import QObject, Signal
        from cmdrhelper.ui.main_window import MainWindow
        from cmdrhelper.ui.mining_view import MiningView
        class Controller(QObject):
            ready=Signal(object)
            loading=Signal()
            refreshFinished=Signal(str)
            publicationChanged=Signal()
            _last_inventory=None
        class Host(QWidget):
            _cargo_mining_ready=MainWindow._cargo_mining_ready
            _cargo_mining_loading=MainWindow._cargo_mining_loading
            _connect_cargo_live_signals=MainWindow._connect_cargo_live_signals
            _refresh_cargo_live_window=MainWindow._refresh_cargo_live_window
            _refresh_cargo_holds=MainWindow._refresh_cargo_holds
            _cargo_live_window_enabled=MainWindow._cargo_live_window_enabled
        controller=Controller()
        mining=MiningView(self.settings,controller=controller)
        mining.setParent(self.parent)
        host=Host(self.parent)
        host.state=self.state
        host.state.settings=self.settings
        host.material_view=NS(mining=mining)
        host._cargo_live_window=None
        host._navigation_hud=None
        self.settings.setValue('cargo_live/enabled',True)
        host._connect_cargo_live_signals()
        host._refresh_cargo_holds()
        window=host._cargo_live_window
        window.show()
        self.state.ship_loadout=None
        self.inv.ship=None
        self.inv.vehicle_records['Ship'].update(last_confirmed={'palladium':81},
            ship_id=7,ship_type='cobra',source_folder=self.tmp.name)
        # Deliberately inconsistent metadata: Mining's displayed_stock is authoritative.
        self.inv.publication_context=None
        self.state.commander_fid='other selection pending'
        for quality in ('stale','confirmed','tracked','unknown'):
            with self.subTest(quality=quality):
                self.inv.ship=None if quality=='stale' else {'palladium':81}
                self.inv.vehicle_records['Ship']['quality']=quality
                controller.ready.emit(self.inv)
                self.app.processEvents()
                self.assertIs(mining._inventory,self.inv)
                self.assertIs(host._cargo_mining_inventory,mining._inventory)
                self.assertIn('81',mining.items['palladium'].text(2))
                self.assertEqual(window.ship_panel.table.item(0,1).text(),'81 t')
                self.assertEqual(window.ship_panel.summary_label.text(),'81 / – t')
        self.inv.ship={'palladium':92}
        controller.ready.emit(self.inv)
        self.assertEqual(window.ship_panel.table.item(0,1).text(),'92 t')
        self.assertIn('92',mining.items['palladium'].text(2))
        window.close(); window.show()
        self.assertEqual(window.ship_panel.table.item(0,1).text(),'92 t')
        controller.loading.emit()
        self.assertEqual(window.ship_panel.table.rowCount(),0)
        self.assertEqual(mining._inventory.displayed_stock('Ship','palladium'),(None,'unknown'))
        controller.ready.emit(self.inv)
        self.assertEqual(window.ship_panel.table.item(0,1).text(),'92 t')
        self.destroy()
        controller.ready.emit(self.inv)
        self.app.processEvents()
