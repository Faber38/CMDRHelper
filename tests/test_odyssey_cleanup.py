import copy
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox, QStyle, QStyleOptionViewItem

from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.odyssey_catalog import all_materials, get_material, localized_name
from cmdrhelper.ui import odyssey_cleanup as cleanup
from cmdrhelper.ui.material_row_style import THEMES
from cmdrhelper.ui.odyssey_view import CLEANUP_COLORS, CLEANUP_ROLE
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
import test_odyssey_view as views
from test_odyssey_inventory import item, snapshot


class CleanupDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = str(Path(temp.name) / 'settings.ini')
        self.settings = QSettings(self.path, QSettings.Format.IniFormat)
        self.addCleanup(set_language, get_language())
        set_language('de')

    def dialog(self, selected=cleanup.DEFAULT_SYMBOLS):
        dialog = cleanup.OdysseyCleanupDialog(selected)
        self.addCleanup(dialog.deleteLater)
        self.addCleanup(dialog.close)
        return dialog

    def test_default_list_is_exactly_50_data_and_31_goods(self):
        defaults = [get_material(symbol) for symbol in cleanup.DEFAULT_SYMBOLS]
        self.assertEqual(len(defaults), 81)
        self.assertTrue(all(defaults))
        self.assertEqual(sum(m.category == 'Data' for m in defaults), 50)
        self.assertEqual(sum(m.category == 'Items' for m in defaults), 31)
        self.assertTrue(all(not m.engineering_flags for m in defaults))
        self.assertIn('sabotagedcomponent', cleanup.DEFAULT_SYMBOLS)
        self.assertIn('biomechanicalcomponent', cleanup.DEFAULT_SYMBOLS)
        self.assertIn('seedgeneaology', cleanup.DEFAULT_SYMBOLS)
        self.assertNotIn('powerregulator', cleanup.DEFAULT_SYMBOLS)
        self.assertEqual(cleanup.load_selection(self.settings, cleanup.selection_key(1, 'F1')),
                         cleanup.DEFAULT_SYMBOLS)

    def test_all_catalog_identities_grouped_and_checkable(self):
        dialog = self.dialog()
        self.assertEqual(len(dialog.items), 223)
        self.assertEqual(set(dialog.groups), set(cleanup.GROUPS))
        self.assertEqual(dialog.selected_symbols(), cleanup.DEFAULT_SYMBOLS)
        for material in all_materials():
            row = dialog.items[material.symbol]
            self.assertEqual(row.parent(), dialog.groups[material.subgroup or material.category])
            self.assertEqual(row.data(0, Qt.ItemDataRole.UserRole), material.symbol)
        self.assertIn('81', dialog.count.text())

    def test_add_remove_save_reload_and_separate_commanders(self):
        key = cleanup.selection_key(1, 'F1')
        dialog = self.dialog()
        dialog.items['accidentlogs'].setCheckState(0, Qt.CheckState.Unchecked)
        dialog.items['graphene'].setCheckState(0, Qt.CheckState.Checked)
        selected = dialog.selected_symbols()
        cleanup.save_selection(self.settings, key, selected)
        # A new settings object represents the next application instance.
        restarted = QSettings(self.path, QSettings.Format.IniFormat)
        self.assertEqual(cleanup.load_selection(restarted, key), selected)
        self.assertEqual(cleanup.selection_key(99, 'F1'), key)
        self.assertEqual(cleanup.load_selection(restarted, cleanup.selection_key(2, 'F2')),
                         cleanup.DEFAULT_SYMBOLS)
        cleanup.save_selection(restarted, cleanup.selection_key(2, 'F2'), set())
        self.assertEqual(cleanup.load_selection(restarted, cleanup.selection_key(2, 'F2')), set())
        self.assertEqual(cleanup.load_selection(restarted, key), selected)

    def test_internal_ids_only_invalid_unknown_and_empty_settings(self):
        key = cleanup.selection_key(1, '')
        self.assertIsNone(cleanup.selection_key(0, ''))
        self.assertNotEqual(key, cleanup.selection_key(2, ''))
        cleanup.save_selection(self.settings, key, {'graphene', 'Graphen', 'unknown', 'Unfallberichte'})
        self.assertEqual(cleanup.load_selection(self.settings, key), {'graphene'})
        self.settings.setValue(key, 'not json')
        self.assertEqual(cleanup.load_selection(self.settings, key), cleanup.DEFAULT_SYMBOLS)
        self.settings.setValue(key, json.dumps([]))
        self.assertEqual(cleanup.load_selection(self.settings, key), set())
        with self.assertRaises(ValueError):
            cleanup.save_selection(self.settings, None, {'graphene'})

    def test_saved_selection_survives_new_python_process(self):
        key = cleanup.selection_key(1, 'F1')
        cleanup.save_selection(self.settings, key, {'graphene', 'accidentlogs'})
        script = ('import json, sys; from PySide6.QtCore import QSettings; '
                  'from cmdrhelper.ui.odyssey_cleanup import load_selection; '
                  's = QSettings(sys.argv[1], QSettings.Format.IniFormat); '
                  'print(json.dumps(sorted(load_selection(s, sys.argv[2]))))')
        result = subprocess.run([sys.executable, '-B', '-c', script, self.path, key],
                                capture_output=True, text=True, check=True, timeout=20)
        self.assertEqual(json.loads(result.stdout), ['accidentlogs', 'graphene'])

    def test_cancel_does_not_persist_draft(self):
        key = cleanup.selection_key(1, 'F1')
        dialog = self.dialog()
        dialog.items['graphene'].setCheckState(0, Qt.CheckState.Checked)
        dialog.cancel_button.click()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Rejected)
        self.assertFalse(self.settings.contains(key))

    def test_restore_requires_confirmation_and_only_edits_draft(self):
        key = cleanup.selection_key(1, 'F1')
        cleanup.save_selection(self.settings, key, {'graphene'})
        dialog = self.dialog({'graphene'})
        with patch.object(QMessageBox, 'exec', return_value=QMessageBox.StandardButton.No):
            dialog.restore_defaults()
        self.assertEqual(dialog.selected_symbols(), {'graphene'})
        with patch.object(QMessageBox, 'exec', return_value=QMessageBox.StandardButton.Yes):
            dialog.restore_defaults()
        self.assertEqual(dialog.selected_symbols(), cleanup.DEFAULT_SYMBOLS)
        self.assertEqual(cleanup.load_selection(self.settings, key), {'graphene'})
        dialog.reject()
        self.assertEqual(cleanup.load_selection(self.settings, key), {'graphene'})
        cleanup.save_selection(self.settings, key, dialog.selected_symbols())
        self.assertEqual(cleanup.load_selection(self.settings, key), cleanup.DEFAULT_SYMBOLS)

    def test_search_local_and_english_filters_and_hidden_selection(self):
        dialog = self.dialog()
        for query in (localized_name('accidentlogs'), 'Accident Logs'):
            dialog.search.setText(query)
            self.assertFalse(dialog.items['accidentlogs'].isHidden())
            self.assertTrue(dialog.items['graphene'].isHidden())
            self.assertEqual(dialog.selected_symbols(), cleanup.DEFAULT_SYMBOLS)
        dialog.search.clear()
        dialog.filter.setCurrentIndex(1)
        self.assertTrue(dialog.items['graphene'].isHidden())
        dialog.items['accidentlogs'].setCheckState(0, Qt.CheckState.Unchecked)
        self.assertTrue(dialog.items['accidentlogs'].isHidden())
        dialog.filter.setCurrentIndex(2)
        self.assertFalse(dialog.items['graphene'].isHidden())
        self.assertTrue(dialog.items['californium'].isHidden())
        self.assertIn('80', dialog.count.text())

    def test_all_twelve_languages_have_keys_and_same_identities(self):
        keys = {key for key in _TRANSLATIONS['en'] if key.startswith('odyssey.cleanup.')}
        self.assertEqual(len(_TRANSLATIONS), 12)
        for language, translations in _TRANSLATIONS.items():
            with self.subTest(language=language):
                self.assertTrue(keys <= translations.keys())
                self.assertTrue(all(translations[key] for key in keys))
                set_language(language)
                dialog = self.dialog()
                self.assertEqual(dialog.selected_symbols(), cleanup.DEFAULT_SYMBOLS)
                self.assertEqual(dialog.items['accidentlogs'].text(0), localized_name('accidentlogs'))
                self.assertIn('81', dialog.count.text())
                self.assertIn('223', dialog.count.text())
                self.assertNotIn('{count}', dialog.count.text())


