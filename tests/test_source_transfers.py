import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from PySide6.QtCore import QSettings
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.source_processing import SourceProcessor
from cmdrhelper.source_transfers import transfer
from cmdrhelper.inara_uploader import InaraUploadError
from test_import_catchup import event, append


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.db = CMDRDatabase(self.root/'test.db')
        self.settings = QSettings(str(self.root/'test.ini'), QSettings.IniFormat)
        self.processors = []
        self.configs = {}
        for name in ('a', 'b'):
            folder = self.root/name; folder.mkdir()
            path = folder/'Journal.2026-09-14T120000.01.log'
            fid = 'F-'+name
            append(path, event('Commander', FID=fid, Name='Same'),
                   event('FSDJump', StarSystem=name, SystemAddress=1 if name == 'a' else 2))
            processor = SourceProcessor(self.db, folder)
            processor.process(enqueue_fids={fid})
            self.assertFalse(self.db.inara_pending(processor.sessions[0]['commander_id']))
            append(path, event('FSDJump', StarSystem='live-'+name, SystemAddress=11 if name == 'a' else 12))
            processor.process(enqueue_fids={fid})
            self.processors.append(processor)
            config = dict(commander='Same', api_key='synthetic-'+name, enabled=True)
            self.configs[fid] = ({}, config)
            self.settings.setValue('inara/commanders/'+fid+'/enabled', True)
            self.settings.setValue('inara/commanders/'+fid+'/api_key', config['api_key'])

    def run_transfer(self, index=0, current=lambda: True):
        processor = self.processors[index]
        return transfer(self.db, SimpleNamespace(id=str(index), path=str(processor.path)),
            processor.sessions, self.configs, self.settings, is_current=current,
            legacy_folder=None, source_folders=[p.path for p in self.processors])

    def test_inflight_selection_change_acknowledges_original_fid_only(self):
        a, b = [p.sessions[0]['commander_id'] for p in self.processors]
        self.assertTrue(self.db.inara_pending(a))
        self.assertTrue(self.db.inara_pending(b))
        active = [True]
        def uploaded(key, name, fid, rows):
            self.assertEqual(fid, 'F-a')
            self.assertEqual(key, 'synthetic-a')
            active[0] = False
            return [r['id'] for r in rows], {}
        with patch('cmdrhelper.source_transfers.upload_batch', side_effect=uploaded):
            self.run_transfer(current=lambda: active[0])
        self.assertFalse(self.db.inara_pending(a))
        self.assertTrue(self.db.inara_pending(b))

    def test_conflicting_source_and_disabled_credentials_never_send(self):
        processor = self.processors[0]
        path = next(processor.path.glob('Journal.*'))
        append(path, event('Commander', FID='foreign', Name='Same'))
        with patch('cmdrhelper.source_transfers.upload_batch') as send:
            self.run_transfer()
            send.assert_not_called()
        self.settings.setValue('inara/commanders/F-b/enabled', False)
        with patch('cmdrhelper.source_transfers.upload_batch') as send:
            self.run_transfer(1)
            send.assert_not_called()

    def test_rate_limit_remains_bound_and_persistent(self):
        cid = self.processors[0].sessions[0]['commander_id']
        with patch('cmdrhelper.source_transfers.upload_batch', side_effect=InaraUploadError('http_error', retry_seconds=3600)):
            self.run_transfer()
        self.assertFalse(self.db.inara_pending(cid))
        with self.db._connect() as con:
            row = con.execute('SELECT retry_count,last_error FROM inara_outbox WHERE commander_id=?', (cid,)).fetchone()
        self.assertEqual(row[0], 1)
        self.assertIn('inara_retry_not_before', row[1])
