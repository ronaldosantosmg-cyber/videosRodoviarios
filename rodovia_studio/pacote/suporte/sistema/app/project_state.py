"""Persistência do projeto: trava entre processos, revisão, histórico e recuperação."""
import os,json,time,uuid,threading,contextlib,hashlib,shutil
from pathlib import Path

_locks={};_guard=threading.Lock();_local=threading.local()
class Conflict(ValueError):pass

def canonical(data):return json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def revision(data):return hashlib.sha256(canonical(data)).hexdigest()
def _json(path):return json.loads(Path(path).read_text(encoding='utf-8'),parse_constant=lambda x:(_ for _ in ()).throw(ValueError('JSON não finito: '+x)))
def _write(path,data):
    from .store import _atomic_write_json
    return _atomic_write_json(path,data)
def _state(d):
    base=Path(d)/'.estado'
    if base.is_symlink():raise ValueError('Pasta de estado não pode ser um link simbólico.')
    base.mkdir(exist_ok=True);return base

@contextlib.contextmanager
def locked(directory):
    source=Path(directory)
    if source.is_symlink() or not source.is_dir():raise FileNotFoundError('Pasta do projeto ausente ou inválida. Localize a pasta original; nenhum projeto vazio foi criado.')
    d=source.resolve();key=str(d)
    with _guard:lock=_locks.setdefault(key,threading.RLock())
    with lock:
        depths=getattr(_local,'depths',{});_local.depths=depths
        if depths.get(key,0):
            depths[key]+=1
            try:yield
            finally:depths[key]-=1
            return
        path=_state(d)/'projeto.lock'
        if path.is_symlink():raise ValueError('Trava do projeto não pode ser um link.')
        with path.open('a+b') as stream:
            if os.name=='nt':
                import msvcrt
                stream.seek(0);stream.write(b'0');stream.flush();start=time.monotonic()
                while True:
                    try:stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1);break
                    except OSError:
                        if time.monotonic()-start>15:raise TimeoutError('Projeto ocupado por outra gravação. Tente novamente.')
                        time.sleep(.05)
            else:
                import fcntl
                fcntl.flock(stream.fileno(),fcntl.LOCK_EX)
            depths[key]=1
            try:yield
            finally:
                depths.pop(key,None)
                if os.name=='nt':stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
                else:fcntl.flock(stream.fileno(),fcntl.LOCK_UN)

def _snapshot(d,data):
    base=_state(d)/'historico';base.mkdir(exist_ok=True)
    if base.is_symlink():raise ValueError('Histórico não pode ser um link.')
    key=revision(data);path=base/(key+'.json')
    if path.is_symlink():raise ValueError('Cópia de configuração não pode ser um link.')
    if not path.exists():_write(path,data)
    return key

def _prune(d,current,previous):
    folder=_state(d)/'historico';files=sorted(folder.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True);total=0
    for i,f in enumerate(files):
        if f.is_symlink() or len(f.stem)!=64:continue
        total+=f.stat().st_size
        if f.stem not in (current,previous) and (i>=20 or total>64*1024*1024):f.unlink()

def _recover_import(d):
    marker=_state(d)/'importacao_pendente.json'
    if not marker.exists():return
    data=_json(marker);folder=_state(d)/'importacoes'/data['id']
    if len(data['id'])!=32 or any(c not in '0123456789abcdef' for c in data['id']):raise ValueError('Registro de importação inválido.')
    if folder.is_symlink() or folder.parent.is_symlink():raise ValueError('Pasta de recuperação inválida.')
    if data.get('state')!='committed':
        for row in data['files']:
            name=row['name']
            if name not in ('input.dxf','input.kmz','input.dwg','config.json','arquivos.json'):raise ValueError('Caminho de recuperação inválido.')
            target=Path(d)/name;backup=folder/name
            if row['existed']:
                if not backup.is_file() or backup.is_symlink() or _file_hash(backup)!=row['sha256']:raise ValueError('Cópia de recuperação da importação está incompleta.')
        for row in data['files']:
            target=Path(d)/row['name'];backup=folder/row['name']
            if row['existed']:
                temp=target.with_name(target.name+'.restaurar-'+uuid.uuid4().hex);shutil.copy2(backup,temp);os.replace(temp,target)
            else:target.unlink(missing_ok=True)
    marker.unlink()

