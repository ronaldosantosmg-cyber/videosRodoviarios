"""2.45: nível de serviço A–F (referência HCM 2000, adotada no Manual de Estudos de Tráfego do DNIT, 2006).

ATENÇÃO: os limiares abaixo vêm da metodologia HCM 2000 como o DNIT a adota; NÃO foram conferidos aqui contra o seu exemplar do manual. Estão em TABELAS
(editável por `service_level_table`) para você ajustar ao critério do seu contrato.

Duas funções:
  • demanda_efetiva(settings): escolhido um nível-alvo, devolve a demanda por faixa (veíc/h/faixa) que coloca a via no MEIO da faixa de v/c daquele nível;
  • analisar(sim): mede na simulação (densidade, velocidade, % de veículos em pelotão, v/c) e classifica A–F por faixa e no conjunto.
"""
import math
import numpy as np

NIVEIS='ABCDEF'
# v/c máximo por nível (A..E). F = demanda acima da capacidade.
TABELAS={
 'pista_dupla':{'nome':'Pista dupla / multifaixa','criterio':'densidade','densidade_max':[11,18,26,35,45],'unidade':'veíc.eq/km/faixa','vc_max':[.32,.50,.72,.89,1.00],'capacidade_ref_vphpl':2200},
 'pista_simples':{'nome':'Pista simples (por sentido)','criterio':'pelotao','pelotao_max':[35,50,65,80],'velocidade_min_kmh':[90,80,70,60],'unidade':'% tempo em pelotão','vc_max':[.15,.27,.43,.64,1.00],'capacidade_ref_vphpl':1700},
}

def tabela(tipo,settings=None):
    t={k:(list(v) if isinstance(v,list) else v) for k,v in TABELAS[tipo].items()}
    over=(getattr(settings,'service_level_table',None) or {}).get(tipo) if settings is not None else None
    if over:t.update({k:v for k,v in over.items() if k in t})
    return t

def faixa_vc(tipo,nivel,settings=None):
    """(inferior, superior) de v/c do nível."""
    vc=tabela(tipo,settings)['vc_max'];i=NIVEIS.index(nivel)
    lo=0. if i==0 else vc[min(i,5)-1];hi=vc[i] if i<5 else vc[-1]*1.1
    return lo,hi

def tipo_da_via(settings,sim=None):
    escolha=getattr(settings,'service_level_road','auto')
    if escolha in TABELAS:return escolha
    if sim is not None:
        try:
            if any(len(ids)>=2 for ids in sim.siblings.values()):return 'pista_dupla'
        except (AttributeError,TypeError):pass
    return 'pista_simples'

def demanda_efetiva(settings,sim=None):
    """Demanda por faixa (veíc/h/faixa) vinda do nível-alvo; None = usar a demanda manual (comportamento antigo)."""
    alvo=getattr(settings,'service_level_target','manual')
    if alvo not in tuple(NIVEIS):return getattr(settings,'traffic_demand_vphpl',None)
    tipo=tipo_da_via(settings,sim);lo,hi=faixa_vc(tipo,alvo,settings)
    cap=float(getattr(settings,'traffic_capacity_vphpl',1900.))
    if tipo=='pista_simples':cap=min(cap,float(tabela(tipo,settings)['capacidade_ref_vphpl']))
    meio=(lo+hi)/2 if alvo!='F' else 1.05
    return max(1.,round(meio*cap,1))

def classificar_densidade(tipo,dens,settings=None):
    lim=tabela(tipo,settings).get('densidade_max')
    if not lim:return None
    for i,l in enumerate(lim):
        if dens<=l:return NIVEIS[i]
    return 'F'
def classificar_pelotao(pct,vel_kmh,settings=None):
    t=tabela('pista_simples',settings);a=None
    for i,l in enumerate(t['pelotao_max']):
        if pct<=l:a=i;break
    a=5 if a is None else a
    b=None
    for i,l in enumerate(t['velocidade_min_kmh']):
        if vel_kmh>=l:b=i;break
    b=4 if b is None else b      # abaixo do último limite: E
    return NIVEIS[max(a,b) if a<5 else 5]
def classificar_vc(tipo,vc,settings=None):
    for i,l in enumerate(tabela(tipo,settings)['vc_max']):
        if vc<=l:return NIVEIS[i]
    return 'F'
def pior(*n):
    n=[x for x in n if x];return max(n,key=NIVEIS.index) if n else None

