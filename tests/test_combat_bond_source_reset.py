"""Reset through the source-backed UI using temporary journals and snapshots only."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from PySide6.QtWidgets import QMessageBox
from cmdrhelper.combat_bond_manager import CombatBondManager
from cmdrhelper.ui.combat_bond_view import CombatBondView
from cmdrhelper.i18n import tr
import test_source_manager as source_fixture
from test_import_catchup import append, event


class SourceCombatBondResetTests(unittest.TestCase):
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
        for rt, amount in [(self.runtime, 157500), (self.other, 900)]:
            observer = next(o for o in rt.watcher.live_observers if type(o) is CombatBondManager)
            observer._root = self.state.combat_bonds.root
            path = Path(rt.processor.sessions[-1]['journal_file'])
            append(path, event('FactionKillBond', Reward=amount, AwardingFaction='Synthetic', VictimFaction='Other'))
            rt.watcher.check_now()
        self.fixture.drain()
        self.state.select_viewed_commander(self.runtime.processor.sessions[-1]['commander_id'])
        self.fixture.drain()
        self.path = Path(self.runtime.processor.sessions[-1]['journal_file'])
        self.fid = self.state.commander_fid
        self.owner = next(o for o in self.runtime.watcher.live_observers if type(o) is CombatBondManager)
        self.other_path = self.state.combat_bonds.root / 'TEST-Heroic.json'
        self.assertEqual(self.state.combat_bonds.snapshot()['total'], 157500)
        self.assertFalse(self.state.combat_bonds.cursors)
        self.assertTrue(self.owner.cursors)
        # Reproduce the reported persisted uncertain balance, using only the
        # synthetic fixture's state and normal atomic snapshot commit.
        from copy import deepcopy
        data = deepcopy(self.owner.states[self.fid])
        data.update(uncertain=True, capture_gap=True)
        self.assertTrue(self.owner._commit(self.fid, data))
        self.assertEqual(self.state.bounties.snapshot()['total'], 0)
        self.bounty_before = deepcopy(self.state.bounties.snapshot())
        self.view = CombatBondView(self.state.combat_bonds, str)
        self.assertEqual(self.view.total.text(), tr('combat_bonds.observed') + ': 157500')
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
        # An already written, not yet consumed combat bond must not reappear after reset.
        append(self.path, event('FactionKillBond', Reward=100, AwardingFaction='Pending', VictimFaction='Other'))
        journal_before = self.path.read_bytes()
        warning = self.confirm()
        warning.assert_not_called()
        self.assertEqual(self.state.combat_bonds.snapshot()['total'], 0)
        self.assertEqual(self.state.combat_bonds.snapshot()['factions'], {})
        self.assertEqual(self.view.table.rowCount(), 0)
        self.assertFalse(self.state.combat_bonds.snapshot()['uncertain'])
        self.assertEqual(self.state.bounties.snapshot(), self.bounty_before)
        self.assertEqual(self.view.total.text(), tr('mining.total') + ': 0')
        self.assertTrue(self.view.total.text().endswith('0'))
        saved = json.loads((self.state.combat_bonds.root / (self.fid + '.json')).read_text())
        self.assertEqual(saved['total'], 0)
        self.assertFalse(saved['uncertain'])
        self.assertFalse(saved['capture_gap'])
        self.assertFalse(saved['redemption_pending'])
        self.assertEqual(saved['pending_redemptions'], [])
        self.assertEqual(saved['last_event']['offset'], len(journal_before))
        self.runtime.watcher.check_now(); self.fixture.drain(); self.view.refresh()
        self.assertEqual(self.state.combat_bonds.snapshot()['total'], 0)
        restarted = CombatBondManager(self.state.combat_bonds.root)
        restarted.set_folder(self.path.parent)
        restarted.identify(self.fid, 'Synthetic', self.path)
        restarted.consume([self.path])
        self.assertEqual(restarted.snapshot()['total'], 0)
        self.assertEqual(restarted.snapshot()['factions'], {})
        self.assertEqual(self.other_path.read_bytes(), other_before)
        self.assertEqual(self.path.read_bytes(), journal_before)
        append(self.path, event('FactionKillBond', Reward=50, AwardingFaction='New', VictimFaction='Other'))
        self.runtime.watcher.check_now(); self.fixture.drain()
        self.assertEqual(self.state.combat_bonds.snapshot()['total'], 50)

    def test_commander_change_during_confirmation_cannot_clear_either_balance(self):
        before = {p.name: p.read_bytes() for p in self.state.combat_bonds.root.glob('*.json')}
        warning = self.confirm(lambda: self.state.select_viewed_commander(
            self.other.processor.sessions[-1]['commander_id']))
        warning.assert_called_once()
        self.assertEqual({p.name:p.read_bytes() for p in self.state.combat_bonds.root.glob('*.json')}, before)
        self.assertEqual(self.state.combat_bonds.snapshot()['total'], 900)

    def test_retired_or_unverified_source_is_rejected(self):
        before = (self.state.combat_bonds.root / (self.fid + '.json')).read_bytes()
        self.runtime.source.enabled = False
        self.assertFalse(self.state.combat_bonds.manual_reset(self.fid))
        self.runtime.source.enabled = True
        row = self.runtime.processor.sessions[-1]
        fid = row['fid_seen']; row['fid_seen'] = 'OTHER'
        self.assertFalse(self.state.combat_bonds.manual_reset(self.fid))
        row['fid_seen'] = fid
        runtime = self.sources.runtimes.pop(self.runtime.source.id)
        try:
            self.assertFalse(self.state.combat_bonds.manual_reset(self.fid))
        finally:
            self.sources.runtimes[runtime.source.id] = runtime
        self.assertEqual((self.state.combat_bonds.root / (self.fid + '.json')).read_bytes(), before)

    def test_failed_save_keeps_balance_and_reader_cursor_for_retry(self):
        target = self.state.combat_bonds.root / (self.fid + '.json')
        before = target.read_bytes()
        offset = self.owner.cursors[str(self.path)]['offset']
        with patch('cmdrhelper.combat_bond_manager.os.replace', side_effect=OSError('synthetic write failure')):
            warning = self.confirm()
        warning.assert_called_once()
        self.assertEqual(target.read_bytes(), before)
        self.assertEqual(self.state.combat_bonds.snapshot()['total'], 157500)
        self.assertEqual(self.owner.cursors[str(self.path)]['offset'], offset)
        self.confirm().assert_not_called()
        self.assertEqual(self.state.combat_bonds.snapshot()['total'], 0)
