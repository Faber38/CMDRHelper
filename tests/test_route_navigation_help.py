"""Help acceptance against current route progression and navigation controls."""
import ast
from html import unescape
from importlib import import_module
import os
from pathlib import Path
import re
import unittest
from unittest.mock import Mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QEvent
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QApplication

from cmdrhelper.help_content import HELP_LANGUAGES, help_topic
from cmdrhelper.route_planner.models import ShipRoute, ShipRouteJump
from cmdrhelper.route_planner.ship_route_controller import ShipRouteController
from cmdrhelper.ui.help_dialog import HelpDialog
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class RouteNavigationHelpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_german_route_workflow_and_limits(self):
        text = help_topic('route_planner', 'de').text
        for phrase in ('Analyse', 'Systemanalyse', 'Erfahrungsdaten', 'eigenen Start',
                       'leeres Startfeld', 'mehrdeutigen', 'keine Schiffsauswahl',
                       'manuelle Vorgaben', 'Fuel Power', 'guided', '500 ly',
                       '25.000 t', 'Hintergrund', 'keinen Abbrechen-Button',
                       'feste Routenfolge', 'keine zusätzliche Häkchenanzeige',
                       'einem späteren System', 'Carrier-Sprünge', 'noch kein Name',
                       'automatisch in die Zwischenablage', 'keine automatische Neuberechnung',
                       'Vorwärtssprung', 'Route abgeschlossen', 'nicht gelöscht',
                       'Nur die Carrierroute', 'CSV-Datei', 'nicht überschrieben',
                       'Netzwerkprobleme', 'Reservekraftstoff'):
            # The first phrase allows natural sentence order around "Schiffsauswahl".
            if phrase == 'keine Schiffsauswahl':
                self.assertIn('Eine Schiffsauswahl gibt es hier nicht', text)
            else:
                self.assertIn(phrase, text)
        self.assertNotIn('Sprungtipp', text)

    def test_german_navigation_entry_saving_and_lifecycle(self):
        text = help_topic('planet_navigation', 'de').text
        for phrase in ('Öffne im Explorer', 'Eine Landung ist nicht erforderlich',
                       '★ Aktuellen Standort speichern', 'nicht das eingegebene Navigationsziel',
                       'System, Körper und Koordinaten', 'Name, Kategorie und Notiz',
                       'lokal und commanderbezogen', 'Abbrechen speichert nichts',
                       '◎ Zu den Koordinaten', 'erst nach Bestätigung',
                       'über Helper-Neustarts', 'laufende Sitzung', 'beendet das Ziel nicht',
                       'Navigation beenden', 'Status.json', 'Journal ergänzt',
                       'keine garantierte Genauigkeit', 'Navigations-HUD', 'Peilung'):
            self.assertIn(phrase, text)
        self.assertNotIn('Öffne in der Übersicht', text)

    def test_all_languages_match_structure_and_current_ui_labels(self):
        route_keys = ('ship_route', 'carrier_route', 'start_system', 'destination_system',
                      'ship_loadout_apply', 'ship_algorithm', 'ship_calculate_spansh',
                      'calculate_spansh', 'ship_current_system', 'ship_next_system',
                      'copy_next_system', 'ship_status_off_route', 'ship_status_complete', 'export_ctsvision')
        for language in HELP_LANGUAGES:
            ui = import_module(f'cmdrhelper.i18n.{language}').TRANSLATIONS
            for context in ('route_planner', 'planet_navigation'):
                with self.subTest(language=language, context=context):
                    text = help_topic(context, language).text
                    master = help_topic(context, 'de').text
                    self.assertEqual(re.findall(r'<(/?\w+)', text), re.findall(r'<(/?\w+)', master))
                    self.assertEqual(text.count('<h3>'), 12)
                    self.assertNotRegex(text, r'\{[^}]+\}')
                    self.assertNotIn('Sprungtipp', text)
                    if context == 'route_planner':
                        keys = ['route_planner.' + key for key in route_keys] + [
                            'nav.jump_tip', 'analysis.system_tab', 'analysis.history_tab']
                    else:
                        keys = ['planet_nav.title', 'planet_nav.enter_target', 'planet_nav.stop',
                                'favorites.save_surface', 'favorites.title', 'favorites.navigate',
                                'favorites.edit', 'favorites.delete']
                    for key in keys:
                        self.assertIn(ui[key], unescape(text))
                    if language != 'en':
                        english = help_topic(context, 'en').text
                        for paragraph in re.findall(r'<p>(.*?)</p>', english):
                            if len(paragraph.split()) > 8:
                                self.assertNotIn(paragraph, text)

    def test_no_duplicate_help_keys(self):
        root = Path(__file__).resolve().parents[1] / 'cmdrhelper' / 'help_content'
        for language in HELP_LANGUAGES:
            for node in ast.walk(ast.parse((root / f'{language}.py').read_text())):
                if isinstance(node, ast.Dict):
                    keys = [key.value for key in node.keys
                            if isinstance(key, ast.Constant) and isinstance(key.value, str)]
                    self.assertEqual(len(keys), len(set(keys)), language)

    def test_render_both_topics_four_languages_themes_and_fonts(self):
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        for language in ('de', 'en', 'fr', 'el'):
            for light, style in ((False, DARK_STYLESHEET), (True, LIGHT_STYLESHEET)):
                for size in (10, 18, 24):
                    self.app.setStyleSheet(style + f'\nQWidget {{ font-size: {size}pt; }}')
                    for context in ('route_planner', 'planet_navigation'):
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
                                capture = os.environ.get('CMDR_BLOCK5_CAPTURES')
                                if capture:
                                    dialog.grab().save(str(Path(capture) / f'{context}-{language}-{light}-{size}.png'))
                                scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
                                self.assertEqual(scroll.verticalScrollBar().value(), scroll.verticalScrollBar().maximum())
                            finally:
                                dialog.close()
                                dialog.deleteLater()
                                self.app.sendPostedEvents(None, QEvent.DeferredDelete)


