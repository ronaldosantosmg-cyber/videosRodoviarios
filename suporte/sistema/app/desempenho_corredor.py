"""Indicadores de desempenho do corredor (tempo de viagem, velocidade média, densidade, fluxo, atraso, paradas e fila por trecho do eixo).
Calculados a partir dos quadros da microssimulação (simulation.py): nenhuma alteração na dinâmica, só medição.
Referência de conteúdo: indicadores citados em casos de uso de simulação de corredores (tempo de viagem, velocidade média, densidade, filas, atrasos, paradas)."""
import math
import numpy as np

BIN_M = 100.
PARADO = 0.3      # m/s: abaixo disso conta como parado (mesmo critério do diagnóstico de paradas)


def analisar_frames(frames, comprimentos, v_livre, dt, bin_m=BIN_M):
    """frames: lista de (ids, ss, ps, to, al) por quadro; comprimentos: comprimento de cada percurso (m); v_livre: m/s."""
    if not frames or dt <= 0: return {'disponivel': False, 'motivo': 'sem quadros de simulação'}
    nb = max(1, int(math.ceil(max(comprimentos or [0]) / bin_m))) if comprimentos else 1
    dist = np.zeros(nb); tempo = np.zeros(nb); tempo_v = np.zeros(nb); passagens = np.zeros(nb)
    prev = {}; first = {}; last = {}; paradas = {}; parado_ate = {}
    T = len(frames) * dt
    for k, (ids, ss, ps, to, al) in enumerate(frames):
        t = k * dt
        for vid, s, p in zip(ids.tolist(), ss.tolist(), ps.tolist()):
            b = min(nb - 1, max(0, int(s // bin_m)))
            tempo[b] += dt
            if vid in prev and prev[vid][1] == p:
                ds = s - prev[vid][0]
                if 0 <= ds < 60 * dt:                       # descarta saltos (troca de percurso / reentrada)
                    dist[b] += ds; tempo_v[b] += dt
                    b0 = min(nb - 1, max(0, int(prev[vid][0] // bin_m)))
                    if b > b0: passagens[b0:b] += 1
                    v = ds / dt
                    if v < PARADO:
                        parado_ate[vid] = parado_ate.get(vid, 0.) + dt
                        if parado_ate[vid] >= 1.0 and parado_ate[vid] - dt < 1.0: paradas[vid] = paradas.get(vid, 0) + 1
                    else: parado_ate[vid] = 0.
            prev[vid] = (s, p)
            if vid not in first: first[vid] = (t, s, p)
            last[vid] = (t, s, p)
    trechos = []
    for b in range(nb):
        if tempo[b] <= 0: continue
        vmed = dist[b] / tempo_v[b] * 3.6 if tempo_v[b] > 0 else 0.
        trechos.append({'de_m': int(b * bin_m), 'ate_m': int((b + 1) * bin_m),
                        'velocidade_media_kmh': round(float(vmed), 1),
                        'densidade_veic_km': round(float(tempo[b] / T / (bin_m / 1000.)), 2),
                        'fluxo_veic_h': round(float(passagens[b] * 3600. / T), 0)})
    # viagens completas = percorreram >= 80% do comprimento do percurso em que terminaram
    tt = []; atr = []
    for vid, (t0, s0, p0) in first.items():
        t1, s1, p1 = last[vid]
        L = comprimentos[p1] if p1 < len(comprimentos) else 0
        if L <= 0 or s1 - s0 < 0.8 * L or t1 <= t0: continue
        dur = t1 - t0; tt.append(dur)
        if v_livre and v_livre > 0: atr.append(max(0., dur - (s1 - s0) / v_livre))
    todas_paradas = sum(paradas.values()); n = len(first)
    vtot = float(dist.sum() / tempo_v.sum() * 3.6) if tempo_v.sum() > 0 else 0.
    return {'disponivel': True, 'periodo_s': round(T, 1), 'veiculos_medidos': n, 'viagens_completas': len(tt),
            'tempo_viagem_medio_s': round(float(np.mean(tt)), 1) if tt else None,
            'atraso_medio_s': round(float(np.mean(atr)), 1) if atr else None,
            'velocidade_media_kmh': round(vtot, 1),
            'paradas_por_veiculo': round(todas_paradas / n, 2) if n else 0.,
            'por_trecho': trechos,
            'escopo': 'Medido após o aquecimento; velocidade = distância/tempo por trecho de 100 m; parada = v<0,3 m/s por ≥1 s.'}


def analisar(sim):
    """Indicadores da simulação `sim` (simulation.Simulation já executada)."""
    try:
        frames = getattr(sim, 'frames', None)
        comps = [float(p['length']) for p in getattr(sim, 'paths', [])]
        vl = float(getattr(getattr(sim, 's', None), 'traffic_speed_kmh', 0) or 0) / 3.6
        r = analisar_frames(frames, comps, vl, getattr(__import__('app.simulation', fromlist=['DT']), 'DT', .2))
        if r.get('disponivel'):
            r['fila_maxima_veic'] = max(list(getattr(sim, 'max_queue_lane', []) or [0]) + [0])
        return r
    except Exception as e:
        return {'disponivel': False, 'motivo': 'falha ao medir: ' + str(e)[:120]}


def comparar(a, b):
    """Diferença B − A entre dois cenários (dicionários de analisar). Positivo = B maior."""
    if not (a.get('disponivel') and b.get('disponivel')): return {'disponivel': False}
    campos = ('tempo_viagem_medio_s', 'atraso_medio_s', 'velocidade_media_kmh', 'paradas_por_veiculo', 'fila_maxima_veic')
    out = {}
    for c in campos:
        x, y = a.get(c), b.get(c)
        out[c] = {'A': x, 'B': y, 'delta': (round(y - x, 2) if x is not None and y is not None else None)}
    return {'disponivel': True, 'indicadores': out}
