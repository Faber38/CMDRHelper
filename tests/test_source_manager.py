"""Actual AppState integration using only synthetic files, DB and settings."""
import tempfile
import json
from datetime import datetime, timezone
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from cmdrhelper.state import AppState
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.game_instances import GameInstance, ProcessSnapshot
from cmdrhelper import startup_runtime
from test_import_catchup import append, event


class ManagerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = CMDRDatabase(self.root/'test.db')
        self.settings = QSettings(str(self.root/'settings.ini'), QSettings.IniFormat)
        self.folders = []
        for index, name in enumerate(('Steam', 'Heroic')):
            folder = self.root/name; folder.mkdir(); self.folders.append(folder)
            path = folder/'Journal.2026-09-14T120000.01.log'
            append(path, event('Commander', FID='TEST-'+name, Name=name),
                   event('Location', StarSystem=name, SystemAddress=index+10),
                   event('Materials', Raw=[dict(Name='iron', Count=index+1)], Manufactured=[], Encoded=[]))
        self.settings.setValue('journal_folder', str(self.folders[0]))
        for target, kwargs in [
            ('cmdrhelper.state.CMDRDatabase', dict(return_value=self.db)),
            ('cmdrhelper.state.QSettings', dict(return_value=self.settings)),
            ('cmdrhelper.source_manager.discover', dict(return_value=[(str(p),p.name) for p in self.folders])),
            ('cmdrhelper.source_manager.inspect_instances', dict(return_value=ProcessSnapshot(True))),
            ('cmdrhelper.state.AppState._request_startup_stations', dict(return_value=None)),
            ('cmdrhelper.source_transfers.transfer', dict(return_value={})),
            ('cmdrhelper.observed_market_observer.cache_path', dict(return_value=self.root/'observed-markets.json')),
        ]:
            patcher = patch(target, **kwargs); patcher.start(); self.addCleanup(patcher.stop)
        self.state = AppState()
        self.state.bounties._root = self.root/'bounties'
        self.state.combat_bonds._root = self.root/'combat-bonds'
        self.addCleanup(self.shutdown)
        self.drain()

    def shutdown(self):
        self.state.sources.stop()
        startup_runtime.shutdown(self.state)
        self.app.processEvents()

    def drain(self):
        deadline = time.monotonic()+15
        while time.monotonic() < deadline:
            self.app.processEvents()
            manager = self.state.sources
            if manager.runtimes and not manager.running and not manager.queue:
                return
            time.sleep(.01)
        self.fail('source work did not finish')

    def test_all_sources_ingested_and_manual_switch_projects_identity(self):
        state = self.state
        self.assertEqual(len(state.sources.runtimes), 2)
        commanders = self.db.list_commanders()
        self.assertEqual({c['fid'] for c in commanders}, {'TEST-Steam','TEST-Heroic'})
        from cmdrhelper.material_inventory import MaterialInventoryReader
        from cmdrhelper.journal_catchup import load_sessions
        rows = load_sessions(self.db)
        for commander in commanders:
            state.select_viewed_commander(commander['id'])
            self.assertEqual(state.commander_fid, commander['fid'])
            self.assertEqual(state.system, commander['current_name'])
            self.assertTrue(MaterialInventoryReader().reconstruct(commander['id'], commander['fid'], rows).known)
        self.assertEqual(int(self.settings.value('commander_view/viewed_commander_id')), state.viewed_commander_id)

    def test_active_projection_reuses_worker_result_across_sources(self):
        from cmdrhelper.journal_reader import read_latest_state
        manager = self.state.sources
        with patch('cmdrhelper.journal_reader.read_latest_state', wraps=read_latest_state) as read:
            for runtime in manager.runtimes.values():
                self.state.select_viewed_commander(runtime.processor.sessions[-1]['commander_id'])
                self.assertEqual(self.state.commander_fid, runtime.processor.sessions[-1]['fid_seen'])
            self.assertEqual(read.call_count, 0)
            path = Path(runtime.processor.sessions[-1]['journal_file'])
            append(path, event('Location', StarSystem='new', SystemAddress=42))
            manager.projection_key = None
            self.assertFalse(manager.refresh_selected())
            self.assertNotEqual(self.state.system, 'new')
            self.assertEqual(read.call_count, 0)
            runtime.watcher.check_now()
            self.drain()
            self.assertEqual(self.state.system, 'new')
            self.assertEqual(read.call_count, 1)
            manager.projection_key = None
            self.assertTrue(manager.refresh_selected())
            self.assertEqual(read.call_count, 1)

    def test_historical_commander_keeps_existing_projection_path(self):
        manager = self.state.sources
        runtime = next(iter(manager.runtimes.values()))
        old_id = runtime.processor.sessions[-1]['commander_id']
        newer = Path(runtime.source.path)/'Journal.2026-09-14T130000.01.log'
        append(newer, event('Commander', FID='NEW-FID', Name='New'),
               event('Location', StarSystem='New system', SystemAddress=99))
        runtime.watcher.check_now()
        self.drain()
        self.state.select_viewed_commander(old_id)
        self.assertEqual(self.state.commander_id, old_id)
        self.assertNotEqual(self.state.system, 'New system')
        self.state.select_viewed_commander(runtime.processor.sessions[-1]['commander_id'])
        self.assertEqual(self.state.commander_fid, 'NEW-FID')
        self.assertEqual(self.state.system, 'New system')

    def test_one_process_selects_multiple_keep_selection(self):
        state = self.state
        state.set_follow_live_commander(True)
        for runtime in state.sources.runtimes.values():
            path = runtime.processor.sessions[-1]['journal_file']
            instance = GameInstance(10, 0, journals=(str(Path(path).resolve()),))
            state.sources.snapshot = ProcessSnapshot(True, [instance])
            state.sources.choose(); state.sources.refresh_selected()
            self.assertEqual(state.commander_fid, runtime.processor.sessions[-1]['fid_seen'])
        before = state.viewed_commander_id
        for snapshot in (ProcessSnapshot(True), ProcessSnapshot(False), ProcessSnapshot(True, [instance, instance])):
            state.sources.snapshot = snapshot
            state.sources.choose()
            self.assertEqual(state.viewed_commander_id, before)

    def test_disable_remove_does_not_delete_files_or_history(self):
        manager = self.state.sources
        source = manager.registry.sources[0]
        manager.registry.update(source.id, enabled=False); manager.reconcile()
        self.assertNotIn(source.id, manager.runtimes)
        manager.registry.remove(source.id); manager.reconcile()
        self.assertTrue(Path(source.path).is_dir())
        self.assertEqual(len(self.db.list_commanders()), 2)

    def prepare_source_market(self):
        """Import through the real source watcher into the temporary market DB."""
        from test_observed_market_cache import sidecar
        manager = self.state.sources
        steam = next(r for r in manager.runtimes.values() if r.source.name == 'Steam')
        heroic = next(r for r in manager.runtimes.values() if r.source.name == 'Heroic')
        data = sidecar(datetime.now(timezone.utc))
        data.update(StationName='Steam Port', StarSystem='Steam')
        Path(steam.source.path, 'Market.json').write_text(json.dumps(data))
        append(Path(steam.processor.sessions[-1]['journal_file']),
               event('Docked', MarketID=123, StationName='Steam Port',
                     StarSystem='Steam', SystemAddress=10, StationType='Coriolis'),
               {k: v for k, v in data.items() if k != 'Items'})
        append(Path(heroic.processor.sessions[-1]['journal_file']),
               event('Docked', MarketID=456, StationName='Heroic Port',
                     StarSystem='Heroic', SystemAddress=11, StationType='Coriolis'))
        for runtime in (steam, heroic):
            runtime.watcher.check_now()
        self.drain()
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            steam.watcher.check_now()
            self.app.processEvents()
            if steam.observed_markets.cache.get_header(123) is not None:
                break
            time.sleep(.01)
        self.assertIsNotNone(steam.observed_markets.cache.get_header(123))
        self.assertIn(steam.observed_markets, steam.watcher.live_observers)
        self.assertIn(heroic.observed_markets, heroic.watcher.live_observers)
        return steam, heroic

    def test_market_projection_steam_heroic_steam(self):
        from cmdrhelper.ui.recommendations_view import current_market, current_market_context
        steam, heroic = self.prepare_source_market()
        for runtime in (steam, heroic, steam):
            self.state.select_viewed_commander(runtime.processor.sessions[-1]['commander_id'])
            self.assertIs(self.state.observed_markets, runtime.observed_markets)
            context = current_market_context(self.state)
            self.assertEqual(context['FID'], 'TEST-' + runtime.source.name)
            self.assertEqual(context['StationName'], runtime.source.name + ' Port')
            market = current_market(self.state)
            if runtime is steam:
                self.assertEqual(market['market_id'], 123)
                self.assertEqual(market['station_name'], 'Steam Port')
                self.assertEqual(market['fid'], 'TEST-Steam')
            else:
                self.assertIsNone(market)

    def test_disable_selected_source_clears_market_immediately(self):
        from cmdrhelper.ui.recommendations_view import current_market, current_market_context
        steam, _ = self.prepare_source_market()
        state, manager = self.state, self.state.sources
        state.select_viewed_commander(steam.processor.sessions[-1]['commander_id'])
        self.assertIsNotNone(current_market(state))
        notifications = []
        state.observedMarketsChanged.connect(lambda: notifications.append(current_market_context(state)))
        manager.registry.update(steam.source.id, enabled=False)
        manager.reconcile()
        self.assertIsNone(current_market(state))
        self.assertIsNone(current_market_context(state))
        self.assertEqual(notifications[-1], None)
        manager.refresh_selected()
        self.assertIsNone(current_market(state))
        self.assertIsNot(state.observed_markets, steam.observed_markets)

    def test_no_selection_clears_market_and_reselection_restores_it(self):
        from cmdrhelper.ui.recommendations_view import current_market, current_market_context
        self.state.viewed_commander_id = None
        self.state.sources.refresh_selected()
        self.assertIsNone(current_market_context(self.state))
        steam, _ = self.prepare_source_market()
        state, manager = self.state, self.state.sources
        cid = steam.processor.sessions[-1]['commander_id']
        state.select_viewed_commander(cid)
        self.assertIsNotNone(current_market(state))
        state.viewed_commander_id = None
        manager.refresh_selected()
        self.assertIsNone(current_market_context(state))
        self.assertIsNone(current_market(state))
        self.assertFalse(state.observed_markets.armed)
        state.select_viewed_commander(cid)
        self.assertIs(state.observed_markets, steam.observed_markets)
        self.assertIsNotNone(current_market(state))

    def test_manual_reimport_completes_existing_ui_protocol(self):
        completed = []
        self.state.databaseImportFinished.connect(lambda stats, error: completed.append((stats, error)))
        self.state.import_journal_archive()
        self.drain()
        self.assertEqual(len(completed), 1)
        self.assertEqual(completed[0][1], '')

    def test_restart_without_game_preserves_automatic_selection(self):
        state = self.state
        state.set_follow_live_commander(True)
        runtime = list(state.sources.runtimes.values())[-1]
        path = runtime.processor.sessions[-1]['journal_file']
        state.sources.snapshot = ProcessSnapshot(True, [GameInstance(7, 0, journals=(str(Path(path).resolve()),))])
        state.sources.choose(); state.sources.refresh_selected()
        selected = state.commander_fid
        self.shutdown()
        self.state = AppState()
        self.state.bounties._root = self.root/'bounties'
        self.state.combat_bonds._root = self.root/'combat-bonds'
        self.drain()
        self.assertEqual(self.state.commander_fid, selected)
        self.assertTrue(self.state.follow_live_commander)
        with self.db._connect() as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], 23)

    def test_switch_and_remove_during_worker_rejects_old_projection(self):
        state = self.state
        runtime = list(state.sources.runtimes.values())[0]
        target = list(state.sources.runtimes.values())[1].processor.sessions[-1]['commander_id']
        entered, release = threading.Event(), threading.Event()
        process = runtime.processor.process
        def blocked(**kwargs):
            entered.set()
            release.wait(5)
            return process(**kwargs)
        with patch.object(runtime.processor, 'process', side_effect=blocked):
            state.sources.request(runtime.source.id)
            deadline = time.monotonic()+3
            while not entered.is_set() and time.monotonic() < deadline:
                self.app.processEvents(); time.sleep(.01)
            self.assertTrue(entered.is_set())
            state.select_viewed_commander(target)
            state.sources.registry.remove(runtime.source.id)
            state.sources.reconcile()
            release.set()
            self.drain()
        self.assertEqual(state.viewed_commander_id, target)
        self.assertEqual(state.commander_id, target)
        self.assertNotIn(runtime.source.id, state.sources.runtimes)

    def test_ui_all_languages_has_no_missing_keys(self):
        from cmdrhelper import i18n
        from cmdrhelper.ui.journal_sources import JournalSourcesPanel
        self.addCleanup(i18n.set_language, i18n.get_language())
        for lang in i18n._TRANSLATIONS:
            i18n.set_language(lang)
            panel = JournalSourcesPanel(self.state.sources)
            self.assertEqual(panel.items.count(), 2)
            self.assertFalse(i18n.tr('sources.title').startswith('sources.'))
            panel.deleteLater()

    def test_ui_disable_during_worker_stops_watcher_keeps_identity_and_offsets(self):
        from PySide6.QtCore import Qt
        from cmdrhelper.ui.journal_sources import JournalSourcesPanel
        from cmdrhelper.journal_catchup import load_sessions
        state = self.state
        manager = state.sources
        runtime = next(iter(manager.runtimes.values()))
        cid = runtime.processor.sessions[-1]['commander_id']
        state.select_viewed_commander(cid)
        before = [(r['journal_file'], r['last_read_offset']) for r in load_sessions(self.db)]
        panel = JournalSourcesPanel(manager)
        self.addCleanup(panel.close)
        for index in range(panel.items.count()):
            if panel.items.item(index).data(Qt.UserRole) == runtime.source.id:
                panel.items.setCurrentRow(index)
        entered, release = threading.Event(), threading.Event()
        process = runtime.processor.process
        def blocked(**kwargs):
            entered.set()
            release.wait(5)
            return process(**kwargs)
        with patch.object(runtime.processor, 'process', side_effect=blocked):
            manager.request(runtime.source.id)
            deadline = time.monotonic()+3
            while not entered.is_set() and time.monotonic() < deadline:
                self.app.processEvents(); time.sleep(.01)
            try:
                self.assertTrue(entered.is_set())
                panel.items.currentItem().setCheckState(Qt.Unchecked)
                self.assertFalse(runtime.watcher.timer.isActive())
                self.assertNotIn(runtime.source.id, manager.runtimes)
                self.assertFalse(manager.registry.get(runtime.source.id).enabled)
            finally:
                release.set()
            self.drain()
        self.assertEqual(state.viewed_commander_id, cid)
        self.assertEqual(state.commander_id, cid)
        self.assertEqual(before, [(r['journal_file'], r['last_read_offset']) for r in load_sessions(self.db)])

    def test_ui_path_change_keeps_id_and_does_not_transfer_old_cursor(self):
        from PySide6.QtWidgets import QDialog
        from cmdrhelper.ui.journal_sources import JournalSourcesPanel
        from cmdrhelper.journal_catchup import load_sessions
        state = self.state
        runtime = next(iter(state.sources.runtimes.values()))
        source = runtime.source
        cid = runtime.processor.sessions[-1]['commander_id']
        state.select_viewed_commander(cid)
        old = {r['journal_file']: r['last_read_offset'] for r in load_sessions(self.db)}
        folder = self.root/'replacement'; folder.mkdir()
        path = folder/Path(runtime.processor.sessions[-1]['journal_file']).name
        append(path, event('Commander', FID='TEST-REPLACEMENT', Name='Replacement'),
               event('Location', StarSystem='Replacement', SystemAddress=12345))
        panel = JournalSourcesPanel(state.sources)
        self.addCleanup(panel.close)
        with patch('cmdrhelper.ui.journal_sources.SourceEditor') as editor:
            dialog = editor.return_value
            dialog.exec.return_value = QDialog.Accepted
            dialog.path.text.return_value = str(folder)
            dialog.name.text.return_value = 'Replacement source'
            dialog.enabled.isChecked.return_value = True
            panel._edit(source)
        self.assertFalse(runtime.watcher.timer.isActive())
        self.drain()
        self.assertEqual(state.sources.registry.get(source.id).path, str(folder))
        rows = {r['journal_file']: r for r in load_sessions(self.db)}
        self.assertEqual(old, {key: rows[key]['last_read_offset'] for key in old})
        self.assertEqual(rows[str(path)]['fid_seen'], 'TEST-REPLACEMENT')
        self.assertEqual(rows[str(path)]['last_read_offset'], path.stat().st_size)
        self.assertEqual(state.viewed_commander_id, cid)
