from __future__ import annotations

from pathlib import Path

import typer

from videos_rodoviarios.engine.analyzer import analyze_road
from videos_rodoviarios.export.geojson_export import write_geojson
from videos_rodoviarios.export.json_export import write_analysis_json
from videos_rodoviarios.export.svg_preview import write_svg_preview
from videos_rodoviarios.geometry.stationing import format_station

app = typer.Typer(help="Motor de análise e preparação de vídeos técnicos rodoviários")


def _validate_paths(dxf: Path, kmz: Path | None) -> None:
    if not dxf.exists():
        raise typer.BadParameter(f"DXF não encontrado: {dxf}")
    if dxf.suffix.lower() != ".dxf":
        raise typer.BadParameter("O arquivo de projeto deve ser DXF.")
    if kmz:
        if not kmz.exists():
            raise typer.BadParameter(f"KMZ/KML não encontrado: {kmz}")
        if kmz.suffix.lower() not in {".kmz", ".kml"}:
            raise typer.BadParameter("O arquivo geográfico deve ser KMZ ou KML.")


@app.command()
def validar(dxf: Path, kmz: Path | None = None) -> None:
    """Valida os arquivos e executa uma leitura técnica curta."""
    _validate_paths(dxf, kmz)
    analysis = analyze_road(dxf, kmz)
    typer.echo(f"OK · {len(analysis.entities)} geometrias · extensão {analysis.extension_m/1000:.3f} km")


@app.command()
def analisar(
    dxf: Path,
    kmz: Path | None = None,
    saida: Path = Path("output"),
    tolerancia_curva: float = typer.Option(0.10, min=0.005, max=5.0, help="Erro máximo de discretização das curvas, em metros."),
    geo_wgs84: bool = typer.Option(False, help="Também transforma o GeoJSON de UTM para WGS84 usando a zona inferida do KML/KMZ."),
) -> None:
    """Analisa eixo, extensão, cortes, aterros e sinalização e gera arquivos de inspeção."""
    _validate_paths(dxf, kmz)
    analysis = analyze_road(dxf, kmz, curve_tolerance_m=tolerancia_curva)
    saida.mkdir(parents=True, exist_ok=True)
    write_analysis_json(analysis, saida / "analise.json")
    write_geojson(analysis, saida / "geometrias_dxf.geojson")
    if geo_wgs84:
        write_geojson(analysis, saida / "geometrias_wgs84.geojson", to_wgs84=True)
    write_svg_preview(analysis, saida / "preview.svg")

    typer.echo("ANÁLISE RODOVIÁRIA")
    typer.echo(f"Extensão geométrica do eixo: {analysis.extension_m/1000:.3f} km")
    if analysis.km_start_m is not None:
        typer.echo(f"Km inicial: {format_station(analysis.km_start_m)}")
        typer.echo(f"Km final:   {format_station(analysis.km_end_m)}")
        typer.echo(f"Intervalo de estaqueamento: {analysis.station_delta_m/1000:.3f} km")
    typer.echo(f"Cortes: {analysis.category_counts.get('cut', 0)}")
    typer.echo(f"Aterros: {analysis.category_counts.get('fill', 0)}")
    typer.echo(f"Sinalização horizontal: {analysis.category_counts.get('marking', 0)}")
    if analysis.offsets:
        typer.echo("Offsets de corte/aterro (mediana):")
        for o in analysis.offsets:
            typer.echo(f"  {o.category:>4} · {o.side:<15} · {o.median_m:8.2f} m · {o.layer}")
    for warning in analysis.warnings:
        typer.echo(f"ATENÇÃO: {warning}")
    typer.echo(f"Arquivos gerados em: {saida.resolve()}")


if __name__ == "__main__":
    app()
