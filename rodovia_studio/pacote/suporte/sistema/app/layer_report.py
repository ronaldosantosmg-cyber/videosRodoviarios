"""1.42.41: relatório de interpretação das layers do DXF.

Mostra, antes do vídeo, o que o motor entendeu de cada layer: papel (projeto, perfil ou nenhum), de onde vem
esse papel, tipos de entidade, confiança e alertas de incoerência. Somente leitura: não altera o mapeamento.
"""
import collections
from pathlib import Path

LINEAR={'LINE','LWPOLYLINE','POLYLINE','SPLINE','ARC','CIRCLE','ELLIPSE'}
AREAL={'HATCH','SOLID','3DFACE','MPOLYGON'}
ANNOT={'TEXT','MTEXT','INSERT','IMAGE','DIMENSION','LEADER','MLEADER','POINT','ATTRIB','ATTDEF','VIEWPORT','WIPEOUT','OLE2FRAME'}

# Geometria esperada por papel: 'linear', 'areal' (hachura ou polilinha fechada) ou 'mista'.
EXPECTED={'axis':'linear','edge_line':'linear','barrier':'linear','sign_h':'mista','sign_v':'ponto','water':'mista',
          'pavement':'areal','existing_pavement':'areal','oae':'areal','shoulder':'mista','median':'mista','cut':'mista','fill':'mista',
          'earthwork':'mista','domain':'mista'}

def _kind(dxftype,closed=False):
    if dxftype in AREAL:return 'areal'
    if dxftype in LINEAR:return 'linear'
    if dxftype in ANNOT:return 'anotacao'
    return 'outro'

def scan(entities):
    """Resume entidades por layer. Aceita qualquer iterável de entidades ezdxf (ou objetos com dxftype()/dxf.layer)."""
    rows=collections.OrderedDict()
    for e in entities:
        layer=str(e.dxf.layer);r=rows.setdefault(layer,{'layer':layer,'types':collections.Counter(),'kinds':collections.Counter(),'closed':0,'total':0})
        t=e.dxftype();r['types'][t]+=1;r['total']+=1
        closed=False
        if t in ('LWPOLYLINE','POLYLINE'):
            try:closed=bool(e.closed)
            except (AttributeError,ValueError):closed=False
        if closed:r['closed']+=1;r['kinds']['areal']+=1
        else:r['kinds'][_kind(t)]+=1
    return rows

def _profile_role(layer,rules):
    from .layer_profiles import norm,ROLE_LABELS
    import fnmatch
    n=norm(layer)
    from .layer_profiles import not_operational
    if not_operational(layer):return None,None,0.0
    for rule in rules:
        if rule.get('role') in ROLE_LABELS and fnmatch.fnmatchcase(n,norm(rule.get('pattern',''))):
            exact='*' not in rule['pattern'] and '?' not in rule['pattern']
            return rule['role'],rule['pattern'],(0.95 if exact else 0.8)
    return None,None,0.0

def _compat(role,kinds):
    exp=EXPECTED.get(role)
    if exp is None or exp=='mista':return True
    geo={k:v for k,v in kinds.items() if k in ('linear','areal')}
    if exp=='ponto':return True
    if not geo:return True
    return kinds.get(exp,0)>0

def interpret(entities,settings,profile_rules=None):
    from .layer_profiles import BUILTIN,ROLE_LABELS
    rules=profile_rules if profile_rules is not None else BUILTIN['rules']
    rows=scan(entities)
    mapping={}
    for role,names in (getattr(settings,'layers',None) or {}).items():
        for n in names:mapping.setdefault(n,[]).append(role)
    out=[];alerts=[];by_role=collections.defaultdict(list)
    for layer,r in rows.items():
        geo=r['kinds']['linear']+r['kinds']['areal']
        roles=mapping.get(layer,[])
        if roles:role=roles[0];origin='projeto';conf=1.0;pattern=None
        else:
            role,pattern,conf=_profile_role(layer,rules);origin='perfil' if role else 'nenhum'
        dominant=max(r['kinds'],key=r['kinds'].get) if r['kinds'] else 'outro'
        row={'layer':layer,'role':role,'role_label':ROLE_LABELS.get(role),'origin':origin,'confidence':conf,'pattern':pattern,
             'entities':r['total'],'types':dict(r['types']),'dominant':dominant,'closed_polylines':r['closed'],'geometry':geo>0,'alerts':[]}
        if role:by_role[role].append(layer)
        if role and not _compat(role,r['kinds']):
            row['alerts'].append({'code':'incoerente','text':f'A layer está como "{ROLE_LABELS.get(role,role)}" mas contém {dominant}; esperado {EXPECTED.get(role)}.'})
        if not role and geo>0:
            row['alerts'].append({'code':'sem_papel','text':'Layer com geometria e sem papel: será ignorada no vídeo. Indique o tipo ou confirme que deve ser ignorada.'})
        if len(roles)>1:row['alerts'].append({'code':'papel_duplo','text':'Layer atribuída a mais de um papel: vale o primeiro ('+ROLE_LABELS.get(roles[0],roles[0])+').'})
        if role and origin=='perfil' and conf<0.6:row['alerts'].append({'code':'baixa_confianca','text':'Papel inferido por padrão genérico do perfil; confirme.'})
        out.append(row);alerts.extend({'layer':layer,**a} for a in row['alerts'])
    present={r['layer'] for r in out}
    for n,roles in mapping.items():
        if n not in present:alerts.append({'layer':n,'code':'ausente','text':'A layer está no mapeamento do projeto mas não existe no desenho atual.'})
    final={r['layer']:r['role'] for r in out}
    for need,text in (('axis','Nenhum eixo reconhecido: não há itinerário de tráfego.'),('pavement','Nenhuma hachura de pavimento: o vídeo não apresentará veículos (sem erro).')):
        if not any(v==need or (need=='pavement' and v=='existing_pavement') for v in final.values()):alerts.append({'layer':None,'code':'papel_ausente','text':text})
    summary={'layers':len(out),'with_role':sum(1 for r in out if r['role']),'without_role':sum(1 for r in out if not r['role'] and r['geometry']),
             'annotation_only':sum(1 for r in out if not r['geometry']),'alerts':len(alerts),'roles':{k:v for k,v in sorted(by_role.items())}}
    return {'layers':out,'alerts':alerts,'summary':summary}

def interpret_directory(directory,settings):
    from .geometry import walk
    import ezdxf
    dxf=Path(directory)/'input.dxf'
    if not dxf.exists():return {'layers':[],'alerts':[{'layer':None,'code':'sem_dxf','text':'Não há DXF no projeto.'}],'summary':{'layers':0,'with_role':0,'without_role':0,'annotation_only':0,'alerts':1,'roles':{}}}
    doc=ezdxf.readfile(dxf)
    return interpret(walk(doc.modelspace()),settings)
