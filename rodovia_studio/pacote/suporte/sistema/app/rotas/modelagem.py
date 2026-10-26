"""Seções e reconhecimento assistido; tarefas usam o despachante comum."""
import json
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field
from .comum import _config,enqueue,idle,dispatch_lock,store
from ..image_context_models import ImageRequest
from ..models import RouteAlignment
router=APIRouter()

@router.post('/api/projects/{pid}/image_context',status_code=202)
def analyze_image(pid,body:ImageRequest):
    with dispatch_lock:
        idle(pid);d,s=_config(pid)
        from pathlib import Path
        li=s.local_imagery
        if not li.image or Path(li.image).name!=li.image or not(d/'imagem_local'/li.image).is_file():raise HTTPException(409,'Carregue uma imagem local georreferenciada para habilitar esta função.')
        if body.crs!=s.crs:raise HTTPException(409,'O CRS mudou. Selecione a área novamente.')
        store.write_json(d/'contexto_imagem/pedido.json',body.model_dump());return enqueue(pid,'image_context')

@router.get('/api/projects/{pid}/image_context')
def image_result(pid):
    d,s=_config(pid);file=d/'contexto_imagem/resultado.json'
    if not file.is_file():raise HTTPException(404,'Analise uma imagem antes de carregar as sugestões.')
    result=json.loads(file.read_text(encoding='utf-8'))
    from ..image_context import source_signature
    if source_signature(d,s,result['request'])!=result['signature']:raise HTTPException(409,'A imagem ou sua georreferência mudou. Repita a análise.')
    return result

class SectionsBody(BaseModel):
    route:RouteAlignment
@router.post('/api/sections/validate')
def section_preview(body:SectionsBody):
    from ..routes import build_lanes
    return {'route':body.route.model_dump(),'lanes':[dict(points=ln['points'].tolist(),direction=ln['dir'],lane=ln['lane']) for ln in build_lanes(body.route)]}

from ..models import Settings
@router.post('/api/modelagem/validate')
def validate_model(settings:Settings):
    return {'valid':True}

@router.get('/api/projects/{pid}/image_context/status')
def image_status(pid):
    from pathlib import Path
    from ..image_context_models import LABELS
    d,s=_config(pid);li=s.local_imagery
    available=bool(li.image and Path(li.image).name==li.image and (d/'imagem_local'/li.image).is_file())
    current=True
    if s.image_context_source:
        from ..image_context import source_signature
        source=s.image_context_source;current=source_signature(d,s,source.request.model_dump())==source.signature
    bounds=None
    if available:
        try:
            from ..local_tiles import LocalMosaic
            mosaic=LocalMosaic(d,s);corners=[source.corners(mosaic.target) for source in mosaic.sources]
            import numpy as np
            pts=np.vstack(corners);bounds=[float(pts[:,0].min()),float(pts[:,1].min()),float(pts[:,0].max()),float(pts[:,1].max())]
        except (ValueError,OSError):available=False
    from ..image_semantic import status
    return {'available':available,'current':current,'groups':LABELS,'bounds':bounds,'semantic':status(store.ROOT/'modelos'/'imagem_aerea')}

@router.get('/api/projects/{pid}/image_context/capture.png')
def image_capture(pid):
    import re,hashlib
    from fastapi.responses import FileResponse
    result=image_result(pid);key=result['source_hash']
    if not re.fullmatch('[a-f0-9]{64}',key):raise HTTPException(409,'Referência da captura inválida. Repita a análise.')
    d,_=_config(pid);base=(d/'contexto_imagem/fontes').resolve();file=base/(key[:24]+'.png')
    if not file.is_file() or file.is_symlink() or not file.resolve().is_relative_to(base):raise HTTPException(404,'Captura ausente. Repita a análise da imagem.')
    if result.get('capture_sha256') and hashlib.sha256(file.read_bytes()).hexdigest()!=result['capture_sha256']:raise HTTPException(409,'Captura alterada. Repita a análise.')
    return FileResponse(file,media_type='image/png',headers={'Cache-Control':'no-store'})
