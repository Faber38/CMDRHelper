"""Pure spherical navigation; geographic convention matches Planet3DWidget."""
from dataclasses import dataclass
import math


def heading360(value):
    return value % 360.0


def relative_heading(bearing, heading):
    return (bearing - heading + 180.0) % 360.0 - 180.0


def unit_point(latitude, longitude):
    p, l = math.radians(latitude), math.radians(longitude)
    return (math.cos(p) * math.sin(l), math.sin(p), math.cos(p) * math.cos(l))


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def view_matrix(latitude, longitude, heading):
    p, l, h = map(math.radians, (latitude, longitude, heading360(heading)))
    east = (math.cos(l), 0.0, -math.sin(l))
    north = (-math.sin(p) * math.sin(l), math.cos(p), -math.sin(p) * math.cos(l))
    right = tuple(math.cos(h) * e - math.sin(h) * n for e, n in zip(east, north))
    forward = tuple(math.sin(h) * e + math.cos(h) * n for e, n in zip(east, north))
    return (right, forward, unit_point(latitude, longitude))


def transform(matrix, point):
    return tuple(dot(row, point) for row in matrix)


@dataclass(frozen=True)
class SurfaceSolution:
    distance_m: float
    bearing: float | None
    relative: float | None
    undefined_reason: str
    matrix: tuple
    target_point: tuple
    arc: tuple


def solve(latitude, longitude, heading, target_latitude, target_longitude, radius):
    values = (latitude, longitude, heading, target_latitude, target_longitude, radius)
    if not all(math.isfinite(v) for v in values) or radius <= 0:
        raise ValueError("Non-finite coordinates or invalid radius")
    if not (-90 <= latitude <= 90 and -90 <= target_latitude <= 90
            and -180 <= longitude <= 180 and -180 <= target_longitude <= 180):
        raise ValueError("Coordinates out of range")
    p, p2 = map(math.radians, (latitude, target_latitude))
    dl = math.radians((target_longitude - longitude + 180) % 360 - 180)
    a = math.sin((p2 - p) / 2) ** 2 + math.cos(p) * math.cos(p2) * math.sin(dl / 2) ** 2
    a = min(1.0, max(0.0, a))
    angle = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    start = unit_point(latitude, longitude)
    target = unit_point(target_latitude, target_longitude)
    # atan2 of the cross-product norm retains precision near antipodes.
    cross = (start[1]*target[2] - start[2]*target[1],
             start[2]*target[0] - start[0]*target[2],
             start[0]*target[1] - start[1]*target[0])
    sin_angle = math.sqrt(dot(cross, cross))
    if a > 0.99:
        angle = math.atan2(sin_angle, dot(start, target))
    reason = ""
    if angle < 1e-10:
        reason = "same_position"
    elif math.pi - angle < 1e-7:
        reason = "antipodal"
    elif abs(math.cos(p)) < 1e-8:
        reason = "pole"
    bearing = relative = None
    if not reason:
        y = math.sin(dl) * math.cos(p2)
        x = math.cos(p)*math.sin(p2) - math.sin(p)*math.cos(p2)*math.cos(dl)
        bearing = heading360(math.degrees(math.atan2(y, x)))
        relative = relative_heading(bearing, heading360(heading))
    matrix = view_matrix(latitude, longitude, heading)
    arc = []
    if not reason:
        steps = max(2, math.ceil(angle / math.radians(2)))
        for i in range(steps + 1):
            t = i / steps
            v = tuple((math.sin((1-t)*angle)*s + math.sin(t*angle)*e) / sin_angle
                      for s, e in zip(start, target))
            arc.append(transform(matrix, v))
    return SurfaceSolution(radius * angle, bearing, relative, reason,
                           matrix, transform(matrix, target), tuple(arc))
