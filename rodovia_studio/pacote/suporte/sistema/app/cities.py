"""1.10: cidades próximas (OpenStreetMap via Overpass, com cache local) para nomes no vídeo."""
import json,math,urllib.request,urllib.parse,hashlib
from pathlib import Path
import numpy as np
from pyproj import CRS,Transformer

ENDPOINTS=['https://overpass-api.de/api/interpreter','https://overpass.kumi.systems/api/interpreter']
RANK={'city':0,'town':1,'municipality':1,'village':2}

def _query(s,w,n,e):
    return f'[out:json][timeout:25];(node["place"~"^(city|town|village)$"]["name"]({s},{w},{n},{e}););out body;'

def _download(q,timeout=30):
    data=urllib.parse.urlencode({'data':q}).encode();last=None
    for url in ENDPOINTS:
        try:
            req=urllib.request.Request(url,data=data,headers={'User-Agent':'RodoviaStudio/1.10'})
            with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode('utf-8'))
        except Exception as e:last=e
    raise OSError(f'Sem acesso ao OpenStreetMap (Overpass): {last}')

def nearby(directory,crs,bounds,radius_km=25,limit=12,fetch=None):
    """Lista de cidades {name,x,y,kind,population,dist_km} no CRS do projeto, perto do trecho."""
    (x0,y0),(x1,y1)=bounds;pad=float(radius_km)*1000
    if not all(map(math.isfinite,[x0,y0,x1,y1])):raise ValueError('Limites do projeto inválidos.')
    tr=Transformer.from_crs(CRS.from_user_input(crs),4326,always_xy=True);back=Transformer.from_crs(4326,CRS.from_user_input(crs),always_xy=True)
    xs=[x0-pad,x1+pad,x0-pad,x1+pad];ys=[y0-pad,y0-pad,y1+pad,y1+pad];lon,lat=tr.transform(xs,ys)
    s,w,n,e=min(lat),min(lon),max(lat),max(lon)
    q=_query(round(s,4),round(w,4),round(n,4),round(e,4))
    cache=Path(directory)/'cidades_osm.json';key=hashlib.sha256(q.encode()).hexdigest()[:16]
    raw=None
    if cache.exists():
        try:
            c=json.loads(cache.read_text(encoding='utf-8'))
            if c.get('key')==key:raw=c['data']
        except (OSError,ValueError):raw=None
    if raw is None:
        raw=fetch(q) if fetch else _download(q)
        try:cache.write_text(json.dumps({'key':key,'data':raw},ensure_ascii=False),encoding='utf-8')
        except OSError:pass
    out=[];seen=set()
    cx=(x0+x1)/2;cy=(y0+y1)/2
    for el in (raw or {}).get('elements',[]):
        tags=el.get('tags') or {};name=(tags.get('name') or '').strip();kind=tags.get('place','')
        if not name or kind not in RANK or 'lat' not in el or 'lon' not in el:continue
        x,y=back.transform(el['lon'],el['lat'])
        if not(math.isfinite(x) and math.isfinite(y)):continue
        # Distância ao retângulo do trecho (0 se dentro).
        dx=max(x0-x,0,x-x1);dy=max(y0-y,0,y-y1);d=math.hypot(dx,dy)
        if d>pad:continue
        try:pop=int(str(tags.get('population','')).replace('.','').replace(' ','') or 0) or None
        except ValueError:pop=None
        k=name.lower()
        if k in seen:continue
        seen.add(k);out.append({'name':name,'x':round(x,2),'y':round(y,2),'kind':kind,'population':pop,'dist_km':round(d/1000,2)})
    # Cidades e vilas grandes primeiro; povoados só os mais próximos.
    out=[c for c in out if c['kind']!='village' or c['dist_km']<=min(8,radius_km)]
    out.sort(key=lambda c:(RANK[c['kind']],-(c['population'] or 0),c['dist_km']))
    return out[:max(1,int(limit))]
