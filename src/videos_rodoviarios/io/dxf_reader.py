from __future__ import annotations
from math import isfinite
from pathlib import Path
import ezdxf
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
 path=make_path(entity);return _sanitize([(p.x,p.y) for p in path.flattening(distance=max(tolerance,.001),segments=8)])
def _layer_state(doc,name):
 try:l=doc.layers.get(name)
 except Exception:return True,False,False
 try:off=bool(l.is_off())
 except Exception:off=False
 try:frozen=bool(l.is_frozen())
 except Exception:frozen=False
 return not(off or frozen),off,frozen
def _hatch_loops(entity,tolerance):
 """Extrai contornos fechados de HATCH; cada loop vira uma superfície mensurável."""
 loops=[]
 try:
  for p in entity.paths:
   try:
    path=make_path(p);pts=_sanitize([(v.x,v.y) for v in path.flattening(distance=max(tolerance,.001),segments=8)])
   except Exception:
    pts=[]
    if hasattr(p,"vertices"):pts=_sanitize([(v[0],v[1]) for v in p.vertices])
   if len(pts)>=3:
    if pts[0]!=pts[-1]:pts.append(pts[0])
    loops.append(pts)
 except Exception:pass
 return loops
def read_dxf(path,curve_tolerance_m=.10):
 path=Path(path)
 if not path.exists():raise FileNotFoundError(path)
 try:doc=ezdxf.readfile(path)
 except ezdxf.DXFStructureError as exc:raise ValueError(f"DXF inválido ou corrompido: {exc}") from exc
 entities=[];texts=[];warnings=[];msp=doc.modelspace()
 for entity in msp:
  etype=entity.dxftype();layer=str(getattr(entity.dxf,"layer","0"));handle=str(getattr(entity.dxf,"handle",""));visible,off,frozen=_layer_state(doc,layer);category=classify_layer(layer)
  if etype=="HATCH":
   loops=_hatch_loops(entity,curve_tolerance_m)
   if not loops:warnings.append(f"Hachura {handle or '?'} da layer {layer} sem contorno utilizável.")
   for idx,points in enumerate(loops):entities.append(GeometryEntity(handle=f"{handle}:H{idx+1}",dxftype="HATCH",layer=layer,category=category,points=points,closed=True,visible=visible,layer_off=off,layer_frozen=frozen))
  elif etype in SUPPORTED_CURVES:
   try:
    points=_flatten(entity,curve_tolerance_m)
    if len(points)>=2:entities.append(GeometryEntity(handle=handle,dxftype=etype,layer=layer,category=category,points=points,closed=bool(getattr(entity,"closed",False)),visible=visible,layer_off=off,layer_frozen=frozen))
    else:warnings.append(f"Entidade {handle or '?'} ({etype}) ignorada por geometria degenerada.")
   except Exception as exc:warnings.append(f"Entidade {handle or '?'} ({etype}) ignorada: {exc}")
  elif etype in SUPPORTED_TEXT:
   try:
    value=entity.dxf.text if etype=="TEXT" else entity.plain_text();ins=entity.dxf.insert;x,y=float(ins.x),float(ins.y)
    if isfinite(x) and isfinite(y):texts.append(TextEntity(handle=handle,layer=layer,text=str(value),x=x,y=y,visible=visible,layer_off=off,layer_frozen=frozen))
   except Exception as exc:warnings.append(f"Texto {handle or '?'} ignorado: {exc}")
 if not entities:raise ValueError("DXF sem geometria suportada e válida em ModelSpace.")
 return entities,texts,warnings
