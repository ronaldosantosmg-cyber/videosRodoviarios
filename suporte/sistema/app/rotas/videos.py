"""1.32: vídeos guardados (um por geração), abrir pastas no Explorer e limpeza de resíduos (Arquivo › Limpar memória)."""
from ..falhas import registrar as _falha
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
        except Exception as _e:_falha(__name__,_e)
        d=find_folder(body.pid) or project_folder(body.pid,s or 'Projeto')
    d.mkdir(parents=True,exist_ok=True)
    opened=False
    if os.name=='nt' and not os.environ.get('RODOVIA_SEM_EXPLORER'):
        try:os.startfile(str(d));opened=True
        except OSError as _e:_falha(__name__,_e)
    return {'pasta':str(d),'aberta':opened}

class Limpeza(_BM):
    categorias:list[str]=Field(min_length=1)
    cancelar_pendentes:bool=False

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
        if row and body.cancelar_pendentes:
            import time
            with store.connect() as c:
                c.execute("UPDATE jobs SET state='cancelled',message='Cancelada para limpar a memória.' WHERE state='queued'")
                c.execute("UPDATE jobs SET state='cancel_requested' WHERE state='running'")
            for _ in range(40):
                with store.connect() as c:row=c.execute("SELECT id FROM jobs WHERE state IN ('queued','running','cancel_requested') LIMIT 1").fetchone()
                if not row:break
                time.sleep(.25)
        if row:raise HTTPException(409,'Há tarefa em andamento. Marque “cancelar tarefas pendentes” ou aguarde terminar antes de limpar.')
        inst,vid=_paths()
        try:return clean_categories(store.ROOT,body.categorias,inst,vid)
        except ValueError as e:raise HTTPException(422,str(e))


@router.get('/api/limpeza/quarentena')
def quarantine_list():
    import json
    from ..quarantine import TOKEN
    base=store.ROOT/'_quarentena';items=[]
    if base.is_dir() and not base.is_symlink():
        for folder in base.iterdir():
            if folder.is_symlink() or not TOKEN.fullmatch(folder.name):continue
            try:
                index=folder/'quarantine.json'
                if index.is_symlink():continue
                data=json.loads(index.read_text(encoding='utf-8'))
                if data.get('state')=='quarantined':items.append({'id':folder.name,'name':data['name'],'category':data['category'],'created':data['created_epoch'],'expires':data['created_epoch']+30*86400})
            except (OSError,ValueError,KeyError):continue
    return {'items':items,'retention_days':30}

class RestoreQuarantine(_BM):
    token:str=Field(pattern=r'^\d{8}_\d{6}_[a-f0-9]{8}$')

@router.post('/api/limpeza/quarentena/restaurar')
def quarantine_restore(body:RestoreQuarantine):
    from ..quarantine import restore
    with dispatch_lock:
        with store.connect() as c:busy=c.execute("SELECT id FROM jobs WHERE state IN ('queued','running','cancel_requested') LIMIT 1").fetchone()
        if busy:raise HTTPException(409,'Aguarde o processamento antes de restaurar arquivos.')
        inst,vid=_paths()
        try:return {'restored':restore(store.ROOT/'_quarentena',body.token,[store.ROOT,inst,vid])}
        except (ValueError,OSError) as error:raise HTTPException(422,str(error))
