"""Arrasto técnico calculado nas coordenadas originais, sem alterar o vídeo."""
import numpy as np
from shapely.geometry import mapping
from shapely.ops import unary_union
from .vehicle_motion import prepare_points,axle_geometry_prepared,PROFILES
from .vehicle_safety import body


def inspect(points,allowed,vehicle='car',station=None,span=60):
    p,d=prepare_points(points)
    if len(p)>200001 or d[-1]>100000:raise ValueError('Divida o trecho antes de inspecionar o arrasto.')
    if vehicle not in PROFILES:raise ValueError('Modelo de veículo não cadastrado.')
    station=float(d[-1]/2 if station is None else station)
    if not np.isfinite([station,span]).all() or not 0<=station<=d[-1] or not 5<=span<=200:raise ValueError('Distância ou extensão de inspeção inválida.')
    stations=np.unique(np.r_[np.linspace(max(0,station-span/2),min(d[-1],station+span/2),min(101,max(3,int(span/2)+1))),station])
    geom=axle_geometry_prepared(p,d,vehicle,stations);length,width,*_=PROFILES[vehicle]
    polygons=[body(c,h,length,width) for c,h in zip(geom['center'],geom['heading'])]
    rows=[{'station_m':float(s),'polygon':np.asarray(g.exterior.coords).tolist(),'center':c.tolist(),'front':f.tolist(),'rear':r.tolist(),'ok':bool(allowed.covers(g))} for s,g,c,f,r in zip(stations,polygons,geom['center'],geom['front'],geom['rear'])]
    return {'vehicle':vehicle,'length_m':length,'width_m':width,'route_length_m':float(d[-1]),'station_m':station,'bodies':rows,'envelope':mapping(unary_union(polygons)),'outside_samples':sum(not r['ok'] for r in rows),'technical_only':True,'scope':'Envelope rígido de frente/traseira, não articulado. Inspeção geométrica local, sem afirmar ausência de colisões com veículos ou pessoas.'}
