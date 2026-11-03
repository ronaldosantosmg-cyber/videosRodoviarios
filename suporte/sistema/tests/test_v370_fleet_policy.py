from types import SimpleNamespace as S
import pytest
from app.fleet_policy import inspect, require_export


def pair(gap=11., speed=10., **cause):
    lead=dict(id=2, p=0, s=30., v=speed, **cause)
    rear=dict(id=1, p=0, s=10., v=speed, v0=20.)
    sim=S(time=0.,leader_state=lambda v, occ:(gap,speed,lead) if v is rear else (999.,0.,None))
    return sim,rear,lead


def test_pair_detected_in_first_sample_at_free_speed():
    sim,rear,lead=pair(speed=20.)
    inspect(sim,[rear,lead],None)
    assert sim.fleet_audit['violations'][0]['vehicle']==1


def test_two_second_headway_boundary_is_allowed():
    sim,rear,lead=pair(gap=40.,speed=20.)
    inspect(sim,[rear,lead],None)
    assert not sim.fleet_audit['violations']


@pytest.mark.parametrize('cause',['semaforo','pedestres','rotatoria'])
def test_only_current_allowed_control_permits_compact_pair(cause):
    sim,rear,lead=pair(_control_cause=cause,_control_until=1.)
    inspect(sim,[rear,lead],None)
    assert not sim.fleet_audit['violations']
    sim.time=2.
    inspect(sim,[rear,lead],None)
    assert sim.fleet_audit['violations']


def test_rail_is_not_an_exception():
    sim,rear,lead=pair(_control_cause='ferrovia',_control_until=10.)
    inspect(sim,[rear,lead],None)
    assert sim.fleet_audit['violations']


def test_missing_simulator_blocks_enabled_fleet():
    with pytest.raises(ValueError):require_export(None,S(traffic=True))
    require_export(None,S(traffic=False))



@pytest.mark.parametrize('setting',[
    {'traffic_classic':True},{'traffic_model':'anterior'},
    {'traffic_prevent_collisions':False},{'traffic_respect_signals':False}])
def test_export_fails_before_loading_project_for_unsafe_mode(tmp_path,setting):
    from app.models import Settings
    from app.render import render
    from app.scene3d import build
    settings=Settings(coordinates_confirmed=True,**setting)
    with pytest.raises(ValueError,match='regra de ouro|Ative'):render(tmp_path,settings)
    with pytest.raises(ValueError,match='regra de ouro|Ative'):build(tmp_path,settings)
    assert not list(tmp_path.iterdir())
