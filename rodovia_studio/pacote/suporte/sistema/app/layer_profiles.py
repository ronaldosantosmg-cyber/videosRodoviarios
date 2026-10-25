"""1.14: perfis de mapeamento de camadas (DXF -> tipo) reutilizáveis entre projetos.

Cada perfil é uma lista ordenada de regras {pattern, role}. O padrão aceita * (qualquer sequência) e
? (um caractere), sem diferenciar maiúsculas/minúsculas nem acentos; a primeira regra que casar vale.
O perfil "Padrão" reúne os nomes mais comuns; o usuário salva os seus (por exemplo, o padrão CAD da
empresa) e aplica em qualquer projeto. Nada é fixo no código: o mapeamento final fica na configuração
do projeto e pode ser alterado camada a camada.
"""
import json,re,unicodedata,fnmatch,threading
from pathlib import Path

ROLE_LABELS={'axis':'Eixo','pavement':'Pista projetada','existing_pavement':'Pista existente','shoulder':'Acostamento',
             'edge_line':'Bordo (linha de borda)','median':'Canteiro','barrier':'Barreira','oae':'OAE','cut':'Corte','fill':'Aterro',
             'earthwork':'Talude (corte/aterro pela proximidade)','domain':'Faixa de domínio','water':'Hidrografia',
             'sign_h':'Sinalização horizontal (pintura)','sign_v':'Sinalização vertical (placas)'}

from .asset_catalog import ASSET_ROLES,DXF_RULES,CATALOG
ROLE_LABELS.update(ASSET_ROLES)

BUILTIN={'name':'Padrão (nomes comuns)','builtin':True,'rules':[
    *DXF_RULES,
    {'pattern':'*SINALIZ*HORIZ*','role':'sign_h'},{'pattern':'*PINTURA*','role':'sign_h'},{'pattern':'*FAIXA*PEDEST*','role':'sign_h'},{'pattern':'*ZEBRAD*','role':'sign_h'},
    {'pattern':'*SINALIZ*VERT*','role':'sign_v'},{'pattern':'*PLACA*','role':'sign_v'},
    {'pattern':'*DOMIN*','role':'domain'},{'pattern':'*FAIXA*FD*','role':'domain'},{'pattern':'FD_*','role':'domain'},
    {'pattern':'*EIXO*','role':'axis'},{'pattern':'*AXIS*','role':'axis'},{'pattern':'*CENTERLINE*','role':'axis'},
    {'pattern':'*NEWJERSEY*','role':'barrier'},{'pattern':'*NEW*JERSEY*','role':'barrier'},{'pattern':'*BARREIRA*','role':'barrier'},{'pattern':'*DEFENSA*','role':'barrier'},
    {'pattern':'*CANTEIRO*','role':'median'},{'pattern':'*MEDIAN*','role':'median'},
    {'pattern':'*ACOST*','role':'shoulder'},{'pattern':'*SHOULDER*','role':'shoulder'},
    {'pattern':'*BORDO*','role':'edge_line'},{'pattern':'*LBO*','role':'edge_line'},{'pattern':'*EDGE*LINE*','role':'edge_line'},
    {'pattern':'*HOAE*','role':'oae'},{'pattern':'OAE','role':'oae'},{'pattern':'*OAE*','role':'oae'},{'pattern':'*PONTE*','role':'oae'},{'pattern':'*VIADUTO*','role':'oae'},
    {'pattern':'*HPAV*EXIST*','role':'existing_pavement'},{'pattern':'*PAV*EXIST*','role':'existing_pavement'},{'pattern':'*PISTA*EXIST*','role':'existing_pavement'},
    {'pattern':'*HPAV*','role':'pavement'},{'pattern':'*PAVIMENTO*','role':'pavement'},{'pattern':'*PISTA*PROJ*','role':'pavement'},
    {'pattern':'*CORTE*','role':'cut'},{'pattern':'*ATERRO*','role':'fill'},
    {'pattern':'*HIDRO*','role':'water'},{'pattern':'RIO*','role':'water'},{'pattern':'*_RIO*','role':'water'},{'pattern':'*-RIO*','role':'water'},{'pattern':'* RIO*','role':'water'},{'pattern':'*CORREGO*','role':'water'},{'pattern':'*LAGO*','role':'water'},{'pattern':'*AGUA*','role':'water'},{'pattern':'*DRENAGEM*NATURAL*','role':'water'},
]}

_lock=threading.Lock()

def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(s).upper()) if not unicodedata.combining(c))

def matches(pattern,name):
    return fnmatch.fnmatchcase(norm(name),norm(pattern))

def role_for(name,rules):
    for r in rules:
        if r.get('role') in ROLE_LABELS and matches(r.get('pattern',''),name):return r['role']
    return None

def apply(layer_names,profile):
    out={}
    for n in layer_names:
        r=role_for(n,profile['rules'])
        if r:out.setdefault(r,[]).append(n)
    return out

def _file(root):return Path(root)/'_perfis_camadas.json'

def load(root):
    f=_file(root);user=[]
    if f.exists():
        try:user=[p for p in json.loads(f.read_text(encoding='utf-8')) if isinstance(p,dict) and p.get('name')]
        except (OSError,ValueError):user=[]
    return [BUILTIN]+user

def validate(p):
    name=str(p.get('name','')).strip()
    if not name or len(name)>80:raise ValueError('Dê um nome ao perfil (até 80 caracteres).')
    if name==BUILTIN['name']:raise ValueError('Esse nome é do perfil padrão; escolha outro.')
    rules=[]
    for r in p.get('rules') or []:
        pat=str(r.get('pattern','')).strip();role=r.get('role')
        if not pat:continue
        if role not in ROLE_LABELS:raise ValueError(f'Tipo inválido na regra "{pat}".')
        if len(pat)>200:raise ValueError('Padrão longo demais.')
        material=r.get('material')
        if material is not None and material not in CATALOG:raise ValueError('Material não cadastrado no catálogo local.')
        rules.append({'pattern':pat,'role':role,**({'material':material} if material else {})})
    if not rules:raise ValueError('O perfil precisa de pelo menos uma regra.')
    if len(rules)>500:raise ValueError('Perfil com regras demais (máximo 500).')
    return {'name':name,'rules':rules}

def save(root,p):
    p=validate(p)
    with _lock:
        user=[x for x in load(root)[1:] if x['name']!=p['name']]+[p]
        f=_file(root);tmp=f.with_suffix('.tmp');tmp.write_text(json.dumps(user,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(f)
    return p

def delete(root,name):
    with _lock:
        user=load(root)[1:];left=[x for x in user if x['name']!=name]
        if len(left)==len(user):return False
        f=_file(root);tmp=f.with_suffix('.tmp');tmp.write_text(json.dumps(left,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(f)
    return True
