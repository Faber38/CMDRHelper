"""Integrated navigation, with isolated favorites data and no live services."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from unittest.mock import patch
from PySide6.QtCore import QCoreApplication, QEvent, SIGNAL
from shiboken6 import isValid
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget, QWidget
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.help_content import help_topic
from cmdrhelper.ui.help_dialog import HelpDialog
import tests.test_context_help as context_tests
import tests.test_favorites as favorite_tests


class NavigationMenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        favorite_tests.FavoriteTests.setUp(self)
        self.addCleanup(set_language, get_language())
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())

    def build_window(self):
        window = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(window)
        window.state = self.state
        window._planet_navigation_controller = None
        window._quick_favorite_hotkey = None
        window._help_dialog = None
        window.pages = QStackedWidget()
        window.nav_buttons = []
        for index in range(window.PAGE_NAVIGATION):
            window.pages.addWidget(QWidget())
            window._nav(str(index), index).setParent(window)
        window.navigation_menu_button = window._nav(tr('nav.navigation'), window.PAGE_NAVIGATION)
        window.navigation_menu_button.setParent(window)
        window.pages.addWidget(window._navigation_page())
        window.setCentralWidget(window.pages)
        def cleanup():
            if isValid(window):
                window.close()
                window.deleteLater()
        self.addCleanup(cleanup)
        window.resize(760, 560)
        window.show()
        return window

    def test_tabs_in_both_themes_and_twelve_languages_at_narrow_width(self):
        self.assertEqual(len(_TRANSLATIONS), 12)
        for language in _TRANSLATIONS:
            set_language(language)
            for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                with self.subTest(language=language, theme=style[:30]):
                    self.app.setStyleSheet(style)
                    window = self.build_window()
                    before = set(self.app.topLevelWidgets())
                    window.navigation_menu_button.click()
                    self.assertEqual(window.pages.currentIndex(), window.PAGE_NAVIGATION)
                    self.assertEqual(window.navigation_menu_button.objectName(), 'navActive')
                    self.assertFalse(window.navigation_menu_button.isCheckable())
                    tabs = window.navigation_tabs
                    self.assertEqual(tabs.currentIndex(), 0)
                    self.assertEqual(tabs.tabText(0), tr('favorites.title'))
                    self.assertEqual(tabs.tabText(1), tr('planet_nav.title'))
                    self.assertFalse(window.favorites_view.isWindow())
                    self.assertFalse(window.planet_navigation_view.isWindow())
                    legend_color = window.planet_navigation_view.palette().color(QPalette.Text).name()
                    self.assertIn("color:" + legend_color, window.planet_navigation_view.legend.text())
                    window.resize(440, 400)
                    for index in (1, 0, 1):
                        tabs.setCurrentIndex(index)
                        self.app.processEvents()
                        self.assertEqual(window.width(), 440)
                        scroll = tabs.currentWidget()
                        view = scroll.widget()
                        self.assertTrue(view.isVisible())
                        self.assertFalse(scroll.grab().isNull())
                        # Oversized contents remain reachable, rather than growing the main window.
                        self.assertLessEqual(view.width(), scroll.viewport().width() + scroll.horizontalScrollBar().maximum())
                        self.assertLessEqual(view.height(), scroll.viewport().height() + scroll.verticalScrollBar().maximum())
                    self.assertEqual(set(self.app.topLevelWidgets()), before)
                    window.close()
                    window.deleteLater()
                    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_return_calls_settings_signals_and_commander_switch(self):
        record = favorite_tests.FavoriteTests.record(self)
        self.store.save(1, record)
        window = self.build_window()
        view, planet = window.favorites_view, window.planet_navigation_view
        controller = window._planet_navigation_controller
        window._show_favorites()
        receivers = controller.receivers(SIGNAL("changed(PyObject)"))
        view.search.setText('Zero')
        view.distance_filter.setChecked(True)
        view.max_distance.setValue(250)
        saved = dict(self.state.values)
        self.state.settings.setValue('planet_navigation/geometry', b'legacy geometry')
        # Geometry of an embedded widget must never overwrite the old preference.
        for _ in range(4):
            self.assertIs(window._favorite_navigator(), controller)
            self.assertEqual(window.navigation_tabs.currentIndex(), 1)
            self.assertTrue(planet._age_timer.isActive())
            window._show_page(window.PAGE_EXPLORER)
            self.assertFalse(planet._age_timer.isActive())
            self.assertFalse(controller.timer.isActive())
            window.navigation_menu_button.click()
            self.assertEqual(window.navigation_tabs.currentIndex(), 1)
            window._show_favorites()
            self.assertFalse(planet._age_timer.isActive())
            self.assertIs(window.favorites_view, view)
            self.assertIs(window.planet_navigation_view, planet)
            self.assertEqual(view.search.text(), 'Zero')
            self.assertEqual(controller.receivers(SIGNAL("changed(PyObject)")), receivers)
        with patch.object(view, 'save_surface') as save:
            window._show_planet_navigation()
            planet.save_location_button.setEnabled(True)
            planet.save_location_button.click()
            save.assert_called_once_with(controller)
        self.assertEqual(self.state.values['planet_navigation/geometry'], b'legacy geometry')
        for key, value in saved.items():
            self.assertEqual(self.state.values[key], value)
        window._show_favorites()
        view.distance_filter.setChecked(False)
        self.assertEqual(view.list.count(), 1)
        self.state.commander_id = 2
        self.state.commander_fid = 'F2'
        self.state.commanderIdentityChanged.emit(2, 'F2', 'Second')
        self.assertEqual(view.list.count(), 0)
        self.assertEqual(len(self.store.list(1)), 1)
        self.state.commander_id = 1
        self.state.commander_fid = 'F1'
        self.state.commanderIdentityChanged.emit(1, 'F1', 'First')
        self.assertEqual(view.list.count(), 1)

    def test_favorite_navigation_action_keeps_target_across_page_changes(self):
        self.store.save(1, favorite_tests.FavoriteTests.record(self))
        window = self.build_window()
        window._show_favorites()
        view = window.favorites_view
        view.list.setCurrentRow(0)
        with patch.object(window, 'raise_') as raise_window, patch.object(window, 'activateWindow') as activate:
            view.coordinates_button.click()
            self.assertEqual(window.pages.currentIndex(), window.PAGE_NAVIGATION)
            self.assertEqual(window.navigation_tabs.currentIndex(), 1)
            controller = window._planet_navigation_controller
            target = controller.target
            self.assertEqual((target.latitude, target.longitude, target.name), (0, 0, 'Zero'))
            self.assertEqual(window.planet_navigation_view.target_name_label.text(), 'Zero')
            window._show_page(window.PAGE_EXPLORER)
            window._show_favorites()
            window._show_planet_navigation()
            self.assertIs(controller.target, target)
            raise_window.assert_not_called()
            activate.assert_not_called()
        self.state.commander_id = 2
        self.state.commander_fid = 'F2'
        self.state.commanderIdentityChanged.emit(2, 'F2', 'Second')
        self.assertIsNone(controller.target)
        self.assertEqual(view.list.count(), 0)

    def test_help_paths_and_existing_contexts_in_all_languages(self):
        for language, strings in _TRANSLATIONS.items():
            with self.subTest(language=language):
                favorites = strings['nav.navigation'] + ' → ' + strings['favorites.title']
                planet = strings['nav.navigation'] + ' → ' + strings['planet_nav.title']
                explorer = help_topic('explorer', language).text
                navigation = help_topic('planet_navigation', language).text
                for text in (explorer, navigation):
                    self.assertIn(favorites, text)
                    self.assertIn(planet, text)
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

    def test_existing_pages_and_help_survive_navigation_changes(self):
        window = self.window
        before = list(window.nav_buttons)
        window.navigation_menu_button.click()
        for index in (window.PAGE_EXPLORER, window.PAGE_PP2, window.PAGE_OVERVIEW, window.PAGE_NAVIGATION):
            window.nav_buttons[index].click()
            self.assertEqual(window.pages.currentIndex(), index)
            self.assertEqual(window.nav_buttons[index].objectName(), 'navActive')
            window.help_button.click()
            self.assertEqual(window._help_dialog.context, window.HELP_CONTEXTS[index])
            window._help_dialog.close()
        self.assertEqual(window.nav_buttons, before)
        self.assertEqual(window.pages.count(), 13)
        self.assertFalse(hasattr(window, 'favorites_button'))
        self.assertFalse(hasattr(window, 'planet_navigation_button'))
