import numpy as np
from app.models import POI
from app.structures import bridge_geometry,bus_geometry,draw_structure

def test_bridge_access_on_both_banks():
    p=POI(title='P1',kind='passarela',x=0,y=0).model_dump()
    g=bridge_geometry([0,0],[1,0],p)
    assert len(g['ramps'])==2
    assert np.all(g['ramps'][0][:,1]<=-19)
    assert np.all(g['ramps'][1][:,1]>=19)
    assert len(g['landings'])==8
    assert np.isclose(np.linalg.norm(g['deck'][1]-g['deck'][0]),38)

def test_bus_bay_matches_direction_and_size():
    p=POI(title='B',kind='onibus',x=0,y=0).model_dump()
    a=bus_geometry([0,0],[1,0],p)
    b=bus_geometry([0,0],[1,0],{**p,'bus_side':'left'})
    assert a['pavement'][:,1].min()==-3
    assert b['pavement'][:,1].max()==3
    assert np.dot(a['u'],b['u'])==-1
    assert np.ptp(a['pavement'][:,0])==60

def test_draw_structures_visible():
    im=np.zeros((600,1000,3),np.uint8)
    screen=lambda points:points*5+[500,300]
    for kind in ('passarela','onibus'):
        p=POI(title=kind,kind=kind,x=0,y=0).model_dump()
        anchor=draw_structure(im,p,np.array([1.,0.]),screen,5)
        assert np.isfinite(anchor).all()
    assert np.count_nonzero(im)>10000
