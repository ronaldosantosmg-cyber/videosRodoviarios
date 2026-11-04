import pytest
from app.models import Settings
from app.simulation import TrafficSim
from app.fleet_policy import require_export,presentation_scope,presentation_vehicles
from test_simulation_blocks import road


def bad_pair(sim):
    ids=next(frame[0] for frame in sim.frames if len(frame[0]))
    vid=int(ids[0]);path=int(sim.info[vid][0])
    sim.fleet_audit['violations']=[{'vehicle':vid,'leader_vehicle':vid+1,'path':path,'time_s':1.,'station_m':100.,'reason':'lider','gap_m':2.,'remaining_to_exit_m':100.}]
    sim.fleet_audit['invalid_paths']=[path]
    return path


def test_partial_scope_preserves_audit_and_excludes_entire_vehicle_tracks():
    cfg=Settings(duration_s=8,traffic_density=3,pedestrians=False,traffic_export_scope='validated_only')
    sim=TrafficSim(road(400),cfg,lambda *_:'car');path=bad_pair(sim)
    require_export(sim,cfg);scope=presentation_scope(sim)
    assert scope['excluded_paths']==[path] and scope['excluded_vehicles']>0
    assert sim.fleet_audit['violations']  # Nenhuma violação foi apagada.
    for t in (0.,2.,4.,6.):
        assert all(sim.info[v[2]][0]!=path for v in presentation_vehicles(sim,t))
    sim.s=sim.s.model_copy(update={'traffic_export_scope':'strict'})
    with pytest.raises(ValueError,match='Regra de ouro'):require_export(sim,sim.s)


def test_partial_scope_never_releases_collisions_or_unfinished_simulation():
    cfg=Settings(duration_s=3,traffic_density=2,pedestrians=False,traffic_export_scope='validated_only')
    sim=TrafficSim(road(300),cfg,lambda *_:'car');bad_pair(sim)
    sim.collisions=1
    with pytest.raises(ValueError,match='Conflito'):require_export(sim,cfg)
    sim.collisions=0;sim.simulation_complete=False
    with pytest.raises(ValueError,match='Conclua'):presentation_scope(sim)
