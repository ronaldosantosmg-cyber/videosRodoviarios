"""Cache local de estado de tráfego: grafo JSON e arrays NPZ, nunca pickle.

Falha de leitura/escrita vira cache miss; a simulação normal continua disponível.
Não carrega classes, módulos ou código escolhidos pelo arquivo de cache.
"""
import collections
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import secrets
import shutil
import tempfile
import types
import zipfile

import numpy as np
from pydantic import BaseModel
from scipy.spatial import cKDTree
from shapely import from_wkb, to_wkb
from shapely.geometry.base import BaseGeometry
from shapely.strtree import STRtree

VERSION=1
MAX_BYTES=512*1024*1024
MAX_NODES=500000
MAX_ENTRIES=8
MAX_DISK_BYTES=2*1024*1024*1024
# Presentation-only settings; all unlisted fields participate in invalidation.
VISUAL_FIELDS=frozenset({'fps','width','height','resolution','video_codec','encoder','crf','preset',
    'camera_mode','camera_height_m','camera_speed_kmh','camera_pitch_deg','camera_fov_deg',
    'day_night_mode','lighting_mode','night_mode','font_family','font_size','text_color',
    'render_quality','realism_profile','imagery_opacity','show_helpers','day_night','night',
    'night_lights','role_colors','texture_params','camera_path','camera_points','camera_route',
    'camera_distance_m','camera_height','camera_fov','camera_pitch','output_width','output_height',
    'night_start_s','night_transition_s','night_darkness','traffic_legacy_migrated','night_signage_glow','cpu_preset',
    'render_workers','video_quality','presentation_guides','earthwork_look','detail_textures',
    'texture_style','texture_areas'})
_CLASSES=(('simulation','Block'),('transport','Transport'),('alternating_traffic','AlternatingTraffic'),
          ('vehicle_safety','PolygonSafety'),('conflict_guard','ConflictGuard'),
          ('shoulder_probe','ShoulderProbe'),('pedestrian_traffic','PedestrianTraffic'))


def _negative_inf():return -math.inf

def _allowed():
    result={}
    for module,name in _CLASSES:
        cls=getattr(importlib.import_module('.'+module,__package__),name);result[module+'.'+name]=cls
    for module in ('models','transport_models','road_sections'):
        for name,cls in vars(importlib.import_module('.'+module,__package__)).items():
            if isinstance(cls,type) and issubclass(cls,BaseModel) and cls.__module__==__package__+'.'+module:
                result[module+'.'+name]=cls
    return result


def _order(value):
    if isinstance(value,np.generic):value=value.item()
    if isinstance(value,tuple):return ('tuple',tuple(_order(v) for v in value))
    return (type(value).__name__,repr(value))


