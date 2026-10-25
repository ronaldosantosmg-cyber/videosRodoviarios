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
        edge_ids={i for i,_ in edges};critical=[]
        for item in getattr(network,'rejected_paths',[]):
            audit=item['audit'];point=audit.get('critical_center_xy') or audit.get('front_xy')
            if point and edge_ids.intersection(item['edges']):critical.append({'point':point,'reasons':audit.get('reasons',[])})
        recovery=raw.get('recovery_reports') or []
        for report in recovery:
            for points in report.get('excluded_geometry',[]):
                if points:critical.append({'point':points[len(points)//2],'reasons':report.get('reasons',[])})
        recovery_info=None
        if raw.get('recovery_enabled'):
            retained=sum(b-a for report in recovery for a,b in report['retained'])
            excluded=sum(b-a for report in recovery for a,b in report['excluded'])
            recovery_info={'enabled':True,'retained_m':round(retained,2),'excluded_m':round(excluded,2),'reports':recovery}
            if recovery and any(i in used for i in active):
                status='adjustment' if excluded>0 else status
                message=f'Fluxo principal recuperado: {retained:.1f} m revalidados; {excluded:.1f} m excluídos da circulação. O eixo original foi preservado.'
                if any(report.get('strategy')=='suavizacao_leve_validada' for report in recovery):message+=' Aplicada suavização leve na trajetória dos veículos (até 0,5 m).'
            elif recovery:
                status='problem';message='Não foi possível recuperar circulação segura. O eixo original foi preservado; revise os pontos indicados no diagnóstico.'
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
                    'technical_automatic':automatic,'technical_manual':manual,'technical_recovery':recovery_info,'technical_points':critical[:20]})
    return out
