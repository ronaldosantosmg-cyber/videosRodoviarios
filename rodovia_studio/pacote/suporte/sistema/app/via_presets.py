"""2.23: tipos de via prontos (presets). Um clique monta o alinhamento de fluxo sobre um eixo, usando o mesmo modelo
das seções tipo (nada de motor novo): o preset só preenche faixas, acostamentos, sentido e canteiro."""
import uuid
from .models import RouteAlignment

PRESETS={
 'pista_simples':{'nome':'Pista simples','descricao':'Uma faixa por sentido, eixo no centro da pista.','faixas':1,'acostamento':2.5,'canteiro':0,'ultrapassagem':'marked'},
 'pista_simples_adicional':{'nome':'Simples com faixa adicional','descricao':'Duas faixas à direita e uma à esquerda (subida).','faixas':1,'acostamento':2.5,'canteiro':0,'ultrapassagem':'marked'},
 'duplicada_canteiro':{'nome':'Duplicada com canteiro','descricao':'Eixo no canteiro; faixas em cada sentido separadas por canteiro.','faixas':2,'acostamento':2.5,'canteiro':3,'ultrapassagem':'safe'},
 'um_sentido_meio':{'nome':'Um sentido — eixo no meio','descricao':'Todas as faixas no mesmo sentido; eixo no meio da pista, sem canteiro.','faixas':2,'acostamento':2.5,'canteiro':0,'ultrapassagem':'safe'},
 'um_sentido_bordo':{'nome':'Um sentido — eixo no bordo','descricao':'Pista de um sentido com o eixo no bordo esquerdo (pista duplicada desenhada por eixo de cada sentido).','faixas':2,'acostamento':2.5,'canteiro':0,'ultrapassagem':'safe'},
 'ramal':{'nome':'Ramal / alça','descricao':'Uma faixa de um só sentido sobre o eixo (sem ultrapassagem).','faixas':1,'acostamento':0,'canteiro':0,'ultrapassagem':'off'},
 'rotatoria':{'nome':'Rotatória','descricao':'Eixo fechado; veículos giram sobre o eixo, sem ultrapassagem.','faixas':1,'acostamento':0,'canteiro':0,'ultrapassagem':'off'},
}
SENTIDOS={'auto':'automatico','crescente':'crescente','decrescente':'decrescente'}

def catalogo():
    return [{'id':k,**{a:b for a,b in v.items()}} for k,v in PRESETS.items()]

def _bands(n,largura,acostamento,pista_ativa=True):
    out=[{'kind':'pista','width_m':largura,'traffic_enabled':pista_ativa} for _ in range(max(0,n))]
    if acostamento>0:out.append({'kind':'acostamento','width_m':acostamento,'traffic_enabled':False})
    return out

def montar(preset,eixo,params=None,anterior=None):
    """Devolve o dict de um RouteAlignment validado. ``eixo``: {name,points[{x,y}],fingerprint,length_m,level}."""
    if preset not in PRESETS:raise ValueError('Tipo de via desconhecido.')
    base=PRESETS[preset];p={**{k:base[k] for k in ('faixas','acostamento','canteiro','ultrapassagem')},**(params or {})}
    n=int(p['faixas']);largura=float(p.get('largura',3.5));acost=float(p['acostamento']);canteiro=float(p['canteiro'])
    if not 1<=n<=4:raise ValueError('Use de 1 a 4 faixas por sentido.')
    if not 2.5<=largura<=5:raise ValueError('A largura da faixa deve ficar entre 2,5 e 5 m.')
    sentido=SENTIDOS.get(p.get('sentido','auto'),'automatico')
    pts=[{'x':float(q['x']),'y':float(q['y'])} for q in eixo['points']]
    length=float(eixo.get('length_m') or 0) or sum(((b['x']-a['x'])**2+(b['y']-a['y'])**2)**.5 for a,b in zip(pts,pts[1:]))
    sec_id=((anterior or {}).get('cross_sections') or [{}])[0].get('id') or uuid.uuid4().hex[:12]
    sec={'id':sec_id,'name':PRESETS[preset]['nome'],'start_m':0,'end_m':max(1.,length),'type':'simples','median_m':0}
    route={'id':(anterior or {}).get('id') or uuid.uuid4().hex[:12],'name':('Via · '+str(eixo.get('name','Eixo')))[:80],'points':pts,'enabled':True,'type':'simples','lanes':1,'median_m':0,
           'lane_width_m':largura,'taper_m':40,'level':int(eixo.get('level',0) or 0),'outside_pavement':False,'source':'via','source_axis_layer':str(eixo.get('name') or eixo.get('layer') or '')[:200],'source_axis_fingerprint':eixo.get('fingerprint','') or '',
           'lane_change':p['ultrapassagem'],'flow_direction':sentido}
    if p.get('velocidade'):route['speed_kmh']=float(p['velocidade'])
    if preset=='pista_simples':
        sec.update(left=_bands(1,largura,acost),right=_bands(1,largura,acost))
    elif preset=='pista_simples_adicional':
        sec.update(left=_bands(1,largura,acost),right=_bands(2,largura,acost))
    elif preset=='duplicada_canteiro':
        sec.update(type='dupla',median_m=canteiro,left=_bands(n,largura,acost),right=_bands(n,largura,acost))
    elif preset=='um_sentido_meio':
        esq=n//2;dir_=n-esq;sec.update(left=_bands(esq,largura,acost),right=_bands(dir_,largura,acost),left_dir='mesmo',right_dir='mesmo')
        if esq==0:sec['left']=[{'kind':'acostamento','width_m':acost,'traffic_enabled':False}] if acost>0 else []
    elif preset=='um_sentido_bordo':
        sec.update(left=[{'kind':'acostamento','width_m':acost,'traffic_enabled':False}] if acost>0 else [],right=_bands(n,largura,acost),left_dir='mesmo',right_dir='mesmo')
    elif preset in ('ramal','rotatoria'):
        route.update(type='unico',lanes=n)
        if preset=='rotatoria':route['flow_role']='rotatoria'
        r=RouteAlignment.model_validate(route);return r.model_dump()
    route.update(cross_sections=[sec],sections_only=True,section_surface=True)
    return RouteAlignment.model_validate(route).model_dump()
