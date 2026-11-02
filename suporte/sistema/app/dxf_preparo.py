"""3.1: rotina de preparo do DXF (somente DXF; não abre DWG).

Gera uma CÓPIA do DXF com as mesmas características do modelo que funciona:
  • camadas renomeadas para nomes canônicos pelo papel (eixo, pista projetada/existente, acostamento, bordo, canteiro,
    barreira, OAE, corte/aterro, faixa de domínio, hidrografia); papéis vêm do perfil de camadas (padrão ou salvo);
  • eixos identificados por nome e, na falta, pela geometria (linhas abertas e longas), com os fragmentos unidos (folga 0,05 m);
  • entidades inválidas (coordenada vazia/não finita/gigante, segmento de comprimento zero) e duplicatas exatas removidas.
O original nunca é alterado. Camadas bloqueadas/congeladas/desligadas ficam como estão (fora dos cálculos, salvo seleção).
Nenhum nome de projeto é usado: a regra é geral."""
import math,os,tempfile
from collections import defaultdict
import numpy as np

TOL=0.05                 # m: união de pontas de eixo
LIMITE=1e9               # |coordenada| acima disso é lixo
EIXO_MIN_M=200.          # comprimento mínimo de um eixo inferido pela geometria
EIXO_MAX_ENT=60          # camada com mais entidades que isso não é eixo (é desenho)
CANONICO={'axis':'EIXO','pavement':'HATCH_PAV_NOVO','existing_pavement':'HATCH_PAV_EXISTENTE','shoulder':'GE_HZ-ACOSTAMENTO',
          'edge_line':'GE_HZ-BORDO','median':'CANTEIRO','barrier':'BARREIRA','oae':'OAE','domain':'FAIXA DE DOMINIO','water':'HIDROGRAFIA',
          'terrain':'TERRAPLENO','cut':'GE_HZ-OFFCORTE','fill':'GE_HZ-OFFATERRO'}
CANONICO_HATCH={'cut':'GE_HZ-HCORTE','fill':'GE_HZ-HATERRO'}
SENTIDOS=('LESTE','OESTE','NORTE','SUL','IDA','VOLTA','DIREITO','ESQUERDO')
CURVAS=('LINE','LWPOLYLINE','POLYLINE','ARC','SPLINE')


def _finito(v):
    try:return math.isfinite(float(v)) and abs(float(v))<LIMITE
    except (TypeError,ValueError):return False


def _pontos(e):
    """vértices (x,y) de uma entidade-curva; vazio se não der. Arcos/splines são achatados (0,05 m)."""
    t=e.dxftype()
    try:
        if t=='LINE':pts=[(e.dxf.start.x,e.dxf.start.y),(e.dxf.end.x,e.dxf.end.y)]
        elif t=='LWPOLYLINE':pts=[(p[0],p[1]) for p in e.get_points('xy')]
        elif t=='POLYLINE':pts=[(v.dxf.location.x,v.dxf.location.y) for v in e.vertices if not getattr(v,'is_face_record',False)] if getattr(e,'is_2d_polyline',True) or getattr(e,'is_3d_polyline',False) else []
        else:
            from ezdxf import path as P
            pts=[(v.x,v.y) for v in P.make_path(e).flattening(.05)]
    except Exception:return []
    return [(float(x),float(y)) for x,y in pts if _finito(x) and _finito(y)] if all(_finito(c) for p in pts for c in p) else []


def _fechado(e,pts):
    if e.dxftype()=='LWPOLYLINE':return bool(e.closed)
    if e.dxftype()=='POLYLINE':return bool(e.is_closed)
    return len(pts)>2 and math.dist(pts[0],pts[-1])<1e-6


def _comprimento(pts):
    if len(pts)<2:return 0.
    a=np.asarray(pts,float);d=np.linalg.norm(np.diff(a,axis=0),axis=1);return float(d[np.isfinite(d)].sum())


# Sinônimos (inglês e variações comuns) usados DEPOIS das regras do perfil; só atuam em camadas sem papel.
SINONIMOS=[{'pattern':p,'role':r} for p,r in [
 ('*EXIST*ROAD*','existing_pavement'),('*ROAD*EXIST*','existing_pavement'),('*EXIST*PAVEMENT*','existing_pavement'),('*EXISTING*CARRIAGEWAY*','existing_pavement'),
 ('*NEW*ROAD*','pavement'),('*ROAD*NEW*','pavement'),('*PROPOSED*ROAD*','pavement'),('*PAVEMENT*','pavement'),('*CARRIAGEWAY*','pavement'),('*ASPHALT*','pavement'),('*ASFALTO*','pavement'),
 ('*GUARDRAIL*','barrier'),('*GUARD*RAIL*','barrier'),('*BARRIER*','barrier'),('*JERSEY*','barrier'),
 ('*CENTRE*LINE*','axis'),('*CENTER*LINE*','axis'),('*ALINHAMENTO*','axis'),('*ALIGNMENT*','axis'),('*TRACADO*','axis'),
 ('*ROAD*EDGE*','edge_line'),('*KERB*','edge_line'),('*CURB*','edge_line'),
 ('*RIGHT*OF*WAY*','domain'),('*ROW*','domain'),('*DESAPROPR*','domain'),
 ('*RIVER*','water'),('*STREAM*','water'),('*DRAINAGE*','water'),
]]

