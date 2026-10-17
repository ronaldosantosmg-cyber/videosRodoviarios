from pathlib import Path

from videos_rodoviarios.core.models import GeometryEntity, RoadAnalysis
from videos_rodoviarios.render.final_renderer import render_video


def test_render_video_generates_mp4(tmp_path: Path):
    center = GeometryEntity(
        handle="1",
        dxftype="LWPOLYLINE",
        layer="EIXO",
        category="center",
        points=[(0.0, 0.0), (50.0, 0.0), (100.0, 25.0), (150.0, 25.0)],
    )
    cut = GeometryEntity(
        handle="2",
        dxftype="LWPOLYLINE",
        layer="CORTE",
        category="cut",
        points=[(0.0, 20.0), (150.0, 45.0)],
    )
    marking = GeometryEntity(
        handle="3",
        dxftype="LWPOLYLINE",
        layer="SINALIZACAO_HORIZONTAL",
        category="marking",
        points=[(0.0, 1.0), (150.0, 26.0)],
    )
    analysis = RoadAnalysis(
        dxf_path="fixture.dxf",
        kmz_path=None,
        entities=[center, cut, marking],
        texts=[],
        main_centerline_handle="1",
        extension_m=160.0,
        km_start_m=0.0,
        km_end_m=160.0,
        station_delta_m=160.0,
        category_counts={"center": 1, "cut": 1, "marking": 1},
        layer_counts={"EIXO": 1, "CORTE": 1, "SINALIZACAO_HORIZONTAL": 1},
        offsets=[],
    )
    target = tmp_path / "smoke.mp4"
    result = render_video(
        analysis,
        target,
        width=320,
        height=180,
        fps=4,
        duration_s=1,
        imagery=False,
    )
    assert result.exists()
    assert result.stat().st_size > 1000
