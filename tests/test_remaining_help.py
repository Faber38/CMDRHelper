"""Focused remaining help corrections, verified against existing controls."""
import ast
from datetime import datetime, timedelta, timezone
from html import unescape
from importlib import import_module
import json
import os
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QEvent
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QApplication
from cmdrhelper.help_content import HELP_LANGUAGES, help_topic
from cmdrhelper.ui.help_dialog import HelpDialog
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.online_services import load_cached_edsm_bodies, fetch_edsm_bodies


class RemainingHelpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_overview_distinguishes_button_and_main_section(self):
        text = unescape(help_topic('overview', 'de').text)
        self.assertIn('„Missionen →“', text)
        self.assertIn('Hauptbereich „Missionen & Belohnungen“', text)
        ui = import_module('cmdrhelper.i18n.de').TRANSLATIONS
        self.assertEqual(ui['overview.missions_button'], 'Missionen →')

    def test_odyssey_unknown_owner_and_stolen_are_not_invented(self):
        text = help_topic('materials', 'de').text
        for phrase in ('ausdrücklich als gestohlen', 'kein bestätigtes „nicht gestohlen“',
                       'Besitzerkennung', 'Tooltip', 'unbekannter Besitzername',
                       'Aktuelle Beschaffbarkeit nicht bestätigt',
                       'bedeutet nicht, dass der Gegenstand nicht beschaffbar ist',
                       '146', '223', '57', 'Ø-Preis', 'Materialhändlersuche'):
            self.assertIn(phrase, text)
        self.assertNotRegex(text, r'Bohrer|Rig-|Kameraideen|Ingenieurverwaltung')

    def test_images_exact_checkboxes_and_actions(self):
        text = help_topic('images', 'de').text
        for phrase in ('Neue BMP-Dateien automatisch konvertieren',
                       'BMP nach erfolgreicher Konvertierung löschen', 'Einstellungen speichern',
                       'Quell- und Zielordner, Zielformat, Aufhellung', 'beide Checkboxzustände',
                       'Galerie aktualisieren', 'aktuellen Galeriefilter', 'keine BMP-Konvertierung'):
            self.assertIn(phrase, text)
        self.assertNotIn('„Automatisch konvertieren“', text)
        self.assertNotIn('„BMP nach Konvertierung löschen“', text)

    def test_settings_distinguishes_cache_services_huds_and_shortcut(self):
        text = help_topic('settings', 'de').text
        for phrase in ('EDSM-Körperdaten und Cache', 'normalen Journalaktualisierung',
                       'keinen API-Key', 'bis zu 24 Stunden', 'Cachedateien werden dadurch nicht gelöscht',
                       'linken Seitenleiste', 'starten selbst keine Onlineabfrage',
                       'eigene öffentliche EDSM-Netzabfrage', 'Inara-Übertragung',
                       'Spansh-Stationsinformationen', 'Hotkey festlegen', 'Hotkey ändern',
                       'Hotkey entfernen', 'Nicht belegt', 'Registrierungskonflikt', 'keinen Screenshot'):
            self.assertIn(phrase, text)

    def test_twelve_languages_structure_controls_and_no_english_prose_fallback(self):
        keys = {
            'overview': ('nav.missions', 'overview.missions_button'),
            'materials': ('odyssey.stolen', 'odyssey.owner', 'odyssey.availability_unknown'),
            'images': ('images.auto_convert', 'images.delete_bmp', 'images.save_settings', 'images.refresh_gallery'),
            'settings': ('settings.use_edsm', 'settings.save_online', 'settings.auto_show',
                         'settings.explorer_value_live_window', 'settings.explorer_bio_live_window',
                         'settings.explorer_geo_live_window', 'settings.cargo_live_window',
                         'settings.cargo_hud', 'settings.navigation_hud', 'settings.edsm_system_status',
                         'quick_favorite.title', 'quick_favorite.set', 'quick_favorite.change',
                         'quick_favorite.remove', 'quick_favorite.unassigned'),
        }
        self.assertEqual(len(HELP_LANGUAGES), 12)
        for language in HELP_LANGUAGES:
            ui = import_module(f'cmdrhelper.i18n.{language}').TRANSLATIONS
            for context, labels in keys.items():
                with self.subTest(language=language, context=context):
                    text = help_topic(context, language).text
                    master = help_topic(context, 'de').text
                    self.assertEqual(re.findall(r'<(/?\w+)', text), re.findall(r'<(/?\w+)', master))
                    self.assertNotRegex(text, r'\{[^}]+\}|\[\[')
                    for key in labels:
                        self.assertIn(ui[key], unescape(text))
                    if language != 'en':
                        for paragraph in re.findall('<p>(.*?)</p>', help_topic(context, 'en').text):
                            if len(paragraph.split()) > 8:
                                self.assertNotIn(paragraph, text)

    def test_german_station_terminology_and_greek_filename(self):
        ui = import_module('cmdrhelper.i18n.de').TRANSLATIONS
        self.assertEqual(ui['settings.online_services'], 'ONLINE-DIENSTE')
        for key in ('release.3_6.2', 'stations.local_notice_settings', 'spansh.refresh_disabled'):
            self.assertIn('Online-Dienste', ui[key])
            self.assertNotIn('Online Services', ui[key])
        text = help_topic('settings', 'el').text
        self.assertIn('τα αρχεία <code>Journal*.log</code>', text)
        self.assertNotIn('Εφημερίδα*.ημερολόγιο', text)

    def test_example_filename_has_local_wrap_points_without_visible_changes(self):
        for language in HELP_LANGUAGES:
            text = help_topic('images', language).text
            self.assertIn('2026-09-04_&#8203;13-18-22_&#8203;EXAMPLE_&#8203;Sol.png', text)
            self.assertIn('2026-09-04_13-18-22_EXAMPLE_Sol.png', unescape(text).replace('\u200b', ''))

    def test_no_duplicate_help_or_i18n_keys(self):
        root = Path(__file__).resolve().parents[1] / 'cmdrhelper'
        for folder in ('help_content', 'i18n'):
            for language in HELP_LANGUAGES:
                for node in ast.walk(ast.parse((root / folder / f'{language}.py').read_text())):
                    if isinstance(node, ast.Dict):
                        keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]
                        self.assertEqual(len(keys), len(set(keys)), (folder, language))

    def test_body_cache_survives_reload_and_expires_after_24_hours(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic-cache.json'
            payload = {'system': 'Synthetic Test', 'data': {'bodies': [], 'body_count': 0}}
            with patch('cmdrhelper.online_services._edsm_cache_file', return_value=path):
                for age, usable in ((23, True), (25, False)):
                    payload['fetched_at'] = (datetime.now(timezone.utc) - timedelta(hours=age)).isoformat()
                    path.write_text(json.dumps(payload))
                    self.assertEqual(load_cached_edsm_bodies('Synthetic Test') is not None, usable)
                payload['fetched_at'] = datetime.now(timezone.utc).isoformat()
                path.write_text(json.dumps(payload))
                with patch('cmdrhelper.online_services._fetch_edsm_json') as fetch:
                    ok, data, source = fetch_edsm_bodies('Synthetic Test')
                    self.assertTrue(ok)
                    self.assertEqual(source, 'cache')
                    self.assertEqual(data, payload['data'])
                    fetch.assert_not_called()

    def test_render_four_topics_at_standard_width(self):
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        for language in ('de', 'en', 'fr', 'el'):
            for light, style in ((False, DARK_STYLESHEET), (True, LIGHT_STYLESHEET)):
                for size in (10, 18, 24):
                    self.app.setStyleSheet(style + f'\nQWidget {{ font-size: {size}pt; }}')
                    for context in ('overview', 'materials', 'images', 'settings'):
                        with self.subTest(language=language, light=light, size=size, context=context):
                            dialog = HelpDialog(context, language=language)
                            try:
                                dialog.show()
                                self.app.processEvents()
                                self.assertEqual(dialog.width(), 640)
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
                                capture = os.environ.get('CMDR_REST_CAPTURES')
                                if capture:
                                    dialog.grab().save(str(Path(capture) / f'{context}-{language}-{light}-{size}.png'))
                                scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
                                self.assertEqual(scroll.verticalScrollBar().value(), scroll.verticalScrollBar().maximum())
                            finally:
                                dialog.close()
                                dialog.deleteLater()
                                self.app.sendPostedEvents(None, QEvent.DeferredDelete)
