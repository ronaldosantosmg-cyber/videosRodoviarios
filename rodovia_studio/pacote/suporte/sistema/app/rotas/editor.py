"""Dados do editor: vetores, snap, seleção de linhas/áreas, alinhamento, rotas, texturas, esquema."""
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

class RoutesBody(_BM):
    route_alignments:list=[]

@router.post('/api/rotas_previa')
def routes_preview(body:RoutesBody):
    """1.30: faixas geradas pelos alinhamentos de rota (o mesmo cálculo usado na rede de tráfego)."""
    from ..models import RouteAlignment
    from ..routes import preview
    class _S:pass
    s=_S();s.route_alignments=[RouteAlignment.model_validate(r) for r in body.route_alignments]
    return {'lanes':preview(s)}


@router.get('/api/projects/{pid}/editor.json')
def editor_file(pid):
    path=store.directory(pid)/'editor.json'
    if not path.exists():raise HTTPException(404,'Gere uma prévia para carregar o editor.')
    from ..dependencies import revisions
    try:
        data=json.loads(path.read_text())
        if data.get('engine_revision')!=revisions(path.parent)['editor']:raise HTTPException(409,'Editor desatualizado. Recalcule os fluxos.')
    except (ValueError,OSError):raise HTTPException(409,'Editor inválido. Recalcule os fluxos.')
    from ..artifacts import require_current
    require_current(path.parent,'editor')
    return JSONResponse(data,headers={'Cache-Control':'no-store'})

@router.post('/api/projects/{pid}/validate_path')
def validate_path(pid,body:dict):
    """Valida um fluxo desenhado antes de aceitá-lo (mesma regra do motor)."""
    import shapely
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    from ..markup import validate_path as check
    from ..models import Point
    d=store.directory(pid)/'editor'
    if not (d/'allowed.wkb').exists():raise HTTPException(409,'Gere a prévia antes de incluir fluxos.')
    try:points=[Point.model_validate(p) for p in body.get('points',[])]
    except Exception:raise HTTPException(422,'Pontos inválidos.')
    g={n:shapely.from_wkb((d/(n+'.wkb')).read_bytes()) for n in ['roads','obstacles','allowed']}
    cfg=Settings.model_validate(json.loads((store.directory(pid)/'config.json').read_text(encoding='utf-8')))
    ex=unary_union([Polygon([(p.x,p.y) for p in a]).buffer(0) for a in cfg.exclusions]) if cfg.exclusions else Polygon()
    allowed=g['allowed'].difference(ex) if not ex.is_empty else g['allowed']
    return check(points,g['roads'],g['obstacles'],ex,allowed)

@router.post('/api/alignment/fit')
def alignment_fit(body:dict):
    from ..alignment import fit
    from ..models import DxfAlignment
    al=DxfAlignment.model_validate(body)
    return fit(al.pairs,al.mode)

@router.get('/api/texture_preview.png')
def texture_preview(surface:str='pista_nova',p:str='{}',m_px:float=.02,realistic:bool=True,estilo:str=''):
    """1.24: amostra da textura de uma superfície com os ajustes informados (para o editor de texturas)."""
    import cv2,numpy as np
    from .. import visual
    from ..geometry import COLORS
    from ..models import TextureParam
    if surface not in visual.TEX_SURF:raise HTTPException(422,'Superfície desconhecida.')
    try:params={surface:TextureParam(**json.loads(p or '{}'))}
    except Exception as e:raise HTTPException(422,'Parâmetros inválidos: '+str(e)[:200])
    m_px=min(max(m_px,.005),.5)
    base={'pista_nova':COLORS['pavement'],'pista_existente':COLORS['existing_pavement'],'concreto':COLORS['oae'],'acostamento':COLORS['shoulder'],
          'canteiro':COLORS['median'],'trilhas':COLORS['existing_pavement'],'talude_corte':'#8a6a4e','talude_aterro':'#6f8a55'}[surface]
    H,W=200,360;im=np.zeros((H,W,3),np.uint8);im[:]=[int(base[i:i+2],16) for i in (1,3,5)]
    code=visual.TEX_SURF[surface][0];surf=np.full((H,W),2 if surface=='trilhas' else code,np.uint8)
    if surface=='trilhas':surf[:,int(W*.3):int(W*.42)]=8;surf[:,int(W*.58):int(W*.7)]=8
    A=np.array([[m_px,0,704000.],[0,-m_px,7811000.]]);valid=np.ones((H,W),bool);lut=visual.texture_lut(params)
    visual.shade_surface(im,surf,A,m_px,valid,True,lut=lut,arte=estilo=='artistico')
    if realistic:visual.shade_realistic(im,surf,A,m_px,valid,lut=lut)
    if estilo=='artistico':visual.shade_artistic(im,surf,A,m_px,valid,lut=lut)   # 1.34
    ok,buf=cv2.imencode('.png',cv2.cvtColor(im,cv2.COLOR_RGB2BGR))
    return Response(buf.tobytes(),media_type='image/png',headers={'Cache-Control':'no-store'})

