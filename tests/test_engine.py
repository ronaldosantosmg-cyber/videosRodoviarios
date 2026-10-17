from pathlib import Path

import ezdxf

from videos_rodoviarios.engine.analyzer import analyze_road
from videos_rodoviarios.geometry.stationing import format_station, parse_station


def make_dxf(path: Path) -> None:
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_lwpolyline([(0, 0, 1.0), (100, 0, 0.0)], format="xyb", dxfattribs={"layer": "F1-HZ-EIXO"})
    msp.add_line((0, 20), (100, 20), dxfattribs={"layer": "OFFSET_CORTE_ESQ"})
    msp.add_line((0, -30), (100, -30), dxfattribs={"layer": "OFFSET_ATERRO_DIR"})
    msp.add_line((0, 3.6), (100, 3.6), dxfattribs={"layer": "SINALIZACAO_HORIZONTAL"})
    msp.add_text("KM 325+000", dxfattribs={"layer": "TEXTOS", "insert": (0, 0)})
    msp.add_text("KM 325+157", dxfattribs={"layer": "TEXTOS", "insert": (100, 0)})
    doc.saveas(path)


def test_stationing():
    assert parse_station("KM 325+850") == 325850
    assert parse_station("325+850") == 325850
    assert format_station(325850) == "325+850"


def test_full_engine_handles_bulge_offsets_and_markings(tmp_path: Path):
    dxf = tmp_path / "road.dxf"
    make_dxf(dxf)
    a = analyze_road(dxf, curve_tolerance_m=0.05)
    assert a.main_centerline_handle
    assert 156.5 < a.extension_m < 157.6
    assert a.category_counts["cut"] == 1
    assert a.category_counts["fill"] == 1
    assert a.category_counts["marking"] == 1
    assert a.km_start_m == 325000
    assert a.km_end_m == 325157
    center = next(e for e in a.entities if e.handle == a.main_centerline_handle)
    assert len(center.points) > 10
    assert len(a.offsets) == 2
    assert all(o.max_m >= o.min_m >= 0 for o in a.offsets)
