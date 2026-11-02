import math
import numpy as np
from app.simulation import TrafficSim


def test_interarrival_mantem_taxa_media_e_nao_gera_rajadas():
    rng = np.random.default_rng(5)
    for rate in (200 / 3600, 600 / 3600, 1500 / 3600):
        x = np.array([TrafficSim.interarrival(rng, rate) for _ in range(20000)])
        assert abs(x.mean() * rate - 1) < .03          # taxa preservada
        assert x.min() >= min(1.2, .5 / rate) - 1e-9   # sem chegadas simultâneas
        assert x.std() / x.mean() <= 1.01              # nunca mais agrupado que Poisson


def test_interarrival_protegido_contra_zero_infinito_e_vazio():
    rng = np.random.default_rng(1)
    for bad in (0, -1, math.inf, math.nan, None, 'x', []):
        assert TrafficSim.interarrival(rng, bad) == math.inf


def _sim(**p):
    s = TrafficSim.__new__(TrafficSim)
    s.paths = [dict(length=1000., lane_change='marked', lane_change_sections=[], **p)]
    s.adjacent = {0: [1]}; s.route_station = lambda i, x: x
    return s


def test_troca_de_faixa_livre_em_pista_dupla_sem_marcacao_e_restrita_nos_demais():
    assert _sim(axis_type='pista_dupla').lane_change_window_allowed(0, 100., 30.)
    assert _sim().lane_change_window_allowed(0, 100., 30.)                       # auto com faixa vizinha
    for t in ('pista_simples', 'acesso', 'retorno', 'dispositivo'):
        assert not _sim(axis_type=t).lane_change_window_allowed(0, 100., 30.)
    s = _sim(axis_type='pista_dupla'); s.adjacent = {0: []}
    assert not s.lane_change_window_allowed(0, 100., 30.)                        # sem faixa vizinha
    s = _sim(axis_type='pista_dupla'); s.paths[0]['lane_change_sections'] = [dict(start_m=90, end_m=140, mode='deny')]
    assert not s.lane_change_window_allowed(0, 100., 30.)                        # trecho proibido vale
    s = _sim(axis_type='pista_dupla'); s.paths[0]['lane_change'] = 'off'
    assert not s.lane_change_window_allowed(0, 100., 30.)


def test_map_s_projeta_pela_geometria_com_faixas_de_comprimentos_diferentes():
    from app.vehicle_motion import prepare_points
    s = TrafficSim.__new__(TrafficSim)
    A = np.column_stack([np.linspace(0, 1000, 1001), np.zeros(1001)])
    B = np.column_stack([np.linspace(-200, 1000, 1201), np.full(1201, 3.5)])
    s.paths = [dict(p=A, d=np.arange(1001.), length=1000.), dict(p=B, d=np.arange(1201.), length=1200.)]
    assert abs(s.map_s(0, 1, 500.) - 700.) < 1.0      # x=500 está a 700 m do início de B (o proporcional daria 600)
    assert abs(s.map_s(1, 0, 700.) - 500.) < 1.0
    assert s.map_s(0, 0, 123.) == 123.
    assert 0 <= s.map_s(0, 1, -50.) <= 1200 and 0 <= s.map_s(0, 1, 1e9) <= 1200   # entradas fora da faixa não quebram
    s._proj_lines = {}; s.paths[1]['p'] = np.array([[math.nan, 0.], [1., 1.]])                          # geometria inválida: reserva proporcional
    assert s.map_s(0, 1, 500.) == 600.
