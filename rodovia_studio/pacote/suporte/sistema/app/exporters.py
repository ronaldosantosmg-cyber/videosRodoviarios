"""Exportação do modelo para outros aplicativos e reimportação das marcações.

Formatos: GeoJSON (CRS do projeto e WGS84), KML/KMZ (Google Earth), DXF (uma layer por tipo),
CSV de obras, pacote .zip do projeto e sequência PNG (com camadas RGBA opcionais).
Cada feição leva 'rs_type' e, nas marcações editáveis, 'rs_model' (JSON do item) para reimportação.
"""
import csv,io,json,zipfile,hashlib,re
from datetime import datetime,timezone
from pathlib import Path
from xml.sax.saxutils import escape
import xml.etree.ElementTree as ET
import numpy as np
from shapely.geometry import LineString,Point,Polygon,mapping,shape
from shapely.ops import transform as shp_transform
from pyproj import CRS,Transformer
from .chainage import fmt

EDITABLE=['inicio_km','destaque','intervencao','chamada','sentido','fluxo_override','fluxo_incluido','exclusao','oae','sem_conexao','obra','par_controle','area_sem_sinalizacao','cidade','interdicao','travessia','faixa_pedestre','zebrado','placa','faixas_trecho','acesso','faixa_adicional','area_pista','acostamento']
LAYERS={'eixo':'RS_EIXO','eixo_secundario':'RS_EIXO_SECUNDARIO','inicio_km':'RS_INICIO_KM','marco_km':'RS_MARCO_KM','trajetoria':'RS_TRAJETORIA',
        'fluxo_incluido':'RS_FLUXO_INCLUIDO','sentido':'RS_SENTIDO','fluxo_override':'RS_FLUXO_OVERRIDE','exclusao':'RS_EXCLUSAO','oae':'RS_OAE',
        'sem_conexao':'RS_SEM_CONEXAO','intervencao':'RS_INTERVENCAO','obra':'RS_OBRA','chamada':'RS_CHAMADA','par_controle':'RS_PAR_CONTROLE','fim_km':'RS_FIM_KM','destaque':'RS_DESTAQUE','area_sem_sinalizacao':'RS_SEM_SINALIZACAO','cidade':'RS_CIDADE','interdicao':'RS_INTERDICAO','travessia':'RS_TRAVESSIA','faixa_pedestre':'RS_FAIXA_PEDESTRE','zebrado':'RS_ZEBRADO','placa':'RS_PLACA','faixas_trecho':'RS_FAIXAS_TRECHO','acesso':'RS_ACESSO','faixa_adicional':'RS_FAIXA_ADICIONAL','area_pista':'RS_AREA_PISTA','acostamento':'RS_ACOSTAMENTO'}
COLORS={'eixo':'ffffff','eixo_secundario':'c8c8c8','inicio_km':'ffd56b','marco_km':'ffd56b','trajetoria':'61e6d7','fluxo_incluido':'e78bff','sentido':'ffe14d',
        'fluxo_override':'ffae5c','exclusao':'ff7860','oae':'d9dcd6','sem_conexao':'ff3b5c','intervencao':'79e6d0','obra':'86dce9','chamada':'86dce9','par_controle':'4fa3ff','fim_km':'ffd56b','destaque':'ff8a3d','area_sem_sinalizacao':'5ad8ff','cidade':'ffffff','interdicao':'ec701c','travessia':'3fe08a','faixa_pedestre':'ffffff','zebrado':'f4f2e2','placa':'c81e24','faixas_trecho':'a78bfa','acesso':'ffcf5c','faixa_adicional':'a78bfa','area_pista':'d8b45a','acostamento':'e8dcaa'}

def _xy(p):return (p['x'],p['y']) if isinstance(p,dict) else (p.x,p.y)

