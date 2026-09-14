"""Local optimizations must preserve archive contents and cargo semantics."""
import json
import inspect
import ntpath
import tempfile
import unittest
from pathlib import Path, PureWindowsPath
from unittest.mock import patch

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.mining_inventory import MiningInventoryReader
from cmdrhelper.mining_carrier import read_carrier_feed


class P1PerformanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.path = self.folder / 'Journal.2026-09-14T120000.01.log'

    def write(self, events, mode='w'):
        with self.path.open(mode, encoding='utf-8') as stream:
            for e in events:
                stream.write(json.dumps(dict(timestamp='2026-09-14T12:00:00Z', **e))+'\n')

    def test_archive_groups_multiple_systems_and_keeps_body_counts_and_materials(self):
        events = [dict(event='Commander', FID='F1', Name='Test')]
        for address, count in ((10, 3), (20, 1), (30, 0)):
            events.append(dict(event='Location', StarSystem=f'S{address}', SystemAddress=address))
            for body in range(count):
                events.append(dict(event='Scan', SystemAddress=address, BodyID=body,
                                   BodyName=f'S{address} {body}', PlanetClass='Rocky body',
                                   Materials={'iron': 12.5}))
        self.write(events)
        db = CMDRDatabase(self.folder / 'state.db')
        db.import_journal_archive(self.folder)
        with db._connect() as con:
            self.assertEqual(con.execute('SELECT system_address,body_count FROM systems ORDER BY 1').fetchall(),
                             [(10,3),(20,1),(30,0)])
            self.assertEqual(con.execute('SELECT system_address,COUNT(*) FROM bodies GROUP BY 1').fetchall(),
                             [(10,3),(20,1)])
            self.assertEqual(con.execute('SELECT COUNT(*) FROM materials WHERE percentage=12.5').fetchone()[0],4)

    def test_marker_does_not_confirm_growth_after_eof(self):
        self.write([dict(event='Commander', FID='F1', Name='Test'),
                    dict(event='Location', StarSystem='A', SystemAddress=10)])
        db = CMDRDatabase(self.folder / 'state.db')
        size = self.path.stat().st_size
        original_open = Path.open
        appended = []
        target = self.path
        class AppendAfterEOF:
            def __init__(self, stream):
                self.stream = stream
            def __getattr__(self, name):
                return getattr(self.stream, name)
            def __iter__(self):
                return iter(self.stream)
            def __enter__(self):
                return self.stream
            def __exit__(self, *args):
                self.stream.close()
                # Precisely between the parser reaching EOF and the later stat
                # used for its import marker (the original race).
                with original_open(target, 'a', encoding='utf-8') as stream:
                    stream.write(json.dumps(dict(event='Location', StarSystem='B',
                                                 SystemAddress=20)) + '\n')
                appended.append(True)
        def open_file(path, *args, **kwargs):
            stream = original_open(path, *args, **kwargs)
            caller = inspect.currentframe().f_back.f_code.co_name
            if path == target and caller == 'import_journal_archive' and not appended:
                return AppendAfterEOF(stream)
            return stream
        with patch.object(Path, 'open', open_file):
            db.import_journal_archive(self.folder)
        self.assertEqual(appended, [True])
        with db._connect() as con:
            self.assertEqual(con.execute('SELECT file_size FROM journal_imports').fetchone()[0],size)
            self.assertEqual(con.execute('SELECT COUNT(*) FROM systems').fetchone()[0],1)
        result = db.import_journal_archive(self.folder)
        self.assertEqual(result['imported_journals'],1)
        with db._connect() as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM systems').fetchone()[0],2)
            self.assertEqual(con.execute('SELECT file_size FROM journal_imports').fetchone()[0],self.path.stat().st_size)

    def test_archive_partial_line_is_not_marked_imported(self):
        self.write([dict(event='Commander', FID='F1', Name='Test')])
        size = self.path.stat().st_size
        with self.path.open('ab') as stream:
            stream.write(b'{"event":"Location","StarSystem":"A","SystemAddress":10}')
        db = CMDRDatabase(self.folder / 'state.db')
        db.import_journal_archive(self.folder)
        with db._connect() as con:
            self.assertEqual(con.execute('SELECT file_size FROM journal_imports').fetchone()[0],size)
            self.assertEqual(con.execute('SELECT fully_imported FROM journal_sessions').fetchone()[0],0)
        with self.path.open('ab') as stream:
            stream.write(b'\n')
        db.import_journal_archive(self.folder)
        with db._connect() as con:
            self.assertEqual(con.execute('SELECT COUNT(*) FROM systems').fetchone()[0],1)

    def test_resolve_is_per_path_and_shared_feed_equals_separate_reader(self):
        self.write([dict(event='Commander', FID='F1', Name='Test'),
                    dict(event='LoadGame', FID='F1', Ship='CobraMkIII'),
                    dict(event='Cargo', Vessel='Ship', Count=0, Inventory=[])]
                   + [dict(event='MiningRefined', Type='gold') for _ in range(1000)])
        sessions = [dict(journal_file=str(self.path),commander_id=1,fid_seen='F1',attribution_status='identified')]
        reader = MiningInventoryReader()
        expected = reader.reconstruct(1,'F1',sessions,live_path=self.path)
        feed = read_carrier_feed(self.path,'F1')
        original_resolve, original_open = Path.resolve, Path.open
        resolves, opens = [], []
        def resolve(path, *args, **kw):
            resolves.append(path)
            return original_resolve(path,*args,**kw)
        def open_file(path,*args,**kw):
            opens.append(path)
            return original_open(path,*args,**kw)
        # Native pathlib normalization (including redundant components) is kept;
        # this test also runs with WindowsPath on Windows.
        live = str(self.folder) + '/./' + self.path.name
        with patch.object(Path,'resolve',resolve), patch.object(Path,'open',open_file):
            actual = reader.reconstruct(1,'F1',sessions,live_path=live,include_carrier_feed=True)
        self.assertEqual(len(resolves),2)
        self.assertEqual(opens.count(self.path),1)
        self.assertEqual(actual.ship,expected.ship)
        self.assertEqual(actual.srv,expected.srv)
        self.assertEqual(actual.checkpoints,expected.checkpoints)
        self.assertEqual(actual.carrier_feed,feed)

    def test_windows_drive_and_unc_comparisons_keep_path_semantics(self):
        # Exercise Windows' case-insensitive path equality on Linux as well.
        # The production resolver remains native pathlib; no string comparison
        # or platform-specific normalization was introduced by the optimization.
        class WindowsPathForTest(PureWindowsPath):
            def resolve(self):
                return WindowsPathForTest(ntpath.normpath(str(self)))
        facts = [(0, dict(event='LoadGame',FID='F1',Ship='CobraMkIII')),
                 (10,dict(event='Cargo',Vessel='Ship',Count=0,Inventory=[]))]
        for base in ('C:/Journals', '//server/share/Journals'):
            name = base + '/Journal.2026-09-14T120000.01.log'
            live = base.lower() + '/./Journal.2026-09-14T120000.01.log'
            with self.subTest(base=base):
                reader = MiningInventoryReader()
                sessions = [dict(journal_file=name,commander_id=1,fid_seen='F1',
                                 attribution_status='identified')]
                with patch('cmdrhelper.mining_inventory.Path', WindowsPathForTest), \
                     patch.object(reader, '_read', return_value=({'F1'}, facts)):
                    result = reader.reconstruct(1,'F1',sessions,live_path=live)
                self.assertTrue(result.snapshot_verified)
                self.assertEqual(result.ship,{})

    def test_invalid_live_event_cannot_be_used_as_carrier_feed(self):
        self.write([dict(event='Commander',FID='F1'),dict(event='Cargo',Vessel='Ship',Count=0,Inventory=[])])
        with self.path.open('ab') as stream:
            stream.write(b'not json\n')
        sessions=[dict(journal_file=str(self.path),commander_id=1,fid_seen='F1',attribution_status='identified')]
        result=MiningInventoryReader().reconstruct(1,'F1',sessions,live_path=self.path,include_carrier_feed=True)
        self.assertIsNone(result.carrier_feed)
        self.assertIsNone(result.ship)
