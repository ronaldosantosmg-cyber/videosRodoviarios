"""2.57: texturas rasterizadas que fazem parte do pacote (assets/texturas), com catálogo verificável.

As imagens são ladrilhos sem emenda feitos das fotos de referência do usuário. Ausentes ou alteradas → o motor volta às texturas
procedurais (nada quebra). O catálogo texturas.json guarda SHA-256, escala física e média de cor de cada ladrilho.
"""
import hashlib,json
from pathlib import Path
import numpy as np

PASTA=Path(__file__).resolve().parent.parent/'assets'/'texturas'
_cache={}

def _sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def catalogo(pasta=None):
    pasta=Path(pasta or PASTA);f=pasta/'texturas.json'
    if not f.is_file() or f.is_symlink() or f.stat().st_size>262144:return None
    try:d=json.loads(f.read_text(encoding='utf-8'))
    except (ValueError,OSError):return None
    return d if isinstance(d,dict) and isinstance(d.get('texturas'),dict) else None

def gerar_catalogo(pasta=None,versao='1',escalas=None):
    """(re)gera texturas.json a partir dos .jpg/.png da pasta."""
    from PIL import Image
    pasta=Path(pasta or PASTA);escalas=escalas or {};out={}
    for f in sorted(pasta.glob('*')):
        if f.suffix.lower() not in ('.jpg','.jpeg','.png') or f.is_symlink():continue
        im=Image.open(f).convert('RGB');a=np.asarray(im.resize((64,64)),np.float64)
        out[f.stem]={'arquivo':f.name,'sha256':_sha(f),'tamanho':list(im.size),'ladrilho':f.stem in escalas,'escala_m':escalas.get(f.stem),'media_rgb':[round(float(x),1) for x in a.mean((0,1))]}
    (pasta/'texturas.json').write_text(json.dumps({'versao':versao,'origem':'fotos de referência do usuário (recortes sem emenda)','texturas':out},ensure_ascii=False,indent=1),encoding='utf-8')
    return out

def status(pasta=None):
    pasta=Path(pasta or PASTA);cat=catalogo(pasta)
    if cat is None:return {'ok':False,'versao':None,'faltando':['texturas.json'],'alteradas':[],'total':0}
    falta=[];alt=[]
    for k,v in cat['texturas'].items():
        f=pasta/v['arquivo']
        if not f.is_file():falta.append(v['arquivo'])
        elif _sha(f)!=v['sha256']:alt.append(v['arquivo'])
    return {'ok':not falta and not alt,'versao':cat.get('versao'),'faltando':falta,'alteradas':alt,'total':len(cat['texturas'])}

def _carregar(nome):
    if nome in _cache:return _cache[nome]
    a=None
    try:
        cat=catalogo()
        v=cat['texturas'][nome] if cat else None
        if v and v.get('ladrilho'):
            f=PASTA/v['arquivo']
            if f.is_file() and not f.is_symlink() and _sha(f)==v['sha256']:
                from PIL import Image
                im=np.asarray(Image.open(f).convert('L'),np.float32)/255.
                a=(im/max(float(im.mean()),1e-3),float(v['escala_m']))
    except Exception:a=None
    _cache[nome]=a;return a

def limpar_cache():_cache.clear()

def detalhe(nome,X,Y,forca=1.0):
    """fator multiplicativo de luminância (média ≈ 1) do ladrilho amostrado em coordenadas de mundo X,Y (m); None se indisponível."""
    t=_carregar(nome)
    if t is None:return None
    a,esc=t;n=a.shape[0]
    u=(np.asarray(X)/esc)%1.0*n;v=(np.asarray(Y)/esc)%1.0*n
    i0=np.floor(u).astype(int)%n;j0=np.floor(v).astype(int)%n;i1=(i0+1)%n;j1=(j0+1)%n;fu=u-np.floor(u);fv=v-np.floor(v)
    r=(a[j0,i0]*(1-fu)+a[j0,i1]*fu)*(1-fv)+(a[j1,i0]*(1-fu)+a[j1,i1]*fu)*fv
    return 1+(r-1)*forca
