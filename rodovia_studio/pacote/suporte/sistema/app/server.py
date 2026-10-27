"""Rodovia Studio — servidor local (FastAPI).

Aqui ficam só a criação do aplicativo, o despachante de tarefas, a segurança (somente local) e o tratamento
de erros. As rotas da API estão em app/rotas/<assunto>.py (1.31). Veja ARQUITETURA.md.
"""
import asyncio,json,os,sys,uuid,shutil,subprocess,threading,time,zipfile,re
from xml.etree.ElementTree import ParseError as ET_ERRORS
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI,UploadFile,File,HTTPException,Request
from pydantic import BaseModel as _BM,ConfigDict,Field
from fastapi.responses import HTMLResponse,FileResponse,JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from . import store
from .models import Settings
from .render import ASSETS
from .rotas.comum import BASE,VERSION,idle,enqueue,stop,dispatch_lock,maintenance_pending
def dispatcher():
    while not stop.is_set():
        from .capture3d import active as capture_active
        if capture_active():stop.wait(.2);continue
        with store.connect() as c:r=c.execute("SELECT * FROM jobs WHERE state='queued' ORDER BY created,rowid LIMIT 1").fetchone()
        if not r:stop.wait(.4);continue
        j=dict(r)
        with dispatch_lock:
            if maintenance_pending.is_set() or store.job(j['id'])['state']!='queued':continue
            store.update(j['id'],state='running',message='Iniciando')
        # Erros que derrubam o processo (memória, DLL, importação) ficam em worker.log do projeto.
        try:wlog=open(store.ROOT/j['project']/'worker.log','ab')
        except OSError:wlog=subprocess.DEVNULL
        try:
            proc=subprocess.Popen([sys.executable,'-m','app.worker',j['id']],cwd=BASE,stdout=wlog,stderr=wlog,start_new_session=os.name!='nt')
        except Exception as e:
            # Falha ao criar o worker não pode matar o despachante nem travar as tarefas seguintes.
            store.update(j['id'],state='failed',message='Não foi possível iniciar a operação.',error=f'{type(e).__name__}: {str(e)[:1000]}')
            try:
                from .execlog import write
                write(store.ROOT/j['project'],'erros','worker_nao_iniciado',erro=type(e).__name__,mensagem=str(e)[:2000])
            except Exception:pass
            continue
        finally:
            if wlog is not subprocess.DEVNULL:wlog.close()
        from .process_supervision import stop_process,heartbeat_path
        heartbeat=heartbeat_path(store.ROOT/j['project'],j['id']);started=time.monotonic();cancel_since=None;forced=None
        while proc.poll() is None:
            if stop.wait(.2):stop_process(proc,tree=True);break
            state=store.job(j['id'])['state']
            if state=='cancel_requested':
                cancel_since=cancel_since or time.monotonic()
                if time.monotonic()-cancel_since>30:
                    stop_process(proc,tree=True);forced='cancelled';break
            try:silence=time.time()-heartbeat.stat().st_mtime
            except FileNotFoundError:silence=time.monotonic()-started
            # Não é limite da duração do cálculo: o sinal de vida continua durante etapas longas.
            if silence>600:
                stop_process(proc,tree=True);forced='failed';break
        heartbeat.unlink(missing_ok=True)
        state=store.job(j['id'])['state']
        if state in ['running','cancel_requested']:
            store.update(j['id'],state=forced or 'interrupted',message='Cancelado por supervisão; arquivos originais preservados.' if forced=='cancelled' else 'Processo sem resposta ou interrompido. Consulte o log e gere novamente.')

