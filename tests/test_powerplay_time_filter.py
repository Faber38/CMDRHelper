"""Synthetic PP2 presentation: local clock boundary and compact transport rows."""
import copy
import os
import time
import unittest
from datetime import date
from unittest.mock import patch
from PySide6.QtCore import QTime
from cmdrhelper.powerplay import PowerplayState
from cmdrhelper.powerplay_chronicle import ChronicleGroup
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests import test_powerplay as base


class TimeFilterTests(unittest.TestCase):
    setUpClass = classmethod(base.PowerplayViewTests.setUpClass.__func__)

    def setUp(self):
        original = os.environ.get('TZ')
        def restore():
            if original is None: os.environ.pop('TZ', None)
            else: os.environ['TZ'] = original
            time.tzset()
        self.addCleanup(restore)
        os.environ['TZ'] = 'Europe/Berlin'; time.tzset()
        base.PowerplayViewTests.setUp(self)
        self.state.powerplay = PowerplayState(merits=12345, rank=4)

    def group(self, stamp, count=43, name='Silber', station='Stronghold Carrier', system='San Xiang'):
        return ChronicleGroup(dict(timestamp=stamp,event='MarketSell',Type='silver',
            Type_Localised=name,Count=count), 'temporal', system=system,station=station,
            credits=[dict(timestamp=stamp,event='PowerplayMerits',MeritsGained=count,TotalMerits=12345)])

    def test_optional_inclusive_local_boundary_preserves_order_values_and_groups(self):
        groups=[self.group('2026-10-06T09:59:59Z',1), self.group('2026-10-06T10:00:00Z',2),
                self.group('2026-10-06T10:01:00Z',3)]
        # Credit time is not the action time. Do not reinterpret an earlier action.
        groups[0].credits[0]['timestamp']='2026-10-06T10:15:00Z'
        self.state.powerplay.chronicle.groups=groups
        before=copy.deepcopy(groups)
        self.view.render()
        totals=(self.view.personal['merits'].text(),self.view.personal['rank'].text(),self.view.rank_summary.text())
        self.assertEqual(self.view.recent.rowCount(),3)
        self.assertEqual([self.view.recent.item(r,3).text() for r in range(3)],['+3','+2','+1'])
        self.view.from_time.setTime(QTime(12,0))
        self.assertEqual(self.view.recent.rowCount(),3)
        self.view.time_filter_enabled.setChecked(True)
        self.assertEqual(self.view.recent.rowCount(),2)
        self.assertEqual([self.view.recent.item(r,3).text() for r in range(2)],['+3','+2'])
        self.assertEqual(groups,before)
        self.assertEqual(totals,(self.view.personal['merits'].text(),self.view.personal['rank'].text(),self.view.rank_summary.text()))
        self.view.time_filter_enabled.setChecked(False)
        self.assertEqual(self.view.recent.rowCount(),3)

    def test_day_change_and_utc_local_midnight(self):
        self.state.powerplay.chronicle.groups=[self.group('2026-10-05T21:59:00Z'),
            self.group('2026-10-05T22:00:00Z'),self.group('2026-10-06T21:59:00Z'),self.group('2026-10-06T22:00:00Z')]
        self.view.render(); self.assertEqual(self.view.recent.rowCount(),2)
        self.view.time_filter_enabled.setChecked(True)
        self.view.from_time.setTime(QTime(23,59)); self.assertEqual(self.view.recent.rowCount(),1)
        self.view._move_day(-1); self.assertEqual(self.view.recent.rowCount(),1)
        self.assertEqual(self.view.selected_day,date(2026,10,5))
        self.view._today(); self.assertEqual(self.view.recent.rowCount(),1)
        self.view.from_time.setTime(QTime(0,0)); self.assertEqual(self.view.recent.rowCount(),2)

    def test_dst_repeated_local_hour_and_utc_timezone(self):
        self.state.powerplay.chronicle.groups=[self.group('2026-10-25T00:29:59Z'),
            self.group('2026-10-25T00:30:00Z'),self.group('2026-10-25T01:30:00Z')]
        self.view.selected_day=date(2026,10,25)
        self.view.from_time.setTime(QTime(2,30));self.view.time_filter_enabled.setChecked(True)
        self.assertEqual(self.view.recent.rowCount(),2)
        os.environ['TZ']='UTC';time.tzset();self.view.render()
        self.assertEqual(self.view.recent.rowCount(),0)
        self.view.from_time.setTime(QTime(1,30));self.assertEqual(self.view.recent.rowCount(),1)

    def test_no_row_limit(self):
        self.state.powerplay.chronicle.groups=[self.group('2026-10-06T12:00:00Z',i) for i in range(1,251)]
        self.view.time_filter_enabled.setChecked(True);self.view.render()
        self.assertEqual(self.view.recent.rowCount(),250)
        self.assertEqual(self.view.recent.item(249,3).text(),'+250')

    def test_compact_rows_full_tooltips_themes_widths_and_existing_actions(self):
        groups=[self.group('2026-10-06T10:00:00Z'),
                self.group('2026-10-06T10:01:00Z',123456,'Long commodity '*10,'Long station '*10,'Long system '*10)]
        self.state.powerplay.chronicle.groups=groups
        actions=tuple(self.view.manage_history.menu().actions())
        for theme in (DARK_STYLESHEET,LIGHT_STYLESHEET):
            self.view.setStyleSheet(theme)
            for width in (480,1200):
                self.view.resize(width,900);self.view.render();self.app.processEvents()
                self.assertEqual(self.view.recent.rowCount(),2)
                short=self.view.recent.item(1,2)
                self.assertEqual(short.text(),'43 t Silber | Stronghold Carrier · San Xiang')
                long=self.view.recent.item(0,2)
                for text in ('Long commodity '*10,'Long station '*10,'Long system '*10):
                    self.assertIn(text,long.toolTip())
                self.assertNotIn('\n',short.text())
                compact_height=self.view.recent.rowHeight(1)
                short.setText(short.text().replace(' | ', '\n'))
                self.view.recent.resizeRowsToContents()
                self.assertLessEqual(compact_height,self.view.recent.rowHeight(1))
                self.view.render()
                self.assertEqual(tuple(self.view.manage_history.menu().actions()),actions)
                self.assertTrue(self.view.previous_day.isEnabled())
                self.view.grab()

    def test_other_event_details_use_compact_separator(self):
        self.state.powerplay.chronicle.groups=[ChronicleGroup(
            dict(timestamp='2026-10-06T10:00:00Z',event='Bounty',Target='Ship',TotalReward=100),
            'explicit',system='System',station='Station')]
        self.view.render()
        self.assertIn(' | Station · System',self.view.recent.item(0,2).text())
        self.assertNotIn('\n',self.view.recent.item(0,2).text())


