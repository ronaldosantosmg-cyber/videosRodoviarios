"""Atualizador do Rodovia Studio (somente biblioteca padrão do Python).

Uso:
  python atualizador.py --pacote <pasta 'pacote' extraída> --raiz <pasta do Rodovia Studio>
  python atualizador.py --raiz <pasta do Rodovia Studio> --procurar   (procura o ZIP mais novo)

Organização a partir da 1.32 (raiz só com o arquivo principal e as pastas de dados):
  <raiz>/Rodovia Studio.exe            arquivo principal (quando compilado)
  <raiz>/ABRIR RODOVIA STUDIO.cmd      arquivo principal enquanto não há o .exe
  <raiz>/projetos/                     projetos, arquivos CAD/KMZ
  <raiz>/videos/                       vídeos gerados (um por geração, sem substituir os anteriores)
  <raiz>/atualizacoes/                 coloque aqui os ZIP de atualização
  <raiz>/sistema/programa/             programa, Python portátil, bibliotecas e recursos
  <raiz>/sistema/documentacao/         manuais e notas de versão
  <raiz>/sistema/backups/              cópias do que cada atualização substituiu
  <raiz>/sistema/logs/                 registros de instalação, atualização e erros
  <raiz>/sistema/*.cmd, LEIA-ME.txt    atualizar, compilar o .exe, abrir (quando há .exe) e instruções

Organizações anteriores são convertidas automaticamente, sem apagar nada:
  1.2–1.7  (app/, runtime/, dados/ na raiz)     -> primeiro para a de 1.8 e depois para a de 1.32;
  1.8–1.31 (suporte/sistema, suporte/...)       -> sistema/programa, sistema/...
O formato do ZIP continua o mesmo (pacote/raiz e pacote/suporte/...), para que atualizadores antigos
consigam entregar o pacote a este atualizador.
"""
import argparse,json,os,re,shutil,sys,time,urllib.request,zipfile,filecmp,tempfile,subprocess
import hashlib, uuid, math
from contextlib import contextmanager
from pathlib import PurePosixPath, PureWindowsPath
from pathlib import Path

SYSTEM_ITEMS=['app','assets','runtime','tests','run.py','diagnostico.py','requirements.txt','requirements-dev.txt','iniciar.ps1','iniciar.sh','VERSAO.json','atualizador.py']
LOG_ITEMS=['instalacao.log','servidor_erro.log']
LEGACY_ITEMS=['INICIAR.cmd','ATUALIZAR.cmd','atualizar.ps1','LEIA-ME.txt','arquivos','PREPARAR_AMBIENTE_TESTE.cmd','_wheels_linux','_wheels_linux.log']
ZIP_RE=re.compile(r'RodoviaStudio_.*atualiza.*\.zip$',re.I)
MAIN_CMD='ABRIR RODOVIA STUDIO.cmd';MAIN_EXE='Rodovia Studio.exe'
# Arquivos auxiliares que antes ficavam na raiz e agora ficam em sistema/.
AUX_ROOT=['ATUALIZAR RODOVIA STUDIO.cmd','COMPILAR INICIADOR.cmd','LEIA-ME.txt']
DATA_DIRS=['projetos','videos','atualizacoes']

class PackageError(RuntimeError):
    pass

def L(p):
    """Caminho longo no Windows (pastas do OneDrive passam facilmente de 260 caracteres)."""
    p=os.path.abspath(str(p))
    if os.name=='nt' and not p.startswith('\\\\?\\'):
        return '\\\\?\\UNC\\'+p[2:] if p.startswith('\\\\') else '\\\\?\\'+p
    return p

def version_tuple(v):
    if not isinstance(v, str) or not re.fullmatch(r'\d+\.\d+(?:\.\d+)?', v):
        raise ValueError('Versão inválida: use maior.menor ou maior.menor.correção.')
    return tuple((list(map(int, v.split('.'))) + [0, 0, 0])[:3])

def program_dir(raiz):
    """Pasta do programa conforme a organização encontrada."""
    raiz=Path(raiz)
    for c in [raiz/'sistema/programa',raiz/'suporte/sistema',raiz]:
        if (c/'app/server.py').exists():return c
    return raiz/'sistema/programa'

def system_dir(raiz):
    raiz=Path(raiz);return raiz/'suporte' if (raiz/'suporte/sistema/app/server.py').exists() and not (raiz/'sistema/programa').exists() else raiz/'sistema'

def installed_version(raiz):
    for f in [Path(raiz)/'sistema/programa/VERSAO.json',Path(raiz)/'suporte/sistema/VERSAO.json',Path(raiz)/'VERSAO.json']:
        if f.exists():
            try:return json.loads(f.read_text(encoding='utf-8')).get('version','0')
            except Exception:pass
    return '0'

