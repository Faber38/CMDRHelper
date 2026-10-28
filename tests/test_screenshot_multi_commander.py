from __future__ import annotations

import os
import tempfile
import time
import unittest
from unittest.mock import patch
from datetime import datetime
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtCore import QObject, QSettings, Signal, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from cmdrhelper.ui.screenshot_view import ScreenshotView, safe_filename_component
from cmdrhelper.screenshot_sources import source_key


def fixture_context(state):
    return dict(fid=state.commander_fid, commander=state.commander, system=state.system,
                source_id="fixture", journal="fixture.log", last_timestamp="2020-01-01T00:00:00Z",
                suggested=state.settings.value(source_key(state.commander_fid), ""))


class DatabaseStub:
    def __init__(self):
        self.commanders = [
            {"id": 1, "fid": "F-A", "current_name": "Same"},
            {"id": 2, "fid": "F-B", "current_name": "Same"},
        ]

    def list_commanders(self):
        return list(self.commanders)


class StateStub(QObject):
    viewedCommanderChanged = Signal(object)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.database = DatabaseStub()
        self.commander_fid = "F-A"
        self.commander = "Same"
        self.system = "Alpha System"
        self.viewed_commander_id = 1


class PoolStub:
    def __init__(self):
        self.workers = []

    def start(self, worker):
        self.workers.append(worker)


class ScreenshotMultiCommanderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "Bilder"
        self.root.mkdir()
        settings = QSettings(
            str(Path(self.temp.name) / "settings.ini"), QSettings.IniFormat
        )
        for fid in ('F-A', 'F-B'):
            source = Path(self.temp.name) / fid
            source.mkdir()
            settings.setValue(source_key(fid), str(source))
        self.context_patch = patch('cmdrhelper.ui.screenshot_view.live_context', fixture_context)
        self.context_patch.start()
        self.addCleanup(self.context_patch.stop)
        self.state = StateStub(settings)
        self.view = ScreenshotView(self.state)
        self.view.timer.stop()
        self.view.gallery_timer.stop()
        self.view.target_edit.setText(str(self.root))
        self.view.format_combo.setCurrentText("PNG")

    def tearDown(self):
        self.view.close()
        self.view.deleteLater()
        self.temp.cleanup()

    def _wait_gallery(self):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            QTest.qWait(10)
            if (self.view._gallery_worker is None
                    and not self.view._populate_timer.isActive()
                    and self.view._preview_worker is None):
                return
        self.fail("Gallery did not finish loading")

    def _source(self, name="Screenshot.bmp", stamp=None, *, fid=None):
        folder = Path(self.temp.name) / (fid or self.state.commander_fid or 'unassigned')
        folder.mkdir(exist_ok=True)
        source = folder / name
        Image.new("RGB", (4, 4), "red").save(source, "BMP")
        if stamp is not None:
            os.utime(source, (stamp, stamp))
        return source

    @staticmethod
    def _image(path):
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (4, 4), "blue").save(path, "PNG")
        return path

    def _set_filter(self, mode):
        self.view.gallery_filter.setCurrentIndex(
            self.view.gallery_filter.findData(mode)
        )

    def test_two_fids_with_same_commander_name_get_separate_folders(self):
        source = self._source()
        first = self.view._output_path(source)
        self.state.commander_fid = "F-B"
        self.view._sync_source()
        second = self.view._output_path(source)
        self.assertEqual(first.parent.name, "Same_F-A")
        self.assertEqual(second.parent.name, "Same_F-B")
        self.assertNotEqual(first.parent, second.parent)

    def test_filename_uses_bmp_time_commander_and_safe_system(self):
        stamp = datetime(2026, 9, 4, 13, 18, 22).timestamp()
        self.state.commander = "TEST_CMDR"
        self.state.commander_fid = "F12345678"
        self.state.system = "Prua Hypai RB-D c29-71"
        source = self._source(stamp=stamp)
        self.state.settings.setValue(source_key("F12345678"), str(source.parent))
        self.view._sync_source()
        path = self.view._output_path(source)
        self.assertEqual(path.parent.name, "TEST_CMDR_F12345678")
        self.assertEqual(
            path.name,
            "Prua_Hypai_RB-D_c29-71_TEST_CMDR_2026-09-04_13-18-22.png",
        )

    def test_unknown_identity_and_optional_system(self):
        self.state.commander = ""
        self.state.commander_fid = ""
        self.state.system = ""
        self.view._sync_source()
        path = self.view._output_path(self._source())
        self.assertEqual(path.parent.name, "UNKNOWN_UNKNOWN")
        self.assertTrue(path.name.startswith("UNKNOWN_SYSTEM_UNKNOWN_COMMANDER_"))

    def test_invalid_and_windows_reserved_components_are_safe(self):
        self.assertEqual(safe_filename_component("CON"), "_CON")
        self.assertEqual(safe_filename_component("LPT1.txt"), "_LPT1.txt")
        cleaned = safe_filename_component(' A/B\\C:*?"<>|. ')
        self.assertNotRegex(cleaned, r'[<>:"/\\|?*]')
        self.assertFalse(cleaned.endswith((".", " ")))

    def test_queue_freezes_identity_and_reserves_same_second_collisions(self):
        self.view.pool = PoolStub()
        first_source = self._source("First.bmp")
        second_source = self._source("Second.bmp", fid="F-B")
        stamp = datetime(2026, 9, 4, 13, 18, 22).timestamp()
        os.utime(first_source, (stamp, stamp))
        os.utime(second_source, (stamp, stamp))
        self.view._queue(first_source)
        self.state.commander = "Bravo"
        self.state.commander_fid = "F-B"
        self.state.system = "Bravo System"
        first_worker = self.view.pool.workers[0]
        self.view._sync_source()
        self.view._queue(second_source)
        second_worker = self.view.pool.workers[1]
        self.assertEqual(first_worker.target.parent.name, "Same_F-A")
        self.assertIn("Alpha_System_Same", first_worker.target.name)
        self.assertEqual(second_worker.target.parent.name, "Bravo_F-B")

        # A second A screenshot queued for the same second cannot reuse target 1.
        self.state.commander = "Same"
        self.state.commander_fid = "F-A"
        self.state.system = "Alpha System"
        third_source = self._source("Third.bmp")
        os.utime(third_source, (stamp, stamp))
        self.view._sync_source()
        self.view._queue(third_source)
        self.assertTrue(self.view.pool.workers[2].target.stem.endswith("_2"))

    def test_gallery_current_follows_viewed_commander(self):
        self.view.show()
        self._wait_gallery()
        a = self._image(self.root / "Same_F-A" / "a.png")
        b = self._image(self.root / "Same_F-B" / "b.png")
        self._set_filter("current")
        self.view._refresh_gallery()
        self._wait_gallery()
        self.assertEqual(self.view.gallery.count(), 1)
        self.assertEqual(Path(self.view.gallery.item(0).data(Qt.UserRole)), a)
        self.state.viewed_commander_id = 2
        self.state.viewedCommanderChanged.emit(2)
        self._wait_gallery()
        self.assertEqual(self.view.gallery.count(), 1)
        self.assertEqual(Path(self.view.gallery.item(0).data(Qt.UserRole)), b)

    def test_all_and_unassigned_filters_keep_legacy_untouched(self):
        legacy = self._image(self.root / "legacy.png")
        self._image(self.root / "Same_F-A" / "a.png")
        self._image(self.root / "Same_F-B" / "b.png")
        self._set_filter("all")
        self.view._refresh_gallery()
        self._wait_gallery()
        self.assertEqual(self.view.gallery.count(), 2)
        self._set_filter("unassigned")
        self.view._refresh_gallery()
        self._wait_gallery()
        self.assertEqual(self.view.gallery.count(), 1)
        self.assertEqual(Path(self.view.gallery.item(0).data(Qt.UserRole)), legacy)
        self.assertTrue(legacy.exists())

    def test_refresh_preserves_current_selection_and_rereads_its_preview(self):
        a = self._image(self.root / 'Same_F-A' / 'a.png')
        self.view._refresh_gallery(a)
        self._wait_gallery()
        Image.new('RGB', (4, 4), 'red').save(a)
        self._image(self.root / 'Same_F-A' / 'b.png')
        self.view._refresh_gallery()
        self._wait_gallery()
        self.assertEqual(self.view.preview_name.text(), a.name)
        self.assertEqual(self.view.gallery.currentItem().data(Qt.UserRole), str(a))
        self.assertEqual(self.view.preview.pixmap().toImage().pixelColor(0, 0).name(), '#ff0000')

    def test_removed_selection_selects_existing_image_then_clears_empty_preview(self):
        a = self._image(self.root / 'Same_F-A' / 'a.png')
        b = self._image(self.root / 'Same_F-A' / 'b.png')
        self.view._refresh_gallery(a)
        self._wait_gallery()
        a.unlink()
        self.view._refresh_gallery()
        self._wait_gallery()
        self.assertEqual(self.view.preview_name.text(), b.name)
        self.assertEqual(self.view.gallery.currentItem().data(Qt.UserRole), str(b))
        b.unlink()
        self.view._refresh_gallery()
        self._wait_gallery()
        self.assertEqual(self.view.preview_name.text(), '')
        self.assertTrue(self.view.preview.pixmap().isNull())

    def test_show_refreshes_gallery_without_waiting_for_timer(self):
        self.view.show()
        self._wait_gallery()
        self.assertEqual(self.view.gallery.count(), 0)
        self.view.hide()
        path = self._image(self.root / 'Same_F-A' / 'new.png')
        self.view.show()
        self._wait_gallery()
        self.assertEqual(self.view.gallery.count(), 1)
        self.assertEqual(self.view.preview_name.text(), path.name)

    def test_keyboard_selection_updates_preview_and_missing_file_clears_it(self):
        a = self._image(self.root / 'Same_F-A' / 'a.png')
        b = self._image(self.root / 'Same_F-A' / 'b.png')
        self.view._refresh_gallery(a)
        self._wait_gallery()
        item = next(self.view.gallery.item(i) for i in range(self.view.gallery.count())
                    if self.view.gallery.item(i).data(Qt.UserRole) == str(b))
        self.view.gallery.setCurrentItem(item)
        self._wait_gallery()
        self.assertEqual(self.view.preview_name.text(), b.name)
        b.unlink()
        self.view._show_preview(item)
        self._wait_gallery()
        self.assertEqual(self.view.preview_name.text(), '')
        self.assertTrue(self.view.preview.pixmap().isNull())

    def test_delete_scope_rejects_outside_traversal_and_symlinks(self):
        allowed = self._image(self.root / "Same_F-A" / "inside.png")
        outside = self._image(Path(self.temp.name) / "outside.png")
        traversal = self.root / "Same_F-A" / ".." / "legacy.png"
        self._image(self.root / "legacy.png")
        self._set_filter("current")
        self.assertTrue(self.view._is_allowed_gallery_path(allowed))
        self.assertFalse(self.view._is_allowed_gallery_path(outside))
        self.assertFalse(self.view._is_allowed_gallery_path(traversal))
        link = self.root / "Same_F-A" / "link.png"
        try:
            link.symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks are not available")
        self.assertFalse(self.view._is_allowed_gallery_path(link))

    def test_symlinked_commander_folder_is_not_scanned_or_used_for_writes(self):
        outside = Path(self.temp.name) / "outside"
        outside.mkdir()
        linked = self.root / "Same_F-A"
        try:
            linked.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks are not available")
        self.assertIsNone(self.view._folder_for_identity("Same", "F-A"))
        self._set_filter("all")
        self.assertNotIn(linked, self.view._gallery_directories())


if __name__ == "__main__":
    unittest.main()
