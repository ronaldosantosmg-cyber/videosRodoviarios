"""2.48: texturas de superfície com o mesmo conceito dos veículos — cada material tem um MAPA DE ALTURA (grão, trincas, tufos, sulcos de erosão, pedras)
e é iluminado (luz difusa + brilho especular) a partir das normais, mais variação de tom em várias escalas.
Tudo ancorado em COORDENADAS DO MUNDO (metros): a textura não "nada" quando a câmera anda nem muda entre ladrilhos vizinhos. Só aparência.
Escalas menores que 2 pixels são descartadas (sem cintilação): em zoom afastado domina o tom; em zoom próximo aparece o grão."""
import numpy as np

LUZ=np.array([-.45,-.55,.70],np.float64);LUZ/=np.linalg.norm(LUZ)
def _h(ix,iy,seed):
    h=(ix.astype(np.int64)*73856093)^(iy.astype(np.int64)*19349663)^(int(seed)*83492791);h=(h^(h>>13))*1274126177&0x7fffffff;return (h%100003)/100003.
def vn(X,Y,s,seed=0):
    """ruído de valor suave em [0,1], período s (m)"""
    u=X/s;v=Y/s;ix=np.floor(u);iy=np.floor(v);fx=u-ix;fy=v-iy;fx=fx*fx*(3-2*fx);fy=fy*fy*(3-2*fy)
    a=_h(ix,iy,seed);b=_h(ix+1,iy,seed);c=_h(ix,iy+1,seed);d=_h(ix+1,iy+1,seed)
    return (a*(1-fx)+b*fx)*(1-fy)+(c*(1-fx)+d*fx)*fy
def stable_noise(X,Y,scale,px,seed=0):
    """Escala física fixa; só a amplitude varia suavemente com a resolução."""
    if not np.isfinite([scale,px]).all() or scale<=0 or px<=0:raise ValueError('Resolução de textura inválida.')
    fade=float(np.clip(scale/px-1,0,1));fade=fade*fade*(3-2*fade)
    if fade<=0:return np.full_like(X,.5,dtype=np.float64)
    return .5+(vn(X,Y,scale,seed)-.5)*fade

def micro_noise(X,Y,px,seed=0):return stable_noise(X,Y,.06,px,seed)-.5

def fbm(X,Y,s0,oc,px,seed=0,ganho=.5):
    """Oitavas fixas no mundo, com transição contínua entre níveis de detalhe."""
    t=np.zeros_like(X);amp=1.;tot=0.;scale=s0
    for o in range(oc):
        t+=amp*(stable_noise(X,Y,scale,px,seed+o*17)-.5);tot+=amp;amp*=ganho;scale*=.5
    return t/max(tot,1e-9)*2

def _normal(h,px,forca):
    gy,gx=np.gradient(h,px);n=np.stack([-gx*forca,gy*forca,np.ones_like(h)],-1);return n/np.linalg.norm(n,axis=-1,keepdims=True)
def _ilum(rgb,h,px,forca,esp,amb=.78):
    """iluminação de 1ª ordem: k = 1 + inclinação·luz (média ≈ 1, então não muda o tom geral do material) + brilho especular suave."""
    gy,gx=np.gradient(h,px);nx=-gx*forca;ny=gy*forca
    k=np.clip(1+(1-amb)*(nx*LUZ[0]+ny*LUZ[1])/LUZ[2]*1.7,.6,1.5)
    n=np.stack([nx,ny,np.ones_like(h)],-1);n/=np.linalg.norm(n,axis=-1,keepdims=True);hv=LUZ+np.array([0,0,1.]);hv/=np.linalg.norm(hv);sp=np.clip((n*hv).sum(-1),0,1)**28
    return rgb*k[...,None]+(sp*esp*255*.6)[...,None]

