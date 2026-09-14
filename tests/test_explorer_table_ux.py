"""Exercise the real Explorer tables, mouse gestures and QSettings round trips."""
import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PySide6.QtCore import QPoint, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget

from cmdrhelper.i18n import get_language, set_language
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.ui.system_view import SystemMapWidget


class ExplorerWindow(MainWindow):
    def __init__(self, settings, theme='dark'):
        QMainWindow.__init__(self)
        self.state = SimpleNamespace(settings=settings, system_bodies=[], system='Test',
            database=SimpleNamespace(learned_bio_values=lambda: {'Zulu': 900, 'Äther': 20, 'Beta': 10000}))
        self.ui_theme = theme
        self._quick_favorite_hotkey = None
        with patch('cmdrhelper.ui.favorites_view.FavoritesView', side_effect=lambda *a, **kw: QWidget()):
            self.setCentralWidget(self._explorer())


class ExplorerTableUxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / 'ui.ini')
        self.settings = QSettings(self.path, QSettings.IniFormat)
        self.addCleanup(set_language, get_language())
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        set_language('de')
        self.window = self.make_window()

    def make_window(self, settings=None, theme='dark'):
        window = ExplorerWindow(settings or self.settings, theme)
        window.resize(2400, 800)
        window.show()
        window.explorer_tabs.setCurrentIndex(2)
        self.app.processEvents()
        self.addCleanup(window.deleteLater)
        self.addCleanup(window.close)
        return window

    def refresh(self, bodies, window=None):
        window = window or self.window
        window.state.system_bodies = bodies
        window._refresh_explorer_tables()
        self.app.processEvents()

    def click(self, table, column):
        header = table.horizontalHeader()
        QTest.mouseClick(header.viewport(), Qt.LeftButton, pos=QPoint(
            header.sectionViewportPosition(column) + header.sectionSize(column) // 2,
            header.height() // 2))
        self.app.processEvents()
        self.assertTrue(header.isSortIndicatorShown())
        self.assertEqual(header.sortIndicatorSection(), column)

    def drag(self, table, column, amount=17):
        header = table.horizontalHeader()
        point = QPoint(header.sectionViewportPosition(column) + header.sectionSize(column) - 1,
                       header.height() // 2)
        QTest.mousePress(header.viewport(), Qt.LeftButton, pos=point)
        QTest.mouseMove(header.viewport(), point + QPoint(amount, 0), 10)
        QTest.mouseRelease(header.viewport(), Qt.LeftButton, pos=point + QPoint(amount, 0))
        self.app.processEvents()

    @staticmethod
    def widths(table):
        return [table.columnWidth(i) for i in range(table.columnCount())]

    @staticmethod
    def names(table):
        return [table.item(r, 0).text() for r in range(table.rowCount())]

    @staticmethod
    def bodies():
        return [dict(short_name=name, biological_signals=count, geological_signals=count,
                     planetary_mining_signals=count, distance_ls=count,
                     biology=[dict(species=species, scan_type='Log')],
                     first_footfall=name == '9', planet_class='Water world')
                for name, count, species in [('10', 10, 'Beta'), ('2', 2, 'Zulu'), ('9', 9, 'Äther')]]

    def test_all_mouse_widths_survive_refresh_sort_restart_language_and_window_resize(self):
        bodies = self.bodies()
        self.refresh(bodies)
        expected = {}
        for tab, attr, key in [(1, 'explorer_value_table', 'explorer/value_column_widths'),
                               (2, 'explorer_bio_table', 'explorer/bio_geo_mining_column_widths')]:
            self.window.explorer_tabs.setCurrentIndex(tab)
            self.app.processEvents()
            table = getattr(self.window, attr)
            # Resize the stretched value-list status column first, including shrinking it.
            for column in [table.columnCount()-1, *range(table.columnCount()-1)]:
                before = table.columnWidth(column)
                amount = -17 if column == table.columnCount()-1 else 17
                self.drag(table, column, amount)
                self.assertEqual(table.columnWidth(column), before + amount)
                self.assertEqual(self.settings.value(key), self.widths(table))
            expected[attr] = self.widths(table)
            self.assertFalse(table.horizontalHeader().stretchLastSection())
            self.assertFalse(table.horizontalHeader().sectionsMovable())
            self.click(table, 0)
            self.click(table, 0)
            self.refresh(bodies[::-1])
            self.assertEqual(self.widths(table), expected[attr])
        for size in (1900, 2700):
            self.window.resize(size, 800)
            self.app.processEvents()
            for attr, widths in expected.items():
                self.assertEqual(self.widths(getattr(self.window, attr)), widths)
        set_language('sv')
        restarted = self.make_window(QSettings(self.path, QSettings.IniFormat))
        self.refresh(bodies, restarted)
        for attr, widths in expected.items():
            self.assertEqual(self.widths(getattr(restarted, attr)), widths)

    def test_independent_settings_and_legacy_bio_widths(self):
        old_widths = [100 + i * 3 for i in range(11)]
        self.settings.setValue('explorer/bio_geo_mining_column_widths', old_widths)
        window = self.make_window(QSettings(self.path, QSettings.IniFormat))
        bio = window.explorer_bio_table
        self.assertEqual(self.widths(bio), old_widths)
        self.click(bio, 4)
        self.drag(bio, 3)
        bio_saved = {key: window.state.settings.value(key) for key in window.state.settings.allKeys()}
        window.explorer_tabs.setCurrentIndex(1)
        self.app.processEvents()
        self.click(window.explorer_value_table, 2)
        self.drag(window.explorer_value_table, 0)
        for key, value in bio_saved.items():
            self.assertEqual(window.state.settings.value(key), value)
        self.assertEqual(window.state.settings.value('explorer/value_sort_column'), 2)
        self.assertEqual(window.state.settings.value('explorer/bio_geo_mining_sort_column'), 4)
        value_saved = {key: window.state.settings.value(key) for key in window.state.settings.allKeys()
                       if key.startswith('explorer/value')}
        window.explorer_tabs.setCurrentIndex(2)
        self.app.processEvents()
        self.click(bio, 0)
        self.drag(bio, 1)
        for key, value in value_saved.items():
            self.assertEqual(window.state.settings.value(key), value)

    def test_natural_names_and_numeric_columns(self):
        table = self.window.explorer_bio_table
        expected = ['2', '3', '9', '9 a', '9 b', '10', '10 a']
        self.refresh([dict(short_name=name, geological_signals=1) for name in expected[::-1]])
        self.click(table, 0)
        self.assertEqual(self.names(table), expected)
        self.click(table, 0)
        self.assertEqual(self.names(table), expected[::-1])
        self.refresh(self.bodies())
        for column in (2, 3, 4, 6, 7):
            expected = ['9', '2', '10'] if column == 6 else ['2', '9', '10']
            self.click(table, column)
            self.assertEqual(self.names(table), expected)
            self.click(table, column)
            self.assertEqual(self.names(table), expected[::-1])

    def test_text_columns_use_ui_language_without_rich_text_markup(self):
        table = self.window.explorer_bio_table
        bodies = [dict(short_name=name, biological_signals=1, bio_genuses=[name]) for name in ['Zulu', 'Äther']]
        for language, expected in [('de', ['Äther', 'Zulu']), ('sv', ['Zulu', 'Äther'])]:
            set_language(language)
            with patch.object(SystemMapWidget, '_type_text', side_effect=lambda body: body['short_name']):
                self.refresh(bodies)
            for column in (1, 5):
                self.click(table, column)
                self.assertEqual(self.names(table), expected)
                self.click(table, column)
                self.assertEqual(self.names(table), expected[::-1])
                for row, name in enumerate(self.names(table)):
                    self.assertIn(name, table.cellWidget(row, 5).text())

    def test_semantic_visited_analysis_and_status(self):
        bodies = [dict(short_name='open', geological_signals=1),
                  dict(short_name='signals', biological_signals=10),
                  dict(short_name='visited', biological_signals=10, journal_scanned=True),
                  dict(short_name='recorded2', biological_signals=10, journal_scanned=True, bio_found_count=2),
                  dict(short_name='recorded10', biological_signals=10, journal_scanned=True, bio_found_count=10),
                  dict(short_name='analysed', biological_signals=10, journal_scanned=True, bio_completed_count=1)]
        self.refresh(bodies[::-1])
        table = self.window.explorer_bio_table
        self.click(table, 8)
        self.assertEqual(set(self.names(table)[:2]), {'open', 'signals'})
        self.click(table, 8)
        self.assertEqual(set(self.names(table)[-2:]), {'open', 'signals'})
        self.click(table, 9)
        self.assertEqual(self.names(table), [b['short_name'] for b in bodies])
        self.click(table, 9)
        self.assertEqual(self.names(table), [b['short_name'] for b in bodies[::-1]])
        self.click(table, 10)
        self.assertEqual(self.names(table)[:2], ['open', 'signals'])
        self.assertEqual(self.names(table)[-1], 'analysed')
        self.click(table, 10)
        self.assertEqual(self.names(table)[0], 'analysed')
        self.assertEqual(self.names(table)[-2:], ['signals', 'open'])

    def test_every_column_retained_after_refresh_system_switch_reopen_and_restart(self):
        bodies = self.bodies()
        table = self.window.explorer_bio_table
        self.refresh(bodies)
        for column in range(11):
            for order in (Qt.AscendingOrder, Qt.DescendingOrder):
                self.click(table, column)
                expected = self.names(table)
                self.refresh([])
                self.window.state.system = 'Other'
                self.refresh(copy.deepcopy(bodies))
                self.assertEqual(self.names(table), expected)
                self.assertEqual(table.horizontalHeader().sortIndicatorOrder(), order)
                for row in range(table.rowCount()):
                    body = table.item(row, 0).data(Qt.UserRole)
                    self.assertIn(body['biology'][0]['species'], table.cellWidget(row, 5).text())
                    for col in range(11):
                        self.assertEqual(table.item(row, col).data(Qt.UserRole), body)
                # Fresh settings object reads the on-disk state.
                restarted = self.make_window(QSettings(self.path, QSettings.IniFormat))
                self.refresh(bodies, restarted)
                restored = restarted.explorer_bio_table
                self.assertEqual(self.names(restored), expected)
                self.assertTrue(restored.horizontalHeader().isSortIndicatorShown())
                self.assertEqual(restored.horizontalHeader().sortIndicatorSection(), column)
                self.assertEqual(restored.horizontalHeader().sortIndicatorOrder(), order)
                restarted.close()
                self.window.explorer_tabs.setCurrentIndex(1)
                self.window.explorer_tabs.setCurrentIndex(2)
                self.assertEqual(self.names(table), expected)

    def test_default_order_and_appearance_values_unchanged_in_both_themes(self):
        bodies = self.bodies()
        before = copy.deepcopy(bodies)
        for theme, style in [('dark', DARK_STYLESHEET), ('light', LIGHT_STYLESHEET)]:
            self.app.setStyleSheet(style)
            settings = QSettings(str(Path(self.tmp.name) / (theme + '.ini')), QSettings.IniFormat)
            window = self.make_window(settings, theme)
            table = window.explorer_bio_table
            self.refresh(bodies, window)
            self.assertEqual(self.names(table), ['10', '9', '2'])
            self.assertFalse(table.horizontalHeader().isSortIndicatorShown())
            def presentation():
                return {table.item(r, 0).text(): (
                    [(table.item(r, c).text(), table.item(r, c).foreground().color().name(),
                      table.item(r, c).font().underline(), table.item(r, c).toolTip()) for c in range(11)],
                    table.cellWidget(r, 5).text()) for r in range(table.rowCount())}
            original = presentation()
            self.click(table, 4)
            self.click(table, 5)
            self.refresh(bodies, window)
            self.assertEqual(presentation(), original)
            self.assertEqual(table.item(0, 4).foreground().color().name(), '#ff9d00')
            self.assertTrue(table.item(0, 4).font().underline())
            self.assertTrue(table.alternatingRowColors())
            self.assertEqual(table.styleSheet(), '')
            self.assertEqual(self.app.styleSheet(), style)
        self.assertEqual(bodies, before)


if __name__ == '__main__':
    unittest.main()
