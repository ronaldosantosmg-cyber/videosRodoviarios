"""Arquivos do projeto: DXF/KMZ, imagens das chamadas, camadas extras, imagem local, ECW e elevação."""
import asyncio,json,os,sys,uuid,shutil,subprocess,threading,time,zipfile,re
from xml.etree.ElementTree import ParseError as ET_ERRORS
from pathlib import Path
from typing import List
from fastapi import APIRouter,UploadFile,File,Form,HTTPException,Request
from fastapi.responses import HTMLResponse,FileResponse,JSONResponse,Response
from pydantic import BaseModel as _BM,ConfigDict,Field
from .. import store
from ..models import Settings
from ..render import ASSETS
from .comum import *
from .comum import _config,_save_config,_receive,_files_meta,_files_info,_img_type,_project_wgs84
router=APIRouter()

@router.post('/api/projects/{pid}/files')
async def upload(pid,file:UploadFile=File(...)):
    idle(pid);ext=Path(file.filename or '').suffix.lower()
    if ext not in ['.dxf','.dwg','.kmz','.kml']:raise HTTPException(415,'Envie DXF, DWG, KMZ ou KML.')
    orig=(file.filename or '')[-200:];kml=ext=='.kml';dwg=ext=='.dwg'
    if dwg:ext='.dxf'   # 1.37: DWG é convertido em DXF (ODA File Converter)
    if kml:ext='.kmz'
    d=store.directory(pid);tmp=d/('upload_'+uuid.uuid4().hex+ext+'.tmp');n=0
    try:
        with tmp.open('wb') as fo:
            while chunk:=await file.read(1024*1024):
                n+=len(chunk)
                if n>400*1024*1024:raise HTTPException(413,'Limite de 400 MB por arquivo.')
                fo.write(chunk)
        if n==0:raise HTTPException(422,'Arquivo vazio.')
        if kml:
            # 1.29: KML solto vira KMZ (o mesmo leitor).
            raw=tmp.read_bytes()
            if b'<kml' not in raw[:4096].lower() and b'kml' not in raw[:4096].lower():raise ValueError('KML inválido.')
            with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('doc.kml',raw)
        if dwg:
            from ..dwg import converter
            bruto=tmp.read_bytes()
            try:dxf=await asyncio.to_thread(converter,bruto,orig)
            except LookupError as e:raise HTTPException(424,str(e))
            except ValueError as e:raise HTTPException(422,str(e))
            (d/'input.dwg').write_bytes(bruto);tmp.write_bytes(dxf)
        if ext=='.dxf':
            head=tmp.open('rb').read(4096)
            if head.startswith(b'AutoCAD Binary DXF'):pass
            elif b'SECTION' not in head.upper() and b'HEADER' not in head.upper():raise ValueError('O arquivo não parece um DXF (texto ou binário). Confira se não é DWG renomeado.')
        if ext=='.kmz':
            from ..kmz_validation import validate
            await asyncio.to_thread(validate,tmp)
        tmp.replace(d/('input'+ext));(d/'analysis.json').unlink(missing_ok=True)
        config=json.loads((d/'config.json').read_text(encoding='utf-8'));config['coordinates_confirmed']=False;store.write_json(d/'config.json',config)
        meta=_files_meta(d);meta[ext[1:]]={'name':Path(orig).name or ('input'+ext),'bytes':n,'sent':time.strftime('%Y-%m-%d %H:%M'),**({'convertido':'DWG'} if dwg else {})};store.write_json(d/'arquivos.json',meta)
        if not dwg and ext=='.dxf':(d/'input.dwg').unlink(missing_ok=True)
    finally:tmp.unlink(missing_ok=True);await file.close()
    return {'ok':True,'bytes':n,'type':ext,'files':_files_info(d)}

@router.get('/api/dwg')
def dwg_info():
    """1.37: há conversor de DWG (ODA File Converter) neste computador?"""
    from ..dwg import conversor,AJUDA
    c=conversor();return {'conversor':c,'ok':bool(c),'ajuda':AJUDA}

