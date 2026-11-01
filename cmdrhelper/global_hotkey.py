"""One opt-in global shortcut; native registrations, no keyboard hooks.

All methods run on Qt's GUI thread. Acquire the replacement first so a conflict
cannot destroy a working shortcut. Backends own and release their resources.
"""
import sys
from . import startup_runtime

from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtGui import QKeySequence, QGuiApplication

SETTING = 'quick_favorite/hotkey'


def combination(text):
    sequence = QKeySequence.fromString(text, QKeySequence.PortableText)
    if sequence.count() != 1 or not sequence[0].key():
        raise ValueError('Invalid single hotkey')
    return sequence[0]


def canonical(text):
    if not text:
        return ''
    return QKeySequence(combination(text)).toString(QKeySequence.PortableText)


def create_backend(callback):
    if sys.platform == 'win32' and QGuiApplication.platformName() == 'windows':
        from cmdrhelper.global_hotkey_windows import WindowsHotkey
        return WindowsHotkey(callback)
    if sys.platform.startswith('linux') and QGuiApplication.platformName() == 'xcb':
        from cmdrhelper.global_hotkey_x11 import X11Hotkey
        return X11Hotkey(callback)
    raise RuntimeError('Global hotkeys require Windows or Linux/X11')


class GlobalHotkey(QObject):
    activated = Signal()
    changed = Signal()
    failed = Signal(str)

    def __init__(self, settings, parent=None, backend_factory=create_backend):
        super().__init__(parent)
        self.settings = settings
        self.factory = backend_factory
        self.backend = None
        self.active = ''
        self.token = None
        self.error = ''
        self._last_failure_diagnostic = None
        self.validator = None
        self.validation_error = ''
        self.suspended = 0

    def _dispatch(self):
        if not self.suspended:
            self.activated.emit()

    def load(self):
        # Empty default must not even initialize a native backend.
        return self.set_hotkey(str(self.settings.value(SETTING, '') or ''), persist=False)

    def set_hotkey(self, text, *, persist=True):
        self.validation_error = ''
        try:
            text = canonical(text)
            if persist and text and self.validator is not None:
                try:
                    self.validator(text)
                except ValueError as exc:
                    self.validation_error = str(exc)
                    raise
            previous = self.settings.value(SETTING, '')
            if text != self.active:
                if text and self.backend is None:
                    self.backend = self.factory(self._dispatch)
                new = self.backend.register(text) if text else None
                try:
                    if persist:
                        self._persist(text)
                    if self.token is not None:
                        self.backend.unregister(self.token)
                except Exception:
                    if new is not None:
                        self.backend.unregister(new)
                    if persist:
                        self.settings.setValue(SETTING, previous)
                        self.settings.sync()
                    raise
                self.token, self.active = new, text
            elif persist:
                self._persist(text)
            self.error = ''
            self._last_failure_diagnostic = None
            self.changed.emit()
            return True
        except (OSError, RuntimeError, ValueError) as exc:
            key = (type(exc).__name__, getattr(exc, 'errno', None), getattr(exc, 'winerror', None))
            if key != self._last_failure_diagnostic:
                self._last_failure_diagnostic = key
                startup_runtime.diagnostic('hotkey', 'failure', exc,
                    reason='hotkey_registration_failed', status='failed', traceback=True)
            self.error = str(exc)
            self.failed.emit(self.error)
            return False

    def _persist(self, text):
        self.settings.setValue(SETTING, text)
        self.settings.sync()
        if isinstance(self.settings, QSettings) and self.settings.status() != QSettings.NoError:
            from .i18n import tr
            self.validation_error = tr('shortcuts.save_failed')
            raise RuntimeError(self.validation_error)

    def close(self):
        if self.backend is not None:
            self.backend.close()
            self.backend = None
        self.token, self.active = None, ''
