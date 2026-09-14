"""Release metadata and all user-visible migration strings in twelve languages."""
import re
import unittest
from pathlib import Path
from cmdrhelper.help_content import HELP_LANGUAGES, help_topic
from cmdrhelper.i18n import get_language, set_language
from cmdrhelper.release_summaries import release_summary
from tools.check_i18n import load_translation_file, placeholders
from tools.publish_release import release_notes

ROOT = Path(__file__).resolve().parents[1]


class Release341Tests(unittest.TestCase):
    def test_twelve_complete_catalogs_and_five_highlights(self):
        self.addCleanup(set_language, get_language())
        reference, _ = load_translation_file(ROOT / 'cmdrhelper/i18n/en.py')
        keys = {k for k in reference if k.startswith('migration.')}
        self.assertEqual(len(keys), 30)
        for language in HELP_LANGUAGES:
            with self.subTest(language=language):
                table, duplicates = load_translation_file(ROOT / f'cmdrhelper/i18n/{language}.py')
                self.assertFalse(duplicates)
                self.assertEqual({k for k in table if k.startswith('migration.')}, keys)
                for key in keys:
                    self.assertEqual(placeholders(table[key]), placeholders(reference[key]))
                    self.assertTrue(table[key].strip())
                    if language != 'en' and (language, key) != ('no', 'migration.launch'):
                        self.assertNotEqual(table[key], reference[key], key)
                set_language(language)
                self.assertEqual(release_summary('3.4.1'), [table[f'migration.release{i}'] for i in range(5)])
                self.assertEqual(release_summary('3.4.1', release_notes(ROOT, '3.4.1')),
                                 release_summary('3.4.1'))
                self.assertIn(table['migration.help'], help_topic('overview', language).text)
                self.assertNotRegex(help_topic('overview', language).text, r'CMDRHelper\s+v?\d+\.\d+')
                readme = ROOT / ('README.md' if language == 'en' else f'README_{language.upper()}.md')
                sections = re.split(r'^## ', readme.read_text(), flags=re.MULTILINE)[1:]
                first = next(section for section in sections
                             if re.search(r'\b3\.4\.1\b', section.splitlines()[0]))
                self.assertIn('3.4.1', first.splitlines()[0])
                for i in range(5):
                    self.assertIn(table[f'migration.release{i}'], first)


if __name__ == '__main__':
    unittest.main()
