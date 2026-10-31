"""Payload-free failure evidence, conservative retries and startup status."""
import json
import os
import subprocess
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import test_startup_repairs as fixtures
from cmdrhelper import startup_repairs as repairs
from cmdrhelper.backfill_support import committed_journals, JournalRepairError
from cmdrhelper.logging_config import _technical_fields
from cmdrhelper.source_manager import SourceManager
from cmdrhelper.source_processing import SourceProcessor


class RepairFailureManagementTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.StartupRepairTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.seed()
        self.db, self.path = self.fixture.db, self.fixture.file
        self.original = self.path.read_bytes()

    def corrupt(self, value=b'{broken}\n', position=2):
        lines = self.original.splitlines(keepends=True)
        lines.insert(position, value)
        self.path.write_bytes(b''.join(lines))
        with self.db._connect() as con:
            con.execute('UPDATE journal_sessions SET last_read_offset=?,last_complete_line_offset=?',
                        (self.path.stat().st_size, self.path.stat().st_size))

    def run_repairs(self):
        return repairs.run_startup_repairs(self.db.path)

    def test_diagnostics_positions_types_and_privacy(self):
        for position in (0, 2, len(self.original.splitlines())):
            for value, reason in ((b'{"SECRET":broken}\n', 'repair_json_syntax'),
                                  (b'[]\n', 'repair_json_type'), (b'\xff\n', 'repair_json_encoding')):
                with self.subTest(position=position, reason=reason):
                    self.corrupt(value, position)
                    with self.db._connect() as con:
                        with self.assertRaises(JournalRepairError) as caught:
                            list(committed_journals(con, self.fixture.cid))
                    error = caught.exception
                    self.assertEqual(error.line_number, position+1)
                    self.assertEqual(error.reason, reason)
                    self.assertNotIn('SECRET', str(error))
                    self.assertNotIn(str(self.path), str(error))
                    self.assertNotIn('F-A', str(error))
                    safe = _technical_fields(vars(error))
                    self.assertEqual(safe['source_ref'], error.source_ref)
                    self.assertEqual(safe['line_number'], position+1)
        self.assertNotIn('source_ref', _technical_fields({'source_ref': str(self.path)}))

    def test_retry_restart_same_size_edit_and_recovery(self):
        self.corrupt()
        before = self.fixture.snapshot()
        first = self.run_repairs()
        self.assertEqual([r['status'] for r in first], ['failed']*5)
        with patch.object(repairs, '_plan', side_effect=AssertionError('must defer')):
            repeated = self.run_repairs()  # New SQLite connection, persistent evidence.
        self.assertTrue(all(r['retry_deferred'] for r in repeated))
        script = """import sys
from unittest.mock import patch
from cmdrhelper import startup_repairs as r
with patch.object(r, '_plan', side_effect=AssertionError('unexpected planning')):
    result = r.run_startup_repairs(sys.argv[1])
assert len(result) == 5 and all(x.get('retry_deferred') and x['status']=='failed' for x in result)
"""
        subprocess.run([sys.executable, '-c', script, str(self.db.path)], check=True,
                       capture_output=True)
        with self.db._connect() as con:
            self.assertTrue(all(repairs.repair_status(con, self.fixture.cid, f) == 'failed'
                                for f in repairs.FEATURES))
        after = self.fixture.snapshot()
        for table in ('biology', 'system_visits', 'commander_bodies'):
            self.assertEqual(before[table], after[table])
        stat = self.path.stat()
        self.path.write_bytes(self.path.read_bytes().replace(b'broken', b'BROKEN'))
        os.utime(self.path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        with patch.object(repairs, '_plan', wraps=repairs._plan) as plan:
            self.run_repairs()
        self.assertEqual(plan.call_count, 5)
        self.path.write_bytes(self.original)
        with self.db._connect() as con:
            con.execute('UPDATE journal_sessions SET last_read_offset=?,last_complete_line_offset=?',
                        (len(self.original), len(self.original)))
        self.assertEqual([r['status'] for r in self.run_repairs()], ['complete']*5)

    def test_new_removed_files_and_protected_coverage_invalidate(self):
        self.corrupt(); self.run_repairs()
        extra = self.path.with_name('Journal.2026-09-08T010000.01.log')
        extra.write_bytes(self.original)
        for change in ('added', 'removed', 'coverage'):
            if change == 'removed':
                extra.unlink()
            if change == 'coverage':
                with self.db._connect() as con:
                    con.execute('UPDATE journal_sessions SET repair_read_offset=repair_read_offset+1')
            with patch.object(repairs, '_plan', wraps=repairs._plan) as plan:
                self.run_repairs()
            self.assertEqual(plan.call_count, 5)

    def test_unknown_io_never_defers(self):
        self.corrupt(); self.run_repairs(); self.path.unlink()
        with patch.object(repairs, '_plan', wraps=repairs._plan) as plan:
            results = self.run_repairs()
        self.assertEqual(plan.call_count, 5)
        self.assertEqual([r['status'] for r in results], ['incomplete']*5)

    def test_commander_and_revision_invalidate(self):
        self.corrupt(); self.run_repairs()
        other = self.db.upsert_commander('OTHER-FID', 'Other')
        self.run_repairs()
        with self.db._connect() as con:
            con.execute('UPDATE commanders SET fid=? WHERE id=?', ('REPLACED-FID', self.fixture.cid))
        with patch.object(repairs, '_plan', wraps=repairs._plan) as plan:
            self.run_repairs()
        self.assertEqual(plan.call_count, 5)
        with patch.dict(repairs.COMMANDER_STATE_REPAIR_REVISIONS,
                        biology_findings=repairs.COMMANDER_STATE_REPAIR_REVISIONS['biology_findings']+1):
            with patch.object(repairs, '_plan', wraps=repairs._plan) as plan:
                self.run_repairs()
            self.assertGreaterEqual(plan.call_count, 5)

    def test_processor_results_reach_partial_startup_and_remain(self):
        # Separate fresh source, no damaged consumed prefix or production settings.
        folder = self.path.parent/'source'; folder.mkdir()
        (folder/self.path.name).write_bytes(self.original)
        processor = SourceProcessor(self.db, folder)
        results = [dict(feature='biology_findings', status='failed'),
                   dict(feature='unsold_cartography', status='incomplete')]
        with patch.object(repairs, 'run_startup_repairs', return_value=results):
            processor.process()
        self.assertEqual(processor.repair_results, results)
        processor.process()
        self.assertEqual(processor.repair_results, results)
        state = SimpleNamespace(_initialization_error='', _startup_completed=False,
                                startup_issues=[], initializationFinished=Mock())
        manager = SimpleNamespace(state=state, _startup_pending={('source', 1): 'Synthetic'},
                                  runtimes={'source': SimpleNamespace(generation=1, processor=processor)})
        manager._complete_startup_if_ready = lambda: SourceManager._complete_startup_if_ready(manager)
        SourceManager._finish_startup_source(manager, 'source', 1)
        self.assertEqual(state.startup_status, 'partial')
        self.assertEqual(state.startup_issues, ['history', 'unsold_cartography'])
        SourceManager._finish_startup_source(manager, 'source', 1)
        state.initializationFinished.emit.assert_called_once_with('')

    def test_hint_storage_is_bounded(self):
        with self.db._connect() as con:
            con.executemany('INSERT INTO app_meta(key,value) VALUES(?,?)',
                            [(f'repair_failure/v1/old/{i}', '0'*64) for i in range(140)])
        self.corrupt(); self.run_repairs()
        with self.db._connect() as con:
            self.assertLessEqual(con.execute("SELECT COUNT(*) FROM app_meta WHERE key LIKE 'repair_failure/v1/%'").fetchone()[0], 128)

    def test_unconfirmed_tail_is_not_a_repair_failure(self):
        with self.path.open('ab') as stream:
            stream.write(b'{broken')
        self.assertEqual([r['status'] for r in self.run_repairs()], ['complete']*5)

    def test_cartography_incomplete_hint_does_not_skip_mapping(self):
        with self.db._connect() as con:
            for feature in repairs.FEATURES:
                repairs._record(con, self.fixture.cid, feature,
                                'incomplete' if feature in ('mapping_metadata', 'unsold_cartography') else 'complete')
            token = repairs._source_token(con, self.fixture.cid)
            con.execute('INSERT OR REPLACE INTO app_meta(key,value) VALUES(?,?)',
                        (f'startup_retry:unsold_cartography:{self.fixture.cid}', token))
        with patch.object(repairs, '_plan', wraps=repairs._plan) as plan:
            results = self.run_repairs()
        self.assertEqual([call.args[2] for call in plan.call_args_list], ['mapping_metadata'])
        self.assertEqual([r['status'] for r in results], ['complete', 'incomplete'])
