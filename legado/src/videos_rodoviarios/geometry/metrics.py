from __future__ import annotations

from math import hypot
from statistics import median

from videos_rodoviarios.core.models import GeometryEntity, OffsetInfo

Point = tuple[float, float]


def _segment_length(a: Point, b: Point) -> float:
    return hypot(b[0] - a[0], b[1] - a[1])


def _polyline_length(points: list[Point]) -> float:
    return sum(_segment_length(a, b) for a, b in zip(points[:-1], points[1:]))


def line_length(entity: GeometryEntity) -> float:
    if len(entity.points) < 2:
        return 0.0
    return float(_polyline_length(entity.points))


def _nearest_on_segment(p: Point, a: Point, b: Point) -> tuple[Point, float]:
    vx, vy = b[0] - a[0], b[1] - a[1]
    wx, wy = p[0] - a[0], p[1] - a[1]
    denom = vx * vx + vy * vy
    if denom <= 1e-18:
        return a, 0.0
    t = max(0.0, min(1.0, (wx * vx + wy * vy) / denom))
    return (a[0] + t * vx, a[1] + t * vy), t


def _distance_and_side_to_polyline(p: Point, center: list[Point]) -> tuple[float, float]:
    best_dist = float("inf")
    best_side = 0.0
    for a, b in zip(center[:-1], center[1:]):
        nearest, _ = _nearest_on_segment(p, a, b)
        dx, dy = p[0] - nearest[0], p[1] - nearest[1]
        dist = hypot(dx, dy)
        if dist < best_dist:
            best_dist = dist
            tx, ty = b[0] - a[0], b[1] - a[1]
            best_side = tx * dy - ty * dx
    if best_dist == float("inf"):
        return 0.0, 0.0
    return best_dist, best_side


def _point_at_distance(points: list[Point], distance: float) -> Point:
    if not points:
        return (0.0, 0.0)
    if len(points) == 1:
        return points[0]
    remaining = max(0.0, distance)
    for a, b in zip(points[:-1], points[1:]):
        seg = _segment_length(a, b)
        if seg <= 1e-18:
            continue
        if remaining <= seg:
            t = remaining / seg
            return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        remaining -= seg
    return points[-1]


def offset_info(entity: GeometryEntity, centerline: GeometryEntity) -> OffsetInfo:
    line_points = entity.points
    center_points = centerline.points
    if len(line_points) < 2:
        raise ValueError("Offset sem geometria suficiente.")
    if len(center_points) < 2:
        raise ValueError("Eixo sem geometria suficiente para calcular offsets.")

    length = _polyline_length(line_points)
    n = max(2, min(31, int(length / 10.0) + 2))
    distances: list[float] = []
    sides: list[float] = []
    for i in range(n):
        p = _point_at_distance(line_points, length * i / (n - 1)) if length > 0 else line_points[0]
        dist, side_value = _distance_and_side_to_polyline(p, center_points)
        distances.append(dist)
        sides.append(side_value)

    left = sum(1 for value in sides if value > 1e-9)
    right = sum(1 for value in sides if value < -1e-9)
    if left > right:
        side = "left"
    elif right > left:
        side = "right"
    else:
        side = "crossing/center"

    return OffsetInfo(
        handle=entity.handle,
        layer=entity.layer,
        category=entity.category,
        side=side,
        min_m=round(min(distances), 3),
        median_m=round(float(median(distances)), 3),
        max_m=round(max(distances), 3),
        length_m=round(float(length), 3),
    )
