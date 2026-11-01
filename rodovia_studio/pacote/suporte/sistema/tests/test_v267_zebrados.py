import math,os
from pathlib import Path
import numpy as np
import pytest
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from app.models import HatchArea
from app.signage import zebra,WHITE,YELLOW
POINTS=[{'x':0,'y':0},{'x':24,'y':0},{'x':24,'y':8},{'x':0,'y':8}]
@pytest.mark.parametrize('change',[{'stripe_width_m':0},{'stripe_width_m':float('nan')},{'spacing_m':1,'stripe_width_m':1},{'angle_deg':float('inf')},{'points':[{'x':0,'y':0}]*3,'world_aligned':True},{'points':[{'x':0,'y':0},{'x':5,'y':5},{'x':5,'y':0},{'x':0,'y':5}],'world_aligned':True}])
def test_invalid_paint_is_refused_before_committing(change):
    with pytest.raises(ValueError):HatchArea.model_validate({'points':POINTS,**change})
@pytest.mark.parametrize('angle',[-45,0,45,135])
def test_metric_stripes_preserve_holes_and_stay_inside(angle):
    area=box(0,0,24,8).difference(box(5,2,9,6));paint,lines=zebra(area,math.radians(angle),YELLOW,2.6,.45,True)
    assert paint and lines
    for rings,color in paint:
        p=Polygon(rings[0],rings[1:]);assert p.is_valid and area.buffer(1e-8).covers(p) and color==YELLOW
        n=np.array([-math.sin(math.radians(angle)),math.cos(math.radians(angle))]);assert np.ptp(np.asarray(p.exterior.coords)@n)<=.450001

def test_anchor_does_not_shift_when_area_is_extended():
    a,_=zebra(box(0,0,20,10),math.pi/4,WHITE,2.6,.45,True);b,_=zebra(box(-10,-10,30,20),math.pi/4,WHITE,2.6,.45,True)
    def union(p):return unary_union([Polygon(r[0],r[1:]) for r,_ in p])
    inner=box(1,1,19,9);assert union(a).intersection(inner).symmetric_difference(union(b).intersection(inner)).area<1e-7

def test_legacy_and_budget():
    h=HatchArea(points=POINTS);assert h.stripe_width_m==.45 and not h.world_aligned
    with pytest.raises(ValueError,match='extenso'):zebra(box(0,0,100000,100000),0,WHITE)

def test_paint_reaches_video_and_webgl_without_changing_routes(tmp_path):
    from test_v264_presentation import sample
    from app.render import Scene,render
    from app.scene3d import build
    from app.encoding import ffmpeg_exe,validate_mp4
    from PIL import Image
    d,s=sample(tmp_path);s.traffic=True;s.duration_s=3
    before=Scene(d,s);old=[p['p'].copy() for p in before.network.paths]
    s.hatch_areas=[HatchArea(points=[{'x':500180,'y':7800001},{'x':500200,'y':7800001},{'x':500200,'y':7800006},{'x':500180,'y':7800006}],color='yellow',angle_deg=-45,stripe_width_m=.6,spacing_m=2,world_aligned=True)]
    (d/'config.json').write_text(s.model_dump_json());scene=Scene(d,s)
    assert len(old)==len(scene.network.paths) and all(np.array_equal(a,b) for a,b in zip(old,[p['p'] for p in scene.network.paths]))
    assert any(col==YELLOW for rings,col in scene.network.fills)
    frame,_=scene.frame(2.8,view=([500190,7800000],60));evidence=Path(os.environ.get('VISUAL_ARTIFACTS','/tmp/rs267-artifacts'));evidence.mkdir(parents=True,exist_ok=True);Image.fromarray(frame).save(evidence/'267_zebrado_render.png')
    data=build(d,s);assert any(m['role']=='road_paint' and m['color']=='#f4c846' and len(m['positions'])>=9 for m in data['meshes'])
    assert validate_mp4(ffmpeg_exe(),render(d,s),72,1280,720,24)['ok']


def test_webgl_handles_disjoint_letters_and_holes_in_physical_paint(tmp_path,monkeypatch):
    from test_v264_presentation import sample
    from app import signage
    from app.scene3d import build
    d,s=sample(tmp_path)
    old=signage.build
    def with_letters(net,*args):
        old(net,*args)
        outer=np.array([[500100,7800001],[500105,7800001],[500105,7800006],[500100,7800006]])
        hole=np.array([[500101,7800002],[500102,7800002],[500102,7800003],[500101,7800003]])
        net.fills.append(([outer,hole,outer+np.array([10,0])],WHITE))
    monkeypatch.setattr(signage,'build',with_letters)
    data=build(d,s)
    assert any(m['role']=='road_paint' and len(m['positions'])>18 for m in data['meshes'])
