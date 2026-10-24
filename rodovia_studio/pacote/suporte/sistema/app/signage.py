"""1.15: sinalização horizontal e vertical completa.

* Divisórias de faixa pela largura real da pista (raios perpendiculares até o bordo do pavimento),
  com o número de faixas calculado (largura / largura da faixa) ou informado por trecho.
* Zebrados nos gores (áreas de pavimento entre ramos que divergem/convergem) e áreas zebradas manuais.
* Setas de faixa preenchidas (reta, à direita, à esquerda e combinadas) escolhidas pelo itinerário.
* Linhas de retenção com legenda PARE nas entradas em nível e linha de "dê a preferência" nas rotatórias.
* Faixas de pedestre (dois pontos) e placas verticais (biblioteca básica), automáticas e manuais.
Tudo é calculado sobre a geometria do projeto; o DXF original não é alterado.
"""
import math
import numpy as np
import cv2
from scipy.spatial import cKDTree
from scipy.ndimage import median_filter
from shapely.geometry import Polygon,LineString,Point,MultiPolygon
from shapely.ops import unary_union
from shapely import contains_xy

WHITE=(244,242,226);YELLOW=(244,200,70)
SIGN_CODES={'R-1':'PARE','R-2':'Dê a preferência','R-19':'Velocidade máxima','A':'Advertência','OBRAS':'Obras',
            'I':'Indicação','S':'Serviço'}

def geoms(g):
    if g is None or g.is_empty:return []
    return [x for x in (list(g.geoms) if hasattr(g,'geoms') else [g]) if x.geom_type=='Polygon' and not x.is_empty]

def tangent(p):
    t=np.gradient(np.asarray(p,float),axis=0) if len(p)>1 else np.array([[1.,0.]])
    return t/np.maximum(np.linalg.norm(t,axis=1)[:,None],1e-9)

def resample(p,step):
    p=np.asarray(p,float);d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    if len(p)<2 or d[-1]<1e-6:return p,np.zeros(len(p))
    s=np.linspace(0,d[-1],max(2,int(d[-1]/step)+1))
    return np.column_stack([np.interp(s,d,p[:,0]),np.interp(s,d,p[:,1])]),s

class Extents:
    """Distâncias de um ponto até a borda do pavimento ao longo da normal (esquerda e direita)."""
    def __init__(self,geom,maxseg=3.):
        A=[];B=[]
        for poly in geoms(geom):
            for ring in [poly.exterior]+list(poly.interiors):
                c=np.asarray(ring.coords)
                for a,b in zip(c[:-1],c[1:]):
                    L=float(np.linalg.norm(b-a))
                    if L<1e-9:continue
                    k=max(1,int(math.ceil(L/maxseg)))
                    for j in range(k):A.append(a+(b-a)*j/k);B.append(a+(b-a)*(j+1)/k)
        self.A=np.array(A).reshape(-1,2);self.B=np.array(B).reshape(-1,2)
        self.tree=cKDTree((self.A+self.B)/2) if len(self.A) else None
    def query(self,p,n,R=25.):
        p=np.asarray(p,float);n=np.asarray(n,float);N=len(p)
        dl=np.full(N,np.inf);dr=np.full(N,np.inf)
        if self.tree is None or N==0:return dl,dr
        lists=self.tree.query_ball_point(p,R+2.)
        ii=np.repeat(np.arange(N),[len(v) for v in lists]);jj=np.fromiter((j for v in lists for j in v),int,count=len(ii))
        if not len(ii):return dl,dr
        A=self.A[jj];D=self.B[jj]-A;P=p[ii];V=n[ii];W=A-P
        den=V[:,0]*D[:,1]-V[:,1]*D[:,0];ok=np.abs(den)>1e-12;den=np.where(ok,den,1.)
        s=(W[:,0]*D[:,1]-W[:,1]*D[:,0])/den;u=(W[:,0]*V[:,1]-W[:,1]*V[:,0])/den
        ok&=(u>=-1e-9)&(u<=1+1e-9)&(np.abs(s)<=R)
        pos=ok&(s>0);neg=ok&(s<0)
        np.minimum.at(dr,ii[pos],s[pos]);np.minimum.at(dl,ii[neg],-s[neg])
        return dl,dr

def _fill(a,valid):
    """Preenche amostras inválidas com a válida mais próxima (sem divisão por vazio)."""
    a=np.asarray(a,float).copy()
    if not valid.any():return a
    idx=np.flatnonzero(valid);near=idx[np.clip(np.searchsorted(idx,np.arange(len(a))),0,len(idx)-1)]
    prev=idx[np.clip(np.searchsorted(idx,np.arange(len(a)))-1,0,len(idx)-1)]
    pick=np.where(np.abs(prev-np.arange(len(a)))<np.abs(near-np.arange(len(a))),prev,near)
    a[~valid]=a[pick[~valid]];return a

def _mode_filter(v,size):
    if len(v)==0:return v
    out=v.copy();h=size//2
    for i in range(len(v)):
        w=v[max(0,i-h):i+h+1];w=w[w>0]
        if len(w):vals,c=np.unique(w,return_counts=True);out[i]=vals[np.argmax(c)]
    return out

