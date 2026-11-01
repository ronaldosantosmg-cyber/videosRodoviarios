"""1.30: faixas de veículos geradas a partir dos alinhamentos de rota (route_alignments).

Cada alinhamento tem um tipo padrão e trechos (início/fim em metros ao longo do alinhamento) com tipo próprio:
  simples — um sentido de cada lado do alinhamento (mão de direção: o sentido do desenho fica à direita);
  dupla   — pista dupla, N faixas por sentido, com canteiro central (median_m);
  unico   — sentido único, N faixas centradas no alinhamento, no sentido em que ele foi desenhado.
Entre trechos de tipos diferentes as faixas fazem transição linear (taper_m). Uma faixa que deixa de existir
converge para a faixa mais externa que continua (e uma que surge diverge dela), de modo que as pontas caem
sobre a faixa vizinha e a rede de tráfego as liga (split_contacts).
"""
from .seguro import sdiv as _sdiv
import numpy as np

STEP=1.0

def _resample(P,step=STEP):
    P=np.asarray(P,float);d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))]
    if not np.isfinite(d).all() or d[-1]>100000:raise ValueError('Divida alinhamentos acima de 100 km antes de gerar faixas.')
    keep=np.r_[True,np.diff(d)>1e-9];P,d=P[keep],d[keep]
    if len(P)<2 or d[-1]<1e-6:return None,None
    s=np.arange(0,d[-1],step);s=np.r_[s,d[-1]] if d[-1]-s[-1]>1e-6 else s
    Q=np.column_stack([np.interp(s,d,P[:,0]),np.interp(s,d,P[:,1])]);return Q,s

def _normals(Q):
    t=np.gradient(Q,axis=0);t/=np.maximum(np.linalg.norm(t,axis=1),1e-9)[:,None]
    return np.column_stack([t[:,1],-t[:,0]])   # à direita do sentido do desenho

def section_at(route,s):
    """Tipo, faixas e canteiro válidos em cada estação s (trechos posteriores na lista prevalecem)."""
    g=lambda o,k,d:(o.get(k,d) if isinstance(o,dict) else getattr(o,k,d))
    n=len(s);typ=np.array([g(route,'type','simples')]*n,dtype=object);lanes=np.full(n,int(g(route,'lanes',1)));med=np.full(n,float(g(route,'median_m',0)));ref=np.array([g(route,'axis_ref','centro')]*n,dtype=object)
    for sec in g(route,'sections',[]) or []:
        a,b=sorted((float(g(sec,'start_m',0)),float(g(sec,'end_m',0))))
        m=(s>=a)&(s<=b)
        typ[m]=g(sec,'type','dupla');lanes[m]=int(g(sec,'lanes',1));med[m]=float(g(sec,'median_m',0));ref[m]=g(sec,'axis_ref','centro')
    return typ,lanes,med,ref

def lane_offsets(typ,lanes,med,width,ref=None):
    """Para cada estação: {('f'|'r',k): deslocamento} das faixas existentes. f = sentido do desenho.
    2.19: no sentido único o eixo pode ficar no MEIO da pista (centro, sem canteiro) ou num bordo
    (bordo_esquerdo: faixas à direita do eixo; bordo_direito: à esquerda). k=0 é a faixa mais à esquerda da marcha."""
    out=[];ref=ref if ref is not None else ['centro']*len(typ)
    for t,n,m,rf in zip(typ,lanes,med,ref):
        o={}
        if t=='unico':
            for k in range(n):o[('f',k)]=width*(k+.5) if rf=='bordo_esquerdo' else (-width*(n-k-.5) if rf=='bordo_direito' else width*(k-(n-1)/2))
        else:
            half=(m/2 if t=='dupla' else 0.)
            for k in range(n):o[('f',k)]=half+width*(k+.5);o[('r',k)]=-(half+width*(k+.5))
        out.append(o)
    return out

def _runs(mask):
    ch=np.diff(np.r_[0,mask.astype(np.int8),0]);return list(zip(np.flatnonzero(ch==1),np.flatnonzero(ch==-1)))

