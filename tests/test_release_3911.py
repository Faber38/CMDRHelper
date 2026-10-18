"""Local v3.9.11 metadata checks; no publication or network."""
import json
from pathlib import Path
import re
import unittest
from cmdrhelper import __version__
from cmdrhelper.database import SCHEMA_VERSION
from cmdrhelper.i18n import _TRANSLATIONS
from cmdrhelper.release_summaries import RELEASE_SUMMARIES, release_summary
from cmdrhelper.update import is_newer_version
from tools.publish_release import release_notes, version_at

ROOT = Path(__file__).resolve().parents[1]


class Release3911Tests(unittest.TestCase):
    def test_version_schema_and_upgrade_order(self):
        self.assertEqual(__version__, '3.9.11')
        self.assertEqual(version_at(ROOT), __version__)
        self.assertEqual(SCHEMA_VERSION, 23)
        self.assertTrue(is_newer_version('3.9.11', '3.9.10'))
        self.assertFalse(is_newer_version('3.9.10', '3.9.11'))

    def test_four_localized_highlights_match_readmes_and_publisher(self):
        notes = release_notes(ROOT, __version__)
        metadata = json.loads(re.search(r'<!-- cmdrhelper-update-summary\s+(.*?)-->', notes, re.S)[1])
        keys = RELEASE_SUMMARIES[__version__]
        self.assertEqual(len(keys), 4)
        self.assertEqual(set(metadata), set(_TRANSLATIONS))
        for language, translations in _TRANSLATIONS.items():
            expected = [translations[key] for key in keys]
            self.assertEqual(metadata[language], expected)
            self.assertTrue(all(expected))
            name = 'README.md' if language == 'en' else f'README_{language.upper()}.md'
            section = (ROOT/name).read_text().split('## CMDRHelper v3.9.11\n', 1)[1].split('\n## ', 1)[0]
            self.assertEqual([line[2:] for line in section.splitlines() if line.startswith('- ')], expected)
        self.assertEqual(len(release_summary('3.9.11')), 4)
        self.assertNotIn('DB-UPDATE:', notes)

    def test_notes_preserve_validation_limits(self):
        text = (ROOT/'docs/release-3.9.11.md').read_text()
        self.assertIn('native Windows-Bestätigung', text)
        self.assertIn('steht aus', text)
        self.assertIn('KDE X11/KWin', text)
        self.assertIn('Version 23', text)
        expected = [_TRANSLATIONS['de'][key] for key in RELEASE_SUMMARIES[__version__]]
        self.assertEqual([line[2:] for line in text.splitlines() if line.startswith('- ')], expected)
