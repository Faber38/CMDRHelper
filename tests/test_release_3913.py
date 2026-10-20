"""Local v3.9.13 release consistency; no publication or network."""
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


class Release3913Tests(unittest.TestCase):
    def test_version_schema_and_upgrade_order(self):
        self.assertEqual(__version__, '3.9.13')
        self.assertEqual(version_at(ROOT), __version__)
        self.assertEqual(SCHEMA_VERSION, 23)
        self.assertTrue(is_newer_version('3.9.13', '3.9.12'))
        self.assertFalse(is_newer_version('3.9.12', '3.9.13'))

    def test_localized_highlights_match_readmes_and_publisher(self):
        notes = release_notes(ROOT, __version__)
        metadata = json.loads(re.search(
            r'<!-- cmdrhelper-update-summary\s+(.*?)-->', notes, re.S)[1])
        keys = RELEASE_SUMMARIES[__version__]
        self.assertEqual(len(keys), 6)
        self.assertEqual(set(metadata), set(_TRANSLATIONS))
        self.assertEqual(len(metadata), 12)
        for language, translations in _TRANSLATIONS.items():
            with self.subTest(language=language):
                expected = [translations[key] for key in keys]
                self.assertEqual(metadata[language], expected)
                self.assertTrue(all(expected))
                name = 'README.md' if language == 'en' else f'README_{language.upper()}.md'
                readme = (ROOT / name).read_text()
                self.assertEqual(readme.count('## CMDRHelper v3.9.13\n'), 1)
                section = readme.split('## CMDRHelper v3.9.13\n', 1)[1].split('\n## ', 1)[0]
                self.assertEqual([line[2:] for line in section.splitlines()
                                  if line.startswith('- ')], expected)
                self.assertIn('## CMDRHelper v3.9.12\n', readme)
        self.assertEqual(len(release_summary('3.9.13')), 6)
        self.assertNotIn('DB-UPDATE:', notes)

    def test_notes_preserve_accuracy_and_validation_limits(self):
        text = (ROOT / 'docs/release-3.9.13.md').read_text()
        for phrase in ('Version 23', 'Näherung', 'keine exakte oder bestätigte Frontier-Berechnung',
                       'Konflikt-CP-Umrechnung ist nicht implementiert',
                       'Qt offscreen', 'KDE X11/KWin und Windows steht aus'):
            self.assertIn(phrase, text)
        expected = [_TRANSLATIONS['de'][key] for key in RELEASE_SUMMARIES[__version__]]
        self.assertEqual([line[2:] for line in text.splitlines()
                          if line.startswith('- ')], expected)
