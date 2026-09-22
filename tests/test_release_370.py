"""Release-candidate metadata stays tied to the single product version."""
import ast
from pathlib import Path
import re
import unittest
import cmdrhelper
from cmdrhelper.version import __version__
from cmdrhelper.i18n import _TRANSLATIONS
from cmdrhelper.release_summaries import RELEASE_SUMMARIES
from tools.publish_release import version_at, release_notes

ROOT = Path(__file__).resolve().parents[1]


class Release370Tests(unittest.TestCase):
    def test_active_version_and_single_source(self):
        self.assertEqual(__version__, '3.7.0')
        self.assertEqual(cmdrhelper.__version__, __version__)
        self.assertEqual(version_at(ROOT), __version__)
        sources = []
        for path in (ROOT / 'cmdrhelper').rglob('*.py'):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '__version__' for t in node.targets):
                    sources.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(sources, ['cmdrhelper/version.py'])
        self.assertIn('VERSION_FILE="cmdrhelper/version.py"', (ROOT / 'create_release.sh').read_text())

    def test_release_summary_and_readmes_preserve_history(self):
        keys = RELEASE_SUMMARIES['3.7.0']
        self.assertEqual(len(set(keys)), 6)
        notes = release_notes(ROOT, '3.7.0')
        self.assertIn('cmdrhelper-update-summary', notes)
        for lang, table in _TRANSLATIONS.items():
            name = 'README.md' if lang == 'en' else 'README_' + lang.upper() + '.md'
            readme = (ROOT / name).read_text()
            headings = re.findall(r'^## .*$', readme, re.M)
            self.assertIn('3.7.0', headings[1])
            self.assertTrue(any('3.6.2' in h for h in headings[2:]))
            for key in keys:
                self.assertTrue(table[key].strip())
                self.assertIn(table[key], readme)
                self.assertIn(table[key], notes)
        self.assertTrue((ROOT / 'docs/release-3.7.0.md').is_file())
