from .traffic import TrafficNetwork
from .hydrography import Hydrography
from .earthworks import earthwork_style
from .structures import draw_structure
import json,math,subprocess,shutil,hashlib,re,os
from pathlib import Path
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter1d
from shapely.geometry import Polygon,LineString,Point
from shapely.ops import unary_union
from shapely import contains_xy
import imageio_ffmpeg
from functools import lru_cache
from .encoding import ffmpeg_exe,select_encoder
from .tempo import tempo
from .geometry import analyze,COLORS
from . import annotations
from .imagery import mosaic,ASSETS
from .chainage import Stationing,fmt as fmt_km
from .markup import oae_items,oae_pois
from .per import works_to_pois
from . import obras_video,ambiente,vida
from . import visual
cv2.setNumThreads(2)

def km(v):
    m=int(round(v));return f'{m//1000}+{m%1000:03d}'
@lru_cache(maxsize=96)
def font(n,b=False):
    return ImageFont.truetype(str(ASSETS/'fonts'/('DejaVuSans-Bold.ttf' if b else 'DejaVuSans.ttf')),max(8,int(n)))
def fit(draw,text,size,width,b=False):
    while size>10 and draw.textbbox((0,0),text,font=font(size,b))[2]>width:size-=1
    if draw.textbbox((0,0),text,font=font(size,b))[2]>width:
        while text and draw.textbbox((0,0),text+'…',font=font(size,b))[2]>width:text=text[:-1]
        text+='…'
    return text,font(size,b)

def poly(e):
    return Polygon(e['points'],holes=e.get('holes',[])).buffer(0)

FINE_M=.035   # 1.19: abaixo de 3,5 cm por pixel de tela usa o detalhe fino
FINE_R=.05

def tour_seconds(T,has_pois,mode='obras'):
    """Tempo de percurso (sobrevoo do eixo) dentro de um vídeo de T segundos, como em Scene.pose."""
    if mode=='continuo':return T-min(4,T*.06)-min(5,T*.06)
    return T-min(8,T*.12)-min(10,T*.12)-(min(88,T*.4) if has_pois else 0)

def duration_for_speed(length_m,speed_kmh,has_pois,mode='obras'):
    """1.27: duração do vídeo (s) para percorrer o eixo na velocidade de avanço dada (3 a 1800 s)."""
    want=length_m/max(speed_kmh/3.6,.1);lo,hi=3.,1800.
    if tour_seconds(hi,has_pois,mode)<=want:return hi
    for _ in range(60):
        mid=(lo+hi)/2
        if tour_seconds(mid,has_pois,mode)<want:lo=mid
        else:hi=mid
    return round(max(45.,hi),1)   # abaixo de 45 s o vídeo curto usa a vista geral (sem percurso)

