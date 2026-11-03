"""Regra de apresentação da frota. Não substitui as reservas físicas de segurança."""
import math

ALLOWED = {'semaforo', 'pedestres', 'rotatoria'}


def inspect(sim, vehicles, occ, dt=1.):
    """Par compacto: folga < max(12 m, 2 s de velocidade), em qualquer amostra.

    Semáforo, travessia e preferência de rotatória permitem a aproximação
    somente enquanto a causa de controle do par estiver vigente.
    """
    if not hasattr(sim, 'fleet_audit'):
        sim.fleet_audit = {'enabled': True, 'violations': [], 'samples': 0,
                           'definition': 'Par de veículos com folga < max(12 m, 2 s de velocidade), sem controle permitido vigente; qualquer amostra.'}
    sim.fleet_audit['samples'] += 1
    for v in vehicles:
        gap, _, lead = sim.leader_state(v, occ)
        if lead is None or gap >= max(12., 2. * max(0., float(v['v']))):
            continue
        permitted = any(w.get('_control_cause') in ALLOWED and
                        sim.time <= w.get('_control_until', -math.inf)
                        for w in (v, lead))
        if permitted:
            continue
        if len(sim.fleet_audit['violations']) < 100 and not any(
                row['vehicle'] == v['id'] for row in sim.fleet_audit['violations']):
            sim.fleet_audit['violations'].append({'vehicle': int(v['id']), 'path': int(v['p']),
                'station_m': round(float(v['s']), 2), 'time_s': round(float(sim.time), 2),
                'reason': v.get('_why', 'desconhecido')})


def validate_mode(settings):
    """Recusa configurações incompatíveis antes de gastar tempo preparando a cena."""
    if not settings.traffic:return
    if settings.traffic_classic or settings.traffic_model!='simulado':
        raise ValueError('A regra de ouro exige o modelo de tráfego simulado para exportar veículos.')
    if not settings.traffic_prevent_collisions or not settings.traffic_respect_signals:
        raise ValueError('Ative prevenção de colisões e respeito à sinalização para exportar a frota.')


def require_export(sim, settings=None, *, allow_partial=False):
    if sim is None:
        if settings is not None and settings.traffic:
            raise ValueError('A frota exige microssimulação validada para exportação.')
        return
    if not allow_partial and getattr(sim,'simulation_complete',True) is not True:
        raise ValueError('A simulação ainda não terminou; o vídeo não pode ser publicado.')
    if not hasattr(sim, 'fleet_audit'):
        raise ValueError('A regra de ouro exige microssimulação validada; o modo clássico não pode ser exportado com veículos.')
    settings = sim.s
    if not settings.traffic_prevent_collisions or not settings.traffic_respect_signals:
        raise ValueError('Ative prevenção de colisões e respeito à sinalização para exportar a frota.')
    if sim.collisions or sim.side_collisions:
        raise ValueError('Conflito veicular detectado; exportação bloqueada.')
    if sim.fleet_audit['violations']:
        row = sim.fleet_audit['violations'][0]
        raise ValueError(f"Regra de ouro: comboio sem semáforo, pedestre ou preferência de rotatória no percurso {row['path']}, posição {row['station_m']} m. Revise a demanda e os fluxos; vídeo bloqueado.")
