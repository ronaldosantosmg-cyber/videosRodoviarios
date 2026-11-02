"""Fase D: vista da cabine."""
import math
import numpy as np
import pytest
import cv2
from test_workflow import drawing,settings
from app.models import Settings,TrafficPath,Point,OAEMark

LANE=[TrafficPath(name='Pista',kind='main',direction='growing',points=[Point(x=500005,y=7799995),Point(x=500295,y=7799995)])]
def S(**kw):
    base={**settings().model_dump(),'derive_traffic_paths':False,'traffic_paths':[t.model_dump() for t in LANE],'duration_s':10}
    return Settings(**{**base,**kw})

def cabin(drawing,**kw):
    from app.render import Scene
    from app.cabin import CabinView
    c={'enabled':True,'start':{'x':500040,'y':7799995},'duration_s':3,**kw.pop('cabin',{})}
    sc=Scene(drawing,S(cabin=c,**kw));return sc,CabinView(sc)

def test_projection_and_motion(drawing):
    sc,cv=cabin(drawing,cabin={'pitch_deg':0,'smoothing_s':0})
    pos,head,h,d=cv.state(0);assert d==pytest.approx(35,abs=1)  # início no ponto clicado
    assert np.allclose(head,[1,0],atol=1e-6) and h==pytest.approx(1.25)
    cam=cv.basis(pos,head,h)
    q,z=cv.project(np.array([[pos[0]+50,pos[1],0.]]),cam)
    # Ponto do chão 50 m à frente: centro horizontal, abaixo do horizonte por atan(h/50).
    assert q[0,0]==pytest.approx(cv.cx) and q[0,1]==pytest.approx(cv.cy+cv.f*h/50) and z[0]==pytest.approx(50)
    # Velocidade e trecho: distância = início + v·t.
    assert cv.state(2)[3]==pytest.approx(d+2*cv.speed,abs=.7)
    assert not cv.reaches_end
    _,long=cabin(drawing,cabin={'duration_s':600});assert long.reaches_end
    assert long.state(1e6)[3]==pytest.approx(long.path['length'])  # fim do trecho: veículo para

def test_frame_layers_sky_ground_hood(drawing):
    sc,cv=cabin(drawing)
    im,meta=cv.frame(1.)
    assert im.shape==(720,1280,3) and meta['mode']=='cabin'
    y_h=int(cv.cy-cv.f*math.tan(math.radians(cv.c.pitch_deg)))
    sky=im[cv.y0+3:y_h-5].reshape(-1,3).mean(0);assert sky[2]>sky[0]  # céu azulado acima do horizonte
    assert im[cv.y1-5,cv.sc.W//2].max()<60  # painel escuro
    assert (im[:20]==im[0,0]).all(axis=2).mean()>.5  # cabeçalho preservado
    _,nohood=cabin(drawing,cabin={'hood':False});b,_=nohood.frame(1.)
    assert np.abs(b[cv.y1-5].astype(int)-im[cv.y1-5]).sum()>0

def test_smoothing_reduces_heading_jitter(drawing):
    from app.models import TrafficPath
    zig=[Point(x=500005+10*i,y=7799995+(.8 if i%2 else -.8)) for i in range(29)]
    lane=[TrafficPath(name='Zigue',kind='main',direction='growing',points=zig).model_dump()]
    _,raw=cabin(drawing,traffic_paths=lane,cabin={'smoothing_s':0})
    _,smooth=cabin(drawing,traffic_paths=lane,cabin={'smoothing_s':2})
    tv=lambda c:np.abs(np.diff(np.arctan2(c.heading[:,1],c.heading[:,0]))).sum()
    assert tv(smooth)<tv(raw)*.5

def test_oae_level_raises_camera_only_on_marked_stretch(drawing):
    oae=[OAEMark(name='Viaduto',start=Point(x=500150,y=7800000),end=Point(x=500250,y=7800000),level_m=8).model_dump()]
    sc,cv=cabin(drawing,oae_marks=oae,cabin={'smoothing_s':0,'duration_s':20})
    hs={x:cv.height[np.argmin(np.abs(cv.path['p'][:,0]-x))] for x in (500060,500200)}
    assert hs[500060]==pytest.approx(1.25) and hs[500200]==pytest.approx(9.25)

def test_start_must_be_on_trajectory(drawing):
    from app.render import Scene
    from app.cabin import CabinView
    sc=Scene(drawing,S(cabin={'enabled':True,'start':{'x':500150,'y':7800080}}))
    with pytest.raises(ValueError,match='trajetória'):CabinView(sc)
    sc=Scene(drawing,S(cabin={'enabled':True}))
    with pytest.raises(ValueError,match='clique'):CabinView(sc)

def test_cabin_video_uses_chosen_duration(drawing):
    from app.render import render
    out=render(drawing,S(cabin={'enabled':True,'start':{'x':500040,'y':7799995},'duration_s':3.5}))
    cap=cv2.VideoCapture(str(out));assert int(cap.get(cv2.CAP_PROP_FRAME_COUNT))==105;cap.release()
    import json;meta=json.loads((drawing/'video.json').read_text(encoding='utf-8'));assert meta['camera']=='cabin' and meta['frames']==105