def layout(p,ext,inside,lane_w,both,zones=(),step=3.,count=0,fwd=True):
    """Seções transversais ao longo da trajetória: bordos, largura e número de faixas POR SENTIDO.
    count>0: número fixo por sentido (1.18; o que sobrar da largura é acostamento); 0: pela largura."""
    q,_=resample(p,step)
    if len(q)<3:return None
    t=tangent(q);n=np.column_stack([t[:,1],-t[:,0]])
    dl,dr=ext.query(q,n);valid=inside(q)&np.isfinite(dl)&np.isfinite(dr)
    if valid.sum()<2:return None
    dl=median_filter(_fill(dl,valid),5,mode='nearest');dr=median_filter(_fill(dr,valid),5,mode='nearest')
    # Alargamentos (tapers, junções) não criam faixas: larguras limitadas ao típico do trecho.
    capl=float(np.median(dl[valid]))+.35;capr=float(np.median(dr[valid]))+.35
    dlc=np.minimum(dl,capl);drc=np.minimum(dr,capr);w=dlc+drc
    lw=max(2.,float(lane_w));wd=w/2 if both else w
    fit=np.maximum(1,np.floor((wd+.6)/lw)).astype(int)            # quantas faixas cabem por sentido
    if count:lanes=np.minimum(fit,int(count))
    else:
        # Pela largura (como na 1.15–1.17): total pela largura; com dois sentidos, metade para cada um.
        lanes=np.clip(np.rint(w/lw),1,6).astype(int)
        if both:lanes=np.maximum(1,lanes//2)
    lanes[(w<2.4)|((wd if count else w)>lw*6.6)|~valid]=0
    for poly,k in zones:
        sel=contains_xy(poly,q[:,0],q[:,1])&(lanes>0);lanes[sel]=int(k)
    lanes=_mode_filter(lanes,9)
    return {'q':q,'t':t,'n':n,'dl':dl,'dr':dr,'dlc':dlc,'drc':drc,'w':w,'lanes':lanes,'valid':valid,'both':bool(both),'capl':capl,'capr':capr,'lw':lw,'fwd':bool(fwd),'auto':not count}

def lane_geometry(L,sl,k,fwd=None):
    """Posições laterais (em relação à trajetória, + = direita dela) das divisórias, da linha de bordo da
    faixa (limite com o acostamento) e dos centros das faixas, com k faixas por sentido e largura fixa
    a partir do bordo interno (lado esquerdo de quem dirige)."""
    dl,dr,lw=L['dlc'][sl],L['drc'][sl],L['lw'];out={'div':[],'edge':[],'centers':[],'center':None}
    def side(inner,outer,sgn,key):
        width=np.abs(outer-inner)
        # Pela largura: divisão igual (1.15–1.17); número fixo: largura de faixa a partir do bordo interno.
        ww=width/max(k,1) if L.get('auto') else np.minimum(lw,width/max(k,1))
        for j in range(1,k):out['div'].append(inner+sgn*j*ww)
        rest=width-k*ww;out['edge'].append(np.where(rest>=1.,inner+sgn*k*ww,np.nan))
        out['centers'].append([inner+sgn*(j+.5)*ww for j in range(k)])
    if L['both']:
        c=(dr-dl)/2;out['center']=c
        side(c,dr,1.,'r');side(c,-dl,-1.,'l')
    else:
        f=L['fwd'] if fwd is None else fwd
        if f:side(-dl,dr,1.,'o')
        else:side(dr,-dl,-1.,'o')
    return out

def band(L):
    """Faixa de rolamento típica (larguras limitadas à mediana): não 'engole' gores nos alargamentos."""
    if L is None:return Polygon()
    dl=np.minimum(L['dl'],L['capl']);dr=np.minimum(L['dr'],L['capr'])
    left=L['q']-L['n']*dl[:,None];right=L['q']+L['n']*dr[:,None]
    try:return Polygon(np.vstack([left,right[::-1]])).buffer(0)
    except Exception:return Polygon()

def chain_line(pts,step=2.):
    """Polilinha -> segmentos curtos (a pintura acompanha as curvas)."""
    q,_=resample(pts,step)
    return list(zip(q[:-1],q[1:]))

def dashes(pts,dash=4.,period=12.,phase=0.):
    q,s=resample(pts,.5);out=[]
    if len(q)<2:return out
    on=((s+phase)%period)<dash;ch=np.diff(np.r_[False,on,False].astype(np.int8))
    for a,b in zip(np.flatnonzero(ch==1),np.flatnonzero(ch==-1)):
        if b-a>=2:out.append(q[a:b])
    return out

def rect(c,u,along,across):
    """Retângulo centrado em c: 'along' na direção u, 'across' na normal."""
    v=np.array([-u[1],u[0]]);a=along/2;b=across/2
    return np.array([c-u*a-v*b,c+u*a-v*b,c+u*a+v*b,c-u*a+v*b])

# ---------- setas de faixa ----------
def _arrow_parts(kind):
    S=[[(-2.5,0),(1.15,0)]]
    R=[[(-2.5,0),(-.6,0),(.9,-1.3)]]
    parts={'S':S,'R':R,'L':[[(u,-v) for u,v in R[0]]],'SR':S+[[(-1.5,0),(.5,-1.25)]],'SL':S+[[(-1.5,0),(.5,1.25)]]}
    return parts.get(kind,S)

_GLYPH={}
def arrow_glyph(kind):
    """Anéis da seta em coordenadas locais (u ao longo do tráfego, v para a esquerda), 5 m de comprimento."""
    if kind in _GLYPH:return _GLYPH[kind]
    shapes=[]
    for path in _arrow_parts(kind):
        P=np.array(path,float);end=P[-1];d=P[-1]-P[-2];d/=max(np.linalg.norm(d),1e-9);nn=np.array([-d[1],d[0]])
        shaft=np.vstack([P[:-1],end-d*1.3]);shapes.append(LineString(shaft).buffer(.11,cap_style=2,join_style=2))
        shapes.append(Polygon([end-d*1.35+nn*.46,end,end-d*1.35-nn*.46]))
    g=unary_union(shapes);rings=[np.asarray(x.exterior.coords) for x in geoms(g)]
    _GLYPH[kind]=rings;return rings

def place(rings,pt,t):
    t=np.asarray(t,float);t=t/max(np.linalg.norm(t),1e-9);v=np.array([-t[1],t[0]])
    return [np.asarray(pt)+r[:,:1]*t+r[:,1:2]*v for r in rings]

_TEXT={}
def text_rings(text):
    """Contornos de um texto (fonte Hershey), normalizados para caixa 1×1 (x para a direita, y para cima)."""
    if text in _TEXT:return _TEXT[text]
    (w,h),base=cv2.getTextSize(text,cv2.FONT_HERSHEY_DUPLEX,4,10);img=np.zeros((h+base+40,w+40),np.uint8)
    cv2.putText(img,text,(20,h+20),cv2.FONT_HERSHEY_DUPLEX,4,255,10,cv2.LINE_AA)
    cs,_=cv2.findContours((img>127).astype(np.uint8),cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
    ys,xs=np.nonzero(img>127);x0,x1,y0,y1=xs.min(),xs.max()+1,ys.min(),ys.max()+1
    out=[np.column_stack([(c[:,0,0]-x0)/(x1-x0),(y1-c[:,0,1])/(y1-y0)]).astype(float) for c in cs if len(c)>=3]
    _TEXT[text]=out;return out

def legend(text,center,t,width,height):
    """Legenda pintada no pavimento, legível para quem chega (base voltada ao motorista)."""
    t=np.asarray(t,float);t=t/max(np.linalg.norm(t),1e-9);r=np.array([t[1],-t[0]])
    return [np.asarray(center)+(q[:,:1]-.5)*width*r+(q[:,1:2]-.5)*height*t for q in text_rings(text)]

def zebra(poly,angle,color,spacing=2.6,bar=.45):
    """Hachura zebrada (barras paralelas) recortada no polígono, mais o contorno."""
    paint=[];lines=[]
    g=poly.buffer(0)
    for part in geoms(g):
        ring=np.asarray(part.exterior.coords)
        if len(ring)>=4:lines.extend(chain_line(ring))
        c=np.asarray(part.centroid.coords[0]);u=np.array([math.cos(angle),math.sin(angle)]);v=np.array([-u[1],u[0]])
        R=float(np.max(np.linalg.norm(ring-c,axis=1)))+1
        for k in np.arange(-R,R,spacing):
            seg=LineString([c+v*k-u*R,c+v*k+u*R]).buffer(bar/2,cap_style=2).intersection(part)
            for x in geoms(seg):
                if x.area>.05:paint.append(([np.asarray(x.exterior.coords)],color))
    return paint,lines

# ---------- construção ----------
PRIO={'main':3,'marginal':2,'device':1,'return':1}

def lane_lines(net,p,both,src,fwd=True):
    """Divisórias de faixa (tracejado branco), linha de bordo da faixa junto ao acostamento e eixo amarelo
    duplo onde há dois sentidos. O número de faixas por sentido vem da configuração (ou da largura), dos
    trechos desenhados e das faixas adicionais (início/fim)."""
    s=net.s;count=int(getattr(s,'lanes_per_direction',2) or 0)
    kind=net.raw_info[src]['kind'] if 0<=src<len(net.raw_info) else 'main'
    if kind!='main' and count:
        # Trajetória paralela dentro de uma pista principal já pintada (ex.: pista existente ao lado da nova):
        # não gera outro conjunto de faixas.
        mains=[band(x) for k_,x in net.lane_info.items() if x is not None and 0<=k_<len(net.raw_info) and net.raw_info[k_]['kind']=='main']
        if mains:
            from shapely.ops import unary_union as _uu
            mb=_uu(mains).buffer(.5);pp=resample(p,3.)[0]
            if np.mean(contains_xy(mb,pp[:,0],pp[:,1]))>.6:net.lane_info[src]=None;return
    L=layout(p,net.ext,net.inside,getattr(s,'lane_width_m',3.5),both,net.lane_zones,count=count if kind=='main' else 0,fwd=fwd)
    net.lane_info[src]=L
    if L is None:return
    apply_ranges(net,L)
    q,n,lanes=L['q'],L['n'],L['lanes']
    jz=getattr(net,'_jz',None)
    def emit(off,color,dashed,sl):
        ok=np.isfinite(off)
        if ok.sum()<2:return
        idx=np.flatnonzero(ok);runs=np.split(idx,np.flatnonzero(np.diff(idx)>1)+1)
        for r in runs:
            if len(r)<2:continue
            pts=q[sl][r]+n[sl][r]*off[r][:,None]
            for piece in (dashes(pts) if dashed else [pts]):
                for a,b in chain_line(piece):
                    if jz is not None and not jz.is_empty and jz.covers(Point(*(a+b)/2)):continue
                    if contains_xy(net.allowed,np.array([a[0],b[0]]),np.array([a[1],b[1]])).all():
                        net.markings.append((a,b,color));net.mark_src.append(src)
    starts=[0]+list(np.flatnonzero(np.diff(lanes)!=0)+1);ends=starts[1:]+[len(lanes)]
    for a,b in zip(starts,ends):
        k=int(lanes[a])
        if k<=0 or b-a<3:continue
        sl=slice(a,b);g=lane_geometry(L,sl,k)
        if g['center'] is not None:
            for off in (-.12,.12):emit(g['center']+off,YELLOW,False,sl)
        for d in g['div']:emit(d,WHITE,True,sl)
        for e in g['edge']:emit(e,WHITE,False,sl)

def apply_ranges(net,L):
    """Faixa adicional (ou menos faixas) entre dois pontos marcados na pista: vale para a pista mais próxima
    dos pontos, entre os km dos dois."""
    for r in getattr(net.s,'lane_ranges',[]) or []:
        a=np.array([r.start.x,r.start.y]);b=np.array([r.end.x,r.end.y])
        if min(np.min(np.linalg.norm(L['q']-a,axis=1)),np.min(np.linalg.norm(L['q']-b,axis=1)))>max(6.,L['capl']+L['capr']):continue
        ca,cb=sorted([float(net.chain(a[None])[0]),float(net.chain(b[None])[0])]);ch=net.chain(L['q'])
        sel=(ch>=ca)&(ch<=cb)&(L['lanes']>0)
        if sel.any():L['lanes'][sel]=int(r.lanes)

def classify_arrows(net):
    """Tipo de cada seta (reta, direita, esquerda, combinadas) pelas saídas do itinerário à frente."""
    E=[e for e in net.edges if not e['disabled'] and len(e['p'])>1]
    if not E or not net.arrows:
        net.arrow_near=[False]*len(net.arrows);return ['S']*len(net.arrows)
    pts=np.concatenate([e['p'] for e in E]);ids=np.concatenate([[k]*len(e['p']) for k,e in enumerate(E)]);tr=cKDTree(pts)
    index={id(e):i for i,e in enumerate(net.edges)};conflict=net.conflict_nodes();out=[];near=[]
    for pt,t in net.arrows:
        d,j=tr.query(pt);kind='S';nc=False
        if d<2.5:
            e=E[ids[j]]
            if e['end'] in conflict:
                k=int(np.argmin(np.linalg.norm(e['p']-pt,axis=1)))
                if e['d'][-1]-e['d'][k]<70:
                    nc=True
                    te=e['t'][-1];cls=set()
                    for jj in net.connections.get(index[id(e)],[]):
                        f=net.edges[jj];v=f['p'][int(np.searchsorted(f['d'],min(20.,f['d'][-1])))]-e['p'][-1]
                        if np.linalg.norm(v)<1e-6:continue
                        ang=math.degrees(math.atan2(te[0]*v[1]-te[1]*v[0],float(te@v)))
                        cls.add('S' if abs(ang)<30 else 'L' if ang>0 else 'R')
                    if len(cls)>=2:kind='SR' if cls>={'S','R'} else 'SL' if cls>={'S','L'} else 'S'
        out.append(kind);near.append(nc or kind!='S')
    net.arrow_near=near
    return out

def thin_arrows(net,gap):
    """1.18: no máximo uma seta por trecho de 'gap' metros no mesmo sentido (evita excesso e setas sobrepostas)."""
    kept=[]
    # Setas dos anéis de rotatória primeiro (indicam a circulação; não podem sumir).
    def ring(p):return any(np.linalg.norm(p-c)<r+10 for c,r in getattr(net,'islands',[]))
    order=sorted(net.arrows,key=lambda a:not ring(a[0]))
    for pt,t in order:
        if all(np.linalg.norm(pt-q)>=gap or float(np.dot(t,u))<.7 for q,u in kept):kept.append((pt,t))
    net.arrows=kept

def multilane_arrows(net,kinds):
    """Repete as setas das vias principais/marginais em cada faixa do mesmo sentido."""
    info=[(k,L) for k,L in net.lane_info.items() if L is not None]
    if not info:return net.arrows,kinds,[p for p,_ in net.arrows]
    Q=np.concatenate([L['q'] for _,L in info]);ref=np.concatenate([[(i,j) for j in range(len(L['q']))] for i,(_,L) in enumerate(info)]);tr=cKDTree(Q)
    arrows=[];out=[];anc=[];mode=getattr(net.s,'lane_arrow_repeat','conflicts');near=getattr(net,'arrow_near',None) or [True]*len(kinds)
    for (pt,t),kind,nc in zip(net.arrows,kinds,near):
        d,j=tr.query(pt)
        if d>6 or mode=='off' or (mode=='conflicts' and not nc):arrows.append((pt,t));out.append(kind);anc.append(pt);continue
        i,jj=ref[j];L=info[i][1];n=int(L['lanes'][jj])
        if n<(2 if L.get('auto') else 1) or abs(float(np.dot(t,L['t'][jj])))<.9:arrows.append((pt,t));out.append(kind);anc.append(pt);continue
        q,nn=L['q'][jj],L['n'][jj];same=float(np.dot(t,L['t'][jj]))>0
        g=lane_geometry(L,slice(jj,jj+1),n,fwd=same)
        cs=g['centers'][0] if not L['both'] else (g['centers'][0] if same else g['centers'][1])
        centers=[float(c[0]) for c in cs]
        # Da direita para a esquerda de quem dirige (direita do motorista = +n quando o sentido coincide).
        centers=sorted(centers,reverse=same)
        for r,c in enumerate(centers):
            p=q+nn*c
            if not contains_xy(net.allowed,p[0:1],p[1:2])[0]:continue
            kk=kind
            if kind in ('SR','R') and r>0:kk='S'
            if kind in ('SL','L') and r<len(centers)-1:kk='S'
            arrows.append((p,t));out.append(kk);anc.append(np.asarray(pt,float))
    # Sem setas sobrepostas (a repetição por faixa prevalece sobre setas avulsas no mesmo lugar).
    keep=[];ka=[];kc=[]
    for (p,t),k,c in sorted(zip(arrows,out,anc),key=lambda x:x[1]=='S'):
        if all(np.linalg.norm(p-q)>=3. for q,_ in keep):keep.append((p,t));ka.append(k);kc.append(c)
    return keep,ka,kc

def two_way_fix(net):
    """Pista com veículos nos dois sentidos (sem canteiro): eixo amarelo e faixas divididas por sentido."""
    live=[e for e in net.edges if not e['disabled'] and len(e['p'])>2]
    for k,L in list(net.lane_info.items()):
        if L is None or L['both']:continue
        g=band(L);tr=cKDTree(L['q']);same=opp=0
        for e in live:
            P=e['p'][::5];T=e['t'][::5];ins=contains_xy(g,P[:,0],P[:,1])
            if not ins.any():continue
            j=tr.query(P[ins])[1];dots=np.sum(T[ins]*L['t'][j],axis=1)
            same+=int((dots>.8).sum());opp+=int((dots<-.8).sum())
        tot=same+opp
        if tot and opp>.2*tot and same>.2*tot:
            keep=[i for i,s_ in enumerate(net.mark_src) if s_!=k]
            net.markings=[net.markings[i] for i in keep];net.mark_src=[net.mark_src[i] for i in keep]
            lane_lines(net,net.raw_info[k]['points'],True,k)

def gores(net):
    """Zebrados nos gores: área pintável entre dois ramos que divergem (ou convergem) de um mesmo nó,
    até o 'nariz' (onde o pavimento entre eles acaba), descontadas as pistas reais dos dois ramos."""
    from itertools import combinations
    by={}
    for k,e in enumerate(net.edges):
        if e['disabled'] or e['length']<10:continue
        by.setdefault(('s',e['start']),[]).append(k);by.setdefault(('e',e['end']),[]).append(k)
    out=[];prev={}
    for i,js in net.connections.items():
        for j in js:prev.setdefault(j,[]).append(i)
    def follow(k,fwd,limit=140.):
        """Pontos a partir do nó, seguindo as arestas seguintes de direção mais parecida (as arestas são curtas)."""
        e=net.edges[k];pts=[e['p'] if fwd else e['p'][::-1]];L=e['length'];cur=k
        while L<limit:
            nxt=net.connections.get(cur,[]) if fwd else prev.get(cur,[])
            if not nxt:break
            t=pts[-1][-1]-pts[-1][max(0,len(pts[-1])-6)]
            def score(j):
                f=net.edges[j];q=f['p'] if fwd else f['p'][::-1];u=q[min(len(q)-1,5)]-q[0]
                return float(u@t)/max(np.linalg.norm(u)*np.linalg.norm(t),1e-9)
            j=max(nxt,key=score)
            if score(j)<.7:break
            f=net.edges[j];pts.append(f['p'] if fwd else f['p'][::-1]);L+=f['length'];cur=j
        return np.vstack(pts)
    for (side,node),ks in by.items():
        for a,b in combinations(ks,2):
            ea,eb=net.edges[a],net.edges[b]
            if ea.get('origin')==eb.get('origin') or ea.get('ring') or eb.get('ring'):continue
            pa=follow(a,side=='s');pb=follow(b,side=='s')
            qa,sa=resample(pa,1.);qb,sb=resample(pb,1.);m=min(len(qa),len(qb),140)
            if m<12:continue
            va=qa[min(m-1,15)]-qa[0];vb=qb[min(m-1,15)]-qb[0]
            if np.linalg.norm(va)<1 or np.linalg.norm(vb)<1:continue
            if float(va@vb)<math.cos(math.radians(40))*np.linalg.norm(va)*np.linalg.norm(vb):continue
            mid=(qa[:m]+qb[:m])/2;ok=contains_xy(net.paved,mid[:,0],mid[:,1])
            j=int(np.argmin(ok)) if not ok.all() else m
            if j<10:continue
            try:
                g=Polygon(np.vstack([qa[:j],qb[:j][::-1]])).buffer(0).intersection(net.paved)
                g=g.difference(unary_union([edge_band(net,ea),edge_band(net,eb)]).buffer(.3))
            except Exception:continue
            for x in geoms(g):
                if 8<=x.area<=900 and not x.buffer(-.5).is_empty:out.append(x)
    out+=nose_gores(net)
    if not out:return []
    return geoms(unary_union(out))

def noses(net,max_angle=60.):
    """Pontas agudas de área não pavimentada entrando no pavimento (narizes de ilhas e de ramos)."""
    out=[]
    for poly in geoms(net.paved):
        for ring in [poly.exterior]+list(poly.interiors):
            r=np.asarray(LineString(ring.coords).simplify(.4).coords)[:-1]
            if len(r)<3:continue
            a=np.roll(r,1,0)-r;b=np.roll(r,-1,0)-r
            la=np.linalg.norm(a,axis=1);lb=np.linalg.norm(b,axis=1);ok=(la>.3)&(lb>.3)
            ua=a/np.maximum(la,1e-9)[:,None];ub=b/np.maximum(lb,1e-9)[:,None]
            ang=np.degrees(np.arccos(np.clip(np.sum(ua*ub,axis=1),-1,1)))
            bis=ua+ub;bis/=np.maximum(np.linalg.norm(bis,axis=1),1e-9)[:,None];probe=r+bis*.6
            grass=~contains_xy(net.paved,probe[:,0],probe[:,1])
            out+=[r[i] for i in np.flatnonzero(ok&(ang<max_angle)&grass)]
    return out

def nose_gores(net):
    """Pavimento sem trajetória de veículos que termina num nariz: zebrado (até 60 m antes do nariz)."""
    ns=noses(net)
    if not ns:return []
    lw=float(getattr(net.s,'lane_width_m',3.5))
    lanes=[LineString(e['p']).buffer(lw/2) for e in net.edges if not e['disabled'] and len(e['p'])>1]
    lanes+=[LineString(c).buffer(lw/2) for c in net.connectors.values() if len(c)>1]
    lanes+=[band(L) for L in net.lane_info.values() if L is not None]
    if not lanes:return []
    left=net.paved.difference(unary_union(lanes).buffer(.3))
    if left.is_empty:return []
    nt=cKDTree(np.array(ns));out=[]
    E=[e for e in net.edges if not e['disabled'] and len(e['p'])>1]
    et=cKDTree(np.concatenate([e['p'] for e in E]));eo=np.concatenate([[e.get('origin',-1)]*len(e['p']) for e in E])
    bp=[]
    for poly in geoms(net.paved):
        for r in [poly.exterior]+list(poly.interiors):bp.append(resample(np.asarray(r.coords),.4)[0])
    bt=cKDTree(np.concatenate(bp))
    for g in geoms(left):
        if g.area<8:continue
        near=[ns[i] for i in nt.query_ball_point(np.asarray(g.centroid.coords[0]),80)]
        hit=[p for p in near if g.distance(Point(*p))<3.]
        if not hit:continue
        g=g.intersection(unary_union([Point(*p).buffer(60) for p in hit]))
        for x in geoms(g):
            if not(8<=x.area<=1500) or x.buffer(-.5).is_empty:continue
            q,_=resample(np.asarray(x.exterior.coords),.5)
            if float(np.mean(bt.query(q)[0]<.45))>.25:continue
            # Gore de verdade: o contorno encosta em faixas de DOIS ramos diferentes (um de cada lado).
            d,j=et.query(q);near=d<lw/2+1.2
            if not near.any():continue
            org=eo[j[near]];vals,cnt=np.unique(org,return_counts=True)
            if (cnt>=.2*len(q)).sum()<2:continue
            out.append(x)
    return out

def edge_band(net,f):
    """Pista real (bordo a bordo) do trecho a que pertence a aresta f."""
    cache=net.__dict__.setdefault('_bands',{})
    if f['base'] in cache:return cache[f['base']]
    k=next((i for i,r in enumerate(net.raw_info) if r['base']==f['base']),None);L=net.lane_info.get(k) if k is not None else None
    if L is None and k is not None:L=layout(net.raw_info[k]['points'],net.ext,net.inside,getattr(net.s,'lane_width_m',3.5),False)
    g=band(L) if L is not None else Polygon()
    if g.is_empty and len(f['p'])>1:g=LineString(f['p']).buffer(3.)
    cache[f['base']]=g;return g

def stop_lines(net):
    """Linha de retenção + PARE (entradas em nível) e linha de dê a preferência (rotatórias), com placas."""
    conflict=net.conflict_nodes();paint=[];signs=[];lw=float(getattr(net.s,'lane_width_m',3.5))
    by_node={}
    for k,e in enumerate(net.edges):
        if e['disabled']:continue
        by_node.setdefault(e['start'],[]).append(k);by_node.setdefault(e['end'],[]).append(k)
    def prio(e):return 2.5 if e.get('ring') else PRIO.get(e['kind'],1)
    # Ilhas de rotatória (inclusive as menos circulares que o tráfego não reconhece como anel).
    rings=list(net.islands)
    for poly in geoms(net.allowed):
        for r_ in poly.interiors:
            h=Polygon(r_)
            if 50<h.area<2000 and 4*math.pi*h.area/max(h.length**2,1e-9)>.3:rings.append((np.asarray(h.centroid.coords[0]),math.sqrt(h.area/math.pi)))
    for k,e in enumerate(net.edges):
        if e['disabled'] or e['end'] not in conflict or e['length']<12 or e.get('ring'):continue
        node=net.nodes[e['end']][0];te=e['t'][-1]
        through=[net.edges[x] for x in by_node.get(e['end'],[]) if x!=k and prio(net.edges[x])>prio(e) and net.edges[x].get('origin')!=e.get('origin')]
        if not through:continue
        ring=any(f.get('ring') for f in through) or any(np.linalg.norm(node-c)<r+16 for c,r in rings)
        if not ring:
            f=max(through,key=prio);jj=int(np.argmin(np.linalg.norm(f['p']-node,axis=1)));tf=f['t'][jj]
            if abs(float(te@tf))>.82:continue  # convergência tangencial (faixa de aceleração): sem retenção
        zone=unary_union([edge_band(net,f) for f in through]).buffer(.6)
        idx=None
        for i in range(len(e['p'])-1,-1,-1):
            if not zone.covers(Point(*e['p'][i])):idx=i;break
        if idx is None or e['d'][-1]-e['d'][idx]>40 or e['d'][idx]<6:continue
        q=e['p'][idx];t=e['t'][idx];n=np.array([t[1],-t[0]])
        dl,dr=net.ext.query(q[None],n[None]);dl=float(dl[0]);dr=float(dr[0])
        if not(np.isfinite(dl) and np.isfinite(dr)):continue
        off=float(e.get('offset',0.))
        a=-(off if e.get('both') else min(dl,8.));b=min(dr,8.)
        if e.get('both'):b=min(b,a+lw*2.3)  # mão dupla: retenção só na metade de quem chega
        if b-a<1.5 or b-a>lw*2.3:continue
        c=q+n*((a+b)/2);span=b-a-.3
        area=net.paved.buffer(-.15)
        def clip(r):
            g=Polygon(r).intersection(area)
            return [np.asarray(x.exterior.coords) for x in geoms(g) if x.area>.05],g.area/max(Polygon(r).area,1e-9)
        if ring:
            for s_ in np.arange(-span/2+.3,span/2,1.2):
                rr,f_=clip(rect(c+n*s_,n,.6,.4))
                if rr:paint.append((rr,WHITE))
            signs.append({'point':q+n*(dr+1.2),'code':'R-2','text':'','heading':float(math.degrees(math.atan2(t[1],t[0]))),'auto':True})
        else:
            rr,f_=clip(rect(c,n,span,.4))
            if f_<.6:continue
            paint.append((rr,WHITE))
            txt=legend('PARE',c-t*2.6,t,min(span-.4,2.6),3.6)
            if contains_xy(area,np.vstack(txt)[:,0],np.vstack(txt)[:,1]).all():paint.append((txt,WHITE))
            signs.append({'point':q+n*(dr+1.2),'code':'R-1','text':'','heading':float(math.degrees(math.atan2(t[1],t[0]))),'auto':True})
    return paint,signs

def crosswalk(net,cw):
    a=np.array([cw.a.x,cw.a.y]);b=np.array([cw.b.x,cw.b.y]);L=float(np.linalg.norm(b-a))
    if L<1:return []
    u=(b-a)/L;out=[];area=net.paved.buffer(.5)
    for s_ in np.arange(.5,L-.2,1.):
        c=a+u*s_
        if area.covers(Point(*c)):out.append(([rect(c,u,.4,float(cw.width_m))],WHITE))
    return out

def main_angle(net,c):
    i=int(net.tree.query(c)[1]);t=net.axis_t[i];return math.atan2(t[1],t[0])

def dxf_signage(net,items):
    paint=[];lines=[]
    for e in items:
        p=np.asarray(e['points'],float)
        name=str(e.get('layer','')).upper();col=YELLOW if ('AMAREL' in name or 'YELLOW' in name) else WHITE
        if e.get('closed') and len(p)>=3:
            if Polygon(p).area>500:continue   # 1.18: área grande demais para pintura (provável pavimento)
            paint.append(([p]+[np.asarray(h) for h in e.get('holes',[])],col))
        elif len(p)>=2:lines.extend((a,b,col) for a,b in chain_line(p))
    return paint,lines

def build(net,dxf_h=(),dxf_v=()):
    """Etapa final do modo completo (chamada em finalize_signage, antes das áreas sem sinalização)."""
    s=net.s;paint=[];signs=[]
    if dxf_h and getattr(s,'dxf_signage','replace')=='replace':
        net.markings=[];net.mark_src=[];net.arrows=[];net.arrow_kinds=[];net.arrow_anchors=[]
    else:two_way_fix(net)
    if dxf_h and getattr(s,'dxf_signage','replace')=='replace':pass
    elif getattr(s,'lane_arrows',True) and net.arrows:
        gap=float(getattr(s,'arrow_min_gap_m',25))
        if gap>0:thin_arrows(net,gap)
        kinds=classify_arrows(net);net.arrows,net.arrow_kinds,net.arrow_anchors=multilane_arrows(net,kinds)
    else:net.arrow_kinds=['S']*len(net.arrows);net.arrow_anchors=[p for p,_ in net.arrows]
    if not (dxf_h and getattr(s,'dxf_signage','replace')=='replace'):
        if getattr(s,'gore_hatch',True):
            G=gores(net)
            if G and net.markings:
                gu=unary_union([g.buffer(.3) for g in G]);M=np.array([(m[0]+m[1])/2 for m in net.markings]);ins=contains_xy(gu,M[:,0],M[:,1])
                keep=[i for i,k in enumerate(ins) if not k or net.mark_src[i]==-2]
                net.markings=[net.markings[i] for i in keep];net.mark_src=[net.mark_src[i] for i in keep]
            for g in G:
                pp,ll=zebra(g.buffer(-.25),main_angle(net,np.asarray(g.centroid.coords[0]))+math.radians(45),WHITE)
                paint+=pp;net.markings+=[(a,b,WHITE) for a,b in ll];net.mark_src+=[-3]*len(ll)
        if getattr(s,'stop_lines',True):
            pp,ss=stop_lines(net);paint+=pp
            if getattr(s,'auto_signs',True):signs+=ss
    if dxf_h:
        pp,ll=dxf_signage(net,dxf_h);paint+=pp;net.markings+=ll;net.mark_src+=[-4]*len(ll)
    for h in getattr(s,'hatch_areas',[]) or []:
        if len(h.points)<3:continue
        poly=Polygon([(p.x,p.y) for p in h.points]).buffer(0)
        ang=math.radians(h.angle_deg) if h.angle_deg is not None else main_angle(net,np.asarray(poly.centroid.coords[0]))+math.radians(45)
        pp,ll=zebra(poly,ang,YELLOW if h.color=='yellow' else WHITE,h.spacing_m)
        paint+=pp;net.markings+=[(a,b,YELLOW if h.color=='yellow' else WHITE) for a,b in ll];net.mark_src+=[-5]*len(ll)
    for cw in getattr(s,'crosswalks',[]) or []:
        if cw.show:paint+=crosswalk(net,cw)
    for e in dxf_v:
        signs.append({'point':np.asarray(e['points'][0],float),'code':e.get('code','I'),'text':e.get('text',''),'heading':e.get('rotation'),'auto':False,'source':'DXF'})
    for m in getattr(s,'signs',[]) or []:
        if m.show:signs.append({'point':np.array([m.point.x,m.point.y]),'code':m.code,'text':m.text,'heading':m.heading_deg,'auto':False,'source':'manual'})
    net.fills=paint;net.signs=signs

def clean(net,area):
    """Remove pinturas e placas automáticas dentro das áreas sem sinalização."""
    if area is None or area.is_empty:return
    if net.fills:
        C=np.array([np.mean(np.vstack(r),axis=0) for r,_ in net.fills]);ins=contains_xy(area,C[:,0],C[:,1])
        net.fills=[x for x,k in zip(net.fills,ins) if not k]
    if net.signs:
        net.signs=[g for g in net.signs if not(g.get('auto') and area.covers(Point(*g['point'])))]

# ---------- desenho no vídeo ----------
def paint_arrays(net):
    """Pré-processa pinturas para o desenho rápido (centro, raio, anéis)."""
    items=[]
    for rings,col in getattr(net,"fills",[]):
        allp=np.vstack(rings);c=allp.mean(0);items.append((c,float(np.max(np.linalg.norm(allp-c,axis=1))),rings,col))
    for (pt,t),k in zip(net.arrows,getattr(net,'arrow_kinds',[]) or []):
        rings=place(arrow_glyph(k),pt,t);items.append((np.asarray(pt,float),2.6,rings,WHITE))
    return items

def draw_paint(im,items,centers,chains,screen,cam,width,limit,m,color_override=None):
    if not items:return
    near=(np.linalg.norm(centers-cam,axis=1)<width*.75)&(chains<=limit)
    for k in np.flatnonzero(near):
        c,r,rings,col=items[k]
        q=[np.rint(screen(x)*16).astype(np.int32) for x in rings]
        cv2.fillPoly(im,q,tuple(int(v) for v in (color_override or col)),cv2.LINE_AA,4)

_SPRITES={}
def sign_sprite(code,text,size):
    key=(code,text,size)
    if key in _SPRITES:return _SPRITES[key]
    from PIL import Image,ImageDraw
    from .render import font
    S=size*4;W=S if code not in ('I','S') else int(S*max(1.,min(3.2,.35+.16*len(text or 'Indicação'))));img=Image.new('RGBA',(W,S),(0,0,0,0));d=ImageDraw.Draw(img)
    def txt(t,box,color,bold=True):
        x0,y0,x1,y1=box;n=int((y1-y0)*.6)
        while n>6 and d.textbbox((0,0),t,font=font(n,bold))[2]>(x1-x0):n-=1
        bb=d.textbbox((0,0),t,font=font(n,bold));d.text(((x0+x1-bb[2])/2,(y0+y1-bb[3])/2-bb[1]/2),t,fill=color,font=font(n,bold))
    m=S*.04
    if code=='R-1':
        r=S/2-m;pts=[(S/2+r*math.cos(math.radians(22.5+45*k)),S/2+r*math.sin(math.radians(22.5+45*k))) for k in range(8)]
        d.polygon(pts,fill=(255,255,255));r2=r*.88;d.polygon([(S/2+r2*math.cos(math.radians(22.5+45*k)),S/2+r2*math.sin(math.radians(22.5+45*k))) for k in range(8)],fill=(200,30,36))
        txt('PARE',(S*.14,S*.3,S*.86,S*.7),(255,255,255))
    elif code=='R-2':
        d.polygon([(m,m*2),(S-m,m*2),(S/2,S-m)],fill=(200,30,36));k=S*.17;d.polygon([(m+k,m*2+k*.6),(S-m-k,m*2+k*.6),(S/2,S-m-k*1.2)],fill=(255,255,255))
    elif code=='R-19':
        d.ellipse([m,m,S-m,S-m],fill=(200,30,36));k=S*.12;d.ellipse([m+k,m+k,S-m-k,S-m-k],fill=(255,255,255))
        txt((text or '80')[:3],(S*.2,S*.25,S*.8,S*.68),(10,10,10));txt('km/h',(S*.32,S*.64,S*.68,S*.8),(10,10,10),False)
    elif code in ('A','OBRAS'):
        bg=(250,200,20) if code=='A' else (240,120,20)
        d.polygon([(S/2,m),(S-m,S/2),(S/2,S-m),(m,S/2)],fill=(15,15,15));k=S*.06
        d.polygon([(S/2,m+k*1.4),(S-m-k*1.4,S/2),(S/2,S-m-k*1.4),(m+k*1.4,S/2)],fill=bg)
        txt((text or ('!' if code=='A' else 'OBRAS'))[:8],(S*.24,S*.36,S*.76,S*.64),(15,15,15))
    else:
        bg=(0,110,60) if code=='I' else (20,70,160)
        d.rounded_rectangle([m,S*.12,W-m,S*.88],radius=S*.08,fill=(255,255,255));d.rounded_rectangle([m+S*.04,S*.16,W-m-S*.04,S*.84],radius=S*.06,fill=bg)
        txt((text or ('Indicação' if code=='I' else 'Serviço'))[:24],(S*.1,S*.22,W-S*.1,S*.78),(255,255,255))
    img=img.resize((max(1,W//4),size),Image.LANCZOS);a=np.array(img)
    _SPRITES[key]=a
    if len(_SPRITES)>400:_SPRITES.pop(next(iter(_SPRITES)))
    return a

def draw_signs(im,sc,cam,width,progress,hdr,ftr):
    signs=getattr(sc.network,'signs',[]) or []
    if not signs or width>900:return
    m=width/sc.W;size=int(np.clip(1.4/m,22*sc.scale*1.6,70*sc.scale*1.6));size=max(14,size)
    H,W=im.shape[:2]
    for g in signs:
        p=np.asarray(g['point'],float)
        if np.linalg.norm(p-cam)>width*.75:continue
        if sc.ch[sc.tree.query(p)[1]]>progress*sc.length+25:continue
        x,y=sc.screen(p[None],cam,width)[0]
        post=int(size*.9)
        if not(0<x<W and hdr+post+size<y<ftr):continue
        x=int(round(x));y=int(round(y))
        cv2.ellipse(im,(x+2,y+1),(max(2,size//6),max(1,size//14)),0,0,360,(25,28,25),-1,cv2.LINE_AA)
        cv2.line(im,(x,y),(x,y-post),(70,74,78),max(2,size//12),cv2.LINE_AA)
        spr=sign_sprite(g['code'],g.get('text','') or '',size);h,w=spr.shape[:2]
        x0=x-w//2;y0=y-post-h+2;x1=x0+w;y1=y0+h
        if x0<0 or y0<0 or x1>W or y1>H:continue
        a=spr[:,:,3:4].astype(np.float32)/255;roi=im[y0:y1,x0:x1]
        roi[:]=(roi*(1-a)+spr[:,:,:3]*a).astype(np.uint8)
