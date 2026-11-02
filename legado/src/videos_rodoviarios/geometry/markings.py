from __future__ import annotations

from dataclasses import dataclass
from math import hypot

Point = tuple[float, float]


@dataclass(slots=True)
class ArrowMarking:
    insertion: Point
    direction_point: Point
    polygon: list[Point]
    length_m: float = 4.0
    kind: str = "arrow"


@dataclass(slots=True)
class LineMarking:
    points: list[Point]
    marking_type: str
    width_m: float
    pattern: str
    kind: str = "line"


def _unit_vector(start: Point, end: Point) -> tuple[float, float]:
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = hypot(dx, dy)
    if length <= 1e-9:
        raise ValueError("O ponto de direção deve ser diferente do ponto de inserção.")
    return dx / length, dy / length


def create_direction_arrow(
    insertion: Point,
    direction_point: Point,
    *,
    length_m: float = 4.0,
    shaft_width_m: float = 0.30,
    head_width_m: float = 1.20,
    head_length_m: float = 1.20,
) -> ArrowMarking:
    """Create a pavement direction arrow from one insertion point and one direction point.

    The default arrow length is fixed at 4.00 m, matching the application's road-marking
    placement rule. The polygon is returned in world coordinates and can be used by both
    preview and final renderers.
    """
    if length_m <= 0:
        raise ValueError("O comprimento da seta deve ser positivo.")
    if head_length_m <= 0 or head_length_m >= length_m:
        raise ValueError("O comprimento da cabeça da seta deve ser menor que o comprimento total.")
    if shaft_width_m <= 0 or head_width_m <= shaft_width_m:
        raise ValueError("As larguras da seta são inválidas.")

    ux, uy = _unit_vector(insertion, direction_point)
    nx, ny = -uy, ux
    x0, y0 = insertion
    shaft_end = length_m - head_length_m

    def pt(along: float, lateral: float) -> Point:
        return (
            x0 + ux * along + nx * lateral,
            y0 + uy * along + ny * lateral,
        )

    polygon = [
        pt(0.0, -shaft_width_m / 2.0),
        pt(shaft_end, -shaft_width_m / 2.0),
        pt(shaft_end, -head_width_m / 2.0),
        pt(length_m, 0.0),
        pt(shaft_end, head_width_m / 2.0),
        pt(shaft_end, shaft_width_m / 2.0),
        pt(0.0, shaft_width_m / 2.0),
    ]
    return ArrowMarking(
        insertion=insertion,
        direction_point=direction_point,
        polygon=polygon,
        length_m=length_m,
    )


def create_edge_line(points: list[Point], *, width_m: float = 0.10) -> LineMarking:
    if len(points) < 2:
        raise ValueError("A faixa de bordo precisa de pelo menos dois pontos.")
    if width_m <= 0:
        raise ValueError("A largura da faixa de bordo deve ser positiva.")
    return LineMarking(
        points=list(points),
        marking_type="edge",
        width_m=width_m,
        pattern="continuous",
    )


def create_center_line(
    points: list[Point],
    *,
    width_m: float = 0.10,
    pattern: str = "continuous",
) -> LineMarking:
    if len(points) < 2:
        raise ValueError("A faixa de eixo precisa de pelo menos dois pontos.")
    if width_m <= 0:
        raise ValueError("A largura da faixa de eixo deve ser positiva.")
    normalized = pattern.strip().lower()
    if normalized not in {"continuous", "dashed", "double_continuous"}:
        raise ValueError("Padrão de faixa de eixo inválido.")
    return LineMarking(
        points=list(points),
        marking_type="center",
        width_m=width_m,
        pattern=normalized,
    )
