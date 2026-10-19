"""Copy clicks use structured favorite data without selecting or opening rows."""
import unittest
from unittest.mock import Mock, patch
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
import test_favorites
from cmdrhelper.ui.favorites_view import FavoritesView
from cmdrhelper.ui.favorite_title_delegate import SYSTEM_NAME_ROLE, COPY_CONFIRMED_ROLE, copy_rect
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class FavoriteCopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        fixture = test_favorites.FavoriteTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture

    def test_all_types_and_mining_exact_copy_without_selection_or_actions(self):
        f = self.fixture
        names = ['Mynoaw IH-S c18-68', 'Moon system', 'Mining system', 'Long ' + 'System '*60]
        for kind, category, name in zip(('surface_location', 'body', 'body', 'system'),
                                        ('bio', 'geo', 'mining', 'other'), names):
            record = f.record(kind)
            record.update(system_name=name.rstrip(), category=category, name='Antimon ect')
            f.store.save(1, record)
        navigate, explore, route = Mock(), Mock(), Mock()
        view = FavoritesView(f.state, navigate, explore, route_callback=route)
        self.addCleanup(view.close)
        view.resize(900, 650); view.show(); self.app.processEvents()
        view.list.setCurrentRow(0)
        selected = view.list.currentItem()
        changed, clicked, activated = Mock(), Mock(), Mock()
        view.list.currentItemChanged.connect(changed)
        view.list.itemClicked.connect(clicked)
        view.list.itemDoubleClicked.connect(activated)
        for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            view.setStyleSheet(theme); self.app.processEvents()
            for row in range(view.list.count()):
                item = view.list.item(row)
                view.list.scrollToItem(item); self.app.processEvents()
                rect = view.list.visualItemRect(item)
                point = copy_rect(rect).center()
                self.assertTrue(view.list.viewport().rect().contains(point))
                self.assertGreater(point.x(), rect.center().x())
                self.app.clipboard().setText('sentinel')
                with patch.object(f.db, '_connect', side_effect=AssertionError('copy must not query DB')):
                    QTest.mouseClick(view.list.viewport(), Qt.LeftButton, pos=point)
                self.assertEqual(self.app.clipboard().text(), item.data(SYSTEM_NAME_ROLE))
                self.assertTrue(item.data(COPY_CONFIRMED_ROLE))
                self.assertIs(view.list.currentItem(), selected)
            # A double click on the icon must not open the row either.
            QTest.mouseDClick(view.list.viewport(), Qt.LeftButton, pos=point)
            QTest.mouseRelease(view.list.viewport(), Qt.LeftButton, pos=point)
        for callback in (changed, clicked, activated, navigate, explore, route):
            callback.assert_not_called()

    def test_missing_system_and_canceled_click_leave_clipboard_unchanged(self):
        f = self.fixture
        view = FavoritesView(f.state, Mock(), Mock())
        self.addCleanup(view.close)
        record = f.record('system'); record.update(id=123, image_path='')
        with patch.object(view.store, 'list', return_value=[record]), patch.object(view, '_distances', return_value=(None, {123: None})):
            for missing in (None, '', '   ', 123):
                record['system_name'] = missing
                # The display formatter expects strings; invalid stored values
                # are checked through the structured copy role below.
                if missing == 123:
                    view.list.item(0).setData(SYSTEM_NAME_ROLE, missing)
                else:
                    view.refresh()
                view.resize(900, 650); view.show(); self.app.processEvents()
                item = view.list.item(0)
                point = copy_rect(view.list.visualItemRect(item)).center()
                self.app.clipboard().setText('unchanged')
                QTest.mouseClick(view.list.viewport(), Qt.LeftButton, pos=point)
                self.assertEqual(self.app.clipboard().text(), 'unchanged')
                self.assertFalse(item.data(COPY_CONFIRMED_ROLE))
        item.setData(SYSTEM_NAME_ROLE, 'Sol')
        QTest.mousePress(view.list.viewport(), Qt.LeftButton, pos=point)
        QTest.mouseRelease(view.list.viewport(), Qt.LeftButton, pos=view.list.visualItemRect(item).center())
        self.assertEqual(self.app.clipboard().text(), 'unchanged')

    def test_green_feedback_restarts_and_expires_independently_in_both_themes(self):
        f = self.fixture
        for name in ('Sol', 'Mynoaw IH-S c18-68'):
            record = f.record('system'); record.update(name=name, system_name=name)
            f.store.save(1, record)
        view = FavoritesView(f.state, Mock(), Mock())
        self.addCleanup(view.close)
        view.resize(900, 650); view.show(); self.app.processEvents()
        view.list.setCurrentRow(0)
        selected = view.list.currentItem()
        def click(row):
            item = view.list.item(row)
            point = copy_rect(view.list.visualItemRect(item)).center()
            QTest.mouseClick(view.list.viewport(), Qt.LeftButton, pos=point)
            self.assertEqual(self.app.clipboard().text(), item.data(SYSTEM_NAME_ROLE))
            self.assertIs(view.list.currentItem(), selected)
        for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            view.setStyleSheet(theme); self.app.processEvents()
            first, second = view.list.item(0), view.list.item(1)
            click(0)
            self.assertTrue(first.data(COPY_CONFIRMED_ROLE))
            self.assertFalse(second.data(COPY_CONFIRMED_ROLE))
            image = view.list.viewport().grab().toImage()
            rect = copy_rect(view.list.visualItemRect(first))
            self.assertTrue(any(
                (lambda c: c.green() > c.red() + 30 and c.green() > c.blue() + 30)(image.pixelColor(x, y))
                for x in range(rect.left(), rect.right()) for y in range(rect.top(), rect.bottom())))
            self.assertEqual(next(iter(view.list._copy_timers.values())).interval(), 2000)
            QTest.qWait(1100)
            click(0)
            self.assertEqual(len(view.list._copy_timers), 1)
            QTest.qWait(1050)
            self.assertTrue(first.data(COPY_CONFIRMED_ROLE))  # original deadline passed
            click(1)
            QTest.qWait(1050)
            self.assertFalse(first.data(COPY_CONFIRMED_ROLE))
            self.assertTrue(second.data(COPY_CONFIRMED_ROLE))
            QTest.qWait(1050)
            self.assertFalse(second.data(COPY_CONFIRMED_ROLE))
            self.assertEqual(view.list._copy_timers, {})
        click(0)
        view.refresh()
        self.assertEqual(view.list._copy_timers, {})
        self.assertFalse(view.list.item(0).data(COPY_CONFIRMED_ROLE))
