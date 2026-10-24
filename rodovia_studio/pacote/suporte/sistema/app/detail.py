"""1.11: detalhe em alta resolução para o vídeo.

Quando a câmera se aproxima (metros por pixel da tela menor que o pixel do mosaico base), o quadro passa
a usar ladrilhos de detalhe alinhados ao terreno, com resolução fixa em metros:
  * imagem aérea: ladrilhos Esri World Imagery (nível 19, ~0,28 m) reprojetados para o CRS do projeto;
  * desenho do projeto (pavimento, canteiro, taludes, OAE, camadas extras): rasterizado no ladrilho com
    a mesma lógica do mosaico base, porém a 0,2 m/pixel (bordas e hachuras nítidas).
Os ladrilhos são gerados sob demanda, guardados em disco (cache por assinatura) e em memória (LRU),
o que funciona também com vários processos de montagem. Sem internet, a imagem detalhada é desligada
na hora (sem esperar) e o vídeo segue com o mosaico base.
"""
import json,math,os,uuid,threading,collections,hashlib
from pathlib import Path
import numpy as np
import cv2
from PIL import Image

T=1024            # pixels por ladrilho de detalhe
R=0.2             # metros por pixel do detalhe
MERC=20037508.342789244
ZMAX=19
VERSION='1.11'

def _rgb(h):return np.array([int(h[i:i+2],16) for i in (1,3,5)],np.uint8)

def placeholder(img):
    """Ladrilho 'Map data not yet available' do Esri: quase todo cinza claro, sem cor."""
    if img is None:return True
    a=np.asarray(img)
    if a.ndim!=3:return True
    hsv=cv2.cvtColor(a,cv2.COLOR_RGB2HSV)
    return float(np.mean((hsv[:,:,1]<10)&(hsv[:,:,2]>180)))>.82

def grade(a):
    """Realce global (sem equalização local, que criaria emendas entre ladrilhos)."""
    f=a.astype(np.float32)
    blur=cv2.GaussianBlur(f,(0,0),1.2);f=np.clip(f*1.45-blur*.45,0,255)
    hsv=cv2.cvtColor(f.astype(np.uint8),cv2.COLOR_RGB2HSV);s=hsv[:,:,1].astype(np.float32)
    hsv[:,:,1]=np.minimum(255,s*(1+.16*(1-s/255))).astype(np.uint8)
    return cv2.cvtColor(hsv,cv2.COLOR_HSV2RGB)

_ONES=np.full((T,T),255,np.uint8)
PNG_FAST=[cv2.IMWRITE_PNG_COMPRESSION,1]   # 1.24: ladrilhos em cache gravados mais rápido (sem perda)

