"""1.30: modelos (templates) de projeto e utilidades da lista de projetos.

Um modelo é um arquivo JSON em <dados>/_modelos/<id>.json com o nome, a descrição, a data, se inclui as
marcações e a configuração (Settings) já migrada. Os modelos não guardam DXF/KMZ nem imagens.
"""
import json,re,time,uuid
from pathlib import Path
from .models import Settings
from .migration import clean_name

# Campos que pertencem a um trecho específico (geometria marcada, km, arquivos). Num modelo "só configurações"
# eles voltam ao padrão; ao aplicar um modelo a um projeto existente, eles são mantidos do projeto.
PROJECT_KEYS=['name','origin','destination','km_start_m','km_end_m','reference_length_m','coordinates_confirmed',
 'preview_center','preview_width_m','works','route_directions','local_imagery','overlays','dxf_alignment','chainage','custom_axis']
MARK_KEYS=['pavement_areas','shoulder_marks','pois','exclusions','traffic_paths','direction_marks','flow_overrides','oae_marks',
 'no_connection_zones','cabin','highlights','clean_areas','cities','lane_blocks','crossing_zones','crosswalks','hatch_areas','signs',
 'lane_zones','accesses','lane_ranges','gantries','connection_rules','advance_zones','texture_areas','route_alignments']
_ID=re.compile(r'^[0-9a-f]{32}$')

def folder(root):
    d=Path(root)/'_modelos';d.mkdir(exist_ok=True);return d

def _file(root,mid):
    if not _ID.match(mid or ''):raise FileNotFoundError('Modelo não encontrado.')
    f=folder(root)/f'{mid}.json'
    if not f.exists():raise FileNotFoundError('Modelo não encontrado.')
    return f

def strip(data,include_marks):
    """Configuração do modelo: sem o que é do trecho; marcações só quando pedidas."""
    fresh=Settings().model_dump();out=dict(data)
    for k in PROJECT_KEYS:
        if k in fresh and k!='name':out[k]=fresh[k]
    if not include_marks:
        for k in MARK_KEYS:
            if k in fresh:out[k]=fresh[k]
    return out

def listing(root):
    rows=[]
    for f in sorted(folder(root).glob('*.json')):
        try:j=json.loads(f.read_text(encoding='utf-8'))
        except Exception:continue
        cfg=j.get('config',{})
        rows.append({'id':f.stem,'name':j.get('name',f.stem),'description':j.get('description',''),'created':j.get('created',''),
                     'include_marks':bool(j.get('include_marks')),'marks':sum(len(cfg.get(k) or []) for k in MARK_KEYS if isinstance(cfg.get(k),list)),
                     'source':j.get('source','')})
    rows.sort(key=lambda r:r['name'].lower());return rows

def unique_name(root,name,exclude=None):
    taken={r['name'].lower() for r in listing(root) if r['id']!=exclude}
    if name.lower() in taken:raise ValueError(f'Já existe um modelo chamado “{name}”. Escolha outro nome.')

def save(root,settings,name,description='',include_marks=False,source=''):
    n=clean_name(name,'')
    if not n:raise ValueError('Nome do modelo inválido: use pelo menos uma letra ou número.')
    unique_name(root,n);mid=uuid.uuid4().hex
    data={'name':n,'description':clean_name(description or '','')[:200] if description else '','created':time.strftime('%Y-%m-%d %H:%M'),
          'include_marks':bool(include_marks),'source':source,'config':strip(settings.model_dump(),include_marks)}
    (folder(root)/f'{mid}.json').write_text(json.dumps(data,ensure_ascii=False,indent=1),encoding='utf-8')
    return {'id':mid,**{k:data[k] for k in ('name','description','created','include_marks')}}

def load(root,mid):
    j=json.loads(_file(root,mid).read_text(encoding='utf-8'))
    s=Settings.model_validate(j.get('config',{}))   # migração automática de modelos antigos
    return j,s

def rename(root,mid,name,description=None):
    f=_file(root,mid);j=json.loads(f.read_text(encoding='utf-8'));n=clean_name(name,'')
    if not n:raise ValueError('Nome do modelo inválido: use pelo menos uma letra ou número.')
    unique_name(root,n,exclude=mid);j['name']=n
    if description is not None:j['description']=clean_name(description,'') if description.strip() else ''
    f.write_text(json.dumps(j,ensure_ascii=False,indent=1),encoding='utf-8');return {'id':mid,'name':n}

def delete(root,mid):
    f=_file(root,mid);trash=Path(root)/'_lixeira';trash.mkdir(exist_ok=True)
    dst=trash/f'modelo_{mid}_{time.strftime("%Y%m%d_%H%M%S")}.json';f.replace(dst);return dst.name

def apply(project,template):
    """Aplica as configurações do modelo a um projeto: mantém o que é do trecho e as marcações do projeto."""
    p=project.model_dump();t=template.model_dump();out=dict(t)
    for k in PROJECT_KEYS+MARK_KEYS+['hidden_layers','frozen_layers']:
        if k in p:out[k]=p[k]
    # Camadas: valem as do projeto; o modelo só preenche quando o projeto ainda não tem.
    for k in ('layers','hatch_roles'):
        if p.get(k):out[k]=p[k]
    out['schema_version']=p.get('schema_version',out.get('schema_version'))
    return Settings.model_validate(out)
