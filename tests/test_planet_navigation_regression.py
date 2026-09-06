"""Small navigation regression checks for this ZIP, which omits upstream tests."""
import math
from types import SimpleNamespace
import unittest

from cmdrhelper.planet_geometry import relative_heading, solve
from cmdrhelper.ui.navigation_hud import hud_lines


class NavigationRegressionTests(unittest.TestCase):
    def test_east_course_and_quarter_circumference(self):
        solution = solve(0, 0, 0, 0, 90, 1000)
        self.assertAlmostEqual(solution.distance_m, math.pi * 500)
        self.assertAlmostEqual(solution.bearing, 90)
        self.assertAlmostEqual(solution.relative, 90)

    def test_dateline_uses_short_route(self):
        solution = solve(0, 179, 90, 0, -179, 1000)
        self.assertAlmostEqual(solution.distance_m, math.radians(2) * 1000)
        self.assertAlmostEqual(solution.bearing, 90)
        self.assertAlmostEqual(solution.relative, 0)

    def test_relative_heading_wraps(self):
        self.assertEqual(relative_heading(5, 355), 10)
        self.assertEqual(relative_heading(355, 5), -10)

    def test_valid_navigation_produces_three_hud_lines(self):
        state = SimpleNamespace(snapshot=object(), solution=solve(0, 0, 0, 0, 90, 1000))
        lines = hud_lines(state)
        self.assertEqual(len(lines), 3)
        self.assertTrue(all(isinstance(line, str) and line for line in lines))
        self.assertIn("090", lines[1])
        self.assertIn("km", lines[2])

    def test_missing_snapshot_or_solution_hides_lines(self):
        solution = solve(0, 0, 0, 0, 90, 1000)
        self.assertEqual(hud_lines(SimpleNamespace(snapshot=None, solution=solution)), ())
        self.assertEqual(hud_lines(SimpleNamespace(snapshot=object(), solution=None)), ())

    def test_same_position_has_no_directional_hud(self):
        solution = solve(0, 0, 0, 0, 0, 1000)
        self.assertEqual(solution.undefined_reason, "same_position")
        self.assertEqual(hud_lines(SimpleNamespace(snapshot=object(), solution=solution)), ())

    def test_invalid_radius_is_rejected(self):
        with self.assertRaises(ValueError):
            solve(0, 0, 0, 0, 90, 0)


if __name__ == "__main__":
    unittest.main()
