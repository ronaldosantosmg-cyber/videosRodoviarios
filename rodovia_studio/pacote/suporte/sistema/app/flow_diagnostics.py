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
        try:
            finite=len(points)>=2 and all(len(p)==2 and all(math.isfinite(float(v)) for v in p) for p in points)
        except (TypeError,ValueError,OverflowError):
            finite=False
        length=sum(math.hypot(float(b[0])-float(a[0]),float(b[1])-float(a[1])) for a,b in zip(points,points[1:])) if finite else 0
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
        # Correção automática conservadora: nunca inventar ligações ou sentido.
        # O motor já exclui geometrias e movimentos recusados dos itinerários.
        if status=='ok':
            automatic='Manter a circulação e monitorar no próximo cálculo.'
            manual='Editar somente se necessário; recalcular após qualquer alteração.'
        elif raw.get('disabled'):
            automatic='Manter desligado; não reativar uma desativação manual.'
            manual='Revisar o traçado e o sentido antes de habilitar e recalcular.'
        elif length<minimum and finite and length>0:
            automatic=f'Manter a geometria e desligar a circulação abaixo de {minimum:g} m.'
            manual='Revisar o limite do projeto ou criar manualmente uma rota contínua válida.'
        else:
            automatic='Excluir os movimentos inválidos da simulação; preservar o traçado original para revisão.'
            manual='Editar os pontos, o sentido e as ligações; recalcular e conferir o diagnóstico antes de circular.'
        out.append({'technical_status':status,'technical_message':message,
                    'technical_automatic':automatic,'technical_manual':manual})
    return out
