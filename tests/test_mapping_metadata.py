"""DSS metadata survives Scan replacement, reloads and bounded recovery."""
import json
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.exploration_status import status_rows
from cmdrhelper.journal_reader import read_latest_state
from cmdrhelper.mapping_metadata_backfill import backfill_mapping_metadata
from cmdrhelper.state import AppState


NAME = 'Plio Aip KN-B d13-229 5 d'
ADDRESS = 7879797001587
STAMP = '2026-09-08T08:12:40Z'
METADATA = dict(mapped_at=STAMP, probes_used=3, efficiency_target=4)


class MappingMetadataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.path = self.folder / 'test.db'
        self.db = CMDRDatabase(self.path)
        self.commander = self.db.upsert_commander('F12520967', 'FABER38')
        self.journal = self.folder / 'Journal.2026-09-08T071547.01.log'
        self.scan = dict(event='Scan', timestamp='2026-09-08T08:04:39Z',
            BodyName=NAME, BodyID=24, SystemAddress=ADDRESS,
            StarSystem='Plio Aip KN-B d13-229', PlanetClass='Rocky body',
            WasDiscovered=True, WasMapped=False)
        self.saa = dict(event='SAAScanComplete', timestamp=STAMP,
            BodyName=NAME, BodyID=24, SystemAddress=ADDRESS,
            ProbesUsed=3, EfficiencyTarget=4)
        self.write([self.scan, self.saa, {**self.scan, 'timestamp': STAMP}])

    def write(self, events):
        identity = dict(event='Commander', timestamp='2026-09-08T05:16:32Z',
                        FID='F12520967', Name='FABER38')
        location = dict(event='Location', timestamp='2026-09-08T08:02:00Z',
                        StarSystem='Plio Aip KN-B d13-229', SystemAddress=ADDRESS)
        self.journal.write_text(''.join(json.dumps(e)+'\n' for e in [identity, location, *events]))

    def live(self):
        data = read_latest_state(self.folder)
        return data, next(b for b in data['system_bodies'] if b['body_id'] == 24)

    def saved(self):
        return self.db.chronicle_system_details(ADDRESS, self.commander, scanned_only=True)['bodies'][0]

    def assert_metadata(self, body, expected=METADATA):
        self.assertEqual({key: body.get(key) for key in expected}, expected)

    def seed_missing(self):
        data, body = self.live()
        for key in METADATA:
            body.pop(key, None)
        self.db.store_snapshot(data, self.commander)

    def repair(self, **extra):
        return backfill_mapping_metadata(self.path, self.journal, 'F12520967',
            ADDRESS, 24, NAME, STAMP, **extra)

    def test_completion_and_later_scan_keep_timestamp_and_both_counts(self):
        data, body = self.live()
        self.assert_metadata(body)
        self.assertTrue(body['self_mapped'])
        self.assertTrue(body['efficient_mapping'])
        before_status = status_rows(body)
        self.db.store_snapshot(data, self.commander)
        saved = self.saved()
        self.assert_metadata(saved)
        self.assertEqual(status_rows(saved), before_status)
        self.assertTrue(saved['self_mapped'])
        self.assertTrue(saved['efficient_mapping'])

    def test_rereading_is_idempotent(self):
        data, _ = self.live()
        self.db.store_snapshot(data, self.commander)
        before = self.saved()
        data, body = self.live()
        self.db.store_snapshot(data, self.commander)
        self.assertEqual(before, self.saved())
        self.assert_metadata(body)

    def test_optional_counts_update_independently_and_absence_preserves(self):
        for supplied, expected in [({}, METADATA),
                ({'ProbesUsed': 0}, {**METADATA, 'probes_used': 0}),
                ({'EfficiencyTarget': 5}, {**METADATA, 'efficiency_target': 5})]:
            partial = {k:v for k,v in self.saa.items() if k not in ('ProbesUsed','EfficiencyTarget')}
            partial.update(timestamp='2026-09-08T08:13:00Z', **supplied)
            self.write([self.scan, self.saa, partial, {**self.scan, 'timestamp':'2026-09-08T08:14:00Z'}])
            data, body = self.live()
            self.assert_metadata(body, expected)
            self.assertTrue(body['self_mapped'])
            self.assertTrue(body['efficient_mapping'])
            self.db.store_snapshot(data, self.commander)
            self.assert_metadata(self.saved(), expected)

    def test_plain_scan_snapshot_cannot_clear_db_metadata(self):
        data, body = self.live()
        self.db.store_snapshot(data, self.commander)
        for key in METADATA:
            body[key] = None
        self.db.store_snapshot(data, self.commander)
        self.assert_metadata(self.saved())

    def test_saved_metadata_returns_in_live_merge(self):
        data, body = self.live()
        self.db.store_snapshot(data, self.commander)
        for key in METADATA:
            body.pop(key)
        state = SimpleNamespace(database=self.db, commander_id=self.commander, system_address=ADDRESS)
        merged = AppState._own_explorer_bodies(state, [body])[0]
        self.assert_metadata(merged)
        self.assert_metadata(self.saved())
        self.assertNotIn('mapped_at', body)  # Caller input remains untouched.

    def test_delta_persists_metadata_even_without_a_scan_in_the_batch(self):
        self.seed_missing()
        self.db.apply_commander_journal_delta(self.commander, self.journal, [self.saa], 10)
        self.assert_metadata(self.saved())
        self.db.apply_commander_journal_delta(self.commander, self.journal, [self.saa], 11)
        self.assert_metadata(self.saved())

    def test_archive_import_preserves_metadata_after_following_scan(self):
        self.db.import_journal_archive(self.folder)
        self.assert_metadata(self.saved())
        self.db.import_journal_archive(self.folder)
        self.assert_metadata(self.saved())

    def test_targeted_backfill_preview_backup_and_second_run_zero(self):
        self.seed_missing()
        preview = self.repair()
        self.assertEqual(preview['missing_fields'], METADATA)
        self.assertEqual(preview['before'], preview['after'])
        result = self.repair(apply=True)
        self.assertEqual(result['changed_rows'], 1)
        self.assertEqual(result['after'], {**result['before'], **METADATA})
        with sqlite3.connect(result['backup']) as con:
            self.assertEqual(con.execute('select mapped_at,probes_used,efficiency_target from commander_bodies').fetchone(), (None,None,None))
            self.assertEqual(con.execute('pragma quick_check').fetchone()[0], 'ok')
        self.assert_metadata(self.saved())
        second = self.repair(apply=True)
        self.assertEqual(second['changed_rows'], 0)
        self.assertIsNone(second['backup'])

    def test_backfill_keeps_existing_values_and_other_commanders(self):
        self.seed_missing()
        with self.db._connect() as con:
            con.execute("update commander_bodies set probes_used=2")
        before = self.saved()
        other = self.db.upsert_commander('OTHER', 'Other')
        data, _ = self.live()
        self.db.store_snapshot(data, other)
        result = self.repair(apply=True)
        self.assertEqual(result['after']['probes_used'], 2)
        self.assertEqual(status_rows(self.saved()), status_rows(before))
        saved_other = self.db.chronicle_system_details(ADDRESS, other, scanned_only=True)['bodies'][0]
        self.assert_metadata(saved_other)

    def test_backfill_refuses_wrong_commander_and_existing_backup(self):
        self.seed_missing()
        text = self.journal.read_text()
        self.journal.write_text(text.replace('F12520967','OTHER'))
        with self.assertRaises(ValueError):
            self.repair(apply=True)
        self.journal.write_text(text)
        occupied = self.folder/'occupied.bak'
        occupied.write_text('keep')
        with self.assertRaises(FileExistsError):
            self.repair(apply=True, backup_path=occupied)
        self.assertEqual(occupied.read_text(), 'keep')
        self.assertIsNone(self.saved()['mapped_at'])
