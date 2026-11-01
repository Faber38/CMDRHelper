"""Application-local bindings and shared validation for the existing global hotkey."""
from contextlib import contextmanager

from PySide6.QtCore import QObject, Signal, Qt, QSettings
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (QApplication, QLineEdit, QTextEdit, QPlainTextEdit,
                             QAbstractSpinBox, QComboBox, QKeySequenceEdit, QDialog)

from .global_hotkey import canonical, SETTING
from .i18n import tr

PREFIX = 'shortcuts/v1/'
ACTIONS = {
    'open_explorer': 'nav.explorer',
    'open_trade': 'nav.trade',
    'open_materials': 'materials.title',
    'open_powerplay': 'nav.pp2',
    'open_navigator': 'planet_nav.title',
    'quit': 'nav.exit',
}


def validate_combination(text):
    """Conservative cross-platform subset; never steal editing/system keys."""
    try:
        value = canonical(text)
    except (ValueError, TypeError):
        raise ValueError(tr('shortcuts.reserved')) from None
    if text and not value:
        raise ValueError(tr('shortcuts.reserved'))
    if not value:
        return value
    combo = QKeySequence(value)[0]
    key, mods = combo.key(), combo.keyboardModifiers()
    # Letters/digits require Control; permitted function keys may stand alone.
    # Alt/Meta and Ctrl+Alt (AltGr) are intentionally outside this subset.
    allowed_mods = Qt.ControlModifier | Qt.ShiftModifier
    if mods & ~allowed_mods:
        raise ValueError(tr('shortcuts.reserved'))
    function = Qt.Key_F2 <= key <= Qt.Key_F12
    alphanumeric = Qt.Key_A <= key <= Qt.Key_Z or Qt.Key_0 <= key <= Qt.Key_9
    if not (function or alphanumeric and mods & Qt.ControlModifier):
        raise ValueError(tr('shortcuts.reserved'))
    # Protect the union of common Windows/Linux editing and application keys,
    # including modified variants (e.g. redo, paste without formatting).
    if mods & Qt.ControlModifier and key in (
            Qt.Key_A, Qt.Key_B, Qt.Key_C, Qt.Key_F, Qt.Key_G, Qt.Key_H,
            Qt.Key_I, Qt.Key_K, Qt.Key_N, Qt.Key_O, Qt.Key_P, Qt.Key_S,
            Qt.Key_T, Qt.Key_U, Qt.Key_V, Qt.Key_W, Qt.Key_X, Qt.Key_Y, Qt.Key_Z):
        raise ValueError(tr('shortcuts.reserved'))
    if key in (Qt.Key_F2, Qt.Key_F3, Qt.Key_F4, Qt.Key_F5, Qt.Key_F6, Qt.Key_F10):
        raise ValueError(tr('shortcuts.reserved'))
    # Include platform-specific editing bindings Qt knows about as well.
    for standard in (QKeySequence.Cut, QKeySequence.Copy, QKeySequence.Paste,
                     QKeySequence.Undo, QKeySequence.Redo, QKeySequence.SelectAll,
                     QKeySequence.Find, QKeySequence.Close, QKeySequence.Save,
                     QKeySequence.NextChild, QKeySequence.PreviousChild):
        if QKeySequence(value) in QKeySequence.keyBindings(standard):
            raise ValueError(tr('shortcuts.reserved'))
    return value