def acabar(color,role,x0,y1,px,mask=None,seed=0,rigido=False,quality="ultra_realista"):
    """color: (n,n,3) uint8/float. Devolve uint8 com relevo iluminado. mask opcional limita os cálculos (não muda o resultado fora dela)."""
    c=np.array(color,np.float64,copy=True)
    if c.ndim==1:return c.astype(np.uint8)
    tab=RIGIDOS if rigido else MATERIAIS
    if role not in tab:return np.clip(c,0,255).astype(np.uint8)
    P=2;c=np.pad(c,((P,P),(P,P),(0,0)),mode='edge');H,W=c.shape[:2]                      # margem: o gradiente na borda do ladrilho fica idêntico ao do vizinho
    xs=np.arange(W)[None,:]-P;ys=np.arange(H)[:,None]-P;X=(x0+(xs+.5)*px+0*ys).astype(np.float64);Y=(y1-(ys+.5)*px+0*xs).astype(np.float64)
    out=tab[role](c,X,Y,px,seed)
    if quality=="realista":out=c*.45+out*.55
    return np.clip(out[P:-P,P:-P],0,255).astype(np.uint8)

# ------------------------------------------------------------------ materiais
def _foto(c,X,Y,px,nome,forca=.7):
    """2.57: detalhe de luminância dos ladrilhos fotográficos do pacote (assets/texturas); só em zoom próximo. Ausente → sem efeito."""
    if px>.012:return c
    try:
        from .texturas_pacote import detalhe
        f=detalhe(nome,X,Y,forca*min(1.,(.012-px)/.004))
    except Exception:return c
    return c if f is None else c*f[...,None]

def _asfalto(c,X,Y,px,seed):
    tom=fbm(X,Y,9.,4,px,seed+1);c=c*(1+.07*tom)[...,None]                                  # tom: manchas de desgaste e emendas
    mancha=np.clip((vn(X,Y,14.,seed+2)-.72)/.12,0,1);c=c*(1-.14*mancha)[...,None]           # trechos mais escuros (óleo/borracha)
    rem=np.clip((vn(X,Y,23.,seed+3)-.78)/.08,0,1);c=c*(1+.12*rem)[...,None]                 # remendos mais claros
    h=.25*fbm(X,Y,.5,5,px,seed+4)+.35*micro_noise(X,Y,px,seed+5)                          # agregado (grão no nível do pixel)
    trinca=1-np.abs(2*vn(X,Y,3.4,seed+6)-1);tr=np.clip((trinca-.985)/.012,0,1)*np.clip((vn(X,Y,17.,seed+7)-.62)/.1,0,1)   # trincas esparsas
    h-=.6*tr;c=c*(1-.35*tr)[...,None]
    return _ilum(_graos(_foto(c,X,Y,px,'asfalto_azulado',.6),X,Y,px,seed),h,px,.9,.05)

# ---- 2.53: agregado visível (grãos claros, rosados e escuros) como nas fotos de referência do asfalto
GRAOS=((.011,.42,(1.9,1.9,1.95)),(.0065,.50,(1.5,1.45,1.45)),(.016,.20,(1.5,1.1,1.1)),(.009,.34,(.45,.45,.48)),(.024,.10,(1.7,1.7,1.7)))   # (célula m, densidade, fator RGB)
def _graos(c,X,Y,px,seed,forca=1.0):
    """grãos de agregado ancorados no mundo; só quando o grão tem ≥ ~1,6 px (senão o tom médio basta). Compensa o brilho médio (não muda o tom geral)."""
    if px>.0075:return c
    out=c.copy();ganho=min(1.,(.0075-px)/.0045)*forca
    for k,(s,dens,fat) in enumerate(GRAOS):
        if s<1.6*px:continue
        ix=np.floor(X/s);iy=np.floor(Y/s);r=_h(ix,iy,seed+900+k);on=r<dens
        if not on.any():continue
        cx=(ix+.25+.5*_h(ix,iy,seed+920+k))*s;cy=(iy+.25+.5*_h(ix,iy,seed+940+k))*s;rad=s*(.22+.22*_h(ix,iy,seed+960+k))
        d=np.hypot(X-cx,Y-cy);cov=np.clip((rad-d)/max(px,1e-6)+.5,0,1)*on*ganho
        f=np.array(fat);out=out*(1-cov[...,None])+out*f*cov[...,None]
    # compensação analítica do brilho médio dos grãos (cobertura esperada ≈ dens·π·rad²/s²)
    E=0.
    for s,dens,fat in GRAOS:
        if s<1.6*px:continue
        E+=dens*np.pi*(.33*s)**2/s**2*(np.mean(fat)-1)
    return out/(1+E*ganho)
