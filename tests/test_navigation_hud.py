import inspect
import os
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QObject, QRect, Qt, Signal
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication
from cmdrhelper.ui.navigation_hud import NavigationHud, TargetWindow, X11WindowTracker, hud_lines
from cmdrhelper.planet_geometry import solve


class Controller(QObject):
    changed = Signal(object)
    state = SimpleNamespace(solution=None)


class HudTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.tracker = Mock(reason="not_found", error="", last_target=None)
        self.tracker.input_is_empty.return_value = True
        self.tracker.current.return_value = TargetWindow(42, QRect(30, 40, 800, 600))
        self.controller = Controller()
        self.controller.state = SimpleNamespace(snapshot=object(), solution=SimpleNamespace(
            relative=2, bearing=17, distance_m=145600, undefined_reason=""))
        self.hud = NavigationHud(self.controller, self.tracker)
        self.addCleanup(self.hud.deleteLater)
        self.addCleanup(self.hud.close)

    def test_native_input_transparency_and_focus_flags(self):
        for flag in (Qt.FramelessWindowHint, Qt.WindowStaysOnTopHint,
                     Qt.WindowDoesNotAcceptFocus, Qt.WindowTransparentForInput):
            self.assertTrue(self.hud.windowFlags() & flag)
        for attr in (Qt.WA_TranslucentBackground, Qt.WA_ShowWithoutActivating,
                     Qt.WA_TransparentForMouseEvents, Qt.WA_X11DoNotAcceptFocus):
            self.assertTrue(self.hud.testAttribute(attr))
        self.assertEqual(self.hud.focusPolicy(), Qt.NoFocus)
        self.assertFalse(self.hud.autoFillBackground())

    def test_x11_mapping_bypasses_helper_workspace_without_taking_input(self):
        with patch("cmdrhelper.ui.navigation_hud.QGuiApplication.platformName", return_value="xcb"):
            hud = NavigationHud(self.controller, self.tracker)
        self.addCleanup(hud.deleteLater)
        self.addCleanup(hud.close)
        self.assertTrue(hud.windowFlags() & Qt.X11BypassWindowManagerHint)
        self.assertTrue(hud.windowFlags() & Qt.WindowDoesNotAcceptFocus)
        self.assertTrue(hud.windowFlags() & Qt.WindowTransparentForInput)

    def test_geometry_visibility_updates_and_toggles_never_request_focus(self):
        with patch.object(self.hud, 'activateWindow', side_effect=AssertionError), \
             patch.object(self.hud, 'raise_', side_effect=AssertionError), \
             patch.object(self.hud, 'setFocus', side_effect=AssertionError):
            self.hud.set_enabled(True)
            self.assertTrue(self.hud.isVisible())
            self.assertEqual(self.hud.geometry(), QRect(30, 40, 800, 600))
            self.tracker.current.return_value = TargetWindow(42, QRect(100, 200, 900, 700))
            self.hud.follow_target()
            self.controller.changed.emit(self.controller.state)
            self.assertEqual(self.hud.geometry(), QRect(100, 200, 900, 700))
            self.tracker.current.return_value = None
            self.hud.follow_target()
            self.assertFalse(self.hud.isVisible())
            self.tracker.current.return_value = TargetWindow(42, QRect(10, 20, 300, 400))
            self.hud.follow_target()
            self.assertTrue(self.hud.isVisible())
            self.hud.set_enabled(False)
            self.assertFalse(self.hud.isVisible())
            self.assertFalse(self.hud.timer.isActive())
            self.hud.set_enabled(True)
            self.assertTrue(self.hud.isVisible())

    def test_unsafe_native_input_region_never_maps_overlay(self):
        self.tracker.input_is_empty.return_value = False
        with patch.object(self.hud, 'show', side_effect=AssertionError):
            with self.assertRaises(RuntimeError):
                self.hud.set_enabled(True)
        self.assertFalse(self.hud.isVisible())
        self.assertFalse(self.hud.timer.isActive())

    def test_paint_has_transparent_background_and_only_sparse_hud(self):
        snapshot = SimpleNamespace(latitude=0., longitude=0., heading=90., radius_m=1_000_000., body_name="Test 1")
        target = SimpleNamespace(latitude=0., longitude=10., name="", binding=SimpleNamespace(body_name="Test 1"))
        self.controller.state = SimpleNamespace(target=target, snapshot=snapshot,
                                               solution=solve(0,0,90,0,10,1_000_000))
        self.hud.set_enabled(True)
        self.hud.resize(800, 600)
        image = QImage(800, 600, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent)
        self.hud.render(image)
        self.assertEqual(image.pixelColor(0, 0).alpha(), 0)
        self.assertEqual(image.pixelColor(400, 300).alpha(), 0)
        self.assertTrue(any(image.pixelColor(x,y).alpha() for x in range(200,600) for y in range(10,115)))
        source = inspect.getsource(NavigationHud)
        self.assertNotIn('drawText(', source)
        self.assertGreater(self.hud.paint_count, 0)
        self.assertEqual(self.hud.windowOpacity(), 1.0)
        for forbidden in ('activateWindow(', 'raise_(', 'setFocus('):
            self.assertNotIn(forbidden, source)

    def test_status_explains_switch_on_wait_show_and_switch_off(self):
        changes = []
        self.hud.status_changed.connect(lambda state, detail: changes.append(state))
        self.tracker.current.return_value = None
        self.tracker.reason = "foreground"
        self.hud.set_enabled(True)
        self.assertEqual(changes[-1], "foreground")
        self.tracker.current.return_value = TargetWindow(42, QRect(30, 40, 800, 600))
        self.hud.follow_target()
        self.assertEqual(changes[-1], "active")
        self.hud.set_enabled(False)
        self.assertEqual(changes[-1], "off")
        self.assertFalse(self.hud.isVisible())

    def test_qt_visible_but_native_unmapped_does_not_claim_displayed(self):
        self.tracker.window_is_viewable.return_value = False
        self.hud.set_enabled(True)
        self.assertTrue(self.hud.isVisible())
        self.assertEqual(self.hud.status, "native_hidden")
        self.tracker.window_is_viewable.return_value = True
        self.hud.follow_target()
        self.assertEqual(self.hud.status, "active")

    def test_offscreen_geometry_reports_reason_without_mapping(self):
        self.tracker.current.return_value = TargetWindow(42, QRect(99999, 99999, 800, 600))
        self.hud.set_enabled(True)
        self.assertEqual(self.hud.status, "outside")
        self.assertFalse(self.hud.isVisible())



    def test_text_uses_confirmed_values_directly_and_clears_when_invalid(self):
        from cmdrhelper.i18n import set_language
        set_language("de")
        self.hud.set_enabled(True)
        for relative,bearing,expected in ((-1,240,"1° LINKS"),(2,121,"2° RECHTS"),
                                          (.1,240,"GERADEAUS"),(-.1,240,"GERADEAUS")):
            self.controller.state=SimpleNamespace(snapshot=object(),
                solution=SimpleNamespace(relative=relative,bearing=bearing,distance_m=145600,undefined_reason=""))
            self.controller.changed.emit(self.controller.state)
            self.assertEqual(hud_lines(self.controller.state),(expected,f"ZIELKURS: {bearing:03d}°", "ENTFERNUNG: 145,6 km"))
        self.assertFalse(hasattr(self.hud,"render_timer"))
        self.assertFalse(hasattr(self.hud,"corridor"))
        self.controller.state.snapshot=None
        self.controller.changed.emit(self.controller.state)
        self.assertEqual(hud_lines(self.controller.state),())
        self.controller.state=SimpleNamespace(snapshot=object(),solution=None)
        self.assertEqual(hud_lines(self.controller.state),())
        self.controller.state.solution=SimpleNamespace(bearing=None,relative=None)
        self.assertEqual(hud_lines(self.controller.state),())

    def test_three_outlined_lines_are_top_centered_with_clear_background(self):
        from cmdrhelper.i18n import set_language
        set_language("de")
        self.controller.state=SimpleNamespace(snapshot=object(),
            solution=SimpleNamespace(relative=-1,bearing=240,distance_m=145600,undefined_reason=""))
        self.hud.set_enabled(True)
        self.hud.resize(800,600)
        image=QImage(800,600,QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent)
        self.hud.render(image)
        rows=[y for y in range(600) if any(image.pixelColor(x,y).alpha() for x in range(800))]
        groups=[]
        for y in rows:
            if not groups or y>groups[-1][-1]+1:
                groups.append([])
            groups[-1].append(y)
        self.assertEqual(len(groups),3)
        self.assertGreater(len(groups[0]),len(groups[1]))
        self.assertGreaterEqual(min(rows),10)
        self.assertLess(max(rows),160)
        for group in groups:
            xs=[x for x in range(800) if any(image.pixelColor(x,y).alpha() for y in group)]
            self.assertAlmostEqual((min(xs)+max(xs))/2,399.5,delta=1)
            # Each line needs a solid orange fill, not just an outline that
            # swallows the smaller glyphs against a dark cockpit background.
            bright=sum(image.pixelColor(x,y).alpha()>200
                       and image.pixelColor(x,y).name()=="#ff9100"
                       for y in group for x in xs)
            self.assertGreater(bright, 200)
        pixels=[image.pixelColor(x,y) for y in rows for x in range(200,600)]
        self.assertTrue(any(c.alpha()>200 and c.lightness()<10 for c in pixels))
        self.assertTrue(any(c.alpha()>200 and c.name()=="#ff9100" for c in pixels))



    def test_navigation_validity_transitions_preserve_enabled_preference(self):
        valid = self.controller.state
        self.controller.state = SimpleNamespace(snapshot=None, solution=None)
        self.hud.set_enabled(True)
        self.assertTrue(self.hud.enabled)
        self.assertFalse(self.hud.isVisible())
        for state, visible in ((valid, True), (SimpleNamespace(snapshot=None, solution=None), False),
                               (valid, True)):
            self.controller.state = state
            self.controller.changed.emit(state)
            self.assertEqual(self.hud.isVisible(), visible)
            self.assertTrue(self.hud.enabled)
        self.hud.set_enabled(False)
        self.controller.changed.emit(valid)
        self.hud.follow_target()
        self.assertFalse(self.hud.isVisible())


class SidebarHudTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from tempfile import TemporaryDirectory
        from PySide6.QtCore import QSettings
        from PySide6.QtWidgets import QMainWindow
        from cmdrhelper.ui.main_window import MainWindow
        self.folder = TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.settings_path = self.folder.name + "/settings.ini"
        self.main = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(self.main)
        self.main.state = SimpleNamespace(settings=QSettings(self.settings_path, QSettings.IniFormat))
        self.main._navigation_hud = None
        self.main._planet_navigation_window = None
        self.main._planet_navigation_controller = None
        self.addCleanup(self.main.deleteLater)

    def test_sidebar_order_and_real_checkbox_persistence(self):
        from PySide6.QtCore import QSettings
        from PySide6.QtWidgets import QCheckBox, QVBoxLayout
        from cmdrhelper.i18n import tr, set_language
        from cmdrhelper.ui.main_window import MainWindow
        set_language("de")
        source = inspect.getsource(MainWindow._build_ui)
        names = ["explorer_value_live_enabled_check", "explorer_bio_live_enabled_check",
                 "cargo_live_enabled_check", "navigation_hud_enabled_check"]
        positions = [source.index("live_layout.addWidget(self." + name + ")") for name in names]
        self.assertEqual(positions, sorted(positions))
        # Execute the actual sidebar switch construction with its real signal connection.
        start = source.index('        self.navigation_hud_enabled_check =')
        end = source.index('        side.addWidget(self.auto_show_frame)', start)
        import textwrap
        layout = QVBoxLayout()
        with patch.object(self.main, "_apply_navigation_hud_enabled") as apply:
            exec(textwrap.dedent(source[start:end]), dict(self=self.main, live_layout=layout,
                                                        QCheckBox=QCheckBox, tr=tr))
            check = self.main.navigation_hud_enabled_check
            self.addCleanup(check.deleteLater)
            self.assertEqual(check.text(), "Navigations-HUD")
            self.assertFalse(check.isChecked())
            for enabled in (True, False):
                check.setChecked(enabled)
                saved = QSettings(self.settings_path, QSettings.IniFormat)
                self.assertEqual(saved.value("navigation_hud/enabled", type=bool), enabled)
                self.assertEqual(self.main._navigation_hud_enabled(), enabled)
            self.assertEqual(apply.call_count, 2)

    def test_new_hud_texts_exist_in_all_twelve_languages(self):
        from cmdrhelper.i18n import _TRANSLATIONS
        from tools.check_i18n import placeholders
        self.assertEqual(len(_TRANSLATIONS), 12)
        for language, table in _TRANSLATIONS.items():
            for key, fields in (("settings.navigation_hud", set()),
                                ("planet_nav.target_course", {"value"}),
                                ("navigation_hud.distance", {"value"})):
                with self.subTest(language=language, key=key):
                    self.assertIn(key, table)
                    self.assertEqual(placeholders(table[key]), fields)

    def test_saved_preference_starts_only_controller_and_hud(self):
        controller = Mock()
        self.main._planet_navigation_controller = controller
        self.main.state.settings.setValue("navigation_hud/enabled", "true")
        with patch("cmdrhelper.ui.navigation_hud.NavigationHud") as cls:
            self.main._apply_navigation_hud_enabled()
            cls.assert_called_once_with(controller)
            controller.start.assert_called_once()
            self.assertIsNone(self.main._planet_navigation_window)
            cls.return_value.set_enabled.assert_called_with(True)
            self.main._planet_navigation_closed(0)
            self.assertEqual(controller.start.call_count, 2)
            self.main._set_navigation_hud_enabled(False)
            cls.return_value.set_enabled.assert_called_with(False)
            controller.stop_target.assert_not_called()
            controller.timer.stop.assert_not_called()

    def test_platform_failure_keeps_preference_and_navigator_available(self):
        with patch("cmdrhelper.ui.navigation_hud.NavigationHud", side_effect=RuntimeError("unsupported")):
            self.main._set_navigation_hud_enabled(True)
        self.assertTrue(self.main._navigation_hud_enabled())
        self.assertTrue(self.main._planet_navigation_controller.timer.isActive())
        self.main._show_planet_navigation()
        window = self.main._planet_navigation_window
        self.addCleanup(window.deleteLater)
        self.assertTrue(window.isVisible())
        window.close()
        self.assertTrue(self.main._planet_navigation_controller.timer.isActive())
        self.main._planet_navigation_controller.timer.stop()


