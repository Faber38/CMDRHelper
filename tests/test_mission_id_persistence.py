"""Synthetic boundary journals; no support-package data is used."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.journal_index import scan_journal_folder
from cmdrhelper.journal_reader import read_journal_delta, read_latest_state
from cmdrhelper.mission_manager import normalize_missions


IDS = (42, 2**63 - 1, 2**63, 2**63 + 1, 2**64 - 1, 2**80, -2**63 - 1, -2**63, 0)


def event(kind, **values):
    return {'timestamp': '2026-01-01T00:00:00Z', 'event': kind, **values}


class MissionIdPersistenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        self.db_path = self.folder / 'state.db'
        self.db = CMDRDatabase(self.db_path)
        self.commander = self.db.upsert_commander('FID-A', 'Synthetic')
        self.path = self.folder / 'Journal.2026-01-01T000000.01.log'

    def journal(self, events):
        self.path.write_text(''.join(json.dumps(e) + '\n' for e in [
            event('LoadGame', FID='FID-A', Commander='Synthetic'), *events
        ]), encoding='utf-8')
        return scan_journal_folder(self.db, self.folder)

    def apply(self):
        session = scan_journal_folder(self.db, self.folder)[0]
        events, offset = read_journal_delta(self.path, session['last_read_offset'])
        self.db.apply_commander_journal_delta(self.commander, self.path, events, offset)
        return offset

    def test_snapshot_delta_boundaries_persist_exactly(self):
        self.journal([
            event('Location', StarSystem='Synthetic system', SystemAddress=42),
            event('Missions', Active=[{'MissionID': mid} for mid in IDS]),
        ])
        offset = self.apply()
        self.db = CMDRDatabase(self.db_path)
        rows = self.db.commander_missions(self.commander)
        self.assertEqual({r['mission_id'] for r in rows}, set(IDS))
        self.assertTrue(all(type(r['mission_id']) is int and r['is_open'] for r in rows))
        self.assertEqual([r['mission_id'] for r in rows], sorted(IDS, reverse=True))
        self.assertEqual({m.mission_id for m in normalize_missions(rows)}, set(IDS))
        self.assertEqual(scan_journal_folder(self.db, self.folder)[0]['last_read_offset'], offset)
        self.assertEqual(self.db.commander_summary(self.commander)['persistent_location']['system_name'], 'Synthetic system')
        self.apply()  # Replay is idempotent.
        self.assertEqual(len(self.db.commander_missions(self.commander)), len(IDS))

    def test_reconstruction_repair_and_terminal_lifecycle(self):
        other = self.db.upsert_commander('FID-B', 'Other')
        self.db.store_commander_missions(other, [{'mission_id': 42, 'name': 'Other'}])
        events = [event('MissionAccepted', MissionID=mid, Name='Mission_Delivery',
                        DestinationSystem='Destination', Reward=123) for mid in IDS]
        events += [event('MissionCompleted', MissionID=IDS[2], Reward=456),
                   event('MissionFailed', MissionID=IDS[3]),
                   event('MissionAbandoned', MissionID=IDS[4])]
        sessions = self.journal(events)
        reconstructed = read_latest_state(self.folder, indexed_sessions=sessions, force_full_history=True)
        self.assertEqual({r['mission_id'] for r in reconstructed['missions']}, set(IDS) - set(IDS[2:5]))
        self.db.repair_commander_state(self.folder, sessions, self.commander, features=('missions',))
        self.assertEqual(self.db.commander_missions(self.commander), [])  # no historical repair
        self.apply()
        self.db = CMDRDatabase(self.db_path)
        rows = {r['mission_id']: r for r in self.db.commander_missions(self.commander)}
        self.assertEqual(set(rows), set(IDS) - set(IDS[2:5]))
        self.assertTrue(all(row['is_open'] for row in rows.values()))
        self.db.store_commander_missions(self.commander, [rows[42]], authoritative=True)
        self.assertEqual([r['mission_id'] for r in self.db.commander_missions(self.commander) if r['is_open']], [42])
        self.assertEqual(self.db.commander_missions(other)[0]['name'], 'Other')
        self.assertEqual(len(self.db.commander_missions(self.commander)), len(IDS) - 3)
        inactive = [r for r in self.db.commander_missions(self.commander) if not r['is_open']]
        self.assertTrue(all(r['terminal_state'] == 'inactive' for r in inactive))

    def test_existing_integer_schema_and_adjacent_ids(self):
        with self.db._connect() as con:
            version = con.execute('PRAGMA user_version').fetchone()[0]
            con.execute('INSERT INTO commander_missions(commander_id,mission_id,name) VALUES(?,?,?)',
                        (self.commander, 42, 'Existing'))
        self.db.store_commander_missions(self.commander, [{'mission_id': mid} for mid in IDS])
        self.db.store_commander_missions(self.commander, [{'mission_id': str(2**63), 'name': 'Updated'}])
        rows = {r['mission_id']: r for r in self.db.commander_missions(self.commander)}
        self.assertEqual(len(rows), len(IDS))
        self.assertEqual(rows[42]['name'], 'Existing')
        self.assertEqual(rows[2**63]['name'], 'Updated')
        with self.db._connect() as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], version)
            self.assertEqual(con.execute('SELECT typeof(mission_id) FROM commander_missions WHERE mission_id=42').fetchone()[0], 'integer')
            self.assertEqual(con.execute("SELECT COUNT(*) FROM commander_missions WHERE typeof(mission_id)='real'").fetchone()[0], 0)
            self.assertEqual(con.execute('PRAGMA integrity_check').fetchone()[0], 'ok')

    def test_sqlite_binding_and_decimal_text_are_not_lossless(self):
        with sqlite3.connect(':memory:') as con:
            con.execute('CREATE TABLE ids(id INTEGER)')
            with self.assertRaises(OverflowError):
                con.execute('INSERT INTO ids VALUES(?)', (2**63,))
            con.execute('INSERT INTO ids VALUES(?)', (str(2**63 + 1),))
            value, kind = con.execute('SELECT id,typeof(id) FROM ids').fetchone()
            self.assertEqual(kind, 'real')
            self.assertNotEqual(int(value), 2**63 + 1)

    def test_redirected_mission_keeps_identity_after_restart(self):
        mid = 2**63 + 1
        self.journal([event('MissionAccepted', MissionID=mid, Name='Mission_Delivery', Reward=123)])
        self.apply()
        self.db = CMDRDatabase(self.db_path)
        with self.path.open('a') as handle:
            handle.write(json.dumps(event('MissionRedirected', MissionID=mid,
                                          NewDestinationSystem='Redirected')) + '\n')
        self.apply()
        rows = self.db.commander_missions(self.commander)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['mission_id'], mid)
        self.assertEqual(rows[0]['reward'], 123)
        self.assertEqual(rows[0]['destination_system'], 'Redirected')

    def test_privacy_classification_never_logs_identifiers(self):
        from cmdrhelper.logging_config import PrivacyFormatter, _technical_fields
        with self.assertLogs('cmdrhelper.database', level='INFO') as captured:
            self.db.store_commander_missions(self.commander, [{'mission_id': mid} for mid in IDS])
        formatted = '\n'.join(PrivacyFormatter('%(message)s').format(r) for r in captured.records)
        for mid in IDS[1:7]:
            self.assertNotIn(str(mid), formatted)
            self.assertNotIn(str(mid), '\n'.join(captured.output))
        self.assertIn('field=mission_id', formatted)
        self.assertIn('python_type=int', formatted)
        self.assertIn('value_class=unsigned_64', formatted)
        self.assertIn('outside_sqlite_int64=True', formatted)
        self.assertEqual(_technical_fields({
            'field': str(2**63), 'python_type': str(2**63), 'value_class': str(2**63),
            'outside_sqlite_int64': 2**63, 'retry_seconds': 2**63, 'MissionID': 2**63,
        }), {})
