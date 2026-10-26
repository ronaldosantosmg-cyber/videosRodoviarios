"""Derivações por alinhamento; a rede e as restrições são sempre revalidadas."""
import hashlib,json,zlib,uuid
from pathlib import Path
import numpy as np

MAX_RAW=48*1024*1024
MAX_FILE=8*1024*1024
BUDGET=64*1024*1024

class RouteLaneCache:
    def __init__(self,directory=None):
        self.folder=Path(directory)/'_cache'/'route_lanes' if directory else None
        self.hits=self.misses=self.invalid=self.write_errors=0
        digest=hashlib.sha256()
        for name in ('routes.py','road_sections.py','route_lane_cache.py','models.py'):
            digest.update(Path(__file__).with_name(name).read_bytes())
        self.engine=digest.hexdigest()

    def get(self,route,settings,compute):
        zones=[z.model_dump() for z in getattr(settings,'alternating_zones',[]) if z.enabled and z.route_id==route.id] if settings else []
        raw=json.dumps([self.engine,route.model_dump(),zones],sort_keys=True,allow_nan=False,separators=(',',':')).encode()
        key=hashlib.sha256(raw).hexdigest()
        identity=hashlib.sha256((route.id or route.name).encode()).hexdigest()
        target=self.folder/(identity+'.json.z') if self.folder else None
        safe=target is not None and not any(p.is_symlink() for p in (self.folder.parent,self.folder,target))
        if safe and target.is_file() and target.stat().st_size<=MAX_FILE:
            try:
                decoder=zlib.decompressobj();data=decoder.decompress(target.read_bytes(),MAX_RAW+1)
                if len(data)>MAX_RAW or not decoder.eof or decoder.unconsumed_tail or decoder.unused_data:raise ValueError('Cache excessivo.')
                def invalid(value):raise ValueError('Número não finito.')
                result=json.loads(data,parse_constant=invalid)
                if result['key']==key:
                    lanes=result['lanes']
                    if not isinstance(lanes,list) or len(lanes)>256:raise ValueError('Faixas inválidas.')
                    for lane in lanes:
                        p=np.asarray(lane['points'],float)
                        if p.ndim!=2 or p.shape[1]!=2 or not 3<=len(p)<=200000 or not np.isfinite(p).all():raise ValueError('Coordenadas inválidas.')
                        values=[lane[k] for k in ('length','start_m','end_m','lane_width_m')]
                        if not np.isfinite(values).all() or lane['length']<=0 or lane['end_m']<=lane['start_m'] or not .2<=lane['lane_width_m']<=10 or lane['dir'] not in ('f','r') or not isinstance(lane['lane'],int) or not 0<=lane['lane']<8:raise ValueError('Metadados inválidos.')
                        actual=float(np.linalg.norm(np.diff(p,axis=0),axis=1).sum())
                        if abs(actual-lane['length'])>max(.001,actual*1e-8):raise ValueError('Comprimento inconsistente.')
                        lane['points']=p
                    self.hits+=1
                    return lanes
            except (ValueError,TypeError,KeyError,OSError,zlib.error):self.invalid+=1
        self.misses+=1;lanes=compute()
        if safe:
            temp=None
            try:
                data=json.dumps({'key':key,'lanes':lanes},default=lambda value:value.tolist(),allow_nan=False,separators=(',',':')).encode()
                if len(data)<=MAX_RAW:
                    compressed=zlib.compress(data,3)
                    if len(compressed)<=MAX_FILE:
                        self.folder.mkdir(parents=True,exist_ok=True);temp=self.folder/('.'+uuid.uuid4().hex+'.tmp');temp.write_bytes(compressed);temp.replace(target)
                        files=sorted((p for p in self.folder.glob('*.json.z') if not p.is_symlink()),key=lambda p:p.stat().st_mtime,reverse=True);total=0
                        for p in files:
                            total+=p.stat().st_size
                            if total>BUDGET:p.unlink(missing_ok=True)
            except (ValueError,TypeError,OSError):self.write_errors+=1
            finally:
                if temp is not None:
                    try:temp.unlink(missing_ok=True)
                    except OSError:self.write_errors+=1
        return lanes

    def report(self):return {'hits':self.hits,'misses':self.misses,'invalid':self.invalid,'write_errors':self.write_errors,'scope':'Somente derivação de faixas; rede, barreiras, sentidos e colisões continuam validados.'}
