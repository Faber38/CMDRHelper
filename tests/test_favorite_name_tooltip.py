"""Full stored favorite names remain readable independently of title elision."""
import unittest
from unittest.mock import Mock

from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QHelpEvent, QTextDocument
from PySide6.QtWidgets import QApplication, QToolTip

import test_favorites
from cmdrhelper.i18n import tr
from cmdrhelper.ui.favorite_title_delegate import FavoriteTitleDelegate, copy_rect
from cmdrhelper.ui.favorites_view import FavoritesView
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class FavoriteNameTooltipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        fixture = test_favorites.FavoriteTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.fixture = fixture
        self.addCleanup(self.app.setStyleSheet, self.app.styleSheet())
        self.addCleanup(QToolTip.hideText)

    def view(self):
        view = FavoritesView(self.fixture.state, Mock(), Mock())
        self.addCleanup(view.close)
        view.resize(900, 650)
        view.show()
        self.app.processEvents()
        return view

    def hover(self, view, point):
        viewport = view.list.viewport()
        event = QHelpEvent(QEvent.ToolTip, point, viewport.mapToGlobal(point))
        QApplication.sendEvent(viewport, event)
        self.app.processEvents()
        return QToolTip.text()

    def plain(self, tooltip):
        document = QTextDocument()
        document.setHtml(tooltip)
        return document.toPlainText()

    def test_full_name_hover_in_both_themes_without_selection_or_data_changes(self):
        f = self.fixture
        names = ('Kurz #18', 'Sehr langer Favoritenname ' * 60 + '#18',
                 '<b>Wörtlich</b>  &  "Text" #18')
        for name in names:
            f.store.save(1, dict(f.record(), name=name))
        before = f.store.list(1)
        view = self.view()
        self.assertIsInstance(view.list.itemDelegate(), FavoriteTitleDelegate)
        view.list.setCurrentRow(0)
        selected = view.list.currentItem()
        changed, clicked, activated = Mock(), Mock(), Mock()
        view.list.currentItemChanged.connect(changed)
        view.list.itemClicked.connect(clicked)
        view.list.itemDoubleClicked.connect(activated)
        for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.app.setStyleSheet(theme)
            self.app.processEvents()
            for row in range(view.list.count()):
                item = view.list.item(row)
                record = f.store.get(1, item.data(Qt.UserRole))
                name = record['name']
                with self.subTest(theme=theme == DARK_STYLESHEET, name=name[:40]):
                    view.list.scrollToItem(item)
                    self.app.processEvents()
                    rect = view.list.visualItemRect(item)
                    point = QPoint(rect.left() + 120, rect.top() + 10)
                    self.assertTrue(view.list.viewport().rect().contains(point))
                    tooltip = self.hover(view, point)
                    self.assertEqual(self.plain(tooltip), name)
                    self.assertTrue(self.plain(tooltip).endswith('#18'))
                    self.assertEqual(item.text().split('\n')[0], name)
                    self.assertIs(view.list.currentItem(), selected)
                    if len(name) > 1000:
                        self.assertGreater(view.list.fontMetrics().horizontalAdvance(name),
                                           view.list.viewport().width())
            QToolTip.hideText()
        for callback in (changed, clicked, activated):
            callback.assert_not_called()
        self.assertEqual(f.store.list(1), before)

    def test_copy_icon_keeps_its_own_tooltip(self):
        f = self.fixture
        f.store.save(1, dict(f.record(), name='Favorit #18'))
        view = self.view()
        item = view.list.item(0)
        rect = view.list.visualItemRect(item)
        self.assertEqual(self.hover(view, copy_rect(rect).center()),
                         tr('favorites.copy_system'))
        self.assertEqual(self.plain(self.hover(view, QPoint(rect.left() + 120, rect.top() + 10))),
                         'Favorit #18')

    def test_refresh_updates_tooltip_after_rename(self):
        f = self.fixture
        saved = f.store.save(1, dict(f.record(), name='Alt #18'))
        view = self.view()
        item = view.list.item(0)
        name = 'Neu <Name> ' * 30 + '#18'
        f.store.save(1, {'name': name}, saved['id'])
        view.refresh()
        self.assertIs(view.list.item(0), item)
        self.assertEqual(self.plain(item.toolTip()), name)
        rect = view.list.visualItemRect(item)
        self.assertEqual(self.plain(self.hover(view, QPoint(rect.left() + 120, rect.top() + 10))),
                         name)


if __name__ == '__main__':
    unittest.main()
