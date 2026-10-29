"""Gera a opção de instalação nova da 2.02 sem modificar o ZIP de atualização aprovado."""
import argparse,concurrent.futures,hashlib,json,os,re,shutil,subprocess,sys,tempfile,urllib.request,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1];BASE=REPO/'rodovia_studio/pacote/suporte/sistema'
PYTHON_URL='https://api.nuget.org/v3-flatcontainer/python/3.12.10/python.3.12.10.nupkg'
PYTHON_SHA='0eb85c2dfccccf1b17352de4c397f69194035b7d37149eacc16f1147d93de3b8'
APP_SHA='2654167d0fadbf9b293f15ecd8bdf89eccc19c069b137ee630f1c0863b7bc0ed'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def get(url):
    with urllib.request.urlopen(url,timeout=60) as r:return r.read()

def dependencies():
    rows=[]
    for line in (BASE/'requirements-windows.lock').read_text().splitlines():
        m=re.fullmatch(r'([\w-]+)==([^ ]+) --hash=sha256:([0-9a-f]{64})',line)
        if m:rows.append(m.groups())
        elif line.strip() and not line.startswith('#'):raise RuntimeError('Dependência sem hash fixo.')
    def resolve(row):
        name,version,digest=row;data=json.loads(get(f'https://pypi.org/pypi/{name}/{version}/json'))
        files=[f for f in data['urls'] if f['digests']['sha256']==digest and f['packagetype']=='bdist_wheel']
        if len(files)!=1:raise RuntimeError('Wheel aprovado não encontrado: '+name)
        f=files[0]
        if not f['filename'].endswith(('-win_amd64.whl','-any.whl')):raise RuntimeError('Wheel não é Windows x64/universal: '+name)
        return dict(name=name,version=version,filename=f['filename'],sha256=digest,bytes=f['size'],url=f['url'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:return list(pool.map(resolve,rows))

def validate_dependencies(rows,cache):
    # Confere os arquivos reais e as dependências avaliando marcadores do Windows,
    # pois pip --platform sozinho ainda pode avaliar marcadores do host Linux.
    import email
    from packaging.requirements import Requirement
    from packaging.markers import default_environment
    from packaging.specifiers import SpecifierSet
    from packaging.utils import canonicalize_name
    versions={canonicalize_name(r['name']):r['version'] for r in rows}
    environment=default_environment();environment.update(sys_platform='win32',platform_system='Windows',os_name='nt',platform_machine='AMD64',python_version='3.12',python_full_version='3.12.10',extra='')
    for row in rows:
        path=Path(cache)/'wheels'/row['filename']
        if not path.is_file() or path.stat().st_size!=row['bytes'] or sha(path)!=row['sha256']:raise RuntimeError('Baixe e confira o wheel antes de empacotar: '+row['filename'])
        with zipfile.ZipFile(path) as z:
            if z.testzip():raise RuntimeError('Wheel corrompido: '+row['filename'])
            metadata=email.message_from_bytes(z.read(next(n for n in z.namelist() if n.endswith('.dist-info/METADATA'))))
        if metadata.get('Requires-Python') and '3.12.10' not in SpecifierSet(metadata['Requires-Python']):raise RuntimeError('Versão Python incompatível: '+row['name'])
        for value in metadata.get_all('Requires-Dist',[]):
            dependency=Requirement(value)
            if dependency.marker is not None and not dependency.marker.evaluate(environment):continue
            name=canonicalize_name(dependency.name)
            if name not in versions or versions[name] not in dependency.specifier:raise RuntimeError('Dependência Windows ausente/incompatível: '+str(dependency))
    return {'wheel_count':len(rows),'bytes':sum(r['bytes'] for r in rows),'windows_markers_checked':True,'hashes_checked':True,'python':'3.12.10'}

def compiler():
    if os.name=='nt':return [str(Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe')]
    root=Path(os.environ.get('MONO_ROOT','/workspace/.tools/mono'))
    os.environ.update(MONO_PATH=str(root/'usr/lib/mono/4.5'),MONO_CFG_DIR=str(root/'etc'),LD_LIBRARY_PATH=str(root/'usr/lib')+':'+str(root/'usr/lib/x86_64-linux-gnu'))
    return [str(root/'usr/bin/mono-sgen'),str(root/'usr/lib/mono/4.5/mcs.exe')]

def compile_cs(source,output,assembly,webview=None):
    common=['/nologo','/win32manifest:'+str(HERE/'aplicativo.manifest'),'/target:winexe','/platform:x64','/r:System.Windows.Forms.dll','/r:System.Drawing.dll','/out:'+str(output)]
    if webview:common+=['/define:WEBVIEW2','/r:'+str(webview/'Microsoft.Web.WebView2.Core.dll'),'/r:'+str(webview/'Microsoft.Web.WebView2.WinForms.dll')]
    else:common+=['/r:System.Web.Extensions.dll','/r:System.IO.Compression.dll','/r:System.IO.Compression.FileSystem.dll']
    subprocess.run(compiler()+common+[str(assembly),str(source)],check=True)
    if os.name!='nt':
        # mcs aceita /win32manifest, mas pode não gravá-lo no PE. Segunda passagem
        # com .res explícito conserva VERSIONINFO e garante RT_MANIFEST.
        from recursos_pe import resources
        resource=output.with_suffix('.res');resource.write_bytes(resources(output.read_bytes(),(HERE/'aplicativo.manifest').read_bytes()))
        flags=[f for f in common if not f.startswith('/win32manifest:')]+['/win32res:'+str(resource)]
        subprocess.run(compiler()+flags+[str(assembly),str(source)],check=True)
        resource.unlink()
    if b'asInvoker' not in output.read_bytes():raise RuntimeError('Manifesto asInvoker não foi incorporado no executável.')

def sign(path,args):
    if not args.certificado:return
    if os.name!='nt' or not args.timestamp:raise RuntimeError('Assinatura requer Windows, certificado do titular e carimbo HTTPS do emissor.')
    subprocess.run(['powershell.exe','-NoProfile','-File',str(HERE/'assinar.ps1'),'-Arquivo',str(path),'-Thumbprint',args.certificado,'-TimestampUrl',args.timestamp],check=True)

def build(args):
    app=REPO/'atualizacoes/RodoviaStudio_2_02_atualizacao.zip'
    if sha(app)!=APP_SHA:raise RuntimeError('O ZIP 2.02 não corresponde à revisão aprovada.')
    approval=json.loads((REPO/'rodovia_studio/evidencias/2.02/entrega-validada/resultado.json').read_text())
    if approval['version']!='2.02' or approval['pytest']!={'tests':995,'failures':0,'errors':0,'skipped':0}:raise RuntimeError('Aprovação da aplicação não encontrada.')
    proof=json.loads((HERE/'evidencias/testes.json').read_text())
    if not proof.get('approved') or proof['source_sha256']!=source_digest():raise RuntimeError('Execute validar_instalador.py antes de gerar o pacote.')
    cache=Path(args.cache);cache.mkdir(parents=True,exist_ok=True);python=cache/'python.3.12.10.nupkg'
    if not python.is_file():python.write_bytes(get(PYTHON_URL))
    if sha(python)!=PYTHON_SHA:raise RuntimeError('O Python oficial não corresponde ao hash auditado.')
    output=REPO/'atualizacoes/RodoviaStudio_2_02_instalacao_completa_r2.zip'
    if output.exists():raise RuntimeError('Instalador histórico já existe; não será sobrescrito.')
    deps=dependencies();dependency_proof=validate_dependencies(deps,cache);evidence=HERE/'evidencias';evidence.mkdir(exist_ok=True)
    (evidence/'dependencias-verificadas.json').write_text(json.dumps(dependency_proof,indent=2)+'\n')
    with tempfile.TemporaryDirectory(prefix='rs_distribution_') as temporary:
        stage=Path(temporary)/'Rodovia Studio 2.02';stage.mkdir();payload=stage/'payload';payload.mkdir()
        shutil.copy2(app,payload/'aplicativo.zip');shutil.copy2(python,payload/'python.nupkg');shutil.copy2(HERE/'instalar.py',stage/'instalar.py');shutil.copy2(HERE/'LEIA-ME.txt',stage/'LEIA-ME.txt')
        webview=Path(os.environ.get('WEBVIEW2_LIB','/workspace/.tools/webview2'));target=payload/'webview2';target.mkdir()
        for name in ('Microsoft.Web.WebView2.Core.dll','Microsoft.Web.WebView2.WinForms.dll'):shutil.copy2(webview/name,target/name)
        # Avisos/licenças oficiais do SDK também acompanham sua redistribuição.
        sdk=webview.parent/'webview2.nupkg'
        if not sdk.is_file():raise RuntimeError('Forneça o pacote original webview2.nupkg para incluir seus avisos e licença.')
        with zipfile.ZipFile(sdk) as z:
            for name in ('LICENSE.txt','NOTICE.txt'):(target/name).write_bytes(z.read(name))
            for name in ('Microsoft.Web.WebView2.Core.dll','Microsoft.Web.WebView2.WinForms.dll'):
                if hashlib.sha256(z.read('lib/net462/'+name)).hexdigest()!=sha(target/name):raise RuntimeError('DLL WebView2 de versão diferente do SDK.')
            loader=z.read('runtimes/win-x64/native/WebView2Loader.dll')
            import struct
            if loader[:2]!=b'MZ' or struct.unpack_from('<H',loader,struct.unpack_from('<I',loader,0x3c)[0]+4)[0]!=0x8664:raise RuntimeError('WebView2Loader precisa ser Windows x64.')
            (target/'WebView2Loader.dll').write_bytes(loader)
        assembly=Path(temporary)/'AssemblyInfo.cs';assembly.write_text('using System.Reflection;\n[assembly: AssemblyCompany("Ronaldo Santos")]\n[assembly: AssemblyCopyright("Ronaldo Santos")]\n[assembly: AssemblyProduct("Rodovia Studio")]\n[assembly: AssemblyFileVersion("2.2.0.0")]\n[assembly: AssemblyVersion("2.2.0.0")]\n')
        compile_cs(BASE/'iniciador/RodoviaStudio.cs',payload/'Rodovia Studio.exe',assembly,target);sign(payload/'Rodovia Studio.exe',args)
        manifest=dict(version='2.02',installer_revision=2,architecture='win_amd64',publisher='Ronaldo Santos',authenticode_signed=bool(args.certificado),first_install_internet=True,python_origin=PYTHON_URL,dependencies=deps,dependency_download_bytes=sum(d['bytes'] for d in deps),files={p.relative_to(stage).as_posix():sha(p) for p in sorted(stage.rglob('*')) if p.is_file()})
        (stage/'distribuicao.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');digest=sha(stage/'distribuicao.json')
        source=Path(temporary)/'Instalador.cs';source.write_text((HERE/'Instalador.cs').read_text().replace('@MANIFEST_SHA@',digest).replace('@SIGNING_NOTICE@','Assinado com certificado de Ronaldo Santos.' if args.certificado else 'Sem certificado Authenticode: o Windows pode mostrar fornecedor desconhecido.'),encoding='utf-8')
        compile_cs(source,stage/'INSTALAR RODOVIA STUDIO.exe',assembly);sign(stage/'INSTALAR RODOVIA STUDIO.exe',args)
        # Conferência final do conteúdo que será instalado, independente da compilação.
        import instalar
        instalar.verify(stage,digest)
        with zipfile.ZipFile(payload/'python.nupkg') as z:assert 'tools/python.exe' in z.namelist() and any('ensurepip' in n for n in z.namelist())
        with zipfile.ZipFile(output.with_suffix('.zip.tmp'),'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for p in sorted(stage.rglob('*')):
                if p.is_file():z.write(p,stage.name+'/'+p.relative_to(stage).as_posix())
        temporary_zip=output.with_suffix('.zip.tmp')
        with zipfile.ZipFile(temporary_zip) as z:
            if z.testzip():raise RuntimeError('Falha de integridade do instalador.')
        temporary_zip.rename(output)
        report=dict(zip=output.name,sha256=sha(output),bytes=output.stat().st_size,manifest_sha256=digest,source_zip_sha256=APP_SHA,source_unchanged=True,dependency_download_bytes=manifest['dependency_download_bytes'],dependency_count=len(deps),authenticode_signed=bool(args.certificado),platform_tested='Linux/Mono; não instalação nativa Windows',publisher='Ronaldo Santos')
        (evidence/'pacote.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(evidence/'distribuicao.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        output.with_suffix('.sha256.txt').write_text(sha(output)+'  '+output.name+'\n');print(json.dumps(report))

def source_digest():
    h=hashlib.sha256()
    for f in sorted([HERE/'instalar.py',HERE/'Instalador.cs',HERE/'assinar.ps1',HERE/'gerar_instalador.py',HERE/'LEIA-ME.txt',HERE/'aplicativo.manifest',HERE/'recursos_pe.py']):h.update(f.name.encode());h.update(f.read_bytes())
    return h.hexdigest()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cache',default='/tmp/rodovia-distribuicao-cache');p.add_argument('--certificado');p.add_argument('--timestamp');build(p.parse_args())