import contextlib,contextvars
_KM_CHAIN=contextvars.ContextVar('km_chain',default=None)   # ponto -> estaca no EIXO PRINCIPAL (já com “inverter eixo”), fornecida pela rede de tráfego
_KM_SIGNS=contextvars.ContextVar('km_signs',default=None)   # {id da rota: +1/-1} calculado pela tela (prévia), que não tem a rede
@contextlib.contextmanager
def km_context(chain=None,signs=None):
    a=_KM_CHAIN.set(chain);b=_KM_SIGNS.set(signs)
    try:yield
    finally:_KM_CHAIN.reset(a);_KM_SIGNS.reset(b)
class _KmChain:
    """Estaca (m) do eixo principal para um ponto. Classe (e não lambda) para a cena poder ser gravada com pickle (snapshot do vídeo)."""
    def __init__(self,st,tree,sign):self.st=st;self.tree=tree;self.sign=sign
    def __call__(self,p):return self.sign*self.st[self.tree.query(np.asarray(p,float))[1]]
def make_chain(axis,ds,km_dir=1):
    """Estaca (m) do eixo principal para um ponto: mesma referência de TrafficNetwork.chain (vale também depois de “inverter eixo”)."""
    from scipy.spatial import cKDTree
    st=np.arange(0,float(ds[-1])+1,2.);dense=np.column_stack([np.interp(st,ds,np.asarray(axis)[:,k]) for k in range(2)])
    return _KmChain(st,cKDTree(dense),1 if km_dir>=0 else -1)
def km_sign(route):
    """+1 se o km CRESCE no sentido dos pontos da rota; -1 se decresce. É a ponte entre “Crescente (km)” e a ordem do desenho.
    Eixos nativos já usam o km (delta de estaca); sem esta ponte as seções usavam a ordem do desenho e ignoravam o estaqueamento/“inverter eixo”."""
    signs=_KM_SIGNS.get()
    key=getattr(route,'id','') or getattr(route,'name','')
    if signs and key in signs:return 1 if signs[key]>=0 else -1
    return km_info(route)[0]
KM_AMBIGUO=.45   # |Δestaca| < 45% do comprimento: ramo/laço/perpendicular ao eixo principal; o km não define um sentido (mesmo limiar de “retorno” em traffic.py)
def km_ambiguo(delta,length):
    return length>0 and abs(delta)<KM_AMBIGUO*length
def km_info(route):
    """(sinal, ambíguo). Ambíguo = a rota não corre paralela ao eixo principal; vale então a ordem do desenho (sinal +1) e a tela avisa."""
    signs=_KM_SIGNS.get()
    key=getattr(route,'id','') or getattr(route,'name','')
    if signs and key in signs:return (1 if signs[key]>=0 else -1),False
    chain=_KM_CHAIN.get();pts=getattr(route,'points',None) or []
    if chain is None or len(pts)<2:return 1,False
    try:
        a=float(chain((pts[0].x,pts[0].y)));b=float(chain((pts[-1].x,pts[-1].y)))
        xy=np.array([(q.x,q.y) for q in pts],float);L=float(np.sum(np.linalg.norm(np.diff(xy,axis=0),axis=1)))
    except (AttributeError,TypeError,ValueError):return 1,False
    if not np.isfinite(a) or not np.isfinite(b):return 1,False
    if km_ambiguo(b-a,L):return 1,True
    return (1 if b-a>=0 else -1),False

def inherited_sense(route,settings):
    """2.21: o sentido Crescente/Decrescente do EIXO vale para a seção cadastrada sobre ele, quando a rota não tem sentido/nós próprios.
    2.39: Crescente = km crescente (e não a ordem do desenho), igual aos eixos nativos; vale para qualquer “inverter eixo”."""
    if settings is None or not getattr(route,'source_axis_fingerprint',''):return 0
    if route.flow_direction!='automatico' or route.flow_start!='automatico' or route.flow_end!='automatico':return 0
    from .native_axes import direction_for
    v=direction_for(getattr(settings,'route_directions',None),'axis:'+route.source_axis_fingerprint,getattr(route,'source_axis_layer',''))   # 2.28: eixo, senão layer
    if v not in ('forward','reverse'):return 0
    k=km_sign(route)
    return k if v=='forward' else -k

