"""Perfis de camadas e prévia por camada."""
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

# ---------------- 1.14: perfis de camadas e prévia por camada ----------------
@router.get('/api/layer_profiles')
def layer_profiles_list():
    from .. import layer_profiles as LP
    return {'profiles':LP.load(store.ROOT),'roles':LP.ROLE_LABELS}

@router.post('/api/layer_profiles')
async def layer_profiles_save(request:Request):
    from .. import layer_profiles as LP
    try:body=await request.json()
    except Exception:raise HTTPException(422,'Envie o perfil em JSON.')
    try:return LP.save(store.ROOT,body)
    except ValueError as e:raise HTTPException(422,str(e))

@router.delete('/api/layer_profiles/{name}')
def layer_profiles_delete(name:str):
    from .. import layer_profiles as LP
    if not LP.delete(store.ROOT,name):raise HTTPException(404,'Perfil não encontrado (o perfil padrão não pode ser excluído).')
    return {'ok':True}

@router.post('/api/projects/{pid}/layer_profiles/apply')
async def layer_profiles_apply(pid,request:Request):
    from .. import layer_profiles as LP
    d=store.directory(pid);a=d/'analysis.json'
    body=await request.json();name=body.get('name');prof=next((p for p in LP.load(store.ROOT) if p['name']==name),None)
    if prof is None:raise HTTPException(404,'Perfil não encontrado.')
    from ..layer_catalog import catalog
    layers=sorted({l['name'] for l in catalog(d)['layers']}|({l['name'] for l in json.loads(a.read_text(encoding='utf-8'))['layers']} if a.exists() else set()))
    mapping=LP.apply(layers,prof)
    from ..asset_catalog import CATALOG
    materials={}
    for name in layers:
        rule=next((rule for rule in prof['rules'] if LP.matches(rule['pattern'],name)),{})
        if rule.get('material') in CATALOG:materials[name]=rule['material']
    return {'materials':materials,'layers':mapping,'matched':sum(len(v) for v in mapping.values()),'total':len(layers)}

@router.get('/api/projects/{pid}/layers_preview.json')
def project_layers_preview(pid):
    f=store.directory(pid)/'camadas_previa.json'
    if not f.exists():raise HTTPException(404,'Analise os arquivos para gerar a prévia das camadas.')
    return FileResponse(f,media_type='application/json',headers={'Cache-Control':'no-store'})


@router.get('/api/materials')
def materials_catalog():
    from ..asset_catalog import CATALOG,ASSET_ROLES
    return {'materials':list(CATALOG.values()),'roles':ASSET_ROLES,'scope':'Materiais procedurais locais; símbolos e dimensões de apresentação não substituem cadastro técnico.'}

@router.get('/api/materials/{key}.png')
def material_image(key:str):
    from ..asset_catalog import CATALOG,png
    if key not in CATALOG:raise HTTPException(404,'Material não cadastrado.')
    return Response(png(key),media_type='image/png',headers={'Cache-Control':'public, max-age=86400'})
