"""Delivery correlations only; all persistence tests use temporary databases."""
from datetime import date, timedelta
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from cmdrhelper.powerplay_chronicle import PowerplayChronicle, chronicle_for_day
from cmdrhelper.i18n import set_language, tr
from tests.test_powerplay_chronicle import event, delivery, credit, bounty, scan, replay
from tests import test_powerplay_store as store
from tests import test_powerplay as base

PLACE = dict(power='Nakato Kaine', system='Hydrae Sector LN-T b3-1', station='Dingle Depot')
FIXTURE = json.loads((Path(__file__).parent/'fixtures/powerplay_deliver_20261012.json').read_text())
REAL = [row['event'] for row in FIXTURE['rows']]


def at_station(*events):
    result = PowerplayChronicle()
    for e in events:
        result.apply(e, **PLACE)
    return result


class DeliveryTests(unittest.TestCase):
    def test_inclusive_window_with_and_without_locker(self):
        for seconds in (-1, 0, 1, 2, 3, 4):
            for locker in ([], [event('ShipLocker')]):
                with self.subTest(seconds=seconds, locker=bool(locker)):
                    groups = at_station(delivery(), *locker, credit(seconds)).groups
                    matched = 0 <= seconds <= 3
                    self.assertEqual(groups[0].certainty, 'temporal' if matched else 'explicit')
                    self.assertEqual(groups[0].credits, [credit(seconds)] if matched else [])
                    if not matched:
                        self.assertEqual(groups[-1].certainty, 'unknown')

    def test_locker_is_only_allowed_once_before_delivery_credits(self):
        from tests.test_powerplay_rare_sales import sale
        for action in (bounty(), scan(), event('SearchAndRescue'), sale(), delivery(kind='PowerplayCollect')):
            with self.subTest(action=action):
                self.assertEqual(at_station(action, event('ShipLocker'), credit(0, 10)).groups[-1].certainty, 'unknown')
        for middle in ([event('ShipLocker'), event('ShipLocker')],
                       [credit(0), event('ShipLocker')], [event('ShipLocker', 4)]):
            self.assertEqual(at_station(delivery(), *middle, credit(1)).groups[-1].certainty, 'unknown')

    def test_barriers_remain_barriers(self):
        for kind in ('Cargo', 'Market', 'Docked', 'Undocked', 'FSDJump', 'PowerplayRank',
                     'MissionCompleted', 'UnknownFutureEvent', 'Fileheader', 'LoadGame',
                     'Shutdown', 'DeliverPowerMicroResources'):
            with self.subTest(kind=kind):
                self.assertEqual(at_station(delivery(), event(kind), credit(1)).groups[-1].certainty, 'unknown')

    def test_context_must_be_known_and_unchanged(self):
        for key in PLACE:
            for value in ('', 'Other'):
                for stage in ('action', 'locker', 'merit'):
                    with self.subTest(key=key, value=value, stage=stage):
                        c = PowerplayChronicle()
                        for name, e in [('action', delivery()), ('locker', event('ShipLocker')), ('merit', credit())]:
                            c.apply(e, **(dict(PLACE, **{key: value}) if stage == name else PLACE))
                        self.assertEqual(c.groups[-1].certainty, 'unknown')
        c = at_station(delivery())
        c.apply(dict(credit(), Power='Edmund Mahon'), **PLACE)
        self.assertEqual(c.groups[-1].certainty, 'unknown')

    def test_invalid_delivery_and_timestamps(self):
        for fields in ({'Count': 0}, {'Count': -1}, {'Count': True}, {'Type': ''}, {'Power': ''},
                       {'timestamp': 'invalid'}, {'timestamp': '2026-10-06T11:13:36'}):
            with self.subTest(fields=fields):
                self.assertEqual(at_station(dict(delivery(), **fields), event('ShipLocker'), credit()).groups[-1].certainty, 'unknown')

    def test_multiple_credits_preserve_values_and_order(self):
        credits = [credit(1, 4800, 285970), credit(1, 84, 286054), credit(2, 84, 286000)]
        group, = at_station(delivery(), event('ShipLocker', 1), *credits).groups
        self.assertEqual(group.certainty, 'temporal')
        self.assertEqual(group.credits, credits)

    def test_credited_delivery_remains_a_competitor(self):
        for marker in ([], [event('DeliverPowerMicroResources', 2)]):
            c = at_station(delivery(), credit(0), *marker, delivery(2), event('ShipLocker', 2), credit(3))
            self.assertEqual(c.groups[-1].certainty, 'unknown')
            self.assertEqual(c.groups[0].credits, [credit(0)])
            self.assertEqual(c.groups[1].credits, [])

    def test_multiple_uncredited_deliveries_and_other_causes(self):
        for action in (delivery(), bounty(), scan(), event('SearchAndRescue')):
            for credited in ([], [credit(0, 10)]):
                with self.subTest(action=action, credited=credited):
                    c = at_station(action, *credited, delivery(), event('ShipLocker'), credit(1, 10))
                    self.assertEqual(c.groups[-1].certainty, 'unknown')

    def test_reverse_credit_order_does_not_resume_matching(self):
        c = at_station(delivery(), credit(2), credit(1), credit(3))
        self.assertEqual(c.groups[0].credits, [credit(2)])
        self.assertEqual(c.groups[-1].certainty, 'unknown')

    def test_real_seven_deliveries_and_absolute_total(self):
        state = replay(*REAL)
        groups = state.chronicle.groups
        deliveries = [g for g in groups if g.action['event'] == 'PowerplayDeliver']
        self.assertEqual(len(deliveries), 7)
        self.assertEqual([[c['MeritsGained'] for c in g.credits] for g in deliveries],
                         [[493], [169], [169], [246], [246], [], [4800, 84]])
        unknown = [g for g in groups if g.certainty == 'unknown']
        self.assertEqual([c['TotalMerits'] for g in unknown for c in g.credits], [281170])
        self.assertEqual([g.action for g in deliveries], [e for e in REAL if e['event'] == 'PowerplayDeliver'])
        self.assertEqual(state.merits, 286054)
        self.assertEqual(deliveries[-1].credits, REAL[-2:])
        # +493 precedes the next delivery even though both have the same time.
        self.assertEqual(deliveries[0].credits[0]['timestamp'], deliveries[1].action['timestamp'])

    def test_day_boundary(self):
        context = [event('Powerplay', Power=PLACE['power']),
                   event('Docked', StarSystem=PLACE['system'], StationName=PLACE['station'])]
        before = dict(delivery(), timestamp='2026-10-06T21:59:59Z')
        after = dict(credit(), timestamp='2026-10-06T22:00:00Z')
        c = chronicle_for_day([*context, before, after], store.DAY+timedelta(days=1), store.ZONE)
        self.assertEqual([g.certainty for g in c.groups], ['unknown'])


