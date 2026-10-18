"""Anonymized scan/sale sequences; original journals are never test inputs."""
from copy import deepcopy
from datetime import timedelta, timezone
import unittest
from unittest.mock import patch

from cmdrhelper.powerplay import PowerplayState
from cmdrhelper.powerplay_chronicle import PowerplayChronicle, chronicle_for_day
from cmdrhelper.i18n import _TRANSLATIONS, set_language
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests.test_powerplay_chronicle import event, credit, scan, bounty, delivery
from tests.test_powerplay_market_sales import sale, groups, PLACE
from tests import test_powerplay as view_base
from tests import test_powerplay_store as store


def osmium_sequence():
    return [event('Powerplay', -2, Power=PLACE['power'], Merits=1000, Rank=1),
            event('Docked', -1, StarSystem=PLACE['system'], StationName=PLACE['station']),
            sale(Type='osmium', Count=244),
            event('PowerplayRank', 2, Power=PLACE['power'], Rank=2),
            credit(2, 9069, 10069), event('Cargo', 3, Vessel='Ship', Count=0),
            credit(3, 9069, 19138)]


class ScanSaleTests(unittest.TestCase):
    def test_osmium_group_preserves_events_absolute_totals_and_rank(self):
        rows = osmium_sequence()
        before = deepcopy(rows)
        state, reference = PowerplayState(), PowerplayState()
        for e in rows:
            state.apply(e)
            reference._apply(e)
            self.assertEqual((state.merits, state.rank), (reference.merits, reference.rank))
        self.assertEqual(rows, before)
        self.assertEqual((state.merits, state.rank), (19138, 2))
        self.assertEqual(len(state.chronicle.groups), 1)
        group = state.chronicle.groups[0]
        self.assertEqual((group.action['Type'], group.action['Count'], group.certainty),
                         ('osmium', 244, 'temporal'))
        self.assertEqual(group.credits, [rows[4], rows[6]])
        self.assertEqual(sum(c['MeritsGained'] for c in group.credits), 18138)

    def test_sale_window_is_inclusive_and_never_slides(self):
        result = groups(sale(), credit(2), credit(3), credit(4), credit(5))
        self.assertEqual([len(g.credits) for g in result], [3, 1])
        self.assertEqual([g.certainty for g in result], ['temporal', 'unknown'])
        rare = groups(sale(Type='leestianeviljuice'), credit(2), credit(3))
        self.assertEqual([len(g.credits) for g in rare], [1, 1])

    def test_scan_amounts_window_cargo_and_locker(self):
        for gain in range(1, 101):
            for delay in (0, 1, 3):
                for middle in ([], [event('Cargo')]):
                    self.assertEqual(groups(scan(), *middle, credit(delay, gain))[0].certainty, 'temporal')
            self.assertEqual(groups(scan(), credit(4, gain))[0].certainty, 'unknown')
            self.assertEqual(groups(scan(), event('ShipLocker'), credit(1, gain))[0].certainty, 'unknown')
        for gain in (0, 101, 2000):
            self.assertEqual(groups(scan(), credit(1, gain))[0].certainty, 'unknown')
        for source in (scan(ScanStage=0), scan(ScanStage=1), scan(ScanStage=2),
                       scan(TargetLocked=False), scan(ScanStage=True)):
            self.assertEqual(groups(source, credit(1, 5))[0].certainty, 'unknown')
        self.assertEqual(groups(scan()), [])

    def test_scan_evidence_survives_credits_partial_scans_and_cargo(self):
        for middle in ([], [credit(0, 10)], [credit(0, 99)], [event('Cargo')],
                       [scan(ScanStage=0)], [event('ShipLocker')],
                       [scan(PilotName_Localised='Other pilot')]):
            with self.subTest(middle=middle):
                result = groups(scan(), *middle, sale(1), credit(2, 9069))
                self.assertEqual(result[-1].certainty, 'unknown')
                self.assertFalse(any(g.action['event']=='MarketSell' for g in result))

    def test_scan_after_sale_blocks_later_sale_credits(self):
        for gain in (5, 10, 9069):
            result = groups(sale(), credit(0, 9069), scan(1), event('Cargo', 1), credit(2, gain))
            self.assertEqual(len(result[0].credits), 1)
            self.assertEqual(result[-1].certainty, 'unknown')

    def test_concurrent_scan_completions_are_not_consumed_by_credits(self):
        result = groups(scan(), scan(ScanStage=0, PilotName_Localised='Other'),
                        scan(PilotName_Localised='Other'), credit(0, 10), credit(1, 10))
        self.assertTrue(all(g.certainty=='unknown' for g in result))
        self.assertEqual(sum(len(g.credits) for g in result), 2)

    def test_new_complete_scan_with_same_target_can_receive_own_reward(self):
        result = groups(scan(), credit(0, 10), scan(10), credit(11, 10))
        self.assertEqual([g.certainty for g in result], ['temporal', 'temporal'])
        self.assertEqual(groups(scan(), scan(10)), [])

    def test_rank_and_cargo_cannot_clear_competing_sales_or_actions(self):
        for other in (sale(1, Type='osmium'), scan(1), bounty(1), delivery(1),
                      event('SearchAndRescue', 1, Count=1)):
            result = groups(sale(), other, event('PowerplayRank', 1, Power=PLACE['power'], Rank=2),
                            event('Cargo', 1), credit(1, 9069))
            self.assertEqual(result[-1].certainty, 'unknown')
        for fields in ({'Power':'Other', 'Rank':2}, {'Power':PLACE['power'], 'Rank':True}):
            self.assertEqual(groups(sale(), event('PowerplayRank', 1, **fields), credit(2))[-1].certainty,
                             'unknown')

    def test_session_and_explicit_reset_discard_all_candidates(self):
        for kind in ('Commander', 'LoadGame', 'Fileheader', 'Shutdown', 'PowerplayDefect'):
            result = groups(sale(), event(kind, 1), credit(2))
            self.assertEqual(result[-1].certainty, 'unknown')
        c = PowerplayChronicle()
        c.apply(scan(), **PLACE)
        c.reset_candidates()
        c.apply(sale(1), **PLACE)
        c.apply(credit(2), **PLACE)
        self.assertEqual(c.groups[0].certainty, 'temporal')

    def test_expired_causes_do_not_block_new_sale_and_context_is_required(self):
        result = groups(scan(), sale(4), credit(5, 9069), credit(8, 9069))
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0].credits), 2)
        for field in PLACE:
            for value in ('', 'changed'):
                c = PowerplayChronicle()
                c.apply(sale(), **PLACE)
                c.apply(credit(1), **dict(PLACE, **{field:value}))
                self.assertEqual(c.groups[-1].certainty, 'unknown')

    def test_rare_rank_barrier_and_delivery_windows_stay_unchanged(self):
        result = groups(sale(Type='leestianeviljuice'),
                        event('PowerplayRank', 1, Power=PLACE['power'], Rank=2), credit(2))
        self.assertEqual([g.certainty for g in result], ['explicit', 'unknown'])
        self.assertEqual(groups(delivery(), credit(4))[-1].certainty, 'unknown')
        self.assertEqual(groups(bounty(), credit(2))[-1].certainty, 'unknown')


