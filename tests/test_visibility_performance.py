"""UI-only lifecycle regression tests using temporary images/settings."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PIL import Image
from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest, QSignalSpy
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout

from cmdrhelper.ui.screenshot_view import ScreenshotView
from cmdrhelper.ui.body_detail_window import BodyDetailWindow
from cmdrhelper.ui.planet_3d_widget import Planet3DWidget
from cmdrhelper.ui.belt_cluster_widget import BeltClusterWidget
from tests.test_screenshot_multi_commander import StateStub
from tests.test_explorer_table_ux import ExplorerWindow


class VisibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.settings = QSettings(str(self.root/'settings.ini'), QSettings.IniFormat)

    def track(self, widget):
        self.addCleanup(widget.deleteLater)
        self.addCleanup(widget.close)
        return widget

    def gallery(self):
        view = self.track(ScreenshotView(StateStub(self.settings)))
        source, target = self.root/'source', self.root/'target'
        source.mkdir(); target.mkdir()
        view.source_edit.setText(str(source)); view.target_edit.setText(str(target))
        view.format_combo.setCurrentText('PNG')
        view.delete_check.setChecked(False)
        view.auto_check.setChecked(False)
        return view, source, target

    def test_gallery_lifecycle_independent_of_automatic_conversion(self):
        view, source, target = self.gallery()
        self.assertFalse(view.gallery_timer.isActive())
        self.assertFalse(view.timer.isActive())
        view.gallery_filter.setCurrentIndex(view.gallery_filter.findData('unassigned'))
        Image.new('RGB', (10, 10)).save(target/'manual.png')
        with patch.object(view, '_gallery_snapshot', wraps=view._gallery_snapshot) as scan:
            view.show()
            self.assertGreater(scan.call_count, 0)
            self.assertEqual(view.gallery.count(), 1)
            self.assertTrue(view.gallery_timer.isActive())
            self.assertFalse(view.timer.isActive())
            view.hide(); scan.reset_mock()
            view._check_gallery_changes()
            scan.assert_not_called()
            self.assertFalse(view.gallery_timer.isActive())
            Image.new('RGB', (10, 10)).save(target/'second.png')
            view.show()
            self.assertEqual(view.gallery.count(), 2)

    def test_hidden_auto_conversion_continues_and_defers_gallery_build(self):
        view, source, target = self.gallery()
        view.pool = SimpleNamespace(start=lambda worker: worker.run())
        view.auto_check.setChecked(True)
        self.assertTrue(view.timer.isActive())
        self.assertFalse(view.gallery_timer.isActive())
        Image.new('RGB', (10, 10), 'red').save(source/'new.bmp')
        with patch.object(view, '_refresh_gallery', wraps=view._refresh_gallery) as build:
            view._scan(); view._scan()
            self.assertEqual(len(list(target.rglob('*.png'))), 1)
            build.assert_not_called()
            self.assertFalse(view.gallery_timer.isActive())
            view.show()
            self.assertEqual(view.gallery.count(), 1)
            build.assert_called_once()
            view.hide()
            self.assertTrue(view.timer.isActive())
            view.auto_check.setChecked(False)
            self.assertFalse(view.timer.isActive())
            with patch.object(view, '_queue') as queue:
                view._scan(); queue.assert_not_called()

    def test_unrelated_files_are_not_statted_by_bmp_scanner(self):
        view, source, target = self.gallery()
        view.auto_check.setChecked(True)
        (source/'unrelated.txt').write_text('not a BMP')
        original = Path.is_file
        calls = []
        def is_file(path):
            calls.append(path)
            return original(path)
        with patch.object(Path, 'is_file', is_file):
            view._scan()
        self.assertNotIn(source/'unrelated.txt', calls)

    def animations(self):
        texture = self.root/'texture.png'
        Image.new('RGB', (64, 32), 'blue').save(texture)
        body = self.track(BodyDetailWindow({}))
        body._body_image_label = QLabel(body)
        body._start_body_image_animation()
        globe = self.track(Planet3DWidget(texture))
        belt = self.track(BeltClusterWidget())
        return [(body, body._body_image_timer), (globe, globe._timer), (belt, belt._timer)]

    def test_all_decorative_timers_pause_hide_minimize_resume_close(self):
        for widget, timer in self.animations():
            with self.subTest(widget=type(widget).__name__):
                self.assertFalse(timer.isActive())
                for _ in range(3):
                    widget.show(); self.app.processEvents()
                    self.assertTrue(timer.isActive())
                    old_id = timer.timerId()
                    widget.show(); self.app.processEvents()
                    self.assertEqual(timer.timerId(), old_id)
                    widget.hide(); self.app.processEvents()
                    self.assertFalse(timer.isActive())
                widget.showMinimized(); self.app.processEvents()
                self.assertFalse(timer.isActive())
                spy = QSignalSpy(timer.timeout)
                QTest.qWait(180)
                self.assertEqual(spy.count(), 0)
                widget.showNormal(); self.app.processEvents()
                self.assertTrue(timer.isActive())
                widget.close(); self.app.processEvents()
                self.assertFalse(timer.isActive())

    def test_child_rotation_tracks_minimized_parent_and_preserves_frame(self):
        texture = self.root/'texture.png'
        Image.new('RGB', (64, 32), 'blue').save(texture)
        parent = self.track(QWidget())
        layout = QVBoxLayout(parent)
        globe = Planet3DWidget(texture, parent)
        layout.addWidget(globe)
        parent.show(); self.app.processEvents()
        self.assertTrue(globe._timer.isActive())
        parent.showMinimized(); self.app.processEvents()
        frame = globe._frame
        with patch.object(globe, '_render_frame') as render:
            QTest.qWait(180)
            render.assert_not_called()
        self.assertIs(globe._frame, frame)
        parent.showNormal(); self.app.processEvents()
        self.assertTrue(globe._timer.isActive())

    def explorer(self):
        window = self.track(ExplorerWindow(self.settings))
        window.state.system_address = 42
        window.state.system_stations = []
        window.pages = SimpleNamespace(currentIndex=lambda: window.PAGE_EXPLORER)
        window.show()
        return window

    def test_ten_model_updates_only_build_selected_tab_then_latest_once(self):
        window = self.explorer()
        with patch.object(window.system_map, 'set_system') as system_map, \
                patch.object(window.stations_view, 'set_system') as stations, \
                patch.object(window, '_refresh_explorer_tables') as tables:
            for index in range(10):
                window.state.system = f'System {index}'
                window._explorer_dirty = True
                window._refresh_visible_details()
            self.assertEqual(system_map.call_count, 10)
            tables.assert_not_called(); stations.assert_not_called()
            self.assertEqual(window._explorer_dirty_tabs, {1, 2, 3})
            window.explorer_tabs.setCurrentIndex(3)
            stations.assert_called_once_with(42, 'System 9', [])
            window._refresh_visible_details()
            self.assertEqual(stations.call_count, 1)
            window.explorer_tabs.setCurrentIndex(1)
            tables.assert_called_once_with(tab=1)
            window.explorer_tabs.setCurrentIndex(2)
            self.assertEqual(tables.call_count, 2)
            tables.assert_called_with(tab=2)

    def test_station_update_hidden_then_live_and_system_switch(self):
        window = self.explorer()
        window._refresh_visible_details()
        with patch.object(window.system_map, 'set_system') as system_map, \
                patch.object(window.stations_view, 'set_system', wraps=window.stations_view.set_system) as stations:
            window.pages.currentIndex = lambda: -1
            for i in range(10):
                window.state.system_stations = [dict(market_id=i, name=f'Station {i}')]
                window._station_model_updated(42)
            system_map.assert_not_called(); stations.assert_not_called()
            self.assertTrue(window.explorer_tabs.tabText(3).endswith('(1)'))
            window.pages.currentIndex = lambda: window.PAGE_EXPLORER
            window.explorer_tabs.setCurrentIndex(3)
            stations.assert_called_once()
            self.assertEqual(window.stations_view.stations[0]['name'], 'Station 9')
            window._station_model_updated(42)
            self.assertEqual(stations.call_count, 2)
            window.state.system_address = 99
            window.state.system = 'Empty'
            window.state.system_stations = []
            window._explorer_dirty = True
            window._refresh_visible_details()
            self.assertEqual(window.stations_view.stations, [])
            window.explorer_tabs.setCurrentIndex(0)
            system_map.assert_called_once_with('Empty', [], [])

    def test_value_and_bio_table_builds_do_not_touch_each_other(self):
        window = self.explorer()
        window.state.system_bodies = [dict(name='Test 1', body_type='Planet', biological_signals=1)]
        with patch.object(window.explorer_value_table, 'setRowCount') as value, \
                patch.object(window.explorer_bio_table, 'setRowCount') as bio:
            window._refresh_explorer_tables(tab=1)
            value.assert_called_once_with(1); bio.assert_not_called()
            value.reset_mock()
            window._refresh_explorer_tables(tab=2)
            bio.assert_called_once_with(1); value.assert_not_called()