@router.delete('/api/projects/{pid}/files/{kind}')
def remove_file(pid,kind:str):
    """1.29: retira o DXF ou o KMZ do projeto (o arquivo original no seu computador não é tocado)."""
    idle(pid)
    if kind not in ('dxf','kmz'):raise HTTPException(404,'Tipo de arquivo desconhecido.')
    d=store.directory(pid);f=d/('input.'+kind)
    if not f.exists():raise HTTPException(404,'Arquivo não carregado.')
    f.unlink();(d/'analysis.json').unlink(missing_ok=True);m=_files_meta(d);m.pop(kind,None);store.write_json(d/'arquivos.json',m)
    return {'files':_files_info(d)}

@router.post('/api/projects/{pid}/overlays',status_code=201)
async def overlay_upload(pid,file:UploadFile=File(...)):
    from ..geometry import overlay_layers,guess
    from ..models import OverlayLayer
    idle(pid);name=file.filename or 'camada.dxf'
    if Path(name).suffix.lower()!='.dxf':raise HTTPException(415,'Envie a camada adicional em DXF.')
    d,s=_config(pid);oid=uuid.uuid4().hex;(d/'camadas').mkdir(exist_ok=True);dest=d/'camadas'/(oid+'.dxf')
    await _receive(file,dest,400*1024*1024)
    try:layers=overlay_layers(dest)
    except Exception as e:
        dest.unlink(missing_ok=True);raise HTTPException(422,'DXF inválido: '+str(e)[:200])
    ov=OverlayLayer(id=oid,name=Path(name).stem[:100] or 'Camada',original_name=name[:260],order=len(s.overlays),roles={l['name']:(l['suggested_role'] or '') for l in layers})
    s.overlays.append(ov);_save_config(pid,s)
    return {'overlay':ov.model_dump(),'layers':layers}

@router.get('/api/projects/{pid}/overlays/{oid}/layers')
def overlay_info(pid,oid):
    from ..geometry import overlay_layers
    if len(oid)!=32 or any(c not in '0123456789abcdef' for c in oid):raise HTTPException(422,'Identificador inválido.')
    path=store.directory(pid)/'camadas'/(oid+'.dxf')
    if not path.exists():raise HTTPException(404,'Camada não encontrada.')
    return overlay_layers(path)

@router.delete('/api/projects/{pid}/overlays/{oid}')
def overlay_delete(pid,oid):
    idle(pid);d,s=_config(pid)
    if not any(o.id==oid for o in s.overlays):raise HTTPException(404,'Camada não encontrada.')
    s.overlays=[o for o in s.overlays if o.id!=oid];_save_config(pid,s)
    (d/'camadas'/(oid+'.dxf')).unlink(missing_ok=True)
    return {'ok':True}

@router.post('/api/projects/{pid}/imagery')
async def imagery_upload(pid,files:List[UploadFile]=File(...),crs:str=Form(''),mode:str=Form('replace')):
    """Imagem local. mode='replace' (a imagem principal, como antes) ou 'add' (1.17: mais uma no mosaico).
    ECW/MrSID e outros formatos do GDAL ficam guardados e são convertidos pela tarefa 'Converter'."""
    from ..local_imagery import IMAGE_EXT,WORLD_EXT,CONVERT_EXT,georef,describe
    from ..models import LocalImagery,LocalSource
    idle(pid);d,s=_config(pid);base=d/'imagem_local';base.mkdir(exist_ok=True)
    names={'image':None,'world':None,'prj':None,'convert':None}
    for f in files:
        ext=Path(f.filename or '').suffix.lower();safe=re.sub(r'[^\w.\- ]','_',Path(f.filename or 'arquivo').name)[:120]
        kind='image' if ext in IMAGE_EXT else 'convert' if ext in CONVERT_EXT else 'world' if ext in WORLD_EXT else 'prj' if ext=='.prj' else None
        if kind is None:raise HTTPException(415,f'Arquivo não suportado: {f.filename}. Use GeoTIFF/COG, JPEG2000 (.jp2), JPG/PNG + arquivo de mundo e .prj, ou ECW/MrSID (conversão com o QGIS).')
        await _receive(f,base/safe,4000*1024*1024 if kind=='convert' else 2500*1024*1024);names[kind]=safe
    if names['convert'] and not names['image']:
        from ..local_tiles import find_gdal
        g=find_gdal()
        from ..ecw_engine import status as ecw_status_
        st=ecw_status_()
        store.write_json(base/'_converter.json',{'file':names['convert'],'mode':mode,'crs':crs.strip() or None})
        return {'needs_conversion':True,'file':names['convert'],'gdal':bool(g),'gdal_bin':g['bin'] if g else None,'internal':bool(st['ecw']),'ready':bool(st['ready'])}
    if not names['image']:raise HTTPException(422,'Envie a imagem (GeoTIFF, JPEG2000, JPG ou PNG).')
    li=LocalImagery(name=names['image'],image=names['image'],world=names['world'],prj=names['prj'],crs=crs.strip() or None)
    try:georef(base/li.image,base/li.world if li.world else None,base/li.prj if li.prj else None,li.crs);info=describe(d,li,s.crs)
    except ValueError as e:
        for k,n in names.items():
            if n and k!='convert':(base/n).unlink(missing_ok=True)
        raise HTTPException(422,str(e))
    if mode=='add' and s.local_imagery.image:
        s.local_imagery.others.append(LocalSource(**{k:getattr(li,k) for k in ('name','image','world','prj','crs')}))
    else:
        li.others=s.local_imagery.others;li.detail=s.local_imagery.detail;li.editor=s.local_imagery.editor
        s.local_imagery=li;s.imagery='local'
    _save_config(pid,s)
    return {'local_imagery':s.local_imagery.model_dump(),'info':info}

