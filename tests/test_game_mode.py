"""Journal reconstruction, real State refresh, overview text and theme colors."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from contextlib import ExitStack

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QSettings
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.game_mode import _file_mode, reconstruct_game_mode
from cmdrhelper.journal_index import scan_journal_folder
from cmdrhelper.journal_reader import read_latest_state, _LIVE_LINE_CACHE
from cmdrhelper.state import AppState
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.game_mode import GameModeRow
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.help_content import help_topic, HELP_LANGUAGES


def load(mode, second=1, fid='TEST-A', **fields):
    return dict(event='LoadGame', FID=fid, Commander=fid,
                timestamp=f'2026-09-10T05:00:{second:02d}Z', GameMode=mode, **fields)


def identity(fid='TEST-A'):
    return dict(event='Commander', FID=fid, Name=fid,
                timestamp='2026-09-10T05:00:00Z')


class GameModeJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.addCleanup(_file_mode.cache_clear)
        self.addCleanup(_LIVE_LINE_CACHE.clear)

    def write(self, events, number=1):
        path = self.folder / f'Journal.2026-09-10T0500{number:02d}.01.log'
        path.write_text(''.join(json.dumps(e) + '\n' for e in events), encoding='utf-8')
        return path

    def mode(self):
        return read_latest_state(self.folder)

    def test_open(self):
        self.write([load('Open', Group='must not survive')])
        self.assertEqual((self.mode()['game_mode'], self.mode()['group_name']), ('Open', ''))

    def test_solo(self):
        self.write([load('Solo')])
        self.assertEqual((self.mode()['game_mode'], self.mode()['group_name']), ('Solo', ''))

    def test_group_preserves_name(self):
        self.write([load('Group', Group='  Élité <A&B> · 私人  ')])
        self.assertEqual(self.mode()['group_name'], '  Élité <A&B> · 私人  ')

    def test_group_to_solo(self):
        self.write([load('Group', Group='Elitedangerous.de'), load('Solo', 2)])
        self.assertEqual((self.mode()['game_mode'], self.mode()['group_name']), ('Solo', ''))

    def test_group_to_open(self):
        self.write([load('Group', Group='Elitedangerous.de'), load('Open', 2)])
        self.assertEqual((self.mode()['game_mode'], self.mode()['group_name']), ('Open', ''))

    def test_multiple_loads_use_timestamp_not_line_order(self):
        self.write([load('Solo', 5), load('Group', 3, Group='Older'), load('Open', 1)])
        self.assertEqual(self.mode()['game_mode'], 'Solo')
        self.assertEqual(self.mode()['game_mode_timestamp'], '2026-09-10T05:00:05Z')

    def test_latest_timestamp_across_files_and_timezones(self):
        self.write([dict(load('Solo'), timestamp='2026-09-10T07:01:00+02:00')])
        self.write([load('Open', 59)], 2)
        self.assertEqual(self.mode()['game_mode'], 'Solo')

    def test_commander_separation(self):
        self.write([load('Group', 20, Group='Other')])
        self.write([load('Open', fid='TEST-B')], 2)
        self.assertEqual(self.mode()['game_mode'], 'Open')
        self.assertEqual(self.mode()['group_name'], '')

    def test_no_inheritance_for_commander_without_load(self):
        self.write([load('Group', Group='Other')])
        self.write([identity('TEST-B')], 2)
        self.assertEqual(self.mode()['game_mode'], '')

    def test_ambiguous_file_is_excluded(self):
        path = self.write([load('Group', Group='Other'), identity('TEST-B')])
        forged_session = dict(journal_file=str(path), fid_seen='TEST-A', attribution_status='identified')
        self.assertEqual(reconstruct_game_mode([forged_session], 'TEST-A')['game_mode'], '')

    def test_unknown_mode(self):
        self.write([load('Arena', Group='not a private group')])
        self.assertEqual(self.mode()['game_mode'], '')
        self.assertEqual(self.mode()['group_name'], '')

    def test_invalid_newer_events_do_not_replace_last_valid_mode(self):
        self.write([load('Solo'), load('Unexpected', 2),
                    dict(load('Open', 3), timestamp='invalid'),
                    dict(load('Open', 4), timestamp='2026-09-10T05:00:04')])
        self.assertEqual(self.mode()['game_mode'], 'Solo')

    def test_no_loadgame(self):
        self.write([identity()])
        self.assertEqual(self.mode()['game_mode_timestamp'], '')
        self.assertEqual(self.mode()['game_mode'], '')

    def test_no_journals(self):
        self.assertEqual(self.mode()['game_mode'], '')

    def test_indexed_start_restores_history_when_current_has_no_load(self):
        self.write([load('Open'), load('Group', 2, Group='Elitedangerous.de')])
        self.write([identity()], 2)
        db = CMDRDatabase(self.folder / 'test.db')
        sessions = scan_journal_folder(db, self.folder)
        result = read_latest_state(self.folder, indexed_sessions=sessions)
        self.assertEqual((result['game_mode'], result['group_name']), ('Group', 'Elitedangerous.de'))
        # A process restart has no in-memory summaries, but the index still suffices.
        _file_mode.cache_clear()
        sessions = scan_journal_folder(db, self.folder)
        self.assertEqual(read_latest_state(self.folder, indexed_sessions=sessions)['game_mode'], 'Group')

    def test_incomplete_live_event_waits_for_newline_and_ignores_music(self):
        path = self.write([load('Open')])
        db = CMDRDatabase(self.folder / 'test.db')
        sessions = scan_journal_folder(db, self.folder)
        with path.open('a') as out:
            out.write(json.dumps(dict(event='Music', MusicTrack='MainMenu')) + '\n')
            out.write(json.dumps(load('Group', 2, Group='Elitedangerous.de')))
        self.assertEqual(read_latest_state(self.folder, indexed_sessions=sessions)['game_mode'], 'Open')
        with path.open('a') as out:
            out.write('\n')
        self.assertEqual(read_latest_state(self.folder, indexed_sessions=sessions)['game_mode'], 'Group')

    def test_unchanged_history_summary_does_not_reopen_files(self):
        path = self.write([load('Solo')])
        session = dict(journal_file=str(path), fid_seen='TEST-A', attribution_status='identified')
        reconstruct_game_mode([session], 'TEST-A')
        with patch.object(Path, 'open', side_effect=AssertionError('reopened history')):
            self.assertEqual(reconstruct_game_mode([session], 'TEST-A')['game_mode'], 'Solo')


class GameModeUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        old_language, old_style = get_language(), self.app.styleSheet()
        self.addCleanup(set_language, old_language)
        self.addCleanup(self.app.setStyleSheet, old_style)
        set_language('de')

    def test_all_twelve_languages_have_ui_and_help(self):
        self.assertEqual(len(HELP_LANGUAGES), 12)
        for language in HELP_LANGUAGES:
            with self.subTest(language=language):
                set_language(language)
                row = GameModeRow()
                for key in ('overview.game_mode', 'game_mode.open', 'game_mode.solo', 'game_mode.group'):
                    self.assertTrue(_TRANSLATIONS[language][key])
                self.assertEqual(row.caption.text(), tr('overview.game_mode') + ':')
                for mode, key in [('Open', 'open'), ('Solo', 'solo'), ('Group', 'group')]:
                    row.set_mode(mode, 'Elitedangerous.de')
                    suffix = ' · Elitedangerous.de' if mode == 'Group' else ''
                    self.assertEqual(row.value.text(), tr('game_mode.' + key) + suffix)
                self.assertIn('LoadGame', help_topic('overview', language).text)
                row.close()

    def test_name_is_literal_and_removed_for_other_modes(self):
        row = GameModeRow()
        row.set_mode('Group', '<b>Ä & 私人</b>')
        self.assertEqual(row.value.text(), 'Private Gruppe · <b>Ä & 私人</b>')
        for mode, expected in [('Solo', 'Solo'), ('Open', 'Offenes Spiel'), ('Invalid', '–')]:
            row.set_mode(mode, '<b>Ä & 私人</b>')
            self.assertEqual(row.value.text(), expected)
        row.close()

    def test_row_is_directly_below_location_in_existing_card(self):
        from test_overview_column_widths import OverviewWindow
        with tempfile.TemporaryDirectory() as directory:
            settings = QSettings(str(Path(directory) / 'ui.ini'), QSettings.IniFormat)
            window = OverviewWindow(settings)
            self.addCleanup(window.close)
            row = window.overview_game_mode
            card = window.overview_location.parentWidget()
            self.assertIs(row.parentWidget(), card)
            self.assertEqual(card.layout().indexOf(row),
                             card.layout().indexOf(window.overview_location) + 1)
            window.resize(900, 650)
            row.set_mode('Group', 'Elitedangerous.de')
            window.show()
            self.app.processEvents()
            self.assertLess(row.height(), 40)

    def check_color(self, theme, mode, expected):
        self.app.setStyleSheet(LIGHT_STYLESHEET if theme == 'light' else DARK_STYLESHEET)
        row = GameModeRow()
        row.set_mode('Group', 'Previous group')
        row.set_mode(mode, 'Elitedangerous.de')
        row.show()
        self.app.processEvents()
        self.assertEqual(row.value.palette().color(QPalette.WindowText).name(), expected)
        neutral = '#20262c' if theme == 'light' else '#d8dde3'
        self.assertEqual(row.caption.palette().color(QPalette.WindowText).name(), neutral)
        row.close()

    def test_theme_switch_recolors_existing_group(self):
        row = GameModeRow()
        row.set_mode('Group', 'Elitedangerous.de')
        row.show()
        for sheet, expected in [(DARK_STYLESHEET, '#79d45a'), (LIGHT_STYLESHEET, '#37852d')]:
            self.app.setStyleSheet(sheet)
            self.app.processEvents()
            self.assertEqual(row.value.palette().color(QPalette.WindowText).name(), expected)
        row.close()

    def test_real_state_live_refresh_updates_overview_and_commander_reset(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            folder = Path(directory)
            path = folder / 'Journal.2026-09-10T050000.01.log'
            path.write_text(json.dumps(load('Open')) + '\n')
            settings = QSettings(str(folder / 'settings.ini'), QSettings.IniFormat)
            settings.setValue('journal_folder', str(folder))
            db = CMDRDatabase(folder / 'state.db')
            stack.enter_context(patch('cmdrhelper.state.QSettings', return_value=settings))
            stack.enter_context(patch('cmdrhelper.state.CMDRDatabase', return_value=db))
            stack.enter_context(patch('cmdrhelper.state.QTimer.singleShot'))
            state = AppState()
            for method in ('_run_journal_learning', '_upload_journal_to_edsm', '_upload_pending_to_inara', '_request_edsm_for_current_system'):
                stack.enter_context(patch.object(state, method))
            view = MagicMock()
            view.state = state
            view.missions_table.currentRow.return_value = -1
            view._explorer_value_yellow_threshold.return_value = 1000000
            view._explorer_value_red_threshold.return_value = 3000000
            view.overview_game_mode = GameModeRow()
            errors = []
            def refresh_ui():
                try:
                    MainWindow.refresh_all(view)
                except Exception:
                    import traceback
                    errors.append(traceback.format_exc())
            state.changed.connect(refresh_ui)
            for event, expected in [(None, 'Offenes Spiel'),
                                    (dict(event='Music', MusicTrack='MainMenu'), 'Offenes Spiel'),
                                    (load('Group', 2, Group='Elitedangerous.de'), 'Private Gruppe · Elitedangerous.de'),
                                    (load('Solo', 3), 'Solo'),
                                    (load('Group', 4, Group='Elitedangerous.de'), 'Private Gruppe · Elitedangerous.de'),
                                    (load('Open', 5), 'Offenes Spiel')]:
                if event:
                    with path.open('a') as out:
                        out.write(json.dumps(event) + '\n')
                self.assertTrue(state.refresh())
                self.assertEqual(errors, [])
                self.assertEqual(view.overview_game_mode.value.text(), expected)
            self.assertEqual(state.group_name, '')
            other = folder / 'Journal.2026-09-10T050100.01.log'
            other.write_text(json.dumps(identity('TEST-B')) + '\n')
            state._journal_index_sessions = None
            self.assertTrue(state.refresh())
            self.assertEqual(state.commander_fid, 'TEST-B')
            self.assertEqual(view.overview_game_mode.value.text(), '–')
            state.reset_commander_runtime_state()
            self.assertEqual((state.game_mode, state.group_name, state.game_mode_timestamp), ('', '', ''))
            state.watcher.timer.stop()
            view.overview_game_mode.close()


for theme, colors in {
    'dark': {'Open': '#ff6b6b', 'Solo': '#f0ad4e', 'Group': '#79d45a', '': '#d8dde3'},
    'light': {'Open': '#b83232', 'Solo': '#b36a00', 'Group': '#37852d', '': '#20262c'},
}.items():
    for mode, color in colors.items():
        def test(self, theme=theme, mode=mode, color=color):
            self.check_color(theme, mode, color)
        setattr(GameModeUITests, f'test_color_{theme}_{mode or "unknown"}', test)
