import json
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QSettings, Qt, QObject, Signal, QRect
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from cmdrhelper.global_hotkey import GlobalHotkey, SETTING
from cmdrhelper.global_hotkey_windows import WindowsHotkey
from cmdrhelper.global_hotkey_x11 import X11Hotkey, Event, ModifierMap
from cmdrhelper.quick_favorite import save_quick_favorite
from cmdrhelper.database import CMDRDatabase
from cmdrhelper.favorites import FavoriteStore
from cmdrhelper.planet_navigation import PlanetNavigationController
from cmdrhelper.ui.favorites_view import FavoritesView
from cmdrhelper.ui.navigation_hud import NavigationHud, TargetWindow
from cmdrhelper.ui.quick_favorite_settings import QuickFavoriteSettings


class QtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])


class HotkeyTests(QtTests):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name) / 'settings.ini')
        self.settings = QSettings(self.path, QSettings.IniFormat)
        self.backend = Mock()
        self.backend.register.side_effect = [1, 2, 3]
        self.factory = Mock(return_value=self.backend)
        self.hotkey = GlobalHotkey(self.settings, backend_factory=self.factory)
        self.addCleanup(self.hotkey.close)

    def test_default_creates_no_backend_and_registers_nothing(self):
        self.assertTrue(self.hotkey.load())
        self.factory.assert_not_called()
        self.assertEqual(self.hotkey.active, '')

    def test_persistence_change_remove_and_shutdown(self):
        self.assertTrue(self.hotkey.set_hotkey('Ctrl+F8'))
        self.assertEqual(QSettings(self.path, QSettings.IniFormat).value(SETTING), 'Ctrl+F8')
        self.assertTrue(self.hotkey.set_hotkey('Alt+F9'))
        self.assertEqual(self.backend.method_calls[:3],
                         [unittest.mock.call.register('Ctrl+F8'),
                          unittest.mock.call.register('Alt+F9'), unittest.mock.call.unregister(1)])
        self.assertTrue(self.hotkey.set_hotkey(''))
        self.backend.unregister.assert_called_with(2)
        self.assertEqual(QSettings(self.path, QSettings.IniFormat).value(SETTING), '')
        self.assertTrue(self.hotkey.set_hotkey('F10'))
        self.hotkey.close()
        self.backend.close.assert_called_once()
        self.hotkey.close()
        self.backend.close.assert_called_once()

    def test_saved_hotkey_loads_and_activation_is_not_local_focus_gated(self):
        self.settings.setValue(SETTING, 'Ctrl+F8')
        self.assertTrue(self.hotkey.load())
        fired = Mock()
        self.hotkey.activated.connect(fired)
        self.factory.call_args.args[0]()  # Native notification, no Helper focus needed.
        fired.assert_called_once_with()

    def test_registration_error_retains_active_binding_and_settings(self):
        self.hotkey.set_hotkey('Ctrl+F8')
        self.backend.register.side_effect = RuntimeError('conflict')
        failed = Mock()
        self.hotkey.failed.connect(failed)
        self.assertFalse(self.hotkey.set_hotkey('Alt+F9'))
        self.assertEqual(self.hotkey.active, 'Ctrl+F8')
        self.assertEqual(self.settings.value(SETTING), 'Ctrl+F8')
        self.backend.unregister.assert_not_called()
        failed.assert_called_once()
        self.assertFalse(self.hotkey.set_hotkey('Ctrl+F8, Ctrl+F9'))

    def test_failed_startup_is_unassigned_and_can_remove_persisted_binding(self):
        self.settings.setValue(SETTING, 'Ctrl+F8')
        self.backend.register.side_effect = RuntimeError('conflict')
        self.assertFalse(self.hotkey.load())
        widget = QuickFavoriteSettings(self.hotkey)
        self.addCleanup(widget.close)
        self.assertTrue(widget.error.text())
        self.assertEqual(self.hotkey.active, '')
        self.assertTrue(widget.remove.isEnabled())
        widget.clear()
        self.assertEqual(self.settings.value(SETTING), '')
        self.assertFalse(widget.error.text())

    def test_settings_dialog_records_changes_and_removes_single_shortcut(self):
        from PySide6.QtCore import QTimer
        from PySide6.QtGui import QKeySequence
        from PySide6.QtWidgets import QKeySequenceEdit, QDialogButtonBox, QLineEdit
        from cmdrhelper.i18n import tr
        widget = QuickFavoriteSettings(self.hotkey)
        # Destroy the parented dialogs while QApplication is still alive.
        from shiboken6 import delete
        self.addCleanup(delete, widget)
        for sequence in ('Ctrl+F8', 'Alt+F9'):
            def fill(sequence=sequence):
                dialog = self.app.activeModalWidget()
                edit = dialog.findChild(QKeySequenceEdit)
                self.assertEqual(edit.maximumSequenceLength(), 1)
                self.assertEqual(edit.findChild(QLineEdit).placeholderText(), tr('quick_favorite.set'))
                edit.setKeySequence(QKeySequence(sequence))
                dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.Save).click()
            QTimer.singleShot(0, fill)
            widget.choose()
            self.assertEqual(self.hotkey.active, sequence)
        widget.remove.click()
        self.assertEqual(self.hotkey.active, '')

    def test_application_quit_connection_cleans_up(self):
        # Use a dedicated QObject signal so this does not quit the suite's app.
        class Lifetime(QObject):
            aboutToQuit = Signal()
        lifetime = Lifetime()
        lifetime.aboutToQuit.connect(self.hotkey.close)
        self.hotkey.set_hotkey('Ctrl+F8')
        lifetime.aboutToQuit.emit()
        self.backend.close.assert_called_once()


