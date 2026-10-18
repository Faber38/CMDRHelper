"""Release metadata and the existing updater's transition from four-component versions."""
import io
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

from cmdrhelper import __version__
from cmdrhelper.database import SCHEMA_VERSION
from cmdrhelper.i18n import _TRANSLATIONS
from cmdrhelper.release_summaries import RELEASE_SUMMARIES
from cmdrhelper import update
from tools.publish_release import release_notes, version_at

ROOT = Path(__file__).resolve().parents[1]


class Release3910Tests(unittest.TestCase):
    def test_publisher_metadata_and_readmes_in_all_languages(self):
        self.assertEqual(version_at(ROOT), __version__)
        self.assertFalse(update.is_newer_version('3.9.10', __version__))
        self.assertEqual(SCHEMA_VERSION, 23)
        notes = release_notes(ROOT, '3.9.10')
        from cmdrhelper.ui.main_window import MainWindow
        self.assertFalse(MainWindow._release_requires_database_update({'release_notes': notes}))
        self.assertNotIn('DB-UPDATE:', notes)
        metadata = json.loads(re.search(
            r'<!-- cmdrhelper-update-summary\s+(.*?)-->', notes, re.S)[1])
        self.assertEqual(set(metadata), set(_TRANSLATIONS))
        self.assertEqual(len(metadata), 12)
        keys = RELEASE_SUMMARIES['3.9.10']
        self.assertEqual(len(keys), 6)
        for language, translations in _TRANSLATIONS.items():
            with self.subTest(language=language):
                expected = [translations[key] for key in keys]
                self.assertEqual(metadata[language], expected)
                self.assertTrue(all(expected))
                if language != 'en':
                    self.assertTrue(all(a != b for a, b in zip(expected, metadata['en'])))
                path = ROOT / ('README.md' if language == 'en' else
                               f'README_{language.upper()}.md')
                section = path.read_text().split('## CMDRHelper v3.9.10\n', 1)[1].split('\n## ', 1)[0]
                self.assertEqual([line[2:] for line in section.splitlines()
                                  if line.startswith('- ')], expected)
        document = (ROOT / 'docs/release-3.9.10.md').read_text()
        self.assertEqual([line[2:] for line in document.splitlines()
                          if line.startswith('- ')], metadata['de'])

    def test_version_order_from_actual_previous_release(self):
        for old in ('3.9.5', '3.9.6', '3.9.6.0', '3.9.6.4', '3.9.6.5', '3.9.6.6', '3.9.6.7', '3.9.8', '3.9.9'):
            self.assertTrue(update.is_newer_version('v3.9.10', old))
            self.assertFalse(update.is_newer_version(old, '3.9.10'))
        for same in ('3.9.10', 'v3.9.10', '3.9.10.0'):
            self.assertFalse(update.is_newer_version(same, '3.9.10'))
        self.assertTrue(update.is_newer_version('3.9.10', '3.9.9'))

    def test_latest_api_asset_and_notes_for_existing_installations(self):
        notes = release_notes(ROOT, '3.9.10')
        payload = dict(tag_name='v3.9.10', draft=False, prerelease=False,
                       body=notes, assets=[dict(name='CMDRHelper_v3.9.10.zip',
                       browser_download_url='https://example.invalid/release.zip', size=123)])
        for current in ('3.9.5', '3.9.6', '3.9.6.5', '3.9.6.6', '3.9.6.7', '3.9.8', '3.9.9', '3.9.10'):
            with self.subTest(current=current), patch.object(update.urllib.request, 'urlopen',
                    return_value=io.BytesIO(json.dumps(payload).encode())):
                result = update.check_latest_release(current_version=current)
                self.assertTrue(result['ok'])
                self.assertEqual(result['newer'], current != '3.9.10')
                self.assertFalse(result['draft'])
                self.assertFalse(result['prerelease'])
                self.assertEqual(result['asset_name'], 'CMDRHelper_v3.9.10.zip')
                self.assertEqual(result['release_notes'], notes)