class CleanupViewTests(unittest.TestCase):
    setUpClass = classmethod(views.OdysseyViewTests.setUpClass.__func__)
    setUp = views.OdysseyViewTests.setUp
    set_inventory = views.OdysseyViewTests.set_inventory
    rows = views.OdysseyViewTests.rows

    def style(self, row, column, selected=False):
        option = QStyleOptionViewItem()
        option.initFrom(self.view.tree)
        if selected:
            option.state |= QStyle.StateFlag.State_Selected
        self.view.row_delegate.initStyleOption(option, self.view.tree.indexFromItem(row, column))
        return option

    def test_default_goods_data_engineering_unknown_and_inventory_unchanged(self):
        inv = views.inventory([snapshot('ShipLocker', Items=[item('californium', 4), item('futurething', 7)],
                                        Data=[item('accidentlogs', 5)]), snapshot('Backpack')])
        self.set_inventory(inv)
        original = copy.deepcopy(self.view.inventory)
        self.assertTrue(self.rows('californium')[0][1].data(0, CLEANUP_ROLE))
        self.assertFalse(self.rows('futurething')[0][1].data(0, CLEANUP_ROLE))
        self.view.tabs.setCurrentIndex(2)
        row = self.rows('accidentlogs')[0][1]
        self.assertTrue(row.data(0, CLEANUP_ROLE))
        self.assertEqual(row.text(1), '5')
        self.assertIn(tr('odyssey.cleanup.no_use'), row.toolTip(0))
        self.view.tabs.setCurrentIndex(1)
        self.assertTrue(all(not r.data(0, CLEANUP_ROLE) for r in self.view.items.values()))
        self.assertEqual(self.view.inventory, original)

    def test_full_row_colors_tooltips_and_selection_in_both_themes(self):
        for light in (False, True):
            self.app.setStyleSheet(LIGHT_STYLESHEET if light else DARK_STYLESHEET)
            self.page.set_light_mode(light)
            row = self.rows('californium')[0][1]
            for column in range(6):
                style = self.style(row, column)
                self.assertEqual(style.backgroundBrush.color().name(), CLEANUP_COLORS[light][0])
                self.assertEqual(style.palette.color(QPalette.ColorRole.Text).name(), CLEANUP_COLORS[light][1])
                self.assertIn(tr('odyssey.cleanup.no_use'), row.toolTip(column))
                selected = self.style(row, column, True)
                self.assertEqual(selected.backgroundBrush.color().name(), THEMES[light]['selected'])
                self.assertEqual(selected.palette.color(QPalette.ColorRole.Text).name(), THEMES[light]['selected_text'])

    def test_saved_custom_engineering_mark_tooltip_and_unmarked_default(self):
        cleanup.save_selection(self.state.settings, self.view._cleanup_key, {'graphene'})
        self.set_inventory(views.inventory(views.pair()))
        self.assertFalse(self.rows('californium')[0][1].data(0, CLEANUP_ROLE))
        self.view.tabs.setCurrentIndex(1)
        row = self.rows('graphene')[0][1]
        self.assertTrue(row.data(0, CLEANUP_ROLE))
        self.assertIn(tr('odyssey.cleanup.personal'), row.toolTip(0))
        self.assertNotIn(tr('odyssey.cleanup.no_use'), row.toolTip(0))
        self.assertIn('Engineering', row.text(5))
        self.assertIn(tr('odyssey.use.suit_upgrade'), row.toolTip(0))

    def test_commander_switch_loading_and_return_restores_preferences(self):
        cleanup.save_selection(self.state.settings, self.view._cleanup_key, set())
        self.set_inventory(views.inventory([], cid=1))
        self.assertFalse(self.rows('californium')[0][1].data(0, CLEANUP_ROLE))
        self.controller.loading.emit()
        self.assertFalse(self.view.cleanup_button.isEnabled())
        self.assertTrue(self.view.loading_state.pending)
        self.assertFalse(self.view._cleanup_symbols)
        self.set_inventory(views.inventory([], cid=2))
        self.assertTrue(self.view.cleanup_button.isEnabled())
        self.assertFalse(self.view.loading_state.pending)
        self.assertTrue(self.rows('californium')[0][1].data(0, CLEANUP_ROLE))
        self.set_inventory(views.inventory([], cid=1))
        self.assertFalse(self.rows('californium')[0][1].data(0, CLEANUP_ROLE))

    def test_dialog_accept_updates_immediately_cancel_and_stale_result_do_not(self):
        original = copy.deepcopy(self.view.inventory)
        key = self.view._cleanup_key
        with patch.object(cleanup.OdysseyCleanupDialog, 'exec', return_value=QDialog.DialogCode.Accepted), \
                patch.object(cleanup.OdysseyCleanupDialog, 'selected_symbols', return_value=frozenset()):
            self.view.manage_cleanup()
        self.assertFalse(self.rows('californium')[0][1].data(0, CLEANUP_ROLE))
        self.assertEqual(self.view.inventory, original)
        with patch.object(cleanup.OdysseyCleanupDialog, 'exec', return_value=QDialog.DialogCode.Rejected):
            self.view.manage_cleanup()
        self.assertEqual(cleanup.load_selection(self.state.settings, key), set())
        def switched():
            self.set_inventory(views.inventory([], cid=2))
            return QDialog.DialogCode.Accepted
        with patch.object(cleanup.OdysseyCleanupDialog, 'exec', side_effect=switched):
            self.view.manage_cleanup()
        self.assertEqual(cleanup.load_selection(self.state.settings, key), set())
        self.assertFalse(self.state.settings.contains(self.view._cleanup_key))

    def test_multiple_stacks_summary_mission_tooltips_and_sort_survive_refresh(self):
        inv = views.inventory([snapshot('ShipLocker', Items=[item('californium', 2, MissionID=42),
                                                           item('californium', 3)]), snapshot('Backpack')])
        self.set_inventory(inv)
        order = [self.view.tree.topLevelItem(i).text(0) for i in range(self.view.tree.topLevelItemCount())]
        rows = self.rows('californium')
        self.assertEqual(len(rows), 2)
        mission = next(row for key, row in rows if key.mission_id)
        self.assertIn('42', mission.toolTip(0))
        self.assertIn('Mission', mission.text(5))
        summary = self.view.summaries[('Items', 'californium')]
        self.assertTrue(summary.data(0, CLEANUP_ROLE))
        self.assertEqual(summary.text(4), '5')
        self.view.render()
        self.assertEqual(order, [self.view.tree.topLevelItem(i).text(0) for i in range(self.view.tree.topLevelItemCount())])

    def test_save_failure_keeps_visible_selection(self):
        before = self.view._cleanup_symbols
        with patch.object(cleanup.OdysseyCleanupDialog, 'exec', return_value=QDialog.DialogCode.Accepted), \
                patch.object(cleanup, 'save_selection', side_effect=OSError), \
                patch.object(QMessageBox, 'warning') as warning:
            self.view.manage_cleanup()
        warning.assert_called_once()
        self.assertEqual(self.view._cleanup_symbols, before)


if __name__ == '__main__':
    unittest.main()
