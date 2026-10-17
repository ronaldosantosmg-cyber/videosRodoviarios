from pathlib import Path

import typer

app = typer.Typer(help="Gerador de vídeos técnicos rodoviários")


@app.command()
def validar(dxf: Path, kmz: Path) -> None:
    """Valida as entradas do primeiro MVP."""
    erros: list[str] = []
    if not dxf.exists():
        erros.append(f"DXF não encontrado: {dxf}")
    if not kmz.exists():
        erros.append(f"KMZ/KML não encontrado: {kmz}")
    if dxf.suffix.lower() != ".dxf":
        erros.append("O primeiro arquivo deve ser DXF.")
    if kmz.suffix.lower() not in {".kmz", ".kml"}:
        erros.append("O segundo arquivo deve ser KMZ ou KML.")

    if erros:
        for erro in erros:
            typer.echo(f"ERRO: {erro}")
        raise typer.Exit(code=1)

    typer.echo("Entradas válidas. Próxima etapa: leitura geométrica e geração de prévia.")


if __name__ == "__main__":
    app()
