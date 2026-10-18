"""Display diagnostics: synthetic inventories, private settings and offline ZIPs."""
import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from zipfile import ZipFile

from PySide6.QtCore import QCoreApplication, QEvent, QSettings
from PySide6.QtWidgets import QApplication, QStackedWidget, QWidget

from cmdrhelper.diagnostics import create_package
from cmdrhelper.odyssey_display_diagnostics import export_snapshot, STALE_SECONDS, COUNTER_LIMIT
from cmdrhelper.ui.main_window import MainWindow
from cmdrhelper.ui.material_view import MaterialView
from cmdrhelper.ui.diagnostics_panel import DiagnosticsPanel
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from test_material_view import State, StubController
from test_odyssey_view import inventory, pair
from test_odyssey_inventory import snapshot


class DisplayDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = State()
        self.state.settings = QSettings(str(self.root/'ui.ini'), QSettings.IniFormat)
        self.state.commander_id = self.state.viewed_commander_id = 1
        self.state.commander_fid = 'F-SYNTHETIC-PRIVATE'
        self.state.database = SimpleNamespace(path=self.root/'not-opened.db')
        self.state.journal_folder = self.root/'not-opened-journals'
        self.controller = StubController()
        self.page = MaterialView(self.state, controller=StubController(), odyssey_controller=self.controller)
        self.pages = QStackedWidget()
        self.pages.addWidget(self.page)
        self.pages.addWidget(QWidget())
        self.pages.resize(1100, 750)
        self.pages.show()
        self.page.tabs.setCurrentIndex(3)
        self.view = self.page.odyssey
        self.view.tabs.setCurrentIndex(1)
        self.controller.ready.emit(inventory(pair()), 'SYNTHETIC PRIVATE NAME')
        self.app.processEvents()
        self.diag = self.view.display_diagnostics
        self.addCleanup(self.cleanup_widgets)

    def cleanup_widgets(self):
        self.pages.close()
        self.pages.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    def capture(self):
        self.diag.capture()
        result = export_snapshot(self.diag.snapshot)
        self.assertEqual(result['status'], 'valid')
        return result

    def row(self):
        return next(item for key, item in self.view.items.items() if key.name == 'graphene')

    def test_never_opened_and_no_lazy_construction(self):
        empty = SimpleNamespace(material_view=SimpleNamespace(odyssey=None))
        self.assertIsNone(MainWindow._odyssey_diagnostics_snapshot(empty))
        self.assertEqual(export_snapshot()['message'], 'Kein Odyssey-Snapshot verfügbar')
        self.assertIsNone(self.diag.snapshot)

    def test_capture_before_main_page_switch_and_preserve_hidden_snapshot(self):
        host = SimpleNamespace(pages=self.pages, material_view=self.page, nav_buttons=[])
        seen = []
        original = self.pages.setCurrentIndex
        def switch(index):
            seen.append((self.view.isVisible(), self.diag.snapshot is not None))
            original(index)
        with patch.object(self.pages, 'setCurrentIndex', side_effect=switch):
            MainWindow._show_page(host, 1)
        self.assertEqual(seen, [(True, True)])
        saved = copy.deepcopy(self.diag.snapshot)
        self.view.set_light_mode(True)
        self.diag.capture()  # Hidden widgets cannot replace the last visible state.
        self.assertEqual(self.diag.snapshot, saved)
        self.assertIs(MainWindow._odyssey_diagnostics_snapshot(host), self.diag.snapshot)

    def test_material_subtab_switch_captures_visible_state(self):
        self.page.tabs.setCurrentIndex(0)
        self.assertFalse(self.view.isVisible())
        self.assertEqual(export_snapshot(self.diag.snapshot)['status'], 'valid')

    def test_commander_switch_invalidates_without_retaining_measurements(self):
        for signal, args in ((self.state.commanderIdentityChanged, (2, 'F-OTHER', 'Other')),
                             (self.state.viewedCommanderChanged, (2,))):
            self.capture()
            signal.emit(*args)
            result = export_snapshot(self.diag.snapshot)
            self.assertEqual(result['status'], 'invalidated')
            self.assertNotIn('stock_cells', result)
            self.assertNotIn('environment', self.diag.snapshot)
        self.view.begin_loading()
        self.diag.capture()
        self.assertEqual(export_snapshot(self.diag.snapshot)['status'], 'invalidated')

    def test_age_and_stale_snapshot(self):
        self.capture()
        created = datetime.fromisoformat(self.diag.snapshot['created_at'])
        result = export_snapshot(self.diag.snapshot, now=created+timedelta(seconds=STALE_SECONDS+1))
        self.assertEqual(result['status'], 'stale')
        self.assertEqual(result['age_seconds'], STALE_SECONDS+1)
        self.assertTrue(result['last_visible'])
        self.assertIn('veraltet', result['message'])

    def test_geometry_screen_and_effective_font(self):
        result = self.capture()
        env, table = result['environment'], result['table']
        screen = self.pages.windowHandle().screen()
        self.assertEqual(env['screen_logical_geometry']['width'], screen.geometry().width())
        self.assertEqual(env['window_dpr'], self.pages.devicePixelRatioF())
        if os.environ.get('QT_QPA_PLATFORM') == 'offscreen':
            self.assertAlmostEqual(env['window_dpr'], float(os.environ.get('QT_SCALE_FACTOR', '1')))
        self.assertEqual(table['column_widths_logical'], [self.view.tree.columnWidth(i) for i in range(7)])
        self.assertEqual(sorted(table['column_visual_order']), list(range(7)))
        self.assertGreater(env['font_pixel_size'], 0)
        self.assertGreater(table['visible_single_rows'], 0)
        self.assertFalse(result['paint_proves_correct_display'])

    def test_window_screen_not_primary_screen(self):
        screen = Mock()
        from PySide6.QtCore import QRect
        screen.geometry.return_value = QRect(1700, 0, 1234, 987)
        screen.availableGeometry.return_value = QRect(1700, 20, 1234, 967)
        for name in ('devicePixelRatio', 'logicalDotsPerInchX', 'logicalDotsPerInchY',
                     'physicalDotsPerInchX', 'physicalDotsPerInchY'):
            getattr(screen, name).return_value = 2.0 if name == 'devicePixelRatio' else 96.0
        handle = SimpleNamespace(screen=lambda: screen)
        with patch.object(self.pages, 'windowHandle', return_value=handle):
            result = self.capture()
        self.assertEqual(result['environment']['screen_logical_geometry']['x'], 1700)
        self.assertEqual(result['environment']['screen_dpr'], 2.0)
        screen.serialNumber.assert_not_called()
        screen.name.assert_not_called()

    def test_unknown_zero_dash_empty_mismatch_and_detail_omission(self):
        initial = self.capture()['stock_cells']
        self.assertGreater(initial['numeric'], 0)
        self.assertGreater(initial['zero'], 0)
        self.assertGreater(initial['unknown'], 0)  # No known carrier stock.
        self.assertEqual(initial['projection_mismatch'], 0)
        row = self.row()
        row.setText(1, '')
        row.setText(2, '—')
        changed = self.capture()['stock_cells']
        self.assertEqual(changed['empty'], initial['empty']+1)
        self.assertEqual(changed['projection_mismatch'], 2)
        self.view.tabs.setCurrentIndex(0)
        result = self.capture()
        self.assertGreater(result['table']['visible_summary_rows'], 0)
        self.assertGreater(result['table']['visible_detail_rows'], 0)
        self.assertGreater(result['stock_cells']['omitted_detail'], 0)
        self.controller.ready.emit(inventory(), '')
        unknown = self.capture()['stock_cells']
        self.assertGreater(unknown['unknown'], 0)
        self.assertEqual(unknown['numeric'], 0)
        self.controller.ready.emit(inventory([snapshot('ShipLocker'), snapshot('Backpack')]), '')
        zero = self.capture()['stock_cells']
        self.assertGreater(zero['zero'], 0)
        self.view.tabs.setCurrentIndex(3)  # Consumables have no carrier column.
        consumables = self.capture()['stock_cells']
        self.assertGreater(consumables['not_applicable'], 0)
        self.assertEqual(consumables['unknown'], 0)

    def test_elision_hidden_columns_order_and_selection(self):
        row = self.row()
        row.setText(1, '123456789012345678901234567890')
        self.view.tree.setColumnWidth(1, 40)
        self.view.tree.setCurrentItem(row)
        self.view.tree.scrollToItem(row)
        self.app.processEvents()
        result = self.capture()
        self.assertGreater(result['stock_cells']['potentially_elided'], 0)
        self.assertEqual(result['table']['selected_rows'], 1)
        self.view.tree.setColumnHidden(1, True)
        result = self.capture()
        self.assertTrue(result['table']['columns_hidden'][1])
        self.assertEqual(result['stock_cells']['potentially_elided'], 0)

    def test_themes_resize_scroll_counters_and_no_model_changes(self):
        original = [(id(i), tuple(i.text(c) for c in range(7))) for i in self.view.items.values()]
        for light, style in ((False, DARK_STYLESHEET), (True, LIGHT_STYLESHEET)):
            self.pages.setStyleSheet(style)
            self.view.set_light_mode(light)
            for width, height in ((480, 400), (1600, 1000)):
                self.pages.resize(width, height)
                self.app.processEvents()
                bar = self.view.tree.verticalScrollBar()
                bar.setValue(bar.maximum())
                self.app.processEvents()
                result = self.capture()
                self.assertEqual(result['environment']['theme'], 'light' if light else 'dark')
                self.assertEqual(result['table']['vertical_scroll']['value'], bar.value())
                self.assertGreater(result['events']['resize'], 0)
                self.assertGreater(result['events']['paint'], 0)
                self.assertGreater(result['events']['geometry_changes'], 0)
        self.assertGreater(self.diag.events['scroll'], 0)
        self.assertEqual(original, [(id(i), tuple(i.text(c) for c in range(7))) for i in self.view.items.values()])
        self.diag.events['paint'] = COUNTER_LIMIT
        self.diag.eventFilter(self.diag.viewport, QEvent(QEvent.Paint))
        self.assertEqual(self.diag.events['paint'], COUNTER_LIMIT)
        self.diag.eventFilter(self.diag.viewport, QEvent(QEvent.UpdateRequest))
        self.assertGreater(self.diag.events['viewport_update_requests'], 0)

    def test_capture_has_no_io_no_repaint_no_model_or_settings_mutation(self):
        before = dict((k, self.state.settings.value(k)) for k in self.state.settings.allKeys())
        with patch('sqlite3.connect', side_effect=AssertionError('DB access')), \
             patch('builtins.open', side_effect=AssertionError('file access')), \
             patch.object(Path, 'open', side_effect=AssertionError('journal access')), \
             patch('socket.socket.connect', side_effect=AssertionError('network')), \
             patch.object(self.view, 'render', side_effect=AssertionError('render')), \
             patch.object(self.view.tree.viewport(), 'update', side_effect=AssertionError('repaint')), \
             patch.object(self.view.tree.viewport(), 'repaint', side_effect=AssertionError('repaint')):
            self.capture()
        self.assertEqual(before, dict((k, self.state.settings.value(k)) for k in self.state.settings.allKeys()))
        self.assertFalse(self.state.database.path.exists())

    def test_gui_thread_and_failure_do_not_leak_exception(self):
        errors = []
        def worker():
            try:
                self.diag.capture()
            except RuntimeError:
                errors.append(True)
        thread = threading.Thread(target=worker)
        thread.start()
        thread.join()
        self.assertEqual(errors, [True])
        with patch.object(self.diag, '_capture', side_effect=ValueError('PRIVATE TOKEN /private/path')):
            self.diag.capture()
        result = export_snapshot(self.diag.snapshot)
        self.assertEqual(result['status'], 'capture_failed')
        self.assertNotIn('PRIVATE', json.dumps(result))

    def test_bounded_scan_and_loading_without_previous_snapshot(self):
        with patch('cmdrhelper.ui.odyssey_diagnostics.ROW_LIMIT', 1):
            result = self.capture()
        self.assertTrue(result['scan_truncated'])
        self.assertEqual(result['stock_cells']['rows_examined'], 1)
        self.assertEqual(result['stock_cells']['cells_examined'], 4)
        self.diag.snapshot = None
        self.view.begin_loading()
        self.diag.capture()
        self.assertEqual(export_snapshot(self.diag.snapshot)['status'], 'unavailable')

    def test_zip_allowlist_rejects_private_payload_and_bad_types(self):
        self.row().setText(1, '987654321')
        self.capture()
        raw = copy.deepcopy(self.diag.snapshot)
        raw.update(fid='F999999', commander='PRIVATE', api_key='PRIVATE', model={'inventory': 987654321},
                   journal='/home/PRIVATE/Journal.log', ServerToken='PRIVATE')
        raw['environment'].update(font_family='/home/PRIVATE/font', platform_plugin='ServerToken PRIVATE',
                                  window_title='PRIVATE', serial_number='PRIVATE')
        raw['table']['column_widths_logical'] = ['PRIVATE'] * 7
        raw['stock_cells']['numeric'] = '987654321'
        raw['stock_cells']['private_amount'] = 987654321
        raw['events']['paint'] = True
        path = create_package(self.root/'report.zip', folder=self.root, odyssey_snapshot=raw)
        with ZipFile(path) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(set(archive.namelist()), {'system_info.json','diagnose_summary.txt','odyssey_display_diagnostics.json'})
            content = archive.read('odyssey_display_diagnostics.json').decode()
            for secret in ('PRIVATE', 'F999999', '987654321', 'graphene', 'SYNTHETIC', str(self.root), 'ServerToken'):
                self.assertNotIn(secret, content)
            clean = json.loads(content)
            self.assertNotIn('paint', clean['events'])
            self.assertNotIn('column_widths_logical', clean['table'])

    def test_panel_provider_and_cancel_and_failure(self):
        self.capture()
        provider = Mock(return_value=self.diag.snapshot)
        panel = DiagnosticsPanel(self.state, odyssey_snapshot=provider)
        self.addCleanup(panel.close)
        with patch('cmdrhelper.ui.diagnostics_panel.QFileDialog.getSaveFileName', return_value=('', '')):
            panel.create()
        provider.assert_not_called()
        with patch('cmdrhelper.ui.diagnostics_panel.QFileDialog.getSaveFileName', return_value=(str(self.root/'report.zip'), '')), \
             patch('cmdrhelper.ui.diagnostics_panel.create_package') as create, \
             patch('cmdrhelper.ui.diagnostics_panel.QMessageBox.information'):
            panel.create()
            self.assertIs(create.call_args.kwargs['odyssey_snapshot'], self.diag.snapshot)
        with patch('cmdrhelper.ui.diagnostics_panel.QFileDialog.getSaveFileName', return_value=(str(self.root/'report.zip'), '')), \
             patch('cmdrhelper.ui.diagnostics_panel.create_package', side_effect=OSError('synthetic failure')), \
             patch('cmdrhelper.ui.diagnostics_panel.QMessageBox.warning') as warning:
            panel.create()
            warning.assert_called_once()
            self.assertTrue(panel.create_button.isEnabled())
