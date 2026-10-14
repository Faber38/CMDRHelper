import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QImage, QPalette, QPixmap, QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog

from cmdrhelper.ui.favorite_image_view import FavoriteImageCanvas, FavoriteImageDialog, FavoriteImageLabel
from cmdrhelper.ui.favorites_view import preview, FavoritesView
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from test_favorites import State
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.favorites import FavoriteStore


class FavoriteImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'original.png'
        image = QImage(2400, 1200, QImage.Format_RGB32)
        image.fill(Qt.red)
        image.save(str(self.path))
        self.original = self.path.read_bytes()
        self.canvas = FavoriteImageCanvas(QPixmap(str(self.path)))
        self.canvas.resize(800, 600)
        self.canvas.show()
        self.app.processEvents()
        self.addCleanup(self.canvas.close)

    def wheel(self, delta, position=None, canvas=None):
        canvas = canvas or self.canvas
        position = position or QPointF(canvas.width() / 2, canvas.height() / 2)
        event = QWheelEvent(position, canvas.mapToGlobal(position.toPoint()),
                            QPoint(), QPoint(0, delta), Qt.NoButton,
                            Qt.NoModifier, Qt.NoScrollPhase, False)
        QApplication.sendEvent(canvas, event)

    def test_wheel_anchor_limits_aspect_ratio_and_original(self):
        key = self.canvas.pixmap.cacheKey()
        self.wheel(600)
        anchor = QPointF(450, 330)
        before = self.canvas.image_rect()
        fraction = (anchor - before.topLeft()) / before.width()
        self.wheel(120, anchor)
        after = self.canvas.image_rect()
        actual = (anchor - after.topLeft()) / after.width()
        self.assertAlmostEqual(actual.x(), fraction.x())
        self.assertAlmostEqual(actual.y(), fraction.y())
        self.assertAlmostEqual(after.width() / after.height(), 2)
        zoom = self.canvas.zoom
        self.wheel(-120, anchor)
        self.assertLess(self.canvas.zoom, zoom)
        for _ in range(20):
            self.wheel(1200)
        self.assertEqual(self.canvas.zoom, self.canvas.MAX_ZOOM)
        for _ in range(20):
            self.wheel(-1200)
        self.assertEqual(self.canvas.zoom, 1)
        self.assertEqual(self.canvas.offset, QPointF())
        self.assertEqual(self.canvas.pixmap.cacheKey(), key)
        self.assertEqual(self.canvas.pixmap.size(), QImage(str(self.path)).size())
        self.assertEqual(self.path.read_bytes(), self.original)

    def test_drag_reset_and_resize(self):
        start, end = QPoint(400, 300), QPoint(470, 350)
        for zoomed in (False, True):
            if zoomed:
                self.wheel(600)
            QTest.mousePress(self.canvas, Qt.LeftButton, pos=start)
            QTest.mouseMove(self.canvas, end)
            QTest.mouseRelease(self.canvas, Qt.LeftButton, pos=end)
            self.assertEqual(self.canvas.offset, QPointF(70, 50) if zoomed else QPointF())
        QTest.mouseDClick(self.canvas, Qt.LeftButton, pos=end)
        self.assertEqual(self.canvas.zoom, 1)
        self.assertEqual(self.canvas.offset, QPointF())
        self.canvas.resize(500, 800)
        self.app.processEvents()
        rect = self.canvas.image_rect()
        self.assertAlmostEqual(rect.width() / rect.height(), 2)
        self.assertLessEqual(rect.width(), self.canvas.width())
        self.assertLessEqual(rect.height(), self.canvas.height())

    def test_detail_double_click_opens_original_and_preserves_favorite(self):
        database = CMDRDatabase(Path(self.temp.name) / 'app.db')
        with database._connect() as con:
            con.execute("INSERT INTO commanders(id,fid) VALUES (1,'F1')")
        store = FavoriteStore(database)
        record = store.save(1, dict(type='system', system_name='Sol', name='Test',
                                    category='other', note='Keep this'), image_source=self.path)
        stored = store.image_file(record['image_path'])
        stored_bytes = stored.read_bytes()
        view = FavoritesView(State(database), lambda _: None, lambda _: None)
        self.addCleanup(view.close)
        view.list.setCurrentRow(0)
        opened = []

        def exec_dialog(dialog):
            if isinstance(dialog, FavoriteImageDialog):
                opened.append(dialog)
                self.assertEqual(dialog.canvas.pixmap.size(), QImage(str(self.path)).size())
                self.assertGreater(dialog.width(), 600)
                self.wheel(600, canvas=dialog.canvas)
            else:
                label = dialog.findChild(FavoriteImageLabel)
                self.assertIsNotNone(label)
                QTest.mouseDClick(label, Qt.LeftButton)
            return QDialog.Rejected

        with patch.object(QDialog, 'exec', exec_dialog):
            view.open_selected()
        self.assertEqual(len(opened), 1)
        self.assertEqual(store.get(1, record['id']), record)
        self.assertEqual(stored.read_bytes(), stored_bytes)
        self.assertEqual(self.path.read_bytes(), self.original)
        self.assertEqual(view.list.count(), 1)

    def test_escape_and_window_close_in_both_themes(self):
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        colors = []
        for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.app.setStyleSheet(style)
            dialog = FavoriteImageDialog(self.canvas.pixmap)
            dialog.show()
            self.app.processEvents()
            colors.append(dialog.canvas.palette().color(QPalette.Base).name())
            self.assertFalse(dialog.canvas.grab().isNull())
            QTest.keyClick(dialog.canvas, Qt.Key_Escape)
            self.assertFalse(dialog.isVisible())
            dialog.show()
            dialog.close()
            self.assertFalse(dialog.isVisible())
        self.assertNotEqual(*colors)

    def test_missing_or_invalid_image_does_not_open(self):
        label = FavoriteImageLabel(self.path)
        label.setPixmap(preview(self.path))
        self.path.write_bytes(b'invalid')
        with patch.object(QDialog, 'exec') as execute:
            QTest.mouseDClick(label, Qt.LeftButton)
            self.path.unlink()
            QTest.mouseDClick(label, Qt.LeftButton)
            label.setPixmap(QPixmap())
            QTest.mouseDClick(label, Qt.LeftButton)
        execute.assert_not_called()


if __name__ == '__main__':
    unittest.main()