def _concreto(c,X,Y,px,seed):
    c=c*(1+.05*fbm(X,Y,6.,3,px,seed+11))[...,None]
    h=.12*fbm(X,Y,.35,4,px,seed+12)+.2*micro_noise(X,Y,px,seed+13)
    poro=np.clip((stable_noise(X,Y,.07,px,seed+14)-.86)/.06,0,1);c=c*(1-.25*poro)[...,None]
    return _ilum(c,h,px,.7,.07)
def _grama(c,X,Y,px,seed):
    ton=fbm(X,Y,11.,4,px,seed+21);c=c*(1+.10*ton)[...,None]
    seco=np.clip((vn(X,Y,19.,seed+22)-.6)/.3,0,1)*.55;c=c*(1-seco[...,None])+seco[...,None]*(c*np.array([1.12,1.04,.78]))   # manchas secas
    tufo=np.clip((vn(X,Y,2.2,seed+23)-.62)/.2,0,1);c=c*(1-.14*tufo)[...,None]
    h=.5*fbm(X*.6,Y*1.0,.35,4,px,seed+24)+.3*micro_noise(X,Y,px,seed+25)                   # lâminas: alongadas em x
    return _ilum(c,h,px,1.1,.04,.72)
def _terra(c,X,Y,px,seed):                                                              # corte: solo exposto
    c=c*(1+.12*fbm(X,Y,7.,4,px,seed+31))[...,None]
    banda=.5+.5*np.sin(Y*1.7+4*vn(X,Y,9.,seed+32));c=c*(1+.07*(banda-.5))[...,None]     # estratos
    sulco=1-np.abs(2*vn(X*.35,Y*1.4,.9,seed+33)-1);h=-.28*np.clip((sulco-.88)/.1,0,1)+.35*fbm(X,Y,.6,4,px,seed+34)   # ravinas de erosão
    pedra=np.clip((stable_noise(X,Y,.22,px,seed+35)-.83)/.08,0,1);h+=.6*pedra;c=c*(1+.18*pedra)[...,None]
    return _ilum(c,h,px,1.2,.06,.70)
def _cascalho(c,X,Y,px,seed):                                                          # acostamento
    c=_foto(c,X,Y,px,'areia_acostamento',.6)
    c=c*(1+.08*fbm(X,Y,5.,3,px,seed+41))[...,None]
    g=stable_noise(X,Y,.08,px,seed+42);h=.5*(g-.5)+.25*fbm(X,Y,.5,3,px,seed+43)
    c=c*(1+.22*(g-.5))[...,None]
    return _ilum(c,h,px,1.0,.08,.74)
def _remendos(X,Y,seed,celx=4.,cely=7.,prob=.10):
    """remendos retangulares (cortes de reparo): máscara e linha de borda, ancorados no mundo."""
    ix=np.floor(X/celx);iy=np.floor(Y/cely);flag=(_h(ix,iy,seed)<prob).astype(np.float64)
    fx=X/celx-ix;fy=Y/cely-iy;borda=(np.minimum(np.minimum(fx,1-fx)*celx,np.minimum(fy,1-fy)*cely)<.07)
    return flag,flag*borda
def _asfalto_novo(c,X,Y,px,seed):                                                       # flexível NOVO: escuro, uniforme, fino, levemente brilhante
    c=c*(1+.025*fbm(X,Y,14.,3,px,seed+51))[...,None]
    h=.18*fbm(X,Y,.5,4,px,seed+52)+.30*micro_noise(X,Y,px,seed+53)
    return _ilum(_graos(_foto(c,X,Y,px,'asfalto_escuro',.8),X,Y,px,seed,.55),h,px,.8,.09)
def _asfalto_exist(c,X,Y,px,seed):                                                      # flexível EXISTENTE: desgastado, trincado, remendado
    c=c*(1+.10*fbm(X,Y,8.,4,px,seed+61))[...,None]
    oxi=np.clip((vn(X,Y,6.,seed+62)-.45)/.4,0,1);c=c*(1+.10*oxi)[...,None]               # oxidação: cinza mais claro
    oleo=np.clip((vn(X,Y,2.6,seed+63)-.80)/.07,0,1);c=c*(1-.22*oleo)[...,None]            # manchas de óleo
    rem,bor=_remendos(X,Y,seed+64,4.,7.,.12);c=c*(1-.13*rem)[...,None]*(1-.35*bor)[...,None]
    jacare=1-np.abs(2*vn(X,Y,1.7,seed+65)-1);ja=np.clip((jacare-.945)/.04,0,1)*np.clip((vn(X,Y,9.,seed+66)-.50)/.1,0,1)   # trincas couro de jacaré
    longi=1-np.abs(2*vn(X*.25,Y,5.,seed+67)-1);lg=np.clip((longi-.985)/.012,0,1)
    cr=np.maximum(ja,lg);c=c*(1-.45*cr)[...,None]
    h=.38*fbm(X,Y,.5,5,px,seed+68)+.50*micro_noise(X,Y,px,seed+69)-.4*cr                # agregado graúdo aparente (desagregação)
    return _ilum(_graos(_foto(c,X,Y,px,'asfalto_azulado',.9),X,Y,px,seed,1.25),h,px,1.0,.03)
