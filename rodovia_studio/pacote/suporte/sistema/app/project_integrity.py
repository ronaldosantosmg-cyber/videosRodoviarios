"""Inspeção não destrutiva e recuperação explícita por cópia conferida."""
import hashlib,json,time,uuid,shutil,re
from pathlib import Path
from .project_state import locked,revision,_json,_write,Conflict
from .models import Settings

def stamp(path):
    if path.is_symlink():raise ValueError('Arquivo de proteção não pode ser um link.')
    if not path.exists():return 'missing'
    if path.stat().st_size>16*1024*1024:raise ValueError('Arquivo de configuração excede 16 MiB.')
    return hashlib.sha256(path.read_bytes()).hexdigest()

def inspect(d):
    d=Path(d)
    if d.is_symlink() or not d.is_dir():raise FileNotFoundError('Pasta original ausente; não criar projeto vazio.')
    issues=[];copies=[];config=None;file=d/'config.json';signature=stamp(file)
    try:
        config=_json(file);Settings.model_validate(config)
    except (OSError,ValueError,UnicodeError,TypeError) as error:
        config=None;issues.append({'file':'config.json','cause':str(error)[:300],'action':'Escolher cópia válida abaixo; preservar o arquivo defeituoso.'})
    base=d/'.estado';history=base/'historico'
    if base.is_symlink() or history.is_symlink():raise ValueError('Histórico de recuperação inválido.')
    if history.is_dir():
        for f in sorted(history.glob('*.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:100]:
            if f.is_symlink() or not re.fullmatch('[0-9a-f]{64}',f.stem):continue
            try:
                if f.stat().st_size>16*1024*1024:continue
                data=_json(f);Settings.model_validate(data)
                if revision(data)!=f.stem:continue
                copies.append({'revision':f.stem,'name':data.get('name'),'modified':f.stat().st_mtime})
            except (OSError,ValueError,UnicodeError,TypeError):continue
    try:meta=_json(d/'arquivos.json') if (d/'arquivos.json').is_file() else {}
    except (OSError,ValueError):meta={};issues.append({'file':'arquivos.json','cause':'Metadados inválidos.','action':'Reimporte a fonte original; os arquivos existentes não foram apagados.'})
    sources=[]
    for ext in ('dxf','kmz','dwg'):
        p=d/('input.'+ext);present=p.is_file() and not p.is_symlink() and p.stat().st_size>0
        expected=ext in meta or p.exists();sources.append({'file':p.name,'present':present,'expected':expected})
        if expected and not present:issues.append({'file':p.name,'cause':'Fonte ausente, vazia ou inválida.','action':'Localize e reimporte a fonte original em Arquivos do projeto.'})
    if config:
        image=(config.get('local_imagery') or {}).get('image')
        if image:
            p=d/'imagem_local'/image
            if Path(image).name!=image or not p.is_file() or p.is_symlink():issues.append({'file':'imagem_local','cause':'Imagem local cadastrada indisponível.','action':'Relocalize a imagem original em Camadas e imagens; não substituir por imagem vazia.'})
    key=revision([d.name,signature,[(x['file'],x['present'],x['expected']) for x in sources]])
    return {'project':d.name,'report_id':key,'config_signature':signature,'config_valid':config is not None and not any(x['file']=='config.json' for x in issues),'state':'bloqueado' if not config or any(x['file']=='config.json' for x in issues) else 'parcial' if issues else 'integro','issues':issues,'copies':copies,'sources':sources,'scope':'Validação da configuração, hashes das cópias e presença das fontes; integridade geométrica e mídia exigem leitura pelo motor.'}

def recover(d,key,report_id):
    if not re.fullmatch('[a-f0-9]{64}',key):raise ValueError('Revisão inválida.')
    d=Path(d)
    with locked(d):
        before=inspect(d)
        if before['report_id']!=report_id:raise Conflict('O projeto mudou. Confira a proteção novamente.')
        if key not in {c['revision'] for c in before['copies']}:raise ValueError('Cópia não conferida; recuperação recusada.')
        data=_json(d/'.estado/historico'/(key+'.json'));Settings.model_validate(data)
        bad=d/'.estado/corrompidos'
        if bad.is_symlink():raise ValueError('Pasta de recuperação inválida.')
        bad.mkdir(exist_ok=True)
        if (d/'config.json').exists():shutil.copy2(d/'config.json',bad/('config_'+uuid.uuid4().hex+'.json'))
        _write(d/'config.json',data)
        # A configuração válida é a fonte de verdade; falha no índice não apaga a restauração.
        try:_write(d/'.estado/config_atual.json',{'revision':key,'time':time.time()})
        except OSError:pass
        _write(d/'.estado/recuperacao.json',{'revision':key,'time':time.time(),'message':'Configuração restaurada de cópia conferida; confira fontes e prévia.'})
        after=inspect(d)
        if not after['config_valid'] or revision(_json(d/'config.json'))!=key:raise ValueError('A conferência final da recuperação falhou.')
        return after
