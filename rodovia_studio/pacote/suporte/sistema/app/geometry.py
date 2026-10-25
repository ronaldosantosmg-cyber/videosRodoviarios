import json, re, unicodedata, zipfile, xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
import numpy as np
import ezdxf
from ezdxf.path import make_path, from_hatch
from pyproj import CRS, Transformer
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union
from shapely import make_valid

ROLES=['axis','pavement','existing_pavement','shoulder','median','barrier','oae','cut','fill','domain','edge_line','water','earthwork','sign_h','sign_v']
COLORS={'sign_h':'#ffffff','sign_v':'#ff5d5d','edge_line':'#f4f2e2','water':'#2a80b9','existing_pavement':'#a4a8a9','pavement':'#454c4e','shoulder':'#858983','median':'#7f9b6e','barrier':'#e0ddd2','oae':'#b9bcb7','cut':'#df6262','fill':'#53bb77','domain':'#ffd56b'}
from .asset_catalog import ASSET_ROLES,CATALOG,DEFAULT,material_for
ROLES.extend(ASSET_ROLES)
COLORS.update({role:CATALOG[DEFAULT[role]]['color'] for role in ASSET_ROLES})

def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFKD',s.upper()) if not unicodedata.combining(c))
def guess(layer):
    """Sugestão pelo perfil padrão (layer_profiles.BUILTIN); o mapeamento final é sempre do projeto."""
    from .layer_profiles import BUILTIN,role_for
    return role_for(layer,BUILTIN['rules'])

def walk(es, depth=0, parent_layer=None):
    if depth>32:raise ValueError('Blocos DXF excedem 32 níveis de aninhamento; confira referências circulares.')
    for e in es:
        if e.dxftype()=='INSERT':
            yield from walk(e.virtual_entities(),depth+1,e.dxf.layer if e.dxf.layer!='0' else parent_layer)
        else:
            if e.dxf.layer=='0' and parent_layer:
                e=e.copy();e.dxf.layer=parent_layer
            yield e

def read_kmz(path,crs):
    if not path or not Path(path).exists(): return [],[]
    from .kmz_validation import documents
    tr=Transformer.from_crs(4326,crs,always_xy=True);lines=[];pois=[];total=0
    local=lambda element:element.tag.rsplit('}',1)[-1]
    for name,root in documents(path):
        for pm in (element for element in root.iter() if local(element)=='Placemark'):
            title=next((node.text or 'Referência KMZ' for node in pm if local(node)=='name'),'Referência KMZ')
            for co in (node for node in pm.iter() if local(node)=='coordinates'):
                values=(co.text or '').split();total+=len(values)
                if total>1000000:raise ValueError('KML excede um milhão de coordenadas. Divida o trecho.')
                try:rows=[tuple(map(float,v.split(',')[:2])) for v in values]
                except (ValueError,TypeError) as exc:raise ValueError('KML contém coordenadas numéricas inválidas.') from exc
                if not rows:continue
                if any(len(row)!=2 for row in rows):raise ValueError('KML contém coordenadas incompletas.')
                coords=np.asarray(rows,float)
                if not np.isfinite(coords).all() or np.any(np.abs(coords[:,0])>180) or np.any(np.abs(coords[:,1])>90):raise ValueError('KML contém longitude/latitude fora do intervalo ou não finitas.')
                lon,lat=coords.T;x,y=tr.transform(lon,lat);p=np.column_stack([x,y])
                if not np.isfinite(p).all():raise ValueError('KML não pode ser transformado para o CRS escolhido.')
                if len(p)==1:pois.append({'id':f'kmz-{len(pois)}','title':title[:100],'subtitle':'Referência do KMZ','kind':'outro','x':float(x[0]),'y':float(y[0])})
                else:lines.append(p)
    return lines,pois