def _concreto_novo(c,X,Y,px,seed):                                                      # rígido NOVO: claro, liso, poros finos
    c=c*(1+.035*fbm(X,Y,7.,3,px,seed+71))[...,None]
    h=.08*fbm(X,Y,.4,4,px,seed+72)+.16*micro_noise(X,Y,px,seed+73)
    poro=np.clip((stable_noise(X,Y,.07,px,seed+74)-.90)/.05,0,1);c=c*(1-.18*poro)[...,None]
    return _ilum(c,h,px,.6,.09)
def _concreto_exist(c,X,Y,px,seed):                                                     # rígido EXISTENTE: manchado, trincado, com reparos
    c=c*(1+.09*fbm(X,Y,6.,4,px,seed+81))[...,None]
    alga=np.clip((vn(X,Y,5.,seed+82)-.58)/.25,0,1)*.5;c=c*(1-alga[...,None])+alga[...,None]*(c*np.array([.90,.99,.84]))   # limo/mofo
    sujo=np.clip((vn(X*.3,Y,2.5,seed+83)-.62)/.2,0,1);c=c*(1-.14*sujo)[...,None]          # rastros de sujeira
    rem,bor=_remendos(X,Y,seed+84,5.,5.,.07);c=c*(1-.28*rem)[...,None]*(1-.3*bor)[...,None]   # reparos em asfalto/argamassa
    tri=1-np.abs(2*vn(X,Y,2.6,seed+85)-1);tr=np.clip((tri-.968)/.025,0,1)*np.clip((vn(X,Y,12.,seed+86)-.45)/.1,0,1)
    desp=np.clip((stable_noise(X,Y,.12,px,seed+87)-.86)/.06,0,1)                            # esborcinados (buracos rasos)
    c=c*(1-.38*tr)[...,None]*(1-.22*desp)[...,None]
    h=.14*fbm(X,Y,.4,4,px,seed+88)+.22*micro_noise(X,Y,px,seed+89)-.35*tr-.4*desp
    return _ilum(c,h,px,.8,.05)
MATERIAIS={'pavement':_asfalto_novo,'existing_pavement':_asfalto_exist,'shoulder':_cascalho,'median':_grama,'terrain':_grama,'fill':_grama,'cut':_terra,'oae':_concreto,'barrier':_concreto}
RIGIDOS={'pavement':_concreto_novo,'existing_pavement':_concreto_exist,'shoulder':_concreto_novo,'oae':_concreto_novo,'barrier':_concreto_novo}

def acabar_blocos(color,mask,role,x0,y1,px,seed=11,bloco=256,rigido=False,quality="ultra_realista"):
    """aplica `acabar` em blocos, só onde a máscara tem pixels (memória e tempo controlados em mosaicos grandes). Resultado idêntico ao de um passo único."""
    n,m=mask.shape[:2]
    out=np.array(np.broadcast_to(np.asarray(color),(n,m,3)) if np.ndim(color)==1 else color,np.uint8,copy=True)
    if role not in (RIGIDOS if rigido else MATERIAIS) or not mask.any():return out
    for j in range(0,n,bloco):
        for i in range(0,m,bloco):
            if not mask[j:j+bloco,i:i+bloco].any():continue
            out[j:j+bloco,i:i+bloco]=acabar(out[j:j+bloco,i:i+bloco],role,x0+i*px,y1-j*px,px,seed=seed,rigido=rigido,quality=quality)
    return out