def connection_data(net):
    """1.27: ligações entre trechos nos cruzamentos (para ver, proibir ou forçar no editor)."""
    seg={r['base']:k for k,r in enumerate(net.raw_info)}
    def at(e,dist,from_end):
        d=e['d'];L=float(d[-1]);x=max(0.,L-dist) if from_end else min(L,dist);j=min(len(d)-1,int(np.searchsorted(d,x)));return [round(float(e['p'][j][0]),3),round(float(e['p'][j][1]),3)]
    out=[];forced=getattr(net,'forced',set())
    for (i,j),c in net.connectors.items():
        a,b=net.edges[i],net.edges[j];c=np.asarray(c)
        out.append({'from':seg.get(a['base']),'to':seg.get(b['base']),'p':np.round(c[::max(1,len(c)//24)],2).tolist()+[np.round(c[-1],2).tolist()],'a':at(a,6,True),'b':at(b,6,False),'forced':(i,j) in forced})
    den=[]
    for i,j,c,rid in getattr(net,'denied',[]):
        a,b=net.edges[i],net.edges[j];c=np.asarray(c)
        den.append({'from':seg.get(a['base']),'to':seg.get(b['base']),'p':np.round(c[::max(1,len(c)//24)],2).tolist()+[np.round(c[-1],2).tolist()],'rule':rid})
    return {'connections':out[:4000],'denied':den,'connection_rules':getattr(net,'rule_report',[])}

SURF_BASE={'pista_nova':1,'pista_existente':2,'concreto':3,'acostamento':4,'canteiro':5,'talude_corte':6,'talude_aterro':7}
def texture_area_codes(items,settings):
    """1.29: códigos de superfície das regiões com textura própria (depois dos das áreas de pista)."""
    used=[e['tex_code'] for e in items if e.get('tex_code')];code=max(used)+1 if used else 32;out=[]
    for a in getattr(settings,'texture_areas',None) or []:
        if not a.enabled or a.texture is None or len(a.points)<3:continue
        p=a.texture.model_dump() if hasattr(a.texture,'model_dump') else dict(a.texture)
        if (p.get('grao',1),p.get('tom',1),p.get('remendos',1),p.get('fissuras',1),p.get('brilho',0))==(1,1,1,1,0):continue
        if code>255:break
        out.append((code,SURF_BASE[a.surface],p,np.array([[q.x,q.y] for q in a.points],float)));code+=1
    return out

def load_picture(directory,name):
    """1.26: imagem enviada para pórtico/destaque (pasta imagens do projeto), em RGB, limitada a 1200 px."""
    if not name:return None
    f=Path(directory)/'imagens'/name
    if not f.exists():return None
    im=cv2.imread(str(f),cv2.IMREAD_COLOR)
    if im is None:return None
    k=1200/max(im.shape[:2])
    if k<1:im=cv2.resize(im,None,fx=k,fy=k,interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(im,cv2.COLOR_BGR2RGB)

def window_fade(o,t,ramp=.6):
    """Opacidade pela janela de exibição (início/fim em segundos), com entrada e saída suaves."""
    a=o.get('start_s');b=o.get('end_s');f=1.
    if a is not None:f=min(f,float(np.clip((t-a)/ramp,0,1)))
    if b is not None:f=min(f,float(np.clip((b-t)/ramp,0,1)))
    return f

def sharpen_imagery(im,quality):
    """1.32: nitidez da imagem aérea do quadro (antes do desenho do projeto, que já é nítido).
    Máscara de nitidez com limiar (não realça o ruído/compressão da imagem de origem)."""
    # Na máxima o quadro é montado 1,5× maior e depois reduzido: raio proporcional e efeito um pouco maior.
    amount,sigma=(.45,1.0) if quality=='alta' else (.75,1.5)
    f=im.astype(np.float32);blur=cv2.GaussianBlur(f,(0,0),sigma);d=f-blur
    m=np.clip((np.abs(d).max(2,keepdims=True)-2.)/4.,0,1)   # diferenças < 2 níveis (ruído) ficam como estão
    return np.clip(f+amount*d*m,0,255).astype(np.uint8)

class Scene:
    def __init__(self,directory,s,status=lambda *a:None):
        self.directory=Path(directory);self.s=s;self.W=s.width;self.H=s.width*9//16;self.scale=self.W/2560
        status(.02,'Lendo geometria');self.items,self.axis,self.ds,self.axes,self.report=analyze(directory,s)
        from .image_context import accepted_items
        self.image_context_items=accepted_items(s,self.items,directory)
        self.map,self.box,self.attribution=mosaic(directory,s,self.report['bounds'],status,warnings=self.report.setdefault('warnings',[]))
        self.n=self.map.shape[0];self.px=(self.box[2]-self.box[0])/self.n
        self.hydro=Hydrography(directory,s,[self.report['bounds'][0][0]-250,self.report['bounds'][0][1]-250,self.report['bounds'][1][0]+250,self.report['bounds'][1][1]+250],status)
        self.enhanced=s.visual_quality=='enhanced';self.water_mask=None
        # 1.14: camadas do DXF mapeadas como Hidrografia somam-se à base pública (ou a substituem, se ela estiver desligada).
        for e in self.items:
            if e['role']!='water':continue
            if e['closed'] and len(e['points'])>=3:
                g=Polygon(e['points'],holes=e.get('holes',[])).buffer(0)
                for part in (list(g.geoms) if hasattr(g,'geoms') else [g]):
                    if part.geom_type=='Polygon' and part.area>1:self.hydro.polygons.append(part)
            elif len(e['points'])>=2:self.hydro.lines.append(np.asarray(e['points']))
        if any(e['role']=='water' for e in self.items) and 'DXF' not in self.hydro.source:self.hydro.source=(self.hydro.source+' + ' if self.hydro.source else '')+'hidrografia do DXF'
        if (self.hydro.lines or self.hydro.polygons) and (s.water_texture or s.water_names):
            if s.water_texture:
                self.map=self.map.copy();wm=self.hydro.paint_map(self.map,self.worldpx,self.px,s.water_texture_opacity,self.enhanced)
                if s.water_animated and self.hydro.polygons:self.water_mask=wm
            self.attribution+=' • Hidrografia: IBGE / © OpenStreetMap (ODbL)'
        if self.hydro.warning:self.report['warnings'].append(self.hydro.warning)
        self.center=(np.array(self.report['bounds'][0])+self.report['bounds'][1])/2
        delta=self.axis[-1]-self.axis[0]
        if np.linalg.norm(delta)<1e-6:
            # Eixo fechado (início = fim): usa a direção principal dos pontos (evita divisão por zero).
            c=self.axis-self.axis.mean(0);delta=np.linalg.svd(c,full_matrices=False)[2][0] if np.ptp(c,axis=0).max()>1e-6 else np.array([1.,0.])
        self.right=delta/np.linalg.norm(delta);self.up=np.array([-self.right[1],self.right[0]])
        self.R=np.column_stack([self.right,self.up]);self.length=self.ds[-1]
        ch=np.arange(0,self.length+2,2);p=np.column_stack([np.interp(ch,self.ds,self.axis[:,k]) for k in range(2)]);self.ch=ch;self.dense=p;self.tree=cKDTree(p);self.smooth=gaussian_filter1d(p,12,axis=0,mode='nearest')
        # Estaqueamento: km = km inicial + distância ao longo do eixo a partir do ponto clicado.
        self.stationing=Stationing.from_settings(self.axis,s)
        self.km_active=s.chainage.mode!='off'
        self.oae=oae_items(s,self.stationing)
        self.pois=[v.model_dump() for v in s.pois] or [dict(p) for p in self.report['kmz_pois']]
        if s.per_callouts and s.works:self.pois+=works_to_pois(s,self.axis,self.ds,self.stationing if self.km_active else None)
        self.pois+=oae_pois(self.oae)
        # Destaques (pontos especiais): caixas com linha de chamada; os marcados como parada entram na câmera.
        self.highlights=[]
        for h in s.highlights:
            d=h.model_dump();d['xy']=np.array([h.point.x,h.point.y]);d['chain']=float(ch[self.tree.query(d['xy'])[1]])
            d['km']=self.stationing.km([h.point.x,h.point.y]) if self.km_active else None
            if h.show_in_video:self.highlights.append(d)
            if h.stop:
                cat=visual.HIGHLIGHT_STYLE.get(h.category,visual.HIGHLIGHT_STYLE['outro'])[2]
                self.pois.append({'id':'hl-'+(h.id or h.name),'title':h.name,'subtitle':h.description or cat,'kind':'outro','x':h.point.x,'y':h.point.y,'km_m':None,'km_mode':'auto','anchor':None,'source':'highlight','no_symbol':True})
        # 1.26: pórticos (dois apoios) com a imagem da placa na caixa de chamada.
        self.gantries=[]
        for g in getattr(s,'gantries',None) or []:
            if not g.show_in_video:continue
            d=g.model_dump();d['a']=np.array([g.a.x,g.a.y],float);d['b']=np.array([g.b.x,g.b.y],float);d['xy']=(d['a']+d['b'])/2
            d['chain']=float(ch[self.tree.query(d['xy'])[1]]);d['km']=self.stationing.km(list(d['xy'])) if self.km_active else None
            d['pic']=load_picture(directory,g.image);d['panel_rgb']=None
            if d['pic'] is not None:d['panel_rgb']=d['pic'].reshape(-1,3).mean(0);d['panel_aspect']=d['pic'].shape[1]/max(1,d['pic'].shape[0])
            self.gantries.append(d)
        for h in self.highlights:h['pic']=load_picture(directory,h.get('image',''))
        for p in self.pois:
            p['chain']=float(ch[self.tree.query([p['x'],p['y']])[1]])
            p['km_auto_m']=self.stationing.km([p['x'],p['y']])
            # Sem início marcado mantém o comportamento 1.2 (km apenas quando digitado).
            if self.km_active and p.get('km_mode','auto')=='auto' and p.get('source')!='oae_mark' and not p.get('per_location'):p['km_m']=p['km_auto_m']
        span=(np.array(self.report['bounds'])-self.center)@self.R
        corners=np.array([[x,y] for x in [self.report['bounds'][0][0],self.report['bounds'][1][0]] for y in [self.report['bounds'][0][1],self.report['bounds'][1][1]]]);q=(corners-self.center)@self.R
        self.overview=max(np.ptp(q[:,0])*1.15,np.ptp(q[:,1])*self.W/(self.H*.76)*1.15,s.view_width_m)
        if getattr(s,'advance_mode','duracao')=='velocidade':
            # 1.27: a duração do vídeo sai da velocidade de avanço escolhida (o percurso leva comprimento/velocidade).
            T=duration_for_speed(self.length,float(s.advance_speed_kmh),bool(self.pois),getattr(s,'camera_mode','obras'))
            s=self.s=s.model_copy(update={'duration_s':T})
        self.exclusion=unary_union([Polygon([(p.x,p.y) for p in a]).buffer(0) for a in s.exclusions]) if s.exclusions else Polygon()
        self.has_surface=any(e['role'] in ['pavement','existing_pavement'] and e['closed'] for e in self.items);self.prepare_surface(status);self.prepare_routes();self.static={};self.headers={};self.shown_poi=None;self.poi_since=-100
        self.prepare_details()
        self.prepare_terrain(status)
        from .detail import Detail
        self.detail=Detail(self)
        status(.25,'Geometria pronta')
    @classmethod
    def light(cls,directory,s,status=lambda *a:None):
        """1.11: cena só com geometria, estaqueamento e rede de tráfego (sem imagem aérea nem rasterização).
        Usada pela análise para o editor mostrar fluxos, sentidos e sinalização sem gerar a prévia."""
        self=cls.__new__(cls);self.directory=Path(directory);self.s=s;self.W=s.width;self.H=s.width*9//16;self.scale=self.W/2560
        status(.1,'Lendo geometria');self.items,self.axis,self.ds,self.axes,self.report=analyze(directory,s)
        from .image_context import accepted_items
        self.image_context_items=accepted_items(s,self.items,directory)
        self.length=self.ds[-1]
        ch=np.arange(0,self.length+2,2);p=np.column_stack([np.interp(ch,self.ds,self.axis[:,k]) for k in range(2)]);self.ch=ch;self.dense=p;self.tree=cKDTree(p)
        self.stationing=Stationing.from_settings(self.axis,s);self.km_active=s.chainage.mode!='off'
        self.oae=oae_items(s,self.stationing)
        self.pois=[v.model_dump() for v in s.pois] or [dict(p) for p in self.report['kmz_pois']]
        if s.per_callouts and s.works:self.pois+=works_to_pois(s,self.axis,self.ds,self.stationing if self.km_active else None)
        self.pois+=oae_pois(self.oae)
        for p in self.pois:
            p['chain']=float(ch[self.tree.query([p['x'],p['y']])[1]]);p['km_auto_m']=self.stationing.km([p['x'],p['y']])
            if self.km_active and p.get('km_mode','auto')=='auto' and p.get('source')!='oae_mark' and not p.get('per_location'):p['km_m']=p['km_auto_m']
        self.exclusion=unary_union([Polygon([(p.x,p.y) for p in a]).buffer(0) for a in s.exclusions]) if s.exclusions else Polygon()
        status(.5,'Calculando fluxos e sinalização');self.prepare_routes()
        return self
    def color(self,role):
        if role in ('pavement','existing_pavement','shoulder'):
            from .pavement import chosen,PRESET_FILL
            st=chosen(self.s,role)
            if st is not None:return st.fill or '#%02x%02x%02x'%PRESET_FILL[role]
            if getattr(self,'_rigid_roles',None) is None:
                ents=[e for e in getattr(self,'items',[]) if e.get('closed') and e.get('role') in ('pavement','existing_pavement','shoulder')]
                self._rigid_roles={r for r in ('pavement','existing_pavement','shoulder') if any(e['role']==r for e in ents) and all(e.get('material')=='rigido' for e in ents if e['role']==r)}
            if role in self._rigid_roles:
                from .pavement import TECH_RIGID,ART_RIGID
                c=TECH_RIGID[role][0] if getattr(self.s,'style_profile','padrao')=='tecnico' else ART_RIGID[role];return '#%02x%02x%02x'%c
        if getattr(self.s,'style_profile','padrao')=='tecnico' and role in visual.TECH_FILL:return visual.TECH_FILL[role]
        return (getattr(self.s,'role_colors',None) or {}).get(role) or COLORS[role]
    def worldpx(self,p):
        return np.column_stack([(p[:,0]-self.box[0])/self.px,(self.box[3]-p[:,1])/self.px])
    def at(self,ch):return np.array([np.interp(ch,self.ds,self.axis[:,k]) for k in range(2)])
    def prepare_surface(self,status):
        self.domain=[e['points'] for e in self.items if e['role']=='domain']
        self.domain_dashes=[]
        for points in self.domain:
            ln=LineString(points)
            self.domain_dashes.extend([[ln.interpolate(v).coords[0],ln.interpolate(min(ln.length,v+6)).coords[0]] for v in np.arange(0,ln.length,10)])
        self.domain_dashes=np.array(self.domain_dashes).reshape(-1,2,2)
        self.domain_centers=self.domain_dashes.mean(1)
        self.geometry_cache_hit=False;cache_dir=None
        try:
            signature=hashlib.sha256()
            extra=sorted((self.directory/'camadas').glob('*.dxf')) if (self.directory/'camadas').exists() else []
            for file in [self.directory/'input.dxf',self.directory/'input.kmz',Path(__file__),Path(__file__).with_name('geometry.py'),Path(__file__).with_name('earthworks.py'),Path(__file__).with_name('visual.py')]+extra:
                if file.exists():
                    with file.open('rb') as f:
                        while chunk:=f.read(1024*1024):signature.update(chunk)
            dump=self.s.model_dump();config={k:dump[k] for k in ['layers','crs','units_to_m','reverse_axis','exclusions','dxf_alignment','overlays']}
            if dump.get('earthwork_look','hatch')!='hatch':config['earthwork_look']=dump['earthwork_look']
            if dump.get('accesses'):config['accesses']=dump['accesses']
            if dump.get('style_profile','padrao')!='padrao':config['style_profile']=dump['style_profile']
            if dump.get('pavement_styles'):config['pavement_styles']=dump['pavement_styles']
            if dump.get('custom_axis'):config['custom_axis']=dump['custom_axis']
            if dump.get('hatch_roles'):config['hatch_roles']=dump['hatch_roles']
            if dump.get('hatch_auto'):config['hatch_auto']=True
            for k,dv in (('pavement_material','flexivel'),('existing_material','flexivel'),('shoulder_material','flexivel'),('joint_spacing_m',5)):
                if dump.get(k,dv)!=dv:config[k]=dump[k]
            for k in ('pavement_areas','shoulder_marks','texture_areas'):
                if dump.get(k):config[k]=dump[k]
            if dump.get('role_colors'):config['role_colors']=dump['role_colors']
            if dump.get('auto_earthworks') is False:config['auto_earthworks']=False
            for k in ('hidden_layers','frozen_layers'):
                if dump.get(k):config[k]=sorted(dump[k])
            signature.update(json.dumps([config,self.box,self.n],sort_keys=True).encode())
            self.geometry_signature=signature.hexdigest();cache_dir=self.directory/'cache_geometria'/signature.hexdigest()[:24]
            if (cache_dir/'ready.json').exists():
                overlay=np.load(cache_dir/'overlay.npy',mmap_mode='r',allow_pickle=False);stations=np.load(cache_dir/'stations.npy',mmap_mode='r',allow_pickle=False)
                if not (cache_dir/'surface.npy').exists():raise ValueError('Cache anterior à 1.5')
                self.surface=np.load(cache_dir/'surface.npy',mmap_mode='r',allow_pickle=False)
                if overlay.shape!=(self.n,self.n,4) or overlay.dtype!=np.uint8 or stations.shape!=(self.n,self.n) or stations.dtype!=np.uint16:raise ValueError('Cache incompatível')
                self.overlay=overlay;self.stations=stations;self.geometry_cache_hit=True
                status(.22,'Geometria recuperada do cache local');return
        except (OSError,ValueError):
            if cache_dir is not None:shutil.rmtree(cache_dir,ignore_errors=True)
            cache_dir=None
        n=self.n;self.overlay=np.zeros((n,n,4),np.uint8);roadmask=np.zeros((n,n),np.uint8);stationmask=np.zeros((n,n),np.uint8);self.surface=np.zeros((n,n),np.uint8)
        from .pavement import paint_rigid,JointField
        for role in ['cut','fill','existing_pavement','pavement','shoulder','median','barrier','oae']:
            mask=np.zeros((n,n),np.uint8);lines=np.zeros_like(mask);rmask=None
            for e in self.items:
                if e['role']!=role:continue
                if e.get('material')=='rigido' and e['closed']:
                    # 1.21: pavimento rígido (placas de concreto).
                    if rmask is None:rmask=np.zeros_like(mask)
                    cv2.fillPoly(rmask,[np.rint(self.worldpx(e['points'])).astype(np.int32)],255)
                    for hole in e.get('holes',[]):cv2.fillPoly(rmask,[np.rint(self.worldpx(hole)).astype(np.int32)],0)
                if role in ['cut','fill'] and not self.exclusion.is_empty:
                    g=poly(e) if e['closed'] else LineString(e['points']);g=g.difference(self.exclusion)
                    geoms=list(g.geoms) if hasattr(g,'geoms') else [g]
                    paths=[np.array(v.exterior.coords if v.geom_type=='Polygon' else v.coords) for v in geoms if not v.is_empty and v.geom_type in ['Polygon','LineString']]
                else:paths=[e['points']]
                for p in paths:
                    q=np.rint(self.worldpx(p)).astype(np.int32)
                    if e['closed']:
                        temp=np.zeros_like(mask);cv2.fillPoly(temp,[q],255)
                        for hole in e.get('holes',[]):cv2.fillPoly(temp,[np.rint(self.worldpx(hole)).astype(np.int32)],0)
                        mask=cv2.bitwise_or(mask,temp)
                    else:cv2.polylines(lines,[q],False,255,1,cv2.LINE_AA)
            if role in ['cut','fill']:
                earth_color,alpha=earthwork_style(mask,lines,role,self.px,look=getattr(self.s,'earthwork_look','hatch'))
                if not self.exclusion.is_empty:
                    # Final raster clip also removes widened offset strokes in cleaned areas.
                    geoms=list(self.exclusion.geoms) if hasattr(self.exclusion,'geoms') else [self.exclusion]
                    for area in geoms:
                        if area.geom_type!='Polygon':continue
                        clip=np.zeros_like(mask)
                        cv2.fillPoly(clip,[np.rint(self.worldpx(np.array(area.exterior.coords))).astype(np.int32)],255)
                        for hole in area.interiors:cv2.fillPoly(clip,[np.rint(self.worldpx(np.array(hole.coords))).astype(np.int32)],0)
                        alpha[clip>0]=0
            else:alpha=np.maximum(mask,lines)
            rgb=np.array([int(self.color(role)[i:i+2],16) for i in [1,3,5]],np.uint8)
            if role=='pavement':
                # The asphalt texture remains fixed in project coordinates.
                grain=np.random.default_rng(57).integers(-3,4,(n,n),dtype=np.int16)
                color=np.clip(rgb.astype(np.int16)[None,None,:]+grain[:,:,None],0,255).astype(np.uint8);del grain
            elif role in ['cut','fill']:color=earth_color
            else:color=rgb
            if getattr(self.s,'style_profile','padrao')=='tecnico' and role in visual.TECH_HATCH:
                # 1.20: hachura fixa nas coordenadas do projeto (dourada na pista nova, cinza-azulada na existente).
                hm,hc=visual.surface_hatch((n,n),self.box[0],self.box[3],self.px,role)
                base_c=np.broadcast_to(np.asarray(color,np.float32),(n,n,3)) if np.ndim(color)==1 else color.astype(np.float32)
                color=(base_c*(1-hm[:,:,None]*.85)+hc*hm[:,:,None]*.85).astype(np.uint8);del hm
            if rmask is not None:
                if getattr(self,'joint_field',None) is None:self.joint_field=JointField(self.axes)
                color=paint_rigid(color,rmask>0,role,self.box[0],self.box[3],self.px,self.joint_field,float(getattr(self.s,'joint_spacing_m',5)),getattr(self.s,'style_profile','padrao')=='tecnico')
            from .pavement import chosen,paint_style
            st=chosen(self.s,role) if role in ('pavement','existing_pavement','shoulder') else None
            if st is not None:color=paint_style(color,mask>0,role,self.box[0],self.box[3],self.px,st,getattr(self,'joint_field',None) or JointField(self.axes),float(getattr(self.s,'joint_spacing_m',5)))  # 1.21: representação escolhida pelo usuário
            select=alpha>0;old=self.overlay[select,:3].astype(np.float32);a=alpha[select,None]/255
            c=color[select] if getattr(color,'ndim',1)==3 else color
            self.overlay[select,:3]=(old*(1-a)+c*a).astype(np.uint8);self.overlay[:,:,3]=np.maximum(self.overlay[:,:,3],alpha)
            # Use straight RGB colors for translucent earthwork over satellite.
            if role in ['cut','fill']:self.overlay[select,:3]=earth_color[select]
            stationmask=np.maximum(stationmask,alpha)
            if role in visual.SURF:self.surface[mask>0]=visual.SURF[role]
            elif role in visual.EARTH_SURF and getattr(self.s,'earthwork_look','hatch')=='natural':self.surface[mask>0]=visual.EARTH_SURF[role]
            elif role in ['median','barrier']:self.surface[mask>0]=0
            if rmask is not None:self.surface[(mask>0)&(rmask>0)]=visual.SURF['oae']   # textura de concreto
            if role in ['pavement','existing_pavement','shoulder','oae']:roadmask=np.maximum(roadmask,mask)
        for e in self.items:
            if e.get('tex_code'):
                # 1.27: área com textura própria (código de superfície exclusivo).
                tm=np.zeros((n,n),np.uint8);cv2.fillPoly(tm,[np.rint(self.worldpx(e['points'])).astype(np.int32)],255)
                for hole in e.get('holes',[]):cv2.fillPoly(tm,[np.rint(self.worldpx(hole)).astype(np.int32)],0)
                self.surface[tm>0]=e['tex_code']
        for code,base,_,pts in self.texture_areas():
            # 1.29: região com textura própria (talude, canteiro, pavimento): só onde a superfície é do tipo escolhido.
            tm=np.zeros((n,n),np.uint8);cv2.fillPoly(tm,[np.rint(self.worldpx(pts)).astype(np.int32)],255)
            self.surface[(tm>0)&(self.surface==base)]=code
        # Camadas DXF adicionais sem classe: desenhadas com o estilo da camada, na ordem escolhida.
        groups={}
        for e in self.items:
            if e['role']=='overlay':groups.setdefault(e['overlay_order'],[]).append(e)
        for order in sorted(groups):
            st=groups[order][0]['style'];rgb=np.array([int(st['color'][i:i+2],16) for i in (1,3,5)],np.uint8)
            mask=np.zeros((n,n),np.uint8);lw=max(1,round(st['width_m']/self.px))
            for e in groups[order]:
                q=np.rint(self.worldpx(e['points'])).astype(np.int32)
                if e['closed'] and st['fill']:cv2.fillPoly(mask,[q],115)
            for e in groups[order]:
                q=np.rint(self.worldpx(e['points'])).astype(np.int32);cv2.polylines(mask,[q],e['closed'],255,lw,cv2.LINE_AA)
            a=(mask.astype(np.float32)*st['opacity']).astype(np.uint8);del mask;select=a>0
            if not select.any():continue
            f=a[select,None]/255;old=self.overlay[select,:3].astype(np.float32)
            self.overlay[select,:3]=(old*(1-f)+rgb*f).astype(np.uint8);self.overlay[:,:,3]=np.maximum(self.overlay[:,:,3],a);stationmask=np.maximum(stationmask,a)
        # Subtle shadow at the outside of the pavement footprint.
        shadow=cv2.GaussianBlur(roadmask,(0,0),1.2);outside=(self.overlay[:,:,3]==0)&(shadow>0)
        self.overlay[outside,:3]=0;self.overlay[outside,3]=(shadow[outside]*.18).astype(np.uint8)
        self.stations=np.full((n,n),65535,np.uint16)
        ys,xs=np.nonzero(stationmask)
        for start in range(0,len(xs),250000):
            xx=xs[start:start+250000];yy=ys[start:start+250000];pts=np.column_stack([self.box[0]+xx*self.px,self.box[3]-yy*self.px]);ids=self.tree.query(pts)[1];self.stations[yy,xx]=np.minimum(65534,self.ch[ids]/self.length*65534).astype(np.uint16)
        if any(e.get('frozen') for e in self.items):
            # 1.26: camada congelada aparece pronta desde o início do vídeo (sem a construção progressiva).
            fz=np.zeros((n,n),np.uint8)
            for e in self.items:
                if not e.get('frozen'):continue
                q=np.rint(self.worldpx(e['points'])).astype(np.int32)
                if e['closed']:cv2.fillPoly(fz,[q],255)
                cv2.polylines(fz,[q],bool(e['closed']),255,3)
            self.stations[(fz>0)&(self.stations!=65535)]=0
        if cache_dir is not None:
            try:
                import uuid
                temp=cache_dir.parent/('preparando_'+uuid.uuid4().hex);temp.mkdir(parents=True)
                np.save(temp/'overlay.npy',self.overlay,allow_pickle=False);np.save(temp/'stations.npy',self.stations,allow_pickle=False);np.save(temp/'surface.npy',self.surface,allow_pickle=False)
                (temp/'ready.json').write_text(json.dumps({'shape':self.n,'version':'1.5'}),encoding='utf-8')
                if not cache_dir.exists():temp.replace(cache_dir)
                else:shutil.rmtree(temp,ignore_errors=True)
                # Retain at most two previous variants; source files and user results are untouched.
                previous=sorted([p for p in cache_dir.parent.iterdir() if p.is_dir() and p!=cache_dir],key=lambda p:p.stat().st_mtime,reverse=True)
                for old in previous[1:]:shutil.rmtree(old,ignore_errors=True)
            except OSError:
                status(.24,'Geometria pronta; cache em disco indisponível, processamento segue normalmente.')
    def prepare_routes(self):
        roads=[poly(e) for e in self.items if e['closed'] and e['role'] in ['pavement','oae']]
        roads.extend(poly(e) for e in self.items if e['closed'] and e['role']=='existing_pavement')
        obstacles=[poly(e) for e in self.items if e['closed'] and e['role'] in ['median','barrier']]
        decks=[o['deck'] for o in self.oae]
        roads.extend(decks)
        from .markup import oae_direction_marks
        self.network=TrafficNetwork(roads,obstacles,self.axes,self.axis,self.ds,self.s,[poly(e) for e in self.items if e['closed'] and e['role']=='oae']+decks,oae_direction_marks(self.oae,self.stationing),[e['points'] for e in self.items if e['role']=='edge_line' and len(e['points'])>=2],[e for e in self.items if e['role']=='sign_h'],[e for e in self.items if e['role']=='sign_v'])
        self.allowed=self.network.allowed
        self.save_editor_geometry(roads,obstacles)
        self.routes=[(e['p'],e['t'],np.ones(len(e['p']),bool),e['length'],i) for i,e in enumerate(self.network.edges)]
        self.markings=np.array([[a,b] for a,b,color in self.network.markings]).reshape(-1,2,2)
        self.marking_colors=np.array([color for a,b,color in self.network.markings],np.uint8).reshape(-1,3)
        # 1.15: pinturas preenchidas (setas de faixa, zebrados, retenções, PARE, faixas de pedestre).
        from . import signage
        self.paint_items=signage.paint_arrays(self.network) if self.network.full else []
        self.paint_centers=np.array([c for c,_,_,_ in self.paint_items]).reshape(-1,2)
        self.paint_chains=self.ch[self.tree.query(self.paint_centers)[1]] if len(self.paint_items) else np.zeros(0)
        sp=getattr(self.s,'signage_paint',None)
        if sp is not None and (sp.white or sp.yellow):
            # 1.29: cores da tinta escolhidas pelo usuário.
            hx=lambda h:np.array([int(h[i:i+2],16) for i in (1,3,5)],np.uint8)
            W0=np.array(signage.WHITE,np.uint8);Y0=np.array(signage.YELLOW,np.uint8)
            if len(self.marking_colors):
                mw=(self.marking_colors==W0).all(1);my=(self.marking_colors==Y0).all(1)
                if sp.white:self.marking_colors[mw]=hx(sp.white)
                if sp.yellow:self.marking_colors[my]=hx(sp.yellow)
            self.paint_items=[(c,r,rings,tuple(int(v) for v in (hx(sp.white) if sp.white and tuple(col)==signage.WHITE else hx(sp.yellow) if sp.yellow and tuple(col)==signage.YELLOW else col))) for c,r,rings,col in self.paint_items]
        if getattr(self.s,'railways',[]) or getattr(self.s,'traffic_signals',[]):
            from .transport import Transport
            controls=Transport(self.s,self.network).report();self.report['transport_controls']=controls;self.report['warnings'].extend(controls['warnings'])
        self.report['traffic_network']=self.network.report
        self.report['warnings'].extend(self.network.warnings)
        (self.directory/'traffic_network.json').write_text(json.dumps(self.network.report,ensure_ascii=False,indent=2),encoding='utf-8')
    def prepare_terrain(self,status=lambda *a:None):
        # Elevação: a ortofoto não é deformada; o relevo vira sombreamento/curvas e superfície 3D na cabine.
        self.terrain=None;el=self.s.elevation
        if el.source=='none':return
        from . import elevation as E
        box=[float(v) for v in self.box];n=min(self.n,2048 if el.source=='local' else 1024)
        try:
            status(.24,'Carregando elevação do terreno')
            dem,label=E.local_dem(self.directory,el,self.s.crs,box,n) if el.source=='local' else E.web_dem(self.directory,self.s.crs,box,n,status=status)
        except Exception as exc:
            self.report['warnings'].append('Elevação indisponível: '+str(exc)[:200]);return
        self.terrain=E.Terrain(dem,box,label,self.surface,self.stations,self.length,el.level_road,el.exaggeration,self.oae)
        E.save_cache(self.directory,self.terrain)
        if el.hillshade or el.contours:
            self.map=np.array(self.map)
            if el.hillshade:E.shade_map(self.map,dem,self.terrain.cell,el.hillshade_opacity,el.exaggeration)
            if el.contours:E.contours(self.map,dem,el.contour_interval_m,box,self.worldpx)
        self.attribution+=' • '+label
    def prepare_details(self):
        # Juntas, guarda-corpos e bordas vetoriais para o modo de qualidade 'enhanced'.
        self.oae_detail=[];self.edges=[];self._fit={}
        if not self.enhanced:return
        from shapely.geometry import LineString as LS
        tan=np.gradient(self.dense,axis=0);tan/=np.maximum(np.linalg.norm(tan,axis=1)[:,None],1e-9)
        def side_rails(ring):
            ring=np.asarray(ring);keep=[];cur=[]
            for a,b in zip(ring[:-1],ring[1:]):
                d=b-a;L=np.linalg.norm(d)
                if L<1e-6:continue
                t=tan[self.tree.query((a+b)/2)[1]]
                if abs(np.dot(d/L,t))>.75:
                    if not cur:cur=[a]
                    cur.append(b)
                elif cur:keep.append(np.array(cur));cur=[]
            if cur:keep.append(np.array(cur))
            return [k for k in keep if len(k)>1 and np.linalg.norm(np.diff(k,axis=0),axis=1).sum()>3]
        def joints(polygon):
            out=[];ids=np.flatnonzero(contains_xy(polygon,self.dense[:,0],self.dense[:,1]))
            if not len(ids):return out
            last=-1e9
            for i in ids:
                if self.ch[i]-last<30:continue
                last=self.ch[i];n=np.array([-tan[i,1],tan[i,0]]);seg=LS([self.dense[i]-n*80,self.dense[i]+n*80]).intersection(polygon)
                for g in (getattr(seg,'geoms',None) or [seg]):
                    if g.geom_type=='LineString' and g.length>1:out.append(np.asarray(g.coords))
            return out
        for e in self.items:
            if e['role']=='oae' and e['closed']:
                pg=poly(e)
                for g in (list(pg.geoms) if hasattr(pg,'geoms') else [pg]):
                    if g.geom_type!='Polygon' or g.area<20:continue
                    ring=np.asarray(g.buffer(-.3).exterior.coords) if not g.buffer(-.3).is_empty and g.buffer(-.3).geom_type=='Polygon' else np.asarray(g.exterior.coords)
                    self.oae_detail.append({'ring':np.asarray(g.exterior.coords),'level':5.,'joints':joints(g),'rails':side_rails(ring),'bbox':np.r_[np.asarray(g.bounds)],'chain_max':float(self.ch[self.tree.query(np.asarray(g.exterior.coords))[1]].max())})
        for o in self.oae:
            g=o['deck'];g=g if g.geom_type=='Polygon' else max(g.geoms,key=lambda x:x.area)
            js=joints(g) if not o.get('polygon') else [h for h in o.get('heads',[])]+joints(g)
            self.oae_detail.append({'ring':np.asarray(g.exterior.coords),'level':float(o['level_m']),'joints':js,'rails':[],'bbox':np.r_[np.asarray(g.bounds)],'chain_max':o['chain'][1],'mark':True})
        # Bordas da superfície de rolamento (união das áreas: sem costuras entre hachuras vizinhas).
        surf=unary_union([poly(e) for e in self.items if e['closed'] and e['role'] in ('pavement','existing_pavement','shoulder','oae')])
        for g in (list(surf.geoms) if hasattr(surf,'geoms') else [surf]):
            if g.geom_type!='Polygon' or g.is_empty:continue
            for r in [g.exterior]+list(g.interiors):
                r=np.asarray(r.coords)
                for k in range(0,len(r)-1,200):
                    c=r[k:k+201]
                    if len(c)>1:self.edges.append((c,np.r_[c.min(0),c.max(0)]))
        self.edge_boxes=np.array([b for _,b in self.edges]).reshape(-1,4)
    def save_editor_geometry(self,roads,obstacles):
        # Superfícies usadas pelo editor para validar fluxos desenhados (rejeição com motivo).
        import shapely
        try:
            d=self.directory/'editor';d.mkdir(exist_ok=True)
            for name,g in [('roads',unary_union(roads) if roads else Polygon()),('obstacles',unary_union(obstacles) if obstacles else Polygon()),('allowed',self.allowed)]:
                tmp=d/(name+'.wkb.tmp');tmp.write_bytes(shapely.to_wkb(g));tmp.replace(d/(name+'.wkb'))
        except OSError:pass
    def editor_data(self):
        st=self.stationing;step=max(1,len(self.axis)//6000)
        def pts(p,stride=1):return np.round(np.asarray(p)[::stride],3).tolist()
        from .flow_diagnostics import flow_diagnostics
        diagnostics=flow_diagnostics(self.network)
        from . import store
        full=[{'id':i,'points':np.asarray(r['points'],float).tolist(),'forward':r['forward'],'both':r['both'],'source':r['source'],'origin_id':r.get('origin_id',r['base']),'origin_key':r.get('origin_key',''),'level':r.get('level',0),'disabled':r['disabled']} for i,r in enumerate(self.network.raw_info)]
        from .dependencies import revisions
        store.write_json(self.directory/'editor/full_flows.json',{'revision':revisions(self.directory,self.s)['editor'],'segments':full})
        segments=[]
        for i,r in enumerate(self.network.raw_info):
            if r.get('automatic_excluded'):continue
            p=r['points'];stride=max(1,len(p)//400)
            q=p[::stride] if len(p)>2 else p
            if len(q)<2 or not np.array_equal(q[-1],p[-1]):q=np.vstack([q,p[-1:]])
            segments.append({**diagnostics[i],'route':r.get('route'),'id':i,'base':r['base'],'origin_id':r.get('origin_id',r['base']),'origin_key':r.get('origin_key',''),'level':r.get('level',0),'kind':r['kind'],'forward':r['forward'],'both':r['both'],'disabled':r['disabled'],'override_ids':r.get('override_ids',[]),'protected_overrides':r.get('protected_overrides',[]),'reversed':r['reversed'],'manual':r['manual'],'source':r['source'],'points':pts(q),'mid':pts(p[len(p)//2][None])[0],'speed_kmh':r.get('speed_kmh'),'length_m':round(float(np.sum(np.linalg.norm(np.diff(p,axis=0),axis=1))),1)})
        from .dependencies import revisions
        return {'engine_revision':revisions(self.directory,self.s)['editor'],'crs':self.s.crs,'axis':pts(self.axis,step) if step==1 else pts(np.vstack([self.axis[::step],self.axis[-1:]])),'axis_length_m':self.length,
                'stationing':{**st.info(),'mode':self.s.chainage.mode},
                'alignment':self.report.get('alignment'),'segments':segments,
                'pois':[{'id':p.get('id'),'title':p.get('title'),'kind':p.get('kind'),'x':p['x'],'y':p['y'],'km_m':p.get('km_m'),'km_auto_m':p.get('km_auto_m'),'km_mode':p.get('km_mode','auto'),'anchor':p.get('anchor'),'source':p.get('source','')} for p in self.pois],
                'oae':[{'id':o['id'],'name':o['name'],'km_start_m':o['km_start_m'],'km_end_m':o['km_end_m'],'km_auto':o['km_auto'],'line':pts(o['line']),'level_m':o['level_m'],'width_m':o['width_m'],'direction':o.get('direction','both'),'polygon':bool(o.get('polygon'))} for o in self.oae],
                'itineraries':len(self.network.paths),'warnings':self.report['warnings'][-20:],
                # 1.11: sinalização e setas como no vídeo (vetores nítidos no editor).
                'markings':[[round(float(a[0]),2),round(float(a[1]),2),round(float(b[0]),2),round(float(b[1]),2),1 if tuple(c)==(244,200,70) else 0] for a,b,c in self.network.markings],
                'arrows':[[round(float(p[0]),2),round(float(p[1]),2),round(float(t[0]),4),round(float(t[1]),4)]+([round(float(c[0]),2),round(float(c[1]),2)] if c is not None else []) for (p,t),c in zip(self.network.arrows,list(getattr(self.network,'arrow_anchors',[]) or [])+[None]*len(self.network.arrows))],
                # 1.15: pinturas preenchidas e placas (como no vídeo).
                'signage_detail':'full' if self.network.full else 'basic',
                'paint':[[1 if tuple(c)==(244,200,70) else 0,[np.round(r,2).tolist() for r in rings]] for _,_,rings,c in getattr(self,'paint_items',[])],
                'signs':[{'x':round(float(g['point'][0]),2),'y':round(float(g['point'][1]),2),'code':g['code'],'text':g.get('text',''),'auto':bool(g.get('auto')),'source':g.get('source','auto')} for g in getattr(self.network,'signs',[])],
                'paths':[{'kinds':pth['kinds'],'p':pts(pth['p'][::max(1,len(pth['p'])//300)])} for pth in self.network.paths[:256]],
                **connection_data(self.network)}
    def texture_areas(self):
        if not hasattr(self,'_tex_areas'):self._tex_areas=texture_area_codes(self.items,self.s)
        return self._tex_areas
    def advance_map(self,u):
        """1.27: fração do percurso (0..1) na fração de tempo u, respeitando os trechos com velocidade própria."""
        if not hasattr(self,'_adv'):
            zones=[z for z in getattr(self.s,'advance_zones',[]) or [] if z.enabled]
            if not zones:self._adv=None
            else:
                w=np.ones(len(self.ch))
                for z in zones:
                    a=float(self.ch[self.tree.query([z.start.x,z.start.y])[1]]);b=float(self.ch[self.tree.query([z.end.x,z.end.y])[1]]);lo,hi=min(a,b),max(a,b)
                    w[(self.ch>=lo)&(self.ch<=hi)]=100./z.speed_pct
                W=np.r_[0,np.cumsum((w[1:]+w[:-1])/2*np.diff(self.ch))];self._adv=(W/max(W[-1],1e-9),self.ch/max(self.length,1e-9))
        if self._adv is None:return u
        return float(np.interp(u,self._adv[0],self._adv[1]))
    def advance_duration(self):
        """1.27: duração do percurso para a velocidade de avanço escolhida (o restante do vídeo continua igual)."""
        v=float(getattr(self.s,'advance_speed_kmh',150))/3.6;return self.length/max(v,.1)
    def pose(self,t):
        kp=ambiente.pose_pontos(self,t)   # 1.36: câmera por pontos-chave
        if kp is not None:self._key_title=kp[2];return kp[0],kp[1],1,None,'chave'
        if self.s.duration_s<45 and self.s.short_video_mode=='auto':
            f=np.clip(t/max(self.s.duration_s,1),0,1);smooth=f*f*(3-2*f)
            candidates=sorted(self.pois,key=lambda p:p['chain'])
            count=min(len(candidates),max(1,int(self.s.duration_s/3)))
            poi=candidates[min(count-1,int(f*count))] if count else None
            return self.center,self.overview*(1-.06*smooth),1,poi,'curto'
        T=self.s.duration_s;intro=min(8,T*.12);outro=min(10,T*.12);detail=min(88,T*.4) if self.pois else 0;tour=T-intro-outro-detail
        if getattr(self.s,'camera_mode','obras')=='continuo':
            # 1.20: voo contínuo até o fim do segmento e breve permanência no ponto final (sem paradas nas obras).
            intro=min(4,T*.06);outro=min(5,T*.06);tour=T-intro-outro
            if t<intro:
                f=t/intro;f=f*f*(3-2*f);return self.center*(1-f)+self.smooth[0]*f,self.overview*(1-f)+self.s.view_width_m*f,0,None,'inicio'
            if t<intro+tour:
                f=(t-intro)/max(tour,.01);f=f*f*(3-2*f)*.12+f*.88;f=self.advance_map(f);ch=f*self.length
                return np.array([np.interp(ch,self.ch,self.smooth[:,k]) for k in range(2)]),self.s.view_width_m,f,None,'tour'
            f=np.clip((t-intro-tour)/max(outro,.01),0,1);f=f*f*(3-2*f)
            return self.smooth[-1],self.s.view_width_m*(1+.15*f),1,None,'fim'
        if t<intro:
            f=t/intro;f=f*f*(3-2*f);return self.center*(1-f)+self.smooth[0]*f,self.overview*(1-f)+self.s.view_width_m*f,0,None,'inicio'
        if t<intro+tour:
            f=(t-intro)/max(tour,.01);f=f-float(np.sin(2*np.pi*f))*.06;f=self.advance_map(f);ch=f*self.length;cam=np.array([np.interp(ch,self.ch,self.smooth[:,k]) for k in range(2)]);poi=min(self.pois,key=lambda p:abs(p['chain']-ch)) if self.pois else None
            if poi and abs(poi['chain']-ch)>550:poi=None
            return cam,self.s.view_width_m,f,poi,'tour'
        if t<T-outro and self.pois:
            candidates=sorted(self.pois,key=lambda p:p['chain'])[:11];k=min(len(candidates)-1,int((t-intro-tour)/detail*len(candidates)));p=candidates[k];return np.array([p['x'],p['y']]),self.s.view_width_m,1,p,'detalhe-'+str(k)
        f=np.clip((t-(T-outro))/max(outro*.6,.01),0,1);f=f*f*(3-2*f)
        return self.smooth[-1]*(1-f)+self.center*f,self.s.view_width_m*(1-f)+self.overview*f,1,None,'fim'
    @property
    def sombra_veiculo(self):
        """1.36: sombra pela hora do sol (desligado: sol fixo a noroeste, como antes)."""
        return ambiente.vetor_sombra(self.s.sun_hour) if getattr(self.s,'sun_shadows',False) else ambiente.SOMBRA_VEICULO
    @property
    def sombra_oae(self):return ambiente.vetor_sombra(self.s.sun_hour)*1.45 if getattr(self.s,'sun_shadows',False) else ambiente.SOMBRA_OAE
    def screen(self,p,cam,width):
        q=(np.asarray(p)-cam)@self.R/(width/self.W);return np.column_stack([q[:,0]+self.W/2,self.H/2-q[:,1]])
    def draw_base(self,cam,width,progress):
        m=width/self.W;cp=self.worldpx(cam[None])[0];dx=np.array([self.right[0],-self.right[1]])*m/self.px;dy=np.array([-self.up[0],self.up[1]])*m/self.px;org=cp-dx*self.W/2-dy*self.H/2;mat=np.column_stack([dx,dy,org]).astype(np.float32)
        # Supersample each camera crop and reduce with Lanczos.
        AA=1.5;big=mat.copy();big[:,:2]/=AA
        def base_im():
            if getattr(self,'_matte',None) is not None:return np.full((self.H,self.W,3),self._matte,np.uint8)
            if self.s.render_profile=='rapido':
                # Perfil rápido: sem superamostragem da imagem aérea (um único warp linear).
                return cv2.warpAffine(self.map,mat,(self.W,self.H),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REFLECT_101)
            if getattr(self.s,'render_engine','otimizado')=='otimizado' and m/self.px<.7:
                # 1.24: imagem base ampliada (pixel da tela menor que o do mosaico): a superamostragem não acrescenta nada.
                return cv2.warpAffine(self.map,mat,(self.W,self.H),flags=cv2.INTER_CUBIC|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REFLECT_101)
            b=cv2.warpAffine(self.map,big,(int(self.W*AA),int(self.H*AA)),flags=cv2.INTER_CUBIC|cv2.WARP_INVERSE_MAP,borderMode=cv2.BORDER_REFLECT_101);return cv2.resize(b,(self.W,self.H),interpolation=cv2.INTER_LANCZOS4)
        base_ov=lambda:cv2.warpAffine(self.overlay,mat,(self.W,self.H),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP)
        im=ov=None
        # 1.11: perto do chão, imagem e desenho vêm dos ladrilhos de detalhe (0,2 m/pixel).
        dsurf=None;det=getattr(self,'detail',None)
        wd=det.weight(m) if det is not None and self.s.render_profile!='rapido' else 0.
        if wd>=1 and m<FINE_M and det.R>FINE_R:
            # 1.19: vista muito próxima (≈10 m na tela): ladrilhos de 5 cm, para a prévia não virar um borrão.
            if getattr(self,'detail_fine',None) is None:
                from .detail import Detail
                self.detail_fine=Detail(self,FINE_R)
            det=self.detail_fine
        if wd>0:
            mat_on=getattr(self,'_matte',None) is None
            dimg,imask,dov,dsurf=det.compose(cam,width,det.enabled_imagery and not det.offline and mat_on,det.enabled_overlay)
            if dimg is not None:
                # 1.24: com o detalhe cobrindo todo o quadro, o mosaico base nem é calculado (mesmo resultado, mais rápido).
                if wd>=1 and int(imask.min())==255:im=dimg.copy()
                else:
                    im=base_im();k=(imask.astype(np.float32)*(wd/255))[:,:,None];im=(im*(1-k)+dimg*k).astype(np.uint8)
            if dov is not None:
                ov=dov if wd>=1 else cv2.addWeighted(dov,wd,base_ov(),1-wd,0)
                if wd<.5:dsurf=None
        if im is None:im=base_im()
        from .image_context import draw as draw_context
        draw_context(self,im,cam,width)
        q=getattr(self.s,'video_quality','padrao')
        if q!='padrao' and getattr(self,'_matte',None) is None and self.s.imagery!='neutral':im=sharpen_imagery(im,q)
        if ov is None:ov=base_ov()
        y0=int(157*self.scale)+1;y1=self.H-int(154*self.scale);view=im[y0:y1];ov=ov[y0:y1];alpha=ov[:,:,3].astype(np.float32)/255
        opacity=getattr(self,'reveal_opacity',1.);alpha*=opacity
        if progress<1:
            st=cv2.warpAffine(self.stations,mat,(self.W,self.H),flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP,borderValue=65535);st=st[y0:y1];ahead=(st.astype(float)/65534-progress)*self.length;alpha*=np.clip(1-ahead/20,0,1);alpha[st==65535]=0
        pc=float(getattr(self.s,'project_contrast',0) or 0)
        if pc>0 and getattr(self,'_matte',None) is None:
            # 1.21: contraste projeto × imagem: a imagem aérea fica mais escura e menos saturada; o projeto, por cima, não.
            g=view.astype(np.float32);gray=g.mean(2,keepdims=True)
            view[:]=np.clip((g*(1-.65*pc)+gray*.65*pc)*(1-.5*pc),0,255).astype(np.uint8)
        view[:]=(view*(1-alpha[:,:,None])+ov[:,:,:3]*alpha[:,:,None]).astype(np.uint8)
        if self.enhanced:
            self._revealed=np.zeros((self.H,self.W),np.uint8);self._revealed[y0:y1]=alpha>.02
        if self.enhanced and getattr(self,'_matte',None) is None:
            # Tela -> mundo (metros), para texturas ancoradas no terreno.
            A=np.array([[self.px,0,self.box[0]],[0,-self.px,self.box[3]]])@np.vstack([mat.astype(np.float64),[0,0,1]])
            Av=A.copy();Av[:,2]+=A[:,1]*y0
            surf=(dsurf if dsurf is not None else cv2.warpAffine(self.surface,mat,(self.W,self.H),flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP))[y0:y1]
            self._via=(y0,surf,alpha>.5)   # 1.36: pista na tela (pista molhada na chuva)
            # 1.21: no vídeo técnico as hachuras ficam limpas (sem texturas por cima), salvo pedido em contrário.
            if not(getattr(self.s,'style_profile','padrao')=='tecnico' and not getattr(self.s,'technical_textures',False)):
                if not hasattr(self,'tex_lut'):self.tex_lut=visual.texture_lut(getattr(self.s,'texture_params',None),[(e['tex_code'],e['tex_base'],e['tex_p']) for e in {e['tex_code']:e for e in self.items if e.get('tex_code')}.values()]+[(c,b,p) for c,b,p,_ in self.texture_areas()])
                visual.shade_surface(view,surf,Av,m,alpha>.5,self.s.median_grass,lut=self.tex_lut,arte=getattr(self.s,'texture_style','')=='artistico')
                ts=getattr(self.s,'texture_style','anterior')
                if ts in ('realistic','artistico'):visual.shade_realistic(view,surf,Av,m,alpha>.5,lut=self.tex_lut)
                if ts=='artistico':visual.shade_artistic(view,surf,Av,m,alpha>.5,lut=self.tex_lut)   # 1.34
            if self.water_mask is not None:
                wm=cv2.warpAffine(self.water_mask,mat,(self.W,self.H),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP)[y0:y1]
                visual.water_ripple(view,wm,Av,getattr(self,'_t',0.))
        if not self.has_surface:
            end=max(2,int(np.searchsorted(self.ds,progress*self.length)))
            coords=self.screen(self.axis[:end],cam,width).astype(np.int32)
            if len(coords)>1:cv2.polylines(im,[coords],False,(120,218,230),max(2,round(4*self.scale)),cv2.LINE_AA)
        before_vectors=im.copy() if opacity<1 else None
        if self.enhanced:self.draw_enhanced_structures(im,cam,width,progress)
        else:self.draw_oae_marks(im,cam,width,progress)
        sp=getattr(self.s,'signage_paint',None);wear=sp is not None and (sp.wear>0 or sp.opacity<1) and width<3000
        pre=im.copy() if wear else None
        # Draw vector lane paint to preserve detail at close range.
        if width<3000 and len(self.markings):
            
            if not hasattr(self,'marking_centers'):self.marking_centers=self.markings.mean(1)
            centers=self.marking_centers;near=np.linalg.norm(centers-cam,axis=1)<width*.75;segments=self.markings[near]
            if len(segments):
                coords=self.screen(segments.reshape(-1,2),cam,width).reshape(-1,2,2)
                if not hasattr(self,'marking_chains'):self.marking_chains=self.ch[self.tree.query(self.marking_centers)[1]]
                for seg,ch,color in zip(coords,self.marking_chains[near],self.marking_colors[near]):
                    if ch<=progress*self.length:cv2.line(im,tuple(seg[0].astype(int)),tuple(seg[1].astype(int)),tuple(map(int,color)),max(1,round(.13/m)),cv2.LINE_AA)
        if wear:im=self.paint_wear(im,pre,mat,m,sp);pre=None
        if width>3000:
            for pts in self.domain:
                q=self.screen(pts,cam,width).astype(np.int32);cv2.polylines(im,[q],False,(30,27,20),max(2,round(4*self.scale)),cv2.LINE_AA);cv2.polylines(im,[q],False,(255,214,107),max(1,round(2*self.scale)),cv2.LINE_AA)
        elif len(self.domain_dashes):
            
            if not hasattr(self,'domain_centers'):self.domain_centers=self.domain_dashes.mean(1)
            centers=self.domain_centers;near=np.linalg.norm(centers-cam,axis=1)<width*.75;segments=self.domain_dashes[near]
            if len(segments):
                coords=self.screen(segments.reshape(-1,2),cam,width).reshape(-1,2,2).astype(np.int32)
                cv2.polylines(im,coords,False,(30,27,20),max(3,round(6*self.scale)),cv2.LINE_AA);cv2.polylines(im,coords,False,(255,214,107),max(1,round(3*self.scale)),cv2.LINE_AA)
        if width<3000 and getattr(self,'paint_items',None):
            from .signage import draw_paint
            pre=im.copy() if wear else None
            draw_paint(im,self.paint_items,self.paint_centers,self.paint_chains,lambda p:self.screen(p,cam,width),cam,width,progress*self.length,m)
            if wear:im=self.paint_wear(im,pre,mat,m,sp)
        if width<1700 and not self.network.full:
            for pt,tan in self.network.arrows:
                if np.linalg.norm(pt-cam)>width*.7:continue
                if self.ch[self.tree.query(pt)[1]]>progress*self.length:continue
                normal=np.array([-tan[1],tan[0]])
                pts=np.array([pt-tan*2.4,pt+tan*2.4,pt+tan*.6+normal*.9,pt+tan*2.4,pt+tan*.6-normal*.9])
                if not contains_xy(self.allowed,pts[:,0],pts[:,1]).all():continue
                cv2.polylines(im,[self.screen(pts,cam,width).astype(np.int32)],False,(242,239,220),max(1,round(.16/m)),cv2.LINE_AA)
        if before_vectors is not None:im=cv2.addWeighted(im,opacity,before_vectors,1-opacity,0)
        return im
    def paint_wear(self,im,pre,mat,m,sp):
        """1.29: tinta gasta/transparente: mistura a pintura com o que havia antes, com manchas fixas no terreno."""
        diff=np.any(im!=pre,axis=2)
        if not diff.any():return im
        ys,xs=np.nonzero(diff);y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
        A=np.array([[self.px,0,self.box[0]],[0,-self.px,self.box[3]]])@np.vstack([mat.astype(np.float64),[0,0,1]])
        A=A.copy();A[:,2]+=A[:,0]*x0+A[:,1]*y0
        k=6;small=(max(1,(y1-y0)//k),max(1,(x1-x0)//k));As=A.copy();As[:,:2]*=k
        n=visual.asphalt().sample(As*np.array([[.12],[.12]]),small,m*k*.12)
        n=cv2.resize(n,(x1-x0,y1-y0),interpolation=cv2.INTER_LINEAR)
        fine=visual.asphalt().sample(A,(y1-y0,x1-x0),m)
        w=np.clip(.5+.35*n+.25*fine,0,1)            # manchas grandes + grão fino
        a=float(sp.opacity)*np.clip(1-float(sp.wear)*(.35+1.1*w),0,1)
        roi=im[y0:y1,x0:x1].astype(np.float32);base=pre[y0:y1,x0:x1].astype(np.float32);sel=diff[y0:y1,x0:x1]
        out=roi.copy();out[sel]=base[sel]+(roi[sel]-base[sel])*a[sel][:,None]
        im[y0:y1,x0:x1]=np.clip(out,0,255).astype(np.uint8);return im
    def draw_enhanced_structures(self,im,cam,width,progress):
        m=width/self.W;scr=lambda p:self.screen(p,cam,width);half=width*.75
        lo=cam-half;hi=cam+half
        if width<1500 and len(self.edges):
            near=(self.edge_boxes[:,2]>lo[0])&(self.edge_boxes[:,0]<hi[0])&(self.edge_boxes[:,3]>lo[1])&(self.edge_boxes[:,1]<hi[1])
            if near.any():
                layer=im.copy()
                for k in np.flatnonzero(near):
                    cv2.polylines(layer,[scr(self.edges[k][0]).astype(np.int32)],False,(52,56,57),max(1,round(.12/m)),cv2.LINE_AA)
                # Bordas só onde o pavimento já foi revelado pela construção progressiva.
                cv2.copyTo(layer,cv2.dilate(self._revealed,np.ones((5,5),np.uint8)),im)
        for o in self.oae_detail:
            b=o['bbox']
            if o['chain_max']>progress*self.length+20 or b[2]<lo[0] or b[0]>hi[0] or b[3]<lo[1] or b[1]>hi[1]:continue
            visual.cast_shadow(im,o['ring'],o['level'],scr,dir=self.sombra_oae)
            if o.get('mark'):
                q=scr(o['ring']).astype(np.int32);cv2.fillPoly(im,[q],(196,198,192),cv2.LINE_AA);cv2.polylines(im,[q],True,(92,96,94),max(1,round(.35/m)),cv2.LINE_AA)
                x0,y0=q.min(0);x1,y1=q.max(0);H,W=im.shape[:2];x0=max(0,x0);y0=max(0,y0);x1=min(W,x1+1);y1=min(H,y1+1)
                if x1>x0 and y1>y0:
                    sel=np.zeros((y1-y0,x1-x0),np.uint8);cv2.fillPoly(sel,[q-[x0,y0]],1)
                    s2w=np.array([[m*self.right[0],-m*self.up[0],0],[m*self.right[1],-m*self.up[1],0]],float)
                    c0=cam-self.right*m*(self.W/2-x0)+self.up*m*(self.H/2-y0);s2w[:,2]=c0
                    c=visual.concrete().sample(s2w,sel.shape,m);roi=im[y0:y1,x0:x1];f=sel>0
                    roi[f]=np.clip(roi[f].astype(np.float32)*(1+.06*c[f])[:,None],0,255).astype(np.uint8)
            visual.oae_details(im,o['joints'],o['rails'],scr,m)
        for o in self.oae:
            if o['chain'][1]>progress*self.length+20:continue
            if o.get('polygon'):rails=[np.asarray(r) for r in o.get('rails',[])]
            else:
                line=o['line'];t=np.gradient(line,axis=0);t/=np.maximum(np.linalg.norm(t,axis=1)[:,None],1e-9);n=np.column_stack([-t[:,1],t[:,0]])
                rails=[line+n*side*(o['width_m']/2-.3) for side in (-1,1)]
            visual.oae_details(im,[],rails,scr,m)
    def draw_oae_marks(self,im,cam,width,progress):
        # OAE marcada por dois pontos: tabuleiro próprio sobre o eixo, guarda-corpos e sombra pelo nível.
        if not self.oae:return
        m=width/self.W
        for o in self.oae:
            if o['chain'][0]>progress*self.length:continue
            c=o['mid'];r=np.linalg.norm(o['line']-c,axis=1).max()+o['width_m']
            if np.linalg.norm(c-cam)>width*.75+r:continue
            deck=o['deck'];geoms=list(deck.geoms) if hasattr(deck,'geoms') else [deck]
            shift=np.array([.35,-.55])*max(0.,o['level_m'])
            for g in geoms:
                ring=np.asarray(g.exterior.coords)
                if o['level_m']>0:
                    sh=im.copy();cv2.fillPoly(sh,[self.screen(ring+shift,cam,width).astype(np.int32)],(18,22,20),cv2.LINE_AA);cv2.addWeighted(sh,.35,im,.65,0,dst=im)
                q=self.screen(ring,cam,width).astype(np.int32)
                cv2.fillPoly(im,[q],(196,198,192),cv2.LINE_AA);cv2.polylines(im,[q],True,(92,96,94),max(1,round(.35/m)),cv2.LINE_AA)
            if o.get('polygon'):rails=[np.asarray(r) for r in o.get('rails',[])]
            else:
                line=o['line'];t=np.gradient(line,axis=0);t/=np.maximum(np.linalg.norm(t,axis=1)[:,None],1e-9);n=np.column_stack([-t[:,1],t[:,0]])
                rails=[line+n*side*(o['width_m']/2-.3) for side in (-1,1)]
            for rail in rails:
                cv2.polylines(im,[self.screen(rail,cam,width).astype(np.int32)],False,(238,236,226),max(1,round(.45/m)),cv2.LINE_AA)
    def apply_night(self,im,cam,width,progress):
        """1.13: escurece a cena, realça a sinalização (retrorrefletiva) e acende faróis e lanternas."""
        n=self._night;k=n*self.s.night_darkness;m=width/self.W;scr=lambda p:self.screen(p,cam,width)
        y0=int(157*self.scale)+1;y1=self.H-int(154*self.scale);view=im[y0:y1]
        f=view.astype(np.float32);visual.darken(f,k)
        glow=np.zeros((self.H,self.W,3),np.uint8)
        if self.s.night_signage_glow and width<3000:
            if len(self.markings):
                centers=self.marking_centers if hasattr(self,'marking_centers') else self.markings.mean(1)
                near=np.linalg.norm(centers-cam,axis=1)<width*.75
                if not hasattr(self,'marking_chains'):self.marking_chains=self.ch[self.tree.query(self.markings.mean(1))[1]]
                segs=self.markings[near&(self.marking_chains<=progress*self.length)]
                if len(segs):
                    q=scr(segs.reshape(-1,2)).reshape(-1,2,2).astype(np.int32);w=max(1,round(.15/m))
                    cols=self.marking_colors[near&(self.marking_chains<=progress*self.length)]
                    for col in np.unique(cols,axis=0):
                        sel=np.all(cols==col,axis=1);cv2.polylines(glow,list(q[sel]),False,tuple(int(v) for v in col),w,cv2.LINE_AA)
            if getattr(self,'paint_items',None):
                from .signage import draw_paint
                draw_paint(glow,self.paint_items,self.paint_centers,self.paint_chains,scr,cam,width,progress*self.length,m)
            if width<1700 and not self.network.full:
                for pt,tan in self.network.arrows:
                    if np.linalg.norm(pt-cam)>width*.7 or self.ch[self.tree.query(pt)[1]]>progress*self.length:continue
                    nn=np.array([-tan[1],tan[0]]);pts=np.array([pt-tan*2.4,pt+tan*2.4,pt+tan*.6+nn*.9,pt+tan*2.4,pt+tan*.6-nn*.9])
                    cv2.polylines(glow,[scr(pts).astype(np.int32)],False,(242,239,220),max(1,round(.16/m)),cv2.LINE_AA)
            g=glow[y0:y1].astype(np.float32);halo=cv2.GaussianBlur(g,(0,0),max(1.5,.6/m))
            f=np.maximum(f,g*(.55+.4*n))+halo*(.55*n)
        # Faróis (feixe aditivo), lâmpadas e lanternas traseiras.
        items=getattr(self,'_night_items',[])
        if items:
            beams=np.zeros((self.H,self.W,3),np.uint8);lamps=[];tails=np.zeros_like(beams)
            for pt,tan,vt,c in items:
                lamps+=visual.headlight_beam(beams,pt,tan,vt,scr);visual.tail_lights(tails,pt,tan,vt,scr,max(1,round(.28/m)))
            b=cv2.GaussianBlur(beams,(0,0),max(1.,.8/m))[y0:y1].astype(np.float32);f+=b*(.28+.5*n)
            tl=tails[y0:y1].astype(np.float32);f=np.maximum(f,tl*min(1.,.4+n))+cv2.GaussianBlur(tl,(0,0),max(1.,.5/m))*(.6*n)
            lay=np.zeros((self.H,self.W,3),np.uint8)
            for p in lamps:
                x,yy=scr(p[None])[0].astype(int);cv2.circle(lay,(x,yy),max(1,round(.3/m)),(255,250,226),-1,cv2.LINE_AA)
            ly=lay[y0:y1].astype(np.float32);f=np.maximum(f,ly)+cv2.GaussianBlur(ly,(0,0),max(1.,.6/m))*.8*n
        view[:]=np.clip(f,0,255).astype(np.uint8)
    def draw_blocks(self,im,t,cam,width):
        """1.12: interdições de faixa: área zebrada laranja/branca, cones na borda e nome (só no período ativo)."""
        m=width/self.W;scr=lambda p:self.screen(p,cam,width)
        for b in self.s.lane_blocks:
            if not b.show or len(b.points)<3:continue
            if not(b.start_s<=t<(b.end_s if b.end_s is not None else 1e9)):continue
            ring=np.array([[p.x,p.y] for p in b.points]);q=scr(ring)
            if q[:,0].max()<0 or q[:,0].min()>self.W or q[:,1].max()<0 or q[:,1].min()>self.H:continue
            qi=q.astype(np.int32);x0,y0=np.maximum(qi.min(0)-2,0);x1,y1=np.minimum(qi.max(0)+3,[self.W,self.H])
            if x1<=x0 or y1<=y0:continue
            mask=np.zeros((y1-y0,x1-x0),np.uint8);cv2.fillPoly(mask,[qi-[x0,y0]],255,cv2.LINE_AA)
            yy,xx=np.mgrid[y0:y1,x0:x1];stripe=((xx+yy)//max(3,int(1.2/m)))%2==0
            col=np.where(stripe[:,:,None],np.array([236,112,28],np.float32),np.array([244,240,232],np.float32))
            a=(mask.astype(np.float32)/255*(.55 if b.mode=='total' else .38))[:,:,None];roi=im[y0:y1,x0:x1]
            roi[:]=(roi*(1-a)+col*a).astype(np.uint8)
            cv2.polylines(im,[qi],True,(236,112,28),max(1,round(.25/m)),cv2.LINE_AA)
            ln=LineString(np.vstack([ring,ring[:1]]))
            for d in np.arange(0,ln.length,max(3.,6*m)):
                c=scr(np.array([ln.interpolate(d).coords[0]]))[0].astype(int);r=max(2,round(.35/m))
                cv2.circle(im,tuple(c),r+1,(40,30,20),-1,cv2.LINE_AA);cv2.circle(im,tuple(c),r,(240,104,24),-1,cv2.LINE_AA);cv2.circle(im,tuple(c),max(1,r//2),(250,250,245),-1,cv2.LINE_AA)
            if width<1500:
                label=('Interdição total' if b.mode=='total' else 'Interdição parcial')+(': '+b.name if b.name and b.name!='Interdição' else '')
                cx,cy=q.mean(0);f=font(15*self.scale*2,True)
                img=Image.fromarray(im);dr=ImageDraw.Draw(img);w=dr.textlength(label,font=f)
                dr.rounded_rectangle((cx-w/2-8,cy-14*self.scale*2-6,cx+w/2+8,cy+6),radius=6,fill=(236,112,28));dr.text((cx-w/2,cy-14*self.scale*2-4),label,font=f,fill=(255,255,255))
                im[:]=np.array(img)

    def traffic(self,status=lambda *a:None):
        """1.12: simulação sem colisões (calculada uma vez); 'anterior' mantém o movimento da 1.11."""
        controls=any(r.enabled for r in getattr(self.s,'railways',[])) or any(s.enabled for s in getattr(self.s,'traffic_signals',[]))
        if not self.s.traffic or (getattr(self.s,'traffic_model','simulado')!='simulado' and not controls):return None
        if getattr(self,'_sim',None) is None:
            from .simulation import TrafficSim
            mix=getattr(self.s,'vehicle_mix','classico')   # 1.37: frota variada
            import functools
            self._sim=TrafficSim(self.network,self.s,functools.partial(visual.vehicle_type,mix=mix),self.s.duration_s,status)
            self.report['traffic_simulation']=self._sim.report()
        return self._sim
    def traffic_iter(self,t):
        sim=self.traffic()
        if sim is None:
            import functools
            return self.network.vehicles_ex(t,self.s.traffic_speed_kmh/3.6,functools.partial(visual.vehicle_type,mix=getattr(self.s,'vehicle_mix','classico')))
        return sim.vehicles_ex(t)
    def fits(self,i,j,pt,tan,vtype):
        key=(i,j,vtype)
        if key not in self._fit:
            T=visual.TYPES[vtype];self._fit[key]=self.allowed.covers(Polygon(visual.body(pt,tan,T['L']+.1,T['B']+.05)))
        return self._fit[key]
    def draw_vehicles(self,im,t,cam,width,progress):
        m=width/self.W;scr=lambda p:self.screen(p,cam,width);items=[]
        for pt,tan,k,identity,j in self.traffic_iter(t):
            ch=self.ch[self.tree.query(pt)[1]]
            if ch>progress*self.length:continue
            q=scr(pt[None])[0]
            if not(5<q[0]<self.W-5 and self.H*.12<q[1]<self.H*.88):continue
            i=identity[0];vt=visual.vehicle_type(self.network.paths[i]['kinds'],identity,getattr(self.s,'vehicle_mix','classico'))
            if not self.fits(i,j,pt,tan,vt):continue
            items.append((pt,tan,vt,visual.vehicle_color(identity,vt)))
        if not items:return
        shadow=np.zeros(im.shape[:2],np.uint8)
        for pt,tan,vt,c in items:
            T=visual.TYPES[vt];cv2.fillPoly(shadow,[scr(visual.body(pt+self.sombra_veiculo*T['H'],tan,T['L']*1.02,T['B']*1.05)).astype(np.int32)],255,cv2.LINE_AA)
        shadow=cv2.GaussianBlur(shadow,(0,0),max(.6,.25/m));f=(1-.42*shadow.astype(np.float32)/255)[:,:,None];im[:]=(im*f).astype(np.uint8)
        if getattr(self,'_night',0)>0:
            # À noite os faróis entram depois do escurecimento (apply_night).
            for pt,tan,vt,c in items:visual.draw_vehicle(im,pt,tan,vt,c,scr,m,shadow_layer=np.zeros((1,1),np.uint8))
            self._night_items=items;return
        beams=np.zeros_like(im) if self.s.headlights else None;lamps=[]
        for pt,tan,vt,c in items:
            visual.draw_vehicle(im,pt,tan,vt,c,scr,m,shadow_layer=np.zeros((1,1),np.uint8))
            if beams is not None:lamps+=visual.headlight_beam(beams,pt,tan,vt,scr)
        if beams is not None:
            beams=cv2.GaussianBlur(beams,(0,0),max(1.,.8/m));cv2.add(im,(beams.astype(np.float32)*.28).astype(np.uint8),dst=im)
            for p in lamps:
                x,y=scr(p[None])[0].astype(int);cv2.circle(im,(x,y),max(1,round(.3/m)),(255,250,226),-1,cv2.LINE_AA)
    def chrome(self,im,title,sub,legend):
        # Cabeçalho (identificação fixa e legenda) e rodapé mínimo.
        sc=self.scale;header=int(157*sc);footer=int(154*sc)
        key=(title,sub,legend)
        if key not in self.headers:
            image=Image.new('RGB',(self.W,header+1),'#081623');dr=ImageDraw.Draw(image)
            tx,ft=fit(dr,f'{self.s.name} | km {km(self.s.km_start_m)} → km {km(self.s.km_end_m)}',38*sc,self.W*.56,True);dr.text((58*sc,25*sc),tx,font=ft,fill='white')
            tx,ft=fit(dr,f'{self.s.origin} → {self.s.destination} • Faixa de domínio em amarelo',22*sc,self.W*.56);dr.text((58*sc,86*sc),tx,font=ft,fill='#c1d5df')
            labels={'existing_pavement':'Existente'+(' (rígido)' if 'existing_pavement' in (getattr(self,'_rigid_roles',None) or ()) else ''),'pavement':'Projetado'+(' (rígido)' if 'pavement' in (getattr(self,'_rigid_roles',None) or ()) else ''),'median':'Canteiro','barrier':'Barreira','oae':'OAE','cut':'Corte','fill':'Aterro','domain':'Domínio','water':'Água'}
            lx=58*sc
            for role in legend:
                color='#2a80b9' if role=='water' else self.color(role)
                dr.rectangle((lx,118*sc,lx+14*sc,128*sc),fill=color)
                text=labels[role];ft=font(13*sc);dr.text((lx+20*sc,114*sc),text,font=ft,fill='#d6e0e3')
                lx+=dr.textlength(text,font=ft)+38*sc
            tx,ft=fit(dr,'Imagem: '+self.attribution,10*sc,self.W*.56);dr.text((58*sc,140*sc),tx,font=ft,fill='#9cb3bf')
            for yy,text,size,color in [(31,title,27,'#86dce9'),(85,sub,22,'#c3d6df')]:
                tx,ft=fit(dr,text,size*sc,960*sc,yy==31);dr.text((1530*sc,yy*sc),tx,font=ft,fill=color)
            if len(self.headers)>128:self.headers.clear()
            self.headers[key]=np.array(image)
        if not hasattr(self,'_footer'):
            image=Image.new('RGB',(self.W,footer),'#081623');dr=ImageDraw.Draw(image)
            fields=[('KM INICIAL',km(self.s.km_start_m)),('KM FINAL',km(self.s.km_end_m)),('EXTENSÃO',f'{self.s.reference_length_m/1000:.3f}'.replace('.',',')+' km'),('OBRA',self.s.work_year)]
            for x,(label,value) in zip([58,690,1320,1950],fields):
                dr.text((x*sc,24*sc),label,font=font(19*sc),fill='#b4cbd6');tx,ft=fit(dr,value,32*sc,560*sc,True);dr.text((x*sc,65*sc),tx,font=ft,fill='white')
            self._footer=np.array(image)
        im[:header+1]=self.headers[key];im[self.H-footer:]=self._footer
    def draw_progress(self,im,progress):
        """1.20: indicador discreto do avanço da revelação (percentual = fração revelada do segmento)."""
        sc=self.scale;y=self.H-int(30*sc);x0=int(58*sc);x1=self.W-int(58*sc);h=max(2,round(5*sc))
        cv2.rectangle(im,(x0,y),(x1,y+h),(38,58,72),-1)
        xe=x0+int((x1-x0)*float(np.clip(progress,0,1)))
        if xe>x0:cv2.rectangle(im,(x0,y),(xe,y+h),(214,184,104),-1)
        txt=f'Revelação do projeto {int(round(100*float(np.clip(progress,0,1))))}%';fs=max(.42,.85*sc)
        (tw,th),_=cv2.getTextSize(txt,cv2.FONT_HERSHEY_SIMPLEX,fs,1);cv2.putText(im,txt,(x1-tw,y-int(8*sc)),cv2.FONT_HERSHEY_SIMPLEX,fs,(200,215,222),1,cv2.LINE_AA)
    BIG=('map','overlay','stations','surface','water_mask')
    def snapshot(self,folder):
        """Grava a cena pronta para processos auxiliares (matrizes grandes em .npy mapeadas na memória)."""
        import pickle
        folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);state=dict(self.__dict__)
        for k in self.BIG:
            v=state.pop(k,None)
            if v is not None:np.save(folder/(k+'.npy'),np.ascontiguousarray(v),allow_pickle=False);state['_npy_'+k]=True
        for k in ('static','headers'):state[k]={}
        for k in [k for k in state if k.startswith('_shade') or k in ('_footer','_revealed')]:state.pop(k,None)
        with open(folder/'scene.pkl','wb') as f:pickle.dump(state,f,protocol=5)
    @classmethod
    def load_snapshot(cls,folder,settings=None):
        import pickle
        folder=Path(folder);obj=cls.__new__(cls)
        with open(folder/'scene.pkl','rb') as f:state=pickle.load(f)
        for k in cls.BIG:
            if state.pop('_npy_'+k,False):state[k]=np.load(folder/(k+'.npy'),mmap_mode='r',allow_pickle=False)
            else:state.setdefault(k,None)
        obj.__dict__.update(state)
        if settings is not None:obj.s=settings
        if getattr(obj,'detail',None) is not None:obj.detail.sc=obj
        if getattr(obj,'detail_fine',None) is not None:obj.detail_fine.sc=obj
        return obj
    def update_callout(self,t,poi):
        if poi is not None and (self.shown_poi is None or t-self.poi_since>=2.5):
            if poi!=self.shown_poi:self.shown_poi=poi;self.poi_since=t
        elif poi is None and t-self.poi_since>=2.5:self.shown_poi=None
        return self.shown_poi
    def advance_state(self,t):
        # Mantém a chamada do cabeçalho coerente sem desenhar o quadro (sequência PNG parcial).
        self.update_callout(t,self.pose(t)[3])
    def layer_rgba(self,t):
        # Camadas do projeto sobre fundo transparente: composição sobre preto e branco recupera alfa e cor.
        out=[]
        for v in (0,255):
            self._matte=v
            try:im,_=self.frame(t)
            finally:self._matte=None
            out.append(im.astype(np.float32))
        black,white=out;alpha=np.clip(1-(white-black).max(2)/255,0,1)
        color=np.where(alpha[:,:,None]>1e-3,black/np.maximum(alpha[:,:,None],1e-3),0)
        return np.dstack([np.clip(color,0,255),alpha*255]).round().astype(np.uint8)
    def frame(self,t,overview=False,view=None):
        self.reveal_opacity=1.
        if self.s.duration_s<45 and self.s.short_video_mode=='auto' and not overview and view is None:
            f=float(np.clip(t/max(1,min(8,self.s.duration_s*.55)),0,1));self.reveal_opacity=f*f*(3-2*f)
        self._t=t;self._night=visual.night_factor(self.s,t);self._night_items=[]
        cam,width,progress,poi,scene=self.pose(t)
        if overview:cam=self.center;width=self.overview;progress=1;poi=None;scene='preview'
        if view is not None:cam=np.asarray(view[0],float);width=float(view[1]);progress=1;poi=None;scene='preview'
        key=scene if scene.startswith('detalhe') and getattr(self,'_matte',None) is None else None
        if key and key in self.static:im=self.static[key].copy()
        else:
            im=self.draw_base(cam,width,progress)
            if key and getattr(self.s,'weather','limpo')=='chuva':self._via_static=getattr(self,'_via',None)
            if key:self.static[key]=im.copy()
        ad=ambiente.antes_depois(self,t) if getattr(self,'_matte',None) is None else None   # 1.36: antes/depois
        if ad is not None:
            antes=self.draw_base(cam,width,-1.);x=int(round(ad*self.W));im[:,x:]=antes[:,x:]
        if getattr(self.s,'lane_blocks',None) and width<3000:self.draw_blocks(im,t,cam,width)
        from . import transport_render
        from .engineering_assets import draw_map as draw_engineering_assets
        draw_engineering_assets(self,im,cam,width)
        transport_render.draw_static(self,im,cam,width)
        if self.s.traffic and width<3000 and self.reveal_opacity>.9 and self.enhanced:self.draw_vehicles(im,t,cam,width,progress)
        elif self.s.traffic and width<3000 and self.reveal_opacity>.9:
            for pt,tan,k,identity in ((a,b,c,d) for a,b,c,d,_ in self.traffic_iter(t)):
                ch=self.ch[self.tree.query(pt)[1]]
                if ch>progress*self.length:continue
                normal=np.array([-tan[1],tan[0]]);q=self.screen(pt[None],cam,width)[0]
                if not(5<q[0]<self.W-5 and self.H*.12<q[1]<self.H*.88):continue
                body=np.array([pt+tan*x+normal*y for x,y in [(-2.3,-.93),(2.3,-.93),(2.3,.93),(-2.3,.93)]])
                if not self.allowed.covers(Polygon(body)):continue
                xy=self.screen(body,cam,width).astype(np.int32)
                lt=cv2.LINE_AA if getattr(self.s,'video_quality','padrao')!='padrao' else cv2.LINE_8   # 1.32: sem serrilhado
                cv2.fillPoly(im,[xy+[2,2]],(22,25,22),lt);cv2.fillPoly(im,[xy],[(241,238,226),(232,192,115),(132,183,205),(208,129,117)][k%4],lt)
                glass=np.array([pt+tan*x+normal*y for x,y in [(.3,-.7),(1.3,-.7),(1.3,.7),(.3,.7)]])
                cv2.fillPoly(im,[self.screen(glass,cam,width).astype(np.int32)],(52,76,89),lt)
        if getattr(self,'_matte',None) is None:   # 1.37: vegetação e pedestres
            hv,fv=int(157*self.scale),int(154*self.scale)
            if getattr(self.s,'vegetation_points',None) or getattr(self.s,'vegetation_areas',None):vida.draw_vegetation(self,im,cam,width,progress,hv,fv)
            if getattr(self.s,'pedestrians',False):vida.draw_pedestrians(self,im,t,cam,width,progress,hv,fv)
        if self._night>0 and getattr(self,'_matte',None) is None:self.apply_night(im,cam,width,progress)
        from .traffic_indicators import draw as draw_indicators
        draw_indicators(self,im,t,cam,width)
        transport_render.draw_dynamic(self,im,t,cam,width)
        if getattr(self.s,'weather','limpo')!='limpo' and getattr(self,'_matte',None) is None:   # 1.36: clima
            v=getattr(self,'_via',None) if not (key and key in self.static) else getattr(self,'_via_static',None);via=None
            if v is not None:via=np.zeros((self.H,self.W),bool);y0v,sv,av=v;via[y0v:y0v+sv.shape[0]]=(sv>0)&(sv!=6)&(sv!=7)&av
            ambiente.clima(self,im,t,int(157*self.scale),int(154*self.scale),via)
        if getattr(self.network,'signs',None) and getattr(self,'_matte',None) is None:
            from .signage import draw_signs
            draw_signs(im,self,cam,width,progress,int(157*self.scale),self.H-int(154*self.scale))
        if self.s.water_names:im=self.hydro.draw_labels(im,lambda points:self.screen(points,cam,width),font,self.scale,self.s.water_names_opacity)
        if overview and self.s.traffic_network_preview:
            for path in self.network.paths:
                cv2.polylines(im,[self.screen(path['p'],cam,width).astype(np.int32)],False,(72,223,200),max(1,round(2*self.scale)),cv2.LINE_AA)
        sched=None
        if obras_video.active(self.s) and getattr(self,'_matte',None) is None:   # 1.35: obras do PER como trecho / linha do tempo
            sched=obras_video.draw(self,im,t,cam,width,progress,int(157*self.scale),int(154*self.scale))
        placed=[];newc=getattr(self.s,'callout_layout','anterior')=='auto'
        if getattr(self,'gantries',None) and width<3000:
            hdr=int(157*self.scale);ftr=self.H-int(154*self.scale);scr=lambda p:self.screen(p,cam,width);mm=width/self.W
            for g in self.gantries:
                if g['chain']>progress*self.length+25 or np.linalg.norm(g['xy']-cam)>width:continue
                visual.draw_gantry(im,g,scr,mm,self.scale)
            for g in sorted(self.gantries,key=lambda g:-np.linalg.norm(g['xy']-cam)):
                if not g['callout'] or g['chain']>progress*self.length+25:continue
                f=window_fade(g,t)
                if f<=0:continue
                q=self.screen(g['xy'][None],cam,width)[0]
                if not(0<q[0]<self.W and hdr<q[1]<ftr):continue
                rgb=visual._rgb(g['color']) if g.get('color') else (255,214,107)
                sub=('Pórtico' if g['kind']=='portico' else 'Semipórtico' if g['kind']=='semiportico' else 'Bandeira')+(f' • km {fmt_km(g["km"])}' if g.get('km') is not None else '')
                card=visual.callout_card(('g',g.get('id'),g.get('image')),g['name'],sub,g.get('description',''),rgb,font,self.scale,'cartao',g.get('text_scale',1),g['pic'])
                lab=self.screen(np.array([[g['label']['x'],g['label']['y']]]),cam,width)[0] if g.get('label') else None
                visual.draw_callout(im,q,card,rgb,self.scale,hdr,ftr,placed,lab,'reta',f,marker_kind='diamond')
        # Symbols are tied to structures; one fixed information slot stays in the header.
        if self.highlights and width<3000 and newc:
            hdr=int(157*self.scale);ftr=self.H-int(154*self.scale)
            for h in sorted(self.highlights,key=lambda h:-np.linalg.norm(h['xy']-cam)):
                if h['chain']>progress*self.length+25:continue
                f=window_fade(h,t)
                if f<=0:continue
                q=self.screen(h['xy'][None],cam,width)[0]
                if not(0<q[0]<self.W and hdr<q[1]<ftr):continue
                lab=self.screen(np.array([[h['label']['x'],h['label']['y']]]),cam,width)[0] if h.get('label') else None
                color,letter,cat=visual.HIGHLIGHT_STYLE.get(h['category'],visual.HIGHLIGHT_STYLE['outro']);rgb=visual._rgb(h.get('color') or color)
                km_text=fmt_km(h['km']) if h.get('show_km') and h.get('km') is not None else ''
                card=visual.callout_card(('h',h.get('id'),h.get('image')),h['name'],cat+(f' • km {km_text}' if km_text else ''),h.get('description',''),rgb,font,self.scale,h.get('style','cartao'),h.get('text_scale',1),h.get('pic'))
                visual.draw_callout(im,q,card,rgb,self.scale,hdr,ftr,placed,lab,h.get('leader','reta'),f,letter,font)
        elif self.highlights and width<3000:
            hdr=int(157*self.scale);ftr=self.H-int(154*self.scale)
            for h in sorted(self.highlights,key=lambda h:-np.linalg.norm(h['xy']-cam)):
                if h['chain']>progress*self.length+25:continue
                if h.get('start_s') is not None or h.get('end_s') is not None:
                    h['_fade']=window_fade(h,t)
                    if h['_fade']<=0:continue
                q=self.screen(h['xy'][None],cam,width)[0]
                if not(0<q[0]<self.W and hdr<q[1]<ftr):continue
                lab=self.screen(np.array([[h['label']['x'],h['label']['y']]]),cam,width)[0] if h.get('label') else None
                visual.draw_highlight(im,q,lab,h,font,self.scale,hdr,ftr,fmt_km(h['km']) if h.get('show_km') and h.get('km') is not None else '')
        hdr=int(157*self.scale);ftr=self.H-int(154*self.scale)
        if self.s.cities_show and self.s.cities:annotations.draw_cities(im,self,cam,width,font,hdr,ftr)
        if self.s.km_markers:annotations.draw_km_markers(im,self,cam,width,progress,font,hdr,ftr)
        anchors={}
        for p in self.pois:
            if p.get('no_symbol'):continue
            a=p.get('anchor')
            q=self.screen(np.array([[a['x'],a['y']] if a else [p['x'],p['y']]]),cam,width)[0];ch=p['chain']
            if a:anchors[p.get('id')]=q
            if ch>progress*self.length+25 or not(35<q[0]<self.W-35 and self.H*.18<q[1]<self.H*.82):continue
            if p['kind'] in ('passarela','onibus') and width<3000:
                idx=self.tree.query([p['x'],p['y']])[1]
                tan=self.dense[min(len(self.dense)-1,idx+2)]-self.dense[max(0,idx-2)]
                anchor=draw_structure(im,p,tan,lambda points:self.screen(points,cam,width),self.W/width)
                q=self.screen(anchor[None],cam,width)[0]
            x,y=np.rint(q).astype(int);rad=max(5,round((8 if width>3000 else 22)*self.scale));cv2.circle(im,(x,y),rad,(10,28,43),-1,cv2.LINE_AA);cv2.circle(im,(x,y),rad,(145,219,232),max(1,round(3*self.scale)),cv2.LINE_AA)
            if width<3000:
                digits=''.join(re.findall(r'\d+',p.get('id','')))
                label={'passarela':'P'+digits,'fauna':'PF'+digits,'oae':'OAE','intersecao':'D','via_marginal':'M'+digits,'correcao':'CH','onibus':'BUS'}.get(p['kind'],'I')
                fs=max(.25,.48*self.scale);sz=cv2.getTextSize(label,cv2.FONT_HERSHEY_SIMPLEX,fs,1)[0];cv2.putText(im,label,(x-sz[0]//2,y+sz[1]//2),cv2.FONT_HERSHEY_SIMPLEX,fs,(184,237,243),1,cv2.LINE_AA)
        sc=self.scale;header=int(157*sc);footer=int(154*sc)
        shade=max(1,round(60*sc))
        if not hasattr(self,'_shade_lut'):
            factors=1-.12*(1-np.arange(shade,dtype=float)/shade)**2
            self._shade_lut=(factors[:,None]*np.arange(256)[None,:]).astype(np.uint8)
        index=np.arange(shade)[:,None,None]
        im[header:header+shade]=self._shade_lut[index,im[header:header+shade]]
        lower=im[self.H-footer-shade:self.H-footer]
        lower[:]=self._shade_lut[index[::-1],lower]
        poi=self.update_callout(t,poi)
        title=poi['title'] if poi else ('Início do trecho' if scene=='inicio' else 'Final do trecho' if scene=='fim' else 'Desenvolvimento do traçado')
        if scene=='chave' and getattr(self,'_key_title',''):title=self._key_title
        sub=poi.get('subtitle','') if poi else f'km {km(self.s.km_start_m)} a km {km(self.s.km_end_m)}'
        if poi and poi.get('km_m') is not None:sub=f"km {fmt_km(poi['km_m'])} • {sub}"
        if not hasattr(self,'legend_points'):
            entities=[e for e in self.items if e['role'] in COLORS]
            lo=np.array([e['points'].min(0) for e in entities]);hi=np.array([e['points'].max(0) for e in entities])
            self.legend_points=np.stack([lo,np.column_stack([lo[:,0],hi[:,1]]),hi,np.column_stack([hi[:,0],lo[:,1]])],axis=1) if len(lo) else np.empty((0,4,2))
            self.legend_roles=np.array([e['role'] for e in entities])
            self.legend_chains=self.ch[self.tree.query(np.array([e['points'].mean(0) for e in entities]))[1]] if entities else np.empty(0)
        qs=self.screen(self.legend_points.reshape(-1,2),cam,width).reshape(-1,4,2)
        shown=(self.legend_chains<=progress*self.length+25)&(qs[:,:,0].max(1)>0)&(qs[:,:,0].min(1)<self.W)&(qs[:,:,1].max(1)>header)&(qs[:,:,1].min(1)<self.H-footer)
        visible=set(self.legend_roles[shown])
        water_geoms=([np.array(g.exterior.coords) for g in self.hydro.polygons] or self.hydro.lines) if self.s.water_texture else []
        for points in water_geoms:
            qs=self.screen(points,cam,width)
            if qs[:,0].max()>0 and qs[:,0].min()<self.W and qs[:,1].max()>header and qs[:,1].min()<self.H-footer:
                visible.add('water');break
        legend=tuple(role for role in ['existing_pavement','pavement','median','barrier','oae','cut','fill','domain','water'] if role in visible)
        self.chrome(im,title,sub,legend)
        if getattr(self.s,'progress_indicator',False):self.draw_progress(im,progress)
        if sched:obras_video.date_box(self,im,sched[0],sched[1],header,font)
        if ad is not None:ambiente.divisoria(self,im,ad,header,footer,font)
        if self.s.direction_badge and getattr(self,'_matte',None) is None:annotations.direction_badge(im,self,cam,width,font,header)
        # Linha de chamada só quando o usuário definiu o ponto de ancoragem desta obra.
        if poi is not None and poi.get('id') in anchors:
            x,y=anchors[poi['id']];x0=int(1530*sc)
            if 0<x<self.W and header<y<self.H-footer:
                pts=np.array([[x0,header],[x0,header+int(18*sc)],[x,y]],np.int32)
                cv2.polylines(im,[pts],False,(10,28,43),max(2,round(5*sc)),cv2.LINE_AA);cv2.polylines(im,[pts],False,(134,220,233),max(1,round(2*sc)),cv2.LINE_AA)
        return im,{'camera':cam.tolist(),'width_m':width,'screen_width':self.W,'screen_height':self.H,'right':self.right.tolist(),'up':self.up.tolist()}

def render(directory,s,status=lambda *a:None,cancel=lambda:False):
    directory=Path(directory)
    if not s.coordinates_confirmed:raise ValueError('Confirme as coordenadas e o alinhamento na etapa de configuração.')
    import time
    # 1.32: qualidade máxima: o quadro é montado 1,5× maior e reduzido (superamostragem: bordas, textos e veículos sem serrilhado).
    OW,OH=s.width,s.width*9//16
    ssaa=getattr(s,'video_quality','padrao')=='maxima' and s.width<=2560 and not s.cabin.enabled
    start=time.monotonic();scene=Scene(directory,s.model_copy(update={'width':s.width*3//2}) if ssaa else s,status);prepared=time.monotonic()-start
    s=scene.s.model_copy(update={'width':OW}) if ssaa else scene.s   # 1.27: com avanço por velocidade, a duração é a calculada pela cena
    cabin=None
    if s.cabin.enabled:
        from .cabin import CabinView
        cabin=CabinView(scene)
    out=directory/'video.partial.mp4';ff=ffmpeg_exe()
    if getattr(scene,'detail',None) is not None and s.render_profile!='rapido':
        try:
            poses=[scene.pose(t)[:2] for t in np.arange(0,s.duration_s,.5)]
            got=scene.detail.prefetch(poses,status,cancel=cancel)
            if scene.detail.offline:scene.report['warnings'].append('Imagem detalhada indisponível (sem internet e sem cache): o vídeo usa o mosaico base; texturas do projeto seguem em alta resolução.')
        except Exception as e:scene.report['warnings'].append('Imagem detalhada não pré-carregada: '+str(e)[:120])
    if s.traffic:scene.traffic(status)
    status(.25,'Testando aceleração NVIDIA / NVENC')
    encoding=select_encoder(ff,OW,OH,s.fps,s.encoder,s.cpu_preset,quality=getattr(s,'video_quality','padrao'))
    (directory/'encoder.json').write_text(json.dumps({k:v for k,v in encoding.items() if k!='args'},ensure_ascii=False,indent=2),encoding='utf-8')
    frames=round((cabin.c.duration_s if cabin else s.duration_s)*s.fps)
    from .parallel import plan_workers,Pool
    workers,why=plan_workers(s.render_workers,scene.W,scene.H,frames,encoding['encoder']!='h264_nvenc')
    snap=directory/'render_tmp'
    if workers>1:
        status(.25,f'Preparando {workers} processos de montagem ({why})')
        shutil.rmtree(snap,ignore_errors=True);scene.snapshot(snap)
    def encode_attempt(profile):
        log=open(directory/'ffmpeg.log','ab')
        log.write(('\nEncoder: '+profile['label']+' — '+profile['reason']+'\n').encode('utf-8'));log.flush()
        cmd=[ff,'-y','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{OW}x{OH}','-r',str(s.fps),'-i','-','-an']+profile['args']+['-g','250','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
        enc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=log);run_start=time.monotonic()
        pool=Pool(snap,workers,0,frames-1,'cabin' if cabin else 'aerial',snap) if workers>1 else None
        shape=(scene.H,scene.W,3);nbytes=scene.H*scene.W*3;tag=f' · {workers} processos' if workers>1 else ''
        # Reset callout state if GPU failed and a CPU retry is required.
        scene.shown_poi=None;scene.poi_since=-100
        try:
            previous=None;last_scene=None;fade_from=None;fade_start=0
            for k in range(frames):
                if cancel():raise InterruptedError('Geração cancelada pelo usuário.')
                t=k/s.fps
                if pool is not None:im=pool.frame(k,nbytes,shape)
                elif cabin is not None:im=cabin.frame(t)[0]
                else:im=scene.frame(t)[0]
                if ssaa:im=cv2.resize(im,(OW,OH),interpolation=cv2.INTER_AREA)
                if cabin is None:
                    # Transição de 0,8 s entre cenas de detalhe (feita aqui, na ordem dos quadros).
                    key=scene.pose(t)[4]
                    if last_scene is not None and key!=last_scene and key not in ['tour','inicio','fim']:
                        fade_from=previous;fade_start=t
                    if fade_from is not None and t-fade_start<.8:
                        a=(t-fade_start)/.8;a=a*a*(3-2*a);im=cv2.addWeighted(fade_from,1-a,im,a,0)
                    last_scene=key;previous=im.copy()
                enc.stdin.write(im.tobytes())
                if os.environ.get('RODOVIA_FRAME_LOG'):
                    with open(os.environ['RODOVIA_FRAME_LOG'],'a') as fl:fl.write(f'{k} {hashlib.sha256(im.tobytes()).hexdigest()[:12]}\n')
                if k%max(1,s.fps)==0:
                    elapsed=max(.001,time.monotonic()-run_start);speed=(k+1)/elapsed;remaining=(frames-k-1)/speed
                    status(.25+.74*(k+1)/frames,f"{profile['label']}{tag}{' · cabine' if cabin else ''} · {k+1}/{frames} quadros · {speed:.1f} q/s · falta ~{tempo(remaining)}")
            enc.stdin.close()
            if enc.wait()!=0:raise RuntimeError('FFmpeg falhou. Consulte ffmpeg.log do projeto.')
            if pool is not None and any(pool.close()):raise RuntimeError('Processo auxiliar terminou com erro.')
            pool=None
        except BaseException:
            enc.kill();enc.wait();out.unlink(missing_ok=True)
            if pool is not None:pool.close(kill=True)
            raise
        finally:log.close()
        return frames
    try:
        frames=encode_attempt(encoding)
    except (BrokenPipeError,RuntimeError,OSError) as e:
        if cancel():raise
        if workers>1 and 'auxiliar' in str(e):
            # Falha num processo auxiliar (memória, por exemplo): refaz em um processo só.
            status(.25,'Processo auxiliar falhou; refazendo em um processo.');workers=1
            frames=encode_attempt(encoding)
        elif encoding['encoder']!='h264_nvenc':raise
        else:
            status(.25,'NVENC falhou durante a gravação. Reiniciando pela CPU.')
            encoding=select_encoder(ff,OW,OH,s.fps,'cpu',s.cpu_preset,quality=getattr(s,'video_quality','padrao'))
            encoding['reason']='Retorno automático à CPU após falha de NVENC: '+str(e)
            frames=encode_attempt(encoding)
    finally:shutil.rmtree(snap,ignore_errors=True)
    status(.995,'Conferindo o vídeo gravado (decodificação completa)')
    from .encoding import validate_mp4
    check=validate_mp4(ff,out,frames,OW,OH,s.fps)
    if not check['ok']:
        out.unlink(missing_ok=True);raise RuntimeError('O vídeo gravado não passou na conferência: '+'; '.join(check['problems'])+'. Gere novamente.')
    from .store import replace
    final=directory/'video.mp4';replace(out,final)
    meta={'frames':frames,'fps':s.fps,'duration_s':frames/s.fps,'width':OW,'height':OH,'video_quality':getattr(s,'video_quality','padrao'),'superamostragem':1.5 if ssaa else 1,'codec':'H.264 High','encoder':encoding['encoder'],'encoder_reason':encoding['reason'],'quality':encoding['quality'],'pix_fmt':'yuv420p','geometric_length_m':scene.length,'reference_length_m':s.reference_length_m,'geometry_cache_hit':scene.geometry_cache_hit,'visual_quality':s.visual_quality,'render_profile':s.render_profile,'workers':workers,'workers_reason':why,'camera':'cabin' if cabin else 'aerial','cabin_reaches_path_end':bool(cabin.reaches_end) if cabin else None,'preparation_seconds':round(prepared,3),'total_seconds':round(time.monotonic()-start,3),'validation':check,'motion_audit':scene.report.get('traffic_simulation'),'network_safety':{'rejected_paths':len(getattr(scene.network,'rejected_paths',[])),'rejected_connections':dict(getattr(scene.network,'rejected_connectors',{}))}}
    if getattr(scene,'_sim',None) is not None:meta['motion_audit']['body_samples']=scene._sim.vehicle_body_state(min(s.duration_s/2,1.5))[:10]
    (directory/'video.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    (directory/'encoder.json').write_text(json.dumps({k:v for k,v in encoding.items() if k!='args'},ensure_ascii=False,indent=2),encoding='utf-8')
    status(1,'Vídeo concluído · '+encoding['label']);return final
