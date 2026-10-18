import tempfile
import unittest
from pathlib import Path
from PySide6.QtCore import QSettings
from cmdrhelper.edsm_uploader import EDSMJournalUploader
from test_import_catchup import event, append


class SourceUploadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.settings = QSettings(str(self.root/'test.ini'), QSettings.IniFormat)
        self.paths = []
        for name in ('a', 'b'):
            folder = self.root/name; folder.mkdir()
            path = folder/'Journal.2026-09-14T120000.01.log'
            append(path, event('Commander', FID='SAME-FID', Name='Same'))
            self.paths.append(path)

    def uploader(self, sid, folders=None):
        return EDSMJournalUploader('Same', 'synthetic', settings=self.settings, fid='SAME-FID',
            source_id=sid, legacy_folder=self.paths[0].parent,
            source_folders=folders or [p.parent for p in self.paths])

    def test_identical_names_and_fid_have_independent_positions(self):
        a, b = self.uploader('a'), self.uploader('b')
        a._set_position(self.paths[0], 12)
        self.assertEqual(b._stored_position(self.paths[1]), 0)
        self.assertNotEqual(a._position_key(self.paths[0]), a._position_key(self.paths[1]))

    def test_new_source_baselines_without_network(self):
        uploader = self.uploader('b')
        result = uploader.process_folder(self.paths[1].parent)
        self.assertTrue(result['initialized'])
        self.assertEqual(uploader._stored_position(self.paths[1]), self.paths[1].stat().st_size)

    def test_unique_legacy_position_preserved(self):
        key = 'edsm_upload/commanders/SAME-FID/positions/'+self.paths[0].name
        self.settings.setValue(key, 12)
        uploader = self.uploader('a', [self.paths[0].parent])
        uploader.process_folder(self.paths[0].parent)
        self.assertEqual(uploader._stored_position(self.paths[0]), 12)
        self.assertEqual(int(self.settings.value(key)), 12)

    def test_ambiguous_legacy_position_is_not_guessed_or_reset(self):
        key = 'edsm_upload/commanders/SAME-FID/positions/'+self.paths[0].name
        self.settings.setValue(key, 12)
        uploader = self.uploader('b')
        with self.assertRaisesRegex(ValueError, 'ambiguous'):
            uploader.process_folder(self.paths[1].parent)
        self.assertEqual(int(self.settings.value(key)), 12)
        self.assertEqual(uploader._stored_position(self.paths[1]), 0)

    def test_readding_source_preserves_pending_position(self):
        old = self.uploader('removed-source')
        old._set_position(self.paths[0], 12)
        added = self.uploader('new-source')
        added.process_folder(self.paths[0].parent)
        self.assertEqual(added._stored_position(self.paths[0]), 12)

    def test_unique_automatically_detected_legacy_source_needs_no_manual_path(self):
        key = 'edsm_upload/commanders/SAME-FID/positions/'+self.paths[0].name
        self.settings.setValue(key, 12)
        uploader = self.uploader('automatic', [self.paths[0].parent])
        uploader.legacy_folder = None
        uploader.process_folder(self.paths[0].parent)
        self.assertEqual(uploader._stored_position(self.paths[0]), 12)
