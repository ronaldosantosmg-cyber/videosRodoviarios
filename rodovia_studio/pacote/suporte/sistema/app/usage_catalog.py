"""Catálogo local de uso; sugestões baseadas em eventos, sem executar código de IA."""
import math
from collections import defaultdict,Counter


def summarize(events,errors):
    groups=defaultdict(lambda:{'concluidas':0,'falhas':0,'duracoes_s':[],'esperas_s':[]})
    stages=defaultdict(list)
    def finite(value):
        try:value=float(value)
        except (TypeError,ValueError):return None
        return value if math.isfinite(value) and value>=0 else None
    for event in events:
        g=groups[str(event.get('tipo') or 'não informado')]
        if event.get('evento') in ('fim','falha'):
            g['concluidas' if event['evento']=='fim' else 'falhas']+=1
            v=finite(event.get('duracao_s'))
            if v is not None:g['duracoes_s'].append(v)
        if event.get('evento')=='inicio':
            v=finite(event.get('espera_s'))
            if v is not None:g['esperas_s'].append(v)
        if event.get('evento')=='etapa_concluida':
            v=finite(event.get('duracao_etapa_s'))
            if v is not None:stages[str(event.get('mensagem') or 'etapa')].append(v)
    def metrics(values):
        if not values:return {'amostras':0,'media_s':None,'p95_s':None,'max_s':None}
        s=sorted(values);return {'amostras':len(s),'media_s':round(sum(s)/len(s),3),'p95_s':round(s[max(0,math.ceil(len(s)*.95)-1)],3),'max_s':round(s[-1],3)}
    kinds={k:{'concluidas':g['concluidas'],'falhas':g['falhas'],'execucao':metrics(g['duracoes_s']),'espera':metrics(g['esperas_s'])} for k,g in groups.items()}
    errors_count=Counter(str(e.get('erro') or e.get('evento') or 'erro') for e in errors)
    recommendations=[]
    for kind,g in kinds.items():
        if g['falhas']:recommendations.append({'funcao':kind,'evidencia':f"{g['falhas']} falha(s) registrada(s)",'acao':'Priorizar o rastreamento e criar um teste de regressão antes de alterar a função.'})
        if (g['espera']['max_s'] or 0)>5:recommendations.append({'funcao':kind,'evidencia':f"Espera máxima {g['espera']['max_s']} s",'acao':'Separar tempo de fila e inicialização; verificar tarefas concorrentes e carga da máquina.'})
        if (g['execucao']['max_s'] or 0)>30:recommendations.append({'funcao':kind,'evidencia':f"Duração máxima {g['execucao']['max_s']} s",'acao':'Comparar as etapas, encoder, resolução e acerto de cache antes de otimizar; medir novamente com os mesmos dados.'})
    for kind,n in errors_count.items():
        recommendations.append({'funcao':'erros','evidencia':f'{kind}: {n} ocorrência(s)','acao':'Investigar a causa no log. Não desativar uma função apenas por ser lenta ou ter uma falha.'})
    return {'escopo':'Eventos locais retidos; não representa todo o histórico nem determina causalidade.','tarefas':kinds,'etapas':{k:metrics(v) for k,v in stages.items()},'erros':dict(errors_count),'melhorias_sugeridas':recommendations}