def _build_lanes(route,settings=None):
    """Faixas do alinhamento: lista de dicts {points (no sentido de tráfego), dir 'f'|'r', lane k, length}."""
    if isinstance(route,dict):
        from .models import RouteAlignment
        route=RouteAlignment.model_validate(route)
    g=lambda k,d:getattr(route,k,d)
    pts=[(p['x'],p['y']) if isinstance(p,dict) else (p.x,p.y) for p in g('points',[])]
    if len(pts)<2:return []
    Q,s=_resample(pts)
    if Q is None or s[-1]<4:return []
    nrm=_normals(Q);width=float(g('lane_width_m',3.5));T=max(STEP*2,float(g('taper_m',40)))
    if g('cross_sections',[]):
        from .transicao_secoes import required_taper
        from .models import RouteAlignment as _RA
        T=max(T,required_taper(_RA.model_validate(route) if isinstance(route,dict) else route))   # 2.55: transição mínima entre seções vizinhas
    typ,lanes,med,ref=section_at(route,s);offs=lane_offsets(typ,lanes,med,width,ref)
    if g('cross_sections',[]):
        from .road_sections import section_offsets
        from .models import RouteAlignment
        offs=section_offsets(RouteAlignment.model_validate(route) if isinstance(route,dict) else route,s,[{} for _ in s] if g('sections_only',False) else offs)
    from .flow_nodes import orient_offsets
    offs=orient_offsets(route,offs,inherited_sense(route,settings))
    if settings is not None:
        from .road_sections import alternating_offsets
        offs=alternating_offsets(route,settings,s,offs)
    keys=sorted({k for o in offs for k in o})
    W=max(1,int(round(T/STEP)))
    result=[]
    for key in keys:
        exist=np.array([key in o for o in offs])
        off=np.array([o.get(key,np.nan) for o in offs],float)
        for a,b in _runs(exist):
            seg=off[a:b].copy()
            # Transição suave dentro do trecho em que a faixa existe (média móvel = rampa linear de comprimento T).
            if len(seg)>2 and np.ptp(seg)>1e-6:
                pad=np.r_[np.full(W,seg[0]),seg,np.full(W,seg[-1])];ker=np.ones(W)/W
                sm=np.convolve(pad,ker,mode='same')[W:W+len(seg)]
                # As pontas continuam no valor do trecho (não “puxa” para fora antes do começo).
                seg=sm
            idx=np.arange(a,b);o=seg
            # Faixa que termina/começa no meio do alinhamento: converge para a faixa mais externa que continua.
            d,k=key
            def target(j):
                cand=[kk for kk in offs[j] if kk[0]==d]
                if not cand:return None
                return offs[j][max(cand,key=lambda c:c[1])]
            pre=[];post=[]
            if a>0:
                tg=target(a-1)
                if tg is not None:
                    j0=max(0,a-W);n=a-j0
                    if n>0:pre=[(j,tg+(_sdiv((o[0]-tg)*i, n))) for i,j in enumerate(range(j0,a))]
            if b<len(s):
                tg=target(b)
                if tg is not None:
                    j1=min(len(s),b+W);n=j1-b
                    if n>0:post=[(j,o[-1]+(_sdiv((tg-o[-1])*(i+1), n))) for i,j in enumerate(range(b,j1))]
            J=np.r_[[j for j,_ in pre],idx,[j for j,_ in post]].astype(int)
            O=np.r_[[v for _,v in pre],o,[v for _,v in post]]
            P=Q[J]+nrm[J]*O[:,None]
            if len(P)<3:continue
            L=float(np.sum(np.linalg.norm(np.diff(P,axis=0),axis=1)))
            if L<4:continue
            if d=='r':P=P[::-1]
            widths=[];coverage=0.
            for section in g('cross_sections',[]):
                if section.end_m<s[J[0]] or section.start_m>s[J[-1]]:continue
                from .road_sections import section_lane_widths
                lw=section_lane_widths(section);same=[(kk[1],v) for kk,v in lw.items() if kk[0]==d]
                coverage+=max(0.,min(section.end_m,s[J[-1]])-max(section.start_m,s[J[0]]))
                if (d,k) in lw:widths.append(lw[(d,k)])
                elif same:widths.append(max(same)[1])
            if coverage<float(s[J[-1]]-s[J[0]])-.01 or not widths:widths.append(width)
            result.append({'points':P,'dir':d,'lane':k,'length':L,'start_m':float(s[J[0]]),'end_m':float(s[J[-1]]),'lane_width_m':min(widths)})
    return result