def features(settings,stationing,axes=(),segments=(),oae=()):
    """Lista de (geometria shapely no CRS do projeto, propriedades)."""
    st=stationing;out=[]
    def km(p):return round(float(st.km(list(p))),3)
    def add(geom,rs,name='',model=None,**props):
        pr={'rs_type':rs,'name':name,**{k:v for k,v in props.items() if v is not None}}
        if model is not None:pr['rs_model']=json.dumps(model,ensure_ascii=False)
        out.append((geom,pr))
    ax=st.axis
    add(LineString(ax),'eixo','Eixo principal',km_start=round(float(st.km(ax[0])),3),km_end=round(float(st.km(ax[-1])),3),length_m=round(st.length,3))
    for i,a in enumerate(axes[1:],1):add(LineString(a['points']),'eixo_secundario',f"Eixo {i} · {a.get('layer','')}")
    add(Point(st.start_point),'inicio_km','Início do estaqueamento',model=settings.chainage.model_dump(),km=st.km_start,defined=st.defined)
    if st.end_point is not None:add(Point(st.end_point),'fim_km','Fim do estaqueamento',km=round(st.km_end_geometric(),3))
    lo,hi=st.km_range()
    for k in range(int(np.ceil(lo/100)*100),int(hi)+1,100):
        add(Point(st.point(k)),'marco_km','km '+fmt(k),km=float(k))
    for s in segments:
        p=np.asarray(s['points'])
        if len(p)<2:continue
        if not s['forward'] and not s['both']:p=p[::-1]
        add(LineString(p),'trajetoria',f"Trajetória {s.get('base','')} ({s['kind']})",direction='dois sentidos' if s['both'] else 'sentido da linha',disabled=bool(s['disabled']),reversed=bool(s['reversed']),km_start=km(p[0]),km_end=km(p[-1]))
    for t in settings.traffic_paths:
        pts=[_xy(p) for p in t.points];add(LineString(pts),'fluxo_incluido',t.name,t.model_dump(),enabled=t.enabled,km_start=km(pts[0]),km_end=km(pts[-1]))
    for d in settings.direction_marks:
        a,b=_xy(d.start),_xy(d.end);add(LineString([a,b]),'sentido','Sentido de via',d.model_dump(),km=km(((a[0]+b[0])/2,(a[1]+b[1])/2)))
    for o in settings.flow_overrides:
        add(Point(o.x,o.y),'fluxo_override','Inversão de fluxo' if o.action=='reverse' else 'Fluxo desativado',o.model_dump(),km=km((o.x,o.y)))
    for i,a in enumerate(settings.exclusions):
        pts=[_xy(p) for p in a];add(Polygon(pts),'exclusao',f'Área de exclusão {i+1}',[{'x':x,'y':y} for x,y in pts])
    oae_by_id={o['id']:o for o in oae}
    for m in settings.oae_marks:
        o=oae_by_id.get(m.id or 'oae')
        line=LineString(o['line']) if o else LineString([_xy(m.start),_xy(m.end)])
        if getattr(m,'polygon',None):line=Polygon([_xy(p) for p in m.polygon])
        add(line,'oae',m.name,m.model_dump(),km_start=o['km_start_m'] if o else km(_xy(m.start)),km_end=o['km_end_m'] if o else km(_xy(m.end)),level_m=m.level_m,width_m=m.width_m)
    for z in settings.no_connection_zones:
        g=Point(*_xy(z.point)) if z.kind=='point' else Polygon([_xy(p) for p in z.points])
        add(g,'sem_conexao',z.name,z.model_dump(),radius_m=z.radius_m if z.kind=='point' else None,km=km(g.centroid.coords[0]))
    for p in settings.pois:
        k=p.km_m if p.km_mode=='manual' and p.km_m is not None else km((p.x,p.y))
        add(Point(p.x,p.y),'intervencao',p.title,p.model_dump(),kind=p.kind,km=k,km_mode=p.km_mode,subtitle=p.subtitle)
        if p.anchor:add(LineString([(p.x,p.y),_xy(p.anchor)]),'chamada','Linha de chamada · '+p.title,{'poi':p.id,'anchor':p.anchor.model_dump()},km=km(_xy(p.anchor)))
    for w in settings.works:
        if w.x is not None:g=Point(w.x,w.y)
        else:g=Point(st.point((w.km_start_m+w.km_end_m)/2))
        add(g,'obra',w.description,w.model_dump(),km_start=w.km_start_m,km_end=w.km_end_m,kind=w.kind)
    for h in settings.highlights:
        add(Point(h.point.x,h.point.y),'destaque',h.name,h.model_dump(),category=h.category,description=h.description,km=km((h.point.x,h.point.y)))
    for i,a in enumerate(getattr(settings,'clean_areas',[])):
        pts=[_xy(p) for p in a];add(Polygon(pts),'area_sem_sinalizacao',f'Área sem sinalização {i+1}',[{'x':x,'y':y} for x,y in pts])
    for b in getattr(settings,'lane_blocks',[]):
        add(Polygon([_xy(p) for p in b.points]),'interdicao',b.name,b.model_dump(),mode=b.mode,speed_kmh=b.speed_kmh)
    for z in getattr(settings,'crossing_zones',[]):
        g=Point(*_xy(z.point)) if z.kind=='point' else Polygon([_xy(p) for p in z.points])
        add(g,'travessia',z.name,z.model_dump(),mode=z.mode,radius_m=z.radius_m if z.kind=='point' else None)
    for c in getattr(settings,'cities',[]):
        add(Point(c.point.x,c.point.y),'cidade',c.name,c.model_dump(),kind=c.kind or None,show=c.show)
    for c in getattr(settings,'crosswalks',[]):
        add(LineString([_xy(c.a),_xy(c.b)]),'faixa_pedestre',c.name,c.model_dump(),width_m=c.width_m,km=km(_xy(c.a)))
    for h in getattr(settings,'hatch_areas',[]):
        add(Polygon([_xy(p) for p in h.points]),'zebrado',h.name,h.model_dump(),color=h.color)
    for g in getattr(settings,'signs',[]):
        add(Point(*_xy(g.point)),'placa',g.code+(' '+g.text if g.text else ''),g.model_dump(),code=g.code,text=g.text or None,km=km(_xy(g.point)))
    for z in getattr(settings,'lane_zones',[]):
        add(Polygon([_xy(p) for p in z.points]),'faixas_trecho',z.name,z.model_dump(),lanes=z.lanes)
    for a in getattr(settings,'accesses',[]):
        add(LineString([_xy(p) for p in a.points]),'acesso',a.name,a.model_dump(),width_m=a.width_m,taper_in_m=a.taper_in_m,taper_out_m=a.taper_out_m,km=km(_xy(a.points[0])))
    for r in getattr(settings,'lane_ranges',[]):
        add(LineString([_xy(r.start),_xy(r.end)]),'faixa_adicional',r.name,r.model_dump(),lanes=r.lanes,km_start=km(_xy(r.start)),km_end=km(_xy(r.end)))
    for a in getattr(settings,'pavement_areas',[]):
        add(Polygon([_xy(p) for p in a.points]),'area_pista',a.name,a.model_dump(),tipo=a.kind)
    for m in getattr(settings,'shoulder_marks',[]):
        add(LineString([_xy(m.start),_xy(m.end)]),'acostamento',m.name,m.model_dump(),width_m=m.width_m,km_start=km(_xy(m.start)),km_end=km(_xy(m.end)))
    for i,pair in enumerate(settings.dxf_alignment.pairs):
        add(LineString([_xy(pair.dxf),_xy(pair.image)]),'par_controle',f'Par de controle {i+1}',pair.model_dump())
    return out

