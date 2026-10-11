"""Rare sales are proven activities with conservative temporal merit links."""
from datetime import date, timedelta
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from cmdrhelper.powerplay_chronicle import chronicle_for_day, is_rare_sale, today_groups
from cmdrhelper.i18n import set_language
from tests.test_powerplay_chronicle import event, bounty, scan, credit, delivery, replay
from cmdrhelper.powerplay_chronicle import PowerplayChronicle
from tests import test_powerplay as base
from tests import test_powerplay_store as store


FIXTURE = json.loads((Path(__file__).parent / 'fixtures/powerplay_rare_sale_20261008.json').read_text())
REAL = FIXTURE['events']
SALE = next(e for e in REAL if e['event'] == 'MarketSell')
DAY = date(2026, 10, 8)


def sale(**fields):
    return dict(event('MarketSell', Type='leestianeviljuice',
                      Type_Localised='Leesti-Teufelssaft', Count=12), **fields)


PLACE = dict(system='Col 285 Sector GJ-T b19-1', station='Morrison Hub', power='Nakato Kaine')
SOONTILL = [
    dict(event='Powerplay', timestamp='2026-10-11T07:33:11Z', Power='Nakato Kaine', Rank=15, Merits=95601),
    dict(event='Docked', timestamp='2026-10-11T09:02:27Z', StationName=PLACE['station'],
         StarSystem=PLACE['system'], MarketID=4369513219),
    dict(event='MarketSell', timestamp='2026-10-11T09:03:08Z', MarketID=4369513219,
         Type='soontillrelics', Type_Localised='Soontill-Relikte', Count=400,
         SellPrice=39766, TotalSale=15906400, AvgPricePaid=17000),
    dict(event='PowerplayMerits', timestamp='2026-10-11T09:03:09Z', Power='Nakato Kaine',
         MeritsGained=15906, TotalMerits=111507),
    dict(event='PowerplayRank', timestamp='2026-10-11T09:03:09Z', Power='Nakato Kaine', Rank=17),
    dict(event='Cargo', timestamp='2026-10-11T09:03:10Z', Vessel='Ship', Count=0),
]


def at_station(*events):
    chronicle = PowerplayChronicle()
    for e in events:
        chronicle.apply(e, **PLACE)
    return chronicle.groups


