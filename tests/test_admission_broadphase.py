from types import SimpleNamespace

from app.vehicle_safety import PolygonSafety


def test_level_cache_respects_station_and_bounds():
    calls = []
    def locate(path, station):
        calls.append((path, station))
        return 0, ('e', int(station >= 50)), 0, 100, station
    sim = SimpleNamespace(locate=locate, net=SimpleNamespace(edges=[{'level': 0}, {'level': 1}]))
    safety = PolygonSafety(sim)
    assert safety.level({'p': 0, 's': 10}) == 0
    assert safety.level({'p': 0, 's': 10}) == 0
    assert calls == [(0, 10)]
    assert safety.level({'p': 0, 's': 60}) == 1
    for station in range(8300):
        safety.level({'p': 0, 's': station})
    assert len(safety.level_cache) <= 8192


def test_narrow_keeps_second_vehicle_after_first_probe_passes():
    seen = []
    def try_pair(new, other):
        seen.append(other['id'])
        return other['id'] == 1
    sim = SimpleNamespace(time=0, shoulder_probe=SimpleNamespace(try_pair=try_pair))
    safety = PolygonSafety(sim)
    safety.level = lambda vehicle: 0
    safety.corridor_conflict = lambda p, q, width, other_width: q == 1
    new = {'p': 0, 's': 0, 'id': 0}
    others = [{'p': 2, 's': 0, 'id': 9}, {'p': 1, 's': 20, 'id': 1}, {'p': 1, 's': 200, 'id': 2}]
    assert not safety.narrow_admission(new, others)
    assert seen == [1, 2]
    assert safety.waiting == {(0, 1): 0}


def test_center_grid_matches_full_admission_with_large_coordinates_and_lane_change():
    import numpy as np
    from app.vehicle_safety import SpatialCenters
    safety = PolygonSafety(SimpleNamespace())
    def pose(vehicle, *args):
        # A troca de faixa pode afastar a pose física da rota de origem.
        center = np.asarray(vehicle['center'], dtype=float).copy()
        if vehicle.get('lc'):
            center[1] += vehicle['lc']['offset']
        return center, np.array([1., 0.])
    safety.pose = pose
    safety.level = lambda vehicle: vehicle.get('level', 0)
    safety.narrow_admission = lambda new, vehicles: True
    base = 7400000.
    vehicles = [{'id': 1, 'p': 0, 's': 0, 'center': (base, -base), 'lc': {'offset': 4}},
                {'id': 2, 'p': 0, 's': 0, 'center': (base + 800, -base)}]
    grid = SpatialCenters(pose, vehicles)
    for dx, dy in [(0, 4), (0, 0), (39.99, 4), (-40, 4), (800, 0)]:
        new = {'id': 3, 'p': 0, 's': 0, 'center': (base + dx, -base + dy)}
        assert safety.admission(new, vehicles) == safety.admission(new, vehicles, near=grid.nearby)
    accepted = {'id': 4, 'p': 0, 's': 0, 'center': (base + 100, -base)}
    assert safety.admission(accepted, vehicles, near=grid.nearby)
    vehicles.append(accepted)
    grid.add(accepted)
    new = {'id': 5, 'p': 0, 's': 0, 'center': accepted['center']}
    assert not safety.admission(new, vehicles, near=grid.nearby)
    assert safety.admission(new, vehicles) == safety.admission(new, vehicles, near=grid.nearby)


def test_center_query_uses_candidate_pose_after_narrow_probe():
    import numpy as np
    from app.vehicle_safety import SpatialCenters
    safety = PolygonSafety(SimpleNamespace())
    safety.pose = lambda vehicle, *args: (np.array(vehicle['center']), np.array([1., 0.]))
    safety.level = lambda vehicle: 0
    def narrow(new, vehicles):
        new['center'] = (100., 0.)
        return True
    safety.narrow_admission = narrow
    vehicles = [{'id': 1, 'p': 0, 's': 0, 'center': (100., 0.)}]
    grid = SpatialCenters(safety.pose, vehicles)
    new = {'id': 2, 'p': 0, 's': 0, 'center': (0., 0.)}
    assert not safety.admission(new, vehicles, near=grid.nearby)
