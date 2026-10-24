"""1.36: ambiente do vídeo — clima (nublado, chuva, neblina), sombras pela hora do sol, comparação antes/depois e
câmera por pontos-chave. Tudo desligado por padrão: o vídeo fica igual ao das versões anteriores."""
import math
import numpy as np,cv2

# ---------------- sol ----------------
SOMBRA_VEICULO=np.array([.25,-.38]);SOMBRA_OAE=np.array([.35,-.55])   # sol fixo a noroeste (como antes)
def sol(hora):
    """Azimute (graus, a partir do norte, sentido horário) e elevação aproximados para o Brasil (~20° S): o sol nasce a
    leste, passa ao norte ao meio-dia (≈ 70° de elevação) e se põe a oeste."""
    h=float(np.clip(hora,6,18));az=(90-(h-6)*15)%360;el=max(10.,70*math.sin(math.pi*(h-6)/12))
    return az,el
def vetor_sombra(hora):
    """Deslocamento da sombra no chão por metro de altura (x = leste, y = norte)."""
    az,el=sol(hora);a=math.radians(az);L=1/math.tan(math.radians(el))
    return -np.array([math.sin(a),math.cos(a)])*L

# ---------------- clima ----------------
def clima(scene,im,t,header,footer,via=None):
    """Aplica o clima à área do mapa (entre o cabeçalho e o rodapé). via: máscara da pista na tela (opcional)."""
    tipo=getattr(scene.s,'weather','limpo')
    if tipo=='limpo':return
    k=float(getattr(scene.s,'weather_intensity',.6));y0,y1=header,scene.H-footer;roi=im[y0:y1].astype(np.float32)
    g=roi.mean(2,keepdims=True)
    if tipo in ('nublado','chuva'):
        sat=.45*k if tipo=='nublado' else .55*k;esc=1-(.14 if tipo=='nublado' else .24)*k
        roi=(roi*(1-sat)+g*sat)*esc;roi[:,:,2]+=6*k;roi[:,:,0]-=3*k
    if tipo=='chuva':
        if via is not None and via[y0:y1].any():
            # Pista molhada: mais escura, com brilho difuso (reflexo do céu) e manchas d'água.
            v=via[y0:y1].astype(np.float32)
            v=cv2.GaussianBlur(v,(0,0),1.)[:,:,None]
            n=_ruido(scene,roi.shape[:2])[:,:,None]
            poca=np.clip(n-.35,0,1.5)   # poças: manchas mais claras (reflexo do céu)
            roi=roi*(1-.34*k*v)+v*k*np.array([26,30,36],np.float32)*poca
        roi=_gotas(scene,roi,t,k)
    if tipo=='neblina':
        H=roi.shape[0];grad=np.linspace(1,.75,H)[:,None,None]   # um pouco mais densa no alto da tela (longe)
        a=np.clip(.55*k*grad,0,.8);roi=roi*(1-a)+np.array([206,210,214],np.float32)*a
        roi=cv2.GaussianBlur(roi,(0,0),.6*k)
    im[y0:y1]=np.clip(roi,0,255).astype(np.uint8)