class DeliveryStoreTests(unittest.TestCase):
    setUp = store.StoreTests.setUp
    journal = store.StoreTests.journal
    sync = store.StoreTests.sync

    def test_source_and_sequence_boundaries_discard_all_candidates(self):
        context = [event('Powerplay', Power=PLACE['power']),
                   event('Docked', StarSystem=PLACE['system'], StationName=PLACE['station'])]
        a = self.journal([*context, delivery(), credit(0)])
        b = self.journal([*context, delivery(1), event('ShipLocker', 1), credit(2)], name='Journal.second.log')
        self.sync(a, b)
        groups = self.db.powerplay_day(a['commander_id'], store.DAY, zone=store.ZONE).groups
        self.assertEqual([g.certainty for g in groups], ['temporal', 'temporal'])
        # Delete a barrier from the temporary DB: sequence continuity still blocks matching.
        s = self.journal([*context, delivery(), event('Cargo'), event('ShipLocker'), credit()], fid='GAP')
        self.sync(s)
        with self.db._connect() as con:
            con.execute("DELETE FROM pp2_events WHERE commander_id=? AND event_type='Cargo'", (s['commander_id'],))
        groups = self.db.powerplay_day(s['commander_id'], store.DAY, zone=store.ZONE).groups
        self.assertEqual([g.certainty for g in groups], ['explicit', 'unknown'])

    def test_source_boundary_cannot_match_previous_delivery(self):
        context = [event('Powerplay', Power=PLACE['power']),
                   event('Docked', StarSystem=PLACE['system'], StationName=PLACE['station'])]
        a = self.journal([*context, delivery()])
        b = self.journal([credit()], name='Journal.second.log')
        self.sync(a, b)
        with self.db._connect() as con:
            ctx = json.loads(con.execute("SELECT context_json FROM pp2_events WHERE event_type='PowerplayDeliver'").fetchone()[0])
            ctx['sequence'] += 1
            con.execute("UPDATE pp2_events SET context_json=? WHERE event_type='PowerplayMerits'", (json.dumps(ctx),))
        self.assertEqual([g.certainty for g in self.db.powerplay_day(a['commander_id'], store.DAY, zone=store.ZONE).groups], ['explicit', 'unknown'])

    def test_real_replay_preserves_persisted_history_and_schema(self):
        s = self.journal(REAL)
        self.sync(s)
        def snapshot():
            with self.db._connect() as con:
                return [con.execute('SELECT * FROM '+t).fetchall() for t in store.PP_TABLES]
        before = snapshot()
        c = self.db.powerplay_day(s['commander_id'], date(2026, 10, 12), zone=store.ZONE)
        self.assertEqual([g.certainty for g in c.groups],
                         ['temporal']*5 + ['explicit', 'unknown', 'temporal'])
        self.assertEqual(snapshot(), before)
        self.assertEqual(self.db.powerplay_merits(s['commander_id']), 286054)
        with self.db._connect() as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], 23)


class DeliveryViewTests(unittest.TestCase):
    setUpClass = classmethod(base.PowerplayViewTests.setUpClass.__func__)
    setUp = base.PowerplayViewTests.setUp

    def test_real_tooltip_in_all_languages_and_themes(self):
        from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
        self.addCleanup(set_language, 'de')
        self.state.powerplay = replay(*REAL)
        for language in ('de', 'en', 'el', 'es', 'fi', 'fr', 'it', 'nl', 'no', 'pl', 'sv', 'tr'):
            set_language(language)
            for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                with self.subTest(language=language, theme=theme[:20]):
                    self.view.setStyleSheet(theme)
                    with patch('cmdrhelper.ui.powerplay_view.local_today', return_value=date(2026, 10, 12)):
                        self.state.changed.emit()
                        self.app.processEvents()
                    table = self.view.recent
                    self.assertEqual(table.rowCount(), 8)
                    self.assertEqual(table.item(0, 4).text(), '≈')
                    self.assertIn(' / ', table.item(0, 3).text())
                    tip = table.item(0, 4).toolTip()
                    self.assertIn(tr('pp2.chronicle.temporal', seconds='1'), tip)
                    self.assertIn('2026-10-12T08:13:14Z', tip)
                    self.assertNotIn('pp2.chronicle.temporal', tip)
                    self.assertNotIn('{seconds}', tip)
                    self.assertNotIn('bonus', tip.lower())
                    if language == 'de':
                        self.assertEqual(table.item(0, 3).text(), '+4.800 / +84')
                        self.assertIn('285.970', tip)
                        self.assertIn('286.054', tip)
