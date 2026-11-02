"""2.57: atualização SÓ de componentes (texturas e IA), sem trocar o programa.

ZIP: RodoviaStudio_componentes_<nome>_<versao>.zip com componente.json:
  {"app":"Rodovia Studio","tipo":"componentes","componentes":{"texturas":{"versao":"2","files":{"texturas/x.jpg":"<sha256>"}},"ia":{"versao":"1","files":{"ia/modelo.json":"..."}}}}
Destinos: texturas/ → <programa>/assets/texturas/ ; ia/ → <instalação>/modelos_ia/. Nada além disso pode ser escrito.
Antes de trocar, os arquivos substituídos vão para sistema/backups/componente_<data>/ (restaurável). Exige o aplicativo fechado.
Uso: python -m app.componentes [--listar] [--instalar [ZIP]] [--restaurar [DATA]] [--raiz PASTA]
"""
import hashlib,json,os,re,shutil,sys,time,zipfile
from pathlib import Path

DESTINOS={'texturas':('programa','assets/texturas'),'ia':('raiz','modelos_ia')}
NOME_RE=re.compile(r'^RodoviaStudio_componentes_.*\.zip$',re.I)
LIM_ARQ=6*1024**3;LIM_N=64

class ComponenteErro(RuntimeError):pass

def _raiz(raiz):
    from atualizador import find_root
    return Path(find_root(raiz)[0])
def _programa(raiz):
    from atualizador import program_dir
    return Path(program_dir(raiz))
def _alvo(raiz,comp):
    base,sub=DESTINOS[comp];b=Path(raiz) if base=='raiz' else _programa(raiz);return b/sub
def _sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1<<22),b''):h.update(c)
    return h.hexdigest()

def estado_instalado(raiz):
    f=Path(raiz)/'sistema'/'componentes.json'
    try:return json.loads(f.read_text(encoding='utf-8'))
    except (OSError,ValueError):return {}

def validar(zf):
    """devolve o manifesto validado; recusa tudo que fuja do contrato antes de escrever qualquer coisa."""
    if 'componente.json' not in zf.namelist():raise ComponenteErro('ZIP sem componente.json (não é pacote de componentes).')
    m=json.loads(zf.read('componente.json'))
    if m.get('app') not in (None,'Rodovia Studio') or m.get('tipo')!='componentes' or not isinstance(m.get('componentes'),dict) or not m['componentes']:raise ComponenteErro('componente.json inválido.')
    infos={i.filename:i for i in zf.infolist() if not i.is_dir()}
    declarados=set()
    for comp,dados in m['componentes'].items():
        if comp not in DESTINOS:raise ComponenteErro('Componente não permitido: '+str(comp))
        files=dados.get('files')
        if not isinstance(files,dict) or not files or len(files)>LIM_N:raise ComponenteErro('Lista de arquivos inválida em '+comp)
        for rel,sha in files.items():
            p=Path(rel)
            if not rel.startswith(comp+'/') or p.is_absolute() or '..' in p.parts or '\\' in rel or ':' in rel:raise ComponenteErro('Caminho recusado: '+rel)
            i=infos.get(rel)
            if i is None:raise ComponenteErro('Arquivo ausente no ZIP: '+rel)
            if (i.external_attr>>16)&0o170000==0o120000:raise ComponenteErro('Link recusado: '+rel)
            if i.file_size>LIM_ARQ:raise ComponenteErro('Arquivo grande demais: '+rel)
            if not isinstance(sha,str) or not re.fullmatch(r'[0-9a-f]{64}',sha):raise ComponenteErro('Hash inválido: '+rel)
            h=hashlib.sha256()
            with zf.open(i) as f:
                for c in iter(lambda:f.read(1<<22),b''):h.update(c)
            if h.hexdigest()!=sha:raise ComponenteErro('Hash divergente: '+rel)
            declarados.add(rel)
    extra=set(infos)-declarados-{'componente.json'}
    if extra:raise ComponenteErro('Arquivos fora do manifesto: '+', '.join(sorted(extra)[:3]))
    return m

def pendentes(raiz):
    raiz=Path(raiz);out=[]
    for d in (raiz/'atualizacoes'/'componentes',raiz/'atualizacoes'):
        if d.is_dir():out+=[z for z in d.glob('*.zip') if NOME_RE.match(z.name)]
    return sorted(out,key=lambda z:z.stat().st_mtime)

