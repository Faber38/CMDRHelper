"""Reported quantities/gains, synthetic context and credit times (no source journal supplied)."""
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import unittest
from unittest.mock import patch

from cmdrhelper.i18n import _TRANSLATIONS, set_language, tr_for_language
from cmdrhelper.powerplay import PowerplayState
from cmdrhelper.powerplay_chronicle import PowerplayChronicle
from tests.test_powerplay_chronicle import event, credit, bounty, delivery, scan
from tests import test_powerplay as view_base
from tests import test_powerplay_store as store

# Only these UTC sale times, commodities, quantities and gains were supplied.
# Date, contexts, initial totals, rank and +1 s merit timestamps below are synthetic.
CASES = [('07:03:17', 'gold', 20, 1158), ('07:03:27', 'osmium', 48, 2788),
         ('07:04:04', 'praseodymium', 8, 79), ('07:04:06', 'samarium', 42, 1243),
         ('07:04:11', 'silver', 40, 1856), ('07:04:13', 'painite', 5, 296)]
DAY = date(2026, 10, 13)
PLACE = dict(system='Fixture System', station='Fixture Station', power='Nakato Kaine')


def sale(second=0, **fields):
    return event('MarketSell', second, **dict(dict(Type='samarium', Count=42), **fields))


def groups(*events):
    c = PowerplayChronicle()
    for e in events:
        c.apply(e, **PLACE)
    return c.groups


def reported_sequence():
    rows = [dict(event='Powerplay', timestamp='2026-10-13T07:00:00Z',
                 Power=PLACE['power'], Merits=10000, Rank=12),
            dict(event='Docked', timestamp='2026-10-13T07:00:01Z',
                 StarSystem=PLACE['system'], StationName=PLACE['station'])]
    total = 10000
    for clock, commodity, count, gain in CASES:
        stamp = datetime.fromisoformat('2026-10-13T'+clock+'+00:00')
        rows.append(dict(event='MarketSell', timestamp=stamp.isoformat(), Type=commodity, Count=count))
        rows.append(dict(event='Cargo', timestamp=stamp.isoformat(), Vessel='Ship', Count=0))
        total += gain
        rows.append(dict(event='PowerplayMerits', timestamp=(stamp+timedelta(seconds=1)).isoformat(),
                         Power=PLACE['power'], MeritsGained=gain, TotalMerits=total))
    return rows


