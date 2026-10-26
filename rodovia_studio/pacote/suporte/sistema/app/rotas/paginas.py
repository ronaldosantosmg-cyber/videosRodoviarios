"""Páginas, ícones, saúde do servidor e “Sobre”."""
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

@router.get('/',response_class=HTMLResponse)
def index():
    # 1.40.5: módulos JS separados. Um erro de sintaxe/execução em um módulo não impede o navegador
    # de tentar carregar os módulos seguintes; /app.js permanece por compatibilidade e diagnóstico.
    try:
        html=(BASE/'app/index.html').read_text(encoding='utf-8')
    except (OSError,UnicodeError):
        raise HTTPException(503,'Interface ausente ou inacessível. Preserve os projetos e solicite à TI a verificação da instalação e da quarentena do antivírus.') from None
    if html.count('<!-- RODOVIA_INTERFACE_MODULES -->')!=1:
        raise HTTPException(503,'Interface incompatível ou incompleta. Verifique a revisão instalada antes de abrir o editor.')
    tags=''.join(f'<script src="/js/{f.name}"></script>' for f in sorted((BASE/'app/js').glob('[0-9][0-9]_*.js')))
    sprite=(BASE/'app/icons/infrarail-sprite.svg').read_text(encoding='utf-8')
    return html.replace('<!-- RODOVIA_INTERFACE_MODULES -->',sprite+tags)

@router.get('/interface/{name}',include_in_schema=False)
def interface_asset(name:str):
    assets={'tema.js':'application/javascript','estrutura.css':'text/css'}
    if name not in assets:raise HTTPException(404,'Recurso de interface não encontrado.')
    return FileResponse(BASE/'app/interface'/name,media_type=assets[name],headers={'Cache-Control':'no-store'})

@router.get('/js/{name}',include_in_schema=False)
def js_module(name:str):
    if not re.fullmatch(r'[0-9]{2}_[A-Za-z0-9_\-]+\.js',name):raise HTTPException(404,'Módulo não encontrado.')
    f=BASE/'app/js'/name
    if not f.is_file():raise HTTPException(404,'Módulo não encontrado.')
    return Response(f.read_text(encoding='utf-8'),media_type='application/javascript',headers={'Cache-Control':'no-store'})
@router.get('/ajuda',response_class=HTMLResponse)
def ajuda():return (BASE/'app/ajuda.html').read_text(encoding='utf-8')
@router.get('/app.js')
def app_js():
    """1.31: a interface fica em app/js/NN_assunto.js; o navegador recebe um script só, na ordem dos números
    (mesmo comportamento de antes, quando tudo estava em app.js). Cada parte começa com uma linha
    // ==== arquivo: NN_assunto.js ==== para localizar erros."""
    return Response(interface_js(),media_type='application/javascript',headers={'Cache-Control':'no-store'})
def interface_js():
    parts=[]
    for f in sorted((BASE/'app/js').glob('[0-9][0-9]_*.js')):
        parts.append(f'// ==== arquivo: {f.name} ====\n'+f.read_text(encoding='utf-8'))
    return ''.join(parts)
@router.get('/estilo.css')
def estilo_css():
    """1.31: estilos da interface (antes dentro do index.html), com as cores principais em variáveis."""
    return FileResponse(BASE/'app/estilo.css',media_type='text/css',headers={'Cache-Control':'no-store'})
@router.get('/api/health')
def health(request:Request):
    import imageio_ffmpeg
    return {'status':'ok','version':VERSION,'ffmpeg':Path(imageio_ffmpeg.get_ffmpeg_exe()).is_file(),'data':str(store.ROOT),'startup_seconds':getattr(request.app.state,'startup_seconds',None)}

@router.get('/marca/icone.png',include_in_schema=False)
def app_icon():
    f=BASE/'app/icone.png'
    return FileResponse(f,media_type='image/png',headers={'Cache-Control':'public, max-age=86400'}) if f.exists() else Response(status_code=404)

@router.get('/marca/georas.png',include_in_schema=False)
def georas_logo():
    f=BASE/'app/georas_logo.png'
    return FileResponse(f,media_type='image/png',headers={'Cache-Control':'public, max-age=86400'}) if f.exists() else Response(status_code=404)

@router.get('/favicon.ico',include_in_schema=False)
def favicon():
    f=BASE/'app/icone.png'
    return FileResponse(f,media_type='image/png') if f.exists() else Response(status_code=204)

@router.get('/api/sobre')
def about():
    """1.27: versões do aplicativo, do formato de projeto e do iniciador (para a janela Sobre)."""
    from ..migration import SCHEMA_VERSION
    import platform
    launcher=None
    try:
        for f in [store.ROOT.parent/'sistema'/'logs'/'iniciador_versao.txt',store.ROOT.parent/'suporte'/'logs'/'iniciador_versao.txt']:
            if f.exists():launcher=f.read_text(encoding='utf-8').strip()[:80];break
    except Exception:pass
    return {'app':VERSION,'schema':SCHEMA_VERSION,'launcher':launcher,'pastas':{'projetos':str(store.ROOT),'videos':str(store.videos_root()),'sistema':str(store.system_root() or '')},'python':platform.python_version(),'system':platform.platform()}

@router.get('/api/capacidades')
def local_capabilities():
    from ..capabilities import inspect_local
    return inspect_local()
