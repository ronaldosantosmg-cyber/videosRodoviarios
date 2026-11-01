"""2.48: veículos em vista superior com acabamento de ilustração realista, desenhados UMA vez por (classe, cor, resolução) e girados no quadro.
Só aparência: a pegada do desenho cabe exatamente em L×B (as dimensões usadas nos cálculos de colisão e reserva lateral não mudam).
Cada peça (carroceria, teto, vidros, faróis…) é sombreada a partir de um mapa de altura próprio (cúpula suave), com luz difusa e brilho especular;
vidros têm degradê e reflexo; tudo em supersampling 3× e reduzido com média de área."""
import math
import numpy as np,cv2

SS=3
BUCKETS=(6,10,16,24,40,64,100)       # px/m em que o sprite é gerado
_CACHE={};_MAX=600
LUZ=np.array([-.45,-.55,.70],np.float32);LUZ/=np.linalg.norm(LUZ)
VIDRO_A=np.array([16,26,38],np.float32);VIDRO_B=np.array([70,96,118],np.float32)

class Tela:
    def __init__(s,L,B,ppm):
        s.L=L;s.B=B;s.k=ppm*SS;s.W=int(round(L*s.k))+6;s.H=int(round(B*s.k))+6
        s.rgb=np.zeros((s.H,s.W,3),np.float32);s.a=np.zeros((s.H,s.W),np.float32)
    def P(s,pts):
        p=np.asarray(pts,np.float64);return np.column_stack([(p[:,0]+s.L/2)*s.k+3,(p[:,1]+s.B/2)*s.k+3])
    def mask(s,pts):
        m=np.zeros((s.H,s.W),np.uint8);q=np.rint(s.P(pts)*16).astype(np.int32);cv2.fillPoly(m,[q],255,cv2.LINE_AA,shift=4);return m.astype(np.float32)/255
    def put(s,m,rgb):                                   # composição "sobre": rgb pode ser (3,) ou imagem
        m3=m[...,None];s.rgb=s.rgb*(1-m3)+np.asarray(rgb,np.float32)*m3;s.a=s.a+m*(1-s.a)
    def linha(s,a,b,cor,esp,alfa=1.):
        m=np.zeros((s.H,s.W),np.uint8);p=np.rint(s.P([a,b])*16).astype(np.int32);cv2.line(m,tuple(p[0]),tuple(p[1]),255,max(1,int(round(esp*s.k))),cv2.LINE_AA,shift=4)
        s.put(m.astype(np.float32)/255*alfa*(s.mask_clip if getattr(s,'mask_clip',None) is not None else 1),cor)

def superelipse(x0,x1,larg,nf=3.2,nb=3.6,n=96,dy=0.):
    xc=(x0+x1)/2;a=(x1-x0)/2;t=np.linspace(0,2*np.pi,n,endpoint=False);c=np.cos(t);s=np.sin(t);ex=np.where(c>=0,nf,nb)
    return np.column_stack([xc+a*np.sign(c)*np.abs(c)**(2/ex),dy+(larg/2)*np.sign(s)*np.abs(s)**(2/ex)])
def retangulo(x0,x1,y0,y1,r=.08):
    r=min(r,(x1-x0)/2,(y1-y0)/2);pts=[]
    for cx,cy,a0 in ((x1-r,y1-r,0),(x0+r,y1-r,90),(x0+r,y0+r,180),(x1-r,y0+r,270)):
        for a in np.linspace(a0,a0+90,6):pts.append((cx+r*math.cos(math.radians(a)),cy+r*math.sin(math.radians(a))))
    return np.array(pts)

def sombrear(T,m,cor,cupula=.5,esp=.30,amb=.52,forca=7.,borda=True):
    """pinta a peça de máscara m com volume: normal a partir de uma cúpula suave (distância à borda)."""
    mb=(m>.5).astype(np.uint8)
    if not mb.any():return
    d=cv2.distanceTransform(mb,cv2.DIST_L2,5);dm=max(float(d.max()),1.);h=(d/dm)**cupula;h=cv2.GaussianBlur(h,(0,0),max(1.1*SS,dm*.30))
    gy,gx=np.gradient(h);n=np.stack([-gx*forca*dm/10,-gy*forca*dm/10,np.ones_like(h)],-1);n/=np.linalg.norm(n,axis=-1,keepdims=True)
    dif=np.clip((n*LUZ).sum(-1),0,1);hv=LUZ+np.array([0,0,1],np.float32);hv/=np.linalg.norm(hv);sp=np.clip((n*hv).sum(-1),0,1)**38
    c=np.asarray(cor,np.float32);col=c*(amb+(1-amb)*dif*1.25)[...,None]+(sp*esp*255)[...,None]
    if borda:col=col*(.72+.28*np.clip(d/(2.2*SS+dm*.12),0,1))[...,None]            # oclusão perto da borda
    T.put(m,np.clip(col,0,255))