@router.get('/api/projects/{pid}/linha')
def pick_line_api(pid,x:float,y:float,tol:float=5,continua:bool=False):
    """Linha do desenho mais próxima do clique (vértices exatos); continua=1 segue as linhas conectadas."""
    from ..webmap import pick_line,chain_lines
    if not(0<tol<=200):raise HTTPException(422,'Tolerância entre 0 e 200 m.')
    try:r=chain_lines(store.directory(pid),x,y,tol) if continua else pick_line(store.directory(pid),x,y,tol)
    except FileNotFoundError as e:raise HTTPException(409,str(e))
    if r is None:raise HTTPException(404,f'Nenhuma linha do desenho a menos de {tol:g} m do ponto.')
    return r

@router.get('/api/projects/{pid}/area')
def pick_area_api(pid,x:float,y:float):
    """1.27: área fechada do desenho sob o clique (para trocar textura, nome ou tipo)."""
    from ..webmap import pick_area
    try:r=pick_area(store.directory(pid),x,y)
    except FileNotFoundError as e:raise HTTPException(409,str(e))
    if r is None:raise HTTPException(404,'Nenhuma área fechada do desenho neste ponto.')
    return r

@router.get('/api/projects/{pid}/avanco')
def advance_info(pid,velocidade_kmh:float|None=None,duracao_s:float|None=None):
    """1.27: converte velocidade de avanço <-> duração do vídeo para este projeto."""
    from ..render import duration_for_speed,tour_seconds
    d,s=_config(pid);a=d/'analysis.json'
    if not a.exists():raise HTTPException(409,'Analise os arquivos primeiro.')
    L=float(json.loads(a.read_text(encoding='utf-8'))['geometric_length_m']);has=bool(s.pois or s.works or s.oae_marks or s.highlights);mode=s.camera_mode
    if velocidade_kmh is not None:
        if not(5<=velocidade_kmh<=5000):raise HTTPException(422,'Velocidade entre 5 e 5000 km/h.')
        T=duration_for_speed(L,velocidade_kmh,has,mode)
    else:
        T=float(duracao_s if duracao_s is not None else s.duration_s)
        if not(3<=T<=1800):raise HTTPException(422,'Duração entre 3 e 1800 s.')
    tour=max(.1,tour_seconds(T,has,mode));v=L/tour*3.6
    return {'comprimento_m':round(L,1),'duracao_s':round(T,1),'percurso_s':round(tour,1),'velocidade_kmh':round(v,1),'aproximado':has}