@router.get('/api/ecw/status')
def ecw_status():
    from ..ecw_engine import status
    return status()

@router.post('/api/projects/{pid}/ecw/install',status_code=202)
def ecw_install(pid):
    """1.24: instala o leitor ECW interno (GDAL para Python + plugin ECW) no Python portátil."""
    return enqueue(pid,'install_ecw')

@router.post('/api/projects/{pid}/imagery/convert',status_code=202)
def imagery_convert(pid):
    d=store.directory(pid)
    if not (d/'imagem_local'/'_converter.json').exists():raise HTTPException(409,'Envie primeiro o arquivo ECW/MrSID.')
    return enqueue(pid,'convert_imagery')

_SRC_FIELDS=('name','image','world','prj','crs','nodata','shift_x','shift_y','rotation_deg','scale')
def _li_entries(li):
    """Imagens do mosaico em ordem de prioridade (0 = principal), como dicionários de origem."""
    first={k:getattr(li,k) for k in _SRC_FIELDS};first['enabled']=True
    return [first]+[o.model_dump() for o in li.others]
def _li_rebuild(li,entries):
    from ..models import LocalImagery,LocalSource
    if not entries:return LocalImagery()
    head={k:entries[0].get(k) for k in _SRC_FIELDS}
    return li.model_copy(update={**head,'others':[LocalSource(**e) for e in entries[1:]]})

@router.delete('/api/projects/{pid}/imagery/{index}')
def imagery_remove(pid,index:int):
    """Retira uma imagem do mosaico (0 = principal; a próxima vira principal). O arquivo fica na pasta do projeto."""
    idle(pid);d,s=_config(pid);li=s.local_imagery;ent=_li_entries(li) if li.image else []
    if not 0<=index<len(ent):raise HTTPException(404,'Imagem não encontrada.')
    ent.pop(index);s.local_imagery=_li_rebuild(li,ent)
    if not ent and s.imagery=='local':s.imagery='esri'
    _save_config(pid,s);_local_cache.pop(pid,None);return {'local_imagery':s.local_imagery.model_dump()}

class ImageOrder(_BM):
    index:int
    to:int

@router.post('/api/projects/{pid}/imagery/order')
def imagery_order(pid,body:ImageOrder):
    """1.19: muda a prioridade de uma imagem nas sobreposições (0 = fica por cima). Onde nenhuma cobre, vale a fonte web."""
    idle(pid);d,s=_config(pid);li=s.local_imagery;ent=_li_entries(li) if li.image else []
    if not(0<=body.index<len(ent) and 0<=body.to<len(ent)):raise HTTPException(404,'Imagem não encontrada.')
    e=ent.pop(body.index);ent.insert(body.to,e);s.local_imagery=_li_rebuild(li,ent)
    _save_config(pid,s);_local_cache.pop(pid,None);return {'local_imagery':s.local_imagery.model_dump()}

