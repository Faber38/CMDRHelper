"""Pixel regressions for the Odyssey stack gutter; isolated synthetic inventory."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QAbstractItemView, QWidget
from cmdrhelper.ui.odyssey_view import CLEANUP_ROLE, CLEANUP_COLORS
from cmdrhelper.ui.material_row_style import STRIPE_ROLE, COLLECTED_ROLE, THEMES
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
import test_odyssey_view as odyssey_fixture
from test_odyssey_view import inventory
from test_odyssey_inventory import snapshot


class OdysseyBranchStyleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.case = odyssey_fixture.OdysseyViewTests('test_loading_overlay_tracks_completion_error_and_navigation')
        self.case.app = self.app
        self.addCleanup(self.case.doCleanups)
        self.case.setUp()
        self.page, self.view = self.case.page, self.case.view
        screen = self.app.primaryScreen().availableGeometry()
        self.page.resize(min(1100, screen.width()-40), min(800, screen.height()-80))
        self.page.move(10, 10)
        self.inv = inventory([snapshot('ShipLocker', Items=[
            dict(Name='pyrolyticcatalyst', Count=1),
            dict(Name='pyrolyticcatalyst', Count=2, OwnerID=7),
            dict(Name='pyrolyticcatalyst', Count=3, OwnerID=8)]), snapshot('Backpack')])
        self.case.set_inventory(self.inv)
        self.tree = self.view.tree
        self.parent = self.view.summaries[('Items','pyrolyticcatalyst')]
        self.item = self.parent.child(0)
        self.tree.scrollToItem(self.parent, QAbstractItemView.PositionAtCenter)
        QTest.qWait(50)

    def theme(self, light, font=12):
        self.app.setStyleSheet((LIGHT_STYLESHEET if light else DARK_STYLESHEET)
                              + f'\nQWidget {{font-size:{font}px;}}')
        self.page.set_light_mode(light)
        self.tree.scrollToItem(self.parent, QAbstractItemView.PositionAtCenter)
        QTest.qWait(50)

    def state(self, *, cleanup=False, collected=False, selected=False, hover=False):
        self.item.setData(0, CLEANUP_ROLE, cleanup)
        self.item.setData(0, COLLECTED_ROLE, collected)
        self.tree.clearSelection()
        self.item.setSelected(selected)
        QTest.mouseMove(self.tree.header().viewport(), QPoint(5, 5))
        QTest.qWait(40)
        if hover:
            QTest.mouseMove(self.tree.viewport(), self.tree.visualRect(self.tree.indexFromItem(self.item, 0)).center())
            QTest.qWait(70)
            self.assertEqual(self.view.row_delegate.hovered, self.tree.indexFromItem(self.item, 0))
        self.tree.viewport().update()
        QTest.qWait(30)

    def assert_pixels(self, color):
        rect = self.tree.visualRect(self.tree.indexFromItem(self.item, 0))
        left = self.tree.header().sectionViewportPosition(0)
        self.assertEqual(self.tree.indentation(), 16)
        self.assertEqual(rect.left()-left, 16)
        self.assertTrue(self.tree.viewport().rect().contains(rect.center()))
        image = self.tree.viewport().grab().toImage()
        dpr = image.devicePixelRatio()
        # Sample the gutter interior at multiple heights, plus blank cell background.
        points = [(x, y) for x in (left+2, left+8, left+13)
                  for y in (rect.top()+3, rect.center().y(), rect.bottom()-3)]
        points.append((rect.right()-8, rect.center().y()))
        for x, y in points:
            self.assertEqual(image.pixelColor(round(x*dpr), round(y*dpr)).name(), color,
                             (x, y, self.app.platformName(), dpr))

    def test_pixel_colors_and_priority_across_themes_fonts(self):
        for light in (False, True, False):
            for font in (12, 18):
                with self.subTest(light=light, font=font):
                    self.theme(light, font)
                    stripe = THEMES[light]['rows'][self.item.data(0, STRIPE_ROLE)]
                    for flags, expected in [({}, stripe),
                            ({'hover':True}, THEMES[light]['hover']),
                            ({'collected':True,'hover':True}, THEMES[light]['live']),
                            ({'cleanup':True,'collected':True,'hover':True}, CLEANUP_COLORS[light][0]),
                            ({'selected':True,'cleanup':True,'collected':True,'hover':True}, THEMES[light]['selected'])]:
                        with self.subTest(flags=flags):
                            self.state(**flags)
                            self.assert_pixels(expected)

    def test_scroll_columns_collapse_and_inventory_update(self):
        for light in (False, True):
            self.theme(light)
            self.state(cleanup=True)
            self.assert_pixels(CLEANUP_COLORS[light][0])
            self.tree.verticalScrollBar().setValue(max(0, self.tree.verticalScrollBar().value()-1))
            QTest.qWait(40)
            self.assert_pixels(CLEANUP_COLORS[light][0])
            header = self.tree.header()
            header.resizeSection(0, 410)
            header.moveSection(header.visualIndex(0), 0)
            QTest.qWait(40)
            self.assert_pixels(CLEANUP_COLORS[light][0])
            original_item = self.item
            self.parent.setExpanded(False)
            QTest.qWait(30)
            self.assertTrue(self.tree.visualItemRect(self.item).isEmpty())
            self.parent.setExpanded(True)
            QTest.qWait(30)
            self.assert_pixels(CLEANUP_COLORS[light][0])
            updated = inventory([snapshot('ShipLocker', Items=[
                dict(Name='pyrolyticcatalyst', Count=11),
                dict(Name='pyrolyticcatalyst', Count=12, OwnerID=7),
                dict(Name='pyrolyticcatalyst', Count=13, OwnerID=8)]), snapshot('Backpack')])
            self.case.set_inventory(updated)
            self.parent = self.view.summaries[('Items','pyrolyticcatalyst')]
            self.item = self.parent.child(0)
            self.assertIs(self.item, original_item)
            self.assertEqual({self.parent.child(i).text(1) for i in range(3)}, {'11', '12', '13'})
            self.tree.scrollToItem(self.parent, QAbstractItemView.PositionAtCenter)
            QTest.qWait(30)
            self.assert_pixels(CLEANUP_COLORS[light][0])
        self.assertFalse(self.tree.rootIsDecorated())
        self.assertFalse(self.tree.expandsOnDoubleClick())
        self.assertEqual(self.tree.viewport().findChildren(QWidget), [])

    def test_expandable_nodes_keep_native_branch_drawing(self):
        from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
        from cmdrhelper.ui.odyssey_view import OdysseyRowDelegate
        trees = []
        for tree_type in (QTreeWidget, type(self.tree)):
            tree = tree_type()
            self.addCleanup(tree.deleteLater)
            self.addCleanup(tree.close)
            tree.setHeaderHidden(True)
            tree.setIndentation(16)
            tree.setItemDelegate(OdysseyRowDelegate(tree))
            parent = QTreeWidgetItem(tree, ['Stack'])
            child = QTreeWidgetItem(parent, ['Detail'])
            child.setData(0, STRIPE_ROLE, 0)
            tree.resize(280, 140)
            tree.show()
            trees.append((tree, parent))
        for light in (False, True):
            self.theme(light)
            images = []
            for expanded in (True, False):
                glyphs = []
                for tree, parent in trees:
                    tree.itemDelegate().light = light
                    parent.setExpanded(expanded)
                    tree.doItemsLayout()
                    QTest.qWait(30)
                    image = tree.viewport().grab().toImage()
                    dpr = image.devicePixelRatio()
                    height = tree.visualItemRect(parent).height()
                    glyphs.append(image.copy(0, 0, round(16*dpr), round(height*dpr)))
                self.assertEqual(glyphs[0], glyphs[1])
                images.append(glyphs[1])
            self.assertNotEqual(images[0], images[1])
