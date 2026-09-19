"""Isolated live fixtures only. Never open user journals or production snapshots."""
import hashlib
import json
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from cmdrhelper.combat_bond_manager import CombatBondManager
from cmdrhelper.bounty_manager import BountyManager
from cmdrhelper.journal_watcher import JournalWatcher
from cmdrhelper.live_journal import journal_batch
from cmdrhelper.ui.combat_bond_view import CombatBondView
from cmdrhelper.i18n import set_language, _TRANSLATIONS
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


def bond(amount=28018, faction='Explorers of Nabudis', **extra):
    return dict(event='FactionKillBond', Reward=amount, AwardingFaction=faction,
                VictimFaction='Ice Storm Squadron', **extra)


def redeem(amount=100, faction='Explorers of Nabudis', **extra):
    return dict(event='RedeemVoucher', Type='CombatBond', Amount=amount, Faction=faction, **extra)


class CombatBondTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.root = self.folder / 'combat_bonds'
        self.manager = CombatBondManager(self.root)
        self.manager.identify('FID-A', 'A')
        self.offset = 0
        set_language('de')
        self.addCleanup(set_language, 'de')

    def apply(self, event, fid='FID-A'):
        self.offset += 100
        return self.manager.apply(fid, fid, event, 'live.log', self.offset,
                                  hashlib.sha256(str(self.offset).encode()).hexdigest())

    def saved(self, fid='FID-A'):
        return json.loads((self.root / f'{fid}.json').read_text())

    def journal(self, name='Journal.2026-09-19T153848.01.log', events=()):
        path = self.folder / name
        path.write_text(''.join(json.dumps(e) + '\n' for e in events))
        return path

    def append(self, path, *events):
        with path.open('a') as stream:
            for event in events:
                stream.write(json.dumps(event) + '\n')

    def arm(self, path, manager=None):
        manager = manager or self.manager
        manager.set_folder(self.folder)
        manager.identify('FID-A', 'A', path)

    def test_first_use_never_reconstructs_even_after_redemption(self):
        path = self.journal(events=[redeem(), bond(237632)])
        self.arm(path)
        self.assertEqual(self.saved()['total'], 0)
        self.assertTrue(self.saved()['from_now'])
        self.append(path, bond())
        self.manager.consume([path])
        self.assertEqual(self.saved()['total'], 28018)

    def test_real_five_event_fixture(self):
        events = [bond(value) for value in [28018, 71091, 59840, 50520, 28163]]
        self.assertEqual(len(events), 5)
        for event in events:
            self.assertTrue(self.apply(event))
        self.assertEqual(self.saved()['total'], 237632)
        self.assertEqual(self.saved()['factions'], {'Explorers of Nabudis': 237632})
        self.assertNotIn('kills', self.saved())
        self.assertNotIn('VictimFaction', self.saved())

    def test_multiple_factions(self):
        self.apply(bond(200000, 'A'))
        self.apply(bond(100000, 'B'))
        self.assertEqual(self.saved()['factions'], {'A': 200000, 'B': 100000})
        self.assertEqual(self.saved()['total'], 300000)

    def test_unknown_factions_and_shared_reward(self):
        for faction in ['', '  ', None, 7, [], {}]:
            self.apply(bond(100, faction, SharedWithOthers=4))
        self.assertEqual(self.saved()['factions'], {'': 600})
        self.assertEqual(self.saved()['total'], 600)

    def test_invalid_amount_preserves_balance_and_marks_uncertain(self):
        self.apply(bond())
        for amount in [-1, True, '100', 1.2, None]:
            self.apply(bond(amount))
        self.assertEqual(self.saved()['total'], 28018)
        self.assertTrue(self.saved()['uncertain'])

    def test_atomic_save_order_and_signal(self):
        calls = []
        real_fsync, real_replace = os.fsync, os.replace
        def fsync(fd):
            calls.append('fsync')
            real_fsync(fd)
        def replace(source, target):
            calls.append('replace')
            self.assertEqual(Path(source).parent, self.root)
            self.assertEqual(json.loads(Path(source).read_text())['total'], 28018)
            real_replace(source, target)
        self.manager.changed.connect(lambda: calls.append(('signal', self.saved()['total'])))
        with patch('cmdrhelper.combat_bond_manager.os.fsync', side_effect=fsync), patch('cmdrhelper.combat_bond_manager.os.replace', side_effect=replace):
            self.apply(bond())
        self.assertEqual(calls, ['fsync', 'replace', ('signal', 28018)])

    def test_failed_write_rolls_back_and_retries(self):
        path = self.journal()
        self.arm(path)
        self.append(path, bond())
        anchor = self.saved()['last_event']
        with patch.object(self.manager, '_save', side_effect=OSError('disk full')):
            self.assertFalse(self.manager.consume([path]))
        self.assertEqual(self.saved()['last_event'], anchor)
        self.assertEqual(self.manager.snapshot()['total'], 0)
        self.assertTrue(self.manager.storage_error)
        self.assertTrue(self.manager.consume([path]))
        self.assertEqual(self.saved()['total'], 28018)
        self.assertFalse(self.manager.storage_error)

    def test_restart_current_suffix_and_dedup(self):
        path = self.journal()
        self.arm(path)
        self.append(path, bond())
        self.manager.consume([path])
        self.append(path, bond(10))
        restarted = CombatBondManager(self.root)
        self.arm(path, restarted)
        for _ in range(3):
            restarted.consume([path])
        self.assertEqual(restarted.snapshot()['total'], 28028)

    def test_duplicate_apply(self):
        args = ('FID-A', 'A', bond(), 'live.log', 100, 'a' * 64)
        self.manager.apply(*args)
        self.manager.apply(*args)
        self.assertEqual(self.saved()['total'], 28018)

    def test_commander_switch(self):
        self.apply(bond(100))
        self.apply(bond(200), 'FID-B')
        self.assertEqual(self.manager.snapshot()['total'], 200)
        self.manager.identify('FID-A', 'A')
        self.assertEqual(self.manager.snapshot()['total'], 100)
        self.assertEqual(self.saved('FID-B')['total'], 200)

    def test_rotation_new_identity_and_late_tail(self):
        path = self.journal()
        self.arm(path)
        self.append(path, bond(10))
        self.manager.consume([path])
        newer = self.journal('Journal.2026-09-19T170000.01.log', [dict(event='Commander', FID='FID-B', Name='B'), bond(20)])
        self.append(path, bond(5))
        self.manager.consume([path, newer])
        self.manager.consume([path, newer])
        self.assertEqual(self.saved()['total'], 15)
        self.assertEqual(self.saved('FID-B')['total'], 20)

    def test_numbered_part_inherits_identity(self):
        path = self.journal()
        self.arm(path)
        newer = self.journal('Journal.2026-09-19T153848.02.log', [bond(20)])
        self.manager.consume([newer])
        self.manager.consume([newer])
        self.assertEqual(self.saved()['total'], 20)

    def test_old_anchor_never_opens_old_file(self):
        old = self.journal()
        self.arm(old)
        self.append(old, bond(10))
        self.manager.consume([old])
        current = self.journal('Journal.2026-09-19T170000.01.log', [bond(999)])
        original = Path.open
        def guard(path, *args, **kwargs):
            if path == old:
                raise AssertionError('archive read')
            return original(path, *args, **kwargs)
        restarted = CombatBondManager(self.root)
        with patch.object(Path, 'open', guard):
            self.arm(current, restarted)
            restarted.consume([old, current])
        self.assertEqual(restarted.snapshot()['total'], 10)
        self.assertTrue(restarted.snapshot()['uncertain'])

    def test_wrong_prefix_does_not_replay(self):
        path = self.journal(events=[bond(1)])
        self.arm(path)
        self.append(path, bond(10))
        self.manager.consume([path])
        path.write_text(path.read_text().replace('Ice Storm', 'Ice StOrm'))
        restarted = CombatBondManager(self.root)
        self.arm(path, restarted)
        self.assertEqual(restarted.snapshot()['total'], 10)
        self.assertTrue(restarted.snapshot()['uncertain'])

    def test_resurrect_srv_capship_and_bounty_never_change_bonds(self):
        self.apply(bond())
        before = self.saved()
        with patch.object(self.manager, '_save', side_effect=AssertionError('unexpected write')):
            for kind in ['Resurrect', 'SRVDestroyed', 'CapShipBond', 'Bounty']:
                self.apply(dict(event=kind, Reward=999))
            self.apply(dict(event='RedeemVoucher', Type='bounty', Amount=28018))
        self.assertEqual(self.saved(), before)

    def test_smaller_amount_still_clears_only_named_faction(self):
        self.apply(bond(1000))
        self.apply(bond(200, 'Other'))
        self.apply(redeem(300, BrokerPercentage=0))
        self.assertEqual(self.saved()['factions'], {'Other': 200})
        self.assertFalse(self.saved()['uncertain'])

    def test_unobserved_factions_list_is_not_guessed(self):
        self.apply(bond(100, 'A'))
        self.apply(bond(200, 'B'))
        self.apply(dict(event='RedeemVoucher', Type='CombatBond', Amount=130,
                        Factions=[dict(Faction='A', Amount=100), dict(Faction='B', Amount=30)]))
        self.assertEqual(self.saved()['factions'], {'A': 100, 'B': 200})
        self.assertTrue(self.saved()['uncertain'])

    def test_ambiguous_redemptions_preserve_amount(self):
        cases = [redeem(100, None), redeem(100, ''), redeem(100, '  '), redeem(100, 7),
                 redeem(100, Factions=[]),
                 dict(event='RedeemVoucher', Type='CombatBond', Amount=100,
                      Factions=[dict(Faction='Explorers of Nabudis', Amount=99)])]
        for event in cases:
            with self.subTest(event=event):
                self.manager.states['FID-A'] = self.manager._empty('FID-A')
                self.apply(bond())
                self.apply(event)
                self.assertEqual(self.saved()['total'], 28018)
                self.assertTrue(self.saved()['uncertain'])
                self.assertTrue(self.saved()['redemption_pending'])

    def test_complete_local_redemption_evidence_survives_restart(self):
        event = redeem(100, BrokerPercentage=25, FutureField={'extra': [1, 2]})
        self.apply(bond())
        self.apply(event)
        restarted = CombatBondManager(self.root)
        restarted.identify('FID-A')
        self.assertEqual(restarted.snapshot()['last_redemption'], event)
        self.assertFalse(restarted.snapshot()['redemption_pending'])
        self.assertEqual(restarted.snapshot()['total'], 0)

    def test_manual_reset_anchors_unprocessed_tail(self):
        path = self.journal()
        self.arm(path)
        self.append(path, bond(), redeem(100, None))
        self.manager.consume([path])
        self.append(path, bond(99))
        self.assertTrue(self.manager.manual_reset('FID-A'))
        self.assertEqual(self.saved()['total'], 0)
        self.assertFalse(self.saved()['uncertain'])
        self.assertFalse(self.saved()['redemption_pending'])
        self.assertFalse(self.saved()['from_now'])
        self.assertFalse(self.saved()['capture_gap'])
        self.assertEqual(self.saved()['pending_redemptions'], [])
        self.assertEqual(self.saved()['last_event']['offset'], path.stat().st_size)
        restarted = CombatBondManager(self.root)
        self.arm(path, restarted)
        self.append(path, bond(7))
        restarted.consume([path])
        self.assertEqual(restarted.snapshot()['total'], 7)

    def test_manual_reset_rejects_identity_change_and_missing_anchor(self):
        self.assertFalse(self.manager.manual_reset('FID-A'))
        path = self.journal()
        self.arm(path)
        self.append(path, dict(event='Commander', FID='FID-B'))
        self.assertFalse(self.manager.manual_reset('FID-A'))
        self.assertFalse(self.manager.manual_reset('FID-B'))

    def test_reset_dialog_cancel_default(self):
        view = CombatBondView(self.manager, str)
        dialog, confirm = view.reset_dialog()
        self.addCleanup(view.close)
        self.addCleanup(dialog.close)
        self.assertNotEqual(dialog.defaultButton(), confirm)
        self.assertEqual(dialog.defaultButton(), dialog.escapeButton())
        self.assertIn('im Spiel', dialog.text())

    def test_ui_themes_empty_uncertain_populated(self):
        view = CombatBondView(self.manager, lambda v: f'{v:,}'.replace(',', '.') + ' Cr')
        self.addCleanup(view.close)
        view.resize(650, 300)
        for style in [DARK_STYLESHEET, LIGHT_STYLESHEET]:
            self.manager.states['FID-A'] = self.manager._empty('FID-A')
            view.refresh()
            view.setStyleSheet(style)
            view.show()
            self.app.processEvents()
            self.assertTrue(view.empty.isHidden())
            self.assertIn('Erfassung ab jetzt.', view.notice.text())
            self.apply(bond(100, ''))
            self.assertEqual(view.table.item(0, 0).text(), 'Unbekannte Fraktion')
            self.apply(redeem(100, None))
            self.assertIn('Beobachteter Betrag: 100 Cr', view.total.text())
            self.assertIn('Einlösung erkannt', view.notice.text())
            self.assertIn('nicht vollständig gesichert', view.toolTip())
            self.assertFalse(view.grab().isNull())
        self.manager.states['FID-A'] = self.manager._empty('FID-A')
        self.manager.states['FID-A']['from_now'] = False
        view.refresh()
        self.assertFalse(view.empty.isHidden())

    def test_twelve_languages(self):
        keys = {k for k in _TRANSLATIONS['de'] if k.startswith('combat_bonds.')}
        self.assertEqual(len(keys), 10)
        self.assertEqual(len(_TRANSLATIONS), 12)
        for language, table in _TRANSLATIONS.items():
            self.assertTrue(all(table.get(k) for k in keys), language)
            for key in ['bounties.from_now', 'bounties.faction', 'bounties.amount', 'bounties.unknown', 'chronicle.reset', 'planet_nav.cancel']:
                self.assertTrue(table.get(key), (language, key))

    def test_watcher_shares_reads_and_retries_independently(self):
        path = self.journal()
        bounties = BountyManager(self.folder / 'bounties')
        watcher = JournalWatcher()
        watcher.live_observers = [bounties, self.manager]
        watcher.set_folder(self.folder)
        with journal_batch():
            bounties.identify('FID-A', 'A', path)
            self.manager.identify('FID-A', 'A', path)
        watcher.journalChanged.connect(lambda: watcher.refresh_finished(True))
        watcher.check_now()
        bounty = dict(event='Bounty', TotalReward=50, Rewards=[dict(Faction='A', Reward=50)])
        self.append(path, bond(), bounty)
        original = Path.open
        reads = []
        def track(p, *args, **kwargs):
            if p == path and args and args[0] == 'rb':
                reads.append(p)
            return original(p, *args, **kwargs)
        with patch.object(Path, 'open', track), patch.object(self.manager, '_save', side_effect=OSError('disk full')):
            watcher.check_now()
        self.assertEqual(len(reads), 1)
        self.assertEqual(bounties.snapshot()['total'], 50)
        self.assertTrue(watcher._live_pending)
        watcher.check_now()
        watcher.check_now()
        self.assertEqual(self.saved()['total'], 28018)
        self.assertEqual(bounties.snapshot()['total'], 50)
        self.append(path, dict(event='Died'))
        watcher.check_now()
        self.assertEqual(bounties.snapshot()['total'], 0)
        self.assertEqual(self.saved()['total'], 0)
        self.append(path, bond(), bounty, redeem(18))
        watcher.check_now()
        self.assertEqual(bounties.snapshot()['total'], 50)
        self.assertEqual(self.saved()['total'], 0)
        self.append(path, dict(event='RedeemVoucher', Type='bounty'))
        watcher.check_now()
        self.assertEqual(bounties.snapshot()['total'], 0)
        self.assertEqual(self.saved()['total'], 0)
        self.assertEqual(self.manager.findChildren(QTimer), [])
        self.assertEqual(len(watcher.findChildren(QTimer)), 1)

    def test_observer_exception_does_not_block_other_observers(self):
        path = self.journal()
        bounties = BountyManager(self.folder / 'bounties')
        watcher = JournalWatcher()
        watcher.live_observers = [bounties, self.manager]
        watcher.set_folder(self.folder)
        with journal_batch():
            bounties.identify('FID-A', 'A', path)
            self.manager.identify('FID-A', 'A', path)
        watcher.journalChanged.connect(lambda: watcher.refresh_finished(True))
        watcher.check_now()
        self.append(path, bond(43684))
        with patch.object(bounties, 'consume', side_effect=RuntimeError('observer failure')):
            watcher.check_now()
        self.assertEqual(self.saved()['total'], 43684)
        self.assertTrue(watcher._live_pending)
        watcher.check_now()
        self.assertFalse(watcher._live_pending)
        self.assertEqual(self.saved()['total'], 43684)

    def test_real_live_restart_keeps_exact_43684_without_old_balance(self):
        path = self.journal(events=[bond(v) for v in [28018, 71091, 59840, 50520, 28163]])
        self.arm(path)
        self.assertEqual(self.saved()['total'], 0)
        self.append(path, bond(43684))
        self.assertTrue(self.manager.consume([path]))
        anchor = self.saved()['last_event']
        restarted = CombatBondManager(self.root)
        self.arm(path, restarted)
        self.assertTrue(restarted.consume([path]))
        self.assertTrue(restarted.consume([path]))
        self.assertEqual(restarted.snapshot()['factions'], {'Explorers of Nabudis': 43684})
        self.assertEqual(restarted.snapshot()['last_event'], anchor)

    def test_startup_batch_reads_current_file_once(self):
        path = self.journal(events=[bond(999)])
        bounties = BountyManager(self.folder / 'bounties')
        bounties.set_folder(self.folder)
        self.manager.set_folder(self.folder)
        original = Path.open
        reads = []
        def track(p, *args, **kwargs):
            if p == path and args and args[0] == 'rb':
                reads.append(p)
            return original(p, *args, **kwargs)
        with patch.object(Path, 'open', track), journal_batch():
            bounties.identify('FID-A', 'A', path)
            self.manager.identify('FID-A', 'A', path)
        self.assertEqual(len(reads), 1)
        self.assertEqual(self.saved()['total'], 0)

    def test_corrupt_json_is_preserved(self):
        self.root.mkdir()
        target = self.root / 'FID-A.json'
        target.write_text('broken')
        self.manager = CombatBondManager(self.root)
        self.manager.identify('FID-A')
        self.apply(bond())
        self.assertTrue(self.saved()['uncertain'])
        self.assertEqual(next(self.root.glob('*.corrupt-*')).read_text(), 'broken')

    def test_truncation_persists_uncertainty(self):
        path = self.journal()
        self.arm(path)
        self.append(path, bond())
        self.manager.consume([path])
        path.write_text('{}\n')
        self.manager.consume([path])
        self.assertTrue(self.saved()['uncertain'])
        self.assertEqual(self.saved()['total'], 28018)

    def test_partial_line_only_counts_after_newline(self):
        path = self.journal()
        self.arm(path)
        with path.open('a') as stream:
            stream.write(json.dumps(bond()))
        self.manager.consume([path])
        self.assertEqual(self.saved()['total'], 0)
        with path.open('a') as stream:
            stream.write('\n')
        self.manager.consume([path])
        self.manager.consume([path])
        self.assertEqual(self.saved()['total'], 28018)

    def test_invalid_json_marks_gap_and_next_event_survives(self):
        path = self.journal()
        self.arm(path)
        with path.open('a') as stream:
            stream.write('{broken}\n{"event":"RedeemVoucher","Type":"CombatBond","Amount":NaN}\n')
        self.append(path, bond())
        self.manager.consume([path])
        self.assertTrue(self.saved()['uncertain'])
        self.assertEqual(self.saved()['total'], 28018)

    def test_failed_reset_preserves_balance_and_anchor(self):
        path = self.journal()
        self.arm(path)
        self.append(path, bond())
        self.manager.consume([path])
        before = self.saved()
        with patch.object(self.manager, '_save', side_effect=OSError('disk full')):
            self.assertFalse(self.manager.manual_reset('FID-A'))
        self.assertEqual(self.saved(), before)
        self.assertEqual(self.manager.snapshot()['total'], 28018)

    def test_redemption_to_observed_zero_shows_empty(self):
        view = CombatBondView(self.manager, str)
        self.addCleanup(view.close)
        view.show()
        self.apply(bond(100))
        self.apply(redeem(100))
        self.assertEqual(self.saved()['total'], 0)
        self.assertFalse(self.saved()['uncertain'])
        self.assertFalse(view.empty.isHidden())

    def test_reset_only_current_fid(self):
        self.apply(bond(90), 'FID-B')
        path = self.journal()
        self.arm(path)
        self.assertTrue(self.manager.manual_reset('FID-A'))
        self.assertEqual(self.saved('FID-B')['total'], 90)
        self.manager.identify('FID-B')
        self.assertEqual(self.manager.snapshot()['total'], 90)

    def test_shared_batch_detects_replacement(self):
        from cmdrhelper.live_journal import read_bytes
        path = self.journal(events=[bond()])
        with journal_batch():
            original = read_bytes(path)
            self.append(path, bond(100))
            with self.assertRaises(OSError):
                read_bytes(path)
        self.assertGreater(len(read_bytes(path)), len(original))

    def test_diagnostics_do_not_log_payload(self):
        import logging
        from cmdrhelper.logging_config import PrivacyFormatter
        event = redeem(100, BrokerPercentage=25, Commander='PRIVATE NAME', FID='F12345678')
        with self.assertLogs('cmdrhelper.combat_bond_manager', level='INFO') as captured:
            self.apply(event)
        rendered = PrivacyFormatter().format(captured.records[-1])
        self.assertIn('CombatBond redemption', rendered)
        self.assertNotIn('PRIVATE NAME', rendered)
        self.assertNotIn('F12345678', rendered)
        self.assertEqual(self.saved()['last_redemption'], event)

    def test_default_path_uses_qstandardpaths(self):
        with patch('cmdrhelper.combat_bond_manager.QStandardPaths.writableLocation', return_value=str(self.folder)):
            manager = CombatBondManager()
            self.assertEqual(manager.root, self.folder / 'combat_bonds')

    def test_real_redemption_clears_observed_subset(self):
        self.apply(bond(43684))
        event = dict(timestamp='2026-09-19T14:44:30Z', event='RedeemVoucher',
                     Type='CombatBond', Amount=953470, Faction='Explorers of Nabudis')
        self.apply(event)
        self.assertEqual(self.saved()['factions'], {})
        self.assertEqual(self.saved()['total'], 0)
        self.assertFalse(self.saved()['redemption_pending'])
        self.assertFalse(self.saved()['uncertain'])
        self.assertEqual(self.saved()['last_redemption'], event)

    def test_amount_is_diagnostic_not_difference(self):
        for amount in [953470, 43684, 1, 0, None]:
            with self.subTest(amount=amount):
                self.apply(bond(43684))
                self.apply(redeem(amount))
                self.assertEqual(self.saved()['total'], 0)
                self.assertFalse(self.saved()['uncertain'])

    def test_redemption_unknown_faction_preserves_other_balances(self):
        self.apply(bond(100, 'A'))
        self.apply(bond(50, 'B'))
        self.apply(redeem(999, 'C'))
        self.assertEqual(self.saved()['factions'], {'A': 100, 'B': 50})
        self.assertFalse(self.saved()['uncertain'])
        self.apply(redeem(1, 'A'))
        self.assertEqual(self.saved()['factions'], {'B': 50})

    def test_capture_gap_survives_redemption_and_death(self):
        self.apply(bond(100))
        self.apply(bond(-1, 'Other'))
        self.apply(redeem(953470))
        self.assertEqual(self.saved()['total'], 0)
        self.assertTrue(self.saved()['capture_gap'])
        self.assertTrue(self.saved()['uncertain'])
        self.assertFalse(self.saved()['redemption_pending'])
        self.apply(dict(event='Died'))
        self.assertTrue(self.saved()['capture_gap'])
        self.assertTrue(self.saved()['uncertain'])

    def test_pending_other_faction_is_not_cleared(self):
        self.manager.states['FID-A'].update(pending_redemptions=['A', 'B'])
        self.manager._sync_uncertainty(self.manager.states['FID-A'])
        self.apply(redeem(100, 'A'))
        self.assertEqual(self.saved()['pending_redemptions'], ['B'])
        self.assertTrue(self.saved()['redemption_pending'])
        self.apply(redeem(100, 'B'))
        self.assertFalse(self.saved()['uncertain'])
        self.assertFalse(self.saved()['redemption_pending'])

    def test_unattributed_redemption_remains_uncertain(self):
        self.apply(redeem(100, None))
        self.apply(redeem(100, 'A'))
        self.assertTrue(self.saved()['redemption_pending'])
        self.assertFalse(self.saved()['capture_gap'])
        self.apply(dict(event='Died'))
        self.assertFalse(self.saved()['redemption_pending'])
        self.assertFalse(self.saved()['uncertain'])

    def test_died_clears_only_current_fid(self):
        self.apply(bond(500), 'FID-B')
        self.apply(bond(100))
        self.apply(dict(event='Died'))
        self.assertEqual(self.saved()['total'], 0)
        self.assertEqual(self.saved()['factions'], {})
        self.assertEqual(self.saved()['last_reset'], 'died')
        self.assertFalse(self.saved()['uncertain'])
        self.assertFalse(self.saved()['from_now'])
        self.assertEqual(self.saved('FID-B')['total'], 500)

    def test_restart_after_redemption_or_death_stays_zero(self):
        path = self.journal()
        self.arm(path)
        for event in [redeem(953470), dict(event='Died')]:
            with self.subTest(event=event):
                self.append(path, bond(43684), event)
                self.manager.consume([path])
                anchor = self.saved()['last_event']
                restarted = CombatBondManager(self.root)
                self.arm(path, restarted)
                restarted.consume([path])
                self.assertEqual(restarted.snapshot()['total'], 0)
                self.assertFalse(restarted.snapshot()['uncertain'])
                self.assertEqual(restarted.snapshot()['last_event'], anchor)
                self.manager = restarted

    def test_legacy_uncertainty_is_not_silently_repaired_or_replayed(self):
        self.apply(bond(43684))
        data = self.saved()
        data.pop('capture_gap')
        data.pop('pending_redemptions')
        data.update(uncertain=True, redemption_pending=True,
                    last_redemption=redeem(953470))
        target = self.root / 'FID-A.json'
        target.write_text(json.dumps(data))
        before = target.read_bytes()
        restarted = CombatBondManager(self.root)
        restarted.identify('FID-A')
        self.assertEqual(target.read_bytes(), before)
        self.assertEqual(restarted.snapshot()['total'], 43684)
        self.assertTrue(restarted.snapshot()['capture_gap'])
        self.assertTrue(restarted.snapshot()['redemption_pending'])

    def test_failed_loss_or_redemption_retries_atomically(self):
        path = self.journal()
        self.arm(path)
        for event in [redeem(953470), dict(event='Died')]:
            self.append(path, bond(43684))
            self.manager.consume([path])
            before = self.saved()
            self.append(path, event)
            with patch.object(self.manager, '_save', side_effect=OSError('disk full')):
                self.assertFalse(self.manager.consume([path]))
            self.assertEqual(self.saved(), before)
            self.assertEqual(self.manager.snapshot()['total'], 43684)
            self.assertTrue(self.manager.consume([path]))
            self.assertEqual(self.saved()['total'], 0)

    def test_uncertainty_reasons_survive_restart_independently(self):
        self.apply(bond(-1))
        self.apply(redeem(100, None))
        restarted = CombatBondManager(self.root)
        restarted.identify('FID-A')
        self.assertTrue(restarted.snapshot()['capture_gap'])
        self.assertEqual(restarted.snapshot()['pending_redemptions'], [''])
        self.manager = restarted
        self.apply(dict(event='Died'))
        self.assertTrue(self.saved()['uncertain'])
        self.assertFalse(self.saved()['redemption_pending'])


if __name__ == '__main__':
    unittest.main()