def convert(e,layer,role,units,entities,warnings,extra=None):
    """Converte uma entidade DXF em polilinhas/polígonos (metros, coordenadas do desenho)."""
    extra=extra or {}
    try:
        if e.dxftype()=='POINT' and role in ASSET_ROLES:
            p=e.dxf.location;entities.append({'layer':layer,'role':role,'closed':False,'points':np.array([[p.x*units,p.y*units]]),'holes':[],**extra});return
        hatch=e.dxftype() in HATCH_TYPES
        paths=list(from_hatch(e)) if hatch else [make_path(e)]
        ps=[]
        for p in paths:
            pts=np.array([(v.x,v.y) for v in p.flattening(.12/units,segments=8)])*units
            if len(pts)>=2: ps.append(pts)
        if hatch and ps:
            # Even/odd fill respects islands rather than filling every loop independently.
            shape=Polygon()
            for p in ps:
                if len(p)>=3: shape=shape.symmetric_difference(make_valid(Polygon(p)))
            # 1.26: coleções aninhadas (MultiPolygon dentro de GeometryCollection) não perdem partes.
            for poly in _polygons(shape):
                entities.append({'layer':layer,'role':role,'closed':True,'points':np.array(poly.exterior.coords),'holes':[np.array(h.coords) for h in poly.interiors],**extra})
        else:
            for pts in ps:
                closed=bool(e.dxf.get('flags',0)&1) if e.dxftype() in ['LWPOLYLINE','POLYLINE'] else np.linalg.norm(pts[0]-pts[-1])<.05
                entities.append({'layer':layer,'role':role,'closed':bool(closed and len(pts)>=3),'points':pts,'holes':[],**extra})
    except (ValueError,TypeError,ezdxf.DXFError,NotImplementedError):
        warnings.append(f'Entidade não convertida: {layer} / {e.dxftype()}')

HATCH_TYPES=('HATCH','MPOLYGON')

def _polygons(g):
    if g.is_empty:return []
    if g.geom_type=='Polygon':return [g]
    if hasattr(g,'geoms'):return [p for x in g.geoms for p in _polygons(x)]
    return []

NO_GEOMETRY={'TEXT','MTEXT','ATTRIB','ATTDEF','DIMENSION','IMAGE','VIEWPORT','POINT','LEADER','MULTILEADER','MLEADER'}

def overlay_layers(path):
    """Camadas de um DXF adicional, com contagem e classe sugerida."""
    doc=ezdxf.readfile(path);counts=Counter(e.dxf.layer for e in walk(doc.modelspace()))
    return [{'name':l,'count':n,'suggested_role':guess(l)} for l,n in sorted(counts.items())]

def read_overlays(directory,settings,warnings):
    """DXF adicionais sobrepostos: mesma leitura do DXF principal, com offset e CRS próprios."""
    from .alignment import fit,apply
    out=[]
    target=CRS.from_user_input(settings.crs)
    for order,ov in enumerate(sorted(settings.overlays,key=lambda o:o.order)):
        if not ov.enabled:continue
        path=Path(directory)/'camadas'/(ov.id+'.dxf')
        if not path.exists():warnings.append(f'Camada {ov.name}: arquivo ausente.');continue
        doc=ezdxf.readfile(path);ents=[]
        for e in walk(doc.modelspace()):
            if e.dxftype() in NO_GEOMETRY:continue
            role=ov.roles.get(e.dxf.layer,'')
            if role=='ignore':continue
            if role and role not in ROLES:role=''
            convert(e,e.dxf.layer,role or 'overlay',settings.units_to_m,ents,warnings,{'overlay':ov.id,'overlay_order':order,'style':{'color':ov.color,'opacity':ov.opacity,'width_m':ov.line_width_m,'fill':ov.fill}})
        if ov.crs and CRS.from_user_input(ov.crs)!=target:
            tr=Transformer.from_crs(CRS.from_user_input(ov.crs),target,always_xy=True)
            for e in ents:
                e['points']=np.column_stack(tr.transform(e['points'][:,0],e['points'][:,1]));e['holes']=[np.column_stack(tr.transform(h[:,0],h[:,1])) for h in e['holes']]
        if ov.alignment.applied and ov.alignment.pairs:
            params=fit(ov.alignment.pairs,ov.alignment.mode)
            for e in ents:e['points']=apply(e['points'],params);e['holes']=[apply(h,params) for h in e['holes']]
        out.extend(ents)
    return out

def sign_code(name,text=''):
    """Código da placa pelo nome do bloco/texto (R-1, R-2, R-19, A, OBRAS, I)."""
    n=norm(name or '');t=norm(text or '')
    if re.search(r'R-?1(?!\d)',n) or 'PARE' in n or t=='PARE':return 'R-1',''
    if re.search(r'R-?2(?!\d)',n) or 'PREFER' in n:return 'R-2',''
    if re.search(r'R-?19',n) or 'VEL' in n:
        m=re.search(r'\d{2,3}',t) or re.search(r'(?<!R-)(?<!R)\b\d{2,3}\b',n);return 'R-19',m.group(0) if m else ''
    if 'OBRA' in n:return 'OBRAS',''
    if re.match(r'A-?\d',n):return 'A',''
    return 'I',(text or name or '')[:40]

