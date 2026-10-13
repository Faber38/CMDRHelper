"""Presentation-only quick-favorite hint animation and existing hotkey visibility."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from PySide6.QtCore import QAbstractAnimation, QTimer
from PySide6.QtGui import QPalette
from PySide6.QtTest import QSignalSpy, QTest
from PySide6.QtWidgets import QApplication, QLabel
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
import tests.test_favorites as favorites_tests


class QuickFavoriteHintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        favorites_tests.FavoriteTests.setUp(self)
        self.addCleanup(set_language, get_language())
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())

    def view(self, binding=''):
        view, hotkey, backend, configure = favorites_tests.FavoriteTests.hint_view(self, binding)
        self.addCleanup(view.deleteLater)
        view.resize(900, 650)
        self.app.processEvents()
        return view, hotkey, backend, configure

    def test_three_nonblocking_cycles_then_steady_yellow(self):
        view, _, backend, configure = self.view()
        hint = view.quick_favorite_hint
        animation = hint._blink
        finished, loops = QSignalSpy(animation.finished), QSignalSpy(animation.currentLoopChanged)
        self.assertTrue(hint.isVisible())
        self.assertEqual(animation.state(), QAbstractAnimation.Running)
        self.assertEqual(animation.loopCount(), 3)
        self.assertEqual(animation.totalDuration(), 2100)
        ticked = []
        QTimer.singleShot(30, lambda: ticked.append(True))
        QTest.qWait(2300)
        self.assertTrue(ticked)
        self.assertEqual(finished.count(), 1)
        self.assertEqual([loops.at(i)[0] for i in range(loops.count())], [1, 2])
        self.assertEqual(animation.state(), QAbstractAnimation.Stopped)
        self.assertTrue(hint.isVisible())
        for label in hint.findChildren(QLabel):
            self.assertEqual(label.palette().color(QPalette.WindowText).name(), '#ffcc33')
            self.assertEqual(label.graphicsEffect().opacity(), 1.0)
        view.refresh()
        QTest.qWait(100)
        self.assertEqual(animation.state(), QAbstractAnimation.Stopped)
        self.assertEqual(finished.count(), 1)
        backend.register.assert_not_called()
        configure.assert_not_called()

    def test_assignment_during_animation_stops_it_and_removal_restarts(self):
        view, hotkey, _, _ = self.view()
        hint = view.quick_favorite_hint
        hint._blink.setCurrentTime(350)
        self.assertAlmostEqual(hint._text_effects[0].opacity(), 0.45)
        view.refresh()
        self.assertEqual(hint._blink.currentTime(), 350)
        self.assertTrue(hotkey.set_hotkey('Ctrl+F8'))
        self.assertFalse(hint.isVisible())
        self.assertEqual(hint._blink.state(), QAbstractAnimation.Stopped)
        self.assertTrue(all(effect.opacity() == 1.0 for effect in hint._text_effects))
        self.assertTrue(hotkey.set_hotkey(''))
        self.assertTrue(hint.isVisible())
        self.assertEqual(hint._blink.state(), QAbstractAnimation.Running)
        self.assertEqual(hint._blink.currentTime(), 0)
        hint._blink.setCurrentTime(350)
        view.hide()
        self.assertEqual(hint._blink.state(), QAbstractAnimation.Stopped)
        self.assertTrue(all(effect.opacity() == 1.0 for effect in hint._text_effects))

    def test_assigned_hotkey_never_starts_animation(self):
        view, _, _, _ = self.view('Ctrl+F8')
        self.assertFalse(view.quick_favorite_hint.isVisible())
        self.assertEqual(view.quick_favorite_hint._blink.state(), QAbstractAnimation.Stopped)

    def test_twelve_languages_theme_changes_geometry_and_focus(self):
        for language in _TRANSLATIONS:
            set_language(language)
            view, _, _, _ = self.view()
            hint = view.quick_favorite_hint
            labels = hint.findChildren(QLabel)
            self.assertEqual([label.text() for label in labels],
                             [tr('quick_favorite.title'), tr('quick_favorite.hint')])
            self.assertIsNone(view.quick_favorite_setup_button.graphicsEffect())
            for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                with self.subTest(language=language, theme=style[:20]):
                    self.app.setStyleSheet(style)
                    view.hide()
                    view.show()
                    view.search.setFocus()
                    self.app.processEvents()
                    focus = self.app.focusWidget()
                    # Offscreen windows may have no native focus after reopening.
                    self.assertIs(view.focusWidget(), view.search)
                    before = [widget.geometry() for widget in (view, hint, *labels)]
                    for cycle in range(3):
                        hint._blink.setCurrentTime(cycle * 700 + 350)
                        self.assertTrue(all(abs(label.graphicsEffect().opacity() - 0.45) < 0.001
                                            for label in labels))
                        self.assertEqual([widget.geometry() for widget in (view, hint, *labels)], before)
                        self.assertIs(self.app.focusWidget(), focus)
                        self.assertIs(view.focusWidget(), view.search)
                        for label in labels:
                            self.assertEqual(label.palette().color(QPalette.WindowText).name(), '#ffcc33')
                    hint._blink.setCurrentTime(2100)
                    self.assertTrue(all(label.graphicsEffect().opacity() == 1.0 for label in labels))
                    self.assertEqual([widget.geometry() for widget in (view, hint, *labels)], before)
                    self.assertIs(self.app.focusWidget(), focus)
                    self.assertIs(view.focusWidget(), view.search)
            view.close()
