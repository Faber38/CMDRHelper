"""Check the actual release metadata consumed by the publisher; no publication."""
import json
from pathlib import Path
import re
import unittest
from collections import Counter

import cmdrhelper
from cmdrhelper.database import SCHEMA_VERSION
from cmdrhelper.i18n import _TRANSLATIONS
from cmdrhelper.odyssey_ranks import RANKS
from cmdrhelper.release_summaries import RELEASE_SUMMARIES
from tools.publish_release import release_notes, version_at

ROOT = Path(__file__).resolve().parents[1]


class Release395Tests(unittest.TestCase):
    def test_publisher_notes_and_readmes_in_twelve_languages(self):
        self.assertEqual(version_at(ROOT), cmdrhelper.__version__)
        self.assertEqual(SCHEMA_VERSION, 23)
        keys = RELEASE_SUMMARIES["3.9.5"]
        self.assertEqual(len(keys), 6)
        notes = release_notes(ROOT, "3.9.5")
        metadata = json.loads(re.search(r"<!-- cmdrhelper-update-summary\s+(.*?)-->", notes, re.S)[1])
        self.assertEqual(set(metadata), set(_TRANSLATIONS))
        self.assertEqual(len(metadata), 12)
        for lang, translations in _TRANSLATIONS.items():
            expected = [translations[key] for key in keys]
            self.assertEqual(metadata[lang], expected)
            self.assertTrue(all(expected))
            if lang != "en":
                self.assertTrue(all(text != _TRANSLATIONS["en"][key] for text, key in zip(expected, keys)))
            path = ROOT / ("README.md" if lang == "en" else f"README_{lang.upper()}.md")
            section = path.read_text().split("## CMDRHelper v3.9.5\n", 1)[1].split("\n## ", 1)[0]
            self.assertEqual([line[2:] for line in section.splitlines() if line.startswith("- ")], expected)
        document = (ROOT / "docs/release-3.9.5.md").read_text()
        self.assertEqual([line[2:] for line in document.splitlines() if line.startswith("- ")], metadata["de"])

    def test_published_odyssey_counts_match_catalog(self):
        self.assertEqual(len(RANKS), 223)
        self.assertEqual(Counter(value.rank for value in RANKS.values()),
                         {"A": 16, "B": 54, "C": 28, "D": 94, "?": 31})
