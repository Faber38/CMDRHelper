"""Cross-language checks for the v3.2 release documentation."""
import cmdrhelper
import re
import ast
import json
import subprocess
import tempfile
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
        self.assertEqual(cmdrhelper.__version__, __version__)
        for language in HELP_LANGUAGES:
            with self.subTest(language=language):
                heading = readme(language).split('\n## ')[1].splitlines()[0]
                self.assertIn(f'v{__version__}', heading)
                self.assertEqual(__version__, '3.2')
                self.assertIn('v3.1', heading)
                self.assertNotIn('v3.0.3', heading)

    def test_readme_heading_structure_and_code_examples_match(self):
        master = readme('de')
        headings = lambda s: re.findall(r'^(#{1,6}) ', s, re.MULTILINE)
        fences = lambda s: re.findall(r'^```[^\n]*\n(.*?)^```', s, re.MULTILINE | re.DOTALL)
        for language in HELP_LANGUAGES:
            with self.subTest(language=language):
                text = readme(language)
                self.assertEqual(headings(text), headings(master))
                self.assertEqual(fences(text), fences(master))
                self.assertEqual(len(text.split('\n## ')[1].split('\n- ')) - 1, 8)

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

    def test_release_highlights_cover_the_eight_user_changes(self):
        for language in HELP_LANGUAGES:
            with self.subTest(language=language):
                section = readme(language).split('\n## ')[1]
                points = section.split('\n- ')[1:]
                self.assertEqual(len(points), 8)
                for token in ('146', 'Raw', 'Manufactured', 'Encoded'):
                    self.assertIn(token, points[0])
                for token in ('Odyssey', '223'):
                    self.assertIn(token, points[1])
                for token in ('Spansh', 'Raw', 'Manufactured', 'Encoded', 'ly', 'Odyssey'):
                    self.assertIn(token, points[2])
                self.assertIn('Elite' if language != 'de' else 'ED-', points[3])
                self.assertIn('Explorer', points[4])
                self.assertIn('DSS', points[5])
                self.assertIn('ID64', points[6])
                self.assertIn('Unable to find route', points[6])
                self.assertIn('v3.2', points[7])
                self.assertIn('v3.1', points[7])
                self.assertNotIn('EDSM', section)
                self.assertNotIn('github.sh', section)
                self.assertNotIn('Schema', section)
        german = readme('de').split('\n## ')[1].split('\n- ')[1:]
        self.assertNotIn('Gold', german[0])
        self.assertIn('Gold', german[1])
        self.assertIn('Unbekannter Bestand', german[0])
        self.assertIn('Alle einzelnen Clusterdaten bleiben erhalten', german[4])

    def test_v32_help_explains_changes_in_the_correct_topics(self):
        for language in HELP_LANGUAGES:
            with self.subTest(language=language):
                for topic in ('materials', 'explorer', 'chronicle', 'route_planner', 'settings'):
                    self.assertIn('<h3>CMDRHelper v3.2</h3>', help_topic(topic, language).text)
                material = help_topic('materials', language).text
                for token in ('146', '223', 'Spansh', 'Raw', 'Manufactured', 'Encoded', 'ly'):
                    self.assertIn(token, material)
                for key in ('trader.search', 'trader.route'):
                    self.assertIn(_TRANSLATIONS[language][key], material)
                route = help_topic('route_planner', language).text
                self.assertIn('ID64', route)
                self.assertIn('Unable to find route', route)
                self.assertIn('DSS', help_topic('explorer', language).text)
                self.assertIn('v3.1', help_topic('settings', language).text)

    def test_release_notes_keep_six_localized_highlights(self):
        from cmdrhelper.release_summaries import RELEASE_SUMMARIES
        keys = RELEASE_SUMMARIES['3.2']
        self.assertEqual(len(keys), 6)
        self.assertEqual(len(set(keys)), 6)
        for language in HELP_LANGUAGES:
            for key in keys:
                with self.subTest(language=language, key=key):
                    self.assertTrue(_TRANSLATIONS[language][key].strip())

    def test_package_uses_the_central_version_import(self):
        tree = ast.parse((ROOT / 'cmdrhelper/__init__.py').read_text())
        self.assertTrue(any(isinstance(node, ast.ImportFrom) and node.module == 'version'
                            and any(alias.name == '__version__' for alias in node.names)
                            for node in tree.body))
        for node in tree.body:
            if isinstance(node, ast.Assign):
                self.assertNotIn('__version__', [n.id for n in node.targets if isinstance(n, ast.Name)])

    def test_logs_are_ignored_without_hiding_documentation_or_fixtures(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            subprocess.run(['git', 'init', '-q', directory], check=True)
            (path / '.gitignore').write_text((ROOT / '.gitignore').read_text())
            ignored = ('logs/cmdrhelper.log.1', 'logs/archive.txt', 'app.log',
                       'app.log.1', 'app.log.2', 'app.log.12.gz')
            visible = ('docs/logging.md', 'tests/test_logging.py',
                       'tests/fixtures/log_events.json', 'docs/example.log.md')
            for name in ignored + visible:
                result = subprocess.run(['git', 'check-ignore', '--no-index', '-q', name], cwd=path)
                self.assertEqual(result.returncode, 0 if name in ignored else 1, name)

    def test_portable_material_fixture_uses_neutral_identity(self):
        fixture = (ROOT / 'tests/fixtures/materials_faber38.json').read_text()
        self.assertNotRegex(fixture, r'\bF\d{6,}\b')
        records = json.loads(fixture)
        identities = {e['FID'] for e in records if 'FID' in e}
        self.assertEqual(identities, {'FTEST0001'})

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
