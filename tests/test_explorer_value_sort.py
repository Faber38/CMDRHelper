import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PySide6.QtCore import QPoint, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QTableWidget, QTabWidget

from cmdrhelper.i18n import get_language, set_language
from cmdrhelper.ui.explorer_value_sort import setup_sort
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.system_view import SystemMapWidget


class ExplorerValueSortTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / 'ui.ini')
        self.settings = QSettings(self.path, QSettings.IniFormat)
        self.main = self.make_main(self.settings)
        self.table = self.main.explorer_value_table
        self.addCleanup(set_language, get_language())
        set_language('de')

    def make_main(self, settings):
        table = QTableWidget(0, 8)
        table.setHorizontalHeaderLabels(['Body', 'Type', 'Distance', 'Scan', 'Current', 'Mapping estimate', 'Mapping', 'Status'])
        table.resize(1200, 400)
        table.show()
        setup_sort(table, settings)
        main = SimpleNamespace(state=SimpleNamespace(system_bodies=[]), explorer_value_table=table,
            explorer_bio_table=QTableWidget(0, 11), explorer_tabs=QTabWidget(),
            _explorer_value_yellow_threshold=lambda: 200000)
        for method in ('_explorer_body_name', '_explorer_body_visited', '_explorer_distance_text', '_format_reward'):
            setattr(main, method, getattr(MainWindow, method))
        for widget in (table, main.explorer_bio_table, main.explorer_tabs):
            self.addCleanup(widget.close)
        self.app.processEvents()
        return main

    def refresh(self, bodies=None, main=None):
        main = main or self.main
        if bodies is not None:
            main.state.system_bodies = bodies
        MainWindow._refresh_explorer_tables(main)

    def names(self, main=None):
        table = (main or self.main).explorer_value_table
        return [table.item(row, 0).text() for row in range(table.rowCount())]

    def click(self, column):
        header = self.table.horizontalHeader()
        point = QPoint(header.sectionViewportPosition(column) + header.sectionSize(column) // 2, header.height() // 2)
        QTest.mouseClick(header.viewport(), Qt.LeftButton, pos=point)
        self.app.processEvents()
        self.assertTrue(header.isSortIndicatorShown())
        self.assertEqual(header.sortIndicatorSection(), column)

    def test_natural_body_order_both_directions(self):
        expected = ['1', '2', '9', '9 a', '9 b', '10', '10 a']
        self.refresh([dict(short_name=name) for name in reversed(expected)])
        self.click(0)
        self.assertEqual(self.names(), expected)
        self.assertEqual(self.table.horizontalHeader().sortIndicatorOrder(), Qt.AscendingOrder)
        self.click(0)
        self.assertEqual(self.names(), expected[::-1])
        self.assertEqual(self.table.horizontalHeader().sortIndicatorOrder(), Qt.DescendingOrder)

    def test_numeric_columns_and_unchanged_values(self):
        bodies = [dict(short_name=str(i), distance_ls=value, scan_value=value,
                       current_value=value, possible_value=value,
                       possible_value_without_efficiency=10000-value)
                  for i, value in enumerate([900, 10000, 20])]
        before = copy.deepcopy(bodies)
        self.refresh(bodies)
        displayed = {self.table.item(r, 0).text(): [self.table.item(r, c).text() for c in range(8)] for r in range(3)}
        for column in range(2, 6):
            with self.subTest(column=column):
                self.click(column)
                self.assertEqual(self.names(), ['2', '0', '1'])
                self.click(column)
                self.assertEqual(self.names(), ['1', '0', '2'])
        self.assertEqual(bodies, before)
        for row in range(3):
            self.assertEqual([self.table.item(row, c).text() for c in range(8)], displayed[self.table.item(row, 0).text()])
            self.assertEqual(self.table.item(row, 0).data(Qt.UserRole), bodies[int(self.table.item(row, 0).text())])

    def test_type_uses_active_language_collation(self):
        for language, expected in [('de', ['Äther', 'Zulu']), ('sv', ['Zulu', 'Äther'])]:
            set_language(language)
            with patch.object(SystemMapWidget, '_type_text', side_effect=lambda body: body['short_name']):
                self.refresh([dict(short_name=name) for name in ['Zulu', 'Äther']])
            # Switch column so the next type click always starts ascending.
            self.click(0)
            self.click(1)
            self.assertEqual(self.names(), expected)
            self.click(1)
            self.assertEqual(self.names(), expected[::-1])

    def test_semantic_mapping_and_scan_status(self):
        bodies = [dict(short_name=str(i), was_mapped=mapped, self_mapped=own,
                       journal_scanned=visited)
                  for i, (mapped, own, visited) in enumerate([
                      (None, False, False), (False, False, False), (True, False, False),
                      (None, False, True), (False, False, True), (True, False, True),
                      (False, True, True)])]
        self.refresh(bodies[::-1])
        self.click(7)
        self.assertEqual(self.names()[:3], list('654'))
        self.assertEqual(set(self.names()[3:]), set('0123'))
        self.click(7)
        self.assertEqual(set(self.names()[:4]), set('0123'))
        self.assertEqual(self.names()[4:], list('456'))
        self.click(6)
        keys = [self.table.item(r, 6).sort_key for r in range(7)]
        self.assertEqual(keys, [0, 0, 0, 0, 1, 2, 3])

    def test_default_refresh_restart_and_layout(self):
        bodies = [dict(short_name='2', possible_value=20), dict(short_name='10', possible_value=100)]
        self.refresh(bodies)
        self.assertEqual(self.names(), ['10', '2'])
        self.assertFalse(self.table.horizontalHeader().isSortIndicatorShown())
        self.assertFalse(self.settings.contains('explorer/value_sort_column'))
        header = self.table.horizontalHeader()
        self.table.setColumnWidth(0, 234)
        header.setSectionsMovable(True)
        header.moveSection(0, 2)
        self.click(0)
        self.click(0)
        bodies.append(dict(short_name='9', possible_value=900))
        bodies[0]['possible_value'] = 2000
        self.refresh()
        self.assertEqual(self.names(), ['10', '9', '2'])
        self.assertEqual(self.table.columnWidth(0), 234)
        self.assertEqual(header.visualIndex(0), 2)
        for settings in (self.settings, QSettings(self.path, QSettings.IniFormat)):
            reopened = self.make_main(settings)
            self.refresh(bodies, reopened)
            self.assertEqual(self.names(reopened), ['10', '9', '2'])
            restored = reopened.explorer_value_table.horizontalHeader()
            self.assertTrue(restored.isSortIndicatorShown())
            self.assertEqual(restored.sortIndicatorSection(), 0)
            self.assertEqual(restored.sortIndicatorOrder(), Qt.DescendingOrder)

    def test_invalid_saved_sort_preserves_default(self):
        self.settings.setValue('explorer/value_sort_column', 99)
        self.settings.setValue('explorer/value_sort_order', 0)
        main = self.make_main(self.settings)
        self.refresh([dict(short_name='2', possible_value=20), dict(short_name='10', possible_value=100)], main)
        self.assertEqual(self.names(main), ['10', '2'])
        self.assertFalse(main.explorer_value_table.horizontalHeader().isSortIndicatorShown())

    def test_every_column_survives_data_refresh_and_restart(self):
        bodies = [dict(short_name='2', planet_class='Water world', distance_ls=10,
                       scan_value=900, current_value=1000, possible_value=2000,
                       journal_scanned=True, was_mapped=False),
                  dict(short_name='10', planet_class='Rocky body', distance_ls=900,
                       scan_value=20, current_value=30, possible_value=40)]
        self.refresh(bodies)
        for column in range(8):
            for order in (Qt.AscendingOrder, Qt.DescendingOrder):
                self.click(column)
                bodies[0].update(self_mapped=True, current_value=3000)
                self.refresh()
                self.assertEqual(self.table._value_sort, (column, order))
                expected = self.names()
                keys = [self.table.item(r, column).sort_key for r in range(2)]
                if order == Qt.AscendingOrder:
                    self.assertFalse(keys[1] < keys[0])
                else:
                    self.assertFalse(keys[0] < keys[1])
                restarted = self.make_main(QSettings(self.path, QSettings.IniFormat))
                self.refresh(bodies, restarted)
                self.assertEqual(self.names(restarted), expected)
                self.assertEqual(restarted.explorer_value_table._value_sort, (column, order))


if __name__ == '__main__':
    unittest.main()
