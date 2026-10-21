from __future__ import annotations
from math import isfinite
from pathlib import Path
import ezdxf
from ezdxf.colors import aci2rgb
from ezdxf.path import make_path
from videos_rodoviarios.core.models import GeometryEntity,TextEntity
from videos_rodoviarios.geometry.classify import classify_layer
SUPPORTED_CURVES={"LINE","LWPOLYLINE","POLYLINE","ARC","SPLINE","CIRCLE","ELLIPSE"};SUPPORTED_TEXT={"TEXT","MTEXT"}
def _sanitize(points):
 clean=[]
 for x,y in points:
  if isfinite(x) and isfinite(y):
   p=(float(x),float(y))
   if not clean or abs(clean[-1][0]-p[0])>1e-9 or abs(clean[-1][1]-p[1])>1e-9:clean.append(p)
 return clean
def _flatten(entity,tolerance):
 if entity.dxftype()=="LINE":return _sanitize([(entity.dxf.start.x,entity.dxf.start.y),(entity.dxf.end.x,entity.dxf.end.y)])
 path=make_path(entity);return _sanitize([(p.x,p.y) for p in path.flattening(distance=max(tolerance,.001),segments=12)])
def _layer_state(doc,name):
 try:l=doc.layers.get(name)
 except Exception:return True,False,False
 try:off=bool(l.is_off())
 except Exception:off=False
 try:frozen=bool(l.is_frozen())
 except Exception:frozen=False
 return not(off or frozen),off,frozen
def _rgb(entity,doc,layer):
 try:
  tc=getattr(entity.dxf,"true_color",None)
  if tc is not None:return ((tc>>16)&255,(tc>>8)&255,tc&255)
  aci=int(getattr(entity.dxf,"color",256))
  if aci in (0,256):
   try:aci=int(doc.layers.get(layer).color)
   except Exception:return None
  r=aci2rgb(abs(aci));return(int(r.r),int(r.g),int(r.b))
 except Exception:return None
def _visual(entity,doc,layer):
 return dict(color_rgb=_rgb(entity,doc,layer),lineweight=int(getattr(entity.dxf,"lineweight",-1)),linetype=str(getattr(entity.dxf,"linetype","BYLAYER")))
def _hatch_loops(entity,tolerance):
 loops=[]
 try:
  for p in entity.paths:
   try:path=make_path(p);pts=_sanitize([(v.x,v.y) for v in path.flattening(distance=max(tolerance,.001),segments=12)])
   except Exception:
    pts=[]
    if hasattr(p,"vertices"):pts=_sanitize([(v[0],v[1]) for v in p.vertices])
   if len(pts)>=3:
    if pts[0]!=pts[-1]:pts.append(pts[0])
    loops.append(pts)
 except Exception:pass
 return loops
def _append_insert(doc,entity,entities,texts,warnings,tolerance,parent_layer):
 name=str(getattr(entity.dxf,"name",""));handle=str(getattr(entity.dxf,"handle",""));layer=str(getattr(entity.dxf,"layer",parent_layer));visible,off,frozen=_layer_state(doc,layer)
 try:
  virtual=list(entity.virtual_entities())
 except Exception as exc:warnings.append(f"Bloco {name or handle} não pôde ser expandido: {exc}");return
 for i,v in enumerate(virtual):
  et=v.dxftype();v_layer=str(getattr(v.dxf,"layer",layer));v_layer=layer if v_layer=="0" else v_layer;category=classify_layer(v_layer);vis,voff,vfrozen=_layer_state(doc,v_layer)
  if et in SUPPORTED_CURVES:
   try:
    pts=_flatten(v,tolerance)
    if len(pts)>=2:entities.append(GeometryEntity(handle=f"{handle}:B{i+1}",dxftype=et,layer=v_layer,category=category,points=pts,closed=bool(getattr(v,"closed",False)),visible=vis,layer_off=voff,layer_frozen=vfrozen,block_name=name,**_visual(v,doc,v_layer)))
   except Exception as exc:warnings.append(f"Entidade do bloco {name} ignorada: {exc}")
  elif et in SUPPORTED_TEXT:
   try:
    value=v.dxf.text if et=="TEXT" else v.plain_text();ins=v.dxf.insert;texts.append(TextEntity(handle=f"{handle}:T{i+1}",layer=v_layer,text=str(value),x=float(ins.x),y=float(ins.y),visible=vis,layer_off=voff,layer_frozen=vfrozen,height=float(getattr(v.dxf,"height",2.5)),rotation=float(getattr(v.dxf,"rotation",0.0)),color_rgb=_rgb(v,doc,v_layer),style=str(getattr(v.dxf,"style",""))))
   except Exception:pass
def read_dxf(path,curve_tolerance_m=.05):
 path=Path(path)
 if not path.exists():raise FileNotFoundError(path)
 try:doc=ezdxf.readfile(path)
 except ezdxf.DXFStructureError as exc:raise ValueError(f"DXF inválido ou corrompido: {exc}") from exc
 entities=[];texts=[];warnings=[]
 for entity in doc.modelspace():
  etype=entity.dxftype();layer=str(getattr(entity.dxf,"layer","0"));handle=str(getattr(entity.dxf,"handle",""));visible,off,frozen=_layer_state(doc,layer);category=classify_layer(layer)
  if etype=="INSERT":_append_insert(doc,entity,entities,texts,warnings,curve_tolerance_m,layer);continue
  if etype=="HATCH":
   loops=_hatch_loops(entity,curve_tolerance_m)
   if not loops:warnings.append(f"Hachura {handle or '?'} da layer {layer} sem contorno utilizável.")
   for idx,points in enumerate(loops):entities.append(GeometryEntity(handle=f"{handle}:H{idx+1}",dxftype="HATCH",layer=layer,category=category,points=points,closed=True,visible=visible,layer_off=off,layer_frozen=frozen,hatch_pattern=str(getattr(entity.dxf,"pattern_name","")),**_visual(entity,doc,layer)))
  elif etype in SUPPORTED_CURVES:
   try:
    points=_flatten(entity,curve_tolerance_m)
    if len(points)>=2:entities.append(GeometryEntity(handle=handle,dxftype=etype,layer=layer,category=category,points=points,closed=bool(getattr(entity,"closed",False)),visible=visible,layer_off=off,layer_frozen=frozen,**_visual(entity,doc,layer)))
   except Exception as exc:warnings.append(f"Entidade {handle or '?'} ({etype}) ignorada: {exc}")
  elif etype in SUPPORTED_TEXT:
   try:
    value=entity.dxf.text if etype=="TEXT" else entity.plain_text();ins=entity.dxf.insert;texts.append(TextEntity(handle=handle,layer=layer,text=str(value),x=float(ins.x),y=float(ins.y),visible=visible,layer_off=off,layer_frozen=frozen,height=float(getattr(entity.dxf,"height",2.5)),rotation=float(getattr(entity.dxf,"rotation",0.0)),color_rgb=_rgb(entity,doc,layer),style=str(getattr(entity.dxf,"style",""))))
   except Exception as exc:warnings.append(f"Texto {handle or '?'} ignorado: {exc}")
 if not entities:raise ValueError("DXF sem geometria suportada e válida em ModelSpace.")
 return entities,texts,warnings
