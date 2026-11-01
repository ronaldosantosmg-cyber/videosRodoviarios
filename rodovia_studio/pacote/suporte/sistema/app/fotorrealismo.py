"""2.46: atmosfera fotográfica — hora do dia (amanhecer, dia, entardecer, noite) e tempo (nublado, chuva, neblina) com comportamento físico plausível:
balanço de branco, exposição, curva de contraste, brilho (bloom), vinheta e clarão do sol baixo; pista molhada com reflexo especular, poças com ondulações e
respingos; chuva em 3 camadas de profundidade; neblina com profundidade, véus animados e halos nas luzes. Desligado por padrão (photo_atmosphere=False).
Imagem em RGB uint8. Determinístico por quadro: o mesmo vídeo sai sempre igual."""
import math
import numpy as np,cv2

PRESET_H={'amanhecer':6.6,'dia':12.,'entardecer':17.4}
def _ss(x):x=np.clip(x,0.,1.);return x*x*(3-2*x)
def hora(s):
    tod=getattr(s,'time_of_day','hora_do_sol')
    if tod=='noite':return None
    return PRESET_H.get(tod,float(getattr(s,'sun_hour',15)))
def perfil(s):
    h=hora(s)
    if h is None:return dict(wb=np.array([.80,.90,1.20],np.float32),exp=.52,sat=.62,contraste=.05,vinheta=.5,bloom=.55,noite=1.,fog=(150,165,190),az=None,glare=0.)
    manha=float(_ss((8.5-h)/2.5));tarde=float(_ss((h-15.5)/2.5));ocaso=float(_ss((h-17.2)/.8));dour=max(manha,tarde)
    wb=1+(np.array([1.13,.97,.76],np.float32)-1)*dour*(1-ocaso)+(np.array([.88,.95,1.18],np.float32)-1)*ocaso
    if manha>tarde:wb=wb*np.array([1.02,.97,1.10],np.float32)   # amanhecer: dourado mais frio e rosado           # amanhecer um pouco mais rosado
    from .ambiente import sol
    az=sol(h)[0]
    return dict(wb=wb.astype(np.float32),exp=1-.14*dour-.28*ocaso,sat=1+.10*dour-.22*ocaso,contraste=.15*(1-.5*dour),vinheta=.10+.28*dour+.22*ocaso,bloom=.05+.20*dour+.30*ocaso,
                noite=0.,fog=tuple(int(v) for v in (np.array([206,210,214])*wb*np.array([1,1,1])).clip(0,255)),az=az,glare=.14*dour*(1-ocaso))