class MarketSaleTests(unittest.TestCase):
    def test_six_reported_sales_with_synthetic_one_second_credits(self):
        state = PowerplayState()
        for e in reported_sequence():
            state.apply(e)
        self.assertEqual([(g.action['Type'], g.action['Count'], g.credits[0]['MeritsGained'])
                          for g in state.chronicle.groups], [(t, c, m) for _, t, c, m in CASES])
        self.assertTrue(all(g.certainty == 'temporal' for g in state.chronicle.groups))
        self.assertEqual((state.merits, state.rank), (17420, 12))

    def test_each_reported_case_at_zero_one_two_seconds_and_outside(self):
        for _, commodity, count, gain in CASES:
            for delay in (-1, 0, 1, 2, 3):
                with self.subTest(commodity=commodity, delay=delay):
                    result = groups(sale(Type=commodity, Count=count), credit(delay, gain))
                    self.assertEqual(result[-1].certainty, 'temporal' if 0 <= delay <= 2 else 'unknown')
                    self.assertEqual(sum(len(g.credits) for g in result), 1)

    def test_multiple_sales_in_same_second_remain_ambiguous_even_after_credit(self):
        for sequence in ((sale(), sale(Type='osmium'), credit()),
                         (sale(), credit(0), sale(Type='osmium'), credit(1))):
            self.assertEqual(groups(*sequence)[-1].certainty, 'unknown')
        result = groups(sale(), sale(Type='osmium'), credit(), credit(2))
        self.assertTrue(all(g.certainty == 'unknown' for g in result))
        # Cargo cannot erase alternatives retained by an unknown credit.
        result = groups(sale(), sale(Type='osmium'), credit(0), event('Cargo'),
                        sale(Type='silver'), credit(1))
        self.assertTrue(all(g.certainty == 'unknown' for g in result))

    def test_competing_pp2_actions_in_both_directions(self):
        for other in (bounty(), delivery(), scan(), event('SearchAndRescue', Count=1),
                      delivery(kind='PowerplayCollect')):
            for sequence in ((sale(), other), (other, sale())):
                with self.subTest(other=other['event'], sequence=sequence):
                    self.assertEqual(groups(*sequence, credit(1, 10))[-1].certainty, 'unknown')
        # Preserve the existing three-second delivery window as an alternative.
        self.assertEqual(groups(delivery(0), sale(2), credit(3))[-1].certainty, 'unknown')
        self.assertEqual(groups(delivery(0), sale(3), credit(4))[-1].certainty, 'temporal')

    def test_cargo_is_transparent_only_to_sales_and_does_not_extend_window(self):
        for commodity in ('samarium', 'leestianeviljuice'):
            result = groups(sale(Type=commodity), event('Cargo', 1), credit(2))
            self.assertEqual(result[-1].certainty, 'temporal')
            self.assertEqual(groups(sale(Type=commodity), event('Cargo', 2), credit(3))[-1].certainty, 'unknown')
        self.assertEqual(groups(bounty(), event('Cargo'), credit())[-1].certainty, 'unknown')
        self.assertEqual(groups(delivery(), event('Cargo'), credit())[-1].certainty, 'unknown')

    def test_intermediate_reverse_or_invalid_timestamps_are_barriers(self):
        for intervening in (event('Cargo', 2), event('Cargo', -1),
                            dict(event('Cargo'), timestamp='invalid'), event('Music', 2)):
            self.assertEqual(groups(sale(), intervening, credit(1))[-1].certainty, 'unknown')
        self.assertEqual(groups(sale(2), sale(1), credit(2))[-1].certainty, 'unknown')
        self.assertEqual(groups(bounty(2), sale(1), credit(2))[-1].certainty, 'unknown')

    def test_context_identity_and_session_boundaries(self):
        for kind in ('Docked', 'Undocked', 'Location', 'FSDJump', 'CarrierJump', 'Commander',
                     'Fileheader', 'LoadGame', 'Shutdown', 'PowerplayJoin', 'PowerplayDefect',
                     'PowerplayLeave', 'RedeemVoucher', 'DeliverPowerMicroResources'):
            self.assertEqual(groups(sale(), event(kind), credit())[-1].certainty, 'unknown', kind)
        for field in PLACE:
            for value in ('', 'different'):
                c = PowerplayChronicle();c.apply(sale(), **PLACE)
                c.apply(credit(), **dict(PLACE, **{field: value}))
                self.assertEqual(c.groups[-1].certainty, 'unknown')
        self.assertEqual(groups(sale(), dict(credit(), Power='Other Power'))[-1].certainty, 'unknown')

    def test_invalid_or_unknown_sales_are_not_guessed_and_sale_alone_is_hidden(self):
        for fields in ({'Type':'unknown'}, {'Count':0}, {'Count':True}, {'Count':-1}, {'Count':'42'}):
            self.assertEqual(groups(sale(**fields), credit())[-1].certainty, 'unknown')
        self.assertEqual(groups(sale()), [])
        self.assertEqual(groups(sale(), credit(gain=0))[-1].certainty, 'unknown')
        self.assertEqual(groups(credit(), sale()), [groups(credit())[0]])

    def test_ordinary_sale_does_not_claim_additional_credits(self):
        result=groups(sale(), credit(), credit(2))
        self.assertEqual([g.certainty for g in result], ['temporal', 'unknown'])
        self.assertEqual(sum(len(g.credits) for g in result), 2)
        rare=groups(sale(Type='leestianeviljuice'), credit(), credit(2))
        self.assertEqual(len(rare), 1)
        self.assertEqual(len(rare[0].credits), 2)

    def test_merit_total_and_rank_match_replay_without_chronicle(self):
        with_chronicle, without = PowerplayState(), PowerplayState()
        for e in reported_sequence()+[event('RedeemVoucher', Type='CombatBond', Amount=300), credit(total=999)]:
            with_chronicle.apply(e);without._apply(e)
            self.assertEqual((with_chronicle.merits,with_chronicle.rank), (without.merits,without.rank))


