"""Release text checks only: never build, commit, tag or publish."""
import ast
import json
from pathlib import Path
import re
import unittest

import cmdrhelper
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language
from cmdrhelper.release_summaries import RELEASE_SUMMARIES, release_summary
from cmdrhelper.version import __version__
from tools.check_i18n import load_translation_file, placeholders
from tools.publish_release import literal, release_notes, version_at

ROOT = Path(__file__).resolve().parents[1]
LANGUAGES = {'de', 'en', 'fr', 'it', 'no', 'sv', 'fi', 'pl', 'nl', 'es', 'tr', 'el'}


class Release382Tests(unittest.TestCase):
    def test_single_version_and_exact_five_summary_keys(self):
        self.assertEqual(__version__, '3.9.0')
        self.assertEqual(cmdrhelper.__version__, __version__)
        self.assertEqual(version_at(ROOT), __version__)
        self.assertEqual(RELEASE_SUMMARIES['3.8.2'],
                         tuple(f'release.3_8_2.{i}' for i in range(5)))
        tree = ast.parse((ROOT / 'cmdrhelper/release_summaries.py').read_text())
        assignment = next(n for n in tree.body if isinstance(n, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == 'RELEASE_SUMMARIES' for t in n.targets))
        names = [ast.literal_eval(key) for key in assignment.value.keys]
        self.assertEqual(len(names), len(set(names)))

    def test_twelve_literal_catalogs_and_runtime_summaries(self):
        self.addCleanup(set_language, get_language())
        self.assertEqual(set(_TRANSLATIONS), LANGUAGES)
        keys = RELEASE_SUMMARIES['3.8.2']
        reference, _ = load_translation_file(ROOT / 'cmdrhelper/i18n/en.py')
        for language in sorted(LANGUAGES):
            with self.subTest(language=language):
                path = ROOT / f'cmdrhelper/i18n/{language}.py'
                table, duplicates = load_translation_file(path)
                self.assertFalse(duplicates)
                self.assertEqual({k for k in table if k.startswith('release.3_8_2.')}, set(keys))
                # Exercise the exact AST reader used by publication, without running it.
                published = literal(path, 'TRANSLATIONS')
                expected = [table[key] for key in keys]
                self.assertEqual([published[key] for key in keys], expected)
                for key in keys:
                    self.assertTrue(table[key].strip())
                    self.assertEqual(placeholders(table[key]), placeholders(reference[key]))
                    self.assertEqual(table[key], _TRANSLATIONS[language][key])
                    if language != 'en':
                        self.assertNotEqual(table[key], reference[key])
                set_language(language)
                self.assertEqual(release_summary('3.8.2'), expected)
                self.assertEqual(release_summary('v3.8.2'), expected)

    def test_release_notes_update_metadata_and_readmes(self):
        self.addCleanup(set_language, get_language())
        notes = release_notes(ROOT, '3.8.2')
        block = re.search(r'<!--\s*cmdrhelper-update-summary\s+(.*?)-->', notes, re.S)
        self.assertIsNotNone(block)
        payload = json.loads(block.group(1))
        self.assertEqual(set(payload), LANGUAGES)
        keys = RELEASE_SUMMARIES['3.8.2']
        for language in sorted(LANGUAGES):
            expected = [_TRANSLATIONS[language][key] for key in keys]
            self.assertEqual(payload[language], expected)
            set_language(language)
            self.assertEqual(release_summary('3.8.2', notes), expected)
            name = 'README.md' if language == 'en' else f'README_{language.upper()}.md'
            text = (ROOT / name).read_text()
            section = text.split('## CMDRHelper v3.8.2\n', 1)[1].split('\n## ', 1)[0]
            self.assertEqual([s[2:] for s in section.splitlines() if s.startswith('- ')], expected)
            self.assertLess(text.index('## CMDRHelper v3.8.2'), text.index('## CMDRHelper v3.8.0'))
        document = (ROOT / 'docs/release-3.8.2.md').read_text()
        self.assertEqual(document.splitlines()[0], '# CMDRHelper v3.8.2')
        self.assertEqual([s[2:] for s in document.splitlines() if s.startswith('- ')],
                         [_TRANSLATIONS['de'][key] for key in keys])
