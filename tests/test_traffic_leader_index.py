import math
import random
from types import MethodType, SimpleNamespace

from app.simulation import TrafficSim


def test_busca_indexada_mantem_lider_distancia_e_desempate():
    sim = TrafficSim.__new__(TrafficSim)
    sim.link_of = [[(('e', 0), 0., 10000.)]]
    sim.link_offsets = [[0.]]
    sim.locate = MethodType(lambda self, path, station: (0, ('e', 0), 0., 10000., station), sim)
    sim.shoulder_probe = SimpleNamespace(laterally_separated=lambda a, b: b.get('separado', False))
    rng = random.Random(42)
    vehicles = [{'id': i, 'p': 0, 's': rng.randrange(100), 'L': 4.5, 'v': rng.random() * 20,
                 'separado': i % 7 == 0} for i in range(150)]
    rows = sorted([(v['s'], v, 0, v['s']) for v in vehicles], key=lambda row: row[0])
    for v in vehicles:
        expected = (math.inf, 0., None)
        for station, other, _, _ in rows:
            if other is v or other['separado']:
                continue
            if station > v['s'] + 1e-6 or abs(station - v['s']) <= 1e-6 and other['id'] < v['id']:
                expected = (station - v['s'] - (other['L'] + v['L']) / 2, other['v'], other)
                break
        assert sim.leader_state(v, {('e', 0): rows}) == expected
