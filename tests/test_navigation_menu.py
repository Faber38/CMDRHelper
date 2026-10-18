"""Integrated navigation, with isolated favorites data and no live services."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
import json
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from unittest.mock import patch
from PySide6.QtCore import QCoreApplication, QEvent, QTimer, SIGNAL, Qt
from PySide6.QtTest import QTest
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

    def test_detach_return_close_and_live_updates_keep_single_navigation(self):
        self.state.journal_folder = self.root
        status = dict(event='Status', timestamp=datetime.now(timezone.utc).isoformat(),
                      Flags=1 << 21, Flags2=0, Latitude=10, Longitude=20,
                      Heading=51, PlanetRadius=1000000, BodyName='Sol 1')
        status_path = self.root / 'Status.json'
        status_path.write_text(json.dumps(status))
        window = self.build_window()
        window._show_planet_navigation()
        controller = window._planet_navigation_controller
        controller.set_target(11, 21, 'Sol 1', 'Destination')
        view, dock = window.planet_navigation_view, window.navigation_dock
        target = controller.target
        timers = window.findChildren(QTimer)
        tail = controller.tail
        receivers = controller.receivers(SIGNAL('changed(PyObject)'))
        timer_receivers = controller.timer.receivers(SIGNAL('timeout()'))
        age_receivers = view._age_timer.receivers(SIGNAL('timeout()'))
        self.assertIsNone(dock.window)
        for cycle in range(3):
            before = {key: label.text() for key, label in view.values.items()}
            dock.button.click()
            self.app.processEvents()
            shell = dock.window
            self.assertTrue(shell.isWindow())
            self.assertTrue(shell.windowFlags() & Qt.WindowStaysOnTopHint)
            self.assertFalse(shell.isModal())
            self.assertTrue(shell.isVisible())
            self.assertIs(shell.scroll.widget(), view)
            self.assertIs(window.navigation_tabs.widget(1).widget(), dock.placeholder)
            self.assertEqual(before, {key: label.text() for key, label in view.values.items()})
            self.assertEqual(controller.target, target)
            shell.resize(620 + cycle * 10, 710)
            self.app.processEvents()
            self.assertEqual(shell.width(), 620 + cycle * 10)
            window._show_favorites()
            window._show_page(window.PAGE_EXPLORER)
            self.assertTrue(view.isVisible())
            self.assertTrue(controller.timer.isActive())
            self.assertTrue(view._age_timer.isActive())
            status.update(Latitude=10 + (cycle + 1) / 10, Heading=60 + cycle)
            status_path.write_text(json.dumps(status))
            QTest.qWait(320)
            self.assertEqual(controller.state.snapshot.heading, 60 + cycle)
            self.assertNotEqual(before['distance'], view.values['distance'].text())
            self.assertEqual(controller.target, target)
            updated = {key: label.text() for key, label in view.values.items()}
            if cycle == 1:
                shell.close()
            else:
                dock.button.click()
            self.app.processEvents()
            self.assertFalse(dock.detached)
            self.assertFalse(shell.isVisible())
            self.assertIs(window.navigation_tabs.widget(1).widget(), view)
            self.assertEqual(window.pages.currentIndex(), window.PAGE_NAVIGATION)
            self.assertEqual(window.navigation_tabs.currentIndex(), 1)
            self.assertEqual(updated, {key: label.text() for key, label in view.values.items()})
            self.assertEqual(window.findChildren(QTimer), timers)
            self.assertIs(controller.tail, tail)
            self.assertEqual(controller.receivers(SIGNAL('changed(PyObject)')), receivers)
            self.assertEqual(controller.timer.receivers(SIGNAL('timeout()')), timer_receivers)
            self.assertEqual(view._age_timer.receivers(SIGNAL('timeout()')), age_receivers)
            self.assertEqual(controller._consumers, {'navigation_window'})
        self.assertIn(dock.geometry_key, self.state.values)
        dock.detach()
        self.assertIs(dock.window, shell)
        self.assertEqual(shell.width(), 640)
        with patch.object(window.favorites_view, 'save_surface') as save:
            view.save_location_button.click()
            save.assert_called_once_with(controller)

    def test_detached_favorite_action_and_shutdown(self):
        self.store.save(1, favorite_tests.FavoriteTests.record(self))
        window = self.build_window()
        dock = window.navigation_dock
        dock.detach()
        self.assertIsNone(dock.window.windowHandle().transientParent())
        window.showMinimized()
        self.app.processEvents()
        self.assertTrue(dock.window.isVisible())
        self.assertFalse(dock.window.isMinimized())
        dock.window.showMinimized()
        window.showNormal()
        self.app.processEvents()
        self.assertTrue(dock.window.isMinimized())
        dock.window.showNormal()
        window._show_favorites()
        window.favorites_view.list.setCurrentRow(0)
        window.favorites_view.coordinates_button.click()
        controller = window._planet_navigation_controller
        self.assertTrue(dock.detached)
        self.assertTrue(dock.view.isVisible())
        self.assertEqual((controller.target.latitude, controller.target.longitude), (0, 0))
        window.close()
        self.assertFalse(dock.window.isVisible())
        self.assertFalse(controller.timer.isActive())
        self.assertFalse(dock.view._age_timer.isActive())
        self.assertFalse(controller._consumers)
        self.assertIsNotNone(controller.target)
        self.assertIn(dock.geometry_key, self.state.values)
        dock.shutdown()  # aboutToQuit after the main window's close is harmless.
        dock.detach()
        self.assertFalse(dock.window.isVisible())

    def test_quit_cleanup_preserves_other_controller_consumers(self):
        window = self.build_window()
        dock = window.navigation_dock
        controller = window._planet_navigation_controller
        controller.consumer_acquire('navigation_hud')
        dock.detach()
        dock.shutdown()  # The same slot is connected to QApplication.aboutToQuit.
        self.assertFalse(dock.window.isVisible())
        self.assertFalse(dock.view.isVisible())
        self.assertEqual(controller._consumers, {'navigation_hud'})
        controller.consumer_release('navigation_hud')

    def test_detached_themes_languages_geometry_and_help(self):
        for language in _TRANSLATIONS:
            set_language(language)
            for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                with self.subTest(language=language, theme=theme[:30]):
                    self.app.setStyleSheet(theme)
                    window = self.build_window()
                    dock = window.navigation_dock
                    self.assertFalse(dock.detached)
                    self.assertEqual(dock.button.text(), tr('planet_nav.detach'))
                    dock.detach()
                    shell = dock.window
                    shell.resize(380, 420)
                    self.app.processEvents()
                    self.assertEqual(shell.size().width(), 380)
                    self.assertEqual(dock.button.text(), tr('planet_nav.attach'))
                    self.assertGreaterEqual(dock.button.width(), dock.button.sizeHint().width())
                    self.assertTrue(dock.button.isVisible())
                    self.assertFalse(shell.grab().isNull())
                    color = dock.view.palette().color(QPalette.Text).name()
                    self.assertIn('color:' + color, dock.view.legend.text())
                    for key in ('detach', 'attach'):
                        self.assertIn(tr('planet_nav.' + key), help_topic('planet_navigation', language).text)
                    dock.attach()
                    window.close()
                    window.deleteLater()
                    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_detached_window_can_move_to_second_screen(self):
        screens = self.app.screens()
        if len(screens) < 2:
            self.skipTest('A second monitor is not available in this Qt environment')
        window = self.build_window()
        dock = window.navigation_dock
        dock.detach()
        shell = dock.window
        shell.windowHandle().setScreen(screens[1])
        shell.move(screens[1].availableGeometry().topLeft())
        self.app.processEvents()
        self.assertEqual(shell.screen(), screens[1])
        dock.attach()
        dock.detach()
        self.assertEqual(shell.screen(), screens[1])

    def test_geometry_restored_but_new_session_starts_integrated(self):
        window = self.build_window()
        dock = window.navigation_dock
        self.state.settings.setValue(dock.geometry_key, 'invalid legacy geometry')
        dock.detach()
        dock.window.resize(610, 680)
        dock.window.move(30, 40)
        self.app.processEvents()
        dock.attach()
        geometry = dock.window.geometry()
        window.close()
        next_window = self.build_window()
        next_dock = next_window.navigation_dock
        self.assertIsNone(next_dock.window)
        self.assertIs(next_dock.home.widget(), next_dock.view)
        next_dock.detach()
        self.app.processEvents()
        self.assertEqual(next_dock.window.geometry(), geometry)

    def test_application_quit_closes_detached_window(self):
        # A separate event loop verifies actual aboutToQuit delivery without
        # terminating the QApplication shared by the rest of this test suite.
        script = textwrap.dedent('''
            from PySide6.QtCore import QTimer
            from tests.test_navigation_menu import NavigationMenuTests
            case = NavigationMenuTests()
            case.setUpClass()
            case.setUp()
            window = case.build_window()
            dock = window.navigation_dock
            dock.detach()
            controller = window._planet_navigation_controller
            controller.set_target(12, 34, 'Sol 1', 'Destination')
            QTimer.singleShot(0, case.app.quit)
            case.app.exec()
            assert dock.stopping
            assert not dock.window.isVisible()
            assert not dock.view._age_timer.isActive()
            assert not controller.timer.isActive()
            assert (controller.target.latitude, controller.target.longitude) == (12, 34)
            assert dock.geometry_key in case.state.values
            case.doCleanups()
        ''')
        result = subprocess.run([sys.executable, '-c', script], capture_output=True,
                                text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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