def acabar_misto(color,mask,rmask,role,x0,y1,px,seed=11,quality="ultra_realista"):
    """pavimento rígido (rmask) e flexível (resto da máscara) recebem texturas diferentes; novo × existente vem do papel (pavement × existing_pavement)."""
    mask=np.asarray(mask,bool);r=np.zeros_like(mask) if rmask is None else (np.asarray(rmask)>0)&mask;f=mask&~r
    out=acabar_blocos(color,f,role,x0,y1,px,seed,quality=quality) if f.any() else np.array(np.broadcast_to(np.asarray(color),mask.shape+(3,)) if np.ndim(color)==1 else color,np.uint8,copy=True)
    if r.any():
        rg=acabar_blocos(color,r,role,x0,y1,px,seed,rigido=True,quality=quality);out[r]=rg[r]
    return out

# ------------------------------------------------------------------ OAE (nova / existente / alargada)
def _oae_nova(c,X,Y,px,seed):return _concreto_novo(c,X,Y,px,seed+500)
def _oae_exist(c,X,Y,px,seed):return _concreto_exist(c,X,Y,px,seed+600)
def _oae_alargada(c,X,Y,px,seed):
    """alargamento: faixa de concreto novo ao lado do antigo, com emenda (junta fria) marcada; as duas metades trocam a cada ~18 m."""
    faixa=(np.floor(X/18.)+np.floor(Y/18.))%2;novo=_concreto_novo(c*1.05,X,Y,px,seed+700);vel=_concreto_exist(c,X,Y,px,seed+800)
    m=(faixa>0)[...,None];out=np.where(m,novo,vel)
    ex=np.minimum(np.abs(X/18.-np.round(X/18.)),np.abs(Y/18.-np.round(Y/18.)))*18.;junta=(ex<max(.05,px*.8))[...,None]
    return out*(1-.4*junta)
MATERIAIS_OAE={'nova':_oae_nova,'existente':_oae_exist,'alargada':_oae_alargada}
def acabar_oae(color,mask,kind,x0,y1,px,seed=11,bloco=256):
    n,m=mask.shape[:2];out=np.array(np.broadcast_to(np.asarray(color),(n,m,3)) if np.ndim(color)==1 else color,np.uint8,copy=True)
    fn=MATERIAIS_OAE.get(kind)
    if fn is None or not mask.any():return out
    for j in range(0,n,bloco):
        for i in range(0,m,bloco):
            if not mask[j:j+bloco,i:i+bloco].any():continue
            P=2;sub=np.pad(out[j:j+bloco,i:i+bloco].astype(np.float64),((P,P),(P,P),(0,0)),mode='edge');H,W=sub.shape[:2]
            xs=np.arange(W)[None,:]+i-P;ys=np.arange(H)[:,None]+j-P;X=(x0+(xs+.5)*px+0*ys).astype(np.float64);Y=(y1-(ys+.5)*px+0*xs).astype(np.float64)
            out[j:j+bloco,i:i+bloco]=np.clip(fn(sub,X,Y,px,seed)[P:-P,P:-P],0,255).astype(np.uint8)
    return out

