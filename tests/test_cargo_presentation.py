"""Synthetic UI regressions: no AppState startup, journals, network or user settings."""
import os
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QObject, QRect, Qt, Signal
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMainWindow

from cmdrhelper.i18n import _TRANSLATIONS, set_language, tr_for_language
from cmdrhelper.ui.cargo_hud import (
    CargoHudData, CargoHudPresentation, cargo_activity_key, cargo_item_name,
)
from cmdrhelper.ui.main_window import CargoLiveWindow, MainWindow
from cmdrhelper.ui.navigation_hud import NavigationHud, TargetWindow
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET


class Settings:
    def __init__(self):
        self.values = {"cargo_live/enabled": True, "cargo_hud/enabled": True}

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value

    def sync(self):
        pass


class Controller(QObject):
    changed = Signal(object)

    def __init__(self):
        super().__init__()
        self.state = SimpleNamespace(snapshot=None, solution=None)
        self.consumer_acquire = Mock()
        self.consumer_release = Mock()


def snapshot(count=1, drones=4):
    return dict(fid="fixture", vessel="Ship", ship_id=1, count=count + drones,
                capacity=100, timestamp="2020-01-01T00:00:00Z", inventory=[
                    dict(frontier_name="silver", display_name="Silber", count=count),
                    dict(frontier_name="drones", count=drones, is_drones=True)])


def bind_context(state, value):
    origin = dict(fid="fixture", journal="synthetic-journal", session_start="2020-01-01",
                  session_generation=1, vessel="Ship", ship_id=1, generation=10)
    value["context"] = origin
    state.commander_fid = "fixture"
    state.ship_cargo_context = dict(origin, active=True)
    state.ship_loadout = SimpleNamespace(ship_id=1, cargo_capacity=100, ship_name="Fixture")
    state._cargo_refresh_data = ({}, dict(attribution_status="identified", commander_id=1,
                                        fid_seen="fixture", journal_file="synthetic-journal"))


class CargoPresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        set_language("de")
        self.addCleanup(set_language, "de")
        self.main = MainWindow.__new__(MainWindow)
        QMainWindow.__init__(self.main)
        self.state = SimpleNamespace(settings=Settings(), cargo_snapshot=snapshot())
        self.main.state = self.state
        self.main._cargo_live_window = None
        self.controller = Controller()
        self.tracker = Mock(reason="active", error="", last_target=None)
        self.tracker.input_is_empty.return_value = True
        self.tracker.current.return_value = TargetWindow(42, QRect(10, 20, 800, 600))
        self.hud = NavigationHud(self.controller, self.tracker)
        self.hud.cargo_provider = lambda: CargoHudData(
            "Fixture", self.state.cargo_snapshot["count"], 100)
        self.hud.cargo_activity_provider = lambda: cargo_activity_key(self.state.cargo_snapshot)
        self.main._navigation_hud = self.hud
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.hud.close()
        self.hud.deleteLater()
        if self.main._cargo_live_window is not None:
            self.main._cargo_live_window.close()
        self.main.deleteLater()
        self.app.processEvents()

    def start(self):
        self.hud.set_cargo_enabled(True)
        self.update(snapshot())
        return self.main._cargo_live_window

    def update(self, value):
        self.state.cargo_snapshot = value
        self.main._refresh_cargo_live_window(value)

    def test_ten_one_second_changes_then_real_fifteen_second_expiry(self):
        window = self.start()
        for index in range(10):
            QTest.qWait(1000)
            self.update(snapshot(index + 2, 10 - index))
            for view in (window, self.hud):
                self.assertTrue(view.isVisible())
                self.assertEqual(view.cargo_visibility.timer.interval(), 15000)
                self.assertGreater(view.cargo_visibility.timer.remainingTime(), 14000)
        QTest.qWait(14000)
        self.assertTrue(window.isVisible())
        self.assertTrue(self.hud.isVisible())
        QTest.qWait(1200)
        self.assertFalse(window.isVisible())
        self.assertFalse(self.hud.isVisible())
        # Polling the same data must not reopen an expired display.
        self.update(deepcopy(self.state.cargo_snapshot))
        self.hud.follow_target()
        self.assertFalse(window.isVisible())
        self.assertFalse(self.hud.isVisible())
        self.update(snapshot(20))
        self.assertTrue(window.isVisible())
        self.assertTrue(self.hud.isVisible())

    def test_visible_updates_reuse_windows_without_show_hide_or_focus(self):
        window = self.start()
        from contextlib import ExitStack
        with ExitStack() as stack:
            for view in (window, self.hud):
                for method in ("show", "hide", "activateWindow", "raise_", "setFocus"):
                    stack.enter_context(patch.object(view, method, side_effect=AssertionError(method)))
            for index in range(10):
                self.update(snapshot(index + 2, index + 5))
                self.assertIs(self.main._cargo_live_window, window)
                self.assertTrue(window.isVisible())
                self.assertTrue(self.hud.isVisible())
        self.assertTrue(window.testAttribute(Qt.WA_ShowWithoutActivating))
        self.assertTrue(self.hud.testAttribute(Qt.WA_ShowWithoutActivating))
        self.assertTrue(self.hud.windowFlags() & Qt.WindowDoesNotAcceptFocus)

    def test_duplicate_timestamp_and_order_do_not_restart_timer(self):
        window = self.start()
        with patch.object(window.cargo_visibility.timer, "start") as live_start, \
                patch.object(self.hud.cargo_visibility.timer, "start") as hud_start:
            value = deepcopy(self.state.cargo_snapshot)
            value["timestamp"] = "2020-01-01T00:01:00Z"
            value["inventory"].reverse()
            self.update(value)
            for _ in range(5):
                self.hud.follow_target()
            live_start.assert_not_called()
            hud_start.assert_not_called()

    def test_limpet_changes_reset_both_timers_even_when_total_is_unchanged(self):
        window = self.start()
        with patch.object(window.cargo_visibility.timer, "start") as live_start, \
                patch.object(self.hud.cargo_visibility.timer, "start") as hud_start:
            for index in range(4):
                self.update(snapshot(index + 2, 3 - index))
            self.assertEqual(live_start.call_count, 4)
            self.assertEqual(hud_start.call_count, 4)

    def test_manual_open_stays_visible_and_manual_close_suppresses_duplicate(self):
        window = self.start()
        window.show()
        self.hud.set_cargo_enabled(True, manual=True)
        self.update(snapshot(4))
        for view in (window, self.hud):
            self.assertFalse(view.cargo_visibility.timer.isActive())
            view.cargo_visibility.timer.timeout.emit()
            self.assertTrue(view.isVisible())
        window.close()
        self.assertFalse(window.cargo_visibility.timer.isActive())
        self.update(snapshot(4))
        self.assertFalse(window.isVisible())
        self.update(snapshot(5))
        self.assertTrue(window.isVisible())
        self.assertFalse(window.cargo_visibility.manual)
        window.reject()  # Escape follows the same policy as the close button.
        self.update(snapshot(5))
        self.assertFalse(window.isVisible())
        self.hud.close()
        self.assertFalse(self.hud.cargo_visibility.timer.isActive())
        self.update(snapshot(6))
        self.assertFalse(self.hud.isVisible())

    def test_explicit_settings_open_and_disabled_settings(self):
        self.start()
        self.main._set_cargo_live_window_enabled(True)
        self.main._set_cargo_hud_enabled(True)
        for view in (self.main._cargo_live_window, self.hud):
            self.assertTrue(view.cargo_visibility.manual)
            self.assertFalse(view.cargo_visibility.timer.isActive())
        self.main._set_cargo_live_window_enabled(False)
        self.main._set_cargo_hud_enabled(False)
        self.update(snapshot(9))
        self.assertFalse(self.main._cargo_live_window.isVisible())
        self.assertFalse(self.hud.isVisible())

    def test_rows_quantities_stolen_and_order_reuse(self):
        window = self.start()
        silver, amount = window.table.item(0, 0), window.table.item(0, 1)
        drone = window.table.item(1, 0)
        drone_height = window.table.rowHeight(1)
        value = snapshot(7)
        value["inventory"].reverse()
        self.update(value)
        self.assertIs(window.table.item(0, 0), silver)
        self.assertIs(window.table.item(0, 1), amount)
        self.assertIs(window.table.item(1, 0), drone)
        self.assertEqual(amount.text(), "7 t")
        self.assertEqual(window.table.rowHeight(1), drone_height)
        value["inventory"].append(dict(frontier_name="osmium", count=2, stolen=1))
        self.update(value)
        self.assertIs(window.table.item(0, 0), silver)
        self.assertIs(window.table.item(2, 0), drone)
        self.assertEqual(window.table.item(1, 0).text(), "Osmium · davon 1 t gestohlen")
        self.assertTrue(drone.font().bold())
        value["inventory"] = [item for item in value["inventory"] if item["frontier_name"] != "silver"]
        self.update(value)
        self.assertIs(window.table.item(1, 0), drone)
        self.assertEqual(window.table.item(0, 0).text(), "Osmium · davon 1 t gestohlen")

    def test_geometry_and_widgets_survive_themes_inventory_and_reopening(self):
        window = self.start()
        original = self.app.styleSheet()
        self.addCleanup(self.app.setStyleSheet, original)
        for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.app.setStyleSheet(theme)
            window.resize(470, 330)
            window.move(80, 90)
            self.app.processEvents()
            geometry = window.geometry()
            table = window.table
            for index in range(4):
                self.update(snapshot(index + 2))
                self.app.processEvents()
                self.assertEqual(window.geometry(), geometry)
                self.assertIs(window.table, table)
                self.assertTrue(window.table.item(1, 0).font().bold())
            window.close()
            self.update(snapshot(10))
            self.assertEqual(window.geometry(), geometry)
        other = CargoLiveWindow(self.state.settings)
        self.addCleanup(other.deleteLater)
        self.addCleanup(other.close)
        other.present_snapshot(snapshot(3))
        self.assertEqual(other.size(), window.size())

    def test_names_all_twelve_languages_and_both_themes(self):
        window = self.start()
        original = self.app.styleSheet()
        self.addCleanup(self.app.setStyleSheet, original)
        self.assertEqual(len(_TRANSLATIONS), 12)
        for theme in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.app.setStyleSheet(theme)
            for language in _TRANSLATIONS:
                set_language(language)
                rows = [dict(frontier_name=name, display_name=name, count=1)
                        for name in ("silver", "samarium", "osmium", "lowtemperaturediamond")]
                rows.append(dict(frontier_name="drones", count=2, is_drones=True))
                window.set_snapshot(dict(vessel="Ship", count=6, inventory=rows))
                for row in range(3):
                    name = rows[row]["frontier_name"]
                    self.assertEqual(window.table.item(row, 0).text(),
                                     tr_for_language(language, "mining.commodity." + name))
                self.assertNotEqual(window.table.item(3, 0).text(), "lowtemperaturediamond")
                self.assertTrue(window.table.item(4, 0).font().bold())
                self.assertEqual(window.table.item(4, 0).text(),
                                 tr_for_language(language, "cargo.live.drones"))

    def test_localized_multipart_unknown_and_raw_identifier_names(self):
        self.assertEqual(cargo_item_name(dict(frontier_name="silver")), "Silber")
        self.assertEqual(cargo_item_name(dict(frontier_name="$Samarium_Name;")), "Samarium")
        self.assertEqual(cargo_item_name(dict(frontier_name="osmium", display_name="osmium")), "Osmium")
        localized = dict(frontier_name="synthetic", display_name="Objets d’art de l’espace")
        self.assertEqual(cargo_item_name(localized), localized["display_name"])
        self.assertEqual(cargo_item_name(dict(frontier_name="unKnownToken")), "unKnownToken")
        set_language("en")
        self.assertEqual(cargo_item_name(dict(frontier_name="silver")), "Silver")
        self.assertEqual(cargo_item_name(dict(frontier_name="lowtemperaturediamond")), "Low Temperature Diamonds")
        self.assertEqual(cargo_item_name(dict(frontier_name="silver", display_name="Silber")), "Silber")

    def test_missing_sidecar_retains_window_only_in_same_session_then_expires(self):
        value = snapshot()
        bind_context(self.state, value)
        # This test isolates the supplemental window; HUD retention is below.
        self.hud.set_cargo_enabled(False)
        self.update(value)
        window = self.main._cargo_live_window
        window.show()  # Even manual displays may not retain unknown data forever.
        silver = window.table.item(0, 0)
        with patch.object(window, 'hide', wraps=window.hide) as hidden:
            self.update(None)
            self.assertTrue(window.isVisible())
            self.assertIs(window.table.item(0, 0), silver)
            hidden.assert_not_called()
        with patch.object(window._pending_snapshot_timer, 'start') as start:
            self.update(None)
            start.assert_not_called()
        self.update(value)
        self.assertFalse(window._pending_snapshot_timer.isActive())
        self.assertIs(window.table.item(0, 0), silver)
        self.update(None)
        window._pending_snapshot_timer.timeout.emit()
        self.assertTrue(window.isVisible())
        self.assertEqual(window.summary_label.text(), '–')
        self.assertEqual(window.table.rowCount(), 0)
        self.update(value)
        self.state.ship_cargo_context['session_generation'] = 2
        self.update(None)
        self.assertTrue(window.isVisible())
        self.assertEqual(window.summary_label.text(), '–')

    def test_both_presentations_survive_pending_sidecars_without_hide_or_show(self):
        value = snapshot()
        bind_context(self.state, value)
        self.state.journal_folder = Path('/synthetic-not-read')
        self.state.active_srv_type = ''
        self.state.cargo_snapshot = value
        presenter = CargoHudPresentation(self.state)
        self.hud.cargo_provider = presenter
        self.hud.cargo_activity_provider = presenter.activity_key
        status = dict(event='Status', Flags=1 << 24, Flags2=0,
                      timestamp='2020-01-01T00:00:01Z')
        from contextlib import ExitStack
        with patch('cmdrhelper.ui.cargo_hud.read_status_data', return_value=(status, None)):
            self.hud.set_cargo_enabled(True)
            self.update(value)
            window = self.main._cargo_live_window
            with ExitStack() as stack:
                for view in (window, self.hud):
                    for method in ('show', 'hide', 'activateWindow', 'raise_'):
                        stack.enter_context(patch.object(view, method, side_effect=AssertionError(method)))
                old_data = self.hud.cargo_data
                self.update(None)
                self.assertIs(self.hud.cargo_data, old_data)
                self.assertTrue(window.isVisible())
                with patch('cmdrhelper.ui.cargo_hud.read_status_data', side_effect=ValueError('partial')):
                    self.hud.follow_target()
                    self.assertIs(self.hud.cargo_data, old_data)
                updated = deepcopy(value)
                updated.update(count=12, timestamp='2020-01-01T00:00:02Z')
                updated['inventory'][0]['count'] = 8
                self.update(updated)
                self.assertIs(self.hud.cargo_data, old_data)
                status['timestamp'] = '2020-01-01T00:00:03Z'
                self.hud.follow_target()
                self.assertEqual(self.hud.cargo_data.used, 12)
                self.assertEqual(window.table.item(0, 1).text(), '8 t')