def crs_urn(crs):
    epsg=CRS.from_user_input(crs).to_epsg()
    return f'urn:ogc:def:crs:EPSG::{epsg}' if epsg else CRS.from_user_input(crs).to_wkt()

def to_wgs84(geom,crs):
    tr=Transformer.from_crs(CRS.from_user_input(crs),4326,always_xy=True)
    return shp_transform(lambda x,y,z=None:tr.transform(x,y),geom)

def geojson(feats,crs,wgs84=False):
    fs=[{'type':'Feature','geometry':mapping(to_wgs84(g,crs) if wgs84 else g),'properties':p} for g,p in feats]
    doc={'type':'FeatureCollection','name':'Rodovia Studio','features':fs,'rs_crs':str(crs),'rs_exported_at':datetime.now(timezone.utc).isoformat()}
    if not wgs84:doc['crs']={'type':'name','properties':{'name':crs_urn(crs)}}
    return json.dumps(doc,ensure_ascii=False,indent=1)

def _kml_coords(g):
    def c(seq):return ' '.join(f'{x:.9f},{y:.9f},0' for x,y,*_ in seq)
    if g.geom_type=='Point':return f'<Point><coordinates>{c(g.coords)}</coordinates></Point>'
    if g.geom_type=='LineString':return f'<LineString><tessellate>1</tessellate><coordinates>{c(g.coords)}</coordinates></LineString>'
    if g.geom_type=='Polygon':
        inner=''.join(f'<innerBoundaryIs><LinearRing><coordinates>{c(r.coords)}</coordinates></LinearRing></innerBoundaryIs>' for r in g.interiors)
        return f'<Polygon><outerBoundaryIs><LinearRing><coordinates>{c(g.exterior.coords)}</coordinates></LinearRing></outerBoundaryIs>{inner}</Polygon>'
    return '<MultiGeometry>'+''.join(_kml_coords(x) for x in g.geoms)+'</MultiGeometry>'

