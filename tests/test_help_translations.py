import os
import re
import unittest
from html.parser import HTMLParser
from importlib import import_module
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
        self.assertEqual(len(de.HELP_TOPICS), 11)
        expected_topics = tuple(de.HELP_TOPICS)
        for language in HELP_LANGUAGES:
            with self.subTest(language=language):
                catalog = __import__(
                    f"cmdrhelper.help_content.{language}", fromlist=["HELP_TOPICS"]
                )
                self.assertEqual(tuple(catalog.HELP_TOPICS), expected_topics)
                self.assertEqual(len(catalog.HELP_TOPICS), 11)

    def test_navigation_translations_preserve_numbers_and_have_no_german_passages(self):
        master = de.HELP_TOPICS["planet_navigation"][1]
        plain = lambda text: re.sub(r"<[^>]+>", "", text)
        numbers = lambda text: re.findall(r"[−+]?\d+°?", plain(text))
        german_passages = [
            plain(block).strip() for block in re.findall(r"<(?:p|li)>(.*?)</(?:p|li)>", master)
            if len(plain(block).split()) >= 4
        ]
        for language in HELP_LANGUAGES[1:]:
            with self.subTest(language=language):
                topic = help_topic("planet_navigation", language)
                self.assertNotEqual(topic, help_topic("planet_navigation", "de"))
                self.assertEqual(numbers(topic.text), numbers(master))
                for term in ("BodyID", "SystemAddress", "Elite", "HUD"):
                    self.assertEqual(topic.text.count(term), master.count(term))
                for passage in german_passages:
                    self.assertNotIn(passage, plain(topic.text))
                self.assertNotRegex(topic.text, r"Planeten-Navigation|Zielkoordinaten|Zielentfernung|"
                                    r"Zielkurs|Breitengrad|Längengrad|Oberflächenabstand|"
                                    r"klickdurchlässig|Navigationswerte|Warte auf planetare")
                sections = re.split(r"<h3>.*?</h3>", topic.text)[1:]
                self.assertEqual(len(sections), 10)
                for section in sections:
                    self.assertRegex(section, r"<(?:p|li)>.+?</(?:p|li)>")

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
                    self.assertEqual(
                        _tag_structure(text),
                        _tag_structure(german_text),
                    )
                    self.assertNotRegex(
                        text, r"<(?:h2|h3|p|li|b|code)>\s*</(?:h2|h3|p|li|b|code)>"
                    )

    def test_favorites_help_preserves_structure_and_localized_actions(self):
        from importlib import import_module
        master = de.HELP_TOPICS["explorer"][1].split("<h3>★ Favoriten</h3>")[1]
        german_passages = re.findall(r"<p>(.*?)</p>", master)
        for language in HELP_LANGUAGES:
            with self.subTest(language=language):
                text = help_topic("explorer", language).text
                ui = import_module(f"cmdrhelper.i18n.{language}").TRANSLATIONS
                favorite_text = text[text.index("<h3>" + ui["favorites.title"] + "</h3>"):]
                self.assertEqual(text.count("<h3>"), 26)
                for tag, count in (("h3", 5), ("p", 17), ("ul", 1), ("li", 3)):
                    self.assertEqual(favorite_text.count(f"<{tag}>"), count)
                for key in ("save_system", "save_body", "save_surface", "open", "edit",
                            "delete", "route", "navigate", "latest", "choose_image", "use_image",
                            "remove_image", "show_explorer"):
                    self.assertIn(ui["favorites." + key], favorite_text)
                for term in ("PNG", "JPEG", "WebP", "BMP", "Windows", "Steam/Proton"):
                    self.assertEqual(favorite_text.count(term), master.count(term))
                self.assertRegex(favorite_text, r"0[,.]0")
                self.assertNotRegex(favorite_text, r"\{[^}]+\}")
                if language != "de":
                    for passage in german_passages:
                        self.assertNotIn(passage, favorite_text)
                    self.assertNotRegex(favorite_text, r"Oberflächenort|Aktuellen Standort speichern|"
                                        r"Letzten Screenshot verwenden|Bild auswählen|"
                                        r"Konvertierungsziel|Favoritenbilder|Beim Commanderwechsel")

    def test_chronicle_translations_preserve_structure_examples_and_identifiers(self):
        master = de.HELP_TOPICS["chronicle"][1]
        plain = lambda text: re.sub(r"<[^>]+>", "", text)
        paragraphs = lambda text: re.findall(r"<p>(.*?)</p>", text)
        german_passages = [plain(p) for p in paragraphs(master)
                           if len(plain(p).split()) >= 5]
        for language in HELP_LANGUAGES:
            with self.subTest(language=language):
                text = help_topic("chronicle", language).text
                self.assertEqual(text.count("<h3>"), 23)
                self.assertEqual(text.count("<p>"), 81)
                self.assertEqual(text.count("<ul>"), 8)
                self.assertEqual(text.count("<li>"), 31)
                self.assertEqual(re.findall(r"<code>(.*?)</code>", text),
                                 re.findall(r"<code>(.*?)</code>", master))
                for translated, german in zip(paragraphs(text), paragraphs(master)):
                    self.assertEqual(re.findall(r"\d+", plain(translated)),
                                     re.findall(r"\d+", plain(german)))
                if language != "de":
                    for passage in german_passages:
                        self.assertNotIn(passage, plain(text))
                    self.assertNotRegex(text, r"Freitext|Zeitraum|Anwenden|Zurücksetzen|"
                                        r"tatsächliche Systembesuche|Gesamtmengen|"
                                        r"Karten-Commander|Eigene Abbau-Funde")

    def test_cargo_help_is_present_in_every_language(self):
        for language in HELP_LANGUAGES:
            catalog = __import__(
                f"cmdrhelper.help_content.{language}", fromlist=["HELP_TOPICS"]
            )
            explorer = catalog.HELP_TOPICS["explorer"][1]
            settings = catalog.HELP_TOPICS["settings"][1]
            combined = explorer + settings
            with self.subTest(language=language):
                self.assertIn("Cargo", combined)
                self.assertIn("SRV", combined)
                self.assertIn("FID", combined)
                self.assertGreaterEqual(
                    combined.count("Cargo") + combined.count("Frachtraum"), 2
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

    def test_material_help_is_localized_with_complete_odyssey_sections(self):
        master = de.HELP_TOPICS['materials'][1]
        german_paragraphs = re.findall(r'<p>(.*?)</p>', master)
        for language in HELP_LANGUAGES:
            with self.subTest(language=language):
                module = import_module('cmdrhelper.help_content.' + language)
                text = help_topic('materials', language).text
                self.assertEqual(text, module.HELP_TOPICS['materials'][1])
                self.assertEqual(_tag_structure(text), _tag_structure(master))
                engineering, odyssey = text.split('<h3>Odyssey</h3>')
                self.assertEqual(odyssey.count('<p>'), 4)
                self.assertIn('1000', odyssey)
                self.assertIn('?', odyssey)
                self.assertNotIn('250', odyssey)
                self.assertNotIn('244', odyssey)
                self.assertEqual(re.findall(r'\d+', engineering),
                                 re.findall(r'\d+', master.split('<h3>Odyssey</h3>')[0]))
                if language != 'de':
                    for paragraph in german_paragraphs:
                        self.assertNotIn(paragraph, text)
                    ui = import_module('cmdrhelper.i18n.' + language).TRANSLATIONS
                    for key in ('items', 'components', 'data', 'consumables', 'locker',
                                'backpack', 'total', 'usage', 'mission', 'engineering', 'empty'):
                        self.assertIn(ui['odyssey.' + key], odyssey)
                    filters = re.findall(r'<p>(.*?)</p>', odyssey)[2]
                    for key in ('materials.all', 'odyssey.mission', 'odyssey.engineering',
                                'odyssey.backpack', 'odyssey.locker', 'odyssey.empty'):
                        self.assertIn(ui[key], filters)
                    self.assertIn('Powerplay', odyssey)

    def test_help_html_is_balanced_in_all_languages(self):
        class BalancedHTML(HTMLParser):
            def __init__(self):
                super().__init__()
                self.stack = []

            def handle_starttag(self, tag, attrs):
                if tag not in ('br', 'hr', 'img', 'meta', 'link', 'input'):
                    self.stack.append(tag)

            def handle_endtag(self, tag):
                if not self.stack or self.stack.pop() != tag:
                    raise AssertionError('Unmatched HTML end tag: ' + tag)

        for language in HELP_LANGUAGES:
            module = import_module('cmdrhelper.help_content.' + language)
            for topic, (_, text) in module.HELP_TOPICS.items():
                with self.subTest(language=language, topic=topic):
                    parser = BalancedHTML()
                    parser.feed(text)
                    parser.close()
                    self.assertEqual(parser.stack, [])

    def test_help_placeholders_match_german_master(self):
        placeholders = lambda text: sorted(re.findall(r'\{[^{}]+\}', text))
        for language in HELP_LANGUAGES:
            module = import_module('cmdrhelper.help_content.' + language)
            with self.subTest(language=language):
                self.assertEqual(placeholders(module.DIALOG_TITLE), placeholders(de.DIALOG_TITLE))
                self.assertEqual(placeholders(module.CLOSE_LABEL), placeholders(de.CLOSE_LABEL))
            for topic, (area, text) in module.HELP_TOPICS.items():
                with self.subTest(language=language, topic=topic):
                    master_area, master_text = de.HELP_TOPICS[topic]
                    self.assertEqual(placeholders(area + text), placeholders(master_area + master_text))

    def test_unknown_or_broken_catalog_falls_back_to_german(self):
        self.assertEqual(help_topic("overview", "xx"), help_topic("overview", "de"))
        with patch("cmdrhelper.help_content._LANGUAGES", {"de": de, "en": object()}):
            self.assertEqual(help_topic("overview", "en"), help_topic("overview", "de"))
        from types import SimpleNamespace
        with patch("cmdrhelper.help_content._LANGUAGES", {"de": de, "en": SimpleNamespace(HELP_TOPICS={})}):
            self.assertEqual(help_topic("planet_navigation", "en"),
                             help_topic("planet_navigation", "de"))


if __name__ == "__main__":
    unittest.main()
