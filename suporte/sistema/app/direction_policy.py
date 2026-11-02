"""2.28: política única de sentido dos eixos.

Antes, o sentido vinha de vários lugares (escolha do eixo, rota cadastrada, seta, OAE, inversão no trecho) e cada tela
mostrava só o seu pedaço. Aqui fica a ordem de decisão, escrita uma vez, e o relatório que diz, para cada eixo,
qual sentido vale, de onde ele vem e o que foi sobrescrito.

Ordem (do mais forte ao mais fraco):
 1. seta desenhada sobre a pista (direction_marks)        -> vale no trecho da seta
 2. sentido explícito da rota cadastrada / trajetória    -> flow_direction, TrafficPath.direction
 3. sentido da OAE                                       -> só sobre o tabuleiro, e só se nada acima definir
 4. escolha do eixo (route_directions['axis:…'])
 5. escolha do layer (route_directions['layer:…'])
 6. automático (geometria e mão de direção)
Modificadores: inverter no trecho (flow_overrides 'reverse') troca o resultado; 'disable' tira os veículos;
inverter eixo (reverse_axis) muda o sentido do km (referência), não escolhe o sentido do tráfego.
"""
from .native_axes import axis_fingerprint,direction_for

ROTULO={'forward':'Crescente (km)','reverse':'Decrescente (km)','off':'Sem veículos','auto':'Automático'}
ORIGEM={'seta':'seta desenhada','rota':'rota cadastrada','oae':'OAE','eixo':'escolha do eixo','layer':'escolha do layer','auto':'automático'}

def resolver_eixo(settings,axis):
    """Sentido efetivo de um eixo do DXF e a cadeia de decisão (todas as fontes, ativas ou sobrescritas)."""
    rd=getattr(settings,'route_directions',None) or {}
    layer=str(axis.get('layer',''));fp=axis_fingerprint(axis['points'],layer,axis.get('level',0));chave='axis:'+fp
    v_eixo=rd.get(chave) if rd.get(chave) in ('forward','reverse','off') else None
    v_layer=rd.get('layer:'+layer) if rd.get('layer:'+layer) in ('forward','reverse','off') else None
    rotas=[r for r in (getattr(settings,'route_alignments',None) or []) if getattr(r,'source_axis_fingerprint','')==fp]
    rota_expl=[r for r in rotas if getattr(r,'flow_direction','automatico') in ('crescente','decrescente')]
    cadeia=[]
    if rota_expl:
        r=rota_expl[0];cadeia.append(dict(fonte='rota',valor='forward' if r.flow_direction=='crescente' else 'reverse',nota=f'rota “{r.name}”'))
    if v_eixo:cadeia.append(dict(fonte='eixo',valor=v_eixo,nota='escolha individual deste eixo'))
    if v_layer:cadeia.append(dict(fonte='layer',valor=v_layer,nota=f'layer {layer}'))
    efetivo=cadeia[0]['valor'] if cadeia else 'auto';origem=cadeia[0]['fonte'] if cadeia else 'auto'
    # 'off' do eixo ou do layer só vale se nenhuma rota explícita assumiu o eixo
    sobrescritos=[dict(c,sobrescrito_por=ORIGEM[origem]) for c in cadeia[1:] if c['valor']!=efetivo]
    conflitos=[f"{ORIGEM[c['fonte']]} ({ROTULO[c['valor']]}) é ignorada: vale {ORIGEM[origem]} ({ROTULO[efetivo]})" for c in sobrescritos]
    return dict(chave=chave,layer=layer,efetivo=efetivo,origem=origem,rotulo=ROTULO[efetivo],cadeia=cadeia,conflitos=conflitos,
                individual=v_eixo,por_layer=v_layer,rotas=[r.name for r in rotas])

def relatorio(axes,settings):
    """Relatório para a tela: um item por eixo, mais avisos gerais (chaves órfãs, setas e OAEs que também mandam)."""
    itens=[];vistas=set()
    for a in axes:
        if a.get('reference_only') or a.get('role') not in (None,'axis'):continue
        try:it=resolver_eixo(settings,a)
        except (ValueError,TypeError,KeyError,OverflowError):continue
        vistas.add(it['chave']);itens.append(it)
    rd=getattr(settings,'route_directions',None) or {}
    orfas=sorted(k for k,v in rd.items() if k.startswith('axis:') and k not in vistas and v!='auto')
    avisos=[]
    if orfas:avisos.append(f'{len(orfas)} escolha(s) antiga(s) por eixo não correspondem a nenhum eixo atual (o desenho mudou). Elas não têm efeito.')
    marcas=len(getattr(settings,'direction_marks',None) or [])
    if marcas:avisos.append(f'{marcas} seta(s) desenhada(s) mandam no trecho onde estão, acima de qualquer escolha de eixo ou layer.')
    inv=[o for o in (getattr(settings,'flow_overrides',None) or []) if getattr(o,'action','')=='reverse' and getattr(o,'enabled',True)]
    if inv:avisos.append(f'{len(inv)} inversão(ões) no trecho trocam o sentido depois da escolha do eixo.')
    if getattr(settings,'reverse_axis',False):avisos.append('“Inverter eixo” está ligado: o km corre ao contrário. “Crescente” segue o km invertido.')
    return dict(eixos=itens,orfas=orfas,avisos=avisos,ordem=[ORIGEM[k] for k in ('seta','rota','oae','eixo','layer','auto')])