def build_lanes(route,settings=None,lane_cache=None):
    from .models import RouteAlignment
    route=RouteAlignment.model_validate(route) if isinstance(route,dict) else route
    return lane_cache.get(route,settings,lambda:_build_lanes(route,settings)) if lane_cache else _build_lanes(route,settings)

LANE_CHANGE_CAP={'acesso':'off','retorno':'off','dispositivo':'off','pista_simples':'marked'}
_RANK={'off':0,'marked':1,'safe':2}


def cap_lane_change(mode,axis_type):
    """A tipologia do eixo só RESTRINGE: acesso/retorno/dispositivo não admitem ultrapassagem; pista simples só em trechos 'allow'."""
    cap=LANE_CHANGE_CAP.get(axis_type)
    return mode if cap is None or _RANK.get(mode,1)<=_RANK[cap] else cap


def raw_paths(settings,lane_cache=None):
    """Entradas “raw” para a rede de tráfego (TrafficNetwork) a partir dos alinhamentos de rota ativos."""
    from .flow_nodes import direction
    out=[]
    for r in getattr(settings,'route_alignments',[]) or []:
        if not getattr(r,'enabled',True):continue
        pts=np.array([[p.x,p.y] for p in r.points],dtype=float)
        route_len=float(np.sum(np.linalg.norm(np.diff(pts,axis=0),axis=1))) if len(pts)>1 else 0.0
        if not np.isfinite(route_len) or route_len < float(getattr(settings,'min_route_segment_m',50)):continue
        axis_type=(getattr(settings,'axis_types',{}) or {}).get('axis:'+r.source_axis_fingerprint,'auto') if r.source_axis_fingerprint else 'auto'
        legacy=[]
        if r.flow_role!='automatico' or r.flow_start!='automatico' or r.flow_end!='automatico' or r.flow_direction!='automatico':
            old=r.model_copy(update=dict(flow_role='automatico',flow_start='automatico',flow_end='automatico',flow_direction='automatico',roundabout_rotation='cadastro',external_demand_vph=None,external_vdm=None))
            legacy=build_lanes(old,settings)
        for ln in build_lanes(r,settings,lane_cache):
            if ln['length']<float(getattr(settings,'min_route_segment_m',50)):continue
            out.append({'points':ln['points'],'legacy_identity_points':[v['points'] for v in legacy if v['lane']==ln['lane'] and (v['dir']==ln['dir'] or r.type=='unico')],'halfwidth':float(r.lane_width_m)/2,'source':f"{r.name} · {'sentido do desenho' if ln['dir']=='f' else 'sentido oposto'} · faixa {ln['lane']+1}",
                        'node_oriented':bool(direction(r) or inherited_sense(r,settings)),'flow_role':r.flow_role,'flow_start':r.flow_start,'flow_end':r.flow_end,'external_demand_vph':r.external_demand_vph,'external_vdm':r.external_vdm,
                        'level':int(r.level),'kind':{'acesso':'access','retorno':'return','dispositivo':'device','rotatoria':'device'}.get(r.flow_role,'main'),'manual':True,'fixed':True,'nopaint':True,'free':bool(r.outside_pavement),'speed_kmh':r.speed_kmh,
                        'route':r.id or r.name,'route_name':r.name,'route_dir':ln['dir'],'route_lane':int(ln['lane']),'route_lane_width_m':ln['lane_width_m'],
                        'route_start_m':float(ln['start_m']),'route_end_m':float(ln['end_m']),
                        'lane_change':cap_lane_change(getattr(r,'lane_change','marked'),axis_type),'axis_type':axis_type,
                        'lane_change_sections':[x.model_dump() if hasattr(x,'model_dump') else dict(x) for x in (getattr(r,'lane_change_sections',[]) or [])]})
    return out

