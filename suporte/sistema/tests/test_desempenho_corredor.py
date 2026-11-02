import numpy as np
from app.desempenho_corredor import analisar_frames, comparar

DT = .2

def frames_fluxo(v, comp=1000., n_veic=1, dur=200.):
    """Um veículo por vez, velocidade constante v (m/s) entrando a cada 20 s."""
    fr = []; K = int(dur / DT)
    for k in range(K):
        t = k * DT; ids = []; ss = []
        for j in range(n_veic):
            s = v * (t - j * 20.)
            if 0 <= s < comp: ids.append(j); ss.append(s)
        fr.append((np.array(ids, np.int32), np.array(ss), np.zeros(len(ids), np.int32), np.full(len(ids), -1, np.int32), np.zeros(len(ids))))
    return fr

def test_velocidade_e_tempo_de_viagem():
    r = analisar_frames(frames_fluxo(20., n_veic=3), [1000.], 20., DT)
    assert r['disponivel'] and abs(r['velocidade_media_kmh'] - 72.) < 1.5
    assert abs(r['tempo_viagem_medio_s'] - 50.) < 1.0 and r['atraso_medio_s'] < 1.0 and r['paradas_por_veiculo'] == 0
    assert len(r['por_trecho']) == 10 and all(abs(t['velocidade_media_kmh'] - 72.) < 2 for t in r['por_trecho'])

def test_atraso_e_paradas_quando_ha_parada():
    # anda a 20 m/s até 400 m, para 10 s, segue
    fr = []; s = 0.; v = 20.; K = 400
    for k in range(K):
        t = k * DT
        if 20. <= t < 30.: v = 0.
        else: v = 20.
        s += v * DT
        if s >= 1000.: break
        fr.append((np.array([1], np.int32), np.array([s]), np.zeros(1, np.int32), np.array([-1], np.int32), np.zeros(1)))
    r = analisar_frames(fr, [1000.], 20., DT)
    assert r['paradas_por_veiculo'] == 1.0 and r['atraso_medio_s'] > 9. and r['velocidade_media_kmh'] < 72.

def test_sem_quadros_e_comparacao():
    assert analisar_frames([], [1000.], 20., DT)['disponivel'] is False
    a = analisar_frames(frames_fluxo(20.), [1000.], 20., DT); b = analisar_frames(frames_fluxo(10.), [1000.], 20., DT)
    c = comparar(a, b)
    assert c['indicadores']['velocidade_media_kmh']['delta'] < -30 and c['indicadores']['atraso_medio_s']['delta'] > 40