def _ruido(scene,shape):
    r=getattr(scene,'_clima_ruido',None)
    if r is None or r.shape!=shape:
        rng=np.random.default_rng(7);small=rng.standard_normal((max(2,shape[0]//24),max(2,shape[1]//24))).astype(np.float32)
        r=cv2.resize(small,(shape[1],shape[0]),interpolation=cv2.INTER_CUBIC);scene._clima_ruido=r
    return r

def _gotas(scene,roi,t,k):
    """Riscos de chuva (determinísticos por quadro: o mesmo vídeo sai sempre igual)."""
    H,W=roi.shape[:2];sc=max(.5,scene.scale);n=int(1400*k*W*H/(1920*900))
    rng=np.random.default_rng(int(round(t*30))+11)
    x=rng.uniform(0,W,n);y=rng.uniform(0,H,n);L=rng.uniform(20,48,n)*sc;ang=math.radians(78)
    dx=np.cos(ang)*L;dy=np.sin(ang)*L
    lay=np.zeros((H,W),np.uint8);th=max(1,int(round(1.6*sc)))
    for a,b,c,d in zip(x,y,x+dx,y+dy):cv2.line(lay,(int(a),int(b)),(int(c),int(d)),255,th,cv2.LINE_AA)
    lay=lay[:,:,None].astype(np.float32)/255
    return roi*(1-.5*k*lay)+np.array([214,222,230],np.float32)*(.5*k*lay)

# ---------------- antes / depois ----------------
def antes_depois(scene,t):
    """Fração da divisória (0 a 1) nos últimos segundos do vídeo, ou None. A divisória varre a tela da esquerda para a
    direita: à esquerda, DEPOIS (com o projeto); à direita, ANTES (só a imagem aérea)."""
    if not getattr(scene.s,'before_after',False):return None
    T=float(scene.s.duration_s);d=min(float(scene.s.before_after_s),T*.5);t0=T-d
    if t<t0:return None
    f=np.clip((t-t0)/max(d*.8,.01),0,1);return float(f*f*(3-2*f))

def divisoria(scene,im,f,header,footer,font):
    from PIL import Image,ImageDraw
    x=int(round(f*scene.W));y0,y1=header,scene.H-footer;sc=max(scene.scale,.7)
    cv2.line(im,(x,y0),(x,y1),(255,255,255),max(2,int(4*sc)),cv2.LINE_AA)
    r=int(22*sc);cy=(y0+y1)//2;cv2.circle(im,(x,cy),r,(255,255,255),-1,cv2.LINE_AA);cv2.circle(im,(x,cy),r,(40,40,40),max(1,int(2*sc)),cv2.LINE_AA)
    for s_ in (-1,1):
        p=np.array([[x+s_*int(6*sc),cy-int(8*sc)],[x+s_*int(14*sc),cy],[x+s_*int(6*sc),cy+int(8*sc)]],np.int32);cv2.fillPoly(im,[p],(40,40,40),cv2.LINE_AA)
    for txt,xx,ok in [('DEPOIS',x-int(20*sc),x>int(160*sc)),('ANTES',x+int(20*sc),x<scene.W-int(160*sc))]:
        if not ok:continue
        ft=font(int(26*sc),True);w=int(ft.getlength(txt))+int(24*sc);h=int(40*sc);bx=xx-w if txt=='DEPOIS' else xx;by=y0+int(24*sc)
        box=Image.new('RGBA',(w,h),(8,22,35,200));ImageDraw.Draw(box).text((int(12*sc),int(5*sc)),txt,font=ft,fill='#ffffff')
        a=np.array(box);al=a[:,:,3:4].astype(np.float32)/255;bx=max(0,min(scene.W-w,bx))
        roi=im[by:by+h,bx:bx+w].astype(np.float32);im[by:by+h,bx:bx+w]=np.clip(roi*(1-al)+a[:,:,:3]*al,0,255).astype(np.uint8)

# ---------------- câmera por pontos-chave ----------------
def pose_pontos(scene,t):
    """Voo entre os pontos-chave: parada em cada um (hold_s) e deslocamento suave até o próximo; a duração do vídeo é
    repartida proporcionalmente. Devolve (centro, largura, título) ou None se houver menos de 2 pontos."""
    K=getattr(scene.s,'camera_keys',None) or []
    if getattr(scene.s,'camera_mode','obras')!='pontos' or len(K)<2:return None
    P=[np.array([k.x,k.y],float) for k in K];Wd=[float(k.width_m) for k in K]
    mov=[]
    for a,b,wa,wb in zip(P[:-1],P[1:],Wd[:-1],Wd[1:]):
        d=np.linalg.norm(b-a)/max(min(wa,wb),1.)   # distância em “telas”
        mov.append(2.+2.5*math.log1p(d)+1.5*abs(math.log(wb/wa)))
    seg=[];tot=0.
    for i,k in enumerate(K):
        seg.append(('para',i,float(k.hold_s)));tot+=float(k.hold_s)
        if i<len(mov):seg.append(('vai',i,mov[i]));tot+=mov[i]
    esc=float(scene.s.duration_s)/max(tot,1e-6);acc=0.
    for tipo,i,d in seg:
        d*=esc
        if t<=acc+d or (tipo,i)==seg[-1][:2]:
            if tipo=='para':return P[i],Wd[i],K[i].title
            f=float(np.clip((t-acc)/max(d,1e-6),0,1));f=f*f*(3-2*f)
            # Zoom “de voo”: afasta um pouco no meio do deslocamento longo (como um drone).
            wa,wb=Wd[i],Wd[i+1];dist=np.linalg.norm(P[i+1]-P[i]);extra=min(1.8,dist/max(wa,wb)*.35)
            w=math.exp(math.log(wa)*(1-f)+math.log(wb)*f)*(1+extra*math.sin(math.pi*f))
            return P[i]*(1-f)+P[i+1]*f,w,K[i+1].title if f>.5 else K[i].title
        acc+=d
    return P[-1],Wd[-1],K[-1].title
