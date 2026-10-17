from __future__ import annotations

from statistics import median

from shapely.geometry import LineString, Point

from videos_rodoviarios.core.models import GeometryEntity, OffsetInfo


def line_length(entity: GeometryEntity) -> float:
    if len(entity.points) < 2:
        return 0.0
    return float(LineString(entity.points).length)


def _side_at(center: LineString, point: Point) -> float:
    d = center.project(point)
    eps = max(min(center.length * 1e-5, 1.0), 0.01)
    p0 = center.interpolate(max(0.0, d - eps))
    p1 = center.interpolate(min(center.length, d + eps))
    pc = center.interpolate(d)
    tx, ty = p1.x - p0.x, p1.y - p0.y
    vx, vy = point.x - pc.x, point.y - pc.y
    return tx * vy - ty * vx


def offset_info(entity: GeometryEntity, centerline: GeometryEntity) -> OffsetInfo:
    line = LineString(entity.points)
    center = LineString(centerline.points)
    n = max(2, min(31, int(line.length / 10.0) + 2))
    distances: list[float] = []
    sides: list[float] = []
    for i in range(n):
        p = line.interpolate(line.length * i / (n - 1)) if line.length else Point(entity.points[0])
        distances.append(float(center.distance(p)))
        sides.append(_side_at(center, p))
    left = sum(1 for s in sides if s > 1e-9)
    right = sum(1 for s in sides if s < -1e-9)
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
        length_m=round(float(line.length), 3),
    )
