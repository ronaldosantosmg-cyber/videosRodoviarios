"""IBGE BC250/2025 WFS: clip vectors, keep names, cache and draw before roads."""
import json,hashlib,urllib.request,urllib.parse
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import cv2
from PIL import Image,ImageDraw
from pyproj import Transformer
from shapely.geometry import shape,box,mapping,LineString,Polygon
from shapely.ops import transform

ENDPOINT='https://geoservicos.ibge.gov.br/geoserver/ows'
LAYERS=['CCAR:BC250_2025_hid_trecho_drenagem_l','CCAR:BC250_2025_hid_massa_dagua_a']
SOURCE='IBGE BC250/2025 + © OpenStreetMap contributors (ODbL)'

def osm_features(elements):
    from shapely.ops import polygonize,unary_union
    result=[]
    for e in elements:
        tags=e.get('tags',{});name=tags.get('name','')
        if e['type']=='way':
            coords=[(p['lon'],p['lat']) for p in e.get('geometry',[])]
            if len(coords)<2:continue
            water=tags.get('natural')=='water' or tags.get('waterway')=='riverbank'
            if water and len(coords)>3 and coords[0]==coords[-1]:g=Polygon(coords).buffer(0)
            elif tags.get('waterway')=='river':g=LineString(coords)
            else:continue
        elif e['type']=='relation':
            rings={role:[] for role in ['outer','inner']}
            for member in e.get('members',[]):
                role=member.get('role','outer') or 'outer'
                coords=[(p['lon'],p['lat']) for p in member.get('geometry',[])]
                if role in rings and len(coords)>1:rings[role].append(LineString(coords))
            outer=list(polygonize(unary_union(rings['outer'])))
            inner=list(polygonize(unary_union(rings['inner'])))
            if not outer:continue
            g=unary_union(outer).difference(unary_union(inner))
        else:continue
        result.append({'type':'Feature','geometry':mapping(g),'properties':{'name':name,'provider':'OpenStreetMap','osm_type':e['type'],'osm_id':e['id']}})
    return result

