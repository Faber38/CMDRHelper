"""Startup completion with synthetic sources, settings and databases only."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.game_instances import ProcessSnapshot
from cmdrhelper.journal_sources import SourceRegistry
from cmdrhelper.state import AppState
from cmdrhelper import startup_runtime
from test_import_catchup import append, event


class SourceStartupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def start_case(self, count=0, *, disabled=False, missing=False, saved=False):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        database = CMDRDatabase(root/'test.db')
        settings = QSettings(str(root/'settings.ini'), QSettings.IniFormat)
        registry = SourceRegistry(settings, [])
        for index in range(count):
            folder = root/str(index)
            folder.mkdir()
            if not missing:
                append(folder/'Journal.2026-10-18T120000.01.log',
                       event('Commander', FID=f'TEST-{index}', Name=f'Pilot {index}'),
                       event('Location', StarSystem='Test', SystemAddress=index+1))
            source = registry.add(str(folder))
            if disabled:
                registry.update(source.id, enabled=False)
            if missing:
                folder.rmdir()
        if saved:
            commander = database.upsert_commander('SAVED-FID', 'Saved Pilot')
            settings.setValue('commander_view/fid', 'SAVED-FID')
        for target, value in [
            ('cmdrhelper.state.CMDRDatabase', database),
            ('cmdrhelper.state.QSettings', settings),
            ('cmdrhelper.source_manager.discover', []),
            ('cmdrhelper.source_manager.inspect_instances', ProcessSnapshot(True)),
            ('cmdrhelper.state.AppState._request_startup_stations', None),
            ('cmdrhelper.source_transfers.transfer', {}),
            ('cmdrhelper.observed_market_observer.cache_path', root/'markets.json'),
        ]:
            mock = patch(target, return_value=value)
            mock.start()
            self.addCleanup(mock.stop)
        state = AppState()
        state.bounties._root = root/'bounties'
        state.combat_bonds._root = root/'combat'
        def close():
            state.sources.stop()
            startup_runtime.shutdown(state)
            self.app.processEvents()
        self.addCleanup(close)
        completed = []
        state.initializationFinished.connect(completed.append)
        deadline = time.monotonic()+10
        while not getattr(state, "_startup_completed", False) and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(.01)
        self.assertTrue(state._startup_completed)
        self.assertEqual(state.startup_status, 'success')
        self.assertEqual(completed, [''])
        self.assertFalse(state.sources.running)
        self.assertEqual(state.sources.queue, [])
        self.assertEqual(len(state.sources.runtimes), 0 if disabled else count)
        state.sources._next()
        self.assertEqual(completed, [''])  # Completion remains idempotent.
        if saved:
            self.assertEqual(state.viewed_commander_id, commander)
            self.assertEqual(state.commander_fid, 'SAVED-FID')
        elif not count or disabled or missing:
            self.assertIsNone(state.viewed_commander_id)
            self.assertFalse(state.commander_fid)
        else:
            # Preserve first-use selection of the first confirmed commander.
            self.assertEqual(state.commander_fid, 'TEST-0')
            self.assertEqual(database.commander_summary(state.viewed_commander_id)['fid'], 'TEST-0')
        expected = 1 if saved else (0 if disabled or missing else count)
        self.assertEqual(len(database.list_commanders()), expected)
        return state

    def test_no_sources(self):
        self.start_case()

    def test_one_source(self):
        self.start_case(1)

    def test_multiple_sources(self):
        self.start_case(3)

    def test_disabled_sources(self):
        state = self.start_case(2, disabled=True)
        self.assertTrue(all(not s.enabled for s in state.sources.registry.sources))

    def test_unreachable_source(self):
        self.start_case(1, missing=True)

    def test_saved_selection_without_source(self):
        self.start_case(saved=True)