def preview(settings):
    """Polilinhas das faixas para o editor (mesmo cálculo da rede)."""
    out=[]
    for i,r in enumerate(getattr(settings,'route_alignments',[]) or []):
        for ln in build_lanes(r,settings):
            if ln['length']<float(getattr(settings,'min_route_segment_m',50)):continue
            out.append({'route':i,'id':r.id,'dir':ln['dir'],'lane':ln['lane'],'enabled':bool(r.enabled),'points':np.round(ln['points'],3).tolist(),'start_m':ln['start_m'],'end_m':ln['end_m']})
    return out


def section_corridors(settings,lane_cache=None):
    """Geometria operacional explicitamente declarada; nunca inclui acostamentos.

    Aceita a seção como fonte de pista quando a hachura DXF é incompleta. As
    barreiras físicas são subtraídas posteriormente pelo mesmo motor comum.
    """
    from shapely.geometry import LineString
    result=[]
    from .road_sections import authorized_intervals
    for route in getattr(settings,'route_alignments',[]):
        if not route.enabled or not route.cross_sections:continue
        iv=authorized_intervals(route)
        if not iv:continue
        for lane in build_lanes(route,settings,lane_cache):
            if lane['length']<settings.min_route_segment_m:continue
            p=lane['points'];n=len(p)
            # estaca aproximada de cada ponto da faixa (reamostragem uniforme): recorta só os intervalos autorizados
            st=lane['start_m']+(lane['end_m']-lane['start_m'])*(np.arange(n)/max(n-1,1))
            if lane['dir']=='r':st=st[::-1]
            for a0,b0 in iv:
                tap=float(getattr(route,'taper_m',0) or 0)
                # a transição só avança além do intervalo onde NÃO há outra seção (início/fim do alinhamento ou lacuna): nunca para dentro de seção vizinha sem autorização
                lo=0. if any(x.start_m<a0-1e-6<=x.end_m+1e-6 for x in route.cross_sections) else tap
                hi=0. if any(x.start_m-1e-6<=b0<x.end_m-1e-6 and x.end_m>b0+1e-6 for x in route.cross_sections) else tap
                m=(st>=a0-lo)&(st<=b0+hi)
                if m.sum()<2:continue
                idx=np.flatnonzero(m);runs=np.split(idx,np.flatnonzero(np.diff(idx)>1)+1)
                for run in runs:
                    q=p[run]
                    if len(q)<2:continue
                    a=q[1]-q[0];b=q[-1]-q[-2]
                    a=a/max(np.linalg.norm(a),1e-9);b=b/max(np.linalg.norm(b),1e-9)
                    # extremidade interna de um intervalo parcial não é estendida (não vaza para o trecho vizinho sem autorização)
                    
                    ext=np.vstack([q[0]-a*(12 if run[0]==0 else 0),q,q[-1]+b*(12 if run[-1]==n-1 else 0)])
                    result.append(LineString(ext).buffer(lane['lane_width_m']/2,cap_style='flat',join_style='round'))
    return result


def confirmed_corridors(settings,lane_cache=None):
    """Autorização por alinhamento, sem usar largura do acostamento como pista."""
    from shapely.geometry import LineString
    out=[]
    for route in settings.route_alignments:
        if not route.enabled or not route.outside_pavement:continue
        for lane in build_lanes(route,settings,lane_cache):
            if lane['length']<settings.min_route_segment_m:continue
            p=lane['points'];a=p[1]-p[0];b=p[-1]-p[-2]
            a/=max(float(np.linalg.norm(a)),1e-9);b/=max(float(np.linalg.norm(b)),1e-9)
            out.append(LineString(np.vstack([p[0]-a*16,p,p[-1]+b*16])).buffer(lane['lane_width_m']/2,cap_style=2))
    return out
