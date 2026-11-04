"""Diagnóstico de espaçamento e controles físicos para exportação da frota."""
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
    invalid=set(sim.fleet_audit.get('invalid_paths',[]))
    for v in vehicles:
        gap, _, lead = sim.leader_state(v, occ)
        if lead is None or gap >= max(12., 2. * max(0., float(v['v']))):
            continue
        permitted = any(w.get('_control_cause') in ALLOWED and
                        sim.time <= w.get('_control_until', -math.inf)
                        for w in (v, lead))
        if permitted:
            continue
        invalid.add(int(v['p']))
        if len(sim.fleet_audit['violations']) < 100 and not any(
                row['vehicle'] == v['id'] for row in sim.fleet_audit['violations']):
            sim.fleet_audit['violations'].append({'vehicle': int(v['id']), 'path': int(v['p']),
                'station_m': round(float(v['s']), 2), 'time_s': round(float(sim.time), 2),
                'reason': v.get('_why', 'desconhecido'),
                'gap_m': round(float(gap),3), 'speed_kmh': round(float(v['v'])*3.6,2),
                'leader_vehicle': int(lead['id']),'leader_path':int(lead['p']),
                'remaining_to_exit_m': round(max(0.,sim.exit_station(v['p'],v.get('t','car'))-v['s']),3) if hasattr(sim,'exit_station') and getattr(sim,'paths',None) else None})

    sim.fleet_audit['invalid_paths']=sorted(invalid)


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
    # Aproximação/ comboio é diagnóstico, não falha de exportação. Não altera
    # os veículos, não apaga ocorrências e não libera colisões físicas.
    if sim.fleet_audit['violations'] and getattr(settings,'traffic_export_scope','strict')=='validated_only':
        if getattr(sim,'simulation_complete',True):presentation_scope(sim)


def presentation_scope(sim):
    """Congela o recorte antes dos quadros; nunca apaga a auditoria original."""
    if getattr(sim.s,'traffic_export_scope','strict')!='validated_only':return {'mode':'strict','excluded_paths':[],'excluded_vehicles':0}
    if getattr(sim,'simulation_complete',True) is not True:raise ValueError('Conclua a validação de todos os trechos antes da apresentação parcial.')
    if sim.collisions or sim.side_collisions:raise ValueError('Conflito físico na simulação; apresentação parcial não pode liberar colisões.')
    invalid=set(sim.fleet_audit.get('invalid_paths',[]))|{int(v['path']) for v in sim.fleet_audit['violations']}
    cached=getattr(sim,'_presentation_scope',None)
    if cached is not None and cached['excluded_paths']==sorted(invalid):return cached
    excluded={int(v['vehicle']) for v in sim.fleet_audit['violations']}
    for ids,_,paths,_,_ in sim.frames:
        excluded.update(int(vid) for vid,path in zip(ids,paths) if int(path) in invalid)
    sim._presentation_excluded_ids=excluded
    sim._presentation_scope={'mode':'validated_only','excluded_paths':sorted(invalid),'excluded_vehicles':len(excluded),
        'intervals':[{'path':i,'start_m':0.,'end_m':float(sim.paths[i]['length'])} for i in sorted(invalid)],
        'scope':'Operação parcial: itinerários reprovados sem veículos durante todo o vídeo; auditoria integral preservada. Colisões físicas continuam bloqueando.'}
    return sim._presentation_scope


def terminal_alpha(sim,vehicle_id,path_index,station):
    from .vehicle_motion import PROFILES
    margin=float(getattr(sim.s,'traffic_exit_hidden_m',25.))
    if margin<=0:return 1.
    path=sim.paths[int(path_index)];offsets=path.get('terminal_offsets_m',[0.,0.])
    end_offset=float(offsets[1]) if len(offsets)>1 else 0.
    length=PROFILES.get(sim.info[int(vehicle_id)][1],PROFILES['car'])[0]
    gate=float(path['length'])+end_offset-margin
    remaining=gate-(float(station)+length/2)
    fade=max(.5,min(8.,margin/2));x=max(0.,min(1.,remaining/fade))
    return x*x*(3-2*x)


def presentation_vehicles(sim,t):
    excluded=set()
    if getattr(sim.s,'traffic_export_scope','strict')=='validated_only':
        presentation_scope(sim);excluded=sim._presentation_excluded_ids
    alpha={int(vid):terminal_alpha(sim,vid,path,s) for vid,path,s,_,_ in sim.state(t)}
    sim._presentation_alpha=alpha
    return (v for v in sim.vehicles_ex(t) if int(v[2]) not in excluded and alpha.get(int(v[2]),1.)>0.)