_SCHEMA_CACHE=None
@router.get('/api/esquema')
def schema_enums():
    """1.29: valores aceitos por campo de cada lista de marcações (para o editor só oferecer opções válidas)."""
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        sc=Settings.model_json_schema();defs=sc.get('$defs',{});out={}
        def enum_of(prop):
            if 'enum' in prop:return prop['enum'],prop.get('default')
            for alt in prop.get('anyOf',[]):
                if 'enum' in alt:return alt['enum']+([None] if any(a.get('type')=='null' for a in prop['anyOf']) else []),prop.get('default')
            return None,None
        for key,prop in sc['properties'].items():
            ref=(prop.get('items') or {}).get('$ref') or prop.get('$ref') or next((a.get('$ref') for a in prop.get('anyOf',[]) if a.get('$ref')),None)
            if not ref:continue
            d=defs.get(ref.split('/')[-1],{});fields={}
            for f,fp in d.get('properties',{}).items():
                vals,default=enum_of(fp)
                if vals:fields[f]={'values':vals,'default':default}
            if fields:out[key]=fields
        _SCHEMA_CACHE=out
    return _SCHEMA_CACHE

@router.get('/api/projects/{pid}/hachuras_previa')
def hatch_preview(pid):
    f=store.directory(pid)/'hachuras_previa.json'
    if not f.exists():return {}
    return JSONResponse(json.loads(f.read_text(encoding='utf-8')))

@router.get('/api/projects/{pid}/geo')
def project_geo(pid):
    from ..webmap import fit
    d=store.directory(pid);a=d/'analysis.json'
    if not a.exists():raise HTTPException(409,'Analise os arquivos para abrir o editor sobre a imagem web.')
    rep=json.loads(a.read_text(encoding='utf-8'));cfg=json.loads((d/'config.json').read_text(encoding='utf-8'))
    key=json.dumps([rep['bounds'],cfg.get('crs')]);cache=d/'geo.json'
    if cache.exists():
        g=json.loads(cache.read_text(encoding='utf-8'))
        if g.get('key')==key:return g
    g=fit(cfg.get('crs','EPSG:31983'),rep['bounds']);g['key']=key;store.write_json(cache,g);return g

@router.get('/api/projects/{pid}/snap')
def project_snap(pid,x0:float,y0:float,x1:float,y1:float):
    """1.24: vértices e pontos médios exatos do desenho dentro da janela (para o snap com precisão total)."""
    from ..webmap import snap_points
    if x1<x0 or y1<y0 or (x1-x0)*(y1-y0)>4e6:raise HTTPException(422,'Janela inválida ou grande demais (aproxime a vista).')
    return snap_points(store.directory(pid),x0,y0,x1,y1)

@router.get('/api/projects/{pid}/vectors.json')
def project_vectors(pid):
    f=store.directory(pid)/'vectors.json'
    if not f.exists():raise HTTPException(404,'Analise os arquivos para gerar os vetores do editor.')
    from ..artifacts import require_current
    require_current(f.parent,'vectors')
    return FileResponse(f,media_type='application/json',headers={'Cache-Control':'no-store'})

# ---------------- 1.10: cidades próximas ----------------
@router.get('/api/projects/{pid}/cities/auto')
def project_cities(pid,radius_km:float=25):
    from ..cities import nearby
    d=store.directory(pid);a=d/'analysis.json'
    if not a.exists():raise HTTPException(409,'Analise os arquivos antes de buscar as cidades próximas.')
    if not(1<=radius_km<=150):raise HTTPException(422,'Raio entre 1 e 150 km.')
    rep=json.loads(a.read_text(encoding='utf-8'));cfg=json.loads((d/'config.json').read_text(encoding='utf-8'))
    try:return {'cities':nearby(d,cfg.get('crs','EPSG:31983'),rep['bounds'],radius_km)}
    except ValueError as e:raise HTTPException(422,str(e))
    except OSError as e:raise HTTPException(503,str(e)+' Você pode marcar as cidades à mão com a ferramenta Cidade.')

@router.post('/api/projects/{pid}/scene3d',status_code=202)
def scene3d_job(pid):return enqueue(pid,'scene3d')

