"""A exceção pertence à fila física do sinal e termina quando ela se dissolve."""
import math
from types import SimpleNamespace as S

import pytest

from app.fleet_policy import inspect
from app.simulation import TrafficSim


def fixture():
    sim = TrafficSim.__new__(TrafficSim)
    sim.v0 = 20.
    sim.speedz = [[]]
    sim.curve_env = [None]
    sim.zones = [[]]
    sim.heavy_reaction = False
    sim.dyn_of = lambda vt: {'a': 1.2, 'b': 2., 'T': 1.4, 's0': 2.3}
    sim.alternating = S(stop_gap=lambda v: math.inf)
    sim.pedestrians = S(stop_gap=lambda v: math.inf)
    sim.merge_conflict = lambda v, occ: (math.inf, 0.)
    sim.gap = 5.
    sim.lead = dict(id=2, p=0, s=110., L=4., v=10.)
    sim.leader_state = lambda v, occ: (sim.gap, sim.lead['v'], sim.lead)
    stop = dict(kind='signal', s=100., clear_span=25.)
    sim.transport = S(stops=[[stop]], red=True)
    def stop_gap(v, t, gap, speed):
        v['_transport_kind'] = 'semaforo' if sim.transport.red else 'caixa_cruzamento'
        return max(0., 100. - v['s'] - v['L']/2) if sim.transport.red else math.inf
    sim.transport.stop_gap = stop_gap
    vehicle = dict(id=1, p=0, s=90., L=4., v=0., v0=20., t='car', acc_k=.6)
    return sim, vehicle


def test_red_queue_is_traced_even_when_leader_is_closer_and_persists_on_green():
    sim, vehicle = fixture()
    sim.accel(vehicle, None, 0.)
    assert vehicle['_why'] == 'lider'
    assert vehicle['_signal_queue']['station'] == 100.
    sim.transport.red = False
    sim.accel(vehicle, None, 20.)
    assert vehicle['_control_cause'] == 'semaforo'
    assert vehicle['_control_until'] > 20.
    sim.time = 20.
    inspect(sim, [vehicle], None)
    assert not sim.fleet_audit['violations']


def test_discharge_removes_hesitation_without_exceeding_calibrated_acceleration():
    sim, vehicle = fixture()
    sim.accel(vehicle, None, 0.)
    sim.transport.red = False
    sim.gap = 1000.
    vehicle['v'] = 0.
    assert .6 * 1.2 < sim.accel(vehicle, None, 20.) <= 1.2


def test_downstream_queue_opens_free_headway_and_then_loses_exception():
    sim, vehicle = fixture()
    sim.accel(vehicle, None, 0.)
    sim.transport.red = False
    vehicle.update(s=140., v=10., acc_k=1.)
    controlled_acceleration = sim.accel(vehicle, None, 20.)
    assert vehicle['_control_until'] > 20.
    free = {key: value for key, value in vehicle.items() if not key.startswith('_')}
    assert controlled_acceleration == pytest.approx(sim.accel(free, None, 20.))
    sim.gap = 40.
    sim.accel(vehicle, None, 21.)
    assert '_signal_queue' not in vehicle
    assert vehicle['_control_until'] < 21.


def test_queue_exception_expires_and_cannot_be_inherited_in_free_downstream_road():
    sim, vehicle = fixture()
    sim.accel(vehicle, None, 0.)
    sim.transport.red = False
    vehicle.update(s=140., v=10.)
    sim.accel(vehicle, None, 1.)
    sim.accel(vehicle, None, 62.)
    assert '_signal_queue' not in vehicle
    assert vehicle['_control_until'] < 62.
    sim.time = 62.
    inspect(sim, [vehicle], None)
    assert sim.fleet_audit['violations']
    sim.lead.update(_signal_queue={'path': 0, 'station': 100., 'span': 25., 'released': 1.},
                    _control_cause='semaforo', _control_until=70.)
    sim.accel(vehicle, None, 63.)
    assert '_signal_queue' not in vehicle
