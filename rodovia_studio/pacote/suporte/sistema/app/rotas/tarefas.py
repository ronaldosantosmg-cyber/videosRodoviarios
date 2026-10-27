"""Tarefas em segundo plano (análise, prévia, vídeo, exportações) e seus resultados."""
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

@router.post('/api/projects/{pid}/analyze',status_code=202)
def analyze_job(pid):return enqueue(pid,'analyze')
@router.post('/api/projects/{pid}/refresh',status_code=202)
def refresh_job(pid):return enqueue(pid,'refresh')
@router.post('/api/projects/{pid}/preview',status_code=202)
def preview_job(pid):return enqueue(pid,'preview')
@router.post('/api/projects/{pid}/render',status_code=202)
def render_job(pid):
    d=store.directory(pid);s=Settings.model_validate(json.loads((d/'config.json').read_text(encoding='utf-8')))
    if not s.coordinates_confirmed:raise HTTPException(422,'Confirme as coordenadas na configuração antes de renderizar.')
    return enqueue(pid,'render')
@router.post('/api/projects/{pid}/reference',status_code=202)
def reference_job(pid):
    if not (ASSETS/'th57/referencia.mp4').exists():raise HTTPException(410,'O vídeo de referência foi substituído pela ficha técnica (somente dados para comparação).')
    return enqueue(pid,'reference')
@router.get('/api/reference/profile')
def reference_profile():
    f=ASSETS/'th57/referencia_ficha.json'
    data=json.loads(f.read_text(encoding='utf-8')) if f.exists() else {'status':'ausente'}
    data['video_present']=(ASSETS/'th57/referencia.mp4').exists();return data
@router.post('/api/projects/{pid}/reference_profile',status_code=202)
def reference_profile_job(pid,remove:bool=False):
    if not (ASSETS/'th57/referencia.mp4').exists():raise HTTPException(410,'O vídeo de referência não está mais na pasta; a ficha técnica já é a referência.')
    return enqueue(pid,'reference_profile_remove' if remove else 'reference_profile')
@router.post('/api/projects/{pid}/compare',status_code=202)
def compare_job(pid):
    from ..videos import current
    if current(store.directory(pid)) is None:raise HTTPException(409,'Gere um vídeo antes de comparar.')
    return enqueue(pid,'compare')
@router.get('/api/projects/{pid}/comparison')
def comparison(pid):
    f=store.directory(pid)/'comparacao.json'
    if not f.exists():return {'rows':[],'reference_status':None}
    return json.loads(f.read_text(encoding='utf-8'))
@router.get('/api/jobs/{jid}')
def get_job(jid):return store.job(jid)
@router.post('/api/jobs/{jid}/cancel')
def cancel(jid):
    with dispatch_lock:
        j=store.job(jid)
        if j['state']=='queued':store.update(jid,state='cancelled',message='Cancelado antes de iniciar')
        elif j['state']=='running':store.update(jid,state='cancel_requested',message='Cancelamento solicitado')
    return store.job(jid)
@router.get('/api/projects/{pid}/preview.png')
def preview_file(pid):
    file=store.directory(pid)/'preview.png'
    if not file.is_file():raise HTTPException(404,'Gere uma prévia primeiro.')
    from ..artifacts import require_current
    require_current(file.parent,'preview')
    return FileResponse(file,media_type='image/png',headers={'Cache-Control':'no-store'})
@router.get('/api/projects/{pid}/video.mp4')
def video_file(pid):
    from ..videos import current
    file=current(store.directory(pid))
    if file is None:raise HTTPException(404,'O vídeo ainda não está pronto.')
    return FileResponse(file,media_type='video/mp4',filename=file.name if file.name!='video.mp4' else 'video_rodoviario.mp4')
@router.get('/api/projects/{pid}/log')
def logs(pid):
    d=store.directory(pid);return {'error':(d/'error.log').read_text(encoding='utf-8')[-8000:] if (d/'error.log').exists() else '', 'ffmpeg':(d/'ffmpeg.log').read_text(encoding='utf-8',errors='replace')[-8000:] if (d/'ffmpeg.log').exists() else ''}

@router.get('/api/projects/{pid}/traffic_network.json')
def traffic_report(pid):
    path=store.directory(pid)/'traffic_network.json'
    if not path.exists():raise HTTPException(404,'Gere uma prévia primeiro.')
    return FileResponse(path,filename='diagnostico_trafego.json')

@router.get('/api/maintenance')
def maintenance_info():
    from ..maintenance import clean
    return clean(store.ROOT)

@router.post('/api/maintenance/cleanup')
def maintenance_clean():
    from ..maintenance import clean
    with dispatch_lock:
        with store.connect() as c:
            row=c.execute("SELECT id FROM jobs WHERE state IN ('queued','running','cancel_requested') LIMIT 1").fetchone()
        if row:raise HTTPException(409,'Termine ou cancele a tarefa antes de limpar os caches.')
        return clean(store.ROOT,True)

@router.post('/api/projects/{pid}/export',status_code=202)
def export_job(pid):return enqueue(pid,'export')
@router.post('/api/projects/{pid}/frames',status_code=202)
def frames_job(pid):return enqueue(pid,'frames')

EXPORTS={'modelo_wgs84.geojson':'application/geo+json','modelo.kml':'application/vnd.google-earth.kml+xml','modelo.kmz':'application/vnd.google-earth.kmz','marcacoes.dxf':'application/dxf','obras.csv':'text/csv'}
@router.get('/api/projects/{pid}/exports')
def export_list(pid):
    d=store.directory(pid)/'exportacao'
    files=[{'name':f.name,'bytes':f.stat().st_size} for f in sorted(d.iterdir()) if f.is_file() and not f.name.endswith('.tmp')] if d.exists() else []
    frames=sorted([p.name for p in (store.directory(pid)/'quadros_png').iterdir() if p.is_dir()]) if (store.directory(pid)/'quadros_png').exists() else []
    return {'files':files,'png_sequences':frames,'folder':str(d)}
@router.get('/api/projects/{pid}/exports/{name}')
def export_file(pid,name):
    if not re.fullmatch(r'[\w.\-]{1,80}',name):raise HTTPException(422,'Nome inválido.')
    f=store.directory(pid)/'exportacao'/name
    if not f.is_file():raise HTTPException(404,'Gere a exportação primeiro.')
    return FileResponse(f,filename=name,media_type=EXPORTS.get(name,'application/geo+json' if name.endswith('.geojson') else 'application/octet-stream'))

@router.get('/api/projects/{pid}/preview_cabin.png')
def preview_cabin(pid):
    f=store.directory(pid)/'preview_cabin.png'
    if not f.is_file():raise HTTPException(404,'Gere a prévia com a vista da cabine ativa e “Câmera do vídeo”.')
    return FileResponse(f,media_type='image/png',headers={'Cache-Control':'no-store'})

@router.get('/api/projects/{pid}/traffic_status')
def traffic_status(pid):
    from ..traffic_presentation import project_status
    return project_status(store.directory(pid))
