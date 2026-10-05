"""Persistent checkpoints and additive schema migration, on synthetic files only."""
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
from threading import Event
import unittest
from unittest.mock import patch

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.pad_metadata import PadMetadata
from cmdrhelper.market_data import PadSize
from cmdrhelper.station_pad_store import read_local
from cmdrhelper.trade_market_source import TradeReadCancelled


def event(**changes):
    return dict(dict(event='Docked', MarketID=2, StarSystem='System', SystemAddress=3,
                     StationName='Port', StationType='Outpost', timestamp='2026-01-01T00:00:00Z',
                     LandingPads=dict(Small=2, Medium=1, Large=0)), **changes)


class LegacyDatabase(CMDRDatabase):
    def _maybe_migrate_v22(self):
        pass


class MigrationTests(unittest.TestCase):
    def test_20_and_21_preserve_existing_schema_and_data(self):
        for version in (20, 21):
            with self.subTest(version=version), TemporaryDirectory() as tmp:
                p = Path(tmp)/'main.db'
                LegacyDatabase(p)
                with sqlite3.connect(p) as con:
                    if version == 21:
                        con.executescript('''CREATE TABLE codex_events (
                            id INTEGER PRIMARY KEY, commander_id INTEGER NOT NULL REFERENCES commanders(id),
                            journal_file TEXT NOT NULL, source_offset INTEGER NOT NULL,
                            event_hash TEXT NOT NULL, event_type TEXT NOT NULL, timestamp TEXT NOT NULL,
                            event_time TEXT NOT NULL, entry_id INTEGER, system_address INTEGER, body_id INTEGER,
                            is_new INTEGER CHECK(is_new IN (0,1) OR is_new IS NULL), raw_json TEXT NOT NULL,
                            UNIQUE(commander_id,journal_file,source_offset,event_hash));
                            CREATE TABLE codex_backfills (journal_file TEXT PRIMARY KEY,
                            commander_id INTEGER NOT NULL REFERENCES commanders(id), version INTEGER NOT NULL,
                            sha256 TEXT NOT NULL, complete_offset INTEGER NOT NULL);
                            CREATE INDEX idx_codex_revision ON codex_events(commander_id,id DESC);
                            PRAGMA user_version=21;''')
                        con.execute("INSERT INTO commanders(id,fid) VALUES(1,'F_SYNTHETIC')")
                        con.execute("INSERT INTO codex_events VALUES(1,1,'archive',5,'hash','CodexEntry','time','time',7,8,9,1,'{}')")
                        con.execute("INSERT INTO codex_backfills VALUES('archive',1,2,'hash',100)")
                    before = con.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY name').fetchall()
                    tables = ['codex_events','codex_backfills'] if version == 21 else []
                    data = {t:con.execute('SELECT * FROM '+t).fetchall() for t in tables}
                CMDRDatabase(p)
                CMDRDatabase(p)
                with sqlite3.connect(p) as con:
                    self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0],22)
                    after = con.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY name').fetchall()
                    self.assertTrue(set(before) <= set(after))
                    for t, rows in data.items():
                        self.assertEqual(con.execute('SELECT * FROM '+t).fetchall(), rows)
                    if version == 20:
                        self.assertFalse(con.execute("SELECT name FROM sqlite_master WHERE name LIKE 'codex_events%' OR name LIKE 'codex_backfills%'").fetchall())
                backups=list(Path(tmp).glob('*.pre-v22-*.bak'))
                self.assertEqual(len(backups),1)
                with sqlite3.connect(backups[0]) as con:
                    self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0],version)

    def test_migration_failure_rolls_back(self):
        from cmdrhelper.station_pad_store import create_schema
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/'main.db'; LegacyDatabase(p)
            def fail(con):
                create_schema(con)
                raise RuntimeError('injected migration failure')
            with patch('cmdrhelper.station_pad_store.create_schema', side_effect=fail):
                with self.assertRaises(RuntimeError): CMDRDatabase(p)
            with sqlite3.connect(p) as con:
                self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0],20)
                self.assertFalse(con.execute("SELECT name FROM sqlite_master WHERE name LIKE 'station_pad_%'").fetchall())
            CMDRDatabase(p)


