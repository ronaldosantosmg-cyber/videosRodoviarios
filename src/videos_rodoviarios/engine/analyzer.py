from __future__ import annotations

from collections import Counter
from pathlib import Path

from videos_rodoviarios.core.models import GeometryEntity, RoadAnalysis
from videos_rodoviarios.geometry.metrics import line_length, offset_info
from videos_rodoviarios.geometry.stationing import parse_station
from videos_rodoviarios.io.dxf_reader import read_dxf
from videos_rodoviarios.io.kml_reader import read_kml_context


def _pick_centerline(entities: list[GeometryEntity], preferred_handle: str | None = None) -> GeometryEntity:
    valid = [e for e in entities if len(e.points) >= 2 and line_length(e) > 1e-6]
    if not valid:
        raise ValueError("DXF sem geometria linear válida para definir o eixo.")

    if preferred_handle:
        selected = next((e for e in valid if e.handle == preferred_handle), None)
        if selected is None:
            raise ValueError(f"A entidade selecionada como eixo ({preferred_handle}) não existe ou não é uma geometria linear válida.")
        return selected

    centers = [e for e in valid if e.category == "center"]
    pool = centers or [e for e in valid if e.category in {"edge", "other"}]
    if not pool:
        pool = valid
    return max(pool, key=line_length)


def analyze_road(
    dxf_path: str | Path,
    kmz_path: str | Path | None = None,
    curve_tolerance_m: float = 0.10,
    centerline_handle: str | None = None,
) -> RoadAnalysis:
    entities, texts, warnings = read_dxf(dxf_path, curve_tolerance_m=curve_tolerance_m)
    center = _pick_centerline(entities, centerline_handle)
    extension_m = line_length(center)

    stations = [v for t in texts if (v := parse_station(t.text)) is not None]
    context = None
    if kmz_path:
        try:
            context = read_kml_context(kmz_path)
            stations.extend(context.station_values_m)
        except Exception as exc:
            warnings.append(f"KMZ/KML não pôde ser lido completamente: {exc}")
            context = None

    stations = sorted(set(round(v, 3) for v in stations))
    km_start = stations[0] if len(stations) >= 2 else None
    km_end = stations[-1] if len(stations) >= 2 else None
    delta = (km_end - km_start) if km_start is not None and km_end is not None else None

    if centerline_handle:
        warnings.append(f"Eixo definido manualmente pela entidade {center.handle} da layer {center.layer}.")
    elif not any(e.category == "center" for e in entities):
        warnings.append("Nenhuma layer de eixo reconhecida; foi usada a geometria linear mais longa como eixo principal.")

    if delta is not None and extension_m > 0:
        diff = abs(delta - extension_m)
        if diff > max(50.0, extension_m * 0.03):
            warnings.append(
                f"Extensão geométrica ({extension_m:.1f} m) difere do intervalo de estaqueamento ({delta:.1f} m) em {diff:.1f} m."
            )

    offsets = []
    for entity in entities:
        if entity.category not in {"cut", "fill"} or len(entity.points) < 2:
            continue
        try:
            offsets.append(offset_info(entity, center))
        except Exception as exc:
            warnings.append(
                f"Offset {entity.handle or '?'} da layer {entity.layer} foi ignorado sem interromper a análise: {exc}"
            )

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