def _perfil(nome_perfil,raiz):
    from . import layer_profiles as LP
    if nome_perfil and raiz is not None:
        p=next((x for x in LP.load(raiz) if x['name']==nome_perfil),None)
        if p is not None:return p
    return LP.BUILTIN


def _sufixo_sentido(nome):
    from .layer_profiles import norm
    n=norm(nome)
    for s in SENTIDOS:
        if s in n:return s
    return ''


def _estado(nome):
    from .presentation import is_existing
    return is_existing({'layer':nome})


def analisar(doc,perfil):
    """estatística por camada e papel; sem alterar nada."""
    from .layer_profiles import role_for
    msp=doc.modelspace();por=defaultdict(lambda:{'n':0,'tipos':defaultdict(int),'abertas':0,'fechadas':0,'comp':0.,'invalidas':0,'hatch':0})
    for e in msp:
        L=por[e.dxf.layer];L['n']+=1;t=e.dxftype();L['tipos'][t]+=1
        if t=='HATCH':L['hatch']+=1
        elif t in CURVAS:
            pts=_pontos(e)
            if len(pts)<2:L['invalidas']+=1;continue
            if _fechado(e,pts):L['fechadas']+=1
            else:L['abertas']+=1;L['comp']+=_comprimento(pts)
    info={}
    for nome,L in por.items():
        lay=doc.layers.get(nome) if doc.layers.has_entry(nome) else None
        preso=bool(lay is not None and (lay.is_locked() or lay.is_frozen() or not lay.is_on()))
        info[nome]={**{k:(dict(v) if k=='tipos' else v) for k,v in L.items()},'papel':role_for(nome,perfil['rules']),'preservada':preso}
    return info


def _inferir_eixos(info):
    """sem eixo por nome: camadas sem papel, só de linhas abertas, poucas entidades e longas."""
    cands=[(n,i['comp']) for n,i in info.items() if i['papel'] is None and not i['preservada'] and i['n']<=EIXO_MAX_ENT
           and i['hatch']==0 and i['fechadas']==0 and i['abertas']>0 and i['comp']>=EIXO_MIN_M]
    return [n for n,_ in sorted(cands,key=lambda x:-x[1])[:4]]


def _mapa(info,eixos_inferidos):
    """camada original -> (papel, nome canônico). Várias camadas do mesmo papel/estado/sentido fundem num só nome."""
    mapa={}
    for nome,i in info.items():
        if i['preservada']:continue
        papel='axis' if nome in eixos_inferidos else i['papel']
        if papel not in CANONICO:continue
        base=CANONICO_HATCH.get(papel) if papel in CANONICO_HATCH and i['hatch']>0 and i['hatch']>=i['n']/2 else CANONICO[papel]
        suf=_sufixo_sentido(nome) if papel=='axis' else ''
        if papel=='oae' and _estado(nome):suf='EXISTENTE'
        mapa[nome]=(papel,base+('_'+suf if suf else ''))
    # eixos sem sentido no nome: EIXO_01, EIXO_02… por comprimento
    livres=sorted([n for n,(p,c) in mapa.items() if p=='axis' and c==CANONICO['axis']],key=lambda n:-info[n]['comp'])
    for k,n in enumerate(livres,1):mapa[n]=('axis',f"{CANONICO['axis']}_{k:02d}")
    return mapa


def _unir_eixo(pts_list,tol=TOL):
    """une fragmentos cujas pontas distam ≤ tol (as pontas próximas passam ao ponto médio) e funde em polilinhas contínuas."""
    from shapely.geometry import LineString,MultiLineString
    from shapely.ops import linemerge
    from scipy.spatial import cKDTree
    frag=[np.asarray(p,float) for p in pts_list if len(p)>=2 and _comprimento(p)>1e-6]
    if not frag:return []
    pontas=np.array([f[i] for f in frag for i in (0,-1)]);dono=np.repeat(np.arange(len(frag)),2)
    if len(pontas)>1:
        for i,j in cKDTree(pontas).query_pairs(tol):
            if dono[i]==dono[j]:continue
            mid=(pontas[i]+pontas[j])/2;pontas[i]=pontas[j]=mid
        for k,f in enumerate(frag):f[0]=pontas[2*k];f[-1]=pontas[2*k+1]
    try:m=linemerge([LineString(f) for f in frag if len(f)>=2])
    except Exception:return [[tuple(q) for q in f] for f in frag]
    partes=list(m.geoms) if isinstance(m,MultiLineString) else [m]
    return [[(x,y) for x,y,*_ in p.coords] for p in partes if p.length>1e-6]