class PadStoreTests(unittest.TestCase):
    def setUp(self):
        tmp=TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name); self.folder=self.root/'journals'; self.folder.mkdir()
        self.db=self.root/'main.db'; CMDRDatabase(self.db)
        self.path=self.folder/'Journal.01.log'

    def write(self, events, path=None, mode='w'):
        with (path or self.path).open(mode) as stream:
            for e in events: stream.write(json.dumps(e)+'\n')

    def read(self, **kw): return read_local(self.db,self.folder,**kw)

    def checkpoint(self):
        with sqlite3.connect(self.db) as con:
            return con.execute('SELECT processed_offset FROM station_pad_journals WHERE journal_path=?',(str(self.path),)).fetchone()[0]

    def test_docked_persists_all_fields_and_u64(self):
        self.write([event(MarketID=2**64-1,SystemAddress=2**64-2)])
        self.assertEqual(self.read()[2**64-1]['system_address'],2**64-2)
        with sqlite3.connect(self.db) as con:
            row=con.execute('SELECT station_type,small_pads,medium_pads,large_pads,source,event_type,event_offset FROM station_pad_evidence').fetchone()
            self.assertEqual(row,('Outpost',2,1,0,'local_elite','Docked',0))

    def test_docking_requested_context_survives_restart(self):
        self.write([dict(event='Location',StarSystem='System',SystemAddress=3)])
        self.read(); e=event(event='DockingRequested');del e['StarSystem'];del e['SystemAddress']
        self.write([e],mode='a')
        self.assertEqual(PadMetadata(self.db).read(self.folder)[2]['system_address'],3)

    def test_session_reset_and_rotation_do_not_leak_context(self):
        self.write([dict(event='Location',StarSystem='System',SystemAddress=3)])
        self.read(); e=event(event='DockingRequested');del e['StarSystem'];del e['SystemAddress']
        self.write([dict(event='LoadGame'),e],mode='a')
        self.write([e],self.folder/'Journal.02.log')
        self.assertEqual(self.read(),{})

    def test_invalid_evidence_does_not_erase_valid(self):
        cases=[dict(MarketID=None),dict(MarketID=True),dict(StationName=''),dict(StarSystem=''),
               dict(SystemAddress=-1),dict(StationType=123),dict(timestamp='invalid'),
               dict(LandingPads={'Small':1,'Medium':0}),dict(LandingPads={'Small':1,'Medium':0,'Large':True}),
               dict(LandingPads={'Small':1,'Medium':-1,'Large':0}),dict(LandingPads={'Small':1,'Medium':0,'Large':2**70})]
        self.write([event()]+[event(**dict(c,timestamp=c.get('timestamp','2026-01-02T00:00:00Z'))) for c in cases])
        self.assertEqual(self.read()[2]['pad'],PadSize.MEDIUM)

    def test_newest_concrete_event_wins_without_event_preference(self):
        self.write([event(timestamp='2026-01-03T00:00:00Z'),event(timestamp='2026-01-02T00:00:00Z',LandingPads=dict(Small=0,Medium=0,Large=1))])
        self.assertEqual(self.read()[2]['pad'],PadSize.MEDIUM)
        self.write([event(event='DockingRequested',timestamp='2026-01-04T00:00:00Z',LandingPads=dict(Small=0,Medium=0,Large=1))],mode='a')
        self.assertEqual(self.read()[2]['pad'],PadSize.LARGE)

    def test_multiple_files_and_replacement_reveal_older_evidence(self):
        self.write([event()]);second=self.folder/'Journal.02.log'
        self.write([event(timestamp='2026-01-02T00:00:00Z',LandingPads=dict(Small=1,Medium=0,Large=0))],second)
        self.assertEqual(self.read()[2]['pad'],PadSize.SMALL)
        replacement=self.root/'replacement'; replacement.write_text('')
        os.replace(replacement,second)
        self.assertEqual(self.read()[2]['pad'],PadSize.MEDIUM)
        self.path.unlink();self.assertEqual(self.read(),{})

    def test_growth_reads_bounded_checks_and_delta_only(self):
        self.write([dict(event='Noise',value='x'*1000)]*1000+[event()]);self.read()
        old=self.path.stat().st_size
        self.write([event(timestamp='2026-01-02T00:00:00Z')],mode='a')
        stats={};self.read(stats=stats)
        self.assertLessEqual(stats['journal_bytes'],self.path.stat().st_size-old+16384)
        self.assertEqual(stats['processed_files'],1)

    def test_historical_addition_only_reads_new_file(self):
        self.write([event()]);self.read()
        self.write([event(MarketID=4)],self.folder/'Journal.00.log')
        stats={};self.assertEqual(set(self.read(stats=stats)),{2,4})
        self.assertEqual(stats['processed_files'],1)

    def test_truncation_and_same_size_rewrite(self):
        self.write([event()]);self.read()
        self.write([event(MarketID=4)])
        os.utime(self.path,ns=(1,1))
        self.assertEqual(set(self.read()),{4})
        self.path.write_text('');self.assertEqual(self.read(),{})

    def test_longer_same_inode_replacement_fails_append_probe(self):
        self.write([event()]);self.read()
        self.write([event(MarketID=4),dict(event='Noise')])
        self.assertEqual(set(self.read()),{4})

    def test_partial_line_resumes_after_newline(self):
        self.write([event()]);offset=self.path.stat().st_size
        tail=json.dumps(event(MarketID=4))
        with self.path.open('a') as f:f.write(tail)
        self.assertEqual(set(self.read()),{2});self.assertEqual(self.checkpoint(),offset)
        with self.path.open('a') as f:f.write('\n')
        self.assertEqual(set(self.read()),{2,4});self.assertEqual(self.checkpoint(),self.path.stat().st_size)

    def test_cancellation_preserves_committed_files(self):
        self.write([event()]);self.write([event(MarketID=4)],self.folder/'Journal.02.log')
        from cmdrhelper.station_pad_store import _process
        cancel=Event()
        def process(*args):
            result=_process(*args);cancel.set();return result
        with patch('cmdrhelper.station_pad_store._process',side_effect=process):
            with self.assertRaises(TradeReadCancelled):self.read(cancel=cancel)
        stats={};self.assertEqual(set(self.read(stats=stats)),{2,4});self.assertEqual(stats['processed_files'],1)

    def test_cancel_at_commit_rolls_back_evidence_and_offset(self):
        self.write([event()]);self.read();offset=self.checkpoint()
        self.write([event(MarketID=4)],mode='a')
        from cmdrhelper import station_pad_store as store
        original=store.check_cancel
        # The second check after parsing occurs inside the commit transaction.
        calls=0
        def cancel(check):
            nonlocal calls
            calls+=1
            if calls==5:raise TradeReadCancelled()
            return original(check)
        with patch.object(store,'check_cancel',side_effect=cancel):
            with self.assertRaises(TradeReadCancelled):self.read()
        self.assertEqual(self.checkpoint(),offset)
        self.assertEqual(set(self.read()),{2,4})

    def test_new_process_reads_zero_historical_bytes(self):
        self.write([event()]);self.read()
        code='''from pathlib import Path
from cmdrhelper.station_pad_store import read_local
import sys,json
original=Path.open
def guarded(p,*a,**k):
    if p.suffix=='.log':raise AssertionError('historical content reopened')
    return original(p,*a,**k)
Path.open=guarded
stats={}; rows=read_local(sys.argv[1],sys.argv[2],stats=stats)
print(json.dumps([len(rows),stats['journal_bytes'],stats['processed_files']]))
'''
        out=subprocess.check_output([sys.executable,'-B','-c',code,str(self.db),str(self.folder)],text=True)
        self.assertEqual(json.loads(out),[1,0,0])

    def test_import_errors_do_not_fall_back_or_advance(self):
        self.write([event()]);self.read();offset=self.checkpoint()
        self.write([event(MarketID=4)],mode='a')
        with patch.object(Path,'open',side_effect=OSError('injected read failure')):
            with self.assertRaises(OSError):PadMetadata(self.db).read(self.folder)
        self.assertEqual(self.checkpoint(),offset)
        self.assertEqual(set(self.read()),{2,4})

    def test_existing_import_progress_is_untouched(self):
        with sqlite3.connect(self.db) as con:
            con.execute("INSERT INTO journal_sessions(journal_file,attribution_status,last_read_offset) VALUES(?,'unknown',17)",(str(self.path),))
        self.write([event()]);self.read()
        with sqlite3.connect(self.db) as con:
            self.assertEqual(con.execute('SELECT last_read_offset FROM journal_sessions').fetchone()[0],17)

    def test_zero_counts_override_spansh(self):
        self.write([event(LandingPads=dict(Small=0,Medium=0,Large=0))])
        folder=self.root/'spansh';folder.mkdir()
        (folder/'3.json').write_text(json.dumps(dict(schema_version=1,source='spansh',system_address=3,
            system_name='System',fetched_at='2026-01-02T00:00:00Z',stations=[dict(market_id=2,station_name='Port',
            landing_pads=dict(small=1,medium=1,large=1))])))
        row=PadMetadata(self.db).read(self.folder,folder)[2]
        self.assertEqual(row['source'],'journal');self.assertIsNone(row['pad'])

    def test_equal_time_tiebreak_matches_previous_resolver(self):
        self.write([event(), event(LandingPads=dict(Small=1,Medium=0,Large=0))])
        self.write([event(LandingPads=dict(Small=0,Medium=0,Large=1))],self.folder/'Journal.02.log')
        self.assertEqual(self.read()[2]['pad'],PadSize.SMALL)

    def test_concurrent_file_growth_does_not_confirm_snapshot(self):
        self.write([event()]);self.read();offset=self.checkpoint()
        self.write([event(MarketID=4)],mode='a')
        from cmdrhelper.station_pad_store import _fingerprints
        def fingerprints(*args):
            result=_fingerprints(*args)
            self.write([dict(event='Noise')],mode='a')
            return result
        with patch('cmdrhelper.station_pad_store._fingerprints',side_effect=fingerprints):
            with self.assertRaises(OSError):self.read()
        self.assertEqual(self.checkpoint(),offset)
        self.assertEqual(set(self.read()),{2,4})

    def test_unavailable_folder_does_not_delete_evidence(self):
        self.write([event()]);self.read()
        with patch('cmdrhelper.station_pad_store.os.scandir',side_effect=PermissionError('unavailable')):
            with self.assertRaises(PermissionError):self.read()
        with sqlite3.connect(self.db) as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM station_pad_evidence').fetchone()[0],1)

    def test_malformed_line_invalidates_inherited_context(self):
        self.write([dict(event='Location',StarSystem='System',SystemAddress=3)])
        with self.path.open('a') as f:f.write('{invalid}\n')
        e=event(event='DockingRequested');del e['StarSystem'];del e['SystemAddress']
        self.write([e],mode='a')
        stats={};self.assertEqual(self.read(stats=stats),{})
        self.assertEqual(stats['invalid_lines'],1)

    def test_parser_revision_rebuilds_affected_files(self):
        self.write([event()]);self.read()
        with sqlite3.connect(self.db) as con:con.execute('UPDATE station_pad_journals SET parser_version=0')
        stats={};self.read(stats=stats);self.assertEqual(stats['processed_files'],1)


if __name__ == '__main__': unittest.main()
