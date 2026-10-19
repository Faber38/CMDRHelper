import os
import unittest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QListWidget, QListWidgetItem, QStyledItemDelegate

from cmdrhelper.ui.favorite_title_delegate import FavoriteTitleDelegate
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class FavoriteTitleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_only_title_changes_in_both_themes_and_selection_states(self):
        previous_style = self.app.styleSheet()
        self.addCleanup(self.app.setStyleSheet, previous_style)
        for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.app.setStyleSheet(theme)
            for selected in (False, True):
                for title in ('Helium-3 1x', 'Iridium', 'Monazit', 'Osmium 2x',
                              'Serendibit', 'A very long favorite title ' * 8):
                    with self.subTest(theme=theme == DARK_STYLESHEET,
                                      selected=selected, title=title):
                        widget = QListWidget()
                        widget.resize(500, 180)
                        widget.setIconSize(QSize(80, 60))
                        widget.setUniformItemSizes(True)
                        pixmap = QPixmap(80, 40)
                        pixmap.fill(Qt.red)
                        text = title + '\nSol · Sol 1\nBiologie · 12 Lj'
                        item = QListWidgetItem(QIcon(pixmap), text)
                        item.setData(Qt.UserRole, 42)
                        widget.addItem(item)
                        widget.show()
                        item.setSelected(selected)
                        self.app.processEvents()
                        baseline = widget.viewport().grab().toImage()
                        original_rect = widget.visualItemRect(item)
                        widget.setItemDelegate(FavoriteTitleDelegate(widget))
                        self.app.processEvents()
                        rendered = widget.viewport().grab().toImage()
                        self.assertEqual(widget.visualItemRect(item), original_rect)
                        self.assertEqual(item.text(), text)
                        self.assertEqual(item.data(Qt.UserRole), 42)
                        self.assertEqual(item.isSelected(), selected)
                        # Outside the new copy area, lower lines and thumbnail
                        # retain their native appearance.
                        lower = original_rect.top() + original_rect.height() // 3 + 1
                        self.assertEqual(baseline.copy(0, lower, baseline.width()-30, baseline.height()-lower),
                                         rendered.copy(0, lower, rendered.width()-30, rendered.height()-lower))
                        self.assertEqual(baseline.copy(0, 0, 85, baseline.height()),
                                         rendered.copy(0, 0, 85, rendered.height()))
                        self.assertNotEqual(baseline, rendered)
                        # Antialiased glyphs blend with the theme/selection surface.
                        yellow_pixels = sum(
                            1 for y in range(lower) for x in range(85, rendered.width())
                            if (lambda c: c.red() > 220 and 165 < c.green() < 225
                                and c.blue() < 100)(rendered.pixelColor(x, y)))
                        self.assertGreater(yellow_pixels, 0)
                        widget.close()


if __name__ == '__main__':
    unittest.main()
