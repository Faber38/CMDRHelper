"""The 3.4.3 release contains only implemented, localized functionality."""
import re
import unittest
from pathlib import Path

import cmdrhelper
from cmdrhelper.version import __version__
from cmdrhelper.help_content import HELP_LANGUAGES, help_topic
from cmdrhelper.i18n import get_language, set_language
from cmdrhelper.release_summaries import RELEASE_SUMMARIES, release_summary
from tools.check_i18n import load_translation_file, placeholders
from tools.publish_release import release_notes, version_at

ROOT = Path(__file__).resolve().parents[1]


class Release343Tests(unittest.TestCase):
    def test_central_version_and_publisher(self):
        self.assertEqual(__version__, '3.4.3')
        self.assertEqual(cmdrhelper.__version__, __version__)
        self.assertEqual(version_at(ROOT), __version__)

    def test_localized_summary_readmes_and_versionless_help(self):
        self.addCleanup(set_language, get_language())
        keys=RELEASE_SUMMARIES['3.4.3']
        self.assertEqual(len(set(keys)),6)
        notes=release_notes(ROOT,'3.4.3')
        self.assertIn('## Neu in Version 3.4.3',notes)
        reference,_=load_translation_file(ROOT/'cmdrhelper/i18n/en.py')
        for lang in HELP_LANGUAGES:
            with self.subTest(lang=lang):
                table, duplicates=load_translation_file(ROOT/f'cmdrhelper/i18n/{lang}.py')
                self.assertFalse(duplicates)
                set_language(lang)
                expected=[table[key] for key in keys]
                self.assertEqual(release_summary('v3.4.3'),expected)
                self.assertEqual(release_summary('3.4.3',notes),expected)
                for key in keys:
                    self.assertEqual(placeholders(table[key]),placeholders(reference[key]))
                    if lang!='en':
                        self.assertNotEqual(table[key],reference[key])
                name='README.md' if lang=='en' else f'README_{lang.upper()}.md'
                text=(ROOT/name).read_text()
                sections=re.split(r'^## ',text,flags=re.M)[1:]
                current=next(s for s in sections if '3.4.3' in s.splitlines()[0])
                self.assertTrue(all(value in current for value in expected))
                self.assertIn('500',current)
                self.assertIn('favorites.json',current)
                self.assertLess(text.index('🚀'),text.index(current))
                old=next(s for s in sections if '3.4.1' in s.splitlines()[0])
                self.assertLess(text.index(current),text.index(old))
                for topic in ('explorer','materials','settings','overview'):
                    body=help_topic(topic,lang).text
                    headings=re.findall(r'<h[1-6][^>]*>(.*?)</h[1-6]>',body,re.S)
                    self.assertNotRegex(' '.join(headings),r'\b\d+\.\d+(?:\.\d+)?\b')
                for token in ('favorites.json','500'):
                    self.assertIn(token,help_topic('explorer',lang).text)
                self.assertIn('diagnose_summary.txt',help_topic('settings',lang).text)
                self.assertNotIn('3.4.1',table['migration.intro'])

    def test_release_documentation_preserves_migration_identity(self):
        from cmdrhelper.parent_migration import COMPLETE, BACKUP_KEY
        self.assertEqual(COMPLETE,'3.4.1-complete')
        self.assertEqual(BACKUP_KEY,'parent_hierarchy_backup.3.4.1')
        doc=(ROOT/'docs/release-3.4.3.md').read_text()
        for value in ('1.262','10.985','10.980','5.961','16.941','32 MiB','256 MiB','SRV | Schiff | Carrier | Gesamt'):
            self.assertIn(value,doc)
