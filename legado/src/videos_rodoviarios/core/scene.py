from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal
from uuid import uuid4

Point = tuple[float, float]

@dataclass(slots=True)
class SceneObject:
    """Elemento manual independente do DXF; pode ser salvo sem alterar a geometria importada."""
    kind: Literal["oae", "footbridge", "gantry", "semi_gantry", "light_pole", "sign", "barrier"]
    points: list[Point]
    id: str = field(default_factory=lambda: uuid4().hex)
    name: str = ""
    station_m: float | None = None
    heading_deg: float = 0.0
    scale: float = 1.0
    visible: bool = True
    properties: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def oae_from_vertices(cls, vertices: list[Point], **properties: Any) -> "SceneObject":
        if len(vertices) < 4:
            raise ValueError("A OAE deve ser definida por quatro ou mais vértices.")
        return cls(kind="oae", points=list(vertices), name="OAE", properties=properties)

    @classmethod
    def oae_from_four_vertices(cls, vertices: list[Point], **properties: Any) -> "SceneObject":
        """Compatibilidade com REV03 inicial; aceita exatamente quatro vértices."""
        if len(vertices) != 4:
            raise ValueError("A OAE deve ser definida por exatamente quatro vértices.")
        return cls.oae_from_vertices(vertices, **properties)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

@dataclass(slots=True)
class TrafficFlow:
    """Fluxo editável de veículos ao longo de uma trajetória."""
    path: list[Point]
    id: str = field(default_factory=lambda: uuid4().hex)
    name: str = "Fluxo"
    direction: Literal["forward", "reverse"] = "forward"
    lane_offset_m: float = 0.0
    speed_kmh: float = 70.0
    density: int = 8
    vehicle_mix: tuple[str, ...] = ("car", "car", "car", "truck")
    visible: bool = True
    def __post_init__(self) -> None:
        if len(self.path) < 2:
            raise ValueError("O fluxo precisa de pelo menos dois pontos.")
        self.speed_kmh = max(1.0, float(self.speed_kmh))
        self.density = max(1, min(80, int(self.density)))
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
