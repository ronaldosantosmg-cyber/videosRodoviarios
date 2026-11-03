import copy
from types import SimpleNamespace as S

import numpy as np
import pytest
from shapely.geometry import box

from app.models import Settings
from app.simulation import DT, TrafficSim
from app.transport_models import TrafficSignal


def road(length=700.):
    paths=[]
    for i in range(2):
        x=np.linspace(0,length,141);p=np.c_[x,np.full(len(x),20.*i)]
        paths.append(dict(p=p,d=x,length=length,kinds=['main'],route=str(i),route_dir='f',route_lane=0,
                          lane_change='marked',route_start_m=0.,route_end_m=length,links=[(('e',i),0.,length)]))
    return S(paths=paths,edges=[dict(kind='main',level=0) for _ in paths],allowed=box(-30,-8,length+30,32))


def vehicle_type(kinds, identity):
    return 'truck' if identity[1] % 4 == 0 else 'car'


def configuration(warmup=0.):
    return Settings(duration_s=38,traffic_density=6,traffic_speed_kmh=60,traffic_warmup_s=warmup,
                    pedestrians=False,traffic_signals=[TrafficSignal(id='s',point={'x':350.,'y':0.},heading_deg=0)])


def assert_equal_simulations(actual, expected):
    assert actual.simulation_complete
    assert actual.t_first == expected.t_first
    assert len(actual.frames) == len(expected.frames)
    for frame, reference in zip(actual.frames, expected.frames):
        for array, baseline in zip(frame, reference):
            np.testing.assert_array_equal(array, baseline)
    assert actual.warning_frames == expected.warning_frames
    for key in ('info','spawned','semeados','spawned_by_path','exited_by_path','active_end',
                'collisions','side_collisions','min_gap','safety_interventions','lane_changes',
                'queue_area_vehicle_s','max_queue_lane','queue_discharged','current_queue',
                'fleet_audit','stop_seconds','stop_by_path','stop_samples','node_transfers'):
        assert getattr(actual,key) == getattr(expected,key), key
    assert actual._continuation['rng'].bit_generator.state == expected._continuation['rng'].bit_generator.state
    assert actual._continuation['V'] == expected._continuation['V']
    assert actual._continuation['nextspawn'] == expected._continuation['nextspawn']


@pytest.mark.parametrize('warmup,block_seconds',[(0.,5.),(.5,2.7)])
def test_blocks_preserve_frames_rng_exits_and_audits(warmup, block_seconds):
    net=road();settings=configuration(warmup)
    full=TrafficSim(net,settings,vehicle_type)
    partial=TrafficSim(net,settings,vehicle_type,defer=True)
    assert partial.frames == [] and partial._continuation is None
    checkpoints=[]
    for checkpoint in partial.run_blocks(block_seconds=block_seconds):
        checkpoints.append(checkpoint)
        assert partial.frames is partial._continuation['frames']
        assert len(partial.frames)==len(partial.warning_frames)
        assert partial._continuation['k']==checkpoint['next_step']
        assert checkpoint['available_until_s']+1e-9>=checkpoint['end_s']+DT
        assert partial.state(checkpoint['end_s']) == full.state(checkpoint['end_s'])
        assert partial.current_queue == partial._continuation['pending']
    assert len(checkpoints)>2 and checkpoints[-1]['complete']
    assert sum(full.exited_by_path)>0
    assert_equal_simulations(partial,full)
    assert list(partial.run_blocks()) == []  # Não duplicar quadros ao reabrir completo.


def test_explicit_graph_restore_resumes_without_reseeding_or_duplicate_frame():
    net=road();settings=configuration()
    full=TrafficSim(net,settings,vehicle_type)
    first=TrafficSim(net,settings,vehicle_type,defer=True)
    blocks=first.run_blocks(block_seconds=5.)
    checkpoint=next(blocks)
    saved_count=len(first.frames)
    restored=TrafficSim(net,settings,vehicle_type,defer=True)
    # Representa a restauração do grafo pelo cache: refs à raiz antiga apontam
    # à nova instância; os controllers continuam ligados ao mesmo V/RNG.
    state=copy.deepcopy(first.__dict__,{id(first):restored,id(net):net,id(settings):settings})
    restored.__dict__.update(state)
    blocks.close()
    assert restored.polygon_safety.sim is restored
    assert restored.shoulder_probe.sim is restored
    assert restored._continuation['frames'] is restored.frames
    assert restored._continuation['k']==checkpoint['next_step']
    assert len(restored.frames)==saved_count
    restored.run()
    assert_equal_simulations(restored,full)


@pytest.mark.parametrize('seconds',[0.,-1.,float('inf'),float('nan')])
def test_invalid_blocks_do_not_start_simulation(seconds):
    sim=TrafficSim(road(),configuration(),vehicle_type,defer=True)
    with pytest.raises(ValueError):next(sim.run_blocks(block_seconds=seconds))
    assert sim.frames==[] and sim._continuation is None


class HistorySequence:
    def __init__(self):self.rows=[]
    def __len__(self):return len(self.rows)
    def __getitem__(self,index):return self.rows[index]
    def __iter__(self):return iter(self.rows)
    def append(self,row):self.rows.append(row)


def test_external_history_hooks_and_partial_report_are_published():
    sim=TrafficSim(road(),configuration(),vehicle_type,defer=True)
    frames=HistorySequence();warnings=HistorySequence()
    sim._history_frames=frames;sim._history_warnings=warnings
    blocks=sim.run_blocks()
    checkpoint=next(blocks)
    assert not sim.simulation_complete and not checkpoint['complete']
    assert sim.frames is frames and sim._continuation['frames'] is frames
    assert sim.warning_frames is warnings
    assert sim.t_first+(len(frames)-1)*DT==pytest.approx(checkpoint['available_until_s'])
    report=sim.report()
    assert report['flow_balance']['conserved']
    assert report['initialization']['simulation_seconds']>=0
    blocks.close()


def test_checkpoint_rejects_duration_extension_without_advancing_state():
    sim=TrafficSim(road(),configuration(),vehicle_type,defer=True)
    blocks=sim.run_blocks()
    checkpoint=next(blocks);blocks.close()
    sim.duration+=5
    with pytest.raises(ValueError,match='duração'):next(sim.run_blocks())
    assert sim._continuation['k']==checkpoint['next_step']
