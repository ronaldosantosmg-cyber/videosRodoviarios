"""Diagnóstico de circulação para o editor; não modifica rotas nem desenha no vídeo."""
import math

REASONS={'canteiro_ou_limite_do_corredor':'interferência com canteiro ou limite do corredor ilustrativo','corpo_fora_da_pista':'corpo do veículo fora do pavimento reconhecido',
         'esterco_excessivo':'curva incompatível com o esterçamento do veículo',
         'mudanca_brusca':'mudança brusca de direção','auto_intersecao':'traçado cruza a si mesmo',
         'ziguezague':'ziguezague','frente_traseira_degeneradas':'frente/traseira sem direção válida',
         'geometria_invalida':'coordenadas ou comprimento inválidos','rota_excessiva':'extensão excessiva'}


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
        circulating=[i for i in active if i in used]
        effective_length=network.origin_info.get(raw.get('origin_id'),(length,False))[0] if raw.get('native_axis') else length
        if not finite or length<=0:status,message='problem','Geometria inválida ou de comprimento nulo.'
        elif raw.get('disabled'):status,message='problem','Fluxo desativado; veículos não circulam neste trecho.'
        elif effective_length<minimum:status,message='adjustment',f'Fluxo abaixo de {minimum:g} m; circulação desligada pelo limite do projeto.'
        elif any(i in getattr(network,'rejected_edge_ids',set()) for i,_ in edges):
            status,message=('adjustment','Há circulação validada, mas parte das ligações foi recusada; localize e revise os trechos excluídos.') if circulating else ('problem','Trajetória recusada pela análise de frente/traseira, esterçamento ou continuidade.')
        elif not active:status,message='problem','Sem faixa habilitada para circulação.'
        elif not any(i in used for i in active):status,message='problem','Trecho sem itinerário utilizável; revise as ligações, o nível e o sentido.'
        elif any(e.get('disabled') or e.get('crossing_blocked') for _,e in edges):status,message='adjustment','Parte das faixas está bloqueada; revise as restrições.'
        else:status,message='ok','Fluxo presente nos itinerários calculados.'
        edge_ids={i for i,_ in edges};critical=[]
        for item in getattr(network,'rejected_paths',[]):
            audit=item['audit'];point=audit.get('critical_center_xy') or audit.get('front_xy')
            if point and edge_ids.intersection(item['edges']):critical.append({'point':point,'reasons':audit.get('reasons',[])})
        if status!='ok' and not circulating and finite and not raw.get('disabled') and effective_length>=minimum:
            from .vehicle_motion import analyze_motion
            if 'diagnostic_audit' not in raw:raw['diagnostic_audit']=analyze_motion(points,allowed=getattr(network,'allowed',None))
            audit=raw['diagnostic_audit']
            if not audit['ok']:
                status='problem';message='Bloqueio localizado: '+ '; '.join(REASONS.get(r,r) for r in audit['reasons'])+'.'
                if audit.get('critical_center_xy'):critical.append({'point':audit['critical_center_xy'],'reasons':audit['reasons']})
        reasons=list(dict.fromkeys(r for item in critical for r in item['reasons']))
        if status=='ok' and raw.get('native_axis') and length<minimum:
            message=f'Subtrecho integrado ao eixo DXF contínuo de {effective_length:.1f} m; não é uma mini-rota independente.'
        if raw.get('lateral_fits') and status=='ok':message+=' Afastamento ajustado automaticamente para acomodar o veículo dentro da pista.'
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
        elif effective_length<minimum and finite and length>0:
            automatic=f'Manter a geometria e desligar a circulação abaixo de {minimum:g} m.'
            manual='Revisar o limite do projeto ou criar manualmente uma rota contínua válida.'
        else:
            automatic='Excluir os movimentos inválidos da simulação; preservar o traçado original para revisão.'
            manual='Editar os pontos, o sentido e as ligações; recalcular e conferir o diagnóstico antes de circular.'
        if 'corpo_fora_da_pista' in reasons:
            manual='Confira a área de pavimento no ponto indicado: corrija a classificação/hachura ou reposicione a faixa dentro da pista. Linhas de bordo não são barreiras; canteiros, obstáculos e cortes continuam bloqueando.'
        elif status=='adjustment' and effective_length>=minimum:
            manual='Confira as pontas, o sentido e a camada Eixo. Para escolha explícita, use Rota de veículos → Selecionar uma linha / Seleção contínua, confirme o sentido e recalcule.'
        if getattr(network,'classic',False) and circulating:
            status='adjustment';message='ENSAIO CLÁSSICO: veículos ilustrativos; somente canteiros e integridade numérica conferidos.'
            automatic='Manter o ensaio explicitamente identificado; não considerar circulação validada.'
            manual='Desative o modo clássico para validar colisões, semáforos e demais restrições.'
        from .flow_assistant import guidance
        assistant=guidance(status,reasons,disabled=bool(raw.get('disabled')),length=effective_length,minimum=minimum,points=critical)
        out.append({'technical_status':status,'technical_message':message,'technical_assistant':assistant,
                    'technical_exclusion':('manual' if raw.get('disabled') else 'length_limit' if finite and length>0 and effective_length<minimum else None),
                    'technical_circulation':{'enabled':bool(circulating),'used_edges':len(circulating),'active_edges':len(active),'blocked_edges':sum(bool(e.get('disabled')) for _,e in edges)},
                    'technical_lateral_fits':raw.get('lateral_fits',[]),'technical_automatic':automatic,'technical_manual':manual,'technical_recovery':recovery_info,'technical_points':critical[:20],'technical_reasons':reasons})
    return out
