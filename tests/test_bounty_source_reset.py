"""Reset through the source-backed UI using temporary journals and snapshots only."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from PySide6.QtWidgets import QMessageBox
from cmdrhelper.bounty_manager import BountyManager
from cmdrhelper.ui.bounty_view import BountyView
import test_source_manager as source_fixture
from test_import_catchup import append, event


class SourceBountyResetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source_fixture.ManagerTests.setUpClass()

    def setUp(self):
        self.fixture = source_fixture.ManagerTests()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.state = self.fixture.state
        self.sources = self.state.sources
        self.runtime = next(r for r in self.sources.runtimes.values() if r.source.name == 'Steam')
        self.other = next(r for r in self.sources.runtimes.values() if r is not self.runtime)
        for rt, amount in [(self.runtime, 500), (self.other, 900)]:
            observer = next(o for o in rt.watcher.live_observers if type(o) is BountyManager)
            observer._root = self.state.bounties.root
            path = Path(rt.processor.sessions[-1]['journal_file'])
            append(path, event('Bounty', TotalReward=amount, Rewards=[dict(Faction='Synthetic', Reward=amount)]))
            rt.watcher.check_now()
        self.fixture.drain()
        self.state.select_viewed_commander(self.runtime.processor.sessions[-1]['commander_id'])
        self.fixture.drain()
        self.path = Path(self.runtime.processor.sessions[-1]['journal_file'])
        self.fid = self.state.commander_fid
        self.owner = next(o for o in self.runtime.watcher.live_observers if type(o) is BountyManager)
        self.other_path = self.state.bounties.root / 'TEST-Heroic.json'
        self.assertEqual(self.state.bounties.snapshot()['total'], 500)
        self.assertFalse(self.state.bounties.cursors)
        self.assertTrue(self.owner.cursors)
        self.view = BountyView(self.state.bounties, str)
        self.addCleanup(self.view.close)

    def confirm(self, during=None):
        dialog, confirm = self.view.reset_dialog()
        def click():
            if during: during()
            confirm.click()
        with patch.object(self.view, 'reset_dialog', return_value=(dialog, confirm)), \
             patch.object(dialog, 'exec', side_effect=click), \
             patch.object(QMessageBox, 'warning') as warning:
            self.view.reset_button.click()
        return warning

    def test_button_resets_shared_snapshot_and_survives_refresh_restart(self):
        other_before = self.other_path.read_bytes()
        # An already written, not yet consumed bounty must not reappear after reset.
        append(self.path, event('Bounty', TotalReward=100, Rewards=[dict(Faction='Pending', Reward=100)]))
        journal_before = self.path.read_bytes()
        warning = self.confirm()
        warning.assert_not_called()
        self.assertEqual(self.state.bounties.snapshot()['total'], 0)
        self.assertEqual(self.state.bounties.snapshot()['factions'], {})
        self.assertEqual(self.view.table.rowCount(), 0)
        self.assertTrue(self.view.total.text().endswith('0'))
        saved = json.loads((self.state.bounties.root / (self.fid + '.json')).read_text())
        self.assertEqual(saved['total'], 0)
        self.assertEqual(saved['last_event']['offset'], len(journal_before))
        self.runtime.watcher.check_now(); self.fixture.drain(); self.view.refresh()
        self.assertEqual(self.state.bounties.snapshot()['total'], 0)
        restarted = BountyManager(self.state.bounties.root)
        restarted.set_folder(self.path.parent)
        restarted.identify(self.fid, 'Synthetic', self.path)
        restarted.consume([self.path])
        self.assertEqual(restarted.snapshot()['total'], 0)
        self.assertEqual(restarted.snapshot()['factions'], {})
        self.assertEqual(self.other_path.read_bytes(), other_before)
        self.assertEqual(self.path.read_bytes(), journal_before)
        append(self.path, event('Bounty', TotalReward=50, Rewards=[dict(Faction='New', Reward=50)]))
        self.runtime.watcher.check_now(); self.fixture.drain()
        self.assertEqual(self.state.bounties.snapshot()['total'], 50)

    def test_commander_change_during_confirmation_cannot_clear_either_balance(self):
        before = {p.name: p.read_bytes() for p in self.state.bounties.root.glob('*.json')}
        warning = self.confirm(lambda: self.state.select_viewed_commander(
            self.other.processor.sessions[-1]['commander_id']))
        warning.assert_called_once()
        self.assertEqual({p.name:p.read_bytes() for p in self.state.bounties.root.glob('*.json')}, before)
        self.assertEqual(self.state.bounties.snapshot()['total'], 900)

    def test_retired_or_unverified_source_is_rejected(self):
        before = (self.state.bounties.root / (self.fid + '.json')).read_bytes()
        self.runtime.source.enabled = False
        self.assertFalse(self.state.bounties.manual_reset(self.fid))
        self.runtime.source.enabled = True
        row = self.runtime.processor.sessions[-1]
        fid = row['fid_seen']; row['fid_seen'] = 'OTHER'
        self.assertFalse(self.state.bounties.manual_reset(self.fid))
        row['fid_seen'] = fid
        runtime = self.sources.runtimes.pop(self.runtime.source.id)
        try:
            self.assertFalse(self.state.bounties.manual_reset(self.fid))
        finally:
            self.sources.runtimes[runtime.source.id] = runtime
        self.assertEqual((self.state.bounties.root / (self.fid + '.json')).read_bytes(), before)

    def test_failed_save_keeps_balance_and_reader_cursor_for_retry(self):
        target = self.state.bounties.root / (self.fid + '.json')
        before = target.read_bytes()
        offset = self.owner.cursors[str(self.path)]['offset']
        with patch('cmdrhelper.bounty_manager.os.replace', side_effect=OSError('synthetic write failure')):
            warning = self.confirm()
        warning.assert_called_once()
        self.assertEqual(target.read_bytes(), before)
        self.assertEqual(self.state.bounties.snapshot()['total'], 500)
        self.assertEqual(self.owner.cursors[str(self.path)]['offset'], offset)
        self.confirm().assert_not_called()
        self.assertEqual(self.state.bounties.snapshot()['total'], 0)
