"""Cursor policy exercised through real widget events, without application data."""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QCursor, QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QGroupBox, QLabel, QLineEdit,
    QMenu, QPlainTextEdit, QPushButton, QRadioButton, QSlider, QSpinBox,
    QSplitter, QTabBar, QTableWidget, QTableWidgetItem, QTextBrowser,
    QTextEdit, QToolButton, QVBoxLayout, QWidget,
)

from cmdrhelper.ui.cursors import install_cursor_policy


class CursorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.owns_policy = not hasattr(cls.app, "_cmdrhelper_cursor_policy")
        cls.policy = install_cursor_policy(cls.app)

    @classmethod
    def tearDownClass(cls):
        if cls.owns_policy:
            cls.app.removeEventFilter(cls.policy)
            del cls.app._cmdrhelper_cursor_policy
            cls.policy.deleteLater()

    def widget(self, cls, *args):
        widget = cls(*args)
        self.addCleanup(widget.deleteLater)
        self.addCleanup(widget.close)
        widget.resize(320, 180)
        widget.show()
        self.app.processEvents()
        return widget

    def move(self, widget, point):
        event = QMouseEvent(QEvent.MouseMove, point, widget.mapToGlobal(point),
                            Qt.NoButton, Qt.NoButton, Qt.NoModifier)
        self.app.sendEvent(widget, event)
        self.app.processEvents()

    def test_buttons_checkboxes_radio_sliders_and_combo_use_hand(self):
        for cls in (QPushButton, QToolButton, QCheckBox, QRadioButton, QSlider, QComboBox, QSpinBox):
            with self.subTest(widget=cls.__name__):
                widget = self.widget(cls)
                self.assertEqual(widget.cursor().shape(), Qt.PointingHandCursor)
                widget.setEnabled(False)
                self.assertEqual(widget.cursor().shape(), Qt.ArrowCursor)
                widget.setEnabled(True)
                self.assertEqual(widget.cursor().shape(), Qt.PointingHandCursor)

    def test_inputs_and_editable_combo_keep_text_cursor(self):
        for cls in (QLineEdit, QTextEdit, QPlainTextEdit):
            widget = self.widget(cls)
            target = widget if isinstance(widget, QLineEdit) else widget.viewport()
            self.move(target, QPoint(10, 10))
            self.assertEqual(target.cursor().shape(), Qt.IBeamCursor)
            widget.setEnabled(False)
            self.assertEqual(target.cursor().shape(), Qt.ArrowCursor)
            widget.setEnabled(True)
            self.move(target, QPoint(10, 10))
            self.assertEqual(target.cursor().shape(), Qt.IBeamCursor)
        combo = self.widget(QComboBox)
        combo.setEditable(True)
        self.app.processEvents()
        self.assertEqual(combo.cursor().shape(), Qt.PointingHandCursor)
        self.assertEqual(combo.lineEdit().cursor().shape(), Qt.IBeamCursor)
        combo.setEnabled(False)
        self.assertEqual(combo.lineEdit().cursor().shape(), Qt.ArrowCursor)

    def test_disabled_parent_restores_children_and_explicit_clickable_label(self):
        parent = self.widget(QWidget)
        layout = QVBoxLayout(parent)
        button, label, edit = QPushButton("Click"), QLabel("Clickable"), QLineEdit()
        label.setCursor(Qt.PointingHandCursor)
        for widget in (button, label, edit):
            layout.addWidget(widget)
        self.app.processEvents()
        parent.setEnabled(False)
        for widget in (button, label, edit):
            self.assertEqual(widget.cursor().shape(), Qt.ArrowCursor)
        parent.setEnabled(True)
        self.assertEqual(button.cursor().shape(), Qt.PointingHandCursor)
        self.assertEqual(label.cursor().shape(), Qt.PointingHandCursor)
        self.assertEqual(edit.cursor().shape(), Qt.IBeamCursor)

    def test_item_view_hit_testing_and_editors(self):
        table = self.widget(QTableWidget, 3, 1)
        table.setItem(0, 0, QTableWidgetItem("Click"))
        disabled = QTableWidgetItem("Disabled")
        disabled.setFlags(disabled.flags() & ~Qt.ItemIsEnabled)
        table.setItem(1, 0, disabled)
        passive = QTableWidgetItem("Passive")
        passive.setFlags(Qt.ItemIsEnabled)
        table.setItem(2, 0, passive)
        self.app.processEvents()
        for row, shape in ((0, Qt.PointingHandCursor), (1, Qt.ArrowCursor), (2, Qt.ArrowCursor)):
            self.move(table.viewport(), table.visualItemRect(table.item(row, 0)).center())
            self.assertEqual(table.viewport().cursor().shape(), shape)
        self.move(table.viewport(), QPoint(250, 140))
        self.assertEqual(table.viewport().cursor().shape(), Qt.ArrowCursor)
        table.editItem(table.item(0, 0))
        self.app.processEvents()
        editor = table.findChild(QLineEdit)
        self.assertIsNotNone(editor)
        self.assertEqual(editor.cursor().shape(), Qt.IBeamCursor)

    def test_readonly_table_and_spinbox_do_not_suggest_edit_actions(self):
        table = self.widget(QTableWidget, 1, 1)
        item = QTableWidgetItem("Read only")
        table.setItem(0, 0, item)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        point = table.visualItemRect(item).center()
        self.move(table.viewport(), point)
        self.assertEqual(table.viewport().cursor().shape(), Qt.ArrowCursor)
        item.setCheckState(Qt.Unchecked)
        self.move(table.viewport(), point)
        self.assertEqual(table.viewport().cursor().shape(), Qt.PointingHandCursor)
        spin = self.widget(QSpinBox)
        spin.setReadOnly(True)
        self.move(spin, QPoint(spin.width()-10, 10))
        self.assertEqual(spin.cursor().shape(), Qt.ArrowCursor)
        self.assertEqual(spin.lineEdit().cursor().shape(), Qt.IBeamCursor)

    def test_checkable_group_only_marks_its_toggle_not_passive_contents(self):
        from PySide6.QtWidgets import QStyle, QStyleOptionGroupBox
        group = self.widget(QGroupBox, "Toggle")
        group.setCheckable(True)
        label = QLabel("Passive", group)
        label.setGeometry(20, 50, 100, 30)
        label.show()
        option = QStyleOptionGroupBox()
        group.initStyleOption(option)
        rect = group.style().subControlRect(QStyle.CC_GroupBox, option, QStyle.SC_GroupBoxCheckBox, group)
        self.move(group, rect.center())
        self.assertEqual(group.cursor().shape(), Qt.PointingHandCursor)
        self.move(label, label.rect().center())
        self.assertEqual(label.cursor().shape(), Qt.ArrowCursor)

    def test_label_links_keep_native_hit_testing(self):
        label = self.widget(QLabel, '<a href="https://example.invalid">Link</a> plain')
        label.setTextInteractionFlags(Qt.LinksAccessibleByMouse)
        self.move(label, QPoint(10, label.height()//2))
        self.assertEqual(label.cursor().shape(), Qt.PointingHandCursor)
        self.move(label, QPoint(200, label.height()//2))
        self.assertEqual(label.cursor().shape(), Qt.ArrowCursor)

    def test_tabs_and_menu_actions_respect_disabled_targets(self):
        tabs = self.widget(QTabBar)
        tabs.addTab("Enabled")
        tabs.addTab("Disabled")
        tabs.setTabEnabled(1, False)
        self.move(tabs, tabs.tabRect(0).center())
        self.assertEqual(tabs.cursor().shape(), Qt.PointingHandCursor)
        self.move(tabs, tabs.tabRect(1).center())
        self.assertEqual(tabs.cursor().shape(), Qt.ArrowCursor)
        menu = self.widget(QMenu)
        action = menu.addAction("Enabled")
        disabled = menu.addAction("Disabled")
        disabled.setEnabled(False)
        menu.adjustSize()
        self.move(menu, menu.actionGeometry(action).center())
        self.assertEqual(menu.cursor().shape(), Qt.PointingHandCursor)
        self.move(menu, menu.actionGeometry(disabled).center())
        self.assertEqual(menu.cursor().shape(), Qt.ArrowCursor)

    def test_text_browser_links_use_hand_only_over_link(self):
        browser = self.widget(QTextBrowser)
        browser.setHtml('<a href="https://example.invalid">Link</a><p>Plain text</p>')
        viewport = browser.viewport()
        point = next(QPoint(x, y) for y in range(4, 25) for x in range(4, 45)
                     if browser.anchorAt(QPoint(x, y)))
        self.move(viewport, point)
        self.assertEqual(viewport.cursor().shape(), Qt.PointingHandCursor)
        self.move(viewport, QPoint(200, 100))
        self.assertEqual(viewport.cursor().shape(), Qt.IBeamCursor)
        browser.setEnabled(False)
        self.assertEqual(viewport.cursor().shape(), Qt.ArrowCursor)

    def test_passive_widgets_and_special_resize_pan_cursors_are_preserved(self):
        for cls in (QWidget, QLabel):
            widget = self.widget(cls)
            self.assertEqual(widget.cursor().shape(), Qt.ArrowCursor)
        widget = self.widget(QWidget)
        for shape in (Qt.OpenHandCursor, Qt.ClosedHandCursor, Qt.SizeHorCursor, Qt.SizeVerCursor, Qt.WaitCursor):
            widget.setCursor(shape)
            self.move(widget, QPoint(30, 30))
            self.assertEqual(widget.cursor().shape(), shape)
            widget.setEnabled(False)
            self.assertEqual(widget.cursor().shape(), Qt.ArrowCursor)
            widget.setEnabled(True)
            self.assertEqual(widget.cursor().shape(), shape)
        splitter = self.widget(QSplitter)
        splitter.addWidget(QWidget())
        splitter.addWidget(QWidget())
        self.app.processEvents()
        handle = splitter.handle(1)
        original = handle.cursor().shape()
        self.move(handle, handle.rect().center())
        self.assertEqual(handle.cursor().shape(), original)

    def test_native_header_resize_and_sort_area(self):
        table = self.widget(QTableWidget, 1, 2)
        table.setSortingEnabled(True)
        header = table.horizontalHeader()
        viewport = header.viewport()
        self.move(viewport, QPoint(30, 10))
        self.assertEqual(viewport.cursor().shape(), Qt.PointingHandCursor)
        self.move(viewport, QPoint(header.sectionSize(0) - 1, 10))
        self.assertIn(viewport.cursor().shape(), (Qt.SplitHCursor, Qt.SizeHorCursor))
        self.move(viewport, QPoint(30, 10))
        self.assertEqual(viewport.cursor().shape(), Qt.PointingHandCursor)

    def test_favorite_image_cursor_tracks_image_and_disabled_state(self):
        from cmdrhelper.ui.favorite_image_view import FavoriteImageLabel
        label = self.widget(FavoriteImageLabel, "/unused/image.png")
        self.assertEqual(label.cursor().shape(), Qt.ArrowCursor)
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.red)
        label.setPixmap(pixmap)
        self.assertEqual(label.cursor().shape(), Qt.PointingHandCursor)
        label.setEnabled(False)
        label.clear()
        label.setEnabled(True)
        self.assertEqual(label.cursor().shape(), Qt.ArrowCursor)

    def test_installation_is_idempotent(self):
        self.assertIs(install_cursor_policy(self.app), self.policy)

    def test_functional_cursor_changed_while_disabled_and_global_override_survive(self):
        widget = self.widget(QWidget)
        widget.setEnabled(False)
        widget.setCursor(Qt.WaitCursor)
        self.assertEqual(widget.cursor().shape(), Qt.ArrowCursor)
        widget.setEnabled(True)
        self.assertEqual(widget.cursor().shape(), Qt.WaitCursor)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            button = self.widget(QPushButton)
            self.move(button, QPoint(20, 20))
            self.assertEqual(QApplication.overrideCursor().shape(), Qt.WaitCursor)
        finally:
            QApplication.restoreOverrideCursor()
