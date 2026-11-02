import json
from pathlib import Path

import ezdxf

from videos_rodoviarios.engine.analyzer import analyze_road
from videos_rodoviarios.export.geojson_export import write_geojson
from videos_rodoviarios.export.json_export import write_analysis_json
from videos_rodoviarios.export.svg_preview import write_svg_preview
from videos_rodoviarios.io.kml_reader import read_kml_context


def test_kml_context_and_exports(tmp_path: Path):
    kml = tmp_path / "context.kml"
    kml.write_text('''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark><name>KM 411+000</name><LineString><coordinates>-43.9,-19.9,0 -43.8,-19.8,0</coordinates></LineString></Placemark><Placemark><name>KM 412+000</name></Placemark></Document></kml>''', encoding="utf-8")
    ctx = read_kml_context(kml)
    assert ctx.utm_zone == 23
    assert ctx.hemisphere == "S"
    assert min(ctx.station_values_m) == 411000
    assert max(ctx.station_values_m) == 412000

    dxf = tmp_path / "road.dxf"
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_line((600000, 7800000), (601000, 7800000), dxfattribs={"layer": "EIXO"})
    msp.add_line((600000, 7800010), (601000, 7800010), dxfattribs={"layer": "CORTE"})
    doc.saveas(dxf)
    a = analyze_road(dxf, kml)

    j = write_analysis_json(a, tmp_path / "analysis.json")
    g = write_geojson(a, tmp_path / "road.geojson")
    s = write_svg_preview(a, tmp_path / "road.svg")
    assert json.loads(j.read_text(encoding="utf-8"))["extension_m"] == 1000.0
    assert json.loads(g.read_text(encoding="utf-8"))["features"]
    svg = s.read_text(encoding="utf-8")
    assert "stroke-linecap=\"round\"" in svg
    assert "#ef4444" in svg
