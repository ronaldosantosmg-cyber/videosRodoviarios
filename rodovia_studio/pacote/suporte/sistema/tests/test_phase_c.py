"""Fase C: água em duas camadas, asfalto em metros, OAE, veículos e faróis."""
import numpy as np
import pytest
from test_workflow import drawing,settings
from app.models import Settings
from app import visual

def S(**kw):return Settings(**{**settings().model_dump(),**kw})

def test_texture_is_anchored_in_world_and_scaled_in_metres():
    tex=visual.asphalt()
    # Mesma área do terreno vista com a câmera deslocada 10 px: valores idênticos no trecho comum.
    m=.02;A=np.array([[m,0,700000.],[0,-m,7800000.]]);B=A.copy();B[0,2]+=10*m
    a=tex.sample(A,(64,128),m);b=tex.sample(B,(64,128),m)
    assert np.allclose(a[:,10:],b[:,:-10],atol=1e-4)
    # Grão definido em metros: com zoom aberto a textura é suavizada (não vira ruído de pixel).
    near=tex.sample(np.array([[.01,0,0],[0,-.01,0]]),(100,100),.01)  # 1 m x 1 m a 1 cm/px
    assert near.std()>.1  # aproximando, o grão continua visível
    far=[tex.sample(np.array([[k,0,0],[0,-k,0]]),(128,128),k) for k in (.2,2.,8.)]
    hf=[float(np.abs(np.diff(f,axis=1)).mean()) for f in far]
    assert hf[0]>hf[1]>hf[2] and hf[2]<.05  # afastando, sem cintilação de pixel
    # Ladrilho contínuo: período de 20,48 m sem costura.
    p=visual.TEX*visual.TEXEL_M;C=A.copy();C[0,2]+=p
    assert np.allclose(tex.sample(A,(32,32),m),tex.sample(C,(32,32),m),atol=1e-3)

def test_water_layers_classic_formula_soft_edge_and_no_invented_banks():
    img=np.full((60,60,3),100,np.uint8);mask=np.zeros((60,60),np.uint8);mask[10:50,10:50]=255
    classic=img.copy();visual.water_paint(classic,mask,.5,.65,False)
    ys,xs=np.nonzero(mask);blue=np.zeros((len(xs),3),np.float32);blue[:]=(42,128,185);blue+=((np.sin(xs*.19+ys*.055)+np.cos(ys*.23))*5)[:,None]
    ref=img.copy();ref[ys,xs]=np.clip(img[ys,xs]*(1-.65)+blue*.65,0,255).astype(np.uint8)
    assert np.array_equal(classic,ref)  # modo anterior preservado
    new=img.copy();visual.water_paint(new,mask,.5,.65,True)
    assert np.array_equal(new[mask==0],img[mask==0])  # nada fora dos polígonos
    d_edge=np.abs(new[10,30].astype(int)-100).sum();d_mid=np.abs(new[30,30].astype(int)-100).sum()
    assert d_edge<d_mid  # transição suave na margem
    off=img.copy();visual.water_paint(off,mask,.5,0.,True);assert np.array_equal(off,img)  # opacidade zero

def test_water_ripple_only_inside_and_animated():
    v=np.full((40,40,3),120,np.uint8);wm=np.zeros((40,40),np.uint8);wm[5:35,5:35]=255;A=np.array([[.5,0,0],[0,-.5,0]])
    a=v.copy();visual.water_ripple(a,wm,A,0.);b=v.copy();visual.water_ripple(b,wm,A,1.)
    assert np.array_equal(a[wm==0],v[wm==0]) and not np.array_equal(a,b)

