"""Navigation menu routing and localized help paths without live app data."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication, QMainWindow
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.help_content import help_topic
from cmdrhelper.ui.help_dialog import HelpDialog
import tests.test_context_help as context_tests


class NavigationMenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_menu_routes_to_existing_methods_in_both_themes_and_twelve_languages(self):
        self.addCleanup(set_language, get_language())
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        for language in _TRANSLATIONS:
            set_language(language)
            for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                with self.subTest(language=language, theme=style[:30]):
                    self.app.setStyleSheet(style)
                    window = MainWindow.__new__(MainWindow)
                    QMainWindow.__init__(window)
                    window._favorites_window = Mock()
                    window._planet_navigation_window = Mock()
                    window._planet_navigation_window.isVisible.return_value = False
                    with patch.object(window, '_ensure_planet_navigation_controller') as controller:
                        menu = window._navigation_menu()
                        menu.show()
                        self.assertFalse(window.favorites_button.isVisible())
                        window.navigation_menu_button.click()
                        self.assertTrue(window.favorites_button.isVisible())
                        self.assertTrue(window.planet_navigation_button.isVisible())
                        self.assertIn(tr('nav.navigation'), window.navigation_menu_button.text())
                        self.assertEqual(window.favorites_button.text(), tr('favorites.title'))
                        self.assertEqual(window.planet_navigation_button.text(), tr('planet_nav.title'))
                        window.favorites_button.click()
                        window._favorites_window.show.assert_called_once_with()
                        window._favorites_window.raise_.assert_called_once_with()
                        window._favorites_window.activateWindow.assert_called_once_with()
                        window.planet_navigation_button.click()
                        controller.assert_called_once_with()
                        window._planet_navigation_window.show.assert_called_once_with()
                        self.assertFalse(menu.grab().isNull())
                        window.navigation_menu_button.click()
                        self.assertFalse(window.favorites_button.isVisible())
                    menu.close()
                    menu.deleteLater()
                    window.deleteLater()

    def test_help_paths_and_existing_contexts_in_all_languages(self):
        for language, strings in _TRANSLATIONS.items():
            with self.subTest(language=language):
                nav = strings['nav.navigation']
                favorites = nav + ' → ' + strings['favorites.title']
                planet = nav + ' → ' + strings['planet_nav.title']
                explorer = help_topic('explorer', language).text
                navigation = help_topic('planet_navigation', language).text
                self.assertIn(favorites, explorer)
                self.assertIn(favorites, navigation)
                self.assertIn(planet, navigation)
                for text in (explorer, navigation):
                    for paragraph in text.split('</p>'):
                        if '★' in paragraph and 'Explorer' in paragraph:
                            self.fail('Obsolete Explorer access instruction: ' + paragraph)
                dialog = HelpDialog('planet_navigation', language=language)
                self.assertIn(planet, dialog.help_text.text())
                dialog.close()
                dialog.deleteLater()


class NavigationPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        context_tests.ContextHelpTests.setUp(self)

    def test_existing_pages_and_help_survive_menu_toggle(self):
        window = self.window
        before = list(window.nav_buttons)
        window.navigation_menu_button.click()
        for index in (window.PAGE_EXPLORER, window.PAGE_PP2, window.PAGE_OVERVIEW):
            window.nav_buttons[index].click()
            self.assertEqual(window.pages.currentIndex(), index)
            self.assertEqual(window.nav_buttons[index].objectName(), 'navActive')
            window.help_button.click()
            self.assertEqual(window._help_dialog.context, window.HELP_CONTEXTS[index])
            window._help_dialog.close()
        window.navigation_menu_button.click()
        self.assertEqual(window.nav_buttons, before)
        self.assertEqual(window.pages.count(), 12)
