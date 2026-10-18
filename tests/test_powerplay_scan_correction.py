"""Synthetic scan rewards; production journals/databases are never test inputs."""
from copy import deepcopy
from datetime import timezone
import unittest

from cmdrhelper.powerplay import PowerplayState
from cmdrhelper.powerplay_chronicle import chronicle_for_day
from cmdrhelper.i18n import tr
from tests.test_powerplay_chronicle import event, scan, credit
from tests.test_powerplay_market_sales import groups, PLACE
from tests import test_powerplay_store as store
from tests import test_powerplay as view_base


def repeated_sequence():
    return [event('Powerplay', -1, Power=PLACE['power'], Merits=1000, Rank=4),
            scan(), credit(1, 10, 1010), scan(21, ScanStage=0),
            scan(21), credit(21, 10, 1020), scan(40), credit(41, 16, 1036)]


class ScanCorrectionTests(unittest.TestCase):
    def test_live_and_historical_rewards_preserve_totals_rank_and_input(self):
        for gain in range(1, 101):
            with self.subTest(gain=gain):
                rows = repeated_sequence() + [scan(60), credit(63, gain, 1036 + gain)]
                original = deepcopy(rows)
                state, reference = PowerplayState(), PowerplayState()
                for row in rows:
                    state.apply(row)
                    reference._apply(row)
                    self.assertEqual((state.merits, state.rank), (reference.merits, reference.rank))
                history = chronicle_for_day(rows, store.DAY, timezone.utc)
                self.assertEqual(history.groups, state.chronicle.groups)
                self.assertEqual([g.certainty for g in history.groups], ['temporal'] * 4)
                self.assertEqual([c['MeritsGained'] for g in history.groups for c in g.credits],
                                 [10, 10, 16, gain])
                self.assertEqual((state.merits, state.rank), (1036 + gain, 4))
                self.assertEqual(rows, original)

    def test_optional_target_fields(self):
        for missing in [('PilotName', 'PilotName_Localised'), ('Ship', 'Ship_Localised'),
                        ('PilotName', 'PilotName_Localised', 'Ship', 'Ship_Localised')]:
            action = scan()
            for key in missing:
                action.pop(key, None)
            result = groups(action, credit(1, 48))
            self.assertEqual(result[0].action, action)
            self.assertEqual(result[0].certainty, 'temporal')

    def test_invalid_amounts_and_outside_window_never_become_scans(self):
        for gain in (0, 101, -1, -10, True, 1.0, 48.5, '16', None):
            with self.subTest(gain=gain):
                self.assertFalse(any(g.action['event'] == 'ShipTargeted'
                                     for g in groups(scan(), credit(1, gain))))
        self.assertEqual(groups(scan(), credit(3, 48))[0].certainty, 'temporal')
        for delay in (3.001, 4):
            self.assertEqual(groups(scan(), credit(delay, 48))[0].certainty, 'unknown')

    def test_credit_and_context_are_required_and_one_scan_cannot_take_two_credits(self):
        self.assertEqual(groups(scan()), [])
        self.assertEqual(groups(credit(1, 48))[0].certainty, 'unknown')
        self.assertEqual(groups(scan(), dict(credit(1, 48), Power='Other'))[0].certainty, 'unknown')
        for middle in (scan(1), event('Bounty', 1), event('FSDJump', 1)):
            self.assertEqual(groups(scan(), middle, credit(1, 48))[-1].certainty, 'unknown')
        result = groups(scan(), credit(1, 48), credit(2, 48))
        self.assertEqual([g.certainty for g in result], ['temporal', 'unknown'])
        self.assertEqual(sum(len(g.credits) for g in result), 2)


class ScanCorrectionStoreTests(unittest.TestCase):
    setUp = store.StoreTests.setUp
    journal = store.StoreTests.journal
    sync = store.StoreTests.sync

    def test_repeat_import_restart_archive_and_display_preserve_facts_and_positions(self):
        from cmdrhelper.database import CMDRDatabase
        session = self.journal(repeated_sequence())
        other = self.journal([scan(), credit(1, 48, 2048)], name='Journal.other.log', fid='B')
        self.sync(session, other)
        def snapshot():
            with self.db._connect() as con:
                return {table: [tuple(r) for r in con.execute('SELECT * FROM ' + table)]
                        for table in ('pp2_events', 'pp2_import_checkpoints', 'journal_sessions', 'journal_imports')}
        before = snapshot()
        self.sync(session, other)
        self.db = CMDRDatabase(self.db.path)
        self.sync(session, other)
        for _ in range(2):
            result = self.db.powerplay_day(session['commander_id'], store.DAY, zone=timezone.utc)
            self.assertEqual([c['MeritsGained'] for g in result.groups for c in g.credits], [10, 10, 16])
            self.assertEqual([g.certainty for g in result.groups], ['temporal'] * 3)
        self.assertEqual(snapshot(), before)
        self.db.import_journal_archive(self.folder)
        after = snapshot()
        self.assertEqual(after['pp2_events'], before['pp2_events'])
        self.assertEqual(self.db.powerplay_merits(session['commander_id']), 1036)
        self.assertEqual(self.db.powerplay_merits(other['commander_id']), 2048)
        result = self.db.powerplay_day(other['commander_id'], store.DAY, zone=timezone.utc)
        self.assertEqual([c['MeritsGained'] for g in result.groups for c in g.credits], [48])


class ScanCorrectionViewTests(unittest.TestCase):
    setUpClass = classmethod(view_base.PowerplayViewTests.setUpClass.__func__)
    setUp = view_base.PowerplayViewTests.setUp

    def test_scan_label_and_existing_unknown_details(self):
        self.state.powerplay = PowerplayState()
        self.state.powerplay.apply(event('ShipTargeted', TargetLocked=True, ScanStage=3))
        self.state.powerplay.apply(credit(1, 48))
        self.view.render()
        self.assertEqual(self.view.recent.rowCount(), 1)
        self.assertEqual(self.view.recent.item(0, 1).text(), tr('pp2.chronicle.ShipTargeted'))
        self.assertEqual(self.view.recent.item(0, 3).text(), '+48')
        self.assertTrue(self.view.recent.item(0, 2).text())
        self.assertEqual(self.view.recent.item(0, 4).text(), '≈')
