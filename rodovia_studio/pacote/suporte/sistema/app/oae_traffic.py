"""Cotas informadas e orientação de OAE; nunca inventa desnível."""
import math
import numpy as np
from shapely.geometry import Point,LineString
from shapely.ops import unary_union


def valid_grade(item):
    try:z=float(item.get('level_m',0))
    except (TypeError,ValueError,OverflowError):return False
    return bool(item.get('grade_confirmed')) and item.get('elevation_valid',True) and math.isfinite(z) and abs(z)>=.1


def classify(items,axes):
    rows=[];warnings=[]
    for item in items:
        deck=item['deck'];line=np.asarray(item['line'],float)
        try:z=float(item.get('level_m',0));valid=math.isfinite(z) and bool(item.get('elevation_valid',True))
        except (ValueError,TypeError,OverflowError):z=0.;valid=False
        if not valid:z=0.;warnings.append('OAE com cota inválida: confira o cadastro; nenhum desnível foi presumido.')
        u=line[-1]-line[0];u/=max(float(np.linalg.norm(u)),1e-9)
        transverse=False;longitudinal=False
        for axis in axes:
            p=np.asarray(axis['points'],float)
            for a,b in zip(p[:-1],p[1:]):
                v=b-a;length=float(np.linalg.norm(v))
                if length<1e-6 or not deck.intersects(LineString([a,b])):continue
                alignment=abs(float((v/length)@u));longitudinal|=alignment>.85;transverse|=alignment<.4
        if transverse and abs(z)<.1:warnings.append('OAE transversal com Z=0: não foi criada uma barreira nem presumido desnível. Informe a cota da estrutura antes de representar uma passagem em níveis diferentes.')
        if abs(z)>=.1 and not item.get('grade_confirmed'):warnings.append('OAE com cota CAD não nula: confirme o desnível relativo no cadastro da OAE. Uma cota absoluta isolada não libera travessia ferroviária.')
        rows.append({'id':item.get('id','OAE'),'z_m':z if valid else None,'longitudinal':longitudinal,'transverse':transverse,'grade_separation_known':valid_grade(item)})
    return rows,warnings


def grade_separated(info,point,road,rail):
    for item in info:
        if not valid_grade(item) or not item['deck'].covers(point):continue
        line=np.asarray(item['line'],float);u=line[-1]-line[0];u/=max(float(np.linalg.norm(u)),1e-9)
        a=abs(float(u@road));b=abs(float(u@rail))
        if max(a,b)>.9 and abs(a-b)>.02:return True
    return False
