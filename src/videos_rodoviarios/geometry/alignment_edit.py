from __future__ import annotations

from dataclasses import dataclass, field
from math import acos, atan2, cos, hypot, pi, sin, tan

Point = tuple[float, float]


def _distance(a: Point, b: Point) -> float:
    return hypot(b[0] - a[0], b[1] - a[1])


def _unit(a: Point, b: Point) -> Point:
    d = _distance(a, b)
    if d <= 1e-9:
        raise ValueError("Pontos coincidentes não definem direção.")
    return ((b[0] - a[0]) / d, (b[1] - a[1]) / d)


def _add(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1])


def _scale(v: Point, value: float) -> Point:
    return (v[0] * value, v[1] * value)


@dataclass(slots=True)
class CurveGeometry:
    radius_m: float
    pi: Point
    pc: Point
    pt: Point
    center: Point
    delta_rad: float
    tangent_m: float
    arc_length_m: float
    points: list[Point]


@dataclass(slots=True)
class EditablePI:
    index: int
    original_pi: Point
    radius_m: float | None = None
    curve: CurveGeometry | None = None

    @property
    def is_dry_pi(self) -> bool:
        return self.curve is None


@dataclass
class EditableAlignment:
    original_points: list[Point]
    edits: dict[int, EditablePI] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.original_points) < 2:
            raise ValueError("O alinhamento precisa de pelo menos dois pontos.")
        self.original_points = list(self.original_points)

    def apply_radius(self, pi_index: int, radius_m: float, *, samples: int = 24) -> CurveGeometry:
        if pi_index <= 0 or pi_index >= len(self.original_points) - 1:
            raise ValueError("Só é possível aplicar curva em um PI interno.")
        curve = build_circular_curve(
            self.original_points[pi_index - 1],
            self.original_points[pi_index],
            self.original_points[pi_index + 1],
            radius_m,
            samples=samples,
        )
        self.edits[pi_index] = EditablePI(
            index=pi_index,
            original_pi=self.original_points[pi_index],
            radius_m=radius_m,
            curve=curve,
        )
        return curve

    def update_radius_from_drag(self, pi_index: int, handle_point: Point, *, samples: int = 24) -> CurveGeometry:
        if pi_index <= 0 or pi_index >= len(self.original_points) - 1:
            raise ValueError("Só é possível ajustar um PI interno.")
        pi_point = self.original_points[pi_index]
        radius = _distance(pi_point, handle_point)
        if radius <= 0.05:
            raise ValueError("O raio calculado pelo arraste é muito pequeno.")
        return self.apply_radius(pi_index, radius, samples=samples)

    def remove_radius(self, pi_index: int) -> Point:
        if pi_index <= 0 or pi_index >= len(self.original_points) - 1:
            raise ValueError("Só é possível restaurar um PI interno.")
        self.edits.pop(pi_index, None)
        return self.original_points[pi_index]

    def rendered_points(self) -> list[Point]:
        result: list[Point] = [self.original_points[0]]
        for idx in range(1, len(self.original_points) - 1):
            edit = self.edits.get(idx)
            if edit and edit.curve:
                if result[-1] != edit.curve.pc:
                    result.append(edit.curve.pc)
                result.extend(edit.curve.points[1:])
            else:
                result.append(self.original_points[idx])
        result.append(self.original_points[-1])
        return result

    def developed_length_m(self) -> float:
        pts = self.rendered_points()
        return sum(_distance(a, b) for a, b in zip(pts, pts[1:]))


def build_circular_curve(prev: Point, pi_point: Point, nxt: Point, radius_m: float, *, samples: int = 24) -> CurveGeometry:
    if radius_m <= 0:
        raise ValueError("O raio deve ser maior que zero.")
    if samples < 3:
        raise ValueError("A curva precisa de pelo menos três amostras.")

    v_in = _unit(pi_point, prev)
    v_out = _unit(pi_point, nxt)
    dot = max(-1.0, min(1.0, v_in[0] * v_out[0] + v_in[1] * v_out[1]))
    delta = pi - acos(dot)
    if abs(delta) <= 1e-6 or abs(pi - delta) <= 1e-6:
        raise ValueError("O PI não define uma deflexão válida para curva circular.")

    tangent = radius_m * tan(abs(delta) / 2.0)
    if tangent >= _distance(pi_point, prev) or tangent >= _distance(pi_point, nxt):
        raise ValueError("O raio informado não cabe entre os segmentos adjacentes.")

    pc = _add(pi_point, _scale(v_in, tangent))
    pt = _add(pi_point, _scale(v_out, tangent))

    bisector = _add(v_in, v_out)
    bisector_len = hypot(bisector[0], bisector[1])
    if bisector_len <= 1e-9:
        raise ValueError("Não foi possível determinar o centro da curva.")
    bisector = (bisector[0] / bisector_len, bisector[1] / bisector_len)
    center_dist = radius_m / cos(abs(delta) / 2.0)
    center = _add(pi_point, _scale(bisector, center_dist))

    a0 = atan2(pc[1] - center[1], pc[0] - center[0])
    a1 = atan2(pt[1] - center[1], pt[0] - center[0])
    cross = (pi_point[0] - prev[0]) * (nxt[1] - pi_point[1]) - (pi_point[1] - prev[1]) * (nxt[0] - pi_point[0])
    sweep = a1 - a0
    if cross > 0 and sweep < 0:
        sweep += 2 * pi
    elif cross < 0 and sweep > 0:
        sweep -= 2 * pi

    points = [
        (
            center[0] + radius_m * cos(a0 + sweep * i / samples),
            center[1] + radius_m * sin(a0 + sweep * i / samples),
        )
        for i in range(samples + 1)
    ]

    return CurveGeometry(
        radius_m=radius_m,
        pi=pi_point,
        pc=pc,
        pt=pt,
        center=center,
        delta_rad=abs(sweep),
        tangent_m=tangent,
        arc_length_m=abs(sweep) * radius_m,
        points=points,
    )
