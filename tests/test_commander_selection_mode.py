"""Synthetic persisted UI selection; no application startup side effects."""
import ast
import inspect
import textwrap
import tempfile
import unittest
from pathlib import Path

from PySide6.QtCore import QObject
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.state import AppState
from tests.test_commander_view import MemorySettings


class SelectionModeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = CMDRDatabase(Path(self.tmp.name) / 'synthetic.db')
        self.a = self.db.upsert_commander('TEST-A', 'Same')
        self.b = self.db.upsert_commander('TEST-B', 'Same')
        self.settings = MemorySettings()

    def restart(self):
        state = AppState.__new__(AppState)
        QObject.__init__(state)
        state.database = self.db
        state.settings = self.settings
        state.commander_id = self.b
        state.commander_fid = 'TEST-B'
        state._journal_index_sessions = [dict(attribution_status='identified', fid_seen='TEST-B', commander_id=self.b)]
        # Execute the actual constructor's selection initialization, without
        # starting importers or opening the user's configuration/database.
        tree = ast.parse(textwrap.dedent(inspect.getsource(AppState.__init__)))
        assignments = [n for n in tree.body[0].body if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Attribute) and t.attr in
                               ('viewed_commander_id', '_viewed_commander_user_selected') for t in n.targets)]
        exec(compile(ast.Module(body=assignments, type_ignores=[]), '<selection-init>', 'exec'), {'self': state})
        return state

    def test_saved_selection_survives_restart(self):
        self.settings.setValue('commander_view/viewed_commander_id', self.a)
        self.settings.setValue('commander_view/follow_live', False)
        state = self.restart()
        self.assertEqual(state.resolve_viewed_commander(), self.a)
        self.assertEqual(state.commander_id, self.b)

    def test_explicit_follow_survives_restart_and_unknown_does_not_follow(self):
        state = self.restart()
        state.select_viewed_commander(self.a)
        state.set_follow_live_commander(True)
        state = self.restart()
        self.assertEqual(state.resolve_viewed_commander(), self.b)
        for status in ('unknown', 'ambiguous'):
            state._journal_index_sessions[-1]['attribution_status'] = status
            state.viewed_commander_id = self.a
            self.assertEqual(state.resolve_viewed_commander(), self.a)

    def test_missing_saved_commander_not_replaced(self):
        self.settings.setValue('commander_view/viewed_commander_id', 98765)
        self.settings.setValue('commander_view/follow_live', False)
        state = self.restart()
        self.assertIsNone(state.resolve_viewed_commander())
        self.assertEqual(self.settings.value('commander_view/viewed_commander_id'), 98765)

    def test_legacy_saved_id_keeps_automatic_mode_without_overwriting_explicit_choice(self):
        self.settings.setValue('commander_view/viewed_commander_id', self.a)
        self.assertTrue(self.restart().follow_live_commander)
        self.assertEqual(self.restart().resolve_viewed_commander(), self.b)
        for value, expected in ((False, False), ('false', False), (True, True), ('true', True)):
            self.settings.setValue('commander_view/follow_live', value)
            self.assertEqual(self.restart().follow_live_commander, expected)

    def test_fid_not_name_and_manual_selection_turns_follow_off(self):
        state = self.restart()
        self.assertEqual(state.resolve_viewed_commander(), self.b)
        self.db.upsert_commander('TEST-B', 'Renamed')
        self.assertEqual(state.resolve_viewed_commander(), self.b)
        state.select_viewed_commander(self.a)
        self.assertFalse(state.follow_live_commander)
        self.assertEqual(self.restart().resolve_viewed_commander(), self.a)
        state.set_follow_live_commander(True)
        state.commander_fid = 'TEST-A'  # CID/FID mismatch must not select B.
        state.viewed_commander_id = self.a
        self.assertEqual(state.resolve_viewed_commander(), self.a)

    def test_live_switch_and_missing_fid_leave_write_identity_separate(self):
        state = self.restart()
        self.assertEqual(state.resolve_viewed_commander(), self.b)
        state.commander_id, state.commander_fid = self.a, 'TEST-A'
        state._journal_index_sessions = [dict(attribution_status='identified', fid_seen='TEST-A', commander_id=self.a)]
        self.assertEqual(state.resolve_viewed_commander(), self.a)
        state.commander_fid = ''
        state.commander_id = self.b
        self.assertEqual(state.resolve_viewed_commander(), self.a)
        state.select_viewed_commander(self.a)
        self.assertEqual(state.commander_id, self.b)
        self.assertEqual(state.commander_fid, '')

    def test_checkbox_all_languages_themes_and_sizes(self):
        from PySide6.QtWidgets import QApplication
        from cmdrhelper import i18n
        from cmdrhelper.ui.commander_view import CommanderView
        from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
        app = QApplication.instance() or QApplication([])
        self.addCleanup(i18n.set_language, i18n.get_language())
        for language in i18n._TRANSLATIONS:
            i18n.set_language(language)
            state = self.restart()
            view = CommanderView(state)
            try:
                for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                    view.setStyleSheet(theme)
                    for width in (480, 1280):
                        with self.subTest(language=language, width=width):
                            view.resize(width, 720)
                            view.show()
                            app.processEvents()
                            checkbox = view.follow_live_checkbox
                            self.assertTrue(checkbox.isVisible())
                            self.assertLessEqual(checkbox.sizeHint().width(), width - 20)
                            self.assertGreaterEqual(checkbox.width(), checkbox.sizeHint().width())
                            self.assertTrue(view.rect().contains(checkbox.geometry()))
                            checkbox.setChecked(False)
                            self.assertFalse(state.follow_live_commander)
                            checkbox.setChecked(True)
                            self.assertTrue(state.follow_live_commander)
                            self.assertEqual(state.commander_id, self.b)
                            self.assertEqual(state.commander_fid, 'TEST-B')
            finally:
                view.close()
                view.deleteLater()
                app.processEvents()

    def test_fixed_selection_survives_both_live_identity_entry_points(self):
        self.settings.setValue('commander_view/viewed_commander_id', self.a)
        self.settings.setValue('commander_view/follow_live', False)
        state = self.restart()
        state._journal_index_sessions[-1]['journal_file'] = str(Path(self.tmp.name) / 'synthetic.log')
        state._prepare_indexed_live_state(emit_identity=False, restore=False)
        self.assertEqual(state.viewed_commander_id, self.a)
        state._apply_commander_identity(dict(commander_fid='TEST-B', commander_identity_name='Renamed',
                                            latest_journal_session=state._journal_index_sessions[-1]))
        self.assertEqual(state.viewed_commander_id, self.a)
        self.assertEqual(state.commander_id, self.b)

    def test_one_commander_and_start_without_live_identity(self):
        state = self.restart()
        state.commander_fid = ''
        state.commander_id = None
        self.assertIsNone(state.resolve_viewed_commander())
        state.commander_fid, state.commander_id = 'TEST-A', self.a
        state._journal_index_sessions = [dict(attribution_status='identified', fid_seen='TEST-A', commander_id=self.a)]
        only_a = [c for c in self.db.list_commanders() if c['id'] == self.a]
        self.assertEqual(state.resolve_viewed_commander(only_a), self.a)