# ------------------------------------------------------------------ água
def agua(image,mask,worldpx,px,opacity=.65,bloco=768):
    """água com ondas (mapa de altura), reflexo do céu por Fresnel, brilho do sol, espuma na margem e cor por profundidade/sedimento.
    Ancorada no mundo: a origem vem do próprio `worldpx` (sem costura entre ladrilhos).
    2.59: processada em blocos (antes um único retângulo em float64: ~5 GB num mosaico 8192² e minutos de troca de disco). Resultado igual."""
    import cv2
    ys,xs=np.nonzero(mask)
    if not len(xs):return
    o=np.asarray(worldpx(np.array([[0.,0.]])),float)[0];X0=-o[0]*px;Y1=o[1]*px
    x0,x1,y0,y1=int(xs.min()),int(xs.max())+1,int(ys.min()),int(ys.max())+1
    del ys,xs
    P=2;margem=int(np.ceil(36./px))+2                                                              # além de 35 m a profundidade já satura
    cy0,cy1=max(0,y0-margem),min(mask.shape[0],y1+margem);cx0,cx1=max(0,x0-margem),min(mask.shape[1],x1+margem)
    inside=(mask[cy0:cy1,cx0:cx1]>127).astype(np.uint8);dist=cv2.distanceTransform(inside,cv2.DIST_L2,3)*px     # float32, só a área útil
    raso=np.array([84,124,108],np.float64);fundo=np.array([24,70,108],np.float64);turvo=np.array([112,112,80],np.float64)
    L=np.array([-.45,-.55,.70]);L/=np.linalg.norm(L);Hv=L+np.array([0,0,1.]);Hv/=np.linalg.norm(Hv);ceu=np.array([176,200,222],np.float64)
    for by in range(y0,y1,bloco):
        for bx in range(x0,x1,bloco):
            ey,ex=min(by+bloco,y1),min(bx+bloco,x1)
            sel_m=mask[by:ey,bx:ex]
            if not sel_m.any():continue
            xx=np.arange(bx-P,ex+P)[None,:];yy=np.arange(by-P,ey+P)[:,None]
            X=(X0+(xx+.5)*px+0*yy).astype(np.float64);Y=(Y1-(yy+.5)*px+0*xx).astype(np.float64)
            h=.55*fbm(X,Y,3.2,4,px,seed=91)+.35*fbm(X*1.0,Y*2.2,.9,3,px,seed=92)+.05*fbm(X,Y,.3,3,px,seed=93)   # ondas
            gy,gx=np.gradient(h,px);nx=-gx*.30;ny=gy*.30;nz=1/np.sqrt(1+nx*nx+ny*ny);nx*=nz;ny*=nz
            d=np.pad(dist,((P,P),(P,P)),mode='edge')[by-cy0:ey-cy0+2*P,bx-cx0:ex-cx0+2*P]
            prof=np.clip(d/35.,0,1);sed=.5+.5*fbm(X,Y,60.,3,px,seed=94)                              # profundidade e sedimento (rios barrentos)
            base=raso+(fundo-raso)*(prof**.7)[...,None];base=base*(1-.35*sed[...,None]*(1-prof)[...,None])+turvo*(.35*sed[...,None]*(1-prof)[...,None])
            fres=.10+.45*(1-nz)**2+.08;c=base*(1-fres[...,None])+ceu*fres[...,None]
            sp=np.clip(nx*Hv[0]+ny*Hv[1]+nz*Hv[2],0,1)**60
            c=c+(sp*90)[...,None]*np.array([1,.98,.92])
            esp=np.clip(1-d/1.4,0,1)*np.clip(.55+.9*fbm(X,Y,.35,3,px,seed=95),0,1);c=c*(1-.55*esp[...,None])+np.array([226,236,240],np.float64)*(.55*esp[...,None])   # espuma
            c=c[P:-P,P:-P];dd=dist[by-cy0:ey-cy0,bx-cx0:ex-cx0]
            a=(np.maximum(np.clip(dd/6.,0,1)**2*(3-2*np.clip(dd/6.,0,1)),.25)*opacity*(sel_m/255.))[...,None]
            roi=image[by:ey,bx:ex].astype(np.float64);image[by:ey,bx:ex]=np.clip(roi*(1-a)+c*a,0,255).astype(np.uint8)

# ------------------------------------------------------------------ vegetação (copas)
_COPAS={};_COPAS_MAX=500
def _ruido_rng(seed,n,m):
    r=np.random.default_rng(seed);return r.standard_normal((n,m)).astype(np.float32)
