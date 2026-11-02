"""Isolated Qt shutdown regressions; no live journals, credentials or network."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtCore import QObject, Signal, QSettings, QTimer, QRunnable, QThreadPool, Qt
from PySide6.QtGui import QFont, QKeyEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFormLayout, QLineEdit,
                              QCheckBox, QComboBox, QFontComboBox, QSpinBox, QLabel,
                              QPushButton, QDialog, QDialogButtonBox)
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.exit_controller import ExitController, ExitDialog, remember
from cmdrhelper.exit_tasks import submit, task_gate, start_thread
from cmdrhelper.global_hotkey import GlobalHotkey
from cmdrhelper.shortcuts import ShortcutManager
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language
from qt_widget_cleanup import destroy_widget


class Signals(QObject):
    done = Signal()


class Work(QRunnable):
    def __init__(self, entered, release, action=lambda: None):
        super().__init__()
        self.entered, self.release, self.action = entered, release, action
        self.signals = Signals()

    def run(self):
        self.entered.set()
        self.release.wait(5)
        self.action()
        self.signals.done.emit()


class SafeExitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.settings = QSettings(str(self.root/'settings.ini'), QSettings.IniFormat)
        self.gate = task_gate()
        self.gate.resume()
        self.w = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(self.w)
        self.w.state = SimpleNamespace(settings=self.settings, commander_fid='SYNTHETIC')
        self.backend = Mock()
        self.hotkey = GlobalHotkey(self.settings, backend_factory=lambda callback: self.backend)
        self.w._quick_favorite_hotkey = self.hotkey
        self.w.shortcut_manager = ShortcutManager(self.w, self.settings, self.hotkey, {'quit':self.w.close})
        self.w.shortcut_manager.load()
        self.button = QPushButton('Exit')
        self.button.clicked.connect(self.w.close)
        self.w.setCentralWidget(self.button)
        self.w.show(); self.w.activateWindow(); self.button.setFocus()
        QTest.qWait(30)
        self.releases = []
        self.addCleanup(self.cleanup)

    def cleanup(self):
        for release in self.releases: release.set()
        if self.gate.failures:
            self.w._exit_controller.cancel()
        self.wait(lambda:not self.gate.pending())
        c = getattr(self.w, '_exit_controller', None)
        if c and not c.approved:
            c.cancel()
            self.wait(lambda:c.phase == 'idle')
        self.hotkey.close()
        destroy_widget(self.w, close=False)
        self.gate.resume()
        self.tmp.cleanup()

    def wait(self, condition, timeout=4000):
        until=time.monotonic()+timeout/1000
        while not condition() and time.monotonic()<until:QTest.qWait(10)
        self.assertTrue(condition(), 'condition did not become true')

    def form(self):
        page=QWidget(); layout=QFormLayout(page)
        for service in ('edsm','inara'):
            combo=QComboBox();combo.addItem('Synthetic','SYNTHETIC')
            setattr(self.w,service+'_commander_combo',combo);layout.addRow(combo)
            for name in ('commander_edit','api_key_edit'):
                field=QLineEdit('saved');setattr(self.w,service+'_'+name,field);layout.addRow(field)
            check=QCheckBox();setattr(self.w,service+'_enabled_check',check);layout.addRow(check)
        self.w.edsm_receive_check=QCheckBox();layout.addRow(self.w.edsm_receive_check)
        self.w.ui_language_combo=QComboBox();self.w.ui_language_combo.addItem('Deutsch','de');self.w.ui_language_combo.addItem('English','en')
        layout.addRow(self.w.ui_language_combo)
        self.w.ui_font_combo=QFontComboBox();layout.addRow(self.w.ui_font_combo)
        self.w.ui_font_size_spin=QSpinBox();self.w.ui_font_size_spin.setValue(12);layout.addRow(self.w.ui_font_size_spin)
        self.w.ui_font_status=QLabel(self.w);self.w.ui_language_status=QLabel(self.w)
        self.w._edsm_system_status=Mock()
        self.w._load_selected_edsm_settings=Mock();self.w._load_selected_inara_settings=Mock()
        self.w.state.refresh=Mock()
        def save(service,**values):
            for key,value in values.items():self.settings.setValue(service+'/'+key,value)
        self.w.state.set_edsm_settings=lambda **v:save('edsm',**v)
        self.w.state.set_inara_settings=lambda **v:save('inara',**v)
        self.button=QPushButton('Exit');self.button.clicked.connect(self.w.close);layout.addRow(self.button)
        self.w.setCentralWidget(page);remember(self.w)
        self.addCleanup(set_language,get_language())

    def work(self, action=lambda:None):
        entered,release=threading.Event(),threading.Event();self.releases.append(release)
        job=Work(entered,release,action);submit(QThreadPool.globalInstance(),job)
        self.assertTrue(entered.wait(2))
        return job,release

    def test_no_work_no_dialog_and_geometry_saved(self):
        self.assertTrue(self.w.close())
        self.assertFalse(self.w.isVisible())
        self.assertIsNone(self.w._exit_controller.dialog)
        self.assertTrue(self.settings.contains('main_window/geometry'))

    def test_focus_change_cancel_keeps_draft_then_discard(self):
        self.form();self.w.edsm_api_key_edit.setText('draft')
        self.button.setFocus();self.button.click()
        c=self.w._exit_controller
        self.assertEqual(c.phase,'drafts');c.dialog.reject()
        self.assertTrue(self.w.isVisible());self.assertEqual(self.w.edsm_api_key_edit.text(),'draft')
        self.assertEqual(c.phase,'idle');self.button.click()
        c.dialog.buttons.button(QDialogButtonBox.Discard).click()
        self.assertFalse(self.w.isVisible());self.assertFalse(self.settings.contains('edsm/api_key'))

    def test_save_uses_existing_routines_and_saved_restart_settings_are_clean(self):
        self.form();self.w.edsm_api_key_edit.setText('draft');self.w.ui_language_combo.setCurrentIndex(1)
        self.w.ui_font_size_spin.setValue(15);self.w.close()
        self.w._exit_controller.dialog.buttons.button(QDialogButtonBox.Save).click()
        self.assertFalse(self.w.isVisible());self.assertEqual(self.settings.value('edsm/api_key'),'draft')
        self.assertEqual(self.settings.value('ui_font_size'),15)
        self.assertEqual(self.settings.value('ui_language'),'en')
        self.assertEqual(self.w._exit_controller.dirty(),[])

    def test_save_failure_and_validation_failure_never_close(self):
        self.form();self.w.edsm_api_key_edit.setText('draft');self.w.close();c=self.w._exit_controller
        with patch.object(self.w.state,'set_edsm_settings',side_effect=OSError('synthetic')):
            c.save()
        self.assertTrue(self.w.isVisible());self.assertEqual(c.phase,'drafts');self.assertIn('edsm',c.dirty())
        self.w.edsm_commander_combo.clear();self.w.state.commander_fid=''
        c.save();self.assertTrue(self.w.isVisible());self.assertEqual(c.phase,'drafts')

    def test_saved_font_and_language_do_not_prompt(self):
        self.form();self.w.edsm_api_key_edit.setText('saved  ')
        self.w.ui_font_size_spin.setValue(15);self.w._save_ui_font_settings()
        self.w.ui_language_combo.setCurrentIndex(1);self.w._save_ui_language_settings()
        self.assertTrue(self.w.close());self.assertIsNone(self.w._exit_controller.dialog)

    def test_wait_keeps_gui_alive_and_applies_result_before_close(self):
        job,release=self.work();applied=[]
        job.signals.done.connect(lambda:applied.append(True),Qt.QueuedConnection)
        heartbeat=[];timer=QTimer();timer.timeout.connect(lambda:heartbeat.append(True));timer.start(10)
        try:
            self.assertFalse(self.w.close());c=self.w._exit_controller
            QTest.qWait(80);self.assertTrue(self.w.isVisible());self.assertGreater(len(heartbeat),2)
            for _ in range(4):self.button.click()
            self.assertIs(c,self.w._exit_controller)
            release.set();self.wait(lambda:not self.w.isVisible());self.assertEqual(applied,[True])
        finally:timer.stop()

    def test_cancel_wait_resumes_admission_and_does_not_duplicate_results(self):
        job,release=self.work();self.w.close();c=self.w._exit_controller
        entered2,release2=threading.Event(),threading.Event();self.releases.append(release2)
        next_job=Work(entered2,release2)
        submit(QThreadPool.globalInstance(),next_job)
        self.assertFalse(entered2.is_set())
        c.cancel();self.assertEqual(c.phase,'idle');self.assertTrue(self.w.isVisible())
        self.assertTrue(entered2.wait(2));release.set();release2.set()
        self.wait(lambda:not self.gate.pending());self.assertTrue(self.w.close())

    def test_python_transaction_worker_must_really_finish(self):
        import sqlite3
        db=self.root/'test.sqlite'
        with sqlite3.connect(db) as con:con.execute('create table evidence(value text)')
        entered,release=threading.Event(),threading.Event();self.releases.append(release)
        def write():
            with sqlite3.connect(db) as con:
                con.execute("insert into evidence values ('accepted')");entered.set();release.wait(3)
        start_thread(threading.Thread(target=write,daemon=True))
        self.assertTrue(entered.wait(2));self.w.close();QTest.qWait(60);self.assertTrue(self.w.isVisible())
        release.set();self.wait(lambda:not self.w.isVisible())
        with sqlite3.connect(db) as con:self.assertEqual(con.execute('select * from evidence').fetchall(),[('accepted',)])

    def test_mining_queued_checkpoint_is_saved_once_before_close(self):
        from cmdrhelper.mining_controller import MiningInventoryController
        from cmdrhelper.mining_inventory import MiningInventory
        c=MiningInventoryController(self.w.state)
        self.w.state.mining_inventory_controller=c
        self.app.processEvents();c.timer.stop();c._dirty=False
        c._running=True
        inventory=MiningInventory(7,'SYNTHETIC');inventory.checkpoints={'synthetic':'checkpoint'}
        entered,release=threading.Event(),threading.Event();self.releases.append(release)
        job=Work(entered,release,lambda:c.results.ready.emit(c._generation,inventory))
        submit(c.pool,job,essential=True);self.assertTrue(entered.wait(2))
        applied=[];c.ready.connect(lambda i:applied.append(i))
        self.w.close();QTest.qWait(60);self.assertFalse(c._closed)
        release.set();self.wait(lambda:not self.w.isVisible())
        self.assertEqual(self.settings.value('materials/mining/cargo_checkpoints/7'),inventory.checkpoints)
        self.assertEqual(applied,[inventory]);c.close();self.assertEqual(applied,[inventory])

    def test_quit_shortcut_in_own_dialog_never_discards_and_tracks_new_binding(self):
        self.form();self.w.edsm_api_key_edit.setText('draft');self.button.setFocus()
        manager=self.w.shortcut_manager;self.assertTrue(manager.set_binding('quit','Ctrl+Q'))
        self.w.activateWindow();QTest.qWait(30);QTest.keyClick(self.button,Qt.Key_Q,Qt.ControlModifier)
        c=self.w._exit_controller;dialog=c.dialog;dialog.activateWindow();QTest.qWait(30)
        QTest.keyClick(dialog,Qt.Key_Q,Qt.ControlModifier)
        self.assertIs(c.dialog,dialog);self.assertEqual(c.phase,'drafts');self.assertEqual(self.w.edsm_api_key_edit.text(),'draft')
        self.assertTrue(manager.set_binding('quit','Ctrl+F8'))
        self.assertEqual(dialog.shortcut.key().toString(),'Ctrl+F8')
        for _ in range(3):QTest.keyClick(dialog,Qt.Key_F8,Qt.ControlModifier)
        self.app.sendEvent(dialog,QKeyEvent(QKeyEvent.KeyPress,Qt.Key_F8,Qt.ControlModifier,'',True))
        self.assertEqual(c.phase,'drafts');self.assertFalse(self.settings.contains('edsm/api_key'))
        self.assertEqual(len([d for d in self.w.findChildren(ExitDialog) if d.isVisible()]),1)

    def test_other_modal_dialog_protects_close_and_quit_shortcut(self):
        self.assertTrue(self.w.shortcut_manager.set_binding('quit','Ctrl+Q'))
        other=QDialog(self.w);other.setWindowModality(Qt.WindowModal);other.show();other.activateWindow();QTest.qWait(30)
        try:
            QTest.keyClick(other,Qt.Key_Q,Qt.ControlModifier)
            self.assertTrue(other.isVisible());self.assertTrue(self.w.isVisible())
            self.assertFalse(self.w.close());self.assertIsNone(self.w._exit_controller.dialog)
        finally:other.close()

    def test_wait_dialog_repeated_shortcut_cannot_skip_running_worker(self):
        self.assertTrue(self.w.shortcut_manager.set_binding('quit','Ctrl+Q'))
        job,release=self.work();self.w.close();c=self.w._exit_controller
        c.dialog.activateWindow();QTest.qWait(30)
        for _ in range(3):QTest.keyClick(c.dialog,Qt.Key_Q,Qt.ControlModifier)
        self.assertTrue(self.w.isVisible());release.set();self.wait(lambda:not self.w.isVisible())

    def test_all_languages_and_themes(self):
        from cmdrhelper.ui.styles import DARK_STYLESHEET,LIGHT_STYLESHEET
        self.addCleanup(set_language,get_language());self.addCleanup(self.app.setStyleSheet,self.app.styleSheet())
        c=ExitController(self.w)
        for language,strings in _TRANSLATIONS.items():
            set_language(language)
            for key in ('title','unsaved','choose','save','discard','cancel','wait','wait_count','wait_long','save_failed','write_failed','resuming','shortcut_help'):
                self.assertTrue(strings['exit.'+key])
            for style in (DARK_STYLESHEET,LIGHT_STYLESHEET):
                self.app.setStyleSheet(style);dialog=ExitDialog(c,True);dialog.show();self.app.processEvents()
                self.assertTrue(dialog.buttons.button(QDialogButtonBox.Save).isEnabled())
                dialog.hide();dialog.deleteLater()

    def test_market_queue_commits_before_exit_without_blocking_gui(self):
        from cmdrhelper.market_writer import MarketWriteWorker
        from cmdrhelper.market_store import MarketStore
        from cmdrhelper.observed_market_observer import ObservedMarketObserver
        from test_market_store import observation, NOW
        worker=MarketWriteWorker(self.root/'legacy.json',self.root/'markets.db',clock=lambda:NOW)
        self.addCleanup(worker.close)
        worker.ready.result(timeout=3)
        observer=ObservedMarketObserver();observer.writer=worker;self.w.state.observed_markets=observer
        entered,release=threading.Event(),threading.Event();self.releases.append(release)
        original=MarketStore.record_observation
        def blocked(store,value,**kwargs):
            entered.set();release.wait(3);return original(store,value,**kwargs)
        with patch.object(MarketStore,'record_observation',blocked):
            first=worker.record(observation());second=worker.record(observation(mid=2))
            self.assertTrue(entered.wait(2));self.w.close();QTest.qWait(60)
            self.assertTrue(self.w.isVisible());self.assertFalse(first.done());release.set()
            self.wait(lambda:not self.w.isVisible())
        self.assertTrue(first.result().inserted);self.assertTrue(second.result().inserted)
        self.assertTrue(worker.is_stopped())
        with MarketStore(self.root/'markets.db',read_only=True,clock=lambda:NOW) as db:
            self.assertEqual(db.get_stats().current_markets,2)

    def test_delayed_route_request_cancels_polling_but_waits_for_response(self):
        from cmdrhelper.route_planner.spansh_client import SpanshFleetCarrierClient
        from cmdrhelper.route_planner.workers import CarrierRouteWorker
        client=SpanshFleetCarrierClient(poll_interval=10)
        entered,release=threading.Event(),threading.Event();self.releases.append(release)
        calls=[]
        def response(*args,**kwargs):
            calls.append(True);entered.set();release.wait(3);return {'state':'queued'}
        client.calculate=lambda request:client._poll('synthetic')
        request=SimpleNamespace(validation_error=lambda:None)
        job=CarrierRouteWorker(request,client)
        with patch.object(client,'_request_json',side_effect=response):
            submit(QThreadPool.globalInstance(),job);self.assertTrue(entered.wait(2))
            self.w.close();QTest.qWait(60)
            self.assertTrue(client.cancelled.is_set());self.assertTrue(self.w.isVisible())
            release.set();self.wait(lambda:not self.w.isVisible())
        self.assertEqual(calls,[True])

    def test_download_cancel_does_not_fake_completion_or_launch_installer(self):
        from cmdrhelper import update
        from tests.test_update_download import ResponseStub,zip_bytes
        entered,release=threading.Event(),threading.Event();self.releases.append(release)
        class SlowResponse(ResponseStub):
            def read(inner,size=-1):
                entered.set();release.wait(3);return super().read(size)
        folder=self.root/'download';folder.mkdir()
        job=update.UpdateDownloadWorker({'asset_url':'https://example.invalid/test.zip','asset_name':'CMDRHelper_v2.1.2.zip','version':'2.1.2'})
        cancelled=[];job.signals.cancelled.connect(lambda:cancelled.append(True),Qt.QueuedConnection)
        with patch.object(update.urllib.request,'urlopen',return_value=SlowResponse(zip_bytes())),patch.object(update.tempfile,'mkdtemp',return_value=str(folder)),patch('cmdrhelper.ui.main_window.launch_installer') as installer:
            submit(QThreadPool.globalInstance(),job);self.assertTrue(entered.wait(2))
            self.w.close();QTest.qWait(60)
            self.assertTrue(job._cancel_event.is_set());self.assertTrue(self.w.isVisible());self.assertFalse(cancelled)
            release.set();self.wait(lambda:not self.w.isVisible());installer.assert_not_called()
        self.assertEqual(cancelled,[True]);self.assertFalse(folder.exists())

    def test_screenshot_conversion_keeps_result_and_stops_only_after_acceptance(self):
        from cmdrhelper.ui.screenshot_view import _ConvertWorker
        from PIL import Image
        source=self.root/'source.bmp';target=self.root/'target.png';Image.new('RGB',(8,8)).save(source)
        entered,release=threading.Event(),threading.Event();self.releases.append(release)
        real_open=Image.open
        def delayed(*args,**kwargs):entered.set();release.wait(3);return real_open(*args,**kwargs)
        job=_ConvertWorker(source,target,'PNG',True);results=[]
        job.signals.finished.connect(lambda *args:results.append(args),Qt.QueuedConnection)
        with patch('cmdrhelper.ui.screenshot_view.Image.open',side_effect=delayed):
            submit(QThreadPool.globalInstance(),job);self.assertTrue(entered.wait(2));self.w.close()
            QTest.qWait(60);self.assertTrue(self.w.isVisible());self.assertTrue(source.exists())
            release.set();self.wait(lambda:not self.w.isVisible())
        self.assertTrue(target.exists());self.assertFalse(source.exists());self.assertEqual(len(results),1);self.assertTrue(results[0][2])

    def test_mining_write_failure_keeps_window_open(self):
        from cmdrhelper.mining_controller import MiningInventoryController
        from cmdrhelper.mining_inventory import MiningInventory
        c=MiningInventoryController(self.w.state);self.w.state.mining_inventory_controller=c
        self.app.processEvents();c.timer.stop();c._dirty=False;c._running=True
        inventory=MiningInventory(7,'SYNTHETIC');inventory.checkpoints={'synthetic':'checkpoint'}
        entered,release=threading.Event(),threading.Event();self.releases.append(release)
        job=Work(entered,release,lambda:c.results.ready.emit(c._generation,inventory))
        submit(c.pool,job,essential=True);self.assertTrue(entered.wait(2))
        with patch('cmdrhelper.mining_controller.save_values',side_effect=OSError('disk full')):
            self.w.close();release.set();self.wait(lambda:not self.gate.pending());QTest.qWait(80)
        self.assertTrue(self.w.isVisible());self.assertFalse(self.settings.contains('materials/mining/cargo_checkpoints/7'))
        self.w._exit_controller.cancel();self.assertEqual(self.w._exit_controller.phase,'idle')
        self.assertTrue(c.retry_pending_save())
        self.assertEqual(self.settings.value('materials/mining/cargo_checkpoints/7'),inventory.checkpoints)
        self.assertIsNone(c._exit_pending_result)

    def upload_while_closing(self, service):
        from tests.test_edsm_response_safety import ResponseSafetyTests,Response
        from tests.test_source_transfers import TransferTests
        case=ResponseSafetyTests() if service=='edsm' else TransferTests();case.setUp()
        entered,release=threading.Event(),threading.Event();self.releases.append(release)
        errors=[]
        try:
            if service=='edsm':
                uploader=case.prepare(1)
                def response(*args,**kwargs):entered.set();release.wait(3);return Response(case.reply([100]))
                case.transport.side_effect=response
                target=lambda:uploader.process_folder(case.root)
                context=patch('builtins.print',wraps=print)
            else:
                cid=case.processors[0].sessions[0]['commander_id']
                def response(key,name,fid,rows):entered.set();release.wait(3);return [row['id'] for row in rows],{}
                target=case.run_transfer
                context=patch('cmdrhelper.source_transfers.upload_batch',side_effect=response)
            def run():
                try:target()
                except Exception as error:errors.append(error)
            with context:
                start_thread(threading.Thread(target=run,daemon=True))
                self.assertTrue(entered.wait(2));self.w.close();QTest.qWait(60);self.assertTrue(self.w.isVisible())
                release.set();self.wait(lambda:not self.w.isVisible())
            self.assertEqual(errors,[])
            if service=='edsm':
                self.assertEqual(uploader._stored_position(case.path),len(case.original));self.assertEqual(case.path.read_bytes(),case.original)
            else:
                self.assertFalse(case.db.inara_pending(cid))
                self.assertTrue(case.db.inara_pending(case.processors[1].sessions[0]['commander_id']))
        finally:
            release.set();self.wait(lambda:not self.gate.pending());case.doCleanups()

    def test_edsm_inflight_confirmation_is_preserved(self):
        self.upload_while_closing('edsm')

    def test_inara_inflight_confirmation_preserves_other_owner(self):
        self.upload_while_closing('inara')

    def test_qsettings_sync_error_keeps_saved_baseline_dirty(self):
        self.form();self.w.ui_font_size_spin.setValue(16);self.w.close();c=self.w._exit_controller
        with patch.object(self.settings,'status',return_value=QSettings.AccessError):c.save()
        self.assertTrue(self.w.isVisible());self.assertIn('font',c.dirty())
        self.assertEqual(c.phase,'drafts')

    def test_finished_worker_can_request_final_essential_result_before_exit(self):
        first,release=self.work();entered2,release2=threading.Event(),threading.Event();self.releases.append(release2)
        results=[]
        second=Work(entered2,release2)
        first.signals.done.connect(lambda:submit(QThreadPool.globalInstance(),second,essential=True),Qt.QueuedConnection)
        second.signals.done.connect(lambda:results.append('saved'),Qt.QueuedConnection)
        self.w.close();release.set();self.wait(entered2.is_set)
        QTest.qWait(60);self.assertTrue(self.w.isVisible());release2.set()
        self.wait(lambda:not self.w.isVisible());self.assertEqual(results,['saved'])

    def test_failed_screenshot_retains_source_and_prevents_exit(self):
        from cmdrhelper.ui.screenshot_view import _ConvertWorker
        from PIL import Image
        source=self.root/'source.bmp';target=self.root/'target.png';Image.new('RGB',(8,8)).save(source)
        entered,release=threading.Event(),threading.Event();self.releases.append(release)
        def failed(*args,**kwargs):entered.set();release.wait(3);raise OSError('synthetic write failure')
        job=_ConvertWorker(source,target,'PNG',True)
        with patch('cmdrhelper.ui.screenshot_view.Image.open',side_effect=failed):
            submit(QThreadPool.globalInstance(),job);self.assertTrue(entered.wait(2));self.w.close();release.set()
            self.wait(lambda:bool(self.gate.failures));QTest.qWait(60)
        self.assertTrue(self.w.isVisible());self.assertTrue(source.exists());self.assertFalse(target.exists())
        self.w._exit_controller.cancel();self.assertEqual(self.gate.failures,[])

    def test_retired_source_writer_is_still_drained(self):
        from cmdrhelper.market_writer import MarketWriteWorker
        from cmdrhelper.market_store import MarketStore
        from test_market_store import observation,NOW
        worker=MarketWriteWorker(self.root/'old.json',self.root/'old.db',clock=lambda:NOW)
        self.addCleanup(worker.close);worker.ready.result(timeout=3)
        entered,release=threading.Event(),threading.Event();self.releases.append(release)
        original=MarketStore.record_observation
        def delayed(store,value,**kwargs):entered.set();release.wait(3);return original(store,value,**kwargs)
        with patch.object(MarketStore,'record_observation',delayed):
            future=worker.record(observation());self.assertTrue(entered.wait(2));worker.request_close()
            # This observer no longer belongs to any current SourceManager runtime.
            self.w.close();QTest.qWait(60);self.assertTrue(self.w.isVisible())
            release.set();self.wait(lambda:not self.w.isVisible())
        self.assertTrue(future.result().inserted);self.assertTrue(worker.is_stopped())

    def test_cancel_after_sealing_writer_restores_normal_writing(self):
        from cmdrhelper.observed_market_observer import ObservedMarketObserver
        from cmdrhelper.observed_market_cache import ObservedMarketCache
        from cmdrhelper.market_store import MarketStore
        from test_market_store import observation,NOW
        cache=ObservedMarketCache(self.root/'legacy.json',clock=lambda:NOW)
        observer=ObservedMarketObserver(cache,use_market_store=True,clock=lambda:NOW)
        observer.cache;worker=observer.writer;worker.ready.result(timeout=3)
        self.w.state.observed_markets=observer
        entered,release=threading.Event(),threading.Event();self.releases.append(release)
        original=MarketStore.close
        def delayed(store):entered.set();release.wait(3);return original(store)
        try:
            with patch.object(MarketStore,'close',delayed):
                self.w.close();self.wait(entered.is_set);c=self.w._exit_controller
                c.cancel();self.assertTrue(self.w.isVisible());self.assertTrue(c.cancel_requested)
                release.set();self.wait(lambda:c.phase=='idle')
            self.assertIsNot(observer.writer,worker);observer.writer.ready.result(timeout=3)
            saved=observer.writer.record(observation()).result(timeout=3)
            self.assertTrue(saved.inserted)
            self.w.close();self.wait(lambda:not self.w.isVisible())
        finally:
            release.set()
            if observer.writer:observer.writer.close()

    def test_unresolved_market_capture_is_not_silently_discarded(self):
        from cmdrhelper.observed_market_observer import ObservedMarketObserver
        observer=ObservedMarketObserver()
        pending=({'event':'Market'}, {}, time.monotonic()-1)
        observer.pending=pending
        self.w.state.observed_markets=observer
        self.w.close();QTest.qWait(80)
        self.assertTrue(self.w.isVisible());self.assertIs(observer.pending,pending)
        self.w._exit_controller.cancel();self.assertIs(observer.pending,pending)

    def test_real_journal_import_commits_cursor_before_close(self):
        from tests.test_source_processing import ProcessingTests
        from test_import_catchup import append,event
        from cmdrhelper.journal_catchup import load_sessions
        from cmdrhelper import startup_runtime
        case=ProcessingTests();case.setUp()
        entered,release=threading.Event(),threading.Event();self.releases.append(release)
        try:
            processor=case.processors[0];processor.process()
            before=processor.sessions[0]['last_read_offset']
            append(case.paths[0],event('Location',StarSystem='Pending',SystemAddress=42))
            journal=case.paths[0].read_bytes();original=case.db.apply_commander_journal_delta
            errors=[]
            def delayed(*args,**kwargs):entered.set();release.wait(3);return original(*args,**kwargs)
            with patch.object(case.db,'apply_commander_journal_delta',side_effect=delayed):
                startup_runtime.start(self.w.state,lambda:processor.process(cancel=self.w.state._startup_cancel),'Synthetic-Import',errors.append,())
                self.assertTrue(entered.wait(2));self.w.close();QTest.qWait(60);self.assertTrue(self.w.isVisible())
                release.set();self.wait(lambda:not self.w.isVisible())
            after=next(row for row in load_sessions(case.db) if row['journal_file']==str(case.paths[0]))['last_read_offset']
            self.assertGreater(after,before);self.assertEqual(after,len(journal));self.assertEqual(case.paths[0].read_bytes(),journal)
            self.assertEqual(errors,[])
            with case.db._connect() as con:self.assertEqual(con.execute('pragma integrity_check').fetchone()[0],'ok')
        finally:
            release.set();self.wait(lambda:not self.gate.pending());case.doCleanups()

    def test_failed_checkpoint_retry_preserves_new_manual_carrier_confirmation(self):
        from cmdrhelper.mining_controller import MiningInventoryController
        from cmdrhelper.mining_inventory import MiningInventory
        c=MiningInventoryController(self.w.state)
        self.app.processEvents();c.timer.stop();c._dirty=False
        inventory=MiningInventory(7,'SYNTHETIC');inventory.carrier_id=42
        inventory.carrier_ledger={'generated':True};inventory.carrier_ledger_before=None
        inventory.checkpoints={'synthetic':'checkpoint'}
        with patch('cmdrhelper.mining_controller.save_values',side_effect=OSError('disk full')):
            c._finished(c._generation,inventory)
        key=c.carrier_ledger.key(inventory.fid,inventory.carrier_id)
        self.settings.setValue(key,{'manual':True});self.settings.sync()
        self.assertTrue(c.retry_pending_save())
        self.assertEqual(self.settings.value(key),{'manual':True})
        self.assertEqual(self.settings.value('materials/mining/cargo_checkpoints/7'),inventory.checkpoints)
        self.assertIsNone(c._exit_pending_result)
        c.timer.stop();c._dirty=False;c.close()

    def test_x11_window_manager_close_uses_same_draft_guard(self):
        import shutil
        import subprocess
        if self.app.platformName() != 'xcb' or not shutil.which('wmctrl'):
            self.skipTest('Requires a real X11 window manager and wmctrl')
        self.form();self.w.edsm_api_key_edit.setText('draft')
        self.w.activateWindow();self.button.setFocus()
        self.assertTrue(QTest.qWaitForWindowActive(self.w,3000))
        # Send the window manager's close request, independent of the user's
        # desktop key bindings (Alt+F4 need not be assigned on every desktop).
        subprocess.run(['wmctrl','-ic',hex(int(self.w.winId()))],check=True,timeout=5)
        self.wait(lambda:getattr(self.w,'_exit_controller',None) is not None)
        self.assertEqual(self.w._exit_controller.phase,'drafts');self.assertTrue(self.w.isVisible())
        self.assertEqual(self.w.edsm_api_key_edit.text(),'draft')
        self.w._exit_controller.cancel();self.assertTrue(self.w.isVisible())

    def test_completed_download_cannot_start_installer_after_exit_is_cancelled(self):
        job,release=self.work();self.w.close()
        with patch.object(self.w,'_update_download_cancelled') as cancelled,patch('cmdrhelper.ui.main_window.launch_installer') as installer:
            self.w._update_download_finished(self.root/'synthetic.zip')
            cancelled.assert_called_once()
            self.w._exit_controller.cancel();release.set();self.wait(lambda:not self.gate.pending())
            installer.assert_not_called();self.assertTrue(self.w.isVisible())