class RareSaleTests(unittest.TestCase):
    def test_soontill_original_and_absolute_personal_state(self):
        state = replay(*SOONTILL)
        self.assertEqual((state.merits, state.rank), (111507, 17))
        group, = state.chronicle.groups
        self.assertEqual(group.certainty, 'temporal')
        self.assertEqual(group.action, SOONTILL[2])
        self.assertEqual(group.credits, [SOONTILL[3]])
        self.assertEqual((group.station, group.system), (PLACE['station'], PLACE['system']))

    def test_inclusive_two_second_window_and_reverse_order(self):
        for second in (-1, 0, 1, 2, 3):
            with self.subTest(second=second):
                groups = at_station(sale(), credit(second))
                if 0 <= second <= 2:
                    self.assertEqual(len(groups), 1)
                    self.assertEqual(groups[0].certainty, 'temporal')
                    self.assertEqual(groups[0].credits, [credit(second)])
                else:
                    self.assertEqual([g.certainty for g in groups], ['explicit', 'unknown'])
        self.assertEqual([g.certainty for g in at_station(credit(0), sale())], ['unknown', 'explicit'])
        group, = at_station(sale())
        self.assertEqual((group.certainty, group.credits), ('explicit', []))

    def test_context_and_power_must_be_known_and_equal(self):
        for field in PLACE:
            for value in ('', ' ', None, 'different'):
                with self.subTest(field=field, value=value):
                    c = PowerplayChronicle()
                    c.apply(sale(), **PLACE)
                    c.apply(credit(), **dict(PLACE, **{field: value}))
                    self.assertEqual(c.groups[-1].certainty, 'unknown')
            for value in ('', ' ', None):
                c = PowerplayChronicle()
                c.apply(sale(), **dict(PLACE, **{field: value}))
                c.apply(credit(), **PLACE)
                self.assertEqual(c.groups[-1].certainty, 'unknown')
        groups = at_station(sale(), dict(credit(), Power='Edmund Mahon'))
        self.assertEqual(groups[-1].certainty, 'unknown')

    def test_invalid_sales_never_link_even_with_context(self):
        for fields in ({'Type': 'gold'}, {'Type': 'unknown'}, {'Type': None},
                       {'Count': 0}, {'Count': -1}, {'Count': True}, {'Count': '400'},
                       {'timestamp': 'invalid'}, {'timestamp': '2026-10-11T09:03:08'}):
            with self.subTest(fields=fields):
                groups = at_station(sale(**fields), credit())
                self.assertEqual([g.certainty for g in groups], ['unknown'])

    def test_barriers_and_journal_boundaries(self):
        for kind in ('Cargo', 'PowerplayRank', 'Docked', 'Undocked', 'FSDJump',
                     'Fileheader', 'LoadGame', 'Shutdown', 'PowerplayJoin', 'PowerplayDefect',
                     'PowerplayLeave', 'Market', 'UnknownFutureEvent'):
            with self.subTest(kind=kind):
                groups = at_station(sale(), event(kind), credit())
                self.assertEqual([g.certainty for g in groups], ['explicit', 'unknown'])
        group, = at_station(sale(), event('Music'), event('Friends'), event('ReceiveText'), credit())
        self.assertEqual(group.certainty, 'temporal')

    def test_competing_actions_in_both_directions_and_after_credits(self):
        actions = [sale(), bounty(), scan(), delivery(), event('SearchAndRescue', Count=1)]
        for action in actions:
            for sequence in ((sale(), action), (action, sale()),
                             (sale(), credit(0), action), (action, credit(0), sale()),
                             (sale(), action, credit(0), sale())):
                with self.subTest(sequence=sequence):
                    groups = at_station(*sequence, credit(1, 10), credit(2, 20))
                    self.assertEqual(groups[-1].certainty, 'unknown')
                    self.assertEqual(groups[-1].credits[-2:], [credit(1, 10), credit(2, 20)])

    def test_separate_identical_and_inconsistent_merit_reports(self):
        credits = [credit(0, 6, 100), credit(1, 3600, 99), credit(1, 3600, 99), credit(2, 10, 109)]
        group, = at_station(sale(), *credits)
        self.assertEqual(group.credits, credits)
        groups = at_station(sale(), *credits, credit(3))
        self.assertEqual(groups[-1].certainty, 'unknown')
        self.assertEqual(groups[0].credits, credits)

    def test_real_sale_and_both_temporal_credits(self):
        groups = replay(*REAL).chronicle.groups
        self.assertEqual(len(groups), 1)
        sold = groups[0]
        self.assertEqual(sold.action, SALE)
        self.assertEqual((sold.station, sold.system, sold.power),
                         ('Peebles Holdings', 'Crucis Sector HC-U b3-5', 'Nakato Kaine'))
        self.assertEqual(sold.certainty, 'temporal')
        self.assertEqual([e['MeritsGained'] for e in sold.credits], [6, 3600])

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

    def test_sales_without_context_cannot_link_in_either_direction(self):
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
        context = [dict(SOONTILL[0], timestamp='2026-10-08T21:59:57Z'),
                   dict(SOONTILL[1], timestamp='2026-10-08T21:59:58Z')]
        old = chronicle_for_day([*context, before, after], DAY, store.ZONE)
        new = chronicle_for_day([*context, before, after], DAY + timedelta(days=1), store.ZONE)
        self.assertEqual([g.action['event'] for g in today_groups(old, DAY, store.ZONE)], ['MarketSell'])
        self.assertEqual([g.certainty for g in new.groups], ['unknown'])


