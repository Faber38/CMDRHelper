"""Cursor filter lifetime regressions using synthetic Qt widgets only."""
import os
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QHoverEvent, QMouseEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog, QMenu, QPushButton, QTableWidget, QVBoxLayout, QWidget
from shiboken6 import delete, isValid

from cmdrhelper.ui.cursors import CursorPolicy
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


def motion(kind=QEvent.MouseMove):
    if kind == QEvent.HoverMove:
        return QHoverEvent(kind, QPointF(2, 2), QPointF(2, 2), QPointF(1, 1), Qt.NoModifier)
    return QMouseEvent(kind, QPointF(2, 2), QPointF(2, 2), Qt.NoButton, Qt.NoButton, Qt.NoModifier)


class CursorLifetimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.policy = CursorPolicy(self.app)
        self.app.installEventFilter(self.policy)
        self.addCleanup(self.remove_policy)

    def remove_policy(self):
        self.app.removeEventFilter(self.policy)
        self.policy.deleteLater()

    def widget(self, cls=QWidget, *args):
        widget = cls(*args)
        self.addCleanup(lambda: delete(widget) if isValid(widget) else None)
        return widget

    def test_deleted_receiver_is_consumed_before_any_qt_access(self):
        widget = self.widget()
        delete(widget)
        self.assertIsInstance(widget, QWidget)
        self.assertFalse(isValid(widget))
        for setting in (False, True):
            self.policy._setting = setting
            for kind in (QEvent.MouseMove, QEvent.HoverMove, QEvent.Show, QEvent.Polish,
                         QEvent.CursorChange, QEvent.Enter, QEvent.Leave, QEvent.EnabledChange):
                with self.subTest(setting=setting, kind=kind):
                    event = motion(kind) if kind in (QEvent.MouseMove, QEvent.HoverMove) else QEvent(kind)
                    # Deliberately call the Python filter; never send Qt an already freed pointer.
                    self.assertTrue(self.policy.eventFilter(widget, event))

    def test_parent_destruction_during_update_prevents_parent_and_viewport_access(self):
        for kind in (QEvent.MouseMove, QEvent.HoverMove):
            parent = self.widget(QTableWidget)
            viewport = parent.viewport()
            with patch.object(self.policy, 'update', side_effect=lambda *args: delete(parent)), \
                 patch.object(viewport, 'parentWidget', side_effect=AssertionError('access after deletion')) as access, \
                 patch.object(self.policy, '_after_native_event') as pending:
                self.assertTrue(self.policy.eventFilter(viewport, motion(kind)))
                self.assertFalse(isValid(viewport))
                access.assert_not_called()
                pending.assert_not_called()

    def test_real_cursor_change_can_destroy_receiver_reentrantly(self):
        class DestroyOnCursor(QObject):
            def eventFilter(self, watched, event):
                if event.type() == QEvent.CursorChange:
                    watched.deleteLater()
                    QCoreApplication.sendPostedEvents(watched, QEvent.DeferredDelete)
                    return True
                return False
        for kind in (QEvent.MouseMove, QEvent.HoverMove):
            widget = self.widget()
            widget.setProperty('cursorClickable', True)
            self.policy._setting = True
            widget.setCursor(Qt.ArrowCursor)
            self.policy._setting = False
            destroy = DestroyOnCursor()
            widget.installEventFilter(destroy)
            self.assertTrue(isValid(widget))
            # The nested CursorChange uses real Qt delivery; the outer call is
            # direct so this also fails safely against the unfixed filter.
            self.assertTrue(self.policy.eventFilter(widget, motion(kind)))
            self.assertFalse(isValid(widget))
            self.assertFalse(self.policy._setting)

    def test_deletion_in_other_update_branches_does_not_forward_event(self):
        for kind in (QEvent.Enter, QEvent.Leave, QEvent.EnabledChange):
            widget = self.widget()
            with patch.object(self.policy, 'update', side_effect=lambda *args: delete(widget)):
                self.assertTrue(self.policy.eventFilter(widget, QEvent(kind)))

    def test_live_events_continue_to_widget_and_keep_cursor_rules(self):
        class Receiver(QPushButton):
            moves = 0
            def mouseMoveEvent(self, event):
                self.moves += 1
                super().mouseMoveEvent(event)
        widget = self.widget(Receiver, 'Synthetic')
        widget.setMouseTracking(True)
        for kind in (QEvent.MouseMove, QEvent.HoverMove, QEvent.Enter, QEvent.Leave):
            event = motion(kind) if kind in (QEvent.MouseMove, QEvent.HoverMove) else QEvent(kind)
            self.assertFalse(self.policy.eventFilter(widget, event))
        self.assertEqual(widget.cursor().shape(), Qt.PointingHandCursor)
        QCoreApplication.sendEvent(widget, motion())
        self.assertEqual(widget.moves, 1)
        self.policy._setting = True
        self.assertFalse(self.policy.eventFilter(widget, motion()))
        self.policy._setting = False
        other = QObject()
        self.assertFalse(self.policy.eventFilter(other, QEvent(QEvent.User)))

    def test_runtime_errors_on_live_widgets_remain_visible(self):
        widget = self.widget()
        with patch.object(self.policy, 'update', side_effect=RuntimeError('synthetic unrelated failure')):
            with self.assertRaisesRegex(RuntimeError, 'synthetic unrelated failure'):
                self.policy.eventFilter(widget, motion())
        self.assertTrue(isValid(widget))

    def test_pending_repair_skips_deleted_viewport(self):
        table = self.widget(QTableWidget)
        viewport = table.viewport()
        self.policy._after_native_event(viewport, QPoint(2, 2))
        delete(table)
        with patch.object(self.policy, 'update') as update:
            self.app.processEvents()
            self.assertFalse(any(call.args and call.args[0] is viewport for call in update.call_args_list))

    def test_dialog_menu_churn_and_themes_have_no_unhandled_exceptions(self):
        old_style = self.app.styleSheet()
        self.addCleanup(self.app.setStyleSheet, old_style)
        errors = []
        with patch.object(sys, 'excepthook', side_effect=lambda *args: errors.append(args)):
            for index in range(30):
                dialog = self.widget(QDialog)
                layout = QVBoxLayout(dialog)
                table = QTableWidget(2, 2)
                button = QPushButton('Synthetic')
                layout.addWidget(table); layout.addWidget(button)
                dialog.show()
                self.app.processEvents()
                self.app.setStyleSheet(DARK_STYLESHEET if index % 2 else LIGHT_STYLESHEET)
                QTest.mouseMove(table.viewport(), QPoint(4, 4))
                button.setEnabled(False); button.setEnabled(True)
                menu = QMenu(dialog)
                menu.addAction('Synthetic')
                menu.popup(dialog.mapToGlobal(QPoint(10, 10)))
                self.app.processEvents()
                QTest.mouseMove(menu, QPoint(5, 5))
                menu.close(); menu.deleteLater()
                self.policy._after_native_event(table.viewport(), QPoint(4, 4))
                dialog.setAttribute(Qt.WA_DeleteOnClose, True)
                dialog.close(); dialog.deleteLater()
                QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
                self.app.processEvents()
                self.assertFalse(isValid(dialog))
            self.assertEqual(errors, [])
