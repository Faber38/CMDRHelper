"""Regression checks for the ten final help-audit finding groups."""
import ast
from html import unescape
from importlib import import_module
import os
from pathlib import Path
import re
import unittest
import unicodedata
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QEvent
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QApplication
from cmdrhelper.help_content import HELP_LANGUAGES, help_topic
from cmdrhelper.help_content.de import HELP_TOPICS
from cmdrhelper.ui.help_dialog import HelpDialog
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


def visible(text):
    return unescape(re.sub('<[^>]+>', '', text)).replace('\u200b', '')


class HelpAuditCorrectionsTests(unittest.TestCase):
    def test_latest_status_matches_current_ui(self):
        for language in 'en el es fi fr it pl sv tr'.split():
            ui = import_module('cmdrhelper.i18n.' + language).TRANSLATIONS
            headings = re.findall('<h3>(.*?)</h3>', help_topic('overview', language).text)
            normalize = lambda value: ''.join(c for c in unicodedata.normalize('NFD', value.casefold()) if not unicodedata.combining(c))
            self.assertIn(normalize(ui['overview.latest_status']), [normalize(h) for h in headings])
        for language in HELP_LANGUAGES:
            self.assertNotIn('Last Stand', help_topic('overview', language).text)
            self.assertNotIn('Last State', help_topic('overview', language).text)

    def test_recent_systems_mean_recent_visits(self):
        expected = dict(en='Recently visited systems', el='Συστήματα που επισκεφτήκατε πρόσφατα',
                        es='Sistemas visitados recientemente', fi='Viimeksi vieraillut järjestelmät',
                        fr='Systèmes récemment visités', it='Sistemi visitati di recente',
                        no='Nylig besøkte systemer', pl='Ostatnio odwiedzone systemy',
                        sv='Senast besökta system', tr='Son ziyaret edilen sistemler')
        for language, heading in expected.items():
            self.assertIn('<h3>' + heading + '</h3>', help_topic('overview', language).text)

    def test_journal_is_not_a_newspaper(self):
        wrong = dict(el=r'εφημερίδα|περιοδικ', es=r'\brevistas?\b', it=r'\brivista\b',
                     nl='tijdschrift', no='tidsskrift', sv='tidning|tidskrift', tr=r'\bdergi')
        for language, pattern in wrong.items():
            for topic in HELP_TOPICS:
                self.assertNotRegex(help_topic(topic, language).text.casefold(), pattern)

    def test_journal_filename_is_language_independent(self):
        for language in HELP_LANGUAGES:
            self.assertEqual(re.findall('<code>(.*?)</code>', help_topic('settings', language).text),
                             ['Journal*.log'])

    def test_unknown_path_and_filename_are_not_translated(self):
        for language in HELP_LANGUAGES:
            text = help_topic('images', language).text
            self.assertIn('UNKNOWN_UNKNOWN/', visible(text))
            self.assertIn('<b>UNKNOWN</b>', text)
            for wrong in ('SCONOSCIUTO', 'DESCONOCIDO', 'NIEZNANY', 'BİLİNMİYOR',
                          'ΑΓΝΩΣΤΟΣ', 'TUNTEMATON', 'INCONNU', 'ONBEKEND', 'UKJENT', 'OKÄND'):
                self.assertNotIn('<b>' + wrong, text)

    def test_all_commanders_filter_matches_ui(self):
        for language in ('el', 'fi', 'no'):
            ui = import_module('cmdrhelper.i18n.' + language).TRANSLATIONS
            self.assertIn(ui['images.filter_all'], help_topic('images', language).text)

    def test_path_wrap_is_invisible(self):
        for language in ('it', 'es', 'no', 'sv'):
            text = help_topic('images', language).text
            self.assertIn('UNKNOWN_&#8203;UNKNOWN/', text)
            self.assertIn('UNKNOWN_UNKNOWN/', visible(text))

    def test_finnish_journal_paragraph_spacing(self):
        text = help_topic('settings', 'fi').text
        self.assertIn('<p>Lokit sisältävät muun muassa:</p>', text)
        self.assertNotIn('Lehdet tarjoavat', text)
        self.assertIn('tallentaa käytetyn Windows- tai Proton-profiilin <code>Journal*.log</code> -tiedostot', text)

    def test_tip_headings(self):
        for language, old, new in (('el', 'Ακρο', 'Συμβουλή'), ('fi', 'Kärki', 'Vinkki'),
                                   ('it', 'Mancia', 'Suggerimento'), ('no', 'Tupp', 'Tips'),
                                   ('sv', 'Dricks', 'Tips'), ('tr', 'Uç', 'İpucu')):
            for topic in ('overview', 'explorer', 'images', 'settings'):
                text = help_topic(topic, language).text
                self.assertNotIn('<h3>' + old + '</h3>', text)
                self.assertIn('<h3>' + new + '</h3>', text)

    def test_html_word_boundaries(self):
        for language in HELP_LANGUAGES:
            for topic in ('images', 'settings'):
                text = help_topic(topic, language).text
                self.assertNotRegex(text, r'\w<(?:b|code)>|</(?:b|code)>\w')

    def test_catalog_structure_and_duplicates(self):
        self.assertEqual(len(HELP_LANGUAGES), 12)
        self.assertEqual(len(HELP_TOPICS), 12)
        for language in HELP_LANGUAGES:
            module = import_module('cmdrhelper.help_content.' + language)
            self.assertEqual(set(module.HELP_TOPICS), set(HELP_TOPICS))
            for node in ast.walk(ast.parse(Path(module.__file__).read_text())):
                if isinstance(node, ast.Dict):
                    keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]
                    self.assertEqual(len(keys), len(set(keys)))
            for topic in HELP_TOPICS:
                text = help_topic(topic, language).text
                self.assertEqual(re.findall(r'<(/?\w+)', text), re.findall(r'<(/?\w+)', HELP_TOPICS[topic][1]))
                self.assertEqual(re.findall(r'\{\w+\}', text), re.findall(r'\{\w+\}', HELP_TOPICS[topic][1]))
                if language != 'en':
                    for paragraph in re.findall('<p>(.*?)</p>', help_topic(topic, 'en').text, re.S):
                        if len(paragraph.split()) > 8:
                            self.assertNotIn(paragraph, text)

    def test_full_864_layout_matrix(self):
        app = QApplication.instance() or QApplication([])
        self.addCleanup(app.setStyleSheet, app.styleSheet())
        count = 0
        with patch('socket.socket.connect', side_effect=AssertionError('Network forbidden')):
            for language in HELP_LANGUAGES:
                for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                    for size in (10, 18, 24):
                        app.setStyleSheet(style + f'\nQWidget {{ font-size: {size}pt; }}')
                        for topic in HELP_TOPICS:
                            with self.subTest(language=language, size=size, topic=topic, light=style == LIGHT_STYLESHEET):
                                dialog = HelpDialog(topic, language=language)
                                try:
                                    dialog.show()
                                    app.processEvents()
                                    self.assertEqual(dialog.width(), 640)
                                    scroll = dialog.scroll_area
                                    self.assertLessEqual(scroll.widget().width(), scroll.viewport().width())
                                    self.assertEqual(scroll.horizontalScrollBar().maximum(), 0)
                                    doc = QTextDocument()
                                    doc.setDefaultFont(dialog.help_text.font())
                                    doc.setHtml(dialog.help_text.text())
                                    doc.setTextWidth(dialog.help_text.width())
                                    self.assertLessEqual(doc.idealWidth(), dialog.help_text.width() + 1)
                                    self.assertFalse(dialog.grab().isNull())
                                    scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
                                    self.assertEqual(scroll.verticalScrollBar().value(), scroll.verticalScrollBar().maximum())
                                    count += 1
                                finally:
                                    dialog.close()
                                    dialog.deleteLater()
                                    app.sendPostedEvents(None, QEvent.DeferredDelete)
        self.assertEqual(count, 864)
