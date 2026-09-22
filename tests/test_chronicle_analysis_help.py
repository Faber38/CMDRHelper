"""Block 6: focused help additions and the map interactions they describe."""
import ast
from html import unescape
from importlib import import_module
import math
import os
from pathlib import Path
import re
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QEvent, QPointF, Qt
from PySide6.QtGui import QMouseEvent, QTextDocument
from PySide6.QtWidgets import QApplication

from cmdrhelper.help_content import HELP_LANGUAGES, help_topic
from cmdrhelper.ui.chronicle_view import ChronicleMapWidget
from cmdrhelper.ui.help_dialog import HelpDialog
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class ChronicleAnalysisHelpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_chronicle_operating_instructions_and_preserved_filters(self):
        text = help_topic('chronicle', 'de').text
        for phrase in ('Mausrad', 'ohne Zusatztaste', 'rechte Maustaste gedrückt halten',
                       'Doppelklick auf freien Kartenraum', 'anfängliche Schrägansicht',
                       'Filter und Systemauswahl bleiben erhalten', 'angeklickte System zum Drehpunkt',
                       'galaktischen Ebene', 'nahezu waagerechter Ansicht', 'Rotationszentrum',
                       'linker Klick auf den Systemnamen', 'Kopiersymbol ⧉', 'ausschließlich den Systemnamen',
                       '✓', 'Suchhilfe / Legende', 'Zeitraum Von/Bis (UTC)', 'Commander-Auswahl',
                       'Verschiebung und Zoom bleiben dabei erhalten'):
            self.assertIn(phrase, text)

    def test_analysis_controls_tables_and_limits(self):
        text = help_topic('jump_tip', 'de').text
        self.assertEqual(help_topic('jump_tip', 'de').area, 'Analyse')
        for phrase in ('freie Namenseingabe', 'füllt nur das Feld', 'lokal auf das unterstützte',
                       'Eine Online-Systemauflösung', 'gibt es hier nicht', 'statt des bisherigen Ergebnisses',
                       'Vergleichstabelle', 'Massencode, Region und Familie', 'eine Fundart, kein Reiseziel',
                       'beim Aufbau der Ansicht', 'bisherige Rangliste stehen', 'Neu auswerten',
                       '1 bis 50', 'anfangs 3', 'ohne historischen Treffer', 'bis zu 50 Kürzel',
                       'Treffer-Systeme / untersuchte Systeme', 'geglätteten historischen Bewertung',
                       'ohne Spaltensortierung oder Detailaktion', 'Leerhinweis', 'Rangliste geleert',
                       'keine Reiseroute', 'keine Fundgarantie'):
            self.assertIn(phrase, text)
        self.assertNotIn('Sprungtipp', text)

    def test_twelve_languages_structure_labels_and_no_fallback_prose(self):
        self.assertEqual(len(HELP_LANGUAGES), 12)
        for language in HELP_LANGUAGES:
            labels = import_module(f'cmdrhelper.i18n.{language}').TRANSLATIONS
            for context in ('chronicle', 'jump_tip'):
                with self.subTest(language=language, context=context):
                    text = help_topic(context, language).text
                    master = help_topic(context, 'de').text
                    self.assertEqual(re.findall(r'<(/?\w+)', text), re.findall(r'<(/?\w+)', master))
                    for local, german in zip(re.findall(r'<p>(.*?)</p>', text),
                                             re.findall(r'<p>(.*?)</p>', master)):
                        self.assertEqual(re.findall(r'\d+', local), re.findall(r'\d+', german))
                    self.assertNotRegex(text, r'\{[^}]+\}|\[\[')
                    self.assertNotIn('Sprungtipp', text)
                    if context == 'jump_tip':
                        for key in ('nav.jump_tip', 'analysis.system', 'analysis.current', 'analysis.run',
                                    'analysis.history_tab', 'score.target', 'score.refresh', 'score.prefer_codes'):
                            self.assertIn(labels[key], unescape(text))
                    else:
                        self.assertIn('⧉', text)
                        self.assertIn('✓', text)
                    if language != 'en':
                        for paragraph in re.findall(r'<p>(.*?)</p>', help_topic(context, 'en').text):
                            if len(paragraph.split()) > 8:
                                self.assertNotIn(paragraph, text)

    def test_no_duplicate_help_keys(self):
        root = Path(__file__).resolve().parents[1] / 'cmdrhelper/help_content'
        for language in HELP_LANGUAGES:
            tree = ast.parse((root / f'{language}.py').read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Dict):
                    keys = [key.value for key in node.keys if isinstance(key, ast.Constant)]
                    self.assertEqual(len(keys), len(set(keys)), language)

    def test_map_reset_retains_selection_and_displayed_systems(self):
        widget = self.map_widget()
        systems = list(widget.systems)
        widget.selected_address = 1
        widget.yaw, widget.pitch = 0.7, 0.2
        widget.pan = QPointF(40, 60)
        widget.scale = 0.2
        event = QMouseEvent(QEvent.MouseButtonDblClick, QPointF(1, 1), QPointF(1, 1),
                            Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        self.app.sendEvent(widget, event)
        self.assertAlmostEqual(widget.yaw, math.radians(-28))
        self.assertAlmostEqual(widget.pitch, math.radians(24))
        self.assertEqual(widget.pan, QPointF())
        self.assertEqual(widget.selected_address, 1)
        self.assertEqual(widget.systems, systems)
        self.assertGreater(widget.scale, 0.2)
        for system in systems:
            self.assertTrue(widget.rect().contains(widget._project(system)[0].toPoint()))

    def map_widget(self):
        widget = ChronicleMapWidget()
        widget.resize(800, 600)
        widget.set_systems([
            dict(system_address=1, name='Synthetic Alpha', x=-100, y=30, z=-50),
            dict(system_address=2, name='Synthetic Beta', x=100, y=-30, z=50),
        ])
        self.addCleanup(widget.close)
        return widget

    def test_rotation_pivot_and_align_preserve_zoom_pan(self):
        widget = self.map_widget()
        point = widget._project(widget.systems[0])[0]
        event = QMouseEvent(QEvent.MouseButtonPress, point, point,
                            Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        self.app.sendEvent(widget, event)
        self.assertEqual(widget._center, (-100, 30, -50))
        pan, scale = QPointF(widget.pan), widget.scale
        widget.align_galaxy()
        self.assertEqual(widget._center, (-100, 30, -50))
        self.assertEqual(widget.pan, pan)
        self.assertEqual(widget.scale, scale)
        # Empty-space pivot lies on the galactic plane, not on a selected star.
        point = QPointF(1, 1)
        expected = widget._screen_to_galactic_plane(point)
        event = QMouseEvent(QEvent.MouseButtonPress, point, point,
                            Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
        self.app.sendEvent(widget, event)
        self.assertEqual(widget._center, expected)
        self.assertEqual(widget._center[1], 0)
        widget.pitch = -widget._display_pitch_offset
        self.assertEqual(widget._screen_to_galactic_plane(point),
                         (widget._center[0], 0, widget._center[2]))

    def test_render_both_topics_four_languages_themes_and_fonts(self):
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        for language in ('de', 'en', 'fr', 'el'):
            for light, style in ((False, DARK_STYLESHEET), (True, LIGHT_STYLESHEET)):
                for size in (10, 18, 24):
                    self.app.setStyleSheet(style + f'\nQWidget {{ font-size: {size}pt; }}')
                    for context in ('chronicle', 'jump_tip'):
                        with self.subTest(language=language, light=light, size=size, context=context):
                            dialog = HelpDialog(context, language=language)
                            try:
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
                                capture = os.environ.get('CMDR_BLOCK6_CAPTURES')
                                if capture:
                                    dialog.grab().save(str(Path(capture) / f'{context}-{language}-{light}-{size}.png'))
                                scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
                                self.assertEqual(scroll.verticalScrollBar().value(), scroll.verticalScrollBar().maximum())
                            finally:
                                dialog.close()
                                dialog.deleteLater()
                                self.app.sendPostedEvents(None, QEvent.DeferredDelete)
