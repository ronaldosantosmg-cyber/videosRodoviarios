from types import SimpleNamespace

import numpy as np
from shapely import convex_hull, multipoints

from app.vehicle_motion import PROFILES, axle_geometry_prepared, axle_pose_prepared, prepare_points
from app.vehicle_safety import LATERAL_BUFFER, PolygonSafety, body_corners


def road():
    t = np.linspace(0, 1.4, 80)
    return prepare_points(np.column_stack((500000 + 120 * np.sin(t), 7800000 + 120 * (1 - np.cos(t)))))


def test_pose_escalar_preserva_geometria_inclusive_nas_extremidades():
    p, d = road()
    for vehicle in PROFILES:
        for station in (-20, 0, 2, 32.5, d[-1], d[-1] + 20):
            old = axle_geometry_prepared(p, d, vehicle, np.array([station]))
            center, heading = axle_pose_prepared(p, d, vehicle, station)
            np.testing.assert_allclose(center, old['center'][0], atol=1e-9, rtol=0)
            np.testing.assert_allclose(heading, old['heading'][0], atol=1e-12, rtol=0)


def test_varredura_vetorizada_preserva_reserva_fisica():
    p, d = road()
    sim = SimpleNamespace(motion_points=[(p, d)], paths=[{'length': d[-1]}])
    safety = PolygonSafety(sim)
    for vehicle in PROFILES:
        length, width, *_ = PROFILES[vehicle]
        for station in (0, 30, d[-1] - 2):
            for forward in (.1, 3, 9):
                v = {'id': 1, 'p': 0, 's': station, 't': vehicle}
                ds = np.linspace(0, forward, max(3, min(17, int(np.ceil(forward / .5)) + 1)))
                g = axle_geometry_prepared(p, d, vehicle, station + ds)
                points = [corner for c, h in zip(g['center'], g['heading'])
                          for corner in body_corners(c, h, length, width, LATERAL_BUFFER)]
                expected = convex_hull(multipoints(points))
                if np.linalg.norm(g['heading'][0] - g['heading'][-1]) > .002:
                    expected = expected.buffer(.03)
                actual = safety.sweep(v, forward)
                assert actual.symmetric_difference(expected).area < 1e-7


def test_cache_de_pose_nao_confunde_posicao_classe_ou_rota():
    p, d = road()
    sim = SimpleNamespace(motion_points=[(p, d)], paths=[{'length': d[-1]}])
    safety = PolygonSafety(sim)
    v = {'id': 1, 'p': 0, 's': 20, 't': 'car'}
    first = safety.pose(v)
    np.testing.assert_array_equal(safety.pose(v)[0], first[0])
    assert not np.array_equal(safety.pose(v, 3)[0], first[0])
    assert not np.array_equal(safety.pose({**v, 't': 'carreta'})[1], first[1])


def test_estudo_indexado_nao_confunde_via_distante_com_faixa_contraria():
    from app.passing_zones import oncoming_flags

    a = np.array([[0, 0], [150, 0], [300, 0]], float)
    b = np.array([[300, 3.5], [150, 3.5], [0, 3.5]], float)
    far = b + [10000, 0]
    assert oncoming_flags([a, b, far]) == [True, True, False]
