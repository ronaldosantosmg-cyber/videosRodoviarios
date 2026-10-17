from __future__ import annotations

from collections import Counter
from pathlib import Path

from videos_rodoviarios.core.models import GeometryEntity, RoadAnalysis
from videos_rodoviarios.geometry.metrics import line_length, offset_info
from videos_rodoviarios.geometry.stationing import parse_station
from videos_rodoviarios.io.dxf_reader import read_dxf
from videos_rodoviarios.io.kml_reader import read_kml_context


def _pick_centerline(entities: list[GeometryEntity]) -> GeometryEntity:
    centers = [e for e in entities if e.category == "center"]
    pool = centers or [e for e in entities if e.category in {"edge", "other"}]
    if not pool:
        pool = entities
    return max(pool, key=line_length)


def analyze_road(dxf_path: str | Path, kmz_path: str | Path | None = None, curve_tolerance_m: float = 0.10) -> RoadAnalysis:
    entities, texts, warnings = read_dxf(dxf_path, curve_tolerance_m=curve_tolerance_m)
    center = _pick_centerline(entities)
    extension_m = line_length(center)

    stations = [v for t in texts if (v := parse_station(t.text)) is not None]
    context = None
    if kmz_path:
        context = read_kml_context(kmz_path)
        stations.extend(context.station_values_m)

    stations = sorted(set(round(v, 3) for v in stations))
    km_start = stations[0] if len(stations) >= 2 else None
    km_end = stations[-1] if len(stations) >= 2 else None
    delta = (km_end - km_start) if km_start is not None and km_end is not None else None

    if not any(e.category == "center" for e in entities):
        warnings.append("Nenhuma layer de eixo reconhecida; foi usada a geometria linear mais longa como eixo principal.")
    if delta is not None and extension_m > 0:
        diff = abs(delta - extension_m)
        if diff > max(50.0, extension_m * 0.03):
            warnings.append(
                f"Extensão geométrica ({extension_m:.1f} m) difere do intervalo de estaqueamento ({delta:.1f} m) em {diff:.1f} m."
            )

    offsets = [offset_info(e, center) for e in entities if e.category in {"cut", "fill"} and len(e.points) >= 2]
    categories = Counter(e.category for e in entities)
    layers = Counter(e.layer for e in entities)

    return RoadAnalysis(
        dxf_path=str(dxf_path),
        kmz_path=str(kmz_path) if kmz_path else None,
        entities=entities,
        texts=texts,
        main_centerline_handle=center.handle,
        extension_m=round(extension_m, 3),
        km_start_m=km_start,
        km_end_m=km_end,
        station_delta_m=round(delta, 3) if delta is not None else None,
        category_counts=dict(sorted(categories.items())),
        layer_counts=dict(sorted(layers.items())),
        offsets=offsets,
        warnings=warnings,
        kml_context=context,
    )
