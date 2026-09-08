"""One opt-in global shortcut; native registrations, no keyboard hooks.

All methods run on Qt's GUI thread. Acquire the replacement first so a conflict
cannot destroy a working shortcut. Backends own and release their resources.
"""
import sys

from PySide6.QtCore import QObject, Signal
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

    def load(self):
        # Empty default must not even initialize a native backend.
        return self.set_hotkey(str(self.settings.value(SETTING, '') or ''), persist=False)

    def set_hotkey(self, text, *, persist=True):
        try:
            text = canonical(text)
            if text != self.active:
                if text and self.backend is None:
                    self.backend = self.factory(self.activated.emit)
                new = self.backend.register(text) if text else None
                if self.token is not None:
                    try:
                        self.backend.unregister(self.token)
                    except Exception:
                        if new is not None:
                            self.backend.unregister(new)
                        raise
                self.token, self.active = new, text
            if persist:
                self.settings.setValue(SETTING, text)
                self.settings.sync()
            self.error = ''
            self.changed.emit()
            return True
        except (OSError, RuntimeError, ValueError) as exc:
            self.error = str(exc)
            self.failed.emit(self.error)
            return False

    def close(self):
        if self.backend is not None:
            self.backend.close()
            self.backend = None
        self.token, self.active = None, ''
