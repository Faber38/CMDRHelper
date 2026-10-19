"""Overview controls with real selection state and isolated settings/database."""
import unittest

from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication, QMainWindow
from cmdrhelper import i18n
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.commander_view import CommanderView
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests import test_commander_selection_mode as selection


def overview(state):
    window = MainWindow.__new__(MainWindow)
    QMainWindow.__init__(window)
    window.state = state
    window.setCentralWidget(window._overview())
    return window


class OverviewFollowTests(unittest.TestCase):
    setUp = selection.SelectionModeTests.setUp
    restart = selection.SelectionModeTests.restart

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def views(self, state):
        window, commander = overview(state), CommanderView(state)
        for widget in (window, commander):
            self.addCleanup(widget.deleteLater)
            self.addCleanup(widget.close)
        return window, commander

    def test_start_toggle_sync_manual_selection_and_restart(self):
        for enabled in (True, False):
            with self.subTest(enabled=enabled):
                self.settings.setValue('commander_view/follow_live', enabled)
                self.settings.setValue('commander_view/viewed_commander_id', self.a)
                state = self.restart()
                state.resolve_viewed_commander()
                window, commander = self.views(state)
                checkbox = window.overview_follow_live_checkbox
                self.assertEqual(checkbox.isChecked(), enabled)
                self.assertEqual(commander.follow_live_checkbox.isChecked(), enabled)
                self.assertEqual(window.overview_manual_commander_hint.isHidden(), enabled)
                state.select_viewed_commander(self.a)
                self.assertFalse(checkbox.isChecked())
                spy = QSignalSpy(state.viewedCommanderChanged)
                checkbox.click()
                self.assertEqual(state.viewed_commander_id, self.b)
                self.assertEqual(spy.count(), 1)
                self.assertTrue(commander.follow_live_checkbox.isChecked())
                self.assertTrue(self.restart().follow_live_commander)
                checkbox.click()
                self.assertEqual(state.viewed_commander_id, self.b)
                self.assertFalse(commander.follow_live_checkbox.isChecked())
                self.assertFalse(self.restart().follow_live_commander)
                commander.follow_live_checkbox.click()
                self.assertTrue(checkbox.isChecked())
                commander.follow_live_checkbox.click()
                self.assertFalse(checkbox.isChecked())

    def test_unknown_fid_and_no_game_keep_manual_commander(self):
        for fid, cid, status in (('', None, 'unknown'), ('UNKNOWN', self.b, 'unknown')):
            state = self.restart()
            state.select_viewed_commander(self.a)
            state.commander_fid, state.commander_id = fid, cid
            state._journal_index_sessions[-1]['attribution_status'] = status
            window, _ = self.views(state)
            window.overview_follow_live_checkbox.click()
            self.assertTrue(state.follow_live_commander)
            self.assertEqual(state.viewed_commander_id, self.a)

    def test_all_translations_themes_and_sizes(self):
        self.addCleanup(i18n.set_language, i18n.get_language())
        for language, translations in i18n._TRANSLATIONS.items():
            i18n.set_language(language)
            self.assertIn('overview.follow_live', translations)
            self.assertIn('overview.manual_commander_hint', translations)
            state = self.restart()
            state.select_viewed_commander(self.a)
            window, _ = self.views(state)
            for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                window.setStyleSheet(theme)
                for width in (800, 1280):
                    with self.subTest(language=language, width=width):
                        window.resize(width, 850)
                        window.show()
                        self.app.processEvents()
                        checkbox = window.overview_follow_live_checkbox
                        hint = window.overview_manual_commander_hint
                        self.assertTrue(checkbox.isVisible())
                        self.assertTrue(hint.isVisible())
                        self.assertGreaterEqual(checkbox.width(), checkbox.sizeHint().width())
                        self.assertTrue(checkbox.parentWidget().rect().contains(checkbox.geometry()))
                        self.assertTrue(hint.parentWidget().rect().contains(hint.geometry()))
                        self.assertEqual(window.width(), width)
            window.close()

    def test_manual_hint_blinks_ten_seconds_without_layout_movement(self):
        state = self.restart()
        state.select_viewed_commander(self.a)
        window, _ = self.views(state)
        window.resize(900, 850)
        window.show()
        self.app.processEvents()
        hint = window.overview_manual_commander_hint
        geometry = hint.geometry()
        effect = window._overview_follow_hint_effect
        self.assertTrue(window._overview_follow_blink_timer.isActive())
        QTest.qWait(600)
        self.assertEqual(effect.opacity(), 0)
        self.assertEqual(hint.geometry(), geometry)
        # Repeated identity refreshes must not restart the ten-second period.
        remaining = window._overview_follow_blink_end.remainingTime()
        state.viewedCommanderChanged.emit(state.viewed_commander_id)
        self.assertLessEqual(window._overview_follow_blink_end.remainingTime(), remaining)
        QTest.qWait(10_000)
        self.assertFalse(window._overview_follow_blink_timer.isActive())
        self.assertEqual(effect.opacity(), 1)
        self.assertFalse(hint.isHidden())
        window.overview_follow_live_checkbox.click()
        self.assertTrue(hint.isHidden())
        window.overview_follow_live_checkbox.click()
        self.assertTrue(window._overview_follow_blink_timer.isActive())
        window.overview_follow_live_checkbox.click()
        self.assertFalse(window._overview_follow_blink_timer.isActive())
        self.assertFalse(window._overview_follow_blink_end.isActive())