def find_root(path):
    """Aceita a raiz ou uma subpasta dela; reconhece as organizações antigas."""
    p=Path(path).resolve()
    for cand in [p,*p.parents,p/'RodoviaStudio',p/'Rodovia_Studio']:
        if (cand/'sistema/programa/app/server.py').exists():return cand,'sistema'
        if (cand/'suporte/sistema/app/server.py').exists():return cand,'nova'
        if (cand/'app/server.py').exists() and (cand/'app').is_dir() and cand.name not in ('sistema','programa'):return cand,'antiga'
    raise ValueError('A pasta escolhida não é a do Rodovia Studio (não encontrei sistema\\programa\\app\\server.py nem suporte\\sistema\\app\\server.py).')

def app_running(ports=range(8765,8785)):
    for port in ports:
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health',timeout=.6) as r:
                if json.loads(r.read()).get('status')=='ok':return port
        except Exception:continue
    return None

def log(raiz,text):
    d=system_dir(raiz)/'logs';d.mkdir(parents=True,exist_ok=True)
    with open(d/'atualizacao.log','a',encoding='utf-8') as f:f.write(time.strftime('%Y-%m-%d %H:%M:%S ')+text+'\n')

def _move_all(plan,stamp,what):
    done=[]
    try:
        for src,dst in plan:
            if not src.exists():continue
            if dst.exists():dst=dst.with_name(dst.name+f'_{stamp}')
            dst.parent.mkdir(parents=True,exist_ok=True);os.replace(src,dst);done.append((src,dst))
    except OSError as e:
        for src,dst in reversed(done):
            try:os.replace(dst,src)
            except OSError:pass
        raise RuntimeError(f'Não foi possível {what} ({e}). Feche o Rodovia Studio, o Explorer nessa pasta e tente de novo; nada foi alterado.')
    return done

def migrate(raiz,stamp,say=print):
    """Organização 1.2–1.7 -> 1.8. Movimentos são desfeitos se algum falhar (arquivo em uso)."""
    raiz=Path(raiz);sup=raiz/'suporte'
    plan=[]
    for n in SYSTEM_ITEMS:plan.append((raiz/n,sup/'sistema'/n))
    for f in sorted(raiz.glob('*.md')):plan.append((f,sup/'documentacao'/f.name))
    plan.append((raiz/'conferencia',sup/'documentacao'/'conferencia'))
    for n in LOG_ITEMS:plan.append((raiz/n,sup/'logs'/n))
    for d in sorted(raiz.glob('backup_antes_*')):plan.append((d,sup/'backups'/d.name))
    for n in LEGACY_ITEMS:plan.append((raiz/n,sup/'backups'/f'legado_{stamp}'/n))
    for z in sorted(raiz.glob('*.zip')):
        if ZIP_RE.search(z.name):plan.append((z,raiz/'atualizacoes'/'aplicadas'/z.name))
    if (raiz/'dados').exists() and not (raiz/'projetos').exists():plan.append((raiz/'dados',raiz/'projetos'))
    done=_move_all(plan,stamp,'reorganizar')
    for d in ['projetos','atualizacoes','suporte/backups','suporte/logs','suporte/documentacao']:(raiz/d).mkdir(parents=True,exist_ok=True)
    say(f'Pastas reorganizadas: {len(done)} itens movidos (nada apagado).')
    return done

def migrate_132(raiz,stamp,say=print):
    """Organização 1.8–1.31 (suporte/...) -> 1.32 (sistema/programa, sistema/...).

    Só move pastas inteiras (rápido, sem copiar). Os .cmd auxiliares da raiz não são movidos aqui, porque o
    ATUALIZAR RODOVIA STUDIO.cmd antigo pode estar em execução neste momento; eles são arrumados na próxima
    abertura do aplicativo (run.py -> organizar_raiz) e quando o pacote é copiado."""
    raiz=Path(raiz);sup=raiz/'suporte';sis=raiz/'sistema'
    if not (sup/'sistema/app/server.py').exists():return []
    plan=[(sup/'sistema',sis/'programa')]
    for d in sorted(sup.iterdir()):
        if d.name!='sistema':plan.append((d,sis/d.name))
    sis.mkdir(exist_ok=True)
    done=_move_all(plan,stamp,'reorganizar as pastas do sistema')
    try:sup.rmdir()
    except OSError:pass
    for d in DATA_DIRS+['sistema/backups','sistema/logs','sistema/documentacao']:(raiz/d).mkdir(parents=True,exist_ok=True)
    say(f'Organização 1.32: “suporte” virou “sistema” ({len(done)} pastas movidas; nada apagado).')
    return done

def handle_old_exe(raiz,stamp,say=print):
    """O Rodovia Studio.exe compilado antes da 1.32 procura suporte\\sistema e deixa de funcionar.
    Ele é guardado em sistema/backups e a raiz volta a ter o ABRIR RODOVIA STUDIO.cmd; na próxima abertura,
    o aplicativo recompila o .exe sozinho (sistema/logs/recompilar_iniciador.txt)."""
    raiz=Path(raiz);exe=raiz/MAIN_EXE
    if not exe.exists():return False
    dst=raiz/'sistema/backups'/f'legado_{stamp}'/MAIN_EXE;dst.parent.mkdir(parents=True,exist_ok=True)
    try:os.replace(exe,dst)   # renomear um .exe em uso é permitido no Windows
    except OSError as e:say(f'Aviso: não consegui guardar o Rodovia Studio.exe antigo ({e}).');return False
    (raiz/'sistema/logs').mkdir(parents=True,exist_ok=True)
    (raiz/'sistema/logs/recompilar_iniciador.txt').write_text('O Rodovia Studio.exe anterior à 1.32 foi guardado em '+str(dst.relative_to(raiz))+'. Recompilar.',encoding='utf-8')
    say('O Rodovia Studio.exe antigo foi guardado em sistema\\backups; ele será recompilado sozinho na próxima abertura (ou use sistema\\COMPILAR INICIADOR.cmd).')
    return True

