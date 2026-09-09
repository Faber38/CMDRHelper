import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtCore import QSettings, Qt, QPoint, QEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QStyle, QStyleOptionViewItem

from cmdrhelper.material_inventory import _Reducer
from cmdrhelper.ui.material_view import MaterialView
from cmdrhelper.ui.material_row_style import STRIPE_ROLE, THEMES
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from test_material_view import StubController, snapshot, event


class MaterialRowStyleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        previous = self.app.styleSheet()
        self.addCleanup(self.app.setStyleSheet, previous)
        settings = QSettings(str(Path(self.tmp.name) / 'ui.ini'), QSettings.Format.IniFormat)
        self.view = MaterialView(SimpleNamespace(settings=settings), controller=StubController())
        self.view.resize(1000, 850)
        self.view.show()
        self.addCleanup(self.view.close)
        self.reducer = _Reducer(1, 'F1')
        self.reducer.apply(snapshot(), ('journal', 0))
        self.view.set_inventory(self.reducer.result)
        self.theme(False)

    def theme(self, light):
        self.app.setStyleSheet(LIGHT_STYLESHEET if light else DARK_STYLESHEET)
        self.view.set_light_mode(light)
        self.app.processEvents()
        QApplication.sendEvent(self.view.tree.viewport(), QEvent(QEvent.Type.Leave))

    def color(self, item, column=0):
        option = QStyleOptionViewItem()
        option.initFrom(self.view.tree)
        if item.isSelected():
            option.state |= QStyle.StateFlag.State_Selected
        self.view.row_delegate.initStyleOption(option, self.view.tree.indexFromItem(item, column))
        return option.backgroundBrush.color().name()

    def point(self, item):
        rect = self.view.tree.visualItemRect(item)
        return QPoint(self.view.tree.columnWidth(0) - 15, rect.center().y())

    def hover(self, item):
        # Move from outside first: a stationary OS cursor emits no new MouseMove.
        QTest.mouseMove(self.view.tree.header().viewport(), QPoint(10, 5))
        QTest.mouseMove(self.view.tree.viewport(), self.point(item))

    def pixel(self, item):
        self.app.processEvents()
        return self.view.tree.viewport().grab().toImage().pixelColor(self.point(item)).name()

    def collect(self, symbol='carbon'):
        self.reducer.apply(event('MaterialCollected', 1, Name=symbol, Category='Raw', Count=1), ('journal', 1))
        self.view.set_inventory(self.reducer.result)
        self.app.processEvents()
        return self.view.items[symbol]

    def test_five_distinct_backgrounds_and_sixth_repeats_in_both_themes(self):
        for light in (False, True):
            self.theme(light)
            group = self.view.tree.topLevelItem(0)
            colors = [self.color(group.child(i)) for i in range(6)]
            self.assertEqual(len(set(colors[:5])), 5)
            self.assertEqual(colors[0], colors[5])
            self.assertEqual(colors[:5], list(THEMES[light]['rows']))
            # Inspect actual rendered pixels, not just configuration values.
            self.assertEqual([self.pixel(group.child(i)) for i in range(6)], colors)

    def test_grade_headers_are_excluded_and_each_block_restarts_at_a(self):
        for light in (False, True):
            self.theme(light)
            for i in range(self.view.tree.topLevelItemCount()):
                group = self.view.tree.topLevelItem(i)
                self.assertIsNone(group.data(0, STRIPE_ROLE))
                self.assertFalse(group.flags() & Qt.ItemFlag.ItemIsSelectable)
                self.assertEqual(group.background(0).style(), Qt.BrushStyle.NoBrush)
                self.assertEqual(self.color(group.child(0)), THEMES[light]['rows'][0])
            self.view.tabs.setCurrentIndex(2)
            last = self.view.tree.topLevelItem(self.view.tree.topLevelItemCount() - 1)
            self.assertIsNone(last.data(0, STRIPE_ROLE))
            self.view.tabs.setCurrentIndex(0)

    def test_selection_overrides_normal_and_live_in_both_themes(self):
        item = self.collect()
        for light in (False, True):
            self.theme(light)
            item = self.view.items['carbon']
            QTest.mouseClick(self.view.tree.viewport(), Qt.MouseButton.LeftButton, pos=self.point(item))
            self.assertTrue(item.isSelected())
            self.assertEqual(self.color(item), THEMES[light]['selected'])
            self.assertEqual(self.pixel(item), THEMES[light]['selected'])
            self.view.clear_highlight()
            item = self.view.items['carbon']
            self.assertTrue(item.isSelected())
            self.assertEqual(self.color(item), THEMES[light]['selected'])
            self.view.tree.clearSelection()
            # Restore visual live marker without modifying inventory.
            self.view.highlight = {'carbon': 1}
            self.view.render()

    def test_live_overrides_hover_and_clears_to_normal(self):
        for light in (False, True):
            self.theme(light)
            self.view.highlight = {'carbon': 1}
            self.view.render()
            item = self.view.items['carbon']
            self.hover(item)
            self.assertEqual(self.color(item), THEMES[light]['live'])
            self.assertEqual(self.pixel(item), THEMES[light]['live'])
            self.view.clear_highlight()
            self.assertEqual(self.color(self.view.items["carbon"]), THEMES[light]["hover"])
            QApplication.sendEvent(self.view.tree.viewport(), QEvent(QEvent.Type.Leave))
            item = self.view.items['carbon']
            self.assertEqual(self.color(item), THEMES[light]['rows'][item.data(0, STRIPE_ROLE)])

    def test_hover_is_visible_across_all_columns_and_leave_restores_rhythm(self):
        for light in (False, True):
            self.theme(light)
            item = self.view.items['carbon']
            self.hover(item)
            self.assertEqual([self.color(item, column) for column in range(4)], [THEMES[light]['hover']] * 4)
            self.assertEqual(self.pixel(item), THEMES[light]['hover'])
            QApplication.sendEvent(self.view.tree.viewport(), QEvent(QEvent.Type.Leave))
            self.assertEqual(self.color(item), THEMES[light]['rows'][item.data(0, STRIPE_ROLE)])

    def test_fill_bar_values_and_styles_are_unchanged_by_row_states(self):
        item = self.view.items['carbon']
        bar = self.view.tree.itemWidget(item, 3)
        before = (bar.value(), bar.format(), bar.styleSheet())
        self.assertTrue(bar.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents))
        self.hover(item)
        QTest.mouseClick(self.view.tree.viewport(), Qt.MouseButton.LeftButton, pos=self.point(item))
        self.assertEqual((bar.value(), bar.format(), bar.styleSheet()), before)

    def test_row_styles_do_not_modify_shared_column_configuration(self):
        header = self.view.tree.header()
        header.resizeSection(0, 410)
        header.moveSection(1, 3)
        saved = self.view.state.settings.value('materials/columns')
        self.theme(True)
        self.view.tabs.setCurrentIndex(2)
        self.assertEqual(self.view.state.settings.value('materials/columns'), saved)
        self.assertEqual([header.logicalIndex(i) for i in range(4)], saved['order'])
        self.assertEqual([header.sectionSize(i) for i in range(4)], saved['widths'])