class WindowsTests(QtTests):
    def setUp(self):
        self.api = Mock()
        self.callback = Mock()
        self.backend = WindowsHotkey(self.callback, self.api)
        self.addCleanup(self.backend.close)

    def test_native_registration_dispatch_repeat_flag_and_cleanup(self):
        token = self.backend.register('Ctrl+Shift+F8')
        self.api.RegisterHotKey.assert_called_with(None, token, 0x4006, 0x77)
        self.assertFalse(self.backend.dispatch(0x0312, token + 1))
        self.assertFalse(self.backend.dispatch(0x100, token))
        self.assertTrue(self.backend.dispatch(0x0312, token))
        self.callback.assert_called_once()
        self.backend.unregister(token)
        self.api.UnregisterHotKey.assert_called_once_with(None, token)
        self.assertFalse(self.backend.dispatch(0x0312, token))
        second = self.backend.register('Alt+F9')
        self.backend.close()
        self.api.UnregisterHotKey.assert_called_with(None, second)

    def test_conflict_and_unregister_failure_are_reported(self):
        self.api.RegisterHotKey.return_value = False
        with self.assertRaises(RuntimeError):
            self.backend.register('F8')
        self.assertFalse(self.backend.tokens)
        self.api.RegisterHotKey.return_value = True
        token = self.backend.register('F8')
        self.api.UnregisterHotKey.return_value = False
        with self.assertRaises(RuntimeError):
            self.backend.unregister(token)
        self.assertIn(token, self.backend.tokens)
        self.api.UnregisterHotKey.return_value = True

    def test_keypad_digit_and_operator_mapping(self):
        self.api.VkKeyScanW.return_value = 0x1bb  # Main keyboard '+' needs Shift.
        token = self.backend.register('Ctrl+Num++')
        self.api.RegisterHotKey.assert_called_with(None, token, 0x4002, 0x6b)
        token = self.backend.register('Alt+Num+1')
        self.api.RegisterHotKey.assert_called_with(None, token, 0x4001, 0x61)

    def test_actual_native_filter_message(self):
        import ctypes
        from ctypes import wintypes
        token = self.backend.register('F8')
        msg = wintypes.MSG()
        msg.message, msg.wParam = 0x0312, token
        self.assertEqual(self.backend.nativeEventFilter(b'windows_dispatcher_MSG', ctypes.addressof(msg)), (True, 0))
        self.callback.assert_called_once()


