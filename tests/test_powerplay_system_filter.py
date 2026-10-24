"""Day-local system selection: synthetic groups/SQLite, no live data or network."""
import copy
import json
from datetime import date
from pathlib import Path
from unittest.mock import patch
import unittest

from PySide6.QtCore import QTime, Qt, Signal
from PySide6.QtTest import QTest
from cmdrhelper.i18n import get_language, set_language, tr, _TRANSLATIONS
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests import test_powerplay_time_filter as time_base
from tests import test_powerplay_day_cache as cache_base
from tests.test_powerplay_store import DAY, event, delivery, credit


class SystemFilterTests(unittest.TestCase):
    setUpClass = classmethod(time_base.TimeFilterTests.setUpClass.__func__)
    setUp = time_base.TimeFilterTests.setUp
    group = time_base.TimeFilterTests.group

    def fill(self):
        self.state.powerplay.chronicle.groups = [
            self.group('2026-10-06T09:00:00Z', 1, system='A'),
            self.group('2026-10-06T10:00:00Z', 2, system='B'),
            self.group('2026-10-06T11:00:00Z', 4, system='C'),
            self.group('2026-10-06T12:00:00Z', 8, system='B'),
            self.group('2026-10-06T13:00:00Z', 16, system='')]
        self.view.render()

    def action(self, key):
        return next(a for a in self.view.system_menu.actions()[2:] if a.data() == key)

    def test_all_single_multiple_reset_unknown_and_merit_integrity(self):
        self.fill(); before = copy.deepcopy(self.state.powerplay.chronicle.groups)
        self.assertIsNone(self.view._selected_systems)
        self.assertEqual(self.view.recent.rowCount(), 5)
        self.assertEqual(self.view.filtered_merits.text(), 'Merits im Filter: +31')
        self.action('b').trigger()
        self.assertEqual(self.view.recent.rowCount(), 2)
        self.assertEqual(self.view.filtered_merits.text(), 'Merits im Filter: +10')
        self.action('c').trigger()
        self.assertEqual(self.view.filtered_merits.text(), 'Merits im Filter: +14')
        self.action('b').trigger()
        self.assertEqual(self.view.recent.rowCount(), 1)
        self.view.system_menu.actions()[0].trigger()
        self.assertEqual(self.view.recent.rowCount(), 5)
        self.action('').trigger()
        self.assertEqual(self.view.filtered_merits.text(), 'Merits im Filter: +16')
        self.assertEqual(self.state.powerplay.chronicle.groups, before)
        self.assertEqual(self.state.powerplay.merits, 12345)

    def test_time_combination_uses_full_day_menu_and_preserves_order(self):
        self.fill(); self.action('b').trigger()
        self.view.from_time.setTime(QTime(13, 0)); self.view.time_filter_enabled.setChecked(True)
        self.assertEqual(self.view.recent.rowCount(), 1)
        self.assertEqual(self.view.filtered_merits.text(), 'Merits im Filter: +8')
        self.assertEqual(set(self.view._system_names), {'', 'a', 'b', 'c'})
        self.view.time_filter_enabled.setChecked(False)
        self.assertEqual([self.view.recent.item(r, 3).text() for r in range(2)], ['+8', '+2'])

    def test_day_navigation_today_direct_change_and_midnight_reset(self):
        self.fill(); self.action('b').trigger()
        self.view._move_day(-1)
        self.assertIsNone(self.view._selected_systems)
        self.view._move_day(1); self.action('b').trigger()
        self.view._today()
        self.assertIsNone(self.view._selected_systems)
        self.action('b').trigger(); self.view.selected_day = date(2026, 10, 5); self.view.render()
        self.assertIsNone(self.view._selected_systems)
        self.view._today(); self.action('b').trigger()
        with patch('cmdrhelper.ui.powerplay_view.local_today', return_value=date(2026, 10, 7)):
            self.view.render()
        self.assertIsNone(self.view._selected_systems)

    def test_commander_switch_resets_without_carrying_choices(self):
        self.fill(); self.action('b').trigger()
        self.state.commander_id = 2; self.state.commander_fid = 'OTHER'
        self.state.powerplay.chronicle.groups = [self.group('2026-10-06T10:00:00Z', 3, system='Other')]
        self.view.render()
        self.assertIsNone(self.view._selected_systems)
        self.assertEqual(self.view._system_names, {'other': 'Other'})
        self.assertEqual(self.view.filtered_merits.text(), 'Merits im Filter: +3')

    def test_commander_signal_resets_even_when_hidden_and_switched_back(self):
        from tests.test_powerplay import ViewState, PowerplayView
        class State(ViewState):
            viewedCommanderChanged = Signal(object)
            commanderIdentityChanged = Signal(object, str, str)
        state = State(); state.commander_id = 1; state.commander_fid = 'A'
        state.powerplay.chronicle.groups = [self.group('2026-10-06T10:00:00Z', system='B')]
        view = PowerplayView(state); self.addCleanup(view.close); self.addCleanup(view.deleteLater)
        view._select_system('b', True)
        state.commander_id = 2; state.commander_fid = 'B'
        state.viewedCommanderChanged.emit(2)
        self.assertIsNone(view._selected_systems)
        state.commander_id = 1; state.commander_fid = 'A'
        state.commanderIdentityChanged.emit(1, 'A', 'Commander A')
        view.render()
        self.assertIsNone(view._selected_systems)

    def test_unchecking_last_selection_shows_no_rows_until_reset(self):
        self.fill(); self.action('b').trigger(); self.action('b').trigger()
        self.assertEqual(self.view._selected_systems, frozenset())
        self.assertEqual(self.view.recent.rowCount(), 0)
        self.assertIn('+0', self.view.filtered_merits.text())
        self.view._all_systems(); self.assertEqual(self.view.recent.rowCount(), 5)

    def test_live_new_system_keeps_selected_and_all_mode_includes_new(self):
        self.fill(); self.action('b').trigger()
        self.state.powerplay.chronicle.groups.extend([
            self.group('2026-10-06T14:00:00Z', 32, system='B'),
            self.group('2026-10-06T15:00:00Z', 64, system='D')])
        self.view.render()
        self.assertEqual(self.view._selected_systems, frozenset({'b'}))
        self.assertEqual(self.view.filtered_merits.text(), 'Merits im Filter: +42')
        self.assertIn('d', self.view._system_names)
        self.assertFalse(self.action('d').isChecked())
        self.view._all_systems()
        self.state.powerplay.chronicle.groups.append(self.group('2026-10-06T16:00:00Z', 128, system='E'))
        self.view.render()
        self.assertEqual(self.view.recent.rowCount(), 8)
        self.assertEqual(self.view.filtered_merits.text(), 'Merits im Filter: +255')

    def test_empty_unknown_only_duplicate_names_and_no_inferred_system(self):
        self.state.system = 'Previously visited'
        self.state.powerplay.chronicle.groups = []
        self.view.render()
        self.assertEqual(self.view._system_names, {})
        self.assertEqual(self.view.filtered_merits.text(), 'Merits im Filter: +0')
        self.state.powerplay.chronicle.groups = [self.group('2026-10-06T10:00:00Z', system=None),
                                               self.group('2026-10-06T11:00:00Z', system='  ')]
        self.view.render()
        self.assertEqual(self.view._system_names, {'': ''})
        self.assertEqual(self.action('').text(), 'System unbekannt')
        self.action('').trigger(); self.assertEqual(self.view.recent.rowCount(), 2)
        self.view._all_systems()
        self.state.powerplay.chronicle.groups = [self.group('2026-10-06T10:00:00Z', system=s)
                                               for s in ('San Xiang', 'San Xiang', ' san xiang ')]
        self.view.render()
        self.assertEqual(len(self.view._system_names), 1)
        self.action('san xiang').trigger(); self.assertEqual(self.view.recent.rowCount(), 3)

    def test_certainties_multiple_credits_not_counted_twice(self):
        groups = [self.group('2026-10-06T10:00:00Z', 2, system='B'),
                  self.group('2026-10-06T11:00:00Z', 4, system='B'),
                  self.group('2026-10-06T12:00:00Z', 8, system='')]
        groups[0].certainty = 'explicit'
        groups[0].credits.append(dict(groups[0].credits[0], MeritsGained=1))
        groups[2].certainty = 'unknown'
        self.state.powerplay.chronicle.groups = groups; self.view.render()
        self.action('b').trigger()
        self.assertEqual(self.view.filtered_merits.text(), 'Merits im Filter: +7')
        self.action('').trigger()
        self.assertEqual(self.view.filtered_merits.text(), 'Merits im Filter: +15')
        self.assertEqual(self.view.recent.item(0,4).text(), '?')

    def test_mouse_and_keyboard_multiple_choices_keep_menu_open(self):
        self.fill(); menu = self.view.system_menu
        menu.popup(self.view.system_filter.mapToGlobal(self.view.system_filter.rect().bottomLeft()))
        self.app.processEvents()
        QTest.mouseClick(menu, Qt.LeftButton, pos=menu.actionGeometry(self.action('b')).center())
        self.assertTrue(menu.isVisible()); self.assertEqual(self.view._selected_systems, frozenset({'b'}))
        menu.setActiveAction(self.action('c')); QTest.keyClick(menu, Qt.Key_Space)
        self.assertTrue(menu.isVisible()); self.assertEqual(self.view._selected_systems, frozenset({'b','c'}))
        QTest.keyClick(menu, Qt.Key_Escape); self.assertFalse(menu.isVisible())

    def test_detach_attach_preserve_filter_table_columns_and_live_updates(self):
        self.fill(); self.action('b').trigger()
        table = self.view.recent
        header = table.horizontalHeader(); header.moveSection(4, 1)
        order = [header.visualIndex(i) for i in range(5)]
        self.view.detach_chronicle()
        self.addCleanup(self.view.attach_chronicle)
        self.assertIs(table, self.view.recent)
        self.assertTrue(self.view.chronicle_window.isAncestorOf(self.view.system_filter))
        self.state.powerplay.chronicle.groups.append(self.group('2026-10-06T14:00:00Z', 32, system='B'))
        self.state.changed.emit()
        self.assertEqual(self.view.filtered_merits.text(), 'Merits im Filter: +42')
        self.view.attach_chronicle()
        self.assertEqual(self.view._selected_systems, frozenset({'b'}))
        self.assertEqual([header.visualIndex(i) for i in range(5)], order)

    def test_twelve_languages_themes_and_narrow_layout(self):
        old = get_language(); self.addCleanup(set_language, old)
        self.fill()
        for lang in _TRANSLATIONS:
            set_language(lang)
            for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                self.view.setStyleSheet(theme)
                for width in (480, 1200):
                    self.view.resize(width,900); self.view.render(); self.app.processEvents()
                    button = self.view.system_filter
                    self.assertEqual(button.text(), tr('pp2.history.system_filter'))
                    self.assertGreaterEqual(button.width(), button.minimumSizeHint().width())
                    self.assertTrue(button.isVisible())
                    self.assertFalse(button.geometry().intersects(self.view.time_filter.geometry()))
                    self.assertEqual(self.view.system_menu.actions()[0].text(), tr('pp2.history.all_systems'))
                    self.assertEqual(self.action('').text(), tr('pp2.history.unknown_system'))


