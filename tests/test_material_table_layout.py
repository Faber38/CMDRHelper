import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtCore import QObject, QSettings, Signal, Qt, QPoint
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QHeaderView

from cmdrhelper.ui.material_view import MaterialView


class Controller(QObject):
    loading = Signal()
    ready = Signal(object, str)


class MaterialTableLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = str(Path(self.tmp.name) / 'ui.ini')
        self.settings = QSettings(self.path, QSettings.Format.IniFormat)
        self.view = self.make_view(self.settings)

    def make_view(self, settings):
        view = MaterialView(SimpleNamespace(settings=settings), controller=Controller())
        view.resize(1000, 600)
        view.show()
        self.app.processEvents()
        self.addCleanup(view.close)
        return view

    def widths(self, view=None):
        return [(view or self.view).tree.columnWidth(i) for i in range(4)]

    def order(self, view=None):
        return [(view or self.view).tree.header().logicalIndex(i) for i in range(4)]

    def config(self):
        return dict(version=1, columns=['name', 'grade', 'stock', 'fill'],
                    widths=[380, 90, 180, 170], order=[0, 2, 3, 1])

    def test_mouse_resize_persists_and_all_columns_interactive(self):
        header = self.view.tree.header()
        for i in range(4):
            self.assertEqual(header.sectionResizeMode(i), QHeaderView.ResizeMode.Interactive)
        start = QPoint(header.sectionViewportPosition(0) + header.sectionSize(0) - 1, header.height() // 2)
        QTest.mousePress(header.viewport(), Qt.MouseButton.LeftButton, pos=start)
        QTest.mouseMove(header.viewport(), start + QPoint(65, 0), 20)
        QTest.mouseRelease(header.viewport(), Qt.MouseButton.LeftButton, pos=start + QPoint(65, 0))
        self.assertGreater(header.sectionSize(0), 320)
        self.assertEqual(self.settings.value('materials/columns')['widths'], self.widths())

    def test_widths_survive_new_settings_instance_and_restart(self):
        header = self.view.tree.header()
        for i, width in enumerate((410, 95, 210, 190)):
            header.resizeSection(i, width)
        restarted = self.make_view(QSettings(self.path, QSettings.Format.IniFormat))
        self.assertEqual(self.widths(restarted), [410, 95, 210, 190])

    def test_order_move_and_restart_including_first_column(self):
        header = self.view.tree.header()
        self.assertTrue(header.sectionsMovable())
        self.assertTrue(header.isFirstSectionMovable())
        header.moveSection(1, 3)
        self.assertEqual(self.settings.value('materials/columns')['order'], [0, 2, 3, 1])
        restarted = self.make_view(QSettings(self.path, QSettings.Format.IniFormat))
        self.assertEqual(self.order(restarted), [0, 2, 3, 1])
        restarted.tree.header().moveSection(0, 2)
        again = self.make_view(QSettings(self.path, QSettings.Format.IniFormat))
        self.assertEqual(self.order(again), [2, 3, 0, 1])

    def test_mouse_can_reorder_header(self):
        header = self.view.tree.header()
        start = QPoint(header.sectionViewportPosition(1) + 20, header.height() // 2)
        target = QPoint(header.sectionViewportPosition(3) + header.sectionSize(3) - 15, start.y())
        QTest.mousePress(header.viewport(), Qt.MouseButton.LeftButton, pos=start)
        QTest.mouseMove(header.viewport(), start + QPoint(25, 0), 30)
        QTest.mouseMove(header.viewport(), target, 30)
        QTest.mouseRelease(header.viewport(), Qt.MouseButton.LeftButton, pos=target)
        self.assertEqual(self.order(), [0, 2, 3, 1])
        self.assertEqual(self.settings.value('materials/columns')['order'], self.order())

    def test_common_layout_survives_tabs_hide_show_render_and_window_resize(self):
        header = self.view.tree.header()
        header.resizeSection(0, 450)
        header.resizeSection(3, 240)
        header.moveSection(1, 3)
        saved = self.settings.value('materials/columns')
        for tab in (1, 2, 0):
            self.view.tabs.setCurrentIndex(tab)
            self.view.hide()
            self.view.show()
            for width in (550, 1200):
                self.view.resize(width, 600)
                self.app.processEvents()
                self.view.render()
                self.assertEqual(self.widths(), saved['widths'])
                self.assertEqual(self.order(), saved['order'])
                self.assertEqual(self.settings.value('materials/columns'), saved)
        self.view.tabs.setCurrentIndex(2)
        header.resizeSection(2, 260)
        for tab in (0, 1):
            self.view.tabs.setCurrentIndex(tab)
            self.assertEqual(self.view.tree.columnWidth(2), 260)
        self.view.resize(550, 600)
        self.app.processEvents()
        self.assertGreater(self.view.tree.horizontalScrollBar().maximum(), 0)

    def assert_defaults(self, saved):
        self.settings.setValue('materials/columns', saved)
        self.settings.sync()
        restored = self.make_view(QSettings(self.path, QSettings.Format.IniFormat))
        self.assertEqual(self.widths(restored), [320, 80, 160, 160])
        self.assertEqual(self.order(restored), [0, 1, 2, 3])
        self.assertTrue(all(not restored.tree.isColumnHidden(i) for i in range(4)))
        restored.close()

    def test_invalid_widths_fall_back_without_disappearing_columns(self):
        for widths in ([0, 90, 180, 170], [-1, 90, 180, 170], [2001, 90, 180, 170],
                       [True, 90, 180, 170], [90.5, 90, 180, 170], ['bad', 90, 180, 170], [70]):
            with self.subTest(widths=widths):
                self.assert_defaults({**self.config(), 'widths': widths})

    def test_invalid_order_falls_back(self):
        for order in ([0, 0, 2, 3], [0, 1, 2], [0, 1, 2, 4], [0, 1, 2, -1],
                      [False, 1, 2, 3], ['0', 1, 2, 3], 'broken'):
            with self.subTest(order=order):
                self.assert_defaults({**self.config(), 'order': order})

    def test_obsolete_corrupt_and_changed_column_schema_use_defaults(self):
        for value in ('broken', b'broken', {}, {**self.config(), 'version': 2},
                      {**self.config(), 'columns': ['name', 'grade', 'stock', 'fill', 'extra']},
                      {**self.config(), 'columns': ['name', 'grade', 'other', 'fill']}):
            with self.subTest(value=value):
                self.assert_defaults(value)

    def test_minimum_width_and_default_visibility(self):
        for i in range(4):
            self.view.tree.header().resizeSection(i, 0)
            self.assertGreaterEqual(self.view.tree.columnWidth(i), 40)
            self.assertFalse(self.view.tree.isColumnHidden(i))
        restored = self.make_view(QSettings(self.path, QSettings.Format.IniFormat))
        self.assertEqual(self.widths(restored), [40] * 4)
