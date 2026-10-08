"""Rare sales are proven activities, never merit or assignment attribution."""
from datetime import date, timedelta
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from cmdrhelper.powerplay_chronicle import chronicle_for_day, is_rare_sale, today_groups
from cmdrhelper.i18n import set_language
from tests.test_powerplay_chronicle import event, bounty, credit, delivery, replay
from tests import test_powerplay as base
from tests import test_powerplay_store as store


FIXTURE = json.loads((Path(__file__).parent / 'fixtures/powerplay_rare_sale_20261008.json').read_text())
REAL = FIXTURE['events']
SALE = next(e for e in REAL if e['event'] == 'MarketSell')
DAY = date(2026, 10, 8)


def sale(**fields):
    return dict(event('MarketSell', Type='leestianeviljuice',
                      Type_Localised='Leesti-Teufelssaft', Count=12), **fields)


class RareSaleTests(unittest.TestCase):
    def test_real_sale_and_both_unassigned_credits(self):
        groups = replay(*REAL).chronicle.groups
        self.assertEqual(len(groups), 2)
        sold, unknown = groups
        self.assertEqual(sold.action, SALE)
        self.assertEqual((sold.station, sold.system, sold.power),
                         ('Peebles Holdings', 'Crucis Sector HC-U b3-5', 'Nakato Kaine'))
        self.assertEqual(sold.certainty, 'explicit')
        self.assertEqual(sold.credits, [])
        self.assertEqual(unknown.certainty, 'unknown')
        self.assertEqual([e['MeritsGained'] for e in unknown.credits], [6, 3600])

    def test_sale_alone_and_missing_context(self):
        groups = replay(sale()).chronicle.groups
        self.assertEqual(len(groups), 1)
        self.assertEqual((groups[0].system, groups[0].station), ('', ''))
        self.assertEqual(groups[0].credits, [])

    def test_only_known_rare_identity_and_positive_integer_count(self):
        for count in (None, 0, -1, True, False, 12.0, '12', [], {}, 2**63):
            with self.subTest(count=count):
                self.assertFalse(is_rare_sale(sale(Count=count)))
                self.assertEqual(replay(sale(Count=count)).chronicle.groups, [])
        missing = sale()
        del missing['Count']
        self.assertEqual(replay(missing).chronicle.groups, [])
        for token in ('gold', 'unknowncommodity', '', None):
            with self.subTest(token=token):
                self.assertEqual(replay(sale(Type=token)).chronicle.groups, [])
        for token in ('LeestianEvilJuice', '$leestianeviljuice_name;'):
            self.assertTrue(is_rare_sale(sale(Type=token)))
        for timestamp in (None, '', 'invalid', '2026-10-08T12:27:32'):
            self.assertFalse(is_rare_sale(sale(timestamp=timestamp)))

    def test_all_sales_are_barriers_in_both_directions(self):
        for source in (bounty(), delivery()):
            for sold in (sale(), sale(Type='gold'), sale(Count=0)):
                with self.subTest(source=source, sold=sold):
                    groups = replay(source, sold, credit(0, 6), credit(0, 3600)).chronicle.groups
                    self.assertEqual(groups[-1].certainty, 'unknown')
                    self.assertEqual([e['MeritsGained'] for e in groups[-1].credits], [6, 3600])
                    self.assertTrue(all(not g.credits for g in groups[:-1]))
        groups = replay(credit(0, 1), sale(), credit(1, 6)).chronicle.groups
        self.assertEqual([g.certainty for g in groups], ['unknown', 'explicit', 'unknown'])

    def test_day_boundary_and_local_day_filter(self):
        before = sale(timestamp='2026-10-08T21:59:59Z')
        after = dict(credit(gain=6), timestamp='2026-10-08T22:00:00Z')
        old = chronicle_for_day([before, after], DAY, store.ZONE)
        new = chronicle_for_day([before, after], DAY + timedelta(days=1), store.ZONE)
        self.assertEqual([g.action['event'] for g in today_groups(old, DAY, store.ZONE)], ['MarketSell'])
        self.assertEqual([g.certainty for g in new.groups], ['unknown'])