@asynccontextmanager
async def lifespan(app):
    stop.clear();maintenance_pending.clear()
    from .imagery_cache import session_temp,prune_orphan_temps,cleanup_session
    # 1.40.7: descarta resíduos de sessões anteriores e cria um temporário exclusivo desta execução.
    prune_orphan_temps(max_age_seconds=0);session_temp()
    with store.connect() as c:c.execute("UPDATE jobs SET state='interrupted',message='Aplicação reiniciada. Inicie a tarefa novamente.' WHERE state IN ('running','cancel_requested')")
    thread=threading.Thread(target=dispatcher,daemon=True);thread.start()
    try:
        started=float(os.environ.get('RODOVIA_BOOT_MONOTONIC',time.monotonic()))
        elapsed=time.monotonic()-started
        import math
        if math.isfinite(elapsed) and elapsed>=0:
            app.state.startup_seconds=round(elapsed,3)
            from .execlog import write
            system=store.ROOT/'_sistema';system.mkdir(exist_ok=True)
            write(system,'execucao','inicializacao',duracao_s=app.state.startup_seconds,versao=VERSION)
    except (ValueError,OSError):pass
    try:
        yield
    finally:
        stop.set()
        from .small_ai import cancel as cancel_ai
        cancel_ai()
        from .capture3d import abort_all
        abort_all();thread.join(timeout=5)
        # Workers já foram encerrados. Agora temporários de projeto e da sessão podem sair com segurança.
        try:
            from .maintenance import clean_categories
            clean_categories(store.ROOT,['temporarios'],install=store.INSTALL,videos=store.videos_root())
        except Exception:pass
        cleanup_session()
app=FastAPI(title='Rodovia Studio',version=VERSION,lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost','testserver'])
@app.middleware('http')
async def local_only(request:Request,call_next):
    origin=request.headers.get('origin','')
    if request.method not in ['GET','HEAD','OPTIONS'] and origin:
        from urllib.parse import urlsplit
        parsed=urlsplit(origin)
        if parsed.hostname not in ['localhost','127.0.0.1','testserver'] or (parsed.port or (443 if parsed.scheme=='https' else 80))!=(request.url.port or (443 if request.url.scheme=='https' else 80)):return JSONResponse({'detail':'Origem não autorizada.'},403)
    if request.method not in ['GET','HEAD','OPTIONS'] and request.headers.get('sec-fetch-site')=='cross-site':return JSONResponse({'detail':'Requisição externa recusada.'},403)
    return await call_next(request)
@app.exception_handler(Exception)
async def unexpected(request,e):
    """1.26: erro inesperado do servidor vai para o registro de erros do projeto (quando a rota é de um projeto)."""
    import traceback
    m=re.match(r'^/api/projects/([0-9a-f]{32})/',request.url.path)
    if m:
        try:
            from .execlog import write
            write(store.directory(m.group(1)),'erros','erro_servidor',rota=request.url.path,metodo=request.method,erro=type(e).__name__,mensagem=str(e)[:2000],rastreamento=traceback.format_exc()[-12000:])
        except Exception:pass
    return JSONResponse({'detail':f'Erro interno ({type(e).__name__}): {str(e)[:300]}'},500)
@app.exception_handler(ValueError)
async def value_error(request,e):return JSONResponse({'detail':str(e)},422)
@app.exception_handler(FileNotFoundError)
async def not_found(request,e):return JSONResponse({'detail':str(e)},404)

# 1.31: as rotas ficam em app/rotas/<assunto>.py; aqui só a criação do aplicativo, o despachante de tarefas,
# a segurança (somente local) e o tratamento de erros.
from .rotas import paginas,projetos,modelos,editor,tarefas,arquivos,web,suporte,camadas,videos,sistema,obras,modelagem,assistencia,protecao
for _m in (paginas,projetos,modelos,editor,tarefas,arquivos,web,suporte,camadas,videos,sistema,obras,modelagem,assistencia,protecao):app.include_router(_m.router)

from starlette.staticfiles import StaticFiles
app.mount('/vendor',StaticFiles(directory=BASE/'app/vendor'),name='vendor-local')
app.mount('/webgl',StaticFiles(directory=BASE/'app/webgl'),name='webgl-local')
