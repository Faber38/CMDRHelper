"""Synthetic mission page rendering; settings only in a temporary directory."""
from copy import deepcopy
import unittest

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QAbstractItemView

from cmdrhelper import models
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language
from cmdrhelper.mission_manager import translate_mission_text
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.mission_status import MISSION_STATUS_ROLE
from tests import test_missions_table_sort as sort_tests


class MissionStatusColorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sort_tests.MissionTableSortTests.setUpClass()
        cls.app = sort_tests.MissionTableSortTests.app

    def setUp(self):
        language = get_language()
        stylesheet = self.app.styleSheet()
        self.addCleanup(set_language, language)
        self.addCleanup(self.app.setStyleSheet, stylesheet)
        self.fixture = sort_tests.MissionTableSortTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.host = self.fixture.host
        self.table = self.host.missions_table
        self.host.page.resize(1800, 800)
        self.host._font_stylesheet_suffix = lambda: ''
        self.host._chronicle_system_window = None
        self.host._refresh_explorer_scan_header = lambda: None

    def theme(self, name):
        MainWindow._set_theme(self.host, name)
        self.app.processEvents()

    def show_status(self, status):
        self.host.state.missions = [models.Mission(
            mission_id=1, name='Synthetic', status=status, next_step='Next', reward=123)]
        self.host._refresh_missions_table()
        self.app.processEvents()

    def cell_image(self, column=3, row=0):
        self.app.processEvents()
        return self.table.viewport().grab(
            self.table.visualItemRect(self.table.item(row, column))).toImage()

    def assert_color(self, image, color):
        target = QColor(color)
        # Font antialiasing blends even the darkest glyph pixels on some Qt builds.
        self.assertTrue(any(max(abs(a - b) for a, b in zip(
            image.pixelColor(x, y).getRgb()[:3], target.getRgb()[:3])) <= 20
            for y in range(image.height()) for x in range(image.width())), color)

    def test_all_statuses_themes_and_selected_rows(self):
        green = {models.STATUS_REDIRECTED, models.STATUS_COMPLETED,
                 models.STATUS_DATA_RECEIVED, models.STATUS_AT_DESTINATION}
        statuses = [value for key, value in vars(models).items() if key.startswith('STATUS_')]
        statuses += ['unknown-status', '', 'Mission angenommen', 'Destination changed']
        for theme, green_color, gold in [('dark', '#65d067', '#ffb000'),
                                          ('light', '#226626', '#765400')]:
            self.theme(theme)
            for status in statuses:
                self.show_status(status)
                for selected in (False, True):
                    with self.subTest(theme=theme, status=status, selected=selected):
                        if selected:
                            self.table.selectRow(0)
                        image = self.cell_image()
                        if status in green:
                            self.assert_color(image, green_color)
                        elif status == models.STATUS_ACCEPTED:
                            self.assert_color(image, gold)
                        else:
                            # Unmapped values render exactly like the standard delegate.
                            self.table.setItemDelegateForColumn(3, self.table.itemDelegate())
                            self.assertEqual(image, self.cell_image())
                            self.table.setItemDelegateForColumn(3, self.host.mission_status_delegate)
                        self.assertEqual(self.table.selectionBehavior(), QAbstractItemView.SelectRows)

    def test_all_languages_use_internal_status_and_leave_other_columns_unchanged(self):
        for language in _TRANSLATIONS:
            set_language(language)
            for theme, green, gold in [('dark', '#65d067', '#ffb000'),
                                        ('light', '#226626', '#765400')]:
                self.theme(theme)
                for status, color in [(models.STATUS_REDIRECTED, green),
                                      (models.STATUS_ACCEPTED, gold)]:
                    with self.subTest(language=language, theme=theme, status=status):
                        self.show_status(status)
                        self.table.selectRow(0)
                        self.assertEqual(self.table.item(0, 3).text(), translate_mission_text(status))
                        self.assertEqual(self.table.item(0, 3).data(MISSION_STATUS_ROLE), status)
                        self.assert_color(self.cell_image(), color)
                        for col in (0, 1, 2, 4, 5, 6):
                            item = self.table.item(0, col)
                            self.assertIsNone(item.data(Qt.ForegroundRole))
                            self.assertIsNone(item.data(MISSION_STATUS_ROLE))
                            self.assertIs(self.table.itemDelegateForColumn(col), None)

    def test_theme_change_refresh_sort_and_selection(self):
        rows = [models.Mission(mission_id=1, name='Zulu', status=models.STATUS_REDIRECTED),
                models.Mission(mission_id=2, name='Alpha', status=models.STATUS_ACCEPTED)]
        original = deepcopy(rows)
        self.host.state.missions = rows
        self.host._refresh_missions_table()
        self.fixture.click(0)
        self.table.selectRow(0)
        item = self.table.item(0, 3)
        for theme, color in [('light', '#765400'), ('dark', '#ffb000'), ('light', '#765400')]:
            self.theme(theme)
            self.assertIs(self.table.item(0, 3), item)  # Theme needs no table rebuild.
            self.assert_color(self.cell_image(), color)
            self.assertEqual(self.fixture.ids(), [2, 1])
            self.assertEqual([i.row() for i in self.table.selectionModel().selectedRows()], [0])
        self.assertEqual(rows, original)
        rows[1].status = models.STATUS_COMPLETED
        self.host._refresh_missions_table()
        self.assert_color(self.cell_image(), '#226626')
        self.assertEqual(self.fixture.ids(), [2, 1])
        self.assertEqual([i.row() for i in self.table.selectionModel().selectedRows()], [0])
        rows[1].status = 'unknown'
        self.host._refresh_missions_table()
        image = self.cell_image()
        self.table.setItemDelegateForColumn(3, self.table.itemDelegate())
        self.assertEqual(image, self.cell_image())

    def test_background_and_other_cells_match_standard_rendering(self):
        for theme in ('dark', 'light'):
            self.theme(theme)
            self.show_status(models.STATUS_REDIRECTED)
            for selected in (False, True):
                if selected:
                    self.table.selectRow(0)
                before = [self.cell_image(col) for col in range(7)]
                self.table.setItemDelegateForColumn(3, self.table.itemDelegate())
                after = [self.cell_image(col) for col in range(7)]
                for col in (0, 1, 2, 4, 5, 6):
                    self.assertEqual(before[col], after[col])
                # Text-free top/bottom strips preserve background and focus border.
                for y in (0, 1, before[3].height() - 2, before[3].height() - 1):
                    for x in range(before[3].width()):
                        self.assertEqual(before[3].pixel(x, y), after[3].pixel(x, y))
                self.table.setItemDelegateForColumn(3, self.host.mission_status_delegate)
