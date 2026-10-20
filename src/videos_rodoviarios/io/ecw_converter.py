from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from videos_rodoviarios.paths import SUPPORT_DIR


@dataclass(slots=True)
class EcwConversionResult:
    source: Path
    output: Path
    gdal_translate: Path
    driver_available: bool


def _portable_gdal_dirs() -> list[Path]:
    root = SUPPORT_DIR / "gdal"
    return [root, root / "bin", SUPPORT_DIR / "ecw", SUPPORT_DIR / "ecw" / "bin"]


def _find_executable(name: str) -> Path | None:
    for folder in _portable_gdal_dirs():
        candidate = folder / name
        if candidate.exists():
            return candidate
    found = shutil.which(name)
    return Path(found) if found else None


def _find_gdal_translate() -> Path | None:
    for name in ("gdal_translate.exe", "gdal_translate"):
        exe = _find_executable(name)
        if exe:
            return exe
    return None


def _find_gdalinfo() -> Path | None:
    for name in ("gdalinfo.exe", "gdalinfo"):
        exe = _find_executable(name)
        if exe:
            return exe
    return None


def portable_gdal_env() -> dict[str, str]:
    env = os.environ.copy()
    existing_path = env.get("PATH", "")
    local_dirs = [str(path) for path in _portable_gdal_dirs() if path.exists()]
    if local_dirs:
        env["PATH"] = os.pathsep.join(local_dirs + [existing_path])

    gdal_root = SUPPORT_DIR / "gdal"
    data_candidates = [gdal_root / "share" / "gdal", gdal_root / "gdal-data"]
    plugin_candidates = [
        gdal_root / "lib" / "gdalplugins",
        gdal_root / "plugins",
        SUPPORT_DIR / "ecw" / "plugins",
    ]
    for candidate in data_candidates:
        if candidate.exists():
            env["GDAL_DATA"] = str(candidate)
            break
    for candidate in plugin_candidates:
        if candidate.exists():
            env["GDAL_DRIVER_PATH"] = str(candidate)
            break
    return env


def ecw_driver_available() -> bool:
    info = _find_gdalinfo()
    if info is None:
        return False
    try:
        proc = subprocess.run(
            [str(info), "--formats"],
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
            env=portable_gdal_env(),
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
    """Converte ECW para GeoTIFF sem instalação.

    ``gdal_executable`` é aceito para compatibilidade com testes e integrações
    legadas. Quando omitido, o runtime portátil em ``apoio/gdal`` é usado.
    """
    src = Path(source)
    if not src.exists():
        raise FileNotFoundError(src)
    if src.suffix.lower() != ".ecw":
        raise ValueError("O arquivo informado não possui extensão .ecw.")

    dst = Path(output) if output is not None else src.with_suffix(".tif")
    translate = Path(gdal_executable) if gdal_executable else _find_gdal_translate()
    if translate is None:
        raise RuntimeError(
            "Runtime GDAL portátil não encontrado. Coloque o runtime em apoio/gdal sem instalar no Windows."
        )

    if gdal_executable is None and not ecw_driver_available():
        raise RuntimeError(
            "O GDAL portátil foi encontrado, mas o driver ECW não está disponível. "
            "Adicione em apoio/ecw uma distribuição Desktop Read-Only autorizada que forneça o driver ECW."
        )

    dst.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(translate),
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
    proc = subprocess.run(command, capture_output=True, text=True, check=False, env=portable_gdal_env())
    if proc.returncode != 0 or not dst.exists():
        detail = (proc.stderr or proc.stdout or "erro desconhecido").strip()
        raise RuntimeError(f"Falha ao converter ECW para GeoTIFF: {detail}")

    return EcwConversionResult(src, dst, translate, True)
