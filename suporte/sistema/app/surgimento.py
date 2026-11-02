"""3.1: surgimento progressivo e destaque do que é projetado enquanto aparece (sinalização, zebrados, placas, engenharia).
Só apresentação: não altera rede, tráfego nem geometria. Existentes seguem `existing_visibility`."""
import numpy as np,cv2
COR=(150,230,255)   # RGB: realce frio, discreto, sobre o branco/amarelo da pintura
JANELA=45.          # m atrás da frente de avanço em que o realce decai

def ligado(s):return bool(getattr(s,'highlight_projected',True))

def peso(ch,frente,janela=JANELA):
    """1 na frente de avanço, decaindo a 0 em `janela` m atrás; 0 fora do que já foi revelado."""
    ch=np.asarray(ch,float);w=1-(frente-ch)/max(janela,1e-6)
    return np.where(ch<=frente,np.clip(w,0,1),0.)

def cadeia(scene,pontos):
    """menor estação (m) do eixo associada a um conjunto de pontos; vazio/não finito → 0."""
    p=np.asarray(pontos,float).reshape(-1,2)
    p=p[np.isfinite(p).all(1)]
    if not len(p):return 0.
    if len(p)>24:p=p[np.linspace(0,len(p)-1,24).astype(int)]
    return float(np.min(np.asarray(scene.ch)[scene.tree.query(p)[1]]))

def visivel(scene,pontos,frente,existente=False,folga=25.):
    """True se a feição já foi alcançada pela frente (ou é existente e está 'já exibida')."""
    if existente and getattr(scene.s,'existing_visibility','initial')=='initial':return True
    return cadeia(scene,pontos)<=frente+folga

def _misturar(im,mascara,forca=.5):
    a=(mascara.astype(np.float32)/255*forca)[:,:,None]
    im[:]=np.clip(im*(1-a)+np.asarray(COR,np.float32)*a,0,255).astype(np.uint8)

def sinalizacao(scene,im,cam,width,progress,m):
    """realce das marcas e zebrados que acabaram de aparecer."""
    if progress>=1 or not ligado(scene.s) or width>=3000 or progress<0:return
    frente=progress*scene.length;glow=np.zeros(im.shape[:2],np.uint8)
    if len(getattr(scene,'markings',())):
        if not hasattr(scene,'marking_centers'):scene.marking_centers=scene.markings.mean(1)
        if not hasattr(scene,'marking_chains'):scene.marking_chains=scene.ch[scene.tree.query(scene.marking_centers)[1]]
        near=np.linalg.norm(scene.marking_centers-cam,axis=1)<width*.75
        w=peso(scene.marking_chains,frente)*near
        idx=np.flatnonzero(w>.02)
        if len(idx):
            seg=scene.screen(scene.markings[idx].reshape(-1,2),cam,width).reshape(-1,2,2)
            esp=max(2,round(.45/m))
            for s_,k in zip(seg,idx):cv2.line(glow,tuple(s_[0].astype(int)),tuple(s_[1].astype(int)),int(255*w[k]),esp,cv2.LINE_AA)
    items=getattr(scene,'paint_items',None)
    if items:
        pw=peso(scene.paint_chains,frente)*(np.linalg.norm(scene.paint_centers-cam,axis=1)<width*.75)
        for k in np.flatnonzero(pw>.02):
            for ring in items[k][2]:
                q=np.rint(scene.screen(ring,cam,width)).astype(np.int32)
                cv2.fillPoly(glow,[q],int(255*pw[k]),cv2.LINE_AA);cv2.polylines(glow,[q],True,int(255*pw[k]),max(2,round(.4/m)),cv2.LINE_AA)
    if glow.any():
        s=max(1.,.35/m);glow=cv2.GaussianBlur(glow,(0,0),s);_misturar(im,np.minimum(glow,255).astype(np.uint8),.55)

def halo(scene,im,x,y,r,w):
    """halo circular suave (placas, pórticos) com peso `w` ∈ (0,1]."""
    if w<=.02:return
    x0,y0=max(0,int(x-r)),max(0,int(y-r));x1,y1=min(im.shape[1],int(x+r)+1),min(im.shape[0],int(y+r)+1)
    if x1<=x0 or y1<=y0:return
    yy,xx=np.ogrid[y0:y1,x0:x1];d=np.sqrt((xx-x)**2+(yy-y)**2)/max(r,1)
    a=(np.clip(1-d,0,1)**1.5*.55*w)[:,:,None];roi=im[y0:y1,x0:x1]
    roi[:]=np.clip(roi*(1-a)+np.asarray(COR,np.float32)*a,0,255).astype(np.uint8)
