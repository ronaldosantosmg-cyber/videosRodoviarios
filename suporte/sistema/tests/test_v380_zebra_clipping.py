from types import SimpleNamespace as S
import numpy as np
from shapely.geometry import Polygon,LineString
from app import signage


def net():
    settings=S(hatch_areas=[],dxf_signage='replace',lane_arrows=False,gore_hatch=False,stop_lines=False,crosswalks=[],signs=[],route_alignments=[])
    return S(s=settings,paths=[],edges=[],warnings=[],arrows=[],markings=[],mark_src=[])


def test_zebra_only_dxf_clips_crossing_even_when_midpoint_outside(monkeypatch):
    n=net();n.markings=[(np.array([-20.,0]),np.array([3.,0]),signage.YELLOW)];n.mark_src=[0]
    monkeypatch.setattr(signage,'two_way_fix',lambda n:None)
    entity=dict(role='sign_h',closed=True,layer='ZEBRADO',points=[[-2,-2],[2,-2],[2,2],[-2,2]])
    signage.build(n,[entity])
    assert len(n.markings)==2
    area=Polygon(entity['points'])
    assert all(LineString([a,b]).intersection(area).length<1e-8 for a,b,_ in n.markings)
    assert sum(LineString([a,b]).length for a,b,_ in n.markings)==19


def test_clipping_preserves_hole_and_explicit_dxf_lines():
    n=net();outer=Polygon([[-5,-5],[5,-5],[5,5],[-5,5]],holes=[[[-2,-2],[2,-2],[2,2],[-2,2]]])
    n.markings=[(np.array([-10.,0]),np.array([10.,0]),signage.YELLOW)]*3;n.mark_src=[0,-4,-2]
    signage.clip_automatic_markings(n,[outer])
    auto=[LineString([a,b]) for (a,b,_),src in zip(n.markings,n.mark_src) if src==0]
    assert len(auto)==3
    assert sum(line.length for line in auto)==14
    assert n.mark_src.count(-4)==n.mark_src.count(-2)==1


def test_annular_zebra_draws_both_borders_without_chord():
    area=Polygon([[-5,-5],[5,-5],[5,5],[-5,5]],holes=[[[-2,-2],[2,-2],[2,2],[-2,2]]])
    paint,lines=signage.zebra(area,0,signage.WHITE)
    assert abs(sum(LineString([a,b]).length for a,b in lines)-56)<1e-8
    assert all(area.boundary.covers(LineString([a,b])) for a,b in lines)
    assert all(Polygon(rings[0],holes=rings[1:]).difference(area).area<1e-8 for rings,_ in paint)


def test_virtual_source_does_not_cut_automatic_line(monkeypatch):
    n=net();n.markings=[(np.array([-10.,0]),np.array([10.,0]),signage.YELLOW)];n.mark_src=[0]
    monkeypatch.setattr(signage,'two_way_fix',lambda n:None)
    signage.build(n,[dict(role='sign_h',closed=True,virtual=True,layer='ZEBRADO',points=[[-2,-2],[2,-2],[2,2],[-2,2]])])
    assert len(n.markings)==1 and LineString(n.markings[0][:2]).length==20


def test_local_clip_preserves_stop_and_pedestrian_paint(monkeypatch):
    n=net();n.s.stop_lines=True;n.s.auto_signs=False;n.s.crosswalks=[S(show=True)]
    stop=([np.array([[-1.,-1.],[1.,-1.],[1.,0.],[-1.,0.]])],signage.WHITE)
    crossing=([np.array([[-1.,0.],[1.,0.],[1.,1.],[-1.,1.]])],signage.WHITE)
    monkeypatch.setattr(signage,'two_way_fix',lambda n:None)
    monkeypatch.setattr(signage,'stop_lines',lambda n:([stop],[]))
    monkeypatch.setattr(signage,'crosswalk',lambda n,c:[crossing])
    signage.build(n,[dict(role='sign_h',closed=True,layer='ZEBRADO',points=[[-2,-2],[2,-2],[2,2],[-2,2]])])
    assert n.fills[0] is stop and n.fills[-1] is crossing


import pytest


@pytest.mark.parametrize('complete',[False,True])
def test_dxf_zebra_excludes_only_automatic_gore_not_manual_or_stop(monkeypatch,complete):
    from app.models import HatchArea
    import app.zebrados as zebrados
    n=net();n.s.gore_hatch=True;n.s.stop_lines=True;n.s.auto_signs=False;n.s.dxf_complete=True
    outer=[[-8,-8],[8,-8],[8,8],[-8,8]];hole=[[-5,-5],[5,-5],[5,5],[-5,5]]
    control=Polygon(outer,holes=[hole]);gore=Polygon([[-12,-12],[12,-12],[12,12],[-12,12]])
    source=dict(role='sign_h',closed=True,layer='ZEBRADO',points=outer,holes=[hole])
    dxf=[source]
    if complete:dxf.append(dict(role='sign_h',closed=False,layer='LINHA',points=[[20,20],[21,20]]))
    h=HatchArea(points=[dict(x=x,y=y) for x,y in outer],holes=[[dict(x=x,y=y) for x,y in hole]],angle_deg=-45,color='yellow')
    manual=HatchArea(points=[dict(x=x,y=y) for x,y in [[6,-1],[7,-1],[7,1],[6,1]]],angle_deg=0,color='yellow')
    monkeypatch.setattr(zebrados,'resolve',lambda net,entities:[h,manual])
    monkeypatch.setattr(signage,'two_way_fix',lambda n:None)
    monkeypatch.setattr(signage,'gores',lambda n:[gore])
    monkeypatch.setattr(signage,'main_angle',lambda n,c:0.)
    stop=([np.array([[30.,30.],[31.,30.],[31.,31.],[30.,31.]])],signage.WHITE)
    monkeypatch.setattr(signage,'stop_lines',lambda n:([stop],[]))
    original=signage.zebra;calls=[]
    def zebra(poly,angle,color,*args):
        calls.append((poly,color));return original(poly,angle,color,*args)
    monkeypatch.setattr(signage,'zebra',zebra)
    signage.build(n,dxf)
    automatic=[p for p,c in calls if c==signage.WHITE]
    assert automatic and all(p.intersection(control).area<1e-8 for p in automatic)
    assert sum(p.intersection(Polygon(hole)).area for p in automatic)>0
    assert sum(p.difference(Polygon(outer)).area for p in automatic)>0
    configured=[p for p,c in calls if c==signage.YELLOW]
    assert len(configured)==2 and configured[0].equals(control)
    assert configured[1].equals(Polygon([[6,-1],[7,-1],[7,1],[6,1]]))
    assert any(item[0] is stop[0] for item in n.fills)
