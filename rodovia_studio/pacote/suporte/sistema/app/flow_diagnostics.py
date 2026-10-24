"""Diagnóstico de circulação para o editor; não modifica rotas nem desenha no vídeo."""
import math


def flow_diagnostics(network):
    minimum=float(getattr(network,'min_route',50))
    used={int(e) for p in network.paths for e in p.get('edges',[])}
    short=set(getattr(network,'short_ignored',set()))
    by_base={}
    for i,edge in enumerate(network.edges):by_base.setdefault(edge['base'],[]).append((i,edge))
    out=[]
    for raw in network.raw_info:
        points=raw.get('points',[])
        finite=len(points)>=2 and all(math.isfinite(float(v)) for p in points for v in p)
        length=sum(math.hypot(float(b[0]-a[0]),float(b[1]-a[1])) for a,b in zip(points,points[1:])) if finite else 0
        edges=by_base.get(raw['base'],[])
        active=[i for i,e in edges if not e.get('disabled') and i not in short]
        if not finite or length<=0:status,message='problem','Geometria inválida ou de comprimento nulo.'
        elif raw.get('disabled'):status,message='problem','Fluxo desativado; veículos não circulam neste trecho.'
        elif length<minimum:status,message='adjustment',f'Fluxo abaixo de {minimum:g} m; circulação desligada pelo limite do projeto.'
        elif any(i in getattr(network,'rejected_edge_ids',set()) for i,_ in edges):status,message='problem','Trajetória recusada pela análise de frente/traseira, esterçamento ou continuidade.'
        elif not active:status,message='problem','Sem faixa habilitada para circulação.'
        elif not any(i in used for i in active):status,message='adjustment','Trecho sem itinerário utilizável; revise as ligações e o sentido.'
        elif any(e.get('disabled') or e.get('crossing_blocked') for _,e in edges):status,message='adjustment','Parte das faixas está bloqueada; revise as restrições.'
        else:status,message='ok','Fluxo presente nos itinerários calculados.'
        out.append({'technical_status':status,'technical_message':message})
    return out
