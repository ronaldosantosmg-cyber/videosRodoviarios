"""3.1: remoção de linhas fantasma (cordas retas longas) em bordos, sinalização e faixa de domínio.

Uma corda fantasma é um segmento que não existe no desenho real: surge quando duas partes
independentes (ou o fim e o início de um laço aberto) são ligadas em uma única polilinha.
Característica: muito mais longo que os segmentos vizinhos (a pista curva tem vértices densos)
e, para bordo/sinalização, longe de qualquer pavimento/acostamento/eixo. O segmento é removido
e a polilinha é dividida; nada é inventado nem fechado. Entradas inválidas (vazias, NaN, inf)
são preservadas sem erro.
"""
import numpy as np
from shapely.geometry import LineString
from shapely.strtree import STRtree

ROLES_TRACO=('edge_line','domain','sign_h')
ROLES_SUPORTE=('pavement','existing_pavement','shoulder','median','axis','barrier','oae')
MIN_FANTASMA_M=30.      # abaixo disso nunca é considerado corda
RAZAO_VIZINHOS=8.       # comprimento / mediana dos vizinhos
APOIO_M=3.              # distância máxima ao contorno do pavimento para a corda ser considerada apoiada


def _vizinhos(L,i,k=3):
    v=np.r_[L[max(0,i-k):i],L[i+1:i+1+k]];v=v[np.isfinite(v)&(v>1e-6)]
    return float(np.median(v)) if len(v) else 0.


def _dist(suporte,q):
    """Distância de cada ponto de q ao suporte (inf se não há suporte)."""
    if suporte is None:return np.full(len(q),np.inf)
    from shapely import points as _pts
    tree,_=suporte
    try:
        idx,d=tree.query_nearest(_pts(q[:,0],q[:,1]),return_distance=True,all_matches=False)
    except Exception:return np.full(len(q),np.inf)
    out=np.full(len(q),np.inf);out[idx[0]]=d
    return out


def _perto_de_outros(outros,q):
    """Máscara das amostras q a até APOIO_M de OUTRA linha de traço (outro dono): sinalização real corre junto de outras."""
    if outros is None:return np.zeros(len(q),bool)
    tree,owners,eu=outros
    from shapely import points as _pts
    try:
        qi,ti=tree.query(_pts(q[:,0],q[:,1]),predicate='dwithin',distance=APOIO_M)
    except Exception:return np.zeros(len(q),bool)
    m=np.zeros(len(q),bool);ok=np.asarray(owners)[ti]!=eu;m[qi[ok]]=True;return m


def segmentos_fantasma(points,suporte=None,razao=RAZAO_VIZINHOS,minimo=MIN_FANTASMA_M,modo='bordo',outros=None):
    """Índices dos segmentos fantasma de uma polilinha.

    modo 'bordo' (bordo/sinalização): corda longa, muito maior que os vizinhos e fora do contorno do pavimento.
    modo 'dominio': corda longa cujo afastamento ao eixo não acompanha as pontas (a faixa de domínio é paralela à via).
    """
    try:P=np.asarray(points,float)
    except (TypeError,ValueError):return []
    if P.ndim!=2 or P.shape[1]!=2 or len(P)<3 or not np.isfinite(P).all():return []
    L=np.linalg.norm(np.diff(P,axis=0),axis=1);out=[]
    for i,l in enumerate(L):
        if l<minimo:continue
        ref=_vizinhos(L,i)
        if not (ref>0 and l>=razao*ref):continue
        n=max(5,int(l//5)+1);t=np.linspace(0,1,n);q=P[i]+(P[i+1]-P[i])*t[:,None]
        d=_dist(suporte,q)
        if modo=='bordo':
            apoiado=float(np.mean((d<=APOIO_M)|_perto_de_outros(outros,q)))   # 3.3: dispositivos longe do eixo (rotatórias, alças)
            if apoiado<.5:out.append(i)
        else:
            ref_d=float(np.mean([d[0],d[-1]])) if np.isfinite(d[[0,-1]]).all() else np.inf
            if np.isfinite(ref_d) and float(np.max(np.abs(d-ref_d)))>max(12.,.35*ref_d):out.append(i)
    return out


def _dividir(points,cortes):
    P=np.asarray(points,float);cortes=set(cortes);partes=[];ini=0
    for i in range(len(P)-1):
        if i in cortes:
            if i+1-ini>=2:partes.append(P[ini:i+1])
            ini=i+1
    if len(P)-ini>=2:partes.append(P[ini:])
    return partes


def _suporte(entities,roles):
    geoms=[]
    for e in entities:
        if e.get('role') not in roles:continue
        # 3.3: contorno E área. Sinalização legítima (eixo, divisor de faixas, zebrado) fica DENTRO do pavimento, longe do
        # contorno; só o contorno a classificaria como "sem base" e cortaria a linha real. Dentro da área a distância é 0.
        try:
            p=np.asarray(e.get('points'),float)
            if e.get('closed') and p.ndim==2 and p.shape[1]==2 and len(p)>=3 and np.isfinite(p).all():
                from shapely.geometry import Polygon
                holes=[np.asarray(h,float) for h in (e.get('holes') or []) if len(h)>=3]
                poly=Polygon(p,holes)
                if not poly.is_valid:poly=poly.buffer(0)
                if not poly.is_empty:geoms.append(poly)
        except (TypeError,ValueError,Exception):pass
        for ring in [e.get('points')]+list(e.get('holes') or []):
            try:
                p=np.asarray(ring,float)
                if p.ndim==2 and p.shape[1]==2 and len(p)>=2 and np.isfinite(p).all():geoms.append(LineString(p))
            except (TypeError,ValueError):continue
    return (STRtree(geoms),geoms) if geoms else None


def limpar(entities,warnings=None):
    """Remove cordas fantasma de bordo/sinalização/domínio; devolve (entidades, quantidade removida)."""
    sup_bordo=_suporte(entities,ROLES_SUPORTE);sup_eixo=_suporte(entities,('axis',));resultado=[];removidos=0;extensao=0.
    geoms,owners=[],[]
    for k,e in enumerate(entities):
        if e.get('role') in ('edge_line','sign_h'):
            try:
                p=np.asarray(e.get('points'),float)
                if p.ndim==2 and p.shape[1]==2 and len(p)>=2 and np.isfinite(p).all():geoms.append(LineString(p));owners.append(k)
            except (TypeError,ValueError):pass
    arvore=STRtree(geoms) if geoms else None
    for k,e in enumerate(entities):
        if e.get('role') not in ROLES_TRACO or e.get('closed') and not e.get('source_hatch_stroke'):resultado.append(e);continue
        dom=e['role']=='domain'
        cortes=segmentos_fantasma(e.get('points'),sup_eixo if dom else sup_bordo,modo='dominio' if dom else 'bordo',outros=(arvore,owners,k) if arvore is not None else None)
        if not cortes:resultado.append(e);continue
        P=np.asarray(e['points'],float)
        extensao+=float(sum(np.linalg.norm(P[i+1]-P[i]) for i in cortes));removidos+=len(cortes)
        for parte in _dividir(P,cortes):resultado.append({**e,'points':parte,'closed':False,'fantasma_cortado':True})
    if removidos and warnings is not None:
        warnings.append(f'Linhas fantasma removidas: {removidos} corda(s) reta(s) sem base no desenho ({extensao:.0f} m) em bordo, sinalização ou faixa de domínio.')
    return resultado,removidos