class Codec:
    def __init__(self,sim,directory=None):
        self.directory=Path(directory).resolve() if directory is not None else None
        self.sim=sim;self.nodes=[];self.arrays={};self.memo={};self.allowed=_allowed()
        self.external={'sim':sim,'net':sim.net,'settings':sim.s,'paths':sim.net.paths}
        self.external_ids={id(v):k for k,v in self.external.items()}

    def encode(self,value):
        if value is None or type(value) in (bool,str,int):return value
        if isinstance(value,np.bool_):return bool(value)
        if isinstance(value,(float,np.floating)):
            f=float(value)
            return f if math.isfinite(f) else {'float':'nan' if math.isnan(f) else ('inf' if f>0 else '-inf')}
        if isinstance(value,np.integer):return int(value)
        if id(value) in self.external_ids:return {'external':self.external_ids[id(value)]}
        if id(value) in self.memo:return {'ref':self.memo[id(value)]}
        if len(self.nodes)>=MAX_NODES:raise ValueError('Cache excede limite de objetos.')
        index=len(self.nodes);self.memo[id(value)]=index;self.nodes.append(None)
        enc=self.encode
        if type(value).__module__==__package__+'.traffic_history':
            from .traffic_history import FrameArchive,FrameSequence,WarningSequence
            if type(value) is FrameArchive:
                value.flush();node={'kind':'history','state':enc(value.export_state())}
            elif type(value) in (FrameSequence,WarningSequence):
                node={'kind':'history_frames' if type(value) is FrameSequence else 'history_warnings','archive':enc(value.archive)}
            else:raise ValueError('Histórico não permitido.')
        elif isinstance(value,np.ndarray):
            if value.dtype.kind not in 'biufc' or value.dtype.hasobject:raise ValueError('Array não numérico.')
            if not np.isfinite(value).all():raise ValueError('Array não finito.')
            key='a'+str(len(self.arrays));self.arrays[key]=value;node={'kind':'array','key':key}
        elif isinstance(value,BaseGeometry):node={'kind':'geometry','wkb':to_wkb(value,hex=True)}
        elif isinstance(value,cKDTree):node={'kind':'kdtree','data':enc(value.data)}
        elif isinstance(value,STRtree):node={'kind':'strtree','geometries':enc(list(value.geometries))}
        elif isinstance(value,np.random.Generator):
            if not isinstance(value.bit_generator,np.random.PCG64):raise ValueError('RNG não suportado.')
            node={'kind':'rng','state':enc(value.bit_generator.state)}
        elif isinstance(value,dict):
            kind='counter' if isinstance(value,collections.Counter) else 'defaultdict' if isinstance(value,collections.defaultdict) else 'dict'
            node={'kind':kind,'items':[[enc(k),enc(value[k])] for k in sorted(value,key=_order)]}
            if kind=='defaultdict':
                f=value.default_factory;factories={None:'none',list:'list',dict:'dict',set:'set',int:'int',float:'float'}
                factory=factories.get(f)
                if factory is None and getattr(f,'__name__','') in ('<lambda>','_negative_inf') and f()==-math.inf:factory='-inf'
                if factory is None:raise ValueError('Fábrica de dicionário não suportada.')
                node['factory']=factory
        elif isinstance(value,(list,tuple,set,frozenset)):
            node={'kind':type(value).__name__,'items':[enc(v) for v in (sorted(value,key=_order) if isinstance(value,set) else value)]}
        else:
            name=next((k for k,c in self.allowed.items() if type(value) is c),None)
            if name is None:raise ValueError('Objeto não permitido: '+type(value).__name__)
            attrs=value.__dict__
            node={'kind':'model' if isinstance(value,BaseModel) else 'object','class':name,
                  'attrs':enc(attrs),'fields_set':sorted(value.model_fields_set) if isinstance(value,BaseModel) else []}
        self.nodes[index]=node
        return {'ref':index}

    def decode(self,root,nodes,arrays):
        if not isinstance(nodes,list) or len(nodes)>MAX_NODES:raise ValueError('Grafo inválido.')
        memo={};busy=set()
        def dec(v):
            if v is None or type(v) in (str,int,float,bool):return v
            if not isinstance(v,dict):raise ValueError('Valor de cache inválido.')
            if set(v)=={'external'}:return self.external[v['external']]
            if set(v)=={'float'}:return {'inf':math.inf,'-inf':-math.inf,'nan':math.nan}[v['float']]
            if set(v)!={'ref'} or type(v['ref']) is not int or not 0<=v['ref']<len(nodes):raise ValueError('Referência inválida.')
            i=v['ref']
            if i in memo:return memo[i]
            if i in busy:raise ValueError('Ciclo imutável inválido.')
            busy.add(i);n=nodes[i];k=n['kind']
            if k in ('dict','counter','defaultdict'):
                if k=='dict':obj={}
                elif k=='counter':obj=collections.Counter()
                else:obj=collections.defaultdict({'none':None,'list':list,'dict':dict,'set':set,'int':int,'float':float,'-inf':_negative_inf}[n['factory']])
                memo[i]=obj
                for key,val in n['items']:obj[dec(key)]=dec(val)
            elif k in ('list','set'):
                obj=[] if k=='list' else set();memo[i]=obj
                for item in n['items']:
                    if k=='list':obj.append(dec(item))
                    else:obj.add(dec(item))
            elif k in ('tuple','frozenset'):obj=(tuple if k=='tuple' else frozenset)(dec(x) for x in n['items'])
            elif k=='array':
                obj=arrays[n['key']]
                if obj.dtype.kind not in 'biufc' or obj.dtype.hasobject or not np.isfinite(obj).all():raise ValueError('Array inválido.')
            elif k=='geometry':obj=from_wkb(bytes.fromhex(n['wkb']))
            elif k=='kdtree':obj=cKDTree(dec(n['data']))
            elif k=='strtree':obj=STRtree(dec(n['geometries']))
            elif k=='rng':obj=np.random.default_rng();obj.bit_generator.state=dec(n['state'])
            elif k=='history':
                if self.directory is None:raise ValueError('Diretório de histórico obrigatório.')
                from .traffic_history import FrameArchive
                obj=FrameArchive.from_state(dec(n['state']),base_directory=self.directory)
            elif k in ('history_frames','history_warnings'):
                archive=dec(n['archive']);obj=archive.frames if k=='history_frames' else archive.warnings
            elif k in ('model','object'):
                cls=self.allowed.get(n['class'])
                if cls is None:raise ValueError('Classe não permitida.')
                if k=='model':
                    if not issubclass(cls,BaseModel):raise ValueError('Modelo inválido.')
                    obj=cls.model_construct();memo[i]=obj
                    object.__setattr__(obj,'__dict__',dec(n['attrs']));object.__setattr__(obj,'__pydantic_fields_set__',set(n['fields_set']))
                else:
                    if issubclass(cls,BaseModel):raise ValueError('Classe inválida.')
                    obj=cls.__new__(cls);memo[i]=obj;obj.__dict__.update(dec(n['attrs']))
            else:raise ValueError('Tipo não permitido.')
            memo[i]=obj;busy.remove(i);return obj
        return dec(root)