class X11Tests(QtTests):
    def setUp(self):
        self.backend = X11Hotkey.__new__(X11Hotkey)
        self.backend.x = Mock()
        self.backend.x.XSetErrorHandler.return_value = None
        self.backend.display, self.backend.root = 10, 20
        self.backend.tokens, self.backend.pressed = set(), set()
        self.backend.notifier = Mock()
        self.backend.callback = Mock()
        self.backend.detectable_repeat = True
        self.backend._key = Mock(side_effect=lambda text: (74 if text == 'F8' else 75, (0, 2, 16, 18)))
        self.addCleanup(self.backend.close)

    def test_grab_variants_change_ungrab_cleanup(self):
        token = self.backend.register('F8')
        self.assertEqual(self.backend.x.XGrabKey.call_count, 4)
        self.backend.x.XGrabKey.assert_called_with(10, 74, 18, 20, 0, 1, 1)
        second = self.backend.register('F9')
        self.backend.unregister(token)
        self.assertEqual(self.backend.x.XUngrabKey.call_count, 4)
        self.backend.close()
        self.assertEqual(self.backend.x.XUngrabKey.call_count, 8)
        self.backend.x.XCloseDisplay.assert_called_once_with(10)
        self.assertFalse(self.backend.tokens)

    def test_badaccess_releases_partial_grabs_and_preserves_old(self):
        import ctypes
        from cmdrhelper.global_hotkey_x11 import ERROR_HANDLER, ErrorEvent
        old = self.backend.register('F8')
        def set_handler(pointer):
            if pointer:
                error = ErrorEvent()
                error.error_code = 10
                ERROR_HANDLER(pointer.value)(10, ctypes.pointer(error))
            return None
        self.backend.x.XSetErrorHandler.side_effect = set_handler
        with self.assertRaises(RuntimeError):
            self.backend.register('F9')
        self.assertEqual(self.backend.tokens, {old})
        self.assertEqual(self.backend.x.XUngrabKey.call_count, 4)
        self.assertTrue(all(c.args[1] == 75 for c in self.backend.x.XUngrabKey.call_args_list))

    def test_key_mapping_includes_actual_numlock_and_capslock_masks(self):
        import ctypes
        x = self.backend.x
        x.XStringToKeysym.side_effect = lambda name: {b'F8':0xffc5, b'Num_Lock':0xff7f, b'Scroll_Lock':0xff14}[name]
        x.XKeysymToKeycode.side_effect = lambda display, symbol: {0xffc5:74,0xff7f:77,0xff14:78}[symbol]
        x.XkbKeycodeToKeysym.return_value = 0xffc5
        codes = (ctypes.c_ubyte * 8)(0,0,0,0,77,0,0,78)
        mapping = ModifierMap(1, codes)
        x.XGetModifierMapping.return_value = ctypes.pointer(mapping)
        code, masks = X11Hotkey._key(self.backend, 'Ctrl+F8')
        self.assertEqual(code, 74)
        self.assertEqual(set(masks), {4,6,20,22,132,134,148,150})
        x.XFreeModifiermap.assert_called_once()

    def test_repeat_and_removed_binding_events_do_not_save_again(self):
        import ctypes
        self.backend.register('F8')
        events = [(2, 74), (2, 74), (3, 74), (2, 74), (2, 75)]
        self.backend.x.XPending.side_effect = lambda _: len(events)
        def next_event(_, pointer):
            kind, code = events.pop(0)
            event = ctypes.cast(pointer, ctypes.POINTER(Event)).contents
            event.type, event.key.keycode, event.key.state = kind, code, 0
        self.backend.x.XNextEvent.side_effect = next_event
        self.backend.drain()
        self.assertEqual(self.backend.callback.call_count, 2)


