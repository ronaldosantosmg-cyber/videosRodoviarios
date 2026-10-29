"""Instalação limpa da distribuição: somente biblioteca padrão, sem shell ou elevação."""
import argparse,hashlib,importlib.util,json,os,re,shutil,stat,subprocess,sys,tempfile,time,urllib.request,zipfile
from pathlib import Path,PurePosixPath,PureWindowsPath

class Cancelled(RuntimeError):pass

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

def emit(stage,percent=None):print(json.dumps({'stage':stage,'percent':percent},ensure_ascii=False),flush=True)

def check(cancel):
    if cancel and Path(cancel).exists():raise Cancelled('Instalação cancelada. Nenhuma instalação anterior foi alterada.')

def safe_name(name):
    if not isinstance(name,str) or not name or '\\' in name or ':' in name or '\x00' in name:raise ValueError('Caminho inválido no pacote.')
    p=PurePosixPath(name)
    if p.is_absolute() or any(part in ('..','') for part in p.parts) or PureWindowsPath(name).drive:raise ValueError('Caminho fora do pacote.')
    return p

def unpack(archive,target,prefix='',cancel=None):
    target=Path(target);total=0
    with zipfile.ZipFile(archive) as z:
        if len(z.infolist())>40000:raise ValueError('Arquivo com entradas demais.')
        for item in z.infolist():
            check(cancel);p=safe_name(item.filename)
            if stat.S_ISLNK(item.external_attr>>16):raise ValueError('Links não são aceitos no pacote.')
            total+=item.file_size
            if total>2*1024**3:raise ValueError('Arquivo descompactado excede o limite de 2 GiB.')
            if prefix and not item.filename.startswith(prefix):continue
            name=item.filename[len(prefix):] if prefix else item.filename
            if not name:continue
            dest=target.joinpath(*safe_name(name).parts)
            if item.is_dir():dest.mkdir(parents=True,exist_ok=True);continue
            dest.parent.mkdir(parents=True,exist_ok=True)
            with z.open(item) as src,dest.open('wb') as dst:shutil.copyfileobj(src,dst,1024*1024)

def verify(root,expected):
    root=Path(root);path=root/'distribuicao.json'
    if not re.fullmatch('[0-9a-f]{64}',expected) or sha(path)!=expected:raise ValueError('Manifesto de distribuição não confere com o instalador.')
    m=json.loads(path.read_text(encoding='utf-8'))
    if m.get('version')!='2.02' or m.get('architecture')!='win_amd64':raise ValueError('Versão ou arquitetura de distribuição inválida.')
    for name,digest in m['files'].items():
        f=root.joinpath(*safe_name(name).parts)
        if f.is_symlink() or not f.is_file() or sha(f)!=digest:raise ValueError('Arquivo ausente ou alterado: '+name)
    return m

def download(row,directory,cancel=None):
    name=row['filename'];safe_name(name)
    if '/' in name or not name.endswith('.whl') or not re.fullmatch('[0-9a-f]{64}',row['sha256']):raise ValueError('Dependência inválida.')
    from urllib.parse import urlparse
    if urlparse(row['url']).scheme!='https' or urlparse(row['url']).hostname!='files.pythonhosted.org':raise ValueError('Origem de dependência não autorizada.')
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True);dest=directory/name
    if dest.is_file() and sha(dest)==row['sha256']:return dest
    temp=dest.with_suffix(dest.suffix+'.download')
    try:
        with urllib.request.urlopen(row['url'],timeout=60) as response,temp.open('wb') as output:
            if urlparse(response.url).scheme!='https' or urlparse(response.url).hostname!='files.pythonhosted.org':raise ValueError('Redirecionamento de dependência não autorizado.')
            size=0
            while True:
                check(cancel);chunk=response.read(1024*1024)
                if not chunk:break
                size+=len(chunk)
                if size>row['bytes']:raise ValueError('Dependência excede o tamanho aprovado.')
                output.write(chunk);emit('Baixando '+name,round(size/row['bytes']*100,1))
        if size!=row['bytes'] or sha(temp)!=row['sha256']:raise ValueError('Hash ou tamanho da dependência não confere: '+name)
        temp.replace(dest);return dest
    finally:temp.unlink(missing_ok=True)

def run(args,cancel=None,cwd=None):
    check(cancel)
    with tempfile.TemporaryFile(mode='w+b') as log:
        process=subprocess.Popen([str(a) for a in args],cwd=cwd,stdout=log,stderr=subprocess.STDOUT,shell=False)
        try:
            while process.poll() is None:check(cancel);time.sleep(.15)
        except BaseException:
            process.terminate()
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:process.kill();process.wait()
            raise
        if process.returncode:
            log.seek(0);message=log.read()[-12000:].decode('utf-8',errors='replace')
            raise RuntimeError('Falha ao preparar componente local:\n'+message)

