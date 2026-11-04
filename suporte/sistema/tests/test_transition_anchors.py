import numpy as np
from shapely.geometry import box
from test_v1423_motion import connector_fixture
from app.models import ConnectionRule
from app.traffic import tangent


def long_connection():
    net,a,b=connector_fixture()
    a['p']=np.c_[np.linspace(-50,0,60),np.zeros(60)]
    b['p']=np.c_[np.linspace(80,130,60),np.full(60,6.)]
    a['t']=tangent(a['p']);b['t']=tangent(b['p'])
    net.allowed=box(-100,-20,160,30)
    return net,a,b


def test_explicit_transition_preserves_tangency_and_default_distance_limit():
    net,a,b=long_connection()
    assert net.connector(a,b,force=True) is None
    p=net.connector(a,b,force=True,max_gap_m=100)
    assert p is not None
    np.testing.assert_allclose(p[0],a['p'][-1]);np.testing.assert_allclose(p[-1],b['p'][0])
    assert np.all(np.diff(p[:,0])>0)
    assert a['origin']!=b['origin']
    assert net.connector(a,b) is None


def test_transition_still_rejects_median_level_and_wrong_way():
    net,a,b=long_connection();net.allowed=box(-100,-20,30,30).union(box(50,-20,160,30))
    assert net.connector(a,b,force=True,max_gap_m=100) is None
    net,a,b=long_connection();b['level']=1
    assert net.connector(a,b,force=True,max_gap_m=100) is None
    net,a,b=long_connection();a.update(route='r',route_dir='f');b.update(route='r',route_dir='r')
    assert net.connector(a,b,force=True,max_gap_m=100) is None


def test_anchor_range_is_explicit_and_persistent():
    r=ConnectionRule(a={'x':0,'y':0},b={'x':80,'y':6},action='force',max_gap_m=100,from_key='a'*64,to_key='b'*64)
    assert ConnectionRule.model_validate_json(r.model_dump_json()).max_gap_m==100
    assert ConnectionRule(a=r.a,b=r.b).max_gap_m==30
