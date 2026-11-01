"""Responsive shortcut presentation with isolated settings and no native hotkeys."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock
import unittest

from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMainWindow, QScrollArea, QBoxLayout
from cmdrhelper.global_hotkey import GlobalHotkey
from cmdrhelper.shortcuts import ACTIONS, ShortcutManager
from cmdrhelper.ui.shortcut_settings import ShortcutSettings
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language


class ShortcutLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_languages_themes_resize_and_binding_labels(self):
        language = get_language()
        self.addCleanup(set_language, language)
        with TemporaryDirectory() as tmp:
            for theme, style in [('dark', DARK_STYLESHEET), ('light', LIGHT_STYLESHEET)]:
                for lang in _TRANSLATIONS:
                    with self.subTest(theme=theme, language=lang):
                        set_language(lang)
                        window = QMainWindow()
                        window.setStyleSheet(style)
                        settings = QSettings(str(Path(tmp) / (theme+lang+'.ini')), QSettings.IniFormat)
                        hotkey = GlobalHotkey(settings, backend_factory=lambda callback: Mock())
                        manager = ShortcutManager(window, settings, hotkey, {a: Mock() for a in ACTIONS})
                        manager.load()
                        editor = ShortcutSettings(manager)
                        scroll = QScrollArea()
                        scroll.setWidgetResizable(True)
                        scroll.setWidget(editor)
                        window.setCentralWidget(scroll)
                        try:
                            window.show()
                            for width, expected in [(360, 1), (600, 2), (850, 3), (1100, 3),
                                                    (1600, 3), (600, 2), (360, 1), (850, 3)]:
                                window.resize(width, 700)
                                QTest.qWait(150)
                                self.assertEqual(scroll.horizontalScrollBar().maximum(), 0)
                                grid = editor.action_grid
                                if expected is not None:
                                    self.assertEqual(grid.columns, expected)
                                self.check_geometry(editor)
                                print(f'MEASURE {theme} {lang} 12px window={window.width()} '
                                      f'available={grid.width()} columns={grid.columns} '
                                      f'card={grid.cards[0].width()} right_free='
                                      f'{grid.width() - max(c.geometry().right()+1 for c in grid.cards)}')
                                color = '#FFCC33' if theme == 'dark' else '#1565C0'
                                for label, _, _ in editor.rows.values():
                                    self.assertIn('color: ' + color, label.text())
                            card_width = editor.action_grid.preferred_card_width()
                            chrome = window.width() - editor.action_grid.width()
                            # Exercise both sides of the measured two/three-column boundary.
                            for columns in (2, 3):
                                threshold = columns * card_width + (columns - 1) * 8
                                for delta in (-20, 20):
                                    window.resize(threshold + chrome + delta, 700)
                                    QTest.qWait(150)
                                    self.assertEqual(editor.action_grid.columns, columns - int(delta < 0))
                                    self.assertEqual(scroll.horizontalScrollBar().maximum(), 0)
                                    self.check_geometry(editor)
                            self.assertTrue(manager.set_binding('quit', 'Ctrl+Q'))
                            self.assertTrue(editor.rows['quit'][1].isEnabled())
                            self.assertTrue(editor.rows['quit'][2].isEnabled())
                            self.assertIn('Q', editor.rows['quit'][0].text())
                            self.assertTrue(manager.set_binding('quit', 'Ctrl+F8'))
                            QTest.qWait(150)
                            self.check_geometry(editor)
                            editor.rows['quit'][2].click()
                            self.assertFalse(manager.bindings['quit'])
                            print(f'LAYOUT {theme} {lang}: card={card_width}, grid thresholds={2*card_width+8}/{3*card_width+16}, window overhead={chrome}')
                            window.setStyleSheet(style + '\nQWidget { font-size: 18px; }')
                            for width in (360, 600, 850, 1100, 1600, 600, 360):
                                window.resize(width, 700)
                                QTest.qWait(150)
                                self.assertEqual(scroll.horizontalScrollBar().maximum(), 0)
                                self.check_geometry(editor)
                                print(f'MEASURE {theme} {lang} 18px window={window.width()} '
                                      f'available={grid.width()} columns={grid.columns} '
                                      f'card={grid.cards[0].width()} right_free='
                                      f'{grid.width() - max(c.geometry().right()+1 for c in grid.cards)}')
                            window.setStyleSheet(LIGHT_STYLESHEET if theme == 'dark' else DARK_STYLESHEET)
                            QTest.qWait(150)
                            color = '#1565C0' if theme == 'dark' else '#FFCC33'
                            for label, _, _ in editor.rows.values():
                                self.assertIn('color: ' + color, label.text())
                        finally:
                            hotkey.close()
                            window.close()
                            window.deleteLater()
                            self.app.processEvents()

    def check_geometry(self, editor):
        grid = editor.action_grid
        self.assertEqual(len(grid.cards), 6)
        self.assertEqual(min(card.x() for card in grid.cards), 0)
        self.assertEqual(len({card.x() for card in grid.cards}), grid.columns)
        self.assertEqual(len({card.y() for card in grid.cards}), (6 + grid.columns - 1) // grid.columns)
        for card in grid.cards:
            self.assertGreaterEqual(card.x(), 0)
            self.assertLessEqual(card.geometry().right(), grid.width())
            self.assertLessEqual(card.geometry().bottom(), grid.height())
            self.assertLessEqual(card.width(), grid.preferred_card_width())
        if grid.width() > 3 * grid.preferred_card_width() + 16:
            self.assertGreater(grid.width() - max(c.geometry().right()+1 for c in grid.cards), 0)
        for index, card in enumerate(grid.cards):
            if index >= grid.columns:
                above = grid.cards[index - grid.columns]
                self.assertEqual(card.y() - above.geometry().bottom() - 1, 8)
            if index % grid.columns:
                previous = grid.cards[index - 1]
                self.assertEqual(card.x() - previous.geometry().right() - 1, 8)
        for label, edit, remove in editor.rows.values():
            self.assertGreaterEqual(label.height(), label.heightForWidth(label.width()))
            for button in (edit, remove):
                self.assertEqual(button.width(), button.sizeHint().width())
            self.assertEqual(edit.x(), label.x())
            controls = edit.parentWidget().layout().itemAt(1).layout()
            if controls.direction() == QBoxLayout.LeftToRight:
                self.assertEqual(remove.x() - edit.geometry().right() - 1, controls.spacing())
                self.assertEqual(edit.y(), remove.y())
            else:
                self.assertEqual(remove.x(), edit.x())
        for button in (editor.global_settings.edit, editor.global_settings.remove, editor.reset_button):
            self.assertGreaterEqual(button.width(), button.sizeHint().width())
