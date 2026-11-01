"""2.29: Central do projeto — um só lugar que lê e organiza ENTRADAS, DERIVADOS e RESULTADOS de um projeto.

Camadas (o que cada uma é e o que pode acontecer com ela):
  entradas   : DXF/KMZ, camadas extras, imagem local, elevação e a configuração (config.json). Nunca são apagadas aqui.
  derivados  : análise, editor, vetores e rede de tráfego. Recalculáveis a partir das entradas.
  resultados : prévia, vídeos, cena 3D e caches de imagem. Recalculáveis, podem ser grandes.
Limpeza protegida: nada é apagado; os arquivos vão para `_limpeza/<data>/` e podem ser restaurados (`desfazer`).
Escopos: resultados · derivados · dxf_novo (derivados + resultados + escolhas presas ao desenho anterior).
A limpeza de configuração por grupos (obras, fluxos…) continua em `workreset` e aparece aqui como `grupos`.
"""
from .falhas import registrar as _falha
import hashlib,json,shutil,time
from pathlib import Path

DERIVADOS=('analysis.json','editor.json','vectors.json','traffic_network.json','editor','_cache')
RESULTADOS=('preview.png','preview.json','video.mp4','video.json','video.partial.mp4','scene3d.json','video3d.mp4','video3d.json','cache_detalhe')
ENTRADAS=('input.dxf','input.kmz','camadas','imagem_local','elevacao','config.json')
PROTEGIDOS=set(ENTRADAS)|{'_limpeza','_lixeira','central.json'}|{'config_antes_limpeza_'}  # prefixos tratados abaixo
ESCOPOS={
    'resultados':('Vídeos, prévias, cena 3D e caches de imagem',RESULTADOS),
    'derivados':('Análise, editor, vetores e rede de tráfego (recalculáveis)',DERIVADOS),
    'dxf_novo':('Tudo que depende do desenho anterior: derivados, resultados e escolhas de sentido de eixos que não existem mais',DERIVADOS+RESULTADOS),
}

def _sha(path,limite=64*1024*1024):
    h=hashlib.sha256();p=Path(path)
    try:
        with p.open('rb') as f:
            n=0
            while True:
                b=f.read(1<<20)
                if not b:break
                h.update(b);n+=len(b)
                if n>=limite:h.update(str(p.stat().st_size).encode());break
    except OSError as e:_falha(__name__,e);return ''
    return h.hexdigest()

def _tamanho(p):
    p=Path(p)
    if p.is_file():return p.stat().st_size
    if p.is_dir():
        t=0
        for f in p.rglob('*'):
            try:
                if f.is_file():t+=f.stat().st_size
            except OSError as e:_falha(__name__,e)
        return t
    return 0

def _mtime(p):
    p=Path(p)
    try:
        if p.is_file():return p.stat().st_mtime
        if p.is_dir():
            ms=[f.stat().st_mtime for f in p.rglob('*') if f.is_file()]
            return max(ms) if ms else p.stat().st_mtime
    except OSError as e:_falha(__name__,e)
    return 0.0

def _carregar(d):
    f=Path(d)/'central.json'
    try:return json.loads(f.read_text(encoding='utf-8')) if f.exists() else {}
    except (OSError,ValueError) as e:_falha(__name__,e);return {}

