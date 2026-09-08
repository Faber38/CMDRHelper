"""Passive X11 key grabs on a dedicated connection integrated into Qt's loop."""
import ctypes as C
from ctypes.util import find_library
from itertools import combinations
from PySide6.QtCore import QSocketNotifier, Qt
from cmdrhelper.global_hotkey import combination


class KeyEvent(C.Structure):
    _fields_ = [('type', C.c_int), ('serial', C.c_ulong), ('send_event', C.c_int),
                ('display', C.c_void_p), ('window', C.c_ulong), ('root', C.c_ulong),
                ('subwindow', C.c_ulong), ('time', C.c_ulong), ('x', C.c_int),
                ('y', C.c_int), ('x_root', C.c_int), ('y_root', C.c_int),
                ('state', C.c_uint), ('keycode', C.c_uint), ('same_screen', C.c_int)]


class Event(C.Union):
    _fields_ = [('type', C.c_int), ('key', KeyEvent), ('pad', C.c_long * 24)]


class ErrorEvent(C.Structure):
    _fields_ = [('type', C.c_int), ('display', C.c_void_p), ('resourceid', C.c_ulong),
                ('serial', C.c_ulong), ('error_code', C.c_ubyte),
                ('request_code', C.c_ubyte), ('minor_code', C.c_ubyte)]


class ModifierMap(C.Structure):
    _fields_ = [('max_keypermod', C.c_int), ('modifiermap', C.POINTER(C.c_ubyte))]


ERROR_HANDLER = C.CFUNCTYPE(C.c_int, C.c_void_p, C.POINTER(ErrorEvent))


