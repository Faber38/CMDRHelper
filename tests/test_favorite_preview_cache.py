"""Bounded preview pixels and view reuse; synthetic images/DB only."""
import os
from pathlib import Path
import tempfile
import unittest
import weakref
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PIL import Image
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from cmdrhelper.database import CMDRDatabase
from cmdrhelper.favorites import FavoriteStore
from cmdrhelper.i18n import get_language, set_language
from cmdrhelper.ui.favorite_preview_cache import FavoritePreviewCache, preview
from cmdrhelper.ui.favorites_view import FavoritesView, FavoriteDialog
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from test_favorites import State


class PreviewFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cache = FavoritePreviewCache()

    def image(self, name='image.png', color='red', size=(600, 300)):
        path = self.root / name
        Image.new('RGB', size, color).save(path)
        return path


class PreviewCacheTests(PreviewFixture):
    def test_hits_and_returned_pixmap_cannot_mutate_cache(self):
        path = self.image()
        first = self.cache.get(path, owner=(1, 'F1'))
        first.fill(Qt.green)
        second = self.cache.get(path, owner=(1, 'F1'))
        self.assertEqual(second.toImage().pixelColor(0, 0).name(), '#ff0000')
        self.assertEqual((self.cache.decodes, self.cache.hits), (1, 1))
        self.cache.get(path, owner=(2, 'F2'))
        self.assertEqual(self.cache.decodes, 2)

    def test_sizes_and_dpr_have_separate_pixels_and_logical_bounds(self):
        path = self.image()
        for width, height, dpr in ((80, 60, 1), (80, 60, 2), (600, 320, 1), (80, 60, 1.5)):
            with self.subTest(size=(width, height, dpr)):
                image = self.cache.get(path, width, height, dpr=dpr)
                self.assertEqual(image.devicePixelRatio(), dpr)
                self.assertLessEqual(image.deviceIndependentSize().width(), width)
                self.assertLessEqual(image.deviceIndependentSize().height(), height)
                self.assertEqual(image.width(), round(width * dpr))
        self.assertEqual(self.cache.decodes, 4)
        self.cache.get(path, 80, 60, dpr=2)
        self.assertEqual(self.cache.hits, 1)

    def test_lru_enforces_24_mib_and_releases_evicted_wrapper(self):
        paths = [self.image(f'{i}.png', size=(1024, 1024)) for i in range(7)]
        for path in paths[:6]:
            self.cache.get(path, 1024, 1024)
        self.assertEqual(self.cache.bytes_used, 24 * 1024 * 1024)
        key = self.cache.key(paths[1], 1024, 1024)
        evicted = weakref.ref(self.cache._entries[key][0])
        self.cache.get(paths[0], 1024, 1024)  # Make zero most recently used.
        self.cache.get(paths[6], 1024, 1024)
        self.assertNotIn(key, self.cache._entries)
        self.assertIsNone(evicted())
        self.assertEqual(self.cache.evictions, 1)
        self.assertLessEqual(self.cache.bytes_used, self.cache.MAX_BYTES)
        self.cache.clear()
        self.assertEqual(self.cache.bytes_used, 0)

    def test_oversize_image_is_displayed_but_not_cached(self):
        path = self.image(size=(2600, 2600))
        self.assertFalse(self.cache.get(path, 2600, 2600).isNull())
        self.assertEqual(self.cache.bytes_used, 0)
        self.assertFalse(self.cache._entries)

    def test_tiny_images_also_have_bounded_bookkeeping(self):
        path = self.image(size=(1, 1))
        for owner in range(260):
            self.cache.get(path, 1, 1, owner=owner)
        self.assertEqual(len(self.cache._entries), 256)
        self.assertEqual(self.cache.evictions, 4)

    def test_changed_replaced_and_deleted_files_drop_old_versions(self):
        path = self.image()
        self.cache.get(path, 80, 60)
        self.cache.get(path, 600, 320)
        old = path.stat()
        self.image(color='blue')
        os.utime(path, ns=(old.st_atime_ns, old.st_mtime_ns))  # ctime must still invalidate.
        self.assertEqual(self.cache.get(path).toImage().pixelColor(0, 0).name(), '#0000ff')
        self.assertEqual(len(self.cache._entries), 1)
        replacement = self.image('replacement.png', 'green')
        replacement.replace(path)
        self.assertEqual(self.cache.get(path).toImage().pixelColor(0, 0).name(), '#008000')
        path.unlink()
        self.assertTrue(self.cache.get(path).isNull())
        self.assertEqual(self.cache.bytes_used, 0)

    def test_decode_failure_and_racing_change_are_not_cached(self):
        path = self.root / 'broken.png'
        path.write_bytes(b'not an image')
        self.assertTrue(self.cache.get(path).isNull())
        self.image('broken.png')
        self.assertFalse(self.cache.get(path).isNull())
        self.cache.clear()
        def racing(path, width, height, *, dpr):
            result = preview(path, width, height, dpr=dpr)
            self.image('broken.png', 'blue')
            return result
        self.assertTrue(self.cache.get(path, decoder=racing).isNull())
        self.assertEqual(self.cache.bytes_used, 0)


