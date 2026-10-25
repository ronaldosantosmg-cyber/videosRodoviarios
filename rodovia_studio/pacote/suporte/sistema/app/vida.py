"""1.37: vegetação (árvores, ipês, eucaliptos, palmeiras, arbustos, cerca-viva) e pedestres (faixas de pedestre,
passarelas e caminhos marcados). Vistos de cima, ancorados em metros, com sombra pelo sol do projeto."""
import math
import numpy as np,cv2
from shapely.geometry import Polygon,Point as SPoint

# tipo -> (cor da copa, cor da sombra interna, cor do brilho, altura/diâmetro, forma)
VEG={'arvore':((58,104,48),(34,66,30),(104,150,74),1.0,'copa'),'ipe':((226,184,40),(160,120,24),(250,222,96),1.0,'copa'),
     'eucalipto':((84,112,82),(52,74,52),(128,156,118),2.2,'estreita'),'palmeira':((70,120,52),(40,74,32),(122,170,88),1.6,'palmeira'),
     'arbusto':((52,92,44),(30,58,26),(90,134,66),.6,'copa'),'cerca_viva':((48,96,42),(28,60,26),(86,132,64),.5,'copa')}

def _pontos_area(a):
    """Plantas da área, sempre no mesmo lugar: grade com sorteio (semente da área) dentro do polígono."""
    P=np.array([[p.x,p.y] for p in a.points]);poly=Polygon(P)
    if not poly.is_valid:poly=poly.buffer(0)
    if poly.is_empty:return []
    area=poly.area;n=int(min(4000,max(1,area*a.density/1000)))
    rng=np.random.default_rng(a.seed or 1);x0,y0,x1,y1=poly.bounds;passo=math.sqrt(area/max(n,1))
    xs=np.arange(x0+passo/2,x1,passo);ys=np.arange(y0+passo/2,y1,passo);out=[]
    for y in ys:
        for x in xs:
            q=(x+rng.uniform(-.42,.42)*passo,y+rng.uniform(-.42,.42)*passo)
            if poly.contains(SPoint(q)):out.append((q[0],q[1],a.kind,a.size_m*rng.uniform(.75,1.25)))
    return out

def prepare(scene):
    s=scene.s;T=[(p.x,p.y,p.kind,p.size_m) for p in getattr(s,'vegetation_points',[])]
    for a in getattr(s,'vegetation_areas',[]):
        if not a.enabled:continue
        L=_pontos_area(a)
        sup=getattr(scene,'surface',None)
        if L and sup is not None:   # áreas não plantam sobre pista, acostamento, canteiro pavimentado ou OAE
            px=np.rint(scene.worldpx(np.array([[t[0],t[1]] for t in L]))).astype(int);H,W=sup.shape[:2]
            dentro=(px[:,0]>=0)&(px[:,0]<W)&(px[:,1]>=0)&(px[:,1]<H);cod=np.zeros(len(L),np.uint8)
            cod[dentro]=sup[px[dentro,1],px[dentro,0]];L=[t for t,c in zip(L,cod) if c not in (1,2,3,4,8)]
        T+=L
    if not T:return None
    A=np.array([[t[0],t[1]] for t in T]);ch=scene.ch[scene.tree.query(A)[1]]
    return {'xy':A,'kind':[t[2] for t in T],'size':np.array([t[3] for t in T]),'chain':ch,'h':np.array([abs(hash((round(t[0],2),round(t[1],2))))%1000/1000 for t in T])}

def _poly_copa(c,r,n,h,irreg):
    ang=np.linspace(0,2*np.pi,n,endpoint=False)+h*6.28
    rr=r*(1+irreg*np.sin(ang*5+h*20)*.5+irreg*np.sin(ang*3+h*7)*.5)
    return np.column_stack([c[0]+rr*np.cos(ang),c[1]+rr*np.sin(ang)]).astype(np.int32)