def kml(feats,crs,name='Rodovia Studio'):
    def abgr(h,a='ff'):return a+h[4:6]+h[2:4]+h[0:2]
    styles=''.join(f'<Style id="{k}"><LineStyle><color>{abgr(v)}</color><width>3</width></LineStyle><PolyStyle><color>{abgr(v,"55")}</color></PolyStyle><IconStyle><color>{abgr(v)}</color></IconStyle></Style>' for k,v in COLORS.items())
    folders={}
    for g,p in feats:
        w=to_wgs84(g,crs);desc=[]
        for k in ['km','km_start','km_end']:
            if k in p and isinstance(p[k],(int,float)):desc.append(f'{k.replace("_"," ")}: {fmt(p[k])}')
        data=''.join(f'<Data name="{escape(str(k))}"><value>{escape(str(v))}</value></Data>' for k,v in p.items())
        folders.setdefault(p['rs_type'],[]).append(f'<Placemark><name>{escape(str(p.get("name","")))}</name><description>{escape(" · ".join(desc))}</description><styleUrl>#{p["rs_type"]}</styleUrl><ExtendedData>{data}</ExtendedData>{_kml_coords(w)}</Placemark>')
    body=''.join(f'<Folder><name>{escape(LAYERS.get(k,k))}</name>{"".join(v)}</Folder>' for k,v in folders.items())
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2"><Document><name>{escape(name)}</name><ExtendedData><Data name="rs_crs"><value>{escape(str(crs))}</value></Data></ExtendedData>{styles}{body}</Document></kml>'

def kmz(feats,crs,name='Rodovia Studio'):
    b=io.BytesIO()
    with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('doc.kml',kml(feats,crs,name))
    return b.getvalue()

