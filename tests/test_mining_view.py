"""Offline mining references, numeric sorting and real QSettings persistence."""
import os
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QCollator, QLocale, QPoint, QSettings, Qt, QObject, Signal, QVariantAnimation, QEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QHeaderView, QDialog, QStyleOptionViewItem, QStyle
from PySide6.QtGui import QColor, QPalette
from cmdrhelper.ui.mining_carrier_dialog import CarrierStockDialog

from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.mining_catalog import MINING_COMMODITIES, value_class
from cmdrhelper.mining_inventory import MiningInventory
from cmdrhelper.ui.material_view import MaterialView
from cmdrhelper.ui.mining_view import MiningView
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.ui.material_row_style import THEMES
from test_material_view import StubController


class RefreshController(QObject):
    loading = Signal()
    ready = Signal(object)
    refreshFinished = Signal(str)

    def __init__(self):
        super().__init__()
        self.calls = 0

    def refresh_now(self):
        self.calls += 1


class MiningViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(set_language, get_language())
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        set_language("de")
        self.path = str(Path(self.tmp.name) / "settings.ini")
        self.view = self.make_view()
        self.view.tabs.setCurrentIndex(4)
        self.app.processEvents()

    def make_view(self):
        settings = QSettings(self.path, QSettings.Format.IniFormat)
        view = MaterialView(SimpleNamespace(settings=settings), controller=StubController(),
                            odyssey_controller=StubController())
        view.resize(1500, 650)
        view.show()
        self.app.processEvents()
        self.addCleanup(view.deleteLater)
        self.addCleanup(view.close)
        return view

    def values(self, column, view=None):
        tree = (view or self.view).mining.tree
        return [tree.topLevelItem(i).data(column, Qt.ItemDataRole.UserRole)
                for i in range(tree.topLevelItemCount())]

    def visible_items(self):
        tree = self.view.mining.tree
        return [tree.topLevelItem(i) for i in range(tree.topLevelItemCount())
                if not tree.topLevelItem(i).isHidden()]

    def visible_symbols(self):
        return {item.data(0, Qt.ItemDataRole.UserRole) for item in self.visible_items()}

    @staticmethod
    def numeric_sorted(values, reverse=False):
        return sorted((v for v in values if v is not None), reverse=reverse) + [None] * values.count(None)

    def test_origin_filter_combination_both_and_jadeite_live_stock(self):
        mining = self.view.mining
        for origin in ("all", "surface", "asteroid"):
            mining.set_origin_filter(origin)
            self.assertEqual(self.visible_symbols(), {c.symbol for c in MINING_COMMODITIES
                if origin == "all" or c.origin in (origin, "both")})
            self.assertIn("platinum", self.visible_symbols())
        mining.set_inventory(MiningInventory(1, "F1", vehicle={"jadeite": 60, "platinum": 12, "benitoite": 7}))
        mining.set_origin_filter("surface")
        mining.only_stock.setChecked(True)
        self.assertEqual(self.visible_symbols(), {"jadeite", "platinum"})
        self.assertEqual(mining.items["jadeite"].text(1), "60")
        self.assertEqual(mining.items["jadeite"].text(4), "41.895")
        mining.search.setText("Jadeit")
        mining.class_filter.setCurrentIndex(mining.class_filter.findData(1))
        self.assertEqual(self.visible_symbols(), {"jadeite"})
        mining.set_origin_filter("asteroid")
        self.assertFalse(self.visible_items())
        mining.search.clear()
        self.assertEqual(self.visible_symbols(), {"platinum"})
        mining.class_filter.setCurrentIndex(0)
        self.assertEqual(self.visible_symbols(), {"platinum", "benitoite"})
        item = mining.items["benitoite"]
        self.assertEqual(item.text(4), "—")
        self.assertEqual(item.text(5), "—")
        self.assertIsNone(item.data(4, Qt.ItemDataRole.UserRole))
        self.assertIsNone(item.data(5, Qt.ItemDataRole.UserRole))

    def test_origin_and_class_filters_persist_without_changing_header_settings(self):
        mining = self.view.mining
        mining.tree.header().resizeSection(2, 141)
        mining.tree.sortItems(4, Qt.SortOrder.AscendingOrder)
        layout = mining.settings.value("materials/mining/columns")
        sort = mining.settings.value(mining.SORT_KEY)
        mining.set_origin_filter("surface")
        mining.class_filter.setCurrentIndex(mining.class_filter.findData(1))
        mining.only_stock.setChecked(True)
        restarted = self.make_view().mining
        self.assertEqual(restarted.origin_filter.currentData(), "surface")
        self.assertEqual(restarted.class_filter.currentData(), 1)
        self.assertTrue(restarted.only_stock.isChecked())
        self.assertEqual(restarted.settings.value("materials/mining/columns"), layout)
        self.assertEqual(restarted.settings.value(mining.SORT_KEY), sort)
        self.assertEqual(restarted.tree.header().sectionSize(2), 141)
        restarted.set_origin_filter("asteroid")
        self.assertEqual(self.make_view().mining.origin_filter.currentData(), "asteroid")

    def test_search_localized_english_case_insensitive_and_clear(self):
        for query, expected in (("  KUPFER  ", {"copper"}), ("Copper", {"copper"}),
                                ("helium", {"helium", "helium3"}),
                                ("Low Temperature", {"lowtemperaturediamond"})):
            self.view.mining.search.setText(query)
            self.assertEqual(self.visible_symbols(), expected)
        self.view.mining.search.setText("no matching commodity")
        self.assertFalse(self.visible_items())
        self.assertTrue(self.view.mining.empty_label.isVisible())
        self.view.mining.search.clear()
        self.assertEqual(len(self.visible_items()), len(MINING_COMMODITIES))
        self.assertFalse(self.view.mining.empty_label.isVisible())

    def test_class_filter_and_combined_search(self):
        mining = self.view.mining
        for category, rank in (("high", 2), ("medium", 1), ("low", 0)):
            mining.class_filter.setCurrentIndex(mining.class_filter.findData(rank))
            expected = {c.symbol for c in MINING_COMMODITIES if value_class(c.average_price) == category}
            self.assertEqual(self.visible_symbols(), expected)
        mining.search.setText("Helium")
        self.assertFalse(self.visible_items())  # No low-value helium.
        mining.class_filter.setCurrentIndex(mining.class_filter.findData(1))
        self.assertEqual(self.visible_symbols(), {"helium3"})
        mining.class_filter.setCurrentIndex(mining.class_filter.findData(2))
        self.assertEqual(self.visible_symbols(), {"helium"})
        mining.class_filter.setCurrentIndex(0)
        self.assertEqual(self.visible_symbols(), {"helium", "helium3"})

    def test_sorting_and_settings_survive_combined_filters(self):
        mining = self.view.mining
        header = mining.tree.header()
        for column, width in enumerate((410, 95, 95, 95, 190, 175)):
            header.resizeSection(column, width)
        for column in (0, 4, 5):
            for order in (Qt.SortOrder.AscendingOrder, Qt.SortOrder.DescendingOrder):
                mining.tree.sortItems(column, order)
                saved_sort = self.view.state.settings.value(mining.SORT_KEY)
                saved_layout = self.view.state.settings.value("materials/mining/columns")
                mining.search.setText("i")
                mining.class_filter.setCurrentIndex(mining.class_filter.findData(1))
                items = self.visible_items()
                self.assertGreater(len(items), 2)
                if column == 0:
                    values = [item.text(0) for item in items]
                    expected = sorted(values, key=QCollator(QLocale("de")).sortKey,
                                      reverse=order == Qt.SortOrder.DescendingOrder)
                else:
                    values = [item.data(column, Qt.ItemDataRole.UserRole) for item in items]
                    expected = sorted(values, reverse=order == Qt.SortOrder.DescendingOrder)
                self.assertEqual(values, expected)
                # Changing sort with active filters keeps the same matching rows.
                symbols = self.visible_symbols()
                mining.tree.sortItems(column, Qt.SortOrder(1 - order.value))
                self.assertEqual(self.visible_symbols(), symbols)
                mining.tree.sortItems(column, order)
                mining.search.clear()
                mining.class_filter.setCurrentIndex(0)
                self.assertEqual(self.view.state.settings.value(mining.SORT_KEY), saved_sort)
                self.assertEqual(self.view.state.settings.value("materials/mining/columns"), saved_layout)
        restarted = self.make_view()
        self.assertEqual(restarted.state.settings.value(mining.SORT_KEY), saved_sort)
        self.assertEqual([restarted.mining.tree.header().sectionSize(i) for i in range(6)], [410, 95, 95, 95, 190, 175])

    def test_heading_count_is_derived_from_supplied_catalog(self):
        subset = MINING_COMMODITIES[:3]
        mining = MiningView(self.view.state.settings, commodities=iter(subset))
        self.addCleanup(mining.deleteLater)
        self.assertEqual(mining.summary.text(), tr("mining.count_summary", count=3))
        self.assertEqual(self.view.mining.summary.text(), tr("mining.count_summary", count=len(MINING_COMMODITIES)))
        self.assertEqual(mining.heading.text(), tr("mining.heading"))
        self.assertEqual(mining.notice.toolTip(), tr("mining.reference_notice"))

    def test_saved_phase_one_widths_are_preserved_and_right_side_stays_free(self):
        settings = self.view.state.settings
        settings.setValue("materials/mining/columns", {
            "version": 1, "columns": ["name", "average_price", "value_class"],
            "widths": [320, 180, 160], "order": [0, 1, 2],
        })
        settings.sync()
        restarted = self.make_view()
        restarted.resize(1500, 700)
        self.app.processEvents()
        mining = restarted.mining
        self.assertLessEqual(mining.content.width(), 1120)
        self.assertGreater(mining.width() - mining.content.width(), 300)
        self.assertEqual([mining.tree.header().sectionSize(i) for i in range(6)], [320, 95, 95, 95, 180, 160])
        self.assertFalse(mining.tree.header().stretchLastSection())

    def test_value_colors_and_price_format_in_both_themes(self):
        for light, colors in ((False, ("#8e969e", "#f0ad4e", "#79d45a")),
                              (True, ("#65717c", "#b36a00", "#37852d"))):
            self.app.setStyleSheet(LIGHT_STYLESHEET if light else DARK_STYLESHEET)
            self.view.set_light_mode(light)
            for item in self.visible_items():
                rank = item.data(5, Qt.ItemDataRole.UserRole)
                self.assertEqual(item.foreground(5).color().name(), colors[rank if rank is not None else 0])
                self.assertEqual(item.text(5).startswith("● "), rank is not None)
                self.assertNotIn("Cr", item.text(4))
                self.assertEqual(item.textAlignment(4), Qt.AlignmentFlag.AlignCenter)
                self.assertTrue(item.font(4).bold())
                self.assertEqual(item.foreground(4).style(), Qt.BrushStyle.NoBrush)

    def test_mining_tab_and_reference_rows(self):
        self.assertEqual(self.view.tabs.count(), 5)
        self.assertEqual(self.view.tabs.tabText(4), tr("mining.title"))
        tree = self.view.mining.tree
        self.assertEqual(tree.columnCount(), 6)
        self.assertEqual(tree.topLevelItemCount(), len(MINING_COMMODITIES))
        self.assertEqual(set(self.values(0)), {c.symbol for c in MINING_COMMODITIES})
        self.assertFalse(self.view.tree.isVisible())
        self.assertFalse(self.view.search.isVisible())
        self.assertFalse(self.view.filter.isVisible())
        self.assertFalse(self.view.trader_panel.search_button.isVisible())
        self.assertTrue(self.view.mining.isVisible())
        self.view.tabs.setCurrentIndex(3)
        self.assertFalse(self.view.mining.isVisible())
        self.assertTrue(self.view.odyssey.isVisible())
        self.view.tabs.setCurrentIndex(0)
        self.assertTrue(self.view.tree.isVisible())
        self.assertTrue(self.view.search.isVisible())

    def test_stock_columns_numeric_sort_unknown_last_and_live_updates_keep_filters(self):
        mining = self.view.mining
        inventory = MiningInventory(1, "F1", vehicle={"gold": 2, "copper": 120, "iridium": 10},
                                    carrier={"gold": 12, "copper": 0, "iridium": 5})
        mining.set_inventory(inventory)
        for column in (1, 2, 3):
            # Mix known and unknown rows to verify placement in both directions.
            mining.items["water"].setData(column, Qt.ItemDataRole.UserRole, None)
            for order in (Qt.SortOrder.AscendingOrder, Qt.SortOrder.DescendingOrder):
                mining.tree.sortItems(column, order)
                values = self.values(column)
                self.assertIsNone(values[-1])
                self.assertEqual(values[:-1], sorted(values[:-1], reverse=order == Qt.SortOrder.DescendingOrder))
        self.assertEqual(mining.items["gold"].text(3), "14")
        self.assertEqual(mining.items["gold"].textAlignment(5), Qt.AlignmentFlag.AlignCenter)
        self.assertEqual(mining.tree.headerItem().textAlignment(5), Qt.AlignmentFlag.AlignCenter)
        mining.search.setText("iridium")
        mining.class_filter.setCurrentIndex(mining.class_filter.findData(2))
        before = mining.tree.sortColumn(), mining.tree.header().sortIndicatorOrder()
        mining.set_inventory(MiningInventory(1, "F1", vehicle={"iridium": 17}))
        self.assertEqual(self.visible_symbols(), {"iridium"})
        self.assertEqual(mining.items["iridium"].text(1), "17")
        self.assertEqual(mining.items["iridium"].text(2), "— ✎")
        self.assertEqual(mining.items["iridium"].text(3), "—")
        self.assertEqual(mining.items["gold"].text(1), "0")
        self.assertEqual(before, (mining.tree.sortColumn(), mining.tree.header().sortIndicatorOrder()))

    def test_legacy_order_and_sort_identity_migrate_and_new_columns_move_persistently(self):
        settings = self.view.state.settings
        settings.setValue("materials/mining/columns", dict(version=1,
            columns=["name", "average_price", "value_class"], widths=[420, 185, 165], order=[2, 0, 1]))
        settings.setValue("materials/mining/sort", dict(column="value_class", direction="ascending"))
        settings.sync()
        restarted = self.make_view()
        header = restarted.mining.tree.header()
        self.assertEqual([header.logicalIndex(i) for i in range(6)], [5, 0, 1, 2, 3, 4])
        self.assertEqual([header.sectionSize(i) for i in (0, 4, 5)], [420, 185, 165])
        self.assertEqual(restarted.mining.tree.sortColumn(), 5)
        header.moveSection(header.visualIndex(2), 0)
        header.resizeSection(2, 123)
        again = self.make_view()
        self.assertEqual(again.mining.tree.header().logicalIndex(0), 2)
        self.assertEqual(again.mining.tree.header().sectionSize(2), 123)

    def test_value_class_boundaries(self):
        # Thresholds are independent of the currently bundled price snapshot.
        for price, expected in ((99_999, "medium"), (100_000, "high"),
                                (24_999, "low"), (25_000, "medium")):
            with self.subTest(price=price):
                self.assertEqual(value_class(price), expected)

    def test_default_price_descending_and_numeric_ascending(self):
        tree = self.view.mining.tree
        self.assertEqual(tree.sortColumn(), 4)
        self.assertEqual(tree.header().sortIndicatorOrder(), Qt.SortOrder.DescendingOrder)
        self.assertEqual(self.values(4), self.numeric_sorted(self.values(4), reverse=True))
        self.assertEqual(self.values(0)[0], "monazite")
        self.assertEqual(self.values(0)[self.values(4).index(496)], "water")
        tree.sortItems(4, Qt.SortOrder.AscendingOrder)
        self.assertEqual(self.values(4), self.numeric_sorted(self.values(4)))

    def test_header_clicks_sort_localized_names_both_directions(self):
        tree = self.view.mining.tree
        header = tree.header()
        position = QPoint(header.sectionViewportPosition(0) + 40, header.height() // 2)
        collator = QCollator(QLocale("de"))
        for _ in range(2):
            QTest.mouseClick(header.viewport(), Qt.MouseButton.LeftButton, pos=position)
            self.assertEqual(tree.sortColumn(), 0)
            names = [tree.topLevelItem(i).text(0) for i in range(tree.topLevelItemCount())]
            descending = header.sortIndicatorOrder() == Qt.SortOrder.DescendingOrder
            self.assertEqual(names, sorted(names, key=collator.sortKey, reverse=descending))

    def test_value_class_sort_has_semantic_order(self):
        tree = self.view.mining.tree
        for order in (Qt.SortOrder.AscendingOrder, Qt.SortOrder.DescendingOrder):
            tree.sortItems(5, order)
            self.assertEqual(self.values(5), self.numeric_sorted(self.values(5),
                             reverse=order == Qt.SortOrder.DescendingOrder))
            self.assertEqual(set(self.values(5)), {None, 0, 1, 2})

    def test_sort_survives_new_settings_instance_and_restart(self):
        for column in range(6):
            for order in (Qt.SortOrder.AscendingOrder, Qt.SortOrder.DescendingOrder):
                self.view.mining.tree.sortItems(column, order)
                self.view.close()
                restarted = self.make_view()
                self.assertEqual(restarted.tabs.currentIndex(), 4)
                self.assertEqual(restarted.mining.tree.sortColumn(), column)
                self.assertEqual(restarted.mining.tree.header().sortIndicatorOrder(), order)
                self.assertEqual(self.values(0, restarted), self.values(0))
                restarted.close()

    def test_mouse_widths_survive_hide_close_and_restart(self):
        header = self.view.mining.tree.header()
        self.assertFalse(header.stretchLastSection())
        for column in range(6):
            self.assertEqual(header.sectionResizeMode(column), QHeaderView.ResizeMode.Interactive)
            before = header.sectionSize(column)
            start = QPoint(header.sectionViewportPosition(column) + before - 1, header.height() // 2)
            end = start + QPoint(15, 0)
            QTest.mousePress(header.viewport(), Qt.MouseButton.LeftButton, pos=start)
            QTest.mouseMove(header.viewport(), end, 20)
            QTest.mouseRelease(header.viewport(), Qt.MouseButton.LeftButton, pos=end)
            self.assertGreater(header.sectionSize(column), before)
        expected = [header.sectionSize(i) for i in range(6)]
        self.view.tabs.setCurrentIndex(0)
        self.view.resize(1200, 700)
        self.view.tabs.setCurrentIndex(4)
        self.view.close()
        restarted = self.make_view()
        self.assertEqual([restarted.mining.tree.header().sectionSize(i) for i in range(6)], expected)

    def test_invalid_sort_settings_restore_default(self):
        for saved in ("bad", {}, {"column": "unknown", "direction": "ascending"},
                      {"column": "name", "direction": "invalid"}):
            self.view.state.settings.setValue("materials/mining/sort", saved)
            self.view.state.settings.sync()
            restarted = self.make_view()
            self.assertEqual(restarted.mining.tree.sortColumn(), 4)
            self.assertEqual(restarted.mining.tree.header().sortIndicatorOrder(), Qt.SortOrder.DescendingOrder)
            restarted.close()

    def test_five_row_tones_follow_live_theme_without_changing_layout(self):
        tree = self.view.mining.tree
        header = tree.header()
        widths = [header.sectionSize(i) for i in range(6)]
        for light, style in ((False, DARK_STYLESHEET), (True, LIGHT_STYLESHEET)):
            self.app.setStyleSheet(style)
            self.view.set_light_mode(light)
            self.app.processEvents()
            self.app.sendEvent(tree.viewport(), QEvent(QEvent.Type.Leave))
            tree.clearSelection()
            pixels = tree.viewport().grab().toImage()
            for row in range(6):
                rect = tree.visualItemRect(tree.topLevelItem(row))
                self.assertEqual(pixels.pixelColor(300, rect.center().y()).name(),
                                 THEMES[light]["rows"][row % 5])
            self.assertEqual([header.sectionSize(i) for i in range(6)], widths)
            self.assertEqual(self.values(4), self.numeric_sorted(self.values(4), reverse=True))

    def test_subtle_selection_hover_and_semantic_text_in_both_themes(self):
        mining = self.view.mining
        tree = mining.tree
        delegate = mining.carrier_delegate
        mining.set_inventory(MiningInventory(1, "F1", vehicle={"gold": 50}, carrier={"gold": 20}))
        mining.search.setText("gold")
        item = mining.items["gold"]
        for light, style in ((False, DARK_STYLESHEET), (True, LIGHT_STYLESHEET)):
            self.app.setStyleSheet(style)
            mining.set_light_mode(light)
            self.app.processEvents()
            rect = tree.visualItemRect(item)
            point = QPoint(300, rect.center().y())
            self.app.sendEvent(tree.viewport(), QEvent(QEvent.Type.Leave))
            tree.clearSelection()
            normal = tree.viewport().grab().toImage().pixelColor(point)
            self.assertEqual(normal.name(), THEMES[light]["rows"][0])
            QTest.mouseMove(tree.viewport(), QPoint(300, rect.bottom() + 5))
            QTest.mouseMove(tree.viewport(), point)
            hover = tree.viewport().grab().toImage().pixelColor(point)
            item.setSelected(True)
            selected = tree.viewport().grab().toImage().pixelColor(point)
            self.assertEqual(len({normal.name(), hover.name(), selected.name()}), 3)
            distance = lambda a, b: sum(abs(x - y) for x, y in zip(a.getRgb()[:3], b.getRgb()[:3]))
            self.assertGreater(distance(selected, normal), distance(hover, normal))
            self.assertLess(distance(selected, normal), 100)
            self.assertNotEqual(selected, tree.palette().color(QPalette.ColorRole.Highlight))
            for column in (1, 2, 3, 5):
                option = QStyleOptionViewItem()
                option.palette = tree.palette()
                option.palette.setColor(QPalette.ColorRole.Highlight, QColor("#00bfff"))
                option.state = QStyle.StateFlag.State_Selected | QStyle.StateFlag.State_MouseOver
                delegate.initStyleOption(option, tree.indexFromItem(item, column))
                self.assertFalse(option.state & QStyle.StateFlag.State_Selected)
                self.assertFalse(option.state & QStyle.StateFlag.State_MouseOver)
                self.assertEqual(option.palette.color(QPalette.ColorRole.Text), item.foreground(column).color())
                self.assertEqual(option.font.bold(), item.font(column).bold())
        # The rhythm follows visible sorted rows, not the original catalogue.
        mining.search.clear()
        tree.sortItems(0, Qt.SortOrder.AscendingOrder)
        mining.class_filter.setCurrentIndex(mining.class_filter.findData(0))
        self.app.sendEvent(tree.viewport(), QEvent(QEvent.Type.Leave))
        tree.clearSelection()
        for row, item in enumerate(self.visible_items()):
            option = QStyleOptionViewItem()
            delegate.initStyleOption(option, tree.indexFromItem(item))
            self.assertEqual(option.backgroundBrush.color().name(), THEMES[True]["rows"][row % 5])

    def test_stock_emphasis_in_both_themes_and_after_live_changes(self):
        mining = self.view.mining
        for light, style, green, muted in (
                (False, DARK_STYLESHEET, "#79d45a", "#8e969e"),
                (True, LIGHT_STYLESHEET, "#37852d", "#65717c")):
            self.app.setStyleSheet(style)
            mining.set_light_mode(light)
            for inventory, expected in (
                    (MiningInventory(1, "F1", vehicle={"gold": 50}, carrier={"gold": 20}), (50, 20, 70)),
                    (MiningInventory(1, "F1", vehicle={}, carrier={}), (0, 0, 0)),
                    (MiningInventory(1, "F1"), (None, None, None))):
                mining.set_inventory(inventory)
                for column, count in enumerate(expected, 1):
                    item = mining.items["gold"]
                    positive = count is not None and count > 0
                    self.assertEqual(item.font(column).bold(), positive)
                    self.assertEqual(item.foreground(column).color().name(), green if positive else muted)
                    text = str(count) if count is not None else "—"
                    self.assertEqual(item.text(column), text + " ✎" if column == 2 else text)
            mining.set_inventory(MiningInventory(1, "F1", vehicle={"gold": 50}))
            mining.set_light_mode(not light)
            self.assertEqual(mining.items["gold"].foreground(1).color().name(),
                             "#79d45a" if light else "#37852d")
            self.assertTrue(mining.items["gold"].font(1).bold())

    def test_only_stock_combines_filters_and_reacts_to_inventory_updates(self):
        mining = self.view.mining
        mining.set_inventory(MiningInventory(1, "F1", vehicle={"gold": 50, "uraninite": 60, "copper": 178}))
        self.assertFalse(mining.only_stock.isChecked())
        self.assertEqual(len(self.visible_items()), len(MINING_COMMODITIES))
        mining.only_stock.setChecked(True)
        self.assertEqual(self.visible_symbols(), {"gold", "uraninite", "copper"})
        self.assertEqual(mining.items["gold"].text(2), "— ✎")
        mining.class_filter.setCurrentIndex(mining.class_filter.findData(0))
        self.assertEqual(self.visible_symbols(), {"uraninite", "copper"})
        mining.search.setText("Kupfer")
        self.assertEqual(self.visible_symbols(), {"copper"})
        mining.set_inventory(MiningInventory(1, "F1", vehicle={"uraninite": 60}))
        self.assertFalse(self.visible_items())
        self.assertTrue(mining.empty_label.isVisible())
        mining.search.clear()
        self.assertEqual(self.visible_symbols(), {"uraninite"})
        mining.class_filter.setCurrentIndex(0)
        # A future known carrier inventory counts even when vehicle cargo is unknown.
        mining.set_inventory(MiningInventory(1, "F1", carrier={"gold": 7}))
        self.assertEqual(self.visible_symbols(), {"gold"})
        mining.set_inventory(MiningInventory(1, "F1"))
        self.assertFalse(self.visible_items())
        mining.only_stock.setChecked(False)
        self.assertEqual(len(self.visible_items()), len(MINING_COMMODITIES))

    def test_only_stock_sort_layout_and_filter_persist(self):
        mining = self.view.mining
        inventory = MiningInventory(1, "F1", vehicle={"gold": 50, "uraninite": 60, "copper": 178})
        mining.set_inventory(inventory)
        mining.tree.header().resizeSection(1, 123)
        saved_layout = mining.settings.value("materials/mining/columns")
        mining.only_stock.setChecked(True)
        for column in (0, 1, 4, 5):
            for order in (Qt.SortOrder.AscendingOrder, Qt.SortOrder.DescendingOrder):
                mining.tree.sortItems(column, order)
                items = self.visible_items()
                values = [item.text(0) if column == 0 else item.data(column, Qt.ItemDataRole.UserRole)
                          for item in items]
                self.assertEqual(values, sorted(values,
                    key=QCollator(QLocale("de")).sortKey if column == 0 else None,
                    reverse=order == Qt.SortOrder.DescendingOrder))
        saved_sort = mining.settings.value(mining.SORT_KEY)
        self.view.close()
        restarted = self.make_view().mining
        self.assertTrue(restarted.only_stock.isChecked())
        restarted.set_inventory(inventory)
        self.assertEqual(sum(not item.isHidden() for item in restarted.items.values()), 3)
        self.assertEqual(restarted.settings.value(mining.SORT_KEY), saved_sort)
        self.assertEqual(restarted.settings.value("materials/mining/columns"), saved_layout)
        self.assertEqual(restarted.tree.header().sectionSize(1), 123)
        restarted.only_stock.setChecked(False)
        self.assertFalse(self.make_view().mining.only_stock.isChecked())

    def make_refresh_view(self):
        controller = RefreshController()
        view = MiningView(self.view.state.settings, controller=controller)
        view.show()
        self.addCleanup(view.deleteLater)
        self.addCleanup(view.close)
        self.app.processEvents()
        return view, controller

    def test_refresh_feedback_success_animation_and_repeat_click_guard(self):
        view, controller = self.make_refresh_view()
        self.assertTrue(view.refresh_button.isEnabled())
        self.assertIn("#79d45a", view.refresh_button.styleSheet())
        self.assertEqual(view.refresh_animation.duration(), 1500)
        for result in ("updated", "unchanged"):
            before = controller.calls
            QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
            self.assertFalse(view.refresh_button.isEnabled())
            self.assertEqual(controller.calls, before + 1)
            QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
            self.assertEqual(controller.calls, before + 1)
            controller.ready.emit(MiningInventory(1, "F1", vehicle={"gold": 50}))
            self.assertEqual(view.items["gold"].text(1), "50")  # No animation delay for data.
            controller.refreshFinished.emit(result)
            self.assertFalse(view.refresh_button.isEnabled())
            view.refresh_animation.setCurrentTime(750)
            middle_style = view.refresh_button.styleSheet()
            view.refresh_animation.setCurrentTime(1500)
            self.assertNotEqual(middle_style, view.refresh_button.styleSheet())
            self.assertTrue(view.refresh_button.isEnabled())
            self.assertEqual(view._refresh_state, "ready")
            self.assertIn("#79d45a", view.refresh_button.styleSheet())
            self.assertEqual(view.refresh_status.text(), tr("mining.refresh_" + result))
            self.assertTrue(view.refresh_status_timer.isActive())
            self.assertEqual(view.refresh_status_timer.interval(), 2500)
            view.refresh_status_timer.setInterval(1)
            QTest.qWait(30)
            self.assertTrue(view.refresh_status.isHidden())
            view.refresh_status_timer.setInterval(2500)

    def test_refresh_error_recovers_and_theme_changes(self):
        view, controller = self.make_refresh_view()
        for light, red, green in ((False, "#ff6b6b", "#79d45a"), (True, "#b83232", "#37852d")):
            view.set_light_mode(light)
            QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
            controller.refreshFinished.emit("error")
            self.assertEqual(view.refresh_animation.state(), QVariantAnimation.State.Stopped)
            self.assertTrue(view.refresh_button.isEnabled())
            self.assertIn(red, view.refresh_button.styleSheet())
            self.assertEqual(view.refresh_status.text(), tr("mining.refresh_error"))
            self.assertFalse(view.refresh_status_timer.isActive())
            QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
            self.assertTrue(view.refresh_status.isHidden())
            controller.refreshFinished.emit("unchanged")
            view.refresh_animation.setCurrentTime(1500)
            self.assertIn(green, view.refresh_button.styleSheet())
            self.assertEqual(view.refresh_status.text(), tr("mining.refresh_unchanged"))

    def test_refresh_hide_close_and_slow_result_cleanup(self):
        view, controller = self.make_refresh_view()
        QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
        view.refresh_animation.setCurrentTime(1500)
        self.assertFalse(view.refresh_button.isEnabled())  # Real read still pending.
        view.hide()  # Same hide event as a tab switch.
        self.assertEqual(view.refresh_animation.state(), QVariantAnimation.State.Stopped)
        self.assertFalse(view.refresh_status_timer.isActive())
        controller.refreshFinished.emit("updated")
        self.assertTrue(view.refresh_button.isEnabled())
        self.assertFalse(view.refresh_status_timer.isActive())
        view.show()
        QTest.mouseClick(view.refresh_button, Qt.MouseButton.LeftButton)
        controller.refreshFinished.emit("unchanged")
        view.close()
        self.assertEqual(view.refresh_animation.state(), QVariantAnimation.State.Stopped)
        self.assertFalse(view.refresh_status_timer.isActive())
        self.assertTrue(view.refresh_button.isEnabled())

    def test_all_twelve_languages_have_same_mining_keys(self):
        # Commodity labels are translated alongside UI labels, without runtime I/O.
        expected = {"mining." + key for key in (
            "title", "name", "average_price", "value_class", "high", "medium", "low",
            "reference_notice", "open_tooltip", "heading", "count_summary",
            "reference_short", "search", "no_matches", "vehicle", "carrier", "total", "stock_unknown",
            "refresh", "refresh_tooltip", "only_stock", "only_stock_tooltip",
            "refresh_updated", "refresh_unchanged", "refresh_error",
            "origin", "origin_surface", "origin_asteroid", "reference_unknown")}
        expected.update("mining.carrier_" + key for key in (
            "edit", "amount", "unavailable", "reset", "apply", "invalid", "confirmed", "tracked", "inconsistent",
            "marked", "edit_hint", "header_help", "dialog_help", "baseline_unknown", "unknown_help"))
        expected.update(c.name_key for c in MINING_COMMODITIES)
        self.assertEqual(len(_TRANSLATIONS), 12)
        for language, translations in _TRANSLATIONS.items():
            self.assertEqual({k for k in translations if k.startswith("mining.")}, expected, language)
            self.assertTrue(all(translations[k].strip() for k in expected), language)

    def test_carrier_dialog_validation_cancel_apply_and_reset(self):
        dialog = CarrierStockDialog("Gold", None, True)
        self.addCleanup(dialog.deleteLater)
        for invalid in ("", "-1", "1.5", "foo", "2147483648"):
            dialog.input.setText(invalid)
            dialog._apply()
            self.assertEqual(dialog.result(), QDialog.DialogCode.Rejected)
            self.assertEqual(dialog.error.text(), tr("mining.carrier_invalid"))
        dialog.input.setText("504")
        dialog._apply()
        self.assertEqual(dialog.count, 504)
        self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
        dialog._reset()
        self.assertIsNone(dialog.count)
        dialog.reject()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Rejected)
        disabled = CarrierStockDialog("Gold", None, False)
        self.addCleanup(disabled.deleteLater)
        self.assertFalse(disabled.apply_button.isEnabled())
        self.assertFalse(disabled.reset_button.isEnabled())
        self.assertEqual(disabled.error.text(), tr("mining.carrier_unavailable"))

    def test_carrier_header_and_unknown_cell_explain_initial_confirmation(self):
        mining = self.view.mining
        self.assertEqual(mining.tree.headerItem().toolTip(2), tr("mining.carrier_header_help"))
        self.assertFalse(mining.tree.headerItem().toolTip(1))
        item = mining.items["gold"]
        self.assertIn(tr("mining.carrier_unknown_help"), item.toolTip(2))
        self.assertTrue(item.toolTip(2).startswith(tr("mining.carrier_edit_hint")))
        self.assertEqual(item.text(2), "— ✎")
        self.assertIsNone(item.data(2, Qt.ItemDataRole.UserRole))
        self.assertIsNone(item.data(3, Qt.ItemDataRole.UserRole))

    def test_carrier_dialog_help_is_muted_wrapped_and_available_in_both_themes(self):
        for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.app.setStyleSheet(style)
            for editable in (False, True):
                dialog = CarrierStockDialog("Gold", None, editable)
                self.addCleanup(dialog.deleteLater)
                self.addCleanup(dialog.close)
                dialog.show()
                self.app.processEvents()
                for label, key in ((dialog.help_text, "carrier_dialog_help"),
                                   (dialog.unknown_note, "carrier_baseline_unknown")):
                    self.assertEqual(label.text(), tr("mining." + key))
                    self.assertTrue(label.isVisible())
                    self.assertTrue(label.wordWrap())
                    self.assertEqual(label.objectName(), "muted")
                    self.assertLessEqual(label.width(), 420)
                self.assertIsNone(dialog.count)
                dialog.close()

    def test_carrier_help_preserves_confirmation_tracking_and_inconsistent_status(self):
        mining = self.view.mining
        for status, count in (("manual", 504), ("tracked", 454), ("inconsistent", None)):
            inventory = MiningInventory(1, "F1", vehicle={"gold": 60}, carrier={"gold": count},
                carrier_records={"gold": dict(count=count, status=status,
                    confirmed_at="2026-09-12T10:30:00.000Z")})
            mining.set_inventory(inventory)
            item = mining.items["gold"]
            tooltip = item.toolTip(2)
            self.assertIn("12.09.26", tooltip)
            self.assertNotIn(tr("mining.carrier_unknown_help"), tooltip)
            self.assertEqual(tr("mining.carrier_tracked") in tooltip, status == "tracked")
            self.assertEqual(tr("mining.carrier_inconsistent") in tooltip, status == "inconsistent")
            self.assertEqual(item.data(2, Qt.ItemDataRole.UserRole), count)
            self.assertEqual(item.data(3, Qt.ItemDataRole.UserRole), 60 + count if count is not None else None)
            self.assertEqual(inventory.carrier_records["gold"]["status"], status)

    def test_edit_markers_alignment_and_numeric_data(self):
        mining = self.view.mining
        mining.set_inventory(MiningInventory(1, "F1", vehicle={"gold": 2},
            carrier={"gold": 30, "copper": 100, "water": None}))
        self.assertEqual(mining.tree.headerItem().text(2), tr("mining.carrier_marked", value=tr("mining.carrier")))
        self.assertEqual(mining.items["gold"].text(2), "30 ✎")
        self.assertEqual(mining.items["water"].text(2), "— ✎")
        self.assertIsNone(mining.items["water"].data(2, Qt.ItemDataRole.UserRole))
        for column in range(6):
            expected = (Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                        if column == 0 else Qt.AlignmentFlag.AlignCenter)
            self.assertEqual(mining.tree.headerItem().textAlignment(column), expected)
            for item in mining.items.values():
                self.assertEqual(item.textAlignment(column), expected)
                self.assertTrue(item.toolTip(2).startswith(tr("mining.carrier_edit_hint")))
        for order in (Qt.SortOrder.AscendingOrder, Qt.SortOrder.DescendingOrder):
            mining.tree.sortItems(2, order)
            values = self.values(2)
            self.assertIsNone(values[-1])
            self.assertEqual(values[:-1], sorted(values[:-1], reverse=order == Qt.SortOrder.DescendingOrder))

    def test_carrier_hover_is_cell_local_and_theme_aware(self):
        mining = self.view.mining
        tree = mining.tree
        viewport = tree.viewport()
        for light, style, color in ((False, DARK_STYLESHEET, "#79d45a"), (True, LIGHT_STYLESHEET, "#37852d")):
            self.app.setStyleSheet(style)
            mining.set_light_mode(light)
            self.app.processEvents()
            row = tree.visualItemRect(tree.topLevelItem(0))
            x = tree.header().sectionViewportPosition(2) + 8
            position = QPoint(x, row.center().y())
            other = QPoint(tree.header().sectionViewportPosition(1) + 8, row.center().y())
            QTest.mouseMove(viewport, QPoint(x, row.bottom() + 5))
            self.app.sendEvent(viewport, QEvent(QEvent.Type.Leave))
            before = viewport.grab().toImage()
            QTest.mouseMove(viewport, position)
            self.app.processEvents()
            self.assertEqual(mining.carrier_delegate.color.name(), color)
            self.assertEqual(tree.indexAt(mining.carrier_delegate.hover_position).column(), 2)
            hovered = viewport.grab().toImage()
            self.assertNotEqual(before.pixelColor(position), hovered.pixelColor(position))
            self.assertNotEqual(before.pixelColor(other), hovered.pixelColor(other))
            self.assertNotEqual(hovered.pixelColor(position), hovered.pixelColor(other))
            self.app.sendEvent(viewport, QEvent(QEvent.Type.Leave))
            self.assertIsNone(mining.carrier_delegate.hover_position)
            self.assertEqual(before.pixelColor(position), viewport.grab().toImage().pixelColor(position))
        QTest.mouseMove(viewport, QPoint(x + 1, row.center().y()))
        self.view.tabs.setCurrentIndex(0)
        self.assertIsNone(mining.carrier_delegate.hover_position)

    def test_carrier_cell_double_click_dispatch_and_tooltips(self):
        view, controller = self.make_refresh_view()
        inventory = MiningInventory(1, "F1", vehicle={"gold": 60}, carrier={"gold": 504},
            carrier_id=123, carrier_feed={"path": "test"}, carrier_records={"gold": dict(
                count=504, status="manual", confirmed_at="2026-09-12T10:30:00.000Z")})
        controller.ready.emit(inventory)
        calls = []
        controller.confirm_carrier = lambda *args: calls.append(args)
        item = view.items["gold"]
        with patch.object(CarrierStockDialog, "exec", return_value=QDialog.DialogCode.Accepted):
            view.tree.itemDoubleClicked.emit(item, 1)
            self.assertFalse(calls)
            # Accepted reset uses None; cancel must never call the controller.
            view.tree.itemDoubleClicked.emit(item, 2)
            self.assertEqual(calls, [("gold", None, (1, "F1", 123))])
        with patch.object(CarrierStockDialog, "exec", return_value=QDialog.DialogCode.Rejected):
            view.tree.itemDoubleClicked.emit(item, 2)
            self.assertEqual(len(calls), 1)
        self.assertIn("12.09.26", item.toolTip(2))  # German locale's short date format.
        self.assertEqual(item.text(3), "564")
        for status, key in (("tracked", "carrier_tracked"), ("inconsistent", "carrier_inconsistent")):
            inventory.carrier_records["gold"]["status"] = status
            controller.ready.emit(inventory)
            self.assertIn(tr("mining." + key), item.toolTip(2))
