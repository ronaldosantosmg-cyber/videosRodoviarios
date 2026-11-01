"""DXF adiantado sem criar fechamentos ou alterar os dados técnicos."""
import os
from pathlib import Path
import numpy as np
import pytest
from scipy.spatial import cKDTree
from app.presentation import source_segments,contour_runs,DXFAdvance
from app.models import Settings


def test_virtual_hatch_chord_is_not_a_drawn_edge_even_when_split():
    e={'points':np.array([[0,0],[20,0],[20,20],[10,10],[0,0]]),'closed':True,'virtual':[[[20,20],[0,0]]]}
    p=source_segments(e)
    assert p.shape==(2,2,2)
    assert np.array_equal(p[0],[[0,0],[20,0]]) and np.array_equal(p[1],[[20,0],[20,20]])
    runs=contour_runs(e);assert len(runs)==1 and np.array_equal(runs[0],[[0,0],[20,0],[20,20]])


def test_leading_dxf_is_clipped_to_front_and_never_connects_separate_entities():
    axis=np.c_[np.arange(101),np.zeros(101)];tree=cKDTree(axis);chain=np.arange(101)
    items=[{'role':'pavement','points':[[0,-4],[100,-4]],'closed':False},{'role':'shoulder','points':[[0,4],[100,4]],'closed':False}, {'role':'domain','points':[[0,-50],[100,50]],'closed':False}]
    d=DXFAdvance(items,tree,chain);p=d.window(40,20)
    assert p.shape==(2,2,2) and np.allclose(p[:,:,0],[[40,60],[40,60]])
    assert np.allclose(p[:,:,1],[[-4,-4],[4,4]])
    assert not len(d.window(40,0))
    assert items[0]['points']==[[0,-4],[100,-4]]


def test_guide_and_dxf_lead_changes_do_not_invalidate_static_3d_or_read_dxf(tmp_path):
    from app.dependencies import revisions,geometry_cache_key
    s=Settings();b=s.model_copy(update={'dxf_lead_m':45,'presentation_guides':True})
    a=revisions(tmp_path,s);c=revisions(tmp_path,b)
    assert a['geometry']==c['geometry'] and a['traffic']==c['traffic'] and a['scene3d']==c['scene3d']
    assert a['video']!=c['video'] and geometry_cache_key(tmp_path,s)==geometry_cache_key(tmp_path,b)
    for bad in (-1,151,float('nan'),float('inf'),''):
        with pytest.raises(ValueError):Settings(dxf_lead_m=bad)


def test_real_construction_frame_draws_dxf_ahead_then_keeps_final_texture(tmp_path):
    from test_v264_presentation import sample
    from app.render import Scene
    from PIL import Image
    d,s=sample(tmp_path);s.dxf_lead_m=0;scene=Scene(d,s);cam=np.array([500250,7800010]);width=650
    base=scene.draw_base(cam,width,.4);scene.s.dxf_lead_m=30
    lead=scene.draw_base(cam,width,.4);done=scene.draw_base(cam,width,1.)
    difference=np.any(base!=lead,axis=2);assert difference.sum()>30
    pts=np.c_[500210+np.linspace(0,30,31),np.full(31,7800020.)]
    pixels=np.rint(scene.screen(pts,cam,width)).astype(int)
    assert any(difference[y,x] for x,y in pixels if 0<=x<scene.W and 0<=y<scene.H)
    scene.s.dxf_lead_m=0;assert np.array_equal(done,scene.draw_base(cam,width,1.))
    if os.environ.get('VISUAL_ARTIFACTS'):
        out=Path(os.environ['VISUAL_ARTIFACTS']);out.mkdir(parents=True,exist_ok=True)
        for image,name in [(base,'266_frente_sem_avanco'),(lead,'266_frente_dxf'),(done,'266_obra_concluida')]:Image.fromarray(image).save(out/(name+'.png'))


def test_3d_fill_cut_pigments_and_manual_colors_are_preserved(tmp_path):
    from test_v264_presentation import sample
    from app.scene3d import build
    from app.presentation import ART_COLORS
    d,s=sample(tmp_path);data=build(d,s)
    for role in ('cut','fill'):
        meshes=[m for m in data['meshes'] if m['role']==role]
        assert meshes and all(m['color']==ART_COLORS[role] for m in meshes)
    s.role_colors['fill']='#3355aa';(d/'config.json').write_text(s.model_dump_json());data=build(d,s)
    assert all(m['color']=='#3355aa' for m in data['meshes'] if m['role']=='fill')
