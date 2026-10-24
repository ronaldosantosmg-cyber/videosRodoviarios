"""Modelos (templates) de projeto."""
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
from .projetos import create
router=APIRouter()

class TemplateBody(_BM):
    name:str=Field(min_length=1,max_length=100)
    description:str=Field(default='',max_length=200)
    include_marks:bool=False

class TemplateNew(_BM):
    name:str=Field(min_length=1,max_length=100)

class TemplateRename(_BM):
    name:str=Field(min_length=1,max_length=100)
    description:str|None=Field(default=None,max_length=200)

@router.get('/api/modelos')
def templates():
    from .. import modelos
    return modelos.listing(store.ROOT)

@router.post('/api/projects/{pid}/modelo',status_code=201)
def template_save(pid,body:TemplateBody):
    from .. import modelos
    d,s=_config(pid);return modelos.save(store.ROOT,s,body.name,body.description,body.include_marks,source=s.name)

@router.get('/api/modelos/{mid}')
def template_get(mid):
    from .. import modelos
    j,s=modelos.load(store.ROOT,mid);return {**{k:j.get(k) for k in ('name','description','created','include_marks')},'id':mid,'config':s.model_dump()}

@router.post('/api/modelos/{mid}/rename')
def template_rename(mid,body:TemplateRename):
    from .. import modelos
    return modelos.rename(store.ROOT,mid,body.name,body.description)

@router.delete('/api/modelos/{mid}')
def template_delete(mid):
    from .. import modelos
    return {'trash':modelos.delete(store.ROOT,mid)}

@router.post('/api/modelos/{mid}/novo',status_code=201)
def template_new_project(mid,body:TemplateNew):
    """Novo projeto a partir do modelo (sem arquivos; envie o DXF/KMZ depois)."""
    from .. import modelos
    from ..migration import clean_name
    n=clean_name(body.name,'')
    if not n:raise HTTPException(422,'Nome inválido: use pelo menos uma letra ou número.')
    j,s=modelos.load(store.ROOT,mid);s.name=n;s.coordinates_confirmed=False
    r=create(s);r['template']=j.get('name');return r

@router.post('/api/projects/{pid}/aplicar_modelo/{mid}')
def template_apply(pid,mid):
    """Aplica as configurações do modelo; mantém as marcações e os dados do trecho. Cópia da configuração anterior."""
    from .. import modelos
    d,s=_config(pid);j,t=modelos.load(store.ROOT,mid)
    b=d/f'config_antes_modelo_{time.strftime("%Y%m%d_%H%M%S")}.json';store.write_json(b,s.model_dump())
    new=modelos.apply(s,t);_save_config(pid,new)
    return {'config':new.model_dump(),'backup':b.name,'template':j.get('name')}