def organize_root(raiz,stamp=None,say=print,keep=()):
    """Raiz só com o arquivo principal e as pastas de dados. Auxiliares vão para sistema/ (nada é apagado:
    versões repetidas vão para sistema/backups/legado_<data>)."""
    raiz=Path(raiz);sis=raiz/'sistema'
    if not (sis/'programa').exists():return []
    stamp=stamp or time.strftime('%Y%m%d_%H%M%S');moved=[]
    for d in DATA_DIRS:(raiz/d).mkdir(exist_ok=True)
    # 1.42: ZIPs de atualização nunca permanecem na raiz. Pacotes antigos/manualmente copiados
    # são movidos para atualizacoes/ e passam pelo mesmo fluxo validado do iniciador.
    for z in sorted(raiz.glob('*.zip')):
        if not ZIP_RE.search(z.name):continue
        dst=raiz/'atualizacoes'/z.name
        if dst.exists():dst=raiz/'atualizacoes'/(z.stem+'_'+stamp+z.suffix)
        try:os.replace(z,dst);moved.append(z.name+' -> atualizacoes')
        except OSError:pass
    names=[n for n in AUX_ROOT if n not in keep]
    if (raiz/MAIN_EXE).exists():names.append(MAIN_CMD)   # com o .exe, o .cmd vira reserva em sistema/
    elif not (raiz/MAIN_CMD).exists() and (sis/MAIN_CMD).exists():
        try:shutil.copy2(sis/MAIN_CMD,raiz/MAIN_CMD);moved.append(MAIN_CMD+' -> raiz')
        except OSError:pass
    for n in names:
        src=raiz/n
        if not src.exists():continue
        dst=sis/n
        if dst.exists():
            same=False
            try:same=filecmp.cmp(src,dst,shallow=False)
            except OSError:pass
            dst=sis/'backups'/f'legado_{stamp}'/n
            if same:
                try:src.unlink();moved.append(n+' (igual ao de sistema)');continue
                except OSError:continue
        try:dst.parent.mkdir(parents=True,exist_ok=True);os.replace(src,dst);moved.append(n)
        except OSError:pass   # em uso: tenta de novo na próxima abertura
    if moved:say('Raiz organizada: '+', '.join(moved)+'.')
    return moved

def _targets(pacote,raiz):
    """Destino de cada arquivo do pacote na organização 1.32."""
    raiz=Path(raiz)
    for part in ('raiz','suporte'):
        base=pacote/part
        if not base.exists():continue
        for f in sorted(p for p in base.rglob('*') if p.is_file()):
            rel=f.relative_to(base)
            if part=='raiz':
                if rel.as_posix()==MAIN_CMD:
                    # O .cmd principal fica na raiz (sem .exe) e sempre tem uma cópia de reserva em sistema/.
                    yield f,raiz/'sistema'/MAIN_CMD,'raiz/'+rel.as_posix()
                    if not (raiz/MAIN_EXE).exists():yield f,raiz/MAIN_CMD,'raiz/'+rel.as_posix()
                else:yield f,raiz/'sistema'/rel,'raiz/'+rel.as_posix()
            else:
                parts=rel.parts
                dest=raiz/'sistema'/'programa'/Path(*parts[1:]) if parts[0]=='sistema' else raiz/'sistema'/rel
                yield f,dest,'suporte/'+rel.as_posix()

def _known_development_residuals(raiz,old,new_targets):
    """Só arquiva testes idênticos aos do ZIP aplicado anterior; desconhecidos ficam."""
    raiz=Path(raiz);out=[];folder=raiz/'atualizacoes'/'aplicadas'
    if not folder.exists():return out
    for z in sorted(folder.glob('*.zip'),key=lambda f:f.stat().st_mtime,reverse=True):
        try:
            with zipfile.ZipFile(z) as archive:
                names=[n for n in archive.namelist() if n=='manifest.json' or n.endswith('pacote/manifest.json')]
                if len(names)!=1 or archive.getinfo(names[0]).file_size>2*1024*1024:continue
                metadata=json.loads(archive.read(names[0]))
                if metadata.get('version')!=old or not isinstance(metadata.get('files'),dict):continue
                for relative,expected in metadata['files'].items():
                    if not relative.startswith('suporte/sistema/tests/'):continue
                    sub=Path(relative).relative_to('suporte/sistema')
                    target=_safe_target(raiz,(Path('sistema/programa')/sub).as_posix())
                    if target in new_targets or not target.is_file() or target.is_symlink():continue
                    if not isinstance(expected,str) or _sha(target)!=expected:continue
                    out.append((target,expected))
                return out
        except (OSError,ValueError,KeyError,zipfile.BadZipFile):continue
    return out