class MarketSaleStoreTests(unittest.TestCase):
    setUp = store.StoreTests.setUp
    journal = store.StoreTests.journal
    sync = store.StoreTests.sync

    def test_old_stored_sales_replay_read_only_without_reimport(self):
        session=self.journal(reported_sequence())
        self.sync(session)
        with self.db._connect() as con:
            before={t:con.execute('SELECT * FROM '+t).fetchall() for t in store.PP_TABLES}
            self.assertEqual(con.execute("SELECT DISTINCT is_fact FROM pp2_events WHERE event_type='MarketSell'").fetchall(),[(0,)])
        Path(session['journal_file']).unlink()  # Synthetic fixture only.
        result=self.db.powerplay_day(session['commander_id'],DAY,zone=timezone.utc)
        self.assertEqual(len(result.groups),6)
        self.assertTrue(all(g.certainty=='temporal' for g in result.groups))
        self.assertEqual(self.db.powerplay_merits(session['commander_id']),17420)
        with self.db._connect() as con:
            self.assertEqual(before,{t:con.execute('SELECT * FROM '+t).fetchall() for t in store.PP_TABLES})
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0],23)

    def test_source_session_commander_and_missing_sequence_boundaries(self):
        context=[event('Powerplay', Power=PLACE['power'], Merits=0),
                 event('Docked', StarSystem=PLACE['system'], StationName=PLACE['station'])]
        first=self.journal([*context,sale()],name='Journal.first.log')
        second=self.journal([*context,credit()],name='Journal.second.log')
        other=self.journal([*context,credit()],name='Journal.other.log',fid='B')
        self.sync(first,second,other)
        for session in (first,other):
            result=self.db.powerplay_day(session['commander_id'],store.DAY,zone=timezone.utc)
            self.assertTrue(all(g.certainty=='unknown' for g in result.groups))
        gap=self.journal([*context,sale(),event('Cargo'),credit()],name='Journal.gap.log',fid='GAP')
        self.sync(gap)
        self.assertEqual(self.db.powerplay_day(gap['commander_id'],store.DAY,zone=timezone.utc).groups[0].certainty,'temporal')
        with self.db._connect() as con:
            con.execute("DELETE FROM pp2_events WHERE commander_id=? AND event_type='Cargo'",(gap['commander_id'],))
        self.assertEqual(self.db.powerplay_day(gap['commander_id'],store.DAY,zone=timezone.utc).groups[0].certainty,'unknown')


class MarketSaleViewTests(unittest.TestCase):
    setUpClass = classmethod(view_base.PowerplayViewTests.setUpClass.__func__)
    setUp = view_base.PowerplayViewTests.setUp

    def test_all_languages_use_existing_names_and_approximate_evidence(self):
        self.addCleanup(set_language,'de')
        self.state.powerplay=PowerplayState()
        for e in reported_sequence():self.state.powerplay.apply(e)
        for language in _TRANSLATIONS:
            set_language(language)
            with patch('cmdrhelper.ui.powerplay_view.local_today',return_value=DAY):self.view.render()
            table=self.view.recent
            self.assertEqual(table.rowCount(),6)
            for row in range(6):
                self.assertEqual(table.item(row,1).text(),tr_for_language(language,'pp2.chronicle.commodity_sale'))
                self.assertEqual(table.item(row,4).text(),'≈')
            if language=='de':
                self.assertTrue(table.item(2,2).text().startswith('42 t Samarium'))
                self.assertEqual(table.item(2,3).text(),'+1.243')
                self.assertIn('keine direkte Zuordnung',table.item(2,4).toolTip())
