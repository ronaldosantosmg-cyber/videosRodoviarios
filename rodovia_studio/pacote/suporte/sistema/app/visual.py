"""Qualidade visual (1.5): textura de asfalto em metros, concreto de OAE, água em camadas e veículos por tipo.

Todas as texturas são ancoradas em coordenadas do projeto (não "nadam" com a câmera) e usam
uma pirâmide pré-filtrada: com zoom aberto, a textura é suavizada em vez de cintilar.
O modo 'classic' mantém o desenho da 1.4 sem alterações.
"""
import math
import numpy as np
import cv2

TEX=512           # texels por lado do ladrilho
TEXEL_M=.04       # 4 cm por texel: ladrilho de 20,48 m
MICRO_M=.02       # 1.19: abaixo disso entra o grão fino

def _tileable_noise(seed,octaves=((8,.45),(32,.3),(128,.18),(256,.07))):
    rng=np.random.default_rng(seed);out=np.zeros((TEX,TEX),np.float32)
    for cells,w in octaves:
        g=rng.standard_normal((cells,cells)).astype(np.float32)
        # Interpolação periódica: a borda do ladrilho continua no lado oposto.
        big=np.tile(g,(3,3));up=cv2.resize(big,(TEX*3,TEX*3),interpolation=cv2.INTER_CUBIC)[TEX:2*TEX,TEX:2*TEX]
        out+=w*up
    out-=out.mean();out/=max(float(out.std()),1e-6)
    return out

class Texture:
    """Ruído ladrilhável com níveis pré-filtrados, amostrado por transformação afim tela->mundo."""
    def __init__(self,seed,octaves=None,base=None):
        if base is None:base=_tileable_noise(seed,octaves) if octaves else _tileable_noise(seed)
        self.levels=[base]
        F=np.fft.rfft2(base);fy=np.fft.fftfreq(TEX)[:,None];fx=np.fft.rfftfreq(TEX)[None,:]
        for k in range(1,9):
            # Nível k: suavização ~1 pixel da tela quando o pixel mede 2^k texels (gaussiana periódica via FFT).
            s=2**k*.6;g=np.exp(-2*(np.pi*s)**2*(fx**2+fy**2))
            self.levels.append(np.fft.irfft2(F*g,s=base.shape).astype(np.float32))
    def sample(self,screen_to_world,shape,m_per_px):
        """screen_to_world: matriz 2x3 (px da tela -> metros). Retorna ruído (H,W) ~N(0,1) suavizado pelo zoom."""
        level=int(np.clip(math.ceil(math.log2(max(m_per_px/TEXEL_M,1))-1e-9),0,len(self.levels)-1))
        M=np.vstack([screen_to_world,[0,0,1]]);T=np.array([[1/TEXEL_M,0,0],[0,-1/TEXEL_M,0],[0,0,1]])
        A=(T@M)[:2]
        # Coordenadas grandes (UTM) perdem precisão em float32: reduz a translação ao período do ladrilho antes.
        A[:,2]=np.mod(A[:,2],TEX);A=A.astype(np.float32)
        out=cv2.warpAffine(self.levels[level],A,(shape[1],shape[0]),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_WRAP)
        # Atenuação: em zoom muito aberto o grão some, sem virar ruído de pixel.
        out=out*float(np.clip(1.4-0.25*level,0.15,1))
        if m_per_px<MICRO_M:
            # 1.19: vista muito próxima (poucos metros na tela): grão fino de 5 mm por texel, para a textura não
            # virar um borrão. Só abaixo de 2 cm por pixel — vídeos e prévias anteriores não mudam.
            w=float(np.clip((MICRO_M-m_per_px)/.012,0,1))*.55
            Tm=np.array([[8/TEXEL_M,0,0],[0,-8/TEXEL_M,0],[0,0,1]]);B=(Tm@M)[:2];B[:,2]=np.mod(B[:,2],TEX)
            lv=int(np.clip(math.ceil(math.log2(max(m_per_px*8/TEXEL_M,1))-1e-9),0,len(self.levels)-1))
            out=out+w*cv2.warpAffine(self.levels[lv],B.astype(np.float32),(shape[1],shape[0]),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_WRAP)
        return out

_ASPHALT=None;_CONCRETE=None;_WATER=None;_GRASS=None;_ASPHALT_F=None;_CONCRETE_F=None
def asphalt_fino():
    """1.34: asfalto do estilo artístico: predominam os grãos finos (o asfalto real não tem manchas de 2–5 m)."""
    global _ASPHALT_F
    if _ASPHALT_F is None:_ASPHALT_F=Texture(58,((16,.12),(64,.28),(256,.6)))
    return _ASPHALT_F
def concrete_fino():
    global _CONCRETE_F
    if _CONCRETE_F is None:_CONCRETE_F=Texture(12,((16,.12),(64,.3),(256,.58)))
    return _CONCRETE_F
def asphalt():
    global _ASPHALT
    if _ASPHALT is None:_ASPHALT=Texture(57)
    return _ASPHALT
def grass():
    global _GRASS
    if _GRASS is None:_GRASS=Texture(23,((16,.25),(64,.35),(256,.4)))
    return _GRASS
def concrete():
    global _CONCRETE
    if _CONCRETE is None:_CONCRETE=Texture(11,((4,.5),(16,.3),(64,.15),(256,.05)))
    return _CONCRETE

# Classes de superfície no raster auxiliar (6/7: taludes; 8: trilha de roda na pista existente, só no detalhe).
SURF={'pavement':1,'existing_pavement':2,'oae':3,'shoulder':4,'median':5}
EARTH_SURF={'cut':6,'fill':7}  # só com taludes 'naturais'

# ---------------- 1.16: texturas realistas ----------------
_SPECKLE=None;_CRACK=None;_SOIL=None
def speckle():
    """Agregado do asfalto: grão fino (4–16 cm)."""
    global _SPECKLE
    if _SPECKLE is None:_SPECKLE=Texture(91,((128,.25),(256,.75)))
    return _SPECKLE
def soil():
    global _SOIL
    if _SOIL is None:_SOIL=Texture(37,((8,.35),(32,.3),(128,.2),(256,.15)))
    return _SOIL
def cracks():
    """Fissuras ladrilháveis (contornos de células irregulares, com falhas), 0..1."""
    global _CRACK
    if _CRACK is None:
        rng=np.random.default_rng(5);n=70;pts=rng.uniform(0,TEX,(n,2))
        img=np.zeros((TEX,TEX),np.int32)
        yy,xx=np.mgrid[0:TEX,0:TEX].astype(np.float32);best=np.full((TEX,TEX),1e9,np.float32)
        for k,(px,py) in enumerate(pts):
            for ox in (-TEX,0,TEX):
                for oy in (-TEX,0,TEX):
                    d=(xx-px-ox)**2+(yy-py-oy)**2;sel=d<best;best[sel]=d[sel];img[sel]=k
        edge=((img!=np.roll(img,1,0))|(img!=np.roll(img,1,1))).astype(np.float32)
        gap=_tileable_noise(77,((16,1.),))>.35;edge*=~gap
        warp=cv2.GaussianBlur(edge,(0,0),.7);warp/=max(float(warp.max()),1e-6)
        t=Texture(0,base=warp-warp.mean());t.levels=[l+warp.mean() for l in t.levels];_CRACK=t
    return _CRACK