class QuickSaveTests(QtTests):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.db = CMDRDatabase(root / 'db.sqlite')
        with self.db._connect() as con:
            con.executemany('INSERT INTO commanders(id,fid) VALUES (?,?)', [(1,'F1'),(2,'F2')])
        self.store = FavoriteStore(self.db)
        self.state = SimpleNamespace(database=self.db, commander_id=1, commander_fid='F1', system='Sol', system_address=0,
                                     system_bodies=[dict(name='Sol 1', body_id=0)], journal_folder=root)
        self.controller = PlanetNavigationController(self.state)
        self.status_path = root / 'Status.json'
        self.status = dict(event='Status', timestamp=datetime.now(timezone.utc).isoformat(),
                           Latitude=0., Longitude=0., Heading=0., PlanetRadius=1e6,
                           BodyName='Sol 1', Flags=1 << 21)
        self.write()
        self.notify, self.refresh = Mock(), Mock()

    def write(self):
        self.status_path.write_text(json.dumps(self.status))

    def save(self):
        return save_quick_favorite(self.controller, self.store, self.notify, self.refresh)

    def test_zero_coordinates_ids_exactly_one_favorite_and_feedback(self):
        result = self.save()
        self.assertEqual(len(self.store.list(1)), 1)
        self.assertEqual((result['latitude'], result['longitude'], result['body_id'], result['system_address']), (0.,0.,0,0))
        self.assertEqual(result['type'], 'surface_location')
        self.assertEqual((result['category'], result['note'], result['image_path']), ('other','',''))
        self.assertTrue(result['created_at'])
        self.assertEqual(result['commander_id'], 1)
        self.assertTrue(self.notify.call_args.args[0][0].startswith('★'))
        self.refresh.assert_called_once()

    def test_ship_srv_and_on_foot_use_the_same_snapshot_path(self):
        for flags, flags2 in ((1 << 21, 0), ((1 << 21) | (1 << 26), 0), (1 << 21, 1)):
            self.status.update(Flags=flags, Flags2=flags2)
            self.write()
            self.assertIsNotNone(self.save())
        self.assertEqual(len(self.store.list(1)), 3)

    def test_press_rereads_status_then_freezes_before_save(self):
        self.controller.poll()
        self.status.update(Latitude=12., Longitude=34.)
        self.write()
        original = self.store.save
        def delayed(commander, record):
            self.status.update(Latitude=56., Longitude=78.)
            self.write()
            self.controller.poll()
            return original(commander, record)
        with patch.object(self.store, 'save', side_effect=delayed):
            result = self.save()
        self.assertEqual((result['latitude'], result['longitude']), (12.,34.))

    def test_invalid_current_status_never_reuses_old_coordinates(self):
        for invalid in ('missing', 'partial', 'no_coordinates', 'nan'):
            with self.subTest(invalid=invalid):
                self.status['Flags'] = 1 << 21
                self.status['Latitude'] = 0.
                self.write()
                self.controller.poll()
                if invalid == 'missing':
                    self.status_path.unlink()
                elif invalid == 'partial':
                    self.status_path.write_text('{')
                else:
                    self.status['Flags' if invalid == 'no_coordinates' else 'Latitude'] = 0 if invalid == 'no_coordinates' else float('nan')
                    self.write()
                self.assertIsNone(self.save())
                self.assertEqual(self.store.list(1), [])
                self.assertTrue(self.notify.call_args.args[0][0].startswith('⚠'))
        self.refresh.assert_not_called()

    def test_commander_isolation_shutdown_and_unique_marker_names(self):
        first, second = self.save(), self.save()
        self.assertNotEqual(first['name'], second['name'])
        self.state.commander_id, self.state.commander_fid = 2, 'F2'
        result = self.save()
        self.assertEqual(result['commander_id'], 2)
        self.assertEqual(len(self.store.list(1)), 2)
        self.assertEqual(len(self.store.list(2)), 1)
        self.controller.tail.context.fid = 'F1'
        self.assertIsNone(self.save())
        self.controller.tail.context.fid = 'F2'
        self.controller.tail.context.running = False
        self.assertIsNone(self.save())

    def test_no_commander_and_storage_failure(self):
        self.state.commander_id = None
        self.assertIsNone(self.save())
        self.state.commander_id = 1
        with patch.object(self.store, 'save', side_effect=OSError('disk full')), \
             self.assertLogs('cmdrhelper.quick_favorite', level='ERROR'):
            self.assertIsNone(self.save())
        self.assertFalse(self.store.list(1))
        self.assertTrue(self.notify.call_args.args[0][0].startswith('⚠'))

    def test_open_favorites_refresh_without_focus_or_dialog(self):
        self.state.settings = QSettings(str(Path(self.temp.name) / 'settings.ini'), QSettings.IniFormat)
        view = FavoritesView(self.state, Mock(), Mock())
        self.addCleanup(view.close)
        view.show()
        self.refresh = view.refresh
        with patch.object(view, 'activateWindow', side_effect=AssertionError), \
             patch.object(view, 'setFocus', side_effect=AssertionError), \
             patch('cmdrhelper.ui.favorites_view.FavoriteDialog', side_effect=AssertionError):
            result = self.save()
            self.assertEqual(view.list.count(), 1)
            self.assertEqual(view.list.item(0).data(Qt.UserRole), result['id'])


