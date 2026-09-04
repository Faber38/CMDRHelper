from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtCore import QObject, QSettings, Signal, Qt
from PySide6.QtWidgets import QApplication

from cmdrhelper.ui.screenshot_view import ScreenshotView, safe_filename_component


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

    def _source(self, name="Screenshot.bmp", stamp=None):
        source = Path(self.temp.name) / name
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
        second = self.view._output_path(source)
        self.assertEqual(first.parent.name, "Same_F-A")
        self.assertEqual(second.parent.name, "Same_F-B")
        self.assertNotEqual(first.parent, second.parent)

    def test_filename_uses_bmp_time_commander_and_safe_system(self):
        stamp = datetime(2026, 9, 4, 13, 18, 22).timestamp()
        source = self._source(stamp=stamp)
        self.state.commander = "FABER38"
        self.state.commander_fid = "F12520967"
        self.state.system = "Prua Hypai RB-D c29-71"
        path = self.view._output_path(source)
        self.assertEqual(path.parent.name, "FABER38_F12520967")
        self.assertEqual(
            path.name,
            "2026-09-04_13-18-22_FABER38_Prua-Hypai-RB-D-c29-71.png",
        )

    def test_unknown_identity_and_optional_system(self):
        self.state.commander = ""
        self.state.commander_fid = ""
        self.state.system = ""
        path = self.view._output_path(self._source())
        self.assertEqual(path.parent.name, "UNKNOWN_UNKNOWN")
        self.assertTrue(path.name.endswith("_UNKNOWN.png"))
        self.assertNotIn("SYSTEM", path.name)

    def test_invalid_and_windows_reserved_components_are_safe(self):
        self.assertEqual(safe_filename_component("CON"), "_CON")
        self.assertEqual(safe_filename_component("LPT1.txt"), "_LPT1.txt")
        cleaned = safe_filename_component(' A/B\\C:*?"<>|. ')
        self.assertNotRegex(cleaned, r'[<>:"/\\|?*]')
        self.assertFalse(cleaned.endswith((".", " ")))

    def test_queue_freezes_identity_and_reserves_same_second_collisions(self):
        self.view.pool = PoolStub()
        first_source = self._source("First.bmp")
        second_source = self._source("Second.bmp")
        stamp = datetime(2026, 9, 4, 13, 18, 22).timestamp()
        os.utime(first_source, (stamp, stamp))
        os.utime(second_source, (stamp, stamp))
        self.view._queue(first_source)
        self.state.commander = "Bravo"
        self.state.commander_fid = "F-B"
        self.state.system = "Bravo System"
        first_worker = self.view.pool.workers[0]
        self.view._queue(second_source)
        second_worker = self.view.pool.workers[1]
        self.assertEqual(first_worker.target.parent.name, "Same_F-A")
        self.assertIn("Same_Alpha-System", first_worker.target.name)
        self.assertEqual(second_worker.target.parent.name, "Bravo_F-B")

        # A second A screenshot queued for the same second cannot reuse target 1.
        self.state.commander = "Same"
        self.state.commander_fid = "F-A"
        self.state.system = "Alpha System"
        third_source = self._source("Third.bmp")
        os.utime(third_source, (stamp, stamp))
        self.view._queue(third_source)
        self.assertTrue(self.view.pool.workers[2].target.stem.endswith("_2"))

    def test_gallery_current_follows_viewed_commander(self):
        a = self._image(self.root / "Same_F-A" / "a.png")
        b = self._image(self.root / "Same_F-B" / "b.png")
        self._set_filter("current")
        self.view._refresh_gallery()
        self.assertEqual(self.view.gallery.count(), 1)
        self.assertEqual(Path(self.view.gallery.item(0).data(Qt.UserRole)), a)
        self.state.viewed_commander_id = 2
        self.state.viewedCommanderChanged.emit(2)
        self.assertEqual(self.view.gallery.count(), 1)
        self.assertEqual(Path(self.view.gallery.item(0).data(Qt.UserRole)), b)

    def test_all_and_unassigned_filters_keep_legacy_untouched(self):
        legacy = self._image(self.root / "legacy.png")
        self._image(self.root / "Same_F-A" / "a.png")
        self._image(self.root / "Same_F-B" / "b.png")
        self._set_filter("all")
        self.view._refresh_gallery()
        self.assertEqual(self.view.gallery.count(), 2)
        self._set_filter("unassigned")
        self.view._refresh_gallery()
        self.assertEqual(self.view.gallery.count(), 1)
        self.assertEqual(Path(self.view.gallery.item(0).data(Qt.UserRole)), legacy)
        self.assertTrue(legacy.exists())

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
