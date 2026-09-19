"""Current mission persistence, ordering, conservative snapshots and cleanup."""
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.journal_index import scan_journal_folder
from cmdrhelper.journal_reader import read_journal_delta, read_latest_state
from cmdrhelper.mission_persistence import cleanup_terminal_missions, snapshot_mission


def event(kind, second=1, **values):
    return dict(event=kind, timestamp=f'2026-09-18T12:00:{second:02d}Z', **values)


class CurrentMissionsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.db = CMDRDatabase(self.folder / 'state.db')
        self.a = self.db.upsert_commander('A', 'Same')
        self.b = self.db.upsert_commander('B', 'Same')
        self.path = self.folder / 'Journal.2026-09-18T120000.01.log'
        self.path.write_text(json.dumps(event('LoadGame', 0, FID='A', Commander='Same'))+'\n')

    def apply(self, *events, path=None):
        path = path or self.path
        with path.open('a') as stream:
            for item in events:
                stream.write(json.dumps(item)+'\n')
        session = next(s for s in scan_journal_folder(self.db, self.folder)
                       if s['journal_file'] == str(path))
        delta, offset = read_journal_delta(path, session['last_read_offset'], include_positions=True)
        self.db.apply_commander_journal_delta(session['commander_id'], path, delta, offset)

    def rows(self):
        return self.db.commander_missions(self.a)

    def test_all_terminal_events_remove_only_matching_commander_and_unknown_is_noop(self):
        for index, terminal in enumerate(('MissionCompleted', 'MissionFailed', 'MissionAbandoned')):
            with self.subTest(terminal=terminal):
                self.db.store_commander_missions(self.b, [{'mission_id': index}])
                self.apply(event('MissionAccepted', 1+index*3, MissionID=index))
                self.assertTrue(self.rows()[0]['is_open'])
                self.apply(event(terminal, 2+index*3, MissionID=index, Reward=123),
                           event(terminal, 3+index*3, MissionID=999))
                self.assertEqual(self.rows(), [])
                self.assertIn(index, [r['mission_id'] for r in self.db.commander_missions(self.b)])

    def test_progress_redirect_and_task_complete_stay_open(self):
        self.apply(event('MissionAccepted', 1, MissionID=7, Name='Mission_Delivery'),
                   event('MissionRedirected', 2, MissionID=7, NewDestinationSystem='Next'),
                   event('CargoDepot', 3, MissionID=7, CargoType='Gold',
                         UpdateType='Deliver', ItemsDelivered=10, TotalItemsToDeliver=10))
        row = self.rows()[0]
        self.assertTrue(row['is_open'])
        self.assertEqual(row['destination_system'], 'Next')
        self.assertEqual(row['status'], 'Aufgabe erledigt')
        self.assertEqual(row['next_step'], 'Zurück zum Missionsterminal')
        self.assertEqual(row['progress_text'], '10/10 geliefert')

    def test_sparse_active_and_complete_preserve_all_details(self):
        self.apply(event('MissionAccepted', 1, MissionID=7, Name='Mission_Delivery',
                         LocalisedName='Named', Reward=456, DestinationSystem='Here',
                         DestinationStation='Port', Commodity='Gold', Count=10,
                         Expiry='2026-09-20T00:00:00Z'),
                   event('CargoDepot', 2, MissionID=7, CargoType='Gold',
                         UpdateType='Deliver', ItemsDelivered=10, TotalItemsToDeliver=10))
        before = self.rows()[0]
        for second, arrays in ((3, dict(Active=[{'MissionID': 7, 'Name': 'Mission_Delivery'}])),
                               (4, dict(Active=[], Complete=[{'MissionID': 7}]))):
            self.apply(event('Missions', second, **arrays))
            after = self.rows()[0]
            self.assertEqual({k:v for k,v in before.items() if k != 'last_update'},
                             {k:v for k,v in after.items() if k != 'last_update'})
        memory = dict(before, commodity='Gold', count=10, extra={'source': 'ReceiveText+Missions'})
        merged = snapshot_mission({'MissionID': 7}, 'later', memory)
        for field in ('commodity', 'count', 'extra', 'summary', 'progress_text', 'next_step'):
            self.assertEqual(merged[field], memory[field])
        reader = read_latest_state(self.folder)
        self.assertEqual([r['mission_id'] for r in reader['missions']], [7])

    def test_missing_and_failed_become_inactive_not_deleted(self):
        self.apply(event('MissionAccepted', 1, MissionID=1),
                   event('MissionAccepted', 2, MissionID=2),
                   event('Missions', 3, Active=[{'MissionID': 3}], Failed=[{'MissionID': 2}]))
        rows = {r['mission_id']: r for r in self.rows()}
        self.assertEqual(set(rows), {1, 2, 3})
        self.assertTrue(rows[3]['is_open'])
        for mid in (1, 2):
            self.assertEqual(rows[mid]['terminal_state'], 'inactive')
        self.apply(event('Missions', 4, Active=[{'MissionID': 1}]))
        self.assertEqual([r['mission_id'] for r in self.db.commander_missions(self.a, only_open=True)], [1])

    def test_old_events_do_not_resurrect_after_restart_or_reset_cursor(self):
        self.apply(event('MissionAccepted', 1, MissionID=7), event('MissionCompleted', 9, MissionID=7))
        self.db = CMDRDatabase(self.db.path)
        for kind in ('MissionAccepted', 'CargoDepot', 'MissionRedirected', 'Missions'):
            values = {'Active': [{'MissionID': 7}]} if kind == 'Missions' else {'MissionID': 7}
            self.apply(event(kind, 2, **values))
            self.assertEqual(self.rows(), [])
        # A forced historical cursor replay must not undo a terminal event.
        with self.db._connect() as con:
            con.execute('UPDATE journal_sessions SET last_read_offset=0')
        self.apply()
        self.assertEqual(self.rows(), [])

    def test_old_snapshot_does_not_close_newer_mission(self):
        self.apply(event('MissionAccepted', 9, MissionID=7))
        self.apply(event('Missions', 2, Active=[]))
        self.assertTrue(self.rows()[0]['is_open'])

    def test_same_second_source_positions_survive_catchup_replay(self):
        from cmdrhelper.journal_catchup import capture, catch_up
        self.apply(event('MissionAccepted', 1, MissionID=7), event('MissionCompleted', 1, MissionID=7))
        with self.db._connect() as con:
            con.execute('UPDATE journal_sessions SET last_read_offset=0')
        context = capture(self.db, self.folder)
        with self.path.open('a') as stream:
            stream.write(json.dumps(event('Location', 2, StarSystem='Here', SystemAddress=42))+'\n')
        catch_up(self.db, context)
        self.assertEqual(self.rows(), [])
        self.assertEqual(self.db.commander_summary(self.a)['persistent_location']['system_name'], 'Here')

    def test_malformed_snapshot_does_not_close_or_advance_anchor(self):
        self.apply(event('MissionAccepted', 1, MissionID=7))
        for values in ({}, {'Active': None}, {'Active': [{}]}, {'Active': [], 'Complete': None}):
            self.apply(event('Missions', 9, **values))
            self.assertTrue(self.rows()[0]['is_open'])
        self.apply(event('MissionCompleted', 2, MissionID=7))
        self.assertEqual(self.rows(), [])

    def test_unidentified_snapshot_is_not_authoritative(self):
        self.apply(event('MissionAccepted', 1, MissionID=7))
        self.db.apply_commander_journal_delta(self.a, 'unidentified.log',
                                             [event('Missions', 2, Active=[])], 100)
        self.assertTrue(self.rows()[0]['is_open'])

    def test_commander_switch_and_restart_load_independent_current_states(self):
        self.apply(event('MissionAccepted', 1, MissionID=7, Name='Alpha'))
        other = self.folder / 'Journal.2026-09-18T130000.01.log'
        other.write_text(json.dumps(event('LoadGame', 0, FID='B', Commander='Same'))+'\n')
        self.apply(event('MissionAccepted', 2, MissionID=7, Name='Bravo'), path=other)
        self.db = CMDRDatabase(self.db.path)
        from cmdrhelper.state import AppState
        host = SimpleNamespace(database=self.db, commander_id=self.a)
        self.assertEqual(AppState._visible_commander_missions(host)[0].name, 'Alpha')
        host.commander_id = self.b
        self.assertEqual(AppState._visible_commander_missions(host)[0].name, 'Bravo')
        self.apply(event('MissionCompleted', 3, MissionID=7), path=other)
        self.assertEqual(AppState._visible_commander_missions(host), [])
        host.commander_id = self.a
        self.assertEqual(AppState._visible_commander_missions(host)[0].name, 'Alpha')

    def test_mission_repair_never_reads_history(self):
        self.apply(event('MissionAccepted', 1, MissionID=7), event('MissionFailed', 2, MissionID=7))
        with patch('cmdrhelper.journal_reader.read_latest_state', side_effect=AssertionError('no replay')):
            result = self.db.repair_commander_state(self.folder, [], self.a, features=('missions',))
        self.assertTrue(result['missions_repair_skipped'])
        self.assertEqual(self.rows(), [])

    def test_catchup_processes_terminal_without_history_and_keeps_other_facts(self):
        from cmdrhelper.journal_catchup import capture, catch_up
        self.apply(event('MissionAccepted', 1, MissionID=7))
        context = capture(self.db, self.folder)
        with self.path.open('a') as stream:
            for item in (event('MissionCompleted', 2, MissionID=7),
                         event('Location', 3, StarSystem='Here', SystemAddress=42)):
                stream.write(json.dumps(item)+'\n')
        catch_up(self.db, context)
        self.assertEqual(self.rows(), [])
        self.assertEqual(self.db.commander_summary(self.a)['persistent_location']['system_name'], 'Here')

    def test_terminal_still_enqueues_inara(self):
        self.apply(event('MissionAccepted', 1, MissionID=7))
        with self.path.open('a') as stream:
            stream.write(json.dumps(event('MissionCompleted', 2, MissionID=7, Reward=123))+'\n')
        session = scan_journal_folder(self.db, self.folder)[0]
        delta, offset = read_journal_delta(self.path, session['last_read_offset'])
        self.db.apply_commander_journal_delta(self.a, self.path, delta, offset, enqueue_inara=True)
        self.assertEqual(self.rows(), [])
        with self.db._connect() as con:
            self.assertEqual(con.execute('SELECT event_name FROM inara_outbox').fetchone()[0],
                             'setCommanderMissionCompleted')

    def test_cleanup_preserves_open_inactive_other_commander_and_pending(self):
        with self.db._connect() as con:
            schema = con.execute('SELECT name,sql FROM sqlite_master').fetchall()
            version = con.execute('PRAGMA user_version').fetchone()
            con.executemany('INSERT INTO commander_missions(commander_id,mission_id,is_open,terminal_state) '
                            'VALUES(?,?,?,?)', [(self.a,1,1,''), (self.a,2,0,'inactive'),
                            (self.a,3,0,'completed'), (self.a,4,0,'failed'),
                            (self.a,5,0,'abandoned'), (self.b,3,0,'completed')])
            con.execute("INSERT INTO app_meta VALUES('pending_mission_offers/A','untouched')")
            self.assertEqual(cleanup_terminal_missions(con, self.a), 3)
            self.assertEqual(cleanup_terminal_missions(con, self.a), 0)
            self.assertEqual(con.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            self.assertEqual(con.execute('PRAGMA foreign_key_check').fetchall(), [])
            self.assertEqual(con.execute('PRAGMA user_version').fetchone(), version)
            self.assertEqual(con.execute('SELECT name,sql FROM sqlite_master').fetchall(), schema)
            self.assertEqual(con.execute("SELECT value FROM app_meta WHERE key='pending_mission_offers/A'").fetchone()[0], 'untouched')
        self.assertEqual({r['mission_id'] for r in self.rows()}, {1,2})
        self.assertEqual(len(self.db.commander_missions(self.b)), 1)

    def test_copy_tool_refuses_existing_destination_and_never_changes_source(self):
        from tools.check_mission_cleanup import check_copy
        self.apply(event('MissionAccepted', 1, MissionID=7))
        with self.db._connect() as con:
            con.execute("INSERT INTO commander_missions(commander_id,mission_id,is_open,terminal_state) "
                        "VALUES(?,8,0,'completed')", (self.a,))
        before = self.rows()
        with self.assertRaises(FileExistsError):
            check_copy(self.db.path, self.db.path, clean=True)
        report = check_copy(self.db.path, self.folder/'cleaned.db', clean=True)
        self.assertEqual(report['removed'][self.a], 1)
        self.assertTrue(report['open_rows_identical'])
        self.assertTrue(report['other_tables_unchanged'])
        self.assertTrue(report['schema_unchanged'])
        self.assertEqual(self.rows(), before)

    def test_commander_tab_queries_only_current_rows(self):
        from cmdrhelper.ui.commander_view import CommanderView
        db = SimpleNamespace(commander_missions=Mock(return_value=[]))
        host = SimpleNamespace(state=SimpleNamespace(database=db), missions_table=Mock())
        CommanderView._refresh_missions(host, self.b)
        db.commander_missions.assert_called_once_with(self.b, only_open=True)

    def test_mission_reset_removed_from_active_ui(self):
        from cmdrhelper.state import AppState
        from cmdrhelper.ui.main_window import MainWindow
        import inspect
        self.assertFalse(hasattr(AppState, 'reset_missions'))
        self.assertFalse(hasattr(MainWindow, '_reset_missions'))
        self.assertNotIn('missions.reset', inspect.getsource(MainWindow))
