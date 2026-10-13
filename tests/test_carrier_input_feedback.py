import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QScrollArea

from cmdrhelper.i18n import _TRANSLATIONS, get_language, set_language, tr
from cmdrhelper.route_planner.carrier_inputs import parse_snapshot
from cmdrhelper.route_planner.carrier_input_widget import CarrierInputWidget
from cmdrhelper.route_planner.route_planner_view import RoutePlannerView
from cmdrhelper.ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET
from tests.test_carrier_route_inputs import stats


class CarrierFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.state = SimpleNamespace(commander_fid="F-A", carrier_input_session="s",
            carrier_input_revision="stats", carrier_snapshot=parse_snapshot(stats(), "F-A", "s"))
        self.view = RoutePlannerView(self.state)
        self.addCleanup(self.view.close)
        self.inputs = self.view.carrier_inputs
        self.view.carrier_start_system.setText("Sol")
        self.view.carrier_destination_system.setText("Alpha")
        self.inputs.storage.setValue(4400)
        self.worker = patch("cmdrhelper.route_planner.route_planner_view.CarrierRouteWorker").start()
        self.addCleanup(patch.stopall)
        self.pool = patch.object(self.view._thread_pool, "start").start()

    def click(self):
        self.view.carrier_calculate_button.click()

    def test_missing_confirmation_no_worker_or_request(self):
        self.click()
        self.worker.assert_not_called()
        self.pool.assert_not_called()
        self.assertTrue(self.inputs.blink_timer.isActive())
        self.assertEqual(self.inputs.input_hint.text(), tr("route_planner.carrier_confirmation_required"))
        self.assertFalse(self.inputs.input_hint.isHidden())
        for field in (self.inputs.callsign, self.inputs.used, self.inputs.tank, self.inputs.storage):
            self.assertFalse(field.property("carrierInputInvalid"))

    def test_exactly_three_blink_cycles(self):
        self.click()
        phases = [self.inputs.confirm.property("carrierConfirmPulse")]
        for _ in range(5):
            self.inputs._advance_blink()
            phases.append(self.inputs.confirm.property("carrierConfirmPulse"))
        self.assertEqual(phases, [True, False, True, False, True, False])
        self.assertFalse(self.inputs.blink_timer.isActive())
        self.assertFalse(self.inputs.input_hint.isHidden())

    def test_real_timer_terminates(self):
        self.click()
        QTest.qWait(1250)
        self.assertEqual(self.inputs._blink_phase, 6)
        self.assertFalse(self.inputs.blink_timer.isActive())
        self.assertFalse(self.inputs.confirm.property("carrierConfirmPulse"))

    def test_repeated_click_does_not_restart_active_animation(self):
        self.click()
        self.inputs._advance_blink()
        for _ in range(4):
            self.click()
        self.assertEqual(self.inputs._blink_phase, 2)
        self.worker.assert_not_called()
        for _ in range(4):
            self.inputs._advance_blink()
        self.click()
        self.assertEqual(self.inputs._blink_phase, 1)

    def test_confirmation_stops_animation_and_clears_hint(self):
        self.click()
        self.inputs.confirm.setChecked(True)
        self.assertFalse(self.inputs.blink_timer.isActive())
        self.assertFalse(self.inputs.confirm.property("carrierConfirmPulse"))
        self.assertTrue(self.inputs.input_hint.isHidden())
        self.click()
        self.worker.assert_called_once()
        self.assertIsNone(self.worker.call_args.args[0].validation_error())

    def test_missing_fields_highlighted_without_blinking(self):
        self.inputs.manual.setChecked(True)
        self.inputs.callsign.clear()
        self.click()
        for field in (self.inputs.callsign, self.inputs.used, self.inputs.tank, self.inputs.storage):
            self.assertTrue(field.property("carrierInputInvalid"))
        self.assertFalse(self.inputs.blink_timer.isActive())
        self.worker.assert_not_called()

    def test_only_invalid_storage_highlighted(self):
        self.inputs.storage.setValue(5400)
        self.click()
        self.assertTrue(self.inputs.storage.property("carrierInputInvalid"))
        for field in (self.inputs.callsign, self.inputs.used, self.inputs.tank):
            self.assertFalse(field.property("carrierInputInvalid"))
        self.assertFalse(self.inputs.blink_timer.isActive())
        self.worker.assert_not_called()

    def test_valid_fields_without_confirmation_are_not_highlighted(self):
        self.inputs.storage.setValue(-1)
        self.click()
        self.inputs.storage.setValue(4400)
        self.click()
        self.assertFalse(self.inputs.storage.property("carrierInputInvalid"))
        self.assertTrue(self.inputs.blink_timer.isActive())

    def test_missing_system_highlight(self):
        for field in (self.view.carrier_start_system, self.view.carrier_destination_system):
            field.clear()
            self.click()
            self.assertTrue(field.property("carrierInputInvalid"))
            field.setText("Sol")
            self.assertFalse(field.property("carrierInputInvalid"))
        self.worker.assert_not_called()

    def test_context_error_does_not_blink_confirmation(self):
        self.state.commander_fid = ""
        self.click()
        self.assertFalse(self.inputs.blink_timer.isActive())
        self.worker.assert_not_called()

    def test_snapshot_hint_appears_and_disappears(self):
        self.state.carrier_snapshot = None
        self.inputs.refresh()
        self.assertFalse(self.inputs.snapshot_hint.isHidden())
        self.assertEqual(self.inputs.snapshot_hint.text(), tr("route_planner.carrier_snapshot_help"))
        self.state.carrier_snapshot = parse_snapshot(stats(FuelLevel=None), "F-A", "s")
        self.inputs.refresh()
        self.assertFalse(self.inputs.snapshot_hint.isHidden())
        self.state.carrier_snapshot = parse_snapshot(stats(), "F-A", "s")
        self.inputs.refresh()
        self.assertTrue(self.inputs.snapshot_hint.isHidden())
        self.assertEqual((self.inputs.used.value(), self.inputs.tank.value()), (5334, 1000))
        self.assertEqual(self.inputs.storage.value(), -1)

    def test_close_parent_stops_animation(self):
        self.view.route_tabs.setCurrentIndex(1)
        self.view.show()
        self.click()
        self.view.close()
        self.assertFalse(self.inputs.blink_timer.isActive())
        self.assertFalse(self.inputs.confirm.property("carrierConfirmPulse"))

    def test_close_input_stops_animation_even_when_hidden(self):
        self.click()
        self.inputs.close()
        self.assertFalse(self.inputs.blink_timer.isActive())

    def test_close_hidden_parent_stops_animation(self):
        self.click()
        self.view.close()
        self.assertFalse(self.inputs.blink_timer.isActive())

    def test_confirmation_is_revealed_in_scroll_area(self):
        scroll = QScrollArea()
        self.addCleanup(scroll.close)
        widget = CarrierInputWidget(self.state)
        scroll.setWidget(widget)
        widget.storage.setValue(4400)
        with patch.object(scroll, "ensureWidgetVisible") as reveal:
            widget.show_validation_feedback(widget.request("S", "D", 500))
            reveal.assert_called_once_with(widget.confirm, 20, 60)

    def test_twelve_languages_and_theme_colors(self):
        self.addCleanup(set_language, get_language())
        for language, texts in _TRANSLATIONS.items():
            set_language(language)
            for key in ("carrier_confirmation_required", "carrier_check_fields", "carrier_snapshot_help"):
                self.assertTrue(texts["route_planner." + key])
            self.click()
            self.assertEqual(self.inputs.input_hint.text(), texts["route_planner.carrier_confirmation_required"])
            for style, color in ((DARK_STYLESHEET, "#ffb74d"), (LIGHT_STYLESHEET, "#9a4d00")):
                self.inputs.setStyleSheet(style)
                self.inputs.confirm.ensurePolished()
                self.assertEqual(self.inputs.confirm.palette().color(self.inputs.confirm.foregroundRole()).name(), color)
            self.inputs.clear_feedback()

    def show_missing_snapshot(self):
        self.state.carrier_snapshot = None
        self.inputs.refresh()
        self.view.route_tabs.setCurrentIndex(1)
        self.view.show()
        self.app.processEvents()
        self.view.carrier_start_system.setText("Sol")
        self.view.carrier_destination_system.setText("Alpha")

    def finish_snapshot_blink(self):
        while self.inputs.snapshot_blink_timer.isActive():
            self.inputs._advance_snapshot_blink()

    def test_snapshot_first_visible_three_cycles_then_stays_visible(self):
        self.state.carrier_snapshot = None
        self.inputs.refresh()
        self.assertFalse(self.inputs.snapshot_blink_timer.isActive())
        self.show_missing_snapshot()
        self.assertTrue(self.inputs.snapshot_blink_timer.isActive())
        phases = [self.inputs.snapshot_hint.property("carrierSnapshotDim")]
        for _ in range(5):
            self.inputs._advance_snapshot_blink()
            phases.append(self.inputs.snapshot_hint.property("carrierSnapshotDim"))
        self.assertEqual(phases, [True, False, True, False, True, False])
        self.assertFalse(self.inputs.snapshot_blink_timer.isActive())
        self.assertTrue(self.inputs.snapshot_hint.isVisible())
        self.inputs.refresh()
        self.assertFalse(self.inputs.snapshot_blink_timer.isActive())

    def test_snapshot_real_timer_finishes(self):
        self.show_missing_snapshot()
        QTest.qWait(1700)
        self.assertFalse(self.inputs.snapshot_blink_timer.isActive())
        self.assertEqual(self.inputs._snapshot_blink_phase, 6)
        self.assertFalse(self.inputs.snapshot_hint.property("carrierSnapshotDim"))

    def test_snapshot_click_repeats_even_with_missing_system(self):
        self.show_missing_snapshot()
        self.finish_snapshot_blink()
        self.view.carrier_start_system.clear()
        self.click()
        self.assertTrue(self.inputs.snapshot_blink_timer.isActive())
        self.inputs._advance_snapshot_blink()
        self.click()
        self.assertEqual(self.inputs._snapshot_blink_phase, 2)
        self.worker.assert_not_called()
        self.pool.assert_not_called()

    def test_snapshot_arrival_removes_hint_and_animation(self):
        self.show_missing_snapshot()
        self.state.carrier_snapshot = parse_snapshot(stats(), "F-A", "s")
        self.inputs.refresh()
        self.assertTrue(self.inputs.snapshot_hint.isHidden())
        self.assertFalse(self.inputs.snapshot_blink_timer.isActive())
        self.click()
        self.assertFalse(self.inputs.snapshot_blink_timer.isActive())

    def test_new_invalid_snapshot_starts_hint(self):
        self.view.route_tabs.setCurrentIndex(1)
        self.view.show()
        self.assertFalse(self.inputs.snapshot_blink_timer.isActive())
        self.state.carrier_snapshot = parse_snapshot(stats(FuelLevel=None), "F-A", "s")
        self.inputs.refresh()
        self.assertTrue(self.inputs.snapshot_hint.isVisible())
        self.assertTrue(self.inputs.snapshot_blink_timer.isActive())

    def test_snapshot_and_confirmation_blink_independently(self):
        self.show_missing_snapshot()
        self.inputs.manual.setChecked(True)
        self.inputs.callsign.setText("ABC-123")
        for field in (self.inputs.used, self.inputs.tank, self.inputs.storage):
            field.setValue(0)
        self.click()
        self.assertTrue(self.inputs.blink_timer.isActive())
        self.assertTrue(self.inputs.snapshot_blink_timer.isActive())
        self.inputs.confirm.setChecked(True)
        self.assertFalse(self.inputs.blink_timer.isActive())
        self.assertTrue(self.inputs.snapshot_blink_timer.isActive())

    def test_snapshot_menu_switch_and_close_stop_animation(self):
        self.show_missing_snapshot()
        self.view.route_tabs.setCurrentIndex(0)
        self.assertFalse(self.inputs.snapshot_blink_timer.isActive())
        self.inputs.refresh()
        self.assertFalse(self.inputs.snapshot_blink_timer.isActive())
        self.view.route_tabs.setCurrentIndex(1)
        self.assertFalse(self.inputs.snapshot_blink_timer.isActive())
        self.click()
        self.assertTrue(self.inputs.snapshot_blink_timer.isActive())
        self.view.close()
        self.assertFalse(self.inputs.snapshot_blink_timer.isActive())

    def test_snapshot_elite_yellow_and_contrast_in_both_themes(self):
        def luminance(channels):
            linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
            return sum(v*w for v, w in zip(linear, (.2126, .7152, .0722)))

        self.show_missing_snapshot()
        for style in (DARK_STYLESHEET, LIGHT_STYLESHEET):
            self.inputs.setStyleSheet(style)
            for dim in (False, True):
                self.inputs._mark(self.inputs.snapshot_hint, "carrierSnapshotDim", dim)
                palette = self.inputs.snapshot_hint.palette()
                foreground = palette.color(self.inputs.snapshot_hint.foregroundRole())
                background = palette.color(self.inputs.snapshot_hint.backgroundRole())
                self.assertEqual(foreground.name(), "#ffcc33")
                self.assertEqual(background.name(), "#2d3036")
                bg = background.getRgbF()[:3]
                alpha = foreground.alphaF()
                fg = [f*alpha+b*(1-alpha) for f, b in zip(foreground.getRgbF()[:3], bg)]
                self.assertGreaterEqual((luminance(fg)+.05)/(luminance(bg)+.05), 4.5)
