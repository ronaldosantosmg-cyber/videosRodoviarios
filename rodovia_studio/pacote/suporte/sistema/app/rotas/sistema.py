"""1.32: atualização pelo próprio aplicativo (Arquivo › Atualizar)."""
import os,sys,subprocess,threading,time,hmac
from fastapi import Request
from pathlib import Path
from fastapi import APIRouter,HTTPException
from .. import store
from .comum import VERSION,BASE,dispatch_lock,maintenance_pending
router=APIRouter()

def _modo():
    if store.INSTALL is None:return 'desenvolvimento'
    return 'exe' if os.environ.get('RODOVIA_PORT_FILE') else 'cmd'

@router.get('/api/atualizacao')
def update_info():
    """ZIPs encontrados exclusivamente em atualizacoes/ e a versão instalada."""
    sys.path.insert(0,str(BASE))
    try:import atualizador as U
    finally:sys.path.pop(0)
    root=store.INSTALL;found=[]
    if root is not None:
        cur=U.version_tuple(VERSION)
        for ver,z,_,_ in U.candidates(root):found.append({'arquivo':z.name,'pasta':str(z.parent),'versao':'.'.join(map(str,ver)),'mais_nova':ver>cur})
    rollbacks=U.rollback_candidates(root) if root is not None else []
    return {'instalada':VERSION,'modo':_modo(),'encontradas':found,'pode_atualizar':any(f['mais_nova'] for f in found),'pasta_atualizacoes':str((root or store.ROOT)/'atualizacoes'),'rollback':next((r for r in rollbacks if not r['restored']),None)}

def _ensure_idle():
    if maintenance_pending.is_set():raise HTTPException(409,'Uma atualização já está sendo preparada.')
    with store.connect() as c:
        if c.execute("SELECT id FROM jobs WHERE state IN ('queued','running','cancel_requested') LIMIT 1").fetchone():
            raise HTTPException(409,'Termine ou cancele a tarefa em andamento antes de atualizar.')


def _shutdown_callback(request):
    callback=getattr(request.app.state,'request_shutdown',None)
    if not callable(callback):raise HTTPException(409,'O encerramento controlado não está disponível nesta sessão.')
    return callback


@router.get('/api/atualizacao/pronto')
def update_ready():
    with dispatch_lock:_ensure_idle()
    return {'pronto':True}


@router.post('/api/sessao/encerrar')
def close_session(request:Request):
    # Apenas o iniciador que criou este servidor conhece o token da sessão.
    token=os.environ.get('RODOVIA_CONTROL_TOKEN','')
    supplied=request.headers.get('X-Rodovia-Control','')
    if not token or not hmac.compare_digest(token,supplied):raise HTTPException(403,'Controle da sessão não autorizado.')
    callback=_shutdown_callback(request)
    with dispatch_lock:
        _ensure_idle();maintenance_pending.set()
    threading.Timer(.4,callback).start()
    return {'encerrando':True}


def _launch_operation(request,restore=False):
    info=update_info()
    if info['modo']=='desenvolvimento' or os.name!='nt':
        raise HTTPException(409,'Atualização automática disponível na instalação Windows.')
    if restore and not info.get('rollback'):raise HTTPException(409,'Nenhuma versão anterior disponível para restabelecer.')
    if not restore and not info['pode_atualizar']:raise HTTPException(409,'Nenhuma atualização mais nova encontrada.')
    root=store.INSTALL
    with dispatch_lock:
        _ensure_idle()
        if info['modo']=='exe':
            # O iniciador salva a janela, encerra sua sessão e só então inicia a troca.
            signal=(store.system_root() or root)/'logs'/'solicitar_atualizacao.json'
            signal.parent.mkdir(parents=True,exist_ok=True)
            store.write_json(signal,{'operacao':'restaurar' if restore else 'atualizar'})
            return {'iniciado':True,'aguardando_iniciador':True}
        callback=_shutdown_callback(request)
        args=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(BASE/'atualizar.ps1'),'-Raiz',str(root),'-Aguardar','90']
        if restore:args+=['-RestaurarAnterior','-Backup',info['rollback']['path']]
        # Argumentos Unicode preservados; sem .cmd interpolado nem encoding ASCII.
        subprocess.Popen(args,cwd=str(root),creationflags=getattr(subprocess,'CREATE_NEW_CONSOLE',0x10),close_fds=True)
        maintenance_pending.set()
        threading.Timer(.5,callback).start()
    return {'iniciado':True,'reabrir_apos_conclusao':True}


@router.post('/api/atualizacao/aplicar')
def update_apply(request:Request):
    return _launch_operation(request)


@router.post('/api/atualizacao/restaurar')
def update_restore(request:Request):
    return _launch_operation(request,restore=True)