class RareSaleStoreTests(unittest.TestCase):
    setUp = store.StoreTests.setUp
    journal = store.StoreTests.journal
    sync = store.StoreTests.sync

    def test_source_boundary_and_sequence_gap_block_rare_link(self):
        context = [event('Powerplay', Power=PLACE['power'], Merits=100),
                   event('Docked', StarSystem=PLACE['system'], StationName=PLACE['station'])]
        first = self.journal([*context, sale()])
        second = self.journal([credit()], name='Journal.second.log')
        self.sync(first, second)
        cid = first['commander_id']
        # Make contexts/sequences match in the temporary DB so that the source
        # boundary itself is the only reason this link must be rejected.
        with self.db._connect() as con:
            context_json = con.execute("SELECT context_json FROM pp2_events WHERE event_type='MarketSell'").fetchone()[0]
            stored_context = json.loads(context_json)
            stored_context['sequence'] += 1
            con.execute("UPDATE pp2_events SET context_json=? WHERE event_type='PowerplayMerits'",
                        (json.dumps(stored_context),))
        groups = self.db.powerplay_day(cid, store.DAY, zone=store.ZONE).groups
        self.assertEqual([g.certainty for g in groups], ['explicit', 'unknown'])

        # Remove a barrier only in the temporary test DB: its sequence gap must
        # still prevent a correlation, even with identical stored context.
        third = self.journal([*context, sale(), event('Cargo'), credit()],
                             name='Journal.gap.log', fid='GAP')
        self.sync(third)
        with self.db._connect() as con:
            con.execute("DELETE FROM pp2_events WHERE commander_id=? AND event_type='Cargo'",
                        (third['commander_id'],))
        before = self.snapshot()
        groups = self.db.powerplay_day(third['commander_id'], store.DAY, zone=store.ZONE).groups
        self.assertEqual([g.certainty for g in groups], ['explicit', 'unknown'])
        self.assertEqual(self.snapshot(), before)

    def test_soontill_replay_preserves_history_total_and_schema(self):
        session = self.journal(SOONTILL, fid='SOONTILL')
        self.sync(session)
        before = self.snapshot()
        group, = self.db.powerplay_day(session['commander_id'], date(2026, 10, 11), zone=store.ZONE).groups
        self.assertEqual(group.certainty, 'temporal')
        self.assertEqual(group.credits, [SOONTILL[3]])
        self.assertEqual(self.db.powerplay_merits(session['commander_id']), 111507)
        self.assertEqual(self.snapshot(), before)
        with self.db._connect() as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], 23)

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
        self.assertEqual([g.certainty for g in groups], ['temporal'])
        self.assertEqual(groups[0].action['Count'], 12)
        self.assertEqual(groups[0].station, 'Peebles Holdings')
        self.assertEqual([c['MeritsGained'] for c in groups[0].credits], [6, 3600])
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

    def test_soontill_display_and_tooltip(self):
        self.addCleanup(set_language, 'de')
        set_language('de')
        self.state.powerplay = replay(*SOONTILL)
        with patch('cmdrhelper.ui.powerplay_view.local_today', return_value=date(2026, 10, 11)):
            self.view.render()
        table = self.view.recent
        self.assertEqual(table.rowCount(), 1)
        self.assertEqual(table.item(0, 1).text(), 'Seltene Waren verkauft')
        self.assertEqual(table.item(0, 2).text(),
                         '400 t Soontill-Relikte\nMorrison Hub · Col 285 Sector GJ-T b19-1')
        self.assertEqual(table.item(0, 3).text(), '+15.906')
        self.assertEqual(table.item(0, 4).text(), '≈')
        tooltip = table.item(0, 4).toolTip()
        for phrase in ('1 s nach', 'keine direkte Zuordnung', 'keine Merit-Ursache',
                       '2026-10-11T09:03:08Z', '2026-10-11T09:03:09Z', '111.507'):
            self.assertIn(phrase, tooltip)

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
            self.assertEqual(table.rowCount(), 1)
            self.assertEqual(table.item(0, 1).text(), title)
            self.assertEqual(table.item(0, 2).text(),
                             '12 t Leesti-Teufelssaft\nPeebles Holdings · Crucis Sector HC-U b3-5')
            self.assertEqual(table.item(0, 3).text(), '+6 / +' + base.QLocale(language).toString(3600))
            self.assertEqual(table.item(0, 4).text(), '≈')
            self.assertIn(caution, table.item(0, 4).toolTip())


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
