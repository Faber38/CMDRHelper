import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from PySide6.QtCore import QSettings
from cmdrhelper.journal_sources import SourceRegistry, discover, KEY


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.settings = QSettings(str(self.root/'settings.ini'), QSettings.IniFormat)

    def test_legacy_restart_preserves_path_and_id(self):
        path = self.root/'missing'
        self.settings.setValue('journal_folder', str(path))
        first = SourceRegistry(self.settings)
        second = SourceRegistry(self.settings)
        self.assertEqual(first.sources[0].config(), second.sources[0].config())
        self.assertEqual(second.sources[0].path, str(path))
        self.assertEqual(self.settings.value('journal_folder'), str(path))

    def test_alias_activation_removal_and_edit(self):
        folder = self.root/'journal'; folder.mkdir()
        alias = self.root/'alias'; alias.symlink_to(folder, target_is_directory=True)
        registry = SourceRegistry(self.settings)
        source = registry.add(folder)
        self.assertIs(registry.add(alias), source)
        identity = source.id
        registry.update(identity, enabled=False, name='Test')
        self.assertEqual(registry.enabled(), [])
        registry.update(identity, enabled=True, path=alias)
        self.assertEqual(source.path, str(folder))
        registry.remove(identity)
        self.assertTrue(folder.exists())
        self.assertEqual(SourceRegistry(self.settings).sources, [])

    def test_heroic_pfx_alias_and_missing_journals(self):
        prefix = self.root/'Games/Heroic/Prefixes/default/Test Game'
        folder = prefix/'drive_c/users/other/Saved Games/Frontier Developments/Elite Dangerous'
        folder.mkdir(parents=True)
        (prefix/'pfx').symlink_to('.', target_is_directory=True)
        with patch('cmdrhelper.journal_reader.default_journal_paths', return_value=[]):
            self.assertEqual(discover(self.root), [])
            (folder/'Journal.2026-10-18T120000.01.log').write_text('{"event":"Fileheader"}\n')
            self.assertEqual(discover(self.root), [(str(folder), 'Heroic / Epic')])

    def test_invalid_config_does_not_silently_reset(self):
        self.settings.setValue(KEY, '{invalid')
        with self.assertRaises(ValueError):
            SourceRegistry(self.settings)
        self.assertEqual(self.settings.value(KEY), '{invalid')

    def test_discovery_does_not_reenable_existing_source(self):
        registry = SourceRegistry(self.settings, [(str(self.root), 'Steam')])
        registry.update(registry.sources[0].id, enabled=False)
        registry.merge([(str(self.root), 'Steam')])
        self.assertFalse(registry.sources[0].enabled)
