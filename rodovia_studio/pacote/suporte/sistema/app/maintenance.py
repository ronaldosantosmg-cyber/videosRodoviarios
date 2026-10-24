"""Remove apenas caches regeneráveis e saídas temporárias interrompidas."""
import shutil
from pathlib import Path

CACHE_DIRS={'cache_geometria','imagery','hidrografia','render_tmp','cache_detalhe','cache_local_web'}
TEMP_FILES={'video.partial.mp4','upload.dxf.tmp','upload.kmz.tmp'}

def candidates(root):
    root=Path(root).resolve()
    if (root/'_ladrilhos').is_dir() and not (root/'_ladrilhos').is_symlink():yield root/'_ladrilhos'
    for project in root.iterdir() if root.exists() else []:
        if project.name=='_ladrilhos':continue
        if project.is_symlink() or not project.is_dir():continue
        for p in project.iterdir():
            if p.is_symlink():continue
            if p.name in CACHE_DIRS and p.is_dir():yield p
            elif p.name in TEMP_FILES and p.is_file():yield p

def size(path):
    if path.is_file():return path.stat().st_size
    return sum(p.stat().st_size for p in path.rglob('*') if p.is_file() and not p.is_symlink())

def clean(root,execute=False):
    total=0;count=0;errors=[]
    for p in candidates(root):
        try:
            n=size(p)
            if execute:
                if p.is_dir():shutil.rmtree(p)
                else:p.unlink()
            total+=n;count+=1
        except OSError as exc:errors.append(p.name+': '+str(exc))
    return {'bytes':total,'items':count,'executed':execute,'errors':errors}

# ------------------------------------------------------------------------------------------------------------
# 1.32: limpeza de resíduos por categoria (Arquivo › Limpar memória). Nunca apaga DXF/KMZ, configuração,
# imagens enviadas, marcações nem os vídeos guardados na pasta de vídeos.
import re,time
from pathlib import Path as _P

CATEGORIAS={
 'caches':('Caches regeneráveis','Ladrilhos de imagem, geometria, detalhe, hidrografia e mosaicos locais. São refeitos quando precisar (a próxima prévia/vídeo demora mais).',True),
 'temporarios':('Arquivos temporários','Vídeos interrompidos, envios incompletos, quadros de montagem e arquivos .tmp.',True),
 'registros':('Registros antigos','Registros de execução e erros com mais de 30 dias e logs de vídeo (ffmpeg) dos projetos.',True),
 'copias_config':('Cópias antigas da configuração','Cópias guardadas antes de limpar o trabalho ou aplicar modelos; ficam as 3 mais recentes de cada projeto.',True),
 'lixeira':('Lixeira','Projetos, modelos e vídeos retirados (pastas _lixeira).',True),
 'atualizacoes':('Atualizações antigas','Cópias de segurança de atualizações anteriores (ficam as 2 mais recentes) e ZIPs já aplicados (fica o mais recente).',True),
 'copias_video':('Cópias de trabalho dos vídeos','O último vídeo de cada projeto também fica dentro do projeto (video.mp4); com a cópia na pasta de vídeos, esta pode sair (a tela volta a mostrá-lo da pasta de vídeos).',False),
 'base_imagens':('Base de imagens processadas','GeoTIFFs reutilizáveis gerados a partir de ECW/MrSID. Não são temporários e ficam preservados por padrão para evitar novas conversões.',False),
}
_DAY=86400

def _projects(root):
    root=_P(root)
    for p in sorted(root.iterdir()) if root.exists() else []:
        if p.is_dir() and not p.is_symlink() and re.fullmatch(r'[0-9a-f]{32}',p.name):yield p

