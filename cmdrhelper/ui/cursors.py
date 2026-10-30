"""Application cursor policy for standard controls, without overriding map gestures.

Item views use hit testing: empty space and disabled items are not clickable.
Qt retains ownership of resize/drag cursors and rich-text label link hit testing.
"""
from weakref import WeakKeyDictionary, ref

from PySide6.QtCore import QEvent, QObject, QPoint, Qt, QTimer
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QAbstractButton, QAbstractItemView, QAbstractSlider, QAbstractSpinBox,
    QComboBox, QGroupBox, QHeaderView, QLineEdit, QMenu, QMenuBar,
    QPlainTextEdit, QStyle, QStyleOptionGroupBox, QTabBar, QTextEdit,
    QTreeView, QWidget,
)
from shiboken6 import isValid


class CursorPolicy(QObject):
    def __init__(self, app):
        super().__init__(app)
        self._disabled = WeakKeyDictionary()
        self._pending = WeakKeyDictionary()
        self._setting = False

    def _set(self, widget, shape):
        if widget.cursor().shape() != shape:
            self._setting = True
            try:
                widget.setCursor(shape)
            finally:
                self._setting = False

    def update(self, widget, position=None):
        if not isValid(widget):
            return
        if not widget.isEnabled():
            if widget not in self._disabled:
                self._disabled[widget] = (QCursor(widget.cursor())
                    if widget.testAttribute(Qt.WA_SetCursor) else None)
            self._set(widget, Qt.ArrowCursor)
            return
        if widget in self._disabled:
            original = self._disabled.pop(widget)
            self._setting = True
            try:
                widget.setCursor(original) if original is not None else widget.unsetCursor()
            finally:
                self._setting = False
        parent = widget.parentWidget()
        if (isinstance(parent, QAbstractItemView) and widget is parent.viewport()
                and parent.cursor().shape() not in (Qt.ArrowCursor, Qt.PointingHandCursor, Qt.IBeamCursor)):
            # QHeaderView installs its native resize cursor on the header, not
            # its viewport. An explicit viewport hand would hide that cursor.
            self._setting = True
            try:
                widget.unsetCursor()
            finally:
                self._setting = False
            return
        # Busy, pan, drag and native resize cursors remain owned by their widgets.
        if widget.cursor().shape() not in (Qt.ArrowCursor, Qt.PointingHandCursor, Qt.IBeamCursor):
            return
        point = position if position is not None else widget.mapFromGlobal(QCursor.pos())
        if isinstance(parent, QGroupBox) and parent.isCheckable():
            self.update(parent, widget.mapTo(parent, point))
        shape = None
        if isinstance(widget, QLineEdit):
            shape = Qt.IBeamCursor
        elif isinstance(widget, QAbstractSpinBox) and widget.isReadOnly():
            shape = Qt.ArrowCursor
        elif isinstance(widget, (QAbstractButton, QComboBox, QAbstractSpinBox, QAbstractSlider)):
            shape = Qt.PointingHandCursor
        elif isinstance(widget, QTabBar):
            tab = widget.tabAt(point)
            shape = Qt.PointingHandCursor if tab >= 0 and widget.isTabEnabled(tab) else Qt.ArrowCursor
        elif isinstance(widget, (QMenu, QMenuBar)):
            action = widget.actionAt(point)
            shape = (Qt.PointingHandCursor if action is not None and action.isEnabled()
                     and not action.isSeparator() else Qt.ArrowCursor)
        elif isinstance(widget, QGroupBox) and widget.isCheckable():
            option = QStyleOptionGroupBox()
            widget.initStyleOption(option)
            control = widget.style().hitTestComplexControl(QStyle.CC_GroupBox, option, point, widget)
            shape = (Qt.PointingHandCursor if control in (QStyle.SC_GroupBoxCheckBox, QStyle.SC_GroupBoxLabel)
                     else Qt.ArrowCursor)
        elif widget.property("cursorClickable") is not None:
            shape = Qt.PointingHandCursor if widget.property("cursorClickable") else Qt.ArrowCursor
        elif isinstance(parent, (QTextEdit, QPlainTextEdit)) and widget is parent.viewport():
            if isinstance(parent, QTextEdit) and parent.anchorAt(point) and parent.textInteractionFlags() & Qt.LinksAccessibleByMouse:
                shape = Qt.PointingHandCursor
            else:
                selectable = parent.textInteractionFlags() & (Qt.TextEditable | Qt.TextSelectableByMouse)
                shape = Qt.IBeamCursor if selectable else Qt.ArrowCursor
        elif isinstance(parent, QAbstractItemView) and widget is parent.viewport():
            shape = self._item_cursor(parent, point)
        if shape is not None:
            self._set(widget, shape)

    @staticmethod
    def _item_cursor(view, point):
        if isinstance(view, QHeaderView):
            section = view.logicalIndexAt(point)
            return (Qt.PointingHandCursor if section >= 0 and (view.sectionsClickable() or view.sectionsMovable())
                    else Qt.ArrowCursor)
        index = view.indexAt(point)
        if not index.isValid() or not index.flags() & Qt.ItemIsEnabled:
            return Qt.ArrowCursor
        flags = index.flags()
        selectable = flags & Qt.ItemIsSelectable and view.selectionMode() != QAbstractItemView.NoSelection
        editable = flags & Qt.ItemIsEditable and view.editTriggers() != QAbstractItemView.NoEditTriggers
        expandable = isinstance(view, QTreeView) and view.itemsExpandable() and view.model().hasChildren(index)
        checkable = flags & Qt.ItemIsUserCheckable and index.data(Qt.CheckStateRole) is not None
        return (Qt.PointingHandCursor if selectable or editable or expandable or checkable
                else Qt.ArrowCursor)

    def _after_native_event(self, widget, point):
        """Some item delegates unset the cursor; let native resize handling run first."""
        already_pending = widget in self._pending
        self._pending[widget] = point
        if already_pending:
            return
        weak_widget = ref(widget)

        def finish():
            target = weak_widget()
            if target is not None and isValid(target):
                position = self._pending.pop(target, None)
                self.update(target, position)

        QTimer.singleShot(0, self, finish)

    def prepare(self, widget):
        parent = widget.parentWidget()
        if (isinstance(parent, QAbstractItemView) and widget is parent.viewport()) or isinstance(widget, (QTabBar, QGroupBox)):
            widget.setMouseTracking(True)
        self.update(widget)

    def eventFilter(self, watched, event):
        if not isinstance(watched, QWidget):
            return False
        # A surviving Python wrapper does not keep its C++ widget alive. Never
        # forward an event to a destroyed receiver, including nested cursor events.
        if not isValid(watched):
            return True
        if self._setting:
            return False
        kind = event.type()
        if kind in (QEvent.Polish, QEvent.Show):
            self.prepare(watched)
        elif kind in (QEvent.EnabledChange, QEvent.Enter):
            self.update(watched)
        elif kind == QEvent.DynamicPropertyChange and bytes(event.propertyName()) == b"cursorClickable":
            self.update(watched)
        elif kind == QEvent.CursorChange:
            if not watched.isEnabled():
                # Preserve a new functional cursor requested while disabled;
                # our own Arrow assignments are guarded by _setting.
                self._disabled[watched] = (QCursor(watched.cursor())
                    if watched.testAttribute(Qt.WA_SetCursor) else None)
                self.update(watched)
            elif isinstance(watched, QLineEdit):
                self.update(watched)
        elif kind in (QEvent.MouseMove, QEvent.HoverMove):
            point = event.position().toPoint()
            self.update(watched, point)
            # setCursor() can dispatch events and destroy the receiver reentrantly.
            if not isValid(watched):
                return True
            parent = watched.parentWidget()
            if isinstance(parent, QAbstractItemView) and watched is parent.viewport():
                self._after_native_event(watched, point)
        elif kind == QEvent.Leave:
            self.update(watched, QPoint(-1, -1))
            if isValid(watched) and watched in self._pending:
                self._pending[watched] = QPoint(-1, -1)
        return not isValid(watched)


def install_cursor_policy(app):
    """Install once, also supporting already-created widgets in UI tests."""
    existing = getattr(app, "_cmdrhelper_cursor_policy", None)
    if existing is not None:
        return existing
    policy = CursorPolicy(app)
    app._cmdrhelper_cursor_policy = policy
    app.installEventFilter(policy)
    for widget in app.allWidgets():
        policy.prepare(widget)
    return policy
