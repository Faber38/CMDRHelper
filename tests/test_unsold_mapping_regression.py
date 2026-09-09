"""Sale-scoped mapping claims: delta boundaries, restart and startup rebuild."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.journal_index import scan_journal_folder
from cmdrhelper.journal_reader import read_journal_delta, read_latest_state
from cmdrhelper.startup_repairs import run_startup_repairs, repair_status
from cmdrhelper.valuation import calculate_body_values


class UnsoldMappingRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.db = CMDRDatabase(self.folder / 'test.db')
        self.cid = self.db.upsert_commander('FTEST0001', 'FABER38')
        self.path = self.folder / 'Journal.2026-09-08T152958.01.log'
        self.scan = dict(event='Scan', timestamp='2026-09-08T15:09:38Z',
                         SystemAddress=6745908858227, BodyID=6,
                         StarSystem='Plio Aip JN-B d13-196', BodyName='Plio Aip JN-B d13-196 5',
                         ScanType='Detailed', PlanetClass='Water world', TerraformState='Terraformable',
                         MassEM=1.627342, WasDiscovered=False, WasMapped=False)
        self.mapping = dict(event='SAAScanComplete', timestamp='2026-09-08T15:24:31Z',
                            SystemAddress=self.scan['SystemAddress'], BodyID=6,
                            BodyName=self.scan['BodyName'], ProbesUsed=7, EfficiencyTarget=7)
        self.follow = dict(self.scan, timestamp=self.mapping['timestamp'])
        self.append([dict(event='LoadGame', timestamp='2026-09-08T15:00:00Z',
                          FID='FTEST0001', Commander='FABER38'),
                     dict(event='Location', timestamp='2026-09-08T15:00:01Z',
                          SystemAddress=self.scan['SystemAddress'], StarSystem=self.scan['StarSystem'])])

    def append(self, events):
        with self.path.open('a') as f:
            f.write(''.join(json.dumps(e)+'\n' for e in events))

    def apply(self):
        session = scan_journal_folder(self.db, self.folder)[0]
        events, offset = read_journal_delta(self.path, session['last_read_offset'])
        self.db.apply_commander_journal_delta(self.cid, self.path, events, offset)

    def claim(self):
        with self.db._connect() as con:
            con.row_factory = sqlite3.Row
            row = con.execute('SELECT * FROM commander_unsold_cartography WHERE commander_id=?',
                              (self.cid,)).fetchone()
            return dict(row) if row else None

    def replay(self):
        return read_latest_state(self.folder, force_full_history=True)['unsold_cartography']

    def assert_mapping(self, value=3536354):
        c = self.claim()
        self.assertEqual(c['raw_estimated_value'], value)
        self.assertEqual(c['mapped_at'], self.mapping['timestamp'])
        self.assertEqual(c['self_mapped'], 1)
        self.assertEqual(c['probes_used'], self.mapping['ProbesUsed'])
        self.assertEqual(c['efficiency_target'], 7)
        r = self.replay()[0]
        for field in ('mapped_at', 'self_mapped', 'efficient_mapping', 'probes_used', 'efficiency_target'):
            self.assertEqual(c[field], r[field])
        self.assertEqual(r['estimated_value'], value)

    def test_faber38_same_delta_follow_scan(self):
        self.append([self.scan, self.mapping, self.follow]); self.apply(); self.assert_mapping()

    def test_scan_mapping_same_timestamp(self):
        self.scan['timestamp'] = self.mapping['timestamp']
        self.test_faber38_same_delta_follow_scan()

    def test_follow_scan_next_delta(self):
        self.append([self.scan, self.mapping]); self.apply()
        self.append([self.follow]); self.apply(); self.assert_mapping()

    def test_restart_between_mapping_and_follow_scan(self):
        self.append([self.scan, self.mapping]); self.apply()
        self.db = CMDRDatabase(self.db.path)
        self.append([self.follow]); self.apply(); self.assert_mapping()

    def test_mapping_in_next_delta_uses_actual_efficiency(self):
        # Normal runtime has stored the scan snapshot before the next delta.
        body = dict(body_id=6, name=self.scan['BodyName'], planet_class='Water world',
                    mass_em=1.627342, terraformable=True, was_discovered=False, was_mapped=False)
        self.db.store_snapshot(dict(system_address=self.scan['SystemAddress'],
                                    system=self.scan['StarSystem'], system_bodies=[body]), self.cid)
        self.append([self.scan]); self.apply()
        self.mapping['ProbesUsed'] = 8
        self.append([self.mapping, self.follow]); self.apply(); self.assert_mapping(2829083)

    def test_discovery_and_efficiency_combinations(self):
        for discovered, mapped in ((False, False), (True, False), (True, True)):
            for probes in (7, 8):
                with self.subTest(discovered=discovered, mapped=mapped, probes=probes):
                    scan = dict(self.scan, WasDiscovered=discovered, WasMapped=mapped)
                    mapping = dict(self.mapping, ProbesUsed=probes)
                    self.append([dict(event='SellExplorationData', timestamp='2026-09-08T15:00:00Z'),
                                 scan, mapping, dict(scan, timestamp=self.follow['timestamp'])])
                    self.apply()
                    value = calculate_body_values(dict(planet_class='Water world', mass_em=1.627342,
                        terraformable=True, was_discovered=discovered, was_mapped=mapped,
                        self_mapped=True, efficient_mapping=probes<=7))['current_value']
                    self.assertEqual(self.claim()['raw_estimated_value'], value)
                    self.assertEqual(self.replay()[0]['estimated_value'], value)

    def test_sale_then_scan_does_not_resurrect_mapping(self):
        for kind in ('SellExplorationData', 'MultiSellExplorationData'):
            with self.subTest(kind=kind):
                self.append([self.scan, self.mapping]); self.apply()
                self.append([dict(event=kind, timestamp='2026-09-08T15:25:00Z'),
                             dict(self.follow, timestamp='2026-09-08T15:26:00Z')]); self.apply()
                self.assertEqual(self.claim()['raw_estimated_value'], 764695)
                self.assertEqual(self.claim()['self_mapped'], 0)
                self.assertEqual(self.replay()[0]['estimated_value'], 764695)
                self.assertFalse(self.replay()[0]['self_mapped'])

    def test_follow_scan_then_sale_clears_claim(self):
        self.append([self.scan, self.mapping, self.follow,
                     dict(event='MultiSellExplorationData', timestamp='2026-09-08T15:25:00Z')])
        self.apply(); self.assertIsNone(self.claim()); self.assertEqual(self.replay(), [])

    def test_sold_scan_then_mapping_follow_scan_only_mapping_increment(self):
        self.append([self.scan, dict(event='SellExplorationData', timestamp='2026-09-08T15:10:00Z'),
                     self.mapping, self.follow]); self.apply()
        self.assert_mapping(3536354 - 764695)
        self.assertEqual(self.claim()['scanned_at'], '')

    def corrupt(self):
        self.append([self.scan, self.mapping, self.follow]); self.apply()
        with self.db._connect() as con:
            con.execute('UPDATE commander_unsold_cartography SET raw_estimated_value=764695, estimated_value=720077')

    def repair(self):
        with patch('cmdrhelper.startup_repairs.FEATURES', ('unsold_cartography',)):
            return run_startup_repairs(self.db.path)

    def test_startup_repair_backup_and_idempotence(self):
        self.corrupt()
        result = self.repair()[0]
        self.assertEqual(result['status'], 'complete'); self.assert_mapping()
        with sqlite3.connect(result['backup']) as backup:
            self.assertEqual(backup.execute('SELECT raw_estimated_value FROM commander_unsold_cartography').fetchone()[0],764695)
        self.assertEqual(self.repair(), [])

    def test_missing_source_leaves_revision_open(self):
        self.corrupt(); self.path.unlink()
        self.assertEqual(self.repair()[0]['status'], 'incomplete')
        self.assertEqual(self.claim()['estimated_value'],720077)
        with self.db._connect() as con:
            self.assertNotEqual(repair_status(con,self.cid,'unsold_cartography'),'complete')

    def test_uncertain_session_never_repairs_claim(self):
        self.corrupt()
        for status in ('ambiguous', 'unknown'):
            with self.db._connect() as con:
                con.execute('UPDATE journal_sessions SET attribution_status=?', (status,))
            self.assertEqual(self.repair()[0]['status'], 'incomplete')
            self.assertEqual(self.claim()['estimated_value'],720077)

    def test_failure_after_writes_rolls_back(self):
        self.corrupt()
        from cmdrhelper.unsold_cartography import apply_cartography_repair
        def fail(*args):
            apply_cartography_repair(*args)
            raise RuntimeError('interrupted')
        with patch('cmdrhelper.unsold_cartography.apply_cartography_repair', fail):
            self.assertEqual(self.repair()[0]['status'],'failed')
        self.assertEqual(self.claim()['estimated_value'],720077)
        self.assertEqual(self.repair()[0]['status'],'complete')

    def test_repair_preserves_other_commander_and_unrelated_tables(self):
        self.corrupt()
        other = self.db.upsert_commander('F-other','Other')
        self.db.store_commander_unsold_data(other, [], [dict(system_address=1,body_id=1,estimated_value=99)])
        with self.db._connect() as con:
            before = con.execute('SELECT * FROM commander_unsold_cartography WHERE commander_id=?',(other,)).fetchall()
            biology = con.execute('SELECT * FROM commander_unsold_biology').fetchall()
        self.repair()
        with self.db._connect() as con:
            self.assertEqual(before,con.execute('SELECT * FROM commander_unsold_cartography WHERE commander_id=?',(other,)).fetchall())
            self.assertEqual(biology,con.execute('SELECT * FROM commander_unsold_biology').fetchall())

    def test_historical_mapped_cache_after_sale_is_not_an_open_claim(self):
        self.db.store_snapshot(dict(system_address=self.scan['SystemAddress'],
            system=self.scan['StarSystem'], system_bodies=[dict(body_id=6, name=self.scan['BodyName'],
                planet_class='Water world', mass_em=1.627342, terraformable=True,
                self_mapped=True, efficient_mapping=True, was_discovered=False, was_mapped=False,
                mapped_at=self.mapping['timestamp'], probes_used=7, efficiency_target=7)]), self.cid)
        self.append([self.scan, self.mapping,
                     dict(event='SellExplorationData', timestamp='2026-09-08T15:25:00Z')]); self.apply()
        self.db = CMDRDatabase(self.db.path)
        self.append([dict(self.follow,timestamp='2026-09-08T15:26:00Z')]); self.apply()
        self.assertEqual(self.claim()['raw_estimated_value'],764695)
        self.assertFalse(self.claim()['self_mapped'])

    def test_schema_metadata_migration_rolls_back_and_retries(self):
        with self.db._connect() as con:
            for field in ('efficient_mapping','probes_used','efficiency_target'):
                con.execute('ALTER TABLE commander_unsold_cartography DROP COLUMN '+field)
            con.execute('PRAGMA user_version=16')
        class Interrupted(sqlite3.Connection):
            def execute(self, sql, *args):
                result = super().execute(sql, *args)
                if sql.startswith('ALTER TABLE commander_unsold_cartography'):
                    raise RuntimeError('migration interrupted')
                return result
        con = sqlite3.connect(self.db.path, factory=Interrupted)
        try:
            with patch.object(self.db,'_connect',return_value=con):
                with self.assertRaises(RuntimeError):self.db._maybe_migrate_v17()
        finally:
            con.close()
        with self.db._connect() as con:
            self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0],16)
            self.assertNotIn('efficient_mapping',[r[1] for r in con.execute('PRAGMA table_info(commander_unsold_cartography)')])
        self.db = CMDRDatabase(self.db.path)
        self.test_restart_between_mapping_and_follow_scan()