_R_SPK=np.zeros(256,np.float32);_R_SPK[[1,2,3,4,6,8]]=(.055,.06,.03,.07,.05,.03)
_R_PATCH=np.zeros(256,np.float32);_R_PATCH[[2,8]]=(.09,.05)
_R_CRACK=np.zeros(256,np.float32);_R_CRACK[2]=.32
_R_SHIFT=np.zeros(256,np.float32);_R_SHIFT[[4,8]]=(.03,-.07)

def shade_realistic(im,surface,s2w,m_per_px,valid,lut=None):
    """Camada extra das texturas 1.16: agregado, remendos e fissuras na pista existente, trilhas de roda,
    acostamento mais claro e solo/grama nos taludes. Ancorada em metros (não 'nada' com a câmera).
    1.24: 'lut' traz as intensidades editadas pelo usuário (None = padrão)."""
    L=lut or DEFAULT_LUT;_R_SPK,_R_PATCH,_R_CRACK,_R_SHIFT=L['spk'],L['patch'],L['crack'],L['shift']
    S=np.where(valid,surface,0).astype(np.uint8)
    rows=np.flatnonzero((S>0).any(1))
    if not len(rows):return
    y0,y1=rows[0],rows[-1]+1;cols=np.flatnonzero((S[y0:y1]>0).any(0));x0,x1=cols[0],cols[-1]+1
    S=S[y0:y1,x0:x1];shape=S.shape;A=_crop(s2w,x0,y0);F=np.ones(shape,np.float32)
    spk=_R_SPK[S]
    if spk.any():F+=spk*speckle().sample(A,shape,m_per_px)
    pt=_R_PATCH[S]
    if pt.any():
        k=8;small=(max(1,shape[0]//k),max(1,shape[1]//k));As=A.copy();As[:,:2]*=k
        low=cv2.resize(soil().sample(As*np.array([[.12],[.12]]),small,m_per_px*k*.12),(shape[1],shape[0]),interpolation=cv2.INTER_LINEAR)
        F-=pt*np.clip(low*1.4-.9,0,1)
    cr=_R_CRACK[S]
    if cr.any() and m_per_px<.25:F-=cr*np.clip(cracks().sample(A,shape,m_per_px),0,1)*float(np.clip((.25-m_per_px)/.15,0,1))
    F+=_R_SHIFT[S]
    roi=im[y0:y1,x0:x1];out=roi.astype(np.float32)*F[:,:,None]
    cut=S==6;fil=S==7
    if cut.any():
        n=soil().sample(A,shape,m_per_px);out*=(1+.10*n*cut)[:,:,None];out[:,:,0]+=cut*4*n
    if fil.any():
        n=grass().sample(A,shape,m_per_px)*fil;out*=(1+.14*n)[:,:,None];out[:,:,1]+=fil*(5+5*n)
    roi[:]=np.clip(out,0,255).astype(np.uint8)

_LUT_GRAIN=np.zeros(256,np.float32);_LUT_GRAIN[[1,2,4]]=(.075,.045,.05)
_LUT_TONE=np.zeros(256,np.float32);_LUT_TONE[[1,2,4]]=(.035,.03,.02)
_LUT_CONC=np.zeros(256,np.float32);_LUT_CONC[3]=.06

def _crop(s2w,x0,y0):
    A=np.array(s2w,float);A[:,2]=A[:,2]+A[:,0]*x0+A[:,1]*y0;return A

def shade_surface(im,surface,s2w,m_per_px,valid,grass_on=True,lut=None,arte=False):
    """Modula pavimento (grão e tom), via existente (mais clara e lisa), acostamento e OAE (concreto)."""
    L=lut or DEFAULT_LUT;_LUT_GRAIN,_LUT_TONE,_LUT_CONC=L['grain'],L['tone'],L['conc']
    if L.get('bright') is not None:
        # 1.24: brilho/tom editado por superfície (só quando o usuário altera).
        B=L['bright'][surface];B[~valid]=0
        if B.any():im[:]=np.clip(im.astype(np.float32)*(1+B[:,:,None]),0,255).astype(np.uint8)
    g=_LUT_GRAIN[surface];c=_LUT_CONC[surface];g[~valid]=0;c[~valid]=0
    gr=((surface==5)&valid) if grass_on else np.zeros(surface.shape,bool)
    rows=np.flatnonzero((g>0).any(1)|(c>0).any(1)|gr.any(1))
    if not len(rows):return
    cols=np.flatnonzero((g[rows[0]:rows[-1]+1]>0).any(0)|(c[rows[0]:rows[-1]+1]>0).any(0)|gr[rows[0]:rows[-1]+1].any(0))
    y0,y1,x0,x1=rows[0],rows[-1]+1,cols[0],cols[-1]+1;shape=(y1-y0,x1-x0)
    A=_crop(s2w,x0,y0);G=g[y0:y1,x0:x1];F=np.ones(shape,np.float32)
    tx_a,tx_c=(asphalt_fino(),concrete_fino()) if arte else (asphalt(),concrete())   # 1.34: artístico = grão fino, sem “nuvens”
    if G.any():
        F+=G*tx_a.sample(A,shape,m_per_px)
        # Variação de tom em grande escala: amostrada em 1/8 e ampliada (barato e suave).
        k=8;small=(max(1,shape[0]//k),max(1,shape[1]//k));As=A.copy();As[:,:2]*=k
        tone=cv2.resize(asphalt().sample(As*np.array([[.07],[.07]]),small,m_per_px*k*.07),(shape[1],shape[0]),interpolation=cv2.INTER_LINEAR)
        F+=_LUT_TONE[surface[y0:y1,x0:x1]]*(G>0)*tone*(.45 if arte else 1)
    C=c[y0:y1,x0:x1]
    if C.any():F+=C*tx_c.sample(A,shape,m_per_px)
    GR=gr[y0:y1,x0:x1];roi=im[y0:y1,x0:x1]
    if GR.any():
        # Grama do canteiro (1.10): textura em metros com leve variação de verde.
        n=grass().sample(A,shape,m_per_px)*GR;F+=float(L.get('grass',.16))*n
        out=roi.astype(np.float32)*F[:,:,None];out[:,:,1]+=GR*(6+5*n);roi[:]=np.clip(out,0,255).astype(np.uint8);return
    roi[:]=np.clip(roi.astype(np.float32)*F[:,:,None],0,255).astype(np.uint8)

def oae_details(im,joints,rails,screen,m_per_px):
    """Juntas de dilatação e guarda-corpos (vetoriais, nítidos em qualquer zoom)."""
    w=max(1,round(.22/m_per_px))
    for seg in joints:
        q=screen(seg).astype(np.int32);cv2.line(im,tuple(q[0]),tuple(q[1]),(98,100,98),w,cv2.LINE_AA)
    for rail in rails:
        q=screen(rail).astype(np.int32)
        cv2.polylines(im,[q],False,(70,72,70),max(1,round(.55/m_per_px)),cv2.LINE_AA)
        cv2.polylines(im,[q],False,(232,231,224),max(1,round(.32/m_per_px)),cv2.LINE_AA)

def cast_shadow(im,ring,level_m,screen,alpha=.32,dir=(.35,-.55)):
    """Sombra da OAE no terreno, deslocada pelo nível (sol fixo a noroeste)."""
    if level_m<=0:return
    shift=np.asarray(dir,float)*level_m;sh=screen(ring+shift).astype(np.int32);deck=screen(ring).astype(np.int32)
    x0,y0=np.minimum(sh.min(0),deck.min(0));x1,y1=np.maximum(sh.max(0),deck.max(0))
    H,W=im.shape[:2];x0=max(0,x0-3);y0=max(0,y0-3);x1=min(W,x1+3);y1=min(H,y1+3)
    if x1<=x0 or y1<=y0:return
    m=np.zeros((y1-y0,x1-x0),np.uint8);cv2.fillPoly(m,[sh-[x0,y0]],255,cv2.LINE_AA);cv2.fillPoly(m,[deck-[x0,y0]],0,cv2.LINE_AA)
    m=cv2.GaussianBlur(m,(0,0),1.2)
    roi=im[y0:y1,x0:x1];f=(1-alpha*m.astype(np.float32)/255)[:,:,None];roi[:]=(roi*f).astype(np.uint8)

# ---------------- Água ----------------
def water_paint(image,mask,worldpx_scale,opacity,enhanced):
    """Textura da água só dentro dos polígonos existentes. mask: 0..255 por pixel do mosaico."""
    ys,xs=np.nonzero(mask)
    if not len(xs):return
    if not enhanced:
        blue=np.zeros((len(xs),3),np.float32);blue[:]=(42,128,185)
        blue+=((np.sin(xs*.19+ys*.055)+np.cos(ys*.23))*5)[:,None]
        alpha=(mask[ys,xs]/255*opacity)[:,None]
        image[ys,xs]=np.clip(image[ys,xs]*(1-alpha)+blue*alpha,0,255).astype(np.uint8);return
    # Borda suave: a opacidade cresce nos primeiros ~6 m a partir da margem mapeada.
    inside=(mask>127).astype(np.uint8);dist=cv2.distanceTransform(inside,cv2.DIST_L2,3)*worldpx_scale
    edge=np.clip(dist/6.,0,1)[ys,xs];edge=edge*edge*(3-2*edge)
    m=worldpx_scale
    tone=(np.sin(xs*m*.021+ys*m*.013)*.5+np.sin(xs*m*.0071-ys*m*.0093)*.5)
    deep=np.clip(dist[ys,xs]/40.,0,1)
    blue=np.empty((len(xs),3),np.float32)
    blue[:,0]=36-10*deep+5*tone;blue[:,1]=112-22*deep+7*tone;blue[:,2]=168-18*deep+6*tone
    # Brilho discreto: faixas finas e esparsas, fixas no terreno.
    glint=np.clip(np.sin(xs*m*.35+np.sin(ys*m*.05)*3)*np.sin(ys*m*.27+xs*m*.02),0,1)**12
    blue+=glint[:,None]*np.array([60,62,58],np.float32)*(.4+.6*deep[:,None])
    alpha=(np.maximum(edge,.25)*opacity*(mask[ys,xs]/255))[:,None]
    image[ys,xs]=np.clip(image[ys,xs]*(1-alpha)+blue*alpha,0,255).astype(np.uint8)

def water_ripple(view,water_mask_screen,s2w,t,strength=7.):
    """Ondulação animada sutil (opcional): só dentro da água visível."""
    sel=water_mask_screen>0
    if not sel.any():return
    ys,xs=np.nonzero(sel);x=s2w[0,0]*xs+s2w[0,1]*ys+s2w[0,2];y=s2w[1,0]*xs+s2w[1,1]*ys+s2w[1,2]
    x=np.mod(x,1000.);y=np.mod(y,1000.)
    r=np.sin(x*.9+t*1.6)*np.sin(y*.7-t*1.1)+.6*np.sin((x+y)*.35+t*.8)
    k=(water_mask_screen[ys,xs]/255.)*strength*r
    view[ys,xs]=np.clip(view[ys,xs].astype(np.float32)+k[:,None],0,255).astype(np.uint8)

# ---------------- Veículos ----------------
CAR_COLORS=[(236,236,232),(196,199,200),(58,60,64),(142,30,34),(36,62,112),(118,122,126),(214,206,186),(28,92,74),(232,192,115),(132,183,205)]
TYPES={'car':{'L':4.5,'B':1.8,'H':1.5},'truck':{'L':12.,'B':3.0,'H':3.6},'bus':{'L':12.4,'B':3.0,'H':3.3},
       # 1.37 (frota variada)
       'moto':{'L':2.1,'B':.8,'H':1.3},'van':{'L':5.4,'B':1.8,'H':2.4},'carreta':{'L':18.6,'B':3.0,'H':4.0},'pickup':{'L':5.3,'B':1.8,'H':1.8}}

def vehicle_type(path_kinds,identity,mix='classico'):
    i,k,cycle=identity;h=(i*7919+k*104729+cycle*31)%100
    if mix=='variado':
        # 1.37: frota variada (proporções típicas de rodovia; motos e vans também nos ramos).
        if not set(path_kinds)&{'main','marginal'}:return 'moto' if h<9 else 'van' if h<15 else 'pickup' if h<27 else 'car'
        return 'carreta' if h<9 else 'truck' if h<18 else 'bus' if h<24 else 'moto' if h<32 else 'van' if h<38 else 'pickup' if h<50 else 'car'
    if not set(path_kinds)&{'main','marginal'}:return 'car'
    return 'truck' if h<16 else 'bus' if h<26 else 'car'

def vehicle_color(identity,vtype):
    i,k,cycle=identity;h=(i*31+k*17+cycle*7)%len(CAR_COLORS)
    if vtype=='bus':return [(226,226,214),(204,64,48),(38,104,170),(240,190,40)][h%4]
    if vtype=='carreta':return [(236,236,230),(30,90,160),(170,36,34),(60,120,70),(210,210,200)][h%5]
    if vtype=='van':return [(240,240,236),(220,220,214),(40,60,90),(170,170,170)][h%4]
    if vtype=='moto':return [(20,20,22),(190,30,30),(30,60,150),(230,230,230)][h%4]
    if vtype=='truck':return [(238,238,232),(176,40,36),(46,84,140),(220,220,210),(90,96,100)][h%5]
    return CAR_COLORS[h]

def body(pt,tan,L,B,x0=None,x1=None):
    n=np.array([-tan[1],tan[0]]);a=-L/2 if x0 is None else x0;b=L/2 if x1 is None else x1
    return np.array([pt+tan*a-n*B/2,pt+tan*b-n*B/2,pt+tan*b+n*B/2,pt+tan*a+n*B/2])

def draw_vehicle(im,pt,tan,vtype,color,screen,m_per_px,shadow_layer=None):
    T=TYPES[vtype];L,B=T['L'],T['B'];n=np.array([-tan[1],tan[0]])
    def P(poly):return screen(poly).astype(np.int32)
    # Sombra suave projetada (sol a noroeste), proporcional à altura.
    sh=body(pt+np.array([.25,-.38])*T['H'],tan,L*1.02,B*1.05)
    cv2.fillPoly(shadow_layer if shadow_layer is not None else im,[P(sh)],(0,0,0) if shadow_layer is None else 255,cv2.LINE_AA)
    dark=tuple(int(c*.72) for c in color)
    if vtype=='car':
        cv2.fillPoly(im,[P(body(pt,tan,L,B))],dark,cv2.LINE_AA)
        cv2.fillPoly(im,[P(body(pt,tan,L-.18,B-.18))],color,cv2.LINE_AA)
        cv2.fillPoly(im,[P(body(pt,tan,0,B-.42,.35,1.25))],(46,66,80),cv2.LINE_AA)   # para-brisa
        cv2.fillPoly(im,[P(body(pt,tan,0,B-.5,-1.75,-1.05))],(46,66,80),cv2.LINE_AA)  # vidro traseiro
        roof=tuple(min(255,int(c*1.06)+6) for c in color);cv2.fillPoly(im,[P(body(pt,tan,0,B-.55,-1.0,.3))],roof,cv2.LINE_AA)
    elif vtype=='truck':
        cv2.fillPoly(im,[P(body(pt,tan,0,B,-L/2,L/2-2.6))],(214,214,206) if color[0]<100 else color,cv2.LINE_AA)  # baú
        for f in np.arange(-L/2+1.2,L/2-2.8,1.2):
            q=P(np.array([pt+tan*f-n*B/2,pt+tan*f+n*B/2]));cv2.line(im,tuple(q[0]),tuple(q[1]),(170,170,162),1,cv2.LINE_AA)
        cv2.fillPoly(im,[P(body(pt,tan,0,B-.1,L/2-2.4,L/2))],color,cv2.LINE_AA)  # cabine
        cv2.fillPoly(im,[P(body(pt,tan,0,B-.45,L/2-.9,L/2-.35))],(46,66,80),cv2.LINE_AA)
    elif vtype=='moto':
        cv2.fillPoly(im,[P(body(pt,tan,L,.34))],(30,30,32),cv2.LINE_AA)                                  # rodas e quadro
        cv2.fillPoly(im,[P(body(pt,tan,0,.62,-.55,.45))],color,cv2.LINE_AA)                                # tanque/carenagem
        hd=pt-tan*.25;r=max(1,int(round(.2/m_per_px)));c=tuple(np.rint(screen(hd[None])[0]).astype(int));cv2.circle(im,c,r,(230,230,226),-1,cv2.LINE_AA)  # capacete
        q=P(np.array([pt+tan*.55-n*.42,pt+tan*.55+n*.42]));cv2.line(im,tuple(q[0]),tuple(q[1]),(60,60,62),max(1,round(.08/m_per_px)),cv2.LINE_AA)  # guidão
    elif vtype in ('van','pickup'):
        cv2.fillPoly(im,[P(body(pt,tan,L,B))],dark,cv2.LINE_AA);cv2.fillPoly(im,[P(body(pt,tan,L-.18,B-.18))],color,cv2.LINE_AA)
        cv2.fillPoly(im,[P(body(pt,tan,0,B-.4,L/2-1.25,L/2-.55))],(46,66,80),cv2.LINE_AA)                # para-brisa
        if vtype=='pickup':cv2.fillPoly(im,[P(body(pt,tan,0,B-.3,-L/2+.25,-.25))],tuple(int(c*.6) for c in color),cv2.LINE_AA)   # caçamba
        else:cv2.fillPoly(im,[P(body(pt,tan,0,B-.5,-L/2+.4,L/2-1.6))],tuple(min(255,int(c*1.04)+5) for c in color),cv2.LINE_AA)
    elif vtype=='carreta':
        cv2.fillPoly(im,[P(body(pt,tan,0,B,-L/2,L/2-3.4))],color,cv2.LINE_AA)                             # semirreboque
        for f in np.arange(-L/2+1.4,L/2-3.6,1.4):
            q=P(np.array([pt+tan*f-n*B/2,pt+tan*f+n*B/2]));cv2.line(im,tuple(q[0]),tuple(q[1]),tuple(int(c*.82) for c in color),1,cv2.LINE_AA)
        cv2.fillPoly(im,[P(body(pt,tan,0,B-.15,L/2-3.0,L/2))],(176,40,36) if color[0]>200 else (226,226,220),cv2.LINE_AA)   # cavalo
        cv2.fillPoly(im,[P(body(pt,tan,0,B-.5,L/2-.95,L/2-.35))],(46,66,80),cv2.LINE_AA)
    else:
        cv2.fillPoly(im,[P(body(pt,tan,L,B))],dark,cv2.LINE_AA);cv2.fillPoly(im,[P(body(pt,tan,L-.16,B-.16))],color,cv2.LINE_AA)
        for side in (-1,1):
            q=P(np.array([pt+tan*(-L/2+1)+n*side*(B/2-.25),pt+tan*(L/2-1.6)+n*side*(B/2-.25)]));cv2.line(im,tuple(q[0]),tuple(q[1]),(46,66,80),max(1,round(.3/m_per_px)),cv2.LINE_AA)
        cv2.fillPoly(im,[P(body(pt,tan,0,B-.35,L/2-.9,L/2-.2))],(46,66,80),cv2.LINE_AA)
        cv2.fillPoly(im,[P(body(pt,tan,0,B-.9,-2.5,2.5))],(200,202,198),cv2.LINE_AA)  # ar-condicionado

def headlight_beam(layer,pt,tan,vtype,screen):
    """Feixe discreto à frente do veículo (camada aditiva)."""
    L=TYPES[vtype]['L'];B=TYPES[vtype]['B'];n=np.array([-tan[1],tan[0]]);front=pt+tan*L/2
    for side in (-1,1):
        o=front+n*side*(B/2-.35)
        beam=np.array([o,o+tan*16+n*side*2.2+n*2.,o+tan*16+n*side*2.2-n*2.]);cv2.fillPoly(layer,[screen(beam).astype(np.int32)],(255,236,190),cv2.LINE_AA)
    return [front+n*s*(B/2-.35) for s in (-1,1)]

# ---------------- Destaques (pontos especiais) ----------------
HIGHLIGHT_STYLE={'edificacao':('#f2a541','E','Edificação'),'interferencia':('#ff5d5d','!','Interferência'),'poste':('#ffd84d','P','Poste'),
                 'rede':('#7cc6ff','R','Rede'),'drenagem':('#4fd1c5','D','Drenagem'),'acesso':('#b48cff','A','Acesso'),'outro':('#ff8a3d','•','Ponto especial'),
                 # 1.35: mais categorias
                 'rede_agua':('#3fa9f5','H','Rede de água/esgoto'),'gas':('#f5a623','G','Gasoduto/oleoduto'),'telecom':('#9b8cff','T','Fibra/telefonia'),
                 'torre':('#e8e8e8','LT','Linha de transmissão/torre'),'arvore':('#5cc96a','V','Árvore/vegetação'),'cerca':('#c9a97a','C','Cerca/muro'),
                 'placa':('#ffef7a','PL','Placa/outdoor'),'desapropriacao':('#ff7aa8','$','Desapropriação'),'ocupacao':('#ff9f5a','O','Ocupação na faixa'),
                 'escola':('#6fd3ff','ES','Escola'),'saude':('#ff6b6b','+','Hospital/posto de saúde'),'comercio':('#ffc061','CM','Comércio/indústria'),
                 'curso_dagua':('#4fc3f7','≈','Curso d’água/nascente'),'geotecnia':('#d4886a','GT','Talude/risco geotécnico'),'patrimonio':('#c792ea','PH','Patrimônio/área protegida'),
                 'ponto_onibus':('#7ee0a8','BUS','Ponto de ônibus'),'pedestre':('#ffffff','PD','Travessia de pedestres'),'acidente':('#ff4040','AC','Ponto crítico de acidentes')}

def _rgb(h):return tuple(int(h[i:i+2],16) for i in (1,3,5))

def _wrap(draw,text,font,width,max_lines=2):
    words=text.split();lines=[];cur=''
    for w in words:
        t=(cur+' '+w).strip()
        if draw.textlength(t,font=font)<=width:cur=t
        else:
            if cur:lines.append(cur)
            cur=w
            if len(lines)==max_lines:break
    if cur and len(lines)<max_lines:lines.append(cur)
    if len(lines)==max_lines and ' '.join(lines)!=text.strip():
        while lines[-1] and draw.textlength(lines[-1]+'…',font=font)>width:lines[-1]=lines[-1][:-1]
        lines[-1]+='…'
    return lines

def draw_highlight(im,marker,label,h,font,scale,top,bottom,km_text=''):
    """Marcador + linha de chamada + caixa de informação, com esmaecimento perto das bordas."""
    from PIL import Image,ImageDraw
    H,W=im.shape[:2];color,letter,cat=HIGHLIGHT_STYLE.get(h['category'],HIGHLIGHT_STYLE['outro'])
    color=h.get('color') or color;rgb=_rgb(color);sc=scale
    mx,my=marker
    edge=min(mx,W-mx,my-top,bottom-my)
    alpha=float(np.clip(edge/(120*sc),0,1))*h.get('_fade',1.)
    if alpha<=.02:return
    probe=ImageDraw.Draw(Image.new('RGB',(1,1)))
    f1=font(22*sc,True);f2=font(16*sc);pad=int(12*sc);maxw=int(430*sc)
    lines=[(h['name'],f1,(255,255,255))]
    sub=cat+(f' • km {km_text}' if km_text else '')
    lines.append((sub,f2,rgb))
    for l in _wrap(probe,h.get('description',''),f2,maxw):lines.append((l,f2,(214,226,232)))
    tw=int(max(probe.textlength(t,font=f) for t,f,_ in lines))+2*pad+int(8*sc);lh=[int((f.size)*1.32) for _,f,_ in lines];th=sum(lh)+2*pad
    if label is None:lx,ly=mx+70*sc,my-90*sc-th
    else:lx,ly=label[0]-tw/2,label[1]-th/2
    lx=float(np.clip(lx,10,W-tw-10));ly=float(np.clip(ly,top+10,bottom-th-10))
    x0,y0=int(lx),int(ly)
    # Linha de chamada até a borda mais próxima da caixa.
    cx=float(np.clip(mx,x0,x0+tw));cy=float(np.clip(my,y0,y0+th))
    layer=im.copy()
    cv2.line(layer,(int(mx),int(my)),(int(cx),int(cy)),(10,22,32),max(3,round(5*sc)),cv2.LINE_AA)
    cv2.line(layer,(int(mx),int(my)),(int(cx),int(cy)),rgb,max(1,round(2.5*sc)),cv2.LINE_AA)
    r=max(6,round(15*sc));cv2.circle(layer,(int(mx),int(my)),r+max(1,round(3*sc)),(10,22,32),-1,cv2.LINE_AA);cv2.circle(layer,(int(mx),int(my)),r,rgb,-1,cv2.LINE_AA)
    card=Image.fromarray(layer[y0:y0+th,x0:x0+tw]).convert('RGBA');ov=Image.new('RGBA',card.size,(0,0,0,0));d=ImageDraw.Draw(ov)
    d.rounded_rectangle((0,0,tw-1,th-1),radius=int(10*sc),fill=(8,22,35,232),outline=rgb+(255,),width=max(1,round(2*sc)))
    d.rectangle((0,int(8*sc),max(2,int(5*sc)),th-int(8*sc)),fill=rgb+(255,))
    y=pad
    for (t,f,c),hh in zip(lines,lh):d.text((pad+int(8*sc),y),t,font=f,fill=c+(255,));y+=hh
    layer[y0:y0+th,x0:x0+tw]=np.array(Image.alpha_composite(card,ov).convert('RGB'))
    # Letra da categoria no marcador.
    lab=Image.fromarray(layer[int(my)-r:int(my)+r,int(mx)-r:int(mx)+r]) if r<=my<H-r and r<=mx<W-r else None
    if lab is not None:
        dd=ImageDraw.Draw(lab);fl=font(r*1.2,True);w=dd.textlength(letter,font=fl);dd.text((r-w/2,r-fl.size*.62),letter,font=fl,fill=(10,22,32))
        layer[int(my)-r:int(my)+r,int(mx)-r:int(mx)+r]=np.array(lab)
    cv2.addWeighted(layer,alpha,im,1-alpha,0,dst=im)


# ---------------- 1.26: caixas de chamada sem sobreposição e pórticos ----------------
_CARD_CACHE={}
def callout_card(key,title,sub,desc,rgb,font,sc,style='cartao',ts=1.,image=None):
    """Cartão RGBA (numpy) da caixa de chamada. image: RGB numpy (opcional), mostrada abaixo do texto."""
    k=(key,title,sub,desc,rgb,round(sc,3),style,ts,None if image is None else image.shape)
    if k in _CARD_CACHE:return _CARD_CACHE[k]
    from PIL import Image,ImageDraw
    probe=ImageDraw.Draw(Image.new('RGB',(1,1)));z=sc*ts
    if style=='etiqueta':
        f=font(19*z,True);pad=int(9*z);tw=int(probe.textlength(title,font=f))+2*pad+int(10*z);th=int(f.size*1.5)+pad
        img=Image.new('RGBA',(tw,th),(0,0,0,0));d=ImageDraw.Draw(img)
        d.rounded_rectangle((0,0,tw-1,th-1),radius=th//2,fill=(8,22,35,236),outline=rgb+(255,),width=max(1,round(2*sc)))
        d.text((pad+int(5*z),pad//2+int(2*z)),title,font=f,fill=(255,255,255,255));arr=np.array(img)
    else:
        big=style=='cartao';f1=font((22 if big else 18)*z,True);f2=font((16 if big else 14)*z);pad=int((12 if big else 9)*z);maxw=int((430 if big else 330)*z)
        lines=[(title,f1,(255,255,255))]
        if sub:lines.append((sub,f2,rgb))
        if big and desc:
            for l in _wrap(probe,desc,f2,maxw):lines.append((l,f2,(214,226,232)))
        tw=int(max(probe.textlength(t,font=f) for t,f,_ in lines))+2*pad+int(8*z);lh=[int(f.size*1.32) for _,f,_ in lines];th=sum(lh)+2*pad
        pic=None
        if image is not None and image.size:
            mw,mh=int((360 if big else 220)*z),int((200 if big else 130)*z);h0,w0=image.shape[:2];k2=min(mw/w0,mh/h0)
            pw,ph=max(1,int(w0*k2)),max(1,int(h0*k2));pic=cv2.resize(image,(pw,ph),interpolation=cv2.INTER_AREA if k2<1 else cv2.INTER_CUBIC)
            tw=max(tw,pw+2*pad+int(8*z));th+=ph+pad
        img=Image.new('RGBA',(tw,th),(0,0,0,0));d=ImageDraw.Draw(img)
        d.rounded_rectangle((0,0,tw-1,th-1),radius=int(10*z),fill=(8,22,35,232),outline=rgb+(255,),width=max(1,round(2*sc)))
        d.rectangle((0,int(8*z),max(2,int(5*z)),th-int(8*z)),fill=rgb+(255,))
        y=pad
        for (t,f,c),hh in zip(lines,lh):d.text((pad+int(8*z),y),t,font=f,fill=c+(255,));y+=hh
        arr=np.array(img)
        if pic is not None:
            x=pad+int(8*z);arr[y:y+pic.shape[0],x:x+pic.shape[1],:3]=pic;arr[y:y+pic.shape[0],x:x+pic.shape[1],3]=255
            cv2.rectangle(arr,(x-1,y-1),(x+pic.shape[1],y+pic.shape[0]),rgb+(255,),1)
    if len(_CARD_CACHE)>400:_CARD_CACHE.clear()
    _CARD_CACHE[k]=arr;return arr

def _overlap(a,b):
    return max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))

def place_card(marker,size,W,top,bottom,placed,sc,label=None):
    """Posição da caixa: a indicada pelo usuário ou a primeira posição livre ao redor do marcador."""
    mx,my=marker;tw,th=size
    if label is not None:
        x=float(np.clip(label[0]-tw/2,10,W-tw-10));y=float(np.clip(label[1]-th/2,top+10,bottom-th-10));return x,y
    cands=[]
    for f in (1,2.2,3.6):
        g=70*sc*f;v=90*sc*f
        cands+=[(mx+g,my-v-th),(mx-g-tw,my-v-th),(mx+g,my+v*.67),(mx-g-tw,my+v*.67),(mx+g*.65,my-th/2),(mx-g*.65-tw,my-th/2),(mx-tw/2,my-v*1.33-th),(mx-tw/2,my+v)]
    best=None
    for k,(x,y) in enumerate(cands):
        inside=10<=x<=W-tw-10 and top+10<=y<=bottom-th-10
        x=float(np.clip(x,10,W-tw-10));y=float(np.clip(y,top+10,bottom-th-10));r=(x,y,x+tw,y+th)
        ov=sum(_overlap(r,p) for p in placed)+(0 if inside else tw*th*.25)+(1e9 if r[0]<=mx<=r[2] and r[1]<=my<=r[3] else 0)
        if best is None or ov<best[0]-1e-6:best=(ov,x,y)
        if ov==0:break
    if best[0]>0 and placed:
        # Sem lugar livre ao redor: procura o espaço livre mais próximo no quadro.
        st=max(8,20*sc);free=None
        for y in np.arange(top+10,bottom-th-10+1,st):
            for x in np.arange(10,W-tw-10+1,st):
                r=(x,y,x+tw,y+th)
                if r[0]<=mx<=r[2] and r[1]<=my<=r[3]:continue
                if any(_overlap(r,p)>0 for p in placed):continue
                dd=(x+tw/2-mx)**2+(y+th/2-my)**2
                if free is None or dd<free[0]:free=(dd,float(x),float(y))
        if free:return free[1],free[2]
    return best[1],best[2]

def draw_callout(im,marker,card,rgb,sc,top,bottom,placed,label=None,leader='reta',alpha=1.,letter=None,font=None,marker_kind='circle'):
    """Marcador + linha de chamada + cartão, desenhados só na região afetada (mais rápido) e sem sobrepor outros cartões."""
    H,W=im.shape[:2];mx,my=marker;th,tw=card.shape[:2]
    edge=min(mx,W-mx,my-top,bottom-my);alpha=float(np.clip(edge/(120*sc),0,1))*alpha
    if alpha<=.02:return None
    x,y=place_card(marker,(tw,th),W,top,bottom,placed,sc,label);x0,y0=int(x),int(y);placed.append((x0,y0,x0+tw,y0+th))
    cx=float(np.clip(mx,x0,x0+tw));cy=float(np.clip(my,y0,y0+th))
    pts=[(mx,my),(cx,cy)] if leader!='cotovelo' else [(mx,my),(mx,cy) if not (x0<=mx<=x0+tw) else (cx,my),(cx,cy)]
    r=max(6,round(15*sc));pad=r+8
    X0=int(max(0,min(x0,mx-pad)));Y0=int(max(0,min(y0,my-pad)));X1=int(min(W,max(x0+tw,mx+pad)));Y1=int(min(H,max(y0+th,my+pad)))
    if X1<=X0 or Y1<=Y0:return None
    roi=im[Y0:Y1,X0:X1];layer=roi.copy();o=np.array([X0,Y0])
    P=np.int32([np.array(p)-o for p in pts])
    cv2.polylines(layer,[P],False,(10,22,32),max(3,round(5*sc)),cv2.LINE_AA);cv2.polylines(layer,[P],False,rgb,max(1,round(2.5*sc)),cv2.LINE_AA)
    m=(int(mx-X0),int(my-Y0))
    if marker_kind=='circle':
        cv2.circle(layer,m,r+max(1,round(3*sc)),(10,22,32),-1,cv2.LINE_AA);cv2.circle(layer,m,r,rgb,-1,cv2.LINE_AA)
        if letter and font is not None:
            from PIL import Image,ImageDraw
            a0,b0=m[0]-r,m[1]-r
            if a0>=0 and b0>=0 and a0+2*r<=layer.shape[1] and b0+2*r<=layer.shape[0]:
                lab=Image.fromarray(layer[b0:b0+2*r,a0:a0+2*r]);dd=ImageDraw.Draw(lab);fl=font(r*1.2,True);w=dd.textlength(letter,font=fl);dd.text((r-w/2,r-fl.size*.62),letter,font=fl,fill=(10,22,32));layer[b0:b0+2*r,a0:a0+2*r]=np.array(lab)
    else:
        q=max(5,round(9*sc));dia=np.int32([[m[0],m[1]-q],[m[0]+q,m[1]],[m[0],m[1]+q],[m[0]-q,m[1]]]);cv2.fillPoly(layer,[dia],rgb,cv2.LINE_AA);cv2.polylines(layer,[dia],True,(10,22,32),max(1,round(2*sc)),cv2.LINE_AA)
    a=card[:,:,3:4].astype(np.float32)/255;sy,sx=y0-Y0,x0-X0
    reg=layer[sy:sy+th,sx:sx+tw];hh,ww=reg.shape[:2]
    reg[:]=(reg*(1-a[:hh,:ww])+card[:hh,:ww,:3]*a[:hh,:ww]).astype(np.uint8)
    cv2.addWeighted(layer,alpha,roi,1-alpha,0,dst=roi)
    return (x0,y0,x0+tw,y0+th)

def draw_gantry(im,g,scr,m,sc):
    """Pórtico em planta: sombra, pilares, viga treliçada e painel da placa."""
    a=g['a'];b=g['b'];u=b-a;L=float(np.linalg.norm(u));u=u/L;n=np.array([-u[1],u[0]]);bw=g['beam_width_m'];H=g['height_m']
    beam=np.array([a-n*bw/2,b-n*bw/2,b+n*bw/2,a+n*bw/2])
    posts=[a] if g['kind']!='portico' else [a,b];ps=.45
    post_rings=[np.array([p+(-ps,-ps),p+(ps,-ps),p+(ps,ps),p+(-ps,ps)]) for p in posts]
    # Sombra no chão (sol fixo a noroeste, como a das OAE), deslocada pela altura.
    shift=np.array([.35,-.55])*H*.6;q=scr(beam+shift).astype(np.int32);q2=[scr(r+shift*.5).astype(np.int32) for r in post_rings]
    allp=np.vstack([q,scr(beam).astype(np.int32)]+q2);x0,y0=np.maximum(allp.min(0)-4,0);x1,y1=allp.max(0)+5
    Hh,Ww=im.shape[:2];x1=min(Ww,x1);y1=min(Hh,y1)
    if x1>x0 and y1>y0:
        roi=im[y0:y1,x0:x1];sh=roi.copy();cv2.fillPoly(sh,[q-[x0,y0]],(0,0,0),cv2.LINE_AA)
        for r in q2:cv2.fillPoly(sh,[r-[x0,y0]],(0,0,0),cv2.LINE_AA)
        cv2.addWeighted(sh,.3,roi,.7,0,dst=roi)
    lw=max(1,round(.12/m))
    for r in post_rings:
        rr=scr(r).astype(np.int32);cv2.fillPoly(im,[rr],(150,155,158),cv2.LINE_AA);cv2.polylines(im,[rr],True,(60,64,68),lw,cv2.LINE_AA)
    col=_rgb(g['color']) if g.get('color') else (206,209,211)
    bq=scr(beam).astype(np.int32);cv2.fillPoly(im,[bq],col,cv2.LINE_AA)
    k=max(2,int(L/max(bw,.5)));zz=[a+u*L*i/k+n*bw*.38*(1 if i%2 else -1) for i in range(k+1)]
    if bw/m>=4:cv2.polylines(im,[scr(np.array(zz)).astype(np.int32)],False,(118,122,126),lw,cv2.LINE_AA)
    cv2.polylines(im,[bq],True,(64,68,72),lw,cv2.LINE_AA)
    if g.get('panel_rgb') is not None:
        pl=min(L*.7,max(2.,g.get('panel_aspect',3.)*2.2));c=a+u*L/2;pn=np.array([c-u*pl/2-n*bw*.5,c+u*pl/2-n*bw*.5,c+u*pl/2-n*(bw*.5+.35),c-u*pl/2-n*(bw*.5+.35)])
        pq=scr(pn).astype(np.int32);cv2.fillPoly(im,[pq],tuple(int(v) for v in g['panel_rgb']),cv2.LINE_AA);cv2.polylines(im,[pq],True,(30,34,36),lw,cv2.LINE_AA)

# ---------------- 1.13: dia / noite ----------------
NIGHT_TINT=np.array([.20,.27,.46],np.float32)

def night_factor(s,t):
    """0 = dia, 1 = noite plena (multiplicado pela escuridão escolhida)."""
    mode=getattr(s,'day_night','off')
    if mode=='off':return 0.
    if mode=='night':return 1.
    f=float(np.clip((t-s.night_start_s)/max(s.night_transition_s,1e-3),0,1));return f*f*(3-2*f)

def darken(view,k):
    """Escurece e esfria a cena (k: 0..1)."""
    if k<=0:return
    f=(1-k)+k*NIGHT_TINT
    np.multiply(view,f[None,None,:],out=view,casting='unsafe')

def tail_lights(layer,pt,tan,vtype,screen,r):
    L=TYPES[vtype]['L'];B=TYPES[vtype]['B'];n=np.array([-tan[1],tan[0]]);rear=pt-tan*L/2
    for side in (-1,1):
        x,y=screen((rear+n*side*(B/2-.3))[None])[0].astype(int);cv2.circle(layer,(x,y),r,(255,40,24),-1,cv2.LINE_AA)


# ---------------- 1.20: perfil "Apresentação técnica" (pista nova dourada, existente cinza-azulada) ----------------
TECH_FILL={'pavement':'#2a3033','existing_pavement':'#6f8291','shoulder':'#5f5b51'}
TECH_HATCH={'pavement':((200,165,90),3.0,1),'existing_pavement':((183,199,212),3.0,-1),'shoulder':((214,205,164),1.6,1)}

def surface_hatch(shape,x0,y1,px,role):
    """Máscara (0..1) de hachura diagonal ancorada nas coordenadas do projeto (não 'nada' com a câmera).
    x0,y1: coordenada do canto superior esquerdo do raster; px: metros por pixel."""
    color,S,sgn=TECH_HATCH[role];h,w=shape
    P=S*math.sqrt(2);ox=x0-round(x0/P)*P;oy=y1-round(y1/P)*P   # deslocar por múltiplos do período não muda a hachura
    X=(ox+(np.arange(w)+.5)*px).astype(np.float32);Y=(oy-(np.arange(h)+.5)*px).astype(np.float32)
    u=(X[None,:]+sgn*Y[:,None])/np.float32(math.sqrt(2))
    d=np.abs(np.mod(u,S)-S/2)          # distância (m) ao meio entre linhas
    half=max(.09,.6*px)                # meia-espessura: 18 cm ou ~1 pixel
    return np.clip((d-(S/2-half))/max(px,1e-6)+.5,0,1).astype(np.float32),np.array(color,np.float32)


# ---------------- 1.24: texturas editáveis ----------------
DEFAULT_LUT={'spk':_R_SPK,'patch':_R_PATCH,'crack':_R_CRACK,'shift':_R_SHIFT,'grain':_LUT_GRAIN,'tone':_LUT_TONE,'conc':_LUT_CONC,'grass':.16,'bright':None}
# Superfície editável -> códigos da máscara de superfície.
TEX_SURF={'pista_nova':[1],'pista_existente':[2],'concreto':[3],'acostamento':[4],'canteiro':[5],'trilhas':[8],'talude_corte':[6],'talude_aterro':[7]}

def texture_lut(params,areas=None):
    """Intensidades por superfície (multiplicadores; 1 = padrão) e brilho (-0,3 a 0,3). None se tudo padrão.
    areas (1.27): [(código, código base, parâmetros)] — áreas com textura própria partem da textura do tipo."""
    if areas:
        L=texture_lut(params) or {k:(v.copy() if isinstance(v,np.ndarray) else v) for k,v in DEFAULT_LUT.items()}
        bright=L['bright'].copy() if L.get('bright') is not None else np.zeros(256,np.float32)
        for code,base,p in areas:
            for k in ('grain','spk','conc','tone','patch','crack','shift'):L[k][code]=L[k][base]
            g=float(p.get('grao',1));t=float(p.get('tom',1));pa=float(p.get('remendos',1));cr=float(p.get('fissuras',1))
            L['grain'][code]*=g;L['spk'][code]*=g;L['conc'][code]*=g;L['tone'][code]*=t;L['patch'][code]*=pa;L['crack'][code]*=cr
            bright[code]=float(np.clip(bright[base]+float(p.get('brilho',0)),-.3,.3))
        L['bright']=bright if bright.any() else None
        return L
    if not params:return None
    L={k:(v.copy() if isinstance(v,np.ndarray) else v) for k,v in DEFAULT_LUT.items()};bright=np.zeros(256,np.float32);changed=False
    for name,p in params.items():
        p=p if isinstance(p,dict) else p.model_dump()
        codes=TEX_SURF.get(name,[])
        for c in codes:
            g=float(p.get('grao',1));t=float(p.get('tom',1));pa=float(p.get('remendos',1));cr=float(p.get('fissuras',1));br=float(p.get('brilho',0))
            if (g,t,pa,cr,br)!=(1,1,1,1,0):changed=True
            L['grain'][c]*=g;L['spk'][c]*=g;L['conc'][c]*=g;L['tone'][c]*=t;L['patch'][c]*=pa;L['crack'][c]*=cr;bright[c]=br
            if c==5:L['grass']=.16*g
    if not changed:return None
    L['bright']=bright if bright.any() else None
    return L

# ---------------- 1.34: texturas “artístico realista” ----------------
# Camada a mais sobre as realistas (só com texture_style='artistico'; os outros estilos não mudam):
#  • bordas da pista com sujeira/oclusão suave e grama mais seca junto ao pavimento;
#  • variação de cor quente/fria no asfalto em grande escala e pedriscos claros de perto;
#  • grama em duas tonalidades (manchas) com folhagem fina; concreto com placas de tom diferente e manchas;
#  • taludes de corte com pedras e veios do solo.
_PAVED=np.zeros(256,bool);_PAVED[[1,2,3,4,8]]=True
_ASPH=np.zeros(256,bool);_ASPH[[1,2,4,8]]=True
_STONE=None
def stones():
    global _STONE
    if _STONE is None:_STONE=Texture(131,((256,1.),))
    return _STONE

def _low(tex,A,shape,m_per_px,scale,k=8):
    """Ruído de grande escala (1/scale do ladrilho), amostrado em 1/k e ampliado."""
    small=(max(1,shape[0]//k),max(1,shape[1]//k));As=A.copy();As[:,:2]*=k
    return cv2.resize(tex.sample(As*np.array([[scale],[scale]]),small,m_per_px*k*scale),(shape[1],shape[0]),interpolation=cv2.INTER_LINEAR)

def shade_artistic(im,surface,s2w,m_per_px,valid,lut=None):
    S=np.where(valid,surface,0).astype(np.uint8)
    rows=np.flatnonzero((S>0).any(1))
    if not len(rows):return
    y0,y1=rows[0],rows[-1]+1;cols=np.flatnonzero((S[y0:y1]>0).any(0));x0,x1=cols[0],cols[-1]+1
    # Margem de 1 px (dentro da imagem): a borda da superfície precisa de vizinhos fora dela para a distância.
    H0,W0=S.shape;y0,x0=max(0,y0-1),max(0,x0-1);y1,x1=min(H0,y1+1),min(W0,x1+1)
    S=S[y0:y1,x0:x1];shape=S.shape;A=_crop(s2w,x0,y0);roi=im[y0:y1,x0:x1];out=roi.astype(np.float32)
    P=_PAVED[S];AS=_ASPH[S];G=S==5
    # Bordas: escurecimento suave até ~0,6 m da borda do pavimento (pó e sombra); grama seca até ~1 m.
    if m_per_px<1.2 and P.any():
        d=cv2.distanceTransform(P.astype(np.uint8),cv2.DIST_L2,3)*m_per_px
        out*=(1-.11*np.exp(-d/.6)*P)[:,:,None]
        if G.any():
            dg=cv2.distanceTransform((~P).astype(np.uint8),cv2.DIST_L2,3)*m_per_px;dry=np.exp(-dg/1.0)*G
            out[:,:,0]+=10*dry;out[:,:,1]+=5*dry;out[:,:,2]-=4*dry
    if AS.any():
        # Cor do asfalto: manchas quentes/frias de dezenas de metros (o asfalto real nunca é cinza uniforme).
        n=_low(soil(),A,shape,m_per_px,.06)*AS;out[:,:,0]+=2.4*n;out[:,:,1]+=1.0*n;out[:,:,2]-=1.6*n
        if m_per_px<.06:
            # De perto: pedriscos claros do agregado.
            w=float(np.clip((.06-m_per_px)/.03,0,1));st=stones().sample(A,shape,m_per_px)
            out+=(w*22*np.clip(st-1.9,0,1)*AS)[:,:,None]
    C=S==3
    if C.any():
        n=_low(concrete(),A,shape,m_per_px,.35)*C;out*=(1+.045*n)[:,:,None]
        stn=np.clip(_low(soil(),A,shape,m_per_px,.5,4)-1.1,0,1)*C;out*=(1-.10*stn)[:,:,None]
    if G.any():
        # Grama em manchas (verde-escuro × verde-amarelado) e folhagem fina.
        n=_low(grass(),A,shape,m_per_px,.22)*G;out[:,:,0]+=7*np.clip(n,0,None);out[:,:,1]+=6*n;out[:,:,2]-=3*np.clip(n,0,None)
        if m_per_px<.3:
            f=grass().sample(A*np.array([[3.],[3.]]),shape,m_per_px*3)*G;out*=(1+.07*f*float(np.clip((.3-m_per_px)/.2,0,1)))[:,:,None]
    CT=S==6
    if CT.any():
        st=stones().sample(A,shape,m_per_px)*CT;out*=(1-.16*np.clip(st-1.6,0,1)*CT)[:,:,None]
        v=_low(soil(),A*np.array([[1.],[4.]]),shape,m_per_px,.3)*CT;out[:,:,0]+=5*v;out[:,:,1]+=2.5*v
    roi[:]=np.clip(out,0,255).astype(np.uint8)
