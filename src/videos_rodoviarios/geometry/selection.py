from __future__ import annotations

from dataclasses import dataclass
from math import hypot

from videos_rodoviarios.core.models import GeometryEntity, Point


@dataclass(slots=True)
class SelectionHit:
    entity: GeometryEntity
    distance: float
    nearest_point: Point
    segment_index: int


def _nearest_on_segment(p: Point, a: Point, b: Point) -> tuple[Point, float]:
    vx, vy = b[0] - a[0], b[1] - a[1]
    wx, wy = p[0] - a[0], p[1] - a[1]
    denom = vx * vx + vy * vy
    if denom <= 1e-18:
        return a, hypot(p[0] - a[0], p[1] - a[1])
    t = max(0.0, min(1.0, (wx * vx + wy * vy) / denom))
    q = (a[0] + t * vx, a[1] + t * vy)
    return q, hypot(p[0] - q[0], p[1] - q[1])


def distance_to_entity(point: Point, entity: GeometryEntity) -> SelectionHit | None:
    if len(entity.points) < 2:
        return None

    best_distance = float("inf")
    best_point: Point | None = None
    best_segment = -1
    for index, (a, b) in enumerate(zip(entity.points[:-1], entity.points[1:])):
        nearest, distance = _nearest_on_segment(point, a, b)
        if distance < best_distance:
            best_distance = distance
            best_point = nearest
            best_segment = index

    if best_point is None:
        return None
    return SelectionHit(entity=entity, distance=best_distance, nearest_point=best_point, segment_index=best_segment)


def rank_entities(
    entities: list[GeometryEntity],
    point: Point,
    *,
    tolerance: float,
    selectable_categories: set[str] | None = None,
    selectable_layers: set[str] | None = None,
) -> list[SelectionHit]:
    """Retorna candidatos dentro da tolerância, do mais próximo ao mais distante.

    A função trabalha em coordenadas do desenho. A interface deve converter a posição
    do cursor para coordenadas de mundo e calcular a tolerância equivalente ao zoom.
    """
    hits: list[SelectionHit] = []
    for entity in entities:
        if selectable_categories is not None and entity.category not in selectable_categories:
            continue
        if selectable_layers is not None and entity.layer not in selectable_layers:
            continue
        hit = distance_to_entity(point, entity)
        if hit is not None and hit.distance <= tolerance:
            hits.append(hit)

    hits.sort(key=lambda hit: (hit.distance, hit.entity.layer, hit.entity.handle))
    return hits


def pick_entity(
    entities: list[GeometryEntity],
    point: Point,
    *,
    tolerance: float,
    selectable_categories: set[str] | None = None,
    selectable_layers: set[str] | None = None,
    cycle_index: int = 0,
) -> SelectionHit | None:
    """Seleciona a entidade mais próxima; cycle_index permite alternar sobrepostas."""
    hits = rank_entities(
        entities,
        point,
        tolerance=tolerance,
        selectable_categories=selectable_categories,
        selectable_layers=selectable_layers,
    )
    if not hits:
        return None
    return hits[cycle_index % len(hits)]
