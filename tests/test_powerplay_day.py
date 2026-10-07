"""Local-day PP2 history across files, DST boundaries and UI scrolling."""
from datetime import date, timedelta
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo

from cmdrhelper.journal_reader import (
    classify_journal_file, read_latest_state, read_today_powerplay_chronicle,
)
from cmdrhelper.powerplay import PowerplayState
from cmdrhelper.powerplay_chronicle import chronicle_for_day, local_event_day, today_groups
from tests import test_powerplay as base
from tests.test_powerplay_chronicle import bounty, credit, delivery, event, scan

BERLIN = ZoneInfo('Europe/Berlin')
DAY = date(2026, 10, 6)


class DayTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        clock = patch('cmdrhelper.powerplay_chronicle.local_today', return_value=DAY)
        clock.start()
        self.addCleanup(clock.stop)

    def write(self, name, rows, fid='A'):
        path = self.folder / name
        identity = dict(event='Commander', timestamp=rows[0]['timestamp'], FID=fid, Name='Test')
        path.write_text(''.join(json.dumps(e)+'\n' for e in [identity, *rows]))
        return classify_journal_file(path)

    def test_utc_to_local_midnight_summer_and_winter(self):
        for day, before, after, end, next_day in [
            (DAY, '2026-10-05T21:59:59Z', '2026-10-05T22:00:00Z',
             '2026-10-06T21:59:59Z', '2026-10-06T22:00:00Z'),
            (date(2026, 1, 6), '2026-01-05T22:59:59Z', '2026-01-05T23:00:00Z',
             '2026-01-06T22:59:59Z', '2026-01-06T23:00:00Z'),
            # The DST transition days have 23 and 25 hours respectively.
            (date(2026, 3, 29), '2026-03-28T22:59:59Z', '2026-03-28T23:00:00Z',
             '2026-03-29T21:59:59Z', '2026-03-29T22:00:00Z'),
            (date(2026, 10, 25), '2026-10-24T21:59:59Z', '2026-10-24T22:00:00Z',
             '2026-10-25T22:59:59Z', '2026-10-25T23:00:00Z'),
        ]:
            with self.subTest(day=day):
                self.assertEqual(local_event_day(before, BERLIN), day-timedelta(days=1))
                self.assertEqual(local_event_day(after, BERLIN), day)
                self.assertEqual(local_event_day(end, BERLIN), day)
                self.assertEqual(local_event_day(next_day, BERLIN), day+timedelta(days=1))
                rows = [dict(delivery(), timestamp=stamp) for stamp in (before, after, end, next_day)]
                groups = chronicle_for_day(rows, day, BERLIN).groups
                self.assertEqual([g.action['timestamp'] for g in groups], [after, end])

    def test_previous_day_filename_and_context_spanning_midnight(self):
        rows = [dict(event('Docked', StarSystem='Origin', StationName='Station'), timestamp='2026-10-05T21:59:00Z'),
                dict(delivery(), timestamp='2026-10-05T21:59:59Z'),
                dict(delivery(), timestamp='2026-10-05T22:00:00Z')]
        session = self.write('Journal.2026-10-05T210000.01.log', rows)
        groups = read_today_powerplay_chronicle([session], 'A', day=DAY, zone=BERLIN).groups
        self.assertEqual(len(groups), 1)
        self.assertEqual((groups[0].station, groups[0].system), ('Station', 'Origin'))
        self.assertEqual(groups[0].action['timestamp'], '2026-10-05T22:00:00Z')

    @unittest.skipUnless(hasattr(time, 'tzset'), 'OS timezone override requires tzset')
    def test_default_user_timezone_uses_offset_of_each_event(self):
        try:
            with patch.dict(os.environ, TZ='Europe/Berlin'):
                time.tzset()
                self.assertEqual(local_event_day('2026-10-05T22:00:00Z'), DAY)
                self.assertEqual(local_event_day('2026-01-05T22:00:00Z'), date(2026, 1, 5))
                self.assertEqual(local_event_day('2026-01-05T23:00:00Z'), date(2026, 1, 6))
        finally:
            time.tzset()

    def test_stale_previous_day_index_cannot_hide_midnight_append(self):
        session = self.write('Journal.2026-10-05T230000.01.log',
                             [dict(delivery(), timestamp='2026-10-05T21:59:59Z')])
        self.assertEqual(read_today_powerplay_chronicle([session], 'A', day=DAY, zone=BERLIN).groups, [])
        with Path(session['journal_file']).open('a') as handle:
            handle.write(json.dumps(dict(delivery(), timestamp='2026-10-05T22:00:00Z'))+'\n')
        groups = read_today_powerplay_chronicle([session], 'A', day=DAY, zone=BERLIN).groups
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].certainty, 'explicit')

    def test_six_earlier_bounties_and_scan_survive_indexed_rotation(self):
        rows = [event('Location', StarSystem='HR 4827', ControllingPower='Nakato Kaine', PowerplayState='Exploited')]
        observed = [('Jim Bell', 453097, 60), ('Andreas Martin Clemenz', 163361, 21),
                    ('Jock Ripper', 360818, 48), ('Flavio Antonietti', 134247, 17),
                    ('Theia Claw', 279561, 37), ('Tiddlywinks', 603200, 80)]
        for n, (pilot, reward, gain) in enumerate(observed):
            rows.extend([dict(bounty(n*10), PilotName_Localised=pilot, TotalReward=reward), credit(n*10+1, gain)])
        first = self.write('Journal.2026-10-06T121000.01.log', rows)
        second = self.write('Journal.2026-10-06T151935.01.log', [scan(100), credit(101, 10),
                            delivery(110), credit(110, 3600, 12783), credit(110, 48, 12831),
                            event('Cargo', 120), credit(121, 3, 13213)])
        data = read_latest_state(self.folder, indexed_sessions=[first, second])['powerplay']
        self.assertEqual(data.merits, 13213)
        groups = data.chronicle.groups
        self.assertEqual(len(groups), 9)
        self.assertEqual([(g.action['PilotName_Localised'], g.action['TotalReward'], g.credits[0]['MeritsGained'])
                          for g in groups[:6]], observed)
        self.assertEqual([g.certainty for g in groups], ['temporal']*7+['explicit', 'unknown'])
        self.assertEqual([g.credits[0]['MeritsGained'] for g in today_groups(data.chronicle, DAY, BERLIN)],
                         [3, 3600, 10, 80, 37, 17, 48, 21, 60])
        self.assertEqual(data.chronicle, read_latest_state(self.folder, indexed_sessions=[first, second])['powerplay'].chronicle)

    def test_rotation_cache_append_and_commander_isolation(self):
        first = self.write('Journal.2026-10-06T100000.01.log', [delivery()])
        groups = read_today_powerplay_chronicle([first], 'A', day=DAY, zone=BERLIN).groups
        self.assertEqual(len(groups), 1)
        second = self.write('Journal.2026-10-06T100000.02.log', [delivery(10)])
        other = self.write('Journal.2026-10-06T120000.01.log', [delivery(20)], 'B')
        self.assertEqual(len(read_today_powerplay_chronicle([first, second, other], 'A', day=DAY, zone=BERLIN).groups), 2)
        with Path(second['journal_file']).open('a') as handle:
            handle.write(json.dumps(credit(10, 48))+'\n')
        # Deliberately retain stale index metadata: bytes must win over it.
        result = read_today_powerplay_chronicle([first, second], 'A', day=DAY, zone=BERLIN)
        self.assertEqual(len(result.groups), 2)
        self.assertEqual(result.groups[-1].credits[0]['MeritsGained'], 48)
        result.groups.clear()
        self.assertEqual(len(read_today_powerplay_chronicle([first, second], 'A', day=DAY, zone=BERLIN).groups), 2)

    def test_cache_does_not_reuse_previous_day_and_no_group_limit(self):
        session = self.write('Journal.2026-10-06T100000.01.log', [delivery(n*10) for n in range(50)])
        self.assertEqual(len(read_today_powerplay_chronicle([session], 'A', day=DAY, zone=BERLIN).groups), 50)
        self.assertEqual(read_today_powerplay_chronicle([session], 'A', day=DAY+timedelta(days=1), zone=BERLIN).groups, [])


class DayViewTests(unittest.TestCase):
    setUpClass = classmethod(base.PowerplayViewTests.setUpClass.__func__)
    setUp = base.PowerplayViewTests.setUp

    def test_all_rows_newest_first_scroll_inside_table_and_rollover(self):
        self.state.powerplay = PowerplayState()
        for n in range(80):
            self.state.powerplay.apply(delivery(n*10))
        self.state.powerplay.apply(dict(delivery(), timestamp='2026-10-05T10:00:00Z'))
        self.view.resize(1200, 900)
        self.state.changed.emit()
        self.app.processEvents()
        table = self.view.recent
        self.assertEqual(table.rowCount(), 80)
        self.assertIn(delivery(790)['timestamp'], table.item(0, 0).toolTip())
        self.assertIn(delivery(0)['timestamp'], table.item(79, 0).toolTip())
        self.assertGreater(table.verticalScrollBar().maximum(), 0)
        self.assertLess(table.height(), self.view.height())
        self.assertLess(self.view.verticalScrollBar().maximum(), table.verticalScrollBar().maximum())
        with patch('cmdrhelper.ui.powerplay_view.local_today', return_value=DAY+timedelta(days=1)):
            self.view.render()
        self.assertEqual(table.rowCount(), 0)