def fetch_osm(ll):
    west,south,east,north=ll;bb=f'{south},{west},{north},{east}'
    query=f'[out:json][timeout:30];(way["natural"="water"]({bb});relation["natural"="water"]({bb});way["waterway"="riverbank"]({bb});way["waterway"="river"]({bb}););out geom;'
    req=urllib.request.Request('https://overpass-api.de/api/interpreter?'+urllib.parse.urlencode({'data':query}),headers={'User-Agent':'RodoviaStudio/1.2','Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=40) as r:data=json.loads(r.read(30000000))
    if data.get('remark'):raise ValueError(data['remark'])
    return osm_features(data.get('elements',[]))

def fetch(bounds,crs):
    to_ll=Transformer.from_crs(crs,4326,always_xy=True)
    ll=to_ll.transform_bounds(*bounds,densify_pts=21)
    output=[];limit=box(*ll)
    for layer in LAYERS:
        params={'service':'WFS','version':'1.0.0','request':'GetFeature','typeName':layer,'outputFormat':'application/json','srsName':'EPSG:4326','bbox':','.join(map(str,ll))+',EPSG:4326','maxFeatures':5000}
        req=urllib.request.Request(ENDPOINT+'?'+urllib.parse.urlencode(params),headers={'User-Agent':'RodoviaStudio/1.2 (cartographic visualisation)'})
        with urllib.request.urlopen(req,timeout=40) as r:data=json.loads(r.read(30000000))
        if data.get('type')!='FeatureCollection':raise ValueError('Resposta de hidrografia inválida')
        if data.get('numberMatched',data.get('totalFeatures',0)) not in (None,'unknown'):
            if int(data.get('numberMatched',data.get('totalFeatures',0)))>5000:raise ValueError('Área de consulta muito grande: reduza a área do projeto.')
        for f in data['features']:
            g=shape(f['geometry']).intersection(limit)
            if g.is_empty:continue
            output.append({'type':'Feature','geometry':mapping(g),'properties':{'name':f.get('properties',{}).get('nome',''),'layer':layer}})
    osm_warning=''
    try:output.extend(fetch_osm(ll))
    except Exception as exc:osm_warning='Áreas de água OSM indisponíveis: '+str(exc)[:140]
    return {'osm_warning':osm_warning,'type':'FeatureCollection','features':output,'source':SOURCE,'url':ENDPOINT,'crs':'EPSG:4326','bounds':list(ll),'retrieved_at':datetime.now(timezone.utc).isoformat(),'width_note':'Linhas representam eixos hidrográficos; largura gráfica ilustrativa, não margens levantadas.'}

class Hydrography:
    def __init__(self,directory,settings,bounds,status=lambda *a:None):
        self.lines=[];self.polygons=[];self.labels=[];self.warning='';self.source=''
        if not settings.hydrography:return
        path=Path(directory)/'hidrografia';path.mkdir(exist_ok=True)
        key=hashlib.sha256(json.dumps([bounds,settings.crs,'osm-water-v1']).encode()).hexdigest()[:16];cached=path/(key+'.geojson')
        asset=Path(__file__).resolve().parents[1]/'assets/th57/hidrografia.geojson'
        data=None
        if cached.exists():data=json.loads(cached.read_text(encoding='utf-8'))
        elif asset.exists():
            preset=json.loads(asset.read_text(encoding='utf-8'));tr=Transformer.from_crs(settings.crs,4326,always_xy=True);ll=tr.transform_bounds(*bounds,densify_pts=21)
            if box(*preset['bounds']).buffer(.00001).covers(box(*ll)):data=preset
        if data is None:
            status(.025,'Consultando hidrografia IBGE')
            try:data=fetch(bounds,settings.crs);cached.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
            except Exception as exc:
                self.warning='Hidrografia IBGE indisponível: '+str(exc)[:160];status(.03,self.warning);return
        self.warning=data.get('osm_warning','');self.source=data.get('source',SOURCE);self.named_lines={};to_world=Transformer.from_crs(4326,settings.crs,always_xy=True).transform;clip=box(*bounds)
        named={}
        def add(g,name):
            if g.is_empty:return
            if g.geom_type=='LineString':
                if g.length<8:return
                p=np.array(g.coords);self.lines.append(p)
                if name:self.named_lines.setdefault(name,[]).append(p)
                if name and (name not in named or g.length>named[name].length):named[name]=g
            elif g.geom_type=='Polygon':
                self.polygons.append(g)
                if name and name not in named:named[name]=g
            elif hasattr(g,'geoms'):
                for part in g.geoms:add(part,name)
        for f in data['features']:add(transform(to_world,shape(f['geometry'])).intersection(clip),f.get('properties',{}).get('name',''))
        for name,g in named.items():
            anchor=g.interpolate(.5,normalized=True) if g.geom_type=='LineString' else g.representative_point()
            self.labels.append((name,np.array(anchor.coords[0])))
    def water_mask(self,shape,worldpx):
        mask=np.zeros(shape,np.uint8)
        for g in self.polygons:
            temp=np.zeros_like(mask);cv2.fillPoly(temp,[np.rint(worldpx(np.array(g.exterior.coords))).astype(np.int32)],255)
            for ring in g.interiors:cv2.fillPoly(temp,[np.rint(worldpx(np.array(ring.coords))).astype(np.int32)],0)
            mask=np.maximum(mask,temp)
        # Water texture is restricted to mapped surface polygons. Drainage axes do not invent banks.
        if not self.polygons:
            for p in self.lines:cv2.polylines(mask,[np.rint(worldpx(p)).astype(np.int32)],False,110,1,cv2.LINE_AA)
        return mask
    def paint_map(self,image,worldpx,meters_per_pixel,opacity=.65,enhanced=False):
        # Blue tint and ripples are anchored to world coordinates (no animated shimmer).
        from .visual import water_paint
        mask=self.water_mask(image.shape[:2],worldpx)
        water_paint(image,mask,meters_per_pixel,opacity,enhanced and bool(self.polygons))
        return mask
    def draw_labels(self,image,screen,font,scale,opacity=1.):
        if not self.labels or opacity<=0:return image
        canvas=Image.fromarray(image);dr=ImageDraw.Draw(canvas);used=[];H,W=image.shape[:2]
        for name,anchor in sorted(self.labels,key=lambda p:('rio ' not in p[0].lower(),p[0])):
            # Place each name on its visible portion, not an off-screen global midpoint.
            visible=[]
            for points in getattr(self,'named_lines',{}).get(name,[]):
                q=screen(points);ok=(q[:,0]>60*scale)&(q[:,0]<W-60*scale)&(q[:,1]>200*scale)&(q[:,1]<H-200*scale)
                visible.extend(q[ok])
            if visible:
                points=np.asarray(visible);x,y=points[np.argmin(np.linalg.norm(points-[W/2,H/2],axis=1))]
            else:x,y=screen(anchor[None])[0]
            ft=font(21*scale,True);bbox=dr.textbbox((0,0),name,font=ft);w=bbox[2]-bbox[0];h=bbox[3]-bbox[1]
            x-=w/2;y+=10*scale;rect=(x-6,y-4,x+w+6,y+h+8)
            if rect[0]<15 or rect[2]>W-15 or rect[1]<180*scale or rect[3]>H-175*scale:continue
            if any(not(rect[2]<b[0] or rect[0]>b[2] or rect[3]<b[1] or rect[1]>b[3]) for b in used):continue
            dr.text((x,y),name,font=ft,fill='#b5e8ff',stroke_width=max(1,round(2*scale)),stroke_fill='#133849');used.append(rect)
            if len(used)>=6:break
        out=np.array(canvas)
        return out if opacity>=1 else cv2.addWeighted(out,opacity,image,1-opacity,0)
