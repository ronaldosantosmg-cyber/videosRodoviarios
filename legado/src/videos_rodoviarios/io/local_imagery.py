from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from videos_rodoviarios.io.ecw_converter import convert_ecw_to_geotiff

SUPPORTED_DIRECT = {".tif", ".tiff", ".png", ".jpg", ".jpeg"}


@dataclass(slots=True)
class LocalImageryResult:
    source: Path
    usable_path: Path
    converted: bool


def prepare_local_imagery(source: str | Path, destination_dir: str | Path) -> LocalImageryResult:
    src = Path(source)
    if not src.exists():
        raise FileNotFoundError(src)

    destination = Path(destination_dir)
    destination.mkdir(parents=True, exist_ok=True)
    suffix = src.suffix.lower()

    if suffix == ".ecw":
        target = destination / f"{src.stem}.tif"
        result = convert_ecw_to_geotiff(src, target)
        return LocalImageryResult(src, result.output, True)

    if suffix not in SUPPORTED_DIRECT:
        raise ValueError("Formato de imagem não suportado. Use ECW, GeoTIFF/TIFF, PNG ou JPEG.")

    target = destination / src.name
    if src.resolve() != target.resolve():
        shutil.copy2(src, target)
    return LocalImageryResult(src, target, False)
