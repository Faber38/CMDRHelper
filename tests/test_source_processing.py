import tempfile
import unittest
from pathlib import Path
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.source_processing import SourceProcessor
from cmdrhelper.journal_catchup import load_sessions
from test_import_catchup import event, append


class ProcessingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = CMDRDatabase(self.root/'test.db')
        self.paths, self.processors = [], []
        for name in ('a', 'b'):
            folder = self.root/name; folder.mkdir()
            path = folder/'Journal.2026-09-14T120000.01.log'
            append(path, event('Commander', FID='F-'+name, Name='Same'),
                   event('Location', StarSystem=name, SystemAddress=1 if name == 'a' else 2))
            self.paths.append(path)
            self.processors.append(SourceProcessor(self.db, folder))

    def test_same_names_distinct_commanders_and_offsets(self):
        for processor in self.processors:
            processor.process()
        rows = load_sessions(self.db)
        self.assertEqual(len(rows), 2)
        self.assertEqual(len({row['commander_id'] for row in rows}), 2)
        for row in rows:
            self.assertEqual(row['last_read_offset'], Path(row['journal_file']).stat().st_size)
        append(self.paths[0], event('Location', StarSystem='changed', SystemAddress=3))
        self.processors[0].process()
        self.assertEqual(self.processors[1].sessions[0]['last_read_offset'], self.paths[1].stat().st_size)

    def test_conflict_does_not_block_other_source(self):
        append(self.paths[0], event('Commander', FID='conflict', Name='Same'))
        for processor in self.processors:
            processor.process()
        rows = load_sessions(self.db)
        bad = next(r for r in rows if r['journal_file'] == str(self.paths[0]))
        self.assertIsNone(bad['commander_id'])
        self.assertEqual(bad['last_read_offset'], 0)
        self.assertGreater(self.processors[1].sessions[0]['last_read_offset'], 0)

    def test_rotation_and_late_tail(self):
        processor = self.processors[0]
        processor.process()
        new = self.paths[0].with_name('Journal.2026-09-14T130000.01.log')
        append(new, event('Commander', FID='F-c', Name='Other'))
        processor.process()
        append(self.paths[0], event('Location', StarSystem='late', SystemAddress=4))
        processor.process()
        rows = processor.sessions
        self.assertEqual({r['fid_seen'] for r in rows}, {'F-a', 'F-c'})
        self.assertEqual(next(r for r in rows if r['fid_seen'] == 'F-a')['last_read_offset'], self.paths[0].stat().st_size)

    def test_partial_tail_and_transaction_rollback(self):
        import sqlite3
        from cmdrhelper.startup_runtime import JournalPending
        processor = self.processors[0]
        processor.process()
        before = dict(processor.sessions[0])
        append(self.paths[0], event('Location', StarSystem='new', SystemAddress=42))
        with self.db._connect() as con:
            con.execute("CREATE TRIGGER fail_cursor BEFORE UPDATE OF last_read_offset ON journal_sessions BEGIN SELECT RAISE(ABORT,'test'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            processor.process()
        after = next(r for r in load_sessions(self.db) if r['journal_file'] == str(self.paths[0]))
        for key in ('last_read_offset', 'last_complete_line_offset', 'modified_ns', 'file_size', 'sha256'):
            self.assertEqual(after[key], before[key], key)
        with self.db._connect() as con:
            con.execute('DROP TRIGGER fail_cursor')
        complete = self.paths[0].stat().st_size
        with self.paths[0].open('ab') as stream: stream.write(b'{"event":"Music"')
        with self.assertRaises(JournalPending): processor.process()
        row = next(r for r in load_sessions(self.db) if r['journal_file'] == str(self.paths[0]))
        self.assertEqual(row['last_read_offset'], complete)
        self.processors[1].process()
        with self.paths[0].open('ab') as stream: stream.write(b'}\n')
        processor.process()
        self.assertEqual(processor.sessions[0]['last_read_offset'], self.paths[0].stat().st_size)

    def test_personal_modules_with_same_local_ids_remain_isolated(self):
        from cmdrhelper.material_inventory import MaterialInventoryReader
        from cmdrhelper.odyssey_inventory import OdysseyInventoryReader
        from cmdrhelper.mining_inventory import MiningInventoryReader
        for index, path in enumerate(self.paths, 1):
            append(path,
                event('Loadout', Ship='cobramkiii', ShipID=7, ShipName='Ship'+str(index), Modules=[]),
                event('MissionAccepted', MissionID=9, Name='Mission_Delivery', Reward=index*100),
                event('Materials', Raw=[dict(Name='iron', Count=index)], Manufactured=[], Encoded=[]),
                event('Cargo', Vessel='Ship', Count=index, Inventory=[dict(Name='gold', Count=index, Stolen=0)]),
                event('ShipLocker', Items=[], Components=[dict(Name='graphene', Count=index, OwnerID=0)], Data=[], Consumables=[]),
                event('Backpack', Items=[], Components=[], Data=[], Consumables=[]),
                event('ScanOrganic', SystemAddress=index, Body=1, ScanType='Analyse',
                      Genus_Localised='Stratum', Species_Localised='Species'+str(index)),
                event('Powerplay', Power='Synthetic', Rank=1, Merits=index*10))
        from unittest.mock import patch
        from datetime import date
        with patch('cmdrhelper.powerplay_store.local_today', return_value=date(2026, 9, 14)):
            for processor in self.processors:
                processor.process()
        rows = load_sessions(self.db)
        material, odyssey, mining = MaterialInventoryReader(), OdysseyInventoryReader(), MiningInventoryReader()
        for index, processor in enumerate(self.processors, 1):
            row = processor.sessions[0]; cid, fid = row['commander_id'], row['fid_seen']
            self.assertEqual(self.db.commander_ships(cid)[0]['ship_name'], 'Ship'+str(index))
            self.assertEqual(self.db.commander_missions(cid)[0]['reward'], index*100)
            self.assertTrue(material.reconstruct(cid, fid, rows).known)
            self.assertEqual(odyssey.reconstruct(cid, fid, rows).count('graphene', 'ShipLocker'), index)
            # Match MiningInventoryController's commander-scoped SQL input.
            owned = [r for r in rows if r['commander_id'] == cid]
            self.assertEqual(mining.reconstruct(cid, fid, owned,
                live_path=row['journal_file']).ship['gold'], index)
            self.assertEqual(self.db.commander_summary(cid)['unsold_biology']['findings'], 1)
            self.assertEqual(self.db.powerplay_merits(cid, power='Synthetic'), index*10)

    def test_restart_resumes_partial_line_with_durable_prefix(self):
        from cmdrhelper.startup_runtime import JournalPending
        processor = self.processors[0]
        processor.process()
        with self.paths[0].open('ab') as stream: stream.write(b'{"event":"Music"')
        with self.assertRaises(JournalPending): processor.process()
        with self.paths[0].open('ab') as stream: stream.write(b'}\n')
        restarted = SourceProcessor(self.db, processor.path)
        restarted.process()
        self.assertEqual(restarted.sessions[0]['last_read_offset'], self.paths[0].stat().st_size)

    def test_restart_rejects_replacement_before_index_can_change_cursor(self):
        from cmdrhelper.journal_catchup import JournalConflict
        processor = self.processors[0]
        processor.process()
        before = dict(processor.sessions[0])
        self.paths[0].write_bytes(self.paths[0].read_bytes().replace(b'Same', b'Other'))
        with self.assertRaises(JournalConflict): SourceProcessor(self.db, processor.path).process()
        row = next(r for r in load_sessions(self.db) if r['journal_file'] == str(self.paths[0]))
        self.assertEqual(row, before)
