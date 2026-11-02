from __future__ import annotations

from dataclasses import dataclass
from math import acos, atan2, cos, hypot, pi, sin, tan

Point = tuple[float, float]


@dataclass(slots=True)
class CircularCurve:
    pi: Point
    radius_m: float
    tangent_m: float
    arc_length_m: float
    delta_rad: float
    pc: Point
    pt: Point
    center: Point
    points: list[Point]


def _unit(a: Point, b: Point) -> Point:
    dx = b[0] - a[0]
    dy = b[1] - a[1]
    length = hypot(dx, dy)
    if length <= 1e-9:
        raise ValueError("Pontos consecutivos do alinhamento não podem coincidir.")
    return dx / length, dy / length


def _dot(a: Point, b: Point) -> float:
    return a[0] * b[0] + a[1] * b[1]


def _cross(a: Point, b: Point) -> float:
    return a[0] * b[1] - a[1] * b[0]


def build_circular_curve(prev: Point, pi_point: Point, next_point: Point, radius_m: float, *, step_m: float = 2.0) -> CircularCurve:
    if radius_m <= 0:
        raise ValueError("O raio deve ser positivo.")
    if step_m <= 0:
        raise ValueError("O passo de discretização deve ser positivo.")

    incoming = _unit(pi_point, prev)
    outgoing = _unit(pi_point, next_point)
    cos_delta = max(-1.0, min(1.0, _dot(incoming, outgoing)))
    delta = acos(cos_delta)
    if delta <= 1e-6 or abs(pi - delta) <= 1e-6:
        raise ValueError("O PI não define uma curva circular válida.")

    tangent = radius_m * tan(delta / 2.0)
    len_in = hypot(prev[0] - pi_point[0], prev[1] - pi_point[1])
    len_out = hypot(next_point[0] - pi_point[0], next_point[1] - pi_point[1])
    if tangent >= len_in or tangent >= len_out:
        raise ValueError("O raio informado não cabe entre os trechos adjacentes ao PI.")

    pc = (pi_point[0] + incoming[0] * tangent, pi_point[1] + incoming[1] * tangent)
    pt = (pi_point[0] + outgoing[0] * tangent, pi_point[1] + outgoing[1] * tangent)

    # Bisector from PI toward the circle center.
    bis = (incoming[0] + outgoing[0], incoming[1] + outgoing[1])
    bis_len = hypot(bis[0], bis[1])
    if bis_len <= 1e-9:
        raise ValueError("Não foi possível determinar a bissetriz da curva.")
    bis = (bis[0] / bis_len, bis[1] / bis_len)
    center_distance = radius_m / sin(delta / 2.0)
    center = (pi_point[0] + bis[0] * center_distance, pi_point[1] + bis[1] * center_distance)

    a0 = atan2(pc[1] - center[1], pc[0] - center[0])
    a1 = atan2(pt[1] - center[1], pt[0] - center[0])
    turn = _cross((-incoming[0], -incoming[1]), outgoing)
    if turn > 0:
        while a1 <= a0:
            a1 += 2 * pi
    else:
        while a1 >= a0:
            a1 -= 2 * pi

    sweep = a1 - a0
    arc_length = abs(sweep) * radius_m
    samples = max(2, int(arc_length / step_m) + 1)
    points = [
        (
            center[0] + radius_m * cos(a0 + sweep * i / samples),
            center[1] + radius_m * sin(a0 + sweep * i / samples),
        )
        for i in range(samples + 1)
    ]

    return CircularCurve(
        pi=pi_point,
        radius_m=radius_m,
        tangent_m=tangent,
        arc_length_m=arc_length,
        delta_rad=abs(sweep),
        pc=pc,
        pt=pt,
        center=center,
        points=points,
    )


def apply_curve_at_vertex(points: list[Point], vertex_index: int, radius_m: float, *, step_m: float = 2.0) -> tuple[list[Point], CircularCurve]:
    if vertex_index <= 0 or vertex_index >= len(points) - 1:
        raise ValueError("A curva só pode ser criada em um vértice interno do alinhamento.")
    curve = build_circular_curve(points[vertex_index - 1], points[vertex_index], points[vertex_index + 1], radius_m, step_m=step_m)
    updated = list(points[:vertex_index])
    if updated[-1] != curve.pc:
        updated.append(curve.pc)
    updated.extend(curve.points[1:-1])
    updated.append(curve.pt)
    updated.extend(points[vertex_index + 1 :])
    return updated, curve


def polyline_length(points: list[Point]) -> float:
    return sum(hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(points, points[1:]))