def draw_vegetation(scene,im,cam,width,progress,header,footer):
    if not hasattr(scene,'_veg'):scene._veg=prepare(scene)
    V=scene._veg
    if V is None or width>4000:return
    m=scene.W/width   # px por metro
    vis=V['chain']<=progress*scene.length+25
    if not vis.any():return
    Q=scene.screen(V['xy'],cam,width);r=V['size']*m/2
    ok=vis&(Q[:,0]>-r)&(Q[:,0]<scene.W+r)&(Q[:,1]>header-r)&(Q[:,1]<scene.H-footer+r)&(r>=.8)
    if not ok.any():return
    sv=scene.sombra_veiculo;R=scene.R;dir_scr=np.array([sv@R[:,0],-(sv@R[:,1])])   # sombra em px por metro de altura
    sh=np.zeros(im.shape[:2],np.uint8)
    idx=np.flatnonzero(ok);idx=idx[np.argsort(Q[idx,1])]
    for i in idx:
        k=V['kind'][i];hgt=V['size'][i]*VEG[k][3];c=Q[i]+dir_scr*hgt*m*.55;rr=max(1.,r[i]*(.55 if VEG[k][4]=='estreita' else 1))
        cv2.fillPoly(sh,[_poly_copa(c,rr,14,V['h'][i],.12)],255,cv2.LINE_AA)
    y0,y1=header,scene.H-footer;ys,xs=np.nonzero(sh[y0:y1])
    if len(ys):   # sombra suavizada só no retângulo que tem sombra
        b=int(max(2,3*m*.3));ya,yb=max(0,ys.min()-b),min(y1-y0,ys.max()+b+1);xa,xb=max(0,xs.min()-b),min(scene.W,xs.max()+b+1)
        reg=cv2.GaussianBlur(sh[y0+ya:y0+yb,xa:xb],(0,0),max(.8,1.2*m*.3)).astype(np.float32)/255
        roi=im[y0+ya:y0+yb,xa:xb];roi[:]=(roi*(1-.45*reg)[:,:,None]).astype(np.uint8)
    for i in idx:
        k=V['kind'][i];cor,esc,bri,_,forma=VEG[k];q=Q[i];rr=max(1.,r[i]);h=V['h'][i]
        var=.88+.24*h;cor=tuple(int(min(255,c*var)) for c in cor)
        if forma=='palmeira':
            for j in range(8):
                a=h*6.28+j*math.pi/4;p2=(int(q[0]+rr*math.cos(a)),int(q[1]+rr*math.sin(a)))
                cv2.line(im,(int(q[0]),int(q[1])),p2,esc,max(1,int(rr*.28)),cv2.LINE_AA);cv2.line(im,(int(q[0]),int(q[1])),p2,cor,max(1,int(rr*.16)),cv2.LINE_AA)
            cv2.circle(im,(int(q[0]),int(q[1])),max(1,int(rr*.18)),(96,82,52),-1,cv2.LINE_AA);continue
        rx=rr*(.55 if forma=='estreita' else 1);ry=rr if forma=='estreita' else rx
        sol=-dir_scr/max(np.linalg.norm(dir_scr),1e-6)
        cv2.ellipse(im,(int(q[0]),int(q[1])),(max(1,int(rx)),max(1,int(ry))),0,0,360,esc,-1,cv2.LINE_AA)
        if rx<6:   # longe: copa simples (rápido)
            if rx>=2.5:cv2.circle(im,(int(q[0]),int(q[1])),max(1,int(rx*.7)),cor,-1,cv2.LINE_AA)
            continue
        n=6 if forma!='estreita' else 4
        for j in range(n):   # copa em tufos (folhagem), iluminada do lado do sol
            a=h*6.28+j*2*math.pi/n;d=.42+.12*math.sin(h*40+j)
            c=q+np.array([math.cos(a)*rx*d,math.sin(a)*ry*d]);rj=max(1,int(rx*(.5+.1*math.cos(h*30+j))))
            lado=float(np.dot([math.cos(a),math.sin(a)],sol))
            tom=tuple(int(min(255,cc*(1+.10*lado))) for cc in cor)
            cv2.circle(im,(int(c[0]),int(c[1])),rj,tom,-1,cv2.LINE_AA)
        cv2.circle(im,(int(q[0]),int(q[1])),max(1,int(rx*.45)),cor,-1,cv2.LINE_AA)
        luz=q+sol*rx*.35;meio=tuple((a_+b_)//2 for a_,b_ in zip(bri,cor));cv2.circle(im,(int(luz[0]),int(luz[1])),max(1,int(rx*.28)),meio,-1,cv2.LINE_AA)

# ---------------- pedestres ----------------
ROUPA=[(200,60,50),(40,90,170),(230,230,224),(50,140,80),(240,190,40),(120,70,140),(30,30,34),(220,120,40)]
def draw_pedestrians(scene,im,t,cam,width,progress,header,footer):
    if not getattr(scene.s,'pedestrians',False) or scene.W/max(width,1)<.35:return
    sim=scene.traffic()
    if sim is not None:control=sim.pedestrians
    else:
        if not hasattr(scene,'_ped_control'):
            from .pedestrian_traffic import without_vehicles
            from .transport import Transport
            scene._ped_control=without_vehicles(scene.s,scene.network,Transport(scene.s,scene.network),scene.s.duration_s)
        control=scene._ped_control
    rows=control.state(t)
    if not rows:return
    m=scene.W/width;rcab=max(1.2,.2*m);rcorpo=max(1.8,.3*m)
    for row in rows:
        p=np.array(row['p']);u=np.array(row['heading']);identity=row['id'];h=(identity*977)%1000/1000;vel=1.3
        ch=scene.ch[scene.tree.query(p)[1]]
        if ch>progress*scene.length+25:continue
        q=scene.screen(p[None],cam,width)[0]
        if not(0<q[0]<scene.W and header<q[1]<scene.H-footer):continue
        step=math.sin(t*vel*6+h*10)*.12*m if row['state']=='crossing' else 0.
        x,y=int(round(q[0])),int(round(q[1]));sv=scene.sombra_veiculo
        dr=np.array([sv@scene.R[:,0],-(sv@scene.R[:,1])])*1.7*m*.6
        cv2.circle(im,(int(x+dr[0]),int(y+dr[1])),max(1,int(rcorpo)),(40,44,40),-1,cv2.LINE_AA)
        us=np.array([u@scene.R[:,0],-(u@scene.R[:,1])]);ns=np.array([-us[1],us[0]])
        if m>6:
            for sign in (-1,1):
                a=np.array([x,y])+ns*sign*rcorpo*.45;b=a+us*step*sign
                cv2.line(im,tuple(a.astype(int)),tuple(b.astype(int)),(60,52,46),max(1,int(m*.06)),cv2.LINE_AA)
        cv2.ellipse(im,(x,y),(max(1,int(rcorpo)),max(1,int(rcorpo*.6))),math.degrees(math.atan2(ns[1],ns[0])),0,360,ROUPA[identity%len(ROUPA)],-1,cv2.LINE_AA)
        cv2.circle(im,(x,y),max(1,int(rcab)),[(60,40,30),(150,110,80),(200,160,120),(40,30,25)][identity%4],-1,cv2.LINE_AA)
