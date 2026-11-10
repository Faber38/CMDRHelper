"""Responsive Chronicle controls using real widgets, themes and callbacks."""
import unittest

from PySide6.QtCore import QDate, QPoint, Qt
from PySide6.QtGui import QFont
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QAbstractButton, QLabel

from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
import test_chronicle_export_layout as export_layout


class ChronicleControlsLayoutTests(unittest.TestCase):
    setUpClass = classmethod(export_layout.ChronicleExportLayoutTests.setUpClass.__func__)
    setUp = export_layout.ChronicleExportLayoutTests.setUp
    tearDown = export_layout.ChronicleExportLayoutTests.tearDown
    apply_results = export_layout.ChronicleExportLayoutTests.apply_results
    assert_visible_actions = export_layout.ChronicleExportLayoutTests.assert_visible_actions

    def inputs(self):
        return [widget for widget in self.w.chronicle_mining_filter_frame.findChildren(QAbstractButton)
                if not widget.parent().inherits('QAbstractSpinBox')] + [
            self.w.chronicle_search_edit, self.w.chronicle_from_date, self.w.chronicle_to_date,
            self.w.chronicle_planetary_mining_minimum, self.w.chronicle_mining_commodity_combo]

    def assert_controls_fit(self):
        widgets = self.inputs()
        for widget in widgets:
            rect = widget.rect().translated(widget.mapTo(self.w, QPoint()))
            self.assertTrue(self.w.rect().contains(rect), (widget, rect, self.w.size()))
            self.assertGreaterEqual(widget.width(), widget.minimumSizeHint().width())
            self.assertGreaterEqual(widget.height(), widget.minimumSizeHint().height())
            self.assertFalse(widget.visibleRegion().isEmpty())
            for ancestor in (widget.parentWidget(), self.w.chronicle_mining_filter_frame):
                local = widget.rect().translated(widget.mapTo(ancestor, QPoint()))
                self.assertTrue(ancestor.rect().contains(local), (widget, local, ancestor.rect()))
        for label in self.w.chronicle_mining_filter_frame.findChildren(QLabel):
            rect = label.rect().translated(label.mapTo(label.parentWidget(), QPoint()))
            self.assertTrue(label.parentWidget().rect().contains(rect))
            self.assertGreaterEqual(label.width(), label.minimumSizeHint().width())
            if label.wordWrap():
                self.assertGreaterEqual(label.height(), label.heightForWidth(label.width()))
        for i, widget in enumerate(widgets):
            rect = widget.rect().translated(widget.mapTo(self.w, QPoint()))
            for other in widgets[i + 1:]:
                other_rect = other.rect().translated(other.mapTo(self.w, QPoint()))
                self.assertFalse(rect.intersects(other_rect), (widget, other))

    def test_columns_wrap_and_recover(self):
        w = self.w
        self.apply_results(3)
        for width, stacked in ((1100, False), (650, True), (1100, False)):
            w.resize(width, 900)
            self.app.processEvents()
            left, right = w.chronicle_search_panel, w.chronicle_options_panel
            if stacked:
                self.assertGreater(right.y(), left.geometry().bottom())
                self.assertEqual(left.x(), right.x())
            else:
                self.assertEqual(left.y(), right.y())
                self.assertGreater(right.x(), left.geometry().right())
                # Before this change the block was 235 px in this fixture.
                self.assertLess(w.chronicle_mining_filter_frame.height(), 200)
            self.assert_controls_fit()
            self.assert_visible_actions()
            self.assertGreater(w.chronicle_search_edit.width(), 200)

    def test_themes_fonts_heights_and_commander_wrapping(self):
        w = self.w
        for i in range(3):
            w.state.database.upsert_commander('OTHER' + str(i), 'Commander ' + str(i))
        w._refresh_chronicle()
        self.apply_results(3)
        for stylesheet in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            w.setStyleSheet(stylesheet)
            for points in (10, 14):
                w.setFont(QFont('Sans', points))
                for width in (750, 1500):
                    for height in (720, 1000):
                        w.resize(width, height)
                        self.app.processEvents()
                        self.assertEqual(w.height(), height)
                        self.assert_controls_fit()
                        self.assert_visible_actions()
                        for check in w.chronicle_commander_checks.values():
                            rect = check.rect().translated(check.mapTo(w.chronicle_filter_frame, QPoint()))
                            self.assertTrue(w.chronicle_filter_frame.rect().contains(rect))
                            self.assertGreaterEqual(check.width(), check.sizeHint().width())

    def test_existing_inputs_and_selection_are_operable_after_reflow(self):
        w = self.w
        w.resize(650, 900)
        self.app.processEvents()
        w.chronicle_search_edit.setFocus()
        QTest.keyClicks(w.chronicle_search_edit, 'Example')
        self.assertEqual(w.chronicle_search_edit.text(), 'Example')
        for check, date in ((w.chronicle_from_check, w.chronicle_from_date),
                            (w.chronicle_to_check, w.chronicle_to_date)):
            QTest.mouseClick(check, Qt.LeftButton, pos=QPoint(8, check.height() // 2))
            self.assertTrue(date.isEnabled())
            date.setDate(QDate(2026, 11, 10))
            self.assertEqual(date.date(), QDate(2026, 11, 10))
        w.chronicle_mining_commodity_combo.addItem('Iron', 'iron')
        for check in (w.chronicle_planetary_mining_check, w.chronicle_personally_mined_check):
            QTest.mouseClick(check, Qt.LeftButton, pos=QPoint(8, check.height() // 2))
            self.assertTrue(check.isChecked())
        w.chronicle_planetary_mining_minimum.setValue(3)
        self.assertEqual(w.chronicle_planetary_mining_minimum.value(), 3)
        self.assertTrue(w.chronicle_mining_commodity_combo.isEnabled())
        w.chronicle_mining_commodity_combo.setFocus()
        QTest.keyClick(w.chronicle_mining_commodity_combo, Qt.Key_End)
        self.assertEqual(w.chronicle_mining_commodity_combo.currentData(), 'iron')
        for check in (w.chronicle_footfall_check, w.chronicle_discovery_check, w.chronicle_mapping_check):
            QTest.mouseClick(check, Qt.LeftButton, pos=QPoint(8, check.height() // 2))
            self.assertTrue(check.isChecked())
            QTest.mouseClick(check, Qt.LeftButton, pos=QPoint(8, check.height() // 2))
            self.assertFalse(check.isChecked())
        self.assertTrue(w.chronicle_personally_mined_check.isChecked())
        commander = next(iter(w.chronicle_commander_checks.values()))
        QTest.mouseClick(commander, Qt.LeftButton)
        self.assertFalse(commander.isChecked())
        QTest.mouseClick(w.chronicle_all_commanders, Qt.LeftButton)
        self.assertTrue(commander.isChecked())
        QTest.mouseClick(w.chronicle_reset_button, Qt.LeftButton)
        self.assertEqual(w.chronicle_search_edit.text(), '')
