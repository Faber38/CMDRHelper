"""Persistent UI controls, table widths and cargo sizing in both app themes."""
import os
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QByteArray, QPoint, QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication, QLabel, QTableWidget, QWidget
from cmdrhelper.i18n import tr, set_language, _TRANSLATIONS
from cmdrhelper.ui.main_window import CargoLiveWindow, ExplorerLiveListWindow, MainWindow
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from cmdrhelper.ui.cargo_hud import cargo_hud_enabled
from cmdrhelper.mining_catalog import MINING_COMMODITIES


class PopupUiSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        set_language("de")
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / "settings.ini")
        self.settings = QSettings(self.path, QSettings.IniFormat)
        self.addCleanup(self.app.setStyleSheet, "")

    def keep(self, widget):
        self.addCleanup(widget.deleteLater)
        self.addCleanup(widget.close)
        return widget

    def popup(self, kind="bio", settings=None):
        return self.keep(ExplorerLiveListWindow("Test", ["Body", "BIO / GEO", "Progress", "Value"],
            settings or self.settings, f"explorer_live/{kind}_geometry", window_kind=kind))

    def main(self, settings=None):
        state = SimpleNamespace(settings=settings or self.settings, system="Test", system_address=1,
            system_bodies=[], database=SimpleNamespace(learned_bio_values=lambda: {}, biology_predictor=lambda: None),
            initializationStarted=Mock(), initializationProgress=Mock(), initializationFinished=Mock(),
            changed=Mock(), viewedCommanderChanged=Mock())
        with ExitStack() as stack:
            for name in ("_apply_saved_ui_font", "refresh_all", "_apply_cargo_hud_enabled"):
                stack.enter_context(patch.object(MainWindow, name))
            for name in ("_overview", "_missions", "_explorer", "_chronicle", "_score_page", "_settings"):
                stack.enter_context(patch.object(MainWindow, name, side_effect=lambda: QWidget()))
            stack.enter_context(patch("cmdrhelper.ui.main_window.QTimer.singleShot"))
            for name in ("RoutePlannerView", "ScreenshotView", "CommanderView"):
                stack.enter_context(patch("cmdrhelper.ui.main_window." + name, side_effect=lambda *a: QWidget()))
            main = self.keep(MainWindow(state))
        main._explorer_live_system = "Test"
        main._apply_cargo_hud_enabled = Mock()
        return main

    def explorer(self, main):
        with patch("cmdrhelper.ui.favorites_view.FavoritesView", side_effect=lambda *a, **kw: QWidget()):
            return self.keep(main._explorer())

    def test_progress_body_names_and_colors_in_dark_and_light(self):
        for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.app.setStyleSheet(style)
            popup = self.popup()
            popup.set_rows("Test", [dict(body_name="3 a a", signals=4, geo_signals=2, species=[
                dict(name="One", scan_type="Log"), dict(name="Two", scan_type="Sample"),
                dict(name="Three", scan_type="Analyse")])])
            popup.show()
            self.app.processEvents()
            self.assertEqual(popup.table.palette().color(QPalette.Text).name(), "#f1f3f5")
            self.assertTrue(all(popup.table.item(i, 0).text() == "3 a a"
                                for i in range(popup.table.rowCount())))
            for row, text, color in [(1, "1/3", "#ffb000"), (2, "2/3", "#68c7ff"),
                                     (3, "3/3 · Fertig", "#65d067")]:
                item = popup.table.item(row, 2)
                self.assertEqual(item.text(), text)
                self.assertEqual(item.foreground().color().name(), color)
            popup.set_rows("Test", [dict(body_name="4 b", signals=1, species=[
                dict(name="Done", scan_type="Analyse")])])
            self.assertEqual(popup.table.item(1, 2).text(), "Fertig")
            self.assertEqual(popup.table.item(1, 2).foreground().color().name(), "#65d067")
            self.assertFalse(popup.grab().isNull())

    def test_mining_legend_and_body_cell_open_central_materials_tab(self):
        main = self.main()
        explorer = self.explorer(main)
        main.pages.removeWidget(main.pages.widget(main.PAGE_EXPLORER))
        main.pages.insertWidget(main.PAGE_EXPLORER, explorer)
        main.state.system_bodies = [dict(name="Test 1", short_name="1", body_id=1,
                                        planetary_mining_signals=12)]
        main._refresh_explorer_tables()
        main.resize(1300, 850)
        main.show()
        main._show_page(main.PAGE_EXPLORER)
        main.explorer_tabs.setCurrentIndex(2)
        self.app.processEvents()
        item = main.explorer_bio_table.item(0, 4)
        self.assertEqual(item.text(), "ABBAU ×12")
        QTest.mouseClick(main.explorer_bio_table.viewport(), Qt.MouseButton.LeftButton,
                         pos=main.explorer_bio_table.visualItemRect(item).center())
        self.assertEqual(main.pages.currentIndex(), main.PAGE_MATERIALS)
        self.assertEqual(main.material_view.CATEGORIES[main.material_view.tabs.currentIndex()], "Mining")
        mining = main.material_view.mining
        self.assertEqual(mining.origin_filter.currentData(), "surface")
        mining.set_origin_filter("asteroid")
        main._show_page(main.PAGE_EXPLORER)
        main.material_view.tabs.setCurrentIndex(0)
        main.mining_legend_label.linkActivated.emit("mining")
        self.assertEqual(main.pages.currentIndex(), main.PAGE_MATERIALS)
        self.assertEqual(main.material_view.tabs.currentIndex(), 4)
        self.assertIs(main.material_view.mining, mining)
        self.assertEqual(mining.tree.topLevelItemCount(), len(MINING_COMMODITIES))
        self.assertEqual(mining.origin_filter.currentData(), "surface")
        main._show_page(main.PAGE_EXPLORER)
        main._explorer_mining_clicked(main.explorer_bio_table.item(0, 0))
        self.assertEqual(main.pages.currentIndex(), main.PAGE_EXPLORER)
        item.setData(Qt.UserRole, dict(planetary_mining_signals=0))
        main._explorer_mining_clicked(item)
        self.assertEqual(main.pages.currentIndex(), main.PAGE_EXPLORER)

    def test_mining_legend_keeps_normal_typography_and_whole_label_click_in_both_themes(self):
        main = self.main()
        explorer = self.explorer(main)
        main.pages.removeWidget(main.pages.widget(main.PAGE_EXPLORER))
        main.pages.insertWidget(main.PAGE_EXPLORER, explorer)
        main.resize(1500, 900)
        main.show()
        label = main.mining_legend_label
        expected = ('<span style="color:#ff9d00; font-size:14px; '
                    'font-weight:700;">ABBAU ×N</span> '
                    f'<span style="font-size:11px;">{tr("explorer.legend_planetary_mining")}</span>')
        self.assertEqual(label.text(), expected)
        self.assertNotIn('<a ', label.text())
        self.assertNotIn('underline', label.text())
        self.assertEqual(label.cursor().shape(), Qt.PointingHandCursor)
        reference = self.keep(QLabel(expected, label.parentWidget()))
        reference.setTextFormat(Qt.RichText)
        reference.setWordWrap(True)
        reference.hide()
        for style, color in ((DARK_STYLESHEET, '#d8dde3'), (LIGHT_STYLESHEET, '#20262c')):
            self.app.setStyleSheet(style)
            main._show_page(main.PAGE_EXPLORER)
            main.explorer_tabs.setCurrentIndex(0)
            self.app.processEvents()
            self.assertTrue(label.isVisible())
            self.assertEqual(label.palette().color(QPalette.WindowText).name(), color)
            self.assertEqual(label.sizeHint(), reference.sizeHint())
            self.assertEqual(label.heightForWidth(label.width()), reference.heightForWidth(label.width()))
            for position in (QPoint(2, 2), label.rect().center(),
                             QPoint(label.width() - 2, label.height() - 2)):
                main._show_page(main.PAGE_EXPLORER)
                self.app.processEvents()
                QTest.mouseClick(label, Qt.RightButton, pos=position)
                self.assertEqual(main.pages.currentIndex(), main.PAGE_EXPLORER)
                QTest.mouseClick(label, Qt.LeftButton, pos=position)
                self.assertEqual(main.pages.currentIndex(), main.PAGE_MATERIALS)
                self.assertEqual(main.material_view.tabs.currentIndex(), 4)
                mining = main.material_view.mining
                self.assertEqual(mining.origin_filter.currentData(), 'surface')
                mining.set_origin_filter('asteroid')

    def test_geo_and_bio_controls_filter_one_popup_and_persist(self):
        main = self.main()
        self.explorer(main)
        main.state.system_bodies = [dict(name="Test 1", short_name="1", biological_signals=2,
                                        geological_signals=3, biology=[dict(species="Test bio", scan_type="Log")])]
        for bio, geo in [(True, False), (True, True), (False, True), (False, False), (True, False)]:
            main.explorer_bio_live_enabled_check.setChecked(bio)
            main.explorer_geo_live_enabled_check.setChecked(geo)
            main._refresh_explorer_live_windows()
            popup = main._explorer_bio_live_window
            texts = [popup.table.cellWidget(i, 1).text() for i in range(popup.table.rowCount())
                     if popup.table.cellWidget(i, 1)]
            self.assertEqual(any('BIO ×' in text for text in texts), bio)
            self.assertEqual(any('GEO ×' in text for text in texts), geo)
            self.assertEqual(popup.isVisible(), bio or geo)
        restored = self.main(QSettings(self.path, QSettings.IniFormat))
        self.assertFalse(restored.explorer_geo_live_enabled_check.isChecked())
        self.assertTrue(restored.explorer_bio_live_enabled_check.isChecked())
        main.state.system = "Next"
        main._refresh_explorer_live_windows()
        self.assertFalse(main._explorer_bio_live_window.isVisible())
        self.assertEqual(main._explorer_bio_live_window.table.rowCount(), 0)

    def test_existing_disabled_bio_popup_does_not_enable_geo_on_upgrade(self):
        self.settings.setValue("explorer_live/bio_enabled", False)
        main = self.main()
        self.assertFalse(main.explorer_geo_live_enabled_check.isChecked())
        main.explorer_bio_live_enabled_check.setChecked(True)
        self.assertFalse(main._explorer_live_window_enabled("geo"))
        restored = self.main(QSettings(self.path, QSettings.IniFormat))
        self.assertFalse(restored.explorer_geo_live_enabled_check.isChecked())

    def test_popup_widths_restore_separately_and_keep_geometry(self):
        for kind, widths in [("bio", [123, 234, 145, 156]), ("value", [151, 251, 161, 171])]:
            popup = self.popup(kind)
            popup.show()
            popup.resize(640, 320)
            popup.move(90, 110)
            for i, width in enumerate(widths):
                popup.table.setColumnWidth(i, width)
            self.app.processEvents()
            position, size = popup.pos(), popup.size()
            popup.close()
            restored = self.popup(kind, QSettings(self.path, QSettings.IniFormat))
            restored.show()
            self.app.processEvents()
            self.assertEqual([restored.table.columnWidth(i) for i in range(4)], widths)
            self.assertEqual(restored.size(), size)
            self.assertEqual(restored.pos(), position)

    def test_explorer_bio_geo_mining_widths_survive_new_settings_instance(self):
        main = self.main()
        self.explorer(main)
        table = main.explorer_bio_table
        widths = [140, 160, 50, 310, 90, 330, 130, 100, 95, 110, 100]
        self.assertEqual([table.columnWidth(i) for i in range(11)], widths)
        for i in range(11):
            table.setColumnWidth(i, 70 + i * 11)
        restored = self.main(QSettings(self.path, QSettings.IniFormat))
        self.explorer(restored)
        self.assertEqual([restored.explorer_bio_table.columnWidth(i) for i in range(11)],
                         [70 + i * 11 for i in range(11)])

    def test_invalid_widths_and_legacy_header_are_defensive(self):
        for invalid in ([0, 100, 100, 100], [1, 2], "bad", [90, -2, 100, 100],
                        [90, 3000, 100, 100], [True, 100, 100, 100], [90, "x", 100, 100]):
            self.settings.setValue("explorer_live/bio_geometry_column_widths", invalid)
            popup = self.popup()
            self.assertEqual([popup.table.columnWidth(i) for i in range(4)], [90, 330, 150, 130])
        self.settings.remove("explorer_live/bio_geometry_column_widths")
        for legacy in (QByteArray(b"bad"), "not bytes"):
            self.settings.setValue("explorer_live/bio_geometry_header_state", legacy)
            popup = self.popup()
            self.assertEqual(popup.table.columnWidth(0), 90)
        old = self.keep(QTableWidget(0, 4))
        for i in range(4):
            old.setColumnWidth(i, 160 + i)
        self.settings.setValue("explorer_live/bio_geometry_header_state", old.horizontalHeader().saveState())
        popup = self.popup()
        self.assertEqual([popup.table.columnWidth(i) for i in range(4)], [160, 161, 162, 163])
        old.hideColumn(1)
        self.settings.setValue("explorer_live/bio_geometry_header_state", old.horizontalHeader().saveState())
        popup = self.popup()
        self.assertEqual([popup.table.columnWidth(i) for i in range(4)], [90, 330, 150, 130])
        self.settings.setValue("explorer/bio_geo_mining_column_widths", [0] * 11)
        main = self.main()
        self.explorer(main)
        self.assertEqual(main.explorer_bio_table.columnWidth(0), 140)
        self.assertTrue(all(main.explorer_bio_table.columnWidth(i) >= 40 for i in range(11)))

    def test_cargo_heights_scrollbar_width_and_position_in_both_themes(self):
        for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.app.setStyleSheet(style)
            cargo = self.keep(CargoLiveWindow(self.settings))
            cargo.show()
            cargo.resize(431, 300)
            cargo.move(120, 130)
            self.app.processEvents()
            position = cargo.pos()
            heights = []
            for count in (0, 1, 5, 100, 1, 0):
                cargo.set_snapshot(dict(vessel="SRV", count=67, capacity=72,
                    inventory=[dict(display_name=f"Cargo {i}", count=1) for i in range(count)]))
                self.app.processEvents()
                heights.append(cargo.height())
                self.assertEqual(cargo.table.palette().color(QPalette.Text).name(), "#f1f3f5")
                self.assertEqual(cargo.width(), 431)
                self.assertEqual(cargo.pos(), position)
                self.assertEqual(cargo.summary_label.text(), "67 / 72 t")
                self.assertEqual(cargo.fill_bar.height(), 8)
                self.assertTrue(cargo.fill_bar.isVisible())
                self.assertEqual(cargo.table.verticalScrollBar().isVisible(), count == 100)
                self.assertFalse(cargo.grab().isNull())
            self.assertEqual(heights[0], heights[-1])
            self.assertLess(heights[0], heights[2])
            self.assertLess(heights[2], heights[3])
            self.assertLessEqual(heights[3], 560)
            self.assertLess(heights[1], 220)

    def test_cargo_hud_checkbox_exists_only_in_auto_show_and_reuses_key(self):
        main = self.main()
        frame = main.auto_show_frame
        check = main.cargo_hud_enabled_check
        self.assertIs(check.parent(), frame)
        self.assertFalse(check.isChecked())
        check.setChecked(True)
        main._apply_cargo_hud_enabled.assert_called_once()
        restored = self.main(QSettings(self.path, QSettings.IniFormat))
        self.assertTrue(restored.cargo_hud_enabled_check.isChecked())
        cargo = self.keep(CargoLiveWindow(self.settings))
        self.assertFalse(hasattr(cargo, "hud_enabled_check"))
        for vessel in ("Ship", "SRV", "Ship"):
            cargo.set_snapshot(dict(vessel=vessel, count=0, capacity=72))
            self.assertTrue(restored.cargo_hud_enabled_check.isChecked())
            self.assertTrue(cargo_hud_enabled(restored.state.settings))
        restored.cargo_hud_enabled_check.setChecked(False)
        self.assertFalse(cargo_hud_enabled(QSettings(self.path, QSettings.IniFormat)))

    def test_new_labels_are_translated_in_all_twelve_languages(self):
        self.assertEqual(len(_TRANSLATIONS), 12)
        for language in _TRANSLATIONS:
            set_language(language)
            for key in ("settings.explorer_geo_live_window", "explorer.scan_done", "settings.cargo_hud"):
                self.assertIn(key, _TRANSLATIONS[language])
                self.assertNotEqual(tr(key), key)
        set_language("de")
