import os,json,sqlite3,uuid,threading,time
from pathlib import Path
def install_root():
    """Pasta principal da instalação (1.32: <raiz>/sistema/programa/app; 1.8–1.31: <raiz>/suporte/sistema/app)."""
    base=Path(__file__).resolve().parents[1]
    if base.name=='programa' and base.parent.name=='sistema':return base.parents[1]
    if base.name=='sistema' and base.parent.name=='suporte':return base.parents[1]
    return None
def default_root():
    r=install_root()
    return r/'projetos' if r is not None else Path(__file__).resolve().parents[1]/'dados'
ROOT=Path(os.environ.get('RODOVIA_DATA') or default_root()).resolve();ROOT.mkdir(parents=True,exist_ok=True)
INSTALL=install_root() if not os.environ.get('RODOVIA_DATA') else None
def videos_root():
    """1.32: vídeos gerados (um arquivo por geração). Instalação: <raiz>/videos; desenvolvimento/testes: <dados>/_videos."""
    if os.environ.get('RODOVIA_VIDEOS'):return Path(os.environ['RODOVIA_VIDEOS']).resolve()
    return INSTALL/'videos' if INSTALL is not None else ROOT/'_videos'
def system_root():
    """Pasta 'sistema' (logs, backups, documentação). None fora de uma instalação."""
    if INSTALL is None:return None
    return INSTALL/'sistema' if (INSTALL/'sistema').is_dir() else INSTALL/'suporte'
DB=ROOT/'studio.sqlite3'
def connect():
    c=sqlite3.connect(DB,timeout=30);c.row_factory=sqlite3.Row;return c

def init():
    with connect() as c:
        c.executescript('CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY,name TEXT,created TEXT DEFAULT CURRENT_TIMESTAMP); CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,project TEXT,kind TEXT,state TEXT,progress REAL DEFAULT 0,message TEXT,error TEXT,created TEXT DEFAULT CURRENT_TIMESTAMP);')
init()
def directory(pid):
    if len(pid)!=32 or any(x not in '0123456789abcdef' for x in pid):raise ValueError('Identificador inválido.')
    p=ROOT/pid
    if p.is_symlink() or not p.is_dir():raise FileNotFoundError('Pasta do projeto ausente ou inválida. Localize a pasta original; não foi criado um projeto vazio.')
    return p

def replace(src,dst,attempts=25):
    # OneDrive, antivírus ou um player com o arquivo aberto bloqueiam a troca por instantes no Windows.
    for k in range(attempts):
        try:return Path(src).replace(dst)
        except PermissionError:
            if k==attempts-1:raise PermissionError(f'Arquivo em uso: {Path(dst).name}. Feche-o (player, OneDrive) e tente novamente.')
            time.sleep(.2)
def _atomic_write_json(file,data):
    """Grava JSON atomicamente e só substitui o arquivo válido anterior depois de reler o temporário.

    Mantém exatamente o mesmo formato/pasta das versões-base; a blindagem acontece somente durante a troca.
    """
    file=Path(file)
    text=json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)
    # Não repetir o nome de destino: hashes de histórico + UUID ultrapassavam MAX_PATH no Windows.
    # .wip não entra na limpeza comum de .tmp enquanto uma gravação estiver em andamento.
    for attempt in range(3):
        tmp=file.with_name('.rs-'+uuid.uuid4().hex+'.wip')
        try:
            file.parent.mkdir(parents=True,exist_ok=True)
            with tmp.open('x+',encoding='utf-8',newline='\n') as stream:
                stream.write(text);stream.flush();os.fsync(stream.fileno())
                stream.seek(0);json.load(stream)
            replace(tmp,file)
            return
        except FileNotFoundError as exc:
            if attempt==2:
                raise FileNotFoundError('Não foi possível concluir a gravação de '+file.name+'. A versão anterior foi preservada. Confira se a pasta está disponível localmente e se o sincronizador não a está movendo.') from exc
            time.sleep(.05*(attempt+1))
        finally:
            try:tmp.unlink(missing_ok=True)
            except OSError:pass

def update(job,**fields):
    if not fields:return
    with connect() as c:c.execute('UPDATE jobs SET '+','.join(k+'=?' for k in fields)+' WHERE id=?',list(fields.values())+[job])
def job(jid):
    with connect() as c:r=c.execute('SELECT * FROM jobs WHERE id=?',(jid,)).fetchone()
    if not r:raise FileNotFoundError('Tarefa não encontrada.')
    return dict(r)


def write_json(file,data):
    file=Path(file)
    if file.name=='config.json':
        from .project_state import save_config
        return save_config(file.parent,data)
    return _atomic_write_json(file,data)
