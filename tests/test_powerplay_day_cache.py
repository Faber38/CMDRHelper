"""One-day display cache: real SQLite commits, no production journals or databases."""
import json
import gc
import os
import sqlite3
from contextlib import closing
from datetime import timedelta
from pathlib import Path
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QCoreApplication, QEvent, QTime, Qt
from shiboken6 import isValid
from cmdrhelper import powerplay_store
from cmdrhelper.powerplay_store import read_day
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests import test_powerplay as base
from tests import test_powerplay_store as store
from tests.test_powerplay_store import DAY, delivery, credit, event


class DayCacheTests(unittest.TestCase):
    journal = store.StoreTests.journal
    sync = store.StoreTests.sync
    setUpClass = classmethod(base.PowerplayViewTests.setUpClass.__func__)

    def setUp(self):
        store.StoreTests.setUp(self)
        self.clock = patch('cmdrhelper.ui.powerplay_view.local_today', return_value=DAY)
        self.today = self.clock.start()
        self.addCleanup(self.clock.stop)
        self.session = self.journal([
            event('Powerplay', Power='Nakato Kaine', Merits=100),
            event('Docked', StarSystem='Test', StationName='Station'),
            delivery(), credit(1, 48, 148)])
        self.sync(self.session)
        self.cid = self.session['commander_id']
        self.state = base.ViewState()
        self.state.database = self.db
        self.state.commander_id = self.cid
        self.state.commander_fid = 'A'
        self.view = base.PowerplayView(self.state)
        self.addCleanup(self.dispose)

    def dispose(self):
        if not isValid(self.view):
            return
        self.view.close()
        self.view.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.processEvents()

    def edit(self, kind, field, value, column='facts_json'):
        with self.db._connect() as con:
            sid, line, raw = con.execute(
                f'SELECT source_id,source_line,{column} FROM pp2_events WHERE commander_id=? AND event_type=?',
                (self.cid, kind)).fetchone()
            data = json.loads(raw)
            data[field] = value
            con.execute(f'UPDATE pp2_events SET {column}=? WHERE commander_id=? AND source_id=? AND source_line=?',
                        (json.dumps(data), self.cid, sid, line))

    def table(self):
        return [[self.view.recent.item(r, c).text() for c in range(5)]
                for r in range(self.view.recent.rowCount())]

    def test_30_unchanged_renders_no_replay_no_table_and_readonly_probe(self):
        before = self.table()
        cache = self.view._day_cache
        statements = []
        cache._con.set_trace_callback(statements.append)
        with patch('cmdrhelper.powerplay_store._decode_day', wraps=powerplay_store._decode_day) as replay, \
                patch.object(self.view.recent, 'setRowCount', wraps=self.view.recent.setRowCount) as table:
            for _ in range(30):
                self.view.render()
            replay.assert_not_called()
            table.assert_not_called()
        self.assertEqual(statements, ['PRAGMA data_version'] * 30)
        self.assertEqual(before, self.table())
        self.assertFalse(cache._con.in_transaction)
        with self.assertRaises(sqlite3.OperationalError):
            cache._con.execute('DELETE FROM pp2_events')
        self.assertEqual(self.view.timer.interval(), 5000)

    def test_equal_count_fact_and_context_corrections_without_policy_revision(self):
        with self.db._connect() as con:
            count = con.execute('SELECT count(*) FROM pp2_events').fetchone()[0]
            revision = con.execute('SELECT revision FROM pp2_history_policy WHERE commander_id=?', (self.cid,)).fetchone()[0]
        self.edit('PowerplayMerits', 'MeritsGained', 99)
        self.view.render()
        self.assertIn('+99', str(self.table()))
        self.edit('PowerplayDeliver', 'station', 'Corrected Station', 'context_json')
        self.view.render()
        self.assertIn('Corrected Station', str(self.table()))
        with self.db._connect() as con:
            self.assertEqual(count, con.execute('SELECT count(*) FROM pp2_events').fetchone()[0])
            self.assertEqual(revision, con.execute('SELECT revision FROM pp2_history_policy WHERE commander_id=?', (self.cid,)).fetchone()[0])

    def test_new_credit_and_personal_totals_rank_are_not_cached(self):
        with Path(self.session['journal_file']).open('a') as handle:
            handle.write(json.dumps(credit(2, 7, 155)) + '\n')
        self.sync(self.session)
        self.state.powerplay.merits = 155
        self.state.powerplay.rank = 3
        self.view.render()
        self.assertIn('+7', str(self.table()))
        self.assertEqual(self.view.personal['merits'].text(), '155')
        self.assertEqual(self.view.personal['rank'].text(), '3')
        with patch.object(self.view.recent, 'setRowCount', wraps=self.view.recent.setRowCount) as table:
            self.state.powerplay.merits = 900
            self.state.powerplay.rank = 4
            self.view.render()
            table.assert_not_called()
        self.assertEqual(self.view.personal['merits'].text(), '900')
        self.assertEqual(self.view.personal['rank'].text(), '4')

    def test_unrelated_commit_preserves_replayed_day_and_table(self):
        token = self.view._day_cache._token
        with self.db._connect() as con:
            con.execute("INSERT OR REPLACE INTO app_meta VALUES('test.unrelated','1')")
        with patch('cmdrhelper.powerplay_store._decode_day') as replay, \
                patch.object(self.view.recent, 'setRowCount', wraps=self.view.recent.setRowCount) as table:
            self.view.render()
            replay.assert_not_called()
            table.assert_not_called()
        self.assertIs(self.view._day_cache._token, token)

    def test_corrected_action_reconstructs_credit_association(self):
        self.assertNotEqual(self.view.recent.item(0, 4).text(), '?')
        self.edit('PowerplayDeliver', 'event', 'Music')
        self.view.render()
        self.assertEqual(self.view.recent.item(0, 4).text(), '?')
        self.assertEqual(self.view._day_cache._chronicle.groups,
                         read_day(self.db, self.cid, DAY).groups)

    def test_commit_during_load_is_seen_on_next_refresh(self):
        from cmdrhelper.powerplay_store import _day_rows
        self.view._day_cache.close()

        def read_then_commit(*args):
            rows = _day_rows(*args)
            self.edit('PowerplayMerits', 'MeritsGained', 321)
            return rows

        with patch('cmdrhelper.powerplay_store._day_rows', side_effect=read_then_commit):
            self.view.render()
        self.assertIn('+48', str(self.table()))
        self.view.render()
        self.assertIn('+321', str(self.table()))

    def test_sorted_rows_and_selection_survive_unchanged_refresh(self):
        with Path(self.session['journal_file']).open('a') as handle:
            for e in (delivery(20), credit(21, 12, 160)):
                handle.write(json.dumps(e) + '\n')
        self.sync(self.session)
        self.view.render()
        self.assertEqual(self.view.recent.rowCount(), 2)
        self.view.recent.sortItems(0, Qt.AscendingOrder)
        self.view.recent.selectRow(0)
        before = self.table()
        items = [self.view.recent.item(row, 0) for row in range(2)]
        self.view.render()
        self.assertEqual(self.table(), before)
        self.assertEqual(self.view.recent.currentRow(), 0)
        self.assertTrue(all(self.view.recent.item(row, 0) is item for row, item in enumerate(items)))

    def test_commander_fid_and_day_isolation_and_midnight(self):
        other = self.journal([credit(1, 777, 777)], name='Journal.2026-10-06T120000.01.log', fid='B')
        self.sync(other)
        self.state.commander_id = other['commander_id']
        self.state.commander_fid = 'B'
        self.view.render()
        self.assertIn('+777', str(self.table()))
        self.assertNotIn('+48', str(self.table()))
        self.state.commander_id = self.cid
        self.state.commander_fid = 'A'
        self.view.render()
        self.assertIn('+48', str(self.table()))
        previous = self.view._day_cache._token
        # Same numeric ID, different proven DB identity is a different scope.
        with self.db._connect() as con:
            con.execute('UPDATE commanders SET fid=? WHERE id=?', ('A-replaced', self.cid))
        self.view.render()
        self.assertIsNot(previous, self.view._day_cache._token)
        self.today.return_value = DAY + timedelta(days=1)
        self.view.render()
        self.assertEqual(self.view.recent.rowCount(), 0)
        self.view._move_day(-1)
        self.assertIn('+48', str(self.table()))
        self.view._move_day(-1)
        self.assertEqual(self.view.recent.rowCount(), 0)
        self.assertEqual(self.view._day_cache._rows, [])

    def test_time_filter_language_sort_and_both_themes_do_not_redecode(self):
        from cmdrhelper.i18n import get_language, set_language
        previous = get_language()
        self.addCleanup(set_language, previous)
        with patch('cmdrhelper.powerplay_store._decode_day') as replay:
            with patch.object(self.view.recent, 'setRowCount', wraps=self.view.recent.setRowCount) as table:
                self.view.from_time.setTime(QTime(23, 59))
                table.assert_not_called()  # Disabled filter has no visual effect.
            self.view.time_filter_enabled.setChecked(True)
            self.assertEqual(self.view.recent.rowCount(), 0)
            self.view.time_filter_enabled.setChecked(False)
            self.assertEqual(self.view.recent.rowCount(), 1)
            for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                self.view.setStyleSheet(style)
                self.view.render()
                self.assertIn('+48', str(self.table()))
            set_language('en')
            self.view.render()
            self.assertIn('Merits', self.view.filtered_merits.text())
            self.view.recent.sortItems(0, Qt.AscendingOrder)
            item = self.view.recent.item(0, 0)
            self.view.render()
            self.assertIs(self.view.recent.item(0, 0), item)
            previous_font = self.view.recent.font().toString()
            # A direct setFont is overridden by the theme's font-size rule.
            self.view.recent.setStyleSheet('font-size: 24pt;')
            self.view.recent.ensurePolished()
            self.assertNotEqual(self.view.recent.font().toString(), previous_font)
            with patch.object(self.view.recent, 'setRowCount', wraps=self.view.recent.setRowCount) as table:
                self.view.render()
                table.assert_called_once()
            replay.assert_not_called()

    def test_detached_hidden_timer_refresh_and_correction(self):
        self.view.detach_chronicle()
        self.view.hide()
        self.assertTrue(self.view.timer.isActive())
        with patch.object(self.view.recent, 'setRowCount', wraps=self.view.recent.setRowCount) as table:
            self.view.timer.timeout.emit()
            table.assert_not_called()
            self.edit('PowerplayMerits', 'MeritsGained', 123)
            self.view.timer.timeout.emit()
            table.assert_called_once()
        self.assertIn('+123', str(self.table()))
        self.view.attach_chronicle()
        self.assertIn('+123', str(self.table()))

    def test_deleted_history_and_empty_day_cached(self):
        with self.db._connect() as con:
            con.execute('DELETE FROM pp2_events WHERE commander_id=?', (self.cid,))
        self.view.render()
        self.assertEqual(self.view.recent.rowCount(), 0)
        with patch.object(self.view.recent, 'setRowCount', wraps=self.view.recent.setRowCount) as table:
            self.view.render()
            table.assert_not_called()

    def test_failed_probe_falls_back_and_destroy_closes_connection(self):
        cache = self.view._day_cache
        con = cache._con
        con.close()  # Simulate an unusable observer connection.
        with patch.object(self.db, 'powerplay_day', wraps=self.db.powerplay_day) as reader:
            self.view.render()
            reader.assert_called_once()
        self.assertIsNone(cache._con)
        self.assertIn('+48', str(self.table()))
        self.view.render()
        con = cache._con
        self.dispose()
        with self.assertRaises(sqlite3.ProgrammingError):
            con.execute('SELECT 1')

    def test_database_replacement_invalidates_even_with_same_version(self):
        cache = self.view._day_cache
        original_token = cache._token
        replacement = self.folder / 'replacement.db'
        with closing(sqlite3.connect(self.db.path)) as src, closing(sqlite3.connect(replacement)) as dst:
            src.backup(dst)
            dst.execute('DELETE FROM pp2_events')
            dst.commit()
            dst.execute('PRAGMA journal_mode=DELETE')
        # Close the old observer and checkpoint WAL before replacing the file.
        # Keep cached request/binding to exercise inode invalidation.
        cache._con.close()
        gc.collect()
        with closing(sqlite3.connect(self.db.path)) as con:
            con.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        replacement.replace(self.db.path)
        self.view.render()
        self.assertIsNot(cache._token, original_token)
        self.assertEqual(self.view.recent.rowCount(), 0)

    def test_large_day_5768_events_matches_uncached_replay(self):
        with self.db._connect() as con:
            source = con.execute('SELECT id FROM pp2_sources WHERE commander_id=?', (self.cid,)).fetchone()[0]
            con.execute('DELETE FROM pp2_events WHERE commander_id=?', (self.cid,))
            con.executemany('INSERT INTO pp2_events VALUES(?,?,?,?,?,?,?,?,?,?)', [
                (self.cid, source, n + 1, n, '2026-10-06T11:13:37Z', 'PowerplayMerits', str(n),
                 json.dumps(credit(1, 1, n + 1)), json.dumps({'sequence': n, 'power': 'Nakato Kaine'}), 1)
                for n in range(5768)])
        self.view.render()
        cached = self.view._day_cache._chronicle
        self.assertEqual(cached.groups, read_day(self.db, self.cid, DAY).groups)
        self.assertEqual(len(self.view._day_cache._rows), 5768)
        with patch('cmdrhelper.powerplay_store._decode_day') as replay:
            for _ in range(30):
                self.view.render()
            replay.assert_not_called()
