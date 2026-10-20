from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot

from videos_rodoviarios.core.models import GeometryEntity

Point = tuple[float, float]


@dataclass(slots=True)
class FlowSegment:
    entity_handle: str
    start: Point
    end: Point
    forward: bool
    source: str = "arrow"


@dataclass(slots=True)
class TrafficFlowModel:
    segments: list[FlowSegment] = field(default_factory=list)

    def set_segment_direction(self, segment: FlowSegment) -> None:
        """Insert or replace the direction of one geometrical road segment."""
        key = _segment_key(segment.entity_handle, segment.start, segment.end)
        self.segments = [
            item
            for item in self.segments
            if _segment_key(item.entity_handle, item.start, item.end) != key
        ]
        self.segments.append(segment)

    def direction_for(self, entity_handle: str, start: Point, end: Point) -> bool | None:
        key = _segment_key(entity_handle, start, end)
        for item in self.segments:
            if _segment_key(item.entity_handle, item.start, item.end) == key:
                return item.forward
        return None


def _segment_key(handle: str, start: Point, end: Point) -> tuple[str, tuple[Point, Point]]:
    a = (round(start[0], 6), round(start[1], 6))
    b = (round(end[0], 6), round(end[1], 6))
    return handle, tuple(sorted((a, b)))  # type: ignore[return-value]


def _project_point_to_segment(point: Point, start: Point, end: Point) -> tuple[Point, float, float]:
    vx = end[0] - start[0]
    vy = end[1] - start[1]
    length2 = vx * vx + vy * vy
    if length2 <= 1e-12:
        return start, 0.0, hypot(point[0] - start[0], point[1] - start[1])
    t = ((point[0] - start[0]) * vx + (point[1] - start[1]) * vy) / length2
    t = max(0.0, min(1.0, t))
    projected = (start[0] + t * vx, start[1] + t * vy)
    distance = hypot(point[0] - projected[0], point[1] - projected[1])
    return projected, t, distance


def nearest_road_segment(
    point: Point,
    entities: list[GeometryEntity],
    *,
    tolerance_m: float = 8.0,
) -> tuple[GeometryEntity, int, Point, Point] | None:
    """Return nearest linear entity segment for a pavement-arrow insertion point."""
    best: tuple[float, GeometryEntity, int, Point, Point] | None = None
    for entity in entities:
        if len(entity.points) < 2:
            continue
        if entity.category not in {"center", "edge", "other", "marking"}:
            continue
        for index, (start, end) in enumerate(zip(entity.points, entity.points[1:])):
            _, _, distance = _project_point_to_segment(point, start, end)
            if distance > tolerance_m:
                continue
            if best is None or distance < best[0]:
                best = (distance, entity, index, start, end)
    if best is None:
        return None
    _, entity, index, start, end = best
    return entity, index, start, end


def flow_from_arrow(
    insertion: Point,
    direction_point: Point,
    entities: list[GeometryEntity],
    *,
    tolerance_m: float = 8.0,
) -> FlowSegment:
    """Create a directional traffic segment from one pavement arrow.

    The arrow is snapped to the nearest road-like segment. Its indicated direction is
    compared with the segment's own point order; this yields a stable forward/reverse
    flag used later by vehicle routing and preview rendering.
    """
    nearest = nearest_road_segment(insertion, entities, tolerance_m=tolerance_m)
    if nearest is None:
        raise ValueError("Nenhum segmento de via foi encontrado próximo da seta.")

    entity, _, start, end = nearest
    sx = end[0] - start[0]
    sy = end[1] - start[1]
    ax = direction_point[0] - insertion[0]
    ay = direction_point[1] - insertion[1]
    if hypot(ax, ay) <= 1e-9:
        raise ValueError("O sentido da seta precisa ser indicado com um segundo ponto.")

    forward = sx * ax + sy * ay >= 0.0
    return FlowSegment(
        entity_handle=entity.handle,
        start=start,
        end=end,
        forward=forward,
    )
