"""Graphics-only cache: bounded rectangles, shared Qt pixels, no system data."""
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import Qt, QRect, QRectF, QEvent
from PySide6.QtGui import QBitmap, QImage, QPixmap, QPixmapCache, QRegion
from PySide6.QtWidgets import QApplication
from cmdrhelper.ui import system_overview as overview
from cmdrhelper.ui.system_view import SystemMapWidget


def original_bounds(pixmap):
    mask = pixmap.toImage().createAlphaMask(Qt.ImageConversionFlag.ThresholdDither)
    visible = QRegion(QBitmap.fromImage(mask)).boundingRect()
    if visible.isEmpty():
        visible = pixmap.rect()
    return QRectF(visible.adjusted(-2, -2, 2, 2).intersected(pixmap.rect()))


class OverviewCacheTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.limit = QPixmapCache.cacheLimit()
        overview._alpha_bounds_cache.clear()
        self.addCleanup(overview._alpha_bounds_cache.clear)
        self.addCleanup(QPixmapCache.setCacheLimit, self.limit)

    def image(self, w=40, h=60, dpr=1):
        image = QImage(w, h, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        for x in range(10, 20):
            for y in range(15, 25):
                image.setPixelColor(x, y, Qt.red)
        pixmap = QPixmap.fromImage(image)
        pixmap.setDevicePixelRatio(dpr)
        return pixmap

    def test_hit_is_copy_and_does_not_repeat_alpha_calculation(self):
        pixmap = self.image()
        with patch.object(overview.QBitmap, 'fromImage', wraps=QBitmap.fromImage) as mask:
            first = overview._alpha_bounds(pixmap)
            first.adjust(10, 10, 10, 10)
            actual = overview._alpha_bounds(QPixmap(pixmap))
            self.assertEqual(mask.call_count, 1)
        self.assertEqual(actual, QRectF(8, 13, 14, 14))

    def test_size_dpr_and_pixel_mutation_never_use_stale_rectangles(self):
        for w, h, dpr in ((40, 60, 1), (80, 120, 1), (40, 60, 2), (40, 60, 1.5)):
            pixmap = self.image(w, h, dpr)
            self.assertEqual(overview._alpha_bounds(pixmap), original_bounds(pixmap))
        pixmap = self.image()
        old = overview._alpha_bounds(pixmap)
        pixmap.fill(Qt.green)
        self.assertNotEqual(overview._alpha_bounds(pixmap), old)
        self.assertEqual(overview._alpha_bounds(pixmap), QRectF(pixmap.rect()))
        pixmap.fill(Qt.transparent)
        self.assertEqual(overview._alpha_bounds(pixmap), original_bounds(pixmap))

    def test_lru_bounded_and_retains_no_pixels(self):
        first = self.image()
        overview._alpha_bounds(first)
        first_key = next(iter(overview._alpha_bounds_cache))
        for _ in range(127):
            overview._alpha_bounds(self.image())
        overview._alpha_bounds(first)
        overview._alpha_bounds(self.image())
        self.assertEqual(len(overview._alpha_bounds_cache), 128)
        self.assertIn(first_key, overview._alpha_bounds_cache)
        self.assertTrue(all(isinstance(v, QRectF) for v in overview._alpha_bounds_cache.values()))
        for _ in range(128):
            overview._alpha_bounds(self.image())
        self.assertNotIn(first_key, overview._alpha_bounds_cache)

    def test_all_packaged_assets_match_original_alpha_bounds(self):
        resolver = SystemMapWidget()
        self.addCleanup(resolver.close)
        paths = list(resolver._body_image_dir.glob('*.png'))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(asset=path.name):
                pixmap = QPixmap(str(path))
                if not pixmap.isNull():
                    self.assertEqual(overview._alpha_bounds(pixmap), original_bounds(pixmap))
                    self.assertEqual(overview._alpha_bounds(pixmap), original_bounds(pixmap))

    def test_qt_limit_warm_reopen_theme_and_system_data_changes(self):
        QPixmapCache.clear(); QPixmapCache.setCacheLimit(10240)
        body = dict(body_id=1, name='One 1', body_type='Planet', planet_class='Rocky body')
        first = overview.SystemOverviewView('One', [body])
        self.assertEqual(QPixmapCache.cacheLimit(), 32768)
        item = first.items_by_key['body', 1]
        image_key, bounds = item.pixmap.cacheKey(), QRectF(item.image_source)
        first.close(); first.deleteLater()
        self.app.sendPostedEvents(None, QEvent.DeferredDelete)
        with patch.object(overview.QBitmap, 'fromImage', wraps=QBitmap.fromImage) as mask:
            for light in (False, True):
                # A different commander/system shares only identical artwork.
                second = overview.SystemOverviewView('Other commander', [dict(body, name='Other 1')], light=light)
                current = second.items_by_key['body', 1]
                self.assertEqual(current.pixmap.cacheKey(), image_key)
                self.assertEqual(current.image_source, bounds)
                self.assertEqual(current.node.body['name'], 'Other 1')
                second.scale(1.8, 1.8); second.resize(800, 500)
                self.assertEqual(current.image_source, bounds)
                second.close(); second.deleteLater()
            self.assertEqual(mask.call_count, 0)
        changed = overview.SystemOverviewView('One', [dict(body, planet_class='Icy body')])
        current = changed.items_by_key['body', 1]
        self.assertNotEqual(current.pixmap.cacheKey(), image_key)
        self.assertEqual(current.image_source, original_bounds(current.pixmap))
        changed.close(); changed.deleteLater()
        self.app.sendPostedEvents(None, QEvent.DeferredDelete)

    def test_qt_eviction_recalculates_for_reloaded_pixels(self):
        resolver = SystemMapWidget()
        body = dict(planet_class='Rocky body')
        pixmap = resolver._body_pixmap(body)
        expected = overview._alpha_bounds(pixmap)
        key = pixmap.cacheKey()
        QPixmapCache.clear()
        other = SystemMapWidget()
        loaded = other._body_pixmap(body)
        self.assertNotEqual(loaded.cacheKey(), key)
        with patch.object(overview.QBitmap, 'fromImage', wraps=QBitmap.fromImage) as mask:
            self.assertEqual(overview._alpha_bounds(loaded), expected)
            mask.assert_called_once()
        resolver.close(); other.close()
