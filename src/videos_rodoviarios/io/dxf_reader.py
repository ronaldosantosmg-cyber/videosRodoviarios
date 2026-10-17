from __future__ import annotations

from pathlib import Path

import ezdxf
from ezdxf.path import make_path

from videos_rodoviarios.core.models import GeometryEntity, TextEntity
from videos_rodoviarios.geometry.classify import classify_layer

SUPPORTED_CURVES = {"LINE", "LWPOLYLINE", "POLYLINE", "ARC", "SPLINE", "CIRCLE", "ELLIPSE"}
SUPPORTED_TEXT = {"TEXT", "MTEXT"}


def _flatten(entity, tolerance: float) -> list[tuple[float, float]]:
    etype = entity.dxftype()
    if etype == "LINE":
        return [
            (float(entity.dxf.start.x), float(entity.dxf.start.y)),
            (float(entity.dxf.end.x), float(entity.dxf.end.y)),
        ]
    path = make_path(entity)
    pts = list(path.flattening(distance=max(tolerance, 0.001), segments=8))
    return [(float(p.x), float(p.y)) for p in pts]


def read_dxf(path: str | Path, curve_tolerance_m: float = 0.10) -> tuple[list[GeometryEntity], list[TextEntity], list[str]]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    try:
        doc = ezdxf.readfile(path)
    except ezdxf.DXFStructureError as exc:
        raise ValueError(f"DXF inválido ou corrompido: {exc}") from exc

    entities: list[GeometryEntity] = []
    texts: list[TextEntity] = []
    warnings: list[str] = []
    msp = doc.modelspace()

    for entity in msp:
        etype = entity.dxftype()
        layer = str(getattr(entity.dxf, "layer", "0"))
        handle = str(getattr(entity.dxf, "handle", ""))
        if etype in SUPPORTED_CURVES:
            try:
                points = _flatten(entity, curve_tolerance_m)
                if len(points) >= 2:
                    closed = bool(getattr(entity, "closed", False))
                    entities.append(
                        GeometryEntity(
                            handle=handle,
                            dxftype=etype,
                            layer=layer,
                            category=classify_layer(layer),
                            points=points,
                            closed=closed,
                        )
                    )
            except Exception as exc:
                warnings.append(f"Entidade {handle or '?'} ({etype}) ignorada: {exc}")
        elif etype in SUPPORTED_TEXT:
            try:
                if etype == "TEXT":
                    value = entity.dxf.text
                    ins = entity.dxf.insert
                else:
                    value = entity.plain_text()
                    ins = entity.dxf.insert
                texts.append(TextEntity(handle=handle, layer=layer, text=str(value), x=float(ins.x), y=float(ins.y)))
            except Exception as exc:
                warnings.append(f"Texto {handle or '?'} ignorado: {exc}")

    if not entities:
        raise ValueError("DXF sem geometria suportada em ModelSpace.")
    return entities, texts, warnings