def split_layers(ents,doc,mode='auto'):
    """1.18: camadas a separar em grupos (cor + tipo de entidade). 'auto': a camada 0, ou uma camada com 60% ou
    mais das entidades, quando ela mistura grupos (desenho com tudo numa camada só)."""
    if mode=='off' or not ents:return set()
    by=Counter(e.dxf.layer for e in ents);groups={}
    for e in ents:groups.setdefault(e.dxf.layer,set()).add((_aci(e,doc),e.dxftype()))
    total=sum(by.values());out=set()
    for l,n in by.items():
        if len(groups[l])<2:continue
        if mode=='all' or (n>=20 and (l=='0' or n>=.6*total)):out.add(l)
    return out

def _aci(e,doc):
    c=e.dxf.get('color',256)
    if c==256:
        try:c=doc.layers.get(e.dxf.layer).color
        except Exception:c=7
    return abs(int(c))

def eff_layer(e,split,doc):
    """Nome usado no mapeamento: o da camada, ou 'camada · cor N · TIPO' quando a camada é separada."""
    l=e.dxf.layer
    if l not in split:return l
    c=e.dxf.get('color',256);cor='bloco' if c==0 else str(_aci(e,doc))
    lt=str(e.dxf.get('linetype','BYLAYER') or 'BYLAYER')
    return f'{l} · cor {cor} · {e.dxftype()}'+('' if lt.upper() in ('BYLAYER','CONTINUOUS','BYBLOCK') else ' · '+lt)

def check_roles(entities):
    """1.18: avisos de mapeamento suspeito (proteção contra camada errada)."""
    out=[];by={}
    for e in entities:by.setdefault((e['role'],e['layer']),[]).append(e)
    for (role,layer),es in by.items():
        if role in ('pavement','existing_pavement','shoulder','median','oae') and not any(x['closed'] for x in es):
            out.append(f'Camada “{layer}” está como {role} mas não tem áreas fechadas (hachura ou polilinha fechada): não será preenchida. Confira o tipo.')
        if role=='axis' and len(es)>40:
            out.append(f'Camada “{layer}” está como eixo e tem {len(es)} entidades: confira se ela contém só o eixo (use “Ver”).')
        if role=='sign_h':
            big=[x for x in es if x['closed'] and len(x['points'])>=3 and Polygon(x['points']).area>500]
            if big:out.append(f'Camada “{layer}” (sinalização horizontal) tem {len(big)} área(s) grande(s) demais para pintura (>500 m²): elas foram ignoradas. Confira se não é pavimento.')
    return out

def read_signs(doc,layers,units,split=frozenset()):
    """Placas verticais do DXF: blocos (INSERT), pontos, círculos e textos nas camadas do tipo 'Sinalização vertical'."""
    out=[]
    for e in doc.modelspace():
        if eff_layer(e,split,doc) not in layers:continue
        k=e.dxftype();txt='';name='';rot=None
        try:
            if k=='INSERT':
                p=e.dxf.insert;name=e.dxf.name;rot=float(e.dxf.get('rotation',0.))
                txt=' '.join(a.dxf.text for a in e.attribs if a.dxf.get('text'))
            elif k=='POINT':p=e.dxf.location
            elif k=='CIRCLE':p=e.dxf.center
            elif k in ('TEXT','MTEXT'):
                p=e.dxf.insert;txt=e.plain_text() if k=='MTEXT' else e.dxf.text;rot=float(e.dxf.get('rotation',0.))
            else:continue
        except (AttributeError,ezdxf.DXFError):continue
        code,text=sign_code(name,txt)
        out.append({'layer':eff_layer(e,split,doc),'role':'sign_v','closed':False,'points':np.array([[p[0]*units,p[1]*units]]),'holes':[],'code':code,'text':text,'rotation':rot})
    return out