class ShortcutManager(QObject):
    changed = Signal()

    def __init__(self, window, settings, hotkey, callbacks):
        super().__init__(window)
        self.window, self.settings, self.hotkey = window, settings, hotkey
        self.callbacks = callbacks
        self.bindings = {key: '' for key in ACTIONS}
        self.errors = {}
        self.error = ''
        self.capture_depth = 0
        self.shortcuts = {}
        for key in ACTIONS:
            shortcut = QShortcut(window)
            shortcut.setContext(Qt.WindowShortcut)
            shortcut.setAutoRepeat(False)
            shortcut.activated.connect(lambda action=key: self.activate(action))
            self.shortcuts[key] = shortcut
        hotkey.shortcut_manager = self
        hotkey.validator = self.validate_global
        hotkey.changed.connect(self.changed.emit)
        app = QApplication.instance()
        app.focusChanged.connect(self._update_enabled)
        app.focusWindowChanged.connect(self._update_enabled)
        self._update_enabled()

    @contextmanager
    def recording(self):
        self.capture_depth += 1
        self.hotkey.suspended += 1
        self._update_enabled()
        try:
            yield
        finally:
            self.hotkey.suspended -= 1
            self.capture_depth -= 1
            self._update_enabled()

    def _global_values(self):
        values = set()
        for raw in (self.hotkey.active, self.settings.value(SETTING, '')):
            try:
                if raw:
                    values.add(canonical(str(raw)))
            except ValueError:
                pass
        return values

    def validate_global(self, text):
        value = validate_combination(text)
        if value and value in self._local_values():
            raise ValueError(tr('shortcuts.conflict'))

    def _local_values(self, exclude=None):
        # Also reserve valid saved values rejected at startup for a conflict.
        # Otherwise assigning another action could appear successful but leave
        # all duplicate bindings inactive on the following load.
        values = set()
        for action, active in self.bindings.items():
            if action == exclude:
                continue
            if active:
                values.add(active)
            try:
                saved = validate_combination(str(self.settings.value(PREFIX + action, '') or ''))
                if saved:
                    values.add(saved)
            except ValueError:
                pass
        return values

    def load(self):
        """Invalid saved bindings stay on disk for removal, never become active."""
        self.errors.clear()
        candidates = {}
        for action in ACTIONS:
            raw = self.settings.value(PREFIX + action, '')
            try:
                value = validate_combination(str(raw or ''))
                candidates[action] = value
            except ValueError as exc:
                self.errors[action] = str(exc)
        for action, value in candidates.items():
            if value and (value in self._global_values() or
                          list(candidates.values()).count(value) > 1):
                self.errors[action] = tr('shortcuts.conflict')
        for action in ACTIONS:
            self.bindings[action] = candidates.get(action, '') if action not in self.errors else ''
            self.shortcuts[action].setKey(QKeySequence(self.bindings[action]))
        self._update_enabled()
        self.changed.emit()

    def set_binding(self, action, text):
        if action not in ACTIONS:
            return False
        try:
            value = validate_combination(text)
            if value and (value in self._global_values() or value in self._local_values(exclude=action)):
                raise ValueError(tr('shortcuts.conflict'))
        except ValueError as exc:
            self.error = str(exc)
            return False
        return self._save({action: value})

    def _save(self, values):
        previous = {a: self.settings.value(PREFIX + a) for a in values}
        for action, value in values.items():
            self.settings.setValue(PREFIX + action, value)
        self.settings.sync()
        if self.settings.status() != QSettings.NoError:
            for action, value in previous.items():
                if value is None:
                    self.settings.remove(PREFIX + action)
                else:
                    self.settings.setValue(PREFIX + action, value)
            self.settings.sync()
            self.error = tr('shortcuts.save_failed')
            return False
        self.error = ''
        self.load()
        return True

    def reset(self):
        return self._save({action: '' for action in ACTIONS})

    def _can_activate(self):
        if self.capture_depth:
            return False
        app = QApplication.instance()
        if (app.activeWindow() is not self.window or app.activeModalWidget() is not None
                or app.activePopupWidget() is not None):
            return False
        focus = app.focusWidget()
        while focus is not None:
            if isinstance(focus, (QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox,
                                  QKeySequenceEdit, QDialog)):
                return False
            if isinstance(focus, QComboBox) and focus.isEditable():
                return False
            focus = focus.parentWidget()
        return True

    def _update_enabled(self, *_args):
        # Disable before shortcut matching so an editor still receives its
        # original keys, rather than merely discarding an activated shortcut.
        allowed = self._can_activate()
        for action, shortcut in self.shortcuts.items():
            shortcut.setEnabled(allowed and bool(self.bindings[action]))

    def activate(self, action):
        if not self.bindings.get(action) or not self._can_activate():
            return
        callback = self.callbacks.get(action)
        if callback is not None:
            callback()
