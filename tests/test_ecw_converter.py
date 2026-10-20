from pathlib import Path

import pytest

from videos_rodoviarios.io.ecw_converter import convert_ecw_to_geotiff


def test_rejects_non_ecw(tmp_path: Path):
    source = tmp_path / "imagem.png"
    source.write_bytes(b"x")
    with pytest.raises(ValueError):
        convert_ecw_to_geotiff(source, gdal_executable="gdal")


def test_missing_source(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        convert_ecw_to_geotiff(tmp_path / "ausente.ecw", gdal_executable="gdal")
