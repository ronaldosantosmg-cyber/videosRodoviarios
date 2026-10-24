"""1.19: limpar o trabalho de um projeto mantendo as características do segmento, e retirar projetos da lista.

Limpar: guarda uma cópia da configuração (config_antes_limpeza_<data>.json) e zera só os grupos escolhidos.
Ficam sempre: arquivos DXF/KMZ, CRS, km inicial/final, estaqueamento, camadas, alinhamento, imagens
(local e web), elevação, camadas extras e parâmetros de vídeo. O DXF não é alterado.
Retirar projeto: a pasta vai para <projetos>/_lixeira (nada é apagado definitivamente pelo programa).
"""
import json,time,shutil
from pathlib import Path

GROUPS={
    'obras':('Intervenções, PER, destaques, interdições e cabine',['pois','works','highlights','lane_blocks','cabin']),
    'sinalizacao':('Placas, faixas de pedestre, zebrados e áreas sem sinalização',['signs','crosswalks','hatch_areas','clean_areas']),
    'geometria':('Acessos, 3ª faixa, faixas por trecho, OAE e exclusões',['accesses','lane_ranges','lane_zones','oae_marks','exclusions']),
    'fluxos':('Fluxos manuais, sentidos, inversões, sem conexão e travessias',['traffic_paths','direction_marks','flow_overrides','no_connection_zones','crossing_zones','route_directions','route_alignments','railways','traffic_signals','signal_links']),
    'cidades':('Cidades marcadas',['cities']),
}
DEFAULT=('obras','sinalizacao')
OUTPUTS=['video.mp4','preview.png']

def backups(d):
    return sorted(Path(d).glob('config_antes_limpeza_*.json'))

def reset(d,settings,groups,outputs=False):
    from .models import Settings
    bad=[g for g in groups if g not in GROUPS]
    if bad or not groups:raise ValueError('Escolha ao menos um grupo válido para limpar.')
    d=Path(d);stamp=time.strftime('%Y%m%d_%H%M%S');b=d/f'config_antes_limpeza_{stamp}.json'
    k=1
    while b.exists():b=d/f'config_antes_limpeza_{stamp}_{k}.json';k+=1
    data=settings.model_dump();b.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    fresh=Settings().model_dump();cleared=[]
    for g in groups:
        for key in GROUPS[g][1]:
            if key in data:
                n=len(data[key]) if isinstance(data[key],(list,dict)) else 1
                data[key]=fresh[key];cleared.append((key,n))
    removed=[]
    if outputs:
        for n in OUTPUTS:
            f=d/n
            if f.exists():
                try:f.unlink();removed.append(n)
                except OSError:pass
        for n in ('cache_detalhe',):
            if (d/n).exists():shutil.rmtree(d/n,ignore_errors=True);removed.append(n)
    return Settings.model_validate(data),{'backup':b.name,'cleared':{k:n for k,n in cleared},'removed':removed}

def undo(d):
    from .models import Settings
    from .migration import migrate
    bs=backups(d)
    if not bs:raise ValueError('Não há limpeza para desfazer neste projeto.')
    b=bs[-1];s=Settings.model_validate(migrate(json.loads(b.read_text(encoding='utf-8'))))
    b.rename(b.with_name(b.stem.replace('config_antes_limpeza_','config_restaurado_')+'.json'))
    return s,b.name

def trash(root,pid):
    root=Path(root);src=root/pid;t=root/'_lixeira';t.mkdir(exist_ok=True)
    dst=t/f'{pid}_{time.strftime("%Y%m%d_%H%M%S")}'
    shutil.move(str(src),str(dst));return dst