class StoredTimeFilterTests(unittest.TestCase):
    from tests.test_powerplay_history_view import HistoryViewTests as _base
    setUpClass = classmethod(base.PowerplayViewTests.setUpClass.__func__)
    setUp = _base.setUp
    journal = _base.journal
    sync = _base.sync

    def test_filter_does_not_change_stored_events_or_merit_total(self):
        from cmdrhelper.powerplay import timestamp
        before=self.db.powerplay_merits(self.state.commander_id)
        with self.db._connect() as con:
            events=con.execute('SELECT * FROM pp2_events').fetchall()
        action=self.db.powerplay_day(self.state.commander_id,self.view.selected_day or date(2026,10,6)).groups[-1].action
        local=timestamp(action['timestamp']).astimezone()
        self.view.from_time.setTime(QTime(local.hour,local.minute))
        self.view.time_filter_enabled.setChecked(True)
        self.assertEqual(self.view.recent.rowCount(),1)
        self.view.from_time.setTime(QTime(local.hour,local.minute).addSecs(60))
        self.assertEqual(self.view.recent.rowCount(),0)
        self.assertEqual(self.db.powerplay_merits(self.state.commander_id),before)
        with self.db._connect() as con:
            self.assertEqual(con.execute('SELECT * FROM pp2_events').fetchall(),events)
        self.view.time_filter_enabled.setChecked(False)
        self.assertEqual(self.view.recent.rowCount(),1)


if __name__=='__main__': unittest.main()
