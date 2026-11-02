"""Política de apresentação; não modifica geometria, rede ou simulação."""
import numpy as np

ART_COLORS={'pavement':'#30373d','existing_pavement':'#858279','shoulder':'#596168','cut':'#a85642','fill':'#54803e','terrain':'#6f8c55'}

def guides(settings):
    return settings.style_profile=='tecnico' or getattr(settings,'presentation_guides',False)

def strength(settings):
    return .55 if getattr(settings,'realism_profile','ultra_realista')=='realista' else 1.

def repair_reveal_stations(alpha,stations,transform,tree,chains,length):
    """Detalhe pode conter polígonos que não ocuparam um pixel do mosaico base.

    Só recupera pixels realmente desenhados; não cria áreas nem antecipa a obra.
    """
    missing=(stations==65535)&(alpha>0)
    if not missing.any():return stations
    if not np.isfinite(length) or length<=0:raise ValueError('Comprimento inválido para apresentação progressiva.')
    ys,xs=np.nonzero(missing);result=stations.copy()
    # Blocos limitam memória em vistas grandes; o mesmo eixo governa todas as camadas.
    for first in range(0,len(xs),65536):
        x=xs[first:first+65536];y=ys[first:first+65536]
        xy=np.c_[x,y]@np.asarray(transform)[:,:2].T+np.asarray(transform)[:,2]
        s=np.asarray(chains)[tree.query(xy)[1]]
        result[y,x]=np.clip(s/length*65534,0,65534).astype(np.uint16)
    return result


def source_segments(entity):
    """Apenas arestas reais; não exibe o fechamento virtual de uma hachura aberta."""
    points=np.asarray(entity['points'],float)
    if points.ndim!=2 or points.shape[1]!=2 or not np.isfinite(points).all():raise ValueError('Contorno DXF inválido.')
    if len(points)<2:return np.empty((0,2,2))
    if entity.get('closed') and np.linalg.norm(points[0]-points[-1])>1e-6:points=np.vstack([points,points[0]])
    from .dxf_trim import runs
    paths=runs(entity)
    if not paths:return np.empty((0,2,2))
    parts=np.concatenate([np.stack([p[:-1],p[1:]],axis=1) for p in paths]);keep=np.linalg.norm(parts[:,1]-parts[:,0],axis=1)>1e-8
    for virtual in entity.get('virtual') or []:
        chord=np.asarray(virtual,float)
        if chord.shape!=(2,2) or not np.isfinite(chord).all():raise ValueError('Fechamento DXF inválido.')
        v=chord[1]-chord[0];length2=float(v@v)
        if length2<1e-10:continue
        t=(parts-chord[0])@v/length2;projection=chord[0]+t[:,:,None]*v
        on=(np.linalg.norm(parts-projection,axis=2).max(1)<.05)&(t.min(1)>-1e-6)&(t.max(1)<1+1e-6)
        keep &= ~on
    return parts[keep]


def contour_runs(entity):
    segments=source_segments(entity);runs=[]
    for a,b in segments:
        if runs and np.linalg.norm(runs[-1][-1]-a)<1e-6:runs[-1].append(b)
        else:runs.append([a,b])
    return [np.asarray(r) for r in runs]


class DXFAdvance:
    """Janela de desenho adiante da frente de material, usando o mesmo eixo da animação."""
    ROLES={'edge_line','overlay','water','railway','building','vegetation','gas','fiber','electric','pole','tower','radar','sign_h','sign_v','axis','pavement','existing_pavement','shoulder','median','oae','cut','fill','terrain','barrier'}
    def __init__(self,items,tree,chains):
        parts=[source_segments(e) for e in items if e.get('role') in self.ROLES and not e.get('reference_only')]
        self.segments=np.concatenate(parts) if parts else np.empty((0,2,2))
        self.chains=np.asarray(chains)[tree.query(self.segments.reshape(-1,2))[1]].reshape(-1,2) if len(self.segments) else np.empty((0,2))
    def window(self,front,lead):
        if not np.isfinite([front,lead]).all() or lead<0:raise ValueError('Avanço DXF inválido.')
        if lead==0 or not len(self.segments):return np.empty((0,2,2))
        a,b=self.chains.T;delta=b-a
        take=(np.maximum(a,b)>=front)&(np.minimum(a,b)<=front+lead)
        segments=self.segments[take].copy();a=a[take];delta=delta[take]
        moving=np.abs(delta)>1e-8
        lo=np.zeros(len(a));hi=np.ones(len(a))
        u=(front-a[moving])/delta[moving];v=(front+lead-a[moving])/delta[moving]
        lo[moving]=np.clip(np.minimum(u,v),0,1);hi[moving]=np.clip(np.maximum(u,v),0,1)
        start=segments[:,0].copy();vector=segments[:,1]-start
        segments[:,0]=start+vector*lo[:,None];segments[:,1]=start+vector*hi[:,None]
        return segments[np.linalg.norm(segments[:,1]-segments[:,0],axis=1)>1e-8]


