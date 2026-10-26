"""v3.9.20 release metadata and existing update dialog contract."""
import json
from pathlib import Path
import re
import unittest

from PySide6.QtWidgets import QApplication
from cmdrhelper import __version__
from cmdrhelper.database import SCHEMA_VERSION
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language
from cmdrhelper.release_summaries import RELEASE_SUMMARIES, release_summary
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.ui.update_confirmation import UpdateConfirmationBox
from cmdrhelper.update import is_newer_version
from tools.publish_release import release_notes, version_at

ROOT = Path(__file__).resolve().parents[1]


class Release3920Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_metadata_readmes_and_real_dialog_all_languages_themes(self):
        self.assertEqual(__version__, '3.9.20')
        self.assertEqual(version_at(ROOT), __version__)
        self.assertEqual(SCHEMA_VERSION, 23)
        self.assertTrue(is_newer_version(__version__, '3.9.19'))
        self.addCleanup(set_language, get_language())
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        notes = release_notes(ROOT, __version__)
        payload = json.loads(re.search(r'<!-- cmdrhelper-update-summary\s+(.*?)-->', notes, re.S)[1])
        self.assertEqual(set(payload), set(_TRANSLATIONS))
        self.assertEqual(len(payload), 12)
        keys = RELEASE_SUMMARIES[__version__]
        self.assertEqual(len(keys), 6)
        for lang, table in _TRANSLATIONS.items():
            expected = [table[key] for key in keys]
            self.assertTrue(all(s.strip() for s in expected))
            self.assertEqual(payload[lang], expected)
            set_language(lang)
            self.assertEqual(release_summary('v3.9.20', notes), expected)
            self.assertEqual(release_summary('v3.9.20'), expected)
            self.assertNotEqual(release_summary('3.9.19'), expected)
            readme = (ROOT / ('README.md' if lang == 'en' else f'README_{lang.upper()}.md')).read_text()
            section = readme.split('## CMDRHelper v3.9.20\n', 1)[1].split('\n## ', 1)[0]
            self.assertEqual([s[2:] for s in section.splitlines() if s.startswith('- ')], expected)
            self.assertIn('## CMDRHelper v3.9.19\n', readme)
            for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                self.app.setStyleSheet(theme)
                box = UpdateConfirmationBox(None, 'Update', 'Test', __version__, notes)
                self.addCleanup(box.close)
                box.show()
                self.app.processEvents()
                self.assertTrue(all(s in box.changes.toPlainText() for s in expected))
                self.assertIn('3.9.20', box.changes.toPlainText())
                self.assertLessEqual(box.changes.height(), 200)
                box.close()
        documented = (ROOT / 'docs/release-3.9.20.md').read_text()
        self.assertEqual([s[2:] for s in documented.splitlines() if s.startswith('- ')], payload['de'])
