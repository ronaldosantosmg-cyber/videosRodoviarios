from types import SimpleNamespace as S
from shapely.geometry import Polygon
from app.pedestrian_traffic import PedestrianTraffic


def test_intersecting_sidewalk_seeds_reserve_people_space():
    pt=lambda x,y:S(x=x,y=y)
    settings=S(pedestrians=True,pedestrian_seed=1,crosswalks=[],pois=[],pedestrian_paths=[
        S(enabled=True,id='h',people_per_100m=1,points=[pt(-10,0),pt(10,0)]),
        S(enabled=True,id='v',people_per_100m=1,points=[pt(0,-10),pt(0,10)])])
    people=PedestrianTraffic(settings,S(allowed=Polygon(),paths=[],edges=[]),S(signals=[],rails=[]))
    assert len(people.routes)==2
    assert len(people.agents)==5
    assert people.admitted==5
    people.check([])


def test_stopped_vehicle_before_crosswalk_yields_without_deadlock():
    import numpy as np
    from shapely.geometry import LineString
    people=PedestrianTraffic.__new__(PedestrianTraffic)
    people.owner=None;people.transport=S(rails=[])
    people.net=S(paths=[{'p':np.array([[0.,0.],[100.,0.]]),'d':np.array([0.,100.])}])
    route=dict(kind='faixa',release_after=0.,burst=None,signal=None,d=np.array([0.,10.]),
               line=LineString([(50,-5),(50,5)]),conflicts=[dict(path=0,a=48.,b=52.)])
    vehicle=dict(p=0,s=43.,L=4.,v=0.,lc=None)
    assert people.can_enter(route,[vehicle],0.,1.3)
    vehicle['v']=10.
    assert not people.can_enter(route,[vehicle],0.,1.3)
    vehicle['v']=0.;vehicle['s']=49.
    assert not people.can_enter(route,[vehicle],0.,1.3)


def test_waiting_crosswalk_requests_braking_but_bridge_does_not():
    import math
    people=PedestrianTraffic.__new__(PedestrianTraffic);people.owner=S(time=0.)
    route=dict(kind='faixa',release_after=0.,burst=None,signal=None,conflicts=[dict(path=0,a=48.,b=52.)])
    people.agents=[dict(route=route,state='waiting')]
    vehicle=dict(p=0,s=0.,L=4.,v=10.,lc=None)
    assert people.stop_gap(vehicle)==46.
    route['kind']='passarela'
    assert math.isinf(people.stop_gap(vehicle))
