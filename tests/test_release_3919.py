"""v3.9.19 metadata contract shared by packaging, GitHub and the updater."""
import json
from pathlib import Path
import re
import unittest

from cmdrhelper import __version__
from cmdrhelper.database import SCHEMA_VERSION
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language
from cmdrhelper.release_summaries import RELEASE_SUMMARIES, release_summary
from cmdrhelper.update import is_newer_version
from tools.publish_release import release_notes, version_at

ROOT = Path(__file__).resolve().parents[1]


class Release3919Tests(unittest.TestCase):
    def test_version_schema_and_upgrade(self):
        self.assertEqual(__version__, '3.9.19')
        self.assertEqual(version_at(ROOT), __version__)
        self.assertEqual(SCHEMA_VERSION, 23)
        self.assertTrue(is_newer_version(__version__, '3.9.18'))
        self.assertFalse(is_newer_version('3.9.18', __version__))

    def test_twelve_readmes_publisher_and_updater_agree(self):
        self.addCleanup(set_language, get_language())
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
                self.assertTrue(all(expected))
                self.assertEqual(metadata[language], expected)
                set_language(language)
                self.assertEqual(release_summary(__version__), expected)
                self.assertEqual(release_summary(__version__, notes), expected)
                path = ROOT / ('README.md' if language == 'en' else f'README_{language.upper()}.md')
                readme = path.read_text()
                self.assertEqual(readme.count('## CMDRHelper v3.9.19\n'), 1)
                section = readme.split('## CMDRHelper v3.9.19\n', 1)[1].split('\n## ', 1)[0]
                self.assertEqual([line[2:] for line in section.splitlines() if line.startswith('- ')], expected)
                self.assertIn('## CMDRHelper v3.9.18\n', readme)

    def test_release_notes_include_limits(self):
        notes = (ROOT / 'docs/release-3.9.19.md').read_text()
        self.assertEqual([line[2:] for line in notes.splitlines() if line.startswith('- ')],
                         [_TRANSLATIONS['de'][key] for key in RELEASE_SUMMARIES[__version__]])
        for phrase in ('MarketSell', '49.595 Cr/t', '551.650 Cr/t', 'System unbekannt',
                       'Version 23', 'Qt offscreen', 'keine native Windows-Prüfung',
                       'null Preisworker', 'keine zusätzliche SQL-Tagesabfrage',
                       'Live-Journalereignis-Korrektur ist nicht enthalten'):
            self.assertIn(phrase, notes)
        self.assertNotRegex(notes, r'/home/|/tmp/|Journal\.\d|F\d{8}')