class ImageAdjust(_BM):
    model_config=ConfigDict(allow_inf_nan=False)
    shift_x:float=Field(default=0,ge=-2000,le=2000)
    shift_y:float=Field(default=0,ge=-2000,le=2000)
    rotation_deg:float=Field(default=0,ge=-30,le=30)
    scale:float=Field(default=1,ge=.8,le=1.25)
    enabled:bool|None=None

@router.put('/api/projects/{pid}/imagery/{index}/adjust')
def imagery_adjust(pid,index:int,body:ImageAdjust):
    """1.19: ajuste por grips (deslocar, girar, escalar) de uma imagem local; o arquivo não é alterado."""
    idle(pid);d,s=_config(pid);li=s.local_imagery;ent=_li_entries(li) if li.image else []
    if not 0<=index<len(ent):raise HTTPException(404,'Imagem não encontrada.')
    u=body.model_dump(exclude_none=True)
    if index==0:u.pop('enabled',None)
    ent[index].update(u);s.local_imagery=_li_rebuild(li,ent)
    _save_config(pid,s);_local_cache.pop(pid,None);return {'local_imagery':s.local_imagery.model_dump()}

_local_cache={}
def _local_mosaic(pid):
    from ..local_tiles import LocalMosaic
    d,s=_config(pid);li=s.local_imagery
    if not li.image:return None
    sig=json.dumps(li.model_dump(),sort_keys=True)+s.crs
    hit=_local_cache.get(pid)
    if hit and hit[0]==sig:return hit[1]
    m=LocalMosaic(d,s);_local_cache[pid]=(sig,m);return m

@router.get('/api/projects/{pid}/local/info')
def local_info(pid):
    from ..local_tiles import find_gdal,gdal_formats
    from pyproj import Transformer
    g=find_gdal();out={'gdal':bool(g),'gdal_bin':g['bin'] if g else None,'sources':[]}
    try:m=_local_mosaic(pid)
    except Exception as e:out['error']=str(e)[:300];return out
    if m is None:return out
    tr=Transformer.from_crs(m.target,3857,always_xy=True)
    for k,(src,b) in enumerate(zip(m.sources,m.bbox)):
        x,y=tr.transform([b[0],b[2]],[b[1],b[3]])
        c=src.corners(m.target)
        out['sources'].append({'index':m.index[k],'name':src.name,'file':src.path.name,'size':list(src.size),'pixel_m':round(src.pixel_m(m.target),4),'crs':src.crs.to_string(),'bounds':list(b),'merc':[min(x),min(y),max(x),max(y)],
                               'corners':[[float(p[0]),float(p[1])] for p in c],'center':list(src.center),'adjust':dict(zip(('shift_x','shift_y','rotation_deg','scale'),src.adj))})
    out['count']=1+len(m.li.others)
    px=m.pixel_m();out['pixel_m']=px
    import math
    out['max_zoom']=int(min(22,max(15,math.ceil(math.log2(2*20037508.342789244/256/max(px,.02))))))
    out['key']=m.key;out['editor']=m.li.editor
    return out

@router.get('/api/projects/{pid}/local_tiles/{z}/{y}/{x}.png')
def local_tile(pid,z:int,y:int,x:int):
    """Ladrilho Web Mercator da imagem local (editor), com cache em disco; 204 fora da cobertura."""
    from ..local_tiles import web_tile
    if not(0<=z<=23 and 0<=x<2**z and 0<=y<2**z):raise HTTPException(422,'Ladrilho inválido.')
    try:m=_local_mosaic(pid)
    except Exception as e:raise HTTPException(409,str(e)[:300])
    if m is None:return Response(status_code=204)
    d=store.directory(pid)/'cache_local_web'/m.key/str(z)/str(y);f=d/f'{x}.png';e=d/f'{x}.empty'
    if f.exists():return FileResponse(f,media_type='image/png',headers={'Cache-Control':'max-age=86400'})
    if e.exists():return Response(status_code=204)
    a=web_tile(m,z,x,y);d.mkdir(parents=True,exist_ok=True)
    if a[:,:,3].max()==0:
        e.write_bytes(b'');return Response(status_code=204)
    import cv2 as _cv
    ok,buf=_cv.imencode('.png',_cv.cvtColor(a,_cv.COLOR_RGBA2BGRA))
    tmp=f.with_suffix('.tmp');tmp.write_bytes(buf.tobytes());tmp.replace(f)
    return Response(buf.tobytes(),media_type='image/png',headers={'Cache-Control':'max-age=86400'})