def _blur(a,s):return cv2.GaussianBlur(a,(0,0),max(.3,s))
def _noise(scene,shape,esc=24,seed=7,key='_foto_ruido'):
    c=getattr(scene,key,None)
    if c is None or c.shape!=shape:
        rng=np.random.default_rng(seed);small=rng.standard_normal((max(2,shape[0]//esc),max(2,shape[1]//esc))).astype(np.float32);c=cv2.resize(small,(shape[1],shape[0]),interpolation=cv2.INTER_CUBIC);setattr(scene,key,c)
    return c
def _wisps(scene,shape,t):
    """véus de neblina: ruído de baixa frequência que deriva lentamente (rola em torno, sem saltos)."""
    base=_noise(scene,(shape[0]*2,shape[1]*2),esc=140,seed=21,key='_foto_veu')
    ox=int(t*14)%base.shape[1];oy=int(t*5)%base.shape[0];r=np.roll(np.roll(base,-ox,1),-oy,0)[:shape[0],:shape[1]]
    return np.clip(.5+.35*r,0,1)

def _luz_brilho(roi,limiar=205.):
    lum=roi.mean(2);return np.clip((lum-limiar)/(255-limiar),0,1)[:,:,None]

def _chuva(scene,roi,t,k,via,sc):
    H,W=roi.shape[:2];lum=roi.mean(2,keepdims=True)
    v=(cv2.GaussianBlur(via.astype(np.float32),(0,0),1.)[:,:,None] if via is not None else np.zeros((H,W,1),np.float32))
    n=_noise(scene,(H,W))[:,:,None];poca=_ss((n-.9)/.5)*v                          # poças dentro da pista
    # asfalto molhado: mais escuro e saturado; fora da pista (terreno, vegetação) levemente mais escuro e saturado
    roi=roi*(1-.30*k*v-.10*k*(1-v))+(roi-lum)*(.18*k)*(.6*v+.4*(1-v))
    # reflexo especular: luzes e faixas claras se alongam (borrão anisotrópico) e se somam só na pista molhada
    b=_luz_brilho(roi,190.)*roi;rf=cv2.GaussianBlur(b,(0,0),sigmaX=2.5*sc,sigmaY=14*sc)
    roi=roi+rf*(.55*k)*(v*.6+poca)
    roi=roi*(1-.35*k*poca)+poca*k*.35*np.array([150,168,188],np.float32)*(lum/140)**.5          # poça: espelho do céu
    # ondulações nas poças
    lay=np.zeros((H,W),np.float32);fase=(t*1.6)%1.;rng=np.random.default_rng(int(t*1.6)+3)
    pts=rng.uniform(0,1,(int(70*k),2))*[W,H]
    for (x,y) in pts:
        xi,yi=int(x),int(y)
        if poca[yi,xi,0]<.35:continue
        for off,al in ((0,1.),(.5,.6)):
            f=(fase+off)%1.;cv2.ellipse(lay,(xi,yi),(max(1,int((3+22*f)*sc)),max(1,int((2+13*f)*sc))),0,0,360,float((1-f)*al),1,cv2.LINE_AA)
    roi=roi+lay[:,:,None]*70*k
    # 3 camadas de chuva (distantes: curtas/fracas; próximas: longas/fortes)
    for camada,(n0,comp,al,esp,vel) in enumerate(((1100,16,.16,1,.55),(650,30,.28,1,1.),(260,56,.42,2,1.8))):
        rng=np.random.default_rng(int(t*30)*7+camada*101+11);n=int(n0*k*W*H/(1920*900))
        x=rng.uniform(0,W,n);y=rng.uniform(0,H,n);L=comp*sc*rng.uniform(.8,1.2,n);ang=math.radians(80);L2=L*(1+.2*vel)
        lay=np.zeros((H,W),np.uint8)
        for a,bb,l in zip(x,y,L2):cv2.line(lay,(int(a),int(bb)),(int(a+math.cos(ang)*l),int(bb+math.sin(ang)*l)),255,max(1,int(round(esp*sc))),cv2.LINE_AA)
        m=cv2.GaussianBlur(lay,(0,0),.5+.4*camada).astype(np.float32)[:,:,None]/255
        roi=roi*(1-al*k*m)+np.array([220,228,238],np.float32)*(al*k*m)
    # véu de chuva e céu cinza
    roi=roi*(1-.10*k)+np.array([170,178,188],np.float32)*(.10*k)
    return roi

def _neblina(scene,roi,t,k,pf,sc):
    H,W=roi.shape[:2];yy,xx=np.mgrid[0:H,0:W].astype(np.float32);d=np.hypot((xx-W/2)/(W/2),(yy-H*.55)/(H*.55))     # distância ao foco da câmera
    dens=np.clip(.22*k+.50*k*d**1.4,0,.94)[:,:,None]
    dens=np.clip(dens*(.75+.5*_wisps(scene,(H,W),t)[:,:,None]),0,.95)
    lonj=cv2.GaussianBlur(roi,(0,0),1.2*sc+2.5*k);m=np.clip(d,0,1)[:,:,None]*.9
    roi=roi*(1-m)+lonj*m                                                          # detalhe distante perde nitidez
    cor=np.array(pf['fog'],np.float32);lum=roi.mean(2,keepdims=True)
    roi=roi*(1-dens)+cor*dens
    roi=(roi-lum)*(1-.35*k)+lum                                                  # dessatura
    br=_luz_brilho(roi,200.)*roi;roi=roi+cv2.GaussianBlur(br,(0,0),9*sc)*(.8*k)    # halos: a luz se espalha na névoa
    return roi

def aplicar(scene,im,t,y0,y1,via=None):
    s=scene.s;tipo=getattr(s,'weather','limpo');k=float(getattr(s,'weather_intensity',.6));pf=perfil(s);sc=max(.5,scene.scale)
    roi=im[y0:y1].astype(np.float32);H,W=roi.shape[:2];v=via[y0:y1] if via is not None else None
    lum=roi.mean(2,keepdims=True)
    if tipo=='nublado':
        roi=(roi*(1-.5*k)+lum*.5*k)*(1-.13*k)+np.array([-2,0,7],np.float32)*k;roi=(roi-roi.mean())*(1-.18*k)+roi.mean()        # luz difusa, baixo contraste
    elif tipo=='chuva':roi=_chuva(scene,roi,t,k,v,sc)
    elif tipo=='neblina':roi=_neblina(scene,roi,t,k,pf,sc)
    # ---- hora do dia ----
    ja_noite=float(getattr(scene,'_night',0.))
    f=1-ja_noite*.7 if pf['noite'] else 1.                                       # se o escurecimento de faróis já agiu, não escurece de novo
    nublado=1-.55*k*(tipo in('nublado','chuva','neblina'))                        # céu fechado: sol/calor menos intensos
    wb=1+(pf['wb']-1)*(nublado if pf['noite']==0 else 1)*f
    roi=roi*wb*(1-(1-pf['exp'])*f)
    lum=roi.mean(2,keepdims=True);roi=(roi-lum)*(1+(pf['sat']-1)*f)+lum
    c=pf['contraste']*(1-.6*(tipo!='limpo')*k)
    if c>0:x=np.clip(roi/255,0,1);roi=255*(x+c*(3*x*x-2*x**3-x))                   # curva em S
    if pf['noite'] and f>0:roi[...,2]+=7*f
    if pf['bloom']>0:
        br=_luz_brilho(roi,215.)*roi;roi=roi+_blur(br,7*sc)*pf['bloom']+_blur(br,22*sc)*pf['bloom']*.6
    if pf['glare']>0 and pf['az'] is not None:                                   # sol baixo: clarão quente vindo do lado do sol
        a=math.radians(pf['az']);dx,dy=math.sin(a),-math.cos(a);yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
        p=((xx/W-.5)*dx+(yy/H-.5)*dy)+.5;gl=_ss((p-.45)/.55)[:,:,None]*pf['glare']*(1-.7*(tipo!='limpo')*k)
        roi=roi+gl*np.array([255,196,120],np.float32)*.55
    yy,xx=np.mgrid[0:H,0:W].astype(np.float32);r=np.hypot((xx-W/2)/(W/2),(yy-H/2)/(H/2));roi=roi*(1-pf['vinheta']*_ss((r-.45)/.9)[:,:,None]*.6)
    if pf['noite'] or pf['exp']<.8:                                              # grão do sensor em pouca luz
        rng=np.random.default_rng(int(t*30)+5);roi=roi+rng.standard_normal((H,W,1)).astype(np.float32)*(2.6*(1-pf['exp'])*4)
    im[y0:y1]=np.clip(roi,0,255).astype(np.uint8)