def vidro(T,m,reflexo=.34,ang=.5):
    ys,xs=np.mgrid[0:T.H,0:T.W].astype(np.float32);u=(xs/T.W*math.cos(ang)+ys/T.H*math.sin(ang));u=(u-u.min())/(np.ptp(u)+1e-6)
    col=VIDRO_A+(VIDRO_B-VIDRO_A)*(u**1.6)[...,None]
    faixa=np.exp(-((u-.42)/.07)**2)+.55*np.exp(-((u-.66)/.04)**2);col=col+faixa[...,None]*255*reflexo*.55
    T.put(m,np.clip(col,0,255))
def cor_lisa(T,m,cor):T.put(m,np.asarray(cor,np.float32))
def mais(c,f):return tuple(min(255,int(v*f)) for v in c)
def finalizar(T):
    a=T.a;pre=T.rgb*a[...,None];h,w=T.H//SS,T.W//SS
    pre=cv2.resize(pre[:h*SS,:w*SS],(w,h),interpolation=cv2.INTER_AREA);al=cv2.resize(a[:h*SS,:w*SS],(w,h),interpolation=cv2.INTER_AREA)
    rgb=pre/np.maximum(al[...,None],1e-4);return np.dstack([np.clip(rgb,0,255),np.clip(al*255,0,255)]).astype(np.uint8)

# ------------------------------------------------------------------ passeio / utilitários
def _rodas(T,xs,B,larg=.2,comp=.78):
    for x in xs:
        for sd in (-1,1):
            y0,y1=sorted((sd*(B/2-larg),sd*(B/2)));sombrear(T,T.mask(retangulo(x-comp/2,x+comp/2,y0,y1,.07)),(26,26,28),.4,.1,.5,borda=False)
def _luzes(T,L,B,faro=(236,240,244)):
    for sd in (-1,1):
        y=sd*(B/2-.27);f=retangulo(L/2-.30,L/2-.04,y-.12,y+.12,.07)
        sombrear(T,T.mask(f),faro,1.0,.4,.7,borda=False)
        lt=np.array([(-L/2+.04,y-.20),(-L/2+.30,y-.17),(-L/2+.36,y+.14),(-L/2+.04,y+.20)]);sombrear(T,T.mask(retangulo(-L/2+.03,-L/2+.2,y-.17,y+.17,.06)),(188,26,26),1.0,.35,.7,borda=False)
def _espelhos(T,x,B,cor):
    for sd in (-1,1):
        e=superelipse(x-.12,x+.09,.2,2.4,2.4,24,dy=sd*(B/2-.10));sombrear(T,T.mask(e),mais(cor,.9),1.0,.3,.6,borda=False)

def passeio(T,key,L,B,cor):
    ro={'hatch':(.24,.06),'sedan':(.26,.27),'suv':(.25,.05)}.get(key,(.25,.2))
    _rodas(T,[L*.31,-L*.31],B)
    body=T.mask(superelipse(-L/2,L/2,B-.04,3.9,4.2));sombrear(T,body,cor,.42,.38,.46)
    cab1=L/2-L*ro[0];cab0=-L/2+L*ro[1]+.1
    gh=T.mask(superelipse(cab0,cab1+.12,B*.74,5.0,3.6,96));vidro(T,gh)
    rf=T.mask(superelipse(cab0+.34,cab1-.70,B*.66,4.2,3.4,96));sombrear(T,rf,mais(cor,1.04),.55,.5,.55)
    if key in('suv','hatch'):
        sr=T.mask(retangulo((cab0+cab1)/2-.55,(cab0+cab1)/2+.5,-B*.20,B*.20,.07));vidro(T,sr,.18)
    if key=='suv':
        for sd in (-1,1):T.mask_clip=None;T.linha((cab0+.45,sd*B*.30),(cab1-.7,sd*B*.30),(24,24,26),.05)
    for x in (cab1-.60,cab0+.45):                                                 # frestas de portas
        for sd in (-1,1):T.mask_clip=None;T.linha((x,sd*(B/2-.04)),(x,sd*B*.33),mais(cor,.5),.014,.8)
    for sd in (-1,1):T.mask_clip=None;T.linha((cab1+.2,sd*B*.17),(L/2-.35,sd*B*.12),mais(cor,.7),.014,.7)   # vincos do capô
    T.mask_clip=None;T.linha((L/2-.06,-B*.30),(L/2-.06,B*.30),(24,24,28),.05,.8);T.linha((-L/2+.05,-B*.28),(-L/2+.05,B*.28),(28,28,32),.05,.85)
    _luzes(T,L,B);_espelhos(T,cab1-.42,B,cor)
    cor_lisa(T,T.mask(retangulo(-L/2+.03,-L/2+.07,-.26,.26,.01)),(236,236,230))

