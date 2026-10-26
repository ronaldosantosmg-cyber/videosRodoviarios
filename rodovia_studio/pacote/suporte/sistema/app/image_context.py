"""Segmentação local por semelhança, amostras e referências CAD; sugestões exigem revisão."""
import hashlib,json
from pathlib import Path
import cv2
import numpy as np
from shapely.geometry import Polygon,Point
from .image_context_models import LABELS,DEFAULT_MATERIAL,ImageFeature


def source_signature(directory,settings,request):
    from .dependencies import input_stamps,digest
    _,images=input_stamps(directory)
    from .models import LocalImagery,WebImagery
    li=LocalImagery.model_validate(settings.local_imagery.model_dump()).model_dump();li.pop('name',None)
    for item in li['others']:item.pop('name',None)
    web=WebImagery.model_validate(settings.web_imagery.model_dump()).model_dump()
    return digest([images,settings.crs,li,web,request])


def segment(rgb,bounds,*,clusters=12,min_area_m2=4.,samples=(),hints=(),limit=500,status=lambda *a:None,cancel=lambda:False,semantic=None):
    image=np.asarray(rgb)
    if image.dtype!=np.uint8 or image.ndim!=3 or image.shape[2] not in (3,4) or min(image.shape[:2])<8 or image.size>2048*2048*4:raise ValueError('Imagem RGB inválida ou acima do limite de análise.')
    x0,y0,x1,y1=map(float,bounds)
    if not np.isfinite(bounds).all() or x1<=x0 or y1<=y0:raise ValueError('Área de análise inválida.')
    if not 2<=clusters<=32 or not .1<=min_area_m2<=10000 or not 1<=limit<=1000:raise ValueError('Parâmetros de segmentação fora dos limites.')
    H,W=image.shape[:2];dx=(x1-x0)/W;dy=(y1-y0)/H
    rgb=np.ascontiguousarray(image[:,:,:3],dtype=np.uint8);valid=(image[:,:,3]>0) if image.shape[2]>3 else np.any(rgb!=[58,73,64],axis=2)
    if valid.sum()<20:raise ValueError('A imagem não tem cobertura suficiente na área selecionada.')
    lab=cv2.cvtColor(rgb,cv2.COLOR_RGB2LAB).astype(np.float32);gray=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY).astype(np.float32)
    mean=cv2.blur(gray,(7,7));texture=np.sqrt(np.maximum(0,cv2.blur(gray*gray,(7,7))-mean*mean))
    values=np.dstack([lab,texture*.6]);flat=values.reshape(-1,4);idx=np.flatnonzero(valid.ravel());rng=np.random.default_rng(1729)
    labels=None
    if semantic is None:
        training=flat[rng.choice(idx,min(len(idx),32768),replace=False)]
        # Trava e semente próprias: resultados não dependem de execuções anteriores.
        import threading
        with _cluster_lock:
            cv2.setRNGSeed(1729);_,_,centers=cv2.kmeans(training,min(clusters,len(training)),None,(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,30,.3),1,cv2.KMEANS_PP_CENTERS)
        labels=np.full(H*W,-1,np.int16)
        for start in range(0,len(idx),32768):
            if cancel():raise InterruptedError('Análise da imagem cancelada.')
            ids=idx[start:start+32768];labels[ids]=((flat[ids,None]-centers[None])**2).sum(2).argmin(1)
        labels=labels.reshape(H,W)
    if semantic is not None:
        labels=np.asarray(semantic['labels']);centers=np.zeros((len(semantic['classes']),4),np.float32)
        if labels.shape!=(H,W) or not np.isfinite(labels).all():raise ValueError('Máscara semântica incompatível.')
        labels=labels.copy();labels[~valid]=-1
    alpha=image[:,:,3] if image.shape[2]==4 else np.full((H,W),255,np.uint8);source_hash=hashlib.sha256(rgb.tobytes()+alpha.tobytes()+np.asarray(bounds,'<f8').tobytes()).hexdigest()
    prepared=[]
    for sample in samples:
        role=sample['role'];px=int((sample['x']-x0)/dx);py=int((y1-sample['y'])/dy)
        if role not in LABELS or role=='unclassified' or not(0<=px<W and 0<=py<H) or not valid[py,px]:raise ValueError('Amostra fora da cobertura ou classe inválida.')
        prepared.append((Point(sample['x'],sample['y']),role,values[py,px]))
    out=[];truncated=False;vertex_count=0
    for cluster in range(len(centers)):
        if cancel():raise InterruptedError('Análise da imagem cancelada.')
        if semantic is not None and semantic['classes'][cluster]=='unclassified':continue
        status(.45+.45*cluster/len(centers),'Agrupando contornos por cor e textura')
        mask=(labels==cluster).astype(np.uint8)
        count,components,stats,_=cv2.connectedComponentsWithStats(mask,8)
        for index in np.argsort(stats[1:,cv2.CC_STAT_AREA])[::-1]+1:
            if stats[index,cv2.CC_STAT_AREA]*dx*dy<min_area_m2:continue
            a,b,w,h,area=map(int,stats[index]);crop=(components[b:b+h,a:a+w]==index).astype(np.uint8)
            contours,hierarchy=cv2.findContours(crop,cv2.RETR_CCOMP,cv2.CHAIN_APPROX_SIMPLE)
            if hierarchy is None:continue
            def ring(c):
                c=cv2.approxPolyDP(c,.8,True).reshape(-1,2)+[a,b]
                return [[float(x0+(x+.5)*dx),float(y1-(y+.5)*dy)] for x,y in c]
            for ci,contour in enumerate(contours):
                if hierarchy[0,ci,3]>=0:continue
                outer=ring(contour)
                if len(outer)<3:continue
                holes=[];child=hierarchy[0,ci,2]
                while child>=0:
                    hole=ring(contours[child])
                    if len(hole)>=3:holes.append(hole)
                    child=hierarchy[0,child,0]
                geometry=Polygon(outer,holes)
                if not geometry.is_valid or geometry.area<min_area_m2 or len(outer)>2000 or any(len(hole)>2000 for hole in holes) or len(holes)>100:continue
                role='unclassified';confidence=0.;evidence='Grupo de semelhança; classe não confirmada.'
                if semantic is not None:
                    role=semantic['classes'][cluster];confidence=float(np.mean(semantic['confidence'][b:b+h,a:a+w][crop>0]))
                    evidence='Modelo semântico local '+semantic['model_sha256'][:12]+'; conferir objeto e altura.'
                inside=[s for s in prepared if geometry.covers(s[0])]
                if inside:
                    classes={s[1] for s in inside}
                    if len(classes)==1:role=inside[0][1];confidence=.9;evidence='Amostra manual dentro deste contorno.'
                elif prepared and semantic is None:
                    distances=[np.linalg.norm(centers[cluster]-s[2]) for s in prepared];best=int(np.argmin(distances))
                    if distances[best]<28:role=prepared[best][1];confidence=.55;evidence='Semelhança com amostra manual; requer revisão.'
                if role=='unclassified':
                    for hint in hints:
                        if hint['role'] in LABELS and hint['geometry'].intersection(geometry).area/geometry.area>.65:
                            role=hint['role'];confidence=.75;evidence='Interseção com referência CAD classificada; conferir.';break
                if role=='unclassified':
                    pixels=rgb[b:b+h,a:a+w][crop>0];r,g,bl=np.median(pixels,axis=0)
                    if g>r*1.12 and g>bl*1.08:role='vegetation';confidence=.4;evidence='Predomínio de verde; hipótese, não classificação semântica.'
                    elif bl>r*1.2 and bl>g*1.06:role='water';confidence=.3;evidence='Predomínio azulado; confirmar água, sombra ou cobertura.'
                    elif r>g*1.2 and r>bl*1.25:role='building' if geometry.area/geometry.minimum_rotated_rectangle.area>.8 else 'cut';confidence=.25;evidence='Cor/forma compatível; confirmar cobertura ou solo.'
                identifier=hashlib.sha256(f'{source_hash}:{cluster}:{index}:{ci}'.encode()).hexdigest()[:24]
                entry=dict(id=identifier,name=f'{LABELS[role]} {len(out)+1}',role=role,points=[dict(x=x,y=y) for x,y in outer],holes=[[dict(x=x,y=y) for x,y in hole] for hole in holes],similarity_group=cluster,confidence=confidence,evidence=evidence,source_hash=source_hash,material=DEFAULT_MATERIAL[role],height_m=6 if role in ('building','vegetation') else 8 if role=='electric' else 0,reviewed=False)
                vertex_count+=len(outer)+sum(len(hole) for hole in holes)
                if vertex_count>100000:truncated=True;break
                out.append(ImageFeature.model_validate(entry).model_dump())
                if len(out)>=limit:truncated=True;break
            if truncated:break
        if truncated:break
    result=dict(features=out,source_hash=source_hash,groups=LABELS,resolution_m=[dx,dy],truncated=truncated,method='similaridade_local_com_amostras_e_referencias',warning='Sugestões de cor/textura não equivalem a reconhecimento semântico certificado. OAE, ferrovia, transmissão e sinalização exigem referência ou amostra/revisão. Alturas são ilustrativas até edição.')
    if semantic is not None:
        result.update(method='modelo_semantico_local',model_sha256=semantic['model_sha256'],evaluation=semantic['evaluation'],warning='Reconhecimento limitado às classes e às condições avaliadas do modelo instalado. Revise os objetos; alturas e desníveis não são inferidos da fotografia.')
    return result

