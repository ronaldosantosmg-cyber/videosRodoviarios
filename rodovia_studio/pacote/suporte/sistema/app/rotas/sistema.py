"""1.32: atualização pelo próprio aplicativo (Arquivo › Atualizar)."""
import os,sys,subprocess,threading,time
from pathlib import Path
from fastapi import APIRouter,HTTPException
from .. import store
from .comum import VERSION,BASE,dispatch_lock
router=APIRouter()

def _modo():
    if store.INSTALL is None:return 'desenvolvimento'
    return 'exe' if os.environ.get('RODOVIA_PORT_FILE') else 'cmd'

@router.get('/api/atualizacao')
def update_info():
    """ZIPs de atualização encontrados (pasta atualizacoes, raiz e Downloads) e a versão instalada."""
    sys.path.insert(0,str(BASE))
    try:import atualizador as U
    finally:sys.path.pop(0)
    root=store.INSTALL;found=[]
    if root is not None:
        cur=U.version_tuple(VERSION)
        for ver,z,_ in U.candidates(root):found.append({'arquivo':z.name,'pasta':str(z.parent),'versao':'.'.join(map(str,ver)),'mais_nova':ver>cur})
    rollbacks=U.rollback_candidates(root) if root is not None else []
    return {'instalada':VERSION,'modo':_modo(),'encontradas':found,'pode_atualizar':any(f['mais_nova'] for f in found),'pasta_atualizacoes':str((root or store.ROOT)/'atualizacoes'),'rollback':rollbacks[0] if rollbacks else None}

@router.post('/api/atualizacao/aplicar')
def update_apply():
    """Fecha o aplicativo e roda o atualizador numa janela própria; ao terminar, abre o Rodovia Studio de novo."""
    info=update_info()
    if not info['pode_atualizar']:raise HTTPException(409,'Nenhuma atualização mais nova encontrada.')
    if info['modo']!='cmd':raise HTTPException(409,'Aberto pelo Rodovia Studio.exe: use o ícone perto do relógio › “Procurar e aplicar atualização”.' if info['modo']=='exe' else 'Atualização automática só na instalação do Windows.')
    with store.connect() as c:
        if c.execute("SELECT id FROM jobs WHERE state IN ('queued','running','cancel_requested') LIMIT 1").fetchone():raise HTTPException(409,'Termine ou cancele a tarefa em andamento antes de atualizar.')
    root=store.INSTALL;prog=BASE;logs=(store.system_root() or root)/'logs';logs.mkdir(parents=True,exist_ok=True)
    main=root/'Rodovia Studio.exe'
    if not main.exists():main=root/'ABRIR RODOVIA STUDIO.cmd'
    if not main.exists():main=root/'sistema'/'ABRIR RODOVIA STUDIO.cmd'
    bat=logs/'atualizar_pelo_aplicativo.cmd'
    bat.write_text('\r\n'.join(['@echo off','title Atualizando o Rodovia Studio','echo Aguardando o Rodovia Studio fechar e aplicando a atualizacao...',
        f'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "{prog/"atualizar.ps1"}" -Raiz "{root}" -Aguardar 90',
        'if errorlevel 1 (echo. & echo A atualizacao nao foi aplicada. Veja a mensagem acima. & pause & exit /b 1)',
        'echo Abrindo o Rodovia Studio...',
        f'start "" "{main}"',
        # o .cmd principal pode ter ido para "sistema" durante a atualização
        f'if not exist "{main}" start "" "{root/"sistema"/"ABRIR RODOVIA STUDIO.cmd"}"','exit /b 0',''])+'\r\n',encoding='ascii',errors='replace')
    if os.name=='nt':
        subprocess.Popen(['cmd','/c',str(bat)],cwd=str(root),creationflags=getattr(subprocess,'CREATE_NEW_CONSOLE',0x10),close_fds=True)
        threading.Timer(1.5,lambda:os._exit(0)).start()   # libera os arquivos para o atualizador
    return {'iniciado':os.name=='nt','script':str(bat)}

@router.post('/api/atualizacao/restaurar')
def update_restore():
    """Fecha o aplicativo, restabelece o backup anterior e abre novamente."""
    info=update_info();rb=info.get('rollback')
    if not rb:raise HTTPException(409,'Nenhuma versão anterior disponível para restabelecer.')
    if info['modo']!='cmd':raise HTTPException(409,'Restabelecimento automático disponível na instalação Windows aberta pelo comando principal.')
    with store.connect() as c:
        if c.execute("SELECT id FROM jobs WHERE state IN ('queued','running','cancel_requested') LIMIT 1").fetchone():raise HTTPException(409,'Termine ou cancele a tarefa em andamento antes de restabelecer a versão.')
    root=store.INSTALL;prog=BASE;logs=(store.system_root() or root)/'logs';logs.mkdir(parents=True,exist_ok=True)
    main=root/'Rodovia Studio.exe'
    if not main.exists():main=root/'ABRIR RODOVIA STUDIO.cmd'
    if not main.exists():main=root/'sistema'/'ABRIR RODOVIA STUDIO.cmd'
    bat=logs/'restaurar_versao_anterior.cmd'
    cmd=f'"{sys.executable}" "{prog/"atualizador.py"}" --raiz "{root}" --restaurar-anterior --backup "{rb["path"]}" --sem-verificar-aberto'
    bat.write_text('\r\n'.join(['@echo off','title Restabelecendo o Rodovia Studio','echo Restabelecendo a versao anterior...',cmd,
        'if errorlevel 1 (echo. & echo A versao anterior nao foi restabelecida. & pause & exit /b 1)',
        'echo Abrindo o Rodovia Studio...',f'start "" "{main}"',f'if not exist "{main}" start "" "{root/"sistema"/"ABRIR RODOVIA STUDIO.cmd"}"','exit /b 0',''])+'\r\n',encoding='ascii',errors='replace')
    if os.name=='nt':
        subprocess.Popen(['cmd','/c',str(bat)],cwd=str(root),creationflags=getattr(subprocess,'CREATE_NEW_CONSOLE',0x10),close_fds=True)
        threading.Timer(1.5,lambda:os._exit(0)).start()
    return {'iniciado':os.name=='nt','backup':rb}
