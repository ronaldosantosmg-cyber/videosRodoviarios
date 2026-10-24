"""1.32: arquivo de vídeos gerados. Cada geração vira um arquivo novo (nada é substituído).

Organização: <videos>/<nome do projeto>/<nome>_<AAAA-MM-DD_HHhMM>_v<NN>.mp4 + .json (ficha: data, versão do
aplicativo, resolução, qualidade, codificador, tempo de geração e a configuração usada). A pasta de cada projeto
tem um arquivo .projeto com o identificador, para dois projetos de mesmo nome não se misturarem.
O vídeo também continua em <projeto>/video.mp4 (último gerado, usado pela tela).
"""
import json,re,shutil,time,unicodedata
from pathlib import Path
from . import store

NAME_OK=re.compile(r'^[\w\-. ]+\.mp4$',re.U)

def slug(name,limit=60):
    t=unicodedata.normalize('NFC',str(name or 'Projeto'))   # acentos ficam (o Windows e o OneDrive aceitam)
    t=re.sub(r'[\\/:*?"<>|\x00-\x1f]+',' ',t);t=re.sub(r'\s+',' ',t).strip(' .')
    return (t[:limit].strip(' .') or 'Projeto')

def project_folder(pid,name,create=True):
    """Pasta do projeto dentro de <videos>; se outro projeto já usa o nome, acrescenta o início do identificador."""
    root=store.videos_root();base=slug(name)
    for cand in [base,f'{base} ({pid[:6]})']:
        d=root/cand;mark=d/'.projeto'
        if d.exists():
            try:
                if mark.read_text(encoding='utf-8').strip()==pid:return d
            except OSError:pass
            if not mark.exists() and not any(d.iterdir()):
                if create:mark.write_text(pid,encoding='utf-8')
                return d
            continue
        if create:d.mkdir(parents=True,exist_ok=True);mark.write_text(pid,encoding='utf-8')
        return d
    d=root/f'{base} ({pid})'
    if create:d.mkdir(parents=True,exist_ok=True);(d/'.projeto').write_text(pid,encoding='utf-8')
    return d

def find_folder(pid):
    """Pasta de vídeos de um projeto (mesmo que o projeto tenha sido renomeado depois)."""
    root=store.videos_root()
    if not root.exists():return None
    for d in root.iterdir():
        try:
            if d.is_dir() and (d/'.projeto').read_text(encoding='utf-8').strip()==pid:return d
        except OSError:continue
    return None

def archive(d,pid,settings,info,seconds=None,source_name='video.mp4'):
    """Copia o vídeo recém-gerado (<projeto>/video.mp4) para o arquivo de vídeos, com a ficha."""
    src=Path(d)/source_name
    if not src.exists():return None
    folder=find_folder(pid) or project_folder(pid,settings.name)
    n=1+max([int(m.group(1)) for f in folder.glob('*.mp4') if (m:=re.search(r'_v(\d+)\.mp4$',f.name))]+[0])
    stamp=time.strftime('%Y-%m-%d_%Hh%M')
    name=f'{slug(settings.name,48)}'+('_3D' if source_name=='video3d.mp4' else '')+f'_{stamp}_v{n:02d}.mp4'
    dst=folder/name;tmp=folder/(name+'.tmp')
    shutil.copyfile(src,tmp);store.replace(tmp,dst)
    from .rotas.comum import VERSION
    meta={'arquivo':name,'projeto':settings.name,'projeto_id':pid,'gerado_em':time.strftime('%Y-%m-%d %H:%M:%S'),'versao_app':VERSION,
          'motor':info.get('motor','2D'),'camera3d':info.get('camera3d'),'scene3d_revision':info.get('scene3d_revision'),'numero':n,'bytes':dst.stat().st_size,'largura':info.get('width'),'altura':info.get('height'),'fps':info.get('fps'),'duracao_s':info.get('duration_s'),
          'quadros':info.get('frames'),'codificador':info.get('encoder'),'qualidade':getattr(settings,'video_quality','padrao'),
          'tempo_geracao_s':round(seconds,1) if seconds else info.get('total_seconds'),'configuracao':settings.model_dump()}
    dst.with_suffix('.json').write_text(json.dumps(meta,ensure_ascii=False,indent=1),encoding='utf-8')
    return dst

def listing(pid):
    folder=find_folder(pid)
    if folder is None:return {'pasta':None,'videos':[]}
    out=[]
    for f in sorted(folder.glob('*.mp4'),key=lambda p:p.stat().st_mtime,reverse=True):
        meta={}
        try:meta=json.loads(f.with_suffix('.json').read_text(encoding='utf-8'))
        except (OSError,ValueError):pass
        meta.pop('configuracao',None)
        out.append({'nome':f.name,'bytes':f.stat().st_size,'data':time.strftime('%Y-%m-%d %H:%M',time.localtime(f.stat().st_mtime)),**{k:meta.get(k) for k in ('numero','largura','altura','fps','duracao_s','codificador','qualidade','tempo_geracao_s','versao_app')}})
    return {'pasta':str(folder),'videos':out}

def path_of(pid,name):
    if not NAME_OK.match(name or '') or '/' in name or '\\' in name or name.startswith('.'):raise FileNotFoundError('Vídeo não encontrado.')
    folder=find_folder(pid)
    f=(folder/name) if folder else None
    if f is None or not f.is_file():raise FileNotFoundError('Vídeo não encontrado.')
    return f

def remove(pid,name):
    """Vai para <videos>/_lixeira (a limpeza de resíduos esvazia a lixeira)."""
    f=path_of(pid,name);trash=store.videos_root()/'_lixeira';trash.mkdir(parents=True,exist_ok=True)
    dst=trash/f'{f.parent.name}__{f.name}'
    if dst.exists():dst=trash/f'{f.parent.name}__{time.strftime("%Y%m%d_%H%M%S")}__{f.name}'
    f.replace(dst)
    j=f.with_suffix('.json')
    if j.exists():j.replace(dst.with_suffix('.json'))
    return dst.name

def current(d):
    """Último vídeo do projeto: <projeto>/video.mp4 ou, se a cópia de trabalho foi limpa, o da pasta de vídeos."""
    d=Path(d);v=d/'video.mp4'
    if v.is_file():return v
    try:
        info=json.loads((d/'video.json').read_text(encoding='utf-8'))
        f=Path(info.get('pasta_videos',''))/info.get('arquivo','')
        if info.get('arquivo') and f.is_file():return f
    except (OSError,ValueError):pass
    return None