def _items(cat,root,install=None,videos=None,now=None):
    """Itens (arquivo ou pasta) de uma categoria."""
    root=_P(root);now=now or time.time();out=[]
    if cat=='caches':
        out+=[p for p in candidates(root) if (p.name in CACHE_DIRS and p.name!='render_tmp') or p.name=='_ladrilhos']
    elif cat=='temporarios':
        for pr in _projects(root):
            for p in pr.iterdir():
                if p.is_symlink():continue
                if (p.is_file() and (p.name in TEMP_FILES or p.suffix=='.tmp' or '.partial.' in p.name or p.name.endswith('.novo'))) or (p.is_dir() and p.name in ('render_tmp','quadros_tmp')):out.append(p)
            conv=pr/'imagem_local'/'_converter.json'
            if conv.is_file():out.append(conv)
    elif cat=='registros':
        for pr in _projects(root):
            for n in ('ffmpeg.log','worker.log','error.log'):
                if (pr/n).is_file() and now-(pr/n).stat().st_mtime>30*_DAY:out.append(pr/n)
            lg=pr/'logs'
            if lg.is_dir():out+=[f for f in lg.glob('*.jsonl') if now-f.stat().st_mtime>30*_DAY]
            snapshots=lg/'execucoes'
            if snapshots.is_dir():out+=[f for f in snapshots.glob('*.json') if now-f.stat().st_mtime>30*_DAY]
        if install is not None:
            for lg in [install/'sistema'/'logs',install/'suporte'/'logs']:
                if lg.is_dir():out+=[f for f in lg.glob('*.log') if now-f.stat().st_mtime>30*_DAY]
    elif cat=='copias_config':
        for pr in _projects(root):
            olds=sorted(pr.glob('config_antes_*.json'),key=lambda f:f.stat().st_mtime,reverse=True)
            out+=olds[3:]
    elif cat=='lixeira':
        for t in [root/'_lixeira']+([videos/'_lixeira'] if videos is not None else []):
            if t.is_dir():out+=list(t.iterdir())
    elif cat=='atualizacoes' and install is not None:
        for b in [install/'sistema'/'backups',install/'suporte'/'backups']:
            if b.is_dir():
                olds=sorted([d for d in b.iterdir() if d.is_dir() and (d.name.startswith('antes_v') or d.name.startswith('legado_'))],key=lambda d:d.stat().st_mtime,reverse=True)
                out+=olds[2:]
        ap=install/'atualizacoes'/'aplicadas'
        if ap.is_dir():out+=sorted(ap.glob('*.zip'),key=lambda f:f.stat().st_mtime,reverse=True)[1:]
    elif cat=='base_imagens':
        b=root/'_base_imagens'
        if b.is_dir():out+=[p for p in b.iterdir() if not p.is_symlink()]
    elif cat=='copias_video' and videos is not None:
        for pr in _projects(root):
            v=pr/'video.mp4';j=pr/'video.json'
            if not v.is_file() or not j.is_file():continue
            try:
                import json as _j;info=_j.loads(j.read_text(encoding='utf-8'));arq=info.get('arquivo');pasta=info.get('pasta_videos')
                target=_P(pasta)/arq if arq and pasta else None
                if target is not None and _safe_cleanup_path(target,[videos]) and target.is_file() and target.stat().st_size==v.stat().st_size:
                    import hashlib
                    with v.open('rb') as left,target.open('rb') as right:
                        if hashlib.file_digest(left,'sha256').digest()==hashlib.file_digest(right,'sha256').digest():out.append(v)
            except (OSError,ValueError):continue
    return [p for p in out if _safe_cleanup_path(p,[root,install,videos])]

def _safe_cleanup_path(path,roots):
    path=_P(path).absolute()
    for base in roots:
        if base is None:continue
        base=_P(base).absolute()
        if path==base or not path.is_relative_to(base):continue
        chain=path
        while chain!=base:
            if chain.is_symlink():break
            chain=chain.parent
        else:
            return path.resolve().is_relative_to(base.resolve())
    return False

def survey(root,install=None,videos=None):
    """Tamanho e quantidade de cada categoria (nada é apagado)."""
    res=[]
    for k,(label,desc,default) in CATEGORIAS.items():
        items=_items(k,root,install,videos);n=0
        for p in items:
            try:n+=size(p)
            except OSError:pass
        res.append({'id':k,'rotulo':label,'descricao':desc,'padrao':default,'itens':len(items),'bytes':n})
    return res

def clean_categories(root,cats,install=None,videos=None):
    bad=[c for c in cats if c not in CATEGORIAS]
    if bad or not cats:raise ValueError('Escolha ao menos uma categoria válida.')
    total=0;count=0;errors=[];by={}
    for c in cats:
        b=0
        for p in _items(c,root,install,videos):
            try:
                n=size(p)
                if p.is_dir() and not p.is_symlink():shutil.rmtree(p)
                else:p.unlink()
                total+=n;b+=n;count+=1
            except OSError as exc:errors.append(p.name+': '+str(exc)[:120])
        by[c]=b
    return {'bytes':total,'items':count,'por_categoria':by,'errors':errors}