class ScanSaleStoreTests(unittest.TestCase):
    setUp = store.StoreTests.setUp
    journal = store.StoreTests.journal
    sync = store.StoreTests.sync

    def test_reimport_restart_and_archive_preserve_two_credits_once(self):
        session = self.journal(osmium_sequence())
        self.sync(session)
        self.sync(session)
        from cmdrhelper.database import CMDRDatabase
        self.db = CMDRDatabase(self.db.path)
        self.db.import_journal_archive(self.folder)
        result = self.db.powerplay_day(session['commander_id'], store.DAY, zone=timezone.utc)
        self.assertEqual(len(result.groups), 1)
        self.assertEqual([c['MeritsGained'] for c in result.groups[0].credits], [9069, 9069])
        self.assertEqual(self.db.powerplay_merits(session['commander_id']), 19138)
        with self.db._connect() as con:
            self.assertEqual(con.execute("SELECT count(*) FROM pp2_events WHERE event_type='PowerplayMerits'").fetchone()[0], 2)
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], 23)

    def test_stored_scan_competition_matches_memory(self):
        rows = osmium_sequence()[:2] + [scan(), event('Cargo'), scan(ScanStage=0), sale(1), credit(2)]
        session = self.journal(rows)
        self.sync(session)
        result = self.db.powerplay_day(session['commander_id'], store.DAY, zone=timezone.utc)
        memory = chronicle_for_day(rows, store.DAY, timezone.utc)
        self.assertEqual(result.groups, memory.groups)
        self.assertEqual(result.groups[-1].certainty, 'unknown')

    def test_scan_evidence_does_not_cross_source_or_commander(self):
        context = osmium_sequence()[:2]
        first = self.journal(context+[scan()], name='Journal.first.log')
        second = self.journal(context+[sale(1), credit(2)], name='Journal.second.log')
        other = self.journal(context+[scan()], name='Journal.other.log', fid='B')
        self.sync(first, second, other)
        result = self.db.powerplay_day(first['commander_id'], store.DAY, zone=timezone.utc)
        self.assertEqual(len(result.groups), 1)
        self.assertEqual(result.groups[0].action['event'], 'MarketSell')
        self.assertEqual(result.groups[0].certainty, 'temporal')
        self.assertEqual(self.db.powerplay_day(other['commander_id'], store.DAY, zone=timezone.utc).groups, [])


class ScanSaleViewTests(unittest.TestCase):
    setUpClass = classmethod(view_base.PowerplayViewTests.setUpClass.__func__)
    setUp = view_base.PowerplayViewTests.setUp

    def test_sum_tooltips_day_order_languages_and_themes(self):
        from PySide6.QtCore import QLocale
        self.addCleanup(set_language, 'de')
        self.state.powerplay = PowerplayState()
        for e in osmium_sequence()+[sale(10, Type='gold'), credit(11, 5, 19143)]:
            self.state.powerplay.apply(e)
        for language in _TRANSLATIONS:
            set_language(language)
            for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                self.view.setStyleSheet(theme)
                with patch('cmdrhelper.ui.powerplay_view.local_today', return_value=store.DAY):
                    for _ in range(2):
                        self.view.render()
                        table = self.view.recent
                        self.assertEqual(table.rowCount(), 2)
                        self.assertEqual(table.item(0,3).text(), '+5')
                        self.assertEqual(table.item(1,3).text(), '+'+QLocale(language).toString(18138))
                        self.assertEqual(table.item(1,4).text(), '≈')
                        tip = table.item(1,3).toolTip()
                        for value in (9069, 10069, 19138):
                            self.assertIn(QLocale(language).toString(value), tip)
                    self.view.selected_day = store.DAY-timedelta(days=1)
                    self.view.render()
                    self.assertEqual(table.rowCount(), 0)
                    self.view.selected_day = None
