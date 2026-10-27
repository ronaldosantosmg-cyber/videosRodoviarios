import numpy as np
import pytest
from types import SimpleNamespace
from shapely.geometry import box,Polygon
from app.models import Settings,RouteAlignment
from app.routes import build_lanes
from app.image_context import segment,accepted_items
from app.vehicle_safety import body,SpatialReservations,LATERAL_BUFFER,LATERAL_CLEARANCE
from app.vehicle_motion import PROFILES


def route(**kw):return RouteAlignment(id='r',name='Eixo genérico',points=[dict(x=0,y=0),dict(x=600,y=0)],**kw)
def section(**kw):return dict(id='s',start_m=0,end_m=600,type='simples',left=[dict(kind='pista',width_m=3.5)],right=[dict(kind='pista',width_m=3.5),dict(kind='acostamento',width_m=2.5),dict(kind='seguranca',width_m=1)],**kw)


def test_section_makes_only_driving_lanes_and_keeps_asymmetric_offsets():
    s=section();s['left'].append(dict(kind='pista',width_m=3.5));lanes=build_lanes(route(cross_sections=[s]))
    assert len(lanes)==3
    assert sorted(round(float(p['points'][100,1]),2) for p in lanes)==[-1.75,1.75,5.25]
    assert sum(p['dir']=='f' for p in lanes)==1 and sum(p['dir']=='r' for p in lanes)==2

@pytest.mark.parametrize('bad',[None,'',float('nan'),float('inf'),0,-1])
def test_section_rejects_invalid_width(bad):
    s=section();s['right'][0]['width_m']=bad
    with pytest.raises(ValueError):route(cross_sections=[s])


def test_sections_cannot_overlap_or_run_past_axis_or_drive_on_nonroad_bands():
    with pytest.raises(ValueError):route(cross_sections=[section(),section()])
    s=section();s['end_m']=601
    with pytest.raises(ValueError):route(cross_sections=[s])
    s=section();s['left'][0]['kind']='acostamento'
    with pytest.raises(ValueError):route(cross_sections=[s])


def test_shared_work_lane_has_opposite_directions_without_changing_source():
    r=route();source=r.model_dump();s=Settings(route_alignments=[r],alternating_zones=[dict(id='z',route_id='r',start_m=150,end_m=350)])
    lanes=build_lanes(r,s);assert len(lanes)==2
    for lane in lanes:
        near=lane['points'][(lane['points'][:,0]>200)&(lane['points'][:,0]<300)]
        assert np.max(np.abs(near[:,1]+1.75))<.01
    assert lanes[0]['dir']!=lanes[1]['dir'] and r.model_dump()==source
    with pytest.raises(ValueError):Settings(route_alignments=[r],alternating_zones=[dict(id='z',route_id='r',start_m=10,end_m=350)])
    with pytest.raises(ValueError):Settings(route_alignments=[route(type='dupla')],alternating_zones=[dict(id='z',route_id='r',start_m=150,end_m=350)])


def test_requested_vehicle_widths_and_lateral_reservation():
    assert all(PROFILES[k][1]==3 for k in ['truck','bus','carreta'])
    assert all(PROFILES[k][1]==1.8 for k in ['car','van','pickup']) and PROFILES['moto'][1]==.8
    assert LATERAL_CLEARANCE==.3 and LATERAL_BUFFER==.15
    reservation=SpatialReservations();reservation.add(1,body([100,0],[1,0],12,3,LATERAL_BUFFER))
    assert reservation.clear(2,body([100,3.3],[1,0],12,3,LATERAL_BUFFER))
    assert not reservation.clear(2,body([100,3.29],[1,0],12,3,LATERAL_BUFFER))
    with pytest.raises(ValueError):body([np.nan,0],[1,0],4,1.8)


def aerial():
    a=np.full((128,128,3),[100,100,100],np.uint8);a[10:55,10:55]=[200,75,45];a[70:115,10:55]=[30,150,30];a[20:100,80:110]=[25,65,180];return a


def test_image_segmentation_is_reproducible_grouped_georeferenced_and_not_auto_approved():
    kwargs=dict(clusters=5,min_area_m2=5,samples=[dict(x=25,y=100,role='building')])
    result=segment(aerial(),[0,0,128,128],**kwargs);copy=segment(aerial(),[0,0,128,128],**kwargs)
    assert result==copy and result['features']
    assert any(f['role']=='building' for f in result['features']) and any(f['role']=='vegetation' for f in result['features'])
    assert not any(f['reviewed'] for f in result['features'])
    assert set(result['groups'])>={'building','water','railway','oae','vegetation','cut','electric','pavement','paint'}
    settings=Settings(image_features=result['features']);assert accepted_items(settings)==[]
    item=next(f for f in result['features'] if f['role']=='building');item['reviewed']=True
    settings=Settings(image_features=[item]);assert accepted_items(settings)
    mask=box(0,0,128,128);assert not accepted_items(settings,[dict(points=np.array(mask.exterior.coords),role='pavement',closed=True)])
    settings.image_groups={'building':__import__('app.image_context_models',fromlist=['ImageGroup']).ImageGroup(render=False)};assert not accepted_items(settings)


def test_image_rejects_invalid_coverage_and_honors_cancel():
    with pytest.raises(ValueError):segment(np.zeros((128,128,4),np.uint8),[0,0,128,128])
    with pytest.raises(ValueError):segment(aerial(),[0,0,np.inf,128])
    with pytest.raises(ValueError):segment(np.full((32,32,3),np.nan),[0,0,128,128])
    with pytest.raises(InterruptedError):segment(aerial(),[0,0,128,128],cancel=lambda:True)


def test_manual_seed_identifies_an_ambiguous_infrastructure_class_without_inventing_height():
    result=segment(aerial(),[0,0,128,128],clusters=5,samples=[dict(x=25,y=100,role='oae')])
    assert any(f['role']=='oae' and 'Amostra manual' in f['evidence'] and not f['reviewed'] for f in result['features'])
    assert all(f['height_m']==0 for f in result['features'] if f['role']=='oae')
