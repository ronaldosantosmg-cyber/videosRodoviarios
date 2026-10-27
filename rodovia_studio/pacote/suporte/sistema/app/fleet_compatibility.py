"""Compatibilidade por classe da frota; mesma decisão de admissão da simulação."""
from . import visual
from .flow_diagnostics import REASONS

def compatibility(sim,network,settings,cancel=lambda:False,status=lambda *a:None,complete=True):
    rows=[]
    if settings.traffic_classic or not hasattr(sim,'motion_valid'):return {'mode':'ensaio','paths':[],'notice':'Clássico ilustrativo: não valida a frota. Desative-o para conferir as proteções normais.' if settings.traffic_classic else 'Ative Incluir veículos e selecione o modelo Simulado para conferir a frota.'}
    total=len(network.paths)
    for i,path in enumerate(network.paths[:300]):
        if cancel():raise InterruptedError('Conferência de frota cancelada.')
        classes=sorted({visual.vehicle_type(path['kinds'],(i,k,0),settings.vehicle_mix) for k in range(100)})
        vehicles=[]
        for vehicle in classes:
            checked=complete or (i,vehicle) in sim.motion_cache
            ok=sim.motion_valid(i,vehicle) if checked else None;audit=sim.motion_cache.get((i,vehicle),{})
            label={'car':'Leve','car6':'Leve 6 m','moto':'Moto','moto2':'Moto 2 m','pickup':'Picape','van':'Van','bus':'Ônibus','truck':'Caminhão','truck18':'Pesado 18 m','carreta':'Carreta','long30':'Longo rígido 30 m'}[vehicle]
            point=(audit.get('critical_center_xy') or path['p'][len(path['p'])//2].tolist()) if checked and not ok else None
            vehicles.append({'label':label,'explanation':[REASONS.get(reason,{'sem_espaco_nos_portais':'Corpo sem espaço nas extremidades','veiculo_mais_largo_que_faixa':'Veículo mais largo que a faixa'}.get(reason,reason)) for reason in audit.get('reasons',[])],'type':vehicle,'ok':bool(ok) if checked else None,'checked':checked,'reasons':audit.get('reasons',[]),'point':point,'length_m':visual.TYPES[vehicle]['L'],'width_m':visual.TYPES[vehicle]['B']})
        bases=sorted({network.edges[e]['base'] for e in path.get('edges',[])})
        rows.append({'path':i,'sources':sorted({network.edges[e]['source'] for e in path.get('edges',[])}),'bases':bases,'vehicles':vehicles,'status':'pending' if any(not v['checked'] for v in vehicles) else 'ok' if all(v['ok'] for v in vehicles) else 'partial' if any(v['ok'] for v in vehicles) else 'blocked'})
        status((i+1)/max(1,total),'Conferindo frota por itinerário')
    result={'mode':'protected','paths':rows,'incomplete':total>300,'notice':'Compatibilidade geométrica por tipo; as regras dinâmicas e filas continuam ativas na simulação.'}
    network.fleet_compatibility=result;return result
