from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class EcwConversionResult:
    source: Path
    output: Path
    gdal_executable: Path
    driver_available: bool


def _find_gdal() -> Path | None:
    candidates = [
        shutil.which("gdal"),
        shutil.which("gdal_translate"),
    ]
    for candidate in candidates:
        if candidate:
            return Path(candidate)
    return None


def ecw_driver_available(gdal_executable: str | Path | None = None) -> bool:
    exe = Path(gdal_executable) if gdal_executable else _find_gdal()
    if exe is None:
        return False

    name = exe.name.lower()
    try:
        if name.startswith("gdal_translate"):
            probe = shutil.which("gdalinfo")
            if not probe:
                return False
            proc = subprocess.run(
                [probe, "--formats"],
                capture_output=True,
                text=True,
                check=False,
                timeout=15,
            )
        else:
            proc = subprocess.run(
                [str(exe), "--formats"],
                capture_output=True,
                text=True,
                check=False,
                timeout=15,
            )
    except (OSError, subprocess.SubprocessError):
        return False

    text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    return "ECW" in text.upper()


def convert_ecw_to_geotiff(
    source: str | Path,
    output: str | Path | None = None,
    *,
    gdal_executable: str | Path | None = None,
) -> EcwConversionResult:
    src = Path(source)
    if not src.exists():
        raise FileNotFoundError(src)
    if src.suffix.lower() != ".ecw":
        raise ValueError("O arquivo informado não possui extensão .ecw.")

    exe = Path(gdal_executable) if gdal_executable else _find_gdal()
    if exe is None:
        raise RuntimeError(
            "GDAL não foi encontrado. Instale ou disponibilize um GDAL com suporte ao driver ECW."
        )

    if not ecw_driver_available(exe):
        raise RuntimeError(
            "O GDAL encontrado não possui o driver ECW. A conversão foi cancelada para não perder o georreferenciamento."
        )

    dst = Path(output) if output else src.with_suffix(".tif")
    dst.parent.mkdir(parents=True, exist_ok=True)

    name = exe.name.lower()
    if name.startswith("gdal_translate"):
        command = [
            str(exe),
            "-of",
            "GTiff",
            "-co",
            "TILED=YES",
            "-co",
            "COMPRESS=DEFLATE",
            "-co",
            "BIGTIFF=IF_SAFER",
            str(src),
            str(dst),
        ]
    else:
        command = [
            str(exe),
            "raster",
            "convert",
            "--output-format",
            "GTiff",
            "--co",
            "TILED=YES",
            "--co",
            "COMPRESS=DEFLATE",
            "--co",
            "BIGTIFF=IF_SAFER",
            str(src),
            str(dst),
        ]

    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0 or not dst.exists():
        detail = (proc.stderr or proc.stdout or "erro desconhecido").strip()
        raise RuntimeError(f"Falha ao converter ECW para GeoTIFF: {detail}")

    return EcwConversionResult(
        source=src,
        output=dst,
        gdal_executable=exe,
        driver_available=True,
    )
