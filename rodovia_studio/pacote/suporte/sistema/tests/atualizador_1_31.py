"""Atualizador do Rodovia Studio (somente biblioteca padrão do Python).

Uso:
  python atualizador.py --pacote <pasta 'pacote' extraída> --raiz <pasta do Rodovia Studio>
  python atualizador.py --raiz <pasta do Rodovia Studio> --procurar   (procura o ZIP mais novo)

Organização a partir da 1.8:
  <raiz>/ABRIR RODOVIA STUDIO.cmd      executor principal
  <raiz>/ATUALIZAR RODOVIA STUDIO.cmd  aplica o ZIP mais novo encontrado
  <raiz>/projetos/                     projetos, arquivos CAD/KMZ e vídeos do usuário
  <raiz>/atualizacoes/                 coloque aqui os ZIP de atualização
  <raiz>/suporte/sistema/              programa, Python portátil, bibliotecas e recursos
  <raiz>/suporte/documentacao/         manuais, notas de versão e imagens de conferência
  <raiz>/suporte/backups/              cópias do que cada atualização substituiu
  <raiz>/suporte/logs/                 registros de instalação, atualização e erros
Instalações antigas (app/, runtime/, dados/ na raiz) são reorganizadas automaticamente,
sem apagar nada: o que não tem lugar novo vai para suporte/backups/legado_<data>.
"""
import argparse,json,os,re,shutil,sys,time,urllib.request,zipfile,filecmp,tempfile
from pathlib import Path

SYSTEM_ITEMS=['app','assets','runtime','tests','run.py','diagnostico.py','requirements.txt','requirements-dev.txt','iniciar.ps1','iniciar.sh','VERSAO.json','atualizador.py']
LOG_ITEMS=['instalacao.log','servidor_erro.log']
LEGACY_ITEMS=['INICIAR.cmd','ATUALIZAR.cmd','atualizar.ps1','LEIA-ME.txt','arquivos','PREPARAR_AMBIENTE_TESTE.cmd','_wheels_linux','_wheels_linux.log']
ZIP_RE=re.compile(r'RodoviaStudio_.*atualiza.*\.zip$',re.I)

def L(p):
    """Caminho longo no Windows (pastas do OneDrive passam facilmente de 260 caracteres)."""
    p=os.path.abspath(str(p))
    if os.name=='nt' and not p.startswith('\\\\?\\'):
        return '\\\\?\\UNC\\'+p[2:] if p.startswith('\\\\') else '\\\\?\\'+p
    return p

def version_tuple(v):
    return tuple(int(x) for x in re.findall(r'\d+',str(v))[:3]) or (0,)

def installed_version(raiz):
    for f in [Path(raiz)/'suporte/sistema/VERSAO.json',Path(raiz)/'VERSAO.json']:
        if f.exists():
            try:return json.loads(f.read_text(encoding='utf-8')).get('version','0')
            except Exception:pass
    return '0'

def find_root(path):
    """Aceita a raiz, a pasta suporte ou a pasta sistema; reconhece a organização antiga."""
    p=Path(path).resolve()
    for cand in [p,p.parent,p.parent.parent,p/'RodoviaStudio',p/'Rodovia_Studio']:
        if (cand/'suporte/sistema/app/server.py').exists():return cand,'nova'
        if (cand/'app/server.py').exists() and (cand/'app').is_dir() and not cand.name=='sistema':return cand,'antiga'
    raise ValueError('A pasta escolhida não é a do Rodovia Studio (não encontrei app\\server.py nem suporte\\sistema\\app\\server.py).')

def app_running(ports=range(8765,8785)):
    for port in ports:
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/api/health',timeout=.6) as r:
                if json.loads(r.read()).get('status')=='ok':return port
        except Exception:continue
    return None

def log(raiz,text):
    d=Path(raiz)/'suporte/logs';d.mkdir(parents=True,exist_ok=True)
    with open(d/'atualizacao.log','a',encoding='utf-8') as f:f.write(time.strftime('%Y-%m-%d %H:%M:%S ')+text+'\n')

def migrate(raiz,stamp,say=print):
    """Organização antiga -> nova. Movimentos são desfeitos se algum falhar (arquivo em uso)."""
    raiz=Path(raiz);sup=raiz/'suporte';done=[]
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
    try:
        for src,dst in plan:
            if not src.exists():continue
            if dst.exists():dst=dst.with_name(dst.name+f'_{stamp}')
            dst.parent.mkdir(parents=True,exist_ok=True);os.replace(src,dst);done.append((src,dst))
    except OSError as e:
        for src,dst in reversed(done):
            try:os.replace(dst,src)
            except OSError:pass
        raise RuntimeError(f'Não foi possível reorganizar ({e}). Feche o Rodovia Studio, o Explorer nessa pasta e tente de novo; nada foi alterado.')
    for d in ['projetos','atualizacoes','suporte/backups','suporte/logs','suporte/documentacao']:(raiz/d).mkdir(parents=True,exist_ok=True)
    say(f'Pastas reorganizadas: {len(done)} itens movidos (nada apagado).')
    return done

