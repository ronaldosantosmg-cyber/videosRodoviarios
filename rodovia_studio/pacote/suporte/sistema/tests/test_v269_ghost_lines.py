import os
from pathlib import Path
import ezdxf,numpy as np
import pytest
from shapely.geometry import LineString,Polygon,Point
from app.geometry import convert
from app.presentation import dash_segments,resample_stroke,source_segments

@pytest.mark.parametrize('role',['domain','edge_line'])
def test_open_hatch_strokes_never_gain_polygon_closure(role):
    doc=ezdxf.new();h=doc.modelspace().add_hatch();raw=np.array([[730000,7800000],[730100,7800000],[730100,7800020]],float);h.paths.add_polyline_path(raw,is_closed=False)
    entities=[];warnings=[];convert(h,'CAMADA',role,1,entities,warnings)
    assert len(entities)==1 and not entities[0]['closed'] and entities[0]['source_hatch_stroke']
    assert np.array_equal(entities[0]['points'],raw) and len(source_segments(entities[0]))==2
    original=LineString(raw);assert all(original.buffer(1e-7).covers(LineString(s)) for s in source_segments(entities[0]))
    assert warnings


def test_disconnected_hatch_loops_are_not_joined_or_repaired_into_long_diagonals():
    doc=ezdxf.new();h=doc.modelspace().add_hatch();a=[(0,0),(10,0),(10,2)];b=[(100,100),(110,100),(110,102)];h.paths.add_polyline_path(a,is_closed=False);h.paths.add_polyline_path(b,is_closed=False)
    out=[];convert(h,'DOMINIO','domain',1,out,[]);assert len(out)==2
    for e,raw in zip(out,[a,b]):assert np.array_equal(e['points'],raw) and LineString(e['points']).length==12


def test_dashes_and_resampled_borders_preserve_sharp_vertices_and_actual_edges():
    points=np.array([[730000,7800000],[730003,7800000],[730003,7800003],[730007,7800003]],float);source=LineString(points)
    for part in dash_segments(points):assert source.buffer(1e-7).covers(LineString(part))
    q=resample_stroke(points,2)
    assert any(np.array_equal(p,points[1]) for p in q) and any(np.array_equal(p,points[2]) for p in q)
    assert all(source.buffer(1e-7).covers(LineString([a,b])) for a,b in zip(q[:-1],q[1:]))


def test_real_render_and_network_do_not_show_open_hatch_closing_chords(tmp_path):
    from test_v1425_scene3d import project
    from app.render import Scene
    from PIL import Image
    d,s=project(tmp_path);doc=ezdxf.readfile(d/'input.dxf')
    for role,name,y in [('domain','DOMINIO_ABERTO',7800060),('edge_line','BORDO_ABERTO',7800010)]:
        doc.layers.new(name);h=doc.modelspace().add_hatch(dxfattribs={'layer':name});h.paths.add_polyline_path([(500100,y),(500200,y),(500200,y+10)],is_closed=False);s.layers[role]=[name]
    doc.saveas(d/'input.dxf');s.presentation_guides=True;s.imagery_pixels=2048;s.traffic=False;(d/'config.json').write_text(s.model_dump_json());scene=Scene(d,s)
    domain=LineString([(500100,7800060),(500200,7800060),(500200,7800070)]);edge=LineString([(500100,7800010),(500200,7800010),(500200,7800020)])
    assert all(domain.buffer(1e-7).covers(LineString(seg)) for seg in scene.domain_dashes)
    paint=[(a,b) for (a,b,c),src in zip(scene.network.markings,scene.network.mark_src) if src==-2];assert paint and all(edge.buffer(1e-7).covers(LineString([a,b])) for a,b in paint)
    assert scene.network.report_signage['edge_origin']=='DXF'
    out=Path(os.environ.get('VISUAL_ARTIFACTS','/tmp/rs269-artifacts'));out.mkdir(parents=True,exist_ok=True);frame,_=scene.frame(2.8,view=([500170,7800035],220));Image.fromarray(frame).save(out/'269_sem_fechamentos_fantasmas.png')