class FavoriteViewCacheTests(PreviewFixture):
    def setUp(self):
        super().setUp()
        self.db = CMDRDatabase(self.root / 'test.db')
        with self.db._connect() as con:
            con.executemany('INSERT INTO commanders(id,fid) VALUES (?,?)', [(1, 'F1'), (2, 'F2')])
        self.state = State(self.db)
        self.store = FavoriteStore(self.db)
        self.first = self.save(1, 'Alpha', 'red')
        self.second = self.save(1, 'Beta', 'blue')
        self.foreign = self.save(2, 'Foreign', 'green')
        self.view = FavoritesView(self.state, Mock(), Mock())
        self.addCleanup(self.view.deleteLater)
        self.addCleanup(self.view.close)
        self.view.show()
        self.app.processEvents()

    def save(self, commander, name, color):
        return self.store.save(commander, dict(type='system', system_name='Sol',
            system_address=0, name=name, category='bio', note=''),
            image_source=self.image(name+'.png', color))

    def test_refresh_reuses_items_selection_scroll_and_decode(self):
        self.view.list.setCurrentRow(1)
        item = self.view.list.currentItem()
        before = self.view._preview_cache.decodes
        for _ in range(4):
            self.view.hide(); self.view.show(); self.view.refresh()
        self.assertIs(self.view.list.currentItem(), item)
        self.assertEqual(self.view._preview_cache.decodes, before)
        self.assertEqual(self.view.selected()['id'], self.second['id'])

    def test_commander_switch_and_stale_selection_never_expose_other_owner(self):
        before = self.view._preview_cache.decodes
        self.view.list.setCurrentRow(0)
        self.state.commander_id, self.state.commander_fid = 2, 'F2'
        self.assertIsNone(self.view.selected())  # Before the UI signal is delivered.
        self.state.commanderIdentityChanged.emit(2, 'F2', 'Other')
        self.assertEqual(self.view.list.count(), 1)
        self.view.list.setCurrentRow(0)
        self.assertEqual(self.view.selected()['id'], self.foreign['id'])
        image = self.view.list.item(0).icon().pixmap(80, 60).toImage()
        self.assertEqual(image.pixelColor(0, 0).name(), '#008000')
        self.state.commander_id, self.state.commander_fid = 1, 'F1'
        self.state.commanderIdentityChanged.emit(1, 'F1', 'First')
        self.assertEqual(self.view.list.count(), 2)
        self.assertEqual(self.view._preview_cache.decodes, before + 1)

    def test_edit_add_delete_and_filters_preserve_fresh_store_checks(self):
        self.view.list.setCurrentRow(1)
        item = self.view.list.currentItem()
        self.store.save(1, dict(self.second, note='changed'), self.second['id'])
        self.view.refresh()
        self.assertIs(self.view.list.currentItem(), item)
        self.assertEqual(self.view.selected()['note'], 'changed')
        self.store.save(1, dict(self.second, name='Aardvark'), self.second['id'])
        self.view.refresh()
        self.assertEqual(self.view.list.currentRow(), 0)
        self.assertEqual(self.view.selected()['id'], self.second['id'])
        self.save(1, 'Third', 'yellow'); self.view.refresh()
        self.assertEqual(self.view.list.count(), 3)
        self.view.search.setText('Alpha')
        self.assertEqual(self.view.list.count(), 1)
        self.assertEqual(self.view.list.item(0).data(Qt.UserRole), self.first['id'])
        self.store.delete(1, self.first['id']); self.view.refresh()
        self.assertEqual(self.view.list.count(), 0)
        self.view.search.clear()
        self.assertEqual(self.view.list.count(), 2)

    def test_missing_or_symlinked_managed_image_clears_warm_icon(self):
        path = self.store.image_file(self.first['image_path'])
        path.unlink(); self.view.refresh()
        self.assertTrue(self.view.list.item(0).icon().isNull())
        path.symlink_to(self.image('outside.png', 'green'))
        self.view.refresh()
        self.assertTrue(self.view.list.item(0).icon().isNull())

    def test_edit_dialog_shares_cache_and_invalidates_old_image(self):
        path = self.store.image_file(self.first['image_path'])
        dialog = FavoriteDialog(self.store, self.state, self.first, self.view)
        self.assertIs(dialog._preview_cache, self.view._preview_cache)
        dialog.select_image(self.image('edited.png', 'blue'))
        dialog._save(); self.view.refresh()
        self.assertFalse(path.exists())
        self.assertFalse(any(key[1] == str(path) for key in self.view._preview_cache._entries))
        self.assertEqual(self.view.list.item(0).icon().pixmap(80,60).toImage().pixelColor(0,0).name(), '#0000ff')
        dialog.deleteLater()

    def test_closed_detail_releases_pixels_and_cache_retained_for_reopen(self):
        self.view.list.setCurrentRow(0)
        with patch.object(QDialog, 'exec', return_value=QDialog.Rejected):
            self.view.open_selected()
            before = self.view._preview_cache.decodes
            self.view.open_selected()
        self.assertEqual(self.view._preview_cache.decodes, before)
        from cmdrhelper.ui.favorite_image_view import FavoriteImageLabel
        self.assertTrue(all(label.pixmap().isNull()
                            for label in self.view.findChildren(FavoriteImageLabel)))

    def test_dpr_event_changes_icon_and_language_theme_keep_valid_pixels(self):
        before = self.view._preview_cache.decodes
        with patch.object(self.view, 'devicePixelRatioF', return_value=2.0):
            self.app.sendEvent(self.view, QEvent(QEvent.DevicePixelRatioChange))
            self.app.processEvents()
            self.assertEqual(self.view._preview_cache.decodes, before + 2)
        self.addCleanup(set_language, get_language())
        for language, style in [('de', DARK_STYLESHEET), ('en', LIGHT_STYLESHEET)]:
            set_language(language);self.view.setStyleSheet(style);self.view.refresh()
            self.assertEqual(self.view._preview_cache.decodes, before + 2)

    def test_foreign_record_dialog_cannot_use_warm_cache(self):
        dialog = FavoriteDialog(self.store, self.state, self.foreign, self.view)
        self.assertTrue(dialog.image.pixmap().isNull())
        dialog.deleteLater()

    def test_warm_screenshot_cache_cannot_bypass_source_changes_or_conflicts(self):
        steam = self.root / 'steam'; steam.mkdir()
        heroic = self.root / 'heroic'; heroic.mkdir()
        for folder, color in ((steam, 'red'), (heroic, 'blue')):
            Image.new('RGB', (20, 10), color).save(folder / 'Screenshot_0001.png')
        key = 'screenshots/commanders/F1/source_dir'
        self.state.values[key] = str(steam)
        dialog = FavoriteDialog(self.store, self.state, self.first, self.view)
        with patch.object(QDialog, 'exec', return_value=QDialog.Accepted):
            dialog._latest()
            self.assertEqual(dialog.image_source, steam / 'Screenshot_0001.png')
            self.state.values[key] = str(heroic)
            dialog._latest()
            self.assertEqual(dialog.image_source, heroic / 'Screenshot_0001.png')
            self.assertEqual(dialog.image.pixmap().toImage().pixelColor(0, 0).name(), '#0000ff')
        before = self.view._preview_cache.decodes
        self.state.values['screenshots/commanders/F2/source_dir'] = str(heroic)
        with patch.object(QMessageBox, 'information') as message, patch.object(QDialog, 'exec') as confirm:
            dialog._latest()
            message.assert_called_once()
            confirm.assert_not_called()
        self.assertEqual(self.view._preview_cache.decodes, before)
        self.state.commander_id, self.state.commander_fid = 2, 'F2'
        self.assertTrue(dialog._preview(heroic / 'Screenshot_0001.png').isNull())
        dialog.deleteLater()