def _rel_target(raiz,target):
    """Caminho persistido no manifesto de rollback, sempre relativo à raiz."""
    return Path(target).resolve().relative_to(Path(raiz).resolve()).as_posix()

def rollback_candidates(raiz):
    """Backups de atualização disponíveis, mais recente primeiro."""
    raiz,_=find_root(raiz);base=system_dir(raiz)/'backups';out=[]
    if not base.exists():return out
    for d in base.glob('antes_v*'):
        if not d.is_dir():continue
        man=d/'rollback.json';info={}
        if man.exists():
            try:info=json.loads(man.read_text(encoding='utf-8'))
            except Exception:info={}
        out.append({'path':str(d),'name':d.name,'timestamp':d.stat().st_mtime,
                    'previous':info.get('previous'),'version':info.get('version'),
                    'manifest':man.exists(),'restored':bool(info.get('restored_at'))})
    return sorted(out,key=lambda x:x['timestamp'],reverse=True)

def _legacy_backup_target(raiz,rel):
    """Traduz rótulos de backup antigos para o layout atual."""
    rel=Path(rel);parts=rel.parts
    if not parts:return None
    if parts[0]=='raiz':
        sub=Path(*parts[1:])
        if sub.as_posix()==MAIN_CMD:return Path(raiz)/MAIN_CMD
        return Path(raiz)/'sistema'/sub
    if parts[0]=='suporte':
        sub=Path(*parts[1:]);sp=sub.parts
        return Path(raiz)/'sistema'/'programa'/Path(*sp[1:]) if sp and sp[0]=='sistema' else Path(raiz)/'sistema'/sub
    return Path(raiz)/rel

def _restore_previous(raiz,backup=None,say=print,check_running=True):
    """Restabelece a atualização anterior sem tocar em projetos/vídeos.

    Atualizações novas gravam rollback.json e permitem remover também arquivos
    que não existiam antes. Backups antigos são restaurados em modo compatível,
    copiando de volta apenas os arquivos que foram efetivamente salvos.
    """
    raiz,_=find_root(raiz)
    if check_running and (port:=app_running()):raise RuntimeError(f'O Rodovia Studio está aberto (porta {port}). Feche o aplicativo antes de restabelecer a versão.')
    cands=rollback_candidates(raiz)
    if backup:
        b=Path(backup);cand=next((x for x in cands if Path(x['path']).resolve()==b.resolve() or x['name']==str(backup)),None)
    else:cand=next((x for x in cands if not x['restored']),None)
    if not cand:raise RuntimeError('Nenhuma versão anterior disponível para restabelecer.')
    bdir=Path(cand['path']);manfile=bdir/'rollback.json';stamp=time.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8]
    safety=system_dir(raiz)/'backups'/f'antes_restaurar_{stamp}';restored=removed=0
    if manfile.exists():
        man=json.loads(manfile.read_text(encoding='utf-8'))
        entries=man.get('files',[])
        for e in entries:
            _safe_target(raiz, e['target'])
            if e.get('had_previous'):
                src = _safe_child(bdir, e['backup'])
                if not src.is_file():raise RuntimeError('Backup incompleto: '+str(src))
                if e.get('sha256') and _sha(src) != e['sha256']:
                    raise RuntimeError('Backup com hash divergente: '+str(src))
        # Snapshot recuperável antes do rollback; uma restauração também pode falhar.
        safety.mkdir(parents=True,exist_ok=True);safety_entries=[]
        for e in entries:
            target=_safe_target(raiz,e['target']);had=target.is_file()
            saved={'target':e['target'],'had_previous':had,'backup':e['target'] if had else None}
            if had:
                snap=safety/e['target'];snap.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(L(target),L(snap));saved['sha256']=_sha(snap)
            safety_entries.append(saved)
        safety_manifest=safety/'snapshot.json'
        safety_info={'state':'restoring','files':safety_entries}
        _write_manifest(safety_manifest,safety_info)
        try:
            for e in reversed(entries):
                target=_safe_target(raiz,e['target'])
                if e.get('had_previous'):
                    src=_safe_child(bdir,e['backup'])
                    target.parent.mkdir(parents=True,exist_ok=True);tmp=target.with_name(target.name+'.restaurando')
                    try:shutil.copy2(L(src),L(tmp));os.replace(L(tmp),L(target));restored+=1
                    finally:tmp.unlink(missing_ok=True)
                elif target.exists() and target.is_file():target.unlink();removed+=1
            man['state']='restored';man['restored_at']=time.strftime('%Y-%m-%dT%H:%M:%S');man['safety_snapshot']=str(safety)
            _write_manifest(manfile,man)
        except Exception as exc:
            try:
                _restore_safety(raiz,safety,safety_entries)
                safety_info['state']='recovered';_write_manifest(safety_manifest,safety_info)
            except Exception as recovery:
                raise RuntimeError(f'Restauração interrompida. Snapshot de recuperação em {safety}: {recovery}') from exc
            raise RuntimeError('Restauração interrompida. O estado anterior à tentativa foi recuperado.') from exc
        safety_info['state']='completed';_write_manifest(safety_manifest,safety_info)
        previous=man.get('previous') or 'anterior'
    else:
        # compatibilidade com backups de atualizadores anteriores
        for src in sorted((x for x in bdir.rglob('*') if x.is_file()),key=lambda x:len(x.parts)):
            target=_legacy_backup_target(raiz,src.relative_to(bdir))
            if target is None:continue
            _safe_target(raiz,target.relative_to(raiz).as_posix())
            if target.exists():
                snap=safety/target.resolve().relative_to(Path(raiz).resolve());snap.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(L(target),L(snap))
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(L(src),L(target));restored+=1
        previous='anterior (backup legado)'
    msg=f'Versão {previous} restabelecida: {restored} arquivos restaurados, {removed} arquivos novos removidos. Snapshot de segurança: {safety.relative_to(raiz)}.'
    say(msg);log(raiz,msg);return {'restored':restored,'removed':removed,'previous':previous,'backup':str(bdir),'safety':str(safety)}