def cache_key(net,settings,duration=None,*,window=None):
    """Assinatura conservadora da física, rede, duração, janela e código local."""
    shell=type('External',(),{})();shell.net=net;shell.s=settings
    codec=Codec(shell)
    cfg=settings.model_dump(mode='python');cfg={k:v for k,v in cfg.items() if k not in VISUAL_FIELDS}
    network={k:getattr(net,k) for k in ('paths','edges','allowed','operational_pavement','shoulder_envelope','connections','origin_info') if hasattr(net,k)}
    if 'paths' in network:network['paths']=[{k:v for k,v in path.items() if k not in ('_cum','_q')} for path in network['paths']]
    # paths must be hashed here rather than represented as an external binding.
    codec.external_ids={}
    root=codec.encode([cfg,network,duration,window])
    h=hashlib.sha256(json.dumps([VERSION,root,codec.nodes],sort_keys=True,separators=(',',':'),allow_nan=False).encode())
    for key,array in sorted(codec.arrays.items()):h.update(key.encode());h.update(array.dtype.str.encode());h.update(str(array.shape).encode());h.update(array.tobytes())
    for file in sorted(Path(__file__).parent.glob('*.py')):h.update(file.name.encode());h.update(file.read_bytes())
    return h.hexdigest()


def _entry(directory,key,complete):
    if not isinstance(key,str) or not re.fullmatch('[0-9a-f]{64}',key):raise ValueError('Chave inválida.')
    return Path(directory)/(key+('.ready' if complete else '.partial'))


def _ready(sim):
    from .fleet_policy import require_export
    if not getattr(sim,'simulation_complete',False) or not getattr(sim,'frames',None):raise ValueError('Simulação incompleta.')
    if getattr(sim,'fleet_audit',{}).get('samples',0)<=0:raise ValueError('Auditoria ausente.')
    continuation=getattr(sim,'_continuation',None)
    if continuation is not None and not continuation.get('complete',False):raise ValueError('Checkpoint ainda parcial.')
    pedestrians=getattr(sim,'pedestrians',None)
    if pedestrians is not None and any(getattr(pedestrians,k,0) for k in ('vehicle_collisions','people_collisions','train_collisions')):raise ValueError('Conflito de pedestres.')
    require_export(sim,sim.s)