def dash_segments(points,dash=6.,gap=4.):
    """Tracejado sobre a polilinha original; não corta curvas/cantos por uma corda."""
    from .dxf_trim import path,at
    if not np.isfinite([dash,gap]).all() or dash<=0 or gap<0:raise ValueError('Tracejado inválido.')
    try:p,ds=path(points)
    except ValueError:return np.empty((0,2,2))
    segments=[]
    for start in np.arange(0,ds[-1],dash+gap):
        end=min(ds[-1],start+dash);inside=p[(ds>start+1e-9)&(ds<end-1e-9)];q=np.vstack([at(p,ds,start),inside,at(p,ds,end)])
        segments.extend(np.stack([q[:-1],q[1:]],axis=1))
    return np.asarray(segments,float).reshape(-1,2,2)


def resample_stroke(points,step=2.):
    """Insere amostras sem remover vértices reais nem ligar entidades independentes."""
    from .dxf_trim import path
    if not np.isfinite(step) or step<=0:raise ValueError('Passo inválido para traço.')
    p,ds=path(points);stations=np.unique(np.r_[ds,np.arange(0,ds[-1],step)])
    return np.column_stack([np.interp(stations,ds,p[:,k]) for k in range(2)])


# Estado de apresentação independente do papel físico (acostamento continua acostamento).
def is_existing(record):
    import re,unicodedata
    if hasattr(record,'model_dump'):record=record.model_dump()
    if not isinstance(record,dict):return False
    state=record.get('presentation_state')
    if state in ('existing','projected'):return state=='existing'
    if record.get('asset_material')=='asphalt_old':return True
    if record.get('role')=='existing_pavement' or record.get('oae_kind')=='existente':return True
    if record.get('oae_kind') in ('nova','alargada'):return False
    text=' '.join(str(record.get(k,'')) for k in ('layer','name','kind'))
    text=''.join(c for c in unicodedata.normalize('NFKD',text.upper()) if not unicodedata.combining(c))
    if re.search(r'PROJ|NOVA?|ALARG',text):return False
    return bool(re.search(r'EXIST|ATUAL|ANTIG',text))


def phase_color(color,existing,settings,role):
    """Existente mais neutro; preserva cores e representações escolhidas manualmente."""
    if not existing or settings.style_profile=='tecnico' or role in settings.role_colors or role in settings.pavement_styles:return color
    c=np.asarray(color,dtype=np.float32);gray=c.mean(axis=-1,keepdims=True)
    return np.clip(c*.76+gray*.24,0,255).astype(np.uint8)


def reveal_mask(scene,cam,width,progress):
    """Campo de distância na vista, compartilhado por TODAS as feições do vídeo.

    No máximo ~33 mil consultas ao eixo por pose; reutilizado nos vários desenhos
    do quadro. Não depende do estado congelado/selecionado de uma camada.
    """
    import cv2
    if not np.isfinite([*cam,width,progress,scene.length]).all() or width<=0 or scene.length<=0:raise ValueError('Vista inválida para revelação do projeto.')
    if progress>=1:return np.ones((scene.H,scene.W),np.float32)
    if progress<0:return np.zeros((scene.H,scene.W),np.float32)
    key=(*np.asarray(cam,float),float(width),scene.W,scene.H)
    if getattr(scene,'_reveal_view_key',None)!=key:
        w=min(scene.W,256);h=min(scene.H,max(2,round(w*scene.H/scene.W)))
        x=np.linspace(0,scene.W-1,w);y=np.linspace(0,scene.H-1,h);X,Y=np.meshgrid(x,y);m=width/scene.W
        points=np.asarray(cam)+(X.ravel()-scene.W/2)[:,None]*m*scene.right-(Y.ravel()-scene.H/2)[:,None]*m*scene.up
        chains=np.asarray(scene.ch)[scene.tree.query(points)[1]].reshape(h,w).astype(np.float32)
        scene._reveal_view_chains=cv2.resize(chains,(scene.W,scene.H),interpolation=cv2.INTER_LINEAR);scene._reveal_view_key=key
    front=progress*scene.length
    return np.clip((front-scene._reveal_view_chains)/20.+1.,0,1).astype(np.float32)


def clip_reveal(scene,image,background,cam,width,progress):
    if progress>=1:return image
    mask=reveal_mask(scene,cam,width,progress)
    # Inteiros no fundo intocado; só a frente suave usa float32. Não aloca float64 HD/4K.
    out=image.copy();out[mask<=0]=background[mask<=0]
    soft=(mask>0)&(mask<1)
    if soft.any():
        a=mask[soft,None];out[soft]=np.clip(background[soft].astype(np.float32)*(1-a)+image[soft]*a,0,255).astype(np.uint8)
    return out


