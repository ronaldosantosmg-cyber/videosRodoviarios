"""Seções e reconhecimento assistido; tarefas usam o despachante comum."""
import json
from fastapi import APIRouter,HTTPException
from pydantic import BaseModel,Field
from .comum import _config,enqueue,idle,dispatch_lock,store
from ..image_context_models import ImageRequest
from ..models import RouteAlignment
router=APIRouter()

@router.get('/api/projects/{pid}/traffic-axes')
def traffic_axes(pid,include_short:bool=False):
    from ..geometry import analyze
    from ..dependencies import revisions
    from shapely.geometry import LineString
    from ..native_axes import axis_fingerprint,needs_direction_review
    d,s=_config(pid);before=revisions(d)['geometry']
    try:_,_,_,axes,_=analyze(d,s)
    except ValueError as error:
        if 'Nenhum eixo encontrado' not in str(error):raise
        _,_,_,axes,_=analyze(d,s.model_copy(update={'layers':{}}))
    if revisions(d)['geometry']!=before:raise HTTPException(409,'O desenho mudou durante a leitura. Abra novamente a seleção de eixo.')
    result=[]
    for index,axis in enumerate(axes):
        if axis.get('reference_only'):continue
        points=axis['points'];length=float(LineString(points).length)
        if (length<s.min_route_segment_m and not include_short) or len(points)>20000:continue
        result.append(dict(index=index,fingerprint=axis_fingerprint(points,axis.get('layer',''),axis.get('level',0)),level=axis.get('level',0),name=axis.get('layer') or f'Eixo {index+1}',direction_key='axis:'+axis_fingerprint(points,axis.get('layer',''),axis.get('level',0)),length_m=length,points=points.tolist()))
    from ..native_axes import direction_diagnostics
    return dict(axes=result,revision=before,minimum_m=s.min_route_segment_m,direction_review_required=needs_direction_review(axes,s),diagnostics=direction_diagnostics(axes,s),
                layers=sorted({r['name'] for r in result}),route_directions={k:v for k,v in (s.route_directions or {}).items() if k.startswith('layer:')})

@router.get('/api/projects/{pid}/direction-report')
def direction_report(pid):
    """2.28: sentido efetivo de cada eixo, de onde ele vem e o que foi sobrescrito (somente leitura)."""
    from ..geometry import analyze
    from ..direction_policy import relatorio
    d,s=_config(pid)
    try:_,_,_,axes,_=analyze(d,s)
    except ValueError as error:
        if 'Nenhum eixo encontrado' not in str(error):raise
        _,_,_,axes,_=analyze(d,s.model_copy(update={'layers':{}}))
    return relatorio(axes,s)

@router.get('/api/projects/{pid}/layer-report')
def layer_report(pid):
    """1.42.41: o que o motor entendeu de cada layer (somente leitura)."""
    from ..layer_report import interpret_directory
    d,s=_config(pid)
    try:return interpret_directory(d,s)
    except ValueError as error:raise HTTPException(422,str(error))

@router.get('/api/projects/{pid}/hatch-coverage')
def hatch_coverage(pid):
    """1.42.41: cobertura/conflitos entre hachuras (somente leitura)."""
    from ..geometry import analyze
    from ..hatch_coverage import analyze_coverage
    d,s=_config(pid)
    try:entities,_,_,_,_=analyze(d,s)
    except ValueError as error:
        if 'Nenhum eixo encontrado' not in str(error):raise HTTPException(422,str(error))
        entities,_,_,_,_=analyze(d,s.model_copy(update={'layers':{}}))
    return analyze_coverage(entities)

@router.get('/api/projects/{pid}/axis-validation')
def axis_validation(pid):
    """1.42.41: continuidade dos eixos sobre o pavimento reconhecido (somente leitura)."""
    from ..geometry import analyze
    from ..axis_validation import validate_axes
    d,s=_config(pid)
    try:entities,_,_,axes,_=analyze(d,s)
    except ValueError as error:
        if 'Nenhum eixo encontrado' not in str(error):raise HTTPException(422,str(error))
        entities,_,_,axes,_=analyze(d,s.model_copy(update={'layers':{}}))
    axes=[a for a in axes if not a.get('reference_only')]
    return validate_axes(axes,entities,[r for r in s.route_alignments if r.enabled])

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
@router.get('/api/via/presets')
def via_presets():
    from ..via_presets import catalogo
    return {'presets':catalogo()}

class ViaBody(BaseModel):
    preset:str
    axis:dict
    params:dict=Field(default_factory=dict)
    previous:dict|None=None

@router.post('/api/via/montar')
def via_montar(body:ViaBody):
    from ..via_presets import montar
    from ..routes import build_lanes
    from ..models import RouteAlignment
    try:route=montar(body.preset,body.axis,body.params,body.previous)
    except (ValueError,KeyError,TypeError) as error:raise HTTPException(422,str(error))
    lanes=build_lanes(RouteAlignment.model_validate(route))
    return {'route':route,'lanes':[dict(points=ln['points'].tolist(),direction=ln['dir'],lane=ln['lane']) for ln in lanes]}

@router.post('/api/sections/validate')
def section_preview(body:SectionsBody):
    from ..routes import build_lanes
    from ..transicao_secoes import eixo_transicao
    return {'route':body.route.model_dump(),'lanes':[dict(points=ln['points'].tolist(),direction=ln['dir'],lane=ln['lane']) for ln in build_lanes(body.route)],'transitions':eixo_transicao(body.route)}

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

@router.post('/api/projects/{pid}/traffic-check',status_code=202)
def check_traffic_job(pid):return enqueue(pid,'traffic_check')

def current_traffic_check(pid):
    from ..project_state import revision
    from ..dependencies import digest,revisions
    d,s=_config(pid);path=d/'traffic_check.json'
    if not path.is_file():raise HTTPException(404,'Execute Testar circulação primeiro.')
    result=json.loads(path.read_text(encoding='utf-8'))
    if result.get('config_revision')!=digest([revision(s.model_dump()),revisions(d,s)]):raise HTTPException(409,'A configuração mudou. Refaça Testar circulação.')
    return d,result

@router.get('/api/projects/{pid}/traffic-check')
def check_traffic_report(pid):return current_traffic_check(pid)[1]

@router.get('/api/projects/{pid}/traffic-check.png')
def check_traffic_image(pid):
    from fastapi.responses import FileResponse
    d,_=current_traffic_check(pid);return FileResponse(d/'traffic_check.png',media_type='image/png',headers={'Cache-Control':'no-store'})