class CargoHudLagTests(unittest.TestCase):
    def setUp(self):
        self.reset_state()
        reader = patch('cmdrhelper.ui.cargo_hud.read_status_data', side_effect=lambda _: (self.status, None))
        reader.start()
        self.addCleanup(reader.stop)

    def reset_state(self):
        self.state = SimpleNamespace(cargo_snapshot=snapshot(), commander_fid="fixture",
            journal_folder=Path('/synthetic-not-read'), active_srv_type="", ship="Fixture",
            ship_loadout=SimpleNamespace(ship_id=1, cargo_capacity=100, ship_name="Fixture"))
        self.status = dict(event="Status", Flags=1 << 24, Flags2=0,
                           timestamp="2020-01-01T00:00:01Z")
        self.presenter = CargoHudPresentation(self.state)

    def test_status_lag_retains_verified_amount_then_updates(self):
        original = self.presenter()
        self.state.cargo_snapshot = snapshot(10)
        self.state.cargo_snapshot['timestamp'] = "2020-01-01T00:00:02Z"
        self.assertIs(self.presenter(), original)
        self.assertEqual(original.used, 5)
        self.status['timestamp'] = "2020-01-01T00:00:03Z"
        self.assertEqual(self.presenter().used, 14)

    def test_retention_is_bounded_even_for_manual_display(self):
        self.presenter()
        self.state.cargo_snapshot['timestamp'] = "2020-01-01T00:00:02Z"
        with patch('cmdrhelper.ui.cargo_hud.time.monotonic', return_value=self.presenter.verified_at + 16):
            self.assertIsNone(self.presenter())

    def test_context_changes_and_regressed_status_never_retain_old_amount(self):
        for mutation in (
            lambda: setattr(self.state, 'commander_fid', 'other'),
            lambda: setattr(self.state.ship_loadout, 'ship_id', 2),
            lambda: self.status.update(Flags=1 << 26),
            lambda: self.status.update(Flags2=1),
            lambda: self.status.update(timestamp="2019-01-01T00:00:00Z"),
        ):
            self.reset_state()
            self.presenter()
            self.state.cargo_snapshot['timestamp'] = "2020-01-01T00:00:02Z"
            mutation()
            self.assertIsNone(self.presenter())

    def test_pending_cargo_and_status_write_keep_last_value_without_new_activity(self):
        bind_context(self.state, self.state.cargo_snapshot)
        original = self.presenter()
        activity = self.presenter.activity_key()
        self.state.cargo_snapshot = None
        self.state.ship_cargo_context['generation'] += 1
        self.assertIs(self.presenter(), original)
        self.assertEqual(self.presenter.activity_key(), activity)
        with patch('cmdrhelper.ui.cargo_hud.read_status_data', side_effect=ValueError('partial')):
            self.assertIs(self.presenter(), original)
        self.state.ship_cargo_context['session_generation'] += 1
        self.assertIsNone(self.presenter())

    def test_status_lag_does_not_bridge_new_session_with_same_ship(self):
        bind_context(self.state, self.state.cargo_snapshot)
        self.presenter()
        self.state.cargo_snapshot = deepcopy(self.state.cargo_snapshot)
        self.state.cargo_snapshot['timestamp'] = "2020-01-01T00:00:02Z"
        self.state.cargo_snapshot['context']['session_generation'] += 1
        self.assertIsNone(self.presenter())


if __name__ == '__main__':
    unittest.main()