def dxf(feats,path):
    import ezdxf
    doc=ezdxf.new('R2010');doc.header['$INSUNITS']=6;msp=doc.modelspace()
    if 'RODOVIA' not in doc.appids:doc.appids.new('RODOVIA')
    for i,(k,layer) in enumerate(LAYERS.items()):
        if layer not in doc.layers:doc.layers.add(layer,color=(i%7)+1)
    for g,p in feats:
        layer=LAYERS.get(p['rs_type'],'RS_OUTROS')
        if layer not in doc.layers:doc.layers.add(layer)
        att={'layer':layer}
        if g.geom_type=='Point':
            e=msp.add_point(g.coords[0],dxfattribs=att)
            if p['rs_type']=='sem_conexao' and p.get('radius_m'):msp.add_circle(g.coords[0],p['radius_m'],dxfattribs=att)
            label=p.get('name','')+(f" km {fmt(p['km'])}" if isinstance(p.get('km'),(int,float)) else '')
            msp.add_text(label[:250],height=2.5,dxfattribs=att).set_placement((g.coords[0][0]+2,g.coords[0][1]+2))
        elif g.geom_type=='LineString':e=msp.add_lwpolyline(list(g.coords),dxfattribs=att)
        elif g.geom_type=='Polygon':e=msp.add_lwpolyline(list(g.exterior.coords)[:-1],close=True,dxfattribs=att)
        else:continue
        # Propriedades em XDATA (fragmentos de 240 caracteres).
        text=json.dumps({k:v for k,v in p.items()},ensure_ascii=False);chunks=[text[i:i+240] for i in range(0,len(text),240)]
        e.set_xdata('RODOVIA',[(1000,c) for c in chunks])
    doc.saveas(path)

def works_csv(feats):
    f=io.StringIO(newline='');w=csv.writer(f,delimiter=';')
    w.writerow(['Descrição','Km inicial','Km final','Tipo','Ano PER','Tabela PER','X','Y','Origem'])
    for g,p in feats:
        if p['rs_type'] not in ('intervencao','obra','oae'):continue
        m=json.loads(p.get('rs_model','{}'))
        a=p.get('km_start',p.get('km'));b=p.get('km_end',p.get('km'))
        c=g.centroid if g.geom_type!='Point' else g
        w.writerow([p.get('name',''),fmt(a) if a is not None else '',fmt(b) if b is not None else '',m.get('kind',p.get('kind','oae' if p['rs_type']=='oae' else 'outro')),m.get('per_year',''),m.get('per_table',''),f'{c.x:.3f}',f'{c.y:.3f}',{'intervencao':'Intervenção','obra':'Obra PER','oae':'OAE marcada'}[p['rs_type']]])
    return '﻿'+f.getvalue()

# ---------- Reimportação ----------
def _read_geojson(data,crs):
    doc=json.loads(data.decode('utf-8-sig') if isinstance(data,bytes) else data)
    src=None
    name=(doc.get('crs') or {}).get('properties',{}).get('name')
    if name:src=CRS.from_user_input(name)
    elif doc.get('rs_crs') and not doc.get('crs'):src=CRS.from_epsg(4326)
    else:src=CRS.from_epsg(4326)
    tr=None if src==CRS.from_user_input(crs) else Transformer.from_crs(src,CRS.from_user_input(crs),always_xy=True)
    out=[]
    for f in doc.get('features',[]):
        g=shape(f['geometry'])
        if tr:g=shp_transform(lambda x,y,z=None:tr.transform(x,y),g)
        out.append((g,f.get('properties') or {}))
    return out

def _read_kml(data,crs):
    root=ET.fromstring(data);ns={'k':'http://www.opengis.net/kml/2.2'};tr=Transformer.from_crs(4326,CRS.from_user_input(crs),always_xy=True);out=[]
    def coords(el):
        return [tr.transform(*map(float,v.split(',')[:2])) for v in (el.text or '').split()]
    for pm in root.iter('{http://www.opengis.net/kml/2.2}Placemark'):
        props={d.get('name'):d.findtext('k:value',default='',namespaces=ns) for d in pm.iter('{http://www.opengis.net/kml/2.2}Data')}
        pt=pm.find('.//k:Point/k:coordinates',ns);ln=pm.find('.//k:LineString/k:coordinates',ns);pg=pm.find('.//k:Polygon/k:outerBoundaryIs/k:LinearRing/k:coordinates',ns)
        if pt is not None:g=Point(coords(pt)[0])
        elif ln is not None:g=LineString(coords(ln))
        elif pg is not None:g=Polygon(coords(pg))
        else:continue
        out.append((g,props))
    return out

