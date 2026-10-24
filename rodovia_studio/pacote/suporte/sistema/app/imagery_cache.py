"""Base persistente de imagens convertidas e temporários de sessão.

1.40.7
- ECW/MrSID/... convertidos ficam numa base compartilhada em projetos/_base_imagens.
- Projetos continuam usando imagem_local/<nome>.tif para compatibilidade.
- O arquivo do projeto é um hardlink para a base quando o sistema de arquivos permite;
  caso contrário, é uma cópia normal.
- Resíduos de processamento ficam em projetos/_temp e são descartáveis.
"""
from __future__ import annotations
import hashlib, json, os, shutil, time, uuid
from pathlib import Path
from . import store

BASE_NAME='_base_imagens'
TEMP_NAME='_temp'


def base_root() -> Path:
    p=store.ROOT/BASE_NAME;p.mkdir(parents=True,exist_ok=True);return p


def temp_root() -> Path:
    p=store.ROOT/TEMP_NAME;p.mkdir(parents=True,exist_ok=True);return p


def session_temp() -> Path:
    token=os.environ.get('RODOVIA_SESSION_ID') or f'{os.getpid()}_{uuid.uuid4().hex[:8]}'
    os.environ['RODOVIA_SESSION_ID']=token
    p=temp_root()/token;p.mkdir(parents=True,exist_ok=True);return p


def fingerprint(path: Path, chunk=8*1024*1024) -> str:
    """SHA-256 do arquivo. Feito uma única vez por upload, evitando falso reaproveitamento."""
    path=Path(path);h=hashlib.sha256()
    with path.open('rb') as f:
        while True:
            b=f.read(chunk)
            if not b:break
            h.update(b)
    return h.hexdigest()


def entry_paths(key: str):
    d=base_root()/key[:2]/key;d.mkdir(parents=True,exist_ok=True)
    return d,d/'imagem.tif',d/'meta.json'


def lookup(src: Path):
    key=fingerprint(src);d,tif,meta=entry_paths(key)
    if not tif.is_file() or not meta.is_file():return key,None
    try:
        m=json.loads(meta.read_text(encoding='utf-8'))
        if m.get('source_sha256')!=key or m.get('output_size')!=tif.stat().st_size:return key,None
        return key,{'dir':d,'tif':tif,'meta':m}
    except (OSError,ValueError,TypeError):return key,None


def register(src: Path, converted: Path, *, world=None, prj=None, check=None, extra=None):
    """Publica conversão validada na base sem substituir uma entrada válida já existente."""
    key=fingerprint(src);d,tif,meta=entry_paths(key)
    if not tif.exists():
        tmp=d/f'.imagem.{uuid.uuid4().hex}.tmp.tif';shutil.copy2(converted,tmp);tmp.replace(tif)
    files={}
    for name,value in [('world',world),('prj',prj)]:
        if not value:continue
        p=Path(value)
        if not p.is_absolute():p=Path(converted).parent/p
        if p.is_file():
            ext='.tfw' if name=='world' else '.prj';dst=d/('imagem'+ext)
            if not dst.exists():shutil.copy2(p,dst)
            files[name]=dst.name
    m={
        'schema':1,'source_sha256':key,'source_name':Path(src).name,
        'source_size':Path(src).stat().st_size,'output_size':tif.stat().st_size,
        'created':time.strftime('%Y-%m-%dT%H:%M:%S'),**files
    }
    if check is not None:m['check']=check
    if extra:m.update(extra)
    tmp=meta.with_suffix('.tmp');tmp.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(meta)
    return {'key':key,'dir':d,'tif':tif,'meta':m}


def materialize(entry, project_dir: Path, filename: str):
    """Materializa o GeoTIFF na estrutura antiga do projeto. Hardlink evita duplicar GB."""
    base=Path(project_dir)/'imagem_local';base.mkdir(parents=True,exist_ok=True)
    dst=base/filename
    if dst.exists():
        try:
            if os.path.samefile(dst,entry['tif']):return dst,False
        except OSError:pass
        dst.unlink()
    linked=False
    try:os.link(entry['tif'],dst);linked=True
    except OSError:shutil.copy2(entry['tif'],dst)
    meta=entry.get('meta') or {}
    for field,ext in [('world','.tfw'),('prj','.prj')]:
        n=meta.get(field)
        if n and (Path(entry['dir'])/n).is_file():
            target=base/(Path(filename).stem+ext);shutil.copy2(Path(entry['dir'])/n,target)
    return dst,linked


def prune_orphan_temps(max_age_seconds=0):
    """Remove sessões temporárias antigas. Nunca toca na base persistente nem em projetos."""
    root=temp_root();now=time.time();removed=[]
    current=os.environ.get('RODOVIA_SESSION_ID')
    for p in list(root.iterdir()) if root.exists() else []:
        if not p.is_dir() or p.name==current:continue
        try:
            if max_age_seconds<=0 or now-p.stat().st_mtime>=max_age_seconds:
                shutil.rmtree(p,ignore_errors=False);removed.append(p.name)
        except OSError:pass
    return removed


def cleanup_session():
    token=os.environ.get('RODOVIA_SESSION_ID')
    if token:
        shutil.rmtree(temp_root()/token,ignore_errors=True)
    try:
        if temp_root().exists() and not any(temp_root().iterdir()):temp_root().rmdir()
    except OSError:pass