def _sha(path):
    with open(L(path), 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def _safe_child(root, relative):
    if not isinstance(relative, str) or not relative or '\\' in relative:
        raise ValueError('Caminho interno inválido.')
    rel = PurePosixPath(relative)
    if rel.is_absolute() or '..' in rel.parts or PureWindowsPath(relative).drive or ':' in relative:
        raise ValueError('Caminho interno inválido: '+relative)
    root = Path(root).resolve()
    target = root.joinpath(*rel.parts)
    # Não atravesse links, mesmo quando apontam para outra pasta dentro da instalação.
    for part in [target, *target.parents]:
        if part == root:break
        if part.is_symlink():raise ValueError('Link não permitido no caminho: '+relative)
    target.resolve().relative_to(root)
    return target


def _safe_target(root, relative):
    target = _safe_child(root, relative)
    parts = PurePosixPath(relative).parts
    if parts[0] != 'sistema' and relative not in (MAIN_CMD, MAIN_EXE):
        raise ValueError('Destino protegido: '+relative)
    if len(parts)>1 and parts[1] in ('backups','logs'):
        raise ValueError('Destino protegido: '+relative)
    return target


def _write_manifest(path, data):
    path = Path(path)
    tmp = path.with_name(path.name+'.novo')
    with open(L(tmp), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.flush();os.fsync(f.fileno())
    os.replace(L(tmp), L(path))


@contextmanager
def _update_lock(raiz):
    logs = system_dir(raiz)/'logs';logs.mkdir(parents=True, exist_ok=True)
    with open(logs/'atualizacao.lock', 'a+b') as f:
        f.seek(0);f.write(b'0');f.flush();f.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise RuntimeError('Já existe uma atualização ou restauração em andamento.') from exc
        try:yield
        finally:
            if os.name == 'nt':
                import msvcrt
                f.seek(0);msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(f, fcntl.LOCK_UN)


def restore_previous(raiz,backup=None,say=print,check_running=True):
    raiz,_=find_root(raiz)
    with _update_lock(raiz):
        return _restore_previous(raiz,backup,say,check_running)


def validate_package(pacote,say=print):
    """Pré-voo antes de tocar na instalação: JSON, sintaxe Python e, quando Node existir, sintaxe JS.

    Um pacote defeituoso é recusado antes de criar/substituir qualquer arquivo.
    """
    pacote=Path(pacote);errors=[]
    required=[pacote/'manifest.json',pacote/'suporte/sistema/app/server.py',pacote/'suporte/sistema/VERSAO.json']
    for f in required:
        if not f.is_file():errors.append('ausente: '+str(f.relative_to(pacote)))
    for f in [pacote/'manifest.json',pacote/'suporte/sistema/VERSAO.json']:
        if not f.is_file():continue
        try:json.loads(f.read_text(encoding='utf-8'))
        except Exception as e:errors.append(f'JSON inválido em {f.name}: {e}')
    if not errors:
        try:
            man=json.loads((pacote/'manifest.json').read_text(encoding='utf-8'))
            version=json.loads((pacote/'suporte/sistema/VERSAO.json').read_text(encoding='utf-8'))
            if man.get('app') not in (None,'Rodovia Studio'):raise ValueError('Aplicativo do pacote não reconhecido.')
            if version_tuple(man.get('version')) != version_tuple(version.get('version')):
                raise ValueError('Manifesto e VERSAO.json têm versões diferentes.')
            for f in pacote.rglob('*'):
                if f.is_symlink():raise ValueError('Pacote contém link: '+str(f))
            if 'files' in man:
                actual={f.relative_to(pacote).as_posix() for f in pacote.rglob('*') if f.is_file() and f!=pacote/'manifest.json'}
                if actual!=set(man['files']):raise ValueError('Lista de arquivos diverge do manifesto de integridade.')
            for rel, expected in man.get('files', {}).items():
                f=_safe_child(pacote, rel)
                if not f.is_file() or _sha(f) != expected:raise ValueError('Hash divergente: '+rel)
            # Detecta destinos protegidos, duplicados ou fora da instalação antes da escrita.
            seen=set()
            virtual=Path(tempfile.gettempdir())/'rs_destinos_validacao'
            for _,target,_ in _targets(pacote, virtual):
                rel=target.relative_to(virtual).as_posix();_safe_target(virtual, rel)
                if rel.casefold() in seen:raise ValueError('Destino duplicado: '+rel)
                seen.add(rel.casefold())
        except (OSError, ValueError, TypeError, AttributeError) as e:errors.append(str(e))
    pyroot=pacote/'suporte/sistema'
    for f in pyroot.rglob('*.py') if pyroot.exists() else []:
        try:compile(f.read_text(encoding='utf-8'),str(f),'exec')
        except Exception as e:errors.append(f'Sintaxe Python em {f.relative_to(pacote)}: {e}')
    node=shutil.which('node')
    if node:
        for f in (pyroot/'app/js').glob('*.js') if (pyroot/'app/js').exists() else []:
            r=subprocess.run([node,'--check',str(f)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            if r.returncode:errors.append(f'Sintaxe JavaScript em {f.name}: {(r.stderr or r.stdout).strip()[:500]}')
    else:
        # Sem Node no computador do usuário: faz verificações estruturais mínimas; a entrega oficial já passa por node --check.
        for f in (pyroot/'app/js').glob('*.js') if (pyroot/'app/js').exists() else []:
            try:t=f.read_text(encoding='utf-8')
            except Exception as e:errors.append(f'JavaScript ilegível em {f.name}: {e}');continue
            if '\x00' in t or not t.strip():errors.append(f'JavaScript inválido/vazio: {f.name}')
    if errors:raise PackageError('Pacote recusado na verificação prévia:\n- '+'\n- '.join(errors[:20]))
    say('Verificação prévia concluída: pacote íntegro e sintaxe Python válida'+(' / JavaScript validada com Node.' if node else '.'))
    return True

def apply(pacote,raiz,say=print,check_running=True):
    raiz,_=find_root(raiz)
    with _update_lock(raiz):
        return _apply(pacote,raiz,say,check_running)


def _apply(pacote,raiz,say=print,check_running=True):
    pacote=Path(pacote);validate_package(pacote,say);raiz,layout=find_root(raiz)
    new=json.loads((pacote/'manifest.json').read_text(encoding='utf-8'))['version']
    if check_running and (port:=app_running()):
        raise RuntimeError(f'O Rodovia Studio está aberto (porta {port}). Feche a janela do aplicativo e tente de novo.')
    stamp=time.strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex[:8];old=installed_version(raiz)
    say(f'Rodovia Studio {old} -> {new} em {raiz}')
    if layout=='antiga':migrate(raiz,stamp,say);layout_now='nova'
    else:layout_now=layout
    old_exe=False
    if layout_now=='nova':
        migrate_132(raiz,stamp,say)
        old_exe=handle_old_exe(raiz,stamp,say)
    final_backup=raiz/'sistema/backups'/f'antes_v{new.replace(".","_")}_{stamp}'
    backup=final_backup.with_name('.preparando_'+final_backup.name)
    rollback_files=[];plan=[];saved=0
    # Todos os backups ficam completos ANTES de substituir o primeiro arquivo.
    for f,target,label in _targets(pacote,raiz):
        target=_safe_target(raiz, target.relative_to(raiz).as_posix())
        had_previous=target.exists()
        if had_previous and filecmp.cmp(L(f),L(target),shallow=False):continue
        entry={'target':_rel_target(raiz,target),'had_previous':had_previous,'backup':label if had_previous else None}
        if had_previous:
            b=backup/label;b.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(L(target),L(b));entry['sha256']=_sha(b);saved+=1
        rollback_files.append(entry);plan.append((f,target))
    residuals=_known_development_residuals(raiz,old,{target for _,target,_ in _targets(pacote,raiz)})
    for target,expected in residuals:
        label='residuos/'+target.relative_to(raiz).as_posix();b=backup/label;b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(L(target),L(b))
        rollback_files.append({'target':_rel_target(raiz,target),'had_previous':True,'backup':label,'sha256':expected,'archived_residual':True});saved+=1
    if not plan and not residuals:
        say('Nenhum arquivo precisa ser substituído.')
        return {'version':new,'previous':old,'copied':0,'backed_up':0,'backup':None}
    backup.mkdir(parents=True,exist_ok=True)
    journal={'version':new,'previous':old,'created_at':time.strftime('%Y-%m-%dT%H:%M:%S'),'state':'prepared','files':rollback_files}
    manifest=backup/'rollback.json';_write_manifest(manifest,journal)
    os.replace(L(backup),L(final_backup));backup=final_backup;manifest=backup/'rollback.json'
    try:
        journal['state']='applying';_write_manifest(manifest,journal)
        for f,target in plan:
            target.parent.mkdir(parents=True,exist_ok=True);tmp=target.with_name(target.name+'.novo')
            try:
                shutil.copy2(L(f),L(tmp));os.replace(L(tmp),L(target))
            finally:
                if tmp.exists():tmp.unlink()
        for target,expected in residuals:
            if target.exists() and _sha(target)==expected:target.unlink()
        journal['archived_residuals']=len(residuals)
        journal['state']='applied';_write_manifest(manifest,journal)
    except Exception as exc:
        journal['state']='failed';_write_manifest(manifest,journal)
        try:_restore_previous(raiz,str(backup),say,check_running=False)
        except Exception as recovery:
            raise RuntimeError(f'Atualização interrompida; restauração pendente em {backup}: {recovery}') from exc
        raise RuntimeError('Atualização interrompida. A versão anterior foi restaurada automaticamente.') from exc
    for d in DATA_DIRS:(raiz/d).mkdir(exist_ok=True)
    msg=f'Atualização {new} aplicada: {len(plan)} arquivos novos/alterados, {saved} anteriores guardados em {backup.relative_to(raiz)}.'
    say(msg);log(raiz,msg)
    return {'version':new,'previous':old,'copied':len(plan),'backed_up':saved,'layout_before':layout,'backup':str(backup),'old_exe_saved':old_exe,'archived_residuals':len(residuals)}


def candidates(raiz):
    """Pacotes pendentes oficiais.

    A partir da 1.42, a fonte de atualização é exclusivamente <raiz>/atualizacoes.
    Aceita tanto o formato atual (manifest.json na raiz do ZIP) quanto o legado
    (pacote/manifest.json), para não quebrar pacotes já distribuídos.
    """
    raiz=Path(raiz);d=raiz/'atualizacoes';out=[]
    if not d.exists():return out
    for z in d.glob('*.zip'):
        if not ZIP_RE.search(z.name):continue
        try:
            with zipfile.ZipFile(z) as zf:
                names=set(zf.namelist())
                manifests=[n for n in names if n=='manifest.json' or n.endswith('pacote/manifest.json')]
                if len(manifests)!=1:continue
                if 'manifest.json' in names:name='manifest.json';package_prefix=''
                else:
                    legacy=next((n for n in names if n.endswith('pacote/manifest.json')),None)
                    if not legacy:continue
                    name=legacy;package_prefix=str(Path(name).parent).replace('\\','/')
                man=json.loads(zf.read(name))
                if not isinstance(man,dict) or man.get('app') not in (None,'Rodovia Studio'):continue
                ver=version_tuple(man.get('version'))
                out.append((ver,z,name,package_prefix))
        except (zipfile.BadZipFile,KeyError,ValueError,TypeError,AttributeError,OSError):continue
    return sorted(out,key=lambda c:(c[0],c[1].stat().st_mtime),reverse=True)

def _archive_zip(z,folder):
    folder.mkdir(parents=True,exist_ok=True);dest=folder/z.name
    if dest.exists():dest=folder/(z.stem+'_'+uuid.uuid4().hex[:8]+z.suffix)
    os.replace(L(z),L(dest))
    return dest


def search_and_apply(raiz,say=print,check_running=True):
    raiz,_=find_root(raiz);cur=version_tuple(installed_version(raiz));found=candidates(raiz)
    if found:
        valid={x[1] for x in found}
        for invalid in (raiz/'atualizacoes').glob('*.zip'):
            if ZIP_RE.search(invalid.name) and invalid not in valid:
                _archive_zip(invalid,raiz/'atualizacoes'/'rejeitadas')
    if not found:
        # ZIP com nome de atualização mas estrutura inválida: coloca em rejeitadas para não gerar loop.
        rej=raiz/'atualizacoes'/'rejeitadas';rej.mkdir(parents=True,exist_ok=True);moved=[]
        for z in (raiz/'atualizacoes').glob('*.zip'):
            if not ZIP_RE.search(z.name):continue
            dst=rej/z.name
            if dst.exists():dst=rej/(z.stem+'_'+time.strftime('%Y%m%d_%H%M%S')+z.suffix)
            try:os.replace(z,dst);moved.append(z.name)
            except OSError:pass
        if moved:say('Pacote(s) inválido(s) movido(s) para atualizacoes/rejeitadas: '+', '.join(moved))
        else:say('Nenhum ZIP de atualização pendente em "atualizacoes".')
        return None
    ver,z,name,package_prefix=found[0]
    if ver<=cur:
        dest=raiz/'atualizacoes'/'aplicadas';dest.mkdir(parents=True,exist_ok=True)
        dst=dest/z.name
        if dst.exists():dst=dest/(z.stem+'_'+time.strftime('%Y%m%d_%H%M%S')+z.suffix)
        try:os.replace(z,dst)
        except OSError:pass
        say(f'Já está atualizado ({".".join(map(str,cur))}). O pacote {z.name} foi arquivado em atualizacoes/aplicadas.');return None
    # 1.19: extrai numa pasta temporária curta (antes, dentro do OneDrive, o caminho passava de 260 caracteres).
    tmp=Path(tempfile.mkdtemp(prefix='rs_'))
    try:
        with zipfile.ZipFile(z) as zf:
            for m in zf.infolist():
                p=Path(m.filename)
                _safe_child(tmp, m.filename.rstrip('/'))
                if (m.external_attr >> 16) & 0o170000 == 0o120000:
                    raise ValueError('ZIP contém link: '+m.filename)
            for m in zf.infolist():
                out=tmp/m.filename
                if m.is_dir():os.makedirs(L(out),exist_ok=True);continue
                os.makedirs(L(out.parent),exist_ok=True)
                with zf.open(m) as src,open(L(out),'wb') as dst:shutil.copyfileobj(src,dst)
        pacote=tmp/Path(package_prefix) if package_prefix else tmp
        validate_package(pacote,say)
        newer=pacote/'suporte/sistema/atualizador.py'
        if newer.exists() and newer.read_bytes()!=Path(__file__).read_bytes() and not os.environ.get('RODOVIA_ATUALIZADOR_INTERNO'):
            # Usa o atualizador que veio no pacote (pode conter reorganizações novas).
            env=dict(os.environ,RODOVIA_ATUALIZADOR_INTERNO='1')
            r=subprocess.run([sys.executable,str(newer),'--raiz',str(raiz),'--pacote',str(pacote)]+([] if check_running else ['--sem-verificar-aberto']),env=env)
            if r.returncode:raise RuntimeError('O atualizador do pacote informou erro (veja acima).')
            res={'version':'.'.join(map(str,ver)),'delegated':True}
        else:res=apply(pacote,raiz,say,check_running)
        dest=raiz/'atualizacoes'/'aplicadas';dest.mkdir(parents=True,exist_ok=True)
        try:
            if z.parent==raiz/'atualizacoes':_archive_zip(z,dest)
        except OSError:pass
        return res
    except (ValueError, PackageError, zipfile.BadZipFile) as exc:
        _archive_zip(z,raiz/'atualizacoes'/'rejeitadas')
        raise RuntimeError('Pacote recusado e movido para atualizacoes/rejeitadas: '+str(exc)) from exc
    finally:shutil.rmtree(L(tmp),ignore_errors=True)

def _restore_safety(raiz,folder,entries):
    # Verifica todo o snapshot antes de reverter a primeira escrita.
    for e in entries:
        _safe_target(raiz,e['target'])
        if e['had_previous']:
            src=_safe_child(folder,e['backup'])
            if not src.is_file() or _sha(src)!=e['sha256']:raise RuntimeError('Snapshot de segurança incompleto ou alterado.')
    for e in reversed(entries):
        target=_safe_target(raiz,e['target'])
        if e['had_previous']:
            tmp=target.with_name(target.name+'.recuperando');target.parent.mkdir(parents=True,exist_ok=True)
            try:shutil.copy2(L(_safe_child(folder,e['backup'])),L(tmp));os.replace(L(tmp),L(target))
            finally:tmp.unlink(missing_ok=True)
        else:target.unlink(missing_ok=True)


def recover_pending(raiz,say=print):
    """Recupera uma troca interrompida por queda de energia antes de abrir o app."""
    raiz,_=find_root(raiz)
    with _update_lock(raiz):
        for file in (system_dir(raiz)/'backups').glob('antes_restaurar_*/snapshot.json'):
            info=json.loads(file.read_text(encoding='utf-8'))
            if info.get('state')=='restoring':
                _restore_safety(raiz,file.parent,info['files'])
                info['state']='recovered';_write_manifest(file,info)
                say('Snapshot recuperado após restauração interrompida.')
        for candidate in rollback_candidates(raiz):
            file=Path(candidate['path'])/'rollback.json'
            if not file.exists():continue
            man=json.loads(file.read_text(encoding='utf-8'))
            if man.get('state') in ('prepared','applying','failed') and not man.get('restored_at'):
                _restore_previous(raiz,candidate['path'],say,check_running=True)


def main(argv=None):
    a=argparse.ArgumentParser();a.add_argument('--raiz',required=True);a.add_argument('--pacote');a.add_argument('--procurar',action='store_true');a.add_argument('--restaurar-anterior',action='store_true');a.add_argument('--backup');a.add_argument('--sem-verificar-aberto',action='store_true')
    a.add_argument('--aguardar',type=float,default=0,help='espera o aplicativo fechar (segundos), usado pela atualização feita de dentro do aplicativo')
    o=a.parse_args(argv)
    try:
        if not math.isfinite(o.aguardar) or o.aguardar<0:raise ValueError('Tempo de espera inválido.')
        if o.aguardar:
            t0=time.time()
            while app_running() and time.time()-t0<o.aguardar:time.sleep(.5)
        if o.restaurar_anterior:restore_previous(o.raiz,o.backup,check_running=not o.sem_verificar_aberto)
        elif o.pacote:apply(o.pacote,o.raiz,check_running=not o.sem_verificar_aberto)
        else:search_and_apply(o.raiz,check_running=not o.sem_verificar_aberto)
        return 0
    except Exception as e:
        print('ERRO: '+str(e))
        try:log(find_root(o.raiz)[0],'ERRO: '+str(e))
        except Exception:pass
        return 1

if __name__=='__main__':sys.exit(main())