def analyze(directory,settings,preview=None,hatch_preview=None):
    directory=Path(directory);dxf=directory/'input.dxf';kmz=directory/'input.kmz'
    crs=CRS.from_user_input(settings.crs)
    if not crs.is_projected: raise ValueError('Informe um sistema projetado em metros, como SIRGAS/UTM.')
    entities=[];counts=Counter();warnings=[];insunits=None;sign_layers=set();sign_texts=0
    if dxf.exists():
        doc=ezdxf.readfile(dxf);insunits=int(doc.header.get('$INSUNITS',0))
        ents=list(walk(doc.modelspace()))
        split=split_layers(ents,doc,getattr(settings,'layer_split','auto'))
        if split:warnings.append('Camada(s) '+', '.join(sorted(split))[:200]+' separada(s) por cor e tipo de entidade (tudo estava numa camada só). Indique o tipo de cada grupo na lista de camadas.')
        hroles=getattr(settings,'hatch_roles',None) or {};hauto=getattr(settings,'hatch_auto',False);hsig={}
        hidden=set(getattr(settings,'hidden_layers',None) or ());frozen=set(getattr(settings,'frozen_layers',None) or ())
        hidden_n=0
        for e in ents:
            layer=eff_layer(e,split,doc);counts[layer]+=1
            if layer in hidden or e.dxf.layer in hidden:hidden_n+=1;continue   # 1.26: camada oculta: fora do editor e do vídeo (o DXF não muda)
            role=next((r for r,ls in settings.layers.items() if layer in ls),None)
            if role is None:role=next((r for r,ls in settings.layers.items() if e.dxf.layer in ls),None)
            guessed=False
            if role is None and (not settings.layers or hauto):
                named=guess(layer)
                if named in ASSET_ROLES or named in ('oae','water'):
                    role=named;guessed=True
            if e.dxftype() in HATCH_TYPES:
                # 1.24: leitura automática das hachuras pela assinatura (camada + padrão + cor).
                sig,info=hatch_signature(e,layer,doc,settings.units_to_m);rec=hsig.setdefault(sig,info);rec['count']+=1;rec['area_m2']+=info['_area']
                if rec is not info:rec['loops']+=info['loops'];rec['islands']+=info['islands']
                if layer in frozen or e.dxf.layer in frozen:rec['frozen']=True
                if hatch_preview is not None:
                    hp=hatch_preview.setdefault(sig,{'n':0,'p':[]})
                    for r in _last_rings:
                        if hp['n']+len(r)<=6000:hp['p'].append(np.round(LineString(r).simplify(.3).coords,2).tolist());hp['n']+=len(r)
                rec['current_role']=role
                if role in ASSET_ROLES:
                    rec['suggested_layer_role']=role;rec['suggested_role']=None;rec['suggested_material']=None
                if sig in hroles:
                    hr=hroles[sig];r_=hr.role if hasattr(hr,'role') else hr.get('role')
                    if r_=='ignore':continue
                    mat=hr.material if hasattr(hr,'material') else hr.get('material')
                    convert(e,layer,r_,settings.units_to_m,entities,warnings,{'material':mat} if mat and mat!='auto' else None);continue
                if role is None and hauto and info['suggested_role']:
                    mat=info['suggested_material']
                    convert(e,layer,info['suggested_role'],settings.units_to_m,entities,warnings,{'material':mat} if mat else None);rec['auto_applied']=True;continue
            if role is None and layer not in {v for ls in settings.layers.values() for v in ls}: role=guess(layer) if not settings.layers else None;guessed=role is not None
            if not role and e.dxftype()=='HATCH' and 'HATCH_MATERIAL' in norm(layer) and getattr(settings,'auto_earthworks',True):role='earth_pending'
            if role=='earthwork':role='earth_pending'
            if role=='pavement' and guessed and 'EXIST' in norm(layer):role='existing_pavement'
            if not role:
                if preview is not None and e.dxftype() not in NO_GEOMETRY:convert(e,layer,'unmapped',settings.units_to_m,preview,[])
                continue
            if role=='sign_v':sign_layers.add(layer);continue
            if role=='sign_h' and e.dxftype() in ('TEXT','MTEXT'):sign_texts+=1;continue
            convert(e,layer,role,settings.units_to_m,entities,warnings)
        if hidden_n:warnings.append(f'{hidden_n} entidade(s) em camada(s) oculta(s) não entram no editor nem no vídeo: '+', '.join(sorted(hidden))[:160]+'.')
        if sign_layers-hidden:entities.extend(read_signs(doc,sign_layers-hidden,settings.units_to_m,split))
        if frozen:
            for v in entities:
                if v['layer'] in frozen:v['frozen']=True
        warnings.extend(check_roles(entities))
        if sign_texts:warnings.append(f'{sign_texts} texto(s) na sinalização horizontal do DXF não são desenhados: converta-os em polilinha/hachura no CAD.')
    # Ajuste DXF x imagem (pares de controle): aplicado só em memória, o DXF não é alterado.
    from .alignment import active,apply
    alignment=active(settings)
    if alignment:
        for e in entities+(preview if preview is not None else []):
            e['points']=apply(e['points'],alignment);e['holes']=[apply(h,alignment) for h in e.get('holes',[])]
    if getattr(settings,'accesses',None):
        from .access import items as access_items
        axes0=[v for v in entities if v['role']=='axis' and len(v['points'])>=2]
        if axes0:
            ax0=max(axes0,key=lambda e:LineString(e['points']).length)['points']
            entities.extend(access_items(settings,entities,ax0,warnings))
    for entity in entities:
        material=material_for('earthwork' if entity['role']=='earth_pending' else entity['role'],entity['layer'],getattr(settings,'layer_materials',{}))
        if material:entity['asset_material']=material
    from .pavement import tag_materials
    tag_materials(entities,settings)
    if getattr(settings,'pavement_areas',None) or getattr(settings,'shoulder_marks',None):
        from .surface_marks import items as surface_items
        entities=surface_items(settings,entities,warnings)
    if settings.overlays:entities.extend(read_overlays(directory,settings,warnings))
    # Native earthwork material hatches inherit the nearest typed cut/fill offset.
    from scipy.spatial import cKDTree
    samples={r:np.concatenate([e['points'] for e in entities if e['role']==r]) for r in ['cut','fill'] if any(e['role']==r for e in entities)}
    trees={r:cKDTree(p) for r,p in samples.items()}
    for e in entities:
        if e['role']=='earth_pending':
            if trees:e['role']=min(trees,key=lambda r:float(np.median(trees[r].query(e['points'][::max(1,len(e['points'])//40)])[0])))
            else:e['role']='earthwork'
    entities=[e for e in entities if e['role']!='earth_pending']
    # 1.40.8: KMZ é input técnico rastreável. Nunca é ignorado silenciosamente.
    kmz_status={
        'present':kmz.exists(), 'read_ok':False, 'used':False, 'required':False,
        'uses':[], 'line_count':0, 'poi_count':0, 'message':'KMZ/KML não carregado.'
    }
    try:
        kml_lines,kml_pois=read_kmz(kmz if kmz.exists() else None,crs)
        if kmz.exists():
            kmz_status.update(read_ok=True,line_count=len(kml_lines),poi_count=len(kml_pois),message='KMZ/KML lido e validado.')
            if kml_lines: kmz_status['uses'].append('referencia_geometrica')
            if kml_pois: kmz_status['uses'].append('pois')
    except Exception as exc:
        if kmz.exists():
            kmz_status['message']=f'KMZ/KML presente, mas inválido: {exc}'
            raise ValueError(kmz_status['message']) from exc
        raise
    axes=[v for v in entities if v['role']=='axis' and len(v['points'])>=2]
    if not axes and kml_lines:
        axes=[{'layer':'KMZ','role':'axis','reference_only':'KMZ' not in settings.layers.get('axis',[]),'closed':False,'points':max(kml_lines,key=lambda p:LineString(p).length),'holes':[]}];entities+=axes
        kmz_status['used']=True;kmz_status['required']=True;kmz_status['uses'].append('eixo_fallback')
        kmz_status['message']='KMZ/KML usado como eixo de referência porque não foi encontrado eixo válido no CAD.'
        warnings.append('Eixo obtido do KMZ. Pavimento só será desenhado se houver geometria no DXF.')
    if not axes:
        selected=next((r for r in getattr(settings,'route_alignments',[]) if r.enabled and len(r.points)>=2),None)
        custom=getattr(settings,'custom_axis',None)
        reference=selected or (custom if custom and custom.enabled and len(custom.points)>=2 else None)
        if reference:
            axes=[{'layer':'Alinhamento selecionado','role':'axis','reference_only':True,'closed':False,'points':np.array([[p.x,p.y] for p in reference.points]),'holes':[]}];entities+=axes
            warnings.append('Eixo de referência obtido de alinhamento selecionado; tráfego usa somente as rotas explicitamente habilitadas.')
    if not axes:
        kmz_status['required']=True
        raise ValueError('Nenhum eixo encontrado. Associe uma camada ao papel eixo ou envie KMZ com linha.')
    axes.sort(key=lambda e:LineString(e['points']).length,reverse=True);axis=axes[0]['points'].copy()
    ca=getattr(settings,'custom_axis',None)
    if ca is not None and ca.enabled and len(ca.points)>=2:
        # 1.22: alinhamento clicado no editor vira o eixo de referência (estaqueamento, câmera, sentido).
        axis=custom_axis_points(ca);warnings.append(f'Eixo de referência: “{ca.name}” ({len(ca.points)} pontos clicados no editor, {LineString(axis).length:.1f} m).')
    if settings.reverse_axis: axis=axis[::-1].copy()
    ds=np.r_[0,np.cumsum(np.linalg.norm(np.diff(axis,axis=0),axis=1))]
    if ds[-1]<10: raise ValueError(f'Eixo com extensão insuficiente ({ds[-1]:.1f} m; mínimo 10 m). Confira a camada do eixo e o fator de unidade.')
    allpts=np.concatenate([e['points'] for e in entities if e['role'] in ['axis','pavement','domain','shoulder']] or [e['points'] for e in entities])
    lo=allpts.min(0);hi=allpts.max(0)
    if np.max(hi-lo)>300000: raise ValueError('Extensão espacial superior a 300 km. Revise camadas, unidades ou coordenadas.')
    georef=None
    if kml_lines:
        kmz_status['used']=True
        if 'georreferenciamento' not in kmz_status['uses']: kmz_status['uses'].append('georreferenciamento')
        kmline=LineString(max(kml_lines,key=lambda p:LineString(p).length));mismatch=float(np.median([kmline.distance(__import__('shapely').geometry.Point(*p)) for p in axis[::max(1,len(axis)//100)]]))
        if mismatch>100: warnings.append(f'DXF/KMZ separados por cerca de {mismatch:.0f} m: confira o sistema de coordenadas.')
        georef=georef_check(axis,ds,kml_lines)
        if georef and 10<georef['median_m']<=100:warnings.append(f"Eixo do DXF e linha do KMZ com desvio mediano de {georef['median_m']:.1f} m (máx. {georef['max_m']:.1f} m em {georef['points']} pontos): confira CRS, unidades e alinhamento.")
    if insunits not in [0,6,None]: warnings.append(f'Unidade DXF INSUNITS={insunits}; fator aplicado: {settings.units_to_m}. Confira na prévia.')
    inferred={r:[] for r in ROLES}
    for l in counts:
        r=guess(l)
        if r: inferred[r].append(l)
    hatches=[]
    if dxf.exists():
        for sig,v in sorted(hsig.items(),key=lambda kv:-kv[1]['area_m2']):
            v=dict(v);v.pop('_area',None);v['sig']=sig;v['area_m2']=round(v['area_m2'],1);hatches.append(v)
    if kmz.exists() and kml_pois:
        kmz_status['used']=True
    if kmz.exists() and kmz_status['read_ok'] and not kmz_status['used']:
        kmz_status['message']='KMZ/KML lido e preservado como referência; não foi necessário nos cálculos principais desta análise.'
    # remove duplicatas mantendo ordem
    kmz_status['uses']=list(dict.fromkeys(kmz_status['uses']))
    report={'hatches':hatches[:300],'layers':[{'name':l,'count':n,'suggested_role':guess(l)} for l,n in sorted(counts.items())], 'suggested_mapping':inferred,'geometric_length_m':float(ds[-1]),'bounds':[lo.tolist(),hi.tolist()],'warnings':list(dict.fromkeys(warnings))[:100],'kmz_pois':kml_pois,'kmz_status':kmz_status,'alignment':alignment,'overlays':[{'id':o.id,'entities':sum(1 for e in entities if e.get('overlay')==o.id)} for o in settings.overlays],'georef_check':georef,'routes':[{'id':str(i),'layer':a['layer'],'length_m':round(LineString(a['points']).length,2),'length_exact_m':float(LineString(a['points']).length),'closed':a['closed']} for i,a in enumerate(axes)],'crs':settings.crs}
    return entities,axis,ds,axes,report


def custom_axis_points(ca,step=1.):
    """Polilinha dos pontos clicados; com 'smooth', curva suave (spline) que passa exatamente pelos pontos."""
    P=np.array([[p.x,p.y] for p in ca.points],float)
    keep=np.r_[True,np.linalg.norm(np.diff(P,axis=0),axis=1)>1e-3];P=P[keep]
    if len(P)<2:raise ValueError('Alinhamento do editor: marque pelo menos dois pontos distintos.')
    if ca.smooth and len(P)>=3:
        from scipy.interpolate import CubicSpline
        d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))]
        cs=CubicSpline(d,P,bc_type='natural');ss=np.linspace(0,d[-1],max(2,int(d[-1]/step)+1));ss=np.unique(np.r_[ss,d])
        return cs(ss)
    return P

HATCH_KW=[('existing_pavement',('EXIST','ATUAL','ANTIG')),('shoulder',('ACOST','SHOULDER')),('median',('CANTEIRO','MEDIAN','ILHA','GRAMA')),
          ('cut',('CORTE','CUT')),('fill',('ATERRO','FILL')),('water',('AGUA','RIO','CORREGO','LAGO')),('oae',('OAE','PONTE','VIADUTO','TABULEIRO')),
          ('pavement',('PAV','PISTA','ASFALT','CBUQ','CAUQ','REVEST','RIGID','CONCRET','CCP','PCC'))]

# 1.26: padrões de hachura do AutoCAD/ISO mais usados em projeto rodoviário -> tipo e material prováveis.
HATCH_PATTERNS={'AR-CONC':('pavement','rigido'),'AR-SAND':('pavement','flexivel'),'AR-RSHKE':('pavement',None),'AR-HBONE':('pavement','rigido'),
    'AR-B816':('pavement','rigido'),'AR-B816C':('pavement','rigido'),'AR-PARQ1':('pavement',None),'CONCRETE':('pavement','rigido'),
    'GRAVEL':('shoulder','flexivel'),'DOTS':('shoulder',None),'GRASS':('median',None),'SWAMP':('water',None),'EARTH':('cut',None),
    'ANSI37':('existing_pavement',None)}
_ACI_RGB={1:(255,0,0),2:(255,255,0),3:(0,255,0),4:(0,255,255),5:(0,0,255),6:(255,0,255),7:(255,255,255),8:(128,128,128),9:(192,192,192),
    250:(51,51,51),251:(80,80,80),252:(105,105,105),253:(130,130,130),254:(190,190,190),255:(255,255,255)}

def _rgb_of(col):
    if col.startswith('#'):return tuple(int(col[i:i+2],16) for i in (1,3,5))
    try:n=int(col.split()[-1])
    except ValueError:return None
    if n in _ACI_RGB:return _ACI_RGB[n]
    try:
        from ezdxf.colors import aci2rgb
        return tuple(aci2rgb(n))
    except Exception:return None

def color_role(rgb):
    """Sugestão fraca pela cor de preenchimento (só quando nome e padrão não dizem nada)."""
    if rgb is None:return None
    import colorsys
    r,g,b=(v/255 for v in rgb);h,l,sat=colorsys.rgb_to_hls(r,g,b);h*=360
    if sat<.15:return 'pavement' if l<.42 else 'existing_pavement' if l<.8 else None
    if 80<=h<=160 and sat>.2:return 'median'
    if 185<=h<=250 and sat>.25:return 'water'
    if (h<=40 or h>=340) and sat>.3:return 'cut' if l<.55 else None
    return None

_last_rings=[]
def hatch_signature(e,layer,doc,units=1.):
    """Assinatura de uma hachura (camada + padrão + cor) e a sugestão de tipo/material, com confiança e motivo."""
    try:pat=str(e.dxf.get('pattern_name','') or ('SOLID' if e.dxf.get('solid_fill',0) else '')).upper()
    except Exception:pat=''
    try:
        tc=e.dxf.get('true_color',None)
        col=('#%06x'%(tc&0xFFFFFF)) if tc is not None else 'ACI '+str(_aci(e,doc))
    except Exception:col='ACI ?'
    area=0.;loops=0;islands=0
    try:
        rings=[]
        for p in from_hatch(e):
            pts=np.array([(v.x,v.y) for v in p.flattening(.5/units,segments=4)])*units
            if len(pts)>=3:rings.append(pts)
        loops=len(rings);_last_rings[:]=rings
        if rings:
            shape=Polygon()
            for r in rings:shape=shape.symmetric_difference(make_valid(Polygon(r)))
            ps=_polygons(shape);area=float(sum(p.area for p in ps));islands=sum(len(p.interiors) for p in ps)
    except Exception:pass
    n=norm(layer+' '+pat);role=None;mat=None;conf=None;why=''
    for r,kws in HATCH_KW:
        k=next((k for k in kws if k in n),None)
        if k:role=r;conf='alta';why=f'nome contém “{k}”';break
    pinfo=HATCH_PATTERNS.get(pat)
    if role is None:
        g=guess(layer)
        if g in ('pavement','existing_pavement','shoulder','median','cut','fill','water','oae'):role=g;conf='alta';why='perfil de camadas'
    if role is None and pinfo:role=pinfo[0];conf='média';why=f'padrão {pat}'
    hint=None
    if role is None and pat in ('SOLID',''):
        hint=color_role(_rgb_of(col))   # só indicação na lista (não é aplicada automaticamente)
    if role in ('pavement','existing_pavement','shoulder'):
        mat='rigido' if any(k in n for k in ('CONC','RIGID','CCP','PCC','AR-CONC')) else 'flexivel' if any(k in n for k in ('ASFALT','CBUQ','CAUQ','TSD','AR-SAND')) else (pinfo[1] if pinfo else None)
    sig=f'{layer} | {pat or "?"} | {col}'
    return sig,{'layer':layer,'pattern':pat or '?','color':col,'count':0,'area_m2':0.,'_area':area,'loops':loops,'islands':islands,'entity':e.dxftype(),
                'suggested_role':role,'suggested_material':mat,'confidence':conf,'reason':why,'color_hint':hint,'current_role':None}

def georef_check(axis,ds,kml_lines,n=25):
    """1.20: confere geometricamente o eixo do DXF contra as linhas do KMZ em pontos distribuídos pelo segmento.
    Retorna desvios (m) e a estaca de cada ponto; só pontos onde há linha KMZ por perto entram na estatística."""
    from shapely.geometry import Point as _P,MultiLineString
    lines=MultiLineString([LineString(p) for p in kml_lines if len(p)>=2])
    if lines.is_empty:return None
    ss=np.linspace(0,ds[-1],n);pts=np.column_stack([np.interp(ss,ds,axis[:,0]),np.interp(ss,ds,axis[:,1])])
    d=np.array([lines.distance(_P(*q)) for q in pts])
    ok=d<500
    if ok.sum()<3:return {'points':int(ok.sum()),'median_m':float(np.median(d)),'p95_m':float(np.percentile(d,95)),'max_m':float(d.max()),'samples':[]}
    dd=d[ok]
    return {'points':int(ok.sum()),'median_m':round(float(np.median(dd)),2),'p95_m':round(float(np.percentile(dd,95)),2),'max_m':round(float(dd.max()),2),
            'samples':[{'s_m':round(float(a),1),'dev_m':round(float(b),2)} for a,b in zip(ss[ok],dd)],'transform':'nenhuma (coordenadas do DXF no CRS do projeto; KMZ convertido de WGS84)'}

def write_layer_preview(directory,entities,unmapped,limit=40000):
    """1.14: geometria simplificada de TODAS as camadas (mapeadas ou não) para conferir no editor qual é qual."""
    import json as _json
    by={}
    for e in list(entities)+list(unmapped or []):
        if e.get('overlay'):continue
        p=np.asarray(e['points'])
        if len(p)<2:continue
        g=LineString(p).simplify(.3)
        q=np.round(np.asarray(g.coords),2).tolist()
        d=by.setdefault(e['layer'],{'role':e['role'] if e['role']!='unmapped' else None,'p':[],'n':0})
        if d['n']+len(q)>limit:continue
        d['p'].append(q);d['n']+=len(q)
    f=Path(directory)/'camadas_previa.json';tmp=f.with_suffix('.tmp');tmp.write_text(_json.dumps(by,separators=(',',':')),encoding='utf-8');tmp.replace(f)
    return {k:v['n'] for k,v in by.items()}
