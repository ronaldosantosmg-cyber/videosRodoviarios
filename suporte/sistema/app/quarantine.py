"""Quarentena restaurável: exclusão definitiva somente após 30 dias de retenção."""
import json,os,re,shutil,time,uuid
from pathlib import Path

DAY=86400
TOKEN=re.compile(r'^\d{8}_\d{6}_[a-f0-9]{8}$')


def _safe(base,path):
    base=Path(base).absolute();path=Path(path).absolute()
    if base.is_symlink() or path==base or not path.is_relative_to(base):return False
    while path!=base:
        if path.is_symlink():return False
        path=path.parent
    return True


def move(path,base,category='residuo',now=None):
    path=Path(path).absolute();base=Path(base).absolute();now=time.time() if now is None else now
    if path.is_symlink() or not path.exists() or base==path or base.is_relative_to(path):raise ValueError('Caminho de quarentena inválido.')
    base.mkdir(parents=True,exist_ok=True)
    if base.is_symlink():raise ValueError('Quarentena não pode ser um link.')
    token=time.strftime('%Y%m%d_%H%M%S',time.localtime(now))+'_'+uuid.uuid4().hex[:8]
    batch=base/token;batch.mkdir();target=batch/'data'
    manifest={'created_epoch':now,'retention_days':30,'source':str(path),'category':category,'name':path.name,'state':'planned'}
    index=batch/'quarantine.json';index.write_text(json.dumps(manifest,ensure_ascii=False),encoding='utf-8')
    try:
        shutil.move(str(path),str(target));manifest['state']='quarantined'
        index.write_text(json.dumps(manifest,ensure_ascii=False),encoding='utf-8')
    except Exception:
        # O manifesto planejado permite recuperar uma movimentação interrompida.
        raise
    return token


def restore(base,token,roots):
    base=Path(base).absolute()
    if not TOKEN.fullmatch(token):raise ValueError('Identificador de quarentena inválido.')
    batch=base/token
    if not _safe(base,batch) or batch.is_symlink():raise ValueError('Lote de quarentena inválido.')
    record=json.loads((batch/'quarantine.json').read_text(encoding='utf-8'))
    target=Path(record['source']).absolute();source=batch/'data'
    if not any(_safe(root,target) for root in roots if root is not None):raise ValueError('Destino fora das pastas autorizadas.')
    if not _safe(batch,source) or not source.exists():raise ValueError('Conteúdo da quarentena ausente.')
    if target.exists():raise ValueError('O destino já existe; restauração não sobrescreve arquivos.')
    target.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(source),str(target))
    record['state']='restored';(batch/'quarantine.json').write_text(json.dumps(record,ensure_ascii=False),encoding='utf-8')
    return str(target)


def purge(base,now=None,execute=False):
    base=Path(base).absolute();now=time.time() if now is None else now;removed=[];errors=[]
    if base.is_symlink() or not base.is_dir():return {'removed':removed,'errors':errors}
    for batch in base.iterdir():
        if not TOKEN.fullmatch(batch.name) or not _safe(base,batch) or not batch.is_dir():continue
        try:
            index=batch/'quarantine.json'
            if index.is_symlink():continue
            record=json.loads(index.read_text(encoding='utf-8'));created=float(record['created_epoch'])
            if record.get('state') not in ('quarantined','restored') or not 0<=created<=now or now-created<30*DAY:continue
            if execute:shutil.rmtree(batch)
            removed.append(batch.name)
        except (OSError,ValueError,KeyError) as exc:errors.append(batch.name+': '+str(exc))
    return {'removed':removed,'errors':errors,'executed':execute}
