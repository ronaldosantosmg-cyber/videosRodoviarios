"""Vista da cabine (1.6): câmera em primeira pessoa acompanhando um veículo numa trajetória validada.

Projeção em perspectiva do PLANO do mapa (homografia), com capô/painel sobrepostos e suavização da
direção. Limitação: não há modelo digital de elevação — o terreno é plano. A única diferença de
altura vem das cotas informadas nas OAE marcadas (nível): ao passar por elas, a câmera sobe e o
restante da cena continua no plano.
"""
import math
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter1d
from shapely.geometry import LineString,Point
from . import visual

SKY_TOP=np.array([92,140,186],np.float32);SKY_LOW=np.array([196,214,226],np.float32);HAZE=np.array([186,200,206],np.float32)

class CabinView:
    def __init__(self,scene):
        self.sc=sc=scene;c=sc.s.cabin;self.c=c
        paths=sc.network.paths
        if not paths:raise ValueError('Vista da cabine: não há trajetórias validadas com veículos. Gere a prévia e confira o tráfego.')
        if c.start is None:raise ValueError('Vista da cabine: clique sobre uma trajetória no editor para escolher o veículo e o início do trecho.')
        p0=np.array([c.start.x,c.start.y]);best=None
        for i,p in enumerate(paths):
            d=np.linalg.norm(p['p']-p0,axis=1);j=int(np.argmin(d))
            if best is None or d[j]<best[0]:best=(float(d[j]),i,j)
        if best[0]>20:raise ValueError(f'Vista da cabine: o ponto escolhido está a {best[0]:.0f} m da trajetória validada mais próxima (máximo 20 m).')
        self.dist0,self.i,j=best;self.path=paths[self.i];self.d0=float(self.path['d'][j])
        self.speed=(c.speed_kmh or sc.s.traffic_speed_kmh)/3.6
        p=self.path['p'];step=float(np.median(np.diff(self.path['d']))) if len(p)>1 else .6
        sigma=max(.01,c.smoothing_s*self.speed/max(step,1e-3))
        t=np.gradient(p,axis=0);t=gaussian_filter1d(t,sigma,axis=0,mode='nearest') if c.smoothing_s>0 else t
        self.heading=t/np.maximum(np.linalg.norm(t,axis=1)[:,None],1e-9)
        # Altura da câmera: olho do motorista + cota das OAE marcadas (rampas de 25 m).
        ch=sc.stationing.geo(p);lift=np.zeros(len(p))
        for o in sc.oae:
            a,b=o['chain'];ramp=np.clip(np.minimum(ch-a,b-ch)/25.+.5,0,1);lift=np.maximum(lift,ramp*o['level_m']*(o['level_m']>0))
        self.terrain=getattr(sc,'terrain',None)
        if self.terrain is not None:
            # Com modelo de elevação: olho = superfície de rolamento (perfil nivelado) + altura do motorista.
            ground=self.terrain.sample(p[:,0],p[:,1]).astype(np.float64)
            self.height=c.eye_height_m+(gaussian_filter1d(ground,sigma,mode='nearest') if c.smoothing_s>0 else ground)
            hs=__import__('app.elevation',fromlist=['hillshade']).hillshade(self.terrain.h,self.terrain.cell)
            self.shade=(.62+.38*hs/max(float(np.median(hs)),1e-3)).astype(np.float32)
        else:self.height=c.eye_height_m+(gaussian_filter1d(lift,sigma,mode='nearest') if c.smoothing_s>0 else lift)
        self.reaches_end=self.d0+self.speed*c.duration_s>self.path['length']
        W,H=sc.W,sc.H;self.y0=int(157*sc.scale)+1;self.y1=H-int(154*sc.scale)
        self.f=(W/2)/math.tan(math.radians(c.fov_deg)/2);self.cx=W/2;self.cy=(self.y0+self.y1)/2
        self.levels=[(sc.map,np.ascontiguousarray(sc.overlay),1)]
        for k in (4,16):
            n=max(64,sc.n//k);self.levels.append((cv2.resize(sc.map,(n,n),interpolation=cv2.INTER_AREA),cv2.resize(np.asarray(sc.overlay),(n,n),interpolation=cv2.INTER_AREA),sc.n/n))
        self.hood=self._hood() if c.hood else None
        self.vehicle_ids=set()
    def state(self,t):
        d=min(self.path['length'],self.d0+self.speed*max(0.,t));j=min(len(self.path['p'])-1,int(np.searchsorted(self.path['d'],d)))
        return self.path['p'][j],self.heading[j],float(self.height[j]),d
    def basis(self,pos,head,h):
        th=math.radians(self.c.pitch_deg);f3=np.array([head[0],head[1],0.]);z=np.array([0,0,1.])
        F=math.cos(th)*f3-math.sin(th)*z;U=math.sin(th)*f3+math.cos(th)*z;R=np.array([head[1],-head[0],0.])
        return np.array([pos[0],pos[1],h]),R,U,F
    def project(self,P,cam):
        C,R,U,F=cam;v=np.atleast_2d(P)-C;xc=v@R;yc=v@U;zc=v@F
        with np.errstate(divide='ignore',invalid='ignore'):
            return np.column_stack([self.cx+self.f*xc/zc,self.cy-self.f*yc/zc]),zc
    def homography(self,cam,scale):
        C,R,U,F=cam;sc=self.sc;px=sc.px*scale
        A=np.array([[px,0,sc.box[0]],[0,-px,sc.box[3]],[0,0,1.]])
        M3=np.column_stack([[R[0],U[0],F[0]],[R[1],U[1],F[1]],[-(R@C),-(U@C),-(F@C)]])
        K=np.array([[self.f,0,self.cx],[0,-self.f,self.cy],[0,0,1.]])
        return K@M3@A
    def ground(self,cam,h):
        """Imagem aérea + camadas do projeto projetadas no plano, com mipmap por distância."""
        W,H=self.sc.W,self.sc.H;th=math.radians(self.c.pitch_deg)
        rows=np.arange(H,dtype=np.float64);ang=np.arctan2(rows-self.cy,self.f)+th  # ângulo abaixo do horizonte
        with np.errstate(divide='ignore'):dist=np.where(ang>1e-4,h/np.tan(np.maximum(ang,1e-4)),np.inf)
        foot=dist**2/np.maximum(self.f*h,1e-6)/self.sc.px  # pixels do mosaico por pixel da tela (vertical)
        out=np.zeros((H,W,3),np.float32);alpha=np.zeros((H,W),np.float32);acc=np.zeros(H,np.float32)
        weights=[np.clip(1-np.abs(np.log2(np.maximum(foot,1e-6))/2-k),0,1) for k in range(len(self.levels))]
        weights[0]=np.where(foot<1,1,weights[0]);weights[-1]=np.where(np.log2(np.maximum(foot,1e-6))/2>len(self.levels)-1,1,weights[-1])
        horizon=int(np.clip(math.floor(self.cy-self.f*math.tan(th))+2,0,H))
        for k,(mp,ov,s) in enumerate(self.levels):
            w=weights[k].astype(np.float32);w[:horizon]=0
            if not w.any():continue
            Hm=self.homography(cam,s)
            g=cv2.warpPerspective(mp,Hm,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
            o=cv2.warpPerspective(np.ascontiguousarray(ov),Hm,(W,H),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0).astype(np.float32)
            a=o[:,:,3:]/255;g=g*(1-a)+o[:,:,:3]*a
            out+=g*w[:,None,None];acc+=w
        out/=np.maximum(acc,1e-6)[:,None,None]
        # Céu e névoa de distância (sem relevo: o horizonte é a linha do plano).
        fog=np.clip((dist-350)/1400,0,1).astype(np.float32);fog[:horizon]=1
        sky_t=np.clip(rows/max(horizon,1),0,1)[:,None].astype(np.float32);sky=SKY_TOP*(1-sky_t)+SKY_LOW*sky_t
        img=out*(1-fog[:,None,None])+np.where((rows<horizon)[:,None,None],sky[:,None,:],HAZE)*fog[:,None,None]
        return np.clip(img,0,255).astype(np.uint8)
    def draw_markings(self,im,cam,pos):
        sc=self.sc
        if not len(sc.markings):return
        near=np.linalg.norm(sc.marking_centers_c-pos,axis=1)<220
        for seg,color in zip(sc.markings[near],sc.marking_colors[near]):
            a,b=seg;t=b-a;L=np.linalg.norm(t)
            if L<1e-6:continue
            t/=L;n=np.array([-t[1],t[0]])*.075
            quad=np.array([[*(a-n),0],[*(b-n),0],[*(b+n),0],[*(a+n),0]])
            q,z=self.project(quad,cam)
            if (z<1).any():continue
            cv2.fillPoly(im,[q.astype(np.int32)],tuple(map(int,color)),cv2.LINE_AA)
    def draw_vehicles(self,im,cam,pos,t):
        sc=self.sc;boxes=[]
        for p,tan,k,identity,j in sc.traffic_iter(t):
            d=np.linalg.norm(p-pos)
            if d<9 or d>350:continue
            vt=visual.vehicle_type(sc.network.paths[identity[0]]['kinds'],identity) if sc.enhanced else 'car'
            if vt!='car' and not sc.fits(identity[0],j,p,tan,vt):vt='car'
            if not sc.fits(identity[0],j,p,tan,'car'):continue
            boxes.append((d,p,tan,vt,visual.vehicle_color(identity,vt)))
        for d,p,tan,vt,color in sorted(boxes,key=lambda b:-b[0]):
            T=visual.TYPES[vt];foot=visual.body(p,tan,T['L'],T['B'])
            base=np.column_stack([foot,np.zeros(4)]);top=np.column_stack([foot,np.full(4,T['H'])])
            q,z=self.project(np.vstack([base,top]),cam)
            if (z<1.5).any():continue
            q=q.astype(np.int32);shadow=self.project(np.column_stack([visual.body(p+np.array([.25,-.38])*T['H']*.5,tan,T['L']*1.05,T['B']*1.1),np.zeros(4)]),cam)[0].astype(np.int32)
            cv2.fillPoly(im,[shadow],(40,44,42),cv2.LINE_AA)
            dark=tuple(int(c*.55) for c in color);mid=tuple(int(c*.78) for c in color)
            cv2.fillConvexPoly(im,cv2.convexHull(q),dark,cv2.LINE_AA)
            # Face mais próxima da câmera e teto.
            faces=[[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]];C=cam[0]
            centers=[np.vstack([base,top])[f].mean(0) for f in faces];near=int(np.argmin([np.linalg.norm(c-C) for c in centers]))
            cv2.fillConvexPoly(im,q[faces[near]],mid,cv2.LINE_AA);cv2.fillConvexPoly(im,q[[4,5,6,7]],color,cv2.LINE_AA)
            # Vidro traseiro/dianteiro na face visível (carros e ônibus).
            if vt!='truck':
                fq=q[faces[near]].astype(np.float32);g=fq[[3,2]]*.85+fq[[0,1]]*.15;h2=fq[[3,2]]*.5+fq[[0,1]]*.5
                cv2.fillConvexPoly(im,np.vstack([g,h2[::-1]]).astype(np.int32),(46,66,80),cv2.LINE_AA)
    def _hood(self):
        W,H=self.sc.W,self.sc.H;y1=self.y1;img=np.zeros((H,W,4),np.uint8)
        dash=int((y1-self.y0)*.13);hood=int((y1-self.y0)*.11)
        # Capô: trapézio escuro com reflexo suave; painel: faixa curva inferior.
        top=y1-dash-hood;pts=np.array([[int(W*.14),y1-dash],[int(W*.33),top],[int(W*.67),top],[int(W*.86),y1-dash]],np.int32)
        cv2.fillPoly(img,[pts],(38,46,54,255),cv2.LINE_AA)
        for k in range(hood):
            f=k/max(hood,1);cv2.line(img,(int(W*(.33-.19*f)),top+k),(int(W*(.67+.19*f)),top+k),(int(38+22*(1-f)),int(46+24*(1-f)),int(54+26*(1-f)),255),1)
        cv2.polylines(img,[pts[1:3]],False,(120,132,140,255),max(1,W//900),cv2.LINE_AA)
        ys=np.arange(y1-dash-int(dash*.25),y1);xs=np.arange(W)
        curve=(y1-dash)-np.cos((xs/W-.5)*math.pi)*dash*.22
        mask=(ys[:,None]>=curve[None,:])
        img[ys[0]:y1][mask]=(20,24,28,255)
        cv2.ellipse(img,(int(W*.29),y1-int(dash*.25)),(int(W*.06),int(dash*.55)),0,180,360,(70,78,86,255),max(2,W//400),cv2.LINE_AA)
        return img
    # ---------- Terreno com elevação: renderização por colunas (raios no plano, ordem frente->fundo) ----------
    def terrain_frame(self,pos,head,h,t):
        sc=self.sc;W,H=sc.W,sc.H;f=self.f;th=math.radians(self.c.pitch_deg);hor=self.cy-f*math.tan(th)
        fwd=np.array(head,float);right=np.array([head[1],-head[0]])
        d=1.2*1.011**np.arange(0,int(math.log(2600/1.2)/math.log(1.011))+1)          # distâncias em planta
        lat=(np.arange(W)-self.cx)/f
        X=pos[0]+fwd[0]*d[:,None]+right[0]*lat[None,:]*d[:,None];Y=pos[1]+fwd[1]*d[:,None]+right[1]*lat[None,:]*d[:,None]
        Ht=self.terrain.sample(X,Y);rows=hor-f*(Ht-h)/d[:,None]
        # Cor: ortofoto + camadas pelo próprio X/Y (sem deformar a imagem), com nível de detalhe pela distância.
        u=((X-sc.box[0])/sc.px).astype(np.float32);v=((sc.box[3]-Y)/sc.px).astype(np.float32)
        foot=np.log2(np.maximum(d/f/sc.px,1e-6))/2
        col=np.zeros(X.shape+(3,),np.float32);acc=np.zeros(len(d),np.float32)
        for k,(mp,ov,scale) in enumerate(self.levels):
            w=np.clip(1-np.abs(foot-k),0,1).astype(np.float32)
            if k==0:w=np.where(foot<0,1,w)
            if k==len(self.levels)-1:w=np.where(foot>k,1,w)
            if not w.any():continue
            uu=u/scale-.5;vv=v/scale-.5
            g=cv2.remap(mp,uu,vv,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
            o=cv2.remap(np.ascontiguousarray(ov),uu,vv,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0).astype(np.float32)
            a=o[:,:,3:]/255;col+=(g*(1-a)+o[:,:,:3]*a)*w[:,None,None];acc+=w
        col/=np.maximum(acc,1e-6)[:,None,None]
        col*=self.terrain.sample(X,Y,self.shade)[:,:,None]
        fog=np.clip((d-350)/1600,0,1).astype(np.float32)[:,None,None];col=col*(1-fog)+HAZE*fog
        # Visibilidade: a menor linha já ocupada em cada coluna (y-buffer); cada pixel recebe a amostra mais próxima que o cobre.
        ymin=np.minimum.accumulate(rows,axis=0);img=np.empty((H,W,3),np.uint8);depth=np.full((H,W),np.inf,np.float32)
        rr=np.arange(H,dtype=np.float64);sky_t=np.clip(rr/max(hor,1),0,1)[:,None];sky=(SKY_TOP*(1-sky_t)+SKY_LOW*sky_t).astype(np.uint8)
        colu=np.clip(col,0,255).astype(np.uint8);n=len(d)
        for c in range(W):
            j=np.searchsorted(-ymin[:,c],-rr,side='left')
            vis=j<n;img[:,c]=sky;img[vis,c]=colu[j[vis],c];depth[vis,c]=d[j[vis]]
        self._depth=depth;self._hor=hor;self._cam2=(pos,fwd,right,h)
        return img
    def project2(self,P):
        pos,fwd,right,h=self._cam2;v=P[:,:2]-pos;d=v@fwd;lat=v@right
        with np.errstate(divide='ignore',invalid='ignore'):return np.column_stack([self.cx+self.f*lat/d,self._hor-self.f*(P[:,2]-h)/d]),d
    def _ztest_fill(self,im,poly_px,depth,color):
        x0,y0=np.floor(poly_px.min(0)).astype(int);x1,y1=np.ceil(poly_px.max(0)).astype(int)+1;H,W=im.shape[:2]
        x0=max(0,x0);y0=max(0,y0);x1=min(W,x1);y1=min(H,y1)
        if x1<=x0 or y1<=y0:return
        m=np.zeros((y1-y0,x1-x0),np.uint8);cv2.fillConvexPoly(m,np.rint(poly_px-[x0,y0]).astype(np.int32),1,cv2.LINE_8)
        ok=(m>0)&(self._depth[y0:y1,x0:x1]>=depth*.97-.5);roi=im[y0:y1,x0:x1];roi[ok]=color
    def terrain_overlays(self,im,pos,t):
        sc=self.sc;T=self.terrain
        if len(sc.markings):
            near=np.linalg.norm(sc.marking_centers_c-pos,axis=1)<200
            for seg,color in zip(sc.markings[near],sc.marking_colors[near]):
                a,b=seg;tv=b-a;L=np.linalg.norm(tv)
                if L<1e-6:continue
                tv/=L;n=np.array([-tv[1],tv[0]])*.075;quad=np.array([a-n,b-n,b+n,a+n]);z=T.sample(quad[:,0],quad[:,1])+.03
                q,dd=self.project2(np.column_stack([quad,z]))
                if (dd<1).any():continue
                self._ztest_fill(im,q,float(dd.min()),tuple(map(int,color)))
        if not sc.s.traffic:return
        boxes=[]
        for p,tan,k,identity,j in sc.traffic_iter(t):
            dist=np.linalg.norm(p-pos)
            if dist<9 or dist>350:continue
            vt=visual.vehicle_type(sc.network.paths[identity[0]]['kinds'],identity) if sc.enhanced else 'car'
            if vt!='car' and not sc.fits(identity[0],j,p,tan,vt):vt='car'
            if not sc.fits(identity[0],j,p,tan,'car'):continue
            boxes.append((dist,p,tan,vt,visual.vehicle_color(identity,vt)))
        for dist,p,tan,vt,color in sorted(boxes,key=lambda b:-b[0]):
            Tt=visual.TYPES[vt];foot=visual.body(p,tan,Tt['L'],Tt['B']);g=float(T.sample(np.array([p[0]]),np.array([p[1]]))[0])
            pts=np.vstack([np.column_stack([foot,np.full(4,g)]),np.column_stack([foot,np.full(4,g+Tt['H'])])])
            q,dd=self.project2(pts)
            if (dd<1.5).any():continue
            dmin=float(dd.min());dark=tuple(int(c*.55) for c in color);mid=tuple(int(c*.78) for c in color)
            self._ztest_fill(im,cv2.convexHull(q.astype(np.float32)).reshape(-1,2),dmin,dark)
            faces=[[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]];C=np.array([*pos,0.]);centers=[pts[f_].mean(0) for f_ in faces]
            near_f=faces[int(np.argmin([np.linalg.norm(c_[:2]-pos) for c_ in centers]))]
            self._ztest_fill(im,q[near_f],dmin,mid);self._ztest_fill(im,q[[4,5,6,7]],dmin,color)
    def frame(self,t):
        sc=self.sc;pos,head,h,d=self.state(t);cam=self.basis(pos,head,h)
        if self.terrain is not None:
            if not hasattr(sc,'marking_centers_c'):sc.marking_centers_c=sc.markings.mean(1) if len(sc.markings) else np.empty((0,2))
            im=self.terrain_frame(pos,head,h,t);self.terrain_overlays(im,pos,t)
            if self.hood is not None:
                a=self.hood[:,:,3:].astype(np.float32)/255;im[:]=(im*(1-a)+self.hood[:,:,:3]*a).astype(np.uint8)
            from .chainage import fmt
            km=sc.stationing.km(pos);g=self.terrain.raw_at(*pos)
            sc.chrome(im,'Vista da cabine',f'km {fmt(km)} • {self.speed*3.6:.0f} km/h'+(f' • cota {g:.0f} m' if g is not None else '')+' • relevo do MDT',())
            return im,{'mode':'cabin','terrain':True,'camera':[*pos.tolist(),h],'heading':head.tolist(),'distance_m':d,'km_m':km,'path':self.i}
        if not hasattr(sc,'marking_centers_c'):sc.marking_centers_c=sc.markings.mean(1) if len(sc.markings) else np.empty((0,2))
        im=self.ground(cam,h);self.draw_markings(im,cam,pos)
        if sc.s.traffic:self.draw_vehicles(im,cam,pos,t)
        if self.hood is not None:
            a=self.hood[:,:,3:].astype(np.float32)/255;im[:]=(im*(1-a)+self.hood[:,:,:3]*a).astype(np.uint8)
        km=sc.stationing.km(pos)
        from .chainage import fmt
        sc.chrome(im,'Vista da cabine',f'km {fmt(km)} • {self.speed*3.6:.0f} km/h • ilustrativo, terreno plano',())
        return im,{'mode':'cabin','camera':cam[0].tolist(),'heading':head.tolist(),'distance_m':d,'km_m':km,'path':self.i}
