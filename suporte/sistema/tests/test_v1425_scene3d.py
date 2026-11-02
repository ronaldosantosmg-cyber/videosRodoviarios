import json,hashlib
from pathlib import Path
import numpy as np
import ezdxf
import pytest
from app.models import Settings
from app.scene3d import build,revision


def project(tmp_path,traffic=True,hole=False):
    d=tmp_path;doc=ezdxf.new();doc.layers.new('EIXO');doc.layers.new('PAVIMENTO');m=doc.modelspace()
    m.add_lwpolyline([(500050,7800000),(500450,7800000)],dxfattribs={'layer':'EIXO'})
    h=m.add_hatch(dxfattribs={'layer':'PAVIMENTO'});h.paths.add_polyline_path([(500000,7799980),(500500,7799980),(500500,7800020),(500000,7800020)],is_closed=True)
    if hole:h.paths.add_polyline_path([(500200,7800008),(500260,7800008),(500260,7800018),(500200,7800018)],is_closed=True,flags=0)
    doc.saveas(d/'input.dxf');s=Settings(layers={'axis':['EIXO'],'pavement':['PAVIMENTO']},width=1280,fps=24,duration_s=3,imagery='neutral',coordinates_confirmed=True,hydrography=False,traffic=traffic)
    (d/'config.json').write_text(s.model_dump_json());return d,s


def test_scene_uses_local_origin_and_original_geometry_with_real_tracks(tmp_path):
    d,s=project(tmp_path);before=(d/'input.dxf').read_bytes();result=build(d,s)
    assert result['format']=='rodovia-scene3d-1' and result['revision']==revision(d)
    assert result['meshes'] and result['vehicles'] and result['simulation_report']['rear_collisions']==0
    assert result['terrain']['elevation_available'] is False and 'plano' in result['terrain']['label']
    assert abs(result['origin_crs'][0]-500250)<1 and abs(result['origin_crs'][1]-7800000)<1
    assert max(abs(v) for m in result['meshes'] for v in m['positions'])<1000
    for v in result['vehicles']:
        values=np.array(v['samples']);assert np.isfinite(values).all() and values.shape[1]==7
        assert np.allclose(np.linalg.norm(values[:,4:],axis=1),1,atol=1e-6)
    assert (d/'input.dxf').read_bytes()==before
    assert (d/'analysis.json').exists() and (d/'editor.json').exists()
    json.dumps(result,allow_nan=False)


def test_triangle_holes_are_not_filled_and_cache_revision_changes(tmp_path):
    d,s=project(tmp_path,False,True);result=build(d,s);triangles=np.concatenate([np.array(m['positions']).reshape(-1,3,3) for m in result['meshes'] if m['role']=='pavement'])
    area=np.sum(np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1)/2)
    assert area==pytest.approx(500*40-60*10,abs=.01)
    assert not result['vehicles'];initial=result['revision'];s.min_route_segment_m=120;(d/'config.json').write_text(s.model_dump_json())
    assert revision(d)!=initial


def test_modified_project_or_cancellation_cannot_publish_stale_scene(tmp_path):
    d,s=project(tmp_path)
    def changed(p,m):
        if p>=.3:
            other=s.model_copy(update={'name':'Alterado'});(d/'config.json').write_text(other.model_dump_json())
    with pytest.raises(ValueError,match='mudou'):build(d,s,status=changed)
    assert not (d/'scene3d.json').exists()
    (d/'config.json').write_text(s.model_dump_json())
    with pytest.raises(InterruptedError):build(d,s,cancel=lambda:True)
    assert not (d/'scene3d.json').exists()


def test_3d_endpoints_reject_missing_and_stale_cache(tmp_path,monkeypatch):
    from fastapi.testclient import TestClient
    from app.server import app
    from app import store
    d,s=project(tmp_path);monkeypatch.setattr(store,'directory',lambda pid:d);client=TestClient(app)
    assert client.get('/api/projects/test/scene3d.json').status_code==404
    build(d,s);assert client.get('/api/projects/test/scene3d.json').status_code==200
    s.min_route_segment_m=200;(d/'config.json').write_text(s.model_dump_json())
    assert client.get('/api/projects/test/scene3d.json').status_code==409
    assert client.get('/vendor/three/build/three.module.js').status_code==200
    assert client.get('/webgl/viewer.mjs').status_code==200