class TrackerTests(unittest.TestCase):
    def tracker(self, rows=None, state="", info=None, active="0xe600001"):
        tracker = X11WindowTracker.__new__(X11WindowTracker)
        tracker.compositor_available = Mock(return_value=True)
        tracker._read = Mock(side_effect=[
            f'_NET_ACTIVE_WINDOW(WINDOW): window id # {active}',
            rows if rows is not None else '0xe600001 0 steam_app_359320.steam_app_359320 host Elite - Dangerous (CLIENT)',
            state,
            info if info is not None else 'Absolute upper-left X: 1920\nAbsolute upper-left Y: -20\nWidth: 1920\nHeight: 1080\nMap State: IsViewable'])
        return tracker

    def test_elite_client_geometry_including_negative_origin(self):
        self.assertEqual(self.tracker().current(), TargetWindow(0xe600001, QRect(1920, -20, 1920, 1080)))

    def test_hidden_launcher_other_window_or_missing_compositor_hides(self):
        for rows in ('0x42 0 steam_app_359320 host elite-launcher',
                     '0x42 0 editor host Elite - Dangerous'):
            tracker = self.tracker(rows=rows)
            self.assertIsNone(tracker.current())
            self.assertEqual(tracker.reason, "not_found")
        tracker = self.tracker(state='_NET_WM_STATE_HIDDEN')
        self.assertIsNone(tracker.current())
        self.assertEqual(tracker.reason, "hidden")
        tracker = self.tracker(info='Absolute upper-left X: 0\nAbsolute upper-left Y: 0\nWidth: 800\nHeight: 600\nMap State: IsUnMapped')
        self.assertIsNone(tracker.current())
        self.assertEqual(tracker.reason, "hidden")
        tracker = self.tracker()
        tracker.compositor_available.return_value = False
        self.assertIsNone(tracker.current())
        self.assertEqual(tracker.reason, "no_compositor")
        tracker._read.assert_not_called()

    def test_clicking_helper_still_discovers_elite_and_explains_wait(self):
        tracker = self.tracker(active='0x123')
        self.assertIsNone(tracker.current())
        self.assertEqual(tracker.reason, 'foreground')
        self.assertEqual(tracker.last_target.geometry, QRect(1920, -20, 1920, 1080))

    def test_disappearing_window_reports_error(self):
        tracker = self.tracker()
        tracker._read.side_effect = OSError('window gone')
        self.assertIsNone(tracker.current())
        self.assertEqual(tracker.reason, 'error')
        self.assertIn('window gone', tracker.error)

    def test_closed_native_connection_is_never_queried(self):
        tracker = X11WindowTracker.__new__(X11WindowTracker)
        tracker.display = None
        tracker.x11 = Mock()
        tracker.shape = Mock()
        self.assertFalse(tracker.compositor_available())
        self.assertFalse(tracker.input_is_empty(42))
        self.assertIsNone(tracker.current())
        self.assertFalse(tracker.x11.mock_calls)
        self.assertFalse(tracker.shape.mock_calls)