def _gravar(d,dados):
    f=Path(d)/'central.json';tmp=f.with_suffix('.tmp');tmp.write_text(json.dumps(dados,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8');tmp.replace(f)

def impressao_dxf(d):
    """Assinatura do desenho de entrada (DXF + KMZ + camadas extras). Muda quando um novo DXF é carregado."""
    d=Path(d);h=hashlib.sha256();ok=False
    for n in ('input.dxf','input.kmz'):
        f=d/n
        if f.is_file():h.update(n.encode());h.update(_sha(f).encode());ok=True
    c=d/'camadas'
    if c.is_dir():
        for f in sorted(c.glob('*')):
            if f.is_file():h.update(f.name.encode());h.update(_sha(f).encode());ok=True
    return h.hexdigest() if ok else ''

def _chaves_orfas(d,settings):
    """Escolhas de sentido/tipo por eixo cuja impressão digital não existe na análise atual."""
    rd=dict(getattr(settings,'route_directions',None) or {});at=dict(getattr(settings,'axis_types',None) or {})
    try:a=json.loads((Path(d)/'analysis.json').read_text(encoding='utf-8'))
    except (OSError,ValueError):return None   # sem análise: não dá para saber
    vivas={r.get('direction_key') for r in a.get('routes',[]) if r.get('direction_key')}
    ro=sorted(k for k,v in rd.items() if k.startswith('axis:') and k not in vivas and v!='auto')
    to=sorted(k for k,v in at.items() if k.startswith('axis:') and k not in vivas and v!='auto')
    return {'route_directions':ro,'axis_types':to}

def estado(d,settings=None):
    """Retrato somente-leitura do projeto: o que existe, o que está desatualizado e o que está protegido."""
    d=Path(d)
    if settings is None:
        from .project_state import read_config
        settings=read_config(d)
    reg=_carregar(d);atual=impressao_dxf(d)
    if atual and not reg.get('dxf'):reg['dxf']=conferir_dxf(d)   # primeira leitura: registra a base de comparação
    mudou=bool(reg.get('dxf')) and bool(atual) and reg['dxf'].get('impressao')!=atual
    ent=[]
    for n in ENTRADAS:
        p=d/n
        if p.exists():ent.append({'nome':n,'bytes':_tamanho(p),'tipo':'pasta' if p.is_dir() else 'arquivo','sha12':(_sha(p)[:12] if p.is_file() and n!='config.json' else '')})
    base=max([_mtime(d/n) for n in ('input.dxf','input.kmz','camadas','config.json')]+[0.0])
    def listar(nomes):
        out=[]
        for n in nomes:
            p=d/n
            if p.exists():out.append({'nome':n,'bytes':_tamanho(p),'modificado':time.strftime('%Y-%m-%d %H:%M',time.localtime(_mtime(p))),'desatualizado':_mtime(p)<base})
        return out
    from .workreset import GROUPS
    data=settings.model_dump() if hasattr(settings,'model_dump') else dict(settings)
    grupos=[{'id':k,'rotulo':v[0],'itens':sum(len(data.get(c) or []) if isinstance(data.get(c),(list,dict)) else 0 for c in v[1])} for k,v in GROUPS.items()]
    orf=_chaves_orfas(d,settings);n_orf=0 if orf is None else len(orf['route_directions'])+len(orf['axis_types'])
    limp=sorted((d/'_limpeza').glob('*')) if (d/'_limpeza').is_dir() else []
    alertas=[]
    if mudou:alertas.append('O desenho (DXF/KMZ) mudou desde a última conferência: derivados e resultados podem estar desatualizados. Use a limpeza “Novo DXF”.')
    if n_orf:alertas.append(f'{n_orf} escolha(s) de sentido/tipo por eixo não correspondem a nenhum eixo da análise atual e não têm efeito.')
    return {'entradas':ent,'configuracao':grupos,'derivados':listar(DERIVADOS),'resultados':listar(RESULTADOS),
            'dxf':{'impressao':atual[:16],'registrada':(reg.get('dxf',{}).get('impressao','')[:16]),'mudou':mudou},
            'orfas':orf,'protecao':{'copias_de_configuracao':len(list(d.glob('config_antes_limpeza_*.json'))),'limpezas_restauraveis':[p.name for p in limp][-10:]},
            'dependencias':{k:invalida(k) for k in ('route_directions','lanes_per_direction','traffic_density','texture_params','weather','width','crs')},'alertas':alertas,'escopos':{k:{'rotulo':v[0],'itens':[n for n in v[1] if (d/n).exists()]} for k,v in ESCOPOS.items()}}

def invalida(chave):
    """O que é recalculado quando a configuração `chave` muda (mesma regra de `dependencies.revisions`).
    Devolve a lista de saídas afetadas, da mais básica à mais final."""
    from .dependencies import TRAFFIC,SIMULATION,CAMERA,VISUAL,PREVIEW_ONLY
    out=[]
    if chave not in TRAFFIC|CAMERA|VISUAL:out+=['geometria','rede de tráfego','editor','prévia','vídeo','cena 3D']
    elif chave in TRAFFIC and chave not in SIMULATION:out+=['rede de tráfego','editor','prévia','vídeo','cena 3D']
    elif chave in SIMULATION:out+=['prévia','vídeo','cena 3D']
    elif chave in VISUAL:out+=['prévia','vídeo','cena 3D']
    elif chave in PREVIEW_ONLY:out+=['prévia']
    elif chave in CAMERA:out+=['prévia','vídeo']
    return out

def conferir_dxf(d):
    """Registra a impressão atual do desenho como a conferida (após limpar ou ao abrir um projeto novo)."""
    reg=_carregar(d);reg['dxf']={'impressao':impressao_dxf(d),'quando':time.strftime('%Y-%m-%d %H:%M:%S')};_gravar(d,reg);return reg['dxf']

def limpar(d,settings,escopo,confirmar=False):
    """Limpeza protegida. Devolve (novas_settings, resumo). Sem `confirmar` apenas simula (nada é movido nem alterado)."""
    if escopo not in ESCOPOS:raise ValueError('Escopo de limpeza inválido. Use: '+', '.join(ESCOPOS)+'.')
    d=Path(d);alvos=[n for n in ESCOPOS[escopo][1] if (d/n).exists()]
    for n in alvos:
        if n in ENTRADAS or n.startswith('_') and n in ('_limpeza','_lixeira'):raise ValueError('Entradas do projeto não podem ser limpas.')
    novas=settings;removidas={}
    if escopo=='dxf_novo':
        orf=_chaves_orfas(d,settings)
        if orf is not None and (orf['route_directions'] or orf['axis_types']):
            data=settings.model_dump();
            for k in orf['route_directions']:data['route_directions'].pop(k,None)
            for k in orf['axis_types']:data['axis_types'].pop(k,None)
            removidas=orf
            from .models import Settings
            novas=Settings.model_validate(data)
    resumo={'escopo':escopo,'simulacao':not confirmar,'movidos':alvos,'escolhas_removidas':{k:len(v) for k,v in removidas.items()},'pasta':''}
    if not confirmar:return settings,resumo
    stamp=time.strftime('%Y%m%d_%H%M%S');dest=d/'_limpeza'/stamp;k=1
    while dest.exists():dest=d/'_limpeza'/f'{stamp}_{k}';k+=1
    dest.mkdir(parents=True)
    # cópia da configuração antes de alterar (permite voltar atrás mesmo das escolhas removidas)
    (dest/'config_antes.json').write_text(json.dumps(settings.model_dump(),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    for n in alvos:
        try:shutil.move(str(d/n),str(dest/n))
        except OSError as e:_falha(__name__,e)
    (dest/'resumo.json').write_text(json.dumps({**resumo,'simulacao':False},ensure_ascii=False,indent=2),encoding='utf-8')
    resumo['pasta']=dest.name
    if escopo=='dxf_novo':conferir_dxf(d)
    return novas,resumo

def desfazer(d):
    """Restaura a última limpeza: devolve os arquivos e a configuração anterior."""
    d=Path(d);pastas=sorted((d/'_limpeza').glob('*')) if (d/'_limpeza').is_dir() else []
    if not pastas:raise ValueError('Não há limpeza para desfazer neste projeto.')
    p=pastas[-1];from .models import Settings;from .migration import migrate
    for item in p.iterdir():
        if item.name in ('config_antes.json','resumo.json'):continue
        alvo=d/item.name
        if alvo.exists():
            if alvo.is_dir():shutil.rmtree(alvo,ignore_errors=True)
            else:alvo.unlink()
        shutil.move(str(item),str(alvo))
    s=Settings.model_validate(migrate(json.loads((p/'config_antes.json').read_text(encoding='utf-8'))))
    p.rename(p.with_name('restaurada_'+p.name));return s,p.name
