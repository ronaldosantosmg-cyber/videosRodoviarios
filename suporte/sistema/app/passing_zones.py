"""2.14: trechos onde a ultrapassagem pela pista contrária é geometricamente possível (função pura, sem simulação).
Critérios: raio mínimo, visibilidade à frente (corda x trajeto), distância às pontas e às seções marcadas como proibidas."""
from .seguro import sdiv as _sdiv
import math
import numpy as np

MIN_RADIUS_M=220.      # raio horizontal mínimo para considerar a curva compatível com ultrapassagem
SIGHT_M=180.           # visibilidade exigida à frente (distância de ultrapassagem para ~70 km/h)
SIGHT_DEVIATION_M=3.0  # desvio máximo do trajeto em relação à corda de visão
END_MARGIN_M=60.       # distância mínima das pontas (acessos, nós, semáforos próximos)
STEP_M=5.

def _arc(points):
    p=np.asarray(points,float);d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))];return p,d

def curvature_radius(points,step=STEP_M):
    """Raio de curvatura (m) por amostra a cada ``step`` m; inf em reta."""
    p,d=_arc(points)
    if len(p)<3 or d[-1]<=0:return np.array([]),np.array([])
    s=np.arange(0,d[-1]+1e-9,step);x=np.interp(s,d,p[:,0]);y=np.interp(s,d,p[:,1])
    R=np.full(len(s),np.inf)
    for i in range(1,len(s)-1):
        a=np.array([x[i-1],y[i-1]]);b=np.array([x[i],y[i]]);c=np.array([x[i+1],y[i+1]])
        ab=np.linalg.norm(b-a);bc=np.linalg.norm(c-b);ca=np.linalg.norm(a-c)
        area2=abs(float((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])))
        if area2>1e-9 and ab>0 and bc>0 and ca>0:R[i]=ab*bc*ca/(2*area2)
    return s,R

def passing_mask(points,sight_m=SIGHT_M,min_radius=MIN_RADIUS_M,end_margin=END_MARGIN_M,deny=()):
    """(estações, máscara bool): onde iniciar uma ultrapassagem é permitido pela geometria."""
    p,d=_arc(points)
    s,R=curvature_radius(points)
    if len(s)==0:return s,np.array([],bool)
    x=np.interp(s,d,p[:,0]);y=np.interp(s,d,p[:,1]);ok=np.ones(len(s),bool)
    ok&=R>=min_radius
    ok&=(s>=end_margin)&(s<=d[-1]-end_margin)
    # visibilidade: o trajeto à frente não pode se afastar da corda mais que SIGHT_DEVIATION_M
    n=max(1,int(sight_m/STEP_M))
    for i in range(len(s)):
        j=min(len(s)-1,i+n)
        if j==i:ok[i]=False;continue
        a=np.array([x[i],y[i]]);b=np.array([x[j],y[j]]);ab=b-a;L=float(np.linalg.norm(ab))
        if L<(_sdiv(.5*sight_m*(j-i), n)):ok[i]=False;continue
        seg=np.column_stack([x[i:j+1],y[i:j+1]])-a;dev=(_sdiv(np.abs(seg[:,0]*ab[1]-seg[:,1]*ab[0]), L))
        if dev.max()>SIGHT_DEVIATION_M:ok[i]=False
    for lo,hi in deny:ok&=~((s>=min(lo,hi))&(s<=max(lo,hi)))
    return s,ok

def window_allowed(points,start_m,end_m,**kw):
    """A manobra inteira (início..fim) precisa estar em estações permitidas, inclusive a visão à frente do retorno."""
    s,ok=passing_mask(points,**kw)
    if len(s)==0:return False
    sel=(s>=start_m-1e-6)&(s<=end_m+1e-6)
    return bool(sel.any() and ok[sel].all())

def zones(points,**kw):
    """Lista de (início, fim) em metros onde a ultrapassagem pode começar."""
    s,ok=passing_mask(points,**kw);out=[];start=None
    for i,v in enumerate(ok):
        if v and start is None:start=s[i]
        if (not v or i==len(ok)-1) and start is not None:
            end=s[i] if v else s[i-1]
            if end-start>=STEP_M*4:out.append((float(start),float(end)))
            start=None
    return out

def has_oncoming(points,others):
    """True se alguma outra trajetória corre em sentido oposto, 1,5–8 m ao lado (pista simples com faixa contrária)."""
    from shapely.geometry import LineString,Point
    p,d=_arc(points)
    if len(p)<2 or d[-1]<=0:return False
    own=LineString(p)
    mid=np.array(own.interpolate(d[-1]/2).coords[0]);t=np.array(own.interpolate(d[-1]/2+1).coords[0])-np.array(own.interpolate(d[-1]/2-1).coords[0])
    n=float(np.linalg.norm(t))
    if n<1e-9:return False
    t/=n;left=np.array([-t[1],t[0]])
    for q in others:
        line=q if isinstance(q,LineString) else LineString(q);s=line.project(Point(mid));near=np.array(line.interpolate(s).coords[0])
        tt=np.array(line.interpolate(min(line.length,s+1)).coords[0])-np.array(line.interpolate(max(0.,s-1)).coords[0]);m=float(np.linalg.norm(tt))
        if m<1e-9:continue
        if 1.5<=abs(float((near-mid)@left))<=8. and float((tt/m)@t)<-.7:return True
    return False


def oncoming_flags(paths):
    """Índice espacial do estudo: não compara cada percurso com toda a rodovia."""
    from shapely.geometry import LineString,box
    from shapely import STRtree
    lines=[LineString(p) for p in paths]
    index=STRtree(lines)
    flags=[]
    for i,line in enumerate(lines):
        mid=line.interpolate(line.length/2)
        candidates=index.query(box(mid.x-8,mid.y-8,mid.x+8,mid.y+8))
        flags.append(has_oncoming(paths[i],[lines[int(k)] for k in candidates if int(k)!=i]))
    return flags

def slice_polyline(points,a,b):
    p,d=_arc(points);s=np.arange(a,b+1e-9,STEP_M)
    return [[round(float(np.interp(x,d,p[:,0])),2),round(float(np.interp(x,d,p[:,1])),2)] for x in s]