def read_any(data,filename,crs):
    ext=Path(filename).suffix.lower()
    if ext in ('.geojson','.json'):return _read_geojson(data,crs)
    if ext=='.kml':return _read_kml(data,crs)
    if ext=='.kmz':
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            name=next((n for n in z.namelist() if n.lower().endswith('.kml')),None)
            if not name:raise ValueError('KMZ sem documento KML.')
            return _read_kml(z.read(name),crs)
    raise ValueError('Formato não suportado para reimportação: use GeoJSON, KML ou KMZ (obras: CSV).')

def apply_import(cfg,feats):
    """Atualiza o dicionário de configuração com as marcações editáveis lidas (substitui cada tipo presente)."""
    found={}
    for g,p in feats:
        kind=p.get('rs_type')
        if kind not in EDITABLE:continue
        m=p.get('rs_model');m=json.loads(m) if isinstance(m,str) and m else (m or {})
        c=lambda xy:{'x':float(xy[0]),'y':float(xy[1])}
        if kind=='inicio_km':
            if m:found.setdefault('chainage',{**m,**({'start':c(g.coords[0])} if m.get('start') else {})})
            elif str(p.get('defined')).lower() in ('true','1'):found.setdefault('chainage',{'mode':'manual','start':c(g.coords[0])})
        elif kind=='destaque':found.setdefault('highlights',[]).append({**m,'point':c(g.coords[0])})
        elif kind=='intervencao':found.setdefault('pois',[]).append({**m,'x':g.x,'y':g.y})
        elif kind=='chamada':found.setdefault('_anchors',{})[m.get('poi')]=c(g.coords[-1])
        elif kind=='sentido':found.setdefault('direction_marks',[]).append({**m,'start':c(g.coords[0]),'end':c(g.coords[-1])})
        elif kind=='fluxo_override':found.setdefault('flow_overrides',[]).append({**m,'x':g.x,'y':g.y})
        elif kind=='fluxo_incluido':found.setdefault('traffic_paths',[]).append({**m,'points':[c(v) for v in g.coords]})
        elif kind=='exclusao':found.setdefault('exclusions',[]).append([c(v) for v in list(g.exterior.coords)[:-1]])
        elif kind=='oae':
            if g.geom_type=='Polygon':found.setdefault('oae_marks',[]).append({**m,'polygon':[c(v) for v in list(g.exterior.coords)[:-1]]})
            else:found.setdefault('oae_marks',[]).append({**m,'start':c(g.coords[0]),'end':c(g.coords[-1])})
        elif kind=='sem_conexao':
            if g.geom_type=='Point':found.setdefault('no_connection_zones',[]).append({**m,'kind':'point','point':c(g.coords[0]),'points':[]})
            else:found.setdefault('no_connection_zones',[]).append({**m,'kind':'area','point':None,'points':[c(v) for v in list(g.exterior.coords)[:-1]]})
        elif kind=='obra':found.setdefault('works',[]).append(m)
        elif kind=='interdicao':found.setdefault('lane_blocks',[]).append({**m,'points':[c(v) for v in list(g.exterior.coords)[:-1]]})
        elif kind=='travessia':
            if g.geom_type=='Point':found.setdefault('crossing_zones',[]).append({**m,'kind':'point','point':c(g.coords[0]),'points':[]})
            else:found.setdefault('crossing_zones',[]).append({**m,'kind':'area','point':None,'points':[c(v) for v in list(g.exterior.coords)[:-1]]})
        elif kind=='area_sem_sinalizacao':found.setdefault('clean_areas',[]).append([c(v) for v in list(g.exterior.coords)[:-1]])
        elif kind=='cidade':found.setdefault('cities',[]).append({**m,'name':m.get('name') or p.get('name') or 'Cidade','point':c(g.coords[0])})
        elif kind=='faixa_pedestre':found.setdefault('crosswalks',[]).append({**m,'a':c(g.coords[0]),'b':c(g.coords[-1])})
        elif kind=='zebrado':found.setdefault('hatch_areas',[]).append({**m,'points':[c(v) for v in list(g.exterior.coords)[:-1]]})
        elif kind=='placa':found.setdefault('signs',[]).append({**m,'point':c(g.coords[0])})
        elif kind=='faixas_trecho':found.setdefault('lane_zones',[]).append({**m,'points':[c(v) for v in list(g.exterior.coords)[:-1]]})
        elif kind=='acesso':found.setdefault('accesses',[]).append({**m,'points':[c(v) for v in g.coords]})
        elif kind=='faixa_adicional':found.setdefault('lane_ranges',[]).append({**m,'start':c(g.coords[0]),'end':c(g.coords[-1])})
        elif kind=='area_pista':found.setdefault('pavement_areas',[]).append({**m,'points':[c(v) for v in list(g.exterior.coords)[:-1]]})
        elif kind=='acostamento':found.setdefault('shoulder_marks',[]).append({**m,'start':c(g.coords[0]),'end':c(g.coords[-1])})
        elif kind=='par_controle':found.setdefault('_pairs',[]).append({**m,'dxf':c(g.coords[0]),'image':c(g.coords[-1])})
    anchors=found.pop('_anchors',{});pairs=found.pop('_pairs',None)
    for p in found.get('pois',[]):
        if p.get('id') in anchors:p['anchor']=anchors[p['id']]
    if pairs is not None:cfg['dxf_alignment']={**cfg.get('dxf_alignment',{}),'pairs':pairs}
    cfg.update(found);return cfg,{k:len(v) if isinstance(v,list) else 1 for k,v in found.items()}