def copa(rx,ry,cor,esc,bri,h,ang_luz,SS=2):
    """copa de árvore vista de cima: cúpula de folhagem com tufos (altura), luz vinda de `ang_luz` (radianos, referencial da tela), contorno irregular e borda suave.
    Retorna RGBA uint8 de (2*ry+3)×(2*rx+3). Determinístico por (h, tamanho, luz)."""
    import cv2
    W=int(2*rx+3)*SS;Hh=int(2*ry+3)*SS;cx=W/2;cy=Hh/2;ax=rx*SS;ay=ry*SS
    ys,xs=np.mgrid[0:Hh,0:W].astype(np.float32);u=(xs-cx)/ax;v=(ys-cy)/ay;rho=np.sqrt(u*u+v*v);th=np.arctan2(v,u)
    seed=int(h*100000)%2**31;rng=np.random.default_rng(seed)
    harm=sum(rng.uniform(.02,.07)*np.sin(k*th+rng.uniform(0,6.28)) for k in (3,5,8,13));borda=1+harm                  # contorno de folhagem
    def ruido(escala):
        n=max(2,int(W/escala));m=max(2,int(Hh/escala));return cv2.resize(_ruido_rng(seed+int(escala),m,n),(W,Hh),interpolation=cv2.INTER_CUBIC)
    folha=.6*ruido(max(3,ax/2.2))+.4*ruido(max(2,ax/5.))+.15*ruido(max(2,ax/12.))
    dome=np.sqrt(np.clip(1-np.minimum(rho/borda,1)**2,0,1));alt=dome*(.75+.35*folha)
    gy,gx=np.gradient(cv2.GaussianBlur(alt,(0,0),max(.8,ax*.03)));L=np.array([np.cos(ang_luz),np.sin(ang_luz)],np.float32)
    claro=np.clip(.5-(gx*L[0]+gy*L[1])*ax*1.3+.30*folha+.25*(dome-.5),0,1)                                          # 0 = sombra de tufo, 1 = lado do sol
    cor=np.array(cor,np.float32);esc=np.array(esc,np.float32);bri=np.array(bri,np.float32)
    col=esc+(cor-esc)*np.clip(claro*1.6,0,1)[...,None];col=col+(bri-col)*np.clip((claro-.62)*2.2,0,1)[...,None]
    col=col*(.80+.20*dome)[...,None]                                                                               # centro mais alto = mais exposto
    a=np.clip((borda-rho)*ax/1.2,0,1);a=a*a*(3-2*a)
    pre=col*a[...,None];h2,w2=Hh//SS,W//SS
    pre=cv2.resize(pre[:h2*SS,:w2*SS],(w2,h2),interpolation=cv2.INTER_AREA);al=cv2.resize(a[:h2*SS,:w2*SS],(w2,h2),interpolation=cv2.INTER_AREA)
    return np.dstack([np.clip(pre/np.maximum(al[...,None],1e-4),0,255),al*255]).astype(np.uint8)
def copa_cache(rx,ry,cor,esc,bri,h,ang_luz):
    q=int(round(rx/2.))*2 or 2;qy=int(round(ry/2.))*2 or 2;k=(q,qy,tuple(cor),tuple(esc),int(h*12),int(round(ang_luz/(np.pi/8))))
    s=_COPAS.get(k)
    if s is None:
        if len(_COPAS)>=_COPAS_MAX:_COPAS.pop(next(iter(_COPAS)))
        s=copa(q,qy,cor,esc,bri,int(h*12)/12.,k[-1]*(np.pi/8));_COPAS[k]=s
    return s
def blit_copa(im,cx,cy,sp):
    h,w=sp.shape[:2];x0=int(round(cx-w/2.));y0=int(round(cy-h/2.));H,W=im.shape[:2]
    xa,ya,xb,yb=max(0,x0),max(0,y0),min(W,x0+w),min(H,y0+h)
    if xa>=xb or ya>=yb:return
    s=sp[ya-y0:yb-y0,xa-x0:xb-x0];a=s[...,3:4].astype(np.float32)/255;roi=im[ya:yb,xa:xb].astype(np.float32);im[ya:yb,xa:xb]=np.clip(roi*(1-a)+s[...,:3]*a,0,255).astype(np.uint8)

# ------------------------------------------------------------------ tinta de sinalização horizontal (zebrados, faixas de pedestre, setas, linhas)
def _voronoi_borda(X,Y,s,seed):
    """distância (m) à borda da célula de Voronoi mais próxima (placas de tinta craquelada); X,Y vetores 1-D."""
    ix=np.floor(X/s);iy=np.floor(Y/s);d1=np.full(X.shape,9.);d2=np.full(X.shape,9.)
    for dx in(-1,0,1):
        for dy in(-1,0,1):
            jx=ix+dx;jy=iy+dy;px_=(jx+.15+.7*_h(jx,jy,seed))*s;py_=(jy+.15+.7*_h(jx,jy,seed+5))*s
            d=np.hypot(X-px_,Y-py_);n=d<d1;d2=np.where(n,d1,np.where(d<d2,d,d2));d1=np.where(n,d,d1)
    return (d2-d1)*.5

