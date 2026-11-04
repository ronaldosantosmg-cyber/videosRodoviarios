import socket,threading,webbrowser,os,sys,json,urllib.request,traceback,time,hashlib
from pathlib import Path
os.environ['RODOVIA_BOOT_MONOTONIC']=str(time.monotonic())
import uvicorn
BASE=Path(__file__).resolve().parent

def studio_health(port):
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health',timeout=2) as r:
            data=json.loads(r.read())
            return data if isinstance(data,dict) and data.get('status')=='ok' else None
    except Exception:return None

def session_state(health,base=BASE):
    """Nunca confirma código ativo somente por VERSAO.json ou porta aberta."""
    if not health:return 'other_service'
    identity=health.get('runtime') or {};root=identity.get('program_root')
    if not root:return 'unverified_studio'
    canonical=lambda p:os.path.normcase(str(Path(p).resolve()))
    if canonical(root)!=canonical(base):return 'other_installation'
    try:
        version=json.loads((Path(base)/'VERSAO.json').read_text(encoding='utf-8'))['version']
        source=hashlib.sha256((Path(base)/'app/fleet_policy.py').read_bytes()).hexdigest()
    except (OSError,ValueError,KeyError):return 'stale_studio'
    probe=(identity.get('policy') or {}).get('probe') or {}
    if (identity.get('version_at_start')!=version or identity.get('source_fingerprint_at_start')!=source
        or identity.get('disk_changed') is not False or probe.get('ok') is not True):return 'stale_studio'
    data=os.environ.get('RODOVIA_DATA')
    if data and canonical(health.get('data') or '')!=canonical(data):return 'other_installation'
    return 'compatible'

def running_studio(port):return session_state(studio_health(port))=='compatible'

def reuse_session(port):
    print(f'O Rodovia Studio desta instalação já está aberto em http://127.0.0.1:{port}, com código conferido.');write_port(port)
    if not os.environ.get('RODOVIA_NO_BROWSER'):webbrowser.open(f'http://127.0.0.1:{port}')

def reject_stale_session(port):
    print(f'Existe uma sessão anterior ou não identificada na porta {port}. Encerre o Rodovia Studio nessa janela e abra novamente. '
          'A sessão antiga não foi reutilizada; projetos e vídeos não foram alterados.')
    raise SystemExit(1)

def free(port):
    with socket.socket() as s:
        try:s.bind(('127.0.0.1',port));return True
        except OSError:return False

def write_port(port):
    """Informa ao iniciador (.exe) a porta em uso."""
    f=os.environ.get('RODOVIA_PORT_FILE')
    if f:
        try:Path(f).parent.mkdir(parents=True,exist_ok=True);Path(f).write_text(str(port),encoding='ascii')
        except OSError:pass

def organizar_pasta():
    """1.32: raiz só com o arquivo principal e as pastas projetos, videos, atualizacoes e sistema."""
    try:
        if BASE.name=='programa' and BASE.parent.name=='sistema':
            import atualizador
            atualizador.recover_pending(BASE.parents[1],say=print)
            atualizador.organize_root(BASE.parents[1],say=print)
    except Exception as e:
        print('Não foi possível preparar a instalação com segurança:',e)
        raise SystemExit(1)

if __name__=='__main__':
    organizar_pasta()
    port=int(os.environ.get('RODOVIA_PORT','8765'))
    if not free(port):
        state=session_state(studio_health(port))
        if state=='compatible':reuse_session(port);raise SystemExit(0)
        if state in ('stale_studio','unverified_studio'):reject_stale_session(port)
        # Outro programa ocupa a porta: procura a próxima livre em vez de encerrar.
        for p in range(port+1,port+20):
            if free(p):print(f'A porta {port} está ocupada por outro programa; usando {p}.');port=p;break
            candidate=session_state(studio_health(p))
            if candidate=='compatible':reuse_session(p);raise SystemExit(0)
            if candidate=='stale_studio':reject_stale_session(p)
        else:print(f'Nenhuma porta livre entre {port} e {port+19}.');raise SystemExit(1)
    write_port(port)
    # 1.23: o Rodovia Studio.exe abre a janela por conta própria (RODOVIA_NO_BROWSER).
    if not os.environ.get('RODOVIA_NO_BROWSER'):threading.Timer(1.5,lambda:webbrowser.open(f'http://127.0.0.1:{port}')).start()
    print(f'Rodovia Studio: http://127.0.0.1:{port}\nMantenha esta janela aberta durante a geração. Ctrl+C encerra o aplicativo.')
    try:
        from app.server import app
        server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='info'))
        app.state.request_shutdown=lambda:setattr(server,'should_exit',True)
        server.run()
    except Exception:
        # Registra a causa no log de instalação para diagnóstico.
        with open(BASE/'servidor_erro.log','a',encoding='utf-8') as f:f.write(time.strftime('%Y-%m-%d %H:%M:%S ')+traceback.format_exc()+'\n')
        traceback.print_exc();raise SystemExit(1)