def cache_save(sim,directory,key,*,complete=False):
    tmp=None
    try:
        if complete:_ready(sim)
        elif getattr(sim,'simulation_complete',False):return False
        state={k:v for k,v in sim.__dict__.items() if k not in ('net','s','vtype') and not callable(v) and not isinstance(v,types.GeneratorType)}
        codec=Codec(sim,directory);root=codec.encode(state)
        directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
        target=_entry(directory,key,complete)
        tmp=Path(tempfile.mkdtemp(prefix='.traffic-',dir=directory))
        np.savez(tmp/'arrays.npz',**codec.arrays)
        arrays_bytes=(tmp/'arrays.npz').read_bytes()
        array_name='arrays-'+secrets.token_hex(12)+'.npz'
        document={'version':VERSION,'key':key,'complete':complete,'root':root,'nodes':codec.nodes,'arrays_file':array_name,'arrays_sha256':hashlib.sha256(arrays_bytes).hexdigest()}
        document['state_sha256']=hashlib.sha256(json.dumps(document,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        payload=json.dumps(document,separators=(',',':'),allow_nan=False).encode()
        if len(payload)+len(arrays_bytes)>MAX_BYTES:raise ValueError('Cache muito grande.')
        (tmp/'state.json').write_bytes(payload)
        target.mkdir(exist_ok=True)
        os.replace(tmp/'arrays.npz',target/array_name)
        os.replace(tmp/'state.json',target/'state.json')
        entries=sorted([p for p in directory.iterdir() if p.is_dir() and re.fullmatch(r'[0-9a-f]{64}\.(ready|partial)',p.name)],key=lambda p:p.stat().st_mtime,reverse=True)
        size=0
        for i,p in enumerate(entries):
            size+=sum(f.stat().st_size for f in p.iterdir() if f.is_file())
            if i>=MAX_ENTRIES or size>MAX_DISK_BYTES:shutil.rmtree(p)
        return True
    except (Exception,RecursionError):return False
    finally:
        if tmp is not None:shutil.rmtree(tmp,ignore_errors=True)


def cache_load_into(sim,directory,key,*,complete=False):
    try:
        target=_entry(directory,key,complete);manifest=target/'state.json'
        if target.is_symlink() or manifest.is_symlink() or manifest.stat().st_size>MAX_BYTES:return False
        state=json.loads(manifest.read_bytes(),parse_constant=lambda value:(_ for _ in ()).throw(ValueError('Constante inválida.')))
        digest=state.pop('state_sha256',None)
        if digest!=hashlib.sha256(json.dumps(state,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest():return False
        if state['version']!=VERSION or state['key']!=key or state['complete'] is not complete:return False
        name=state.get('arrays_file','')
        if not re.fullmatch(r'arrays-[0-9a-f]{24}\.npz',name):return False
        files=[manifest,target/name]
        if files[1].is_symlink() or sum(p.stat().st_size for p in files)>MAX_BYTES:return False
        if hashlib.sha256(files[1].read_bytes()).hexdigest()!=state['arrays_sha256']:return False
        with zipfile.ZipFile(files[1]) as z:
            if sum(i.file_size for i in z.infolist())>MAX_BYTES or len(z.infolist())>MAX_NODES:return False
            for info in z.infolist():
                if not re.fullmatch(r'a[0-9]+\.npy',info.filename):return False
                with z.open(info) as array_file:
                    version=np.lib.format.read_magic(array_file)
                    reader=np.lib.format.read_array_header_1_0 if version==(1,0) else np.lib.format.read_array_header_2_0 if version==(2,0) else None
                    if reader is None:return False
                    shape,_,dtype=reader(array_file)
                    if dtype.hasobject or dtype.kind not in 'biufc' or len(shape)>32 or math.prod(shape)*dtype.itemsize>MAX_BYTES:return False
        with np.load(files[1],allow_pickle=False) as archive:
            codec=Codec(sim,directory);attrs=codec.decode(state['root'],state['nodes'],archive)
        if not isinstance(attrs,dict) or any(k in attrs for k in ('net','s','vtype')):return False
        if attrs.get('duration')!=sim.duration:return False
        continuation=attrs.get('_continuation')
        if continuation is not None:
            if not isinstance(continuation,dict):return False
            maximum=math.ceil((sim.duration+10.)/.2)+2
            if not 0<=continuation.get('k',-1)<=continuation.get('steps',-1)<=maximum:return False
            if continuation.get('n')!=len(sim.net.paths):return False
        previous=sim.__dict__.copy()
        sim.__dict__.update(attrs)
        try:
            if complete:_ready(sim)
            elif getattr(sim,'simulation_complete',False):raise ValueError('Checkpoint marcado completo.')
        except Exception:
            sim.__dict__.clear();sim.__dict__.update(previous);return False
        return True
    except (Exception,RecursionError):return False


def prune_history(directory,active_roots=()):
    """Coleta históricos órfãos SOMENTE com produtores parados.

    Chamador deve manter roots ainda usados por leitores em active_roots. Um
    manifesto ilegível cancela a coleta: não adivinhar suas referências.
    """
    base=Path(directory).resolve();histories=base/'histories';active={Path(p).resolve() for p in active_roots}
    def entries():
        return sorted([p for p in base.iterdir() if not p.is_symlink() and p.is_dir() and re.fullmatch(r'[0-9a-f]{64}\.(ready|partial)',p.name)],key=lambda p:p.stat().st_mtime)
    def roots():
        result=set(active)
        for entry in entries():
            doc=json.loads((entry/'state.json').read_bytes());digest=doc.pop('state_sha256',None)
            if digest!=hashlib.sha256(json.dumps(doc,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest():raise ValueError('Manifesto inválido.')
            nodes=doc['nodes']
            def dec(value,depth=0):
                if depth>64:raise ValueError('Referência profunda.')
                if value is None or type(value) in (str,int,float,bool):return value
                node=nodes[value['ref']]
                if node['kind']=='dict':return {dec(k,depth+1):dec(v,depth+1) for k,v in node['items']}
                if node['kind']=='list':return [dec(v,depth+1) for v in node['items']]
                raise ValueError('Referência de histórico inválida.')
            for node in nodes:
                if node['kind']=='history':
                    root=Path(dec(node['state'])['root']).resolve()
                    if not root.is_relative_to(histories):raise ValueError('Histórico fora da raiz.')
                    result.add(root)
        return result
    def size():return sum(p.stat().st_size for p in base.rglob('*') if p.is_file() and not p.is_symlink())
    def collect(referenced):
        count=0
        if histories.exists() and not histories.is_symlink():
            for child in histories.iterdir():
                if child.is_dir() and not child.is_symlink() and re.fullmatch('[0-9a-f]{32}',child.name) and child.resolve() not in referenced:
                    shutil.rmtree(child);count+=1
        return count
    try:
        if not base.exists():return {'removed':0,'bytes_remaining':0,'over_budget':False}
        referenced=roots();removed=collect(referenced)
        # Evicção de snapshots antigos pode liberar seus históricos; leitores
        # explicitamente pinados continuam protegidos após perder o manifesto.
        for entry in entries():
            if size()<=MAX_DISK_BYTES:break
            shutil.rmtree(entry);removed+=1
            removed+=collect(roots())
        remaining=size()
        return {'removed':removed,'bytes_remaining':remaining,'over_budget':remaining>MAX_DISK_BYTES}
    except Exception:
        return {'removed':0,'bytes_remaining':None,'over_budget':None}


def compact_cache(directory):
    """Chamar após encerrar produtores/leitores: remove gerações NPZ superadas."""
    removed=0
    try:
        base=Path(directory)
        if not base.exists() or base.is_symlink():return 0
        for entry in base.iterdir():
            if entry.is_symlink() or not entry.is_dir() or not re.fullmatch(r'[0-9a-f]{64}\.(ready|partial)',entry.name):continue
            manifest=entry/'state.json'
            if manifest.is_symlink() or not manifest.is_file() or manifest.stat().st_size>MAX_BYTES:continue
            doc=json.loads(manifest.read_bytes());digest=doc.pop('state_sha256',None)
            if digest!=hashlib.sha256(json.dumps(doc,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest():continue
            keep=doc.get('arrays_file','')
            for path in entry.glob('arrays-*.npz'):
                if path.name!=keep and not path.is_symlink():path.unlink();removed+=1
    except (OSError,ValueError,KeyError):pass
    return removed
