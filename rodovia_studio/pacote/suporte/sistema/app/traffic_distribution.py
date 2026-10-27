"""Distribuição por movimento validado; não cria ligações nem altera obstáculos."""
import math
import numpy as np
from collections import defaultdict


def movement_weights(network,default_secondary=20.):
    custom={}
    for row in getattr(network,'rule_report',[]):
        if row.get('applied') and row.get('action')=='force' and row.get('share_pct') is not None and 'from_edge' in row:
            key=(row['from_edge'],row['to_edge'])
            if key in custom and custom[key]!=row['share_pct']:raise ValueError('Percentuais conflitantes para a mesma ligação. Edite as regras do ramal.')
            custom[key]=float(row['share_pct'])/100
    weights={};groups=[]
    for i,children in getattr(network,'connections',{}).items():
        children=[j for j in children if not network.edges[j].get('disabled')]
        if not children:continue
        if len(children)==1:
            value=custom.get((i,children[0]))
            if value is not None and value not in (0.,1.):raise ValueError('Percentual de ramal exige saída principal e secundária válidas. Há somente uma saída neste ponto; conecte as duas vias ou deixe o percentual em branco.')
            weights[(i,children[0])]=1. if value is None else value;continue
        incoming=network.edges[i]
        def priority(j):
            edge=network.edges[j];origin=edge.get('origin');length=getattr(network,'origin_info',{}).get(origin,(edge.get('length',0),))[0]
            same=int(origin is not None and origin==incoming.get('origin'))
            cosine=float(np.asarray(incoming['t'][-1])@np.asarray(edge['t'][0]))
            return same,float(length),cosine,-j
        main=max(children,key=priority);secondary=float(default_secondary)/100
        defaults={j:(1-secondary if j==main else secondary/(len(children)-1)) for j in children}
        fixed={j:custom[(i,j)] for j in children if (i,j) in custom};total=sum(fixed.values());free=[j for j in children if j not in fixed]
        if total>1+1e-9 or not free and abs(total-1)>1e-9:raise ValueError('Percentuais das saídas de um mesmo ponto devem totalizar 100%. Revise as ligações do ramal.')
        denominator=sum(defaults[j] for j in free)
        for j in children:
            value=fixed[j] if j in fixed else (1-total)*(defaults[j]/denominator if denominator>0 else 1/len(free))
            weights[(i,j)]=value
        groups.append({'from_edge':i,'primary_edge':main,'outputs':[{'edge':j,'percent':round(weights[(i,j)]*100,6)} for j in children]})
    return weights,groups


def apply_distribution(sim):
    net=sim.net;settings=sim.s
    weights,groups=movement_weights(net,getattr(settings,'traffic_branch_share_pct',20))
    probabilities={};rows=[]
    for entry,ids in sim.siblings.items():
        scores=[]
        for i in ids:
            score=1.
            for link,_,_ in sim.link_of[i]:
                if link[0]=='c':score*=weights.get((link[1],link[2]),1.)
            scores.append(score)
        total=sum(scores)
        if total<=0:probabilities[entry]=[0.]*len(ids)
        else:probabilities[entry]=[v/total for v in scores]
        # Somente uma demanda física por entrada, repartida entre seus itinerários.
        demand=getattr(settings,'traffic_demand_vphpl',None)
        reference=ids[int(np.argmax(scores))]
        arrival=float(demand)/3600 if demand is not None else sim.rate[reference]
        for i,p in zip(ids,probabilities[entry]):sim.rate[i]=arrival*p
        rows.append({'entry':str(entry),'vehicles_h':round(arrival*3600,3),'itineraries':[{'path':i,'percent':round(p*100,6)} for i,p in zip(ids,probabilities[entry])]})
    vdm=getattr(settings,'traffic_vdm',None)
    if vdm is not None:
        axis=np.asarray(net.axis);direction=axis[-1]-axis[0];forward=[];reverse=[]
        for entry,ids in sim.siblings.items():
            h=sim.paths[ids[0]]['p'][1]-sim.paths[ids[0]]['p'][0]
            (forward if float(h@direction)>=0 else reverse).append(entry)
        total=float(vdm)*float(settings.traffic_peak_hour_fraction)
        forward_share=1. if not reverse else 0. if not forward else settings.traffic_forward_share_pct/100
        for entries,share in [(forward,forward_share),(reverse,1-forward_share)]:
            if not entries:continue
            arrival=total*share/len(entries)/3600
            for entry in entries:
                for i,p in zip(sim.siblings[entry],probabilities[entry]):sim.rate[i]=arrival*p
        for row in rows:row['vehicles_h']=round(sum(sim.rate[i] for i in sim.siblings[next(e for e in sim.siblings if str(e)==row['entry'])])*3600,3)
    effective='rotas' if getattr(settings,'traffic_route_only',False) else 'VDM' if vdm is not None else 'demanda_horaria' if getattr(settings,'traffic_demand_vphpl',None) is not None else 'densidade'
    sim.distribution_report={'effective_mode':effective,'default_secondary_percent':getattr(settings,'traffic_branch_share_pct',20),'movements':groups,'entries':rows,'vdm':vdm,'mode':'VDM' if vdm is not None else 'demanda_horaria' if getattr(settings,'traffic_demand_vphpl',None) is not None else 'densidade','scope':'Percentuais de escolha dos itinerários disponíveis, não garantia de contagem em vídeo curto. VDM refere-se ao conjunto das entradas e à fração horária configurada; não certifica nível de serviço.'}
