"""2.57: instalação da IA local GRATUITA (llama.cpp MIT + SmolLM3-3B Apache-2.0, GGUF Q4_K_M) na pasta modelos_ia.

Tudo gratuito e offline depois de instalado. Duas formas:
  python -m app.ia_instalar --gguf CAMINHO.gguf --runtime PASTA_COM_llama-server [--raiz PASTA]   (arquivos já baixados)
  python -m app.ia_instalar --baixar [--raiz PASTA]  (baixa nos endereços de assets/ia_catalogo.json, HTTPS, hosts permitidos)
O manifesto modelo.json guarda o SHA-256 calculado NO SEU computador; alteração posterior bloqueia o uso. Não autentica o publicador.
"""
import hashlib,json,os,shutil,sys,urllib.request
from pathlib import Path
from urllib.parse import urlsplit

HOSTS={'huggingface.co','cdn-lfs.huggingface.co','cas-bridge.xethub.hf.co','github.com','objects.githubusercontent.com','release-assets.githubusercontent.com'}
CATALOGO=Path(__file__).resolve().parent.parent/'assets'/'ia_catalogo.json'

def _sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1<<22),b''):h.update(c)
    return h.hexdigest()

def pasta_ia(raiz=None):
    from . import small_ai
    if raiz:return Path(raiz)/'modelos_ia'
    return small_ai.assets()

def gravar_manifesto(pasta):
    pasta=Path(pasta);m=pasta/'modelo.gguf'
    if not m.is_file():raise ValueError('modelo.gguf ausente.')
    with open(m,'rb') as f:
        if f.read(4)!=b'GGUF':raise ValueError('Arquivo não é GGUF.')
    exe='llama-server.exe' if os.name=='nt' else 'llama-server'
    if not (pasta/'runtime'/exe).is_file():raise ValueError('runtime/'+exe+' ausente.')
    files={}
    for f in sorted(pasta.rglob('*')):
        if f.is_file() and not f.is_symlink() and f.name!='modelo.json' and not f.name.endswith('.part'):files[f.relative_to(pasta).as_posix()]=_sha(f)
    if len(files)>32:raise ValueError('Runtime com arquivos demais (>32).')
    data={'parameters_billions':3,'quantization':'Q4_K_M','licenca':'Apache-2.0 (modelo) / MIT (llama.cpp)','files':files}
    (pasta/'modelo.json').write_text(json.dumps(data,ensure_ascii=False,indent=1),encoding='utf-8');return data

def instalar_local(gguf,runtime,raiz=None,say=print):
    dest=pasta_ia(raiz);(dest/'runtime').mkdir(parents=True,exist_ok=True)
    gguf=Path(gguf);runtime=Path(runtime)
    if not gguf.is_file() or not runtime.is_dir():raise ValueError('Informe o .gguf e a pasta do runtime.')
    shutil.copy2(gguf,dest/'modelo.gguf')
    for f in runtime.iterdir():
        if f.is_file() and not f.is_symlink():shutil.copy2(f,dest/'runtime'/f.name)
    d=gravar_manifesto(dest);say(f'IA local instalada em {dest} ({len(d["files"])} arquivos).');return d

def _baixar(url,destino,say):
    u=urlsplit(url)
    if u.scheme!='https' or u.hostname not in HOSTS or u.username or u.password:raise ValueError('Endereço não permitido: '+url)
    class NR(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,req,fp,code,msg,hdrs,newurl):
            n=urlsplit(newurl)
            if n.scheme!='https' or n.hostname not in HOSTS:raise ValueError('Redirecionamento para host não permitido: '+str(n.hostname))
            return super().redirect_request(req,fp,code,msg,hdrs,newurl)
    op=urllib.request.build_opener(NR());tmp=Path(str(destino)+'.part');n=0
    with op.open(url,timeout=60) as r,open(tmp,'wb') as f:
        while c:=r.read(1<<22):
            f.write(c);n+=len(c)
            if n>6*1024**3:raise ValueError('Download excede 6 GiB.')
    os.replace(tmp,destino);say(f'baixado {Path(destino).name}: {n/1e6:.0f} MB');return destino

def baixar(raiz=None,say=print):
    cat=json.loads(CATALOGO.read_text(encoding='utf-8'));dest=pasta_ia(raiz);tmp=dest/'_download';tmp.mkdir(parents=True,exist_ok=True)
    try:
        _baixar(cat['modelo']['url'],dest/'modelo.gguf',say)
        z=_baixar(cat['runtime'][('windows' if os.name=='nt' else 'linux')]['url'],tmp/'runtime.zip',say)
        import zipfile
        (dest/'runtime').mkdir(exist_ok=True)
        with zipfile.ZipFile(z) as zf:
            for i in zf.infolist():
                nome=Path(i.filename)
                if i.is_dir() or nome.is_absolute() or '..' in nome.parts:continue
                with zf.open(i) as s,open(dest/'runtime'/nome.name,'wb') as o:shutil.copyfileobj(s,o)
        d=gravar_manifesto(dest);say('IA local instalada.');return d
    finally:shutil.rmtree(tmp,ignore_errors=True)

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--raiz');ap.add_argument('--gguf');ap.add_argument('--runtime');ap.add_argument('--baixar',action='store_true')
    a=ap.parse_args(argv)
    try:
        if a.gguf and a.runtime:instalar_local(a.gguf,a.runtime,a.raiz)
        elif a.baixar:baixar(a.raiz)
        else:ap.print_help();return 1
    except (ValueError,OSError) as e:print('ERRO:',e);return 2
    return 0
if __name__=='__main__':sys.exit(main())