def destination(path):
    p=Path(path).expanduser().absolute()
    if p.exists() or p.is_symlink():raise ValueError('Escolha uma pasta nova. Instalações e dados existentes não serão sobrescritos.')
    if not p.name or p==p.parent or len(str(p))>160:raise ValueError('Escolha uma pasta local curta, fora da raiz do disco.')
    if any(x.is_symlink() or getattr(x,'is_junction',lambda:False)() for x in [p.parent,*p.parent.parents]):raise ValueError('Pasta de instalação não pode atravessar links.')
    return p

def install(root,target,expected,cancel=None):
    if os.name!='nt' or sys.maxsize<=2**32:raise RuntimeError('Instalador destinado ao Windows x64.')
    root=Path(root);m=verify(root,expected);target=destination(target);target.parent.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(target.parent).free<3*1024**3:raise RuntimeError('Reserve pelo menos 3 GiB livres para instalar e gerar vídeos.')
    # Só esta pasta temporária criada pela operação pode ser removida em caso de falha.
    stage=Path(tempfile.mkdtemp(prefix='.rodovia-instalar-',dir=target.parent));committed=False
    try:
        emit('Conferindo e instalando o programa');extracted=stage/'_pacote';unpack(root/'payload/aplicativo.zip',extracted,cancel=cancel)
        updater=extracted/'pacote/suporte/sistema/atualizador.py';spec=importlib.util.spec_from_file_location('rs_installer_updater',updater);u=importlib.util.module_from_spec(spec)
        previous=sys.dont_write_bytecode;sys.dont_write_bytecode=True
        try:spec.loader.exec_module(u)
        finally:sys.dont_write_bytecode=previous
        # apply é para instalações existentes. Na pasta nova, reutiliza validação e
        # mapeamento do atualizador, sem fabricar uma versão anterior/rollback fictício.
        u.validate_package(extracted/'pacote',say=lambda *a:None)
        for source,dest,_ in u._targets(extracted/'pacote',stage):
            check(cancel);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
        for name in u.DATA_DIRS:(stage/name).mkdir(exist_ok=True)
        shutil.rmtree(extracted)
        program=stage/'sistema/programa';runtime=program/'runtime';emit('Preparando Python 3.12 local');unpack(root/'payload/python.nupkg',runtime,'tools/',cancel)
        python=runtime/'python.exe';wheels=program/'pacotes'
        for row in m['dependencies']:download(row,wheels,cancel)
        emit('Instalando bibliotecas e FFmpeg');run([python,'-m','ensurepip','--default-pip'],cancel,program)
        for lock in ('pip-bootstrap.lock','requirements-windows.lock'):
            run([python,'-m','pip','--isolated','install','--no-index','--find-links',wheels,'--only-binary=:all:','--require-hashes','--disable-pip-version-check','-r',program/lock],cancel,program)
        run([python,'-m','pip','check'],cancel,program)
        emit('Verificando imagens georreferenciadas, cálculos e vídeo H.264');run([python,'-c','import rasterio; assert rasterio.__gdal_version__'],cancel,program);run([python,program/'diagnostico.py'],cancel,program)
        shutil.copy2(root/'payload/Rodovia Studio.exe',stage/'Rodovia Studio.exe')
        shutil.copytree(root/'payload/webview2',program/'webview2',dirs_exist_ok=True)
        (runtime/'dependencias.ok').write_text(sha(program/'requirements-windows.lock')+'\n')
        (stage/'sistema/distribuicao.json').write_text(json.dumps({'version':m['version'],'installation_complete':False,'publisher':'Ronaldo Santos','installer_manifest_sha256':expected,'authenticode_signed':m['authenticode_signed'],'python':'3.12.10','source_zip_sha256':m['files']['payload/aplicativo.zip']},ensure_ascii=False,indent=2)+'\n')
        check(cancel)
        if target.exists():raise ValueError('A pasta de destino passou a existir. Nada foi sobrescrito.')
        stage.rename(target);committed=True
        try:
            final_python=target/'sistema/programa/runtime/python.exe';final_program=target/'sistema/programa'
            run([final_python,'-c','import rasterio; assert rasterio.__gdal_version__'],cancel=None,cwd=final_program)
            run([final_python,final_program/'diagnostico.py'],cancel=None,cwd=final_program)
        except Exception:
            # O destino já pode ter recebido arquivos do usuário. Nunca removê-lo.
            emit('Verificação final falhou. Pasta preservada para diagnóstico: '+str(target));raise
        report=target/'sistema/distribuicao.json';data=json.loads(report.read_text());data['installation_complete']=True;report.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        emit('Concluído. Abra Rodovia Studio.exe na pasta escolhida.',100)
        return target
    finally:
        if not committed and stage.exists():shutil.rmtree(stage)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raiz',required=True);p.add_argument('--destino',required=True);p.add_argument('--manifest-sha',required=True);p.add_argument('--cancelar');a=p.parse_args()
    try:install(a.raiz,a.destino,a.manifest_sha,a.cancelar)
    except Cancelled as e:emit(str(e));sys.exit(2)
    except Exception as e:emit('Falhou: '+str(e));sys.exit(1)
