"""Real popup constructors/formatting with synthetic data and memory settings."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from copy import deepcopy
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QMainWindow
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language
from cmdrhelper.ui.main_window import ExplorerLiveListWindow, MainWindow
from tests.test_live_window_focus import _Settings


class ExplorerRefreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.addCleanup(set_language, get_language())

    def main(self, bodies):
        main = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(main)
        main.state = SimpleNamespace(settings=_Settings(), system='Synthetic',
                                     system_bodies=bodies)
        main._explorer_value_live_window = None
        main._explorer_bio_live_window = None
        main._explorer_live_system = 'Synthetic'
        main.show()
        self.addCleanup(main.deleteLater)
        self.addCleanup(main.close)
        return main

    def body(self, name='Synthetic 1', value=300_000, **fields):
        return dict(name=name, body_type='Planet', possible_value=value, **fields)

    def test_all_languages_numeric_order_and_simultaneous_bio_geo(self):
        for language in _TRANSLATIONS:
            with self.subTest(language=language):
                set_language(language)
                main = self.main([
                    self.body(biological_signals=1, geological_signals=2),
                    self.body('Synthetic 2', 1_200_000),
                    self.body('Synthetic 3', 250_000),
                ])
                main._refresh_explorer_live_windows()
                value, bio = main._explorer_value_live_window, main._explorer_bio_live_window
                self.assertTrue(value.isVisible())
                self.assertTrue(bio.isVisible())
                self.assertEqual([value.table.item(r, 2).text() for r in range(3)],
                                 [MainWindow._format_reward(n) for n in (1_200_000, 300_000, 250_000)])
                self.assertEqual(value.table.item(1, 2).text(),
                                 '300.000 Cr' if language == 'de' else '300,000 Cr')
                text = ' '.join(bio.table.cellWidget(r, 1).text()
                                for r in range(bio.table.rowCount()) if bio.table.cellWidget(r, 1))
                self.assertIn('BIO', text)
                self.assertIn('GEO', text)
                main.close()

    def test_no_qualifying_bodies_and_system_change_do_not_show_popups(self):
        main = self.main([self.body(value=199_999),
                          self.body('Synthetic 2', self_mapped=True, geological_signals=2)])
        main._refresh_explorer_live_windows()
        self.assertFalse(main._explorer_value_live_window.isVisible())
        self.assertFalse(main._explorer_bio_live_window.isVisible())
        main.state.system_bodies = [self.body(biological_signals=1, geological_signals=1)]
        main._refresh_explorer_live_windows()
        self.assertTrue(main._explorer_value_live_window.isVisible())
        self.assertTrue(main._explorer_bio_live_window.isVisible())
        main.state.system = 'Next'
        main.state.system_bodies = []
        for _ in range(2):
            main._refresh_explorer_live_windows()
            self.assertFalse(main._explorer_value_live_window.isVisible())
            self.assertFalse(main._explorer_bio_live_window.isVisible())

    def test_failed_initial_and_updated_refresh_retry_identical_data(self):
        set_language('en')
        main = self.main([self.body(biological_signals=1, geological_signals=1)])
        for amount in (300_000, 1_200_000):
            with self.subTest(amount=amount):
                old_key = deepcopy(getattr(main, '_explorer_live_render_key', None))
                main.state.system_bodies[0]['possible_value'] = amount
                with patch.object(ExplorerLiveListWindow, 'set_rows', side_effect=RuntimeError('synthetic failure')):
                    with self.assertRaisesRegex(RuntimeError, 'synthetic failure'):
                        main._refresh_explorer_live_windows()
                self.assertEqual(getattr(main, '_explorer_live_render_key', None), old_key)
                main._refresh_explorer_live_windows()
                self.assertNotEqual(main._explorer_live_render_key, old_key)
                self.assertEqual(main._explorer_value_live_window.table.item(0, 2).text(),
                                 MainWindow._format_reward(amount))
                self.assertTrue(main._explorer_bio_live_window.isVisible())
