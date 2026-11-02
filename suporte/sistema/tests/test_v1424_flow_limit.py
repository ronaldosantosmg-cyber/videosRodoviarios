from types import SimpleNamespace
import numpy as np
import pytest
from shapely.geometry import box
from app.models import Settings,RouteAlignment
from app.routes import raw_paths
from app.traffic import TrafficNetwork
from app.flow_diagnostics import flow_diagnostics

@pytest.mark.parametrize('minimum',list(range(20,201,20))+[50])
def test_explicit_routes_follow_project_limit_and_keep_originals(minimum):
    for length in [minimum-.1,minimum,minimum+.1]:
        route=RouteAlignment(id='r',type='unico',points=[{'x':0,'y':0},{'x':length,'y':0}])
        s=Settings(min_route_segment_m=minimum,route_alignments=[route])
        assert bool(raw_paths(s))==(length>=minimum)
        again=Settings.model_validate_json(s.model_dump_json())
        assert again.min_route_segment_m==minimum and again.route_alignments[0].enabled
        assert again.route_alignments[0].points[1].x==length

def test_raising_and_lowering_limit_never_reenables_manually_disabled_route():
    route=dict(id='r',type='unico',points=[{'x':0,'y':0},{'x':90,'y':0}])
    for minimum,expected in [(20,True),(100,False),(200,False),(40,True)]:
        assert bool(raw_paths(Settings(min_route_segment_m=minimum,route_alignments=[route])))==expected
        assert not raw_paths(Settings(min_route_segment_m=minimum,route_alignments=[dict(route,enabled=False)]))

def test_short_filter_applies_to_all_sources_before_contact_splits():
    n=TrafficNetwork.__new__(TrafficNetwork)
    n.origin_info={0:(119.9,True),1:(120.,True),2:(130.,False)}
    n.edges=[{'origin':0,'length':119.9,'ring':True,'route':'manual'}, {'origin':1,'length':12,'route':'explicit'}, {'origin':2,'length':20}]
    assert n.short_edges(120)=={0}

def test_actual_network_uses_the_selected_limit():
    axis=np.array([[0.,0.],[200.,0.]])
    route=dict(id='r',type='unico',points=[{'x':20,'y':0},{'x':160,'y':0}])
    for minimum,expected in [(120,True),(160,False),(40,True)]:
        s=Settings(derive_traffic_paths=False,hydrography=False,min_route_segment_m=minimum,route_alignments=[route])
        n=TrafficNetwork([box(-20,-20,220,20)],[],[],axis,np.array([0.,200.]),s)
        assert bool(n.paths)==expected
        assert n.report['minimum_flow_length_m']==minimum
        assert all(p['length']>=minimum for p in n.paths)

def test_diagnostic_uses_selected_limit_instead_of_fifty():
    n=SimpleNamespace(min_route=120,raw_info=[{'base':0,'points':np.array([[0.,0.],[90.,0.]])}],edges=[{'base':0,'disabled':False}],paths=[],short_ignored={0})
    result=flow_diagnostics(n)[0]
    assert result['technical_status']=='adjustment' and '120 m' in result['technical_message']
    assert 'desligada' in result['technical_message']