def utilitario(T,key,L,B,cor):
    _rodas(T,[L*.30,-L*.30],B)
    body=T.mask(superelipse(-L/2,L/2,B-.04,3.4,4.5));sombrear(T,body,cor,.4,.36,.46)
    if key=='pickup':
        cab1=L/2-L*.26;sombrear(T,T.mask(retangulo(-L/2+.14,-.1,-B/2+.2,B/2-.2,.06)),mais(cor,.38),.3,.15,.5)      # caçamba
        gh=T.mask(superelipse(.05,cab1+.05,B*.78,4,3.2));vidro(T,gh);sombrear(T,T.mask(superelipse(.5,cab1-.85,B*.6,3.5,3.2)),mais(cor,1.04),.55,.5,.55)
        for sd in (-1,1):T.mask_clip=None;T.linha((-L/2+.14,sd*(B/2-.2)),(-.1,sd*(B/2-.2)),mais(cor,1.2),.05)
        _espelhos(T,cab1-.8,B,cor)
    else:
        sombrear(T,T.mask(retangulo(-L/2+.32,L/2-1.45,-B/2+.2,B/2-.2,.14)),mais(cor,1.06),.5,.45,.55)
        vidro(T,T.mask(superelipse(L/2-1.5,L/2-.35,B*.8,3.6,3.4)))
        for sd in (-1,1):vidro(T,T.mask(retangulo(L/2-3.0,L/2-1.6,sd*(B/2-.17)-.06,sd*(B/2-.17)+.06,.03)),.2)
        _espelhos(T,L/2-1.6,B,cor)
    _luzes(T,L,B)

# ------------------------------------------------------------------ pesados
def caminhao(T,key,L,B,cor):
    cab=2.3 if key not in('toco','cacamba') else 2.5;xc=L/2-cab;branco=(236,236,230) if sum(cor)<330 else cor
    _rodas(T,[xc+.9,-L/2+1.2,-L/2+2.4] if L>7 else [xc+.9,-L/2+1.2],B,.3,1.0)
    sombrear(T,T.mask(retangulo(-L/2,xc-.05,-B/2+.1,B/2-.1,.04)),(58,60,64),.3,.1,.5,borda=False)           # chassi
    if key=='cacamba':
        sombrear(T,T.mask(retangulo(-L/2,xc-.08,-B/2,B/2,.1)),mais(cor,.92),.25,.35,.5);sombrear(T,T.mask(retangulo(-L/2+.2,xc-.3,-B/2+.2,B/2-.2,.05)),mais(cor,.36),.3,.1,.5)
    else:
        sombrear(T,T.mask(retangulo(-L/2,xc-.08,-B/2,B/2,.12)),branco,.25,.42,.5)
        for f in np.arange(-L/2+.9,xc-.4,.9):T.mask_clip=None;T.linha((f,-B/2+.1),(f,B/2-.1),mais(branco,.82),.025)
        T.mask_clip=None;T.linha((-L/2+.04,-B/2+.2),(-L/2+.04,B/2-.2),(110,110,106),.05)
    sombrear(T,T.mask(superelipse(xc,L/2,B-.05,3.0,5.0)),cor,.45,.4,.48)
    vidro(T,T.mask(superelipse(L/2-.75,L/2-.12,B*.80,3.4,3.4)));sombrear(T,T.mask(superelipse(xc+.5,L/2-.85,B*.72,3.8,3.4)),mais(cor,1.08),.5,.45,.55)
    _espelhos(T,L/2-.9,B,cor)
    for sd in (-1,1):
        y=sd*(B/2-.24);sombrear(T,T.mask(retangulo(L/2-.2,L/2-.03,y-.13,y+.13,.03)),(240,240,230),.5,.4,.6,borda=False)
        sombrear(T,T.mask(retangulo(-L/2,-L/2+.1,y-.1,y+.1,.03)),(190,28,28),.5,.3,.6,borda=False)