@router.get('/api/projects/{pid}/scene3d.json')
def scene3d_file(pid):
    from ..scene3d import revision
    d=store.directory(pid);f=d/'scene3d.json'
    if not f.is_file():raise HTTPException(404,'Construa a cena 3D primeiro.')
    try:
        data=json.loads(f.read_text(encoding='utf-8'))
        if data.get('revision')!=revision(d):raise HTTPException(409,'Cena desatualizada. Reconstrua o 3D.')
    except (ValueError,OSError):raise HTTPException(409,'Cena inválida. Reconstrua o 3D.')
    from ..artifacts import require_current
    require_current(d,'scene3d')
    return JSONResponse(data,headers={'Cache-Control':'no-store'})

from typing import Literal
class Camera3D(_BM):
    model_config=ConfigDict(allow_inf_nan=False,extra='forbid')
    position:list[float]=Field(min_length=3,max_length=3)
    target:list[float]=Field(min_length=3,max_length=3)
    follow_id:int|None=Field(default=None,ge=0)
    light:Literal['dia','entardecer']='dia'
class Capture3D(_BM):
    model_config=ConfigDict(allow_inf_nan=False,extra='forbid')
    revision:str=Field(pattern=r'^[a-f0-9]{64}$')
    width:Literal[1280,1920,2560,3840]=1280
    fps:Literal[24,30]=24
    duration_s:float=Field(ge=3,le=60)
    camera:Camera3D

@router.post('/api/projects/{pid}/scene3d/capture',status_code=202)
def capture3d_begin(pid,body:Capture3D):
    from ..scene3d import revision
    from ..capture3d import begin
    d,s=_config(pid)
    with dispatch_lock:
        idle(pid)
        if not (d/'scene3d.json').is_file():raise HTTPException(409,'Construa a cena 3D primeiro.')
        data=json.loads((d/'scene3d.json').read_text())
        if body.revision!=data.get('revision') or body.revision!=revision(d):raise HTTPException(409,'A cena está desatualizada. Reconstrua o 3D.')
        if body.duration_s>data.get('duration_s',0)+.0001:raise HTTPException(422,'A duração excede a prévia simulada disponível.')
        s=s.model_copy(update={'width':body.width,'fps':body.fps})
        return begin(d,pid,s,body.revision,body.camera.model_dump(),body.duration_s)

@router.post('/api/projects/{pid}/scene3d/capture/{jid}/frame')
async def capture3d_frame(pid,jid,index:int,request:Request):
    from ..capture3d import session
    from starlette.concurrency import run_in_threadpool
    s=session(jid,request.headers.get('X-Rodovia-Capture'))
    if s.pid!=pid:raise HTTPException(403,'Projeto de exportação inválido.')
    data=bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data)>16*1024*1024:s.abort('Quadro acima do limite.');raise HTTPException(413,'Quadro acima de 16 MB.')
    return await run_in_threadpool(s.feed,index,bytes(data))

@router.post('/api/projects/{pid}/scene3d/capture/{jid}/finish')
def capture3d_finish(pid,jid,request:Request):
    from ..capture3d import session
    s=session(jid,request.headers.get('X-Rodovia-Capture'))
    if s.pid!=pid:raise HTTPException(403,'Projeto de exportação inválido.')
    return s.finish()

@router.post('/api/projects/{pid}/scene3d/capture/{jid}/cancel')
def capture3d_cancel(pid,jid,request:Request):
    from ..capture3d import session
    s=session(jid,request.headers.get('X-Rodovia-Capture'))
    if s.pid!=pid:raise HTTPException(403,'Projeto de exportação inválido.')
    s.abort('Cancelado pelo usuário.',cancelled=True);return {'cancelled':True}

@router.get('/api/projects/{pid}/scene3d/capture/{jid}')
def capture3d_status(pid,jid,request:Request):
    from ..capture3d import session
    s=session(jid,request.headers.get('X-Rodovia-Capture'))
    if s.pid!=pid:raise HTTPException(403,'Projeto de exportação inválido.')
    return {'ready':s.ready,'ended':s.ended,'accepted':s.count,'frames':s.frames,'job':store.job(jid)}

@router.post('/api/transport/validate')
def transport_validate(body:Settings):
    return {key:[row.model_dump() for row in getattr(body,key)] for key in ('railways','traffic_signals','signal_links')}
