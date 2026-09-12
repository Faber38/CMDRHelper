"""Release 3.4 metadata, translations and current documentation stay aligned."""
import re
from pathlib import Path
import unittest

import cmdrhelper
from cmdrhelper.help_content import HELP_LANGUAGES, help_topic
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language
from cmdrhelper.release_summaries import RELEASE_SUMMARIES, release_summary
from cmdrhelper.version import __version__
from tools.check_i18n import load_translation_file, placeholders
from tools.publish_release import release_notes, version_at

ROOT = Path(__file__).resolve().parents[1]


class Release34Tests(unittest.TestCase):
    def setUp(self):
        self.addCleanup(set_language, get_language())

    def test_central_version_and_publisher_agree(self):
        self.assertEqual(__version__, '3.4')
        self.assertEqual(cmdrhelper.__version__, __version__)
        self.assertEqual(version_at(ROOT), __version__)

    def test_six_localized_highlights_and_generated_update_metadata(self):
        keys = RELEASE_SUMMARIES['3.4']
        self.assertEqual(len(set(keys)), 6)
        self.assertTrue(all(key.startswith('release.3_4.') for key in keys))
        notes = release_notes(ROOT, '3.4')
        self.assertIn('## Neu in Version 3.4', notes)
        self.assertNotIn('3.3.1', notes)
        self.assertNotRegex(notes, r'Bestpreis|Handelsroutenfinder|TTS|Chat-Monitor')
        for language in HELP_LANGUAGES:
            with self.subTest(language=language):
                table, duplicates = load_translation_file(ROOT / 'cmdrhelper/i18n' / (language + '.py'))
                self.assertFalse(duplicates)
                set_language(language)
                expected = [table[key] for key in keys]
                self.assertTrue(all(value.strip() for value in expected))
                self.assertEqual(release_summary('v3.4'), expected)
                self.assertEqual(release_summary('3.4', notes), expected)
                for key in keys:
                    self.assertEqual(placeholders(table[key]),
                                     placeholders(_TRANSLATIONS['en'][key]))
                    if language != 'en':
                        self.assertNotEqual(table[key], _TRANSLATIONS['en'][key])

    def test_readmes_include_34_before_unchanged_older_history_and_help_has_no_version(self):
        for language in HELP_LANGUAGES:
            name = 'README.md' if language == 'en' else 'README_' + language.upper() + '.md'
            text = (ROOT / name).read_text(encoding='utf-8')
            section = re.split(r'^## ', text, flags=re.MULTILINE)[1]
            with self.subTest(language=language):
                self.assertIn('3.4', section.splitlines()[0])
                for term in ('57', 'Surface', 'Asteroid', 'Both', 'CargoTransfer', '—', 'ABBAU ×N', 'A-6-a'):
                    self.assertIn(term, section)
                self.assertNotRegex(section, r'Bestpreis|Handelsroutenfinder|TTS|Chat-Monitor')
                self.assertIn('3.3.1', text[text.index(section) + len(section):])
                help_text = help_topic('materials', language).text
                self.assertIn('<h3>Mining</h3>', help_text)
                self.assertIn('<h3>CMDRHelper</h3>', help_text)
                self.assertNotRegex(help_text, r'CMDRHelper\s+v?\d+\.\d+')


if __name__ == '__main__':
    unittest.main()
