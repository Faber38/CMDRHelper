import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QObject, QRect, QSettings, Qt, Signal
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMainWindow

from cmdrhelper.cargo import cargo_snapshot
from cmdrhelper.i18n import set_language, _TRANSLATIONS
from cmdrhelper.route_planner.models import ShipLoadoutData
from cmdrhelper.ui.cargo_hud import CargoHudData, cargo_fill_fraction, cargo_hud_data, cargo_hud_enabled
from cmdrhelper.ui.main_window import CargoLiveWindow, MainWindow
from cmdrhelper.ui.navigation_hud import NavigationHud, TargetWindow


class Controller(QObject):
    changed = Signal(object)

    def __init__(self):
        super().__init__()
        self.state = SimpleNamespace(snapshot=None, solution=None)


class CargoHudTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        set_language("de")
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        self.settings_path = str(self.folder / "settings.ini")
        self.settings = QSettings(self.settings_path, QSettings.IniFormat)
        self.state = SimpleNamespace(
            settings=self.settings, commander_fid="F-A", journal_folder=self.folder,
            ship="Cobra", ship_loadout=ShipLoadoutData(
                ship_id=51, ship_name="ERFT-BÜFFEL", cargo_capacity=256),
            active_srv_type="", cargo_snapshot=None,
        )
        self.controller = Controller()
        self.tracker = Mock(reason="active", error="", last_target=None)
        self.tracker.input_is_empty.return_value = True
        self.tracker.current.return_value = TargetWindow(42, QRect(10, 20, 800, 600))
        self.hud = NavigationHud(self.controller, self.tracker)
        self.hud.cargo_provider = lambda: cargo_hud_data(self.state)
        self.addCleanup(self.hud.deleteLater)
        self.addCleanup(self.hud.close)

    def status(self, vessel="Ship", **extra):
        status = dict(event="Status", timestamp="2026-09-04T16:01:00Z",
                      Flags=1 << (24 if vessel == "Ship" else 26), Flags2=0)
        status.update(extra)
        (self.folder / "Status.json").write_text(json.dumps(status))

    def cargo(self, vessel="Ship", used=128, vehicle="", capacity=None):
        self.state.active_srv_type = vehicle if vessel == "SRV" else ""
        self.state.cargo_snapshot = cargo_snapshot({
            "event": "Cargo", "timestamp": "2026-09-04T16:00:00Z",
            "Vessel": vessel, "Count": used,
            "Inventory": [{"Name": "copper", "Count": used}] if used else [],
        }, fid="F-A", ship_id=51, cargo_capacity=256,
            srv_type=vehicle, srv_capacity=capacity)
        self.status(vessel)

    def test_default_off_and_real_checkbox_persistence(self):
        window = CargoLiveWindow(self.settings)
        self.addCleanup(window.close)
        self.addCleanup(window.deleteLater)
        self.assertFalse(cargo_hud_enabled(self.settings))
        self.assertFalse(window.hud_enabled_check.isChecked())
        self.assertEqual(window.hud_enabled_check.text(), "Im Elite-HUD anzeigen")
        changes = []
        window.hud_enabled_changed.connect(changes.append)
        window.hud_enabled_check.setChecked(True)
        saved = QSettings(self.settings_path, QSettings.IniFormat)
        restored = CargoLiveWindow(saved)
        self.addCleanup(restored.close)
        self.addCleanup(restored.deleteLater)
        self.assertTrue(restored.hud_enabled_check.isChecked())
        for vessel in ("Ship", "SRV", "Ship"):
            restored.set_snapshot({"vessel": vessel, "count": 0, "capacity": 72})
            self.assertTrue(restored.hud_enabled_check.isChecked())
        restored.hud_enabled_check.setChecked(False)
        saved.sync()
        self.assertFalse(cargo_hud_enabled(QSettings(self.settings_path, QSettings.IniFormat)))
        self.assertEqual(changes, [True])
        for value in (False, "false", "0", "off", "no"):
            saved.setValue("cargo_hud/enabled", value)
            self.assertFalse(cargo_hud_enabled(saved))

    def test_ship_and_known_srvs_use_own_names_and_capacities(self):
        self.cargo()
        self.assertEqual(cargo_hud_data(self.state).text,
                         "ERFT-BÜFFEL · FRACHTRAUM 128 / 256 t")
        for vehicle, maximum in (("mev_rhino", 72), ("testbuggy", 4),
                                 ("combat_multicrew_srv_01", 2)):
            with self.subTest(vehicle=vehicle):
                self.cargo("SRV", 2, vehicle)
                data = cargo_hud_data(self.state)
                self.assertEqual(data.vehicle_name, vehicle)
                self.assertEqual(data.capacity, maximum)
                self.assertNotEqual(data.capacity, self.state.ship_loadout.cargo_capacity)
        self.cargo("SRV", 67, "Rhino aus Elite", 80)
        self.assertEqual(cargo_hud_data(self.state).text, "Rhino aus Elite · FRACHTRAUM 67 / 80 t")

    def test_unknown_vehicle_and_capacity_show_only_confirmed_content(self):
        self.cargo("SRV", 7, "New vehicle")
        data = cargo_hud_data(self.state)
        self.assertEqual(data.text, "New vehicle · FRACHTRAUM 7 t")
        self.assertIsNone(data.fraction)
        self.assertIsNone(data.capacity)
        self.cargo()
        self.state.ship_loadout.cargo_capacity = None
        self.state.cargo_snapshot["capacity"] = None
        self.assertEqual(cargo_hud_data(self.state).text, "ERFT-BÜFFEL · FRACHTRAUM 128 t")

    def test_capacity_changes_and_explicit_values_take_precedence(self):
        self.cargo()
        self.state.ship_loadout.cargo_capacity = 512
        self.assertEqual(cargo_hud_data(self.state).capacity, 512)
        self.cargo("SRV", 67, "mev_rhino", 80)
        self.assertEqual(cargo_hud_data(self.state).capacity, 80)
        self.status("SRV", CargoCapacity=96)
        self.assertEqual(cargo_hud_data(self.state).capacity, 96)
        self.status("SRV", CargoCapacity=-1)
        self.assertEqual(cargo_hud_data(self.state).capacity, 80)

    def test_fill_zero_half_partial_full_and_defensive_limits(self):
        for used, capacity, fraction in ((0,72,0), (36,72,.5), (67,72,67/72),
                                          (72,72,1), (100,72,1), (-1,72,0),
                                          (1,None,None), (0,0,None), (1,-1,None),
                                          (1,True,None), (1,"72",None)):
            with self.subTest(used=used, capacity=capacity):
                self.assertEqual(cargo_fill_fraction(used, capacity), fraction)

    def test_vehicle_changes_hide_stale_snapshot_then_resume(self):
        self.cargo()
        self.hud.set_cargo_enabled(True)
        self.assertTrue(self.hud.isVisible())
        self.assertEqual(self.hud.cargo_data.capacity, 256)
        # Status detects entry before the matching Cargo event has arrived.
        self.status("SRV")
        self.hud.follow_target()
        self.assertFalse(self.hud.isVisible())
        self.cargo("SRV", 67, "mev_rhino")
        self.hud.follow_target()
        self.assertEqual(self.hud.cargo_data.capacity, 72)
        self.assertTrue(self.hud.isVisible())
        self.status("Ship")
        self.hud.follow_target()
        self.assertFalse(self.hud.isVisible())
        self.cargo("Ship", 128)
        self.hud.follow_target()
        self.assertEqual(self.hud.cargo_data.capacity, 256)
        self.assertTrue(self.hud.isVisible())
        self.assertTrue(self.hud.cargo_enabled)
        self.assertFalse(self.hud.enabled)

    def test_cargo_pickup_and_drop_update_on_existing_overlay_timer(self):
        self.cargo("SRV", 36, "mev_rhino")
        self.hud.set_cargo_enabled(True)
        for used in (67, 72, 36, 0):
            self.cargo("SRV", used, "mev_rhino")
            self.hud.timer.timeout.emit()
            self.assertEqual(self.hud.cargo_data.used, used)
            self.assertEqual(self.hud.cargo_data.fraction, used/72)

    def test_invalid_context_never_reuses_previous_data(self):
        for mutation in (
            lambda: setattr(self.state, "commander_fid", "F-B"),
            lambda: setattr(self.state.ship_loadout, "ship_id", 52),
            lambda: self.status(Flags=1 << 25),
            lambda: self.status(Flags=0),
            lambda: self.status(Flags=(1 << 24) | (1 << 26)),
            lambda: self.status(Flags2=1),
            lambda: self.status(Flags2=2),
            lambda: self.status(Flags2=4),
            lambda: self.status(timestamp="2020-01-01T00:00:00Z"),
            lambda: self.status(timestamp="2099-01-01T00:00:00Z"),
            lambda: (self.folder / "Status.json").write_text('{"event":'),
            lambda: setattr(self.state, "cargo_snapshot", None),
        ):
            self.state.commander_fid = "F-A"
            self.state.ship_loadout.ship_id = 51
            self.cargo()
            self.hud.set_cargo_enabled(True)
            mutation()
            self.hud.follow_target()
            self.assertIsNone(self.hud.cargo_data)
            self.assertFalse(self.hud.isVisible())
            self.assertTrue(self.hud.cargo_enabled)
        self.cargo("SRV", 2, "mev_rhino")
        self.state.active_srv_type = "testbuggy"
        self.assertIsNone(cargo_hud_data(self.state))

    def test_navigation_and_temporary_message_are_independent(self):
        self.cargo("SRV", 67, "mev_rhino")
        self.hud.set_cargo_enabled(True)
        self.controller.state = SimpleNamespace(snapshot=object(), solution=SimpleNamespace(
            relative=2, bearing=17, distance_m=145600, undefined_reason=""))
        for navigation_enabled in (False, True):
            self.hud.set_enabled(navigation_enabled)
            self.hud.show_message(("★ Favorit gespeichert", "Sol 1"), 20)
            self.assertTrue(self.hud.message_lines)
            self.assertTrue(self.hud.isVisible())
            QTest.qWait(50)
            self.assertFalse(self.hud.message_lines)
            self.assertTrue(self.hud.isVisible())
            self.assertTrue(self.hud.cargo_enabled)
            self.assertEqual(self.hud.enabled, navigation_enabled)
        self.hud.set_cargo_enabled(False)
        self.assertTrue(self.hud.isVisible())  # Navigation survives cargo off.
        self.hud.set_enabled(False)
        self.assertFalse(self.hud.isVisible())

    def test_minimize_restore_move_and_focus_neutrality(self):
        self.cargo()
        with patch.object(self.hud, "activateWindow", side_effect=AssertionError), \
             patch.object(self.hud, "raise_", side_effect=AssertionError), \
             patch.object(self.hud, "setFocus", side_effect=AssertionError):
            self.hud.set_cargo_enabled(True)
            self.tracker.current.return_value = None
            self.tracker.reason = "hidden"
            self.hud.follow_target()
            self.assertFalse(self.hud.isVisible())
            self.assertTrue(self.hud.timer.isActive())
            self.tracker.current.return_value = TargetWindow(42, QRect(-10, 30, 800, 500))
            self.hud.follow_target()
            self.assertTrue(self.hud.isVisible())
            self.assertEqual(self.hud.geometry(), QRect(-10, 30, 800, 500))
            self.hud.set_cargo_enabled(False)
            self.assertFalse(self.hud.timer.isActive())

    def test_sparse_paint_left_top_and_no_collision_on_narrow_clients(self):
        self.cargo("SRV", 67, "mev_rhino")
        self.hud.set_cargo_enabled(True)
        def render():
            image = QImage(self.hud.size(), QImage.Format_ARGB32_Premultiplied)
            image.fill(Qt.transparent)
            self.hud.render(image)
            return image
        self.hud.resize(800, 600)
        image = render()
        self.assertEqual(self.hud.cargo_geometry.topLeft().toPoint().x(), 16)
        self.assertEqual(self.hud.cargo_geometry.top(), 16)
        self.assertLess(self.hud.cargo_geometry.height(), 32)
        self.assertEqual(image.pixelColor(0, 0).alpha(), 0)
        self.assertEqual(image.pixelColor(400, 300).alpha(), 0)
        self.assertTrue(any(image.pixelColor(x, y).alpha()
                            for x in range(16, 436) for y in range(16, 48)))
        self.controller.state = SimpleNamespace(snapshot=object(), solution=SimpleNamespace(
            relative=2, bearing=17, distance_m=145600, undefined_reason=""))
        self.hud.set_enabled(True)
        self.hud.show_message(("★ Favorit gespeichert", "Sol 1"))
        render()
        self.assertGreater(self.hud.cargo_geometry.top(), 150)
        self.hud.clear_message()
        self.hud.set_enabled(False)
        self.cargo("SRV", 2, "Unknown")
        self.hud.follow_target()
        render()
        self.assertLess(self.hud.cargo_geometry.height(), 22)

    def test_saved_cargo_switch_starts_overlay_without_navigation_or_live_window(self):
        main = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(main)
        self.addCleanup(main.deleteLater)
        main.state = self.state
        main._navigation_hud = None
        main._planet_navigation_controller = self.controller
        main._cargo_live_window = None
        main._planet_navigation_window = None
        self.cargo()
        self.settings.setValue("cargo_hud/enabled", True)
        with patch("cmdrhelper.ui.navigation_hud.NavigationHud", return_value=self.hud):
            main._apply_cargo_hud_enabled()
        self.assertTrue(self.hud.isVisible())
        self.assertFalse(self.hud.enabled)
        self.assertIsNone(main._cargo_live_window)
        self.assertIsNone(main._planet_navigation_window)
        main._set_cargo_live_window_enabled(True)
        window = main._cargo_live_window
        self.addCleanup(window.close)
        window.hud_enabled_check.setChecked(False)
        self.assertFalse(self.hud.isVisible())
        window.hud_enabled_check.setChecked(True)
        self.assertTrue(self.hud.isVisible())
        main._set_cargo_live_window_enabled(False)
        self.assertTrue(self.hud.isVisible())

    def test_all_new_keys_and_placeholders_in_twelve_languages(self):
        from tools.check_i18n import placeholders
        self.assertEqual(len(_TRANSLATIONS), 12)
        for language, table in _TRANSLATIONS.items():
            for key, fields in (("enabled", set()), ("label", set()), ("ship", set()),
                                ("srv", set()), ("summary", {"vehicle", "cargo", "amount"})):
                with self.subTest(language=language, key=key):
                    self.assertEqual(placeholders(table["cargo.hud." + key]), fields)


if __name__ == "__main__":
    unittest.main()
