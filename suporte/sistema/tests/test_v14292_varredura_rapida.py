"""2.60: varredura de colisão sem Polígonos intermediários e interpolação única dos eixos devem dar o mesmo resultado."""
import numpy as np
from shapely.geometry import MultiPoint
from app import vehicle_motion as vm
from app.vehicle_safety import PolygonSafety,body,body_corners,LATERAL_BUFFER,PROFILES

def _antigo(p,d,vehicle,s):
    L,B,wb,_=vm.PROFILES[vehicle];s=np.asarray(s,float)
    c=vm.interpolate(p,d,s);f=vm.interpolate(p,d,s+wb/2);r=vm.interpolate(p,d,s-wb/2)
    h=f-r;h=h/np.maximum(np.linalg.norm(h,axis=1)[:,None],1e-9);return c,h

def test_eixos_identicos_ao_calculo_separado():
    rng=np.random.default_rng(3);p=np.cumsum(rng.normal(size=(40,2))*5+[8,0],axis=0);p,d=vm.prepare_points(p)
    for t in ('car','carreta','moto'):
        s=np.linspace(-5,d[-1]+5,57);g=vm.axle_geometry_prepared(p,d,t,s);c,h=_antigo(p,d,t,s)
        assert np.array_equal(g['center'],c) and np.array_equal(g['heading'],h)

def test_cantos_iguais_ao_poligono():
    c=(10.,3.);h=(.6,.8)
    a=np.array(body(c,h,4.5,1.8,LATERAL_BUFFER).exterior.coords)[:4];b=np.array(body_corners(c,h,4.5,1.8,LATERAL_BUFFER))
    assert np.array_equal(a,b)

def test_varredura_igual_ao_metodo_antigo():
    rng=np.random.default_rng(5);p=np.cumsum(rng.normal(size=(30,2))*3+[10,1],axis=0);p,d=vm.prepare_points(p)
    class Sim:motion_points=[(p,d)];time=0
    s=PolygonSafety(Sim())
    for t in ('car','truck','carreta'):
        for pos in (3.,40.,120.):
            for fw in (0.,.2,1.7,6.):
                v={'p':0,'s':pos,'t':t,'id':1}
                import math
                if fw<1e-9:ref=s.footprint(v)
                else:
                    pts=[]
                    for ds in np.linspace(0,fw,max(3,min(17,int(math.ceil(fw/.5))+1))):pts.extend(s.footprint(v,float(ds),.2*float(ds)/fw).exterior.coords)
                    ref=MultiPoint(pts).convex_hull
                    ref=ref.buffer(.03) if np.linalg.norm(s.pose(v)[1]-s.pose(v,fw)[1])>.002 else ref
                got=s.sweep(v,fw)
                assert ref.symmetric_difference(got).area<1e-9
