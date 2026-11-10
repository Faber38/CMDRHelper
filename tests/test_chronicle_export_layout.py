"""Export actions stay visible above results, independently of map height."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QPoint, QPointF, QSettings, Qt
from PySide6.QtGui import QFont, QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.i18n import get_language, set_language
from tests.test_discovery_chronicle import ChronicleWindow
from qt_widget_cleanup import destroy_widget


class ChronicleExportLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(set_language, get_language())
        set_language('de')
        self.errors = []
        self.addCleanup(setattr, sys, 'excepthook', sys.excepthook)
        sys.excepthook = lambda *args: self.errors.append(args)
        db = CMDRDatabase(Path(self.tmp.name)/'db.sqlite')
        cid = db.upsert_commander('LAYOUT', 'Layout')
        self.w = ChronicleWindow(db, QSettings(str(Path(self.tmp.name)/'ui.ini'), QSettings.IniFormat), cid)
        self.addCleanup(destroy_widget, self.w, close=False)
        self.w.show(); self.app.processEvents()

    def tearDown(self):
        self.assertEqual(self.errors, [])

    def apply_results(self, count):
        w = self.w
        result = dict(commander_id=1, commander_name='Layout', fid='LAYOUT',
                      system_address=60, system_name='Example', body_id=7,
                      short_name='3', body_name='Example 3', x=1, y=2, z=3,
                      kind='first_footfall', timestamp='2026-11-10T08:08:56Z', discovery=True)
        rows = [dict(result, body_id=i) for i in range(count)]
        w.chronicle_footfall_check.setChecked(True)
        w.chronicle_discovery_check.setChecked(True)
        with patch.object(w.state.database, 'search_discoveries', return_value=rows):
            w.chronicle_apply_button.click()
        self.app.processEvents()

    def assert_visible_actions(self):
        w = self.w
        results = w.chronicle_search_results
        top = results.mapTo(w, QPoint(0, 0)).y()
        for button in (w.chronicle_copy_list, w.chronicle_export_csv):
            rect = button.rect().translated(button.mapTo(w, QPoint(0, 0)))
            self.assertTrue(w.rect().contains(rect), (w.size(), rect))
            self.assertFalse(button.visibleRegion().isEmpty())
            self.assertLess(rect.bottom(), top)
            # They must be reachable, not merely have the Qt visible flag.
            center = button.mapTo(w, button.rect().center())
            self.assertIs(w.childAt(center), button)

    def test_large_result_set_short_windows_and_tall_map(self):
        self.apply_results(11959)
        w = self.w
        self.assertEqual(w.chronicle_search_results.count(), 11959)
        for height in (720, 900, 1080):
            for map_height in (520, 1500):
                w.chronicle_map.setMinimumHeight(map_height)
                w.resize(1100, height)
                self.app.processEvents()
                self.assertEqual(w.height(), height)
                self.assert_visible_actions()
                self.assertTrue(w.chronicle_copy_list.isEnabled())
                self.assertTrue(w.chronicle_export_csv.isEnabled())
                self.assertLess(w.chronicle_map_scroll.height(), w.height())
        self.assertTrue(w.chronicle_map_scroll.verticalScrollBar().maximum() > 0)
        self.assertEqual(w.chronicle_map.minimumHeight(), 1500)

    def test_font_scaling_and_real_clicks(self):
        self.apply_results(3)
        w = self.w
        for point_size in (10, 14):
            w.setFont(QFont('Sans', point_size)); w.resize(1250, 1000)
            self.app.processEvents(); self.assert_visible_actions()
        with patch('cmdrhelper.ui.main_window.QFileDialog.getSaveFileName', return_value=('', '')) as save:
            QTest.mouseClick(w.chronicle_export_csv, Qt.LeftButton)
            save.assert_called_once()
        QTest.mouseClick(w.chronicle_copy_list, Qt.LeftButton)
        self.assertIn('Layout', QApplication.clipboard().text())
        self.assertIn('Erstbetretung', QApplication.clipboard().text())

    def test_empty_results_buttons_exist_visible_disabled(self):
        self.apply_results(0)
        self.w.resize(1100, 720); self.app.processEvents()
        for button in (self.w.chronicle_copy_list, self.w.chronicle_export_csv):
            rect = button.rect().translated(button.mapTo(self.w, QPoint()))
            self.assertTrue(self.w.rect().contains(rect))
            self.assertFalse(button.visibleRegion().isEmpty())
            self.assertFalse(button.isEnabled())

    def test_map_wheel_still_zooms_in_scroll_container(self):
        self.apply_results(3)
        w = self.w
        w.resize(1100, 720); self.app.processEvents()
        chart = w.chronicle_map
        before = chart.scale
        bar = w.chronicle_map_scroll.verticalScrollBar()
        previous_scroll = bar.value()
        pos = QPointF(80, 80)
        event = QWheelEvent(pos, QPointF(chart.mapToGlobal(pos.toPoint())),
                            QPoint(), QPoint(0, 120), Qt.NoButton, Qt.NoModifier,
                            Qt.NoScrollPhase, False)
        QApplication.sendEvent(chart, event)
        self.assertNotEqual(chart.scale, before)
        self.assertEqual(bar.value(), previous_scroll)
        self.assertEqual(chart.minimumHeight(), 520)
        self.assert_visible_actions()
