import copy
import json
import subprocess
import sys
import unittest
from unittest.mock import patch

from PySide6.QtCore import QCollator, QLocale
from PySide6.QtWidgets import QDialog, QLineEdit

from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.ui import odyssey_cleanup as cleanup
from cmdrhelper.ui.odyssey_view import CLEANUP_COLORS, CLEANUP_ROLE, OdysseyView
from test_material_view import StubController
from test_odyssey_inventory import item, snapshot
import test_odyssey_view as views


class OdysseySortTests(unittest.TestCase):
    setUpClass = classmethod(views.OdysseyViewTests.setUpClass.__func__)
    setUp = views.OdysseyViewTests.setUp
    set_inventory = views.OdysseyViewTests.set_inventory
    rows = views.OdysseyViewTests.rows

    def order(self):
        return [key for key, item in sorted(self.view.items.items(),
                key=lambda pair: self.view.tree.indexOfTopLevelItem(pair[1]))]

    def assert_order(self, cleanup_first):
        rows = {r.key: r for r in self.view.rows}
        collator = QCollator(QLocale(get_language()))
        expected = sorted(self.view.items, key=lambda key: (
            not bool(self.view.items[key].data(0, CLEANUP_ROLE)) if cleanup_first else False,
            collator.sortKey(rows[key].name), key.name, repr(key)))
        self.assertEqual(self.order(), expected)

    def apply_selection(self, selected):
        with patch.object(cleanup.OdysseyCleanupDialog, 'exec', return_value=QDialog.DialogCode.Accepted), \
                patch.object(cleanup.OdysseyCleanupDialog, 'selected_symbols', return_value=frozenset(selected)):
            self.view.manage_cleanup()

    def test_legend_colors_position_visibility_and_tooltip(self):
        for light in (False, True):
            self.page.set_light_mode(light)
            self.app.processEvents()
            self.assertIn(CLEANUP_COLORS[light][0], self.view.cleanup_swatch.styleSheet())
            self.assertEqual(self.view.cleanup_legend.text(), 'Aufräumkandidat')
            self.assertEqual(self.view.cleanup_swatch.toolTip(), tr('odyssey.cleanup.legend_tip'))
            self.assertEqual(self.view.cleanup_legend.toolTip(), tr('odyssey.cleanup.legend_tip'))
            self.assertLess(self.view.cleanup_swatch.geometry().bottom(), self.view.tree.geometry().top())
            self.assertTrue(self.view.cleanup_swatch.isVisible())
        self.page.tabs.setCurrentIndex(0)
        self.assertFalse(self.view.cleanup_swatch.isVisible())

    def test_both_modes_all_categories_and_group_alphabetization(self):
        # Include individually selected Components and Consumables, not just defaults.
        self.apply_selection(cleanup.DEFAULT_SYMBOLS | {'graphene', 'healthpack'})
        for mode in (0, 1):
            self.view.sort_order.setCurrentIndex(mode)
            for category in range(4):
                self.view.tabs.setCurrentIndex(category)
                self.assertEqual(self.view.sort_order.currentIndex(), mode)
                self.assert_order(mode == 0)
                if mode == 0:
                    marked = [bool(self.view.items[key].data(0, CLEANUP_ROLE)) for key in self.order()]
                    self.assertEqual(marked, sorted(marked, reverse=True))

    def test_identical_german_names_keep_ids_amounts_and_powerplay_usage(self):
        self.set_inventory(views.inventory([snapshot('ShipLocker', Items=[
            item('agriculturalprocesssample', 7), item('poweragriculture', 11)]), snapshot('Backpack')]))
        normal = self.rows('agriculturalprocesssample')[0][1]
        power = self.rows('poweragriculture')[0][1]
        self.assertIsNot(normal, power)
        self.assertEqual(normal.text(0), power.text(0))
        self.assertEqual(normal.text(0), 'Agrikulturverfahren-Probe')
        self.assertEqual(normal.text(1), '7')
        self.assertEqual(power.text(1), '11')
        self.assertTrue(normal.data(0, CLEANUP_ROLE))
        self.assertFalse(power.data(0, CLEANUP_ROLE))
        self.assertIn('Powerplay', power.text(5))
        for mode in (0, 1):
            self.view.sort_order.setCurrentIndex(mode)
            keys = [k.name for k in self.order()]
            self.assertLess(keys.index('agriculturalprocesssample'), keys.index('poweragriculture'))
        # Same-name tie remains canonical when both are in the same group.
        self.apply_selection({'agriculturalprocesssample', 'poweragriculture'})
        self.view.sort_order.setCurrentIndex(0)
        self.assertEqual([k.name for k in self.order()[:2]], ['agriculturalprocesssample', 'poweragriculture'])

    def test_sort_persists_navigation_new_view_and_new_process(self):
        self.view.sort_order.setCurrentIndex(0)
        self.page.hide()
        self.page.show()
        self.view.render()
        self.page.tabs.setCurrentIndex(0)
        self.page.tabs.setCurrentIndex(3)
        self.assertEqual(self.view.sort_order.currentData(), 'cleanup')
        controller = StubController()
        reopened = OdysseyView(self.state, QLineEdit(), controller=controller)
        self.addCleanup(reopened.deleteLater)
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.sort_order.currentData(), 'cleanup')
        script = ('import json, sys; from PySide6.QtCore import QSettings; '
                  's=QSettings(sys.argv[1], QSettings.Format.IniFormat); '
                  'print(json.dumps(s.value("materials/odyssey/sort")))')
        result = subprocess.run([sys.executable, '-B', '-c', script, self.state.settings.fileName()],
                                capture_output=True, text=True, check=True, timeout=20)
        self.assertEqual(json.loads(result.stdout), 'cleanup')
        self.view.sort_order.setCurrentIndex(1)
        self.assertEqual(self.state.settings.value('materials/odyssey/sort'), 'alphabetical')

    def test_add_remove_restore_reorders_reuses_rows_without_inventory_work(self):
        original = copy.deepcopy(self.view.inventory)
        self.view.sort_order.setCurrentIndex(0)
        existing = dict(self.view.items)
        for selected in ({'vehicleschematic'}, set(), cleanup.DEFAULT_SYMBOLS):
            with patch.object(self.view, 'begin_loading', side_effect=AssertionError('unexpected reconstruction')):
                self.apply_selection(selected)
            self.assert_order(True)
            self.assertEqual(self.view.inventory, original)
            self.assertEqual(self.view._cleanup_symbols, selected)
            self.assertTrue(all(self.view.items[key] is row for key, row in existing.items()))
        self.assertFalse(self.view.loading_state.pending)
        self.assertFalse(self.view.loading_state.isVisible())

    def test_commander_change_keeps_sort_but_not_personal_selection(self):
        self.view.sort_order.setCurrentIndex(0)
        self.apply_selection({'vehicleschematic'})
        self.set_inventory(views.inventory([], cid=2))
        self.assertEqual(self.view.sort_order.currentData(), 'cleanup')
        self.assertEqual(self.view._cleanup_symbols, cleanup.DEFAULT_SYMBOLS)
        self.assert_order(True)
        self.set_inventory(views.inventory([], cid=1))
        self.assertEqual(self.view._cleanup_symbols, {'vehicleschematic'})
        self.assertEqual(self.order()[0].name, 'vehicleschematic')

    def test_search_filters_empty_and_repeated_render_do_not_change_preferences(self):
        self.view.sort_order.setCurrentIndex(0)
        saved = self.view._cleanup_symbols
        self.page.search.setText('Agrikulturverfahren-Probe')
        self.assertEqual(len(self.view.items), 2)
        self.assert_order(True)
        self.view.filter.setCurrentIndex(self.view.filter.findData('engineering'))
        self.assertFalse(self.view.items)
        self.view.render()
        self.page.search.clear()
        self.view.filter.setCurrentIndex(self.view.filter.findData('all'))
        self.assert_order(True)
        self.assertEqual(self.view._cleanup_symbols, saved)

    def test_inventory_updates_reuse_rows_clear_old_tooltips_and_keep_amounts(self):
        self.view.sort_order.setCurrentIndex(0)
        self.set_inventory(views.inventory([snapshot('ShipLocker', Items=[item('californium', 4)]), snapshot('Backpack')]))
        row = self.rows('californium')[0][1]
        self.set_inventory(views.inventory([snapshot('ShipLocker', Items=[item('californium', 8)]), snapshot('Backpack')]))
        self.assertIs(self.rows('californium')[0][1], row)
        self.assertEqual(row.text(1), '8')
        self.assertEqual(row.toolTip(0).count(tr('odyssey.cleanup.no_use')), 1)
        self.apply_selection(set())
        self.assertIs(self.rows('californium')[0][1], row)
        self.assertNotIn(tr('odyssey.cleanup.no_use'), row.toolTip(0))

    def test_summary_and_child_rows_reused_during_sort_and_stack_transitions(self):
        self.set_inventory(views.inventory(views.pair()))
        children = dict(self.rows('vehicleschematic'))
        summary = self.view.summaries[('Items', 'vehicleschematic')]
        summary.setExpanded(False)
        self.view.sort_order.setCurrentIndex(0)
        self.assertIs(self.view.summaries[('Items', 'vehicleschematic')], summary)
        self.assertFalse(summary.isExpanded())
        self.assertTrue(all(self.view.items[key] is child for key, child in children.items()))
        normal_key = next(key for key in children if key.mission_id is None)
        self.set_inventory(views.inventory([snapshot('ShipLocker', Items=[item('vehicleschematic', 5)]), snapshot('Backpack')]))
        self.assertIs(self.view.items[normal_key], children[normal_key])
        self.assertIsNone(self.view.items[normal_key].parent())
        self.assertEqual(self.view.items[normal_key].text(4), '5')

    def test_all_twelve_languages_legend_sort_labels_and_default_fallback(self):
        for language, translations in _TRANSLATIONS.items():
            set_language(language)
            self.view.render()
            self.assertEqual(self.view.cleanup_legend.text(), translations['odyssey.cleanup.legend'])
            self.assertEqual(self.view.cleanup_legend.toolTip(), translations['odyssey.cleanup.legend_tip'])
            for index, mode in enumerate(('cleanup', 'alphabetical')):
                self.assertEqual(self.view.sort_order.itemText(index), translations['odyssey.sort.' + mode])
            self.assert_order(False)
        self.state.settings.setValue('materials/odyssey/sort', 'invalid')
        reopened = OdysseyView(self.state, QLineEdit(), controller=StubController())
        self.addCleanup(reopened.deleteLater)
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.sort_order.currentData(), 'alphabetical')


if __name__ == '__main__':
    unittest.main()