class X11Hotkey:
    def __init__(self, callback):
        self.callback = callback
        library = find_library('X11')
        if not library:
            raise RuntimeError('libX11 unavailable')
        self.x = C.CDLL(library)
        signatures = {
            'XOpenDisplay': ([C.c_char_p], C.c_void_p),
            'XDefaultRootWindow': ([C.c_void_p], C.c_ulong),
            'XConnectionNumber': ([C.c_void_p], C.c_int),
            'XCloseDisplay': ([C.c_void_p], C.c_int),
            'XStringToKeysym': ([C.c_char_p], C.c_ulong),
            'XKeysymToKeycode': ([C.c_void_p, C.c_ulong], C.c_ubyte),
            'XkbKeycodeToKeysym': ([C.c_void_p, C.c_ubyte, C.c_int, C.c_int], C.c_ulong),
            'XGetModifierMapping': ([C.c_void_p], C.POINTER(ModifierMap)),
            'XFreeModifiermap': ([C.POINTER(ModifierMap)], C.c_int),
            'XGrabKey': ([C.c_void_p, C.c_int, C.c_uint, C.c_ulong, C.c_int, C.c_int, C.c_int], C.c_int),
            'XUngrabKey': ([C.c_void_p, C.c_int, C.c_uint, C.c_ulong], C.c_int),
            'XSync': ([C.c_void_p, C.c_int], C.c_int),
            'XSetErrorHandler': ([C.c_void_p], C.c_void_p),
            'XPending': ([C.c_void_p], C.c_int),
            'XNextEvent': ([C.c_void_p, C.POINTER(Event)], C.c_int),
            'XPeekEvent': ([C.c_void_p, C.POINTER(Event)], C.c_int),
            'XkbSetDetectableAutoRepeat': ([C.c_void_p, C.c_int, C.POINTER(C.c_int)], C.c_int),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self.x, name)
            function.argtypes, function.restype = args, result
        self.display = self.x.XOpenDisplay(None)
        if not self.display:
            raise RuntimeError('Cannot open X11 display')
        self.tokens = set()
        self.pressed = set()
        try:
            self.root = self.x.XDefaultRootWindow(self.display)
            supported = C.c_int()
            self.x.XkbSetDetectableAutoRepeat(self.display, 1, C.byref(supported))
            self.detectable_repeat = bool(supported.value)
            self.notifier = QSocketNotifier(self.x.XConnectionNumber(self.display), QSocketNotifier.Read)
            self.notifier.activated.connect(self.drain)
        except Exception:
            self.x.XCloseDisplay(self.display)
            self.display = None
            raise

    def _key(self, text):
        combo = combination(text)
        key, mods = combo.key(), combo.keyboardModifiers()
        names = {Qt.Key_Space:'space', Qt.Key_Tab:'Tab', Qt.Key_Backspace:'BackSpace',
                 Qt.Key_Return:'Return', Qt.Key_Enter:'KP_Enter', Qt.Key_Escape:'Escape',
                 Qt.Key_Insert:'Insert', Qt.Key_Delete:'Delete', Qt.Key_Home:'Home',
                 Qt.Key_End:'End', Qt.Key_Left:'Left', Qt.Key_Up:'Up', Qt.Key_Right:'Right',
                 Qt.Key_Down:'Down', Qt.Key_PageUp:'Prior', Qt.Key_PageDown:'Next',
                 Qt.Key_Pause:'Pause', Qt.Key_Print:'Print', Qt.Key_CapsLock:'Caps_Lock',
                 Qt.Key_NumLock:'Num_Lock', Qt.Key_ScrollLock:'Scroll_Lock'}
        if Qt.Key_F1 <= key <= Qt.Key_F35:
            symbol = self.x.XStringToKeysym(f'F{int(key)-int(Qt.Key_F1)+1}'.encode())
        elif key in names:
            symbol = self.x.XStringToKeysym(names[key].encode())
        elif 0 < key < 0x1000000:
            char = chr(key).lower()
            symbol = ord(char) if ord(char) < 256 else 0x01000000 | ord(char)
        else:
            raise ValueError('Unsupported hotkey')
        if mods & Qt.KeypadModifier:
            if Qt.Key_0 <= key <= Qt.Key_9:
                symbol = self.x.XStringToKeysym(f'KP_{chr(key)}'.encode())
            elif key in {Qt.Key_Plus, Qt.Key_Minus, Qt.Key_Asterisk, Qt.Key_Slash,
                         Qt.Key_Period, Qt.Key_Comma, Qt.Key_Enter, Qt.Key_Return}:
                name = {Qt.Key_Plus:'KP_Add', Qt.Key_Minus:'KP_Subtract', Qt.Key_Asterisk:'KP_Multiply',
                        Qt.Key_Slash:'KP_Divide', Qt.Key_Period:'KP_Decimal', Qt.Key_Comma:'KP_Separator',
                        Qt.Key_Enter:'KP_Enter', Qt.Key_Return:'KP_Enter'}[key]
                symbol = self.x.XStringToKeysym(name.encode())
            else:
                raise ValueError('Unsupported keypad hotkey')
        code = self.x.XKeysymToKeycode(self.display, symbol)
        if not code:
            raise ValueError('Key unavailable in current keyboard layout')
        native = sum(value for flag, value in ((Qt.ShiftModifier, 1), (Qt.ControlModifier, 4),
                     (Qt.AltModifier, 8), (Qt.MetaModifier, 64)) if mods & flag)
        # Resolve shifted punctuation; reject other groups instead of registering
        # a different physical combination silently.
        if not mods & Qt.KeypadModifier:
            levels = [self.x.XkbKeycodeToKeysym(self.display, code, 0, level) for level in (0, 1)]
            if symbol not in levels:
                raise ValueError('Key unavailable in primary keyboard layout')
            if symbol != levels[0]:
                native |= 1
        mapping = self.x.XGetModifierMapping(self.display)
        if not mapping:
            raise RuntimeError('Cannot read keyboard modifiers')
        locks = {2}  # Caps Lock, plus the actual Num/Scroll Lock modifier masks.
        try:
            lock_codes = {self.x.XKeysymToKeycode(self.display, self.x.XStringToKeysym(name))
                          for name in (b'Num_Lock', b'Scroll_Lock')}
            lock_codes.discard(0)
            for index in range(8):
                if any(mapping.contents.modifiermap[index * mapping.contents.max_keypermod + n] in lock_codes
                       for n in range(mapping.contents.max_keypermod)):
                    locks.add(1 << index)
        finally:
            self.x.XFreeModifiermap(mapping)
        variants = {native | sum(subset) for n in range(len(locks)+1) for subset in combinations(locks, n)}
        return code, tuple(sorted(variants))

    def register(self, text):
        token = self._key(text)
        if any(token[0] == code and set(token[1]).intersection(variants)
               for code, variants in self.tokens):
            raise ValueError('Equivalent hotkey is already registered')
        code, variants = token
        errors = []
        self.x.XSync(self.display, 0)
        previous = None

        @ERROR_HANDLER
        def handler(display, error):
            if display == self.display:
                errors.append(error.contents.error_code)
            elif previous:
                return ERROR_HANDLER(previous)(display, error)
            return 0

        previous = self.x.XSetErrorHandler(C.cast(handler, C.c_void_p))
        try:
            for mods in variants:
                self.x.XGrabKey(self.display, code, mods, self.root, 0, 1, 1)
            self.x.XSync(self.display, 0)
            if errors:
                for mods in variants:
                    self.x.XUngrabKey(self.display, code, mods, self.root)
                self.x.XSync(self.display, 0)
                raise RuntimeError('XGrabKey failed (shortcut reserved or in use)')
        finally:
            self.x.XSetErrorHandler(previous)
        self.tokens.add(token)
        return token

    def unregister(self, token):
        if token in self.tokens:
            code, variants = token
            for mods in variants:
                self.x.XUngrabKey(self.display, code, mods, self.root)
            self.x.XSync(self.display, 0)
            self.tokens.remove(token)
            self.pressed.discard(code)

    def drain(self, *_):
        while self.display and self.x.XPending(self.display):
            event = Event()
            self.x.XNextEvent(self.display, C.byref(event))
            key = event.key
            if event.type == 3:
                if not self.detectable_repeat and self.x.XPending(self.display):
                    following = Event()
                    self.x.XPeekEvent(self.display, C.byref(following))
                    if (following.type == 2 and following.key.keycode == key.keycode
                            and following.key.time == key.time):
                        continue
                self.pressed.discard(key.keycode)
            elif event.type == 2 and key.keycode not in self.pressed:
                self.pressed.add(key.keycode)
                if any(key.keycode == code and key.state & 255 in variants for code, variants in self.tokens):
                    self.callback()

    def close(self):
        if self.display:
            self.notifier.setEnabled(False)
            for token in list(self.tokens):
                self.unregister(token)
            self.x.XCloseDisplay(self.display)
            self.display = None
            self.notifier.deleteLater()
