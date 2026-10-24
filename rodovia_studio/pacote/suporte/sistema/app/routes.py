"""1.30: faixas de veículos geradas a partir dos alinhamentos de rota (route_alignments).

Cada alinhamento tem um tipo padrão e trechos (início/fim em metros ao longo do alinhamento) com tipo próprio:
  simples — um sentido de cada lado do alinhamento (mão de direção: o sentido do desenho fica à direita);
  dupla   — pista dupla, N faixas por sentido, com canteiro central (median_m);
  unico   — sentido único, N faixas centradas no alinhamento, no sentido em que ele foi desenhado.
Entre trechos de tipos diferentes as faixas fazem transição linear (taper_m). Uma faixa que deixa de existir
converge para a faixa mais externa que continua (e uma que surge diverge dela), de modo que as pontas caem
sobre a faixa vizinha e a rede de tráfego as liga (split_contacts).
"""
import numpy as np

STEP=1.0

def _resample(P,step=STEP):
    P=np.asarray(P,float);d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))]
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
    n=len(s);typ=np.array([g(route,'type','simples')]*n,dtype=object);lanes=np.full(n,int(g(route,'lanes',1)));med=np.full(n,float(g(route,'median_m',0)))
    for sec in g(route,'sections',[]) or []:
        a,b=sorted((float(g(sec,'start_m',0)),float(g(sec,'end_m',0))))
        m=(s>=a)&(s<=b)
        typ[m]=g(sec,'type','dupla');lanes[m]=int(g(sec,'lanes',1));med[m]=float(g(sec,'median_m',0))
    return typ,lanes,med

def lane_offsets(typ,lanes,med,width):
    """Para cada estação: {('f'|'r',k): deslocamento} das faixas existentes. f = sentido do desenho."""
    out=[]
    for t,n,m in zip(typ,lanes,med):
        o={}
        if t=='unico':
            for k in range(n):o[('f',k)]=width*(k-(n-1)/2)
        else:
            half=(m/2 if t=='dupla' else 0.)
            for k in range(n):o[('f',k)]=half+width*(k+.5);o[('r',k)]=-(half+width*(k+.5))
        out.append(o)
    return out

def _runs(mask):
    ch=np.diff(np.r_[0,mask.astype(np.int8),0]);return list(zip(np.flatnonzero(ch==1),np.flatnonzero(ch==-1)))

def build_lanes(route):
    """Faixas do alinhamento: lista de dicts {points (no sentido de tráfego), dir 'f'|'r', lane k, length}."""
    g=lambda k,d:(route.get(k,d) if isinstance(route,dict) else getattr(route,k,d))
    pts=[(p['x'],p['y']) if isinstance(p,dict) else (p.x,p.y) for p in g('points',[])]
    if len(pts)<2:return []
    Q,s=_resample(pts)
    if Q is None or s[-1]<4:return []
    nrm=_normals(Q);width=float(g('lane_width_m',3.5));T=max(STEP*2,float(g('taper_m',40)))
    typ,lanes,med=section_at(route,s);offs=lane_offsets(typ,lanes,med,width)
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
                    if n>0:pre=[(j,tg+(o[0]-tg)*i/n) for i,j in enumerate(range(j0,a))]
            if b<len(s):
                tg=target(b)
                if tg is not None:
                    j1=min(len(s),b+W);n=j1-b
                    if n>0:post=[(j,o[-1]+(tg-o[-1])*(i+1)/n) for i,j in enumerate(range(b,j1))]
            J=np.r_[[j for j,_ in pre],idx,[j for j,_ in post]].astype(int)
            O=np.r_[[v for _,v in pre],o,[v for _,v in post]]
            P=Q[J]+nrm[J]*O[:,None]
            if len(P)<3:continue
            L=float(np.sum(np.linalg.norm(np.diff(P,axis=0),axis=1)))
            if L<4:continue
            if d=='r':P=P[::-1]
            result.append({'points':P,'dir':d,'lane':k,'length':L,'start_m':float(s[J[0]]),'end_m':float(s[J[-1]])})
    return result

def raw_paths(settings):
    """Entradas “raw” para a rede de tráfego (TrafficNetwork) a partir dos alinhamentos de rota ativos."""
    out=[]
    for r in getattr(settings,'route_alignments',[]) or []:
        if not getattr(r,'enabled',True):continue
        pts=np.array([[p.x,p.y] for p in r.points],dtype=float)
        route_len=float(np.sum(np.linalg.norm(np.diff(pts,axis=0),axis=1))) if len(pts)>1 else 0.0
        if not np.isfinite(route_len) or route_len < float(getattr(settings,'min_route_segment_m',50)):continue
        for ln in build_lanes(r):
            out.append({'points':ln['points'],'halfwidth':float(r.lane_width_m)/2,'source':f"{r.name} · {'sentido do desenho' if ln['dir']=='f' else 'sentido oposto'} · faixa {ln['lane']+1}",
                        'level':int(r.level),'kind':'main','manual':True,'fixed':True,'nopaint':True,'free':bool(r.outside_pavement),'speed_kmh':r.speed_kmh,
                        'route':r.id or r.name,'route_name':r.name,'route_dir':ln['dir'],'route_lane':int(ln['lane']),
                        'route_start_m':float(ln['start_m']),'route_end_m':float(ln['end_m']),
                        'lane_change':getattr(r,'lane_change','marked'),
                        'lane_change_sections':[x.model_dump() if hasattr(x,'model_dump') else dict(x) for x in (getattr(r,'lane_change_sections',[]) or [])]})
    return out

def preview(settings):
    """Polilinhas das faixas para o editor (mesmo cálculo da rede)."""
    out=[]
    for i,r in enumerate(getattr(settings,'route_alignments',[]) or []):
        for ln in build_lanes(r):
            out.append({'route':i,'id':r.id,'dir':ln['dir'],'lane':ln['lane'],'enabled':bool(r.enabled),'points':np.round(ln['points'],3).tolist(),'start_m':ln['start_m'],'end_m':ln['end_m']})
    return out
