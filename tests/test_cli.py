from pathlib import Path

from typer.testing import CliRunner

from videos_rodoviarios.cli import app

runner = CliRunner()


def test_validar_rejeita_arquivos_inexistentes(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["validar", str(tmp_path / "trecho.dxf"), str(tmp_path / "trecho.kmz")],
    )
    assert result.exit_code == 1
    assert "DXF não encontrado" in result.stdout
    assert "KMZ/KML não encontrado" in result.stdout


def test_validar_aceita_extensoes_corretas(tmp_path: Path) -> None:
    dxf = tmp_path / "trecho.dxf"
    kmz = tmp_path / "trecho.kmz"
    dxf.write_text("0\nEOF\n", encoding="utf-8")
    kmz.write_bytes(b"PK")

    result = runner.invoke(app, ["validar", str(dxf), str(kmz)])
    assert result.exit_code == 0
    assert "Entradas válidas" in result.stdout
