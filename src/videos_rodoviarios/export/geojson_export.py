from __future__ import annotations

import json
from pathlib import Path

from pyproj import Transformer

from videos_rodoviarios.core.models import RoadAnalysis


def _transformer(analysis: RoadAnalysis) -> Transformer | None:
    ctx = analysis.kml_context
    if not ctx or not ctx.utm_zone or not ctx.hemisphere:
        return None
    epsg = 32600 + ctx.utm_zone if ctx.hemisphere == "N" else 32700 + ctx.utm_zone
    return Transformer.from_crs(epsg, 4326, always_xy=True)


def write_geojson(analysis: RoadAnalysis, path: str | Path, to_wgs84: bool = False) -> Path:
    transformer = _transformer(analysis) if to_wgs84 else None
    features = []
    for e in analysis.entities:
        coords = e.points
        if transformer:
            coords = [transformer.transform(x, y) for x, y in coords]
        features.append({
            "type": "Feature",
            "properties": {"handle": e.handle, "layer": e.layer, "category": e.category, "dxftype": e.dxftype},
            "geometry": {"type": "LineString", "coordinates": coords},
        })
    data = {"type": "FeatureCollection", "features": features}
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
