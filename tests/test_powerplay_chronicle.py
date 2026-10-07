"""Conservative journal adjacency and the PP2 chronicle table."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cmdrhelper.powerplay import PowerplayState
from cmdrhelper.journal_reader import read_latest_state, classify_journal_file
from tests import test_powerplay as base


def event(kind, second=0, **fields):
    return dict(event=kind, timestamp=(datetime(2026, 10, 6, 11, 13, 36, tzinfo=timezone.utc)
                                      + timedelta(seconds=second)).isoformat(), **fields)


def credit(second=1, gain=60, total=100):
    return event('PowerplayMerits', second, Power='Nakato Kaine', MeritsGained=gain, TotalMerits=total)


def bounty(second=0):
    return event('Bounty', second, PilotName_Localised='Jim Bell', Target='federation_dropship',
                 Target_Localised='Federal Dropship', TotalReward=453097)


def scan(second=0, **fields):
    return event('ShipTargeted', second, **dict(dict(TargetLocked=True, ScanStage=3,
                 PilotName_Localised='Morgan Stattin', Ship='type7', Ship_Localised='Type-7 Transporter'), **fields))


def delivery(second=0, kind='PowerplayDeliver'):
    return event(kind, second, Power='Nakato Kaine', Type='kainemisinformation',
                 Type_Localised='Kaine-Fehlinformationen', Count=10)


def replay(*events):
    state = PowerplayState(power='Nakato Kaine', merits=9183)
    for e in events:
        state.apply(e)
    return state


class ChronicleTests(unittest.TestCase):
    def setUp(self):
        clock = patch('cmdrhelper.powerplay_chronicle.local_today', return_value=datetime(2026, 10, 6).date())
        clock.start()
        self.addCleanup(clock.stop)

    def test_bounty_with_target_loss_and_multiple_credits(self):
        state = replay(bounty(), event('ShipTargeted', TargetLocked=False), credit(), credit(gain=3200, total=3300))
        groups = state.chronicle.groups
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].certainty, 'temporal')
        self.assertEqual(groups[0].action['PilotName_Localised'], 'Jim Bell')
        self.assertEqual([c['MeritsGained'] for c in groups[0].credits], [60, 3200])
        self.assertEqual(replay(bounty()).chronicle.groups, [])

    def test_scan_requires_actual_complete_scan_and_matching_first_credit(self):
        for second in (0, 1, 3):
            group = replay(scan(), credit(second, 10)).chronicle.groups[0]
            self.assertEqual(group.certainty, 'temporal')
        for source in [scan(ScanStage=2), scan(TargetLocked=False), scan(ScanStage=True),
                       event('Scan', ScanType='Detailed'), event('DataScanned')]:
            self.assertEqual(replay(source, credit(gain=10)).chronicle.groups[0].certainty, 'unknown')
        self.assertEqual(replay(scan(), credit(gain=9)).chronicle.groups[0].certainty, 'unknown')
        state = replay(scan(), credit(gain=10), credit(gain=10))
        self.assertEqual([g.certainty for g in state.chronicle.groups], ['temporal', 'unknown'])

    def test_salvage_requires_adjacency(self):
        action = event('SearchAndRescue', Name='usscargoblackbox', Name_Localised='Black Box', Count=2)
        group = replay(action, credit(0, 194)).chronicle.groups[0]
        self.assertEqual(group.certainty, 'temporal')
        self.assertEqual(group.action['Count'], 2)
        state = replay(action, event('Cargo', Count=5), credit(0, 194))
        self.assertEqual(state.chronicle.groups[0].certainty, 'unknown')

    def test_explicit_transport_groups_only_same_second_delivery_credits(self):
        state = replay(delivery(kind='PowerplayCollect'), delivery(10), credit(10, 3600, 12783), credit(10, 48, 12831))
        self.assertEqual(len(state.chronicle.groups), 2)
        self.assertTrue(all(g.certainty == 'explicit' for g in state.chronicle.groups))
        self.assertEqual([c['MeritsGained'] for c in state.chronicle.groups[1].credits], [3600, 48])
        state.apply(credit(11, 10))
        self.assertEqual(state.chronicle.groups[-1].certainty, 'unknown')
        state = replay(delivery(kind='PowerplayCollect'), credit(0, 10))
        self.assertEqual([g.certainty for g in state.chronicle.groups], ['explicit', 'unknown'])

    def test_windows_invalid_times_and_intervening_actions(self):
        for action, late in [(bounty(), 2), (scan(), 4), (event('SearchAndRescue'), 2)]:
            for second in (-1, late):
                self.assertEqual(replay(action, credit(second, 10)).chronicle.groups[0].certainty, 'unknown')
        for kind in ('Cargo', 'MarketSell', 'FSDJump', 'Docked', 'Undocked', 'UnderAttack',
                     'Fileheader', 'LoadGame', 'UnknownFutureEvent', 'MaterialCollected'):
            with self.subTest(kind=kind):
                self.assertEqual(replay(bounty(), event(kind), credit()).chronicle.groups[0].certainty, 'unknown')
        for time in ('', 'invalid', '2026-10-06T11:13:36'):
            action = dict(bounty(), timestamp=time)
            self.assertEqual(replay(action, credit()).chronicle.groups[0].certainty, 'unknown')

    def test_ambiguous_candidates_and_noisy_but_safe_sequence(self):
        for actions in [(bounty(), scan()), (scan(), bounty()), (delivery(), bounty())]:
            self.assertEqual(replay(*actions, credit(0, 10)).chronicle.groups[-1].certainty, 'unknown')
        state = replay(bounty(), event('Music'), event('ReceiveText'), event('Friends'), credit())
        self.assertEqual(state.chronicle.groups[0].certainty, 'temporal')

    def test_unknown_burst_preserves_inconsistent_totals_without_summing(self):
        state = replay(credit(0, 10, 13241), credit(2, 4, 13233), credit(2, 13, 13246), credit(5, 10, 13256))
        self.assertEqual(state.merits, 13256)
        self.assertEqual(len(state.chronicle.groups), 1)
        self.assertEqual(state.chronicle.groups[0].certainty, 'unknown')
        self.assertEqual([c['MeritsGained'] for c in state.chronicle.groups[0].credits], [10, 4, 13, 10])
        state.apply(event('PowerplayMerits', 6, Power='Nakato Kaine', MeritsGained=100))
        self.assertEqual(state.merits, 13256)
        state.apply(event('Cargo', 7, Count=0))
        state.apply(credit(8))
        self.assertEqual(len(state.chronicle.groups), 2)

    def test_no_group_limit_independent_of_old_raw_event_limit(self):
        state = replay()
        for second in range(20):
            state.apply(delivery(second * 10))
            state.apply(credit(second * 10, 3600))
            state.apply(credit(second * 10, 48))
        self.assertEqual(len(state.chronicle.groups), 20)
        self.assertEqual(sum(len(g.credits) for g in state.chronicle.groups), 40)
        self.assertEqual(state.chronicle.groups[0].action['timestamp'], delivery(0)['timestamp'])

    def test_context_reset_and_local_journal_reconstruction(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            path = folder/'Journal.2026-10-06T100000.01.log'
            rows = [event('Commander', FID='A', Name='Test'), event('Powerplay', Power='Nakato Kaine', Merits=9183),
                    event('Docked', StarSystem='HIP 70049', StationName='Mille Enterprise'), delivery()]
            path.write_text(''.join(json.dumps(e)+'\n' for e in rows))
            sessions = [classify_journal_file(path)]
            initial = read_latest_state(folder, indexed_sessions=sessions)['powerplay']
            self.assertEqual(initial.chronicle.groups[0].station, 'Mille Enterprise')
            with path.open('a') as f:
                f.write(json.dumps(credit(0, 3600, 12783))+'\n'+json.dumps(credit(0, 48, 12831))+'\n')
            first = read_latest_state(folder, indexed_sessions=sessions)['powerplay']
            second = read_latest_state(folder, indexed_sessions=sessions)['powerplay']
            self.assertEqual(first, second)
            self.assertEqual(len(first.chronicle.groups), 1)
            self.assertEqual(len(first.chronicle.groups[0].credits), 2)
            first.apply(event('PowerplayLeave', Power='Nakato Kaine'))
            self.assertEqual(first.chronicle.groups, [])


class ChronicleViewTests(unittest.TestCase):
    setUpClass = classmethod(base.PowerplayViewTests.setUpClass.__func__)
    setUp = base.PowerplayViewTests.setUp

    def test_table_details_symbols_and_tooltips(self):
        self.state.powerplay = replay(bounty(), credit(), event('Cargo', 2),
                                     delivery(3), credit(3, 3600, 12783), credit(3, 48, 12831),
                                     event('Cargo', 4), credit(10, 3, 12834))
        self.state.changed.emit()
        table = self.view.recent
        self.assertEqual(table.rowCount(), 3)
        self.assertEqual([table.item(r, 4).text() for r in range(3)], ['?', '✓', '≈'])
        self.assertIn('keinen Vergütungsgrund', table.item(0, 4).toolTip())
        self.assertIn('direkt im Elite-Journal', table.item(1, 4).toolTip())
        self.assertIn('Vergütungsgründe sind nicht belegt', table.item(1, 4).toolTip())
        self.assertIn('1 s nach', table.item(2, 4).toolTip())
        self.assertIn('keine direkte Zuordnung', table.item(2, 4).toolTip())
        self.assertEqual(table.item(1, 3).text(), '+3.600 / +48')
        self.assertIn('Jim Bell · Federal Dropship · 453.097 Cr', table.item(2, 2).text())
        self.assertIn(bounty()['timestamp'], table.item(2, 0).toolTip())
        self.assertNotIn('abgeschlossen', base.table_text(self.view))

    def test_today_older_and_compact_unknown_block(self):
        today = datetime.now().astimezone().replace(hour=10, minute=12, second=23, microsecond=0)
        self.state.powerplay = replay()
        for n in range(8):
            self.state.powerplay.apply(dict(credit(n, n+1), timestamp=(today+timedelta(seconds=n)).isoformat()))
        with patch('cmdrhelper.ui.powerplay_view.local_today', return_value=today.date()):
            self.state.changed.emit()
        table = self.view.recent
        self.assertEqual(table.rowCount(), 1)
        self.assertEqual(table.item(0, 0).text(), '10:12')
        self.assertEqual(table.item(0, 3).text(), '+1 / +2 / +3 / +4 / +5 / …')
        self.assertIn('+8 Merits', table.item(0, 3).toolTip())
        self.assertIn(today.isoformat(), table.item(0, 0).toolTip())

    def test_missing_details_are_not_invented(self):
        self.state.powerplay = replay(event('Bounty'), credit())
        self.state.changed.emit()
        self.assertEqual(self.view.recent.item(0, 2).text(), 'Unbekannt')