class RareSaleStoreTests(unittest.TestCase):
    setUp = store.StoreTests.setUp
    journal = store.StoreTests.journal
    sync = store.StoreTests.sync

    def snapshot(self):
        with self.db._connect() as con:
            return {table: con.execute('SELECT * FROM ' + table).fetchall() for table in store.PP_TABLES}

    def test_historical_zero_fact_replay_and_preview_are_read_only(self):
        session = self.journal(REAL, fid='F_TEST_PP2_RARE_SALE')
        self.sync(session)
        cid = session['commander_id']
        with self.db._connect() as con:
            self.assertEqual(con.execute("SELECT is_fact FROM pp2_events WHERE event_type='MarketSell'").fetchone()[0], 0)
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], 23)
        before = self.snapshot()
        # Replay must work after the journal is gone, without sync/reimport.
        Path(session['journal_file']).unlink()
        groups = self.db.powerplay_day(cid, DAY, zone=store.ZONE).groups
        self.assertEqual([g.certainty for g in groups], ['explicit', 'unknown'])
        self.assertEqual(groups[0].action['Count'], 12)
        self.assertEqual(groups[0].station, 'Peebles Holdings')
        self.assertEqual(groups[0].credits, [])
        self.assertEqual([c['MeritsGained'] for c in groups[1].credits], [6, 3600])
        preview = self.db.powerplay_delete_preview(cid, zone=store.ZONE)
        # Preview counts source facts, not display groups: sale + two credits.
        self.assertEqual((preview['events'], preview['days']), (3, 1))
        for days in (7, 30):
            retained = DAY + timedelta(days=days-1)
            self.assertEqual(self.db.powerplay_delete_preview(cid, days, day=retained, zone=store.ZONE)['events'], 0)
            self.assertEqual(self.db.powerplay_delete_preview(cid, days, day=retained+timedelta(days=1), zone=store.ZONE)['events'], 3)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.db.powerplay_merits(cid), 88861)

    def test_preview_excludes_normal_and_invalid_sales_and_respects_deletion(self):
        session = self.journal([sale(), sale(Type='gold'), sale(Count=0), sale(Count=None)])
        self.sync(session)
        cid = session['commander_id']
        preview = self.db.powerplay_delete_preview(cid, zone=store.ZONE)
        self.assertEqual((preview['events'], preview['days']), (1, 1))
        self.assertEqual(len(self.db.powerplay_day(cid, store.DAY, zone=store.ZONE).groups), 1)
        self.db.delete_powerplay_history(cid, preview)
        self.sync(session)
        self.assertEqual(self.db.powerplay_day(cid, store.DAY, zone=store.ZONE).groups, [])
        self.assertEqual(self.db.powerplay_delete_preview(cid)['events'], 0)


class RareSaleViewTests(unittest.TestCase):
    setUpClass = classmethod(base.PowerplayViewTests.setUpClass.__func__)
    setUp = base.PowerplayViewTests.setUp

    def test_real_sale_text_and_evidence_in_german_and_english(self):
        self.addCleanup(set_language, 'de')
        self.state.powerplay = replay(*REAL)
        for language, title, caution in (
                ('de', 'Seltene Waren verkauft', 'keinen Wochenauftragsabschluss'),
                ('en', 'Rare goods sold', 'not a merit cause or weekly assignment completion')):
            set_language(language)
            with patch('cmdrhelper.ui.powerplay_view.local_today', return_value=DAY):
                self.view.render()
            table = self.view.recent
            self.assertEqual(table.rowCount(), 2)
            self.assertEqual(table.item(0, 4).text(), '?')
            self.assertEqual(table.item(1, 1).text(), title)
            self.assertEqual(table.item(1, 2).text(),
                             '12 t Leesti-Teufelssaft\nPeebles Holdings · Crucis Sector HC-U b3-5')
            self.assertEqual(table.item(1, 3).text(), '—')
            self.assertEqual(table.item(1, 4).text(), '✓')
            self.assertIn(caution, table.item(1, 4).toolTip())


class RareSaleHistoryViewTests(unittest.TestCase):
    setUpClass = classmethod(base.PowerplayViewTests.setUpClass.__func__)
    setUp = store.StoreTests.setUp
    journal = store.StoreTests.journal
    sync = store.StoreTests.sync

    def test_navigation_counts_sale_without_credits(self):
        session = self.journal([sale()])
        self.sync(session)
        state = base.ViewState()
        state.database = self.db
        state.commander_id = session['commander_id']
        with patch('cmdrhelper.ui.powerplay_view.local_today', return_value=store.DAY+timedelta(days=1)):
            view = base.PowerplayView(state)
            self.addCleanup(view.close)
            self.assertEqual(view.recent.rowCount(), 0)
            view._move_day(-1)
            self.assertEqual(view.recent.rowCount(), 1)
            self.assertEqual(view.recent.item(0, 3).text(), '—')
            view._today()
            self.assertEqual(view.recent.rowCount(), 0)
