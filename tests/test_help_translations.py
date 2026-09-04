import os
import re
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QDialogButtonBox

from cmdrhelper.help_content import HELP_LANGUAGES, help_topic
from cmdrhelper.help_content import de
from cmdrhelper.ui.help_dialog import HelpDialog


EXPECTED_LANGUAGES = (
    "de", "en", "fr", "it", "no", "sv", "fi", "pl", "nl", "es", "tr", "el",
)
TECHNICAL_TERMS = (
    "CMDRHelper", "Elite Dangerous", "Frontier", "Inara", "EDSM", "Spansh",
    "CTSVision", "Fleet Carrier", "Rhino", "FID", "API-Key", "SQLite",
    "FSDJump", "MissionAccepted", "Statistics", "Bank_Account", "MercCoins",
    "MiningRefined", "MaterialCollected", "Scan.Materials", "PlanetClass",
    "frontier_name", "display_name", "viewed_commander_id",
    "Prua Hypai NV-E c28-66",
)


def _tag_structure(text):
    return re.findall(r"<(/?[a-z0-9]+)(?: [^>]*)?>", text)


class HelpTranslationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_all_languages_and_topics_are_registered(self):
        self.assertEqual(HELP_LANGUAGES, EXPECTED_LANGUAGES)
        expected_topics = tuple(de.HELP_TOPICS)
        for language in HELP_LANGUAGES:
            with self.subTest(language=language):
                catalog = __import__(
                    f"cmdrhelper.help_content.{language}", fromlist=["HELP_TOPICS"]
                )
                self.assertEqual(tuple(catalog.HELP_TOPICS), expected_topics)
                self.assertEqual(len(catalog.HELP_TOPICS), 9)

    def test_every_translation_preserves_the_complete_section_structure(self):
        for language in HELP_LANGUAGES[1:]:
            catalog = __import__(
                f"cmdrhelper.help_content.{language}", fromlist=["HELP_TOPICS"]
            )
            for topic_id, (german_area, german_text) in de.HELP_TOPICS.items():
                with self.subTest(language=language, topic=topic_id):
                    area, text = catalog.HELP_TOPICS[topic_id]
                    self.assertTrue(area.strip())
                    self.assertTrue(text.strip())
                    self.assertNotEqual((area, text), (german_area, german_text))
                    self.assertEqual(_tag_structure(text), _tag_structure(german_text))
                    self.assertNotRegex(
                        text, r"<(?:h2|h3|p|li|b|code)>\s*</(?:h2|h3|p|li|b|code)>"
                    )

    def test_translations_are_not_german_placeholder_help(self):
        german_openings = (
            "Die Übersicht ist die Startseite von CMDRHelper.",
            "Die Missionsansicht zeigt die aus dem Elite-Dangerous-Journal bekannten Missionen",
            "Der Explorer wertet die vom aktiven Commander entdeckten",
            "Die Chronik ist die persönliche Reise- und Fundhistorie",
        )
        for language in HELP_LANGUAGES[1:]:
            catalog = __import__(
                f"cmdrhelper.help_content.{language}", fromlist=["HELP_TOPICS"]
            )
            combined = "\n".join(text for _area, text in catalog.HELP_TOPICS.values())
            with self.subTest(language=language):
                for opening in german_openings:
                    self.assertNotIn(opening, combined)

    def test_required_technical_terms_and_examples_remain_unchanged(self):
        german = "\n".join(
            area + "\n" + text for area, text in de.HELP_TOPICS.values()
        )
        for language in HELP_LANGUAGES[1:]:
            catalog = __import__(
                f"cmdrhelper.help_content.{language}", fromlist=["HELP_TOPICS"]
            )
            combined = "\n".join(
                area + "\n" + text for area, text in catalog.HELP_TOPICS.values()
            )
            with self.subTest(language=language):
                for term in TECHNICAL_TERMS:
                    if term in german:
                        self.assertIn(term, combined)
                self.assertNotRegex(combined, r"(?i)zxq")

    def test_every_localized_help_page_opens_with_localized_chrome(self):
        for language in HELP_LANGUAGES:
            for topic_id in de.HELP_TOPICS:
                with self.subTest(language=language, topic=topic_id):
                    dialog = HelpDialog(topic_id, language=language)
                    topic = help_topic(topic_id, language)
                    self.assertEqual(dialog.windowTitle(), topic.dialog_title)
                    self.assertEqual(dialog.help_text.text(), topic.text)
                    close_button = dialog.buttons.button(
                        QDialogButtonBox.StandardButton.Close
                    )
                    self.assertEqual(close_button.text(), topic.close_label)
                    dialog.close()

    def test_unknown_or_broken_catalog_falls_back_to_german(self):
        self.assertEqual(help_topic("overview", "xx"), help_topic("overview", "de"))
        with patch("cmdrhelper.help_content._LANGUAGES", {"de": de, "en": object()}):
            self.assertEqual(help_topic("overview", "en"), help_topic("overview", "de"))


if __name__ == "__main__":
    unittest.main()
