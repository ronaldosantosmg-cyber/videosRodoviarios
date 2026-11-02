import numpy as np
from shapely.geometry import box
from app.flow_tools import cut_raw_paths,join_segments
from app.models import FlowCut,Settings
from app.traffic import TrafficNetwork


def test_explicit_cut_removes_only_the_interval_and_keeps_source_array():
    points=np.array([[0.,0.],[300.,0.]]);copy=points.copy()
    cuts=[FlowCut(start=dict(x=120,y=0),end=dict(x=180,y=0))]
    pieces,report=cut_raw_paths([dict(points=points,origin=0)],cuts)
    assert report[0]['status']=='applied' and report[0]['excluded_m']==60
    assert len(pieces)==2 and pieces[0]['points'][-1,0]==120 and pieces[1]['points'][0,0]==180
    np.testing.assert_array_equal(copy,points)
    s=Settings(derive_traffic_paths=False,flow_cuts=cuts,signage_detail='basic')
    n=TrafficNetwork([box(-10,-10,310,10)],[],[dict(points=points)],points,np.array([0.,300.]),s)
    assert n.paths and not any(p['p'][:,0].min()<120 and p['p'][:,0].max()>180 for p in n.paths)


def test_join_keeps_one_way_direction_and_rejects_an_impossible_connection():
    a=dict(points=[[0,0],[100,0]],forward=True,both=False,level=0)
    b=dict(points=[[105,0],[200,0]],forward=True,both=False,level=0)
    result=join_segments(a,b,box(-10,-10,210,10),50)
    assert result['ok'] and result['points'][0]==[0.,0.] and result['points'][-1]==[200.,0.]
    import pytest
    with pytest.raises(ValueError):join_segments(a,{**b,'level':1},box(-10,-10,210,10),50)
    with pytest.raises(ValueError):join_segments(a,{**b,'points':[[200,0],[300,0]]},box(-10,-10,310,10),50)


def test_cut_with_an_unknown_geometry_identity_does_not_modify_a_parallel_axis():
    points=np.array([[0.,0.],[300.,0.]])
    cut=FlowCut(start=dict(x=100,y=0),end=dict(x=120,y=0),target_key='a'*64)
    pieces,report=cut_raw_paths([dict(points=points,origin=0,origin_key='b'*64)],[cut])
    assert report[0]['status']=='unmatched' and len(pieces)==1
    np.testing.assert_array_equal(pieces[0]['points'],points)


def test_cutting_out_a_manual_disable_anchor_never_reenables_the_remaining_axis():
    points=np.array([[0.,0.],[300.,0.]])
    s=Settings(derive_traffic_paths=False,signage_detail='basic',flow_overrides=[dict(id='disabled-before-cut',x=150,y=0,action='disable')],flow_cuts=[dict(start=dict(x=120,y=0),end=dict(x=180,y=0))])
    n=TrafficNetwork([box(-10,-10,310,10)],[],[dict(points=points)],points,np.array([0.,300.]),s)
    assert not n.paths
    assert n.raw_info and all(row['disabled'] for row in n.raw_info)
    assert all('disabled-before-cut' in row['override_ids'] for row in n.raw_info)
    assert s.flow_overrides[0].enabled
