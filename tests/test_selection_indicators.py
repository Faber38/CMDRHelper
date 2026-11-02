"""Isolated paint/input regressions: no application state or live services."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from tempfile import TemporaryDirectory

from PySide6.QtCore import QEvent, QPoint, QSettings, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtTest import QTest, QSignalSpy
from PySide6.QtWidgets import (QApplication, QButtonGroup, QCheckBox, QHBoxLayout,
                              QLabel, QListWidget, QListWidgetItem, QMenu, QPushButton,
                              QProxyStyle, QRadioButton, QStyle, QTableWidget,
                              QTableWidgetItem, QTreeWidget, QTreeWidgetItem,
                              QStyleFactory, QStyleOptionButton, QVBoxLayout, QWidget)

from cmdrhelper.i18n import _TRANSLATIONS
from cmdrhelper.ui.selection_indicators import (
    SelectionIndicatorStyle, install_selection_indicators, set_selection_indicator_theme)
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class SelectionIndicatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.saved_sheet = self.app.styleSheet()
        self.saved_name = self.app.style().objectName() or "Fusion"
        self.widgets = []

    def tearDown(self):
        for widget in self.widgets:
            widget.close()
            widget.deleteLater()
        self.app.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.setStyleSheet("")
        self.app._selection_indicator_style = None
        self.app.setStyle(QStyleFactory.create(self.saved_name) or QStyleFactory.create("Fusion"))
        self.app.setStyleSheet(self.saved_sheet)

    def configure(self, native="Fusion", theme="dark", size=10, accent=True):
        self.app.setStyleSheet("")
        self.app._selection_indicator_style = None
        self.app.setStyle(QStyleFactory.create(native))
        if accent:
            install_selection_indicators(self.app)
        self.theme(theme, size)

    def theme(self, theme, size=10):
        set_selection_indicator_theme(self.app, theme)
        sheet = LIGHT_STYLESHEET if theme == "light" else DARK_STYLESHEET
        self.app.setStyleSheet(sheet + f"\nQWidget {{font-size:{size}pt;}}")

    def widget(self, kind, state=0, disabled=False):
        widget = QCheckBox("Auswahl") if kind == "check" else QRadioButton("Auswahl")
        if kind == "check":
            widget.setCheckState((Qt.Unchecked, Qt.PartiallyChecked, Qt.Checked)[state])
        else:
            widget.setAutoExclusive(False)
            widget.setChecked(state == 2)
        widget.setEnabled(not disabled)
        widget.resize(260, 40)
        self.widgets.append(widget)
        return widget

    @staticmethod
    def render(widget, extra=QStyle.State_None):
        widget.ensurePolished()
        option = QStyleOptionButton()
        widget.initStyleOption(option)
        option.state &= ~(QStyle.State_HasFocus | QStyle.State_MouseOver
                          | QStyle.State_KeyboardFocusChange)
        option.state |= extra
        check = isinstance(widget, QCheckBox)
        rect = widget.style().subElementRect(
            QStyle.SE_CheckBoxIndicator if check else QStyle.SE_RadioButtonIndicator,
            option, widget)
        image = QImage(widget.size(), QImage.Format_ARGB32)
        image.fill(option.palette.window().color())
        painter = QPainter(image)
        widget.style().drawControl(QStyle.CE_CheckBox if check else QStyle.CE_RadioButton,
                                   option, painter, widget)
        painter.end()
        return image, rect, widget.sizeHint()

    @staticmethod
    def without_indicator(image, rect):
        copy = image.copy()
        painter = QPainter(copy)
        painter.fillRect(rect, Qt.black)
        painter.end()
        return copy

    def test_pixels_geometry_glyphs_focus_and_hover(self):
        extras = (QStyle.State_None, QStyle.State_MouseOver,
                  QStyle.State_HasFocus | QStyle.State_KeyboardFocusChange)
        for native in ("Fusion", "Windows"):
            for theme in ("dark", "light"):
                for size in (10, 14, 18):
                    snapshots = {}
                    for accent in (False, True):
                        self.configure(native, theme, size, accent)
                        for kind, states in (("check", (0, 1, 2)), ("radio", (0, 2))):
                            for disabled in (False, True):
                                for state in states:
                                    widget = self.widget(kind, state, disabled)
                                    for extra in extras:
                                        key = kind, disabled, state, extra
                                        result = self.render(widget, extra)
                                        if not accent:
                                            snapshots[key] = result
                                            continue
                                        before, old_rect, old_hint = snapshots[key]
                                        after, rect, hint = result
                                        with self.subTest(native=native, theme=theme, size=size,
                                                          kind=kind, state=state,
                                                          disabled=disabled, extra=extra):
                                            self.assertEqual(rect, old_rect)
                                            self.assertEqual(hint, old_hint)
                                            self.assertEqual(self.without_indicator(before, rect),
                                                             self.without_indicator(after, rect))
                                            inner = rect.adjusted(3, 3, -3, -3)
                                            self.assertEqual(before.copy(inner), after.copy(inner))
                                            self.assertNotEqual(before.copy(rect), after.copy(rect))
                                    widget.deleteLater()
                                    self.widgets.remove(widget)
                        self.app.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_languages_input_and_late_created_widgets(self):
        self.configure()
        for theme in ("dark", "light"):
            for size in (10, 14, 18):
                self.theme(theme, size)
                for language, texts in _TRANSLATIONS.items():
                    with self.subTest(theme=theme, size=size, language=language):
                        window = QWidget()
                        window.resize(1024, 768)
                        layout = QVBoxLayout(window)
                        group = QButtonGroup(window)
                        radios = []
                        for key in ("browse.all_goods", "browse.mining", "browse.cargo_only"):
                            radio = QRadioButton(texts[key])
                            layout.addWidget(radio)
                            group.addButton(radio)
                            radios.append(radio)
                        check = QCheckBox(texts["recommend.local_only"])
                        disabled = QCheckBox(texts["trade.carriers"])
                        disabled.setEnabled(False)
                        layout.addWidget(check)
                        layout.addWidget(disabled)
                        layout.addStretch()
                        window.show()
                        window.activateWindow()
                        self.assertTrue(QTest.qWaitForWindowActive(window, 1000))
                        for widget in radios + [check, disabled]:
                            self.assertTrue(widget.property("accentIndicator"))
                            self.assertGreaterEqual(widget.width(), widget.sizeHint().width())
                        radios[0].setChecked(True)
                        radios[0].setFocus(Qt.TabFocusReason)
                        QTest.keyClick(radios[0], Qt.Key_Down)
                        self.assertTrue(radios[1].isChecked())
                        self.assertEqual(sum(r.isChecked() for r in radios), 1)
                        check.setFocus(Qt.TabFocusReason)
                        QTest.keyClick(check, Qt.Key_Space)
                        self.assertTrue(check.isChecked())
                        QTest.keyClick(check, Qt.Key_Tab)
                        self.assertFalse(disabled.hasFocus())
                        check.setFocus(Qt.TabFocusReason)
                        QTest.keyClick(check, Qt.Key_Backtab)
                        self.assertTrue(any(r.hasFocus() for r in radios))
                        rect = self.render(check)[1]
                        QTest.mouseClick(check, Qt.LeftButton, pos=rect.center())
                        self.assertFalse(check.isChecked())
                        QTest.mouseClick(check, Qt.LeftButton,
                                         pos=QPoint(rect.right() + 20, check.height() // 2))
                        self.assertTrue(check.isChecked())
                        QTest.mouseClick(disabled, Qt.LeftButton)
                        self.assertFalse(disabled.isChecked())
                        window.close()
                        window.deleteLater()
                        self.app.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_theme_repolish_does_not_emit_selection_signals(self):
        self.configure()
        for kind in ("check", "radio"):
            widget = self.widget(kind, 2)
            spy = QSignalSpy(widget.toggled)
            for theme in ("dark", "light", "dark"):
                self.theme(theme)
                for _ in range(3):
                    widget.style().unpolish(widget)
                    widget.style().polish(widget)
                image, rect, _ = self.render(widget)
                accent = QColor("#1565C0" if theme == "light" else "#FFCC33")
                pixels = [image.pixelColor(x, y) for x in range(rect.left(), rect.right() + 1)
                          for y in range(rect.top(), rect.bottom() + 1)]
                self.assertTrue(any(abs(c.hue() - accent.hue()) < 8 and c.saturation() > 80
                                    for c in pixels))
                self.assertTrue(widget.isChecked())
            self.assertEqual(spy.count(), 0)

    def test_dynamic_chronicle_fields_do_not_refresh_filters_when_polished(self):
        from cmdrhelper.ui.main_window import MainWindow
        self.configure()
        container = QWidget()
        self.widgets.append(container)
        layout = QHBoxLayout(container)
        layout.addWidget(QLabel("Commander"))
        layout.addWidget(QCheckBox("Alle"))
        layout.addStretch()
        changed = Mock()
        owner = SimpleNamespace(_chronicle_filter_ids=(), chronicle_commander_checks={},
                                chronicle_filter_layout=layout, ui_theme="dark",
                                _chronicle_filter_changed=changed,
                                _show_only_chronicle_commander=Mock(),
                                _update_chronicle_all_checkbox=Mock())
        MainWindow._sync_chronicle_filters(owner, [{"id": 1, "display_name": "Synthetic"}])
        for theme in ("dark", "light", "dark"):
            self.theme(theme)
            for widget in owner.chronicle_commander_checks.values():
                self.render(widget)
                self.assertTrue(widget.property("accentIndicator"))
        changed.assert_not_called()

    def test_explicit_and_local_style_exclusions(self):
        for theme in ("dark", "light"):
            snapshots = {}
            for accent in (False, True):
                self.configure(theme=theme, accent=accent)
                for special in ("explicit", "local", "pulse"):
                    for state in (0, 1, 2):
                        widget = self.widget("check", state)
                        if special == "local":
                            widget.setStyleSheet("QCheckBox::indicator {border:2px solid red;}")
                        else:
                            widget.setProperty("preserveSelectionIndicator", True)
                        if special == "pulse":
                            widget.setProperty("carrierConfirmPulse", True)
                        image, _, _ = self.render(widget)
                        key = special, state
                        if accent:
                            self.assertFalse(widget.property("accentIndicator"))
                            self.assertEqual(image, snapshots[key])
                        else:
                            snapshots[key] = image

    def test_unknown_style_falls_back_and_install_is_idempotent(self):
        self.configure()
        style = self.app._selection_indicator_style
        install_selection_indicators(self.app)
        self.assertIs(self.app._selection_indicator_style, style)
        self.app.setStyleSheet("")
        self.app._selection_indicator_style = None
        unknown = QProxyStyle(QStyleFactory.create("Fusion"))
        self.app.setStyle(unknown)
        install_selection_indicators(self.app)
        self.assertIs(self.app.style(), unknown)
        self.assertIsNone(self.app._selection_indicator_style)
        self.theme("light")
        widget = self.widget("check", 2)
        self.render(widget)
        self.assertFalse(widget.property("accentIndicator"))

    def test_production_special_widgets_keep_their_indicator_pixels(self):
        from cmdrhelper.route_planner.carrier_input_widget import CarrierInputWidget
        from cmdrhelper.ui.screenshot_view import ScreenshotView
        with TemporaryDirectory() as directory:
            settings = QSettings(directory + "/settings.ini", QSettings.IniFormat)
            for theme in ("dark", "light"):
                snapshots = {}
                for accent in (False, True):
                    self.configure(theme=theme, accent=accent)
                    carrier = CarrierInputWidget(SimpleNamespace())
                    with patch.multiple(ScreenshotView, _load_settings=Mock(),
                                        _sync_source=Mock(), _request_gallery_refresh=Mock(),
                                        _update_watch_state=Mock()):
                        screenshots = ScreenshotView(SimpleNamespace(settings=settings))
                    for name, widget in (("auto", screenshots.auto_check),
                                         ("delete", screenshots.delete_check),
                                         ("confirm", carrier.confirm)):
                        widget.resize(500, 40)
                        widget.blockSignals(True)
                        for enabled in (False, True):
                            widget.setEnabled(enabled)
                            for checked in (False, True):
                                widget.setChecked(checked)
                                for pulse in (False, True) if name == "confirm" else (False,):
                                    widget.setProperty("carrierConfirmPulse", pulse)
                                    widget.style().unpolish(widget)
                                    widget.style().polish(widget)
                                    image = self.render(widget)[0]
                                    key = name, enabled, checked, pulse
                                    if accent:
                                        self.assertFalse(widget.property("accentIndicator"))
                                        self.assertEqual(image, snapshots[key])
                                    else:
                                        snapshots[key] = image
                    carrier.close()
                    screenshots.close()
                    carrier.deleteLater()
                    screenshots.deleteLater()
                    self.app.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_market_theme_and_repaint_do_not_read_or_refilter(self):
        from test_saved_markets import ViewTests, MATE, MarketStore, ui
        self.configure()
        fixture = ViewTests()
        fixture.setUpClass()
        fixture.setUp()
        try:
            fixture.select(MATE)
            view = fixture.view
            selected = view._selected_id
            count = view.goods_proxy.rowCount()
            spy = QSignalSpy(view.goods_mode.buttonToggled)
            with patch.object(MarketStore, "get_current", side_effect=AssertionError("DB read")), \
                 patch.object(ui, "read_markets", side_effect=AssertionError("market reload")), \
                 patch.object(view, "filter_goods", side_effect=AssertionError("refilter")):
                for theme in ("light", "dark", "light"):
                    self.theme(theme)
                    for widget in (view.all_goods, view.mining_only, view.cargo_only):
                        self.render(widget)
                        self.assertTrue(widget.property("accentIndicator"))
                    self.app.processEvents()
                self.assertEqual(spy.count(), 0)
                self.assertEqual(view._selected_id, selected)
                self.assertEqual(view.goods_proxy.rowCount(), count)
        finally:
            fixture.doCleanups()

    def test_item_views_delegate_buttons_and_menu_keep_pixels(self):
        from cmdrhelper.ui.remembered_targets import RememberedTargetDelegate
        for theme in ("dark", "light"):
            snapshots = {}
            for accent in (False, True):
                self.configure(theme=theme, accent=accent)
                listing = QListWidget(objectName="shipCargoList")
                tree = QTreeWidget()
                tree.setHeaderHidden(True)
                table = QTableWidget(2, 1)
                table.setItemDelegate(RememberedTargetDelegate(table))
                menu = QMenu()
                button = QPushButton("Auswahl")
                button.setCheckable(True)
                button.setChecked(True)
                for row in range(2):
                    state = Qt.Checked if row else Qt.Unchecked
                    item = QListWidgetItem("Fracht", listing)
                    item.setCheckState(state)
                    item = QTreeWidgetItem(tree, ["Odyssey"])
                    item.setCheckState(0, state)
                    item = QTableWidgetItem("Merken")
                    item.setCheckState(state)
                    table.setItem(row, 0, item)
                    action = menu.addAction("System " + str(row))
                    action.setCheckable(True)
                    action.setChecked(bool(row))
                for name, widget in (("list", listing), ("tree", tree), ("table", table),
                                     ("menu", menu), ("button", button)):
                    widget.resize(280, 140)
                    widget.ensurePolished()
                    image = QImage(widget.size(), QImage.Format_ARGB32)
                    image.fill(Qt.transparent)
                    widget.render(image)
                    if accent:
                        self.assertFalse(widget.property("accentIndicator"))
                        self.assertEqual(image, snapshots[name], (theme, name))
                    else:
                        snapshots[name] = image
                    widget.deleteLater()
                self.app.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_checkbox_cell_widgets_are_not_opted_in(self):
        self.configure()
        table = QTableWidget(1, 1)
        self.widgets.append(table)
        cell = QCheckBox("Cell widget")
        table.setCellWidget(0, 0, cell)
        cell.ensurePolished()
        self.assertFalse(cell.property("accentIndicator"))


if __name__ == "__main__":
    unittest.main()