@router.post('/api/projects/{pid}/elevation')
async def elevation_upload(pid,files:List[UploadFile]=File(...),crs:str=Form('')):
    """MDT local: GeoTIFF de elevação ou imagem de 1 banda + arquivo de mundo (+ .prj ou CRS)."""
    from ..local_imagery import IMAGE_EXT,WORLD_EXT,georef
    idle(pid);d,s=_config(pid);base=d/'elevacao';base.mkdir(exist_ok=True);names={'image':None,'world':None,'prj':None}
    for f in files:
        ext=Path(f.filename or '').suffix.lower();safe=re.sub(r'[^\w.\- ]','_',Path(f.filename or 'mdt').name)[:120]
        kind='image' if ext in IMAGE_EXT else 'world' if ext in WORLD_EXT else 'prj' if ext=='.prj' else None
        if kind is None:raise HTTPException(415,f'Arquivo não suportado: {f.filename}. Use GeoTIFF (ou TIF/PNG + arquivo de mundo) e .prj.')
        await _receive(f,base/safe,1500*1024*1024);names[kind]=safe
    if not names['image']:raise HTTPException(422,'Envie o arquivo de elevação (GeoTIFF).')
    try:georef(base/names['image'],base/names['world'] if names['world'] else None,base/names['prj'] if names['prj'] else None,crs.strip() or None)
    except ValueError as e:
        for n in names.values():
            if n:(base/n).unlink(missing_ok=True)
        raise HTTPException(422,str(e))
    s.elevation=s.elevation.model_copy(update={'source':'local','file':names['image'],'world':names['world'],'prj':names['prj'],'crs':crs.strip() or None});_save_config(pid,s)
    return {'elevation':s.elevation.model_dump()}

@router.get('/api/projects/{pid}/elevation_at')
def elevation_at(pid,x:float,y:float):
    from ..elevation import value_at
    return {'z':value_at(store.directory(pid),x,y)}

# ---------------- 1.26: imagens (pórticos/destaques), linhas do desenho, sessões e registros ----------------
@router.post('/api/projects/{pid}/imagens',status_code=201)
async def image_upload(pid,file:UploadFile=File(...)):
    import cv2,numpy as np,hashlib
    d=store.directory(pid);(d/'imagens').mkdir(exist_ok=True);tmp=d/'imagens'/(uuid.uuid4().hex+'.upload')
    try:
        await _receive(file,tmp,15*1024*1024);raw=tmp.read_bytes()
        im=cv2.imdecode(np.frombuffer(raw,np.uint8),cv2.IMREAD_UNCHANGED)
        if im is None or im.ndim<2 or min(im.shape[:2])<8:raise HTTPException(415,'Envie uma imagem PNG ou JPG válida (mínimo 8×8 pixels).')
        if im.ndim==3 and im.shape[2]==4:
            a=im[:,:,3:4].astype(np.float32)/255;im=(im[:,:,:3]*a+255*(1-a)).astype(np.uint8)   # transparência sobre branco
        elif im.ndim==2:im=cv2.cvtColor(im,cv2.COLOR_GRAY2BGR)
        k=1600/max(im.shape[:2])
        if k<1:im=cv2.resize(im,None,fx=k,fy=k,interpolation=cv2.INTER_AREA)
        data=cv2.imencode('.png',im)[1].tobytes();name=hashlib.sha256(data).hexdigest()[:24]+'.png';f=d/'imagens'/name
        if not f.exists():f.write_bytes(data)
        return {'image':name,'size':[int(im.shape[1]),int(im.shape[0])]}
    finally:tmp.unlink(missing_ok=True)

@router.get('/api/projects/{pid}/imagens/{name}')
def image_get(pid,name:str):
    if not re.fullmatch(r'[0-9a-f]{16,40}\.(png|jpg)',name):raise HTTPException(404,'Imagem não encontrada.')
    f=store.directory(pid)/'imagens'/name
    if not f.exists():raise HTTPException(404,'Imagem não encontrada.')
    return FileResponse(f,media_type='image/png' if name.endswith('.png') else 'image/jpeg',headers={'Cache-Control':'max-age=86400'})