def tinta(im,pre,A,m,desgaste=.12):
    """realismo da tinta aplicada (fotos de referência: faixa amarela com agregado aparecendo, seta branca craquelada em placas):
    manchas de desgaste ancoradas no mundo; de perto, grãos do asfalto furando a tinta, craquelê em placas nos trechos mais gastos,
    microbrilho de esferas refletivas e sombrinha de espessura. A (2×3) leva pixel do `im` → mundo. Não mexe fora da pintura."""
    import cv2
    diff=np.any(im!=pre,axis=2)
    if not diff.any():return im
    ys,xs=np.nonzero(diff);y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
    sel=diff[y0:y1,x0:x1];gy,gx=np.nonzero(sel)
    px_=gx+x0+.5;py_=gy+y0+.5;X=(A[0,0]*px_+A[0,1]*py_+A[0,2]).astype(np.float64);Y=(A[1,0]*px_+A[1,1]*py_+A[1,2]).astype(np.float64)
    w=np.clip(.5+.5*fbm(X,Y,2.4,4,m,seed=301),0,1)                                    # manchas de desgaste (grandes → finas)
    perda=np.clip(desgaste*(.5+1.3*w)+.10*np.clip(fbm(X,Y,.35,3,m,seed=302)+.2,0,1),0,.62)
    roi=im[y0:y1,x0:x1].astype(np.float32);base=pre[y0:y1,x0:x1].astype(np.float32)
    cur=roi[sel];bas=base[sel]
    if m<.03:                                                                          # de perto
        regiao=np.clip((vn(X,Y,1.3,seed=310)-.40)/.35,0,1)*np.clip(desgaste/.12,0,2.5)      # onde a tinta está mais gasta
        furo=np.clip((vn(X,Y,max(.006,m*1.3),seed=311)-(.84-.12*np.clip(regiao,0,1)))/.05,0,1)   # grãos do asfalto aparecendo
        perda=np.clip(perda+.8*furo*(.55+.45*np.clip(regiao,0,1)),0,.95)
        if m<.012:                                                                     # craquelê: placas de ~7 cm com fendas finas
            Xw=X+.03*fbm(X,Y,.12,3,m,seed=322);Yw=Y+.03*fbm(X,Y,.12,3,m,seed=323)
            bd=_voronoi_borda(Xw,Yw,.09,seed=320)*np.where(_h(np.floor(X/.09),np.floor(Y/.09),324)<.35,.4,1.);fenda=np.clip(1-bd/max(.0035,m*1.6),0,1)*np.clip(regiao*1.4,0,1)
            perda=np.clip(perda+.85*fenda,0,.95)
            cur=cur*(1+.05*(_h(np.floor(X/.07),np.floor(Y/.07),321)-.5))[:,None]       # cada placa um pouco diferente
    a=1-perda
    out=bas+(cur-bas)*a[:,None]
    if m<.07:                                                                          # esferas refletivas
        br=np.clip((vn(X,Y,max(.012,m*1.1),seed=303)-.93)/.07,0,1);out=out+(br*28)[:,None]
    roi[sel]=out
    if m<.07:
        borda=cv2.dilate(sel.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)&~sel;roi[borda]*=.93
    im[y0:y1,x0:x1]=np.clip(roi,0,255).astype(np.uint8);return im

def texturizar_tela(im,mask,screen,kind='concreto',seed=17):
    """textura (concreto novo/existente) numa região da TELA (máscara booleana), ancorada em coordenadas do mundo — para estruturas desenhadas por primitivas."""
    if not mask.any():return
    ys,xs=np.nonzero(mask);y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
    # mapeamento tela→mundo (afim) obtido de 3 pontos conhecidos pela função screen (mundo→tela)
    o=np.array([0.,0.]);S=np.asarray(screen(np.array([o,o+[1.,0.],o+[0.,1.]])),float);M=np.array([S[1]-S[0],S[2]-S[0]]).T          # px por metro em x,y mundo
    Mi=np.linalg.inv(M);gx,gy=np.meshgrid(np.arange(x0,x1)+.5,np.arange(y0,y1)+.5)
    W=np.einsum('ij,jhw->ihw',Mi,np.stack([gx-S[0,0],gy-S[0,1]]));X=W[0].astype(np.float64);Y=W[1].astype(np.float64);px=float(1/np.sqrt(abs(np.linalg.det(M)))) if abs(np.linalg.det(M))>1e-12 else 1.
    sub=im[y0:y1,x0:x1].astype(np.float64);fn=_concreto_exist if kind=='existente' else _concreto_novo
    out=np.clip(fn(sub,X,Y,px,seed),0,255).astype(np.uint8);m=mask[y0:y1,x0:x1]
    roi=im[y0:y1,x0:x1];roi[m]=out[m]
