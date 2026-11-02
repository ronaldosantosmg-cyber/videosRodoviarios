from test_workflow import drawing
import json
import numpy as np
from shapely.geometry import LineString,box,Polygon
from app.models import Settings,TrafficPath,Point
from app.traffic import TrafficNetwork,valid_centers
from app.hydrography import Hydrography

def test_right_hand_traffic_and_connected_return():
    axis=np.array([[0.,0.],[200.,0.]]);ds=np.array([0.,200.])
    bottom=np.array([[0.,-7.],[180.,-7.]]);top=np.array([[180.,7.],[0.,7.]])
    angle=np.linspace(-np.pi/2,np.pi/2,90);turn=np.column_stack([180+7*np.cos(angle),7*np.sin(angle)])
    roads=[LineString(np.vstack([bottom,turn[1:],top[1:]])).buffer(4,cap_style=2)]
    s=Settings(derive_traffic_paths=False,hydrography=False,traffic_paths=[TrafficPath(name='Retorno nativo',kind='return',points=[Point(x=x,y=y) for x,y in turn])])
    n=TrafficNetwork(roads,[box(0,-2,174,2)],[{'points':bottom},{'points':top}],axis,ds,s)
    for e in n.edges:
        if e['kind']=='main':
            assert e['sign']==(1 if e['p'][:,1].mean()<0 else -1)
    return_paths=[p for p in n.paths if 'return' in p['kinds'] and p['length']>300]
    assert return_paths,n.report
    for p in return_paths:
        assert valid_centers(n.allowed,p['p']).all()
        assert np.linalg.norm(np.diff(p['p'],axis=0),axis=1).max()<.7
        assert p['p'][0,1]<0 and p['p'][-1,1]>0

def test_hydro_clips_names_and_cache_offline(tmp_path,monkeypatch):
    import app.hydrography as m
    data={'type':'FeatureCollection','source':'IBGE teste','features':[{'type':'Feature','properties':{'name':'Rio de teste'},'geometry':{'type':'LineString','coordinates':[[-43.001,-19.8],[-43.,-19.8]]}}]}
    monkeypatch.setattr(m,'fetch',lambda *args:data)
    from pyproj import Transformer
    tr=Transformer.from_crs(4326,31983,always_xy=True);x,y=tr.transform(-43.,-19.8);bounds=[x-200,y-200,x+200,y+200]
    s=Settings(hydrography=True);a=Hydrography(tmp_path,s,bounds)
    assert len(a.lines)==1 and a.labels[0][0]=='Rio de teste'
    monkeypatch.setattr(m,'fetch',lambda *args:(_ for _ in ()).throw(AssertionError('Cache deveria evitar rede')))
    b=Hydrography(tmp_path,s,bounds);assert len(b.lines)==1

def test_no_turn_at_grade_separated_crossing():
    from app.traffic import tangent
    axis=np.array([[-50.,0.],[50.,0.]])
    n=TrafficNetwork([box(-55,-6,55,6),box(-6,-55,6,55)],[],[{'points':axis}],axis,np.array([0.,100.]),Settings(derive_traffic_paths=False,hydrography=False),[box(-8,-8,8,8)])
    node=n.node(np.array([0.,0.]),0)
    a={'t':np.array([[1.,0.]]),'p':np.array([[-3.,0.]]),'end':node}
    b={'t':np.array([[0.,1.]]),'p':np.array([[0.,3.]])}
    assert n.connector(a,b) is None

def test_short_video_stable_camera_and_cad_median_preserved(drawing):
    from app.render import Scene,poly
    from test_workflow import settings
    sc=Scene(drawing,settings())
    a=sc.pose(0);b=sc.pose(1.5);c=sc.pose(2.99)
    assert np.array_equal(a[0],b[0]) and np.array_equal(b[0],c[0])
    assert c[1]>.9*a[1]
    assert a[2]==b[2]==c[2]==1
    medians=[poly(e) for e in sc.items if e['role']=='median']
    assert len(medians)==1 and abs(medians[0].area-600)<1e-5
    assert medians[0].bounds==(500000.,7799999.,500300.,7800001.)

def test_existing_road_role_without_geometry_changes(tmp_path):
    import ezdxf
    from app.geometry import analyze
    from test_workflow import settings
    d=ezdxf.new();d.layers.new('EIXO');d.layers.new('GE_SC-HPAV_EXIST');m=d.modelspace()
    m.add_lwpolyline([(0,0),(100,0)],dxfattribs={'layer':'EIXO'})
    p=[(0,-5),(100,-5),(100,5),(0,5)]
    m.add_lwpolyline(p,close=True,dxfattribs={'layer':'GE_SC-HPAV_EXIST'});d.saveas(tmp_path/'input.dxf')
    entities,*_=analyze(tmp_path,settings())
    e=next(e for e in entities if e['role']=='existing_pavement')
    assert np.array_equal(e['points'][:4],p)
