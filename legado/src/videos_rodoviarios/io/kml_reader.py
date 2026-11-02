from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from videos_rodoviarios.core.models import KmlContext
from videos_rodoviarios.geometry.crs import infer_utm_from_lonlat
from videos_rodoviarios.geometry.stationing import parse_station


def _read_kml_bytes(path: Path) -> bytes:
    if path.suffix.lower() == ".kml":
        return path.read_bytes()
    if path.suffix.lower() != ".kmz":
        raise ValueError("O arquivo geográfico deve ser KML ou KMZ.")
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".kml")]
        if not names:
            raise ValueError("KMZ sem arquivo KML interno.")
        preferred = next((n for n in names if n.lower().endswith("doc.kml")), names[0])
        return zf.read(preferred)


def read_kml_context(path: str | Path) -> KmlContext:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    raw = _read_kml_bytes(p)
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise ValueError(f"KML inválido: {exc}") from exc

    names: list[str] = []
    coordinates: list[tuple[float, float, float | None]] = []
    station_values: list[float] = []

    for elem in root.iter():
        tag = elem.tag.rsplit("}", 1)[-1]
        if tag == "name" and elem.text:
            name = elem.text.strip()
            if name:
                names.append(name)
                val = parse_station(name)
                if val is not None:
                    station_values.append(val)
        elif tag == "coordinates" and elem.text:
            for token in re.split(r"\s+", elem.text.strip()):
                if not token:
                    continue
                parts = token.split(",")
                if len(parts) < 2:
                    continue
                try:
                    lon, lat = float(parts[0]), float(parts[1])
                    alt = float(parts[2]) if len(parts) > 2 and parts[2] else None
                    coordinates.append((lon, lat, alt))
                except ValueError:
                    continue

    if coordinates:
        lon = sum(c[0] for c in coordinates) / len(coordinates)
        lat = sum(c[1] for c in coordinates) / len(coordinates)
        utm = infer_utm_from_lonlat(lon, lat, datum="WGS84")
        zone = utm.zone
        hemisphere = utm.hemisphere
        projected_epsg = utm.epsg
    else:
        lon = lat = None
        zone = None
        hemisphere = None
        projected_epsg = None

    return KmlContext(
        path=str(p),
        names=names,
        coordinates=coordinates,
        centroid_lon=lon,
        centroid_lat=lat,
        utm_zone=zone,
        hemisphere=hemisphere,
        datum="WGS84",
        geographic_epsg=4326,
        projected_epsg=projected_epsg,
        crs_source="kml_wgs84_inferred_utm",
        station_values_m=station_values,
    )