class SystemFilterCacheTests(unittest.TestCase):
    setUpClass = classmethod(cache_base.DayCacheTests.setUpClass.__func__)
    setUp = cache_base.DayCacheTests.setUp
    dispose = cache_base.DayCacheTests.dispose
    journal = cache_base.DayCacheTests.journal
    sync = cache_base.DayCacheTests.sync

    def test_menu_open_no_sql_replay_or_table_rebuild_and_filter_no_day_query(self):
        from cmdrhelper import powerplay_store
        con = self.view._day_cache._con
        before = tuple(con.iterdump())
        statements = []; con.set_trace_callback(statements.append)
        with patch.object(powerplay_store, '_day_rows', side_effect=AssertionError('No day query')), \
             patch.object(powerplay_store, '_decode_day', side_effect=AssertionError('No replay')):
            with patch.object(self.view.recent, 'setRowCount') as rebuild, \
                 patch('cmdrhelper.ui.powerplay_view.today_groups', side_effect=AssertionError('No grouping')):
                for _ in range(10): self.view.system_menu.aboutToShow.emit()
                rebuild.assert_not_called()
                self.assertEqual(statements, [])
            self.view._select_system('test', True)
            self.view._all_systems()
            self.assertEqual(statements, ['PRAGMA data_version']*2)
        con.set_trace_callback(None)
        self.assertEqual(tuple(con.iterdump()), before)
        self.assertEqual(con.execute('PRAGMA user_version').fetchone()[0], 23)

    def test_sql_day_adds_new_system_without_reset_or_duplicate_merits(self):
        self.view._select_system('test', True)
        with Path(self.session['journal_file']).open('a') as f:
            for e in (event('Docked', 20, StarSystem='Other', StationName='Other port'),
                      delivery(21), credit(22, 7, 155)):
                f.write(json.dumps(e)+'\n')
        self.sync(self.session); self.view.render()
        self.assertEqual(self.view._selected_systems, frozenset({'test'}))
        self.assertEqual(set(self.view._system_names), {'test','other'})
        self.assertIn('+48',self.view.filtered_merits.text())
        self.view._select_system('other',True)
        self.assertIn('+55',self.view.filtered_merits.text())
