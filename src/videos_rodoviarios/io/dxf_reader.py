from __future__ import annotations

from math import isfinite
from pathlib import Path

import ezdxf
from ezdxf.path import make_path

from videos_rodoviarios.core.models import GeometryEntity, TextEntity
from videos_rodoviarios.geometry.classify import classify_layer

SUPPORTED_CURVES = {"LINE", "LWPOLYLINE", "POLYLINE", "ARC", "SPLINE", "CIRCLE", "ELLIPSE"}
SUPPORTED_TEXT = {"TEXT", "MTEXT"}


def _sanitize(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    clean: list[tuple[float, float]] = []
    for x, y in points:
        if not (isfinite(x) and isfinite(y)):
            continue
        p = (float(x), float(y))
        if not clean or abs(clean[-1][0] - p[0]) > 1e-9 or abs(clean[-1][1] - p[1]) > 1e-9:
            clean.append(p)
    if len(clean) >= 2 and all(abs(clean[0][i] - p[i]) <= 1e-9 for p in clean[1:] for i in (0, 1)):
        return []
    return clean


def _flatten(entity, tolerance: float) -> list[tuple[float, float]]:
    etype = entity.dxftype()
    if etype == "LINE":
        return _sanitize([
            (float(entity.dxf.start.x), float(entity.dxf.start.y)),
            (float(entity.dxf.end.x), float(entity.dxf.end.y)),
        ])
    path = make_path(entity)
    pts = list(path.flattening(distance=max(tolerance, 0.001), segments=8))
    return _sanitize([(float(p.x), float(p.y)) for p in pts])


def _layer_state(doc, layer_name: str) -> tuple[bool, bool, bool]:
    try:
        layer = doc.layers.get(layer_name)
    except Exception:
        return True, False, False

    try:
        is_off = bool(layer.is_off())
    except Exception:
        is_off = False
    try:
        is_frozen = bool(layer.is_frozen())
    except Exception:
        is_frozen = False
    return not (is_off or is_frozen), is_off, is_frozen


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
        visible, layer_off, layer_frozen = _layer_state(doc, layer)
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
                            visible=visible,
                            layer_off=layer_off,
                            layer_frozen=layer_frozen,
                        )
                    )
                else:
                    warnings.append(f"Entidade {handle or '?'} ({etype}) ignorada por geometria degenerada.")
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
                x, y = float(ins.x), float(ins.y)
                if isfinite(x) and isfinite(y):
                    texts.append(
                        TextEntity(
                            handle=handle,
                            layer=layer,
                            text=str(value),
                            x=x,
                            y=y,
                            visible=visible,
                            layer_off=layer_off,
                            layer_frozen=layer_frozen,
                        )
                    )
            except Exception as exc:
                warnings.append(f"Texto {handle or '?'} ignorado: {exc}")

    if not entities:
        raise ValueError("DXF sem geometria suportada e válida em ModelSpace.")
    return entities, texts, warnings
