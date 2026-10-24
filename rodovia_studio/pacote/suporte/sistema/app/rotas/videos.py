"""1.32: vídeos guardados (um por geração), abrir pastas no Explorer e limpeza de resíduos (Arquivo › Limpar memória)."""
import os,sys,subprocess
from fastapi import APIRouter,HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel as _BM,Field
from .. import store
from .comum import dispatch_lock
router=APIRouter()

@router.get('/api/projects/{pid}/videos')
def videos_list(pid):
    from ..videos import listing
    store.directory(pid);return listing(pid)

@router.get('/api/projects/{pid}/videos/{name}')
def videos_file(pid,name:str,baixar:bool=False):
    from ..videos import path_of
    store.directory(pid);f=path_of(pid,name)
    return FileResponse(f,media_type='video/mp4',filename=f.name if baixar else None,headers=None if baixar else {'Content-Disposition':'inline'})

@router.delete('/api/projects/{pid}/videos/{name}')
def videos_delete(pid,name:str):
    from ..videos import remove
    store.directory(pid);return {'lixeira':remove(pid,name)}

class Pasta(_BM):
    tipo:str=Field(pattern='^(videos|projetos|videos_projeto|sistema|atualizacoes)$')
    pid:str|None=None

@router.post('/api/abrir_pasta')
def open_folder(body:Pasta):
    """Abre a pasta no Explorer (o servidor é local). Fora do Windows devolve o caminho."""
    from ..videos import find_folder,project_folder
    if body.tipo=='videos':d=store.videos_root()
    elif body.tipo=='projetos':d=store.ROOT
    elif body.tipo=='sistema':d=store.system_root() or store.ROOT
    elif body.tipo=='atualizacoes':d=(store.INSTALL or store.ROOT)/'atualizacoes'
    else:
        if not body.pid:raise HTTPException(422,'Informe o projeto.')
        s=None
        try:
            import json
            s=json.loads((store.directory(body.pid)/'config.json').read_text(encoding='utf-8')).get('name')
        except Exception:pass
        d=find_folder(body.pid) or project_folder(body.pid,s or 'Projeto')
    d.mkdir(parents=True,exist_ok=True)
    opened=False
    if os.name=='nt' and not os.environ.get('RODOVIA_SEM_EXPLORER'):
        try:os.startfile(str(d));opened=True
        except OSError:pass
    return {'pasta':str(d),'aberta':opened}

class Limpeza(_BM):
    categorias:list[str]=Field(min_length=1)

def _paths():
    from ..store import INSTALL,videos_root
    return INSTALL,videos_root()

@router.get('/api/limpeza')
def cleanup_survey():
    from ..maintenance import survey
    inst,vid=_paths();return {'categorias':survey(store.ROOT,inst,vid)}

@router.post('/api/limpeza')
def cleanup_run(body:Limpeza):
    from ..maintenance import clean_categories
    with dispatch_lock:
        with store.connect() as c:
            row=c.execute("SELECT id FROM jobs WHERE state IN ('queued','running','cancel_requested') LIMIT 1").fetchone()
        if row:raise HTTPException(409,'Termine ou cancele a tarefa em andamento antes de limpar.')
        inst,vid=_paths()
        try:return clean_categories(store.ROOT,body.categorias,inst,vid)
        except ValueError as e:raise HTTPException(422,str(e))