def analisar(sim,intervalo_s=1.0):
    """Mede o nível de serviço na simulação já executada (usa sim.frames). Só faixas de circulação principal (kind main/marginal)."""
    frames=getattr(sim,'frames',None)
    if not frames:return {'disponivel':False,'motivo':'simulação sem quadros'}
    from .simulation import TYPE_DYN,DT
    settings=sim.s;tipo=tipo_da_via(settings,sim);paths=sim.paths
    principais=[i for i,p in enumerate(paths) if str(p.get('kind') or (p.get('kinds') or ['main'])[0]).lower() in ('main','marginal')] or list(range(len(paths)))
    comp={i:float(paths[i]['length']) for i in principais}
    passo=max(1,int(round(intervalo_s/DT)));dens={i:[] for i in principais};vel={i:[] for i in principais};seg={i:[0,0] for i in principais}
    pcu_por_id={}
    for vid,(pj,vt,_) in getattr(sim,'info',{}).items():pcu_por_id[vid]=float(TYPE_DYN.get(vt,TYPE_DYN['car'])['pcu'])
    anterior=None
    for k in range(0,len(frames),passo):
        ids,ss,ps,to,al=frames[k];ids=np.asarray(ids);ss=np.asarray(ss,float);ps=np.asarray(ps)
        v_inst={}
        if anterior is not None and len(ids):
            m,mp=anterior
            for i,s_,p_ in zip(ids.tolist(),ss.tolist(),ps.tolist()):
                if i in m and mp.get(i)==p_:v_inst[i]=max(0.,(s_-m[i])/(passo*DT))
        for i in principais:
            sel=np.flatnonzero(ps==i)
            if not len(sel):dens[i].append(0.);continue
            eq=sum(pcu_por_id.get(int(ids[j]),1.) for j in sel);dens[i].append(eq/(comp[i]/1000.))
            ordem=sel[np.argsort(ss[sel])]
            for a_,b_ in zip(ordem[:-1],ordem[1:]):       # b_ está à frente de a_: seguidor a_
                va=v_inst.get(int(ids[a_]))
                if va is None:continue
                hw=float(ss[b_]-ss[a_])/max(va,.1);seg[i][1]+=1;seg[i][0]+=1 if hw<3.0 else 0
            for j in sel:
                if int(ids[j]) in v_inst:vel[i].append(v_inst[int(ids[j])])
        anterior=({int(i):float(s_) for i,s_ in zip(ids.tolist(),ss.tolist())},{int(i):int(p_) for i,p_ in zip(ids.tolist(),ps.tolist())})
    horas=max(1e-6,(len(frames)*DT)/3600.);cap=float(getattr(settings,'traffic_capacity_vphpl',1900.))
    linhas=[];tudo_d=[];tudo_v=[];pel=[0,0]
    for i in principais:
        if not dens[i]:continue
        d=float(np.mean(dens[i]));v=float(np.mean(vel[i])*3.6) if vel[i] else None;fluxo=(sim.spawned_by_path[i]/horas) if hasattr(sim,'spawned_by_path') else None
        p=100.*seg[i][0]/seg[i][1] if seg[i][1] else 0.
        nd=classificar_densidade(tipo,d,settings) if tipo=='pista_dupla' else None
        npel=classificar_pelotao(p,v if v is not None else 999,settings) if tipo=='pista_simples' else None
        vc=(fluxo/cap) if fluxo is not None else None;nvc=classificar_vc(tipo,vc,settings) if vc is not None else None
        linhas.append({'faixa':i,'densidade_eq_km':round(d,2),'velocidade_kmh':None if v is None else round(v,1),'pelotao_pct':round(p,1),'fluxo_vph':None if fluxo is None else round(fluxo,1),'vc':None if vc is None else round(vc,3),'nivel':pior(nd,npel),'nivel_vc':nvc})
        tudo_d.append(d);pel[0]+=seg[i][0];pel[1]+=seg[i][1]
        if v is not None:tudo_v.append(v)
    if not linhas:return {'disponivel':False,'motivo':'sem veículos nas faixas principais'}
    D=float(np.mean(tudo_d));V=float(np.mean(tudo_v)) if tudo_v else None;P=100.*pel[0]/pel[1] if pel[1] else 0.
    n=classificar_densidade(tipo,D,settings) if tipo=='pista_dupla' else classificar_pelotao(P,V if V is not None else 999,settings)
    return {'disponivel':True,'tipo_via':tipo,'tipo_nome':tabela(tipo,settings)['nome'],'criterio':tabela(tipo,settings)['criterio'],'alvo':getattr(settings,'service_level_target','manual'),'nivel':n,
            'densidade_eq_km_faixa':round(D,2),'velocidade_media_kmh':None if V is None else round(V,1),'pelotao_pct':round(P,1),'faixas':linhas,
            'referencia':'HCM 2000 / Manual de Estudos de Tráfego DNIT (2006) — limiares editáveis; conferir com o exemplar do contrato.'}
