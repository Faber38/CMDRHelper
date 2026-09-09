import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from unittest.mock import Mock
from PySide6.QtCore import QObject, Signal
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from cmdrhelper.route_planner.route_planner_view import RoutePlannerView


class State(QObject):
    changed = Signal()
    positionChanged = Signal(str, object, str)
    system = ''
    system_address = None


class CurrentSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.state = State()
        self.view = RoutePlannerView(self.state)
        self.addCleanup(self.view.close)

    def update(self, system):
        self.state.system = system
        self.state.changed.emit()

    def test_restored_state_after_construction(self):
        self.update('Plio Aip LG-G b52-0')
        self.assertEqual(self.view.ship_current_system.text(), self.state.system)
        for field in (self.view.ship_start_system, self.view.carrier_start_system):
            self.assertEqual(field.text(), self.state.system)

    def test_initial_state(self):
        self.state.system = 'Sol'
        view = RoutePlannerView(self.state)
        self.addCleanup(view.close)
        self.assertEqual(view.ship_current_system.text(), 'Sol')
        self.assertEqual(view.ship_start_system.text(), 'Sol')
        self.assertEqual(view.carrier_start_system.text(), 'Sol')

    def test_automatic_starts_follow_system(self):
        self.update('A')
        self.update('B')
        self.assertEqual(self.view.ship_start_system.text(), 'B')
        self.assertEqual(self.view.carrier_start_system.text(), 'B')

    def test_manual_starts_survive_refresh_and_jump(self):
        for field in (self.view.ship_start_system, self.view.carrier_start_system):
            field.selectAll()
            QTest.keyClicks(field, 'Manual')
        self.update('A')
        self.state.system = 'B'
        self.state.positionChanged.emit('B', 2, 'FSDJump')
        self.state.changed.emit()
        self.assertEqual(self.view.ship_current_system.text(), 'B')
        self.view._refresh_ship_route_status()
        self.assertEqual(self.view.ship_current_system.text(), 'B')
        for field in (self.view.ship_start_system, self.view.carrier_start_system):
            self.assertEqual(field.text(), 'Manual')

    def test_manual_modes_independent(self):
        QTest.keyClicks(self.view.carrier_start_system, 'Carrier origin')
        self.update('B')
        self.assertEqual(self.view.ship_start_system.text(), 'B')
        self.assertEqual(self.view.carrier_start_system.text(), 'Carrier origin')

    def test_cleared_manual_start_resumes_automatic(self):
        field = self.view.ship_start_system
        QTest.keyClicks(field, 'Manual')
        field.clear()
        self.update('B')
        self.update('C')
        self.assertEqual(field.text(), 'C')

    def test_open_and_handoff_sync_without_calculation(self):
        self.state.system = 'Plio Aip LG-G b52-0'
        with unittest.mock.patch.object(self.view._thread_pool, 'start') as start:
            self.view.set_destination_system('NGC 6530 Sector ZE-X b2-0')
            self.view.show()
            self.app.processEvents()
            start.assert_not_called()
        self.assertEqual(self.view.ship_start_system.text(), self.state.system)
        self.assertEqual(self.view.ship_current_system.text(), self.state.system)
        self.assertEqual(self.view.ship_destination_system.text(), 'NGC 6530 Sector ZE-X b2-0')
        self.assertIsNone(self.view._ship_controller.route)
        self.assertIsNone(self.view._carrier_route)

    def test_unknown_state_clears_only_automatic(self):
        self.update('A')
        self.view.carrier_start_system.selectAll()
        QTest.keyClicks(self.view.carrier_start_system, 'Manual')
        self.update('')
        self.assertEqual(self.view.ship_current_system.text(), '–')
        self.assertEqual(self.view.ship_start_system.text(), '')
        self.assertEqual(self.view.carrier_start_system.text(), 'Manual')

    def test_carrier_jump_does_not_change_route_data(self):
        route = Mock()
        self.view._carrier_route = route
        self.state.system = 'B'
        self.state.positionChanged.emit('B', 2, 'CarrierJump')
        self.assertIs(self.view._carrier_route, route)
        self.assertEqual(self.view.carrier_start_system.text(), 'B')
        self.assertIsNone(self.view._carrier_worker)
        route.assert_not_called()

    def test_state_refresh_does_not_feed_synthetic_route_events(self):
        with unittest.mock.patch.object(self.view._ship_controller, 'handle_position') as position:
            self.update('A')
            self.update('B')
            position.assert_not_called()
            self.state.positionChanged.emit('B', 2, 'CarrierJump')
            position.assert_called_once_with('B', 2, 'CarrierJump')

    def test_handoff_preserves_manual_start(self):
        QTest.keyClicks(self.view.ship_start_system, 'Manual')
        self.update('Current')
        self.view.set_destination_system('Trader system')
        self.assertEqual(self.view.ship_start_system.text(), 'Manual')
        self.assertEqual(self.view.ship_current_system.text(), 'Current')
        self.assertEqual(self.view.ship_destination_system.text(), 'Trader system')
