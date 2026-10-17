from typer.testing import CliRunner

from videos_rodoviarios.cli import app

runner = CliRunner()


def test_validar_rejeita_inexistente():
    result = runner.invoke(app, ["validar", "--dxf", "x.dxf"])
    assert result.exit_code != 0


def test_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "analisar" in result.stdout.lower()