def existing_backdrop(scene,image,cam,width,mat,det=None,weight=0.):
    """Subcamada existente, antes do projeto; nunca recompõe geometria ou simulação."""
    import cv2,copy
    from . import visual
    if getattr(scene.s,'existing_visibility','initial')!='initial':return image.copy()
    out=image.copy();ov=surf=None
    if getattr(scene,'existing_overlay',None) is not None:
        ov=cv2.warpAffine(scene.existing_overlay,mat,(scene.W,scene.H),flags=cv2.INTER_LINEAR|cv2.WARP_INVERSE_MAP)
        surf=cv2.warpAffine(scene.existing_surface,mat,(scene.W,scene.H),flags=cv2.INTER_NEAREST|cv2.WARP_INVERSE_MAP)
    if det is not None and weight>0 and any(is_existing(o['e']) for o in det.paths()):
        if not hasattr(det,'_existing_variant'):
            variant=copy.copy(det);variant.sc=det.sc;variant.lock=det.lock;variant._tr=det._tr;variant._paths=[o for o in det.paths() if is_existing(o['e'])];variant.key=det.key+'-existing';variant.dir=det.dir.parent/variant.key;variant.mem=__import__('collections').OrderedDict();variant.enabled_imagery=False;variant.local=None;variant.esri_ok=False;variant._existing_only=True;det._existing_variant=variant
        _,_,detail,surface=det._existing_variant.compose(cam,width,False,True)
        if detail is not None:
            ov=detail if ov is None or weight>=1 else cv2.addWeighted(detail,weight,ov,1-weight,0)
            if surface is not None and weight>=.5:surf=surface
    if ov is not None:
        alpha=ov[:,:,3:4].astype(np.float32)/255
        out[:]=(out*(1-alpha)+ov[:,:,:3]*alpha).astype(np.uint8)
        if scene.enhanced and getattr(scene,'_matte',None) is None and not(scene.s.style_profile=='tecnico' and not scene.s.technical_textures):
            A=np.array([[scene.px,0,scene.box[0]],[0,-scene.px,scene.box[3]]])@np.vstack([mat.astype(np.float64),[0,0,1]])
            if not hasattr(scene,'_existing_tex_lut'):scene._existing_tex_lut=visual.texture_lut(scene.s.texture_params,[(e['tex_code'],e['tex_base'],e['tex_p']) for e in {e['tex_code']:e for e in scene.items if e.get('tex_code')}.values()]+[(c,b,p) for c,b,p,_ in scene.texture_areas()])
            lut=scene._existing_tex_lut
            mask=alpha[:,:,0]>.5;unshaded=out.copy() if strength(scene.s)<1 else None
            visual.shade_surface(out,surf,A,width/scene.W,mask,scene.s.median_grass,lut=lut,arte=scene.s.texture_style=='artistico',sol=scene.sol_ambiente())
            if scene.s.texture_style in ('artistico','realistic'):visual.shade_realistic(out,surf,A,width/scene.W,mask,lut=lut,earth_grass=scene.s.earthwork_look=='textura')
            if scene.s.texture_style=='artistico':visual.shade_artistic(out,surf,A,width/scene.W,mask,lut=lut)
            if unshaded is not None:out[:]=cv2.addWeighted(out,strength(scene.s),unshaded,1-strength(scene.s),0)
    # Feições existentes cadastradas também pertencem à subcamada, não só as pistas.
    clone=copy.copy(scene);clone.items=[e for e in scene.items if is_existing(e)]
    clone.image_context_items=[e for e in getattr(scene,'image_context_items',[]) if is_existing(e)]
    from .image_context import draw as draw_context
    draw_context(clone,out,cam,width)
    from .engineering_assets import draw_map
    draw_map(clone,out,cam,width)
    if scene.enhanced:
        clone.edges=[];clone.oae_detail=[o for o in getattr(scene,'oae_detail',[]) if o.get('existing')];clone.oae=[o for o in getattr(scene,'oae',[]) if is_existing(o)];clone._projected_screen=np.zeros(out.shape[:2],np.uint8)
        clone.draw_enhanced_structures(out,cam,width,1.)
    from .dxf_trim import runs
    for e in clone.items:
        role=e.get('role')
        if role not in ('domain','edge_line','sign_h'):continue
        if role=='domain' and not guides(scene.s):continue
        color=(230,209,125) if role=='domain' else (208,205,190)
        for path in runs(e):
            q=np.rint(scene.screen(path,cam,width)).astype(np.int32)
            if e.get('closed') and role=='sign_h':cv2.fillPoly(out,[q],color,cv2.LINE_AA)
            else:cv2.polylines(out,[q],False,color,max(1,round(.15*scene.W/width)),cv2.LINE_AA)
    clone.s=scene.s.model_copy(update={k:[e for e in getattr(scene.s,k) if is_existing(e)] for k in ('railways','traffic_signals','vegetation_points','vegetation_areas')})
    for k in ('_transport_visual','_transport_geometry','_veg'):clone.__dict__.pop(k,None)
    from .transport_render import draw_static
    draw_static(clone,out,cam,width)
    if clone.s.vegetation_points or clone.s.vegetation_areas:
        from .vida import draw_vegetation
        draw_vegetation(clone,out,cam,width,1,int(157*scene.scale),int(154*scene.scale))
    return out
