from dataclasses import replace
import json
import math
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter, QColor
from PySide6.QtWidgets import (QApplication, QLabel, QDialog, QComboBox, QLineEdit,
                              QDoubleSpinBox, QDialogButtonBox, QWidget, QMainWindow)

from cmdrhelper.planet_geometry import (heading360, relative_heading, solve,
                                      transform, unit_point, view_matrix)
from cmdrhelper.planet_navigation import PlanetNavigationController
from cmdrhelper.status_reader import StatusError, parse_status, read_status
from cmdrhelper.ui.planet_3d_widget import Planet3DWidget, grid_distances, grid_distance_y
from cmdrhelper.ui.planet_navigation_window import PlanetNavigationWindow, angle_text
from cmdrhelper.i18n import set_language


BASE = datetime(2026, 1, 1, tzinfo=timezone.utc)


def stamp(seconds):
    return (BASE + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def event(name, seconds, **values):
    return dict(timestamp=stamp(seconds), event=name, **values)


def status(seconds=10, **values):
    return dict(event("Status", seconds, Flags=(1 << 24) | (1 << 21), Flags2=0,
                      Latitude=10.0, Longitude=20.0, Heading=51,
                      PlanetRadius=1_000_000, BodyName="Test 1"), **{}) | values


class GeometryTests(unittest.TestCase):
    def test_player_fixed_for_positions_headings_and_poles(self):
        for lat, lon in ((0, 0), (30, 100), (-73, -179.99), (90, 150), (-90, -120)):
            for h in (0, 51, 180, -116, 359):
                with self.subTest(lat=lat, lon=lon, h=h):
                    anchor = transform(view_matrix(lat, lon, h), unit_point(lat, lon))
                    for actual, expected in zip(anchor, (0, 0, 1)):
                        self.assertAlmostEqual(actual, expected, places=12)

    def test_51_to_74_is_23_right_in_both_numbers_and_projection(self):
        # Destination 0.2 radians away at bearing 74 degrees from (0, 0).
        bearing, distance = math.radians(74), 0.2
        lat = math.degrees(math.asin(math.sin(distance) * math.cos(bearing)))
        lon = math.degrees(math.atan2(math.sin(bearing)*math.sin(distance), math.cos(distance)))
        result = solve(0, 0, 51, lat, lon, 1_000_000)
        self.assertAlmostEqual(result.bearing, 74)
        self.assertAlmostEqual(result.relative, 23)
        self.assertGreater(result.target_point[0], 0)
        self.assertGreater(result.target_point[1], 0)
        self.assertAlmostEqual(math.degrees(math.atan2(*result.target_point[:2])), 23)

    def test_heading_rotates_target_and_inverse_texture_coordinates(self):
        north = solve(0, 0, 0, 10, 0, 1_000_000)
        east = solve(0, 0, 90, 10, 0, 1_000_000)
        self.assertAlmostEqual(north.target_point[0], 0)
        self.assertGreater(north.target_point[1], 0)
        self.assertLess(east.target_point[0], 0)
        self.assertAlmostEqual(east.target_point[1], 0)
        for lat, lon, h in ((40, 100, 51), (-30, -130, -116)):
            matrix = view_matrix(lat, lon, h)
            world = unit_point(23, -51)
            projected = transform(matrix, world)
            inverse = tuple(sum(matrix[j][i]*projected[j] for j in range(3)) for i in range(3))
            for a, b in zip(inverse, world):
                self.assertAlmostEqual(a, b)

    def test_heading_normalization_and_wrap(self):
        self.assertEqual(heading360(-116), 244)
        self.assertEqual(relative_heading(1, 359), 2)
        self.assertEqual(relative_heading(359, 1), -2)
        self.assertEqual(relative_heading(180, 0), -180)
        self.assertEqual(angle_text(359.7), "000°")
        self.assertEqual(solve(0, 0, -116, 1, 1, 1000), solve(0, 0, 244, 1, 1, 1000))

    def test_dateline_short_path(self):
        result = solve(0, 179.9, 90, 0, -179.9, 1_000_000)
        self.assertAlmostEqual(result.distance_m, 1_000_000 * math.radians(.2), places=5)
        self.assertAlmostEqual(result.bearing, 90)
        self.assertAlmostEqual(result.relative, 0)

    def test_degenerate_positions(self):
        for args, reason in (((20, 30, 0, 20, 30), "same_position"),
                             ((0, 0, 0, 0, 180), "antipodal"),
                             ((90, 100, 20, 45, 0), "pole"),
                             ((-90, -100, 20, -45, 0), "pole")):
            result = solve(*args, 1_000_000)
            self.assertEqual(result.undefined_reason, reason)
            self.assertIsNone(result.bearing)
            self.assertIsNone(result.relative)
            self.assertEqual(result.arc, ())
            self.assertTrue(math.isfinite(result.distance_m))
        self.assertAlmostEqual(solve(0, 0, 0, 0, 180, 1000).distance_m, math.pi*1000)

    def test_far_side_is_distinct_from_behind_heading(self):
        behind = solve(0, 0, 0, -1, 0, 1000)
        far = solve(0, 0, 0, 0, 120, 1000)
        self.assertLess(behind.target_point[1], 0)
        self.assertGreater(behind.target_point[2], 0)
        self.assertLess(far.target_point[2], 0)
        self.assertTrue(any(p[2] >= 0 for p in far.arc))
        self.assertTrue(any(p[2] < 0 for p in far.arc))
        for p in far.arc:
            self.assertAlmostEqual(sum(v*v for v in p), 1)


class StatusTests(unittest.TestCase):
    def test_complete_status_negative_heading_and_zero_coordinates(self):
        s = parse_status(status(Latitude=0, Longitude=0, Heading=-116))
        self.assertEqual((s.latitude, s.longitude, s.heading), (0, 0, 244))

    def test_missing_and_invalid_fields_never_inherit(self):
        for field in ("Latitude", "Longitude", "Heading", "PlanetRadius", "BodyName", "timestamp", "Flags"):
            d = status()
            del d[field]
            with self.subTest(field=field), self.assertRaises(StatusError):
                parse_status(d)
        for changes in (dict(Latitude=91), dict(Longitude=-181), dict(PlanetRadius=0),
                        dict(Heading=float("nan")), dict(Latitude=True), dict(Heading="51"),
                        dict(Flags=True), dict(Flags2=-1), dict(BodyName=""),
                        dict(timestamp="2026-01-01T00:00:10")):
            with self.subTest(changes=changes), self.assertRaises(StatusError):
                parse_status(status(**changes))

    def test_haslatlong_and_hyperspace_override_existing_coordinates(self):
        for flags, code in ((1 << 24, "no_coordinates"), ((1 << 21) | (1 << 30), "hyperspace")):
            with self.assertRaises(StatusError) as cm:
                parse_status(status(Flags=flags))
            self.assertEqual(cm.exception.code, code)

    def test_file_reader_partial_duplicate_and_recovery(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "Status.json"
            for raw in ("", "{", '{"event":"Status","event":"Status"}', "null"):
                path.write_text(raw)
                with self.assertRaises(StatusError):
                    read_status(path)
            path.write_text(json.dumps(status()))
            self.assertEqual(read_status(path).body_name, "Test 1")
            original_stat = path.stat
            before = original_stat()
            after = SimpleNamespace(st_dev=before.st_dev, st_ino=before.st_ino,
                                    st_size=before.st_size, st_mtime_ns=before.st_mtime_ns + 1)
            with patch.object(Path, "stat", side_effect=[before, after]), self.assertRaises(StatusError):
                read_status(path)


class _Settings:
    def __init__(self):
        self.values = {}

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value

    def sync(self):
        pass


class NavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.journal = self.folder / "Journal.2026-01-01T000000.01.log"
        self.status_path = self.folder / "Status.json"
        self.app_state = SimpleNamespace(journal_folder=self.folder, commander_fid="F-A",
                                         system_address=42, system_bodies=[], viewed_commander_id=99)
        self.append(event("Fileheader", 0), event("Commander", 1, FID="F-A"),
                    event("LoadGame", 2, FID="F-A"), self.location("Location", 3))
        self.write_status()
        self.controller = PlanetNavigationController(self.app_state)
        self.addCleanup(self.controller.deleteLater)
        self.controller.poll()

    def location(self, name, seconds, **values):
        return event(name, seconds, **(dict(SystemAddress=42, BodyID=1, Body="Test 1", BodyType="Planet") | values))

    def append(self, *events):
        with self.journal.open("a") as f:
            for e in events:
                f.write(json.dumps(e) + "\n")

    def write_status(self, seconds=10, **values):
        self.status_path.write_text(json.dumps(status(seconds, **values)))

    def start_target(self):
        self.controller.set_target(11, 21)
        self.assertIsNotNone(self.controller.state.solution)

    def test_marker_circles_size_depth_colors_and_overlay_order(self):
        widget = Planet3DWidget(None, diameter=100, navigation=True)
        self.addCleanup(widget.deleteLater)
        cases = [
            ("front", (20, 35), "#ff9f1c"),
            ("behind_heading_but_front_hemisphere", (-20, 0), "#ff9f1c"),
            ("rear_hemisphere", (0, 120), "#ff5252"),
            ("same_position", (0, 0), "#ff9f1c"),
        ]
        for name, destination, color in cases:
            with self.subTest(case=name):
                solution = solve(0, 0, 0, *destination, 1000)
                if name == "behind_heading_but_front_hemisphere":
                    self.assertEqual(solution.relative, -180)
                    self.assertGreater(solution.target_point[2], 0)
                widget.set_navigation_solution(solution)
                image = QImage(100, 100, QImage.Format_ARGB32)
                image.fill(QColor("#101010"))
                painter = QPainter(image)
                widget._paint_navigation(painter, 0, 0)
                painter.end()
                # Fixed player circle extends in all four directions.
                for x, y in ((42, 50), (58, 50), (50, 42), (50, 58)):
                    self.assertEqual(image.pixelColor(x, y).name(), "#ffffff")
                if name != "same_position":
                    self.assertEqual(image.pixelColor(50, 50).name(), "#14202b")
                x = round(50 + 50 * solution.target_point[0])
                y = round(50 - 50 * solution.target_point[1])
                # Actual rendered center has the depth color, even over a route
                # or relative-direction arrow. No star is drawn.
                self.assertEqual(image.pixelColor(x, y).name(), color)
                pixels = [(px, py) for px in range(100) for py in range(100)
                          if image.pixelColor(px, py).name() == color]
                self.assertLess(max(px for px, _ in pixels) - min(px for px, _ in pixels), 16)
                self.assertLess(max(py for _, py in pixels) - min(py for _, py in pixels), 16)
                self.assertIs(widget._navigation_solution, solution)
                self.assertEqual(solution, solve(0, 0, 0, *destination, 1000))

    def test_binding_uses_active_journal_not_viewed_commander(self):
        self.start_target()
        target = self.controller.target
        self.assertEqual(target.binding.fid, "F-A")
        self.assertEqual(target.binding.system_address, 42)
        self.assertEqual(target.binding.body_id, 1)
        with self.assertRaises(AttributeError):
            target.latitude = 99
        self.app_state.viewed_commander_id = 123
        self.controller.poll()
        self.assertEqual(self.controller.target, target)

    def test_first_planetary_supercruise_snapshot_activates_all_pilot_displays(self):
        self.start_target()
        target = self.controller.target
        window = PlanetNavigationWindow(self.controller, _Settings())
        self.addCleanup(window.deleteLater)
        self.append(self.location("LeaveBody", 20))
        self.status_path.write_text(json.dumps(event("Status", 21, Flags=1 << 4, Flags2=0)))
        self.controller.poll()
        self.assertIsNone(self.controller.state.solution)
        self.assertIsNone(window.globe._navigation_solution)

        # ApproachBody confirms the planet while the ship is still in SC.
        self.append(self.location("ApproachBody", 22))
        self.controller.poll()
        self.assertIsNone(self.controller.state.solution)
        self.write_status(23, Flags=(1 << 4) | (1 << 21) | (1 << 24))
        self.controller.poll()
        self.assertEqual(self.controller.target, target)
        self.assertEqual(self.controller.state.reason, "")
        self.assertIsNotNone(window.globe._navigation_solution)
        for key in ("current_coords", "target_coords", "bearing", "heading", "relative", "distance"):
            self.assertNotEqual(window.values[key].text(), "–")
        self.assertIn("°", window.target_course_label.text())
        self.assertNotIn("–", window.target_distance_label.text())

        # Clearing the target still permits immediate manual entry in SC.
        self.controller.stop_target()
        self.assertTrue(window.input_button.isEnabled())
        self.start_target()
        self.assertIsNotNone(window.globe._navigation_solution)

    def test_planetary_navigation_continues_across_flight_and_vehicle_phases(self):
        self.start_target()
        target = self.controller.target
        phases = [
            ("planetary_supercruise", 30, (1 << 4) | (1 << 24), 0, None),
            ("glide", 40, 1 << 24, 1 << 12, "SupercruiseExit"),
            ("normal_flight", 50, 1 << 24, 0, None),
            ("landed", 60, (1 << 24) | (1 << 1), 0, "Touchdown"),
            ("srv", 70, 1 << 26, 0, "LaunchSRV"),
            ("on_foot", 80, 0, (1 << 0) | (1 << 4), "Disembark"),
        ]
        for name, seconds, flags, flags2, journal_event in phases:
            with self.subTest(phase=name):
                if journal_event:
                    self.append(self.location(journal_event, seconds, OnPlanet=True))
                self.write_status(seconds + 1, Flags=flags | (1 << 21), Flags2=flags2)
                self.controller.poll()
                self.assertEqual(self.controller.target, target)
                self.assertEqual(self.controller.state.reason, "")
                self.assertIsNotNone(self.controller.state.solution)

    def test_supercruise_does_not_relax_hyperspace_or_telemetry_validation(self):
        self.start_target()
        sc_flags = (1 << 4) | (1 << 21) | (1 << 24)
        for field in ("Latitude", "Longitude", "Heading", "PlanetRadius", "BodyName"):
            with self.subTest(missing=field):
                payload = status(20, Flags=sc_flags)
                del payload[field]
                self.status_path.write_text(json.dumps(payload))
                self.controller.poll()
                self.assertIsNone(self.controller.state.solution)
        self.write_status(21, Flags=sc_flags)
        self.controller.poll()
        self.assertIsNotNone(self.controller.state.solution)
        self.write_status(22, Flags=sc_flags | (1 << 30))
        self.controller.poll()
        self.assertEqual(self.controller.state.reason, "waiting_planetary_position")
        self.assertIsNone(self.controller.state.solution)

    def test_missing_flags_and_partial_status_clear_all_live_fields(self):
        self.start_target()
        for raw in (json.dumps(status(20, Flags=0)), "{", json.dumps(event("Status", 21, Flags=0))):
            self.status_path.write_text(raw)
            self.controller.poll()
            self.assertIsNone(self.controller.state.snapshot)
            self.assertIsNone(self.controller.state.solution)
        self.write_status(22, Heading=-116)
        self.controller.poll()
        self.assertEqual(self.controller.state.snapshot.heading, 244)

    def test_unoccupied_ship_touchdown_is_not_player_location(self):
        self.start_target()
        self.append(self.location("Touchdown", 20, Body="Other 2", BodyID=2, PlayerControlled=False))
        self.controller.poll()
        self.assertIsNotNone(self.controller.state.solution)

    def test_widget_and_window_focus_rendering_pause_and_geometry(self):
        set_language("de")
        settings = _Settings()
        window = PlanetNavigationWindow(self.controller, settings)
        self.addCleanup(window.deleteLater)
        with patch.object(window, "raise_", side_effect=AssertionError("focus")), \
             patch.object(window, "activateWindow", side_effect=AssertionError("focus")), \
             patch.object(window, "setFocus", side_effect=AssertionError("focus")):
            window.show()
            self.assertTrue(window.testAttribute(Qt.WA_ShowWithoutActivating))
            self.assertFalse(window.windowFlags() & Qt.WindowDoesNotAcceptFocus)
            self.assertFalse(window.windowFlags() & Qt.WindowTransparentForInput)
            self.assertFalse(window.globe._timer.isActive())
            self.start_target()
            first = window.globe._frame.copy()
            self.write_status(11, Heading=141)
            self.controller.poll()
            self.assertNotEqual(first, window.globe._frame)
            frame = window.globe._frame.copy()
            window.globe._advance_rotation()
            self.assertEqual(frame, window.globe._frame)
            self.assertIsNotNone(window.globe._navigation_solution)
            # Exercise far-side and degenerate overlays through the actual painter.
            for target in ((-10, -160), (0, 140), (10, 20)):
                window.globe.set_navigation_solution(solve(10, 20, 51, *target, 1_000_000))
                window.grab()
            self.status_path.write_text("{")
            self.controller.poll()
            self.assertIsNone(window.globe._navigation_solution)
            self.assertEqual(window.values["current_coords"].text(), "–")
            self.assertEqual(window.values["bearing"].text(), "–")
            window.close()
            self.assertIn("planet_navigation/geometry", settings.values)
            window.show()
            self.controller.poll()
            window.close()

    def test_navigation_layout_resizes_graphic_before_clipping_details(self):
        set_language("de")
        self.write_status(10, Latitude=0, Longitude=0, Heading=0)
        self.controller.poll()
        parent = QMainWindow()
        self.addCleanup(parent.deleteLater)
        parent.setMinimumSize(320, 240)
        parent_minimum = parent.minimumSize()
        settings = _Settings()
        window = PlanetNavigationWindow(self.controller, settings, parent)
        self.addCleanup(window.deleteLater)
        self.addCleanup(window.close)
        window.show()
        sides = []
        for width, height in ((360, 500), (900, 1000), (1400, 620), (450, 1400), (360, 500)):
            window.resize(width, height)
            self.app.processEvents()
            for distance_m in (20_000, 358_400, 380_000, 380_001, 500_000):
                with self.subTest(size=(width, height), distance=distance_m):
                    self.controller.set_target(0, math.degrees(distance_m / 1_000_000), "Test 1")
                    self.app.processEvents()
                    expected_mode = "grid" if distance_m <= 380_000 else "globe"
                    self.assertEqual(window.globe.navigation_display_mode, expected_mode)
                    for label in window.findChildren(QLabel):
                        # Includes headings, wrapped explanations and every detail value.
                        self.assertGreaterEqual(label.height(), label.minimumSizeHint().height())
                        if label.hasHeightForWidth():
                            self.assertGreaterEqual(label.height(), label.heightForWidth(label.width()))
                        self.assertGreaterEqual(label.width(), label.minimumSizeHint().width())
                        self.assertTrue(window.rect().contains(label.geometry()))
                        self.assertFalse(label.geometry().intersects(window.globe.geometry()))
                    for label in window.values.values():
                        self.assertNotEqual(label.text(), "–")
                    self.assertIn("Zielentfernung:", window.target_distance_label.text())
                    self.assertIn("Zielkurs:", window.target_course_label.text())
            sides.append(min(window.globe.width(), window.globe.height()))
            self.assertEqual(parent.minimumSize(), parent_minimum)
        self.assertLess(sides[0], 284)
        self.assertGreater(sides[1], 284)
        self.assertGreater(sides[3], sides[0])
        self.assertEqual(sides[0], sides[-1])
        window.move(40, 50)
        self.app.processEvents()
        geometry = window.geometry()
        window.close()
        restored = PlanetNavigationWindow(self.controller, settings, parent)
        self.addCleanup(restored.deleteLater)
        self.addCleanup(restored.close)
        restored.show()
        self.app.processEvents()
        self.assertEqual(restored.geometry(), geometry)

    def test_resize_preserves_round_globe_grid_perspective_and_marker_positions(self):
        widget = Planet3DWidget(None, diameter=260, navigation=True)
        self.addCleanup(widget.deleteLater)
        self.addCleanup(widget.close)
        widget.show()
        # A target east of heading puts both markers well apart in either mode.
        for distance in (380_001, 380_000, 145_000, 500_000):
            self.controller.set_target(10, 20 + math.degrees(distance / 1_000_000), "Test 1")
            solution = replace(self.controller.state.solution, distance_m=distance)
            widget.set_navigation_solution(solution)
            expected_mode = "grid" if distance <= 380_000 else "globe"
            frame = widget._frame
            for width, height in ((142, 142), (568, 568), (900, 284), (284, 900)):
                with self.subTest(size=(width, height), mode=expected_mode):
                    widget.resize(width, height)
                    self.app.processEvents()
                    image = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
                    image.fill(Qt.transparent)
                    widget.render(image, renderFlags=QWidget.DrawChildren)
                    # Rendered outline has equal horizontal/vertical diameters in
                    # wide and tall widgets as well as at half/double scale.
                    xs = [x for x in range(width) if image.pixelColor(x, height // 2).alpha() > 128]
                    ys = [y for y in range(height) if image.pixelColor(width // 2, y).alpha() > 128]
                    self.assertAlmostEqual(max(xs) - min(xs), max(ys) - min(ys), delta=2)
                    self.assertAlmostEqual((max(xs) + min(xs)) / 2, (width - 1) / 2, delta=1)
                    self.assertAlmostEqual((max(ys) + min(ys)) / 2, (height - 1) / 2, delta=1)
                    scale = min(width, height) / 284
                    size = 260 * scale
                    left, top = (width - size) / 2, (height - size) / 2
                    if expected_mode == "globe":
                        target_x = left + size / 2 * (1 + solution.target_point[0])
                        target_y = top + size / 2 * (1 - solution.target_point[1])
                        player_y = height / 2
                    else:
                        # Independent perspective expectation from distance and direction.
                        d = distance / 400_000
                        angle = math.radians(solution.relative)
                        lateral, forward = d * math.sin(angle), d * math.cos(angle)
                        target_x = left + size * (.5 + .46 * lateral / (1 + abs(lateral))
                                                   / (1 + max(0, forward)))
                        target_y = top + size * (.12 + .72 / (1 + d))
                        player_y = top + size * .84
                    target_pixels = [image.pixelColor(x, y)
                                     for x in range(round(target_x) - 1, round(target_x) + 2)
                                     for y in range(round(target_y) - 1, round(target_y) + 2)]
                    # Subpixel marker edges are antialiased at half size.
                    self.assertTrue(any(c.red() > 230 and 130 < c.green() < 175 and c.blue() < 50
                                        for c in target_pixels))
                    # The white position circle scales with the same factor.
                    ring_x = round(width / 2 + 8 * scale)
                    near_ring = [image.pixelColor(x, y) for x in range(ring_x - 1, ring_x + 2)
                                 for y in range(round(player_y) - 1, round(player_y) + 2)]
                    self.assertTrue(any(c.red() > 220 and c.green() > 220 and c.blue() > 220 for c in near_ring))
                    self.assertIs(widget._navigation_solution, solution)
                    self.assertIs(widget._frame, frame)
                    self.assertEqual(widget.navigation_display_mode, expected_mode)

    def test_display_threshold_is_inclusive_and_has_no_history(self):
        widget = Planet3DWidget(None, diameter=260, navigation=True)
        self.addCleanup(widget.deleteLater)
        solution = solve(0, 0, 0, 1, 1, 1_000_000)
        # Both directions, exact boundaries and the observed 358.4-km case.
        for distance in (500_000, 381_000, 380_000, 358_400, 145_000, 20_000,
                         380_000, 381_000, 380_000.001, 380_000, 379_999.999):
            with self.subTest(distance=distance):
                current = replace(solution, distance_m=distance)
                widget.set_navigation_solution(current)
                self.assertIs(widget._navigation_solution, current)
                self.assertEqual(widget.navigation_display_mode,
                                 "grid" if distance <= 380_000 else "globe")
        widget.set_navigation_solution(None)
        self.assertIsNone(widget._navigation_solution)
        widget.set_navigation_solution(replace(solution, distance_m=358_400))
        self.assertEqual(widget.navigation_display_mode, "grid")
        self.assertEqual(list(grid_distances(358_400)), list(range(50_000, 400_001, 50_000)))
        self.assertGreater(grid_distance_y(50_000), grid_distance_y(100_000))

    def test_navigator_works_without_hud_or_hud_controls(self):
        self.start_target()
        window = PlanetNavigationWindow(self.controller, _Settings())
        self.addCleanup(window.deleteLater)
        before = self.controller.state
        with patch("cmdrhelper.ui.navigation_hud.NavigationHud", side_effect=AssertionError):
            window.show()
            self.assertFalse(hasattr(window, "hud_button"))
            self.assertFalse(hasattr(window, "hud_status"))
            self.assertIs(window.globe._navigation_solution, before.solution)
            window.close()
            self.assertEqual(self.controller.state, before)

    def test_coordinates_appear_disappear_and_return_without_events(self):
        self.status_path.write_text(json.dumps(event("Status", 11, Flags=0)))
        self.controller.set_target(32, 15, "Test 1")
        self.assertEqual(self.controller.state.reason, "waiting_planetary_position")
        for has_coordinates in (True, False, True):
            self.write_status(12, Flags=(1 << 21) if has_coordinates else 0)
            self.controller.poll()
            self.assertEqual(self.controller.state.solution is not None, has_coordinates)
            if not has_coordinates:
                self.assertIsNone(self.controller.state.snapshot)
                self.assertEqual(self.controller.state.reason, "waiting_planetary_position")

    def test_historical_events_never_block_current_snapshot(self):
        self.start_target()
        for name, values in (("LeaveBody", {}), ("StartJump", {"JumpType": "Hyperspace"}),
                             ("StartJump", {"JumpType": "Supercruise"}),
                             ("FSDJump", {"SystemAddress": 999}),
                             ("SupercruiseEntry", {}), ("ApproachBody", {"Body": "Other"}),
                             ("Shutdown", {}), ("LoadGame", {"FID": "Other"})):
            with self.subTest(event=name, values=values):
                self.append(event(name, 100, **values))
                self.controller.poll()
                self.assertIsNotNone(self.controller.state.solution)

    def test_hyperspace_is_only_a_current_snapshot_property(self):
        self.start_target()
        self.write_status(20, Flags=(1 << 21) | (1 << 30))
        self.controller.poll()
        self.assertIsNone(self.controller.state.solution)
        self.assertEqual(self.controller.state.reason, "waiting_planetary_position")
        self.write_status(21)
        self.controller.poll()
        self.assertIsNotNone(self.controller.state.solution)

    def test_body_mismatch_waits_then_immediately_recovers(self):
        self.start_target()
        self.write_status(20, BodyName="Other 1")
        self.controller.poll()
        self.assertIsNone(self.controller.state.solution)
        self.assertEqual(self.controller.state.reason, "waiting_planetary_position")
        self.write_status(21)
        self.controller.poll()
        self.assertIsNotNone(self.controller.state.solution)

    def test_multiple_targets_and_stop_on_same_snapshot(self):
        for lat, lon in ((32, 15), (-10, 40), (0, 0)):
            self.controller.set_target(lat, lon)
            self.assertEqual(self.controller.state.solution, solve(10, 20, 51, lat, lon, 1_000_000))
            self.controller.stop_target()
            self.assertIsNone(self.controller.target)
            self.assertIsNone(self.controller.state.solution)

    def test_restart_at_planet_without_approach_or_technical_ids(self):
        self.journal.write_text(json.dumps(event("Location", 1, StarSystem="Test",
                                                Body="Test 1", BodyType="Planet")) + "\n")
        controller = PlanetNavigationController(SimpleNamespace(journal_folder=self.folder))
        self.addCleanup(controller.deleteLater)
        controller.poll()
        self.assertEqual(controller.current_body.body_name, "Test 1")
        controller.set_target(32, 15)
        self.assertIsNotNone(controller.state.solution)
        self.assertIsNone(controller.target.binding.body_id)
        self.assertIsNone(controller.target.binding.system_address)

    def test_missing_or_incomplete_journal_does_not_veto_status(self):
        for raw in (None, "{", "null\n"):
            if raw is None:
                self.journal.unlink()
            else:
                self.journal.write_text(raw)
            self.controller.set_target(32, 15, "Test 1")
            self.assertIsNotNone(self.controller.state.solution)

    def test_body_name_target_without_status_or_ids(self):
        self.status_path.unlink()
        self.controller.set_target(32, 15, "Destination 2", "Site")
        self.assertIsNone(self.controller.state.solution)
        self.assertIsNone(self.controller.target.binding.body_id)
        self.write_status(20, BodyName="Destination 2")
        self.controller.poll()
        self.assertIsNotNone(self.controller.state.solution)
        for lat, lon, body in ((91, 0, "Test 1"), (0, 181, "Test 1"), (0, 0, ""),
                               (True, 0, "Test 1"), (float("nan"), 0, "Test 1")):
            with self.assertRaises(ValueError):
                self.controller.set_target(lat, lon, body)

    def test_dialog_only_needs_body_name_and_coordinates(self):
        window = PlanetNavigationWindow(self.controller, _Settings())
        self.addCleanup(window.deleteLater)
        def enter(dialog):
            selector = dialog.findChild(QComboBox)
            self.assertTrue(selector.isEditable())
            self.assertEqual(selector.currentText(), "Test 1")
            labels = [label.text() for label in dialog.findChildren(QLabel)]
            self.assertNotIn("BodyID", labels)
            self.assertNotIn("SystemAddress", labels)
            name = [field for field in dialog.findChildren(QLineEdit)
                    if field.parent() == dialog][0]
            name.setText("Site")
            lat, lon = dialog.findChildren(QDoubleSpinBox)
            lat.setValue(32)
            lon.setValue(15)
            dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.Ok).click()
            return QDialog.Accepted
        with patch.object(QDialog, "exec", enter):
            window._enter_target()
        self.assertEqual(self.controller.target.name, "Site")
        self.assertIsNotNone(self.controller.state.solution)

    def test_short_body_name_resolves_when_current_system_confirms_it(self):
        self.status_path.unlink()
        self.append(event("Location", 20, StarSystem="Test", SystemAddress=42))
        self.controller.set_target(32, 15, "1")
        self.write_status(21)
        self.controller.poll()
        self.assertIsNotNone(self.controller.state.solution)
        self.assertEqual(self.controller.target.binding.body_name, "Test 1")

    def test_optional_ids_completed_without_reauthorizing_target(self):
        self.controller.set_target(32, 15, "New 2")
        self.assertIsNone(self.controller.target.binding.body_id)
        self.append(event("Location", 20, StarSystem="New", SystemAddress=77,
                          Body="New 2", BodyID=2, BodyType="Planet"))
        self.write_status(21, BodyName="New 2")
        self.controller.poll()
        self.assertIsNotNone(self.controller.state.solution)
        self.assertEqual(self.controller.target.binding.body_id, 2)
        self.assertEqual(self.controller.target.binding.system_address, 77)

    def test_manual_dialog_without_status_or_known_body(self):
        self.status_path.unlink()
        self.journal.unlink()
        self.controller = PlanetNavigationController(SimpleNamespace(journal_folder=self.folder))
        self.addCleanup(self.controller.deleteLater)
        window = PlanetNavigationWindow(self.controller, _Settings())
        self.addCleanup(window.deleteLater)
        def enter(dialog):
            dialog.findChild(QComboBox).setCurrentText("Destination 2")
            lat, lon = dialog.findChildren(QDoubleSpinBox)
            lat.setValue(32)
            lon.setValue(15)
            dialog.findChild(QDialogButtonBox).button(QDialogButtonBox.Ok).click()
            return QDialog.Accepted
        with patch.object(QDialog, "exec", enter):
            window._enter_target()
        self.assertIsNotNone(self.controller.target)
        self.assertEqual(self.controller.state.reason, "waiting_planetary_position")
        self.write_status(20, BodyName="Destination 2")
        self.controller.poll()
        self.assertIsNotNone(self.controller.state.solution)


if __name__ == "__main__":
    unittest.main()