class TemporaryHudTests(QtTests):
    def setUp(self):
        class Controller(QObject):
            changed = Signal(object)
        self.controller = Controller()
        self.controller.state = SimpleNamespace(snapshot=object(), solution=SimpleNamespace(
            relative=2, bearing=17, distance_m=100, undefined_reason=''))
        tracker = Mock(reason='active', error='', last_target=None)
        tracker.input_is_empty.return_value = True
        tracker.current.return_value = TargetWindow(42, QRect(0, 0, 800, 600))
        self.hud = NavigationHud(self.controller, tracker)
        self.addCleanup(self.hud.close)

    def test_disabled_hud_message_visible_then_completely_hidden(self):
        self.controller.state = SimpleNamespace(snapshot=None, solution=None)
        self.hud.show_message(('★ saved', 'Sol 1'), 30)
        self.assertFalse(self.hud.enabled)
        self.assertTrue(self.hud.isVisible())
        QTest.qWait(60)
        self.assertFalse(self.hud.enabled)
        self.assertFalse(self.hud.isVisible())
        self.assertFalse(self.hud.timer.isActive())

    def test_enabled_hud_returns_to_navigation_without_switch_change(self):
        self.hud.set_enabled(True)
        self.hud.show_message(('★ saved',), 30)
        self.assertTrue(self.hud.enabled)
        self.assertTrue(self.hud.isVisible())
        QTest.qWait(60)
        self.assertEqual(self.hud.message_lines, ())
        self.assertTrue(self.hud.enabled)
        self.assertTrue(self.hud.isVisible())
        self.assertTrue(self.hud.timer.isActive())

    def test_retrigger_extends_message_and_toggle_does_not_cancel_it(self):
        self.hud.show_message(('one',), 30)
        self.hud.show_message(('two',), 2000)
        self.hud.set_enabled(True)
        self.hud.set_enabled(False)
        QTest.qWait(60)
        self.assertEqual(self.hud.message_lines, ('two',))
        self.assertTrue(self.hud.isVisible())
        self.hud.clear_message()
        self.assertFalse(self.hud.isVisible())

    def test_focus_and_input_remain_untouched_for_error_message(self):
        with patch.object(self.hud, 'activateWindow', side_effect=AssertionError), \
             patch.object(self.hud, 'raise_', side_effect=AssertionError), \
             patch.object(self.hud, 'setFocus', side_effect=AssertionError):
            self.hud.show_message(('⚠ no coordinates',), 30)
            self.assertTrue(self.hud.windowFlags() & Qt.WindowTransparentForInput)
            QTest.qWait(60)
            self.assertFalse(self.hud.isVisible())

    def test_main_window_path_does_not_write_hud_preference(self):
        from cmdrhelper.ui.main_window import MainWindow
        host = SimpleNamespace(_ensure_navigation_hud=lambda:self.hud, state=SimpleNamespace(settings=Mock()))
        MainWindow._quick_favorite_message(host, ('saved',))
        host.state.settings.setValue.assert_not_called()
        self.assertFalse(self.hud.enabled)


if __name__ == '__main__':
    unittest.main()