def test_water_toggles_are_independent(drawing,monkeypatch):
    import app.hydrography as h
    from app.render import Scene
    data={'type':'FeatureCollection','source':'teste','features':[{'type':'Feature','properties':{'name':'Lagoa Teste'},'geometry':{'type':'Polygon','coordinates':[[]]}}]}
    from pyproj import Transformer
    tr=Transformer.from_crs(31983,4326,always_xy=True);ring=[tr.transform(x,y) for x,y in [(500050,7800030),(500250,7800030),(500250,7800080),(500050,7800080),(500050,7800030)]]
    data['features'][0]['geometry']['coordinates']=[ring]
    monkeypatch.setattr(h,'fetch',lambda *a:data)
    base=Scene(drawing,S(hydrography=False)).map
    tex=Scene(drawing,S(hydrography=True,water_names=False))
    names=Scene(drawing,S(hydrography=True,water_texture=False))
    assert not np.array_equal(tex.map,base) and np.array_equal(names.map,base)
    view=((500150,7800055),260)
    a,_=tex.frame(0,view=view);b,_=names.frame(0,view=view);c,_=Scene(drawing,S(hydrography=True,water_texture=False,water_names=False)).frame(0,view=view)
    assert not np.array_equal(b,c)  # só nomes: texto desenhado
    half=Scene(drawing,S(hydrography=True,water_texture=False,water_names_opacity=.5)).frame(0,view=view)[0]
    assert np.abs(half.astype(int)-c).sum()<np.abs(b.astype(int)-c).sum()

def test_enhanced_pavement_differs_classic_kept(drawing):
    from app.render import Scene
    view=((500150,7800000),90)
    a=Scene(drawing,S(visual_quality='classic',traffic=False)).frame(0,view=view)[0]
    b=Scene(drawing,S(visual_quality='enhanced',traffic=False)).frame(0,view=view)[0]
    assert np.abs(a.astype(int)-b.astype(int)).sum()>0
    c=Scene(drawing,S(visual_quality='classic',traffic=False)).frame(0,view=view)[0]
    assert np.array_equal(a,c)

def test_vehicle_types_colors_and_headlights(drawing):
    from app.render import Scene
    kinds=[visual.vehicle_type(['main'],(i,k,0)) for i in range(20) for k in range(16)]
    assert {'car','truck','bus'}<=set(kinds) and kinds.count('car')>len(kinds)/2
    assert all(visual.vehicle_type(['device'],(i,k,0))=='car' for i in range(10) for k in range(5))
    assert visual.vehicle_type(['main'],(3,2,1))==visual.vehicle_type(['main'],(3,2,1))
    assert len({visual.vehicle_color((i,0,0),'car') for i in range(30)})>5
    im=np.zeros((200,300,3),np.uint8);scr=lambda p:np.asarray(p)*5+[150,100]
    for vt in ('car','truck','bus'):
        x=im.copy();visual.draw_vehicle(x,np.array([0.,0.]),np.array([1.,0.]),vt,(200,40,40),scr,.2);assert np.count_nonzero(x)>50
    beams=np.zeros_like(im);visual.headlight_beam(beams,np.array([0.,0.]),np.array([1.,0.]),'car',scr)
    assert beams[100+8,150+40].any() and not beams[100+8,150-40].any()  # feixe só à frente
    from app.models import TrafficPath,Point
    lane=[TrafficPath(name='Pista',kind='main',direction='growing',points=[Point(x=500005,y=7799995),Point(x=500295,y=7799995)])]
    sc_off=Scene(drawing,S(headlights=False,derive_traffic_paths=False,traffic_paths=lane,duration_s=60));sc_on=Scene(drawing,S(headlights=True,derive_traffic_paths=False,traffic_paths=lane,duration_s=60))
    assert sc_off.network.paths
    t=next(t for t in np.arange(0,60,.1) if any(abs(p[0]-500150)<40 for p,*_ in sc_off.network.vehicles(t,70/3.6)))
    a=sc_off.frame(t,view=((500150,7800000),120))[0].astype(int);b=sc_on.frame(t,view=((500150,7800000),120))[0].astype(int)
    assert (b-a).sum()>0  # faróis acesos clareiam

def test_oae_shadow_outside_deck():
    im=np.full((100,100,3),200,np.uint8);ring=np.array([[0,0],[20,0],[20,6],[0,6],[0,0]],float)
    scr=lambda p:np.asarray(p)*3+[10,40]
    visual.cast_shadow(im,ring,8,scr)
    assert im[52,40].max()==200  # dentro do tabuleiro (y=4 m): sem sombra
    assert im[int(40+(-4.4+1)*3),int(10+(2.8+10)*3)].max()<200  # deslocada pelo nível
    flat=np.full((100,100,3),200,np.uint8);visual.cast_shadow(flat,ring,0,scr);assert (flat==200).all()