import threading
_cluster_lock=threading.Lock()


def run(directory,settings,request,status,cancel,jid=None):
    from .imagery import mosaic
    from . import store
    original_status=status
    def status(progress,message):
        if cancel():raise InterruptedError('Análise da imagem cancelada.')
        original_status(progress,message)
    d=Path(directory);li=settings.local_imagery
    if not li.image or Path(li.image).name!=li.image or not(d/'imagem_local'/li.image).is_file() or not (d/'imagem_local'/li.image).resolve().is_relative_to((d/'imagem_local').resolve()):raise ValueError('Carregue uma imagem local georreferenciada para habilitar esta função.')
    if request['crs']!=settings.crs:raise ValueError('O CRS mudou; selecione novamente a área.')
    from pyproj import CRS
    crs=CRS.from_user_input(settings.crs)
    if not crs.is_projected or any(abs(axis.unit_conversion_factor-1)>1e-6 for axis in crs.axis_info[:2]):raise ValueError('A análise de áreas exige um CRS projetado em metros.')
    signature=source_signature(d,settings,request);box=request['bounds'];n=request['pixels']
    status(.05,'Preparando a imagem na área selecionada')
    if request['source']=='local':
        from .local_tiles import LocalMosaic
        image=LocalMosaic(d,settings).render_base(box,n,status);attribution='Imagem local georreferenciada'
    else:
        web=settings.model_copy(deep=True);web.imagery='esri';web.imagery_pixels=2048
        image,box,attribution=mosaic(d,web,[[box[0],box[1]],[box[2],box[3]]],status)
        image=cv2.resize(image,(n,n),interpolation=cv2.INTER_AREA)
    if cancel():raise InterruptedError('Análise cancelada.')
    hints=[]
    try:
        from .geometry import analyze
        items,*_=analyze(d,settings)
        for item in items:
            if item['closed'] and item['role'] in LABELS:
                poly=Polygon(item['points'],holes=item.get('holes',[]))
                if poly.is_valid:hints.append(dict(role=item['role'],geometry=poly))
    except (ValueError,FileNotFoundError):pass
    semantic=None
    if request.get('method')=='semantic':
        from .image_semantic import predict
        status(.3,'Reconhecendo classes com modelo semântico local')
        semantic=predict(image,store.ROOT/'modelos'/'imagem_aerea',cancel=cancel)
    result=segment(image,box,clusters=request['clusters'],min_area_m2=request['min_area_m2'],samples=request['samples'],hints=hints,status=status,cancel=cancel,semantic=semantic)
    result.update(signature=signature,request=request,bounds=box,attribution=attribution,job_id=jid)
    from .project_state import read_config
    from .models import Settings
    if source_signature(d,Settings.model_validate(read_config(d)),request)!=signature:raise ValueError('As imagens mudaram durante a análise. Repita a operação.')
    if cancel():raise InterruptedError('Análise cancelada.')
    target=d/'contexto_imagem';target.mkdir(exist_ok=True)
    sources=target/'fontes';sources.mkdir(exist_ok=True)
    from PIL import Image
    from datetime import datetime,timezone
    capture=sources/(result['source_hash'][:24]+'.png')
    metadata=capture.with_suffix('.json')
    if metadata.exists() and json.loads(metadata.read_text(encoding='utf-8')).get('source_hash')!=result['source_hash']:raise ValueError('Conflito de referência de captura; a fonte anterior foi preservada.')
    tmp=sources/'.captura.wip.png'
    try:Image.fromarray(image).save(tmp);store.replace(tmp,capture)
    finally:tmp.unlink(missing_ok=True)
    store.write_json(capture.with_suffix('.json'),dict(bounds=box,crs=settings.crs,attribution=attribution,time_utc=datetime.now(timezone.utc).isoformat(),source_hash=result['source_hash']))
    result['capture']=capture.name;result['capture_sha256']=hashlib.sha256(capture.read_bytes()).hexdigest()
    store.write_json(target/'resultado.json',result);status(1,f"{len(result['features'])} contornos sugeridos; revise antes de aplicar")