def apply(pacote,raiz,say=print,check_running=True):
    pacote=Path(pacote);raiz,layout=find_root(raiz)
    man=json.loads((pacote/'manifest.json').read_text(encoding='utf-8'));new=man.get('version','0')
    if check_running and (port:=app_running()):raise RuntimeError(f'O Rodovia Studio está aberto (porta {port}). Feche a janela do aplicativo e tente de novo.')
    stamp=time.strftime('%Y%m%d_%H%M%S');old=installed_version(raiz)
    say(f'Rodovia Studio {old} -> {new} em {raiz}')
    if layout=='antiga':migrate(raiz,stamp,say)
    backup=raiz/'suporte/backups'/f'antes_v{new.replace(".","_")}_{stamp}';copied=0;saved=0
    for part,dest in [('raiz',raiz),('suporte',raiz/'suporte')]:
        base=pacote/part
        if not base.exists():continue
        for f in sorted(p for p in base.rglob('*') if p.is_file()):
            rel=f.relative_to(base);target=dest/rel
            if os.path.exists(L(target)):
                if filecmp.cmp(L(f),L(target),shallow=False):continue
                b=backup/(part+'/'+rel.as_posix());os.makedirs(L(b.parent),exist_ok=True);shutil.copy2(L(target),L(b));saved+=1
            os.makedirs(L(target.parent),exist_ok=True);tmp=target.with_name(target.name+'.novo')
            shutil.copy2(L(f),L(tmp));os.replace(L(tmp),L(target));copied+=1
    for d in ['projetos','atualizacoes']:(raiz/d).mkdir(exist_ok=True)
    msg=f'Atualização {new} aplicada: {copied} arquivos novos/alterados, {saved} anteriores guardados em {backup.relative_to(raiz) if saved else "(nenhum)"}.'
    say(msg);log(raiz,msg);return {'version':new,'previous':old,'copied':copied,'backed_up':saved,'layout_before':layout,'backup':str(backup)}

def candidates(raiz):
    raiz=Path(raiz);places=[raiz/'atualizacoes',raiz,Path.home()/'Downloads']
    out=[]
    for d in places:
        if not d.exists():continue
        for z in d.glob('*.zip'):
            if not ZIP_RE.search(z.name):continue
            try:
                with zipfile.ZipFile(z) as zf:
                    name=next(n for n in zf.namelist() if n.endswith('pacote/manifest.json'))
                    out.append((version_tuple(json.loads(zf.read(name)).get('version','0')),z,name))
            except (StopIteration,zipfile.BadZipFile,KeyError,ValueError):continue
    return sorted(out,key=lambda c:(c[0],c[1].stat().st_mtime),reverse=True)

def search_and_apply(raiz,say=print,check_running=True):
    raiz,_=find_root(raiz);cur=version_tuple(installed_version(raiz));found=candidates(raiz)
    if not found:
        say('Nenhum ZIP de atualização encontrado. Salve o arquivo RodoviaStudio_<versão>_atualizacao.zip na pasta "atualizacoes" (ou em Downloads) e execute de novo.');return None
    ver,z,name=found[0]
    if ver<=cur:say(f'Já está atualizado ({".".join(map(str,cur))}). O ZIP mais novo encontrado é {z.name}.');return None
    # 1.19: extrai numa pasta temporária curta (antes, dentro do OneDrive, o caminho passava de 260 caracteres).
    tmp=Path(tempfile.mkdtemp(prefix='rs_'))
    try:
        with zipfile.ZipFile(z) as zf:
            for m in zf.infolist():
                p=Path(m.filename)
                if p.is_absolute() or '..' in p.parts:raise RuntimeError('ZIP com caminho inválido: '+m.filename)
            for m in zf.infolist():
                out=tmp/m.filename
                if m.is_dir():os.makedirs(L(out),exist_ok=True);continue
                os.makedirs(L(out.parent),exist_ok=True)
                with zf.open(m) as src,open(L(out),'wb') as dst:shutil.copyfileobj(src,dst)
        pacote=tmp/Path(name).parent
        newer=pacote/'suporte/sistema/atualizador.py'
        if newer.exists() and newer.read_bytes()!=Path(__file__).read_bytes() and not os.environ.get('RODOVIA_ATUALIZADOR_INTERNO'):
            # Usa o atualizador que veio no pacote (pode conter reorganizações novas).
            import subprocess
            env=dict(os.environ,RODOVIA_ATUALIZADOR_INTERNO='1')
            r=subprocess.run([sys.executable,str(newer),'--raiz',str(raiz),'--pacote',str(pacote)]+([] if check_running else ['--sem-verificar-aberto']),env=env)
            if r.returncode:raise RuntimeError('O atualizador do pacote informou erro (veja acima).')
            res={'version':'.'.join(map(str,ver)),'delegated':True}
        else:res=apply(pacote,raiz,say,check_running)
        dest=raiz/'atualizacoes'/'aplicadas';dest.mkdir(parents=True,exist_ok=True)
        try:
            if z.parent==raiz/'atualizacoes' or z.parent==raiz:os.replace(z,dest/z.name)
        except OSError:pass
        return res
    finally:shutil.rmtree(L(tmp),ignore_errors=True)

def main(argv=None):
    a=argparse.ArgumentParser();a.add_argument('--raiz',required=True);a.add_argument('--pacote');a.add_argument('--procurar',action='store_true');a.add_argument('--sem-verificar-aberto',action='store_true')
    o=a.parse_args(argv)
    try:
        if o.pacote:apply(o.pacote,o.raiz,check_running=not o.sem_verificar_aberto)
        else:search_and_apply(o.raiz,check_running=not o.sem_verificar_aberto)
        return 0
    except Exception as e:
        print('ERRO: '+str(e))
        try:log(find_root(o.raiz)[0],'ERRO: '+str(e))
        except Exception:pass
        return 1

if __name__=='__main__':sys.exit(main())
