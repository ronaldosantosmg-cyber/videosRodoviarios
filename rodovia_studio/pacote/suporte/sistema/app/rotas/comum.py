"""Funções comuns às rotas da API (fila de tarefas, configuração do projeto, arquivos enviados)."""
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
BASE=Path(__file__).resolve().parents[2]
# Despachante de tarefas (server.py) e cancelamento (rotas/tarefas.py) usam a mesma trava.
stop=threading.Event();dispatch_lock=threading.Lock()
VERSION=json.loads((BASE/'VERSAO.json').read_text(encoding='utf-8')).get('version','1.3.0') if (BASE/'VERSAO.json').exists() else '1.3.0'
def idle(pid):
    store.directory(pid)
    with store.connect() as c:r=c.execute("SELECT id FROM jobs WHERE project=? AND state IN ('queued','running','cancel_requested')",(pid,)).fetchone()
    if r:raise HTTPException(409,'Aguarde a tarefa atual terminar ou cancele-a.')
def enqueue(pid,kind):
    store.directory(pid);jid=uuid.uuid4().hex
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        busy=c.execute("SELECT id FROM jobs WHERE project=? AND state IN ('queued','running','cancel_requested')",(pid,)).fetchone()
        if busy:raise HTTPException(409,'Aguarde a tarefa atual terminar ou cancele-a.')
        c.execute('INSERT INTO jobs(id,project,kind,state,message) VALUES(?,?,?,?,?)',(jid,pid,kind,'queued','Na fila'))
    return {'id':jid,'state':'queued'}

def _files_meta(d):
    f=d/'arquivos.json'
    try:return json.loads(f.read_text(encoding='utf-8')) if f.exists() else {}
    except ValueError:return {}
def _files_info(d):
    m=_files_meta(d);out={}
    for k in ('dxf','kmz'):
        f=d/('input.'+k)
        out[k]=({'name':m.get(k,{}).get('name') or f.name,'bytes':f.stat().st_size,'sent':m.get(k,{}).get('sent') or time.strftime('%Y-%m-%d %H:%M',time.localtime(f.stat().st_mtime)),**({'convertido':m[k]['convertido']} if m.get(k,{}).get('convertido') else {})} if f.exists() else None)
    return out

def _config(pid):
    d=store.directory(pid);return d,Settings.model_validate(json.loads((d/'config.json').read_text(encoding='utf-8')))
def _save_config(pid,s):
    d=store.directory(pid);store.write_json(d/'config.json',s.model_dump() if hasattr(s,'model_dump') else s)
async def _receive(file,dest,limit):
    n=0;tmp=Path(str(dest)+'.tmp')
    try:
        with tmp.open('wb') as fo:
            while chunk:=await file.read(1024*1024):
                n+=len(chunk)
                if n>limit:raise HTTPException(413,f'Limite de {limit//1024//1024} MB por arquivo.')
                fo.write(chunk)
        if n==0:raise HTTPException(422,'Arquivo vazio.')
        store.replace(tmp,dest)
    finally:tmp.unlink(missing_ok=True);await file.close()
    return n

# ---------------- 1.19: outras fontes web ----------------
def _img_type(data):return 'image/png' if data[:8]==b'\x89PNG\r\n\x1a\n' else 'image/jpeg'

# ---------------- 1.25: catálogo QuickMapServices ----------------
def _project_wgs84(pid):
    from ..qms import project_area_wgs84
    d,s=_config(pid);a=d/'analysis.json'
    if not a.exists():raise HTTPException(409,'Analise os arquivos primeiro: a busca usa a área do trecho.')
    rep=json.loads(a.read_text(encoding='utf-8'))
    try:return project_area_wgs84(s.crs,rep['bounds'],margin_m=200)
    except Exception as e:raise HTTPException(422,f'Não foi possível converter a área do projeto para WGS84: {e}')
__all__=['stop','dispatch_lock','BASE', 'VERSION', 'idle', 'enqueue', '_config', '_save_config', '_receive', '_files_meta', '_files_info', '_img_type', '_project_wgs84', 'ASSETS', 'store', 'Settings', '_BM']
