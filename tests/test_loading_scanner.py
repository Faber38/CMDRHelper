"""Focused offscreen lifecycle and responsiveness checks, no live user data."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import time
import unittest
from pathlib import Path
from threading import Event
from unittest.mock import patch

from PIL import Image
from PySide6.QtCore import QSettings, QTimer
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QStackedWidget, QWidget
from cmdrhelper.i18n import _TRANSLATIONS, tr_for_language
from cmdrhelper.ui.loading_scanner import LoadingScanner
from cmdrhelper.ui.screenshot_view import ScreenshotView
from cmdrhelper.ui import screenshot_loader
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests.test_screenshot_multi_commander import StateStub


def wait_for(predicate, timeout=5000):
    deadline = time.monotonic() + timeout / 1000
    while not predicate() and time.monotonic() < deadline:
        QTest.qWait(10)
    assert predicate(), 'asynchronous operation timed out'


class LoadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.target = root / 'images'
        self.target.mkdir()
        settings = QSettings(str(root / 'settings.ini'), QSettings.IniFormat)
        settings.setValue('screenshots/target_dir', str(self.target))
        self.view = ScreenshotView(StateStub(settings))
        self.host = QStackedWidget()
        self.host.addWidget(QWidget())
        self.host.addWidget(self.view)
        self.host.resize(1100, 800)
        self.host.show()

    def tearDown(self):
        self.host.close()
        self.view.pool.waitForDone(5000)
        self.app.processEvents()
        self.host.deleteLater()
        self.temp.cleanup()

    def image(self, name='ok.png'):
        folder = self.target / 'Same_F-A'
        folder.mkdir(exist_ok=True)
        path = folder / name
        Image.new('RGB', (800, 600), 'blue').save(path)
        return path

    def test_visible_animation_clicks_navigation_and_cached_reopen(self):
        self.image()
        gate = Event()
        entered = Event()
        original = screenshot_loader.read_image
        def blocked(*args):
            entered.set()
            gate.wait(3)
            return original(*args)
        try:
            with patch.object(screenshot_loader, 'read_image', blocked):
                start = time.monotonic()
                self.host.setCurrentWidget(self.view)
                wait_for(entered.is_set)
                self.assertTrue(self.view.scanner.isVisible())
                first = self.view.scanner.grab().toImage()
                visible_ms = (time.monotonic() - start) * 1000
                worker = self.view._gallery_worker
                for _ in range(10):
                    self.host.setCurrentWidget(self.view)
                    self.view._check_gallery_changes()
                self.assertIs(self.view._gallery_worker, worker)
                QTest.qWait(130)
                second = self.view.scanner.grab().toImage()
                self.assertNotEqual(first, second)
                self.assertTrue(self.view.scanner.timer.isActive())
                print(f'First visible scanner incl. worker start: {visible_ms:.1f} ms')
                self.host.setCurrentIndex(0)
                self.assertFalse(self.view.scanner.timer.isActive())
                gate.set()
                wait_for(lambda: self.view._ready)
                self.assertEqual(self.host.currentIndex(), 0)
                self.assertEqual(self.view.gallery.count(), 1)
                self.host.setCurrentWidget(self.view)
                self.assertIs(self.view._stack.currentWidget(), self.view._content)
                self.assertFalse(self.view.scanner.timer.isActive())
        finally:
            gate.set()

    def test_real_image_load_keeps_event_loop_running(self):
        for index in range(80):
            self.image(f'{index}.png')
        ticks = []
        heartbeat = QTimer()
        heartbeat.setInterval(10)
        heartbeat.timeout.connect(lambda: ticks.append(time.monotonic()))
        start = time.monotonic()
        heartbeat.start()
        try:
            self.host.setCurrentWidget(self.view)
            wait_for(lambda: self.view._ready)
            self.assertEqual(self.view.gallery.count(), 80)
            self.assertGreater(len(ticks), 0)
            gaps = [b-a for a, b in zip([start] + ticks, ticks + [time.monotonic()])]
            print(f'80 images: {(time.monotonic()-start)*1000:.1f} ms, '
                  f'maximum event loop heartbeat gap: {max(gaps)*1000:.1f} ms')
        finally:
            heartbeat.stop()

    def test_empty_corrupt_error_retry(self):
        self.host.setCurrentWidget(self.view)
        wait_for(lambda: self.view._ready)
        self.assertEqual(self.view.gallery.count(), 0)
        good = self.image()
        good.with_name('bad.png').write_bytes(b'corrupt')
        self.view._request_gallery_refresh()
        wait_for(lambda: self.view._gallery_worker is None and not self.view._populate_timer.isActive())
        self.assertEqual(self.view.gallery.count(), 1)
        self.assertIn('1', self.view.last_action.text())
        with patch.object(screenshot_loader, 'read_image', side_effect=OSError('test failure')):
            self.view._request_gallery_refresh()
            wait_for(lambda: self.view._stack.currentWidget() is self.view._error_page)
        self.assertFalse(self.view.scanner.timer.isActive())
        self.assertIn('test failure', self.view._load_error.text())
        self.view._request_gallery_refresh()
        wait_for(lambda: self.view._ready)
        self.assertEqual(self.view.gallery.count(), 1)

    def test_close_during_load(self):
        self.image()
        gate = Event()
        original = screenshot_loader.read_image
        try:
            with patch.object(screenshot_loader, 'read_image', lambda *args: (gate.wait(3), original(*args))[1]):
                self.host.setCurrentWidget(self.view)
                worker = self.view._gallery_worker
                self.host.close()
                self.assertTrue(worker.cancelled.is_set())
                self.assertFalse(self.view.scanner.timer.isActive())
                gate.set()
                self.view.pool.waitForDone(5000)
                self.app.processEvents()
                self.assertFalse(self.view._ready)
        finally:
            gate.set()

    def test_themes_languages_and_scanner_lifecycle(self):
        scanner = LoadingScanner()
        try:
            for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
                scanner.setStyleSheet(style)
                scanner.show()
                QTest.qWait(40)
                self.assertTrue(scanner.timer.isActive())
                self.assertFalse(scanner.grab().isNull())
                scanner.hide()
                self.assertFalse(scanner.timer.isActive())
            self.assertEqual(len(_TRANSLATIONS), 12)
            for lang, table in _TRANSLATIONS.items():
                for key in ('loading.data', 'loading.error', 'loading.retry', 'loading.skipped'):
                    self.assertIn(key, table)
                    self.assertNotEqual(tr_for_language(lang, key), key)
            scanner.setText('Custom translated status')
            self.assertEqual(scanner._text, 'Custom translated status')
        finally:
            scanner.close()
