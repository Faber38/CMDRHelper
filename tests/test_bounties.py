"""Live-only snapshots; all journals and persistence stay in temporary directories."""
import json
import hashlib
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from cmdrhelper.bounty_manager import BountyManager
from cmdrhelper.journal_watcher import JournalWatcher
from cmdrhelper.ui.bounty_view import BountyView
from cmdrhelper.i18n import set_language, tr, _TRANSLATIONS
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


def bounty(amount=52528, faction='Example Faction', **extra):
    # Anonymized technical reference fixture; never seed production.
    return dict(timestamp='2016-09-20T13:35:46Z', event='Bounty',
                Rewards=[dict(Faction=faction, Reward=amount)], TotalReward=amount, **extra)


class BountyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.root = self.folder / 'snapshots'
        self.manager = BountyManager(self.root)
        self.manager.identify('FID-A', 'Commander A')
        self.offset = 0
        set_language('de')
        self.addCleanup(set_language, 'de')

    def apply(self, event, fid='FID-A', source='live.log'):
        self.offset += 100
        self.assertTrue(self.manager.apply(fid, fid, event, source, self.offset,
                                           hashlib.sha256(f"{source}:{self.offset}".encode()).hexdigest()))

    def saved(self, fid='FID-A'):
        return json.loads((self.root / f'{fid}.json').read_text())

    def journal(self, name='Journal.2016-09-20T140000.01.log', events=()):
        path = self.folder / name
        path.write_text(''.join(json.dumps(e) + '\n' for e in events))
        return path

    def append(self, path, *events):
        with path.open('a') as stream:
            for e in events:
                stream.write(json.dumps(e) + '\n')

    def arm(self, path):
        self.manager.set_folder(self.folder)
        self.manager.identify('FID-A', 'Commander A', path)

    def test_first_use_without_null_point_ignores_old_bounties(self):
        path = self.journal(events=[bounty()])
        with patch.object(Path, 'open', side_effect=AssertionError('Historical content read')):
            self.manager.set_folder(self.folder)
        self.manager.identify('FID-A', 'Commander A', path)
        self.assertTrue(self.manager.consume([path]))
        self.assertEqual(self.manager.snapshot()['total'], 0)
        self.assertTrue(self.saved()['from_now'])
        self.assertEqual(self.saved()['last_event']['offset'], path.stat().st_size)

    def test_reference_fixture_saved_immediately(self):
        self.apply(bounty())
        self.assertEqual(self.manager.snapshot()['total'], 52528)
        self.assertEqual(self.saved()['factions'], {'Example Faction': 52528})
        self.assertFalse(any(k in self.saved() for k in ['PilotName', 'Target', 'Ship']))

    def test_same_faction_adds(self):
        self.apply(bounty())
        self.apply(bounty(100))
        self.assertEqual(self.saved()['total'], 52628)

    def test_second_faction(self):
        self.apply(bounty())
        self.apply(bounty(100, 'Other'))
        self.assertEqual(len(self.saved()['factions']), 2)
        self.assertEqual(self.saved()['total'], 52628)

    def test_multiple_rewards_and_shared_with_others(self):
        event = bounty(176300, SharedWithOthers=3, VictimFaction='Never use this')
        event['Rewards'] = [dict(Faction=f, Reward=n) for f, n in [('A', 87800), ('B', 39000), ('C', 49500)]]
        self.apply(event)
        self.assertEqual(self.saved()['factions'], dict(A=87800, B=39000, C=49500))
        self.assertEqual(self.saved()['total'], 176300)

    def test_unknown_factions_keep_amount(self):
        for faction in ['', '  ', None, 42]:
            self.apply(bounty(100, faction))
        self.assertEqual(self.saved()['factions'], {'': 400})

    def test_redeem_resets_entire_snapshot_immediately(self):
        self.apply(bounty())
        self.apply(bounty(100, 'Other'))
        self.apply(dict(event='RedeemVoucher', Type='bounty', Amount=1, Factions=[]))
        self.assertEqual(self.saved()['total'], 0)
        self.assertEqual(self.saved()['factions'], {})

    def test_died_resets_immediately(self):
        self.apply(bounty())
        self.apply(dict(event='Died'))
        self.assertEqual(self.saved()['total'], 0)

    def test_irrelevant_events_never_reset_or_write(self):
        self.apply(bounty())
        with patch.object(self.manager, '_save', side_effect=AssertionError('Unexpected write')):
            for kind in ['SRVDestroyed', 'ShipyardSwap', 'FSDJump', 'LoadGame', 'Shutdown',
                         'FactionKillBond', 'CapShipBond', 'EngineerContribution']:
                self.apply(dict(event=kind, Type='Bounty', Reward=999))
            self.apply(dict(event='RedeemVoucher', Type='CombatBond', Amount=52528))
        self.assertEqual(self.manager.snapshot()['total'], 52528)

    def test_restart_loads_json_and_catches_up_same_journal(self):
        path = self.journal(events=[bounty()])
        self.arm(path)
        self.append(path, bounty())
        self.manager.consume([path])
        self.append(path, bounty(999))  # Arrived while Helper was closed.
        self.manager = BountyManager(self.root)
        self.arm(path)
        self.manager.consume([path])
        self.assertEqual(self.manager.snapshot()['total'], 53527)
        self.append(path, bounty(100))
        self.manager.consume([path])
        self.assertEqual(self.saved()['total'], 53627)

    def test_commander_a_b_a_and_same_names(self):
        self.apply(bounty())
        self.manager.identify('FID-B', 'Commander A')
        self.assertEqual(self.manager.snapshot()['total'], 0)
        self.apply(bounty(123), 'FID-B')
        self.manager.identify('FID-A', 'Renamed')
        self.assertEqual(self.manager.snapshot()['total'], 52528)
        self.assertEqual(self.saved('FID-B')['total'], 123)

    def test_duplicate_notifications_and_persisted_event_identity(self):
        path = self.journal()
        self.arm(path)
        self.append(path, bounty())
        for _ in range(3):
            self.manager.consume([path])
        self.assertEqual(self.saved()['total'], 52528)
        restarted = BountyManager(self.root)
        restarted.identify('FID-A')
        self.assertTrue(restarted.apply('FID-A', '', bounty(), str(path), path.stat().st_size,
                                        self.saved()['last_event']['prefix_sha256']))
        self.assertEqual(restarted.snapshot()['total'], 52528)

    def test_rotation_multiple_new_files_and_previous_tail(self):
        path = self.journal()
        self.arm(path)
        self.append(path, bounty(10))
        part = self.journal('Journal.2016-09-20T140000.02.log', [bounty(20)])
        newer = self.journal('Journal.2016-09-20T150000.01.log',
                             [dict(event='Commander', FID='FID-A', Name='A'), bounty(30)])
        for _ in range(2):
            self.manager.consume([path, part, newer])
        self.assertEqual(self.saved()['total'], 60)
        self.assertLessEqual(len(self.manager.cursors), 2)

    def test_rotation_new_commander_has_separate_identity(self):
        path = self.journal()
        self.arm(path)
        self.append(path, bounty(10))
        newer = self.journal('Journal.2016-09-20T150000.01.log',
                             [dict(event='Commander', FID='FID-B', Name='B'), bounty(30)])
        self.manager.consume([path, newer])
        self.assertEqual(self.saved()['total'], 10)
        self.assertEqual(self.saved('FID-B')['total'], 30)

    def test_new_session_without_fid_does_not_inherit_commander(self):
        path = self.journal()
        self.arm(path)
        newer = self.journal('Journal.2016-09-20T150000.01.log', [bounty()])
        self.manager.consume([newer])
        self.assertEqual(self.manager.snapshot()['total'], 0)
        self.assertEqual(self.saved()['total'], 0)

    def test_incomplete_line_waits_for_newline(self):
        path = self.journal()
        self.arm(path)
        with path.open('a') as stream:
            stream.write(json.dumps(bounty()))
        self.manager.consume([path])
        self.assertEqual(self.manager.snapshot()['total'], 0)
        with path.open('a') as stream:
            stream.write('\n')
        self.manager.consume([path])
        self.assertEqual(self.saved()['total'], 52528)

    def test_corrupt_json_kept_and_backed_up_before_live_recovery(self):
        self.root.mkdir()
        path = self.root / 'FID-C.json'
        path.write_bytes(b'{broken')
        self.manager.identify('FID-C', 'C')
        self.assertEqual(self.manager.snapshot()['total'], 0)
        self.assertTrue(self.manager.snapshot()['uncertain'])
        self.assertEqual(path.read_bytes(), b'{broken')
        self.apply(bounty(100), 'FID-C')
        backups = list(self.root.glob('FID-C.json.corrupt-*'))
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0].read_bytes(), b'{broken')
        self.assertEqual(self.saved('FID-C')['total'], 100)
        self.assertTrue(self.saved('FID-C')['uncertain'])
        self.apply(dict(event='Died'), 'FID-C')
        self.assertFalse(self.saved('FID-C')['uncertain'])

    def test_wrong_fid_schema_and_invalid_amounts_are_rejected(self):
        self.root.mkdir()
        for data in [dict(schema=99), dict(fid='other'), dict(total=-1),
                     dict(total=True), dict(factions={'A': -1}), dict(total=10)]:
            candidate = self.manager._empty('FID-C')
            candidate.update(data)
            (self.root / 'FID-C.json').write_text(json.dumps(candidate))
            reader = BountyManager(self.root)
            reader.identify('FID-C')
            self.assertTrue(reader.snapshot()['uncertain'])
            self.assertEqual(reader.snapshot()['total'], 0)

    def test_atomic_save_failure_preserves_old_json_and_retries_once(self):
        path = self.journal()
        self.arm(path)
        self.append(path, bounty(10))
        self.manager.consume([path])
        old_bytes = (self.root / 'FID-A.json').read_bytes()
        self.append(path, bounty(20))
        with patch('cmdrhelper.bounty_manager.os.replace', side_effect=OSError('disk unavailable')):
            self.assertFalse(self.manager.consume([path]))
        self.assertEqual((self.root / 'FID-A.json').read_bytes(), old_bytes)
        self.assertEqual(self.manager.snapshot()['total'], 10)
        self.assertFalse(list(self.root.glob('*.tmp')))
        self.assertTrue(self.manager.consume([path]))
        self.assertEqual(self.saved()['total'], 30)

    def test_atomic_write_fsync_before_same_directory_replace(self):
        operations = []
        replace = os.replace
        fsync = os.fsync
        def checked_replace(source, target):
            self.assertEqual(Path(source).parent, Path(target).parent)
            self.assertEqual(json.loads(Path(source).read_text())['total'], 52528)
            operations.append('replace')
            replace(source, target)
        def checked_sync(fd):
            operations.append('fsync')
            fsync(fd)
        with patch('cmdrhelper.bounty_manager.os.replace', side_effect=checked_replace), \
             patch('cmdrhelper.bounty_manager.os.fsync', side_effect=checked_sync):
            self.apply(bounty())
        self.assertEqual(operations, ['fsync', 'replace'])

    def test_reward_mismatch_is_not_invented(self):
        e = bounty()
        e['TotalReward'] = 1
        self.apply(e)
        self.assertEqual(self.saved()['total'], 0)
        self.assertTrue(self.saved()['uncertain'])

    def test_unsafe_fid_never_creates_a_file(self):
        self.apply(bounty(), '../outside')
        self.assertFalse(self.root.exists())

    def test_app_data_location_used(self):
        with patch('cmdrhelper.bounty_manager.QStandardPaths.writableLocation', return_value=str(self.folder)) as location:
            self.assertEqual(BountyManager().root, self.folder / 'bounties')
            location.assert_called_once()

    def test_existing_watcher_not_refresh_or_new_timer_drives_live_events(self):
        path = self.journal(events=[dict(event='Commander', FID='FID-A', Name='A'), bounty(999)])
        watcher = JournalWatcher()
        watcher.live_observer = self.manager
        watcher.set_folder(self.folder)
        self.manager.identify('FID-A', 'A', path)
        watcher.journalChanged.connect(lambda: watcher.refresh_finished(True))
        watcher.check_now()
        self.assertEqual(self.manager.snapshot()['total'], 0)
        self.append(path, bounty())
        watcher.check_now()
        watcher.check_now()
        self.assertEqual(self.saved()['total'], 52528)
        self.assertEqual(self.manager.findChildren(QTimer), [])
        self.assertEqual(len(watcher.findChildren(QTimer)), 1)

    def test_truncated_journal_is_not_replayed(self):
        path = self.journal(events=[bounty(999)])
        self.arm(path)
        path.write_text('{}\n')
        self.manager.consume([path])
        self.append(path, bounty())
        self.manager.consume([path])
        self.assertEqual(self.manager.snapshot()['total'], 0)
        self.assertTrue(self.manager.snapshot()['uncertain'])

    def test_ui_empty_populated_unknown_and_themes(self):
        view = BountyView(self.manager, lambda value: f'{value:,}'.replace(',', '.') + ' Cr')
        self.addCleanup(view.close)
        view.resize(650, 300)
        for stylesheet in [DARK_STYLESHEET, LIGHT_STYLESHEET]:
            view.setStyleSheet(stylesheet)
            view.show()
            self.app.processEvents()
            self.assertFalse(view.empty.isHidden())
            self.assertTrue(view.table.isHidden())
            self.apply(bounty())
            self.apply(bounty(100, ''))
            self.app.processEvents()
            self.assertEqual(view.table.rowCount(), 2)
            self.assertEqual(view.table.item(1, 0).text(), 'Unbekannte Fraktion')
            self.assertEqual(view.total.text(), 'Gesamt: 52.628 Cr')
            self.assertIn('live', view.toolTip())
            self.assertFalse(view.grab().isNull())
            self.apply(dict(event='Died'))

    def test_twelve_languages_have_all_keys(self):
        keys = {key for key in _TRANSLATIONS['de'] if key.startswith('bounties.')}
        self.assertEqual(len(keys), 12)
        self.assertEqual(len(_TRANSLATIONS), 12)
        for language, table in _TRANSLATIONS.items():
            self.assertTrue(all(table.get(key) for key in keys), language)
            self.assertTrue(table.get('mining.total'), language)

    def test_missions_page_integration(self):
        from types import SimpleNamespace
        from unittest.mock import Mock
        from PySide6.QtWidgets import QMainWindow, QTableWidgetItem, QSizePolicy
        from cmdrhelper.ui.main_window import MainWindow
        from cmdrhelper.models import Mission
        host = QMainWindow()
        self.addCleanup(host.close)
        from cmdrhelper.combat_bond_manager import CombatBondManager
        bonds = CombatBondManager(self.folder / "combat_bonds")
        host.state = SimpleNamespace(bounties=self.manager, combat_bonds=bonds, refresh=lambda: None, missions=[
            Mission(name='Mission A', summary='Details A', progress_text='1 / 3'),
            Mission(name='Mission B', summary='Details B', progress_text='2 / 4')],
                                     settings=SimpleNamespace(value=lambda *args: None, setValue=Mock()))
        host._card = lambda title: MainWindow._card(host, title)
        host._format_reward = MainWindow._format_reward
        host._reset_missions = lambda: None
        host._translate_mission_text = MainWindow._translate_mission_text
        host._mission_selection_changed = lambda: MainWindow._mission_selection_changed(host)
        host._save_missions_header_state = lambda *args: None
        page = MainWindow._missions(host)
        host.setCentralWidget(page)
        host.resize(1100, 850)
        host.show()
        self.app.processEvents()
        self.assertIs(host.bounty_view.parent(), page)
        active = host.missions_table.parentWidget()
        details = host.mission_detail_title.parentWidget()
        layout = page.layout()
        self.assertEqual(layout.indexOf(host.bounty_view), layout.indexOf(active) + 1)
        self.assertEqual(layout.indexOf(host.combat_bond_view), layout.indexOf(host.bounty_view) + 1)
        self.assertEqual(layout.indexOf(details), layout.indexOf(host.combat_bond_view) + 1)
        self.assertEqual(layout.stretch(layout.indexOf(active)), 1)
        self.assertEqual(host.bounty_view.sizePolicy().verticalPolicy(), QSizePolicy.Maximum)
        host.missions_table.setRowCount(2)
        for row in range(2):
            host.missions_table.setItem(row, 0, QTableWidgetItem(host.state.missions[row].name))
        for style in [DARK_STYLESHEET, LIGHT_STYLESHEET]:
            host.setStyleSheet(style)
            self.app.processEvents()
            empty_height = host.bounty_view.height()
            self.assertTrue(host.bounty_view.table.isHidden())
            self.assertLess(empty_height, active.height())
            self.assertLessEqual(empty_height, host.bounty_view.sizeHint().height())
            self.apply(bounty())
            self.apply(bounty(100, 'Other faction'))
            self.app.processEvents()
            self.assertEqual(host.bounty_view.total.text(), 'Gesamt: 52.628 Cr')
            self.assertEqual(host.bounty_view.table.rowCount(), 2)
            self.assertGreater(host.bounty_view.height(), empty_height)
            self.assertLess(host.bounty_view.geometry().bottom(), details.geometry().top())
            for row in range(2):
                host.missions_table.selectRow(row)
                self.assertEqual(host.mission_detail_title.text(), host.state.missions[row].name)
                self.assertEqual(host.mission_detail_text.text(), host.state.missions[row].summary)
                self.assertIn(host.state.missions[row].progress_text, host.mission_progress_text.text())
            host.missions_table.clearSelection()
            self.assertEqual(host.mission_detail_title.text(), tr('missions.none_selected'))
            self.assertEqual(host.mission_detail_text.text(), tr('missions.select_above'))
            self.assertFalse(host.grab().isNull())
            self.apply(dict(event='Died'))

    def test_existing_from_now_snapshot_does_not_reinitialize_old_bounties(self):
        path = self.journal(events=[bounty()])
        self.arm(path)
        before = self.saved()
        self.assertEqual(before['total'], 0)
        self.assertTrue(before['from_now'])
        self.restart(path)
        self.assertEqual(self.saved(), before)
        self.append(path, bounty(100))
        self.manager.consume([path])
        self.manager.consume([path])
        self.assertEqual(self.saved()['total'], 100)

    def test_watcher_write_failure_does_not_block_other_state_and_retries(self):
        path = self.journal()
        watcher = JournalWatcher()
        watcher.live_observer = self.manager
        watcher.set_folder(self.folder)
        self.manager.identify('FID-A', 'A', path)
        refreshes = []
        def refreshed():
            refreshes.append(True)
            watcher.refresh_finished(True)
        watcher.journalChanged.connect(refreshed)
        watcher.check_now()
        self.append(path, bounty())
        with patch.object(self.manager, '_save', side_effect=OSError('full')):
            watcher.check_now()
        self.assertEqual(len(refreshes), 2)
        self.assertTrue(watcher._live_pending)
        watcher.check_now()
        self.assertFalse(watcher._live_pending)
        self.assertEqual(self.saved()['total'], 52528)
        self.assertEqual(len(refreshes), 2)

    def test_boundary_failure_never_falls_back_to_historical_replay(self):
        path = self.journal(events=[bounty()])
        with patch('cmdrhelper.bounty_manager.journal_files', side_effect=OSError('unavailable')):
            self.manager.set_folder(self.folder)
        self.manager.identify('FID-A', 'A', path)
        self.manager.consume([path])
        self.assertEqual(self.manager.snapshot()['total'], 0)
        self.assertFalse(self.root.exists())

    def restart(self, path, fid='FID-A'):
        self.manager = BountyManager(self.root)
        self.manager.set_folder(self.folder)
        self.manager.identify(fid, fid, path)

    def test_first_start_uses_last_reset_in_current_journal_only(self):
        old = self.journal('Journal.2016-09-19T140000.01.log', [bounty(999999)])
        current = self.journal(events=[dict(event='Commander', FID='FID-A', Name='A'),
                                      bounty(999), dict(event='Died'), bounty(111),
                                      dict(event='RedeemVoucher', Type='bounty'), bounty()])
        original_open = Path.open
        def current_only(path, *args, **kwargs):
            if path == old:
                raise AssertionError('Older journal opened')
            return original_open(path, *args, **kwargs)
        with patch.object(Path, 'open', current_only):
            self.restart(current)
        self.assertEqual(self.saved()['factions'], {'Example Faction': 52528})
        self.assertFalse(self.saved()['from_now'])
        self.assertFalse(self.saved()['uncertain'])
        self.assertEqual(self.saved()['last_event']['offset'], current.stat().st_size)
        self.manager.consume([current])
        self.assertEqual(self.saved()['total'], 52528)

    def test_restart_no_new_events_does_not_rewrite_snapshot(self):
        path = self.journal(events=[dict(event='Died'), bounty()])
        self.arm(path)
        previous = (self.root / 'FID-A.json').read_bytes()
        with patch.object(BountyManager, '_save', side_effect=AssertionError('Unexpected write')):
            self.restart(path)
            self.manager.consume([path])
        self.assertEqual((self.root / 'FID-A.json').read_bytes(), previous)

    def test_crash_gap_two_bounties_and_next_live_event(self):
        path = self.journal(events=[dict(event='Died'), bounty()])
        self.arm(path)
        offset = self.saved()['last_event']['offset']
        self.append(path, bounty(10000, 'A'), bounty(20000, 'B'))
        self.restart(path)
        self.assertEqual(self.saved()['total'], 82528)
        self.assertEqual(self.saved()['factions']['A'], 10000)
        self.assertEqual(self.saved()['factions']['B'], 20000)
        self.assertGreater(self.saved()['last_event']['offset'], offset)
        self.manager.consume([path])
        self.append(path, bounty(100, 'A'))
        self.manager.consume([path])
        self.assertEqual(self.saved()['total'], 82628)

    def test_catchup_redeem_then_new_bounty(self):
        path = self.journal(events=[dict(event='Died'), bounty()])
        self.arm(path)
        self.append(path, dict(event='RedeemVoucher', Type='bounty'), bounty(100))
        self.restart(path)
        self.assertEqual(self.saved()['total'], 100)
        self.assertEqual(self.saved()['last_reset'], 'redeemed')

    def test_catchup_died_clears_balance(self):
        path = self.journal(events=[dict(event='Died'), bounty()])
        self.arm(path)
        self.append(path, dict(event='Died'))
        self.restart(path)
        self.assertEqual(self.saved()['total'], 0)

    def test_changed_journal_without_reset_keeps_balance_and_marks_gap(self):
        old = self.journal(events=[dict(event='Died'), bounty()])
        self.arm(old)
        self.append(old, bounty(999))
        current = self.journal('Journal.2016-09-21T140000.01.log',
                               [dict(event='Commander', FID='FID-A'), bounty(9999)])
        original_open = Path.open
        def no_old(path, *args, **kwargs):
            if path == old:
                raise AssertionError('Offline old journal opened')
            return original_open(path, *args, **kwargs)
        with patch.object(Path, 'open', no_old):
            self.restart(current)
        self.assertEqual(self.saved()['total'], 52528)
        self.assertTrue(self.saved()['uncertain'])
        self.append(current, bounty(10))
        self.manager.consume([current])
        self.assertEqual(self.saved()['total'], 52538)

    def test_changed_journal_with_reset_resynchronizes(self):
        old = self.journal(events=[dict(event='Died'), bounty()])
        self.arm(old)
        current = self.journal('Journal.2016-09-21T140000.01.log',
                               [dict(event='Commander', FID='FID-A'), bounty(9999),
                                dict(event='RedeemVoucher', Type='bounty'), bounty(10)])
        self.restart(current)
        self.assertEqual(self.saved()['total'], 10)
        self.assertFalse(self.saved()['uncertain'])

    def test_invalid_anchor_keeps_balance_without_replay(self):
        path = self.journal(events=[bounty()])
        self.arm(path)
        self.append(path, bounty(100))
        self.manager.consume([path])
        data = self.saved()
        data['last_event']['offset'] = 999999
        (self.root / 'FID-A.json').write_text(json.dumps(data))
        self.restart(path)
        self.assertEqual(self.saved()['total'], 100)
        self.assertTrue(self.saved()['uncertain'])

    def test_prefix_rewrite_invalidates_anchor(self):
        path = self.journal(events=[bounty(100)])
        self.arm(path)
        self.append(path, bounty(200))
        self.manager.consume([path])
        path.write_bytes(path.read_bytes().replace(b'100', b'999'))
        self.restart(path)
        self.assertEqual(self.saved()['total'], 200)
        self.assertTrue(self.saved()['uncertain'])

    def test_commander_switches_have_separate_anchors(self):
        a = self.journal(events=[dict(event='Commander', FID='FID-A'), dict(event='Died'), bounty(10)])
        self.arm(a)
        b = self.journal('Journal.2016-09-21T140000.01.log',
                         [dict(event='Commander', FID='FID-B'), dict(event='Died'), bounty(20)])
        self.restart(b, 'FID-B')
        b_bytes = (self.root / 'FID-B.json').read_bytes()
        a_new = self.journal('Journal.2016-09-22T140000.01.log', [dict(event='Commander', FID='FID-A')])
        self.restart(a_new)
        self.assertEqual(self.saved()['total'], 10)
        self.assertEqual(self.saved()['last_event']['file'], str(a_new))
        self.assertEqual((self.root / 'FID-B.json').read_bytes(), b_bytes)

    def test_live_rotation_checkpoints_new_file_without_bounty(self):
        a = self.journal(events=[dict(event='Died'), bounty(10)])
        self.arm(a)
        b = self.journal('Journal.2016-09-21T140000.01.log', [dict(event='Commander', FID='FID-A')])
        self.manager.consume([b])
        self.assertEqual(self.saved()['last_event']['file'], str(b))
        self.append(b, bounty(20))
        self.restart(b)
        self.assertEqual(self.saved()['total'], 30)
        self.assertFalse(self.saved()['uncertain'])

    def test_catchup_write_crash_restarts_at_last_committed_event(self):
        path = self.journal(events=[dict(event='Died'), bounty(10)])
        self.arm(path)
        self.append(path, bounty(10000, 'A'), bounty(20000, 'B'))
        original_save = BountyManager._save
        def fail_second(manager, data):
            if data['total'] == 30010:
                raise OSError('simulated crash before replace')
            original_save(manager, data)
        with patch.object(BountyManager, '_save', fail_second):
            self.restart(path)
        self.assertEqual(self.saved()['total'], 10010)
        self.restart(path)
        self.assertEqual(self.saved()['total'], 30010)
        self.manager.consume([path])
        self.assertEqual(self.saved()['total'], 30010)

    def test_manual_reset_advances_anchor_past_pending_events_and_survives_restart(self):
        path = self.journal(events=[dict(event='Died'), bounty()])
        self.arm(path)
        self.append(path, bounty(10000))  # Not delivered by watcher yet.
        journal_before = path.read_bytes()
        self.assertTrue(self.manager.manual_reset('FID-A'))
        data = self.saved()
        self.assertEqual(data['total'], 0)
        self.assertEqual(data['factions'], {})
        self.assertEqual(data['last_reset'], 'manual')
        self.assertEqual(data['last_event']['offset'], len(journal_before))
        self.assertEqual(data['last_event']['prefix_sha256'], hashlib.sha256(journal_before).hexdigest())
        self.assertEqual(path.read_bytes(), journal_before)
        self.restart(path)
        self.manager.consume([path])
        self.assertEqual(self.saved()['total'], 0)
        self.append(path, bounty(100))
        self.manager.consume([path])
        self.assertEqual(self.saved()['total'], 100)

    def test_manual_reset_changes_only_current_fid(self):
        self.apply(bounty(900), 'FID-B')
        b_bytes = (self.root / 'FID-B.json').read_bytes()
        path = self.journal(events=[dict(event='Died'), bounty()])
        self.arm(path)
        self.assertTrue(self.manager.manual_reset('FID-A'))
        self.assertEqual((self.root / 'FID-B.json').read_bytes(), b_bytes)
        self.manager.identify('FID-B')
        self.assertEqual(self.manager.snapshot()['total'], 900)
        self.manager.identify('FID-A')
        self.assertEqual(self.manager.snapshot()['total'], 0)

    def test_manual_reset_missing_and_corrupt_json(self):
        path = self.journal()
        self.arm(path)
        (self.root / 'FID-A.json').unlink()
        self.assertTrue(self.manager.manual_reset('FID-A'))
        (self.root / 'FID-A.json').write_bytes(b'broken')
        self.restart(path)
        self.assertTrue(self.manager.manual_reset('FID-A'))
        self.assertEqual(self.saved()['total'], 0)
        self.assertFalse(self.saved()['uncertain'])
        self.assertEqual(next(self.root.glob('*.corrupt-*')).read_bytes(), b'broken')

    def test_manual_reset_invalid_anchor_does_not_resurrect_old_kills(self):
        path = self.journal(events=[dict(event='Died'), bounty()])
        self.arm(path)
        self.manager.manual_reset('FID-A')
        data = self.saved()
        data['last_event']['prefix_sha256'] = '0' * 64
        (self.root / 'FID-A.json').write_text(json.dumps(data))
        self.restart(path)
        self.assertEqual(self.saved()['total'], 0)
        self.assertTrue(self.saved()['uncertain'])

    def test_manual_reset_rejects_changed_commander_and_write_failure(self):
        path = self.journal(events=[dict(event='Died'), bounty()])
        self.arm(path)
        before = (self.root / 'FID-A.json').read_bytes()
        self.assertFalse(self.manager.manual_reset('FID-B'))
        with patch('cmdrhelper.bounty_manager.os.replace', side_effect=OSError('full')):
            self.assertFalse(self.manager.manual_reset('FID-A'))
        self.assertEqual((self.root / 'FID-A.json').read_bytes(), before)
        self.append(path, dict(event='Commander', FID='FID-B'))
        self.assertFalse(self.manager.manual_reset('FID-A'))

    def test_reset_dialog_default_cancel_and_cancel_changes_nothing(self):
        from PySide6.QtWidgets import QMessageBox
        path = self.journal(events=[dict(event='Died'), bounty()])
        self.arm(path)
        view = BountyView(self.manager, str)
        self.addCleanup(view.close)
        dialog, confirm = view.reset_dialog()
        self.assertEqual(dialog.defaultButton().text(), 'Abbrechen')
        self.assertIs(dialog.escapeButton(), dialog.defaultButton())
        self.assertEqual(confirm.text(), 'Zurücksetzen')
        self.assertEqual(dialog.windowTitle(), 'Kopfgeldanzeige zurücksetzen?')
        before = (self.root / 'FID-A.json').read_bytes()
        with patch.object(view, 'reset_dialog', return_value=(dialog, confirm)), \
             patch.object(dialog, 'exec', side_effect=lambda: dialog.defaultButton().click()):
            view.confirm_reset()
        self.assertEqual((self.root / 'FID-A.json').read_bytes(), before)
        self.assertEqual(self.manager.snapshot()['total'], 52528)

    def test_reset_dialog_confirm_updates_ui_immediately(self):
        path = self.journal(events=[dict(event='Died'), bounty()])
        self.arm(path)
        view = BountyView(self.manager, str)
        self.addCleanup(view.close)
        dialog, confirm = view.reset_dialog()
        with patch.object(view, 'reset_dialog', return_value=(dialog, confirm)), \
             patch.object(dialog, 'exec', side_effect=confirm.click):
            view.confirm_reset()
        self.assertEqual(self.saved()['total'], 0)
        self.assertTrue(view.table.isHidden())
        self.assertFalse(view.empty.isHidden())
        self.assertEqual(view.total.text(), 'Gesamt: 0')