def accepted_items(settings,technical=(),directory=None):
    if not settings.image_features:return []
    if directory is not None and settings.image_context_source:
        source=settings.image_context_source
        if source_signature(directory,settings,source.request.model_dump())!=source.signature:return []
    from shapely.ops import unary_union
    masks=[Polygon(e['points'],holes=e.get('holes',[])) for e in technical if e.get('closed') and e.get('role') not in ('axis','line','unknown')]
    mask=unary_union([p for p in masks if p.is_valid]) if masks else None;out=[]
    for feature in settings.image_features:
        group=settings.image_groups.get(feature.role)
        if not(feature.enabled and feature.reviewed and feature.render) or feature.role=='unclassified' or group is not None and not group.render:continue
        poly=Polygon([(p.x,p.y) for p in feature.points],holes=[[(p.x,p.y) for p in h] for h in feature.holes])
        if mask is not None:poly=poly.difference(mask)
        parts=poly.geoms if hasattr(poly,'geoms') else [poly]
        for part in parts:
            if part.geom_type!='Polygon' or part.area<.01:continue
            out.append(dict(points=np.asarray(part.exterior.coords)[:-1],holes=[np.asarray(r.coords)[:-1] for r in part.interiors],closed=True,role=feature.role,layer=feature.name,asset_material=feature.material,wall_material=feature.wall_material,height_m=feature.height_m,paint_color=feature.paint_color,context=True))
    return out