def instalar(raiz,zip_path,say=print,check_running=True):
    raiz=_raiz(raiz)
    if check_running:
        from atualizador import app_running
        if app_running():raise ComponenteErro('Feche o Rodovia Studio antes de atualizar texturas/IA.')
    with zipfile.ZipFile(zip_path) as zf:
        m=validar(zf);stamp=time.strftime('%Y%m%d_%H%M%S');bk=raiz/'sistema'/'backups'/('componente_'+stamp);feitos=[]
        est=estado_instalado(raiz)
        try:
            for comp,dados in m['componentes'].items():
                alvo=_alvo(raiz,comp);alvo.mkdir(parents=True,exist_ok=True)
                if alvo.is_symlink():raise ComponenteErro('Destino é link: '+str(alvo))
                for rel in dados['files']:
                    dest=alvo/Path(rel).relative_to(comp)
                    if any(p.is_symlink() for p in [dest,*dest.parents] if alvo in p.parents or p==alvo):raise ComponenteErro('Link no destino: '+rel)
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    tmp=dest.with_name(dest.name+'.novo')
                    with zf.open(rel) as src,open(tmp,'wb') as out:shutil.copyfileobj(src,out,1<<22)
                    if _sha(tmp)!=dados['files'][rel]:tmp.unlink();raise ComponenteErro('Falha de gravação: '+rel)
                    if dest.exists():
                        b=bk/comp/Path(rel).relative_to(comp);b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(dest,b);feitos.append((dest,b))
                    else:feitos.append((dest,None))
                    os.replace(tmp,dest)
                est[comp]={'versao':str(dados.get('versao','?')),'instalado_em':stamp}
            (raiz/'sistema').mkdir(exist_ok=True)
            (raiz/'sistema'/'componentes.json').write_text(json.dumps(est,ensure_ascii=False,indent=1),encoding='utf-8')
        except Exception:
            for dest,b in reversed(feitos):                      # tudo ou nada: desfaz o que já foi trocado
                try:
                    if b is None:dest.unlink(missing_ok=True)
                    else:shutil.copy2(b,dest)
                except OSError:pass
            raise
    try:
        from . import texturas_pacote;texturas_pacote.limpar_cache()
    except Exception:pass
    say('Componentes instalados: '+', '.join(f"{c} {d.get('versao','?')}" for c,d in m['componentes'].items())+'. Backup em '+str(bk))
    return {'componentes':list(m['componentes']),'backup':str(bk),'stamp':stamp}

def instalar_pendentes(raiz,say=print,check_running=True):
    raiz=_raiz(raiz);res=[]
    for z in pendentes(raiz):
        try:r=instalar(raiz,z,say,check_running)
        except (ComponenteErro,zipfile.BadZipFile,ValueError,OSError) as e:
            say(f'RECUSADO {z.name}: {e}');dest=raiz/'atualizacoes'/'rejeitadas';dest.mkdir(parents=True,exist_ok=True);shutil.move(str(z),str(dest/z.name));continue
        dest=raiz/'atualizacoes'/'aplicadas';dest.mkdir(parents=True,exist_ok=True);shutil.move(str(z),str(dest/z.name));res.append(r)
    if not res:say('Nenhum pacote de componentes válido pendente.')
    return res

def restaurar(raiz,stamp=None,say=print,check_running=True):
    raiz=_raiz(raiz)
    if check_running:
        from atualizador import app_running
        if app_running():raise ComponenteErro('Feche o Rodovia Studio antes de restaurar.')
    base=raiz/'sistema'/'backups'
    opcoes=sorted(p for p in base.glob('componente_*') if p.is_dir())
    if not opcoes:raise ComponenteErro('Não há backup de componentes.')
    b=base/('componente_'+stamp) if stamp else opcoes[-1]
    if not b.is_dir():raise ComponenteErro('Backup não encontrado.')
    n=0
    for comp in DESTINOS:
        for f in (b/comp).rglob('*') if (b/comp).is_dir() else []:
            if f.is_file():
                dest=_alvo(raiz,comp)/f.relative_to(b/comp);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest);n+=1
    try:
        from . import texturas_pacote;texturas_pacote.limpar_cache()
    except Exception:pass
    say(f'{n} arquivo(s) restaurados de {b.name}.');return n

def empacotar(saida,texturas=None,ia=None,versao_texturas='1',versao_ia='1'):
    """cria um ZIP de componentes. texturas/ia = pasta de origem (ou None)."""
    comps={};arqs={}
    for nome,pasta,ver in (('texturas',texturas,versao_texturas),('ia',ia,versao_ia)):
        if not pasta:continue
        fs={}
        for f in sorted(Path(pasta).rglob('*')):
            if f.is_file() and not f.is_symlink():
                rel=nome+'/'+f.relative_to(pasta).as_posix();fs[rel]=_sha(f);arqs[rel]=f
        comps[nome]={'versao':ver,'files':fs}
    if not comps:raise ValueError('Nada a empacotar.')
    with zipfile.ZipFile(saida,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('componente.json',json.dumps({'app':'Rodovia Studio','tipo':'componentes','componentes':comps},ensure_ascii=False,indent=1))
        for rel,f in arqs.items():z.write(f,rel)
    return saida

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--raiz',default='.');ap.add_argument('--listar',action='store_true');ap.add_argument('--instalar',nargs='?',const='*');ap.add_argument('--restaurar',nargs='?',const='')
    a=ap.parse_args(argv)
    try:
        raiz=_raiz(a.raiz)
        if a.restaurar is not None:restaurar(raiz,a.restaurar or None);return 0
        if a.instalar not in (None,'*'):instalar(raiz,a.instalar);return 0
        if a.instalar=='*':
            r=instalar_pendentes(raiz);return 0
        print('Instalado:',json.dumps(estado_instalado(raiz),ensure_ascii=False));print('Pendentes:',[z.name for z in pendentes(raiz)]);return 0
    except ComponenteErro as e:print('ERRO:',e);return 2
if __name__=='__main__':sys.exit(main())
