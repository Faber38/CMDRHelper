"""Station help remains localised and distinguishes the three data caches."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from html import unescape
from importlib import import_module
from pathlib import Path
import re
import unittest

from PySide6.QtCore import QEvent
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QApplication

from cmdrhelper.help_content import HELP_LANGUAGES, help_topic
from cmdrhelper.ui.help_dialog import HelpDialog
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class StationHelpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_german_explorer_explains_actual_station_controls_and_sources(self):
        text = help_topic('explorer', 'de').text
        for passage in ('Stationen &amp; Einrichtungen', 'aufklappbare Karten', 'Namensteilen',
                        'Groß-/Kleinschreibung', 'Suche und beide Filter', 'Orbitalstationen',
                        'Siedlungen', 'unbekannte Entfernungen', 'numerisch', 'alphabetisch',
                        'Kopf einer Stationskarte', 'Landeplätze', 'höchstens drei Services',
                        'nicht geschätzt', 'Journalinformationen Vorrang', 'keine Fleet Carrier',
                        'keine Netzabfrage', 'Automatisch an Fenster anpassen',
                        'standardmäßig eingeschaltet', 'einmal an die Fenstergröße',
                        'manuell zoomen und verschieben'):
            self.assertIn(passage, text)

    def test_german_settings_explains_switch_triggers_cache_and_manual_failures(self):
        text = help_topic('settings', 'de').text
        for passage in ('Spansh-Stationsinformationen ergänzen', 'Schalter ist anfangs aus',
                        'nicht gelöscht', 'keine Netzabfrage', 'Live-Eintritt',
                        'Programmstart, Commanderwechsel, Archivimport', 'weniger als 7 Tage',
                        'höchstens ein automatischer Versuch', 'auch ein Fehlschlag zählt',
                        'über Helper-Neustarts erhalten', 'auch offline',
                        'keine Handelsmarktpreise', 'flüchtigen RAM-Suchcache',
                        'nur unter 24 Stunden gültig', 'fehlgeschlagenen automatischen Tagesversuch',
                        'heute nach lokalem Kalender', 'fehlgeschlagener manueller Versuch'):
            self.assertIn(passage, text)

    def test_twelve_languages_include_local_controls_and_matching_sections(self):
        for language in HELP_LANGUAGES:
            ui = import_module(f'cmdrhelper.i18n.{language}').TRANSLATIONS
            for context, keys, count in (
                ('explorer', ('stations.search', 'stations.all_bodies', 'spansh.services',
                              'spansh.refresh', 'explorer.overview_auto_fit', 'explorer.overview_fit'), 34),
                ('settings', ('spansh.enabled', 'settings.online_services',
                              'spansh.refresh', 'spansh.refresh_already_today'), 35),
            ):
                with self.subTest(language=language, context=context):
                    text = help_topic(context, language).text
                    self.assertEqual(text.count('<h3>'), count)
                    self.assertNotRegex(text, r'\{[^}]+\}')
                    for key in keys:
                        self.assertIn(ui[key], unescape(text))
                    master = help_topic(context, 'de').text
                    self.assertEqual(re.findall(r'<(/?\w+)', text), re.findall(r'<(/?\w+)', master))
            settings = help_topic('settings', language).text
            self.assertIn('7', settings)
            self.assertIn('24', settings)
            self.assertIn('mémoire vive' if language == 'fr' else 'RAM', settings)
            self.assertNotEqual(ui['explorer.overview_auto_fit'], 'explorer.overview_auto_fit')
            if language != 'en':
                for context in ('explorer', 'settings'):
                    text = help_topic(context, language).text
                    for paragraph in re.findall('<p>(.*?)</p>', help_topic(context, 'en').text):
                        if 'station cache' in paragraph or 'Automatically fit to window' in paragraph:
                            self.assertNotIn(paragraph, text)

    def test_help_rendering_dark_light_10_18_24_without_horizontal_overflow(self):
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        for language in ('de', 'en', 'fr', 'el'):
            for light, style in ((False, DARK_STYLESHEET), (True, LIGHT_STYLESHEET)):
                for size in (10, 18, 24):
                    self.app.setStyleSheet(style + f'\nQWidget {{ font-size: {size}pt; }}')
                    for context in ('explorer', 'settings'):
                        with self.subTest(language=language, light=light, size=size, context=context):
                            dialog = HelpDialog(context, language=language)
                            dialog.show()
                            self.app.processEvents()
                            scroll = dialog.scroll_area
                            self.assertLessEqual(scroll.widget().width(), scroll.viewport().width())
                            self.assertEqual(scroll.horizontalScrollBar().maximum(), 0)
                            self.assertGreater(scroll.verticalScrollBar().maximum(), 0)
                            doc = QTextDocument()
                            doc.setDefaultFont(dialog.help_text.font())
                            doc.setHtml(dialog.help_text.text())
                            doc.setTextWidth(dialog.help_text.width())
                            self.assertLessEqual(doc.idealWidth(), dialog.help_text.width() + 1)
                            self.assertFalse(dialog.grab().isNull())
                            capture = os.environ.get('CMDR_BLOCK4_CAPTURES')
                            if capture and size == 24:
                                # Show the added block in the visual review capture.
                                target = 'Stationen & Einrichtungen' if language == 'de' else {
                                    'en': 'Stations and facilities', 'fr': 'Stations et installations',
                                    'el': 'Σταθμοί και εγκαταστάσεις'}[language]
                                if context == 'settings':
                                    target = {'de': 'Spansh-Stationsinformationen', 'en': 'Spansh station information',
                                              'fr': 'Informations de stations Spansh', 'el': 'Στοιχεία σταθμών Spansh'}[language]
                                cursor = doc.find(target)
                                if not cursor.isNull():
                                    scroll.verticalScrollBar().setValue(int(doc.documentLayout().blockBoundingRect(cursor.block()).top()))
                                dialog.grab().save(str(Path(capture) / f'help-{context}-{language}-{light}-{size}.png'))
                            dialog.close()
                            dialog.deleteLater()
                            self.app.sendPostedEvents(None, QEvent.DeferredDelete)
