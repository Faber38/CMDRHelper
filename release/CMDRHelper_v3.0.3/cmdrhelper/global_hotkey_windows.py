"""RegisterHotKey / WM_HOTKEY on the Qt GUI thread, without keyboard hooks."""
import ctypes
from ctypes import wintypes
from PySide6.QtCore import QAbstractNativeEventFilter, QCoreApplication, Qt
from cmdrhelper.global_hotkey import combination


class WindowsHotkey(QAbstractNativeEventFilter):
    def __init__(self, callback, api=None):
        super().__init__()
        self.callback = callback
        self.api = api if api is not None else ctypes.WinDLL('user32', use_last_error=True)
        if api is None:
            self.api.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
            self.api.RegisterHotKey.restype = wintypes.BOOL
            self.api.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
            self.api.UnregisterHotKey.restype = wintypes.BOOL
            self.api.VkKeyScanW.argtypes = [wintypes.WCHAR]
            self.api.VkKeyScanW.restype = ctypes.c_short
        self.tokens = {}
        self.next_id = 0x4300
        QCoreApplication.instance().installNativeEventFilter(self)

    def register(self, text):
        combo = combination(text)
        key, mods = combo.key(), combo.keyboardModifiers()
        native_mods = sum(value for flag, value in ((Qt.AltModifier, 1), (Qt.ControlModifier, 2),
                          (Qt.ShiftModifier, 4), (Qt.MetaModifier, 8)) if mods & flag)
        special = {Qt.Key_Space:0x20, Qt.Key_Tab:9, Qt.Key_Backspace:8, Qt.Key_Return:13,
                   Qt.Key_Enter:13, Qt.Key_Escape:27, Qt.Key_Insert:45, Qt.Key_Delete:46,
                   Qt.Key_Home:36, Qt.Key_End:35, Qt.Key_Left:37, Qt.Key_Up:38,
                   Qt.Key_Right:39, Qt.Key_Down:40, Qt.Key_PageUp:33, Qt.Key_PageDown:34,
                   Qt.Key_Pause:19, Qt.Key_Print:44, Qt.Key_CapsLock:20,
                   Qt.Key_NumLock:144, Qt.Key_ScrollLock:145}
        if Qt.Key_F1 <= key <= Qt.Key_F24:
            vk = 0x70 + int(key) - int(Qt.Key_F1)
        elif key in special:
            vk = special[key]
        elif 0x30 <= key <= 0x39 or 0x41 <= key <= 0x5a:
            vk = int(key)
        elif 0 < key < 0x10000:
            mapped = self.api.VkKeyScanW(chr(key))
            if mapped == -1:
                raise ValueError('Key unavailable in current keyboard layout')
            vk = mapped & 255
            shift = (mapped >> 8) & 7
            native_mods |= (4 if shift & 1 else 0) | (2 if shift & 2 else 0) | (1 if shift & 4 else 0)
        else:
            raise ValueError('Unsupported hotkey')
        if mods & Qt.KeypadModifier:
            if 0x30 <= vk <= 0x39:
                vk += 0x30
            elif key in {Qt.Key_Plus, Qt.Key_Minus, Qt.Key_Asterisk, Qt.Key_Slash,
                         Qt.Key_Period, Qt.Key_Comma, Qt.Key_Enter, Qt.Key_Return}:
                vk = {Qt.Key_Plus:0x6b, Qt.Key_Minus:0x6d, Qt.Key_Asterisk:0x6a,
                      Qt.Key_Slash:0x6f, Qt.Key_Period:0x6e, Qt.Key_Comma:0x6e,
                      Qt.Key_Enter:13, Qt.Key_Return:13}[key]
                # Keypad operators do not need the main keyboard's inferred Shift.
                native_mods = sum(value for flag, value in ((Qt.AltModifier, 1), (Qt.ControlModifier, 2),
                                  (Qt.ShiftModifier, 4), (Qt.MetaModifier, 8)) if mods & flag)
            else:
                raise ValueError('Unsupported keypad hotkey')
        token = self.next_id
        self.next_id += 1
        if not self.api.RegisterHotKey(None, token, native_mods | 0x4000, vk):
            raise RuntimeError('RegisterHotKey failed (shortcut reserved or in use)')
        self.tokens[token] = (native_mods, vk)
        return token

    def unregister(self, token):
        if token in self.tokens:
            if not self.api.UnregisterHotKey(None, token):
                raise RuntimeError('UnregisterHotKey failed')
            del self.tokens[token]

    def dispatch(self, message, token):
        if message == 0x0312 and token in self.tokens:
            self.callback()
            return True
        return False

    def nativeEventFilter(self, event_type, message):
        if bytes(event_type) in (b'windows_generic_MSG', b'windows_dispatcher_MSG'):
            msg = ctypes.cast(int(message), ctypes.POINTER(wintypes.MSG)).contents
            if self.dispatch(msg.message, msg.wParam):
                return True, 0
        return False, 0

    def close(self):
        for token in list(self.tokens):
            self.unregister(token)
        QCoreApplication.instance().removeNativeEventFilter(self)