def preparar(origem,destino=None,*,perfil=None,raiz=None,aplicar=True):
    """Lê `origem` (DXF) e devolve o relatório. Com aplicar=True e `destino`, grava a cópia preparada (substituição atômica).
    Nunca altera `origem`. Levanta ValueError (mensagem em português) para arquivo vazio ou ilegível."""
    import ezdxf
    from .dxf_leitura import ler as ler_dxf
    _av_leitura=[]
    try:doc=ler_dxf(origem,_av_leitura)
    except ValueError:raise
    except Exception as e:raise ValueError('Não foi possível ler o DXF: '+str(e)[:160])
    msp=doc.modelspace()
    if len(msp)==0:raise ValueError('O DXF está vazio (nenhuma entidade no desenho).')
    prof=_perfil(perfil,raiz);prof={**prof,'rules':list(prof['rules'])+SINONIMOS};info=analisar(doc,prof)
    avisos=list(_av_leitura)
    tem_eixo=any(i['papel']=='axis' and not i['preservada'] for i in info.values())
    inferidos=[] if tem_eixo else _inferir_eixos(info)
    if inferidos:avisos.append('Nenhuma camada de eixo pelo nome; eixo inferido pela geometria em: '+', '.join(inferidos)+'. Confira.')
    if not tem_eixo and not inferidos:avisos.append('Nenhum eixo identificado (nem por nome, nem por geometria). Associe uma camada ao papel Eixo.')
    mapa=_mapa(info,set(inferidos))
    # extensão e unidade
    xs=[];ys=[]
    for e in msp:
        if e.dxftype() in CURVAS:
            for x,y in _pontos(e):xs.append(x);ys.append(y)
    if xs:
        ext=(min(xs),min(ys),max(xs),max(ys))
        if max(ext[2]-ext[0],ext[3]-ext[1])<=1e-9:avisos.append('Extensão do desenho nula: confira o conteúdo e as unidades.')
        elif max(abs(v) for v in ext)<=360 and max(ext[2]-ext[0],ext[3]-ext[1])<5:avisos.append('Coordenadas parecem geográficas (graus). O app espera metros projetados (ex.: UTM).')
    else:ext=None;avisos.append('Nenhuma curva legível no desenho (só hachuras/blocos?).')
    rel={'camadas':[{'origem':n,'papel':(mapa[n][0] if n in mapa else info[n]['papel']),'destino':(mapa[n][1] if n in mapa else n),
                     'entidades':info[n]['n'],'preservada':info[n]['preservada']} for n in sorted(info)],
         'eixos':sorted({c for n,(p,c) in mapa.items() if p=='axis'}),'eixos_inferidos':inferidos,
         'sem_papel':sorted(n for n,i in info.items() if n not in mapa and not i['preservada'] and i['papel'] is None),
         'extensao':ext,'avisos':avisos,'removidas':{'invalidas':0,'duplicadas':0},'eixos_unidos':0,'aplicado':False}
    if not aplicar or destino is None:return rel
    # --- aplica na cópia
    vistos=set();remover=[];por_destino=defaultdict(list)
    for e in list(msp):
        t=e.dxftype();nome=e.dxf.layer
        if t in CURVAS:
            pts=_pontos(e)
            if len(pts)<2 or _comprimento(pts)<=1e-9 and not _fechado(e,pts):
                if info[nome]['preservada']:continue
                remover.append(e);rel['removidas']['invalidas']+=1;continue
            if not info[nome]['preservada'] and t in ('LINE','LWPOLYLINE'):
                chave=(nome,t,tuple(sorted((round(x,3),round(y,3)) for x,y in pts)))
                if chave in vistos:remover.append(e);rel['removidas']['duplicadas']+=1;continue
                vistos.add(chave)
        if nome in mapa and mapa[nome][0]=='axis' and t in CURVAS:
            pts=_pontos(e)
            if len(pts)>=2:por_destino[mapa[nome][1]].append(pts);remover.append(e);continue
    for e in remover:
        try:msp.delete_entity(e)
        except Exception:pass
    for nome,(papel,novo) in mapa.items():
        if novo==nome:continue
        if not doc.layers.has_entry(novo):
            src=doc.layers.get(nome) if doc.layers.has_entry(nome) else None
            doc.layers.add(novo,color=(abs(src.color) if src is not None else 7))
        for e in msp.query(f'*[layer=="{nome}"]') if '"' not in nome else [x for x in msp if x.dxf.layer==nome]:
            e.dxf.layer=novo
    for destino_layer,frag in por_destino.items():
        if not doc.layers.has_entry(destino_layer):doc.layers.add(destino_layer,color=7)
        for pts in _unir_eixo(frag):
            msp.add_lwpolyline(pts,dxfattribs={'layer':destino_layer});rel['eixos_unidos']+=1
    for nome,(papel,novo) in mapa.items():
        if novo!=nome and not any(e.dxf.layer==nome for e in msp):
            try:doc.layers.discard(nome)
            except Exception:pass
    destino=str(destino);tmp=tempfile.NamedTemporaryFile(prefix='.preparo_',suffix='.dxf',dir=os.path.dirname(os.path.abspath(destino)) or '.',delete=False);tmp.close()
    try:doc.saveas(tmp.name);os.replace(tmp.name,destino)
    finally:
        if os.path.exists(tmp.name):os.unlink(tmp.name)
    rel['aplicado']=True;return rel
