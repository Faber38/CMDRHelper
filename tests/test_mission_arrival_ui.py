"""Synthetic real mission table: arrival, finite animation and rendered colors."""
from copy import deepcopy
import unittest
from unittest.mock import Mock

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language
from cmdrhelper.mission_arrival import ArrivalPosition
from cmdrhelper.models import STATUS_REDIRECTED, STATUS_ACCEPTED
from cmdrhelper.ui.main_window import MainWindow
from tests import test_missions_table_sort as fixtures
from tests.test_mission_arrival import mission, event, dock


class ArrivalUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.MissionTableSortTests.setUpClass()
        cls.app = fixtures.MissionTableSortTests.app

    def setUp(self):
        self.addCleanup(set_language, get_language())
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        self.fixture = fixtures.MissionTableSortTests(); self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.host = self.fixture.host
        self.table = self.host.missions_table
        self.controller = self.host.mission_arrival
        self.host.page.resize(1800, 800)
        self.host._font_stylesheet_suffix = lambda: ''
        self.host._chronicle_system_window = None
        self.host._refresh_explorer_scan_header = lambda: None
        self.identity = ('heroic', 1, 1, 'A', 'journal', 'start', 1, 2, 3, 4)
        self.position = ArrivalPosition(system='HIP 97950')
        self.closed = set()
        self.controller.source = Mock()
        self.controller.source.snapshot.side_effect = lambda state: (self.identity, self.position, self.closed)
        self.host.state.missions = [mission()]
        self.host._refresh_missions_table()
        self.app.processEvents()

    def marked(self, row=0, col=0):
        return self.controller.marked(self.table.model().index(row, col))

    def arrive(self):
        self.position.feed(dock(), 10)
        self.controller.update()

    def test_three_pulses_then_stable_and_timer_stopped(self):
        self.arrive()
        self.assertTrue(self.controller.timer.isActive())
        phases = [self.marked()]
        for _ in range(6):
            self.controller.advance(); phases.append(self.marked())
        self.assertEqual(phases, [True, False, True, False, True, False, True])
        self.assertFalse(self.controller.timer.isActive())
        self.assertFalse(self.controller.blink)

    def test_refresh_sort_language_and_theme_do_not_restart(self):
        other = mission(2); other.name = 'Alpha'; other.status = STATUS_REDIRECTED
        self.host.state.missions.append(other)
        self.host._refresh_missions_table(); self.arrive()
        self.controller.advance()
        remaining = dict(self.controller.blink)
        self.table.selectRow(0)
        for language in _TRANSLATIONS:
            set_language(language)
            self.host._refresh_missions_table()
            self.fixture.click(0)
            MainWindow._set_theme(self.host, 'light')
            MainWindow._set_theme(self.host, 'dark')
            self.assertEqual(self.controller.blink, remaining)
            selected = self.table.selectionModel().selectedRows()
            self.assertEqual(self.table.item(selected[0].row(), 0).mission.mission_id, 1069627151)
        for _ in range(5): self.controller.advance()
        self.host._refresh_missions_table()
        self.assertFalse(self.controller.timer.isActive())

    def test_hidden_arrival_and_hiding_animation_never_replay(self):
        self.table.hide(); self.arrive()
        self.assertFalse(self.controller.timer.isActive())
        self.table.show(); self.controller.update()
        self.assertTrue(self.marked())
        self.assertFalse(self.controller.timer.isActive())
        self.position.feed(event('SupercruiseEntry', StarSystem='HIP 97950'), 11)
        self.controller.update()
        self.position.feed(dock(), 12); self.controller.update()
        self.assertTrue(self.controller.timer.isActive())
        self.table.hide()
        self.assertFalse(self.controller.timer.isActive())
        self.table.show(); self.controller.update()
        self.assertFalse(self.controller.timer.isActive())

    def test_batched_departure_rearrival_blinks_but_repeated_docked_does_not(self):
        self.arrive()
        for _ in range(6): self.controller.advance()
        self.position.feed(dock(), 11); self.controller.update()
        self.assertFalse(self.controller.timer.isActive())
        self.position.feed(event('SupercruiseEntry', StarSystem='HIP 97950'), 12)
        self.position.feed(dock(), 13)
        self.controller.update()
        self.assertTrue(self.controller.timer.isActive())

    def test_start_commander_change_and_loss_silent_or_clear(self):
        self.position.feed(dock(), 1)
        self.controller.identity = None
        self.controller.update()
        self.assertTrue(self.marked())
        self.assertFalse(self.controller.timer.isActive())
        self.identity = ('steam', 2, 2, 'B', 'other', 'start', 2, 3, 4, 5)
        self.controller.update()
        self.assertFalse(self.marked())  # old commander's table must never match by ID
        self.host.state.commander_id = 2
        self.host._refresh_missions_table()
        self.assertTrue(self.marked())
        self.assertFalse(self.controller.timer.isActive())
        self.controller.source.snapshot.side_effect = None
        self.controller.source.snapshot.return_value = None
        self.controller.update()
        self.assertFalse(self.marked())
        self.assertFalse(self.controller.timer.isActive())

    def test_multiple_redirect_terminal_and_mission_status_unchanged(self):
        other = mission(2)
        self.host.state.missions.append(other)
        original = deepcopy(self.host.state.missions)
        self.host._refresh_missions_table(); self.arrive()
        self.assertTrue(self.marked(0)); self.assertTrue(self.marked(1))
        self.assertEqual(self.host.state.missions, original)
        other.destination_station = 'Hoffman Installation'
        self.host._refresh_missions_table()
        self.assertFalse(self.marked(1))
        self.closed.add(1069627151)
        self.controller.update()
        self.assertFalse(self.marked(0))
        self.assertFalse(self.controller.timer.isActive())

    def test_render_themes_selection_all_languages_and_status_colors(self):
        self.position.feed(dock(), 1)
        self.controller.identity = None; self.controller.update()
        for language in _TRANSLATIONS:
            set_language(language)
            for theme, bg, selected_bg, green, gold in [
                    ('dark', '#302918', '#514222', '#65d067', '#ffb000'),
                    ('light', '#fff4cf', '#eadca5', '#226626', '#765400')]:
                MainWindow._set_theme(self.host, theme)
                for status, color in [(STATUS_ACCEPTED, gold), (STATUS_REDIRECTED, green),
                                      ('unknown', '#20262c' if theme == 'light' else '#d8dde3')]:
                    self.host.state.missions[0].status = status
                    self.host._refresh_missions_table()
                    for selected in (False, True):
                        if selected: self.table.selectRow(0)
                        else: self.table.clearSelection(); self.table.setCurrentItem(None)
                        self.app.processEvents()
                        for col in range(7):
                            image = self.table.viewport().grab(self.table.visualItemRect(self.table.item(0, col))).toImage()
                            self.assertEqual(image.pixelColor(1, 3).name(), selected_bg if selected else bg)
                            if col == 3:
                                rgb = QColor(color).getRgb()[:3]
                                self.assertTrue(any(max(abs(a-b) for a,b in zip(
                                    image.pixelColor(x,y).getRgb()[:3], rgb)) <= 20
                                    for y in range(image.height()) for x in range(image.width())))
        self.assertFalse(self.controller.timer.isActive())