# ---------- Pacote do projeto ----------
PACKAGE_FILES=['config.json','input.dxf','input.kmz']
PACKAGE_DIRS=['camadas','imagem_local']

def package(directory,version):
    d=Path(directory);b=io.BytesIO();manifest={'app':'Rodovia Studio','version':version,'created':datetime.now(timezone.utc).isoformat(),'files':[]}
    with zipfile.ZipFile(b,'w',zipfile.ZIP_DEFLATED,allowZip64=True) as z:
        files=[d/f for f in PACKAGE_FILES if (d/f).exists()]+[f for sub in PACKAGE_DIRS if (d/sub).exists() for f in sorted((d/sub).iterdir()) if f.is_file()]
        for f in files:
            rel=f.relative_to(d).as_posix();z.write(f,'projeto/'+rel)
            manifest['files'].append({'path':rel,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
        z.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    return b.getvalue()

SAFE=re.compile(r'^(config\.json|input\.dxf|input\.kmz|camadas/[0-9a-f]{32}\.dxf|imagem_local/[^/\\]{1,200})$')

def unpack(data,directory,limit=900*1024*1024):
    """Extrai um pacote do Rodovia Studio, conferindo caminhos e SHA-256 do manifesto."""
    d=Path(directory)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        try:manifest=json.loads(z.read('manifest.json'))
        except KeyError:raise ValueError('Pacote sem manifest.json: não foi gerado pelo Rodovia Studio.')
        if sum(i.file_size for i in z.infolist())>limit:raise ValueError('Pacote descompactado excede o limite.')
        for f in manifest.get('files',[]):
            rel=f['path']
            if not SAFE.match(rel) or '..' in rel:raise ValueError('Caminho não permitido no pacote: '+rel)
            blob=z.read('projeto/'+rel)
            if hashlib.sha256(blob).hexdigest()!=f['sha256']:raise ValueError('Arquivo corrompido no pacote: '+rel)
            out=d/rel;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(blob)
    return manifest