class Detail:
    def __init__(self,scene,res=None):
        self.sc=scene;s=scene.s
        self.R=float(res or getattr(s,'detail_resolution_m',R) or R)
        # 1.32: qualidade máxima: detalhe a 0,1 m e ladrilhos Esri até o nível 20 (onde existirem; senão nível 19).
        self.maxima=getattr(s,'video_quality','padrao')=='maxima'
        if self.maxima and not res:self.R=min(self.R,.1)
        self.zmax=20 if self.maxima else ZMAX
        self.quality=getattr(s,'video_quality','padrao')
        self.enabled_overlay=bool(getattr(s,'detail_textures',True))
        # 1.17: imagem local de alta resolução tem prioridade; Esri completa onde ela não cobre.
        self.local=None;self.local_error=''
        li=getattr(s,'local_imagery',None)
        if li is not None and li.image and getattr(li,'detail',True) and getattr(s,'imagery_detail','auto')!='off':
            try:
                from .local_tiles import LocalMosaic
                self.local=LocalMosaic(scene.directory,s)
            except Exception as e:self.local_error=str(e)[:200]
        self.esri_ok=s.imagery in ('esri','cache')
        self.enabled_imagery=getattr(s,'imagery_detail','auto')!='off' and (self.esri_ok or self.local is not None)
        self.x0=float(scene.box[0]);self.y1=float(scene.box[3])
        sig=getattr(scene,'geometry_signature','') or hashlib.sha256(repr(scene.box).encode()).hexdigest()
        extra=json.dumps([VERSION,self.R,T,s.visual_quality,getattr(s,'median_grass',True),s.water_texture,s.water_texture_opacity])
        # 1.16: só acrescenta à chave quando muda algo (projetos anteriores reaproveitam o cache).
        self.realistic=getattr(s,'texture_style','anterior') in ('realistic','artistico');look=getattr(s,'earthwork_look','hatch')   # 1.34: artístico usa o mesmo detalhe
        if self.realistic or look!='hatch':
            net=getattr(scene,'network',None);sig_e=hashlib.sha256(b''.join(np.round(e['p'][::25],1).tobytes() for e in getattr(net,'edges',[]) if not e['disabled'])).hexdigest()[:12] if net is not None else ''
            extra+=json.dumps(['1.16',self.realistic,look,sig_e])
        if self.local is not None:extra+=json.dumps(['local',self.local.key])
        if self.zmax!=ZMAX:extra+=json.dumps(['zmax',self.zmax])
        if self.quality!='padrao':extra+=json.dumps(['q1.32',self.quality])
        if getattr(s,'style_profile','padrao')!='padrao':extra+=json.dumps(['perfil',s.style_profile])
        if getattr(s,'pavement_styles',None):extra+=json.dumps(['repr',{k:v.model_dump() for k,v in s.pavement_styles.items()}],sort_keys=True)
        mats=[getattr(s,k,'flexivel') for k in ('pavement_material','existing_material','shoulder_material')]
        if 'rigido' in mats or any(e.get('material')=='rigido' for e in getattr(scene,'items',[])):extra+=json.dumps(['rigido','1.21',mats,getattr(s,'joint_spacing_m',5)])
        self.key=hashlib.sha256((sig+extra).encode()).hexdigest()[:20]
        self.dir=Path(scene.directory)/'cache_detalhe'/self.key
        self.tile_root=Path(scene.directory).resolve().parent/'_ladrilhos'
        # 1.19: fonte web escolhida (padrão Esri atual: mesma chave e mesmo cache de antes).
        from .webmap import web_source
        try:self.web=web_source(s)
        except ValueError:self.web=None;self.esri_ok=False
        if self.web is not None and self.web.kind!='esri':
            self.key=hashlib.sha256((self.key+self.web.key).encode()).hexdigest()[:20];self.dir=Path(scene.directory)/'cache_detalhe'/self.key
        self.mem=collections.OrderedDict();self.lock=threading.Lock();self.offline=False;self.fetch=None
        self._paths=None;self._tr=None
        self.base_px=float(scene.px)
    # ---------- estado serializável (processos auxiliares) ----------
    def __getstate__(self):
        d=dict(self.__dict__);d['mem']=collections.OrderedDict();d['lock']=None;d['_tr']=None;d['sc']=None;d['_paths']=None;return d
    def __setstate__(self,d):
        self.__dict__.update(d);self.lock=threading.Lock()
    def weight(self,m_per_px):
        """0 = só o mosaico base; 1 = só o detalhe. Transição suave entre 90% e 60% do pixel base."""
        if not(self.enabled_overlay or self.enabled_imagery):return 0.
        hi=self.base_px*.9;lo=self.base_px*.6
        if m_per_px>=hi:return 0.
        if m_per_px<=lo:return 1.
        f=(hi-m_per_px)/max(hi-lo,1e-9);return float(f*f*(3-2*f))
    # ---------- geometria dos ladrilhos ----------
    def tile_box(self,i,j):
        S=T*self.R;return self.x0+i*S,self.y1-(j+1)*S,self.x0+(i+1)*S,self.y1-j*S
    def worldpx(self,i,j):
        X0=self.x0+i*T*self.R;Y1=self.y1-j*T*self.R
        return lambda p:np.column_stack([(np.asarray(p)[:,0]-X0)/self.R,(Y1-np.asarray(p)[:,1])/self.R])
    def tiles_for(self,cam,width,W,H,R_):
        """Ladrilhos que cobrem o retângulo (girado) visto pela câmera."""
        hw=width/2;hh=width*H/W/2
        corners=np.array([cam+R_[:,0]*sx*hw+R_[:,1]*sy*hh for sx in (-1,1) for sy in (-1,1)])
        S=T*self.R;ix=(corners[:,0]-self.x0)/S;iy=(self.y1-corners[:,1])/S
        return [(i,j) for i in range(int(np.floor(ix.min())),int(np.floor(ix.max()))+1) for j in range(int(np.floor(iy.min())),int(np.floor(iy.max()))+1)]
    # ---------- desenho do projeto em alta resolução ----------
    def paths(self):
        if self._paths is not None:return self._paths
        from shapely.geometry import Polygon,LineString,box as sbox
        sc=self.sc;out=[]
        for e in sc.items:
            role=e['role']
            if role not in ('cut','fill','existing_pavement','pavement','shoulder','median','barrier','oae','overlay'):continue
            if role in ('cut','fill') and not sc.exclusion.is_empty:
                try:
                    g=(Polygon(e['points'],holes=e.get('holes',[])).buffer(0) if e['closed'] else LineString(e['points'])).difference(sc.exclusion)
                except Exception:continue
                geoms=list(g.geoms) if hasattr(g,'geoms') else [g]
                for v in geoms:
                    if v.is_empty:continue
                    if v.geom_type=='Polygon':out.append({'role':role,'closed':True,'p':np.asarray(v.exterior.coords),'holes':[np.asarray(h.coords) for h in v.interiors],'e':e})
                    elif v.geom_type=='LineString':out.append({'role':role,'closed':False,'p':np.asarray(v.coords),'holes':[],'e':e})
            else:out.append({'role':role,'closed':bool(e['closed']),'p':np.asarray(e['points']),'holes':list(e.get('holes',[])),'e':e})
        for o in out:o['bb']=np.r_[o['p'].min(0),o['p'].max(0)]
        self._paths=out;return out
    def overlay_tile(self,i,j):
        """RGBA + superfície do ladrilho (mesma lógica do mosaico base, a 0,2 m/pixel)."""
        from .geometry import COLORS
        from .earthworks import earthwork_style
        from . import visual
        sc=self.sc;x0,y0,x1,y1=self.tile_box(i,j);wp=self.worldpx(i,j);n=T
        ov=np.zeros((n,n,4),np.uint8);surf=np.zeros((n,n),np.uint8);road=np.zeros((n,n),np.uint8)
        pad=4.
        near=[o for o in self.paths() if o['bb'][2]>=x0-pad and o['bb'][0]<=x1+pad and o['bb'][3]>=y0-pad and o['bb'][1]<=y1+pad]
        excl=None
        if not sc.exclusion.is_empty:
            from shapely.geometry import box as sbox
            g=sc.exclusion.intersection(sbox(x0-pad,y0-pad,x1+pad,y1+pad))
            if not g.is_empty:
                excl=np.zeros((n,n),np.uint8)
                for a in (list(g.geoms) if hasattr(g,'geoms') else [g]):
                    if a.geom_type!='Polygon':continue
                    cv2.fillPoly(excl,[np.rint(wp(np.asarray(a.exterior.coords))*16).astype(np.int32)],255,cv2.LINE_8,4)
                    for h in a.interiors:cv2.fillPoly(excl,[np.rint(wp(np.asarray(h.coords))*16).astype(np.int32)],0,cv2.LINE_8,4)
        q=lambda p:np.rint(wp(p)*16).astype(np.int32)  # subpixel (shift=4)
        for role in ['cut','fill','existing_pavement','pavement','shoulder','median','barrier','oae']:
            items=[o for o in near if o['role']==role]
            if not items:continue
            mask=np.zeros((n,n),np.uint8);lines=np.zeros_like(mask);rmask=None
            for o in items:
                if o['closed']:
                    tmp=np.zeros_like(mask);cv2.fillPoly(tmp,[q(o['p'])],255,cv2.LINE_AA,4)
                    for h in o['holes']:cv2.fillPoly(tmp,[q(np.asarray(h))],0,cv2.LINE_AA,4)
                    mask=np.maximum(mask,tmp)
                    if o['e'].get('material')=='rigido':rmask=tmp if rmask is None else np.maximum(rmask,tmp)
                else:cv2.polylines(lines,[q(o['p'])],False,255,max(1,round(.25/self.R)),cv2.LINE_AA,4)
            if role in ('cut','fill'):
                hard=(mask>127).astype(np.uint8)*255
                color,alpha=earthwork_style(hard,lines,role,self.R,phase=(i*n,j*n),look=getattr(sc.s,'earthwork_look','hatch'))
                if excl is not None:alpha[excl>0]=0
            else:alpha=mask
            rgb=_rgb(sc.color(role) if hasattr(sc,'color') else COLORS[role])
            if role=='pavement':
                rng=np.random.default_rng((57,i,j));grain=rng.integers(-3,4,(n,n),dtype=np.int16)
                color=np.clip(rgb.astype(np.int16)[None,None,:]+grain[:,:,None],0,255).astype(np.uint8)
            elif role not in ('cut','fill'):color=rgb
            if getattr(sc.s,'style_profile','padrao')=='tecnico' and role in visual.TECH_HATCH:
                hm,hc=visual.surface_hatch((n,n),x0,y1,self.R,role)
                base_c=np.broadcast_to(np.asarray(color,np.float32),(n,n,3)) if np.ndim(color)==1 else color.astype(np.float32)
                color=(base_c*(1-hm[:,:,None]*.85)+hc*hm[:,:,None]*.85).astype(np.uint8)
            if rmask is not None:
                from .pavement import paint_rigid,JointField
                if getattr(sc,'joint_field_net',None) is None:
                    net=getattr(sc,'network',None);f=JointField.from_network(net) if net is not None else None
                    sc.joint_field_net=f if f is not None and f.ok else JointField(sc.axes)
                color=paint_rigid(color,rmask>127,role,x0,y1,self.R,sc.joint_field_net,float(getattr(sc.s,'joint_spacing_m',5)),getattr(sc.s,'style_profile','padrao')=='tecnico')
            from .pavement import chosen,paint_style
            st=chosen(sc.s,role) if role in ('pavement','existing_pavement','shoulder') else None
            if st is not None and st.pattern=='placas' and getattr(sc,'joint_field_net',None) is None:
                from .pavement import JointField
                net=getattr(sc,'network',None);f=JointField.from_network(net) if net is not None else None
                sc.joint_field_net=f if f is not None and f.ok else JointField(sc.axes)
            if st is not None:color=paint_style(color,mask>127,role,x0,y1,self.R,st,getattr(sc,'joint_field_net',None),float(getattr(sc.s,'joint_spacing_m',5)))  # 1.21: representação escolhida pelo usuário
            sel=alpha>0;a=alpha[sel,None].astype(np.float32)/255;old=ov[sel,:3].astype(np.float32)
            c=color[sel] if getattr(color,'ndim',1)==3 else color
            ov[sel,:3]=(old*(1-a)+c*a).astype(np.uint8);ov[:,:,3]=np.maximum(ov[:,:,3],alpha)
            if role in ('cut','fill'):ov[sel,:3]=color[sel]
            m=mask>127
            if role in visual.SURF:surf[m]=visual.SURF[role]
            elif role in visual.EARTH_SURF and getattr(sc.s,'earthwork_look','hatch')=='natural':surf[m]=visual.EARTH_SURF[role]
            elif role in ('median','barrier'):surf[m]=0
            if rmask is not None:surf[m&(rmask>127)]=visual.SURF['oae']
            if role in ('pavement','existing_pavement','shoulder','oae'):road=np.maximum(road,mask)
        for o in near:
            if o['closed'] and o['e'].get('tex_code'):
                tm=np.zeros((n,n),np.uint8);cv2.fillPoly(tm,[q(o['p'])],255,cv2.LINE_AA,4)
                for h in o['holes']:cv2.fillPoly(tm,[q(np.asarray(h))],0,cv2.LINE_AA,4)
                surf[tm>127]=o['e']['tex_code']
        if hasattr(sc,'texture_areas'):
            for code,base,_,pts in sc.texture_areas():
                tm=np.zeros((n,n),np.uint8);cv2.fillPoly(tm,[q(pts)],255,cv2.LINE_AA,4);surf[(tm>127)&(surf==base)]=code
        groups={}
        for o in near:
            if o['role']=='overlay':groups.setdefault(o['e']['overlay_order'],[]).append(o)
        for order in sorted(groups):
            st=groups[order][0]['e']['style'];rgb=_rgb(st['color']);mask=np.zeros((n,n),np.uint8);lw=max(1,round(st['width_m']/self.R))
            for o in groups[order]:
                if o['closed'] and st['fill']:cv2.fillPoly(mask,[q(o['p'])],115,cv2.LINE_AA,4)
            for o in groups[order]:cv2.polylines(mask,[q(o['p'])],o['closed'],255,lw,cv2.LINE_AA,4)
            a=(mask.astype(np.float32)*st['opacity']).astype(np.uint8);sel=a>0
            if not sel.any():continue
            f=a[sel,None]/255;old=ov[sel,:3].astype(np.float32);ov[sel,:3]=(old*(1-f)+rgb*f).astype(np.uint8);ov[:,:,3]=np.maximum(ov[:,:,3],a)
        if self.realistic and (surf==2).any():self.wheel_paths(surf,i,j)
        if road.any():
            shadow=cv2.GaussianBlur(road,(0,0),1.0/self.R);outside=(ov[:,:,3]==0)&(shadow>0)
            ov[outside,:3]=0;ov[outside,3]=(shadow[outside]*.18).astype(np.uint8)
        return ov,surf
    def wheel_paths(self,surf,i,j):
        """1.16: trilhas de roda (±0,85 m do centro da faixa, 0,6 m de largura) na pista existente."""
        net=getattr(self.sc,'network',None)
        if net is None:return
        x0,y0,x1,y1=self.tile_box(i,j);wp=self.worldpx(i,j);m=np.zeros_like(surf)
        w=max(1,round(.6/self.R))
        for e in net.edges:
            if e['disabled'] or len(e['p'])<2:continue
            p=e['p']
            if p[:,0].max()<x0-3 or p[:,0].min()>x1+3 or p[:,1].max()<y0-3 or p[:,1].min()>y1+3:continue
            t=e['t'];n=np.column_stack([t[:,1],-t[:,0]])
            for side in (-.85,.85):cv2.polylines(m,[np.rint(wp(p+n*side)*16).astype(np.int32)],False,255,w,cv2.LINE_AA,4)
        m=cv2.GaussianBlur(m,(0,0),max(.6,.25/self.R))
        surf[(m>110)&(surf==2)]=8
    # ---------- imagem aérea detalhada ----------
    def transformer(self):
        if self._tr is None:
            from pyproj import CRS,Transformer
            self._tr=Transformer.from_crs(CRS.from_user_input(self.sc.s.crs),3857,always_xy=True)
        return self._tr
    def esri(self,z,x,y):
        from .webmap import tile
        data=tile(self.tile_root,z,y,x,fetch=self.fetch,timeout=8,source=self.web)
        a=cv2.imdecode(np.frombuffer(data,np.uint8),cv2.IMREAD_COLOR)
        return None if a is None else cv2.cvtColor(a,cv2.COLOR_BGR2RGB)
    def imagery_tile(self,i,j):
        """1.17: imagem local (RGBA, alfa = cobertura) e, por baixo, Esri; RGB, RGBA (só local, parcial) ou None."""
        loc=None
        if self.local is not None:
            box=self.tile_box(i,j)
            if self.local.covers(box):
                loc=self.local.sample_box(box,T,T)
                if loc[:,:,3].max()==0:loc=None
                elif loc[:,:,3].min()==255:return self._water(loc[:,:,:3].copy(),i,j)
        esri=self.esri_tile(i,j) if self.esri_ok and not self.offline else None
        if loc is None:return esri
        if esri is None:
            rgb=self._water(loc[:,:,:3].copy(),i,j);return np.dstack([rgb,loc[:,:,3]])
        a=loc[:,:,3:4].astype(np.float32)/255;lr=self._water(loc[:,:,:3].copy(),i,j)
        return (lr*a+esri*(1-a)).astype(np.uint8)
    def _water(self,out,i,j):
        sc=self.sc
        if getattr(sc,'hydro',None) is not None and sc.s.water_texture and (sc.hydro.lines or sc.hydro.polygons):
            try:sc.hydro.paint_map(out,self.worldpx(i,j),self.R,sc.s.water_texture_opacity,sc.enhanced)
            except Exception:pass
        return out
    def esri_tile(self,i,j):
        """Reprojeta os ladrilhos Esri para o ladrilho de detalhe (afim local; erro << 1 cm em 205 m)."""
        if self.offline or not self.esri_ok:return None
        x0,y0,x1,y1=self.tile_box(i,j);tr=self.transformer()
        u=np.array([0,T,0,T,T/2],float);v=np.array([0,0,T,T,T/2],float)
        mx,my=tr.transform(x0+u*self.R,y1-v*self.R);mx=np.asarray(mx);my=np.asarray(my)
        if not(np.all(np.isfinite(mx)) and np.all(np.isfinite(my))):return None
        lat=math.degrees(2*math.atan(math.exp(float(my.mean())/6378137))-math.pi/2)
        ground=lambda z:2*MERC/256/2**z*math.cos(math.radians(lat))
        z=getattr(self,'zmax',ZMAX) if self.web is None or self.web.kind=='esri' else max(15,min(self.web.max_zoom,21))
        while z>15 and ground(z-1)<=self.R*1.6:z-=1
        for zz in range(z,max(13,z-4),-1):
            scale=256*2**zz/(2*MERC);px=(mx+MERC)*scale;py=(MERC-my)*scale
            tx0,tx1=int(np.floor(px.min())//256),int(np.floor(px.max())//256);ty0,ty1=int(np.floor(py.min())//256),int(np.floor(py.max())//256)
            if (tx1-tx0+1)*(ty1-ty0+1)>36:continue
            canvas=np.zeros(((ty1-ty0+1)*256,(tx1-tx0+1)*256,3),np.uint8);ok=True
            for ty in range(ty0,ty1+1):
                for tx in range(tx0,tx1+1):
                    try:a=self.esri(zz,tx,ty)
                    except ValueError:a=None
                    except Exception:
                        self.offline=True;return None
                    if a is None or placeholder(a):ok=False;break
                    canvas[(ty-ty0)*256:(ty-ty0+1)*256,(tx-tx0)*256:(tx-tx0+1)*256]=a
                if not ok:break
            if not ok:continue
            # Afim ladrilho(u,v) -> canvas(px,py) pelos quatro cantos (mínimos quadrados).
            A=np.column_stack([u,v,np.ones_like(u)]);M=np.vstack([np.linalg.lstsq(A,px-tx0*256,rcond=None)[0],np.linalg.lstsq(A,py-ty0*256,rcond=None)[0]]).astype(np.float32)
            up=cv2.INTER_LANCZOS4 if getattr(self,'quality','padrao')!='padrao' else cv2.INTER_CUBIC   # 1.32: ampliação mais nítida
            flags=(cv2.INTER_AREA if M[0,0]>1.2 else up)|cv2.WARP_INVERSE_MAP
            out=cv2.warpAffine(canvas,M,(T,T),flags=flags,borderMode=cv2.BORDER_REFLECT_101)
            out=grade(out)
            if self.realistic:out=self.match_base(out,i,j)
            sc=self.sc
            if getattr(sc,'hydro',None) is not None and sc.s.water_texture and (sc.hydro.lines or sc.hydro.polygons):
                try:sc.hydro.paint_map(out,self.worldpx(i,j),self.R,sc.s.water_texture_opacity,sc.enhanced)
                except Exception:pass
            return out
        return None
    def match_base(self,img,i,j):
        """1.16: casa a cor de baixa frequência do ladrilho com a do mosaico base (sem salto na transição)."""
        sc=self.sc;mp=getattr(sc,'map',None)
        if mp is None or sc.s.imagery=='neutral':return img
        x0,y0,x1,y1=self.tile_box(i,j);q=sc.worldpx(np.array([[x0,y1],[x1,y0]]))
        c0=np.floor(q.min(0)).astype(int);c1=np.ceil(q.max(0)).astype(int)
        H,W=mp.shape[:2]
        if c0[0]<0 or c0[1]<0 or c1[0]>W or c1[1]>H or (c1-c0).min()<4:return img
        crop=np.asarray(mp[c0[1]:c1[1],c0[0]:c1[0]]).astype(np.float32)
        # Recorte exato do ladrilho no mosaico (afim) na resolução do mosaico, depois ampliado.
        A=np.array([[(x1-x0)/T/sc.px,0,(x0-sc.box[0])/sc.px-c0[0]],[0,(y1-y0)/T/sc.px,(sc.box[3]-y1)/sc.px-c0[1]]],np.float32)
        small=max(8,int(T*self.R/sc.px))
        As=A.copy();As[:,:2]*=T/small
        base=cv2.warpAffine(crop,As,(small,small),flags=cv2.INTER_AREA|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REFLECT_101)
        det=cv2.resize(img.astype(np.float32),(small,small),interpolation=cv2.INTER_AREA)
        sig=max(1.,small/12);b=cv2.GaussianBlur(base,(0,0),sig);d=cv2.GaussianBlur(det,(0,0),sig)
        gain=np.clip((b+4)/(d+4),.7,1.45);gain=cv2.resize(gain,(T,T),interpolation=cv2.INTER_CUBIC)
        return np.clip(img.astype(np.float32)*gain,0,255).astype(np.uint8)
    # ---------- cache ----------
    def get(self,i,j):
        k=(i,j)
        with self.lock:
            if k in self.mem:self.mem.move_to_end(k);return self.mem[k]
        d=self.dir;d.mkdir(parents=True,exist_ok=True)
        fo=d/f'ov_{i}_{j}.png';fs=d/f'sf_{i}_{j}.png';fi=d/f'im_{i}_{j}.jpg';fn=d/f'im_{i}_{j}.none';fa=d/f'im_{i}_{j}.png'
        ov=surf=img=None
        if self.enabled_overlay:
            if fo.exists() and fs.exists():
                ov=cv2.imread(str(fo),cv2.IMREAD_UNCHANGED);surf=cv2.imread(str(fs),cv2.IMREAD_UNCHANGED)
                if ov is not None:ov=cv2.cvtColor(ov,cv2.COLOR_BGRA2RGBA)
            if ov is None or surf is None:
                ov,surf=self.overlay_tile(i,j)
                self._save(fo,cv2.cvtColor(ov,cv2.COLOR_RGBA2BGRA),PNG_FAST);self._save(fs,surf,PNG_FAST)
        if self.enabled_imagery and (not self.offline or self.local is not None):
            if fi.exists():
                img=cv2.imread(str(fi));img=None if img is None else cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
            elif fa.exists():
                img=cv2.imread(str(fa),cv2.IMREAD_UNCHANGED);img=None if img is None else cv2.cvtColor(img,cv2.COLOR_BGRA2RGBA)
            elif not fn.exists():
                img=self.imagery_tile(i,j)
                if img is not None and img.shape[2]==4:self._save(fa,cv2.cvtColor(img,cv2.COLOR_RGBA2BGRA),PNG_FAST)
                elif img is not None:self._save(fi,cv2.cvtColor(img,cv2.COLOR_RGB2BGR),[cv2.IMWRITE_JPEG_QUALITY,92])
                elif not self.offline:
                    try:fn.write_bytes(b'')
                    except OSError:pass
        val=(img,ov,surf)
        with self.lock:
            self.mem[k]=val
            while len(self.mem)>48:self.mem.popitem(last=False)
        return val
    @staticmethod
    def _save(path,arr,params=()):
        tmp=path.with_name(path.stem+'_'+uuid.uuid4().hex[:8]+path.suffix)
        try:
            if cv2.imwrite(str(tmp),arr,list(params)):os.replace(tmp,path)
        except OSError:pass
        finally:
            if tmp.exists():
                try:tmp.unlink()
                except OSError:pass
    # ---------- composição no quadro ----------
    def compose(self,cam,width,want_imagery,want_overlay):
        """Retorna (imagem, máscara da imagem, overlay RGBA, superfície) no tamanho do quadro, ou None."""
        sc=self.sc;W,H=sc.W,sc.H;m=width/W
        dx=np.array([sc.right[0],-sc.right[1]])*m/self.R;dy=np.array([-sc.up[0],sc.up[1]])*m/self.R
        cp=np.array([(cam[0]-self.x0)/self.R,(self.y1-cam[1])/self.R]);org=cp-dx*W/2-dy*H/2
        img=np.zeros((H,W,3),np.uint8) if want_imagery else None;imask=np.zeros((H,W),np.uint8) if want_imagery else None
        ov=np.zeros((H,W,4),np.uint8) if want_overlay else None;surf=np.zeros((H,W),np.uint8) if want_overlay else None
        Minv=np.linalg.inv(np.array([[dx[0],dy[0],org[0]],[dx[1],dy[1],org[1]],[0,0,1]]))
        any_img=False
        for i,j in self.tiles_for(cam,width,W,H,sc.R):
            ti,to,ts=self.get(i,j)
            if ti is None and to is None:continue
            # Cantos do ladrilho na tela -> retângulo de destino.
            c=np.array([[i*T,j*T,1],[(i+1)*T,j*T,1],[i*T,(j+1)*T,1],[(i+1)*T,(j+1)*T,1]],float)@Minv.T
            xa=max(0,int(np.floor(c[:,0].min()))-1);xb=min(W,int(np.ceil(c[:,0].max()))+1);ya=max(0,int(np.floor(c[:,1].min()))-1);yb=min(H,int(np.ceil(c[:,1].max()))+1)
            if xb<=xa or yb<=ya:continue
            M=np.array([[dx[0],dy[0],org[0]+dx[0]*xa+dy[0]*ya-i*T],[dx[1],dy[1],org[1]+dx[1]*xa+dy[1]*ya-j*T]],np.float32)
            size=(xb-xa,yb-ya)
            # Máscara de validade do ladrilho (sem bordas duplicadas entre vizinhos).
            one=cv2.warpAffine(_ONES,M,size,flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_CONSTANT,borderValue=0)>0
            if want_imagery and ti is not None:
                flags=(cv2.INTER_AREA if m/self.R>1.6 else cv2.INTER_LINEAR)|cv2.WARP_INVERSE_MAP
                w=cv2.warpAffine(ti,M,size,flags=flags,borderMode=cv2.BORDER_REPLICATE)
                # 1.24: cópia com máscara (np.copyto) em vez de indexação booleana: mesmo resultado, bem mais rápida.
                one3=one[:,:,None]
                if w.shape[2]==4:
                    # Imagem local parcial (sem Esri por baixo): alfa = cobertura.
                    np.copyto(img[ya:yb,xa:xb],w[:,:,:3],where=one3);np.copyto(imask[ya:yb,xa:xb],w[:,:,3],where=one)
                else:np.copyto(img[ya:yb,xa:xb],w,where=one3);np.copyto(imask[ya:yb,xa:xb],np.uint8(255),where=one)
                any_img=True
            if want_overlay and to is not None:
                w=cv2.warpAffine(to,M,size,flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REPLICATE)
                np.copyto(ov[ya:yb,xa:xb],w,where=one[:,:,None])
                s2=cv2.warpAffine(ts,M,size,flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REPLICATE)
                np.copyto(surf[ya:yb,xa:xb],s2,where=one)
        return (img if any_img else None),imask,ov,surf
    # ---------- pré-carregamento ----------
    def prefetch(self,frames,status=lambda *a:None,workers=8,cancel=lambda:False):
        """Baixa em paralelo os ladrilhos Esri necessários às poses do vídeo (antes da montagem)."""
        if not self.enabled_imagery or (self.offline and self.local is None):return 0
        from concurrent.futures import ThreadPoolExecutor
        need=set()
        sc=self.sc
        for cam,width in frames:
            if self.weight(width/sc.W)<=0:continue
            need.update(self.tiles_for(cam,width,sc.W,sc.H,sc.R))
        todo=[k for k in sorted(need) if not (self.dir/f'im_{k[0]}_{k[1]}.jpg').exists() and not (self.dir/f'im_{k[0]}_{k[1]}.png').exists() and not (self.dir/f'im_{k[0]}_{k[1]}.none').exists()]
        if not todo:return 0
        done=[0]
        def job(k):
            if (self.offline and self.local is None) or cancel():return
            self.get(*k);done[0]+=1
            if done[0]%8==0:status(.25+.04*done[0]/len(todo),f'Imagem detalhada: {done[0]}/{len(todo)} ladrilhos')
        # Primeiro um ladrilho sozinho: se não houver internet, desiste logo.
        job(todo[0])
        if (not self.offline or self.local is not None) and len(todo)>1:
            with ThreadPoolExecutor(max_workers=workers) as pool:list(pool.map(job,todo[1:]))
        return done[0]
