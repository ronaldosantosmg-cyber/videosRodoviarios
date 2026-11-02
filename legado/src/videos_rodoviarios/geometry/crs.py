from __future__ import annotations

from dataclasses import dataclass

from pyproj import CRS


@dataclass(slots=True)
class CrsChoice:
    datum: str
    zone: int | None
    hemisphere: str | None
    epsg: int | None
    geographic: bool = False


SUPPORTED_DATUMS = ("SIRGAS2000", "WGS84", "SAD69")


def utm_epsg(datum: str, zone: int, hemisphere: str) -> int:
    key = datum.upper().replace(" ", "").replace("_", "")
    hemi = hemisphere.upper()
    if not 1 <= zone <= 60:
        raise ValueError("Fuso UTM deve estar entre 1 e 60.")
    if hemi not in {"N", "S"}:
        raise ValueError("Hemisfério deve ser N ou S.")
    if key in {"SIRGAS2000", "SIRGAS"}:
        return (31960 if hemi == "S" else 31900) + zone
    if key in {"WGS84", "WGS1984"}:
        return (32700 if hemi == "S" else 32600) + zone
    if key in {"SAD69", "SAD1969"}:
        return (29100 if hemi == "S" else 29160) + zone
    raise ValueError(f"Datum não suportado: {datum}")


def make_utm_choice(datum: str, zone: int, hemisphere: str) -> CrsChoice:
    epsg = utm_epsg(datum, zone, hemisphere)
    CRS.from_epsg(epsg)  # valida no PROJ instalado
    return CrsChoice(datum=datum, zone=zone, hemisphere=hemisphere.upper(), epsg=epsg, geographic=False)


def make_geographic_choice(datum: str) -> CrsChoice:
    key = datum.upper().replace(" ", "").replace("_", "")
    epsg = {"WGS84": 4326, "WGS1984": 4326, "SIRGAS2000": 4674, "SIRGAS": 4674, "SAD69": 4618, "SAD1969": 4618}.get(key)
    if epsg is None:
        raise ValueError(f"Datum geográfico não suportado: {datum}")
    CRS.from_epsg(epsg)
    return CrsChoice(datum=datum, zone=None, hemisphere=None, epsg=epsg, geographic=True)


def infer_utm_from_lonlat(lon: float, lat: float, datum: str = "SIRGAS2000") -> CrsChoice:
    zone = max(1, min(60, int((lon + 180.0) // 6.0) + 1))
    hemisphere = "N" if lat >= 0 else "S"
    return make_utm_choice(datum, zone, hemisphere)