class DocumentedShipProgressTests(unittest.TestCase):
    """Validate the behaviour described by the help using synthetic routes."""
    def setUp(self):
        self.copy = Mock()
        self.controller = ShipRouteController(self.copy)
        self.route = ShipRoute(tuple(ShipRouteJump(name, address) for name, address in
                                    [('Alpha', 1), ('Beta', 2), ('Gamma', 3), ('Delta', 4)]))
        self.controller.set_route(self.route, 'Alpha', 1)

    def test_load_manual_copy_matching_jump_and_duplicate(self):
        self.copy.assert_not_called()
        self.assertEqual(self.controller.next_jump.system, 'Beta')
        self.assertTrue(self.controller.copy_next())
        self.copy.assert_called_once_with('Beta')
        self.copy.reset_mock()
        self.assertTrue(self.controller.handle_position('Beta', 2, 'FSDJump'))
        self.copy.assert_called_once_with('Gamma')
        self.assertFalse(self.controller.handle_position('Beta', 2, 'FSDJump'))
        self.copy.assert_called_once_with('Gamma')

    def test_carrier_and_location_do_not_advance_or_copy(self):
        for event in ('CarrierJump', 'Location'):
            self.assertFalse(self.controller.handle_position('Beta', 2, event))
            self.assertEqual(self.route.reached_index, 0)
            self.assertEqual(self.controller.next_jump.system, 'Beta')
            self.copy.assert_not_called()

    def test_off_route_preserves_target_and_later_forward_match_resumes(self):
        self.assertFalse(self.controller.handle_position('Elsewhere', 99, 'FSDJump'))
        self.assertEqual(self.route.status, ShipRouteController.OFF_ROUTE)
        self.assertEqual(self.controller.next_jump.system, 'Beta')
        self.copy.assert_not_called()
        self.assertTrue(self.controller.handle_position('Gamma', 3, 'FSDJump'))
        self.assertEqual(self.route.status, ShipRouteController.ACTIVE)
        self.assertEqual(self.route.reached_index, 2)
        self.copy.assert_called_once_with('Delta')

    def test_completion_retains_route_and_does_not_touch_clipboard(self):
        self.controller.handle_position('Gamma', 3, 'FSDJump')
        self.copy.reset_mock()
        self.assertTrue(self.controller.handle_position('Delta', 4, 'FSDJump'))
        self.assertEqual(self.route.status, ShipRouteController.COMPLETE)
        self.assertIs(self.controller.route, self.route)
        self.assertIsNone(self.controller.next_jump)
        self.assertFalse(self.controller.copy_next())
        self.copy.assert_not_called()