def read_config(directory):
    from .models import Settings
    d=Path(directory)
    with locked(d):
        _recover_import(d);base=_state(d);path=d/'config.json'
        if path.is_symlink():raise ValueError('Configuração não pode ser um link simbólico.')
        try:
            data=_json(path);Settings.model_validate(data);key=revision(data)
        except (ValueError,FileNotFoundError,UnicodeError,TypeError):
            try:meta=_json(base/'config_atual.json') if (base/'config_atual.json').exists() else {}
            except (ValueError,UnicodeError):raise ValueError('Configuração e índice de recuperação inválidos. Abra Proteção de dados para escolher uma cópia conferida.')
            key=meta.get('revision','')
            if len(key)!=64 or any(c not in '0123456789abcdef' for c in key):raise ValueError('Configuração inválida e não há cópia válida registrada para recuperação.')
            saved=base/'historico'/(key+'.json')
            if saved.is_symlink() or saved.parent.is_symlink():raise ValueError('Cópia de recuperação inválida.')
            data=_json(saved)
            if revision(data)!=key:raise ValueError('A cópia da configuração falhou na conferência.')
            Settings.model_validate(data)
            bad=base/'corrompidos'
            if bad.is_symlink():raise ValueError('Pasta de recuperação inválida.')
            bad.mkdir(exist_ok=True)
            if path.exists():shutil.copy2(path,bad/('config_'+uuid.uuid4().hex+'.json'))
            _write(path,data);_write(base/'recuperacao.json',{'revision':key,'time':time.time(),'message':'Configuração recuperada da última gravação válida.'})
        _snapshot(d,data)
        pointer=base/'config_atual.json'
        try:known=_json(pointer).get('revision')
        except (ValueError,OSError):known=None
        if known!=key:_write(pointer,{'revision':key,'time':time.time()})
        (base/'config_pendente.json').unlink(missing_ok=True)
        return data

def save_config(directory,data,expected=None):
    from .models import Settings
    d=Path(directory);data=data.model_dump() if hasattr(data,'model_dump') else data
    Settings.model_validate(data);key=revision(data)
    with locked(d):
        base=_state(d);old=read_config(d) if (d/'config.json').exists() or (base/'config_atual.json').exists() or (base/'historico').exists() else None;previous=revision(old) if old is not None else None
        if expected is not None and expected.strip('"')!=previous:raise Conflict('O projeto foi alterado em outra janela. Reabra a versão atual antes de salvar; suas alterações locais foram mantidas.')
        if key==previous:return {'revision':key,'previous':previous,'changed':False}
        if old is not None:_snapshot(d,old)
        _snapshot(d,data);_write(base/'config_pendente.json',{'previous':previous,'next':key})
        _write(d/'config.json',data);_write(base/'config_atual.json',{'revision':key,'time':time.time()});(base/'config_pendente.json').unlink(missing_ok=True)
        _prune(d,key,previous)
        return {'revision':key,'previous':previous,'changed':True}

def state(directory):
    from .dependencies import revisions
    from .artifacts import status
    d=Path(directory)
    with locked(d):
        data=read_config(d);keys=revisions(d,data)
        recovery=_json(_state(d)/'recuperacao.json') if (_state(d)/'recuperacao.json').exists() else None
        return {'config':data,'config_revision':revision(data),'revisions':keys,'artifacts':status(d,keys),'recovery':recovery}

def history(directory):
    d=Path(directory)
    with locked(d):
        read_config(d);out=[]
        for f in (_state(d)/'historico').glob('*.json'):
            if not f.is_symlink():out.append({'revision':f.stem,'bytes':f.stat().st_size,'modified':f.stat().st_mtime})
        return sorted(out,key=lambda r:r['modified'],reverse=True)

def restore(directory,key,expected):
    d=Path(directory)
    if len(key)!=64 or any(c not in '0123456789abcdef' for c in key):raise ValueError('Revisão de recuperação inválida.')
    with locked(d):
        path=_state(d)/'historico'/(key+'.json')
        if path.is_symlink():raise ValueError('Cópia de recuperação inválida.')
        data=_json(path)
        if revision(data)!=key:raise ValueError('Cópia de recuperação alterada.')
        return save_config(d,data,expected)


def _file_hash(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk:=stream.read(1024*1024):h.update(chunk)
    return h.hexdigest()


def import_files(directory,replacements,metadata):
    """Valida antes desta chamada; publica entradas, identidade e metadados juntos.

    O diário permite reverter mesmo após encerramento entre duas trocas de arquivo.
    As fontes anteriores ficam na cópia da transação para recuperação.
    """
    d=Path(directory)
    allowed={'input.dxf','input.kmz','input.dwg'}
    if not replacements or not set(replacements)<=allowed:raise ValueError('Arquivos de importação inválidos.')
    with locked(d):
        config=read_config(d);config['coordinates_confirmed']=False
        identity=uuid.uuid4().hex;folder=_state(d)/'importacoes'/identity
        folder.mkdir(parents=True);rows=[]
        for name in (*replacements,'config.json','arquivos.json'):
            source=d/name
            if source.is_symlink():raise ValueError('Arquivo do projeto não pode ser um link.')
            row={'name':name,'existed':source.exists()}
            if source.exists():
                shutil.copy2(source,folder/name);row['sha256']=_file_hash(folder/name)
            rows.append(row)
        marker=_state(d)/'importacao_pendente.json'
        _write(marker,{'id':identity,'state':'prepared','files':rows})
        try:
            for name,source in replacements.items():
                if source is None:(d/name).unlink(missing_ok=True)
                else:os.replace(source,d/name)
            # Não chama save_config durante um diário de importação aberto.
            _snapshot(d,config);_write(d/'config.json',config);_write(d/'arquivos.json',metadata)
            _write(marker,{'id':identity,'state':'committed','files':rows})
            marker.unlink();read_config(d)
        except BaseException:
            _recover_import(d)
            raise
