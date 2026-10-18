"""Real source ingestion/projection with synthetic Windows process evidence."""
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from cmdrhelper.state import AppState
from cmdrhelper.database import CMDRDatabase
from cmdrhelper import startup_runtime
from cmdrhelper.game_instances import GameInstance
from test_import_catchup import append, event


class WindowsSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.folder = self.root/'Saved Games/Frontier Developments/Elite Dangerous'
        self.folder.mkdir(parents=True)
        self.db = CMDRDatabase(self.root/'test.db')
        self.settings = QSettings(str(self.root/'settings.ini'), QSettings.IniFormat)
        self.instance = GameInstance(7, 0, windows_started=123456)
        self.users = {}
        self.api = Mock()
        self.api.instances.return_value = []
        self.api.file_users.side_effect = lambda path: self.users.get(path, set())
        self.state, self.serial = None, 0
        for target, kwargs in [
            ('cmdrhelper.state.CMDRDatabase', dict(return_value=self.db)),
            ('cmdrhelper.state.QSettings', dict(return_value=self.settings)),
            ('cmdrhelper.source_manager.discover', dict(return_value=[(str(self.folder), 'Windows')])),
            ('cmdrhelper.game_instances.os', dict(new=SimpleNamespace(name='nt'))),
            ('cmdrhelper.game_instances._WindowsProcesses', dict(return_value=self.api)),
            ('cmdrhelper.state.AppState._request_startup_stations', dict(return_value=None)),
            ('cmdrhelper.source_transfers.transfer', dict(return_value={})),
            ('cmdrhelper.observed_market_observer.cache_path', dict(return_value=self.root/'markets.json')),
        ]:
            p = patch(target, **kwargs); p.start(); self.addCleanup(p.stop)
        self.addCleanup(self.stop)

    def journal(self, fid, name, *, live=True):
        self.serial += 1
        path = self.folder/f'Journal.2026-10-18T12{self.serial:02}00.01.log'
        append(path, event('Commander', FID=fid, Name=name),
               event('Location', StarSystem='System-'+name, SystemAddress=self.serial))
        if live:
            self.api.instances.return_value = [self.instance]
            self.users = {str(path.resolve()): {(self.instance.pid, self.instance.windows_started)}}
        return path

    def start(self):
        self.state = AppState()
        self.state.bounties._root = self.root/'bounties'
        self.state.combat_bonds._root = self.root/'combat'
        self.drain()

    def stop(self):
        if self.state is not None:
            self.state.sources.stop(); startup_runtime.shutdown(self.state)
            self.app.processEvents(); self.state = None

    def drain(self):
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            self.app.processEvents()
            m = self.state.sources
            if m.runtimes and not m.running and not m.queue and all(r.processor.initialized for r in m.runtimes.values()):
                return
            time.sleep(.01)
        self.fail('source processing did not finish')

    def refresh(self):
        rt = next(iter(self.state.sources.runtimes.values()))
        rt.watcher._current = None
        rt.watcher.check_now(); self.drain()
        self.state.sources._tick()

    def assert_view(self, fid):
        self.assertEqual(self.state.commander_fid, fid)
        self.assertEqual(self.db.commander_summary(self.state.viewed_commander_id)['fid'], fid)

    def test_helper_before_game_switch_four_commanders_and_no_game_restart(self):
        self.journal('NANJAN', 'Nanjan OHare', live=False)
        self.start(); self.assert_view('NANJAN')
        for fid, name in [('MEDORA', 'MEDORA SKYWARD'), ('THIRD', 'Third'), ('FOURTH', 'Fourth')]:
            self.journal(fid, name); self.refresh(); self.assert_view(fid)
        self.assertEqual(len(self.db.list_commanders()), 4)
        self.api.instances.return_value = []; self.users = {}
        self.state.sources._tick(); self.assert_view('FOURTH')
        self.stop(); self.start(); self.assert_view('FOURTH')

    def test_helper_after_game_and_legacy_upgrade(self):
        self.journal('NANJAN', 'Nanjan OHare'); self.start()
        self.assert_view('NANJAN'); self.stop()
        self.settings.remove('commander_view/follow_live')
        self.journal('MEDORA', 'MEDORA SKYWARD')
        self.start(); self.assertTrue(self.state.follow_live_commander)
        self.assert_view('MEDORA')

    def test_manual_selection_and_explicit_follow_survive_restart(self):
        self.journal('NANJAN', 'Nanjan OHare'); self.start()
        cid = self.state.viewed_commander_id
        self.journal('MEDORA', 'MEDORA SKYWARD'); self.refresh(); self.assert_view('MEDORA')
        self.state.select_viewed_commander(cid)
        self.state.sources._tick(); self.assert_view('NANJAN')
        self.stop(); self.start(); self.assertFalse(self.state.follow_live_commander)
        self.assert_view('NANJAN')
        self.state.set_follow_live_commander(True); self.state.sources._tick(); self.assert_view('MEDORA')
        self.stop(); self.start(); self.assertTrue(self.state.follow_live_commander); self.assert_view('MEDORA')

    def test_multiple_processes_unknown_and_conflicting_identity_do_not_switch(self):
        self.journal('NANJAN', 'Nanjan OHare'); self.start()
        self.journal('MEDORA', 'MEDORA SKYWARD')
        self.api.instances.return_value = [self.instance, GameInstance(8, 0, windows_started=999)]
        self.refresh(); self.assert_view('NANJAN')
        unknown = self.journal('', 'Unknown'); self.refresh(); self.assert_view('NANJAN')
        path = self.journal('MEDORA', 'MEDORA SKYWARD')
        append(path, event('Commander', FID='OTHER', Name='Other'))
        self.refresh(); self.assert_view('NANJAN')
        rt = next(iter(self.state.sources.runtimes.values()))
        # Rejected journals are recorded separately, never installed as the
        # current identified runtime session by the existing ingestion path.
        self.assertEqual(rt.processor.context['rejected'][str(unknown)], 'unknown')
        self.assertEqual(rt.processor.context['rejected'][str(path)], 'ambiguous')
        self.assertNotIn('OTHER', {c['fid'] for c in self.db.list_commanders()})

    def test_process_name_without_open_current_journal_does_not_select(self):
        self.journal('NANJAN', 'Nanjan OHare'); self.start()
        self.journal('MEDORA', 'MEDORA SKYWARD', live=False)
        self.refresh(); self.assert_view('NANJAN')