def draw(scene,image,cam,width):
    """Somente texturas; contornos de edição nunca entram no quadro exportado."""
    from .asset_catalog import image as texture
    items=getattr(scene,'image_context_items',[])
    for item in items:
        q=np.clip(scene.screen(item['points'],cam,width),-1000000,1000000).astype(np.int32)
        x0,y0=np.maximum(q.min(0),[0,0]);x1,y1=np.minimum(q.max(0)+1,[scene.W,scene.H])
        if x1<=x0 or y1<=y0:continue
        mask=np.zeros((y1-y0,x1-x0),np.uint8);cv2.fillPoly(mask,[q-[x0,y0]],255)
        for hole in item['holes']:cv2.fillPoly(mask,[np.clip(scene.screen(hole,cam,width),-1000000,1000000).astype(np.int32)-[x0,y0]],0)
        tex=texture(item['asset_material']) if item['role']!='paint' else np.full((128,128,3),(244,200,70) if item['paint_color']=='yellow' else (244,242,226),np.uint8)
        m=width/scene.W;right=getattr(scene,'right',np.array([1.,0.]));up=getattr(scene,'up',np.array([0.,1.]));anchor=item['points'][0]
        for row in range(0,y1-y0,256):
            count=min(256,y1-y0-row);Y,X=np.indices((count,x1-x0));Y+=row
            wx=cam[0]+(X+x0-scene.W/2)*m*right[0]-(Y+y0-scene.H/2)*m*up[0]
            wy=cam[1]+(X+x0-scene.W/2)*m*right[1]-(Y+y0-scene.H/2)*m*up[1]
            ix=np.floor((wx-anchor[0])/.1).astype(np.int64)%128;iy=np.floor(-(wy-anchor[1])/.1).astype(np.int64)%128
            tile=tex[iy,ix];roi=image[y0+row:y0+row+count,x0:x1];inside=mask[row:row+count]>0;roi[inside]=tile[inside]



def meshes(items,local):
    """Volumes ilustrativos e superfícies trianguladas, já recortados pelas máscaras técnicas."""
    import shapely
    from .asset_catalog import CATALOG,ASSET_ROLES
    from .engineering_assets import asset_meshes
    flat=lambda item:item['role'] in ('building','vegetation','electric') and item['height_m']<=0
    out=asset_meshes([item for item in items if not flat(item)],local)
    for mesh in out:mesh['id']='image-'+mesh['id']
    for i,item in enumerate(items):
        if item['role'] in ASSET_ROLES and not flat(item):continue
        poly=Polygon(item['points'],holes=item['holes']);positions=[]
        for triangle in shapely.constrained_delaunay_triangles(poly).geoms:positions.extend(local(np.asarray(triangle.exterior.coords)[:3],.025+item['height_m']).ravel().tolist())
        if positions:
            material=CATALOG[item['asset_material']]
            out.append(dict(id='image-surface-'+str(i),name=item['layer']+' · imagem revisada',role=item['role'],positions=positions,color=('#f4c846' if item['paint_color']=='yellow' else '#f4f2e2') if item['role']=='paint' else material['color'],asset_material=material['id'],texture_pattern=material['pattern'],illustrative_dimensions=True))
    if sum(len(m['positions'])//3 for m in out)>200000:raise ValueError('Contornos da imagem excedem o limite 3D. Reduza a área ou simplifique os objetos.')
    return out