def onibus(T,key,L,B,cor):
    _rodas(T,[L/2-1.3,-L/2+1.6,-L/2+2.9] if L>10 else [L/2-1.3,-L/2+1.3],B,.3,1.0)
    sombrear(T,T.mask(superelipse(-L/2,L/2,B-.04,4.0,6.0)),cor,.3,.38,.5)
    for sd in (-1,1):vidro(T,T.mask(retangulo(-L/2+1.0,L/2-1.4,sd*(B/2-.14)-.12,sd*(B/2-.14)+.12,.06)),.22)
    vidro(T,T.mask(superelipse(L/2-.95,L/2-.1,B*.84,3.0,3.0)))
    sombrear(T,T.mask(retangulo(-L/2+.5,L/2-1.15,-B/2+.46,B/2-.46,.2)),mais(cor,1.1),.4,.45,.55)
    for x in (.12,.5):sombrear(T,T.mask(retangulo(-L/2+L*x-.55,-L/2+L*x+.55,-.45,.45,.1)),(214,216,212),.4,.4,.6,borda=False)
    sombrear(T,T.mask(retangulo(-L/2+.12,-L/2+.62,-B/2+.55,B/2-.55,.06)),mais(cor,.7),.4,.2,.5,borda=False)
    _espelhos(T,L/2-.85,B,cor)
    for sd in (-1,1):
        y=sd*(B/2-.22);sombrear(T,T.mask(retangulo(L/2-.2,L/2-.03,y-.14,y+.14,.03)),(240,240,230),.5,.4,.6,borda=False);sombrear(T,T.mask(retangulo(-L/2,-L/2+.09,y-.12,y+.12,.03)),(190,28,28),.5,.3,.6,borda=False)

def carreta(T,key,L,B,cor):
    cab=3.0;xc=L/2-cab;dois=key=='bitrem';lona=(236,236,230) if sum(cor)<330 else cor
    _rodas(T,[xc+.9,xc-.9,-L/2+1.2,-L/2+2.5]+([-L/2+(L-cab)*.5+.5,-L/2+(L-cab)*.5+1.7] if dois else []),B,.3,1.0)
    sombrear(T,T.mask(retangulo(-L/2,xc,-B/2+.2,B/2-.2,.03)),(52,54,58),.3,.1,.5,borda=False)
    cortes=[(-L/2,-L/2+(L-cab)*.5-.3),(-L/2+(L-cab)*.5+.3,xc-.15)] if dois else [(-L/2,xc-.15)]
    for a,b in cortes:
        sombrear(T,T.mask(retangulo(a,b,-B/2,B/2,.1)),lona,.22,.40,.5)
        for f in np.arange(a+.8,b-.3,.8):T.mask_clip=None;T.linha((f,-B/2+.08),(f,B/2-.08),mais(lona,.84),.025)
        T.mask_clip=None;T.linha((a+.04,-B/2+.2),(a+.04,B/2-.2),(110,110,106),.05)
    cc=(176,40,36) if sum(cor)>=330 else (226,226,220)
    sombrear(T,T.mask(superelipse(xc,L/2,B-.12,3.0,5.0)),cc,.45,.4,.48)
    vidro(T,T.mask(superelipse(L/2-.8,L/2-.12,B*.78,3.4,3.4)));sombrear(T,T.mask(superelipse(xc+.4,L/2-.9,B*.7,3.8,3.4)),mais(cc,1.08),.5,.45,.55)
    _espelhos(T,L/2-.85,B,cc)
    for sd in (-1,1):
        y=sd*(B/2-.25);sombrear(T,T.mask(retangulo(L/2-.2,L/2-.03,y-.13,y+.13,.03)),(240,240,230),.5,.4,.6,borda=False);sombrear(T,T.mask(retangulo(-L/2,-L/2+.1,y-.1,y+.1,.03)),(190,28,28),.5,.3,.6,borda=False)

