"""Medidas em planta; não mistura altura, eixos de apoio e travessia livre."""
import math


def distance(a,b):
    return math.hypot(float(a.x)-float(b.x),float(a.y)-float(b.y))


def gantry_dimensions(g):
    measured=distance(g.crossing_a,g.crossing_b) if g.crossing_a and g.crossing_b else None
    supports=distance(g.a,g.b)
    return {'id':g.id,'name':g.name,'support_axis_distance_m':supports,'crossing_m':measured,
            'crossing_status':'measured' if measured is not None else 'not_measured',
            'beam_width_m':g.beam_width_m,'height_m':g.height_m,
            'scope':'Medidas horizontais em coordenadas do projeto; altura não integra a travessia.'}


def resize_crossing(g,width):
    """Ajuste explícito: mantém centro e orientação, postes fora da travessia."""
    from .models import Point
    if not math.isfinite(width) or not 2<=width<=100:raise ValueError('Travessia deve estar entre 2 e 100 m.')
    L=distance(g.a,g.b);ux=(g.b.x-g.a.x)/L;uy=(g.b.y-g.a.y)/L
    cx=(g.a.x+g.b.x)/2;cy=(g.a.y+g.b.y)/2
    point=lambda d:Point(x=cx+ux*d,y=cy+uy*d)
    half=width/2
    # Postes quadrados de 0,9 m em planta, alinhados à viga.
    return g.model_copy(update={'a':point(-half-.45),'b':point(half+(.45 if g.kind=='portico' else 0)),
                                'crossing_a':point(-half),'crossing_b':point(half)})


def audit(settings):
    from shapely.geometry import Polygon
    rows=[]
    for group in ('route_alignments','traffic_paths','pavement_areas','shoulder_marks','lane_ranges','crosswalks'):
        for element in getattr(settings,group,[]) or []:
            points=getattr(element,'points',None)
            row={'kind':group,'id':getattr(element,'id',''),'name':getattr(element,'name',group)}
            if points:
                xy=[(p.x,p.y) for p in points]
                if group=='pavement_areas':
                    shape=Polygon(xy);row.update(perimeter_m=shape.length,area_m2=shape.area,valid=shape.is_valid)
                else:row['length_m']=sum(distance(a,b) for a,b in zip(points,points[1:]))
            else:
                a=getattr(element,'a',None) or getattr(element,'start',None)
                b=getattr(element,'b',None) or getattr(element,'end',None)
                if a is not None and b is not None:row['endpoint_distance_m']=distance(a,b)
            if hasattr(element,'width_m'):row['configured_width_m']=element.width_m
            rows.append(row)
    return {'units':'m','gantries':[gantry_dimensions(g) for g in settings.gantries],
            'elements':rows,'note':'Dimensões em planta. Comprimento de linha e largura cadastrada são grandezas distintas; perímetro não é largura.'}
