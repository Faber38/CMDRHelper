"""View-only loading lifecycle and material widget reuse regressions."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PySide6.QtCore import QSettings, QTimer, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QWidget

from cmdrhelper.i18n import _TRANSLATIONS, tr
from cmdrhelper.ui.loading_state import LoadingState
from cmdrhelper.ui.material_view import MaterialView
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from test_material_view import StubController, snapshot
from cmdrhelper.material_inventory import _Reducer


class LoadingLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.host = QWidget()
        self.host.resize(500, 400)
        self.loading = LoadingState(self.host)
        self.host.show()
        self.addCleanup(self.host.close)
        self.addCleanup(self.host.deleteLater)

    def test_fast_completion_does_not_flash(self):
        self.loading.begin()
        self.loading.finish()
        QTest.qWait(180)
        self.assertFalse(self.loading.isVisible())
        self.assertFalse(self.loading.delay.isActive())

    def test_slow_work_animates_then_finishes_without_minimum_duration(self):
        beats = []
        self.loading.scanner.timer.timeout.connect(lambda: beats.append(1))
        self.loading.begin()
        QTest.qWait(260)
        self.assertTrue(self.loading.isVisible())
        self.assertGreaterEqual(len(beats), 2)
        self.loading.finish()
        self.assertFalse(self.loading.isVisible())
        self.assertFalse(self.loading.scanner.timer.isActive())

    def test_repeated_begin_hide_reopen_and_close(self):
        self.loading.begin()
        started = self.loading.started
        self.loading.begin()
        self.assertEqual(self.loading.started, started)
        self.host.hide()
        QTest.qWait(180)
        self.assertFalse(self.loading.delay.isActive())
        self.host.show()
        QTest.qWait(5)
        self.assertTrue(self.loading.isVisible())
        self.host.close()
        self.assertFalse(self.loading.scanner.timer.isActive())
        self.assertFalse(self.loading.delay.isActive())

    def test_error_is_terminal_and_new_request_clears_it(self):
        self.loading.begin()
        self.loading.finish('read failed')
        self.assertFalse(self.loading.pending)
        self.assertIn('read failed', self.loading.message.text())
        self.assertFalse(self.loading.scanner.timer.isActive())
        self.loading.begin()
        self.assertFalse(self.loading.error)
        self.loading.finish()

    def test_both_themes_and_existing_twelve_translations(self):
        previous = self.app.styleSheet()
        self.addCleanup(self.app.setStyleSheet, previous)
        for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.app.setStyleSheet(style)
            self.loading.begin()
            QTest.qWait(180)
            self.assertFalse(self.loading.grab().isNull())
            self.loading.finish()
        self.assertEqual(len(_TRANSLATIONS), 12)
        for table in _TRANSLATIONS.values():
            self.assertIn('loading.data', table)
            self.assertIn('loading.error', table)


class MaterialReuseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        settings = QSettings(str(Path(self.tmp.name)/'settings.ini'), QSettings.IniFormat)
        self.view = MaterialView(SimpleNamespace(settings=settings), controller=StubController())
        self.addCleanup(self.view.deleteLater)
        self.addCleanup(self.view.close)
        self.view.show()
        self.reducer = _Reducer(1, 'F1')
        self.reducer.apply(snapshot(), ('journal', 0))
        self.view.set_inventory(self.reducer.result, 'A')

    def test_category_round_trip_reuses_rows_and_bars(self):
        self.view.tabs.setCurrentIndex(1)
        original = {k:(v,self.view.tree.itemWidget(v,3)) for k,v in self.view.items.items()}
        self.view.tabs.setCurrentIndex(2)
        self.view.tabs.setCurrentIndex(1)
        for key,(row,bar) in original.items():
            self.assertIs(self.view.items[key], row)
            self.assertIs(self.view.tree.itemWidget(row,3),bar)
        with patch.object(self.view.tree,'doItemsLayout') as layout:
            self.view.render()
            layout.assert_not_called()

    def test_changed_counts_update_existing_widgets_and_identity_clears_stock(self):
        item = self.view.items['iron']
        bar = self.view.tree.itemWidget(item,3)
        self.reducer.apply(snapshot([{'Name':'iron','Count':17}]), ('journal',1))
        self.view.set_inventory(self.reducer.result,'A')
        self.assertIs(self.view.items['iron'],item)
        self.assertIs(self.view.tree.itemWidget(item,3),bar)
        self.assertEqual(item.text(2),'17 / 300')
        self.view.begin_loading()
        self.assertIn('?',self.view.items['iron'].text(2))
        self.assertIsNone(self.view.tree.itemWidget(item,3))
        self.view.set_inventory(self.reducer.result, 'A')
        self.assertEqual(item.toolTip(2), '')

    def test_filter_round_trip_keeps_order_and_widgets(self):
        rows = dict(self.view.items)
        self.view.search.setText('iron')
        self.view.search.clear()
        for key,item in rows.items():
            self.assertIs(self.view.items[key],item)
        self.assertEqual(self.view.items['iron'].text(2),'0 / 300')