def moto(T,key,L,B,cor):
    sombrear(T,T.mask(retangulo(-L/2,-L/2+.62,-.09,.09,.08)),(24,24,26),.4,.1,.5,borda=False);sombrear(T,T.mask(retangulo(L/2-.62,L/2,-.09,.09,.08)),(24,24,26),.4,.1,.5,borda=False)
    sombrear(T,T.mask(retangulo(-L/2+.45,L/2-.45,-.1,.1,.08)),(66,66,70),.4,.2,.5)
    sombrear(T,T.mask(superelipse(-.1,.55,.34,2.6,2.6)),cor,.6,.5,.5);sombrear(T,T.mask(retangulo(-.6,-.1,-.17,.17,.1)),(32,32,34),.5,.2,.5)
    T.mask_clip=None;T.linha((.5,-B/2+.02),(.5,B/2-.02),(70,70,74),.05)
    sombrear(T,T.mask(superelipse(-.35,.12,min(.5,B-.1),2.4,2.4)),(44,52,74),.6,.3,.5);sombrear(T,T.mask(superelipse(-.34,-.06,.26,2.2,2.2)),(236,236,232),.7,.6,.5)

def _desenha(style,key,cor,L,B,ppm):
    T=Tela(L,B,ppm)
    if style=='car':passeio(T,key,L,B,cor)
    elif style in('van','pickup'):utilitario(T,style,L,B,cor)
    elif style=='truck':caminhao(T,key,L,B,cor)
    elif style=='bus':onibus(T,key,L,B,cor)
    elif style=='carreta':carreta(T,key,L,B,cor)
    elif style=='moto':moto(T,key,L,B,cor)
    else:return None
    return finalizar(T)

def obter(key,style,cor,L,B,ppm_necessario):
    b=next((x for x in BUCKETS if x>=ppm_necessario),BUCKETS[-1]);k=(key,style,tuple(int(c) for c in cor),round(L,2),round(B,2),b)
    s=_CACHE.get(k)
    if s is None:
        if len(_CACHE)>=_MAX:_CACHE.pop(next(iter(_CACHE)))
        s=_desenha(style,key,cor,L,B,b);_CACHE[k]=s
    return s,b

def blit(im,pt,tan,key,style,cor,screen,mpp,L,B):
    """Desenha o sprite alinhado à pose real (centro pt, rumo tan). Retorna False se não deve/pode desenhar."""
    if L/mpp<12:return False
    need=1.0/mpp;sp,b=obter(key,style,cor,L,B,need)
    if sp is None:return False
    pt=np.asarray(pt,float);tan=np.asarray(tan,float);n=np.array([-tan[1],tan[0]])
    c=np.asarray(screen(np.array([pt,pt+tan,pt+n])),float);o=c[0];ex=c[1]-c[0];ey=c[2]-c[0]          # px por metro ao longo de tan e de n
    h,w=sp.shape[:2];pad=3/ SS if False else 0
    # pixel do sprite (u,v) -> metros locais: x=(u+.5)/b-(w/2)/b..., a tela foi criada com margem de 3 subpixels SS e depois reduzida: centro do sprite = centro do veículo
    cu,cv_=w/2.,h/2.;M=np.array([[ex[0]/b,ey[0]/b,o[0]-ex[0]*cu/b-ey[0]*cv_/b],[ex[1]/b,ey[1]/b,o[1]-ex[1]*cu/b-ey[1]*cv_/b]],np.float64)
    corners=np.array([[0,0,1],[w,0,1],[w,h,1],[0,h,1]],float)@M.T;x0,y0=np.floor(corners.min(0)).astype(int)-1;x1,y1=np.ceil(corners.max(0)).astype(int)+1
    H,W=im.shape[:2]
    if x1<0 or y1<0 or x0>=W or y0>=H:return True
    x0c,y0c,x1c,y1c=max(x0,0),max(y0,0),min(x1,W),min(y1,H);M2=M.copy();M2[0,2]-=x0c;M2[1,2]-=y0c
    pre=sp.astype(np.float32);pre[...,:3]*=pre[...,3:4]/255.
    out=cv2.warpAffine(pre,M2,(x1c-x0c,y1c-y0c),flags=cv2.INTER_AREA if min(np.linalg.norm(ex),np.linalg.norm(ey))/b<.75 else cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
    a=out[...,3:4]/255.;roi=im[y0c:y1c,x0c:x1c].astype(np.float32);im[y0c:y1c,x0c:x1c]=np.clip(roi*(1-a)+out[...,:3],0,255).astype(np.uint8)
    return True
