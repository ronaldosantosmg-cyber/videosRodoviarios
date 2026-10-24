"""Sessões de trabalho e registros (execução, erros, prompt para IA)."""
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

class SessionState(_BM):
    model_config=ConfigDict(extra='forbid')
    state: dict

def _sessions_file(pid):return store.directory(pid)/'sessoes.json'
def _sessions(pid):
    f=_sessions_file(pid)
    try:return json.loads(f.read_text(encoding='utf-8')) if f.exists() else {}
    except ValueError:return {}
def _session_name(name):
    name=(name or '').strip()
    if not(1<=len(name)<=60) or any(c in name for c in '\\/<>:"|?*'):raise HTTPException(422,'Nome da sessão: 1 a 60 caracteres, sem \\ / < > : " | ? *.')
    return name

@router.get('/api/projects/{pid}/sessoes')
def sessions_list(pid):
    S=_sessions(pid);return {'sessions':[{'name':k,'saved':v.get('saved'),'state':v.get('state',{})} for k,v in sorted(S.items(),key=lambda kv:kv[1].get('saved',''),reverse=True)]}

@router.put('/api/projects/{pid}/sessoes/{name}')
def sessions_save(pid,name:str,body:SessionState):
    name=_session_name(name);raw=json.dumps(body.state)
    if len(raw)>200000:raise HTTPException(413,'Estado da sessão grande demais.')
    S=_sessions(pid)
    if name not in S and len(S)>=50:raise HTTPException(409,'Limite de 50 sessões salvas; apague alguma.')
    S[name]={'saved':time.strftime('%Y-%m-%d %H:%M:%S'),'state':body.state};store.write_json(_sessions_file(pid),S);return {'name':name,'saved':S[name]['saved']}

@router.delete('/api/projects/{pid}/sessoes/{name}')
def sessions_delete(pid,name:str):
    S=_sessions(pid)
    if name not in S:raise HTTPException(404,'Sessão não encontrada.')
    del S[name];store.write_json(_sessions_file(pid),S);return {'deleted':name}

@router.get('/api/projects/{pid}/registros')
def logs_list(pid,tipo:str='execucao',limite:int=300):
    from ..execlog import read
    if tipo not in ('execucao','erros'):raise HTTPException(422,'Tipo deve ser execucao ou erros.')
    return {'tipo':tipo,'eventos':read(store.directory(pid),tipo,max(1,min(2000,limite)))}

class ClientError(_BM):
    model_config=ConfigDict(extra='forbid')
    mensagem: str = Field(max_length=2000)
    pilha: str = Field(default='',max_length=8000)
    origem: str = Field(default='',max_length=300)
    acao: str = Field(default='',max_length=300)

@router.post('/api/projects/{pid}/registros/erro_tela')
def logs_client(pid,body:ClientError):
    from ..execlog import write,read
    d=store.directory(pid)
    recent=[e for e in read(d,'erros',30) if e.get('evento')=='erro_tela' and e.get('mensagem')==body.mensagem]
    if len(recent)>=5:return {'ok':True,'repetido':True}   # evita encher o registro com o mesmo erro
    write(d,'erros','erro_tela',mensagem=body.mensagem,pilha=body.pilha,origem=body.origem,acao=body.acao);return {'ok':True}

@router.delete('/api/projects/{pid}/registros')
def logs_clear(pid):
    from ..execlog import clear
    return {'removed':clear(store.directory(pid))}

@router.get('/api/projects/{pid}/prompt_ia.md')
def logs_prompt(pid):
    from ..execlog import ai_prompt
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(ai_prompt(store.directory(pid),pid),media_type='text/markdown; charset=utf-8',headers={'Content-Disposition':'attachment; filename="prompt_ia_rodovia_studio.md"'})

@router.get('/api/projects/{pid}/registros.zip')
def logs_zip(pid):
    from ..execlog import bundle
    return Response(bundle(store.directory(pid),pid),media_type='application/zip',headers={'Content-Disposition':'attachment; filename="registros_rodovia_studio.zip"'})

@router.get('/api/projects/{pid}/catalogo_uso')
def usage_catalog(pid):
    from ..execlog import read
    from ..usage_catalog import summarize
    d=store.directory(pid)
    return summarize(read(d,'execucao',3000),read(d,'erros',1000))
