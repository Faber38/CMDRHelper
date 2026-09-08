"""Cross-language checks for the documentation-only v3.1 update."""
import ast
import re
import unittest
from pathlib import Path

from cmdrhelper.help_content import HELP_LANGUAGES, help_topic
from cmdrhelper.i18n import _TRANSLATIONS
from cmdrhelper.version import __version__

ROOT = Path(__file__).resolve().parents[1]


def readme(language):
    name = 'README.md' if language == 'en' else f'README_{language.upper()}.md'
    return (ROOT / name).read_text(encoding='utf-8')


class DocumentationReleaseTests(unittest.TestCase):
    def test_package_version_and_readme_release_headings_agree(self):
        tree = ast.parse((ROOT / 'cmdrhelper/__init__.py').read_text())
        package_version = next(ast.literal_eval(n.value) for n in tree.body
                               if isinstance(n, ast.Assign)
                               and any(getattr(t, 'id', '') == '__version__' for t in n.targets))
        self.assertEqual(package_version, __version__)
        for language in HELP_LANGUAGES:
            with self.subTest(language=language):
                heading = readme(language).split('\n## ')[1].splitlines()[0]
                self.assertIn(f'v{__version__}', heading)
                self.assertIn('v3.0.3', heading)

    def test_readme_heading_structure_and_code_examples_match(self):
        master = readme('de')
        headings = lambda s: re.findall(r'^(#{1,6}) ', s, re.MULTILINE)
        fences = lambda s: re.findall(r'^```[^\n]*\n(.*?)^```', s, re.MULTILINE | re.DOTALL)
        for language in HELP_LANGUAGES:
            with self.subTest(language=language):
                text = readme(language)
                self.assertEqual(headings(text), headings(master))
                self.assertEqual(fences(text), fences(master))
                self.assertEqual(len(text.split('\n## ')[1].split('\n- ')) - 1, 7)

    def test_new_controls_and_statuses_use_localized_ui_names(self):
        keys = ('settings.auto_show', 'settings.edsm_system_status', 'settings.cargo_hud',
                'edsm_status.known', 'edsm_status.unknown', 'edsm_status.no_response',
                'explorer.scan_done', 'body_detail.already_discovered', 'body_detail.already_mapped')
        for language in HELP_LANGUAGES:
            combined = '\n'.join(help_topic(t, language).text
                                 for t in ('overview', 'explorer', 'settings'))
            for key in keys:
                with self.subTest(language=language, key=key):
                    self.assertIn(_TRANSLATIONS[language][key], combined)
                    self.assertIn(_TRANSLATIONS[language][key], readme(language))

    def test_all_help_languages_preserve_historical_flags_and_visit_examples(self):
        for language in HELP_LANGUAGES:
            with self.subTest(language=language):
                explorer = help_topic('explorer', language).text
                for literal in ('WasDiscovered=false', 'WasMapped=false', '★', '◉', '◎', '◉✓',
                                '1/3', '2/3', '3/3', 'DSS', 'BIO / GEO / ABBAU'):
                    self.assertIn(literal, explorer)
                for literal in ('Location', 'FSDJump', 'CarrierJump', 'A → A → A', 'A → B → C → A'):
                    self.assertIn(literal, help_topic('overview', language).text)
                    self.assertIn(literal, readme(language))
                self.assertIn('HTTP', help_topic('settings', language).text)

    def test_manual_backfill_docs_link_to_automatic_start_repairs(self):
        for filename, feature in (('biology-persistence.md', 'biology_findings'),
                                  ('system-visits.md', 'system_visits')):
            with self.subTest(filename=filename):
                text = (ROOT / 'docs' / filename).read_text(encoding='utf-8')
                self.assertIn('[startup-repairs.md](startup-repairs.md)', text)
                self.assertIn(f'`{feature}`', text)
        self.assertNotIn('keine automatische Anwendung beim Programmstart',
                         (ROOT / 'docs/system-visits.md').read_text(encoding='utf-8'))
        self.assertNotIn('kein automatischer Startimport',
                         (ROOT / 'docs/biology-persistence.md').read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
